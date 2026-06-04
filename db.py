import sqlite3
import os
from datetime import datetime, timedelta
import pytz
from config import STANDART_TZ, BOSHLANGICH_YONALISHLAR

def _tz():
    """Joriy vaqt zonasi (DB dan)"""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        r = conn.execute("SELECT qiymat FROM sozlama WHERE kalit='vaqt_zona'").fetchone()
        conn.close()
        nom = r["qiymat"] if r else STANDART_TZ
        return pytz.timezone(nom)
    except:
        return pytz.timezone(STANDART_TZ)

DB_PATH = os.environ.get("DB_PATH", "/data/hayot.db")


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def bugun_str():
    return datetime.now(_tz()).strftime("%d.%m.%Y")


def hozir_str():
    return datetime.now(_tz()).strftime("%d.%m.%Y %H:%M")


def init_db():
    # /data papkasi bo'lmasa lokal ishlatish
    if not os.path.exists("/data"):
        global DB_PATH
        DB_PATH = "hayot.db"

    conn = get_db()
    c = conn.cursor()

    # Yo'nalishlar (kontekstlar)
    c.execute("""CREATE TABLE IF NOT EXISTS yonalishlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nomi TEXT NOT NULL,
        emoji TEXT DEFAULT '📌',
        ai_shaxsiyat TEXT,
        tartib INTEGER DEFAULT 0,
        faol INTEGER DEFAULT 1
    )""")

    # Vazifalar
    c.execute("""CREATE TABLE IF NOT EXISTS vazifalar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        yonalish_id INTEGER,
        matn TEXT NOT NULL,
        muddat TEXT,
        ustuvorlik TEXT DEFAULT 'oddiy',
        holat TEXT DEFAULT 'faol',
        yaratilgan TEXT,
        bajarilgan TEXT
    )""")

    # Eslatmalar
    c.execute("""CREATE TABLE IF NOT EXISTS eslatmalar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        yonalish_id INTEGER,
        matn TEXT NOT NULL,
        vaqt TEXT,
        tur TEXT DEFAULT 'bir_marta',
        takror TEXT,
        keyingi_vaqt TEXT,
        faol INTEGER DEFAULT 1,
        yaratilgan TEXT
    )""")

    # Budjet
    c.execute("""CREATE TABLE IF NOT EXISTS budjet (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        yonalish_id INTEGER,
        tur TEXT NOT NULL,
        summa REAL NOT NULL,
        izoh TEXT,
        sana TEXT,
        yaratilgan TEXT
    )""")

    # Muhim sanalar (tug'ilgan kunlar, yubileylar)
    c.execute("""CREATE TABLE IF NOT EXISTS muhim_sanalar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nomi TEXT NOT NULL,
        sana TEXT NOT NULL,
        yillik INTEGER DEFAULT 1,
        eslat_kun_oldin INTEGER DEFAULT 3,
        izoh TEXT,
        yaratilgan TEXT
    )""")

    # Kunlik reja (AI tuzgan yoki o'zi yozgan)
    c.execute("""CREATE TABLE IF NOT EXISTS kunlik_reja (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sana TEXT NOT NULL,
        reja TEXT,
        yaratilgan TEXT
    )""")

    # AI suhbat tarixi (har yo'nalish uchun)
    c.execute("""CREATE TABLE IF NOT EXISTS ai_tarix (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        yonalish_id INTEGER,
        rol TEXT,
        matn TEXT,
        vaqt TEXT
    )""")

    # Sozlamalar
    c.execute("""CREATE TABLE IF NOT EXISTS sozlama (
        kalit TEXT PRIMARY KEY,
        qiymat TEXT
    )""")

    conn.commit()

    # Boshlang'ich yo'nalishlarni qo'shish (faqat bo'sh bo'lsa)
    mavjud = c.execute("SELECT COUNT(*) FROM yonalishlar").fetchone()[0]
    if mavjud == 0:
        for i, (nomi, emoji, shaxs) in enumerate(BOSHLANGICH_YONALISHLAR):
            c.execute(
                "INSERT INTO yonalishlar (nomi, emoji, ai_shaxsiyat, tartib) VALUES (?,?,?,?)",
                (nomi, emoji, shaxs, i))
        conn.commit()

    conn.close()


