"""
Sistema de Inventário Web - Módulo de Autenticação
Gerenciamento de usuários, login, permissões e auditoria
"""

import streamlit as st
from typing import Any
import bcrypt
import secrets
from datetime import datetime, timedelta
import re
from database.connection import db

class AuthenticationManager:
    def __init__(self):
        self.conn = db.get_connection()
    
    def hash_password(self, password: str) -> str:
        """Gera hash seguro da senha"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verifica se a senha confere com o hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_token(self) -> str:
        """Gera token único para sessão"""
        return secrets.token_hex(32)
    
    def validate_email(self, email: str) -> bool:
        """Valida formato do email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password_strength(self, password: str) -> tuple[bool, list[str]]:
        """Valida força da senha"""
        errors: list[str] = []
        
        if len(password) < 6:
            errors.append("Senha deve ter pelo menos 6 caracteres")
        
        if not re.search(r'[A-Za-z]', password):
            errors.append("Senha deve conter pelo menos uma letra")
        
        if not re.search(r'[0-9]', password):
            errors.append("Senha deve conter pelo menos um número")
        
        return len(errors) == 0, errors
    
    def create_user(self, nome: str, email: str, password: str, perfil: str = 'usuario', criado_por: int | None = None) -> tuple[bool, str]:
        """Cria novo usuário"""
        try:
            cursor = self.conn.cursor()
            
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
            INSERT INTO usuarios (nome, email, password_hash, perfil, ativo, criado_por)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """, (nome, email, password_hash, perfil, True, criado_por))
            
            result = cursor.fetchone()
            user_id = result['id'] if result else None
            self.conn.commit()
            
            # Log da ação
            log_user_id = user_id if criado_por is None else criado_por
            if log_user_id is not None:
                self.log_action(
                    log_user_id,
                    'criar',
                    'usuarios',
                    user_id,
                    f"Usuario criado: {nome} ({email})"
                )
            
            return True, f"Usuário {nome} criado com sucesso"
            
        except Exception as e:
            print(str(e))
            return False, f"Erro ao criar usuário: {str(e)}"
    
    def authenticate_user(self, email: str, password: str) -> tuple[bool, str, dict[str, Any] | None]:
        """Autentica usuário"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
            SELECT id, nome, email, password_hash, perfil, ativo 
            FROM usuarios WHERE email = %s
            """, (email,))
            
            user = cursor.fetchone()
            
            if not user:
                return False, "Email não encontrado", None
            
            if not user['ativo']:
                return False, "Usuário inativo", None
            
            if not self.verify_password(password, user['password_hash']):
                return False, "Senha incorreta", None
            
            # Atualiza último login
            cursor.execute("""
            UPDATE usuarios SET ultimo_login = CURRENT_TIMESTAMP WHERE id = %s
            """, (user['id'],))
            
            self.conn.commit()
            
            # Log do login
            self.log_action(user['id'], 'login', 'sistema', None, f"Login realizado: {email}")
            
            return True, "Login realizado com sucesso", dict(user)
            
        except Exception as e:
            print(str(e))
            return False, f"Erro na autenticação: {str(e)}", None
    
    def create_session(self, user_id: int) -> str:
        """Cria sessão para usuário"""
        try:
            cursor = self.conn.cursor()
            
            token = self.generate_token()
            expiration = datetime.now() + timedelta(hours=8)
            
            cursor.execute("""
            INSERT INTO sessoes (usuario_id, token, data_expiracao, ativo)
            VALUES (%s, %s, %s, %s)
            """, (user_id, token, expiration, 1))
            
            self.conn.commit()
            return token
            
        except Exception as e:
            print(str(e))
            st.error(f"Erro ao criar sessão: {e}")
            return ""
    
    def validate_session(self, token: str) -> tuple[bool, dict[str, Any] | None]:
        """Valida sessão ativa"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
            SELECT s.*, u.id as user_id, u.nome, u.email, u.perfil, u.ativo
            FROM sessoes s
            JOIN usuarios u ON s.usuario_id = u.id
            WHERE s.token = %s AND s.ativo = true AND s.data_expiracao > CURRENT_TIMESTAMP
            """, (token,))
            
            session = cursor.fetchone()
            
            if not session:
                return False, None
            
            if not session['ativo']:
                return False, None
            
            return True, dict(session)
            
        except Exception as e:
            print(str(e))
            return False, None
    
    def logout_user(self, token: str | None = None, user_id: int | None = None):
        """Faz logout do usuário"""
        try:
            cursor = self.conn.cursor()
            
            if token:
                cursor.execute("UPDATE sessoes SET ativo = false WHERE token = %s", (token,))
            elif user_id:
                cursor.execute("UPDATE sessoes SET ativo = false WHERE usuario_id = %s", (user_id,))
            
            self.conn.commit()
            
            # Log do logout
            if user_id:
                self.log_action(user_id, 'logout', 'sistema', None, "Logout realizado")
                
        except Exception as e:
            print(str(e))
            st.error(f"Erro no logout: {e}")
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
        """Altera senha do usuário"""
        try:
            cursor = self.conn.cursor()
            
            # Busca usuário atual
            cursor.execute("SELECT password_hash FROM usuarios WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return False, "Usuário não encontrado"
            
            # Verifica senha atual
            if not self.verify_password(old_password, user['password_hash']):
                return False, "Senha atual incorreta"
            
            # Valida nova senha
            is_strong, errors = self.validate_password_strength(new_password)
            if not is_strong:
                return False, "; ".join(errors)
            
            # Atualiza senha
            new_hash = self.hash_password(new_password)
            cursor.execute("""
            UPDATE usuarios SET password_hash = %s WHERE id = %s
            """, (new_hash, user_id))
            
            self.conn.commit()
            
            # Log da ação
            self.log_action(user_id, 'editar', 'usuarios', user_id, "Senha alterada")
            
            return True, "Senha alterada com sucesso"
            
        except Exception as e:
            print(str(e))
            return False, f"Erro ao alterar senha: {str(e)}"
    
    def get_users(self, active_only: bool = True) -> list[dict[str, Any]]:
        """Lista usuários do sistema"""
        try:
            cursor = self.conn.cursor()
            
            query = "SELECT * FROM usuarios"
            if active_only:
                query += " WHERE ativo = 1"
            query += " ORDER BY nome"
            
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            print(str(e))
            st.error(f"Erro ao buscar usuários: {e}")
            return []
    
    def update_user(self, user_id: int, nome: str, email: str, perfil: str, ativo: bool, updated_by: int) -> tuple[bool, str]:
        """Atualiza dados do usuário"""
        try:
            cursor = self.conn.cursor()
            
            # Busca dados atuais
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
            old_data = dict(cursor.fetchone())
            
            # Validações
            if not self.validate_email(email):
                return False, "Email inválido"
            
            # Verifica se email já existe em outro usuário
            cursor.execute("SELECT id FROM usuarios WHERE email = %s AND id != %s", (email, user_id))
            if cursor.fetchone():
                return False, "Email já está em uso por outro usuário"
            
            # Atualiza usuário
            cursor.execute("""
            UPDATE usuarios SET nome = %s, email = %s, perfil = %s, ativo = %s
            WHERE id = %s
            """, (nome, email, perfil, ativo, user_id))
            
            self.conn.commit()
            
            # Log da ação
            new_data: dict[str, Any] = {
                'nome': nome, 'email': email, 'perfil': perfil, 'ativo': ativo
            }
            
            self.log_action(
                updated_by,
                'editar',
                'usuarios',
                user_id,
                f"Usuario atualizado: {nome}",
                str(old_data),
                str(new_data)
            )
            
            return True, "Usuário atualizado com sucesso"
            
        except Exception as e:
            print(str(e))
            return False, f"Erro ao atualizar usuário: {str(e)}"
    
    def delete_user(self, user_id: int, deleted_by: int) -> tuple[bool, str]:
        """Remove usuário (soft delete)"""
        try:
            cursor = self.conn.cursor()
            
            # Busca dados do usuário
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                return False, "Usuário não encontrado"
            
            # Inativa usuário
            cursor.execute("UPDATE usuarios SET ativo = false WHERE id = %s", (user_id,))
            
            # Inativa todas as sessões
            cursor.execute("UPDATE sessoes SET ativo = false WHERE usuario_id = %s", (user_id,))
            
            self.conn.commit()
            
            # Log da ação
            self.log_action(
                deleted_by, 
                'excluir', 
                'usuarios', 
                user_id, 
                f"Usuario removido: {user_data['nome']}"
            )
            
            return True, f"Usuário {user_data['nome']} removido com sucesso"
            
        except Exception as e:
            print(str(e))
            return False, f"Erro ao remover usuário: {str(e)}"
    
    def log_action(self, user_id: int, action: str, module: str, item_id: int | None = None, 
                  notes: str = "", old_data: str = "", new_data: str = ""):
        """Registra ação no log de auditoria"""
        try:
            cursor = self.conn.cursor()
            
            # Busca nome do usuário
            cursor.execute("SELECT nome FROM usuarios WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            user_name = user['nome'] if user else 'Sistema'
            
            cursor.execute("""
            INSERT INTO logs_auditoria 
            (usuario_id, usuario_nome, acao, modulo, item_id, dados_anteriores, dados_novos, observacoes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, user_name, action, module, item_id, old_data, new_data, notes))
            
            self.conn.commit()
            
        except Exception as e:
            print(str(e))
            print(f"Erro ao registrar log: {e}")
    
    def check_permission(self, user_profile: str, required_permission: str) -> bool:
        """Verifica permissões do usuário"""
        permissions = {
            'admin': ['create', 'read', 'update', 'delete', 'manage_users', 'view_reports', 'manage_system'],
            'gestor': ['create', 'read', 'update', 'view_reports', 'manage_items'],
            'usuario': ['read', 'create_basic', 'update_basic']
        }
        
        user_permissions = permissions.get(user_profile, [])
        return required_permission in user_permissions
    
    def get_user_permissions(self, user_profile: str) -> list[str]:
        """Retorna lista de permissões do usuário"""
        permissions = {
            'admin': ['create', 'read', 'update', 'delete', 'manage_users', 'view_reports', 'manage_system'],
            'gestor': ['create', 'read', 'update', 'view_reports', 'manage_items'],
            'usuario': ['read', 'create_basic', 'update_basic']
        }
        
        return permissions.get(user_profile, [])

# Instância global do gerenciador de autenticação
auth_manager = AuthenticationManager()
