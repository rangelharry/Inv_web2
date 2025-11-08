#!/usr/bin/env python3
"""Script para testar dados do banco"""

from database.connection import db

def test_database():
    print("=== TESTE DO BANCO DE DADOS ===")
    
    try:
        conn = db.get_connection()
        print(f"Conexão obtida: {conn}")
        
        if conn and hasattr(conn, 'cursor'):
            cursor = conn.cursor()
            
            # Testar estrutura da tabela movimentacoes
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'movimentacoes' ORDER BY ordinal_position")
            columns = cursor.fetchall()
            print('\\nColunas da tabela movimentacoes:')
            for col in columns:
                print(f'  - {col["column_name"]}')
                
            # Testar dados de movimentacoes
            cursor.execute('SELECT COUNT(*) as total FROM movimentacoes')
            result = cursor.fetchone()
            print(f'\\nTotal de movimentações: {result["total"]}')
            
            if result["total"] > 0:
                cursor.execute('SELECT * FROM movimentacoes LIMIT 2')
                rows = cursor.fetchall()
                print('\\nExemplo de movimentação:')
                for row in rows:
                    print(f'  - Tipo: {row.get("tipo", "N/A")}, Data: {row.get("data_movimentacao", "N/A")}')
        else:
            print(f"Erro: conexão inválida - {conn}")
            
    except Exception as e:
        print(f'Erro: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database()