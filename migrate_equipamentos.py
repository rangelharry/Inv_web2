"""
Script para migrar equipamentos elétricos e manuais do SQLite para PostgreSQL
Complementa a migração anterior
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

def migrate_equipamentos_eletricos(sqlite_conn, postgres_conn):
    """Migra tabela equipamentos_eletricos"""
    try:
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        sqlite_cursor.execute("SELECT * FROM equipamentos_eletricos")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print("⚠️  Tabela equipamentos_eletricos está vazia")
            return
        
        for row in rows:
            postgres_cursor.execute("""
                INSERT INTO equipamentos_eletricos (
                    codigo, nome, categoria_id, marca, modelo, numero_serie, voltagem, potencia,
                    status, localizacao, obra_atual_id, responsavel_atual_id, valor_compra,
                    data_compra, data_garantia, fornecedor, nota_fiscal, observacoes,
                    historico_manutencao, proxima_manutencao, ativo, data_criacao, criado_por
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['codigo'], row['nome'], row['categoria_id'], row['marca'], row['modelo'],
                row['numero_serie'], row['voltagem'], row['potencia'], row['status'], row['localizacao'],
                row['obra_atual_id'], row['responsavel_atual_id'], row['valor_compra'], row['data_compra'],
                row['data_garantia'], row['fornecedor'], row['nota_fiscal'], row['observacoes'],
                row['historico_manutencao'], row['proxima_manutencao'], 
                bool(row['ativo']) if row['ativo'] is not None else True,
                row['data_criacao'], row['criado_por']
            ))
        
        postgres_conn.commit()
        print(f"✅ Migrados {len(rows)} registros da tabela equipamentos_eletricos")
        
    except Exception as e:
        print(f"❌ Erro ao migrar equipamentos_eletricos: {e}")
        postgres_conn.rollback()

def migrate_equipamentos_manuais(sqlite_conn, postgres_conn):
    """Migra tabela equipamentos_manuais"""
    try:
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
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
                row['codigo'], row['descricao'], row['tipo'], row['categoria_id'], row['quantitativo'],
                row['status'], row['estado'], row['marca'], row['localizacao'], row['obra_atual_id'],
                row['responsavel_atual_id'], row['valor'], row['data_compra'], row['loja'],
                row['observacoes'], bool(row['ativo']) if row['ativo'] is not None else True,
                row['data_criacao'], row['criado_por']
            ))
        
        postgres_conn.commit()
        print(f"✅ Migrados {len(rows)} registros da tabela equipamentos_manuais")
        
    except Exception as e:
        print(f"❌ Erro ao migrar equipamentos_manuais: {e}")
        postgres_conn.rollback()

