#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_simple_login():
    print("=== TESTE SIMPLES DE LOGIN ===")
    
    try:
        from modules.auth import AuthenticationManager
        
        auth = AuthenticationManager()
        print("✅ AuthenticationManager carregado")
        
        # Teste básico de login
        result = auth.authenticate_user("admin@inventario.com", "Admin123!")
        print(f"Resultado: {result}")
        
        if result[0]:  # success
            print("✅ LOGIN FUNCIONOU!")
            print(f"Dados do usuário: {result[2]}")
        else:
            print("❌ Login falhou")
            print(f"Mensagem: {result[1]}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_login()