# ============ YO'NALISHLAR ============
def get_yonalishlar():
    conn = get_db()
    r = conn.execute("SELECT * FROM yonalishlar WHERE faol=1 ORDER BY tartib").fetchall()
    conn.close()
    return r


def get_yonalish(yid):
    conn = get_db()
    r = conn.execute("SELECT * FROM yonalishlar WHERE id=?", (yid,)).fetchone()
    conn.close()
    return r


def yonalish_qosh(nomi, emoji, shaxsiyat):
    conn = get_db()
    t = conn.execute("SELECT COALESCE(MAX(tartib),0)+1 FROM yonalishlar").fetchone()[0]
    conn.execute("INSERT INTO yonalishlar (nomi, emoji, ai_shaxsiyat, tartib) VALUES (?,?,?,?)",
                 (nomi, emoji, shaxsiyat, t))
    conn.commit()
    conn.close()


def yonalish_ochir(yid):
    conn = get_db()
    conn.execute("UPDATE yonalishlar SET faol=0 WHERE id=?", (yid,))
    conn.commit()
    conn.close()


# ============ VAZIFALAR ============
def vazifa_qosh(yonalish_id, matn, muddat=None, ustuvorlik="oddiy"):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO vazifalar (yonalish_id, matn, muddat, ustuvorlik, holat, yaratilgan) VALUES (?,?,?,?,'faol',?)",
        (yonalish_id, matn, muddat, ustuvorlik, hozir_str()))
    conn.commit()
    vid = cur.lastrowid
    conn.close()
    return vid


def vazifalar_royxat(yonalish_id=None, holat="faol"):
    conn = get_db()
    if yonalish_id:
        r = conn.execute(
            "SELECT v.*, y.emoji, y.nomi as yon_nomi FROM vazifalar v LEFT JOIN yonalishlar y ON v.yonalish_id=y.id WHERE v.yonalish_id=? AND v.holat=? ORDER BY CASE v.ustuvorlik WHEN 'muhim' THEN 1 WHEN 'orta' THEN 2 ELSE 3 END, v.muddat",
            (yonalish_id, holat)).fetchall()
    else:
        r = conn.execute(
            "SELECT v.*, y.emoji, y.nomi as yon_nomi FROM vazifalar v LEFT JOIN yonalishlar y ON v.yonalish_id=y.id WHERE v.holat=? ORDER BY CASE v.ustuvorlik WHEN 'muhim' THEN 1 WHEN 'orta' THEN 2 ELSE 3 END, v.muddat",
            (holat,)).fetchall()
    conn.close()
    return r


def vazifa_bajar(vid):
    conn = get_db()
    conn.execute("UPDATE vazifalar SET holat='bajarildi', bajarilgan=? WHERE id=?",
                 (hozir_str(), vid))
    conn.commit()
    conn.close()


def vazifa_ochir(vid):
    conn = get_db()
    conn.execute("DELETE FROM vazifalar WHERE id=?", (vid,))
    conn.commit()
    conn.close()


def bugungi_vazifalar():
    """Bugun muddati keladigan yoki muddatsiz faol vazifalar"""
    conn = get_db()
    bugun = bugun_str()
    r = conn.execute(
        "SELECT v.*, y.emoji, y.nomi as yon_nomi FROM vazifalar v LEFT JOIN yonalishlar y ON v.yonalish_id=y.id WHERE v.holat='faol' AND (v.muddat=? OR v.muddat IS NULL OR v.muddat='') ORDER BY CASE v.ustuvorlik WHEN 'muhim' THEN 1 WHEN 'orta' THEN 2 ELSE 3 END",
        (bugun,)).fetchall()
    conn.close()
    return r


