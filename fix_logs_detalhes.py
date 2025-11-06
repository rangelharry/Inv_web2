import sqlite3

# Caminho do banco de dados (ajuste se necessário)
db_path = 'database/inventario.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verifica se a coluna 'detalhes' já existe
cursor.execute("PRAGMA table_info(logs_auditoria)")
columns = [col[1] for col in cursor.fetchall()]

if 'detalhes' not in columns:
    cursor.execute("ALTER TABLE logs_auditoria ADD COLUMN detalhes TEXT")
    print("Coluna 'detalhes' adicionada com sucesso!")
else:
    print("Coluna 'detalhes' já existe.")

conn.commit()
conn.close()
print("Pronto!")
