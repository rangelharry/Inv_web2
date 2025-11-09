#!/usr/bin/env python3
"""
Script de teste completo do sistema - verifica todos os módulos
"""

def test_database_connection():
    """Testa conexão com banco"""
    print("=== TESTANDO CONEXÃO COM BANCO ===")
    try:
        from database.connection import db
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        print(f"✅ Conexão OK: {result}")
        return True
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        return False

def test_auth_module():
    """Testa módulo de autenticação"""
    print("\n=== TESTANDO MÓDULO AUTH ===")
    try:
        from modules.auth import AuthenticationManager
        auth = AuthenticationManager()
        
        # Teste básico
        success, msg, user_data = auth.authenticate_user('admin@sistema.com', 'Admin123!')
        print(f"✅ Autenticação: {success} - {msg}")
        
        users = auth.get_users()
        print(f"✅ Usuários encontrados: {len(users)}")
        return True
    except Exception as e:
        print(f"❌ Erro no módulo auth: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_insumos_module():
    """Testa módulo de insumos"""
    print("\n=== TESTANDO MÓDULO INSUMOS ===")
    try:
        from modules.insumos import InsumosManager
        manager = InsumosManager()
        
        insumos = manager.get_insumos()
        print(f"✅ Insumos encontrados: {len(insumos)}")
        
        # Teste de estatísticas
        stats = manager.get_dashboard_stats()
        print(f"✅ Estatísticas: {stats}")
        return True
    except Exception as e:
        print(f"❌ Erro no módulo insumos: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_usuarios_module():
    """Testa módulo de usuários"""
    print("\n=== TESTANDO MÓDULO USUÁRIOS ===")
    try:
        from modules.usuarios import UsuariosManager
        manager = UsuariosManager()
        
        usuarios = manager.get_usuarios()
        print(f"✅ Usuários encontrados: {len(usuarios)}")
        
        # Teste de estatísticas
        stats = manager.get_dashboard_stats()
        print(f"✅ Estatísticas usuários: {stats}")
        return True
    except Exception as e:
        print(f"❌ Erro no módulo usuários: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logs_module():
    """Testa módulo de logs"""
    print("\n=== TESTANDO MÓDULO LOGS ===")
    try:
        from modules.logs_auditoria import LogsAuditoriaManager
        manager = LogsAuditoriaManager()
        
        logs = manager.get_logs()
        print(f"✅ Logs encontrados: {len(logs)}")
        
        # Teste de estatísticas
        stats = manager.get_dashboard_stats()
        print(f"✅ Estatísticas logs: {stats}")
        
        modulos = manager.get_modulos_disponiveis()
        print(f"✅ Módulos disponíveis: {modulos}")
        return True
    except Exception as e:
        print(f"❌ Erro no módulo logs: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_equipamentos_modules():
    """Testa módulos de equipamentos"""
    print("\n=== TESTANDO MÓDULOS EQUIPAMENTOS ===")
    try:
        from modules.equipamentos_eletricos import EquipamentosEletricosManager
        from modules.equipamentos_manuais import EquipamentosManuaisManager
        
        # Equipamentos elétricos
        manager_ee = EquipamentosEletricosManager()
        equipamentos_ee = manager_ee.get_equipamentos()
        print(f"✅ Equipamentos elétricos: {len(equipamentos_ee)}")
        
        # Equipamentos manuais
        manager_em = EquipamentosManuaisManager()
        equipamentos_em = manager_em.get_equipamentos()
        print(f"✅ Equipamentos manuais: {len(equipamentos_em)}")
        
        return True
    except Exception as e:
        print(f"❌ Erro nos módulos equipamentos: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_relatorios_module():
    """Testa módulo de relatórios"""
    print("\n=== TESTANDO MÓDULO RELATÓRIOS ===")
    try:
        from modules.relatorios import RelatoriosManager
        manager = RelatoriosManager()
        
        # Teste relatório básico
        relatorio = manager.gerar_relatorio_estoque_baixo()
        print(f"✅ Relatório estoque baixo: {len(relatorio)} itens")
        
        return True
    except Exception as e:
        print(f"❌ Erro no módulo relatórios: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTE COMPLETO DO SISTEMA")
    print("=" * 50)
    
    tests = [
        test_database_connection,
        test_auth_module,
        test_insumos_module,
        test_usuarios_module,
        test_logs_module,
        test_equipamentos_modules,
        test_relatorios_module
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES:")
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Testes passaram: {passed}/{total}")
    print(f"❌ Testes falharam: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 TODOS OS MÓDULOS ESTÃO FUNCIONANDO!")
    else:
        print("⚠️  ALGUNS MÓDULOS PRECISAM DE CORREÇÃO!")
    
    return passed == total

if __name__ == "__main__":
    main()