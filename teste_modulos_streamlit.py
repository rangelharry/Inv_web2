"""
Teste de simulação do ambiente Streamlit
"""

import os
import sys

# Simular algumas variáveis do Streamlit
class MockStreamlit:
    def __init__(self):
        self.session_state = {}
    
    def write(self, text):
        print(f"ST WRITE: {text}")
    
    def error(self, text):
        print(f"ST ERROR: {text}")
    
    def success(self, text):
        print(f"ST SUCCESS: {text}")

# Simular streamlit
sys.modules['streamlit'] = MockStreamlit()

def test_dashboard_executivo():
    """Teste específico do dashboard executivo"""
    try:
        from modules.dashboard_executivo import show_dashboard_executivo_page
        print("✅ Importação do dashboard executivo realizada")
        
        # Não vamos executar a função pois ela precisa do Streamlit real
        # Apenas verificar se importa sem erros
        print("✅ Dashboard executivo pronto para uso")
        
    except Exception as e:
        print(f"❌ Erro no dashboard executivo: {e}")
        import traceback
        traceback.print_exc()

def test_other_modules():
    """Teste de outros módulos"""
    modules_to_test = [
        ("gestao_financeira", "show_gestao_financeira_page"),
        ("analise_preditiva", "show_analise_preditiva_page"),
        ("metricas_performance", "show_metricas_performance_page"),
    ]
    
    for module_name, function_name in modules_to_test:
        try:
            module = __import__(f"modules.{module_name}", fromlist=[function_name])
            func = getattr(module, function_name)
            print(f"✅ {module_name}: OK")
        except Exception as e:
            print(f"❌ {module_name}: {e}")

if __name__ == "__main__":
    print("🧪 Testando módulos específicos...")
    test_dashboard_executivo()
    test_other_modules()