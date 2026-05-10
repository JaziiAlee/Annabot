# Deploy ana on Render.com

## Step 1: Create Render Account

1. Go to [https://render.com](https://render.com)
2. Click **"Get Started for Free"**
3. Sign up with your **email** or **GitHub** account

## Step 2: Create New Web Service

1. In your Render Dashboard, click **"New +"**
2. Select **"Web Service"**

## Step 3: Connect GitHub Repo

1. You should see your GitHub repos listed
2. Find and click on **"ItsJazii / Annabot"**
3. Click **"Connect"**

## Step 4: Configure Service

1. **Name**: `anna-bot`
2. **Runtime**: `Python 3`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `python main.py`
5. Click **"Create Web Service"**

## Step 5: Set Environment Variable

1. Click the **"Environment"** tab in your service dashboard
2. Add Environment Variable:
   - **Key**: `BOT_TOKEN`
   - **Value**: (paste your bot token from @BotFather)
3. Click **"Save Changes"**

## Step 6: Deploy

1. Render will automatically deploy from your GitHub repo
2. Wait for the build to complete (1-2 minutes)
3. You'll see a URL like: `https://anna-bot.onrender.com`
4. Check the logs - you should see: `ana is running...`

## Step 7: Keep It Alive (Important!)

Render free tier **sleeps after 15 minutes** of no web traffic. To keep your bot running 24/7:

### Set up UptimeRobot (Free)

1. Go to [https://uptimerobot.com](https://uptimerobot.com)
2. Sign up for free
3. Click **"Add New Monitor"**
4. Settings:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: `anna-bot`
   - **URL**: `https://anna-bot.onrender.com` (your Render URL)
   - **Monitoring Interval**: Every 5 minutes (free tier)
5. Click **"Create Monitor"**

UptimeRobot will ping your bot every 5 minutes, keeping it awake forever!

## Step 8: Add Bot to Telegram Group

1. Add your bot `@annatranlatorbot` to any group
2. Make sure it has permission to read messages and send replies
3. Send a non-English message (e.g., "Hola, ¿cómo estás?")
4. ana will automatically reply with: `🇺🇸 Hello, how are you?`

## Troubleshooting

**Bot not responding?**
- Check Render logs for errors
- Make sure `/setprivacy` is **Disabled** in @BotFather
- Make sure the bot is an admin in the group (or at least not restricted)

**Render says "Service slept"?**
- UptimeRobot isn't set up correctly
- Check that the URL in UptimeRobot matches your Render URL exactly

**Translation not working?**
- Check Render logs for "Translation failed" errors
- Google Translate might be rate-limiting - usually fixes itself

## Your Bot Details

- **Bot Name**: ana (Anna)
- **Bot Username**: @annatranlatorbot
- **Bot Token**: Set in Render Environment Variables (never commit tokens to code!)
- **Health Check URL**: `https://anna-bot.onrender.com` (after deployment)
- **GitHub Repo**: https://github.com/ItsJazii/Annabot
