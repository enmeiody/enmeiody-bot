import logging
from datetime import datetime, timedelta
import pytz
from telebot import types
from config import EGA_ID, USTUVORLIK, USTUVORLIK_NOMI, BUDJET_TUR, VAQT_ZONALARI
from db import (_tz, sozlama_ol, sozlama_saqla, profil_qosh, profil_ol, profil_ochir, profil_matn, get_yonalishlar, get_yonalish, yonalish_qosh, yonalish_ochir,
                vazifa_qosh, vazifalar_royxat, vazifa_bajar, vazifa_ochir, bugungi_vazifalar,
                eslatma_qosh, eslatmalar_royxat, eslatma_ochir,
                budjet_qosh, budjet_xulosa, budjet_royxat,
                sana_qosh, sanalar_royxat, sana_ochir, yaqin_sanalar,
                kunlik_reja_saqla, kunlik_reja_ol,
                ai_tarix_qosh, ai_tarix_ol, ai_tarix_tozala,
                bugun_str, hozir_str)
from keyboards import (bosh_menyu, yonalishlar_kb, ustuvorlik_kb, vazifa_kb,
                       eslatma_tur_kb, budjet_tur_kb, orqaga_kb, tasdiq_kb)
from handlers.astate import astate
from handlers.ai_h import ai_javob, kunlik_reja_tuz


def faqat_ega(uid):
    """Faqat bot egasi ishlatishi mumkin"""
    return EGA_ID == 0 or uid == EGA_ID


def fmt_pul(s):
    return f"{int(s):,}".replace(",", " ")


