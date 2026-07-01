"""
database.py — PostgreSQL version for Render deployment.
Falls back to SQLite for local development automatically.
"""

import os
import uuid
from datetime import datetime, timedelta

DATABASE_URL = os.environ.get("DATABASE_URL")

# ── Detect which database to use ──────────────────────────────────────────────
if DATABASE_URL:
    # PostgreSQL on Render
    import psycopg2
    import psycopg2.extras

    def get_connection():
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        return conn

    def _row_to_dict(row, cursor):
        cols = [desc[0] for desc in cursor.description]
        return dict(zip(cols, row))

    POSTGRES = True
else:
    # SQLite for local development
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "orders.db")

    def get_connection():
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    POSTGRES = False


# ── Table creation ─────────────────────────────────────────────────────────────

def setup_database():
    conn = get_connection()
    cur  = conn.cursor()

    if POSTGRES:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id               SERIAL PRIMARY KEY,
                order_id         TEXT UNIQUE NOT NULL,
                customer_name    TEXT NOT NULL,
                customer_email   TEXT NOT NULL,
                customer_phone   TEXT NOT NULL,
                product_name     TEXT NOT NULL,
                category         TEXT NOT NULL,
                brand            TEXT NOT NULL,
                model            TEXT NOT NULL,
                quantity         INTEGER NOT NULL,
                unit_price       REAL NOT NULL,
                total_price      REAL NOT NULL,
                order_date       TEXT NOT NULL,
                delivery_address TEXT NOT NULL,
                status           TEXT NOT NULL DEFAULT 'PENDING'
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id              SERIAL PRIMARY KEY,
                invoice_id      TEXT UNIQUE NOT NULL,
                order_id        TEXT NOT NULL,
                generated_at    TEXT NOT NULL,
                pdf_path        TEXT,
                status          TEXT NOT NULL DEFAULT 'AWAITING APPROVAL',
                approval_token  TEXT UNIQUE,
                boss_email      TEXT,
                your_email      TEXT,
                sent_at         TEXT,
                approved_at     TEXT,
                forwarded_at    TEXT,
                supplier_email  TEXT
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id         TEXT UNIQUE NOT NULL,
                customer_name    TEXT NOT NULL,
                customer_email   TEXT NOT NULL,
                customer_phone   TEXT NOT NULL,
                product_name     TEXT NOT NULL,
                category         TEXT NOT NULL,
                brand            TEXT NOT NULL,
                model            TEXT NOT NULL,
                quantity         INTEGER NOT NULL,
                unit_price       REAL NOT NULL,
                total_price      REAL NOT NULL,
                order_date       TEXT NOT NULL,
                delivery_address TEXT NOT NULL,
                status           TEXT NOT NULL DEFAULT 'PENDING'
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id      TEXT UNIQUE NOT NULL,
                order_id        TEXT NOT NULL,
                generated_at    TEXT NOT NULL,
                pdf_path        TEXT,
                status          TEXT NOT NULL DEFAULT 'AWAITING APPROVAL',
                approval_token  TEXT UNIQUE,
                boss_email      TEXT,
                your_email      TEXT,
                sent_at         TEXT,
                approved_at     TEXT,
                forwarded_at    TEXT,
                supplier_email  TEXT
            )
        """)

    conn.commit()
    conn.close()
    print("[DB] Tables ready.")


# ── Seed data ──────────────────────────────────────────────────────────────────

def seed_orders():
    conn = get_connection()
    cur  = conn.cursor()

    if POSTGRES:
        cur.execute("SELECT COUNT(*) FROM orders")
        count = cur.fetchone()[0]
    else:
        cur.execute("SELECT COUNT(*) FROM orders")
        count = cur.fetchone()[0]

    if count > 0:
        print("[DB] Already seeded.")
        conn.close()
        return

    base = datetime.now()
    rows = [
        ("ORD-001","Ahmed Khan",    "ahmed@gmail.com",  "0300-1234567","Samsung Galaxy S24",      "Smartphone",  "Samsung","Galaxy S24",       2,185000,370000,-17,"House 12, Block A, Gulshan, Karachi"),
        ("ORD-002","Sara Malik",    "sara@gmail.com",   "0311-2345678","iPhone 15 Pro",            "Smartphone",  "Apple",  "iPhone 15 Pro",    1,320000,320000,-16,"Flat 5, DHA Phase 2, Lahore"),
        ("ORD-003","Bilal Ahmed",   "bilal@gmail.com",  "0321-3456789","Samsung Galaxy Buds2 Pro", "Accessories","Samsung","Buds2 Pro",        3, 22000, 66000,-15,"Shop 7, Blue Area, Islamabad"),
        ("ORD-004","Fatima Noor",   "fatima@gmail.com", "0333-4567890","Xiaomi 14 Pro",            "Smartphone",  "Xiaomi", "14 Pro",           1,145000,145000,-14,"House 45, Johar Town, Lahore"),
        ("ORD-005","Usman Ali",     "usman@gmail.com",  "0345-5678901","OnePlus 12",               "Smartphone",  "OnePlus","12",               2,135000,270000,-13,"B-3, North Nazimabad, Karachi"),
        ("ORD-006","Hina Javed",    "hina@gmail.com",   "0301-6789012","Apple AirPods Pro 2",      "Accessories","Apple",  "AirPods Pro 2",    4, 58000,232000,-12,"House 88, G-10, Islamabad"),
        ("ORD-007","Tariq Mehmood", "tariq@gmail.com",  "0312-7890123","iPhone 14",                "Smartphone",  "Apple",  "iPhone 14",        1,195000,195000,-11,"Apartment 3, Clifton Block 9, Karachi"),
        ("ORD-008","Rida Hussain",  "rida@gmail.com",   "0322-8901234","Samsung 65W Charger",      "Accessories","Samsung","65W Charger",      5,  3500, 17500,-10,"House 22, Bahria Town, Rawalpindi"),
        ("ORD-009","Kashif Sultan", "kashif@gmail.com", "0334-9012345","Google Pixel 8 Pro",       "Smartphone",  "Google", "Pixel 8 Pro",      1,175000,175000, -9,"Plot 15, I-8, Islamabad"),
        ("ORD-010","Lubna Shah",    "lubna@gmail.com",  "0346-0123456","Anker 20000mAh Power Bank","Accessories","Anker",  "PowerCore 20000",  6,  8500, 51000, -8,"House 67, Model Town, Lahore"),
        ("ORD-011","Jawad Iqbal",   "jawad@gmail.com",  "0302-1234568","Vivo V30 Pro",             "Smartphone",  "Vivo",   "V30 Pro",          2, 92000,184000, -7,"Flat 12, Gulberg III, Lahore"),
        ("ORD-012","Sumera Baig",   "sumera@gmail.com", "0313-2345679","Xiaomi Redmi Note 13 Pro", "Smartphone",  "Xiaomi", "Redmi Note 13 Pro",3, 68000,204000, -6,"House 9, F-7, Islamabad"),
        ("ORD-013","Fahad Anwar",   "fahad@gmail.com",  "0323-3456780","Spigen iPhone 15 Case",    "Accessories","Spigen", "Tough Armor Case", 10,  2800, 28000, -5,"Shop 3, Tariq Road, Karachi"),
        ("ORD-014","Rabia Zulfiqar","rabia@gmail.com",  "0335-4567891","OPPO Reno 11 Pro",         "Smartphone",  "OPPO",   "Reno 11 Pro",      1, 89000, 89000, -4,"House 34, Cantt, Peshawar"),
        ("ORD-015","Adil Rehman",   "adil@gmail.com",   "0347-5678902","Baseus USB-C Hub 7-in-1",  "Accessories","Baseus", "USB-C Hub",        4,  5500, 22000, -3,"Flat 8, Bahria Town, Karachi"),
        ("ORD-016","Zahida Parveen","zahida@gmail.com", "0303-6789013","Samsung Galaxy A55",       "Smartphone",  "Samsung","Galaxy A55",       3, 75000,225000, -2,"House 56, Hayatabad, Peshawar"),
        ("ORD-017","Pervaiz Sultan","pervaiz@gmail.com","0314-7890124","Belkin 3-in-1 MagSafe",    "Accessories","Belkin", "MagSafe Charger",  2, 18500, 37000, -1,"House 101, Wapda Town, Lahore"),
        ("ORD-018","Mehnaz Waheed", "mehnaz@gmail.com", "0324-8901235","iPhone 15",                "Smartphone",  "Apple",  "iPhone 15",        2,245000,490000,  0,"Apartment 7, Zamzama, Karachi"),
    ]

    for r in rows:
        dt = (base + timedelta(days=r[11])).strftime("%Y-%m-%d %H:%M:%S")
        if POSTGRES:
            cur.execute("""
                INSERT INTO orders
                (order_id,customer_name,customer_email,customer_phone,
                 product_name,category,brand,model,
                 quantity,unit_price,total_price,order_date,delivery_address,status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'PENDING')
                ON CONFLICT (order_id) DO NOTHING
            """, (r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8],r[9],r[10],dt,r[12]))
        else:
            cur.execute("""
                INSERT OR IGNORE INTO orders
                (order_id,customer_name,customer_email,customer_phone,
                 product_name,category,brand,model,
                 quantity,unit_price,total_price,order_date,delivery_address,status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'PENDING')
            """, (r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8],r[9],r[10],dt,r[12]))

    conn.commit()
    conn.close()
    print("[DB] 18 orders seeded.")


# ── Read functions ─────────────────────────────────────────────────────────────

def fetch_all_orders():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY order_date DESC")
    rows = cur.fetchall()
    if POSTGRES:
        result = [_row_to_dict(r, cur) for r in rows]
    else:
        result = [dict(r) for r in rows]
    conn.close()
    return result


def fetch_order_by_id(order_id):
    conn = get_connection()
    cur  = conn.cursor()
    if POSTGRES:
        cur.execute("SELECT * FROM orders WHERE order_id=%s", (order_id,))
        row = cur.fetchone()
        result = _row_to_dict(row, cur) if row else None
    else:
        cur.execute("SELECT * FROM orders WHERE order_id=?", (order_id,))
        row = cur.fetchone()
        result = dict(row) if row else None
    conn.close()
    return result


def update_order_status(order_id, status):
    conn = get_connection()
    cur  = conn.cursor()
    if POSTGRES:
        cur.execute("UPDATE orders SET status=%s WHERE order_id=%s", (status, order_id))
    else:
        cur.execute("UPDATE orders SET status=? WHERE order_id=?", (status, order_id))
    conn.commit()
    conn.close()


def save_invoice_to_db(invoice_id, order_id, boss_email, your_email, token):
    conn = get_connection()
    cur  = conn.cursor()
    now  = datetime.now().isoformat()
    if POSTGRES:
        cur.execute("""
            INSERT INTO invoices
            (invoice_id,order_id,generated_at,status,approval_token,boss_email,your_email,sent_at)
            VALUES (%s,%s,%s,'AWAITING APPROVAL',%s,%s,%s,%s)
            ON CONFLICT (invoice_id) DO NOTHING
        """, (invoice_id, order_id, now, token, boss_email, your_email, now))
    else:
        cur.execute("""
            INSERT OR IGNORE INTO invoices
            (invoice_id,order_id,generated_at,status,approval_token,boss_email,your_email,sent_at)
            VALUES (?,?,'AWAITING APPROVAL',?,?,?,?,?)
        """, (invoice_id, order_id, now, token, boss_email, your_email, now))
    conn.commit()
    conn.close()


def fetch_all_invoices():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM invoices ORDER BY generated_at DESC")
    rows = cur.fetchall()
    if POSTGRES:
        result = [_row_to_dict(r, cur) for r in rows]
    else:
        result = [dict(r) for r in rows]
    conn.close()
    return result


def fetch_invoice_by_token(token):
    conn = get_connection()
    cur  = conn.cursor()
    if POSTGRES:
        cur.execute("SELECT * FROM invoices WHERE approval_token=%s", (token,))
        row = cur.fetchone()
        result = _row_to_dict(row, cur) if row else None
    else:
        cur.execute("SELECT * FROM invoices WHERE approval_token=?", (token,))
        row = cur.fetchone()
        result = dict(row) if row else None
    conn.close()
    return result


def update_invoice_status(invoice_id, status, extra_field=None, extra_value=None):
    conn = get_connection()
    cur  = conn.cursor()
    now  = datetime.now().isoformat()
    if extra_field:
        if POSTGRES:
            cur.execute(
                f"UPDATE invoices SET status=%s, {extra_field}=%s WHERE invoice_id=%s",
                (status, extra_value, invoice_id)
            )
        else:
            cur.execute(
                f"UPDATE invoices SET status=?, {extra_field}=? WHERE invoice_id=?",
                (status, extra_value, invoice_id)
            )
    else:
        if POSTGRES:
            cur.execute("UPDATE invoices SET status=%s WHERE invoice_id=%s", (status, invoice_id))
        else:
            cur.execute("UPDATE invoices SET status=? WHERE invoice_id=?", (status, invoice_id))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    if not POSTGRES:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print("Old DB deleted.")
    setup_database()
    seed_orders()
    orders = fetch_all_orders()
    print(f"\nTotal: {len(orders)} orders")
    for o in orders:
        print(f"  {o['order_id']} | {o['customer_name']:<16} | PKR {o['total_price']:>10,.0f} | {o['status']}")