def migrate_movimentacoes(sqlite_conn, postgres_conn):
    """Migra tabela movimentacoes"""
    try:
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        sqlite_cursor.execute("SELECT * FROM movimentacoes")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print("⚠️  Tabela movimentacoes está vazia")
            return
        
        for row in rows:
            postgres_cursor.execute("""
                INSERT INTO movimentacoes (
                    tipo, tipo_item, item_id, codigo_item, descricao_item, quantidade, unidade,
                    obra_origem_id, obra_destino_id, responsavel_origem_id, responsavel_destino_id,
                    valor_unitario, valor_total, motivo, observacoes, documento, data_movimentacao,
                    data_previsao_retorno, status, usuario_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['tipo'], row['tipo_item'], row['item_id'], row['codigo_item'], row['descricao_item'],
                row['quantidade'], row['unidade'], row['obra_origem_id'], row['obra_destino_id'],
                row['responsavel_origem_id'], row['responsavel_destino_id'], row['valor_unitario'],
                row['valor_total'], row['motivo'], row['observacoes'], row['documento'],
                row['data_movimentacao'], row['data_previsao_retorno'], row['status'], row['usuario_id']
            ))
        
        postgres_conn.commit()
        print(f"✅ Migrados {len(rows)} registros da tabela movimentacoes")
        
    except Exception as e:
        print(f"❌ Erro ao migrar movimentacoes: {e}")
        postgres_conn.rollback()

def migrate_logs_auditoria(sqlite_conn, postgres_conn):
    """Migra tabela logs_auditoria"""
    try:
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        # Verifica se a coluna 'detalhes' existe no SQLite
        sqlite_cursor.execute("PRAGMA table_info(logs_auditoria)")
        columns_info = sqlite_cursor.fetchall()
        columns = [col[1] for col in columns_info]
        
        if 'detalhes' in columns:
            # SQLite tem coluna 'detalhes', mas PostgreSQL não
            sqlite_cursor.execute("""
                SELECT usuario_id, usuario_nome, acao, modulo, item_tipo, item_id, item_codigo,
                       dados_anteriores, dados_novos, ip_address, user_agent, observacoes, data_acao
                FROM logs_auditoria
            """)
        else:
            sqlite_cursor.execute("SELECT * FROM logs_auditoria")
        
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print("⚠️  Tabela logs_auditoria está vazia")
            return
        
        for row in rows:
            postgres_cursor.execute("""
                INSERT INTO logs_auditoria (
                    usuario_id, usuario_nome, acao, modulo, item_tipo, item_id, item_codigo,
                    dados_anteriores, dados_novos, ip_address, user_agent, observacoes, data_acao
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['usuario_id'], row['usuario_nome'], row['acao'], row['modulo'],
                row['item_tipo'], row['item_id'], row['item_codigo'], row['dados_anteriores'],
                row['dados_novos'], row['ip_address'], row['user_agent'], row['observacoes'],
                row['data_acao']
            ))
        
        postgres_conn.commit()
        print(f"✅ Migrados {len(rows)} registros da tabela logs_auditoria")
        
    except Exception as e:
        print(f"❌ Erro ao migrar logs_auditoria: {e}")
        postgres_conn.rollback()

def migrate_sessoes(sqlite_conn, postgres_conn):
    """Migra tabela sessoes"""
    try:
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        sqlite_cursor.execute("SELECT * FROM sessoes")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print("⚠️  Tabela sessoes está vazia")
            return
        
        for row in rows:
            postgres_cursor.execute("""
                INSERT INTO sessoes (usuario_id, token, data_criacao, data_expiracao, ativo)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                row['usuario_id'], row['token'], row['data_criacao'], row['data_expiracao'],
                bool(row['ativo']) if row['ativo'] is not None else True
            ))
        
        postgres_conn.commit()
        print(f"✅ Migrados {len(rows)} registros da tabela sessoes")
        
    except Exception as e:
        print(f"❌ Erro ao migrar sessoes: {e}")
        postgres_conn.rollback()

def main():
    """Função principal para migrar equipamentos e dados complementares"""
    print("🔧 Migrando equipamentos e dados complementares")
    print("=" * 50)
    
    sqlite_conn = get_sqlite_connection()
    postgres_conn = get_postgres_connection()
    
    if not sqlite_conn or not postgres_conn:
        print("❌ Falha na conexão com os bancos")
        return
    
    try:
        print("\n⚡ Migrando equipamentos elétricos...")
        migrate_equipamentos_eletricos(sqlite_conn, postgres_conn)
        
        print("\n🔨 Migrando equipamentos manuais...")
        migrate_equipamentos_manuais(sqlite_conn, postgres_conn)
        
        print("\n📄 Migrando movimentações...")
        migrate_movimentacoes(sqlite_conn, postgres_conn)
        
        print("\n📋 Migrando logs de auditoria...")
        migrate_logs_auditoria(sqlite_conn, postgres_conn)
        
        print("\n🔐 Migrando sessões...")
        migrate_sessoes(sqlite_conn, postgres_conn)
        
        print("\n" + "=" * 50)
        print("🎉 MIGRAÇÃO COMPLEMENTAR CONCLUÍDA!")
        print("✅ Equipamentos e dados complementares migrados")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE A MIGRAÇÃO: {e}")
        
    finally:
        if sqlite_conn:
            sqlite_conn.close()
        if postgres_conn:
            postgres_conn.close()
        print("\n🔒 Conexões fechadas")

if __name__ == "__main__":
    main()