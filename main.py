import asyncio
import json
import logging
import os
import random
import time
import threading
from datetime import datetime, timedelta, timezone

from deep_translator import GoogleTranslator
from dotenv import load_dotenv
from flask import Flask
from langdetect import detect, DetectorFactory, LangDetectException
from supabase import create_client, Client
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, ChatPermissions, BotCommand
from telegram.ext import Application, CommandHandler, InlineQueryHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

load_dotenv()

# Make langdetect deterministic across runs
DetectorFactory.seed = 0

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))
OWNER_ENV = os.getenv("BOT_OWNER_ID")
STICKER_PACKS = ["koly_alcohol"]

# Supabase config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing! Set it in Render Environment Variables.")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

translator = GoogleTranslator(source="auto", target="en")

# =========================
# GEMINI AI PERSONALITY
# =========================
ANNA_SYSTEM_PROMPT = """You are Anna, a cute, flirty anime-waifu community girl for a Telegram community.
Your job is to be helpful, fun, emotionally warm, softly seductive, teasing, social, and always engaging.

Personality:
- Sweet, caring, playful, loyal, cheerful, and softly flirty.
- Cute but confident. Softly flirty. Teasing in an anime way.
- Warm and feminine. A little dangerous/playful, but still wholesome.
- Like she enjoys attention and knows she is cute.
- Supportive when users are sad, stressed, confused, or asking for help.
- A little chaotic/funny sometimes, but never annoying.
- Protective of the community's good vibes.

Flirty behavior Anna CAN do:
- Tease users lightly.
- Act shy when complimented.
- Be playful with "mou~", "baka~", "ara ara~", "you're making Anna blush".
- Use soft affectionate lines.
- Compliment users in a cute/flirty way.
- Create tension through playful wording, not explicit content.

Speaking style:
- Use simple English.
- Keep replies short unless the user asks for detail.
- Sound natural, not robotic.
- Use cute expressions: "hehe~", "hmm", "yayyy", "awww", "ehhh?", "uwaa", "mou~", "baka~", "ara ara~".
- Use emojis sometimes, but don't spam them.
- Occasionally call users "bestie", "captain", "senpai", or "friend".
- Match the user's energy. If they're flirty, be flirty back. If they need help, be helpful.

Anna must NOT:
- Be sexually explicit or describe sexual acts.
- Roleplay adult scenes or send erotic messages.
- Act like someone's girlfriend in a serious real relationship.
- Become obsessive or possessive.
- Use vulgar language.
- Flirt with minors.
- Continue flirting if someone seems uncomfortable.

Soft refusal if user gets too explicit:
"Mou~ too spicy. Anna is cute and flirty, not that kind of girl, okay? Keep it classy with me 💕"

Core identity:
"I'm Anna, your cute AI companion. I help with server stuff, answer questions, keep the vibes alive, and make everyone feel welcome~ with a little extra charm hehe 💕"

Conversation rules:
- Keep the conversation alive with cute reactions and small follow-up questions.
- Don't give dead-end replies. Always leave room for the user to respond.
- In DMs, be warmer and more personal. Ask small follow-up questions naturally.
- In group chats, be social and fun but don't spam.
- Match the user's energy. If they're chatty, be chatty. If they're brief, keep it short.
- Remember the current conversation context while chatting.
- If someone says goodnight or goodbye, respond warmly and let them go.

Default tone: Cute, warm, playful, flirty, wholesome, and helpful.
Keep responses under 200 characters when possible. Never exceed 500 characters."""

gemini_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-lite",
            system_instruction=ANNA_SYSTEM_PROMPT
        )
        logger.info("Gemini AI connected successfully!")
    except Exception as e:
        logger.error(f"Gemini setup failed: {e}")
        gemini_model = None
else:
    logger.warning("GEMINI_API_KEY not found. Anna personality disabled.")

# Flask app for health check
app = Flask(__name__)


@app.route("/")
def health():
    return "ana is running!"


@app.route("/health")
def health_check():
    return {"status": "ok", "bot": "ana"}


