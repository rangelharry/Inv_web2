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
    
    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """Busca usuário por ID"""
        try:
            # Converter para int nativo do Python
            user_id = int(user_id)
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, nome, email, perfil, ativo 
                FROM usuarios 
                WHERE id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            if result:
                if isinstance(result, dict):
                    return result
                else:
                    return {
                        'id': result[0],
                        'nome': result[1], 
                        'email': result[2],
                        'perfil': result[3],
                        'ativo': result[4]
                    }
            return None
            
        except Exception as e:
            print(f"Erro ao buscar usuário por ID: {e}")
            return None
    
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
    
    def get_user_module_permissions(self, user_id: int) -> dict[str, bool]:
        """Obtém permissões de módulos do usuário"""
        try:
            # Converter para int nativo do Python para evitar problemas com numpy
            user_id = int(user_id)
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT modulo, acesso 
                FROM permissoes_modulos 
                WHERE usuario_id = %s
            """, (user_id,))
            
            results = cursor.fetchall()
            permissions = {}
            
            for result in results:
                if isinstance(result, dict):
                    permissions[result['modulo']] = result['acesso']
                else:
                    permissions[result[0]] = result[1]
            
            # Se não tem permissões cadastradas, usar padrões baseados no perfil
            if not permissions:
                return self._get_default_permissions_by_profile(user_id)
            
            return permissions
            
        except Exception as e:
            print(f"Erro ao buscar permissões de módulo: {e}")
            # Fallback: retornar permissões baseadas no perfil
            return self._get_default_permissions_by_profile(user_id)
    
    def _get_default_permissions_by_profile(self, user_id: int) -> dict[str, bool]:
        """Obtém permissões padrão baseadas no perfil do usuário"""
        try:
            user_data = self.get_user_by_id(user_id)
            if not user_data:
                return {'dashboard': True}  # Acesso mínimo
            
            perfil = user_data.get('perfil', 'usuario')
            
            if perfil == 'admin':
                # Admin tem acesso a tudo
                return {
                    'dashboard': True,
                    'insumos': True,
                    'equipamentos_eletricos': True,
                    'equipamentos_manuais': True,
                    'movimentacao': True,
                    'obras': True,
                    'responsaveis': True,
                    'relatorios': True,
                    'logs': True,
                    'usuarios': True,
                    'configuracoes': True,
                    'qr_codes': True,
                    'reservas': True,
                    'manutencao': True,
                    'dashboard_exec': True,
                    'localizacao': True,
                    'financeiro': True,
                    'analise': True,
                    'subcontratados': True,
                    'relatorios_custom': True,
                    'metricas': True,
                    'backup': True,
                    'lgpd': True,
                    'orcamentos': True,
                    'faturamento': True,
                    'integracao': True
                }
            elif perfil == 'gestor':
                # Gestor tem acesso limitado
                return {
                    'dashboard': True,
                    'insumos': True,
                    'equipamentos_eletricos': True,
                    'equipamentos_manuais': True,
                    'movimentacao': True,
                    'obras': True,
                    'responsaveis': True,
                    'relatorios': True,
                    'qr_codes': True,
                    'reservas': True,
                    'manutencao': True,
                    'localizacao': True,
                    'financeiro': True,
                    'relatorios_custom': True,
                    'metricas': True
                }
            else:
                # Usuário normal tem acesso básico
                return {
                    'dashboard': True,
                    'insumos': True,
                    'equipamentos_eletricos': True,
                    'equipamentos_manuais': True,
                    'relatorios': True
                }
                
        except Exception as e:
            print(f"Erro ao obter perfil do usuário: {e}")
            return {'dashboard': True}
    
    def check_module_permission(self, user_id: int, module: str) -> bool:
        """Verifica se usuário tem acesso ao módulo específico"""
        try:
            # Dashboard sempre acessível
            if module == 'dashboard':
                return True
                
            permissions = self.get_user_module_permissions(user_id)
            return permissions.get(module, False)
        except Exception as e:
            print(f"Erro ao verificar permissão do módulo: {e}")
            # Dashboard sempre acessível mesmo em caso de erro
            return module == 'dashboard'
    
    def update_user_module_permissions(self, user_id: int, permissions: dict[str, bool]) -> bool:
        """Atualiza permissões de módulos do usuário"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            for modulo, acesso in permissions.items():
                cursor.execute("""
                    INSERT INTO permissoes_modulos (usuario_id, modulo, acesso)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (usuario_id, modulo) 
                    DO UPDATE SET acesso = EXCLUDED.acesso
                """, (user_id, modulo, acesso))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Erro ao atualizar permissões: {e}")
            conn.rollback()
            return False
    
    def logout_user(self, token: str = None) -> bool:
        """Realiza logout do usuário limpando a sessão"""
        try:
            # Limpar dados da sessão
            if 'authenticated' in st.session_state:
                del st.session_state.authenticated
            if 'user_data' in st.session_state:
                del st.session_state.user_data
            if 'session_token' in st.session_state:
                del st.session_state.session_token
            
            # Registrar logout no log de auditoria se houver usuário logado
            if token and 'user_data' in st.session_state:
                user_id = st.session_state.user_data.get('id')
                if user_id:
                    self.log_user_action(user_id, "logout", "Sistema", "Logout realizado com sucesso")
            
            return True
            
        except Exception as e:
            print(f"Erro ao realizar logout: {e}")
            return False

# Instância global do gerenciador de autenticação
auth_manager = AuthenticationManager()