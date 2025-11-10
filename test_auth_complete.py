#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_auth_methods():
    print("=== TESTE COMPLETO DE MÉTODOS AUTH ===")
    
    try:
        from modules.auth import AuthenticationManager
        
        auth = AuthenticationManager()
        print("✅ AuthenticationManager carregado")
        
        # Teste de métodos
        methods_to_test = [
            'authenticate_user',
            'create_session',
            'get_session_user',
            'is_admin',
            'logout',
            'check_permission'
        ]
        
        for method_name in methods_to_test:
            if hasattr(auth, method_name):
                print(f"✅ Método {method_name} existe")
            else:
                print(f"❌ Método {method_name} NÃO existe")
        
        # Teste de login
        print("\n--- Teste de Login ---")
        result = auth.authenticate_user("admin@inventario.com", "Admin123!")
        if result[0]:
            print("✅ Login funcionando")
            user_data = result[2]
            
            # Teste create_session
            print("\n--- Teste create_session ---")
            token = auth.create_session(user_data['id'])
            if token:
                print(f"✅ Session criada: {token[:20]}...")
            else:
                print("❌ Erro ao criar session")
        else:
            print(f"❌ Login falhou: {result[1]}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_auth_methods()