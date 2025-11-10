from database.connection import db

try:
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'equipamentos_eletricos' ORDER BY ordinal_position")
    cols = cur.fetchall()
    print("Colunas da tabela equipamentos_eletricos:")
    for col in cols:
        if isinstance(col, tuple):
            print(f"- {col[0]}")
        else:
            print(f"- {col}")
except Exception as e:
    print(f"Erro: {e}")