#!/usr/bin/env python3
"""
Script para limpar todas as tabelas e recriar dados limpos
"""

import bcrypt
from database.connection import db

def clean_all_tables():
    """Limpa todas as tabelas na ordem correta"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        print("🗑️ Limpando todas as tabelas...")
        
        # Ordem correta para evitar violação de FK
        tables_order = [
            'sessoes',
            'logs_auditoria', 
            'movimentacoes',
            'equipamentos_eletricos',
            'equipamentos_manuais',
            'insumos',
            'usuarios',
            'categorias'
        ]
        
        for table in tables_order:
            try:
                cursor.execute(f"DELETE FROM {table}")
                print(f"   ✅ Tabela {table} limpa")
            except Exception as e:
                print(f"   ⚠️ Erro ao limpar {table}: {e}")
        
        conn.commit()
        print("✅ Todas as tabelas limpas!")
        
    except Exception as e:
        print(f"❌ Erro geral na limpeza: {e}")

def recreate_essential_data():
    """Recria dados essenciais"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        print("🔧 Recriando dados essenciais...")
        
        # 1. Criar categorias
        categorias = [
            ('Ferramentas', 'Ferramentas manuais e elétricas', 'manual', '#FF6B6B'),
            ('Eletrônicos', 'Equipamentos eletrônicos', 'eletrico', '#4ECDC4'),
            ('Materiais', 'Insumos e materiais diversos', 'insumo', '#45B7D1'),
            ('Segurança', 'Equipamentos de segurança', 'manual', '#96CEB4')
        ]
        
        for nome, desc, tipo, cor in categorias:
            cursor.execute("""
                INSERT INTO categorias (nome, descricao, tipo, cor)
                VALUES (%s, %s, %s, %s)
            """, (nome, desc, tipo, cor))
        
        print("   ✅ Categorias criadas")
        
        # 2. Criar usuários com hashes corretos
        # Admin
        admin_password = 'admin123'
        admin_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("""
            INSERT INTO usuarios (nome, email, password_hash, perfil, ativo, criado_em)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, ('Administrador', 'admin@inventario.com', admin_hash, 'admin', True))
        
        # Usuário teste
        teste_password = 'teste123'
        teste_hash = bcrypt.hashpw(teste_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("""
            INSERT INTO usuarios (nome, email, password_hash, perfil, ativo, criado_em)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, ('Usuário Teste', 'teste@admin.com.br', teste_hash, 'gestor', True))
        
        conn.commit()
        print("   ✅ Usuários criados com hashes corretos")
        
        # 3. Verificar criação
        cursor.execute("SELECT id, nome, email, perfil FROM usuarios")
        users = cursor.fetchall()
        
        print(f"\n📊 Usuários criados: {len(users)}")
        for user_id, nome, email, perfil in users:
            print(f"   • ID: {user_id} | {nome} ({email}) - {perfil}")
        
        # 4. Testar logins
        cursor.execute("SELECT email, password_hash FROM usuarios")
        users_auth = cursor.fetchall()
        
        test_credentials = [
            ('admin@inventario.com', 'admin123'),
            ('teste@admin.com.br', 'teste123')
        ]
        
        print("\n🔐 Testando autenticação:")
        for email, password in test_credentials:
            user_hash = next((h for e, h in users_auth if e == email), None)
            if user_hash and bcrypt.checkpw(password.encode('utf-8'), user_hash.encode('utf-8')):
                print(f"   ✅ {email}: Login OK")
            else:
                print(f"   ❌ {email}: Login FALHOU")
                
    except Exception as e:
        print(f"❌ Erro ao recriar dados: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔧 LIMPEZA COMPLETA E RECRIAÇÃO DO BANCO")
    print("=" * 60)
    
    clean_all_tables()
    print("\n" + "-" * 60)
    recreate_essential_data()
    
    print("\n" + "=" * 60)
    print("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
    print("\nCredenciais para login:")
    print("   🔑 Admin:")
    print("      Email: admin@inventario.com")
    print("      Senha: admin123")
    print("   🔑 Teste:")
    print("      Email: teste@admin.com.br") 
    print("      Senha: teste123")
    print("\n🌐 Acesse: http://localhost:8501")