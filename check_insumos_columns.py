from database.connection import db

conn = db.get_connection()
cursor = conn.cursor()

# Verificar todas as colunas da tabela insumos
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='insumos' ORDER BY ordinal_position")
cols = cursor.fetchall()

print('Todas as colunas da tabela insumos:')
for col in cols:
    if isinstance(col, tuple):
        print(f'  - {col[0]}')
    elif isinstance(col, dict):
        print(f'  - {list(col.values())[0]}')

# Verificar especificamente por colunas de vencimento/validade
print('\nBuscando colunas relacionadas a vencimento/validade:')
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='insumos' AND (column_name LIKE '%venc%' OR column_name LIKE '%valid%')")
venc_cols = cursor.fetchall()

if venc_cols:
    for col in venc_cols:
        if isinstance(col, tuple):
            print(f'  - {col[0]}')
        elif isinstance(col, dict):
            print(f'  - {list(col.values())[0]}')
else:
    print('  - Nenhuma coluna de vencimento encontrada')