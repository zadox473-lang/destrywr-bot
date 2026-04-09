import asyncio
import random
import os
import re
from datetime import datetime
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.errors import FloodWait, UserNotParticipant
from telethon import TelegramClient, events
from telethon.tl.functions.channels import EditTitleRequest, EditPhotoRequest, InviteToChannelRequest
from telethon.tl.functions.messages import AddChatUserRequest, DeleteChatUserRequest
from telethon.errors import FloodWaitError
from flask import Flask, jsonify
import threading
import time

# ==================== FLASK WEB SERVER ====================
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return jsonify({
        "status": "running",
        "bot_name": "PROXY USERBOT MANAGER",
        "creator": "@PROXYFXC x @HUNNYFXC",
        "users_connected": len(user_sessions) if 'user_sessions' in globals() else 0,
        "active_spams": len(active_spams) if 'active_spams' in globals() else 0
    })

@app_flask.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()})

@app_flask.route('/stats')
def stats():
    return jsonify({
        "total_users": len(user_sessions) if 'user_sessions' in globals() else 0,
        "active_spams": len(active_spams) if 'active_spams' in globals() else 0,
        "active_nc_reply": len(nc_reply_active) if 'nc_reply_active' in globals() else 0,
        "muted_groups": sum(len(v) for v in muted_groups.values()) if 'muted_groups' in globals() else 0,
        "muted_bots": sum(len(v) for v in muted_bots.values()) if 'muted_bots' in globals() else 0
    })

def run_flask():
    """Run Flask server in a separate thread"""
    port = int(os.environ.get('PORT', 8080))
    app_flask.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ==================== CONFIG ====================
API_ID = 32363027
API_HASH = "f54ca2aba552a66200e5878a2c1aa151"
BOT_TOKEN = "8629603752:AAFe-C1neRtbR1xwnziWwCg3jaNOL_clyGk"
OWNER_ID = 8554863978

# Force Join Channels
FORCE_CHANNELS = [
    {"id": "@lawsmok", "link": "https://t.me/lawsmok"},
    {"id": "@creepynetwork", "link": "https://t.me/creepynetwork"},
    {"id": "@proxydominates", "link": "https://t.me/proxydominates"}
]

# Protected Bots (Never mute/delete)
PROTECTED_BOTS = [
    "proxyrdp7_bot", "Hunnyabbuu_bot", "Hunnyabbu_bot", "JajaoqmN_bot",
    "Hunnyfcx_bot", "Hunnyf4cks_bot", "proxyrdp4_bot", "proxyrdp3_bot",
    "proxyrdp5_bot", "proxyrdp6_bot", "proxyrdp1_bot", "proxyrdp2_bot"
]

# Spam Messages
SPAM_MESSAGES = [
    "{target} 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗜 𝗖𝗛𝗨𝗧 𝗠𝗘 𝗖𝗛𝗔𝗡𝗚𝗘𝗦 𝗖𝗢𝗠𝗠𝗜𝗧 𝗞𝗥𝗨𝗚𝗔 🤖",
    "{target} 𝗧𝗘𝗥𝗜 𝗠𝗨𝗠𝗠𝗬 𝗞𝗜 𝗖𝗛𝗨𝗧 𝗢𝗟𝗫 𝗣𝗘 𝗕𝗘𝗖𝗛 𝗗𝗨𝗡𝗚𝗔 😎",
    "{target} 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔𝗞𝗢 𝗖𝗛𝗢𝗗 𝗗𝗔𝗟𝗔 𝗥𝗔𝗡𝗗 🤣"
]

# NC Reply Messages
NC_REPLY_TEXTS = [
    "𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗜 𝗖𝗛𝗨𝗧 𝗠𝗘 𝗖𝗛𝗔𝗡𝗚𝗘𝗦 𝗖𝗢𝗠𝗠𝗜𝗧 𝗞𝗥𝗨𝗚𝗔 🤖",
    "𝗧𝗘𝗥𝗜 𝗠𝗨𝗠𝗠𝗬 𝗞𝗜 𝗖𝗛𝗨𝗧 𝗢𝗟𝗫 𝗣𝗘 𝗕𝗘𝗖𝗛 𝗗𝗨𝗡𝗚𝗔 😎"
]

# Entry Image
ENTRY_IMAGE = "https://img-cdn.domiadi.com/DarkOwnerX4-8430364965/20260405_53ee9985.jpg"

