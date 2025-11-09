"""
Configurações e fixtures compartilhadas para todos os testes
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import tempfile
from typing import Generator, Dict, Any

# Adiciona o diretório root ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(scope="session")
def test_db():
    """Cria uma conexão de banco de dados para testes"""
    from database.connection import db
    # Mock da conexão para evitar problemas reais de BD
    with patch.object(db, 'get_connection') as mock_conn:
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_cursor.fetchall.return_value = []
        mock_cursor.description = [('id',), ('nome',)]
        mock_cursor.execute.return_value = None
        mock_cursor.commit.return_value = None
        
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.commit.return_value = None
        mock_connection.rollback.return_value = None
        
        mock_conn.return_value = mock_connection
        yield mock_connection

@pytest.fixture
def mock_streamlit():
    """Mock do Streamlit para testes"""
    with patch('streamlit.session_state', {}), \
         patch('streamlit.error'), \
         patch('streamlit.success'), \
         patch('streamlit.warning'), \
         patch('streamlit.info'), \
         patch('streamlit.write'), \
         patch('streamlit.markdown'), \
         patch('streamlit.columns'), \
         patch('streamlit.form'), \
         patch('streamlit.text_input'), \
         patch('streamlit.number_input'), \
         patch('streamlit.selectbox'), \
         patch('streamlit.button'), \
         patch('streamlit.checkbox'):
        yield

@pytest.fixture
def sample_user_data():
    """Dados de usuário de exemplo para testes"""
    return {
        'id': 1,
        'nome': 'Usuário Teste',
        'email': 'teste@exemplo.com',
        'perfil': 'admin',
        'ativo': True
    }

@pytest.fixture
def sample_insumo_data():
    """Dados de insumo de exemplo para testes"""
    return {
        'codigo': 'INS001',
        'descricao': 'Insumo de Teste',
        'categoria_id': 1,
        'unidade': 'UN',
        'quantidade_atual': 100,
        'quantidade_minima': 10,
        'fornecedor': 'Fornecedor Teste',
        'marca': 'Marca Teste',
        'localizacao': 'Estoque A1',
        'observacoes': 'Teste',
        'data_validade': '2025-12-31'
    }

@pytest.fixture
def sample_equipamento_data():
    """Dados de equipamento de exemplo para testes"""
    return {
        'codigo': 'EQ001',
        'descricao': 'Equipamento Teste',
        'categoria_id': 1,
        'marca': 'Marca Teste',
        'modelo': 'Modelo Teste',
        'estado': 'bom',
        'localizacao': 'Local A1',
        'responsavel_id': 1,
        'obra_id': 1
    }

@pytest.fixture
def mock_auth_manager():
    """Mock do AuthenticationManager para testes"""
    mock = Mock()
    mock.authenticate_user.return_value = (True, "Login realizado com sucesso", {'id': 1, 'nome': 'Teste'})
    mock.create_user.return_value = (True, "Usuário criado com sucesso")
    mock.get_users.return_value = [{'id': 1, 'nome': 'Teste', 'email': 'teste@test.com'}]
    mock.is_admin.return_value = True
    mock.get_session_user.return_value = {'id': 1, 'nome': 'Teste', 'perfil': 'admin'}
    return mock

@pytest.fixture
def temp_file():
    """Cria um arquivo temporário para testes"""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        yield f.name
    os.unlink(f.name)

class MockCursor:
    """Mock cursor para simulação de consultas de banco"""
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self.fetchone_result = fetchone_result
        self.fetchall_result = fetchall_result or []
        self.description = [('id',), ('nome',), ('email',)]
        self.execute_calls = []
    
    def execute(self, query, params=None):
        self.execute_calls.append((query, params))
        
    def fetchone(self):
        return self.fetchone_result
        
    def fetchall(self):
        return self.fetchall_result
        
    def commit(self):
        pass
        
    def rollback(self):
        pass

@pytest.fixture
def mock_cursor():
    """Fixture para mock cursor"""
    return MockCursor()

# Configurações globais para testes
TEST_DB_NAME = "test_inventory.db"
TEST_CONFIG = {
    'database': {
        'name': TEST_DB_NAME,
        'user': 'test',
        'password': 'test'
    },
    'app': {
        'name': 'Sistema Inventário - Testes',
        'debug': True
    }
}

@pytest.fixture(autouse=True)
def cleanup_session_state():
    """Limpa o session_state do Streamlit após cada teste"""
    yield
    # Limpeza após o teste
    import streamlit as st
    if hasattr(st, 'session_state'):
        for key in list(st.session_state.keys()):
            del st.session_state[key]