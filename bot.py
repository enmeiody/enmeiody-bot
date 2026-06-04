import os
import logging
import threading
import time
from datetime import datetime, timedelta
import pytz
import telebot
from config import TZ, EGA_ID

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set!")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from db import init_db
init_db()
logging.info("Database initialized")

bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=4)
bot.set_my_commands([
    telebot.types.BotCommand("start", "Bosh menyu"),
])

from handlers import asosiy
asosiy.register(bot)

from db import (get_yonalishlar, get_yonalish, bugungi_vazifalar, yaqin_sanalar,
                eslatmalar_royxat, get_db, bugun_str, kunlik_reja_ol)
from config import USTUVORLIK


def _haftaning_kuni_uz(dt):
    kunlar = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    return kunlar[dt.weekday()]


def eslatmalar_ishchi():
    yuborilgan = {}

    while True:
        try:
            now = datetime.now(TZ)
            bugun = now.strftime("%d.%m.%Y")
            soat = now.strftime("%H:%M")
            soat_min = (now.hour, now.minute)
            haftakun = _haftaning_kuni_uz(now)

            if EGA_ID == 0:
                time.sleep(60)
                continue

            # ===== 07:00 - Ertalabki reja =====
            if soat_min == (7, 0) and yuborilgan.get(f"07_{bugun}") != True:
                yuborilgan[f"07_{bugun}"] = True
                vazifalar = bugungi_vazifalar()
                sanalar = yaqin_sanalar(7)

                matn = f"🌅 Xayrli tong! — {bugun} ({haftakun})\n" + "━" * 25 + "\n\n"

                if vazifalar:
                    matn += "📋 Bugungi vazifalar:\n"
                    for v in vazifalar:
                        em = USTUVORLIK.get(v["ustuvorlik"], "🟢")
                        matn += f"{em} {v['emoji']} {v['matn']}\n"
                    matn += "\n"
                else:
                    matn += "📋 Bugun rejalashtirilgan vazifa yo'q\n\n"

                if sanalar:
                    matn += "🎂 Muhim sanalar:\n"
                    for s in sanalar:
                        so = s["sana_obj"]
                        if s["farq"] == 0:
                            matn += f"🎉 BUGUN: {so['nomi']}!\n"
                        else:
                            matn += f"📅 {so['nomi']} — {s['farq']} kun qoldi\n"

                try:
                    bot.send_message(EGA_ID, matn)
                except Exception as e:
                    logging.error(f"Ertalabki xabar xato: {e}")

            # ===== Eslatmalar (har daqiqa tekshirish) =====
            conn = get_db()
            eslatmalar = conn.execute("SELECT * FROM eslatmalar WHERE faol=1").fetchall()
            conn.close()

            for e in eslatmalar:
                kv = e["keyingi_vaqt"] or ""
                yubor = False

                if e["tur"] == "bir_marta":
                    # Format: "05.06.2026 14:30"
                    if kv == f"{bugun} {soat}":
                        yubor = True
                        # Bir martalik - o'chirish
                        conn = get_db()
                        conn.execute("UPDATE eslatmalar SET faol=0 WHERE id=?", (e["id"],))
                        conn.commit()
                        conn.close()

                elif e["tur"] == "har_kun":
                    # Format: "08:00"
                    if kv.strip() == soat:
                        kalit = f"esl_{e['id']}_{bugun}"
                        if yuborilgan.get(kalit) != True:
                            yuborilgan[kalit] = True
                            yubor = True

                elif e["tur"] == "har_hafta":
                    # Format: "Dushanba 09:00"
                    qism = kv.split()
                    if len(qism) == 2 and qism[0] == haftakun and qism[1] == soat:
                        kalit = f"esl_{e['id']}_{bugun}"
                        if yuborilgan.get(kalit) != True:
                            yuborilgan[kalit] = True
                            yubor = True

                if yubor:
                    y = get_yonalish(e["yonalish_id"]) if e["yonalish_id"] else None
                    emoji = y["emoji"] if y else "⏰"
                    try:
                        bot.send_message(EGA_ID, f"⏰ ESLATMA\n\n{emoji} {e['matn']}")
                    except Exception as ex:
                        logging.error(f"Eslatma xato: {ex}")

            # ===== Muhim sanalar (09:00 da tekshirish) =====
            if soat_min == (9, 0) and yuborilgan.get(f"sana_{bugun}") != True:
                yuborilgan[f"sana_{bugun}"] = True
                sanalar = yaqin_sanalar(30)
                for s in sanalar:
                    so = s["sana_obj"]
                    eslat = so["eslat_kun_oldin"] or 3
                    if s["farq"] == eslat or s["farq"] == 0:
                        if s["farq"] == 0:
                            xabar = f"🎉 BUGUN: {so['nomi']}!\n\nUnutmang! 🎂"
                        else:
                            xabar = f"🔔 Eslatma: {so['nomi']}\n\n📅 {s['farq']} kundan keyin ({so['sana']})\n\nTayyorgarlik ko'rishni boshlang!"
                        if so["izoh"]:
                            xabar += f"\n\n📝 {so['izoh']}"
                        try:
                            bot.send_message(EGA_ID, xabar)
                        except: pass

            # ===== 21:00 - Kun yakuni =====
            if soat_min == (21, 0) and yuborilgan.get(f"21_{bugun}") != True:
                yuborilgan[f"21_{bugun}"] = True
                conn = get_db()
                bajarilgan = conn.execute(
                    "SELECT COUNT(*) FROM vazifalar WHERE holat='bajarildi' AND bajarilgan LIKE ?",
                    (f"{bugun}%",)).fetchone()[0]
                qolgan = conn.execute(
                    "SELECT COUNT(*) FROM vazifalar WHERE holat='faol'").fetchone()[0]
                conn.close()

                ertaga = (now + timedelta(days=1)).strftime("%d.%m.%Y")
                ertaga_kun = _haftaning_kuni_uz(now + timedelta(days=1))

                matn = f"🌙 Kun yakuni — {bugun}\n" + "━" * 25 + "\n\n"
                matn += f"✅ Bugun bajardingiz: {bajarilgan} ta vazifa\n"
                matn += f"📋 Qolgan faol vazifalar: {qolgan} ta\n\n"
                matn += f"😴 Yaxshi dam oling!\n📅 Ertaga: {ertaga_kun}"

                try:
                    bot.send_message(EGA_ID, matn)
                except: pass

            # Xotira tozalash
            if len(yuborilgan) > 200:
                yuborilgan.clear()

            time.sleep(50)
        except Exception as e:
            logging.error(f"Eslatma ishchi xato: {e}")
            time.sleep(60)


eslatma_thread = threading.Thread(target=eslatmalar_ishchi, daemon=True)
eslatma_thread.start()

if __name__ == "__main__":
    logging.info("Hayot Assistenti boti ishga tushdi!")
    bot.infinity_polling(timeout=30, long_polling_timeout=30)
