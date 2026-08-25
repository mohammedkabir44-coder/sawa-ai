import os, sys
os.chdir("C:\\whatsapp commerce\\backend")
sys.path.insert(0, "C:\\whatsapp commerce\\backend")

from app.core.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print("Tables:", sorted(tables))
print()

tables_to_check = [
    'sms_messages', 'whatsapp_templates', 'orders', 'whatsapp_campaigns',
    'order_items', 'whatsapp_recipients', 'whatsapp_messages', 'whatsapp_engagements'
]

for table in tables_to_check:
    columns = [c['name'] for c in inspector.get_columns(table)]
    indexes = inspector.get_indexes(table)
    print(f"\nTable: {table}")
    print(f"  Columns: {columns}")
    print(f"  Indexes: {[idx['name'] for idx in indexes]}")

wa_columns = [c['name'] for c in inspector.get_columns('whatsapp_accounts')]
wa_indexes = inspector.get_indexes('whatsapp_accounts')
print(f"\nTable: whatsapp_accounts")
print(f"  Columns: {wa_columns}")
print(f"  Indexes: {[idx['name'] for idx in wa_indexes]}")
