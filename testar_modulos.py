"""
Script para verificar módulos que estão após 'Configurações'
"""

modules_after_config = [
    ("QR/Códigos de Barras", "modules.barcode_utils", "show_barcode_page"),
    ("Reservas", "modules.reservas", "show_reservas_page"),
    ("Manutenção Preventiva", "modules.manutencao_preventiva", "show_manutencao_page"),
    ("Dashboard Executivo", "modules.dashboard_executivo", "show_dashboard_executivo_page"),
    ("Localização", "modules.controle_localizacao", "show_localizacao_page"),
    ("Gestão Financeira", "modules.gestao_financeira", "show_gestao_financeira_page"),
    ("Análise Preditiva", "modules.analise_preditiva", "show_analise_preditiva_page"),
    ("Gestão de Subcontratados", "modules.gestao_subcontratados", "show_subcontratados_page"),
    ("Relatórios Customizáveis", "modules.relatorios_customizaveis", "show_relatorios_customizaveis_page"),
    ("Métricas Performance", "modules.metricas_performance", "show_metricas_performance_page"),
    ("Backup e Recovery", "modules.backup_recovery", "show_backup_recovery_page"),
    ("LGPD/Compliance", "modules.lgpd_compliance", "show_lgpd_compliance_page"),
    ("Orçamentos e Cotações", "modules.orcamentos_cotacoes", "show_orcamentos_cotacoes_page"),
    ("Sistema de Faturamento", "modules.sistema_faturamento", "show_faturamento_page"),
    ("Integração ERP/SAP", "modules.integracao_erp", "show_erp_integration_page")
]

def test_module_imports():
    """Testa importação de todos os módulos"""
    missing_modules = []
    working_modules = []
    
    for module_name, module_path, function_name in modules_after_config:
        try:
            # Tentar importar o módulo
            exec(f"import {module_path}")
            
            # Verificar se a função existe
            module_obj = eval(module_path)
            if hasattr(module_obj, function_name):
                working_modules.append(module_name)
                print(f"✅ {module_name}: OK")
            else:
                missing_modules.append((module_name, module_path, f"Função {function_name} não encontrada"))
                print(f"❌ {module_name}: Função {function_name} não encontrada")
                
        except ImportError as e:
            missing_modules.append((module_name, module_path, f"Módulo não encontrado: {e}"))
            print(f"❌ {module_name}: Módulo não encontrado - {e}")
        except Exception as e:
            missing_modules.append((module_name, module_path, f"Erro: {e}"))
            print(f"❌ {module_name}: Erro - {e}")
    
    print(f"\n📊 Resumo:")
    print(f"✅ Módulos funcionando: {len(working_modules)}")
    print(f"❌ Módulos com problemas: {len(missing_modules)}")
    
    if missing_modules:
        print(f"\n🔧 Módulos que precisam ser criados/corrigidos:")
        for name, path, error in missing_modules:
            print(f"  - {name} ({path}): {error}")
    
    return working_modules, missing_modules

if __name__ == "__main__":
    test_module_imports()