# Entry ASCII Art (Animation)
ENTRY_ART = [
    "▒▒▒▒▒▒▒▒▄▄▄▄▄▄▄▄▒▒▒▒▒▒▒▒",
    "▒▒█▒▒▒▄██████████▄▒▒█▒▒▒",
    "▒▒▒▒▒▒████████████▒▒▒▒▒▒",
    "▒▒▒▒▒██▄▀██████▀▄██▒▒▒▒▒",
    "▒▒▒▒▒██▄▄▄▄██▄▄▄▄██▒▒▒▒▒",
    "▒▒▒▒▒██████████████▒▒▒▒▒",
    "▒▒▒▒▒████─▀▐▐▀█─█─█▒▒▒▒▒",
    "▒▒█████──────────▐████▒▒",
    "▒▒█▀▀██▄█─▄───▐─▄██▀▀█▒▒",
    "▒▒█▒▒███████▄██████▒▒█▒▒",
    "▒▒▒▒▒██████████████▒▒▒▒▒",
    "█▒▒▒▒██████████████▒▒▒▒█",
    "█▒▒▒▒▒▒▒▒▐▒▒▒▒▌▒▒▒▒▒▒▒▒█",
    "▒▒▒▒▒▒▒▒▒▐▒▒▒▒▌▒▒▒▒▒▒▒▒▒",
    "╔══════════════════════════════════════╗",
    "║   DEV - @PROXYFXC x @HUNNYFXC       ║",
    "╚══════════════════════════════════════╝"
]

# ==================== BOX FUNCTIONS ====================
def box_message(title, content, footer=None):
    lines = []
    lines.append(f"╔{'═' * (len(title) + 2)}╗")
    lines.append(f"║ {title} ║")
    lines.append(f"╠{'═' * (len(title) + 2)}╣")
    for line in content.split('\n'):
        lines.append(f"║ {line:<{len(title)}} ║")
    lines.append(f"╚{'═' * (len(title) + 2)}╝")
    if footer:
        lines.append(f"\n{footer}")
    return '\n'.join(lines)

def simple_box(text):
    lines = text.split('\n')
    max_len = max(len(l) for l in lines)
    result = []
    result.append(f"╔{'═' * (max_len + 2)}╗")
    for line in lines:
        result.append(f"║ {line:<{max_len}} ║")
    result.append(f"╚{'═' * (max_len + 2)}╝")
    return '\n'.join(result)

