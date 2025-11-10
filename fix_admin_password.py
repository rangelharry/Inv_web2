#!/usr/bin/env python3
"""
Script para corrigir hash de senha do usuário admin
"""

import bcrypt
from database.connection import db

def fix_admin_password():
    """Corrige o hash da senha do usuário admin"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Buscar usuário admin
        cursor.execute("SELECT id, email, password_hash FROM usuarios WHERE email = 'admin@inventario.com'")
        admin = cursor.fetchone()
        
        if not admin:
            # Criar usuário admin se não existir
            password = 'admin123'
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute("""
                INSERT INTO usuarios (nome, email, password_hash, perfil, ativo)
                VALUES (%s, %s, %s, %s, %s)
            """, ('Administrador', 'admin@inventario.com', password_hash, 'admin', True))
            conn.commit()
            print("✅ Usuário admin criado com sucesso!")
            print("   Email: admin@inventario.com")
            print("   Senha: admin123")
            return
        
        admin_id, email, current_hash = admin
        
        # Verificar se o hash está correto
        if not current_hash or not current_hash.startswith('$2'):
            print(f"⚠️  Hash inválido detectado para {email}")
            print(f"   Hash atual: {current_hash[:30] if current_hash else 'None'}...")
            
            # Recriar hash correto
            password = 'admin123'
            new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute("""
                UPDATE usuarios 
                SET password_hash = %s 
                WHERE id = %s
            """, (new_hash, admin_id))
            conn.commit()
            
            print("✅ Hash corrigido com sucesso!")
            print(f"   Novo hash: {new_hash[:30]}...")
        else:
            print("✅ Hash do usuário admin está correto!")
            
        # Testar login
        test_password = 'admin123'
        if bcrypt.checkpw(test_password.encode('utf-8'), current_hash.encode('utf-8') if current_hash else b''):
            print("✅ Teste de login: SUCESSO")
        else:
            print("❌ Teste de login: FALHOU")
            
    except Exception as e:
        print(f"❌ Erro ao corrigir senha admin: {e}")

def check_all_users():
    """Verifica todos os usuários do sistema"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, nome, email, password_hash FROM usuarios")
        users = cursor.fetchall()
        
        print(f"\n📊 Total de usuários: {len(users)}")
        
        for user_id, nome, email, password_hash in users:
            hash_status = "✅ Válido" if password_hash and password_hash.startswith('$2') else "❌ Inválido"
            print(f"   • {nome} ({email}): {hash_status}")
            
            if not password_hash or not password_hash.startswith('$2'):
                print(f"     Hash problemático: {password_hash[:30] if password_hash else 'None'}...")
                
    except Exception as e:
        print(f"❌ Erro ao verificar usuários: {e}")

if __name__ == "__main__":
    print("🔧 CORRIGINDO HASH DE SENHAS DO SISTEMA")
    print("=" * 50)
    
    check_all_users()
    print("\n" + "=" * 50)
    fix_admin_password()
    print("\n" + "=" * 50)
    check_all_users()
    
    print("\n✅ Correção concluída!")
    print("Agora tente fazer login novamente com:")
    print("   Email: admin@inventario.com")
    print("   Senha: admin123")