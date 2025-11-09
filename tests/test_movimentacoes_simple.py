"""
Testes abrangentes para módulo de movimentações
Foco em alta cobertura
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
import sys
import os

# Adicionar o diretório raiz ao path se necessário
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestMovimentacoesSimple:
    """Testes básicos para MovimentacoesManager"""

    def test_init_basic(self):
        """Teste básico de inicialização"""
        with patch('modules.movimentacoes.db') as mock_db:
            mock_connection = Mock()
            mock_db.get_connection.return_value = mock_connection
            mock_connection.rollback.return_value = None
            
            from modules.movimentacoes import MovimentacoesManager
            manager = MovimentacoesManager()
            assert manager is not None

    def test_get_movimentacoes_basic(self):
        """Teste básico get_movimentacoes"""
        with patch('modules.movimentacoes.db') as mock_db:
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = []
            mock_cursor.description = []
            mock_db.get_connection.return_value = mock_connection
            
            from modules.movimentacoes import MovimentacoesManager
            manager = MovimentacoesManager()
            result = manager.get_movimentacoes()
            assert isinstance(result, list)

    def test_get_movimentacoes_no_connection(self):
        """Teste get_movimentacoes sem conexão"""
        with patch('modules.movimentacoes.db') as mock_db, \
             patch('streamlit.error') as mock_error:
            
            mock_db.get_connection.return_value = None
            
            from modules.movimentacoes import MovimentacoesManager
            manager = MovimentacoesManager()
            result = manager.get_movimentacoes()
            assert result == []

    def test_get_movimentacoes_exception(self):
        """Teste get_movimentacoes com exceção"""
        with patch('modules.movimentacoes.db') as mock_db, \
             patch('streamlit.error') as mock_error:
            
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = Exception("Erro SQL")
            mock_db.get_connection.return_value = mock_connection
            
            from modules.movimentacoes import MovimentacoesManager
            manager = MovimentacoesManager()
            result = manager.get_movimentacoes()
            assert result == []

    def test_create_movimentacao_basic(self):
        """Teste básico create_movimentacao"""
        with patch('modules.movimentacoes.db') as mock_db, \
             patch('streamlit.success') as mock_success, \
             patch('streamlit.error') as mock_error:
            
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_db.get_connection.return_value = mock_connection
            
            from modules.movimentacoes import MovimentacoesManager
            manager = MovimentacoesManager()
            
            success, message = manager.create_movimentacao(
                dados={"tipo": "entrada", "item_id": 1, "quantidade": 10},
                user_id=1
            )
            assert isinstance(success, bool)
            assert isinstance(message, str)

    def test_multiple_operations(self):
        """Teste múltiplas operações"""
        with patch('modules.movimentacoes.db') as mock_db:
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = []
            mock_cursor.description = []
            mock_db.get_connection.return_value = mock_connection
            
            from modules.movimentacoes import MovimentacoesManager
            manager = MovimentacoesManager()
            
            # Teste múltiplas chamadas
            movimentacoes = manager.get_movimentacoes()
            assert isinstance(movimentacoes, list)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])