# ============ ESLATMALAR ============
def eslatma_qosh(yonalish_id, matn, vaqt, tur="bir_marta", takror=None):
    conn = get_db()
    conn.execute(
        "INSERT INTO eslatmalar (yonalish_id, matn, vaqt, tur, takror, keyingi_vaqt, faol, yaratilgan) VALUES (?,?,?,?,?,?,1,?)",
        (yonalish_id, matn, vaqt, tur, takror, vaqt, hozir_str()))
    conn.commit()
    conn.close()


def eslatmalar_royxat(yonalish_id=None):
    conn = get_db()
    if yonalish_id:
        r = conn.execute(
            "SELECT e.*, y.emoji FROM eslatmalar e LEFT JOIN yonalishlar y ON e.yonalish_id=y.id WHERE e.yonalish_id=? AND e.faol=1 ORDER BY e.keyingi_vaqt",
            (yonalish_id,)).fetchall()
    else:
        r = conn.execute(
            "SELECT e.*, y.emoji FROM eslatmalar e LEFT JOIN yonalishlar y ON e.yonalish_id=y.id WHERE e.faol=1 ORDER BY e.keyingi_vaqt").fetchall()
    conn.close()
    return r


def eslatma_ochir(eid):
    conn = get_db()
    conn.execute("UPDATE eslatmalar SET faol=0 WHERE id=?", (eid,))
    conn.commit()
    conn.close()


# ============ BUDJET ============
def budjet_qosh(yonalish_id, tur, summa, izoh=None):
    conn = get_db()
    conn.execute(
        "INSERT INTO budjet (yonalish_id, tur, summa, izoh, sana, yaratilgan) VALUES (?,?,?,?,?,?)",
        (yonalish_id, tur, summa, izoh, bugun_str(), hozir_str()))
    conn.commit()
    conn.close()


def budjet_xulosa(yonalish_id=None, oy=None):
    """Daromad/rasxod xulosasi. oy = '06.2026' formatida"""
    conn = get_db()
    shart = "WHERE 1=1"
    params = []
    if yonalish_id:
        shart += " AND yonalish_id=?"
        params.append(yonalish_id)
    if oy:
        shart += " AND sana LIKE ?"
        params.append(f"%.{oy}")

    daromad = conn.execute(
        f"SELECT COALESCE(SUM(summa),0) FROM budjet {shart} AND tur='daromad'",
        params).fetchone()[0]
    rasxod = conn.execute(
        f"SELECT COALESCE(SUM(summa),0) FROM budjet {shart} AND tur='rasxod'",
        params).fetchone()[0]
    conn.close()
    return {"daromad": daromad, "rasxod": rasxod, "balans": daromad - rasxod}


def budjet_royxat(yonalish_id=None, limit=20):
    conn = get_db()
    if yonalish_id:
        r = conn.execute(
            "SELECT b.*, y.emoji, y.nomi as yon_nomi FROM budjet b LEFT JOIN yonalishlar y ON b.yonalish_id=y.id WHERE b.yonalish_id=? ORDER BY b.id DESC LIMIT ?",
            (yonalish_id, limit)).fetchall()
    else:
        r = conn.execute(
            "SELECT b.*, y.emoji, y.nomi as yon_nomi FROM budjet b LEFT JOIN yonalishlar y ON b.yonalish_id=y.id ORDER BY b.id DESC LIMIT ?",
            (limit,)).fetchall()
    conn.close()
    return r


# ============ MUHIM SANALAR ============
def sana_qosh(nomi, sana, yillik=1, eslat_kun_oldin=3, izoh=None):
    conn = get_db()
    conn.execute(
        "INSERT INTO muhim_sanalar (nomi, sana, yillik, eslat_kun_oldin, izoh, yaratilgan) VALUES (?,?,?,?,?,?)",
        (nomi, sana, yillik, eslat_kun_oldin, izoh, hozir_str()))
    conn.commit()
    conn.close()