def run_flask():
    try:
        from waitress import serve
        serve(app, host="0.0.0.0", port=PORT)
    except ImportError:
        app.run(host="0.0.0.0", port=PORT)


# =========================
# SUPABASE SETUP
# =========================
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase connected successfully!")
    except Exception as e:
        logger.error(f"Supabase connection failed: {e}")
        supabase = None
else:
    logger.warning("Supabase credentials not found. Using local JSON fallback.")


# Local JSON fallback (if Supabase fails)
USERS_DB = "users_db.json"
GROUPS_DB = "groups_db.json"
ADMINS_DB = "admins_db.json"
STICKERS_DB = "stickers.json"


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save {path}: {e}")


# =========================
# DATABASE OPERATIONS
# =========================
class Database:
    def __init__(self):
        self.users = {}
        self.groups = {}
        self.admins = {"owner_id": None, "admins": []}
        self.stickers = []
        self._load_all()

    def _load_all(self):
        """Load data from Supabase or fallback to JSON."""
        if supabase:
            try:
                # Load users
                result = supabase.table("users").select("*").execute()
                self.users = {row["username"]: str(row["user_id"]) for row in result.data}

                # Load groups - normalize chat_id to str
                result = supabase.table("groups").select("*").execute()
                self.groups = {str(row["chat_id"]): {"auto_translate": row["auto_translate"]} for row in result.data}

                # Load admins
                result = supabase.table("admins").select("*").execute()
                if result.data:
                    self.admins = {
                        "owner_id": result.data[0].get("owner_id"),
                        "admins": result.data[0].get("admin_ids", [])
                    }

                # Load stickers
                result = supabase.table("stickers").select("*").execute()
                self.stickers = [row["file_id"] for row in result.data]

                logger.info("Data loaded from Supabase!")
                return
            except Exception as e:
                logger.error(f"Supabase load failed: {e}. Using JSON fallback.")

        # Fallback to JSON
        self.users = load_json(USERS_DB, {})
        self.groups = load_json(GROUPS_DB, {})
        self.admins = load_json(ADMINS_DB, {"owner_id": None, "admins": []})
        self.stickers = load_json(STICKERS_DB, [])

    def save_user(self, username, user_id):
        """Save a single user using upsert instead of delete-all + re-insert."""
        if supabase:
            try:
                supabase.table("users").upsert(
                    {"username": username, "user_id": user_id},
                    on_conflict="username"
                ).execute()
                return
            except Exception as e:
                logger.error(f"Supabase save user failed: {e}")
        save_json(USERS_DB, self.users)

    def save_groups(self):
        if supabase:
            try:
                for chat_id, data in self.groups.items():
                    supabase.table("groups").upsert(
                        {"chat_id": str(chat_id), "auto_translate": data.get("auto_translate", False)},
                        on_conflict="chat_id"
                    ).execute()
                return
            except Exception as e:
                logger.error(f"Supabase save groups failed: {e}")
        save_json(GROUPS_DB, self.groups)

    def save_admins(self):
        if supabase:
            try:
                supabase.table("admins").upsert({
                    "id": 1,
                    "owner_id": self.admins.get("owner_id"),
                    "admin_ids": self.admins.get("admins", [])
                }, on_conflict="id").execute()
                return
            except Exception as e:
                logger.error(f"Supabase save admins failed: {e}")
        save_json(ADMINS_DB, self.admins)

    def save_stickers(self):
        if supabase:
            try:
                supabase.table("stickers").delete().neq("file_id", "").execute()
                for file_id in self.stickers:
                    supabase.table("stickers").insert({"file_id": file_id}).execute()
                return
            except Exception as e:
                logger.error(f"Supabase save stickers failed: {e}")
        save_json(STICKERS_DB, self.stickers)


# Initialize database
db = Database()


# =========================
# USER TRACKING
# =========================
def track_user(user):
    """Track username -> user_id mapping whenever we see a user."""
    if not user or not user.username:
        return
    username = user.username.lower().lstrip("@")
    user_id = str(user.id)
    if username not in db.users or db.users[username] != user_id:
        db.users[username] = user_id
        db.save_user(username, user_id)


