#!/usr/bin/env python3
"""Teste do módulo de insumos"""

from modules.insumos import InsumosManager

def test_insumos():
    print("=== TESTE DO MÓDULO INSUMOS ===")
    
    try:
        manager = InsumosManager()
        insumos = manager.get_insumos()
        print(f"Total de insumos encontrados: {len(insumos)}")
        
        if len(insumos) > 0:
            print("Primeiros 3 insumos:")
            for i, insumo in enumerate(insumos[:3]):
                print(f"  {i+1}. ID: {insumo['id']}, Código: {insumo['codigo']}, Descrição: {insumo['descricao']}")
            print("✅ Módulo de insumos funcionando!")
        else:
            print("❌ Nenhum insumo retornado pelo módulo")
            
    except Exception as e:
        print(f"❌ Erro no módulo de insumos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_insumos()