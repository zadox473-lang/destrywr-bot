import time
import requests
import threading
from flask import Flask

app = Flask(__name__)

# 🔥 APNA NAYA TOKEN DALO (jo regenerate kiya hai)
BOT_TOKEN = "YOUR_NEW_TOKEN_HERE"

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

CHANNELS = ["ProxyeFans", "CrushxAmok"]

def get_chat_id(username):
    url = f"{API_URL}/getChat"
    try:
        r = requests.get(url, params={"chat_id": f"@{username}"}, timeout=10)
        if r.status_code == 200:
            return r.json()["result"]["id"]
    except:
        pass
    return None

def accept_request(chat_id, user_id):
    url = f"{API_URL}/approveChatJoinRequest"
    try:
        requests.post(url, json={"chat_id": chat_id, "user_id": user_id}, timeout=10)
    except:
        pass

def decline_request(chat_id, user_id):
    url = f"{API_URL}/declineChatJoinRequest"
    try:
        requests.post(url, json={"chat_id": chat_id, "user_id": user_id}, timeout=10)
    except:
        pass

def process_all():
    for name in CHANNELS:
        chat_id = get_chat_id(name)
        if not chat_id:
            print(f"❌ {name} - Bot admin nahi hai")
            continue
        
        url = f"{API_URL}/getChatJoinRequests"
        try:
            r = requests.get(url, params={"chat_id": chat_id, "limit": 100}, timeout=10)
            if r.status_code != 200:
                continue
                
            for req in r.json().get("result", []):
                user = req.get("user", {})
                if user.get("is_deleted"):
                    decline_request(chat_id, user["id"])
                    print(f"🗑️ {name} - Deleted account rejected")
                else:
                    accept_request(chat_id, user["id"])
                    print(f"✅ {name} - User accepted")
        except:
            pass

def auto_run():
    while True:
        process_all()
        time.sleep(10)  # Har 10 second mein check karega

@app.route('/')
def home():
    return "✅ Bot is running! Join requests auto-accept ho rahi hai"

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    # Background thread start karo
    thread = threading.Thread(target=auto_run, daemon=True)
    thread.start()
    print("🚀 Bot started on Render!")
    app.run(host="0.0.0.0", port=10000)