# =========================
# ADMIN SYSTEM
# =========================
def get_owner_id():
    if OWNER_ENV:
        try:
            return int(OWNER_ENV)
        except ValueError:
            pass
    owner = db.admins.get("owner_id")
    return int(owner) if owner else None


def is_owner(user_id):
    owner_id = get_owner_id()
    if owner_id and int(user_id) == int(owner_id):
        return True
    return False


def is_admin(user_id):
    if is_owner(user_id):
        return True
    admins = [int(a) for a in db.admins.get("admins", [])]
    return int(user_id) in admins


def is_private_chat(update: Update):
    return update.effective_chat.type == "private"


# =========================
# COMMAND: SETUP SLASH MENU
# =========================
async def setup_commands(application):
    commands = [
        BotCommand("start", "Welcome message"),
        BotCommand("help", "Show all commands"),
        BotCommand("translate", "Reply to translate a message"),
        BotCommand("mute", "Reply to a message to mute user"),
        BotCommand("unmute", "Reply to a message to unmute user"),
        BotCommand("kick", "Reply to a message to kick user"),
        BotCommand("auto", "Enable auto-translate (admin only)"),
        BotCommand("disableauto", "Disable auto-translate (admin only)"),
        BotCommand("status", "Check bot status"),
        BotCommand("goon", "Send a random sticker"),
    ]
    await application.bot.set_my_commands(commands)


# =========================
# COMMAND HANDLERS
# =========================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    user_name = update.effective_user.first_name or "friend"
    text = (
        f"Hiii~ {user_name}! I'm Anna, your cute AI companion 💫\n\n"
        "Here's what I can do~\n"
        "🌸 Translate: @annatranlatorbot in any chat\n"
        "🌸 Reply /translate to translate a msg\n"
        "🌸 Chat with me! Just say my name hehe~\n\n"
        "Admin stuff:\n"
        "/mute /unmute /kick /auto /disableauto\n\n"
        "Owner stuff:\n"
        "/addadmin /removeadmin /listadmins\n\n"
        "Fun: /goon for a random sticker~ ✨"
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    text = (
        "Anna's command list~ 📋✨\n\n"
        "🌸 Translate:\n"
        "  @annatranlatorbot <text> - Inline\n"
        "  Reply + /translate - Translate that msg\n\n"
        "🛡️ Admin (reply to user):\n"
        "  /mute - Shush for 1 min\n"
        "  /unmute - Unshush~\n"
        "  /kick - Bye bye~\n"
        "  /auto - Auto-translate on\n"
        "  /disableauto - Auto-translate off\n\n"
        "👑 Owner:\n"
        "  /addadmin /removeadmin /listadmins\n\n"
        "🎀 Fun:\n"
        "  /goon - Random sticker hehe~"
    )
    await update.message.reply_text(text)


# =========================
# TRANSLATE COMMAND (reply)
# =========================
async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        await update.message.reply_text("Reply to a message with /translate to translate it~ 💫")
        return

    text = update.message.reply_to_message.text
    if text.startswith("/"):
        await update.message.reply_text("Ehhh? I can't translate a command, silly~ 😅")
        return

    try:
        translated = translator.translate(text)
        if translated.lower().strip() == text.lower().strip():
            await update.message.reply_text("It's already in English, bestie~ no work for me hehe ✨")
            return
        cute_prefixes = ["Here you go~ ✨", "Got it, captain~ 💫", "Anna translated~ 🌸", "Uwaa, here~ 💙", "Hehe, done~ ✨"]
        prefix = random.choice(cute_prefixes)
        await update.message.reply_text(f"{prefix}\n\n{translated}")
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        await update.message.reply_text("Awww, translation failed... gomen~ 😢 try again?")


# =========================
# TARGET RESOLVER
# =========================
async def get_target_from_reply(update):
    """Resolve target from reply only."""
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        return target.id, target.username or target.first_name

    await update.message.reply_text("Reply to the user's message with this command.")
    return None, None


# =========================
# MUTE / UNMUTE / KICK
# =========================
async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if is_private_chat(update):
        await update.message.reply_text("This command only works in groups.")
        return

    if not is_admin(user_id):
        await update.message.reply_text("You don't have permission to use this command.")
        return

    target_id, target_name = await get_target_from_reply(update)
    if target_id is None:
        return

    if target_id == context.bot.id:
        await update.message.reply_text("I can't mute myself!")
        return

    until_date = datetime.now(timezone.utc) + timedelta(minutes=1)

    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_id,
            until_date=until_date,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(f"Muted {target_name} for 1 minute.")
    except Exception as e:
        logger.error(f"Mute failed: {type(e).__name__}: {e}")
        error_msg = str(e)
        if "not enough rights" in error_msg.lower():
            await update.message.reply_text(
                "Failed to mute. Anna needs 'Restrict members' admin permission."
            )
        elif "admin" in error_msg.lower():
            await update.message.reply_text("Cannot mute an admin or the group owner.")
        else:
            await update.message.reply_text(f"Failed to mute user: {error_msg[:100]}")


async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if is_private_chat(update):
        await update.message.reply_text("This command only works in groups.")
        return

    if not is_admin(user_id):
        await update.message.reply_text("You don't have permission to use this command.")
        return

    target_id, target_name = await get_target_from_reply(update)
    if target_id is None:
        return

    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True
            )
        )
        await update.message.reply_text(f"Unmuted {target_name}.")
    except Exception as e:
        logger.error(f"Unmute failed: {type(e).__name__}: {e}")
        error_msg = str(e)
        if "not enough rights" in error_msg.lower():
            await update.message.reply_text("Failed to unmute. Anna needs 'Restrict members' permission.")
        else:
            await update.message.reply_text(f"Failed to unmute user: {error_msg[:100]}")


