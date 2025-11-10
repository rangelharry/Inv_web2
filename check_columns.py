from database.connection import db

conn = db.get_connection()
cursor = conn.cursor()
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='equipamentos_eletricos' ORDER BY ordinal_position")
cols = cursor.fetchall()

print('Colunas em equipamentos_eletricos:')
for col in cols:
    if isinstance(col, tuple):
        print(f'  - {col[0]}')
    elif isinstance(col, dict):
        print(f'  - {list(col.values())[0]}')
    else:
        print(f'  - {col}')