def register(bot):

    # ============ START ============
    @bot.message_handler(commands=["start"])
    def h_start(msg):
        uid = msg.from_user.id
        if not faqat_ega(uid):
            bot.send_message(msg.chat.id,
                f"Bu shaxsiy bot. Sizning ID: {uid}\nAgar bu sizniki bo'lsa, EGA_ID ga shu raqamni qo'ying.")
            return
        astate.pop(uid, None)
        bot.send_message(msg.chat.id,
            "🧠 Salom! Men sening ikkinchi miyangman.\n\n"
            "Hayotingni boshqarishda yordam beraman:\n"
            "📋 Kunlik reja\n✅ Vazifalar\n⏰ Eslatmalar\n"
            "💰 Budjet\n🎂 Muhim sanalar\n🧠 AI suhbat\n\n"
            "Har bir yo'nalishing alohida. Boshladik!",
            reply_markup=bosh_menyu())

    # ============ BUGUNGI REJA ============
    @bot.message_handler(func=lambda m: m.text == "📋 Bugungi reja" and faqat_ega(m.from_user.id))
    def h_bugungi(msg):
        uid = msg.from_user.id
        bugun = bugun_str()
        vazifalar = bugungi_vazifalar()
        sanalar = yaqin_sanalar(7)
        eslatmalar = eslatmalar_royxat()

        matn = f"📋 BUGUNGI REJA — {bugun}\n" + "━" * 25 + "\n\n"

        if vazifalar:
            matn += "✅ Vazifalar:\n"
            for v in vazifalar:
                em = USTUVORLIK.get(v["ustuvorlik"], "🟢")
                matn += f"{em} {v['emoji']} {v['matn']}\n"
            matn += "\n"
        else:
            matn += "✅ Bugun faol vazifa yo'q\n\n"

        if sanalar:
            matn += "🎂 Yaqin muhim sanalar:\n"
            for s in sanalar:
                so = s["sana_obj"]
                if s["farq"] == 0:
                    matn += f"🎉 BUGUN: {so['nomi']}!\n"
                else:
                    matn += f"📅 {so['nomi']} — {s['farq']} kundan keyin\n"
            matn += "\n"

        saqlangan = kunlik_reja_ol(bugun)
        if saqlangan:
            matn += "🧠 AI reja:\n" + saqlangan + "\n"

        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("🧠 AI dan kunlik reja so'rash", callback_data="AI_REJA"))
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "AI_REJA")
    def cb_ai_reja(call):
        uid = call.from_user.id
        if not faqat_ega(uid): return
        bot.answer_callback_query(call.id, "AI reja tuzmoqda...")
        vazifalar = bugungi_vazifalar()
        sanalar = yaqin_sanalar(7)
        eslatmalar = eslatmalar_royxat()
        reja = kunlik_reja_tuz(vazifalar, sanalar, eslatmalar)
        if reja:
            kunlik_reja_saqla(bugun_str(), reja)
            bot.send_message(call.message.chat.id, f"🧠 Bugungi reja:\n\n{reja}")
        else:
            bot.send_message(call.message.chat.id, "⚠️ AI ulanmagan. ANTHROPIC_API_KEY kerak.")

    # ============ VAZIFALAR ============
    @bot.message_handler(func=lambda m: m.text == "✅ Vazifalar" and faqat_ega(m.from_user.id))
    def h_vazifalar(msg):
        kb = yonalishlar_kb("VYON_", [
            ("📊 Barcha vazifalar", "VBARCHA"),
            ("➕ Yangi vazifa", "VYANGI"),
        ])
        bot.send_message(msg.chat.id, "✅ Qaysi yo'nalish vazifalari?", reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("VYON_"))
    def cb_vyon(call):
        uid = call.from_user.id
        yid = int(call.data.replace("VYON_", ""))
        y = get_yonalish(yid)
        vazifalar = vazifalar_royxat(yid, "faol")
        matn = f"{y['emoji']} {y['nomi']} — vazifalar\n" + "━" * 22 + "\n\n"
        if not vazifalar:
            matn += "Faol vazifa yo'q"
        bot.send_message(call.message.chat.id, matn)
        for v in vazifalar:
            em = USTUVORLIK.get(v["ustuvorlik"], "🟢")
            t = f"{em} {v['matn']}"
            if v["muddat"]:
                t += f"\n📅 Muddat: {v['muddat']}"
            bot.send_message(call.message.chat.id, t, reply_markup=vazifa_kb(v["id"]))
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("➕ Yangi vazifa qo'shish", callback_data=f"VYANGI_{yid}"))
        bot.send_message(call.message.chat.id, "—", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "VBARCHA")
    def cb_vbarcha(call):
        vazifalar = vazifalar_royxat(None, "faol")
        if not vazifalar:
            bot.send_message(call.message.chat.id, "Faol vazifa yo'q")
            bot.answer_callback_query(call.id)
            return
        matn = "📊 BARCHA VAZIFALAR\n" + "━" * 22 + "\n\n"
        for v in vazifalar:
            em = USTUVORLIK.get(v["ustuvorlik"], "🟢")
            matn += f"{em} {v['emoji']} {v['matn']}"
            if v["muddat"]:
                matn += f" (📅 {v['muddat']})"
            matn += "\n"
        bot.send_message(call.message.chat.id, matn)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "VYANGI" or c.data.startswith("VYANGI_"))
    def cb_vyangi(call):
        uid = call.from_user.id
        if "_" in call.data:
            yid = int(call.data.replace("VYANGI_", ""))
            astate[uid] = {"step": "vazifa_matn", "yid": yid}
            bot.send_message(call.message.chat.id, "✏️ Vazifa matnini yozing:")
        else:
            kb = yonalishlar_kb("VYANGIYON_")
            bot.send_message(call.message.chat.id, "Qaysi yo'nalishga?", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("VYANGIYON_"))
    def cb_vyangiyon(call):
        uid = call.from_user.id
        yid = int(call.data.replace("VYANGIYON_", ""))
        astate[uid] = {"step": "vazifa_matn", "yid": yid}
        bot.send_message(call.message.chat.id, "✏️ Vazifa matnini yozing:")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("VBAJAR_"))
    def cb_vbajar(call):
        vid = int(call.data.replace("VBAJAR_", ""))
        vazifa_bajar(vid)
        bot.edit_message_text("✅ Bajarildi!", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Tabriklayman! 🎉")

    @bot.callback_query_handler(func=lambda c: c.data.startswith("VOCHIR_"))
    def cb_vochir(call):
        vid = int(call.data.replace("VOCHIR_", ""))
        vazifa_ochir(vid)
        bot.edit_message_text("🗑 O'chirildi", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("VUST_"))
    def cb_vust(call):
        uid = call.from_user.id
        ust = call.data.replace("VUST_", "")
        st = astate.get(uid, {})
        st["ustuvorlik"] = ust
        st["step"] = "vazifa_muddat"
        astate[uid] = st
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("📅 Bugun", callback_data="VMUD_bugun"),
            types.InlineKeyboardButton("📅 Ertaga", callback_data="VMUD_ertaga"),
            types.InlineKeyboardButton("📆 Sana yozaman", callback_data="VMUD_qol"),
            types.InlineKeyboardButton("➖ Muddatsiz", callback_data="VMUD_yoq"),
        )
        bot.send_message(call.message.chat.id, "Muddat?", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("VMUD_"))
    def cb_vmud(call):
        uid = call.from_user.id
        tur = call.data.replace("VMUD_", "")
        st = astate.get(uid, {})
        muddat = None
        if tur == "bugun":
            muddat = bugun_str()
        elif tur == "ertaga":
            muddat = (datetime.now(_tz()) + timedelta(days=1)).strftime("%d.%m.%Y")
        elif tur == "qol":
            st["step"] = "vazifa_muddat_qol"
            astate[uid] = st
            bot.send_message(call.message.chat.id, "📆 Sanani yozing (kun.oy.yil, masalan 15.06.2026):")
            bot.answer_callback_query(call.id)
            return
        # Saqlash
        vazifa_qosh(st["yid"], st["matn"], muddat, st.get("ustuvorlik", "oddiy"))
        astate.pop(uid, None)
        y = get_yonalish(st["yid"])
        em = USTUVORLIK.get(st.get("ustuvorlik", "oddiy"), "🟢")
        t = f"✅ Vazifa qo'shildi!\n\n{em} {y['emoji']} {st['matn']}"
        if muddat:
            t += f"\n📅 {muddat}"
        bot.send_message(call.message.chat.id, t, reply_markup=bosh_menyu())
        bot.answer_callback_query(call.id)

    # ============ ESLATMALAR ============
    @bot.message_handler(func=lambda m: m.text == "⏰ Eslatmalar" and faqat_ega(m.from_user.id))
    def h_eslatmalar(msg):
        eslatmalar = eslatmalar_royxat()
        matn = "⏰ ESLATMALAR\n" + "━" * 20 + "\n\n"
        if eslatmalar:
            for e in eslatmalar:
                tur_emoji = {"bir_marta": "⏰", "har_kun": "🔁", "har_hafta": "📅"}.get(e["tur"], "⏰")
                matn += f"{tur_emoji} {e['emoji'] or ''} {e['matn']}\n   🕐 {e['keyingi_vaqt']}\n"
        else:
            matn += "Eslatma yo'q"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("➕ Yangi eslatma", callback_data="EYANGI"))
        if eslatmalar:
            kb.add(types.InlineKeyboardButton("🗑 Eslatma o'chirish", callback_data="EOCHIR_MENU"))
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "EYANGI")
    def cb_eyangi(call):
        kb = yonalishlar_kb("EYON_")
        bot.send_message(call.message.chat.id, "Qaysi yo'nalishga eslatma?", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("EYON_"))
    def cb_eyon(call):
        uid = call.from_user.id
        yid = int(call.data.replace("EYON_", ""))
        astate[uid] = {"step": "eslatma_matn", "yid": yid}
        bot.send_message(call.message.chat.id, "✏️ Eslatma matnini yozing:")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("ETUR_"))
    def cb_etur(call):
        uid = call.from_user.id
        tur = call.data.replace("ETUR_", "")
        st = astate.get(uid, {})
        st["tur"] = tur
        st["step"] = "eslatma_vaqt"
        astate[uid] = st
        if tur == "bir_marta":
            yoriq = "🕐 Vaqtni yozing (kun.oy.yil soat:daqiqa)\nMasalan: 05.06.2026 14:30"
        elif tur == "har_kun":
            yoriq = "🕐 Soatni yozing (soat:daqiqa)\nMasalan: 08:00"
        else:
            yoriq = "🕐 Kun va soatni yozing\nMasalan: Dushanba 09:00"
        bot.send_message(call.message.chat.id, yoriq)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "EOCHIR_MENU")
    def cb_eochir_menu(call):
        eslatmalar = eslatmalar_royxat()
        kb = types.InlineKeyboardMarkup(row_width=1)
        for e in eslatmalar:
            kb.add(types.InlineKeyboardButton(f"🗑 {e['matn'][:30]}", callback_data=f"EOCHIR_{e['id']}"))
        bot.send_message(call.message.chat.id, "Qaysi eslatmani o'chirish?", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("EOCHIR_") and c.data != "EOCHIR_MENU")
    def cb_eochir(call):
        eid = int(call.data.replace("EOCHIR_", ""))
        eslatma_ochir(eid)
        bot.edit_message_text("🗑 Eslatma o'chirildi", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    # ============ BUDJET ============
    @bot.message_handler(func=lambda m: m.text == "💰 Budjet" and faqat_ega(m.from_user.id))
    def h_budjet(msg):
        oy = datetime.now(_tz()).strftime("%m.%Y")
        x = budjet_xulosa(oy=oy)
        matn = f"💰 BUDJET — {oy}\n" + "━" * 20 + "\n\n"
        matn += f"💰 Daromad: {fmt_pul(x['daromad'])} so'm\n"
        matn += f"💸 Rasxod:  {fmt_pul(x['rasxod'])} so'm\n"
        matn += "─" * 20 + "\n"
        bal = x["balans"]
        belgi = "✅" if bal >= 0 else "⚠️"
        matn += f"{belgi} Balans: {fmt_pul(bal)} so'm"
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("➕ Daromad", callback_data="BYANGI_daromad"),
            types.InlineKeyboardButton("➖ Rasxod", callback_data="BYANGI_rasxod"),
        )
        kb.add(types.InlineKeyboardButton("📊 Yo'nalish bo'yicha", callback_data="BYON_MENU"))
        kb.add(types.InlineKeyboardButton("📜 Oxirgi yozuvlar", callback_data="BTARIX"))
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("BYANGI_"))
    def cb_byangi(call):
        uid = call.from_user.id
        tur = call.data.replace("BYANGI_", "")
        astate[uid] = {"step": "budjet_yon", "btur": tur}
        kb = yonalishlar_kb("BYONSEL_")
        emoji = "💰" if tur == "daromad" else "💸"
        bot.send_message(call.message.chat.id, f"{emoji} Qaysi yo'nalish?", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("BYONSEL_"))
    def cb_byonsel(call):
        uid = call.from_user.id
        yid = int(call.data.replace("BYONSEL_", ""))
        st = astate.get(uid, {})
        st["yid"] = yid
        st["step"] = "budjet_summa"
        astate[uid] = st
        bot.send_message(call.message.chat.id, "💵 Summani yozing (faqat raqam, so'mda):")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "BYON_MENU")
    def cb_byon_menu(call):
        matn = "📊 YO'NALISH BO'YICHA BUDJET\n" + "━" * 25 + "\n\n"
        oy = datetime.now(_tz()).strftime("%m.%Y")
        for y in get_yonalishlar():
            x = budjet_xulosa(y["id"], oy)
            if x["daromad"] or x["rasxod"]:
                matn += f"{y['emoji']} {y['nomi']}:\n"
                matn += f"   💰 +{fmt_pul(x['daromad'])}  💸 -{fmt_pul(x['rasxod'])}\n"
                matn += f"   = {fmt_pul(x['balans'])} so'm\n\n"
        bot.send_message(call.message.chat.id, matn)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "BTARIX")
    def cb_btarix(call):
        yozuvlar = budjet_royxat(None, 15)
        matn = "📜 OXIRGI YOZUVLAR\n" + "━" * 20 + "\n\n"
        for b in yozuvlar:
            emoji = "💰" if b["tur"] == "daromad" else "💸"
            belgi = "+" if b["tur"] == "daromad" else "-"
            matn += f"{emoji} {belgi}{fmt_pul(b['summa'])} | {b['emoji']} {b['izoh'] or ''}\n   {b['sana']}\n"
        bot.send_message(call.message.chat.id, matn)
        bot.answer_callback_query(call.id)

    # ============ MUHIM SANALAR ============
    @bot.message_handler(func=lambda m: m.text == "🎂 Muhim sanalar" and faqat_ega(m.from_user.id))
    def h_sanalar(msg):
        sanalar = sanalar_royxat()
        matn = "🎂 MUHIM SANALAR\n" + "━" * 20 + "\n\n"
        if sanalar:
            for s in sanalar:
                takror = "🔁 yillik" if s["yillik"] else ""
                matn += f"📅 {s['sana']} — {s['nomi']} {takror}\n"
        else:
            matn += "Sana yo'q"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("➕ Yangi sana", callback_data="SYANGI"))
        if sanalar:
            kb.add(types.InlineKeyboardButton("🗑 O'chirish", callback_data="SOCHIR_MENU"))
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "SYANGI")
    def cb_syangi(call):
        uid = call.from_user.id
        astate[uid] = {"step": "sana_nomi"}
        bot.send_message(call.message.chat.id, "✏️ Nomi (masalan: Onamning tug'ilgan kuni):")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "SOCHIR_MENU")
    def cb_sochir_menu(call):
        sanalar = sanalar_royxat()
        kb = types.InlineKeyboardMarkup(row_width=1)
        for s in sanalar:
            kb.add(types.InlineKeyboardButton(f"🗑 {s['nomi'][:30]}", callback_data=f"SOCHIR_{s['id']}"))
        bot.send_message(call.message.chat.id, "Qaysi sanani o'chirish?", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("SOCHIR_") and c.data != "SOCHIR_MENU")
    def cb_sochir(call):
        sid = int(call.data.replace("SOCHIR_", ""))
        sana_ochir(sid)
        bot.edit_message_text("🗑 O'chirildi", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    # ============ AI SUHBAT ============
    @bot.message_handler(func=lambda m: m.text == "🧠 AI suhbat" and faqat_ega(m.from_user.id))
    def h_ai(msg):
        kb = yonalishlar_kb("AIYON_")
        bot.send_message(msg.chat.id,
            "🧠 Qaysi yo'nalishda suhbatlashamiz?\n(Har yo'nalish alohida xarakterga ega)",
            reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AIYON_"))
    def cb_aiyon(call):
        uid = call.from_user.id
        yid = int(call.data.replace("AIYON_", ""))
        y = get_yonalish(yid)
        astate[uid] = {"step": "ai_suhbat", "yid": yid}
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🗑 Suhbatni tozalash", callback_data=f"AITOZA_{yid}"))
        kb.add(types.InlineKeyboardButton("🔙 Chiqish", callback_data="AICHIQ"))
        bot.send_message(call.message.chat.id,
            f"{y['emoji']} {y['nomi']} yo'nalishi\n\nSavolingizni yozing, men shu yo'nalish bo'yicha yordam beraman.",
            reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("AITOZA_"))
    def cb_aitoza(call):
        yid = int(call.data.replace("AITOZA_", ""))
        ai_tarix_tozala(yid)
        bot.answer_callback_query(call.id, "Suhbat tozalandi 🗑")

    @bot.callback_query_handler(func=lambda c: c.data == "AICHIQ")
    def cb_aichiq(call):
        uid = call.from_user.id
        astate.pop(uid, None)
        bot.send_message(call.message.chat.id, "AI suhbatdan chiqdingiz.", reply_markup=bosh_menyu())
        bot.answer_callback_query(call.id)

    # ============ YO'NALISHLAR ============
    @bot.message_handler(func=lambda m: m.text == "📂 Yo'nalishlar" and faqat_ega(m.from_user.id))
    def h_yonalishlar(msg):
        matn = "📂 YO'NALISHLAR\n" + "━" * 20 + "\n\n"
        for y in get_yonalishlar():
            matn += f"{y['emoji']} {y['nomi']}\n"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("➕ Yangi yo'nalish", callback_data="YYANGI"))
        kb.add(types.InlineKeyboardButton("🗑 O'chirish", callback_data="YOCHIR_MENU"))
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "YYANGI")
    def cb_yyangi(call):
        uid = call.from_user.id
        astate[uid] = {"step": "yon_nomi"}
        bot.send_message(call.message.chat.id, "✏️ Yo'nalish nomi (masalan: Sport):")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "YOCHIR_MENU")
    def cb_yochir_menu(call):
        kb = types.InlineKeyboardMarkup(row_width=1)
        for y in get_yonalishlar():
            kb.add(types.InlineKeyboardButton(f"🗑 {y['emoji']} {y['nomi']}", callback_data=f"YOCHIR_{y['id']}"))
        bot.send_message(call.message.chat.id, "Qaysi yo'nalishni o'chirish?", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("YOCHIR_") and c.data != "YOCHIR_MENU")
    def cb_yochir(call):
        yid = int(call.data.replace("YOCHIR_", ""))
        yonalish_ochir(yid)
        bot.edit_message_text("🗑 Yo'nalish o'chirildi", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    # ============ MEN HAQIMDA (AI xotirasi) ============
    @bot.message_handler(func=lambda m: m.text == "👤 Men haqimda" and faqat_ega(m.from_user.id))
    def h_men_haqimda(msg):
        royxat = profil_ol(None)
        matn = "👤 MEN HAQIMDA\n" + "━" * 20 + "\n\n"
        matn += "AI shu ma'lumotlarni doim biladi:\n\n"
        if royxat:
            for p in royxat:
                if p["yonalish_id"]:
                    y = get_yonalish(p["yonalish_id"])
                    teg = f"{y['emoji']}" if y else ""
                else:
                    teg = "🌐"
                matn += f"{teg} {p['matn']}\n"
        else:
            matn += "Hali ma'lumot yo'q.\n\nMisol: 'Mening ismim Ali', 'Veganman', 'Har kuni 6:00 da turaman'"
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton("➕ Ma'lumot qo'shish", callback_data="PROF_QOSH"))
        if royxat:
            kb.add(types.InlineKeyboardButton("🗑 O'chirish", callback_data="PROF_OCHIR_MENU"))
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "PROF_QOSH")
    def cb_prof_qosh(call):
        kb = yonalishlar_kb("PROFYON_", [("🌐 Umumiy (hamma joyda)", "PROFYON_0")])
        bot.send_message(call.message.chat.id,
            "Bu ma'lumot qaysi yo'nalishga tegishli?\n(Umumiy = AI har doim biladi)",
            reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("PROFYON_"))
    def cb_profyon(call):
        uid = call.from_user.id
        yid = int(call.data.replace("PROFYON_", ""))
        astate[uid] = {"step": "profil_qosh", "yid": yid if yid else None}
        bot.send_message(call.message.chat.id,
            "✏️ Ma'lumotni yozing:\n(masalan: Mening ismim Ali, 3 ta farzandim bor)")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data == "PROF_OCHIR_MENU")
    def cb_prof_ochir_menu(call):
        royxat = profil_ol(None)
        kb = types.InlineKeyboardMarkup(row_width=1)
        for p in royxat:
            kb.add(types.InlineKeyboardButton(f"🗑 {p['matn'][:35]}", callback_data=f"PROFOCH_{p['id']}"))
        bot.send_message(call.message.chat.id, "Qaysi ma'lumotni o'chirish?", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("PROFOCH_"))
    def cb_profoch(call):
        pid = int(call.data.replace("PROFOCH_", ""))
        profil_ochir(pid)
        bot.edit_message_text("🗑 O'chirildi", call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    # ============ SOZLAMALAR ============
    @bot.message_handler(func=lambda m: m.text == "⚙️ Sozlamalar" and faqat_ega(m.from_user.id))
    def h_sozlamalar(msg):
        uid = msg.from_user.id
        joriy_tz = sozlama_ol("vaqt_zona", "Asia/Tashkent")
        # Joriy vaqtni ko'rsatish
        hozir = datetime.now(_tz()).strftime("%H:%M")
        tz_nomi = joriy_tz
        for nom, kod in VAQT_ZONALARI:
            if kod == joriy_tz:
                tz_nomi = nom
                break
        matn = ("⚙️ SOZLAMALAR\n" + "━" * 20 + "\n\n"
                f"🆔 Sizning ID: {uid}\n"
                f"🕐 Vaqt zonasi: {tz_nomi}\n"
                f"🕐 Hozirgi vaqt: {hozir}\n\n"
                "📌 Avtomatik xabarlar:\n"
                "• 07:00 — Ertalabki reja\n"
                "• 21:00 — Kun yakuni\n"
                "• Eslatmalar — belgilangan vaqtda\n"
                "• Muhim sanalar — oldindan")
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🌍 Vaqt zonasini o'zgartirish", callback_data="TZ_MENU"))
        bot.send_message(msg.chat.id, matn, reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: c.data == "TZ_MENU")
    def cb_tz_menu(call):
        kb = types.InlineKeyboardMarkup(row_width=1)
        for nom, kod in VAQT_ZONALARI:
            kb.add(types.InlineKeyboardButton(nom, callback_data=f"TZSET_{kod}"))
        bot.send_message(call.message.chat.id, "🌍 Vaqt zonasini tanlang:", reply_markup=kb)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda c: c.data.startswith("TZSET_"))
    def cb_tzset(call):
        kod = call.data.replace("TZSET_", "")
        sozlama_saqla("vaqt_zona", kod)
        nom = kod
        for n, k in VAQT_ZONALARI:
            if k == kod:
                nom = n
                break
        hozir = datetime.now(_tz()).strftime("%H:%M")
        bot.edit_message_text(
            f"✅ Vaqt zonasi o'zgartirildi!\n\n{nom}\n🕐 Hozirgi vaqt: {hozir}",
            call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, "Saqlandi!")

    # ============ MATN HANDLER (step machine) ============
    @bot.message_handler(func=lambda m: True, content_types=["text"])
    def h_matn(msg):
        uid = msg.from_user.id
        if not faqat_ega(uid):
            return
        text = msg.text.strip()
        st = astate.get(uid, {})
        step = st.get("step")

        # Bosh menyu tugmalari - skip
        menyu_btnlar = ["📋 Bugungi reja", "✅ Vazifalar", "⏰ Eslatmalar", "💰 Budjet",
                        "🎂 Muhim sanalar", "🧠 AI suhbat", "👤 Men haqimda",
                        "📂 Yo'nalishlar", "⚙️ Sozlamalar"]
        if text in menyu_btnlar:
            return

        # ----- VAZIFA -----
        if step == "vazifa_matn":
            st["matn"] = text
            st["step"] = "vazifa_ust"
            astate[uid] = st
            bot.send_message(msg.chat.id, "Ustuvorlik darajasi?", reply_markup=ustuvorlik_kb("VUST_"))
            return

        if step == "vazifa_muddat_qol":
            st["matn_muddat"] = text
            vazifa_qosh(st["yid"], st["matn"], text, st.get("ustuvorlik", "oddiy"))
            astate.pop(uid, None)
            bot.send_message(msg.chat.id, f"✅ Vazifa qo'shildi!\n📅 Muddat: {text}", reply_markup=bosh_menyu())
            return

        # ----- ESLATMA -----
        if step == "eslatma_matn":
            st["matn"] = text
            st["step"] = "eslatma_tur"
            astate[uid] = st
            bot.send_message(msg.chat.id, "Eslatma turi?", reply_markup=eslatma_tur_kb())
            return

        if step == "eslatma_vaqt":
            tur = st.get("tur", "bir_marta")
            # Vaqtni normalizatsiya qilish
            vaqt = text
            eslatma_qosh(st["yid"], st["matn"], vaqt, tur)
            astate.pop(uid, None)
            tur_nomi = {"bir_marta": "bir martalik", "har_kun": "har kuni", "har_hafta": "har hafta"}.get(tur, "")
            bot.send_message(msg.chat.id,
                f"✅ Eslatma qo'shildi!\n⏰ {st['matn']}\n🕐 {vaqt} ({tur_nomi})",
                reply_markup=bosh_menyu())
            return

        # ----- BUDJET -----
        if step == "budjet_summa":
            try:
                summa = float(text.replace(" ", "").replace(",", ""))
                st["summa"] = summa
                st["step"] = "budjet_izoh"
                astate[uid] = st
                bot.send_message(msg.chat.id, "📝 Izoh yozing (yoki '-' qo'ying):")
            except:
                bot.send_message(msg.chat.id, "⚠️ Faqat raqam yozing")
            return

        if step == "budjet_izoh":
            izoh = None if text == "-" else text
            budjet_qosh(st["yid"], st["btur"], st["summa"], izoh)
            astate.pop(uid, None)
            emoji = "💰" if st["btur"] == "daromad" else "💸"
            bot.send_message(msg.chat.id,
                f"{emoji} Saqlandi!\n{fmt_pul(st['summa'])} so'm" + (f"\n📝 {izoh}" if izoh else ""),
                reply_markup=bosh_menyu())
            return

        # ----- MUHIM SANA -----
        if step == "sana_nomi":
            st["nomi"] = text
            st["step"] = "sana_sana"
            astate[uid] = st
            bot.send_message(msg.chat.id, "📅 Sanani yozing (kun.oy.yil, masalan 18.04.1990):")
            return

        if step == "sana_sana":
            sana_qosh(st["nomi"], text, yillik=1, eslat_kun_oldin=3)
            astate.pop(uid, None)
            bot.send_message(msg.chat.id,
                f"🎂 Saqlandi!\n📅 {text} — {st['nomi']}\n\n3 kun oldin eslataman.",
                reply_markup=bosh_menyu())
            return

        # ----- YO'NALISH -----
        if step == "yon_nomi":
            st["nomi"] = text
            st["step"] = "yon_emoji"
            astate[uid] = st
            bot.send_message(msg.chat.id, "😀 Emoji yuboring (masalan 🏃):")
            return

        if step == "yon_emoji":
            st["emoji"] = text
            st["step"] = "yon_shaxs"
            astate[uid] = st
            bot.send_message(msg.chat.id,
                "🧠 AI bu yo'nalishda qanday yordam bersin? Qisqacha yozing.\n"
                "(masalan: Sport, mashqlar, ovqatlanish va motivatsiya bo'yicha yordam ber)")
            return

        if step == "yon_shaxs":
            yonalish_qosh(st["nomi"], st["emoji"], text)
            astate.pop(uid, None)
            bot.send_message(msg.chat.id,
                f"✅ Yangi yo'nalish qo'shildi!\n{st['emoji']} {st['nomi']}",
                reply_markup=bosh_menyu())
            return

        # ----- MEN HAQIMDA (profil qo'shish) -----
        if step == "profil_qosh":
            yid = st.get("yid")
            profil_qosh(text, yid)
            astate.pop(uid, None)
            joy = "umumiy" if not yid else get_yonalish(yid)["nomi"]
            bot.send_message(msg.chat.id,
                f"✅ Eslab qoldim! ({joy})\n\nEndi AI bu ma'lumotni doim biladi.",
                reply_markup=bosh_menyu())
            return

        # ----- AI SUHBAT -----
        if step == "ai_suhbat":
            yid = st["yid"]
            y = get_yonalish(yid)
            bot.send_chat_action(msg.chat.id, "typing")
            tarix = ai_tarix_ol(yid, 10)
            profil = profil_matn(yid)
            javob = ai_javob(y["ai_shaxsiyat"], text, tarix, profil)
            ai_tarix_qosh(yid, "user", text)
            ai_tarix_qosh(yid, "assistant", javob)
            bot.send_message(msg.chat.id, javob)
            return

        # ----- Hech qaysi step yo'q -> AI ga yuborish (Umumiy yo'nalish) -----
        if not step:
            yonalishlar = get_yonalishlar()
            if yonalishlar:
                yid = yonalishlar[0]["id"]  # Umumiy
                y = get_yonalish(yid)
                bot.send_chat_action(msg.chat.id, "typing")
                tarix = ai_tarix_ol(yid, 6)
                profil = profil_matn(yid)
                javob = ai_javob(y["ai_shaxsiyat"], text, tarix, profil)
                ai_tarix_qosh(yid, "user", text)
                ai_tarix_qosh(yid, "assistant", javob)
                bot.send_message(msg.chat.id, javob)
            return
