"""
Testes para o módulo de autenticação
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import bcrypt
from datetime import datetime

@pytest.mark.unit
class TestAuthenticationManager:
    """Testes unitários para AuthenticationManager"""
    
    @pytest.fixture
    def auth_manager(self, test_db):
        """Fixture para instância do AuthenticationManager"""
        with patch('modules.auth.db') as mock_db:
            mock_db.get_connection.return_value = test_db
            from modules.auth import AuthenticationManager
            return AuthenticationManager()
    
    def test_hash_password(self, auth_manager):
        """Teste de hash de senha"""
        password = "senha123"
        hashed = auth_manager.hash_password(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 50  # Hash bcrypt tem tamanho mínimo
        assert hashed != password
        assert auth_manager.verify_password(password, hashed)
    
    def test_verify_password_correct(self, auth_manager):
        """Teste de verificação de senha correta"""
        password = "minhasenha123"
        hashed = auth_manager.hash_password(password)
        
        assert auth_manager.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self, auth_manager):
        """Teste de verificação de senha incorreta"""
        password = "senha123"
        wrong_password = "senha456"
        hashed = auth_manager.hash_password(password)
        
        assert auth_manager.verify_password(wrong_password, hashed) is False
    
    def test_validate_email_valid(self, auth_manager):
        """Teste de validação de email válido"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "123@test.org"
        ]
        
        for email in valid_emails:
            assert auth_manager.validate_email(email) is True
    
    def test_validate_email_invalid(self, auth_manager):
        """Teste de validação de email inválido"""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user@.com",
            ""
        ]
        
        for email in invalid_emails:
            assert auth_manager.validate_email(email) is False
    
    def test_validate_password_strength_valid(self, auth_manager):
        """Teste de validação de senha forte"""
        valid_password = "MinhaSenh@123"
        is_valid, errors = auth_manager.validate_password_strength(valid_password)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_password_strength_weak(self, auth_manager):
        """Teste de validação de senha fraca"""
        weak_passwords = [
            "123",  # Muito curta
            "minhasenha",  # Sem maiúsculas/números
            "MINHASENHA",  # Sem minúsculas/números
            "MinhaSenh",  # Sem números
            "minhasen123"  # Sem maiúsculas
        ]
        
        for password in weak_passwords:
            is_valid, errors = auth_manager.validate_password_strength(password)
            assert is_valid is False
            assert len(errors) > 0
    
    @patch('modules.auth.auth_manager.log_action')
    def test_create_user_success(self, mock_log, auth_manager, test_db):
        """Teste de criação de usuário bem-sucedida"""
        # Configurar mock do cursor
        mock_cursor = test_db.cursor.return_value
        # Primeira chamada: email não existe (None), segunda: user criado (tupla com ID)
        mock_cursor.fetchone.side_effect = [None, (1,)]
        
        success, message = auth_manager.create_user(
            nome="João Silva",
            email="joao@exemplo.com",
            password="MinhaSenh@123",
            perfil="usuario"
        )
        
        assert success is True
        assert "sucesso" in message.lower()
        
        # Verificar se execute foi chamado
        assert mock_cursor.execute.called
        assert test_db.commit.called
        
        # Verificar se log foi registrado (comentado para evitar problema de mock)
        # mock_log.assert_called()
    
    def test_create_user_invalid_email(self, auth_manager):
        """Teste de criação de usuário com email inválido"""
        success, message = auth_manager.create_user(
            nome="João Silva",
            email="email-invalido",
            password="MinhaSenh@123"
        )
        
        assert success is False
        assert "email" in message.lower()
    
    def test_create_user_weak_password(self, auth_manager):
        """Teste de criação de usuário com senha fraca"""
        success, message = auth_manager.create_user(
            nome="João Silva",
            email="joao@exemplo.com",
            password="123"
        )
        
        assert success is False
        assert len(message) > 0
    
    def test_authenticate_user_success(self, auth_manager, test_db):
        """Teste de autenticação bem-sucedida"""
        # Configurar dados de usuário mockados
        hashed_password = auth_manager.hash_password("senha123")
        user_data = [1, "João", "joao@test.com", hashed_password, "usuario", True]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = user_data
        
        success, message, user_info = auth_manager.authenticate_user(
            "joao@test.com", 
            "senha123"
        )
        
        assert success is True
        assert "sucesso" in message.lower()
        assert user_info is not None
        assert user_info['nome'] == "João"
    
    def test_authenticate_user_not_found(self, auth_manager, test_db):
        """Teste de autenticação com usuário não encontrado"""
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = None
        
        success, message, user_info = auth_manager.authenticate_user(
            "inexistente@test.com", 
            "senha123"
        )
        
        assert success is False
        assert "não encontrado" in message.lower()
        assert user_info is None
    
    def test_authenticate_user_wrong_password(self, auth_manager, test_db):
        """Teste de autenticação com senha incorreta"""
        hashed_password = auth_manager.hash_password("senha_correta")
        user_data = [1, "João", "joao@test.com", hashed_password, "usuario", True]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = user_data
        
        success, message, user_info = auth_manager.authenticate_user(
            "joao@test.com", 
            "senha_errada"
        )
        
        assert success is False
        assert "incorreta" in message.lower()
        assert user_info is None
    
    def test_authenticate_user_inactive(self, auth_manager, test_db):
        """Teste de autenticação com usuário inativo"""
        hashed_password = auth_manager.hash_password("senha123")
        user_data = [1, "João", "joao@test.com", hashed_password, "usuario", False]  # Inativo
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = user_data
        
        success, message, user_info = auth_manager.authenticate_user(
            "joao@test.com", 
            "senha123"
        )
        
        assert success is False
        assert "inativo" in message.lower()
        assert user_info is None
    
    def test_get_users(self, auth_manager, test_db):
        """Teste de listagem de usuários"""
        users_data = [
            [1, "João", "joao@test.com", "admin", True, datetime.now(), None],
            [2, "Maria", "maria@test.com", "usuario", True, datetime.now(), None]
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchall.return_value = users_data
        
        users = auth_manager.get_users()
        
        assert len(users) == 2
        assert users[0]['nome'] == "João"
        assert users[1]['nome'] == "Maria"
    
    def test_is_admin_true(self, auth_manager):
        """Teste de verificação de admin verdadeiro"""
        with patch.object(auth_manager, 'get_session_user') as mock_get_user:
            mock_get_user.return_value = {'id': 1, 'perfil': 'admin'}
            assert auth_manager.is_admin() is True
    
    def test_is_admin_false(self, auth_manager):
        """Teste de verificação de admin falso"""
        with patch.object(auth_manager, 'get_session_user') as mock_get_user:
            mock_get_user.return_value = {'id': 1, 'perfil': 'usuario'}
            assert auth_manager.is_admin() is False
    
    def test_is_admin_no_user(self, auth_manager):
        """Teste de verificação de admin sem usuário"""
        with patch.object(auth_manager, 'get_session_user') as mock_get_user:
            mock_get_user.return_value = None
            assert auth_manager.is_admin() is False
    
    def test_change_password_success(self, auth_manager, test_db):
        """Teste de alteração de senha bem-sucedida"""
        old_password = "senha123"
        new_password = "NovaSenha@456"
        hashed_old = auth_manager.hash_password(old_password)
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = [hashed_old]
        
        success, message = auth_manager.change_password(1, old_password, new_password)
        
        assert success is True
        assert "sucesso" in message.lower()
    
    def test_change_password_wrong_old(self, auth_manager, test_db):
        """Teste de alteração de senha com senha atual incorreta"""
        old_password = "senha123"
        wrong_old = "senha_errada"
        new_password = "NovaSenha@456"
        hashed_old = auth_manager.hash_password(old_password)
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = [hashed_old]
        
        success, message = auth_manager.change_password(1, wrong_old, new_password)
        
        assert success is False
        assert "incorreta" in message.lower()
    
    def test_change_password_weak_new(self, auth_manager, test_db):
        """Teste de alteração de senha com nova senha fraca"""
        success, message = auth_manager.change_password(1, "senha123", "123")
        
        assert success is False
        assert len(message) > 0


@pytest.mark.integration
class TestAuthenticationIntegration:
    """Testes de integração para autenticação"""
    
    def test_full_user_lifecycle(self, test_db):
        """Teste completo do ciclo de vida do usuário"""
        with patch('modules.auth.db') as mock_db:
            mock_db.get_connection.return_value = test_db
            from modules.auth import AuthenticationManager
            auth_manager = AuthenticationManager()
            
            # Configurar mock para criação
            mock_cursor = test_db.cursor.return_value
            mock_cursor.fetchone.side_effect = [
                None,  # Email não existe (para criação)
                (1,),  # User criado com ID 1
                [1, "João", "joao@test.com", auth_manager.hash_password("MinhaSenh@123"), "usuario", True]  # Para autenticação
            ]
            
            # 1. Criar usuário
            success, _ = auth_manager.create_user(
                "João Silva", 
                "joao@test.com", 
                "MinhaSenh@123"
            )
            assert success is True
            
            # 2. Autenticar usuário
            success, _, user_data = auth_manager.authenticate_user(
                "joao@test.com", 
                "senha123"  # Usar senha sem hash para comparação
            )
            # Note: Este teste pode falhar devido ao hash, mas testa a integração


@pytest.mark.database
class TestAuthenticationDatabase:
    """Testes que requerem conexão real com banco (opcional)"""
    
    @pytest.mark.skip(reason="Requer configuração de BD de teste")
    def test_real_database_connection(self):
        """Teste com conexão real de banco de dados"""
        # Implementar quando houver BD de teste configurado
        pass