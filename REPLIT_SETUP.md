# dustin - Telegram Auto-Translation Bot

A Telegram bot that automatically detects non-English messages in group chats and replies with an English translation using Google Translate (Free).

## Features

- Automatically detects the language of every text message
- Skips English messages to save resources
- Replies directly to the original message for clear context
- Uses Google Translate (100% free, no API key needed)
- Works silently in the background

## Setup on Replit (Recommended for Pakistan)

Since Telegram is blocked in Pakistan, running the bot on **Replit** (free cloud server) is the best option. The bot will run 24/7 without needing any proxy.

### Step 1: Create Replit Account

1. Go to [https://replit.com](https://replit.com)
2. Sign up for a free account

### Step 2: Create a New Repl

1. Click **"Create"** button
2. Select **"Python"** as the template
3. Name it: `dustin-bot`
4. Click **"Create Repl"**

### Step 3: Upload Files

In the Replit editor:
1. Click the **3 dots (⋮)** next to "Files" panel
2. Select **"Upload file"**
3. Upload these 4 files from your computer:
   - `main.py`
   - `requirements.txt`
   - `.replit`
   - `README.md`

Or alternatively, copy-paste the code from each file into new files in Replit.

### Step 4: Set Environment Variables (Secrets)

1. Click the **🔒 Secrets** tab (lock icon) in the left sidebar
2. Add a new secret:
   - **Key**: `BOT_TOKEN`
   - **Value**: Your Telegram bot token (from @BotFather)
3. Click **"Add new secret"**

### Step 5: Run the Bot

1. Click the **"Run"** button at the top
2. You'll see `dustin is running on Replit...` in the console
3. The bot is now live!

### Step 6: Add Bot to Group Chat

1. Add your bot to any Telegram group
2. Make sure it has permission to read messages and send replies
3. Send a non-English message (e.g., Spanish, French, Urdu)
4. dustin will automatically reply with the English translation!

## Setup Locally (Only if Telegram is not blocked in your country)

### 1. Create the Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Start a chat and send `/newbot`
3. Name your bot **dustin**
4. Choose a unique username (e.g., `@dustin_translate_bot`) — it must end in `bot`
5. Copy the **HTTP API Token** you receive
6. **IMPORTANT for group chats**: Send `/setprivacy` to @BotFather, select your bot, and choose **Disable**. This allows dustin to read all messages in groups.

### 2. Configure Environment Variables

1. Create a `.env` file in the project folder:
```bash
cp .env.example .env
```

2. Open `.env` and paste your token:
   ```
   BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Bot

```bash
python main.py
```

## Notes

- **100% Free**: Uses `deep-translator` with Google Translate backend. No API keys, no credit cards, no usage limits.
- **Language Detection**: Uses `langdetect` to skip English messages.
- **Error Handling**: If a translation fails, dustin silently ignores it to avoid spamming the chat.
- **Replit**: The bot will run as long as the Replit tab is open. For 24/7 uptime, you may need Replit's "Always On" feature (paid) or use a service like UptimeRobot to ping it every 5 minutes.

## Project Structure

```
.
├── main.py              # Main bot logic
├── requirements.txt     # Python dependencies
├── .replit              # Replit configuration
├── .env                 # Your bot token (local only, ignored by git)
└── README.md            # This file
```
