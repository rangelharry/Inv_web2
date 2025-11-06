import sqlite3

# Conectar ao database
conn = sqlite3.connect('inventory.db')
cursor = conn.cursor()

# Atualizar todos os códigos de MAN- para EM-
cursor.execute("UPDATE equipamentos_manuais SET codigo = REPLACE(codigo, 'MAN-', 'EM-') WHERE codigo LIKE 'MAN-%'")
affected = cursor.rowcount

# Commit das mudanças
conn.commit()
conn.close()

print(f'Atualizados {affected} equipamentos de MAN- para EM-')