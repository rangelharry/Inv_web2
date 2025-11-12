"""
Sistema de Inventário Web - Módulo de Gestão de Usuários
Autor: Desenvolvido com IA
Data: 2025
"""

import streamlit as st  # type: ignore
import pandas as pd  # type: ignore
import bcrypt  # type: ignore
from datetime import datetime, date  # type: ignore # noqa: F401
from database.connection import db  # type: ignore
from typing import Any, Dict, List, Optional  # type: ignore

class UsuariosManager:
    """Manager para operações com usuários"""
    
    def __init__(self):
        self.db = db
    
    def create_usuario(self, data: Dict[str, Any]) -> Optional[int]:
        """Cria um novo usuário"""
        conn = None
        try:
            # Obter nova conexão para garantir transação limpa
            conn = self.db.get_connection()  # type: ignore
            cursor = conn.cursor()  # type: ignore
            
            # Hash da senha
            password_hash = bcrypt.hashpw(data['senha'].encode('utf-8'), bcrypt.gensalt())
            
            cursor.execute("""
                INSERT INTO usuarios (
                    nome, email, password_hash, perfil, ativo
                ) VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, (
                data['nome'], data['email'], password_hash.decode('utf-8'),
                data['perfil'], bool(data.get('ativo', True))
            ))
            
            # Recuperar o id do usuário criado
            result = cursor.fetchone()
            usuario_id = result['id'] if result else None
            
            # Commit da transação
            conn.commit()  # type: ignore
            
            # Log da ação (fora da transação principal)
            try:
                from modules.auth import auth_manager
                auth_manager.log_action(  # type: ignore
                    1, f"Criou usuário: {data['nome']} (ID: {usuario_id})",  # type: ignore
                    "Usuários", None  # type: ignore
                )  # type: ignore
            except Exception as log_e:
                pass  # Log não crítico
            
            return usuario_id
        except Exception as e:
            # Fazer rollback explícito para limpar o estado da transação
            try:
                if hasattr(self.db.get_connection(), 'rollback'):
                    self.db.get_connection().rollback()  # type: ignore
            except:
                pass
            st.error(f"Erro ao criar usuário: {str(e)}")  # type: ignore
            return None
    
    def get_usuarios(self, filters: Dict[str, Any] = None) -> pd.DataFrame:  # type: ignore
        """Busca usuários com filtros"""
        try:
            cursor = self.db.get_connection().cursor()  # type: ignore
            
            query = """
                SELECT 
                    id, nome, email, perfil, ativo, 
                    data_criacao, ultimo_login,
                    CASE 
                        WHEN ativo = TRUE THEN 'Ativo' 
                        ELSE 'Inativo' 
                    END as status_texto
                FROM usuarios
                WHERE 1=1
            """
            
            params = []  # type: ignore
            
            if filters:
                if filters.get('nome'):  # type: ignore
                    query += " AND nome ILIKE %s"  # type: ignore
                    params.append(f"%{filters['nome']}%")  # type: ignore
                
                if filters.get('email'):  # type: ignore
                    query += " AND email ILIKE %s"  # type: ignore
                    params.append(f"%{filters['email']}%")  # type: ignore
                
                if filters.get('perfil') and filters['perfil'] != 'Todos':  # type: ignore
                    query += " AND perfil = %s"  # type: ignore
                    params.append(filters['perfil'])  # type: ignore
                
                if filters.get('status') and filters['status'] != 'Todos':  # type: ignore
                    ativo_value = True if filters['status'] == 'Ativo' else False  # type: ignore
                    query += " AND ativo = %s"  # type: ignore
                    params.append(ativo_value)  # type: ignore
            
            query += " ORDER BY nome"  # type: ignore
            
            cursor.execute(query, params)  # type: ignore
            rows = cursor.fetchall()
            
            if rows:
                columns = [desc[0] for desc in cursor.description]
                # Converter RealDictRow para dicts simples se necessário
                if hasattr(rows[0], '_asdict'):
                    # Se é namedtuple
                    data_list = [row._asdict() for row in rows]
                elif hasattr(rows[0], 'keys'):
                    # Se é RealDictRow
                    data_list = [dict(row) for row in rows]
                else:
                    # Se é tupla simples
                    data_list = [dict(zip(columns, row)) for row in rows]
                
                df = pd.DataFrame(data_list)  # type: ignore
                return df
            else:
                return pd.DataFrame()  # type: ignore
                
        except Exception as e:
            st.error(f"Erro ao buscar usuários: {str(e)}")
            return pd.DataFrame()
    
    def update_usuario(self, usuario_id: int, data: Dict[str, Any]) -> bool:
        """Atualiza dados do usuário"""
        try:
            cursor = self.db.get_connection().cursor()  # type: ignore
            
            # Converter usuario_id para int se necessário
            try:  # type: ignore
                usuario_id_int = int(usuario_id)  # type: ignore
            except (ValueError, TypeError) as e:  # type: ignore
                st.error(f"❌ ID de usuário inválido: {usuario_id}")  # type: ignore
                return False  # type: ignore
            
            # Primeiro, verificar se o usuário existe ANTES de qualquer operação
            cursor.execute("SELECT id, nome, email FROM usuarios WHERE id = %s", (usuario_id_int,))  # type: ignore
            user_before = cursor.fetchone()  # type: ignore
            
            if not user_before:  # type: ignore
                st.error(f"❌ Usuário com ID {usuario_id_int} não encontrado!")  # type: ignore
                return False  # type: ignore
            
            # Construir UPDATE simples e direto
            update_parts = []  # type: ignore
            params = []  # type: ignore
            
            # Campos básicos
            if 'nome' in data:  # type: ignore
                update_parts.append("nome = %s")  # type: ignore
                params.append(data['nome'])  # type: ignore
                
            if 'email' in data:  # type: ignore
                update_parts.append("email = %s")  # type: ignore
                params.append(data['email'])  # type: ignore
                
            if 'perfil' in data:  # type: ignore
                update_parts.append("perfil = %s")  # type: ignore
                params.append(data['perfil'])  # type: ignore
                
            if 'ativo' in data:  # type: ignore
                update_parts.append("ativo = %s")  # type: ignore
                params.append(bool(data['ativo']))  # type: ignore
            
            # Senha
            if data.get('nova_senha'):  # type: ignore
                password_hash = bcrypt.hashpw(data['nova_senha'].encode('utf-8'), bcrypt.gensalt())  # type: ignore
                update_parts.append("password_hash = %s")  # type: ignore
                params.append(password_hash.decode('utf-8'))  # type: ignore
            
            if not update_parts:  # type: ignore
                st.warning("⚠️ Nenhum campo para atualizar.")  # type: ignore
                return False  # type: ignore
            
            # Executar UPDATE
            params.append(usuario_id_int)  # Adicionar ID no final  # type: ignore
            query = f"UPDATE usuarios SET {', '.join(update_parts)} WHERE id = %s"  # type: ignore
            
            cursor.execute(query, params)  # type: ignore
            rows_affected = cursor.rowcount  # type: ignore
            
            # Verificar usuário APÓS o update mas ANTES do commit
            cursor.execute("SELECT id, nome, email FROM usuarios WHERE id = %s", (usuario_id_int,))  # type: ignore
            user_after = cursor.fetchone()  # type: ignore
            
            # Commit
            self.db.get_connection().commit()  # type: ignore
            
            # Verificar usuário APÓS commit
            cursor.execute("SELECT id, nome, email FROM usuarios WHERE id = %s", (usuario_id_int,))  # type: ignore
            user_final = cursor.fetchone()  # type: ignore
            
            if rows_affected > 0:  # type: ignore
                st.success("✅ Usuário atualizado com sucesso!")  # type: ignore
                return True
            else:
                st.error("❌ Falha na atualização - nenhuma linha foi modificada.")  # type: ignore
                return False
                
        except Exception as e:
            self.db.get_connection().rollback()  # type: ignore
            st.error(f"Erro ao atualizar usuário: {str(e)}")  # type: ignore
            import traceback  # type: ignore
            return False
    
    def delete_usuario(self, usuario_id: int, nome: str) -> bool:
        """Remove um usuário"""
        try:
            cursor = self.db.get_connection().cursor()  # type: ignore
            cursor.execute("UPDATE usuarios SET ativo = FALSE WHERE id = %s", (usuario_id,))  # type: ignore
            self.db.get_connection().commit()  # type: ignore
            
            # Log da ação
            from modules.auth import auth_manager
            auth_manager.log_action(  # type: ignore
                1, f"Desativou usuário: {nome} (ID: {usuario_id})",  # type: ignore
                "Usuários", None  # type: ignore
            )  # type: ignore
            
            return True
        except Exception as e:
            self.db.get_connection().rollback()  # type: ignore
            st.error(f"Erro ao desativar usuário: {str(e)}")  # type: ignore
            return False
    
    def get_perfis(self) -> List[str]:
        """Retorna lista de perfis disponíveis"""
        return ['admin', 'gestor', 'usuario']
    
    def get_status_options(self) -> List[str]:
        """Retorna opções de status"""
        return ['Ativo', 'Inativo']
    
    def verify_password_updated(self, usuario_id: int) -> str:  # type: ignore
        """Verifica se a senha foi atualizada (para debug)"""
        try:
            cursor = self.db.get_connection().cursor()  # type: ignore
            cursor.execute("SELECT password_hash FROM usuarios WHERE id = %s", (usuario_id,))  # type: ignore
            result = cursor.fetchone()  # type: ignore
            if result:  # type: ignore
                return result[0][:20] + "..."  # Primeiros 20 caracteres do hash  # type: ignore
            return "Usuário não encontrado"  # type: ignore
        except Exception as e:  # type: ignore
            return f"Erro: {str(e)}"  # type: ignore
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Estatísticas para dashboard"""
        try:
            cursor = self.db.get_connection().cursor()  # type: ignore
            
            # Total de usuários
            cursor.execute("SELECT COUNT(*) as count FROM usuarios WHERE ativo = TRUE")
            result = cursor.fetchone()
            total = result[0] if result else 0
            
            # Usuários por perfil
            cursor.execute("""
                SELECT perfil, COUNT(*) as count
                FROM usuarios 
                WHERE ativo = TRUE 
                GROUP BY perfil
            """)
            results = cursor.fetchall()
            perfis = {row[0]: row[1] for row in results}
            
            # Logins recentes (último mês)
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM usuarios 
                WHERE ultimo_login >= NOW() - INTERVAL '30 days'
                AND ativo = TRUE
            """)
            result = cursor.fetchone()
            logins_mes = result[0] if result else 0
            
            return {
                'total': total,
                'admins': perfis.get('admin', 0),
                'gestores': perfis.get('gestor', 0),
                'usuarios': perfis.get('usuario', 0),
                'logins_mes': logins_mes
            }
        except Exception as e:
            st.error(f"Erro ao obter estatísticas: {str(e)}")
            return {
                'total': 0,
                'admins': 0,
                'gestores': 0,
                'usuarios': 0,
                'logins_mes': 0
            }

def show_usuarios_page():
    """Interface principal de usuários"""
    
    st.title("👥 Gestão de Usuários")
    
    # Importar auth_manager localmente para evitar erros de escopo
    from modules.auth import auth_manager
    
    user_data = st.session_state.user_data
    if not auth_manager.check_permission(user_data['perfil'], "read"):
        st.error("❌ Você não tem permissão para acessar esta página.")
        return
    
    manager = UsuariosManager()
    
    # Abas principais
    tab1, tab2, tab3 = st.tabs(["📋 Lista", "➕ Adicionar", "📊 Estatísticas"])
    
    with tab1:
        st.subheader("Lista de Usuários")
        
        # Filtros
        with st.expander("🔍 Filtros", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                filtro_nome = st.text_input("Nome")
                filtro_email = st.text_input("E-mail")
            with col2:
                filtro_perfil = st.selectbox("Perfil", ["Todos"] + manager.get_perfis())
                filtro_status = st.selectbox("Status", ["Todos"] + manager.get_status_options())
        
        # Aplicar filtros
        filters = {}
        if filtro_nome:
            filters['nome'] = filtro_nome
        if filtro_email:
            filters['email'] = filtro_email
        if filtro_perfil != "Todos":
            filters['perfil'] = filtro_perfil
        if filtro_status != "Todos":
            filters['status'] = filtro_status
        
        # Buscar usuários
        df = manager.get_usuarios(filters)  # type: ignore
        
        if not df.empty:
            # Tabela customizada com botões de edição
            st.write("### Lista de Usuários")
            
            # Cabeçalho da tabela
            cols = st.columns([3, 3, 1.5, 1.5, 2, 2, 1.5])
            cols[0].write("**Nome**")
            cols[1].write("**E-mail**")
            cols[2].write("**Perfil**")
            cols[3].write("**Status**")
            cols[4].write("**Data Criação**")
            cols[5].write("**Último Login**")
            cols[6].write("**Ações**")
            
            # Linhas da tabela
            for idx, row in df.iterrows():  # type: ignore # noqa: F841
                cols = st.columns([3, 3, 1.5, 1.5, 2, 2, 1.5])  # type: ignore
                cols[0].write(row['nome'])  # type: ignore
                cols[1].write(row['email'])  # type: ignore
                cols[2].write(row['perfil'])  # type: ignore
                
                # Status com cor
                if row['status_texto'] == 'Ativo':
                    cols[3].success(row['status_texto'])
                else:
                    cols[3].error(row['status_texto'])
                
                cols[4].write(str(row['data_criacao'])[:10] if row['data_criacao'] else '-')
                cols[5].write(str(row['ultimo_login'])[:10] if row['ultimo_login'] else 'Nunca')
                
                # Botões de ação
                from modules.auth import auth_manager
                if auth_manager.check_permission(user_data['perfil'], "update"):
                    if cols[6].button("✏️", key=f"edit_user_{row['id']}_{idx}", help="Editar usuário"):
                        st.session_state.editing_user = row['id']
                        st.rerun()
            
            # Formulário de edição inline
            if st.session_state.get('editing_user'):  # type: ignore
                user_to_edit = df[df['id'] == st.session_state.editing_user].iloc[0]  # type: ignore
                
                st.markdown("---")
                st.write(f"### ✏️ Editando: {user_to_edit['nome']}")
                
                with st.form(f"edit_user_{user_to_edit['id']}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        new_nome = st.text_input("Nome", value=user_to_edit['nome'])  # type: ignore
                        new_email = st.text_input("E-mail", value=user_to_edit['email'])  # type: ignore
                    
                    with col2:
                        new_perfil = st.selectbox("Perfil",  # type: ignore
                                                manager.get_perfis(),  # type: ignore
                                                index=manager.get_perfis().index(user_to_edit['perfil']))  # type: ignore
                        new_ativo = st.checkbox("Ativo", value=bool(user_to_edit['ativo']))  # type: ignore
                    
                    with col3:
                        new_senha = st.text_input("Nova Senha (opcional)", type="password")
                        confirm_senha = st.text_input("Confirmar Nova Senha", type="password")
                    
                    # Seção de permissões de módulos
                    st.subheader("🔒 Permissões de Acesso aos Módulos")
                    
                    # Obter permissões atuais do usuário
                    from modules.auth import auth_manager
                    current_permissions = auth_manager.get_user_module_permissions(user_to_edit['id'])
                    
                    # Debug: mostrar permissões atuais
                    st.info(f"**Permissões atuais:** {len(current_permissions)} módulos carregados")
                    with st.expander("🔍 Debug - Permissões Atuais"):
                        for mod, perm in current_permissions.items():
                            st.write(f"- {mod}: {'✅' if perm else '❌'}")
                    
                    # Lista de módulos disponíveis
                    modules_list = [
                        ("dashboard", "Dashboard"),
                        ("insumos", "Insumos"),
                        ("equipamentos_eletricos", "Equipamentos Elétricos"),
                        ("equipamentos_manuais", "Equipamentos Manuais"), 
                        ("movimentacao", "Movimentação"),
                        ("obras", "Obras/Departamentos"),
                        ("responsaveis", "Responsáveis"),
                        ("relatorios", "Relatórios"),
                        ("logs", "Logs de Auditoria"),
                        ("usuarios", "Usuários"),
                        ("configuracoes", "Configurações"),
                        ("qr_codes", "QR/Códigos de Barras"),
                        ("reservas", "Reservas"),
                        ("manutencao", "Manutenção Preventiva"),
                        ("dashboard_exec", "Dashboard Executivo"),
                        ("localizacao", "Localização"),
                        ("financeiro", "Gestão Financeira"),
                        ("analise", "Análise Preditiva"),
                        ("subcontratados", "Gestão de Subcontratados"),
                        ("relatorios_custom", "Relatórios Customizáveis"),
                        ("metricas", "Métricas Performance"),
                        ("backup_automatico", "Backup Automático"),
                        ("auditoria_avancada", "Auditoria Completa"),
                        ("lgpd", "LGPD/Compliance"),
                        ("orcamentos", "Orçamentos e Cotações"),
                        ("faturamento", "Sistema de Faturamento"),
                        ("integracao", "Integração ERP/SAP")
                    ]
                    
                    st.write("Selecione os módulos que o usuário poderá acessar:")
                    edit_permissions = {}
                    
                    # Criar checkboxes em colunas
                    col_perm1, col_perm2, col_perm3, col_perm4 = st.columns(4)
                    
                    for idx, (module_key, module_name) in enumerate(modules_list):
                        # Distribuir entre as colunas
                        col = [col_perm1, col_perm2, col_perm3, col_perm4][idx % 4]
                        with col:
                            # Verificar se o usuário tem acesso atualmente a este módulo
                            has_access = current_permissions.get(module_key, False)
                            edit_permissions[module_key] = st.checkbox(
                                module_name, 
                                value=has_access,
                                key=f"edit_perm_{user_to_edit['id']}_{module_key}"
                            )
                    
                    col_save, col_cancel = st.columns(2)
                    
                    with col_save:
                        if st.form_submit_button("💾 Salvar", type="primary"):
                            # Validações
                            errors = []  # type: ignore
                            
                            if not new_nome or not new_nome.strip():  # type: ignore
                                errors.append("Nome é obrigatório")  # type: ignore
                                
                            if not new_email or not new_email.strip():  # type: ignore
                                errors.append("E-mail é obrigatório")  # type: ignore
                            
                            # Validação de senha
                            if new_senha:  # type: ignore
                                if len(new_senha) < 6:  # type: ignore
                                    errors.append("A nova senha deve ter pelo menos 6 caracteres")  # type: ignore
                                elif new_senha != confirm_senha:  # type: ignore
                                    errors.append("As senhas não coincidem")  # type: ignore
                            
                            if errors:  # type: ignore
                                for error in errors:  # type: ignore
                                    st.error(f"❌ {error}")  # type: ignore
                            else:
                                # Preparar dados para atualização
                                update_data = {  # type: ignore
                                    'nome': new_nome.strip(),  # type: ignore
                                    'email': new_email.strip(),  # type: ignore
                                    'perfil': new_perfil,  # type: ignore
                                    'ativo': new_ativo  # type: ignore
                                }  # type: ignore
                                
                                # Adicionar senha apenas se foi informada
                                if new_senha and new_senha.strip():  # type: ignore
                                    update_data['nova_senha'] = new_senha.strip()  # type: ignore
                                    st.info("🔐 Nova senha será aplicada...")  # type: ignore
                                
                                # Executar atualização
                                if manager.update_usuario(user_to_edit['id'], update_data):  # type: ignore
                                    # Atualizar permissões de módulos
                                    from modules.auth import auth_manager
                                    
                                    # Debug: mostrar permissões que serão salvas
                                    st.write(f"**Debug - Permissões a salvar:** {len(edit_permissions)} módulos")
                                    for mod, perm in edit_permissions.items():
                                        if perm:  # Mostrar apenas as marcadas
                                            st.write(f"- {mod}: {'✅' if perm else '❌'}")
                                    
                                    perm_result = auth_manager.update_user_module_permissions(user_to_edit['id'], edit_permissions)
                                    
                                    if perm_result:
                                        st.success("✅ Usuário e permissões atualizados com sucesso!")
                                        st.session_state.editing_user = None  # type: ignore
                                        st.rerun()  # type: ignore
                                    else:
                                        st.warning("⚠️ Usuário atualizado, mas houve erro nas permissões")
                                else:  # type: ignore
                                    st.error("❌ Falha ao atualizar o usuário. Verifique os logs.")  # type: ignore
                    
                    with col_cancel:
                        if st.form_submit_button("❌ Cancelar"):
                            st.session_state.editing_user = None
                            st.rerun()
                
                # Debug: mostrar hash atual (apenas para admin) - fora do formulário
                if user_data['perfil'] == 'admin':  # type: ignore
                    if st.button("🔍 Ver Hash Atual", key=f"debug_hash_{user_to_edit['id']}"):  # type: ignore
                        current_hash = manager.verify_password_updated(user_to_edit['id'])  # type: ignore
                        st.code(f"Hash atual: {current_hash}")  # type: ignore
            
            # Ações em lote (apenas para admin)
            from modules.auth import auth_manager
            if auth_manager.check_permission(user_data['perfil'], "delete"):
                st.subheader("Ações")
                
                selected_ids = st.multiselect(  # type: ignore
                    "Selecionar usuários para ação:",  # type: ignore
                    options=df['id'].tolist(),  # type: ignore
                    format_func=lambda x: df[df['id'] == x]['nome'].iloc[0]  # type: ignore
                )  # type: ignore
                
                if selected_ids:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Ativar Selecionados"):
                            for user_id in selected_ids:
                                manager.update_usuario(user_id, {'ativo': True})
                            st.success("Usuários ativados!")
                            st.rerun()
                    
                    with col2:
                        if st.button("❌ Desativar Selecionados", type="secondary"):  # type: ignore
                            for user_id in selected_ids:  # type: ignore
                                nome = df[df['id'] == user_id]['nome'].iloc[0]  # type: ignore
                                manager.delete_usuario(user_id, nome)  # type: ignore
                            st.success("Usuários desativados!")
                            st.rerun()
        else:
            st.info("📭 Nenhum usuário encontrado com os filtros aplicados.")
    
    with tab2:
        from modules.auth import auth_manager
        if not auth_manager.check_permission(user_data['perfil'], "create"):
            st.error("❌ Você não tem permissão para adicionar usuários.")
            return
        
        st.subheader("Adicionar Novo Usuário")
        
        with st.form("form_usuario", clear_on_submit=True):
            # Informações básicas
            st.markdown("### Informações Básicas")
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome Completo *", placeholder="Ex: João Silva", key="form_usuario_nome")
                email = st.text_input("E-mail *", placeholder="joao@empresa.com", key="form_usuario_email")
            
            with col2:
                perfil = st.selectbox("Perfil *", manager.get_perfis(), key="form_usuario_perfil")
                ativo = st.checkbox("Usuário Ativo", value=True, key="form_usuario_ativo")
            
            # Senha
            st.markdown("### Credenciais de Acesso")
            col1, col2 = st.columns(2)
            
            with col1:
                senha = st.text_input("Senha *", type="password", placeholder="Mínimo 6 caracteres", key="form_usuario_senha")
            
            with col2:
                confirma_senha = st.text_input("Confirmar Senha *", type="password", key="form_usuario_confirma_senha")
            
            # Permissões por módulo
            st.markdown("### 🔐 Permissões por Módulo")
            st.info("Selecione quais módulos este usuário poderá acessar:")
            
            # Lista de módulos disponíveis
            modulos_disponiveis = [
                ("dashboard", "📊 Dashboard", True),  # Dashboard sempre habilitado
                ("insumos", "📦 Insumos", False),
                ("equipamentos_eletricos", "⚡ Equipamentos Elétricos", False),
                ("equipamentos_manuais", "🔧 Equipamentos Manuais", False),
                ("movimentacao", "🔄 Movimentações", False),
                ("obras", "🏗️ Obras/Departamentos", False),
                ("responsaveis", "👥 Responsáveis", False),
                ("relatorios", "📊 Relatórios", False),
                ("logs", "📋 Logs de Auditoria", False),
                ("usuarios", "👤 Usuários", False),
                ("configuracoes", "⚙️ Configurações", False),
                ("qr_codes", "📱 QR/Códigos de Barras", False),
                ("reservas", "📅 Reservas", False),
                ("manutencao", "🔧 Manutenção Preventiva", False),
                ("dashboard_exec", "📈 Dashboard Executivo", False),
                ("localizacao", "📍 Localização", False),
                ("financeiro", "💰 Gestão Financeira", False),
                ("analise", "🔮 Análise Preditiva", False),
                ("subcontratados", "🏢 Gestão de Subcontratados", False),
                ("relatorios_custom", "📋 Relatórios Customizáveis", False),
                ("metricas", "⚡ Métricas Performance", False),
                ("backup_automatico", "💾 Backup Automático", False),
                ("auditoria_avancada", "🔍 Auditoria Completa", False),
                ("lgpd", "🛡️ LGPD/Compliance", False),
                ("orcamentos", "🧮 Orçamentos e Cotações", False),
                ("faturamento", "🧾 Sistema de Faturamento", False),
                ("integracao", "🔗 Integração ERP/SAP", False)
            ]
            
            col_perm1, col_perm2, col_perm3 = st.columns(3)
            permissions = {}
            
            for i, (modulo_id, modulo_nome, default_value) in enumerate(modulos_disponiveis):
                col = [col_perm1, col_perm2, col_perm3][i % 3]
                
                with col:
                    if modulo_id == "dashboard":
                        st.checkbox(modulo_nome, value=True, disabled=True, key=f"perm_{modulo_id}")
                        permissions[modulo_id] = True
                    elif modulo_id in ["usuarios", "configuracoes", "backup_automatico", "lgpd", "integracao"] and perfil != "admin":
                        st.checkbox(modulo_nome, value=False, disabled=True, key=f"perm_{modulo_id}")
                        permissions[modulo_id] = False
                    elif modulo_id == "auditoria_avancada" and perfil == "usuario":
                        st.checkbox(modulo_nome, value=False, disabled=True, key=f"perm_{modulo_id}")
                        permissions[modulo_id] = False
                    else:
                        # Definir valores padrão baseados no perfil selecionado
                        if perfil == "admin":
                            default_perm = True
                        elif perfil == "gestor" and modulo_id in ["insumos", "equipamentos_eletricos", "equipamentos_manuais", "movimentacao", "obras", "responsaveis", "relatorios", "qr_codes", "reservas", "manutencao", "localizacao", "financeiro", "relatorios_custom", "metricas"]:
                            default_perm = True
                        elif perfil == "usuario" and modulo_id in ["insumos", "equipamentos_eletricos", "equipamentos_manuais", "relatorios"]:
                            default_perm = True
                        else:
                            default_perm = False
                            
                        permissions[modulo_id] = st.checkbox(modulo_nome, value=default_perm, key=f"perm_{modulo_id}")
            
            submitted = st.form_submit_button("💾 Cadastrar Usuário", type="primary")
            
            if submitted:
                if nome and email and senha and perfil:
                    if len(senha) < 6:
                        st.error("❌ A senha deve ter pelo menos 6 caracteres!")
                    elif senha != confirma_senha:
                        st.error("❌ As senhas não coincidem!")
                    else:
                        data = {  # type: ignore
                            'nome': nome,  # type: ignore
                            'email': email,  # type: ignore
                            'perfil': perfil,  # type: ignore
                            'senha': senha,  # type: ignore
                            'ativo': ativo  # type: ignore
                        }  # type: ignore
                        
                        usuario_id = manager.create_usuario(data)  # type: ignore
                        if usuario_id:
                            # Salvar permissões de módulos após o usuário ser criado
                            try:
                                import time
                                time.sleep(0.1)  # Pequeno delay para garantir que o commit foi processado
                                
                                from modules.auth import auth_manager
                                perm_success = auth_manager.update_user_module_permissions(usuario_id, permissions)
                                
                                if perm_success:
                                    st.success(f"✅ Usuário '{nome}' cadastrado com sucesso! (ID: {usuario_id})")
                                else:
                                    st.warning(f"⚠️ Usuário '{nome}' criado (ID: {usuario_id}), mas houve problema ao salvar permissões. Verifique as permissões manualmente.")
                            except Exception as perm_error:
                                st.warning(f"⚠️ Usuário '{nome}' criado (ID: {usuario_id}), mas erro nas permissões: {perm_error}")
                            
                            # Limpar formulário após sucesso
                            for key in list(st.session_state.keys()):
                                if key.startswith('form_usuario_') or key.startswith('perm_'):
                                    del st.session_state[key]
                            st.rerun()
                        else:
                            st.error("❌ Erro ao cadastrar usuário. Verifique os dados e tente novamente.")
                else:
                    st.error("❌ Preencha todos os campos obrigatórios marcados com *")
    
    with tab3:
        st.subheader("Estatísticas dos Usuários")
        
        stats = manager.get_dashboard_stats()
        
        # Cards de estatísticas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total", stats['total'])
        
        with col2:
            st.metric("Administradores", stats['admins'])
        
        with col3:
            st.metric("Gestores", stats['gestores'])
        
        with col4:
            st.metric("Usuários", stats['usuarios'])
        
        # Gráficos
        if stats['total'] > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico por perfil
                perfis_data = {
                    'admin': stats['admins'],
                    'gestor': stats['gestores'],
                    'usuario': stats['usuarios']
                }
                
                st.plotly_chart(  # type: ignore
                    {  # type: ignore
                        'data': [{  # type: ignore
                            'type': 'pie',  # type: ignore
                            'labels': list(perfis_data.keys()),  # type: ignore
                            'values': list(perfis_data.values()),  # type: ignore
                            'title': 'Usuários por Perfil'  # type: ignore
                        }],  # type: ignore
                        'layout': {'title': 'Distribuição por Perfil'}  # type: ignore
                    },  # type: ignore
                    width='stretch'  # type: ignore
                )  # type: ignore
            
            with col2:
                # Métrica de logins
                st.metric("Logins (Último Mês)", stats['logins_mes'])
                
                if stats['total'] > 0:
                    engajamento = (stats['logins_mes'] / stats['total']) * 100
                    st.metric("Taxa de Engajamento", f"{engajamento:.1f}%")
        else:
            st.info("📊 Nenhum dado disponível para gerar gráficos.")

# Manager global
usuarios_manager = UsuariosManager()