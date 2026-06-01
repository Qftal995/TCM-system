"""数据备份恢复工具 — JSON 格式"""
from database import get_conn


def export_json():
    """导出全部表数据为 dict"""
    conn = get_conn()
    cur = conn.cursor()
    tables = ["herbs", "patients", "formulas", "formula_items", "prescriptions", "prescription_items", "stock_in_records"]
    data = {}
    for t in tables:
        cur.execute(f"SELECT * FROM {t}")
        rows = cur.fetchall()
        data[t] = [dict(r) for r in rows]
    conn.close()
    return {"version": 1, "exported_at": __import__("datetime").datetime.now().isoformat(), "tables": data}


def import_json(data):
    """从 dict 恢复数据 — 按表先删后插（保留自增 ID），事务包裹"""
    ver = data.get("version", 0)
    if ver > 1:
        raise ValueError(f"备份文件版本 {ver} 高于当前支持的版本 1，无法恢复")

    tables_data = data.get("tables", data)
    required_tables = ["herbs", "patients", "formulas", "formula_items", "prescriptions", "prescription_items", "stock_in_records"]
    for t in required_tables:
        if t not in tables_data:
            raise ValueError(f"备份文件缺少关键表: {t}")

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA foreign_keys=OFF")
        cur.execute("BEGIN")

        for t in required_tables:
            rows = tables_data.get(t, [])
            cur.execute(f"DELETE FROM {t}")
            if not rows:
                continue
            cols = list(rows[0].keys())
            placeholders = ",".join(["?"] * len(cols))
            colnames = ",".join(cols)
            for r in rows:
                cur.execute(f"INSERT INTO {t}({colnames}) VALUES({placeholders})", [r.get(c) for c in cols])

        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA foreign_key_check")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
