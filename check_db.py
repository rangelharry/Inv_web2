import sqlite3
import os

# Verificar quais bancos existem
bancos = ['inventory.db', 'database/inventario.db']
for banco in bancos:
    if os.path.exists(banco):
        print(f"\n=== Verificando {banco} ===")
        conn = sqlite3.connect(banco)
        cursor = conn.cursor()
        
        # Listar todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print("Tabelas disponíveis:", tables)
        
        # Verificar se existe tabela equipamentos_eletricos
        if 'equipamentos_eletricos' in tables:
            cursor.execute("PRAGMA table_info(equipamentos_eletricos)")
            columns = cursor.fetchall()
            print("\nColunas da tabela equipamentos_eletricos:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM equipamentos_eletricos")
            count = cursor.fetchone()[0]
            print(f"\nNúmero de registros: {count}")
            
            if count > 0:
                cursor.execute("SELECT * FROM equipamentos_eletricos LIMIT 1")
                sample = cursor.fetchone()
                print(f"Exemplo de registro: {sample}")
        else:
            print("Tabela equipamentos_eletricos não existe!")
        
        conn.close()
    else:
        print(f"Banco {banco} não encontrado")