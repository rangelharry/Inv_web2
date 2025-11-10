from database.connection import db

conn = db.get_connection()
cursor = conn.cursor()

# Verificar colunas de equipamentos_eletricos
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='equipamentos_eletricos' AND (column_name LIKE '%vida%' OR column_name LIKE '%util%')")
cols_ee = cursor.fetchall()

print('Colunas vida/util em equipamentos_eletricos:')
for col in cols_ee:
    if isinstance(col, tuple):
        print(f'  - {col[0]}')
    elif isinstance(col, dict):
        print(f'  - {list(col.values())[0]}')

# Verificar colunas de equipamentos_manuais
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='equipamentos_manuais' AND (column_name LIKE '%vida%' OR column_name LIKE '%util%')")
cols_em = cursor.fetchall()

print('Colunas vida/util em equipamentos_manuais:')
for col in cols_em:
    if isinstance(col, tuple):
        print(f'  - {col[0]}')
    elif isinstance(col, dict):
        print(f'  - {list(col.values())[0]}')