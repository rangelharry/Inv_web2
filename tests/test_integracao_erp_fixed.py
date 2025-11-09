"""
Teste ERP corrigido com classe correta
"""

import pytest
from unittest.mock import patch, Mock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestIntegracaoERPFixed:
    """Teste ERP com classe correta"""

    def test_init_erp_manager(self):
        """Teste inicialização ERPIntegrationManager"""
        with patch('modules.integracao_erp.db') as mock_db:
            mock_connection = Mock()
            mock_db.get_connection.return_value = mock_connection
            
            from modules.integracao_erp import ERPIntegrationManager
            manager = ERPIntegrationManager()
            assert manager is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])