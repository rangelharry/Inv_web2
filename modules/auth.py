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
    
    def validate_password_strength(self, password: str) -> tuple[bool, list[str]]:
        """Valida força da senha"""
        errors = []
        
        if len(password) < 8:
            errors.append("Senha deve ter pelo menos 8 caracteres")
        if not re.search(r'[A-Z]', password):
            errors.append("Senha deve conter pelo menos uma letra maiúscula")
        if not re.search(r'[a-z]', password):
            errors.append("Senha deve conter pelo menos uma letra minúscula")
        if not re.search(r'[0-9]', password):
            errors.append("Senha deve conter pelo menos um número")
        
        return len(errors) == 0, errors
    
    def create_user(self, nome: str, email: str, password: str, perfil: str = 'usuario', criado_por: Optional[int] = None) -> Tuple[bool, str]:
        """Cria novo usuário"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Validações
            if not self.validate_email(email):
                return False, "Email inválido"
            
            is_strong, errors = self.validate_password_strength(password)
            if not is_strong:
                return False, "; ".join(errors)
            
            # Verifica se email já existe
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            if cursor.fetchone():
                return False, "Email já está em uso"
            
            # Cria usuário
            password_hash = self.hash_password(password)
            cursor.execute("""
            INSERT INTO usuarios (nome, email, password_hash, perfil, ativo)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, (nome, email, password_hash, perfil, True))
            
            result = cursor.fetchone()
            user_id = result[0] if result else None
            conn.commit()
            
            # Log da ação
            if user_id:
                self.log_action(
                    user_id,
                    'criar',
                    'usuarios',
                    user_id,
                    f'Usuário criado: {nome} ({email})'
                )
            
            return True, f"Usuário {nome} criado com sucesso!"
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            return False, f"Erro ao criar usuário: {e}"
    
    def authenticate_user(self, email: str, password: str):
        """Autentica usuário"""
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
            user_id, nome, email, password_hash, perfil, ativo = user
            if not ativo:
                return False, "Usuário inativo", None
            print(f"[DEBUG] Hash lido do banco: {repr(password_hash)} | Tipo: {type(password_hash)} | Tamanho: {len(password_hash) if password_hash else 0}")
            # Se o hash vier como bytes, converte para string e limpa espaços/quebras
            if isinstance(password_hash, bytes):
                password_hash = password_hash.decode('utf-8')
            password_hash = str(password_hash).strip()
            print(f"[DEBUG] Hash após tratamento: {repr(password_hash)} | Tamanho: {len(password_hash)}")
            if self.verify_password(password, password_hash):
                # Atualiza último login
                cursor.execute("""
                    UPDATE usuarios 
                    SET ultimo_login = %s 
                    WHERE id = %s
                """, (datetime.now(), user_id))
                conn.commit()
                # Log de login
                self.log_action(user_id, 'login', 'usuarios', user_id, 'Login realizado')
                return True, "Login realizado com sucesso", {
                    'id': user_id,
                    'nome': nome,
                    'email': email,
                    'perfil': perfil
                }
            return False, "Senha incorreta", None
        except Exception as e:
            print(f"[DEBUG] Exceção na autenticação: {e}")
            return False, f"Erro na autenticação: {e}", None
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Altera senha do usuário"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Validações
            is_strong, errors = self.validate_password_strength(new_password)
            if not is_strong:
                return False, "; ".join(errors)
            
            # Verifica senha atual
            cursor.execute("SELECT password_hash FROM usuarios WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            if not result or not self.verify_password(old_password, result[0]):
                return False, "Senha atual incorreta"
            
            # Atualiza senha
            new_hash = self.hash_password(new_password)
            cursor.execute("""
                UPDATE usuarios 
                SET password_hash = %s, senha_alterada_em = %s 
                WHERE id = %s
            """, (new_hash, datetime.now(), user_id))
            conn.commit()
            
            # Log
            self.log_action(user_id, 'alterar_senha', 'usuarios', user_id, 'Senha alterada')
            
            return True, "Senha alterada com sucesso!"
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            return False, f"Erro ao alterar senha: {e}"
    
    def get_users(self) -> list[dict]:
        """Retorna lista de usuários"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, nome, email, perfil, ativo, criado_em, ultimo_login
                FROM usuarios 
                ORDER BY nome
            """)
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'nome': row[1],
                    'email': row[2],
                    'perfil': row[3],
                    'ativo': row[4],
                    'criado_em': row[5],
                    'ultimo_login': row[6]
                })
            
            return users
            
        except Exception as e:
            print(f"Erro ao listar usuários: {e}")
            return []
    
    def toggle_user_status(self, user_id: int, admin_user_id: int) -> Tuple[bool, str]:
        """Ativa/desativa usuário"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Verifica status atual
            cursor.execute("SELECT ativo, nome FROM usuarios WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            if not result:
                return False, "Usuário não encontrado"
            
            current_status, nome = result
            new_status = not current_status
            
            # Atualiza status
            cursor.execute("""
                UPDATE usuarios 
                SET ativo = %s 
                WHERE id = %s
            """, (new_status, user_id))
            conn.commit()
            
            # Log
            action = 'ativar' if new_status else 'desativar'
            self.log_action(admin_user_id, action, 'usuarios', user_id, f'Usuário {action}do: {nome}')
            
            status_text = "ativado" if new_status else "desativado"
            return True, f"Usuário {nome} {status_text} com sucesso!"
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            return False, f"Erro ao alterar status: {e}"
    
    def reset_password(self, user_id: int, new_password: str, admin_user_id: int) -> Tuple[bool, str]:
        """Reset de senha por administrador"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Validação da nova senha
            is_strong, errors = self.validate_password_strength(new_password)
            if not is_strong:
                return False, "; ".join(errors)
            
            # Atualiza senha
            new_hash = self.hash_password(new_password)
            cursor.execute("""
                UPDATE usuarios 
                SET password_hash = %s, senha_alterada_em = %s 
                WHERE id = %s
            """, (new_hash, datetime.now(), user_id))
            conn.commit()
            
            # Log
            cursor.execute("SELECT nome FROM usuarios WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            nome = user[0] if user else f"ID {user_id}"
            
            self.log_action(admin_user_id, 'reset_senha', 'usuarios', user_id, f'Senha resetada para: {nome}')
            
            return True, f"Senha resetada com sucesso para {nome}!"
            
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            return False, f"Erro ao resetar senha: {e}"
    
    def log_action(self, user_id: int, action: str, table_name: str, item_id: Optional[int], details: str = ""):
        """Registra ação no log de auditoria"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Pega nome do usuário
            cursor.execute("SELECT nome FROM usuarios WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            # Insere log
            cursor.execute("""
            INSERT INTO logs_auditoria (user_id, user_name, action, table_name, item_id, details, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, user[0] if user else f"ID {user_id}", action, table_name, item_id, details, datetime.now()))
            
            conn.commit()
            
        except Exception as e:
            print(f"Erro ao registrar log: {e}")
    
    def get_session_user(self) -> Optional[dict]:
        """Retorna usuário da sessão atual"""
        if 'user' in st.session_state:
            return st.session_state.user
        return None
    
    def is_admin(self) -> bool:
        """Verifica se usuário atual é admin"""
        user = self.get_session_user()
        return user and user.get('perfil') == 'admin'
    
    def require_auth(self):
        """Decorator/middleware para páginas que requerem autenticação"""
        if 'user' not in st.session_state:
            st.error("Acesso negado. Faça login primeiro.")
            st.stop()
    
    def require_admin(self):
        """Decorator/middleware para páginas que requerem admin"""
        self.require_auth()
        if not self.is_admin():
            st.error("Acesso negado. Apenas administradores podem acessar esta página.")
            st.stop()
    
    def logout(self):
        """Faz logout do usuário"""
        if 'user' in st.session_state:
            user = st.session_state.user
            self.log_action(user['id'], 'logout', 'usuarios', user['id'], 'Logout realizado')
            del st.session_state.user
        
        # Limpa outros dados da sessão se necessário
        for key in list(st.session_state.keys()):
            if key.startswith('auth_'):
                del st.session_state[key]

# Instância global do gerenciador de autenticação
auth_manager = AuthenticationManager()