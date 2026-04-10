import time
import requests
from flask import Flask

app = Flask(__name__)

# 🔥 APNA NAYA TOKEN YAHAN PASTE KAR (pehle @BotFather se naya le)
BOT_TOKEN = "8772193060:AAFOrADPod-gr1HT5IEGJq41HrNTdErlD48"  # <-- NAYA TOKEN DALO BHAI

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# TERE CHANNELS
CHANNELS = [
    {"name": "ProxyeFans", "username": "@ProxyeFans", "chat_id": None},
    {"name": "CrushxAmok", "username": "@CrushxAmok", "chat_id": None}
]

def get_chat_id(username):
    """Channel ka numeric chat_id fetch karega"""
    url = f"{API_URL}/getChat"
    response = requests.get(url, params={"chat_id": username})
    if response.status_code == 200:
        return response.json()["result"]["id"]
    return None

def accept_join_request(chat_id, user_id):
    """Join request accept karega"""
    url = f"{API_URL}/approveChatJoinRequest"
    response = requests.post(url, json={
        "chat_id": chat_id,
        "user_id": user_id
    })
    return response.status_code == 200

def decline_join_request(chat_id, user_id):
    """Deleted account ki request decline karega"""
    url = f"{API_URL}/declineChatJoinRequest"
    response = requests.post(url, json={
        "chat_id": chat_id,
        "user_id": user_id
    })
    return response.status_code == 200

def process_requests():
    """Har channel ki pending join requests check karega"""
    for channel in CHANNELS:
        if channel["chat_id"] is None:
            channel["chat_id"] = get_chat_id(channel["username"])
            if not channel["chat_id"]:
                print(f"❌ {channel['name']} - chat_id nahi mila")
                continue
        
        # Pending requests fetch karo
        url = f"{API_URL}/getChatJoinRequests"
        response = requests.get(url, params={
            "chat_id": channel["chat_id"],
            "limit": 100
        })
        
        if response.status_code != 200:
            print(f"❌ {channel['name']} - requests nahi mili")
            continue
        
        requests_data = response.json().get("result", [])
        
        for req in requests_data:
            user = req.get("user", {})
            user_id = user.get("id")
            is_deleted = user.get("is_deleted", False)
            
            if is_deleted:
                # Deleted account - decline karo
                decline_join_request(channel["chat_id"], user_id)
                print(f"🗑️ {channel['name']} - Deleted account {user_id} rejected")
            else:
                # Active account - accept karo
                accept_join_request(channel["chat_id"], user_id)
                print(f"✅ {channel['name']} - User {user_id} accepted")

@app.route('/')
def home():
    return "Bot is running! Join requests auto-accept kar raha hu bhai!"

@app.route('/process')
def process():
    process_requests()
    return "Requests processed!"

if __name__ == "__main__":
    print("🚀 Bot start ho raha hai...")
    # Pehle chat_ids fetch karo
    for channel in CHANNELS:
        chat_id = get_chat_id(channel["username"])
        if chat_id:
            channel["chat_id"] = chat_id
            print(f"✅ {channel['name']} - chat_id: {chat_id}")
        else:
            print(f"❌ {channel['name']} - Bot channel mein admin nahi hai ya username galat hai")
    
    # Flask app run karo
    app.run(host="0.0.0.0", port=5000)
