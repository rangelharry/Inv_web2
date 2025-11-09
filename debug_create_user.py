import sys
sys.path.append('e:/GITHUB/Inv_web2')

from unittest.mock import Mock, patch
from modules.auth import AuthenticationManager

# Mock do banco
mock_db = Mock()
mock_cursor = Mock()
mock_db.cursor.return_value = mock_cursor
# Primeira chamada: email não existe (None), segunda: user criado com ID 1
mock_cursor.fetchone.side_effect = [None, (1,)]

# Testar com mock
with patch('modules.auth.db') as mock_db_module:
    mock_db_module.get_connection.return_value = mock_db
    
    auth_manager = AuthenticationManager()
    success, message = auth_manager.create_user(
        nome="João Silva",
        email="joao@exemplo.com", 
        password="MinhaSenh@123",
        perfil="usuario"
    )
    
    print(f"Success: {success}")
    print(f"Message: {message}")
    print(f"Cursor execute calls: {mock_cursor.execute.call_args_list}")