# 🤖 Telegram Auto-Poster Bot

An advanced Telegram bot for managing channels and scheduling posts.
Supports text, photos, videos, documents, and stickers.

## ✨ Features
- **Multi-Channel Support**: Manage multiple channels with custom names.
- **Scheduling**: Schedule posts for a specific date and time.
- **Immediate Posting**: Post messages instantly to any configured channel.
- **Owner Control**: Secured commands (only the owner can control the bot).
- **Format Preservation**: Keeps all formatting, captions, and media types intact.

## 🚀 Setup Guide

### 1. Create Bot & Get Token
1. Open [@BotFather](https://t.me/BotFather) on Telegram.
2. Send `/newbot`.
3. Give it a name and a username (e.g., `MyAutoPosterBot`).
4. Copy the **API Token** sent by BotFather.

### 2. Local Installation
1. Install Python (if not installed).
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Create a `.env` file in this folder and add your token:
   ```
   BOT_TOKEN=your_api_token_here
   ```
   *(Or just set it as an environment variable)*.

4. Run the bot:
   ```sh
   python bot.py
   ```

### 3. Initial Configuration
1. Open your bot in Telegram and send `/start`.
2. It will tell you that the owner is not set and show your ID.
3. Run `/setowner <your_id>` to claim ownership.
   - Example: `/setowner 123456789`
4. Now you are the admin!

### 4. Adding Channels
1. Add your bot to the target channel as an **Admin** (needs "Post Messages" permission).
2. Get the Channel ID:
   - Forward a message from the channel to [@userinfobot](https://t.me/userinfobot) or use a modified client.
   - Or, just try adding the channel username (e.g., `@mychannel`) if it's public.
   - IDs usually look like `-1001234567890`.
3. Add it to the bot:
   ```
   /addchannel news -1001234567890
   ```

## 📅 Usage

### Immediate Posting
1. Send `/post <channel_name>` (e.g., `/post news`).
2. The bot will say it's ready.
3. Send the message (text, image, video, etc.) you want to post.
4. Bot copies it to the channel immediately.

### Scheduled Posting
1. Send `/schedule <channel_name> <YYYY-MM-DD HH:MM>`.
   - Example: `/schedule news 2024-10-25 14:30`
2. The bot will confirm the time.
3. Send the message you want to schedule.
4. Bot will post it automatically at that time.

## ☁️ Deployment

### Deploy on Render (Free)
1. Fork/Upload this code to GitHub.
2. Create a new **Web Service** on [Render.com](https://render.com).
   - *Note: Render Free Web Services spin down, so Background Worker might be better for 24/7 uptime, or just use a helper service to keep it awake.*
   - **Better Option**: Create a **Background Worker** on Render (might require paid plan) OR use **Railway** / **Fly.io** for better bot hosting.
   - *For this code setup (`Procfile`), it's configured as a `worker` process.*
3. Connect your GitHub repo.
4. In **Environment Variables**, add:
   - Key: `BOT_TOKEN`
   - Value: `your_telegram_bot_token`
5. Deploy!

### Deploy on Railway
1. Create a new project on [Railway.app](https://railway.app).
2. Deploy from GitHub repo.
3. Add `BOT_TOKEN` in variables.
4. Railway detects the `Procfile` or `requirements.txt` and runs it.

## 🛠 Commands List
- `/setowner <id>`: Set bot owner
- `/addchannel <name> <id>`: Save a channel
- `/removechannel <name>`: Remove a channel
- `/listchannels`: Show saved channels
- `/post <name>`: Post next message immediately
- `/schedule <name> <time>`: Schedule next message
- `/status`: Check config
- `/cancel`: Cancel current operation