def sanalar_royxat():
    conn = get_db()
    r = conn.execute("SELECT * FROM muhim_sanalar ORDER BY sana").fetchall()
    conn.close()
    return r


def sana_ochir(sid):
    conn = get_db()
    conn.execute("DELETE FROM muhim_sanalar WHERE id=?", (sid,))
    conn.commit()
    conn.close()


def yaqin_sanalar(kun=7):
    """Keyingi N kun ichidagi muhim sanalar"""
    conn = get_db()
    sanalar = conn.execute("SELECT * FROM muhim_sanalar").fetchall()
    conn.close()
    bugun = datetime.now(_tz()).date()
    natija = []
    for s in sanalar:
        try:
            d, m, y = s["sana"].split(".")
            # Bu yilgi sana
            bu_yil = datetime(bugun.year, int(m), int(d)).date()
            if bu_yil < bugun:
                bu_yil = datetime(bugun.year + 1, int(m), int(d)).date()
            farq = (bu_yil - bugun).days
            if 0 <= farq <= kun:
                natija.append({"sana_obj": s, "farq": farq, "keyingi": bu_yil})
        except:
            pass
    natija.sort(key=lambda x: x["farq"])
    return natija


# ============ KUNLIK REJA ============
def kunlik_reja_saqla(sana, reja):
    conn = get_db()
    mavjud = conn.execute("SELECT id FROM kunlik_reja WHERE sana=?", (sana,)).fetchone()
    if mavjud:
        conn.execute("UPDATE kunlik_reja SET reja=? WHERE sana=?", (reja, sana))
    else:
        conn.execute("INSERT INTO kunlik_reja (sana, reja, yaratilgan) VALUES (?,?,?)",
                     (sana, reja, hozir_str()))
    conn.commit()
    conn.close()


def kunlik_reja_ol(sana):
    conn = get_db()
    r = conn.execute("SELECT reja FROM kunlik_reja WHERE sana=?", (sana,)).fetchone()
    conn.close()
    return r["reja"] if r else None


# ============ AI TARIX ============
def ai_tarix_qosh(yonalish_id, rol, matn):
    conn = get_db()
    conn.execute("INSERT INTO ai_tarix (yonalish_id, rol, matn, vaqt) VALUES (?,?,?,?)",
                 (yonalish_id, rol, matn, hozir_str()))
    # Faqat oxirgi 20 ta xabarni saqlash (har yo'nalish uchun)
    conn.execute("""DELETE FROM ai_tarix WHERE id NOT IN (
        SELECT id FROM ai_tarix WHERE yonalish_id=? ORDER BY id DESC LIMIT 20
    ) AND yonalish_id=?""", (yonalish_id, yonalish_id))
    conn.commit()
    conn.close()


def ai_tarix_ol(yonalish_id, limit=10):
    conn = get_db()
    r = conn.execute(
        "SELECT rol, matn FROM ai_tarix WHERE yonalish_id=? ORDER BY id DESC LIMIT ?",
        (yonalish_id, limit)).fetchall()
    conn.close()
    return list(reversed(r))


def ai_tarix_tozala(yonalish_id):
    conn = get_db()
    conn.execute("DELETE FROM ai_tarix WHERE yonalish_id=?", (yonalish_id,))
    conn.commit()
    conn.close()


# ============ SOZLAMA ============
def sozlama_ol(kalit, default=None):
    conn = get_db()
    r = conn.execute("SELECT qiymat FROM sozlama WHERE kalit=?", (kalit,)).fetchone()
    conn.close()
    return r["qiymat"] if r else default


def sozlama_saqla(kalit, qiymat):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO sozlama (kalit, qiymat) VALUES (?,?)",
                 (kalit, str(qiymat)))
    conn.commit()
    conn.close()
