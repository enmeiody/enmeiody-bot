import os
import pytz

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Vaqt zonasi - Uzbekiston (UTC+5)
TZ = pytz.timezone("Asia/Tashkent")

# Egasi (faqat siz) - Telegram ID
EGA_ID = int(os.environ.get("EGA_ID", "0"))

# Boshlang'ich yo'nalishlar (keyin qo'shish/o'chirish mumkin)
BOSHLANGICH_YONALISHLAR = [
    ("Umumiy", "🌐", "Sen umumiy hayot yordamchisisan. Kunlik rejalar, sog'liq, shaxsiy rivojlanish va boshqa narsalarda yordam berasan. Samimiy va qisqa gapirasan."),
    ("SMM", "🎬", "Sen SMM mutaxassisi yordamchisisan. Kontent rejalar, post g'oyalari, trend tahlili, auditoriya o'sishi haqida professional maslahat berasan."),
    ("DJ", "🎧", "Sen musiqa va DJ lik yordamchisisan. Trek tanlash, set tuzish, miks g'oyalari, chiqishlar rejasi haqida yordam berasan."),
    ("Dasturchi", "💻", "Sen dasturlash yordamchisisan. Kod, loyihalar, texnologiyalar, debugging va o'rganish rejalarida yordam berasan. Texnik va aniq gapirasan."),
    ("Bloger", "📝", "Sen blogerlik yordamchisisan. Video g'oyalari, ssenariy, montaj rejasi, kontent strategiyasi haqida ijodiy yordam berasan."),
    ("Oila", "👨‍👩‍👧", "Sen oilaviy ishlar yordamchisisan. Muhim sanalar, sovg'alar, oilaviy reja, sog'liq va e'tibor haqida iliq yordam berasan."),
]

# Ustuvorlik
USTUVORLIK = {"muhim": "🔴", "orta": "🟡", "oddiy": "🟢"}
USTUVORLIK_NOMI = {"muhim": "Muhim", "orta": "O'rta", "oddiy": "Oddiy"}

# Budjet turlari
BUDJET_TUR = {"daromad": "💰", "rasxod": "💸"}
