import sqlite3
import os

# Testar diferentes caminhos de banco
caminhos = [
    "database/inventario.db",
    "inventario.db", 
    "inventory.db"
]

for caminho in caminhos:
    if os.path.exists(caminho):
        print(f"Banco encontrado: {caminho}")
        conn = sqlite3.connect(caminho)
        cursor = conn.cursor()
        
        # Verificar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = cursor.fetchall()
        print(f"  Tabelas: {[t[0] for t in tabelas]}")
        
        # Verificar se equipamentos_manuais existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='equipamentos_manuais'")
        tem_eq_manuais = cursor.fetchone()
        print(f"  Tem equipamentos_manuais: {tem_eq_manuais is not None}")
        
        if tem_eq_manuais:
            cursor.execute("SELECT COUNT(*) FROM equipamentos_manuais")
            count = cursor.fetchone()[0]
            print(f"  Registros: {count}")
            
        conn.close()
        print()
    else:
        print(f"Não encontrado: {caminho}")