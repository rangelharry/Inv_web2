import sys
sys.path.append('e:/GITHUB/Inv_web2')

from modules.insumos import InsumosManager

# Dados de teste
sample_data = {
    'codigo': 'INS001',
    'descricao': 'Insumo de Teste',
    'categoria_id': 1,
    'unidade': 'UN',
    'quantidade_atual': 100,
    'quantidade_minima': 10,
    'fornecedor': 'Fornecedor Teste',
    'marca': 'Marca Teste',
    'localizacao': 'Estoque A',
    'observacoes': 'Teste',
    'data_validade': '2025-12-31'
}

try:
    manager = InsumosManager()
    success, message = manager.criar_insumo(sample_data, 1)
    print(f"Success: {success}")
    print(f"Message: {message}")
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()