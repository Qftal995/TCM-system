"""Fix historical stock: deduct missing (doses-1) per prescription item."""
import sqlite3, os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tcm.db")
conn = sqlite3.connect(DB)
cur = conn.cursor()

# All prescriptions are doses=7, fee boundary at #36→#37
cur.execute("SELECT id, prescription_no, total_price FROM prescriptions ORDER BY id")
prescs = cur.fetchall()

fixes = []
for pid, pno, total in prescs:
    fee = 50 if pid <= 36 else 70
    cur.execute("SELECT herb_name, actual_grams, unit_price FROM prescription_items WHERE prescription_id=?", [pid])
    items = cur.fetchall()
    per_dose = sum(g * up for _, g, up in items)

    # total = per_dose * doses + fee
    doses = round((total - fee) / per_dose) if per_dose > 0 else 1

    for hname, grams, up in items:
        extra_kg = grams * (doses - 1) / 1000
        fixes.append((pid, pno, doses, hname, grams, extra_kg))

print(f"Prescriptions: {len(prescs)}")
print(f"Item corrections: {len(fixes)}")
print(f"All doses=7: {all(f[2] == 7 for f in fixes)}")

# Summary by herb
from collections import defaultdict
by_herb = defaultdict(float)
for _, _, _, hname, _, extra in fixes:
    by_herb[hname] += extra

print(f"\nAffected herbs: {len(by_herb)}")
print(f"Total extra deduction: {sum(f[5] for f in fixes):.3f} kg")

print("\nTop 20 herbs by correction:")
for name, kg in sorted(by_herb.items(), key=lambda x: -x[1])[:20]:
    print(f"  {name}: {kg:.3f} kg")

# Apply
print("\nApplying corrections...")
for pid, pno, doses, hname, grams, extra in fixes:
    cur.execute("UPDATE herbs SET stock_qty = MAX(0, stock_qty - ?) WHERE name=?", [extra, hname])

# Add doses column and update
try:
    cur.execute("ALTER TABLE prescriptions ADD COLUMN doses INTEGER DEFAULT 7")
except:
    pass
for pid, pno, doses, _, _, _ in fixes:
    cur.execute("UPDATE prescriptions SET doses=? WHERE id=?", [doses, pid])

conn.commit()
conn.close()
print("Done. Stock corrected, doses column added and populated.")
