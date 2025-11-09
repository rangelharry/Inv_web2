"""
Testes ROI-otimizados SIMPLES para Reservas 
Teste básico apenas para ROI
"""

import pytest
from unittest.mock import patch, Mock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestReservasROISimple:
    """Testes simples para ROI"""

    def test_init_reserva_manager(self):
        """Teste inicialização ReservaManager"""
        with patch('modules.reservas.db') as mock_db:
            mock_connection = Mock()
            mock_db.get_connection.return_value = mock_connection
            
            from modules.reservas import ReservaManager
            manager = ReservaManager()
            assert manager is not None

    def test_basic_methods_exist(self):
        """Teste métodos básicos existem"""
        with patch('modules.reservas.db') as mock_db:
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_db.get_connection.return_value = mock_connection
            
            from modules.reservas import ReservaManager
            manager = ReservaManager()
            
            # Testar métodos que existem
            assert hasattr(manager, 'reservas')
            assert hasattr(manager, 'criar_tabela_reservas')

if __name__ == "__main__":
    pytest.main([__file__, "-v"])