# ==================== BOT CLIENT ====================
bot = Client("proxy_final_main_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ==================== STORAGE ====================
user_sessions = {}  # user_id: telethon_client
active_spams = {}    # chat_id: bool
active_nc_reply = {} # user_id: bool
auto_reply_targets = {} # user_id: target_mention
muted_groups = {}    # group_id: bool (mute action active)
muted_users = {}     # user_id: bool (per user mute)
opponent_bots_list = {} # group_id: list of bot usernames
nc_reply_active = {}
muted_bots = {}
backup_profiles = {}

# ==================== FORCE JOIN CHECK ====================
async def check_force_join(user_id):
    not_joined = []
    for channel in FORCE_CHANNELS:
        try:
            member = await bot.get_chat_member(channel["id"], user_id)
            if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
                not_joined.append(channel)
        except UserNotParticipant:
            not_joined.append(channel)
        except Exception:
            not_joined.append(channel)
    return not_joined

async def force_join_message(message):
    not_joined = await check_force_join(message.from_user.id)
    if not_joined:
        buttons = []
        for ch in not_joined:
            buttons.append([InlineKeyboardButton(f"📢 Join {ch['id']}", url=ch['link'])])
        buttons.append([InlineKeyboardButton("✅ Check Join", callback_data="check_join")])
        
        await message.reply(
            simple_box("⚠️ ACCESS DENIED ⚠️\n\nYOU MUST JOIN THESE CHANNELS FIRST"),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return False
    return True

# ==================== START COMMAND ====================
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    if not await force_join_message(message):
        return
    
    welcome_text = """🔥 PROXY USERBOT MANAGER 🔥

1️⃣ Get Session from @stingsessions_bot
2️⃣ Connect using /add <session_string>
3️⃣ Type .help in Saved Messages

👑 DEV: @PROXYFXC"""
    
    await message.reply(simple_box(welcome_text))

@bot.on_callback_query()
async def callback_handler(client, callback: CallbackQuery):
    if callback.data == "check_join":
        not_joined = await check_force_join(callback.from_user.id)
        if not_joined:
            await callback.answer("❌ You haven't joined all channels!", show_alert=True)
        else:
            await callback.message.delete()
            welcome_text = """🔥 PROXY USERBOT MANAGER 🔥

1️⃣ Get Session from @stingsessions_bot
2️⃣ Connect using /add <session_string>
3️⃣ Type .help in Saved Messages

👑 DEV: @PROXYFXC"""
            await callback.message.reply(simple_box(welcome_text))
            await callback.answer("✅ Access Granted!", show_alert=True)

# ==================== ADD SESSION ====================
@bot.on_message(filters.command("add") & filters.private)
async def add_session(client, message):
    if not await force_join_message(message):
        return
    
    if len(message.command) < 2:
        await message.reply(simple_box("❌ Usage: /add <session_string>"))
        return
    
    session_string = message.command[1]
    msg = await message.reply(simple_box("🔄 Connecting..."))
    
    try:
        from telethon.sessions import StringSession
        from telethon.tl.functions.channels import CreateChannelRequest
        
        tele_client = TelegramClient(
            StringSession(session_string),
            API_ID,
            API_HASH
        )
        await tele_client.start()
        me = await tele_client.get_me()
        
        user_sessions[message.from_user.id] = tele_client
        
        # Register event handlers for telethon
        @tele_client.on(events.MessageEdited)
        async def on_edit(event):
            if event.chat_id in muted_groups.get(message.from_user.id, []):
                if event.sender_id and event.sender_id not in user_sessions:
                    if event.sender.username and event.sender.username.lower() in [b.lower() for b in PROTECTED_BOTS]:
                        return
                    try:
                        await event.delete()
                    except:
                        pass
        
        @tele_client.on(events.MessageNew)
        async def on_message(event):
            # Auto reply
            if event.sender_id and event.sender_id in auto_reply_targets:
                target_mention = auto_reply_targets[event.sender_id]
                msg = random.choice(SPAM_MESSAGES).format(target=target_mention)
                try:
                    await event.reply(msg)
                except:
                    pass
        
        @tele_client.on(events.ChatAction)
        async def on_chat_action(event):
            if event.chat_id in muted_groups.get(message.from_user.id, []):
                if event.user_added or event.user_joined:
                    pass
        
        # Store muted groups
        if message.from_user.id not in muted_groups:
            muted_groups[message.from_user.id] = set()
        
        await msg.edit(simple_box(f"✅ Connected!\nUser: {me.first_name}\nID: {me.id}\n\nType .help in Saved Messages"))
        
    except Exception as e:
        await msg.edit(simple_box(f"❌ Error: {str(e)[:100]}"))

# ==================== COMMANDS FOR USERBOT ====================
async def execute_user_command(user_id, command_func, *args):
    if user_id not in user_sessions:
        return None
    client = user_sessions[user_id]
    return await command_func(client, user_id, *args)

# ==================== HELP ====================
@bot.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    if not await force_join_message(message):
        return
    
    help_text = """📋 COMMANDS LIST

.help - Show all commands
.spame - Start infinite spam (reply to user)
.stope - Stop all spam/raid
.proxytech - Fast abuse spam (reply to user)
.proxyatc - Auto reply on user (reply)
.proxyatcstop - Stop auto reply
.ncreplye - Toggle NC reply ON/OFF
.pinge - Ping pong
.allbotse - List all opponent bots in group
.mutee - Mute single bot (reply)
.muteaction - Mute ALL opponent bots in GC
.unmuteaction - Unmute all opponent bots
.raidgc - Group raid on multiple users
.raiddm - DM raid on single user
.clonee - Clone profile (reply to user)
.backe - Restore profile
.setdpe - Set DP (reply to photo)
.deldpe - Delete DP
.dpchange - Change group DP fast repeatedly
.gccreate <count> <name> - Auto create groups
.addbotse - Add all protected bots to group
.entry - Show entry image + ASCII art
.broadcast <msg> - Owner only

👑 DEV: @PROXYFXC"""
    
    await message.reply(simple_box(help_text))

# ==================== SPAM COMMANDS ====================
@bot.on_message(filters.command("spame") & filters.private)
async def spame_command(client, message):
    if not await force_join_message(message):
        return
    
    if not message.reply_to_message:
        await message.reply(simple_box("❌ Reply to a user!"))
        return
    
    if message.from_user.id not in user_sessions:
        await message.reply(simple_box("❌ Add session first: /add <session_string>"))
        return
    
    target = message.reply_to_message.from_user
    mention = f"<a href='tg://user?id={target.id}'>{target.first_name}</a>"
    
    tele_client = user_sessions[message.from_user.id]
    chat_id = message.chat.id
    
    active_spams[chat_id] = True
    
    await message.reply(simple_box(f"🚀 Spamming {target.first_name}..."))
    
    async def spam_loop():
        while active_spams.get(chat_id, False):
            msg = random.choice(SPAM_MESSAGES).format(target=mention)
            try:
                await tele_client.send_message(chat_id, msg, parse_mode='html')
                await asyncio.sleep(0.2)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except:
                await asyncio.sleep(1)
    
    asyncio.create_task(spam_loop())

@bot.on_message(filters.command("stope") & filters.private)
async def stope_command(client, message):
    if not await force_join_message(message):
        return
    
    active_spams[message.chat.id] = False
    if message.from_user.id in auto_reply_targets:
        del auto_reply_targets[message.from_user.id]
    
    await message.reply(simple_box("🛑 All spam/raid stopped!"))

@bot.on_message(filters.command("proxytech") & filters.private)
async def proxytech_command(client, message):
    if not await force_join_message(message):
        return
    
    if not message.reply_to_message:
        await message.reply(simple_box("❌ Reply to a user!"))
        return
    
    if message.from_user.id not in user_sessions:
        await message.reply(simple_box("❌ Add session first!"))
        return
    
    target = message.reply_to_message.from_user
    mention = f"<a href='tg://user?id={target.id}'>{target.first_name}</a>"
    tele_client = user_sessions[message.from_user.id]
    chat_id = message.chat.id
    
    active_spams[chat_id] = True
    
    await message.reply(simple_box(f"⚡ Fast spamming {target.first_name}..."))
    
    async def fast_spam():
        for _ in range(50):  # 50 fast messages
            if not active_spams.get(chat_id, False):
                break
            msg = random.choice(SPAM_MESSAGES).format(target=mention)
            try:
                await tele_client.send_message(chat_id, msg, parse_mode='html')
                await asyncio.sleep(0.1)
            except:
                pass
    
    asyncio.create_task(fast_spam())

# ==================== AUTO REPLY ====================
@bot.on_message(filters.command("proxyatc") & filters.private)
async def proxyatc_command(client, message):
    if not await force_join_message(message):
        return
    
    if not message.reply_to_message:
        await message.reply(simple_box("❌ Reply to a user!"))
        return
    
    target = message.reply_to_message.from_user
    mention = f"<a href='tg://user?id={target.id}'>{target.first_name}</a>"
    auto_reply_targets[target.id] = mention
    
    await message.reply(simple_box(f"🎯 Auto-reply enabled on {target.first_name}"))

@bot.on_message(filters.command("proxyatcstop") & filters.private)
async def proxyatcstop_command(client, message):
    if not await force_join_message(message):
        return
    
    if message.from_user.id in auto_reply_targets:
        del auto_reply_targets[message.from_user.id]
    await message.reply(simple_box("🛑 Auto-reply stopped!"))

# ==================== NC REPLY ====================
@bot.on_message(filters.command("ncreplye") & filters.private)
async def ncreplye_command(client, message):
    if not await force_join_message(message):
        return
    
    user_id = message.from_user.id
    if user_id not in nc_reply_active:
        nc_reply_active[user_id] = False
    
    nc_reply_active[user_id] = not nc_reply_active[user_id]
    status = "ON" if nc_reply_active[user_id] else "OFF"
    await message.reply(simple_box(f"🔄 NC Reply: {status}"))

# ==================== PING ====================
@bot.on_message(filters.command("pinge") & filters.private)
async def pinge_command(client, message):
    if not await force_join_message(message):
        return
    
    start = datetime.now()
    msg = await message.reply(simple_box("🏓 Pinging..."))
    end = datetime.now()
    ms = (end - start).microseconds / 1000
    await msg.edit(simple_box(f"🏓 Pong!\n⏱️ {ms:.2f}ms"))

# ==================== ALL BOTS ====================
@bot.on_message(filters.command("allbotse") & filters.private)
async def allbotse_command(client, message):
    if not await force_join_message(message):
        return
    
    if message.from_user.id not in user_sessions:
        await message.reply(simple_box("❌ Add session first!"))
        return
    
    tele_client = user_sessions[message.from_user.id]
    chat_id = message.chat.id
    
    bots = []
    async for member in tele_client.iter_participants(chat_id):
        if member.bot:
            bots.append(f"@{member.username}" if member.username else member.first_name)
    
    result = "\n".join(bots) if bots else "No bots found"
    await message.reply(simple_box(f"🤖 BOTS IN GROUP:\n\n{result}"))

# ==================== MUTE COMMANDS ====================
@bot.on_message(filters.command("mutee") & filters.private)
async def mutee_command(client, message):
    if not await force_join_message(message):
        return
    
    if not message.reply_to_message:
        await message.reply(simple_box("❌ Reply to a bot!"))
        return
    
    target = message.reply_to_message.from_user
    if target.username and target.username.lower() in [b.lower() for b in PROTECTED_BOTS]:
        await message.reply(simple_box("❌ This bot is protected!"))
        return
    
    if message.from_user.id not in muted_bots:
        muted_bots[message.from_user.id] = set()
    
    muted_bots[message.from_user.id].add(target.id)
    await message.reply(simple_box(f"🔇 Muted: {target.first_name}"))

@bot.on_message(filters.command("muteaction") & filters.private)
async def muteaction_command(client, message):
    if not await force_join_message(message):
        return
    
    if message.from_user.id not in user_sessions:
        await message.reply(simple_box("❌ Add session first!"))
        return
    
    tele_client = user_sessions[message.from_user.id]
    chat_id = message.chat.id
    
    if message.from_user.id not in muted_groups:
        muted_groups[message.from_user.id] = set()
    
    muted_groups[message.from_user.id].add(chat_id)
    
    # Get all bots in group
    bots_list = []
    async for member in tele_client.iter_participants(chat_id):
        if member.bot and not (member.username and member.username.lower() in [b.lower() for b in PROTECTED_BOTS]):
            bots_list.append(member.id)
            if member.id not in muted_bots.get(message.from_user.id, set()):
                if message.from_user.id not in muted_bots:
                    muted_bots[message.from_user.id] = set()
                muted_bots[message.from_user.id].add(member.id)
    
    await message.reply(simple_box(f"🔇 Muted {len(bots_list)} bots in this group!"))

@bot.on_message(filters.command("unmuteaction") & filters.private)
async def unmuteaction_command(client, message):
    if not await force_join_message(message):
        return
    
    if message.from_user.id in muted_groups:
        muted_groups[message.from_user.id].discard(message.chat.id)
    
    await message.reply(simple_box("🔊 Unmuted all bots in this group!"))

# ==================== RAID COMMANDS ====================
@bot.on_message(filters.command("raidgc") & filters.private)
async def raidgc_command(client, message):
    if not await force_join_message(message):
        return
    
    if message.from_user.id not in user_sessions:
        await message.reply(simple_box("❌ Add session first!"))
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.reply(simple_box("❌ Usage: .raidgc @username1 @username2 ..."))
        return
    
    tele_client = user_sessions[message.from_user.id]
    chat_id = message.chat.id
    usernames = args[1:]
    
    active_spams[chat_id] = True
    
    await message.reply(simple_box(f"💣 Raiding {len(usernames)} users..."))
    
    async def raid_loop():
        while active_spams.get(chat_id, False):
            for username in usernames:
                mention = f"<a href='tg://user?id={username}'>{username}</a>"
                msg = random.choice(SPAM_MESSAGES).format(target=mention)
                try:
                    await tele_client.send_message(chat_id, msg, parse_mode='html')
                    await asyncio.sleep(0.3)
                except:
                    pass
    
    asyncio.create_task(raid_loop())

@bot.on_message(filters.command("raiddm") & filters.private)
async def raiddm_command(client, message):
    if not await force_join_message(message):
        return
    
    if not message.reply_to_message:
        await message.reply(simple_box("❌ Reply to a user!"))
        return
    
    if message.from_user.id not in user_sessions:
        await message.reply(simple_box("❌ Add session first!"))
        return
    
    target = message.reply_to_message.from_user
    tele_client = user_sessions[message.from_user.id]
    mention = f"<a href='tg://user?id={target.id}'>{target.first_name}</a>"
    
    active_spams[target.id] = True
    
    await message.reply(simple_box(f"💣 DM Raiding {target.first_name}..."))
    
    async def dm_raid():
        while active_spams.get(target.id, False):
            msg = random.choice(SPAM_MESSAGES).format(target=mention)
            try:
                await tele_client.send_message(target.id, msg, parse_mode='html')
                await asyncio.sleep(0.2)
            except:
                await asyncio.sleep(1)
    
    asyncio.create_task(dm_raid())

# ==================== CLONE / BACKUP ====================
@bot.on_message(filters.command("clonee") & filters.private)
async def clonee_command(client, message):
    if not await force_join_message(message):
        return
    
    if not message.reply_to_message:
        await message.reply(simple_box("❌ Reply to a user!"))
        return
    
    if message.from_user.id not in user_sessions:
        await message.reply(simple_box("❌ Add session first!"))
        return
    
    tele_client = user_sessions[message.from_user.id]
    target = message.reply_to_message.from_user
    
    await message.reply(simple_box(f"👤 Cloning {target.first_name}..."))
    
    try:
        # Backup current profile
        me = await tele_client.get_me()
        backup_profiles[message.from_user.id] = {
            "first_name": me.first_name,
            "last_name": me.last_name or ""
        }
        
        # Clone target
        await tele_client.edit_profile(
            first_name=target.first_name or "",
            last_name=target.last_name or ""
        )
        
        # Clone photo if exists
        photos = await tele_client.get_profile_photos(target.id, limit=1)
        if photos:
            file = await tele_client.download_media(photos[0], bytes)
            await tele_client.edit_profile_photo(photo=file)
        
        await message.reply(simple_box(f"✅ Cloned: {target.first_name}"))
    except Exception as e:
        await message.reply(simple_box(f"❌ Error: {str(e)[:50]}"))

@bot.on_message(filters.command("backe") & filters.private)
async def backe_command(client, message):
    if not await force_join_message(message):
        return
    
    if message.from_user.id not in user_sessions:
        await message.reply(simple_box("❌ Add session first!"))
        return
    
    if message.from_user.id not in backup_profiles:
        await message.reply(simple_box("❌ No backup found!"))
        return
    
    tele_client = user_sessions[message.from_user.id]
    backup = backup_profiles[message.from_user.id]
    
    await message.reply(simple_box("🔄 Restoring profile..."))
    
    try:
        await tele_client.edit_profile(
            first_name=backup["first_name"],
            last_name=backup["last_name"]
        )
        await message.reply(simple_box("✅ Profile restored!"))
    except Exception as e:
        await message.reply(simple_box(f"❌ Error: {str(e)[:50]}"))

# ==================== DP COMMANDS ====================
@bot.on_message(filters.command("setdpe") & filters.private)
async def setdpe_command(client, message):
    if not await force_join_message(message):
        return
    
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply(simple_box("❌ Reply to a photo!"))
        return
    
    if message.from_user.id not in user_sessions:
        await message.reply(simple_box("❌ Add session first!"))
        return
    
    tele_client = user_sessions[message.from_user.id]
    
    await message.reply(simple_box("📸 Setting DP..."))
    
    try:
        file = await message.reply_to_message.download()
        await tele_client.edit_profile_photo(photo=file)
        os.remove(file)
        await message.reply(simple_box("✅ DP updated!"))
    except Exception as e:
        await message.reply(simple_box(f"❌ Error: {str(e)[:50]}"))

@bot.on_message(filters.command("deldpe") & filters.private)
async def deldpe_command(client, message):
    if not await force_join_message(message):
        return
    
    if message.from_user.id not in user_sessions:
        await message.reply(simple_box("❌ Add session first!"))
        return
    
    tele_client = user_sessions[message.from_user.id]
    
    await message.reply(simple_box("🗑️ Deleting DP..."))
    
    try:
        await tele_client.edit_profile_photo(photo=None)
        await message.reply(simple_box("✅ DP deleted!"))
    except Exception as e:
        await message.reply(simple_box(f"❌ Error: {str(e)[:50]}"))

@bot.on_message(filters.command("dpchange") & filters.private)
async def dpchange_command(client, message):
    if not await force_join_message(message):
        return
    
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply(simple_box("❌ Reply to a photo!"))
        return
    
    if message.from_user.id not in user_sessions:
        await message.reply(simple_box("❌ Add session first!"))
        return
    
    tele_client = user_sessions[message.from_user.id]
    chat_id = message.chat.id
    
    await message.reply(simple_box("🔄 Changing group DP repeatedly..."))
    
    file = await message.reply_to_message.download()
    
    async def change_dp_loop():
        for _ in range(20):
            try:
                await tele_client(EditPhotoRequest(chat_id, photo=file))
                await asyncio.sleep(0.5)
            except:
                pass
    
    asyncio.create_task(change_dp_loop())
    await asyncio.sleep(2)
    os.remove(file)

# ==================== CREATE GROUP ====================
@bot.on_message(filters.command("gccreate") & filters.private)
async def gccreate_command(client, message):
    if not await force_join_message(message):
        return
    
    if message.from_user.id not in user_sessions:
        await message.reply(simple_box("❌ Add session first!"))
        return
    
    args = message.text.split()
    if len(args) < 3:
        await message.reply(simple_box("❌ Usage: .gccreate <count> <name>"))
        return
    
    try:
        count = int(args[1])
        name = " ".join(args[2:])
    except:
        await message.reply(simple_box("❌ Invalid count!"))
        return
    
    tele_client = user_sessions[message.from_user.id]
    
    await message.reply(simple_box(f"📝 Creating {count} groups..."))
    
    for i in range(count):
        try:
            from telethon.tl.functions.channels import CreateChannelRequest
            group_name = f"{name} {i+1}"
            result = await tele_client(CreateChannelRequest(
                title=group_name,
                about="Created by PROXY BOT",
                megagroup=True
            ))
            await asyncio.sleep(1)
        except Exception as e:
            await message.reply(simple_box(f"❌ Error on group {i+1}: {str(e)[:50]}"))
            break
    
    await message.reply(simple_box(f"✅ Created {count} groups!"))

# ==================== ADD BOTS TO GROUP ====================
@bot.on_message(filters.command("addbotse") & filters.private)
async def addbotse_command(client, message):
    if not await force_join_message(message):
        return
    
    if message.from_user.id not in user_sessions:
        await message.reply(simple_box("❌ Add session first!"))
        return
    
    tele_client = user_sessions[message.from_user.id]
    chat_id = message.chat.id
    
    await message.reply(simple_box("🤖 Adding protected bots..."))
    
    added = 0
    for bot_name in PROTECTED_BOTS:
        try:
            await tele_client(InviteToChannelRequest(chat_id, [bot_name]))
            added += 1
            await asyncio.sleep(0.5)
        except:
            pass
    
    await message.reply(simple_box(f"✅ Added {added} bots!"))

# ==================== ENTRY COMMAND ====================
@bot.on_message(filters.command("entry") & filters.private)
async def entry_command(client, message):
    if not await force_join_message(message):
        return
    
    msg = await message.reply(simple_box("🎬 LOADING..."))
    
    # Animate ASCII art line by line
    for line in ENTRY_ART:
        await msg.edit(simple_box(line))
        await asyncio.sleep(0.15)
    
    # Send image
    await msg.delete()
    await message.reply_photo(
        ENTRY_IMAGE,
        caption=simple_box("🔥 PROXY USERBOT READY 🔥\n\n👑 DEV: @PROXYFXC")
    )

# ==================== BROADCAST (OWNER ONLY) ====================
@bot.on_message(filters.command("broadcast") & filters.private)
async def broadcast_command(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply(simple_box("❌ Owner only command!"))
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(simple_box("❌ Usage: .broadcast <message>"))
        return
    
    broadcast_msg = args[1]
    
    await message.reply(simple_box("📢 Broadcasting..."))
    
    sent = 0
    for user_id in user_sessions.keys():
        try:
            await client.send_message(user_id, simple_box(f"📢 BROADCAST\n\n{broadcast_msg}"))
            sent += 1
            await asyncio.sleep(0.5)
        except:
            pass
    
    await message.reply(simple_box(f"✅ Broadcast sent to {sent} users!"))

# ==================== START BOT ====================
async def main():
    """Main async function to run both Flask and Bot"""
    print("🔥 PROXY USERBOT MANAGER STARTING...")
    print("╔══════════════════════════════════════╗")
    print("║   DEV - @PROXYFXC x @HUNNYFXC       ║")
    print("╚══════════════════════════════════════╝")
    
    # Start Flask in thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Start the bot
    await bot.run()
    
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())
