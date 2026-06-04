from telebot import types
from db import get_yonalishlar, budjet_xulosa
from config import USTUVORLIK, USTUVORLIK_NOMI


def bosh_menyu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("📋 Bugungi reja", "✅ Vazifalar")
    kb.add("⏰ Eslatmalar", "💰 Budjet")
    kb.add("🎂 Muhim sanalar", "🧠 AI suhbat")
    kb.add("👤 Men haqimda", "📂 Yo'nalishlar")
    kb.add("⚙️ Sozlamalar")
    return kb


def yonalishlar_kb(prefix, qoshimcha=None):
    """prefix: callback boshlanishi, masalan 'VYON_' """
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for y in get_yonalishlar():
        btns.append(types.InlineKeyboardButton(
            f"{y['emoji']} {y['nomi']}",
            callback_data=f"{prefix}{y['id']}"))
    kb.add(*btns)
    if qoshimcha:
        for matn, cb in qoshimcha:
            kb.add(types.InlineKeyboardButton(matn, callback_data=cb))
    return kb


def ustuvorlik_kb(prefix):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("🔴 Muhim", callback_data=f"{prefix}muhim"),
        types.InlineKeyboardButton("🟡 O'rta", callback_data=f"{prefix}orta"),
        types.InlineKeyboardButton("🟢 Oddiy", callback_data=f"{prefix}oddiy"),
    )
    return kb


def vazifa_kb(vid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ Bajarildi", callback_data=f"VBAJAR_{vid}"),
        types.InlineKeyboardButton("🗑 O'chir", callback_data=f"VOCHIR_{vid}"),
    )
    return kb


def eslatma_tur_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("⏰ Bir martalik (bugun/ertaga)", callback_data="ETUR_bir_marta"),
        types.InlineKeyboardButton("🔁 Har kuni", callback_data="ETUR_har_kun"),
        types.InlineKeyboardButton("📅 Har hafta", callback_data="ETUR_har_hafta"),
    )
    return kb


def budjet_tur_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("💰 Daromad", callback_data="BTUR_daromad"),
        types.InlineKeyboardButton("💸 Rasxod", callback_data="BTUR_rasxod"),
    )
    return kb


def orqaga_kb(cb="ORQAGA"):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data=cb))
    return kb


def tasdiq_kb(ha_cb, yoq_cb="BEKOR"):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ Ha", callback_data=ha_cb),
        types.InlineKeyboardButton("❌ Yo'q", callback_data=yoq_cb),
    )
    return kb
