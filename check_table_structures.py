"""
Verificação da estrutura das tabelas para otimização
"""

from database.connection import db

def check_table_structure():
    """Verifica estrutura de todas as tabelas principais"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        tables = ['insumos', 'equipamentos_eletricos', 'equipamentos_manuais', 'movimentacoes']
        
        for table in tables:
            print(f"\n=== Tabela: {table} ===")
            cursor.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table}' 
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            for col in columns:
                if isinstance(col, dict):
                    print(f"  - {col['column_name']} ({col['data_type']})")
                else:
                    print(f"  - {col[0]} ({col[1]})")
                
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    check_table_structure()