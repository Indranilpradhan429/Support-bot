import telebot, os
from datetime import datetime
from flask import Flask
import threading

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Running - All Fixed"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

USERS_FILE = "users.txt"
BAN_FILE = "banned.txt"

def get_users():
    if not os.path.exists(USERS_FILE): return set()
    try:
        with open(USERS_FILE, "r") as f: return set([l.strip() for l in f if l.strip()])
    except: return set()

def add_user(uid):
    if str(uid) not in get_users():
        with open(USERS_FILE, "a") as f: f.write(f"{uid}\n")

def get_banned():
    if not os.path.exists(BAN_FILE): return set()
    try:
        with open(BAN_FILE, "r") as f: return set([l.strip() for l in f if l.strip()])
    except: return set()

def ban_user(uid):
    if str(uid) not in get_banned():
        with open(BAN_FILE, "a") as f: f.write(f"{uid}\n")

def unban_user(uid):
    banned = get_banned()
    if str(uid) in banned:
        banned.remove(str(uid))
        with open(BAN_FILE, "w") as f:
            for b in banned: f.write(f"{b}\n")

@bot.message_handler(commands=['start'])
def start(m):
    if str(m.chat.id) in get_banned():
        bot.send_message(m.chat.id, "❌ You are banned.")
        return
    add_user(m.chat.id)
    bot.send_message(m.chat.id, "Hi 👋\nSend your message, Admin will reply soon.")

@bot.message_handler(commands=['stats','stat','users','total','statistics'])
def stats_cmd(m):
    if m.chat.id != ADMIN_ID:
        bot.send_message(m.chat.id, f"Not admin. Your ID: {m.chat.id}")
        return
    bot.send_message(ADMIN_ID, f"📊 Bot Statistics\n\n👥 Total Users: {len(get_users())}\n🚫 Banned: {len(get_banned())}\n🤖 Status: Online")

@bot.message_handler(commands=['info'])
def info_cmd(m):
    if m.chat.id != ADMIN_ID: return
    if m.reply_to_message and m.reply_to_message.forward_from:
        u = m.reply_to_message.forward_from
        bot.send_message(ADMIN_ID, f"👤 User Info\n\nID: `{u.id}`\nName: {u.first_name}\nUsername: @{u.username if u.username else 'None'}\nBanned: {'Yes' if str(u.id) in get_banned() else 'No'}", parse_mode="Markdown")
    else:
        bot.send_message(ADMIN_ID, "❌ Forwarded msg e Reply diye /info likho.")

@bot.message_handler(commands=['ban'])
def ban_cmd(m):
    if m.chat.id != ADMIN_ID: return
    parts = m.text.split()
    uid = m.reply_to_message.forward_from.id if (m.reply_to_message and m.reply_to_message.forward_from) else (parts[1] if len(parts)>1 else None)
    if uid:
        ban_user(uid)
        bot.send_message(ADMIN_ID, f"✅ Banned {uid}. Tar msg ar asbe na.")
    else:
        bot.send_message(ADMIN_ID, "Use: /ban USER_ID or Reply diye /ban")

@bot.message_handler(commands=['unban'])
def unban_cmd(m):
    if m.chat.id != ADMIN_ID: return
    parts = m.text.split()
    uid = m.reply_to_message.forward_from.id if (m.reply_to_message and m.reply_to_message.forward_from) else (parts[1] if len(parts)>1 else None)
    if uid:
        unban_user(uid)
        bot.send_message(ADMIN_ID, f"✅ Unbanned {uid}")
    else:
        bot.send_message(ADMIN_ID, "Use: /unban USER_ID or Reply diye /unban")

@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(m):
    if m.chat.id != ADMIN_ID: return
    text = m.text.replace("/broadcast","").strip()
    users = get_users()
    banned = get_banned()
    count=0
    for uid in users:
        if str(uid) in banned: continue
        try:
            if text: bot.send_message(int(uid), text)
            elif m.reply_to_message: bot.copy_message(int(uid), m.chat.id, m.reply_to_message.message_id)
            count+=1
        except: pass
    bot.send_message(ADMIN_ID, f"✅ Broadcast done to {count} users.")

@bot.message_handler(func=lambda m: True, content_types=['text','photo','video','document','sticker','voice','audio'])
def all_msg(m):
    if m.chat.id == ADMIN_ID:
        if m.text and m.text.startswith('/'): return
        if m.reply_to_message and m.reply_to_message.forward_from:
            try: bot.copy_message(m.reply_to_message.forward_from.id, m.chat.id, m.message_id)
            except: bot.send_message(ADMIN_ID, "❌ User blocked bot or deleted.")
    else:
        if str(m.chat.id) in get_banned(): return
        add_user(m.chat.id)
        bot.forward_message(ADMIN_ID, m.chat.id, m.message_id)
        if m.document and m.document.file_name:
            bot.send_message(ADMIN_ID, f"📁 File: {m.document.file_name}")

threading.Thread(target=run_flask).start()
bot.infinity_polling()
