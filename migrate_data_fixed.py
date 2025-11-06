"""
Script melhorado para migrar dados do SQLite para PostgreSQL
Corrige incompatibilidades de tipos entre os bancos
"""

import sqlite3
import psycopg2
import psycopg2.extras
import streamlit as st
from datetime import datetime
import toml

def get_postgres_connection():
    """Conecta ao PostgreSQL usando os secrets"""
    try:
        # Lê do arquivo secrets
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

def convert_value(value, column_name):
    """Converte valores do SQLite para PostgreSQL"""
    # Converte campos boolean (1/0 para true/false)
    if column_name in ['ativo', 'lido'] and value is not None:
        return bool(value)
    
    # Mantém outros valores como estão
    return value

def migrate_usuarios(sqlite_conn, postgres_conn):
    """Migra tabela usuarios com conversão de tipos"""
    try:
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        sqlite_cursor.execute("SELECT * FROM usuarios")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print("⚠️  Tabela usuarios está vazia")
            return
        
        for row in rows:
            postgres_cursor.execute("""
                INSERT INTO usuarios (nome, email, password_hash, perfil, ativo, data_criacao, ultimo_login)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                row['nome'],
                row['email'], 
                row['password_hash'],
                row['perfil'],
                bool(row['ativo']) if row['ativo'] is not None else True,
                row['data_criacao'],
                row['ultimo_login']
            ))
        
        postgres_conn.commit()
        print(f"✅ Migrados {len(rows)} registros da tabela usuarios")
        
    except Exception as e:
        print(f"❌ Erro ao migrar usuarios: {e}")
        postgres_conn.rollback()

def migrate_categorias(sqlite_conn, postgres_conn):
    """Migra tabela categorias"""
    try:
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        sqlite_cursor.execute("SELECT * FROM categorias")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print("⚠️  Tabela categorias está vazia")
            return
        
        for row in rows:
            postgres_cursor.execute("""
                INSERT INTO categorias (nome, descricao, tipo, cor, ativo, data_criacao)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                row['nome'],
                row['descricao'],
                row['tipo'],
                row['cor'],
                bool(row['ativo']) if row['ativo'] is not None else True,
                row['data_criacao']
            ))
        
        postgres_conn.commit()
        print(f"✅ Migrados {len(rows)} registros da tabela categorias")
        
    except Exception as e:
        print(f"❌ Erro ao migrar categorias: {e}")
        postgres_conn.rollback()

def migrate_obras(sqlite_conn, postgres_conn):
    """Migra tabela obras"""
    try:
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        sqlite_cursor.execute("SELECT * FROM obras")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print("⚠️  Tabela obras está vazia")
            return
        
        for row in rows:
            postgres_cursor.execute("""
                INSERT INTO obras (codigo, nome, endereco, cidade, estado, cep, status, responsavel, 
                                 telefone, email, observacoes, data_inicio, data_previsao, data_conclusao,
                                 valor_orcado, valor_gasto, data_criacao, criado_por)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['codigo'], row['nome'], row['endereco'], row['cidade'], row['estado'], row['cep'],
                row['status'], row['responsavel'], row['telefone'], row['email'], row['observacoes'],
                row['data_inicio'], row['data_previsao'], row['data_conclusao'], row['valor_orcado'],
                row['valor_gasto'], row['data_criacao'], row['criado_por']
            ))
        
        postgres_conn.commit()
        print(f"✅ Migrados {len(rows)} registros da tabela obras")
        
    except Exception as e:
        print(f"❌ Erro ao migrar obras: {e}")
        postgres_conn.rollback()

def migrate_responsaveis(sqlite_conn, postgres_conn):
    """Migra tabela responsaveis"""
    try:
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        sqlite_cursor.execute("SELECT * FROM responsaveis")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print("⚠️  Tabela responsaveis está vazia")
            return
        
        for row in rows:
            postgres_cursor.execute("""
                INSERT INTO responsaveis (codigo, nome, cpf, telefone, email, cargo, departamento,
                                        obra_id, ativo, observacoes, data_admissao, data_demissao,
                                        data_criacao, criado_por)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['codigo'], row['nome'], row['cpf'], row['telefone'], row['email'], row['cargo'],
                row['departamento'], row['obra_id'], bool(row['ativo']) if row['ativo'] is not None else True,
                row['observacoes'], row['data_admissao'], row['data_demissao'], row['data_criacao'], row['criado_por']
            ))
        
        postgres_conn.commit()
        print(f"✅ Migrados {len(rows)} registros da tabela responsaveis")
        
    except Exception as e:
        print(f"❌ Erro ao migrar responsaveis: {e}")
        postgres_conn.rollback()

