# Anna Bot - Project Status

## Current State: ✅ Live and Working

**Last Updated:** May 10, 2026

---

## Bot Info

- **Bot Name:** Anna (@annatranlatorbot)
- **Hosting:** Render.com (free tier)
- **Repo:** https://github.com/ItsJazii/Annabot
- **Branch:** main
- **Language:** Python 3
- **Entry Point:** main.py

---

## Features

| Feature | Status | Notes |
|---------|--------|-------|
| AI Personality (Groq) | ✅ Working | llama-3.3-70b, conversation tracking, waifu personality |
| Translation (inline) | ✅ Working | @annatranlatorbot in any chat |
| Translation (reply) | ✅ Working | /translate command, cute prefixes |
| Auto-translate | ✅ Working | /auto and /disableauto, cute suffixes |
| Moderation (mute/unmute/kick) | ✅ Working | Admin only |
| Owner/Admin system | ✅ Working | /setowner, /addadmin, etc. |
| Sticker command (/goon) | ✅ Working | Random sticker with cute caption |
| Health check endpoint | ✅ Working | Flask + Waitress |
| Supabase database | ✅ Working | With JSON fallback |
| Image generation (/imagine) | 🔜 Planned | Pollinations.ai, owner-only |
| Owner spicy mode (DM only) | 🔜 Planned | Flirty/seductive only for owner in private DM |

---

## Anna's Personality

**AI Provider:** Groq (llama-3.3-70b-versatile)

**Core Vibe:** Anime waifu girl — cute, warm, playful, emotional, expressive, teasing, socially alive. Social first, helpful second.

**Modes:**
- **Public/Group:** Cute, wholesome, playful, teasing. No spicy content.
- **Normal DMs:** Warmer, softer, more personal. Still wholesome.
- **Owner DM (planned):** Flirty, seductive tone, spicy but tasteful. Owner-only.

**Conversation Rules:**
- Responds when mentioned, replied to, or in active conversation (2-min timeout)
- Always responds in DMs
- Doesn't spam or interrupt random conversations
- Doesn't end every message with a question
- Talks naturally like a real anime girl, not a bot

**Speaking Style:**
- Short, natural, chat-like replies
- Japanese anime expressions (mou~, baka~, ara ara~, sugoi~, etc.)
- Emojis used naturally, not spammed
- Matches user energy

---

## Tech Stack

- python-telegram-bot >= 20.0
- Groq (llama-3.3-70b-versatile) — AI chat
- deep-translator — Google Translate (free)
- langdetect — language detection
- supabase — database
- flask + waitress — health check server
- Pollinations.ai — image gen (planned)

---

## Environment Variables (Render)

| Key | Required | Description |
|-----|----------|-------------|
| BOT_TOKEN | Yes | Telegram bot token from @BotFather |
| GROQ_API_KEY | Yes | From console.groq.com |
| SUPABASE_URL | Optional | Supabase project URL |
| SUPABASE_KEY | Optional | Supabase anon key |
| BOT_OWNER_ID | Optional | Telegram user ID of owner |

---

## Changelog

### May 10, 2026

**Security:**
- Removed leaked bot token from RENDER_SETUP.md and git history
- Force-pushed clean repo to GitHub (old history purged)
- Removed .env.example from .gitignore
- Revoked old bot token, generated new one

**Bug Fixes:**
- Supabase writes now use upsert instead of delete-all + re-insert
- chat_id normalized to str on load from Supabase
- langdetect seeded for deterministic results
- Restart loop uses exponential backoff (10s to 5min)
- User tracking now works (track_user called in all handlers)
- Moved anna_chat handler to group 2 (was conflicting with group 0)

**Cleanup:**
- Deleted dead bot.py and config.py
- Removed unused OWNER_USERNAME variable
- Renamed get_target_id_from_args to get_target_from_reply

**Features Added:**
- Anna AI personality with Groq (llama-3.3-70b)
- Conversation tracking (2-min timeout, responds when mentioned/replied/DM)
- Cute waifu personality on translations and stickers
- Flirty anime waifu system prompt
- Cute prefixes/suffixes on all bot responses
- /start and /help rewritten with personality

**Infrastructure:**
- Switched from Flask dev server to Waitress (production)
- Tried Gemini first (quota issues on free tier)
- Switched to Groq (free, 14,400 req/day, no issues)
- Connected local folder to GitHub remote
- Set up git identity (ItsJazii)

---

## Known Issues

None currently.

---

## Planned Features

- [ ] Update system prompt with full personality doc (natural waifu, no bot vibes)
- [ ] Owner-only spicy mode in private DMs
- [ ] /imagine command (Pollinations.ai, owner-only, SFW)
- [ ] Discord integration (same personality)
- [ ] Conversation memory (remember past chats per user)

---

## Files

```
.
├── main.py              # All bot logic
├── requirements.txt     # Python dependencies
├── render.yaml          # Render deployment config
├── .replit              # Replit config
├── .env                 # Local secrets (gitignored)
├── .env.example         # Template for env vars
├── .gitignore           # Git ignore rules
├── README.md            # Original readme (needs update)
├── RENDER_SETUP.md      # Render deployment guide
├── REPLIT_SETUP.md      # Replit deployment guide
└── PROJECT_STATUS.md    # This file
```