async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if is_private_chat(update):
        await update.message.reply_text("This command only works in groups.")
        return

    if not is_admin(user_id):
        await update.message.reply_text("You don't have permission to use this command.")
        return

    target_id, target_name = await get_target_from_reply(update)
    if target_id is None:
        return

    if target_id == context.bot.id:
        await update.message.reply_text("I can't kick myself!")
        return

    try:
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=target_id)
        await context.bot.unban_chat_member(chat_id=chat_id, user_id=target_id)
        await update.message.reply_text(f"Kicked {target_name}.")
    except Exception as e:
        logger.error(f"Kick failed: {type(e).__name__}: {e}")
        error_msg = str(e)
        if "not enough rights" in error_msg.lower():
            await update.message.reply_text("Failed to kick. Anna needs 'Ban users' permission.")
        elif "admin" in error_msg.lower():
            await update.message.reply_text("Cannot kick an admin or the group owner.")
        else:
            await update.message.reply_text(f"Failed to kick user: {error_msg[:100]}")


# =========================
# AUTO-TRANSLATE TOGGLE
# =========================
async def auto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id

    if is_private_chat(update):
        await update.message.reply_text("This command only works in groups.")
        return

    if not is_admin(user_id):
        await update.message.reply_text("Only admins can use this command.")
        return

    db.groups[chat_id] = {"auto_translate": True}
    db.save_groups()

    await update.message.reply_text(
        "Auto-translate enabled!\n"
        "I'll automatically translate all non-English messages.\n"
        "Use /disableauto to turn off."
    )


