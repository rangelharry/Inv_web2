"""
Script final para corrigir os equipamentos manuais
Trata valores inválidos como "-" em campos numéricos
"""

import sqlite3
import psycopg2
import psycopg2.extras
import toml

def get_postgres_connection():
    """Conecta ao PostgreSQL usando os secrets"""
    try:
        secrets = toml.load('.streamlit/secrets.toml')
        conn_string = secrets['DATABASE_URL']
        
        conn = psycopg2.connect(
            conn_string,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        print("✅ Conectado ao PostgreSQL")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar PostgreSQL: {e}")
        return None

def get_sqlite_connection():
    """Conecta ao SQLite antigo"""
    try:
        conn = sqlite3.connect('database/inventario_backup.db')
        conn.row_factory = sqlite3.Row
        print("✅ Conectado ao SQLite")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar SQLite: {e}")
        return None

def clean_numeric_value(value):
    """Limpa valores numéricos, convertendo "-" e valores inválidos para None"""
    if value is None or value == "" or value == "-":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def migrate_equipamentos_manuais_fixed(sqlite_conn, postgres_conn):
    """Migra tabela equipamentos_manuais com correção de valores numéricos"""
    try:
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        # Limpa a tabela primeiro
        postgres_cursor.execute("DELETE FROM equipamentos_manuais")
        postgres_cursor.execute("ALTER SEQUENCE equipamentos_manuais_id_seq RESTART WITH 1")
        
        sqlite_cursor.execute("SELECT * FROM equipamentos_manuais")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print("⚠️  Tabela equipamentos_manuais está vazia")
            return
        
        for row in rows:
            postgres_cursor.execute("""
                INSERT INTO equipamentos_manuais (
                    codigo, descricao, tipo, categoria_id, quantitativo, status, estado,
                    marca, localizacao, obra_atual_id, responsavel_atual_id, valor,
                    data_compra, loja, observacoes, ativo, data_criacao, criado_por
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['codigo'], 
                row['descricao'], 
                row['tipo'], 
                row['categoria_id'], 
                row['quantitativo'], 
                row['status'], 
                row['estado'], 
                row['marca'], 
                row['localizacao'], 
                row['obra_atual_id'],
                row['responsavel_atual_id'], 
                clean_numeric_value(row['valor']),  # Limpa valores numéricos
                row['data_compra'], 
                row['loja'],
                row['observacoes'], 
                bool(row['ativo']) if row['ativo'] is not None else True,
                row['data_criacao'], 
                row['criado_por']
            ))
        
        postgres_conn.commit()
        print(f"✅ Migrados {len(rows)} registros da tabela equipamentos_manuais (corrigido)")
        
    except Exception as e:
        print(f"❌ Erro ao migrar equipamentos_manuais: {e}")
        postgres_conn.rollback()

def main():
    """Função principal para corrigir equipamentos manuais"""
    print("🔧 Corrigindo migração dos equipamentos manuais")
    print("=" * 50)
    
    sqlite_conn = get_sqlite_connection()
    postgres_conn = get_postgres_connection()
    
    if not sqlite_conn or not postgres_conn:
        print("❌ Falha na conexão com os bancos")
        return
    
    try:
        print("\n🔨 Migrando equipamentos manuais (versão corrigida)...")
        migrate_equipamentos_manuais_fixed(sqlite_conn, postgres_conn)
        
        print("\n" + "=" * 50)
        print("🎉 CORREÇÃO CONCLUÍDA!")
        print("✅ Equipamentos manuais migrados com valores corrigidos")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE A CORREÇÃO: {e}")
        
    finally:
        if sqlite_conn:
            sqlite_conn.close()
        if postgres_conn:
            postgres_conn.close()
        print("\n🔒 Conexões fechadas")

if __name__ == "__main__":
    main()