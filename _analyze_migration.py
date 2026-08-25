import pathlib
import re

p = pathlib.Path(
    "backend/alembic/versions/c10ac2e075e7_final_schema_for_production.py"
)
lines = p.read_text(encoding="utf-8").splitlines()

sections = {"header": [], "upgrade": [], "downgrade": []}
current = "header"
for l in lines:
    if l.startswith("def upgrade"):
        current = "upgrade"
        continue
    if l.startswith("def downgrade"):
        current = "downgrade"
        continue
    sections[current].append(l)

for name, body in sections.items():
    ops = [l.strip() for l in body if re.search(r"op\.(drop|create|add|alter)", l)]
    drops = [o for o in ops if "drop_" in o]
    creates = [o for o in ops if "create_table" in o]
    print(f"{name}: {len(ops)} ops | {len(drops)} drops | {len(creates)} create_table")
    if name == "upgrade" and drops:
        for d in drops:
            print("   UPGRADE-DROP:", d)