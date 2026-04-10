import time
import requests
import threading
from flask import Flask
import os

app = Flask(__name__)

# 🔥 TERA TOKEN (PEHLE REGENERATE KAR)
BOT_TOKEN = "8772193060:AAFOrADPod-gr1HT5IEGJq41HrNTdErlD48"
ADMIN_ID = "8602543306"

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

CHANNELS = [
    {"name": "CrushxAmok", "username": "@CrushxAmok"},
    {"name": "ProxyeFans", "username": "@ProxyeFans"}
]

adding_active = False
total_added = 0

def send_message(chat_id, text):
    url = f"{API_URL}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
    except:
        pass

def get_chat_id(username):
    url = f"{API_URL}/getChat"
    try:
        r = requests.get(url, params={"chat_id": username}, timeout=10)
        if r.status_code == 200:
            return r.json()["result"]["id"]
    except:
        pass
    return None

def accept_request(chat_id, user_id, username, channel_name):
    global total_added
    url = f"{API_URL}/approveChatJoinRequest"
    try:
        response = requests.post(url, json={"chat_id": chat_id, "user_id": user_id}, timeout=10)
        if response.status_code == 200:
            total_added += 1
            msg = f"✅ @{username} accepted in {channel_name}\n📊 Total: {total_added}"
            send_message(ADMIN_ID, msg)
            return True
    except:
        pass
    return False

def decline_request(chat_id, user_id, channel_name):
    url = f"{API_URL}/declineChatJoinRequest"
    try:
        requests.post(url, json={"chat_id": chat_id, "user_id": user_id}, timeout=10)
        send_message(ADMIN_ID, f"🗑️ Deleted account rejected from {channel_name}")
    except:
        pass

def process_pending_requests():
    """Already pending join requests ko process karega"""
    global total_added
    
    for channel in CHANNELS:
        chat_id = get_chat_id(channel["username"])
        if not chat_id:
            send_message(ADMIN_ID, f"❌ Bot is not admin in {channel['name']} or channel not found")
            continue
        
        # Pending requests fetch karo
        url = f"{API_URL}/getChatJoinRequests"
        try:
            r = requests.get(url, params={"chat_id": chat_id, "limit": 200}, timeout=10)
            
            if r.status_code != 200:
                send_message(ADMIN_ID, f"❌ Failed to get requests from {channel['name']}")
                continue
            
            requests_data = r.json().get("result", [])
            pending_count = len(requests_data)
            
            if pending_count > 0:
                send_message(ADMIN_ID, f"📢 Found {pending_count} pending requests in {channel['name']}\n🔄 Processing...")
                
                for req in requests_data:
                    user = req.get("user", {})
                    user_id = user.get("id")
                    username = user.get("username", "unknown")
                    is_deleted = user.get("is_deleted", False)
                    
                    if is_deleted:
                        decline_request(chat_id, user_id, channel['name'])
                    else:
                        accept_request(chat_id, user_id, username, channel['name'])
                    
                    time.sleep(0.5)  # Rate limit avoid karne ke liye
                
                send_message(ADMIN_ID, f"✅ Completed {channel['name']}! Total added: {total_added}")
            else:
                send_message(ADMIN_ID, f"📭 No pending requests in {channel['name']}")
                
        except Exception as e:
            send_message(ADMIN_ID, f"❌ Error in {channel['name']}: {str(e)}")

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

def handle_join_request(update):
    global adding_active, total_added
    if not adding_active:
        return
    
    join_req = update.get("chat_join_request", {})
    chat = join_req.get("chat", {})
    user = join_req.get("user", {})
    
    chat_username = chat.get("username", "")
    chat_id = chat.get("id")
    user_id = user.get("id")
    username = user.get("username", "unknown")
    is_deleted = user.get("is_deleted", False)
    
    # Check if it's our channel
    channel_names = ["CrushxAmok", "ProxyeFans"]
    if chat_username not in channel_names:
        return
    
    if is_deleted:
        decline_request(chat_id, user_id, chat_username)
    else:
        accept_request(chat_id, user_id, username, chat_username)

def handle_message(message):
    global adding_active, total_added
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")
    user_id = message.get("from", {}).get("id")
    
    # Sirf admin
    if str(user_id) != ADMIN_ID:
        send_message(chat_id, "❌ Unauthorized")
        return
    
    if text == "/start":
        send_message(chat_id, "🤖 Bot Active!\n\nCommands:\n/add_members - Start adding (including pending)\n/stop - Stop adding\n/status - Check status")
    
    elif text == "/add_members":
        adding_active = True
        total_added = 0
        send_message(chat_id, "✅ Member adding STARTED!\n\n📢 Processing ALL pending join requests...")
        # Turant pending requests process karo
        process_pending_requests()
    
    elif text == "/stop":
        adding_active = False
        send_message(chat_id, f"⛔ Stopped! Total added: {total_added}")
    
    elif text == "/status":
        status = "ACTIVE ✅" if adding_active else "INACTIVE ⛔"
        send_message(chat_id, f"Status: {status}\nTotal added: {total_added}")

def main_loop():
    offset = 0
    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                
                if "chat_join_request" in update:
                    handle_join_request(update)
                
                if "message" in update:
                    handle_message(update["message"])
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)

@app.route('/')
def home():
    return "✅ Bot is running! Send /add_members to process all pending requests"

if __name__ == "__main__":
    thread = threading.Thread(target=main_loop, daemon=True)
    thread.start()
    print("🚀 Bot Started!")
    print("Send /add_members to process ALL pending join requests")
    app.run(host="0.0.0.0", port=10000)
