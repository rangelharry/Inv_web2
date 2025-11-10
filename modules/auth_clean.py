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

# Instância global do gerenciador de autenticação
auth_manager = AuthenticationManager()