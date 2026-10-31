import telebot
import os
from datetime import datetime
from flask import Flask
import threading

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)
@app.route('/')
def home(): return "Bot Running"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

USERS_FILE = "users.txt"
STATS_FILE = "stats.txt"

def get_users():
    if not os.path.exists(USERS_FILE): return set()
    try:
        with open(USERS_FILE, "r") as f:
            return set([x.strip() for x in f.read().splitlines() if x.strip()])
    except: return set()

def add_user(uid):
    users = get_users()
    if str(uid) not in users:
        with open(USERS_FILE, "a") as f:
            f.write(str(uid)+"\n")
        with open(STATS_FILE, "a") as f:
            f.write(f"{uid},{datetime.now().strftime('%Y-%m-%d')}\n")

@bot.message_handler(commands=['start'])
def start(m):
    add_user(m.chat.id)
    bot.send_message(m.chat.id, "Hi! Send your message here. Admin will reply you soon.")

# STATS - Alada kore dilam jate 100% kaj kore
@bot.message_handler(commands=['stats','stat','users'])
def stats_cmd(m):
    if m.chat.id != ADMIN_ID: return
    users = get_users()
    total = len(users)
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_c = 0
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                for line in f:
                    if today_str in line:
                        today_c+=1
        except: pass
    bot.send_message(ADMIN_ID, f"📊 Bot Statistics\n\n👥 Total Users: {total}\n📅 Joined Today: {today_c}\n🤖 Status: Online\n🕒 {datetime.now().strftime('%d-%m-%Y %H:%M')}")

@bot.message_handler(commands=['info'])
def info_cmd(m):
    if m.chat.id != ADMIN_ID: return
    if m.reply_to_message and m.reply_to_message.forward_from:
        u = m.reply_to_message.forward_from
        bot.send_message(ADMIN_ID, f"👤 User Info\n\nID: {u.id}\nName: {u.first_name}\nUsername: @{u.username if u.username else 'No username'}")
    else:
        bot.send_message(ADMIN_ID, "❌ Reply diye /info likho.\nExample: Forwarded msg e Reply > /info\n\nJodi user privacy on rakhe tahole ID dekha jabe na.")

@bot.message_handler(commands=['broadcast','botcast'])
def broadcast_cmd(m):
    if m.chat.id != ADMIN_ID: return
    msg_text = m.text.replace("/broadcast","").replace("/botcast","").strip()
    users = get_users()
    if not msg_text and m.reply_to_message:
        count=0
        for uid in users:
            try:
                bot.copy_message(int(uid), m.chat.id, m.reply_to_message.message_id)
                count+=1
            except: pass
        bot.send_message(ADMIN_ID, f"✅ Broadcast sent to {count} users.")
        return
    if not msg_text:
        bot.send_message(ADMIN_ID, "Usage: /broadcast Your message")
        return
    count=0
    for uid in users:
        try:
            bot.send_message(int(uid), msg_text)
            count+=1
        except: pass
    bot.send_message(ADMIN_ID, f"✅ Broadcast sent to {count} users.")

@bot.message_handler(func=lambda m: True, content_types=['text','photo','video','document','sticker','voice','audio'])
def handle(m):
    if m.chat.id == ADMIN_ID:
        if m.text and m.text.startswith('/'): return
        if m.reply_to_message and m.reply_to_message.forward_from:
            try:
                bot.copy_message(m.reply_to_message.forward_from.id, m.chat.id, m.message_id)
            except:
                bot.send_message(ADMIN_ID, "User ke msg pathano jacche na. User bot block koreche hoyto.")
    else:
        add_user(m.chat.id)
        bot.forward_message(ADMIN_ID, m.chat.id, m.message_id)
        bot.send_message(m.chat.id, "Your message has been sent to admin.")

threading.Thread(target=run_flask).start()
print("Bot Started")
bot.infinity_polling()
