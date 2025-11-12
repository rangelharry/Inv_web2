"""
Script para testar se as movimentações estão sendo gravadas corretamente
"""
import os
import sys
sys.path.insert(0, r'e:\GITHUB\Inv_web2')

try:
    import psycopg2
    from database.connection_postgres import DatabaseConnection
    
    print("=== TESTE DE VERIFICAÇÃO DE MOVIMENTAÇÕES ===\n")
    
    # Conectar ao banco
    db = DatabaseConnection()
    conn = db.get_connection()
    
    if conn:
        cursor = conn.cursor()
        
        print("1. ESTRUTURA DA TABELA MOVIMENTAÇÕES:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'movimentacoes' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            print(f"   {col[0]}: {col[1]} ({col[2]})")
        
        print("\n2. ÚLTIMAS 5 MOVIMENTAÇÕES:")
        cursor.execute("""
            SELECT 
                id, tipo, quantidade,
                insumo_id, equipamento_eletrico_id, equipamento_manual_id,
                obra_origem_id, obra_destino_id,
                data_movimentacao, usuario_id,
                movimentacao_origem_id, tipo_movimentacao, motivo
            FROM movimentacoes 
            ORDER BY data_movimentacao DESC 
            LIMIT 5
        """)
        
        movs = cursor.fetchall()
        if movs:
            for i, mov in enumerate(movs):
                print(f"\n   Movimentação {i+1}:")
                print(f"     ID: {mov[0]}")
                print(f"     Tipo: {mov[1]}")
                print(f"     Quantidade: {mov[2]}")
                print(f"     Insumo ID: {mov[3]}")
                print(f"     Equipamento Elétrico ID: {mov[4]}")
                print(f"     Equipamento Manual ID: {mov[5]}")
                print(f"     Obra Origem ID: {mov[6]}")
                print(f"     Obra Destino ID: {mov[7]}")
                print(f"     Data: {mov[8]}")
                print(f"     Usuário ID: {mov[9]}")
                print(f"     Movimentação Origem ID: {mov[10]}")
                print(f"     Tipo Movimentação: {mov[11]}")
                print(f"     Motivo: {mov[12]}")
        else:
            print("   Nenhuma movimentação encontrada")
        
        print("\n3. ESTATÍSTICAS:")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(insumo_id) as com_insumo,
                COUNT(equipamento_eletrico_id) as com_eq_eletrico,
                COUNT(equipamento_manual_id) as com_eq_manual,
                COUNT(CASE WHEN insumo_id IS NULL AND equipamento_eletrico_id IS NULL AND equipamento_manual_id IS NULL THEN 1 END) as sem_item
            FROM movimentacoes
        """)
        
        stats = cursor.fetchone()
        print(f"   Total de movimentações: {stats[0]}")
        print(f"   Com insumo: {stats[1]}")
        print(f"   Com equipamento elétrico: {stats[2]}")
        print(f"   Com equipamento manual: {stats[3]}")
        print(f"   Sem item associado: {stats[4]}")
        
        cursor.close()
        conn.close()
        
    else:
        print("❌ Erro: Não foi possível conectar ao banco")
        
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
except Exception as e:
    print(f"❌ Erro geral: {e}")

print("\n=== FIM DO TESTE ===")