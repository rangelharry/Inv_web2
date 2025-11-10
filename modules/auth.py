"""
Sistema de Inventário Web - Módulo de Autenticação
Gerenciamento de usuários, login, permissões e auditoria
"""

import streamlit as st
from typing import Any, Optional, Tuple
import bcrypt
import secrets
from datetime import datetime, timedelta
import re
from database.connection import db
import psycopg2

class AuthenticationManager:
    def __init__(self):
        self.db = db
    
    def get_connection(self):
        """Obtém conexão com tratamento de erro e retry"""
        try:
            return self.db.get_connection()
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            print(f"Erro de conexão: {e}. Tentando reconectar...")
            return self.db.get_connection()  # Reconecta automaticamente
    
    def hash_password(self, password: str) -> str:
        """Gera hash seguro da senha"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verifica se a senha confere com o hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def validate_email(self, email: str) -> bool:
        """Valida formato do email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def authenticate_user(self, email: str, password: str) -> Tuple[bool, str, Optional[dict]]:
        """Autentica usuário - Retorna (sucesso, mensagem, dados_usuario)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, nome, email, password_hash, perfil, ativo
                FROM usuarios 
                WHERE email = %s
            """, (email,))
            
            user = cursor.fetchone()
            if not user:
                return False, "Usuário não encontrado", None
            
            user_id = user['id']
            nome = user['nome'] 
            email_db = user['email']
            password_hash = user['password_hash']
            perfil = user['perfil']
            ativo = user['ativo']
            
            if not ativo:
                return False, "Usuário inativo", None
            
            if self.verify_password(password, password_hash):
                # Atualiza último login se coluna existir
                try:
                    cursor.execute("""
                        UPDATE usuarios 
                        SET ultimo_login = %s 
                        WHERE id = %s
                    """, (datetime.now(), user_id))
                    conn.commit()
                except:
                    # Coluna pode não existir, ignora erro
                    pass
                
                user_info = {
                    'id': user_id,
                    'nome': nome,
                    'email': email_db,
                    'perfil': perfil
                }
                
                return True, "Login realizado com sucesso", user_info
            
            return False, "Senha incorreta", None
            
        except Exception as e:
            print(f"Erro na autenticação: {e}")
            return False, f"Erro na autenticação: {e}", None
    
    def get_session_user(self) -> Optional[dict]:
        """Retorna usuário da sessão atual"""
        try:
            if hasattr(st.session_state, 'user') and st.session_state.user is not None:
                return st.session_state.user
            return None
        except:
            return None
    
    def is_admin(self) -> bool:
        """Verifica se usuário atual é admin"""
        try:
            user = self.get_session_user()
            if user and user.get('perfil') == 'admin':
                return True
            return False
        except:
            return False
    
    def create_session(self, user_id: int) -> str:
        """Cria sessão para o usuário e retorna token"""
        try:
            # Gera token da sessão
            session_token = secrets.token_urlsafe(32)
            
            # Salva usuário na sessão do Streamlit
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, nome, email, perfil, ativo
                FROM usuarios 
                WHERE id = %s
            """, (user_id,))
            
            user = cursor.fetchone()
            if user:
                user_info = {
                    'id': user['id'],
                    'nome': user['nome'],
                    'email': user['email'],
                    'perfil': user['perfil']
                }
                
                # Salva na sessão
                st.session_state.user = user_info
                st.session_state.session_token = session_token
                
            return session_token
            
        except Exception as e:
            print(f"Erro ao criar sessão: {e}")
            return ""
    
    def logout(self):
        """Faz logout do usuário"""
        try:
            # Limpa dados da sessão
            if 'user' in st.session_state:
                del st.session_state.user
            if 'session_token' in st.session_state:
                del st.session_state.session_token
                
            # Limpa outros dados relacionados à autenticação
            keys_to_remove = [key for key in st.session_state.keys() if key.startswith('auth_')]
            for key in keys_to_remove:
                del st.session_state[key]
                
        except Exception as e:
            print(f"Erro no logout: {e}")
    
    def require_auth(self):
        """Verifica se usuário está autenticado"""
        if 'user' not in st.session_state:
            st.error("⚠️ Acesso negado. Faça login primeiro.")
            st.stop()
    
    def require_admin(self):
        """Verifica se usuário é admin"""
        self.require_auth()
        if not self.is_admin():
            st.error("⚠️ Acesso negado. Apenas administradores podem acessar esta página.")
            st.stop()
    
    def check_permission(self, user_perfil: str, action: str) -> bool:
        """Verifica permissões do usuário"""
        permissions = {
            'admin': ['create', 'read', 'update', 'delete'],
            'gestor': ['create', 'read', 'update'],
            'usuario': ['read']
        }
        
        user_permissions = permissions.get(user_perfil, [])
        return action in user_permissions
    
    def log_action(self, user_id: int, action: str, table_name: str, item_id=None, details: str = ""):
        """Registra ação no log de auditoria (método simplificado)"""
        try:
            # Para compatibilidade - apenas imprime no console por enquanto
            print(f"LOG: User {user_id} - {action} on {table_name} (item: {item_id}) - {details}")
        except Exception as e:
            print(f"Erro ao registrar log: {e}")

# Instância global do gerenciador de autenticação
auth_manager = AuthenticationManager()