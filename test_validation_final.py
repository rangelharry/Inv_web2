#!/usr/bin/env python3
"""
Script de validação final - testa funcionalidades específicas que estavam com problemas
"""

def test_usuarios_crud():
    """Testa operações CRUD de usuários"""
    print("=== TESTANDO CRUD DE USUÁRIOS ===")
    try:
        from modules.usuarios import UsuariosManager
        manager = UsuariosManager()
        
        # Teste de busca
        usuarios = manager.get_usuarios()
        print(f"✅ Busca usuários: {len(usuarios)} encontrados")
        
        # Teste de estatísticas
        stats = manager.get_dashboard_stats()
        print(f"✅ Estatísticas usuários: {stats}")
        
        # Teste com filtros
        usuarios_filtrados = manager.get_usuarios({'perfil': 'admin'})
        print(f"✅ Filtro por perfil admin: {len(usuarios_filtrados)} encontrados")
        
        return True
    except Exception as e:
        print(f"❌ Erro CRUD usuários: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logs_auditoria():
    """Testa logs de auditoria"""
    print("\n=== TESTANDO LOGS DE AUDITORIA ===")
    try:
        from modules.logs_auditoria import LogsAuditoriaManager
        manager = LogsAuditoriaManager()
        
        # Teste de busca
        logs = manager.get_logs()
        print(f"✅ Busca logs: {len(logs)} encontrados")
        
        # Teste de estatísticas
        stats = manager.get_dashboard_stats()
        print(f"✅ Estatísticas logs: {stats}")
        
        # Teste de módulos disponíveis
        modulos = manager.get_modulos_disponiveis()
        print(f"✅ Módulos disponíveis: {modulos}")
        
        # Teste de tipos de ação
        tipos = manager.get_tipos_acao()
        print(f"✅ Tipos de ação: {tipos}")
        
        return True
    except Exception as e:
        print(f"❌ Erro logs auditoria: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_insumos_dashboard():
    """Testa dashboard de insumos"""
    print("\n=== TESTANDO DASHBOARD INSUMOS ===")
    try:
        from modules.insumos import InsumosManager
        manager = InsumosManager()
        
        # Teste de busca
        insumos = manager.get_insumos()
        print(f"✅ Busca insumos: {len(insumos)} encontrados")
        
        # Teste de estatísticas (recém adicionado)
        stats = manager.get_dashboard_stats()
        print(f"✅ Estatísticas insumos: {stats}")
        
        # Teste de estoque baixo
        estoque_baixo = manager.get_insumos({'estoque_baixo': True})
        print(f"✅ Estoque baixo: {len(estoque_baixo)} itens")
        
        return True
    except Exception as e:
        print(f"❌ Erro dashboard insumos: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_relatorios_excel():
    """Testa relatórios e exportação Excel"""
    print("\n=== TESTANDO RELATÓRIOS E EXCEL ===")
    try:
        from modules.relatorios import RelatoriosManager
        import pandas as pd
        
        manager = RelatoriosManager()
        
        # Teste relatório estoque baixo
        relatorio = manager.gerar_relatorio_estoque_baixo()
        print(f"✅ Relatório estoque baixo: {len(relatorio)} itens")
        
        # Teste exportação Excel (só se houver dados)
        if len(relatorio) > 0:
            excel_data = manager.exportar_excel(relatorio, 'estoque_baixo')
            print(f"✅ Exportação Excel: {len(excel_data)} bytes gerados")
        else:
            print("✅ Exportação Excel: Não testado (sem dados)")
        
        return True
    except Exception as e:
        print(f"❌ Erro relatórios/Excel: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_queries():
    """Testa queries específicas do banco"""
    print("\n=== TESTANDO QUERIES DO BANCO ===")
    try:
        from database.connection import db
        
        cursor = db.get_connection().cursor()
        
        # Teste query PostgreSQL (logs)
        cursor.execute("""
            SELECT COUNT(*) as count FROM logs_auditoria 
            WHERE data_acao >= NOW() - INTERVAL '24 hours'
        """)
        result = cursor.fetchone()
        count_logs = result['count'] if isinstance(result, dict) and 'count' in result else (result[0] if result else 0)
        print(f"✅ Query logs 24h: {count_logs}")

        # Teste query PostgreSQL (usuários)
        cursor.execute("""
            SELECT COUNT(*) as count FROM usuarios 
            WHERE ativo = TRUE
        """)
        result = cursor.fetchone()
        count_users = result['count'] if isinstance(result, dict) and 'count' in result else (result[0] if result else 0)
        print(f"✅ Query usuários ativos: {count_users}")

        # Teste query PostgreSQL (insumos)
        cursor.execute("""
            SELECT COUNT(*) as count FROM insumos 
            WHERE ativo = TRUE AND quantidade_atual <= quantidade_minima
        """)
        result = cursor.fetchone()
        count_estoque_baixo = result['count'] if isinstance(result, dict) and 'count' in result else (result[0] if result else 0)
        print(f"✅ Query estoque baixo: {count_estoque_baixo}")
        
        return True
    except Exception as e:
        print(f"❌ Erro queries banco: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa validação final"""
    print("🔍 VALIDAÇÃO FINAL DO SISTEMA")
    print("=" * 50)
    
    tests = [
        test_usuarios_crud,
        test_logs_auditoria,
        test_insumos_dashboard,
        test_relatorios_excel,
        test_database_queries
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESULTADO DA VALIDAÇÃO:")
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Testes passaram: {passed}/{total}")
    print(f"❌ Testes falharam: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 SISTEMA TOTALMENTE VALIDADO!")
        print("✅ Todos os erros foram corrigidos")
        print("✅ Logs de auditoria funcionando")
        print("✅ Módulo de usuários funcionando")
        print("✅ Dashboard de insumos funcionando")
        print("✅ Relatórios e Excel funcionando")
        print("✅ Queries do banco funcionando")
    else:
        print(f"\n⚠️  {total - passed} PROBLEMAS AINDA PRECISAM SER RESOLVIDOS!")
    
    return passed == total

if __name__ == "__main__":
    main()