def migrate_insumos(sqlite_conn, postgres_conn):
    """Migra tabela insumos"""
    try:
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        sqlite_cursor.execute("SELECT * FROM insumos")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print("⚠️  Tabela insumos está vazia")
            return
        
        for row in rows:
            postgres_cursor.execute("""
                INSERT INTO insumos (codigo, descricao, categoria_id, unidade, quantidade_atual,
                                   quantidade_minima, preco_unitario, preco_ultima_compra, fornecedor,
                                   marca, localizacao, observacoes, status_validade, data_validade,
                                   data_ultima_entrada, data_ultima_saida, ativo, data_criacao, criado_por)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['codigo'], row['descricao'], row['categoria_id'], row['unidade'], row['quantidade_atual'],
                row['quantidade_minima'], row['preco_unitario'], row['preco_ultima_compra'], row['fornecedor'],
                row['marca'], row['localizacao'], row['observacoes'], row['status_validade'], row['data_validade'],
                row['data_ultima_entrada'], row['data_ultima_saida'], bool(row['ativo']) if row['ativo'] is not None else True,
                row['data_criacao'], row['criado_por']
            ))
        
        postgres_conn.commit()
        print(f"✅ Migrados {len(rows)} registros da tabela insumos")
        
    except Exception as e:
        print(f"❌ Erro ao migrar insumos: {e}")
        postgres_conn.rollback()

def clear_postgres_tables(postgres_conn):
    """Limpa as tabelas PostgreSQL"""
    try:
        cursor = postgres_conn.cursor()
        
        tables = [
            'logs_auditoria', 'anexos', 'alertas', 'movimentacoes',
            'equipamentos_manuais', 'equipamentos_eletricos', 'insumos',
            'responsaveis', 'obras', 'categorias', 'configuracoes', 'sessoes', 'usuarios'
        ]
        
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
            cursor.execute(f"ALTER SEQUENCE IF EXISTS {table}_id_seq RESTART WITH 1")
        
        postgres_conn.commit()
        print("✅ Tabelas PostgreSQL limpas")
        
    except Exception as e:
        print(f"❌ Erro ao limpar tabelas: {e}")

def main():
    """Função principal de migração"""
    print("🚀 Iniciando migração SQLite → PostgreSQL (versão melhorada)")
    print("=" * 60)
    
    sqlite_conn = get_sqlite_connection()
    postgres_conn = get_postgres_connection()
    
    if not sqlite_conn or not postgres_conn:
        print("❌ Falha na conexão com os bancos")
        return
    
    try:
        print("\n🧹 Limpando tabelas PostgreSQL...")
        clear_postgres_tables(postgres_conn)
        
        print("\n📦 Migrando tabelas principais...")
        
        # Migra em ordem de dependência
        migrate_usuarios(sqlite_conn, postgres_conn)
        migrate_categorias(sqlite_conn, postgres_conn)
        migrate_obras(sqlite_conn, postgres_conn)
        migrate_responsaveis(sqlite_conn, postgres_conn)
        migrate_insumos(sqlite_conn, postgres_conn)
        
        print("\n" + "=" * 60)
        print("🎉 MIGRAÇÃO PRINCIPAL CONCLUÍDA!")
        print("✅ Dados principais transferidos para PostgreSQL")
        print("📝 Execute novamente o sistema para verificar o funcionamento")
        
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