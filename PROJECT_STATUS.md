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
| Translation (inline) | ✅ Working | @annatranlatorbot in any chat |
| Translation (reply) | ✅ Working | /translate command |
| Auto-translate | ✅ Working | /auto and /disableauto |
| Moderation (mute/unmute/kick) | ✅ Working | Admin only |
| Owner/Admin system | ✅ Working | /setowner, /addadmin, etc. |
| Sticker command (/goon) | ✅ Working | Random sticker with cute caption |
| Health check endpoint | ✅ Working | Flask + Waitress |
| Supabase database | ✅ Working | With JSON fallback |
| AI Personality (Groq) | ✅ Working | Groq llama-3.3-70b, conversation tracking |
| Image generation (/imagine) | 🔜 Planned | Pollinations.ai, owner-only |

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

- **Security:** Removed leaked bot token from RENDER_SETUP.md and git history
- **Security:** Force-pushed clean repo to GitHub (old history purged)
- **Security:** Removed .env.example from .gitignore
- **Bug Fix:** Supabase writes now use upsert instead of delete-all + re-insert
- **Bug Fix:** chat_id normalized to str on load from Supabase
- **Bug Fix:** langdetect seeded for deterministic results
- **Bug Fix:** Restart loop uses exponential backoff (10s to 5min)
- **Bug Fix:** User tracking now works (track_user called in all handlers)
- **Cleanup:** Deleted dead bot.py and config.py
- **Cleanup:** Removed unused OWNER_USERNAME variable
- **Feature:** Added Anna AI personality (Groq, llama-3.3-70b)
- **Feature:** Conversation tracking (2-min timeout, responds when mentioned/replied/DM)
- **Feature:** Cute waifu personality on translations and stickers
- **Feature:** Flirty anime waifu system prompt
- **Infra:** Switched from Flask dev server to Waitress (production)
- **Infra:** Switched from Gemini to Groq (free tier quota issues with Gemini)
- **Debug:** Currently investigating why anna_chat handler doesn't respond in DMs

---

## Known Issues

None currently.

---

## Planned Features

- [ ] /imagine command (Pollinations.ai, owner-only, SFW)
- [ ] Owner-only flirty mode (more playful responses for owner)
- [ ] Discord integration (same personality)
- [ ] Conversation memory (remember past chats per user)
