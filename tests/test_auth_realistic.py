"""
Testes abrangentes para o módulo de autenticação com alta cobertura
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
import bcrypt
from datetime import datetime
import re

class TestAuthenticationManagerReal:
    """Testes baseados na interface real do AuthenticationManager"""
    
    @pytest.fixture
    def auth_manager_with_mock(self, test_db):
        """Fixture com mock completo do banco mais realístico"""
        with patch('modules.auth.db') as mock_db, \
             patch('streamlit.session_state', new_callable=dict) as mock_session:
            
            # Configurar mock da conexão
            mock_connection = Mock()
            mock_cursor = Mock()
            
            # Configurar comportamento do cursor
            mock_cursor.fetchone.return_value = None
            mock_cursor.fetchall.return_value = []
            mock_cursor.execute.return_value = None
            mock_cursor.description = []
            
            # Configurar comportamento da conexão
            mock_connection.cursor.return_value = mock_cursor
            mock_connection.commit.return_value = None
            mock_connection.rollback.return_value = None
            
            # Configurar comportamento do db
            mock_db.get_connection.return_value = mock_connection
            
            from modules.auth import AuthenticationManager
            return AuthenticationManager(), mock_cursor, mock_connection
    
    def test_create_user_success(self, auth_manager_with_mock):
        """Testa criação bem-sucedida de usuário"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        # Mock para verificar se email já existe (não existe) e criação
        mock_cursor.fetchone.side_effect = [
            None,  # Email não existe
            (123,)  # ID do usuário criado
        ]
        
        success, message = auth_manager.create_user(
            "João Silva", "joao@example.com", "Senha123@"
        )
        
        assert success is True
        assert "sucesso" in message.lower()
        assert mock_cursor.execute.call_count == 2  # Verifica email + insert
        mock_connection.commit.assert_called_once()
    
    def test_create_user_invalid_email(self, auth_manager_with_mock):
        """Testa criação com email inválido"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        success, message = auth_manager.create_user(
            "João Silva", "email-invalido", "Senha123@"
        )
        
        assert success is False
        assert "email inválido" in message.lower()
        # Não deve chamar o banco se email for inválido
        mock_cursor.execute.assert_not_called()
    
    def test_create_user_weak_password(self, auth_manager_with_mock):
        """Testa criação com senha fraca"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        success, message = auth_manager.create_user(
            "João Silva", "joao@example.com", "123"  # Senha fraca
        )
        
        assert success is False
        assert "pelo menos" in message.lower()
        mock_cursor.execute.assert_not_called()
    
    def test_create_user_duplicate_email(self, auth_manager_with_mock):
        """Testa criação com email duplicado"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        # Mock para email já existente
        mock_cursor.fetchone.return_value = (1,)
        
        success, message = auth_manager.create_user(
            "João Silva", "joao@example.com", "Senha123@"
        )
        
        assert success is False
        assert "já está em uso" in message.lower()
    
    def test_create_user_database_error(self, auth_manager_with_mock):
        """Testa criação com erro de banco"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        # Mock para erro de banco
        mock_cursor.execute.side_effect = Exception("Database error")
        
        success, message = auth_manager.create_user(
            "João Silva", "joao@example.com", "Senha123@"
        )
        
        assert success is False
        assert "erro" in message.lower()
        mock_connection.rollback.assert_called_once()
    
    def test_authenticate_user_success(self, auth_manager_with_mock):
        """Testa autenticação bem-sucedida"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        # Hash da senha para comparação
        password = "Senha123@"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Mock do usuário encontrado - retorna tupla como na implementação real
        user_data = (1, 'João Silva', 'joao@example.com', hashed_password, 'admin', True)
        mock_cursor.fetchone.return_value = user_data
        
        user = auth_manager.authenticate_user("joao@example.com", password)
        
        assert user is not None
        assert user['id'] == 1
        assert user['nome'] == 'João Silva'
        assert user['email'] == 'joao@example.com'
        assert user['perfil'] == 'admin'
        
        # Verifica se fez update do último login
        assert mock_cursor.execute.call_count == 2  # SELECT + UPDATE
        mock_connection.commit.assert_called_once()
    
    def test_authenticate_user_not_found(self, auth_manager_with_mock):
        """Testa autenticação com usuário não encontrado"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        mock_cursor.fetchone.return_value = None
        
        user = auth_manager.authenticate_user("naoexiste@example.com", "Senha123@")
        
        assert user is None
    
    def test_authenticate_user_inactive(self, auth_manager_with_mock):
        """Testa autenticação com usuário inativo"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        # Usuário inativo (último campo = False)
        user_data = (1, 'João Silva', 'joao@example.com', 'hash', 'usuario', False)
        mock_cursor.fetchone.return_value = user_data
        
        user = auth_manager.authenticate_user("joao@example.com", "Senha123@")
        
        assert user is None
    
    def test_authenticate_user_wrong_password(self, auth_manager_with_mock):
        """Testa autenticação com senha incorreta"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        # Hash de uma senha diferente
        hashed_password = bcrypt.hashpw("OutraSenha123@".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user_data = (1, 'João Silva', 'joao@example.com', hashed_password, 'usuario', True)
        mock_cursor.fetchone.return_value = user_data
        
        user = auth_manager.authenticate_user("joao@example.com", "SenhaErrada")
        
        assert user is None
    
    def test_authenticate_user_database_error(self, auth_manager_with_mock):
        """Testa autenticação com erro de banco"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        mock_cursor.execute.side_effect = Exception("Database connection failed")
        
        user = auth_manager.authenticate_user("joao@example.com", "Senha123@")
        
        assert user is None
    
    def test_hash_password(self, auth_manager_with_mock):
        """Testa hash de senha"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        password = "MinhaSenh@123"
        hashed = auth_manager.hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith('$2b$')  # bcrypt hash format
    
    def test_verify_password(self, auth_manager_with_mock):
        """Testa verificação de senha"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        password = "MinhaSenh@123"
        hashed = auth_manager.hash_password(password)
        
        assert auth_manager.verify_password(password, hashed) is True
        assert auth_manager.verify_password("SenhaErrada", hashed) is False
        assert auth_manager.verify_password("", hashed) is False
    
    def test_validate_email_valid(self, auth_manager_with_mock):
        """Testa validação de emails válidos"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        valid_emails = [
            "test@example.com",
            "user123@domain.org",
            "firstname.lastname@company.co.uk",
            "user+tag@domain.com"
        ]
        
        for email in valid_emails:
            assert auth_manager.validate_email(email) is True
    
    def test_validate_email_invalid(self, auth_manager_with_mock):
        """Testa validação de emails inválidos"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user@@domain.com",
            "",
            "user space@domain.com",
            "user@domain"
        ]
        
        for email in invalid_emails:
            assert auth_manager.validate_email(email) is False
    
    def test_validate_password_strength_strong(self, auth_manager_with_mock):
        """Testa validação de senhas fortes"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        strong_passwords = [
            "MinhaSenh@123",
            "Password123!",
            "Str0ng@Pass",
            "Complex1ty$"
        ]
        
        for password in strong_passwords:
            is_valid, errors = auth_manager.validate_password_strength(password)
            assert is_valid is True
            assert len(errors) == 0
    
    def test_validate_password_strength_weak(self, auth_manager_with_mock):
        """Testa validação de senhas fracas"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        # Senha muito curta
        is_valid, errors = auth_manager.validate_password_strength("123")
        assert is_valid is False
        assert any("8 caracteres" in error for error in errors)
        
        # Sem maiúscula
        is_valid, errors = auth_manager.validate_password_strength("minhasenha123")
        assert is_valid is False
        assert any("maiúscula" in error for error in errors)
        
        # Sem minúscula
        is_valid, errors = auth_manager.validate_password_strength("MINHASENHA123")
        assert is_valid is False
        assert any("minúscula" in error for error in errors)
        
        # Sem número
        is_valid, errors = auth_manager.validate_password_strength("MinhaSenh@")
        assert is_valid is False
        assert any("número" in error for error in errors)
    
    def test_get_users(self, auth_manager_with_mock):
        """Testa listagem de usuários"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        # Mock da descrição das colunas
        mock_cursor.description = [
            ['id'], ['nome'], ['email'], ['perfil'], ['ativo'], ['data_criacao']
        ]
        
        # Mock dos dados dos usuários
        mock_cursor.fetchall.return_value = [
            (1, 'Admin', 'admin@test.com', 'admin', True, '2024-01-01'),
            (2, 'Usuario', 'user@test.com', 'usuario', True, '2024-01-02')
        ]
        
        users = auth_manager.get_users()
        
        assert len(users) == 2
        assert users[0]['nome'] == 'Admin'
        assert users[1]['nome'] == 'Usuario'
        assert users[0]['perfil'] == 'admin'
        assert users[1]['perfil'] == 'usuario'
    
    def test_get_users_empty(self, auth_manager_with_mock):
        """Testa listagem sem usuários"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        mock_cursor.description = []
        mock_cursor.fetchall.return_value = []
        
        users = auth_manager.get_users()
        
        assert len(users) == 0
    
    def test_get_users_database_error(self, auth_manager_with_mock):
        """Testa listagem com erro de banco"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        mock_cursor.execute.side_effect = Exception("Database error")
        
        users = auth_manager.get_users()
        
        assert len(users) == 0
    
    def test_change_password_success(self, auth_manager_with_mock):
        """Testa alteração de senha com sucesso"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        # Hash da senha atual
        current_password = "SenhaAtual123@"
        old_password_hash = bcrypt.hashpw(current_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Mock para buscar usuário
        mock_cursor.fetchone.return_value = (old_password_hash,)
        
        success, message = auth_manager.change_password(
            1, current_password, "NovaSenha123@"
        )
        
        assert success is True
        assert "sucesso" in message.lower()
        mock_connection.commit.assert_called_once()
    
    def test_change_password_wrong_old(self, auth_manager_with_mock):
        """Testa alteração com senha atual incorreta"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        # Hash de uma senha diferente
        old_password_hash = bcrypt.hashpw("OutraSenha".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        mock_cursor.fetchone.return_value = (old_password_hash,)
        
        success, message = auth_manager.change_password(
            1, "SenhaErrada", "NovaSenha123@"
        )
        
        assert success is False
        assert "incorreta" in message.lower()
    
    def test_change_password_weak_new(self, auth_manager_with_mock):
        """Testa alteração para senha fraca"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        # Hash da senha atual
        current_password = "SenhaAtual123@"
        old_password_hash = bcrypt.hashpw(current_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        mock_cursor.fetchone.return_value = (old_password_hash,)
        
        success, message = auth_manager.change_password(
            1, current_password, "123"  # Senha fraca
        )
        
        assert success is False
        assert "pelo menos" in message.lower()
    
    def test_toggle_user_status(self, auth_manager_with_mock):
        """Testa ativação/desativação de usuário"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        # Mock para verificar se usuário existe e buscar status atual
        mock_cursor.fetchone.side_effect = [
            (True,),  # Status atual (ativo)
            (1,)      # Confirmação da atualização
        ]
        
        success, message = auth_manager.toggle_user_status(1, 2)  # user_id=1, admin_id=2
        
        assert success is True
        mock_connection.commit.assert_called_once()
    
    def test_toggle_user_status_not_found(self, auth_manager_with_mock):
        """Testa toggle de usuário inexistente"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        mock_cursor.fetchone.return_value = None
        
        success, message = auth_manager.toggle_user_status(999, 2)
        
        assert success is False
        assert "não encontrado" in message.lower()
    
    def test_reset_password_success(self, auth_manager_with_mock):
        """Testa reset de senha por admin"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        mock_cursor.fetchone.return_value = (1,)  # Confirmação
        
        success, message = auth_manager.reset_password(1, "NovaSenha123@", 2)
        
        assert success is True
        mock_connection.commit.assert_called_once()
    
    def test_reset_password_weak(self, auth_manager_with_mock):
        """Testa reset com senha fraca"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        success, message = auth_manager.reset_password(1, "123", 2)  # Senha fraca
        
        assert success is False
        assert "pelo menos" in message.lower()
    
    def test_log_action(self, auth_manager_with_mock):
        """Testa registro de log de ação"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        # Não deve lançar exceção
        auth_manager.log_action(
            user_id=1,
            action="CREATE",
            table_name="usuarios",
            item_id=2,
            details="Criação de novo usuário"
        )
        
        # Verificar se execute foi chamado
        mock_cursor.execute.assert_called()
        mock_connection.commit.assert_called_once()
    
    def test_get_session_user(self, auth_manager_with_mock):
        """Testa recuperação do usuário da sessão"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        # Mock da sessão Streamlit
        with patch('streamlit.session_state', {'user': {'id': 1, 'nome': 'João'}}):
            user = auth_manager.get_session_user()
            assert user is not None
            assert user['id'] == 1
            assert user['nome'] == 'João'
    
    def test_is_admin_true(self, auth_manager_with_mock):
        """Testa verificação de admin - usuário admin"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        with patch('streamlit.session_state', {'user': {'perfil': 'admin'}}):
            assert auth_manager.is_admin() is True
    
    def test_is_admin_false(self, auth_manager_with_mock):
        """Testa verificação de admin - usuário comum"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        with patch('streamlit.session_state', {'user': {'perfil': 'usuario'}}):
            assert auth_manager.is_admin() is False
    
    def test_is_admin_no_user(self, auth_manager_with_mock):
        """Testa verificação de admin sem usuário logado"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        with patch('streamlit.session_state', {}):
            assert auth_manager.is_admin() is False
    
    def test_require_auth_with_user(self, auth_manager_with_mock):
        """Testa require_auth com usuário logado"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        with patch('streamlit.session_state', {'user': {'id': 1}}):
            # Não deve lançar exceção
            auth_manager.require_auth()
    
    def test_require_admin_with_admin(self, auth_manager_with_mock):
        """Testa require_admin com usuário admin"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        with patch('streamlit.session_state', {'user': {'perfil': 'admin'}}):
            # Não deve lançar exceção
            auth_manager.require_admin()
    
    def test_logout(self, auth_manager_with_mock):
        """Testa logout do usuário"""
        auth_manager, mock_cursor, mock_connection = auth_manager_with_mock
        
        with patch('streamlit.session_state', {'user': {'id': 1}}) as mock_session:
            auth_manager.logout()
            # Verifica se user foi removido da sessão
            assert 'user' not in mock_session


@pytest.mark.integration  
class TestAuthenticationIntegrationReal:
    """Testes de integração abrangentes para autenticação"""
    
    def test_full_user_lifecycle(self):
        """Testa ciclo completo de usuário com mocks realísticos"""
        with patch('modules.auth.db') as mock_db, \
             patch('streamlit.session_state', new_callable=dict) as mock_session:
            
            # Configurar mocks
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_db.get_connection.return_value = mock_connection
            
            from modules.auth import AuthenticationManager
            auth_manager = AuthenticationManager()
            
            # 1. Criar usuário
            mock_cursor.fetchone.side_effect = [None, (1,)]  # Email não existe, criação bem-sucedida
            success, _ = auth_manager.create_user("João Silva", "joao@test.com", "Senha123@")
            assert success is True
            
            # 2. Autenticar usuário
            password = "Senha123@"
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user_data = (1, 'João Silva', 'joao@test.com', hashed, 'usuario', True)
            mock_cursor.fetchone.return_value = user_data
            
            user = auth_manager.authenticate_user("joao@test.com", password)
            assert user is not None
            assert user['nome'] == 'João Silva'
            
            # 3. Alterar senha
            mock_cursor.fetchone.return_value = (hashed,)
            success, _ = auth_manager.change_password(1, password, "NovaSenha123@")
            assert success is True
            
            # 4. Desativar usuário (admin)
            mock_cursor.fetchone.side_effect = [(True,), (1,)]
            success, _ = auth_manager.toggle_user_status(1, 2)
            assert success is True
            
            # 5. Reativar usuário
            mock_cursor.fetchone.side_effect = [(False,), (1,)]
            success, _ = auth_manager.toggle_user_status(1, 2)
            assert success is True
    
    def test_authentication_workflow_with_logging(self):
        """Testa workflow de autenticação com logs completos"""
        with patch('modules.auth.db') as mock_db:
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_db.get_connection.return_value = mock_connection
            
            from modules.auth import AuthenticationManager
            auth_manager = AuthenticationManager()
            
            # Criar usuário com log
            mock_cursor.fetchone.side_effect = [None, (1,)]
            success, _ = auth_manager.create_user(
                "Admin User", "admin@test.com", "Admin123@", "admin", 1
            )
            assert success is True
            
            # Verificar que log_action foi chamado (implícito no create_user)
            assert mock_cursor.execute.call_count >= 3  # CHECK email + INSERT user + LOG action
    
    def test_password_security_workflow(self):
        """Testa workflow completo de segurança de senhas"""
        with patch('modules.auth.db') as mock_db:
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_db.get_connection.return_value = mock_connection
            
            from modules.auth import AuthenticationManager
            auth_manager = AuthenticationManager()
            
            # 1. Tentar senha fraca - deve falhar
            success, message = auth_manager.create_user(
                "Test User", "test@example.com", "123"
            )
            assert success is False
            assert "pelo menos 8 caracteres" in message
            
            # 2. Tentar senha sem maiúscula - deve falhar
            success, message = auth_manager.create_user(
                "Test User", "test@example.com", "minhasenha123"
            )
            assert success is False
            assert "maiúscula" in message
            
            # 3. Senha forte - deve passar
            mock_cursor.fetchone.side_effect = [None, (1,)]
            success, message = auth_manager.create_user(
                "Test User", "test@example.com", "MinhaSenh@123"
            )
            assert success is True
    
    def test_admin_operations_workflow(self):
        """Testa workflow completo de operações administrativas"""
        with patch('modules.auth.db') as mock_db, \
             patch('streamlit.session_state', {'user': {'perfil': 'admin'}}) as mock_session:
            
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_db.get_connection.return_value = mock_connection
            
            from modules.auth import AuthenticationManager
            auth_manager = AuthenticationManager()
            
            # Verificar se é admin
            assert auth_manager.is_admin() is True
            
            # Reset de senha por admin
            mock_cursor.fetchone.return_value = (1,)
            success, _ = auth_manager.reset_password(1, "NovaSenh@123", 2)
            assert success is True
            
            # Toggle status de usuário
            mock_cursor.fetchone.side_effect = [(True,), (1,)]
            success, _ = auth_manager.toggle_user_status(1, 2)
            assert success is True
    
    def test_session_management_workflow(self):
        """Testa workflow completo de gerenciamento de sessão"""
        with patch('modules.auth.db') as mock_db:
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_db.get_connection.return_value = mock_connection
            
            from modules.auth import AuthenticationManager
            auth_manager = AuthenticationManager()
            
            # Simular login
            password = "Senha123@"
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user_data = (1, 'João Silva', 'joao@test.com', hashed, 'admin', True)
            mock_cursor.fetchone.return_value = user_data
            
            user = auth_manager.authenticate_user("joao@test.com", password)
            assert user is not None
            
            # Simular sessão ativa
            with patch('streamlit.session_state', {'user': user}) as mock_session:
                # Verificar sessão
                session_user = auth_manager.get_session_user()
                assert session_user == user
                
                # Verificar admin
                assert auth_manager.is_admin() is True
                
                # Logout
                auth_manager.logout()
                assert 'user' not in mock_session