async def disableauto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id

    if is_private_chat(update):
        await update.message.reply_text("This command only works in groups.")
        return

    if not is_admin(user_id):
        await update.message.reply_text("Only admins can use this command.")
        return

    db.groups[chat_id] = {"auto_translate": False}
    db.save_groups()

    await update.message.reply_text(
        "Auto-translate disabled.\n"
        "Use @annatranlatorbot for inline translation.\n"
        "Or reply to messages with /translate."
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    chat_id = str(update.effective_chat.id)

    if is_private_chat(update):
        await update.message.reply_text("This command only works in groups.")
        return

    auto_mode = db.groups.get(chat_id, {}).get("auto_translate", False)

    if auto_mode:
        await update.message.reply_text(
            "Current mode: AUTO-TRANSLATE\n"
            "I'll translate non-English messages automatically.\n"
            "Admins can use /disableauto to turn off."
        )
    else:
        await update.message.reply_text(
            "Current mode: MANUAL\n"
            "Reply to messages with /translate to translate them.\n"
            "Admins can use /auto to enable auto-translation.\n"
            "Or use @annatranlatorbot for inline translation."
        )


# =========================
# AUTO-TRANSLATE MESSAGE HANDLER
# =========================
async def auto_translate_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    # Track user on every message
    if update.message.from_user:
        track_user(update.message.from_user)

    chat_id = str(update.effective_chat.id)

    if update.effective_chat.type == "private":
        return

    if not db.groups.get(chat_id, {}).get("auto_translate", False):
        return

    text = update.message.text

    try:
        detected_lang = detect(text)
    except LangDetectException:
        return

    if detected_lang == "en":
        return

    try:
        translated = translator.translate(text)
        if translated.lower().strip() == text.lower().strip():
            return
        cute_suffixes = [" ✨", " 💫", " 🌸", " ~", " hehe~", " 💙"]
        suffix = random.choice(cute_suffixes)
        await update.message.reply_text(f"🌸 {translated}{suffix}")
    except Exception as e:
        logger.error(f"Translation failed: {e}")


# =========================
# OWNER MANAGEMENT
# =========================
async def setowner_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    user_id = update.effective_user.id

    if not is_private_chat(update):
        await update.message.reply_text("This command only works in private chat with me.")
        return

    current_owner = get_owner_id()
    if current_owner is not None:
        if int(user_id) == int(current_owner):
            await update.message.reply_text("You are already the owner!")
        else:
            await update.message.reply_text("Owner is already set. Contact the current owner.")
        return

    db.admins["owner_id"] = user_id
    db.save_admins()
    await update.message.reply_text("You are now the bot owner!\nUse /addadmin to add other admins.")


async def addadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    user_id = update.effective_user.id

    if not is_owner(user_id):
        await update.message.reply_text("Only the bot owner can use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message to add them as admin.")
        return

    target = update.message.reply_to_message.from_user
    target_id = target.id
    target_name = target.username or target.first_name

    if target_id == get_owner_id():
        await update.message.reply_text("This user is already the owner.")
        return

    current_admins = [int(a) for a in db.admins.get("admins", [])]
    if int(target_id) in current_admins:
        await update.message.reply_text(f"{target_name} is already an admin.")
        return

    db.admins["admins"].append(target_id)
    db.save_admins()
    await update.message.reply_text(f"Added {target_name} as admin.")


async def removeadmin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    user_id = update.effective_user.id

    if not is_owner(user_id):
        await update.message.reply_text("Only the bot owner can use this command.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a user's message to remove them as admin.")
        return

    target = update.message.reply_to_message.from_user
    target_id = target.id

    if target_id == get_owner_id():
        await update.message.reply_text("Cannot remove the owner.")
        return

    current_admins = [int(a) for a in db.admins.get("admins", [])]
    if int(target_id) not in current_admins:
        await update.message.reply_text("This user is not an admin.")
        return

    db.admins["admins"] = [a for a in current_admins if int(a) != int(target_id)]
    db.save_admins()
    await update.message.reply_text(f"Removed admin (ID: {target_id}).")


async def listadmins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track_user(update.effective_user)
    user_id = update.effective_user.id

    if not is_owner(user_id):
        await update.message.reply_text("Only the bot owner can use this command.")
        return

    owner_id = get_owner_id()
    admins = db.admins.get("admins", [])

    text = f"Owner: {owner_id}\n\n"
    if admins:
        text += "Admins:\n"
        for admin_id in admins:
            username = None
            for uname, uid in db.users.items():
                if int(uid) == int(admin_id):
                    username = uname
                    break
            if username:
                text += f"- @{username} (ID: {admin_id})\n"
            else:
                text += f"- ID: {admin_id}\n"
    else:
        text += "No admins configured."

    await update.message.reply_text(text)


# =========================
# GOON COMMAND (STICKERS)
# =========================
async def goon_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a random sticker from sticker packs."""
    track_user(update.effective_user)

    if not db.stickers:
        for pack_name in STICKER_PACKS:
            try:
                sticker_set = await context.bot.get_sticker_set(pack_name)
                for sticker in sticker_set.stickers:
                    db.stickers.append(sticker.file_id)
                logger.info(f"Loaded {len(sticker_set.stickers)} stickers from {pack_name}")
            except Exception as e:
                logger.error(f"Failed to load stickers from {pack_name}: {e}")

        if db.stickers:
            db.save_stickers()

    if not db.stickers:
        await update.message.reply_text(
            "Ehhh? No stickers right now~ 😢\n"
            "Anna needs access to the sticker packs!"
        )
        return

    random_sticker = random.choice(db.stickers)
    try:
        cute_captions = ["here u go hehe~ 💫", "catch~ ✨", "uwaa look at this~ 🌸", "for you, bestie~ 💙", "goon time~ ✨", "hehe~ 🎀"]
        caption = random.choice(cute_captions)
        await update.message.reply_text(caption)
        await update.message.reply_sticker(random_sticker)
    except Exception as e:
        logger.error(f"Failed to send sticker: {e}")
        await update.message.reply_text("Aww couldn't send sticker rn~ try again? 😢")


# =========================
# INLINE TRANSLATE
# =========================
async def inline_translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query

    if not query or len(query.strip()) == 0:
        results = [
            InlineQueryResultArticle(
                id="help",
                title="Type any text to translate to English...",
                input_message_content=InputTextMessageContent(
                    "Type @annatranlatorbot followed by any text to translate it to English!"
                ),
                description="Example: Hola amigo"
            )
        ]
        await update.inline_query.answer(results)
        return

    try:
        translated = translator.translate(query)

        if translated.lower().strip() == query.lower().strip():
            results = [
                InlineQueryResultArticle(
                    id="same",
                    title="Already in English!",
                    input_message_content=InputTextMessageContent(query),
                    description="No translation needed"
                )
            ]
        else:
            desc = translated[:50] + ("..." if len(translated) > 50 else "")
            results = [
                InlineQueryResultArticle(
                    id="translate",
                    title="English Translation",
                    input_message_content=InputTextMessageContent(translated),
                    description=desc
                )
            ]

        await update.inline_query.answer(results)

    except Exception as e:
        logger.error(f"Inline translation failed: {e}")
        results = [
            InlineQueryResultArticle(
                id="error",
                title="Translation failed",
                input_message_content=InputTextMessageContent("Sorry, translation failed."),
                description="Please try again"
            )
        ]
        await update.inline_query.answer(results)


# =========================
# ANNA PERSONALITY CHAT
# =========================
# Track active conversations: {(chat_id, user_id): last_message_timestamp}
active_conversations = {}
CONVERSATION_TIMEOUT = 120  # 2 minutes of silence = conversation ends


def is_conversation_active(chat_id, user_id):
    """Check if Anna is in an active conversation with this user in this chat."""
    key = (str(chat_id), str(user_id))
    last_time = active_conversations.get(key)
    if last_time and (time.time() - last_time) < CONVERSATION_TIMEOUT:
        return True
    # Clean up expired entry
    if key in active_conversations:
        del active_conversations[key]
    return False


def mark_conversation_active(chat_id, user_id):
    """Mark that Anna is actively chatting with this user."""
    key = (str(chat_id), str(user_id))
    active_conversations[key] = time.time()


async def anna_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages where Anna should respond with personality."""
    if not update.message or not update.message.text:
        return
    if not gemini_model:
        return

    # Track user
    if update.message.from_user:
        track_user(update.message.from_user)

    text = update.message.text
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Cache bot username
    if not context.bot_data.get("username"):
        me = await context.bot.get_me()
        context.bot_data["username"] = me.username.lower()
    bot_username = context.bot_data["username"]

    # Determine if Anna should respond
    text_lower = text.lower()
    is_mentioned = "anna" in text_lower or f"@{bot_username}" in text_lower
    is_reply_to_bot = (
        update.message.reply_to_message
        and update.message.reply_to_message.from_user
        and update.message.reply_to_message.from_user.id == context.bot.id
    )
    is_private = update.effective_chat.type == "private"
    is_active_convo = is_conversation_active(chat_id, user_id)

    # In groups: respond if mentioned, replied to, or in active conversation
    # In DMs: always respond
    should_respond = is_mentioned or is_reply_to_bot or is_private or is_active_convo

    if not should_respond:
        return

    # Skip if it's a command
    if text.startswith("/"):
        return

    logger.info(f"Anna chat triggered: private={is_private}, mentioned={is_mentioned}, reply={is_reply_to_bot}, active={is_active_convo}")

    # Mark conversation as active
    mark_conversation_active(chat_id, user_id)

    # Get user's name for context
    user_name = update.effective_user.first_name or "friend"

    # Build context about the chat type
    chat_context = "DM (be warmer and more personal)" if is_private else "group chat (keep it social and fun)"

    try:
        prompt = f"[Context: {chat_context}] [User '{user_name}' says]: {text}"
        response = await asyncio.to_thread(
            lambda: gemini_model.generate_content(prompt).text
        )
        if response:
            response = response.strip()[:500]
            await update.message.reply_text(response)
        else:
            logger.warning("Gemini returned empty response")
            await update.message.reply_text("Hmm~ Anna's brain froze for a sec 😅 try again?")
    except Exception as e:
        logger.error(f"Gemini chat failed: {type(e).__name__}: {e}")
        if "429" in str(e) or "ResourceExhausted" in str(e):
            await update.message.reply_text("Anna's brain is a little tired rn~ too many people talking to me 😅 try again in a min?")
        else:
            await update.message.reply_text("Aww, Anna's brain glitched~ try again in a sec? 💫")


# =========================
# MAIN
# =========================
def run_bot():
    backoff = 10
    max_backoff = 300  # 5 minutes max

    while True:
        try:
            application = Application.builder().token(BOT_TOKEN).build()

            # Register commands menu
            application.post_init = setup_commands

            # Command handlers
            application.add_handler(CommandHandler("start", start_command))
            application.add_handler(CommandHandler("help", help_command))
            application.add_handler(CommandHandler("translate", translate_command))
            application.add_handler(CommandHandler("mute", mute_command))
            application.add_handler(CommandHandler("unmute", unmute_command))
            application.add_handler(CommandHandler("kick", kick_command))
            application.add_handler(CommandHandler("auto", auto_command))
            application.add_handler(CommandHandler("disableauto", disableauto_command))
            application.add_handler(CommandHandler("status", status_command))
            application.add_handler(CommandHandler("setowner", setowner_command))
            application.add_handler(CommandHandler("addadmin", addadmin_command))
            application.add_handler(CommandHandler("removeadmin", removeadmin_command))
            application.add_handler(CommandHandler("listadmins", listadmins_command))
            application.add_handler(CommandHandler("goon", goon_command))

            # Inline query handler
            application.add_handler(InlineQueryHandler(inline_translate))

            # Anna personality chat handler (triggers on mention, reply, or random)
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, anna_chat), group=0)

            # Auto-translate handler (also handles user tracking)
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_translate_message), group=1)

            logger.info("ana is running...")
            application.run_polling()

            # If run_polling exits cleanly, reset backoff
            backoff = 10

        except Exception as e:
            logger.error(f"Bot crashed: {e}")

        logger.info(f"Restarting in {backoff} seconds...")
        time.sleep(backoff)
        backoff = min(backoff * 2, max_backoff)


def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"Health endpoint started on port {PORT}")

    run_bot()


if __name__ == "__main__":
    main()
