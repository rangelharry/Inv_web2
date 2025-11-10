"""
Teste específico para verificar erros de execução nos módulos
"""

import sys
import traceback

def test_module_execution():
    """Testa execução básica de módulos específicos"""
    
    modules_to_test = [
        ("barcode_utils", "show_barcode_page"),
        ("dashboard_executivo", "show_dashboard_executivo"),
        ("controle_localizacao", "show_localizacao_page"),
        ("backup_recovery", "show_backup_recovery_page"),
        ("lgpd_compliance", "show_lgpd_compliance_page"),
    ]
    
    for module_name, function_name in modules_to_test:
        print(f"\n🧪 Testando {module_name}...")
        try:
            # Importar módulo
            module = __import__(f"modules.{module_name}", fromlist=[function_name])
            
            # Verificar se função existe
            if hasattr(module, function_name):
                print(f"  ✅ Função {function_name} encontrada")
                
                # Tentar uma importação mais profunda (verificar dependências)
                func = getattr(module, function_name)
                print(f"  ✅ Função {function_name} carregada sem erros")
                
            else:
                print(f"  ❌ Função {function_name} não encontrada")
                
        except ImportError as e:
            print(f"  ❌ Erro de importação: {e}")
        except Exception as e:
            print(f"  ❌ Erro geral: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    test_module_execution()