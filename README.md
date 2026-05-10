# dustin - Telegram Auto-Translation Bot

A Telegram bot that automatically detects non-English messages in group chats and replies with an English translation using Google Translate (Free). Built with Telethon to support MTProto proxies.

## Features

- Automatically detects the language of every text message
- Skips English messages to save resources
- Replies directly to the original message for clear context
- Uses Google Translate (100% free, no API key needed)
- Supports MTProto proxies (for regions where Telegram is blocked)
- Works silently in the background

## Setup

### 1. Create the Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Start a chat and send `/newbot`
3. Name your bot **dustin**
4. Choose a unique username (e.g., `@dustin_translate_bot`) — it must end in `bot`
5. Copy the **HTTP API Token** you receive
6. **IMPORTANT for group chats**: Send `/setprivacy` to @BotFather, select your bot, and choose **Disable**. This allows dustin to read all messages in groups.

### 2. Get API ID and API Hash (for Telethon)

1. Go to [https://my.telegram.org](https://my.telegram.org)
2. Log in with your phone number (Telegram will send a code)
3. Click **API development tools**
4. Fill in any app name (e.g., `dustin_bot`) and a short name
5. Click **Create application**
6. Copy the **api_id** (a number) and **api_hash** (a long string)

### 3. Configure Environment Variables

1. Rename `.env.example` to `.env`:
```bash
ren .env.example .env
```

2. Open `.env` and paste your credentials:
   ```
   BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   API_ID=12345678
   API_HASH=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
   ```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Bot

```bash
python bot.py
```

You will see: `dustin is running...`

## Adding to Group Chats

1. Add `@dustin_translate_bot` (or your chosen username) to your group
2. Make sure the bot is **not** restricted and has permission to send messages
3. dustin will now automatically translate any non-English message by replying to it

## Notes

- **100% Free**: Uses `deep-translator` with Google Translate backend. No API keys, no credit cards, no usage limits.
- **Language Detection**: Uses `langdetect` to skip English messages.
- **Error Handling**: If a translation fails, dustin silently ignores it to avoid spamming the chat.
- **MTProto Proxy**: The bot is pre-configured with the proxy you provided. If you want to change it, edit the `PROXY` tuple in `bot.py`.

## Project Structure

```
.
├── bot.py              # Main bot logic (Telethon + MTProto proxy)
├── config.py           # Config loader and validation
├── requirements.txt    # Python dependencies
├── .env                # Your credentials (ignored by git)
├── .env.example        # Template for .env
└── README.md           # This file
```
