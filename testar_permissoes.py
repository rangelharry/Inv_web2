"""
Script para verificar as permissões do usuário teste
"""

import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from modules.auth import auth_manager

def test_user_permissions():
    """Testa as permissões do usuário teste"""
    try:
        # Buscar usuário teste
        conn = auth_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, nome, email, perfil FROM usuarios WHERE email = %s", ("teste@exemplo.com",))
        user = cursor.fetchone()
        
        if not user:
            print("❌ Usuário teste não encontrado!")
            return
        
        print(f"👤 Usuário encontrado: {user['nome']} ({user['email']})")
        print(f"📋 Perfil: {user['perfil']}")
        print(f"🆔 ID: {user['id']}")
        
        # Verificar permissões
        permissions = auth_manager.get_user_module_permissions(user['id'])
        
        print(f"\n🔒 Permissões do usuário:")
        for module, access in permissions.items():
            status = "✅" if access else "❌"
            print(f"  {status} {module}: {access}")
        
        # Testar módulos específicos
        print(f"\n🧪 Testes específicos:")
        modules_to_test = [
            'dashboard',
            'equipamentos_eletricos', 
            'movimentacao',
            'usuarios',
            'relatorios',
            'insumos'
        ]
        
        for module in modules_to_test:
            has_access = auth_manager.check_module_permission(user['id'], module)
            status = "✅ PERMITIDO" if has_access else "❌ NEGADO"
            print(f"  {module}: {status}")
        
    except Exception as e:
        print(f"❌ Erro ao verificar permissões: {e}")

if __name__ == "__main__":
    test_user_permissions()