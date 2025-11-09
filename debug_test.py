"""
Teste simples para debugar o problema
"""

import sys
sys.path.append('e:/GITHUB/Inv_web2')

from unittest.mock import Mock, patch
from modules.insumos import InsumosManager

# Mock do banco
mock_db = Mock()
mock_cursor = Mock()
mock_db.cursor.return_value = mock_cursor

# Configurar fetchone para retornar None (código não existe) e depois o ID criado
mock_cursor.fetchone.side_effect = [None, (1,)]  # Primeira chamada: código não existe, segunda: ID criado

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

# Testar com mock
with patch('modules.insumos.db') as mock_db_module:
    mock_db_module.get_connection.return_value = mock_db
    
    with patch('modules.insumos.auth_manager') as mock_auth:
        manager = InsumosManager()
        success, message = manager.criar_insumo(sample_data, 1)
        
        print(f"Success: {success}")
        print(f"Message: {message}")
        
        # Verificar se os mocks foram chamados
        print(f"Cursor execute called: {mock_cursor.execute.called}")
        print(f"DB commit called: {mock_db.commit.called}")
        
        # Ver as chamadas execute
        print(f"Execute calls: {mock_cursor.execute.call_args_list}")