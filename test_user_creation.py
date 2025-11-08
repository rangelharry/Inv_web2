#!/usr/bin/env python3
"""Teste de criação de usuário PostgreSQL"""

import sys
import traceback
sys.path.append('.')

from modules.auth import AuthenticationManager

def main():
    print("=== TESTE DE CRIAÇÃO DE USUÁRIO POSTGRESQL ===")
    
    try:
        auth = AuthenticationManager()
        print("✅ AuthenticationManager inicializado")
        
        # Teste de criação de usuário
        nome = "Administrador"
        email = "admin@sistema.com"
        password = "Admin123!"
        perfil = "admin"
        
        print(f"Criando usuário: {nome} ({email})")
        
        # Testar criação sem log primeiro
        try:
            conn = auth.get_connection()
            cursor = conn.cursor()
            
            print("✅ Conexão obtida")
            
            # Validações
            if not auth.validate_email(email):
                print("❌ Email inválido")
                return
                
            print("✅ Email válido")
            
            # Verifica se email já existe
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            existing = cursor.fetchone()
            if existing:
                print(f"❌ Email já existe: {existing}")
                return
                
            print("✅ Email não existe, pode criar")
            
            # Cria usuário
            password_hash = auth.hash_password(password)
            print("✅ Hash da senha criado")
            
            cursor.execute("""
            INSERT INTO usuarios (nome, email, password_hash, perfil, ativo)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, (nome, email, password_hash, perfil, True))
            
            result = cursor.fetchone()
            print(f"✅ Insert result: {result}")
            
            user_id = result['id'] if result else None
            print(f"✅ User ID: {user_id}")
            
            conn.commit()
            print("✅ Commit realizado")
            
            if user_id:
                print(f"✅ Usuário criado com ID: {user_id}")
            else:
                print("❌ User ID é None")
                
        except Exception as e:
            print(f"❌ Erro na criação manual: {e}")
            import traceback
            traceback.print_exc()
            if 'conn' in locals():
                conn.rollback()
        
        # Teste de autenticação
        print("\nTestando autenticação...")
        auth_result = auth.authenticate_user(email, password)
        print(f"✅ Autenticação: {auth_result}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()