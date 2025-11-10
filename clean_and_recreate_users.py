#!/usr/bin/env python3
"""
Script para limpar e recriar dados corrompidos do banco
"""

import bcrypt
from database.connection import db

def clean_and_recreate_users():
    """Limpa e recria a tabela de usuários"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        print("🗑️ Limpando dados corrompidos...")
        
        # Deletar todos os usuários
        cursor.execute("DELETE FROM usuarios")
        conn.commit()
        
        print("✅ Dados corrompidos removidos!")
        
        # Criar usuário admin com hash correto
        password = 'admin123'
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        print(f"🔐 Criando hash seguro: {password_hash[:30]}...")
        
        cursor.execute("""
            INSERT INTO usuarios (nome, email, password_hash, perfil, ativo, criado_em)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, ('Administrador', 'admin@inventario.com', password_hash, 'admin', True))
        
        conn.commit()
        
        print("✅ Usuário admin recriado com sucesso!")
        
        # Criar usuário teste também
        teste_password = 'teste123'
        teste_hash = bcrypt.hashpw(teste_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("""
            INSERT INTO usuarios (nome, email, password_hash, perfil, ativo, criado_em)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, ('Usuário Teste', 'teste@admin.com.br', teste_hash, 'gestor', True))
        
        conn.commit()
        
        print("✅ Usuário teste recriado com sucesso!")
        
        # Verificar usuários criados
        cursor.execute("SELECT id, nome, email, password_hash FROM usuarios")
        users = cursor.fetchall()
        
        print(f"\n📊 Usuários válidos criados: {len(users)}")
        for user_id, nome, email, password_hash in users:
            hash_status = "✅ Válido" if password_hash and password_hash.startswith('$2') else "❌ Inválido"
            print(f"   • ID: {user_id} | {nome} ({email}): {hash_status}")
        
        # Testar login admin
        test_password = 'admin123'
        admin_user = next((u for u in users if u[2] == 'admin@inventario.com'), None)
        if admin_user:
            admin_hash = admin_user[3]
            if bcrypt.checkpw(test_password.encode('utf-8'), admin_hash.encode('utf-8')):
                print("✅ Teste de login admin: SUCESSO")
            else:
                print("❌ Teste de login admin: FALHOU")
        
        # Testar login teste
        test_password2 = 'teste123'
        teste_user = next((u for u in users if u[2] == 'teste@admin.com.br'), None)
        if teste_user:
            teste_hash = teste_user[3]
            if bcrypt.checkpw(test_password2.encode('utf-8'), teste_hash.encode('utf-8')):
                print("✅ Teste de login teste: SUCESSO")
            else:
                print("❌ Teste de login teste: FALHOU")
                
    except Exception as e:
        print(f"❌ Erro ao recriar usuários: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔧 LIMPEZA E RECRIAÇÃO DE USUÁRIOS")
    print("=" * 50)
    
    clean_and_recreate_users()
    
    print("\n" + "=" * 50)
    print("✅ Processo concluído!")
    print("\nCredenciais válidas:")
    print("   👤 Admin:")
    print("      Email: admin@inventario.com")
    print("      Senha: admin123")
    print("   👤 Teste:")
    print("      Email: teste@admin.com.br")
    print("      Senha: teste123")