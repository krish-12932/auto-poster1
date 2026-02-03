
import os
import logging
import json
import datetime
import asyncio
import pytz
from datetime import datetime
from tzlocal import get_localzone
from typing import Dict, Optional, Any

from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram.error import BadRequest

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

CONFIG_FILE = "config.json"

# --- Persistence ---
def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_FILE):
        return {"owner_id": None, "channels": {}}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {"owner_id": None, "channels": {}}

def save_config(config: Dict[str, Any]):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving config: {e}")

# Global Config (Cached in memory)
CONFIG = load_config()

# --- Decorators ---
def owner_only(func):
    """Decorator to restrict access to the owner only."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user:
            return
        user_id = update.effective_user.id
        if CONFIG["owner_id"] is None:
            await update.message.reply_text("Owner not set! Use /setowner to claim ownership.")
            return
        if user_id != CONFIG["owner_id"]:
            await update.message.reply_text("⛔ You are not authorized to use this bot.")
            return
        return await func(update, context)
    return wrapper

# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = (
        "🤖 *Telegram Auto-Poster Bot*\n\n"
        "I can help you post messages to your channels immediately or schedule them.\n\n"
        "if you have any problem then contact @Priyashrama59\n\n"
        "To get started, if owner is not set, use /setowner <your_id>.\n"
        "Then add channels using /addchannel.\n"
        "See /start for all commands."
    )
    if CONFIG["owner_id"] is None:
         msg += f"\n\n⚠️ Owner NOT set. Your ID: `{user_id}`"
    
    help_text = (
        "\n\n*Commands:*\n"
        "/setowner <owner\\_id> - Set bot owner (One time)\n"
        "/addchannel <name> <channel\\_id> - Add a channel\n"
        "/removechannel <name> - Remove a channel\n"
        "/listchannels - List saved channels\n"
        "/post <channel\\_name> - Post next message immediately\n"
        "/schedule <channel\\_name> <DATE> <TIME> [AM/PM] - Schedule post\n"
        "/status - Check bot configuration\n"
        "/cancel - Cancel current operation"
    )
    
    await update.message.reply_text(msg + help_text, parse_mode="Markdown")

async def set_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Allow setting owner if currently None or if the sender IS the owner (updating ID logic if needed, usually same)
    if CONFIG["owner_id"] is not None and CONFIG["owner_id"] != user_id:
        await update.message.reply_text("⛔ Owner is already set. You cannot change it.")
        return

    if not context.args:
        # If no args, try to set the current user as owner
        new_owner_id = user_id
    else:
        try:
            new_owner_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid ID format. Use numeric ID.")
            return

    CONFIG["owner_id"] = new_owner_id
    save_config(CONFIG)
    await update.message.reply_text(f"✅ Owner set to ID: `{new_owner_id}`", parse_mode="Markdown")

@owner_only
async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("usage: /addchannel <name> <channel_id>")
        return
    
    name = context.args[0]
    channel_id = context.args[1]
    
    # Basic validation
    if not (channel_id.startswith("-100") or channel_id.startswith("@")):
         await update.message.reply_text("⚠️ Channel ID usually starts with -100 or is a @username. Proceeding anyway.")

    CONFIG["channels"][name] = channel_id
    save_config(CONFIG)
    await update.message.reply_text(f"✅ Channel `{name}` added with ID: `{channel_id}`", parse_mode="Markdown")

@owner_only
async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("usage: /removechannel <name>")
        return
    
    name = context.args[0]
    if name in CONFIG["channels"]:
        del CONFIG["channels"][name]
        save_config(CONFIG)
        await update.message.reply_text(f"🗑️ Channel `{name}` removed.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Channel `{name}` not found.", parse_mode="Markdown")

@owner_only
async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not CONFIG["channels"]:
        await update.message.reply_text("No channels configured.")
        return
    
    msg = "*Saved Channels:*\n"
    for name, cid in CONFIG["channels"].items():
        msg += f"- `{name}`: `{cid}`\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

@owner_only
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner = CONFIG.get("owner_id", "Not Set")
    count = len(CONFIG.get("channels", {}))
    await update.message.reply_text(f"ℹ️ *Status*\nOwner ID: `{owner}`\nChannels: {count}", parse_mode="Markdown")

# --- Posting Logic ---

@owner_only
async def start_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("usage: /post <channel_name>")
        return
    
    channel_name = context.args[0]
    if channel_name not in CONFIG["channels"]:
        await update.message.reply_text(f"❌ Channel '{channel_name}' not found.")
        return

    context.user_data["post_mode"] = "immediate"
    context.user_data["target_channel"] = CONFIG["channels"][channel_name]
    context.user_data["target_channel_name"] = channel_name
    
    await update.message.reply_text(
        f"📩 *Ready to Post*\n"
        f"Destination: `{channel_name}`\n"
        f"Send the message (text, photo, video, etc) now to post it immediately.",
        parse_mode="Markdown"
    )

@owner_only
async def start_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # usage: /schedule channel YYYY-MM-DD HH:MM [AM/PM]
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("usage: /schedule <channel_name> <YYYY-MM-DD> <HH:MM> [AM/PM]")
        return
    
    channel_name = args[0]
    date_str = args[1]
    time_str = args[2]
    am_pm = args[3].upper() if len(args) > 3 else None
    
    if channel_name not in CONFIG["channels"]:
        await update.message.reply_text(f"❌ Channel `{channel_name}` not found.", parse_mode="Markdown")
        return

    try:
        # Determine local timezone
        try:
             local_tz = get_localzone()
        except:
             local_tz = pytz.timezone('Asia/Kolkata')

        if am_pm:
            # 12-hour format: YYYY-MM-DD HH:MM AM/PM
            dt_str = f"{date_str} {time_str} {am_pm}"
            naive_dt = datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
        else:
            # 24-hour format: YYYY-MM-DD HH:MM
            dt_str = f"{date_str} {time_str}"
            naive_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        
        # Localize the naive datetime to make it aware
        schedule_dt = local_tz.localize(naive_dt)
        
        now = datetime.now(local_tz) # Make now aware too
        
        if schedule_dt <= now:
            await update.message.reply_text("❌ Scheduled time must be in the future.")
            return

        context.user_data["post_mode"] = "schedule"
        context.user_data["target_channel"] = CONFIG["channels"][channel_name]
        context.user_data["target_channel_name"] = channel_name
        context.user_data["schedule_time"] = schedule_dt
        
        display_time = schedule_dt.strftime("%Y-%m-%d %I:%M %p")
        
        await update.message.reply_text(
            f"🕒 *Ready to Schedule*\n"
            f"Destination: `{channel_name}`\n"
            f"Time: `{display_time}`\n"
            f"Send the message now to schedule it.",
            parse_mode="Markdown"
        )
        
    except ValueError:
        await update.message.reply_text("❌ Invalid format.\nUse `YYYY-MM-DD HH:MM` (24hr)\nOR `YYYY-MM-DD HH:MM AM/PM` (12hr)", parse_mode="Markdown")

# Job Callback
async def post_job(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    channel_id = job_data["channel_id"]
    message_id = job_data["message_id"]
    chat_id = job_data["chat_id"]
    
    try:
        await context.bot.copy_message(chat_id=channel_id, from_chat_id=chat_id, message_id=message_id)
        # Notify owner (optional, requires storing owner chat id or just best effort)
        # await context.bot.send_message(chat_id=chat_id, text=f"✅ Scheduled post sent to {channel_id}")
    except Exception as e:
        logger.error(f"Failed to run scheduled post: {e}")
        # await context.bot.send_message(chat_id=chat_id, text=f"❌ Failed to send scheduled post: {e}")

async def handle_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Verify owner
    if not update.effective_user or (CONFIG["owner_id"] is not None and update.effective_user.id != CONFIG["owner_id"]):
        return # Ignore non-owners or when owner not set
        
    post_mode = context.user_data.get("post_mode")
    if not post_mode:
        return # Not expecting a post
    
    target_channel = context.user_data.get("target_channel")
    target_name = context.user_data.get("target_channel_name")
    
    if post_mode == "immediate":
        try:
            await update.message.copy(chat_id=target_channel)
            await update.message.reply_text(f"✅ Posted to `{target_name}`!", parse_mode="Markdown")
        except BadRequest as e:
            await update.message.reply_text(f"❌ Error posting: {e}\n(Make sure bot is admin in the channel)")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
            
    elif post_mode == "schedule":
        schedule_time = context.user_data.get("schedule_time")
        if schedule_time:
            # Add to job queue
            # Note: message_id and chat_id are needed to copy
            context.job_queue.run_once(
                post_job,
                when=schedule_time,
                data={
                    "channel_id": target_channel,
                    "message_id": update.message.message_id,
                    "chat_id": update.message.chat_id
                }
            )
            await update.message.reply_text(f"✅ Scheduled for `{schedule_time}`!", parse_mode="Markdown")
            
    # Reset state
    context.user_data["post_mode"] = None
    context.user_data["target_channel"] = None
    context.user_data["target_channel_name"] = None
    context.user_data["schedule_time"] = None

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("post_mode"):
        context.user_data.clear()
        await update.message.reply_text("🚫 Operation cancelled.")
    else:
        await update.message.reply_text("Nothing to cancel.")

def main():
    # Load Token from Env
    # Use python-dotenv for local dev
    from dotenv import load_dotenv
    load_dotenv()
    
    TOKEN = os.getenv("BOT_TOKEN")
    
    if not TOKEN:
        print("Error: BOT_TOKEN env variable not set.")
        return

    async def post_init(application):
        await application.bot.set_my_commands([
            ("start", "Start the bot"),
            ("setowner", "Set bot owner"),
            ("addchannel", "Add a channel"),
            ("removechannel", "Remove a channel"),
            ("listchannels", "List saved channels"),
            ("post", "Post immediately"),
            ("schedule", "Schedule a post"),
            ("status", "Check status"),
            ("cancel", "Cancel operation"),
        ])

    # JobQueue defaults to UTC if not specified. Using local timezone.
    # Note: python-telegram-bot v20+ manages job_queue via builder
    # We will use the system's local timezone
    try:
         # Try to get system local timezone
         local_tz = get_localzone()
    except:
         # Fallback to Asia/Kolkata since user is in India (based on log) or UTC
         local_tz = pytz.timezone('Asia/Kolkata')
         
    # defaults = ContextTypes.DEFAULT_TYPE(job_queue=None) # REMOVED: Causing crash and not needed.
    
    # Correct way for PTB v20: Just pass valid timezone to job_queue init via builder if possible,
    # OR better: run_once() uses the datetime's timezone.
    # If the datetime object has timezone info, PTB respects it.
    # Our code uses `datetime.datetime.strptime` which returns NAIVE datetime.
    # We need to make it AWARE.
    
    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setowner", set_owner))
    application.add_handler(CommandHandler("status", status))
    
    application.add_handler(CommandHandler("addchannel", add_channel))
    application.add_handler(CommandHandler("removechannel", remove_channel))
    application.add_handler(CommandHandler("listchannels", list_channels))
    
    application.add_handler(CommandHandler("post", start_post))
    application.add_handler(CommandHandler("schedule", start_schedule))
    application.add_handler(CommandHandler("cancel", cancel))
    
    # Message Handler (Must be last to avoid catching commands)
    # Handle everything: text, photo, video, audio, document, voice, sticker, animation
    application.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_content))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
