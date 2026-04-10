import time
import requests
import threading
from flask import Flask
import os

app = Flask(__name__)

# 🔥 TERA TOKEN (PEHLE REGENERATE KAR LENA)
BOT_TOKEN = "8772193060:AAFOrADPod-gr1HT5IEGJq41HrNTdErlD48"

# TERI TELEGRAM ID
ADMIN_ID = "8602543306"

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

CHANNELS = ["CrushxAmok", "ProxyeFans"]

adding_active = False
added_count = 0
pending_requests = {}

def send_message(chat_id, text):
    url = f"{API_URL}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    except:
        pass

def get_chat_id(username):
    url = f"{API_URL}/getChat"
    try:
        r = requests.get(url, params={"chat_id": f"@{username}"}, timeout=10)
        if r.status_code == 200:
            return r.json()["result"]["id"]
    except:
        pass
    return None

def accept_request(chat_id, user_id, username, channel_name):
    global added_count
    url = f"{API_URL}/approveChatJoinRequest"
    try:
        response = requests.post(url, json={"chat_id": chat_id, "user_id": user_id}, timeout=10)
        if response.status_code == 200:
            added_count += 1
            send_message(ADMIN_ID, f"✅ @{username} added to {channel_name}\n📊 Total: {added_count}")
            return True
    except:
        pass
    return False

def get_updates(offset=None):
    url = f"{API_URL}/getUpdates"
    params = {"timeout": 30, "allowed_updates": ["chat_join_request", "message"]}
    if offset:
        params["offset"] = offset
    try:
        r = requests.get(url, params=params, timeout=35)
        if r.status_code == 200:
            return r.json().get("result", [])
    except:
        pass
    return []

def process_join_request(update):
    global adding_active, added_count
    if not adding_active:
        return
    
    join_req = update.get("chat_join_request", {})
    chat = join_req.get("chat", {})
    user = join_req.get("user", {})
    
    chat_title = chat.get("title", "Unknown")
    chat_username = chat.get("username", "")
    user_id = user.get("id")
    username = user.get("username", "unknown")
    is_deleted = user.get("is_deleted", False)
    
    # Check if this is one of our channels
    if chat_username not in CHANNELS:
        return
    
    if is_deleted:
        url = f"{API_URL}/declineChatJoinRequest"
        requests.post(url, json={"chat_id": chat["id"], "user_id": user_id})
        send_message(ADMIN_ID, f"🗑️ Deleted account rejected from {chat_title}")
    else:
        accept_request(chat["id"], user_id, username, chat_title)

def handle_message(message):
    global adding_active, added_count
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")
    user_id = message.get("from", {}).get("id")
    
    # Sirf admin ko command sunega
    if str(user_id) != ADMIN_ID:
        send_message(chat_id, "❌ You are not authorized to use this bot")
        return
    
    if text == "/start":
        send_message(chat_id, "🤖 Bot is active!\nUse /add_members to start adding members")
    
    elif text == "/add_members":
        adding_active = True
        added_count = 0
        send_message(chat_id, "✅ Member adding STARTED!\n\nI will notify you whenever someone joins.\n\nMembers will be auto-added from both channels:\n• @CrushxAmok\n• @ProxyeFans")
    
    elif text == "/stop":
        adding_active = False
        send_message(chat_id, f"⛔ Member adding STOPPED!\n\nTotal members added: {added_count}")
    
    elif text == "/status":
        status = "ACTIVE ✅" if adding_active else "INACTIVE ⛔"
        send_message(chat_id, f"📊 Status: {status}\n✅ Total added: {added_count}\n📢 Channels: @CrushxAmok, @ProxyeFans")
    
    else:
        send_message(chat_id, "Available commands:\n/start - Start bot\n/add_members - Start auto adding\n/stop - Stop adding\n/status - Check status")

def main_loop():
    offset = 0
    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                
                if "chat_join_request" in update:
                    process_join_request(update)
                
                if "message" in update:
                    handle_message(update["message"])
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)

@app.route('/')
def home():
    return "✅ Bot is running! Send /add_members to start"

if __name__ == "__main__":
    # Start background thread
    thread = threading.Thread(target=main_loop, daemon=True)
    thread.start()
    print("🚀 Bot started!")
    print(f"📢 Channels: {CHANNELS}")
    print(f"👤 Admin ID: {ADMIN_ID}")
    app.run(host="0.0.0.0", port=10000)
