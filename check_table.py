import sys
sys.path.append('e:/GITHUB/Inv_web2')

from modules.database import get_connection

try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'insumos' ORDER BY ordinal_position")
    columns = cur.fetchall()
    
    print("Colunas da tabela insumos:")
    for col in columns:
        print(f"- {col[0]} ({col[1]})")
    
    conn.close()
except Exception as e:
    print(f"Erro: {e}")