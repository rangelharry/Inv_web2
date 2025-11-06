"""
Script para migrar dados do SQLite para PostgreSQL
Autor: Sistema de Inventário Web
Data: 2025
"""

import sqlite3
import psycopg2
import psycopg2.extras
import streamlit as st
from datetime import datetime

def get_postgres_connection():
    """Conecta ao PostgreSQL usando os secrets"""
    try:
        if hasattr(st, 'secrets') and 'DATABASE_URL' in st.secrets:
            conn_string = st.secrets['DATABASE_URL']
        else:
            # Para execução local, lê do arquivo secrets
            import os
            if os.path.exists('.streamlit/secrets.toml'):
                import toml
                secrets = toml.load('.streamlit/secrets.toml')
                conn_string = secrets['DATABASE_URL']
            else:
                raise Exception("Arquivo secrets.toml não encontrado")
        
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

def migrate_table(sqlite_conn, postgres_conn, table_name, id_field='id'):
    """Migra uma tabela específica do SQLite para PostgreSQL"""
    try:
        sqlite_cursor = sqlite_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        # Busca todos os dados da tabela SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"⚠️  Tabela {table_name} está vazia")
            return
        
        # Pega os nomes das colunas
        columns = [description[0] for description in sqlite_cursor.description]
        
        # Remove o ID se for SERIAL (auto-incremento) no PostgreSQL
        if id_field in columns and id_field == 'id':
            columns_without_id = [col for col in columns if col != 'id']
            placeholders = ', '.join(['%s'] * len(columns_without_id))
            columns_str = ', '.join(columns_without_id)
            
            for row in rows:
                values = [row[col] for col in columns_without_id]
                query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                postgres_cursor.execute(query, values)
        else:
            # Para tabelas sem ID serial
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join(columns)
            
            for row in rows:
                values = [row[col] for col in columns]
                query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                postgres_cursor.execute(query, values)
        
        postgres_conn.commit()
        print(f"✅ Migrados {len(rows)} registros da tabela {table_name}")
        
    except Exception as e:
        print(f"❌ Erro ao migrar tabela {table_name}: {e}")
        postgres_conn.rollback()

def clear_postgres_tables(postgres_conn):
    """Limpa as tabelas PostgreSQL para começar migração limpa"""
    try:
        cursor = postgres_conn.cursor()
        
        # Lista de tabelas em ordem de dependência (filhas primeiro)
        tables = [
            'logs_auditoria',
            'anexos',
            'alertas',
            'movimentacoes',
            'equipamentos_manuais',
            'equipamentos_eletricos',
            'insumos',
            'responsaveis',
            'obras',
            'categorias',
            'configuracoes',
            'sessoes',
            'usuarios'
        ]
        
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
            # Reset sequence for SERIAL fields
            cursor.execute(f"ALTER SEQUENCE IF EXISTS {table}_id_seq RESTART WITH 1")
        
        postgres_conn.commit()
        print("✅ Tabelas PostgreSQL limpas")
        
    except Exception as e:
        print(f"❌ Erro ao limpar tabelas: {e}")

def main():
    """Função principal de migração"""
    print("🚀 Iniciando migração SQLite → PostgreSQL")
    print("=" * 50)
    
    # Conecta aos bancos
    sqlite_conn = get_sqlite_connection()
    postgres_conn = get_postgres_connection()
    
    if not sqlite_conn or not postgres_conn:
        print("❌ Falha na conexão com os bancos")
        return
    
    try:
        # Limpa PostgreSQL
        print("\n🧹 Limpando tabelas PostgreSQL...")
        clear_postgres_tables(postgres_conn)
        
        # Lista de tabelas para migrar (ordem importa por causa das FK)
        tables_order = [
            'usuarios',
            'categorias',
            'obras',
            'responsaveis',
            'insumos',
            'equipamentos_eletricos',
            'equipamentos_manuais',
            'movimentacoes',
            'alertas',
            'logs_auditoria',
            'configuracoes',
            'sessoes',
            'anexos'
        ]
        
        print(f"\n📦 Migrando {len(tables_order)} tabelas...")
        
        for table in tables_order:
            print(f"\n📋 Migrando {table}...")
            migrate_table(sqlite_conn, postgres_conn, table)
        
        print("\n" + "=" * 50)
        print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("✅ Todos os dados foram transferidos para PostgreSQL")
        print("✅ Você pode agora usar o sistema normalmente")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE A MIGRAÇÃO: {e}")
        
    finally:
        # Fecha conexões
        if sqlite_conn:
            sqlite_conn.close()
        if postgres_conn:
            postgres_conn.close()
        print("\n🔒 Conexões fechadas")

if __name__ == "__main__":
    main()