import discord
import requests
import os
import sys
import threading
import time

# --- Discord settings ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# --- Telegram settings ---
TELEGRAM_TOKEN = "#your bot token"
TELEGRAM_CHAT_ID = #your chat id
TELEGRAM_THREAD_ID = #your thread id

LAST_UPDATE_FILE = "last_update.txt"

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "message_thread_id": TELEGRAM_THREAD_ID
    }
    r = requests.post(url, data=payload)
    print("Telegram response:", r.json())

def reload_bot():
    send_to_telegram("♻️ Bot reloading")
    # We save the current update_id so that we don't catch the same message after restarting
    with open(LAST_UPDATE_FILE, "w") as f:
        f.write(str(last_update_id))
    os.execv(sys.executable, ['python'] + sys.argv)

def telegram_listener():
    global last_update_id
    last_update_id = None

    # uploading the last processed update_id if any
    if os.path.exists(LAST_UPDATE_FILE):
        with open(LAST_UPDATE_FILE, "r") as f:
            try:
                last_update_id = int(f.read().strip())
            except ValueError:
                last_update_id = None

    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
            if last_update_id:
                url += f"?offset={last_update_id+1}"
            r = requests.get(url)
            data = r.json()

            if "result" in data:
                for update in data["result"]:
                    last_update_id = update["update_id"]
                    if "message" in update:
                        msg = update["message"]
                        text = msg.get("text", "")
                        chat_id = msg["chat"]["id"]
                        thread_id = msg.get("message_thread_id")

                        if chat_id == TELEGRAM_CHAT_ID and thread_id == TELEGRAM_THREAD_ID:
                            if text.strip() == "/reload":
                                reload_bot()
        except Exception as e:
            print("Error Telegram listener:", e)

        time.sleep(2)

@client.event
async def on_ready():
    print(f'We: {client.user}!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    thread_name = None
    if hasattr(message, "channel"):
        if hasattr(message.channel, "name"):
            thread_name = message.channel.name
        elif hasattr(message.channel, "parent") and message.channel.parent:
            thread_name = message.channel.parent.name

    if not thread_name:
        thread_name = "general" 

    author = message.author.display_name if hasattr(message.author, "display_name") else str(message.author)

    text = f"#{thread_name} new announcement:\n{author}: {message.content}"
    print(text)
    send_to_telegram(text)


# Launching Telegram listener in a separate thread
threading.Thread(target=telegram_listener, daemon=True).start()

# start Discord-bot
DISCORD_TOKEN = "your-token"
client.run(DISCORD_TOKEN)
