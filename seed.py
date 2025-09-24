import json
from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///./policies.db", connect_args={"check_same_thread": False})

with open("seeds.json") as f:
    items = json.load(f)

with engine.begin() as conn:
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uniq_policy_number ON policies(number);"))
    for it in items:
        # UPSERT: ignorera om numret redan finns
        conn.execute(
            text("""
            INSERT OR IGNORE INTO policies (number, holder, premium, status)
            VALUES (:number, :holder, :premium, :status)
            """),
            it
        )
print(f"Seeded {len(items)} items (duplicates ignored).")
