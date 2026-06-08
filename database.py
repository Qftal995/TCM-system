"""中药诊疗管理系统 — 数据库初始化与操作"""
import sqlite3
import os
import sys
import shutil
from datetime import date, timedelta

def _app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(_app_dir(), "data", "tcm.db")

def _bundled_db():
    """Path to the bundled database file (only valid when frozen)."""
    return os.path.join(sys._MEIPASS, "data", "tcm.db")

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn

def init_db(seed=True):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    if getattr(sys, 'frozen', False) and not os.path.exists(DB_PATH):
        shutil.copy2(_bundled_db(), DB_PATH)
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS herbs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            alias TEXT DEFAULT '',
            supplier TEXT DEFAULT '',
            purchase_price REAL DEFAULT 0,
            sell_price REAL DEFAULT 0,
            purchase_date TEXT DEFAULT '',
            shelf_life_days INTEGER DEFAULT 365,
            expiry_date TEXT DEFAULT '',
            stock_qty REAL DEFAULT 0,
            stock_warn_threshold REAL DEFAULT 5,
            expiry_warn_days INTEGER DEFAULT 30,
            created_at TEXT DEFAULT (date('now')),
            updated_at TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            age INTEGER DEFAULT 0,
            gender TEXT DEFAULT '',
            address TEXT DEFAULT '',
            condition TEXT DEFAULT '',
            created_at TEXT DEFAULT (date('now'))
        );

        CREATE TABLE IF NOT EXISTS formulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            category TEXT DEFAULT '',
            is_builtin INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS formula_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            formula_id INTEGER NOT NULL REFERENCES formulas(id),
            herb_id INTEGER NOT NULL REFERENCES herbs(id),
            default_grams REAL DEFAULT 9
        );

        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_no TEXT UNIQUE NOT NULL,
            patient_id INTEGER REFERENCES patients(id),
            formula_name TEXT DEFAULT '',
            diagnosis TEXT DEFAULT '',
            total_price REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS prescription_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_id INTEGER NOT NULL REFERENCES prescriptions(id),
            herb_id INTEGER NOT NULL REFERENCES herbs(id),
            herb_name TEXT DEFAULT '',
            actual_grams REAL DEFAULT 0,
            unit_price REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS stock_in_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            herb_id INTEGER NOT NULL REFERENCES herbs(id),
            herb_name TEXT DEFAULT '',
            supplier TEXT DEFAULT '',
            qty REAL DEFAULT 0,
            purchase_price REAL DEFAULT 0,
            purchase_date TEXT DEFAULT '',
            shelf_life_days INTEGER DEFAULT 365,
            expiry_date TEXT DEFAULT '',
            approver TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT DEFAULT ''
        );
    """)
    # ── Migrations ──
    migrations = [
        "ALTER TABLE patients ADD COLUMN monthly_no TEXT DEFAULT ''",
        "ALTER TABLE patients ADD COLUMN medical_record_no TEXT DEFAULT ''",
        "ALTER TABLE patients ADD COLUMN occupation TEXT DEFAULT ''",
        "ALTER TABLE patients ADD COLUMN visit_date TEXT DEFAULT ''",
        "ALTER TABLE patients ADD COLUMN diagnosis TEXT DEFAULT ''",
        "ALTER TABLE patients ADD COLUMN treatment TEXT DEFAULT ''",
        "ALTER TABLE prescriptions ADD COLUMN treatment TEXT DEFAULT ''",
        "ALTER TABLE herbs ADD COLUMN purchase_note TEXT DEFAULT ''",
        "ALTER TABLE herbs ADD COLUMN name2 TEXT DEFAULT ''",
    ]
    for sql in migrations:
        try:
            cur.execute(sql)
        except sqlite3.OperationalError:
            pass  # column already exists
    # Sync name2 for existing rows
    try:
        cur.execute("UPDATE herbs SET name2=name WHERE name2='' OR name2 IS NULL")
    except sqlite3.OperationalError:
        pass
    # Ensure default service_fee
    try:
        cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('service_fee','50')")
        cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('alert_expiry_months','3')")
        cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('alert_low_stock_kg','1.0')")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    if seed:
        seed_if_empty(conn)
    conn.close()

def seed_if_empty(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM herbs")
    if cur.fetchone()[0] > 0:
        return

    today = date.today().isoformat()

    # Seed herbs (18 条, 含同一药材不同药商)
    herbs_data = [
        ('黄芪','黄耆','同仁堂',58,0.85,'2026-04-15',730,'2028-04-14',25.0,5.0,30),
        ('当归','秦归','同仁堂',120,1.80,'2026-03-20',540,'2027-09-11',2.5,5.0,60),
        ('党参','潞党参','九州通',45,0.68,'2026-05-01',365,'2027-04-30',18.0,3.0,30),
        ('枸杞','枸杞子','康美药业',35,0.55,'2025-12-10',180,'2026-06-07',12.0,3.0,30),
        ('陈皮','橘皮','同仁堂',22,0.38,'2024-11-01',365,'2025-10-31',6.0,5.0,60),
        ('甘草','国老','九州通',18,0.30,'2026-04-20',1080,'2029-04-19',30.0,5.0,60),
        ('茯苓','云苓','康美药业',28,0.45,'2026-02-15',730,'2028-02-14',1.8,3.0,30),
        ('白术','于术','同仁堂',42,0.65,'2026-05-05',540,'2027-11-01',15.0,3.0,30),
        ('白芍','芍药','九州通',38,0.58,'2026-01-10',180,'2026-07-08',10.0,5.0,45),
        ('桂枝','桂心','同仁堂',15,0.25,'2024-08-20',365,'2025-08-20',8.0,5.0,30),
        ('黄连','川连','康美药业',95,1.40,'2026-04-01',540,'2027-09-26',20.0,5.0,60),
        ('麻黄','龙沙','九州通',20,0.32,'2026-05-10',365,'2027-05-09',0.8,3.0,30),
        ('柴胡','茈胡','同仁堂',55,0.80,'2026-04-10',540,'2027-10-04',14.0,5.0,60),
        ('杏仁','苦杏仁','康美药业',32,0.48,'2026-03-25',365,'2027-03-24',9.0,3.0,30),
        ('大黄','川军','九州通',25,0.38,'2026-01-18',730,'2028-01-17',11.0,5.0,60),
        ('黄芩','枯芩','同仁堂',48,0.72,'2026-04-25',730,'2028-04-24',16.0,5.0,60),
        ('黄芪','北芪','九州通',52,0.78,'2026-03-10',730,'2028-03-09',40.0,5.0,30),
        ('当归','西归','康美药业',115,1.75,'2026-02-28',540,'2027-08-22',15.0,5.0,60),
    ]
    cur.executemany(
        "INSERT INTO herbs(name,alias,supplier,purchase_price,sell_price,purchase_date,shelf_life_days,expiry_date,stock_qty,stock_warn_threshold,expiry_warn_days,purchase_note,name2) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [row + ("", row[0]) for row in herbs_data]
    )

    # Seed patients (5 条)
    patients_data = [
        ('张三','13800001111',45,'男','北京市朝阳区望京街道10号','风寒感冒，头痛发热','2026-05-01','2026-05-01'),
        ('李四','13900002222',32,'女','上海市浦东新区陆家嘴','脾胃虚弱，食欲不振','2026-05-05','2026-05-05'),
        ('王五','13700003333',58,'男','广州市天河区体育西路','腰膝酸软，失眠多梦','2026-05-10','2026-05-10'),
        ('赵六','13600004444',27,'女','成都市武侯区天府大道','经期不调，痛经','2026-05-12','2026-05-12'),
        ('孙七','13500005555',63,'男','武汉市洪山区珞喻路','慢性支气管炎，咳嗽痰多','2026-05-15','2026-05-15'),
    ]
    cur.executemany(
        "INSERT INTO patients(name,phone,age,gender,address,condition,visit_date,created_at) VALUES(?,?,?,?,?,?,?,?)",
        patients_data
    )

    # Seed formulas (9 条)
    formula_data = [
        ('麻黄汤','发汗解表，宣肺平喘','解表剂'),
        ('桂枝汤','解肌发表，调和营卫','解表剂'),
        ('小柴胡汤','和解少阳','和解剂'),
        ('四物汤','补血调血','补益剂'),
        ('四君子汤','益气健脾','补益剂'),
        ('六味地黄丸','滋阴补肾','补益剂'),
        ('逍遥散','疏肝解郁，养血健脾','和解剂'),
        ('补中益气汤','补中益气，升阳举陷','补益剂'),
        ('十全大补汤加味','气血双补，扶正固本，十六味大方','补益剂'),
    ]
    cur.executemany("INSERT INTO formulas(name,description,category) VALUES(?,?,?)", formula_data)

    # Formula items (herb_id references from seed order: 1=黄芪同仁堂, 2=当归同仁堂, ...)
    formula_items = [
        (1,12,9),(1,10,6),(1,6,3),(1,14,9),           # 麻黄汤
        (2,10,9),(2,9,9),(2,6,6),(2,14,9),             # 桂枝汤
        (3,13,12),(3,11,6),(3,3,9),(3,6,6),            # 小柴胡汤
        (4,2,9),(4,9,9),(4,1,12),(4,3,9),              # 四物汤
        (5,3,12),(5,8,9),(5,7,9),(5,6,6),              # 四君子汤
        (6,4,9),(6,7,9),(6,9,6),(6,13,6),              # 六味地黄丸
        (7,13,9),(7,2,9),(7,9,9),(7,8,9),              # 逍遥散
        (8,1,15),(8,3,9),(8,8,9),(8,6,6),              # 补中益气汤
        (9,1,15),(9,2,9),(9,3,12),(9,4,9),(9,5,6),(9,6,6),(9,7,9),(9,8,9),(9,9,9),(9,10,6),(9,11,3),(9,12,6),(9,13,6),(9,14,9),(9,15,3),(9,16,9),
    ]
    cur.executemany("INSERT INTO formula_items(formula_id,herb_id,default_grams) VALUES(?,?,?)", formula_items)

    # Seed prescriptions (2 条)
    cur.execute("INSERT INTO prescriptions(prescription_no,patient_id,formula_name,diagnosis,total_price,created_at) VALUES('CF-20260517-001',1,'麻黄汤','风寒感冒',9.60,'2026-05-17 10:30')")
    cur.execute("INSERT INTO prescriptions(prescription_no,patient_id,formula_name,diagnosis,total_price,created_at) VALUES('CF-20260517-002',2,'四君子汤','脾胃虚弱',19.86,'2026-05-17 14:00')")
    cur.executemany("INSERT INTO prescription_items(prescription_id,herb_id,herb_name,actual_grams,unit_price) VALUES(?,?,?,?,?)", [
        (1,12,'麻黄',9,0.32),(1,10,'桂枝',6,0.25),(1,6,'甘草',3,0.30),(1,14,'杏仁',9,0.48),
        (2,3,'党参',12,0.68),(2,8,'白术',9,0.65),(2,7,'茯苓',9,0.45),(2,6,'甘草',6,0.30),
    ])

    # Seed stock_in_records (2 条)
    cur.executemany("INSERT INTO stock_in_records(herb_id,herb_name,supplier,qty,purchase_price,purchase_date,shelf_life_days,expiry_date,approver,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)", [
        (1,'黄芪','同仁堂',10,55,'2026-05-10',730,'2028-05-09','张医师','approved','2026-05-17 09:00'),
        (7,'茯苓','康美药业',5,26,'2026-05-15',730,'2028-05-14','张医师','pending','2026-05-17 11:00'),
    ])

    conn.commit()
