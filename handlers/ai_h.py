import os
import json
import urllib.request
import logging

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

ASOSIY_KONTEKST = """Sen foydalanuvchining shaxsiy "ikkinchi miyasi"sisan - uning hayotini boshqarishga yordam beruvchi aqlli yordamchi.

Foydalanuvchi bilan o'zbek tilida, samimiy va do'stona gaplashasan. Qisqa va aniq javob berasan, ortiqcha gap yo'q.

Sen quyidagilarni qila olasan (foydalanuvchiga eslatib turishing mumkin):
- Vazifa qo'shish va kuzatish
- Eslatmalar o'rnatish
- Budjet (daromad/rasxod) hisobi
- Muhim sanalarni eslab qolish
- Kunlik reja tuzish

Agar foydalanuvchi biror vazifa, eslatma yoki reja haqida gapirsa, unga buni botda saqlashni taklif qil."""


def ai_javob(shaxsiyat, savol, tarix=None, qoshimcha_kontekst=""):
    """
    shaxsiyat: yo'nalish AI xarakteri
    savol: foydalanuvchi savoli
    tarix: [(rol, matn), ...] oldingi suhbat
    """
    if not ANTHROPIC_API_KEY:
        return "⚠️ AI hozircha ulanmagan. ANTHROPIC_API_KEY ni Railway sozlamalarida qo'shing."

    system = ASOSIY_KONTEKST + "\n\n--- Hozirgi yo'nalish ---\n" + (shaxsiyat or "")
    if qoshimcha_kontekst:
        system += "\n\n--- Joriy holat ---\n" + qoshimcha_kontekst

    messages = []
    if tarix:
        for t in tarix:
            rol = "user" if t["rol"] == "user" else "assistant"
            messages.append({"role": rol, "content": t["matn"]})
    messages.append({"role": "user", "content": savol})

    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "system": system,
        "messages": messages,
    }

    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
            })
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data["content"][0]["text"]
    except Exception as e:
        logging.error(f"AI xato: {e}")
        return f"⚠️ AI javob berolmadi. Qayta urinib ko'ring."


def kunlik_reja_tuz(vazifalar, sanalar, eslatmalar):
    """AI yordamida kunlik reja tuzish"""
    if not ANTHROPIC_API_KEY:
        return None

    kontekst = "Bugungi vazifalar:\n"
    for v in vazifalar:
        kontekst += f"- [{v['ustuvorlik']}] {v['matn']}\n"
    if sanalar:
        kontekst += "\nYaqin muhim sanalar:\n"
        for s in sanalar:
            kontekst += f"- {s['sana_obj']['nomi']} ({s['farq']} kundan keyin)\n"
    if eslatmalar:
        kontekst += "\nBugungi eslatmalar:\n"
        for e in eslatmalar:
            kontekst += f"- {e['vaqt']}: {e['matn']}\n"

    savol = f"{kontekst}\n\nShu ma'lumotlar asosida menga qisqa, aniq kunlik reja tuzib ber. Ustuvorlikka qarab tartibla. Motivatsion bo'lsin lekin ortiqcha gap yo'q."

    return ai_javob("Sen kunlik reja tuzuvchi yordamchisan.", savol)
