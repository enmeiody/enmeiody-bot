import os
import pytz

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Egasi (faqat siz) - Telegram ID
EGA_ID = int(os.environ.get("EGA_ID", "0"))

# Standart vaqt zonasi (sozlamalardan o'zgartirish mumkin)
STANDART_TZ = "Asia/Tashkent"

# Mavjud vaqt zonalari (tugma uchun)
VAQT_ZONALARI = [
    ("🇺🇿 Toshkent", "Asia/Tashkent"),
    ("🇨🇳 Xitoy (Pekin)", "Asia/Shanghai"),
    ("🇷🇺 Moskva", "Europe/Moscow"),
    ("🇹🇷 Istanbul", "Europe/Istanbul"),
    ("🇦🇪 Dubay", "Asia/Dubai"),
    ("🇰🇿 Olmaota", "Asia/Almaty"),
    ("🇰🇷 Seul", "Asia/Seoul"),
    ("🇬🇧 London", "Europe/London"),
    ("🇺🇸 Nyu-York", "America/New_York"),
]


def get_tz():
    """Joriy vaqt zonasini DB dan o'qiydi, bo'lmasa standart"""
    try:
        from db import sozlama_ol
        nom = sozlama_ol("vaqt_zona", STANDART_TZ)
        return pytz.timezone(nom)
    except:
        return pytz.timezone(STANDART_TZ)


# Eski kod mosligi uchun (dinamik chaqiriladi)
TZ = pytz.timezone(STANDART_TZ)

# Boshlang'ich yo'nalishlar
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
