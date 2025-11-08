import streamlit as st
import pandas as pd
from datetime import datetime, date  # type: ignore
from typing import Any
from database.connection import db
from modules.auth import auth_manager

class ResponsaveisManager:
    def __init__(self):
        self.db: Any = db
    
    def create_responsavel(self, data: dict[str, Any]) -> int | None:
        """Cria um novo responsável"""
        try:
            cursor = self.db.conn.cursor()  # type: ignore
            
            cursor.execute("""
                INSERT INTO responsaveis (
                    codigo, nome, cargo, email, telefone, cpf,
                    departamento, data_admissao, ativo, observacoes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data.get('codigo'), data['nome'], data['cargo'], data['email'], 
                data['telefone'], data.get('cpf'), data.get('departamento'),
                data.get('data_admissao'), 1 if data.get('ativo', True) else 0,
                data.get('observacoes')
            ))
            
            # Recuperar o id do responsável criado
            cursor.execute("SELECT currval(pg_get_serial_sequence('responsaveis','id'))")
            result = cursor.fetchone()
            responsavel_id = result['id'] if result else None
            self.db.conn.commit()  # type: ignore
            
            # Log da ação
            auth_manager.log_action(
                1,  # id do usuário
                f"Criou responsável: {data['nome']} (ID: {responsavel_id})",
                "Responsáveis",
                responsavel_id
            )
            
            return responsavel_id
        except Exception as e:
            self.db.conn.rollback()  # type: ignore
            st.error(f"Erro ao criar responsável: {e}")
            return None
    
    def get_responsaveis(self, filters: dict[str, Any] | None = None) -> pd.DataFrame:
        """Busca responsáveis com filtros"""
        try:
            cursor = self.db.conn.cursor()
            
            query = """
                SELECT 
                    id, codigo, nome, cargo, email, telefone, cpf,
                    departamento, data_admissao, ativo, observacoes, data_criacao
                FROM responsaveis
                WHERE 1=1
            """
            params: list[Any] = []
            
            if filters:
                if filters.get('nome'):
                    query += " AND nome LIKE %s"
                    params.append(f"%{filters['nome']}%")
                if filters.get('cargo'):
                    query += " AND cargo LIKE %s"
                    params.append(f"%{filters['cargo']}%")
                if filters.get('departamento'):
                    query += " AND departamento LIKE %s"
                    params.append(f"%{filters['departamento']}%")
                if filters.get('ativo') is not None:
                    query += " AND ativo = %s"
                    params.append(filters['ativo'])
            
            query += " ORDER BY nome"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            columns = [
                'id', 'codigo', 'nome', 'cargo', 'email', 'telefone', 'cpf',
                'departamento', 'data_admissao', 'ativo', 'observacoes', 'data_criacao'
            ]
            
            return pd.DataFrame(results, columns=columns) if results else pd.DataFrame()
            
        except Exception as e:
            st.error(f"Erro ao buscar responsáveis: {e}")
            return pd.DataFrame()
    
    def update_responsavel(self, responsavel_id: int, data: dict[str, Any]) -> bool:
        """Atualiza um responsável"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("""
                UPDATE responsaveis SET
                    codigo = %s, nome = %s, cargo = %s, email = %s, telefone = %s, cpf = %s,
                    departamento = %s, data_admissao = %s, ativo = %s, observacoes = %s
                WHERE id = %s
            """, (
                data.get('codigo'), data['nome'], data['cargo'], data['email'], 
                data['telefone'], data.get('cpf'), data.get('departamento'),
                data.get('data_admissao'), 1 if data.get('ativo', True) else 0,
                data.get('observacoes'), responsavel_id
            ))
            
            self.db.conn.commit()
            
            # Log da ação
            auth_manager.log_action(
                1,  # id do usuário, ajuste conforme necessário
                f"Atualizou responsável: {data['nome']} (ID: {responsavel_id})",
                "Responsáveis",
                responsavel_id
            )
            
            return True
        except Exception as e:
            self.db.conn.rollback()
            st.error(f"Erro ao atualizar responsável: {e}")
            return False
    
    def delete_responsavel(self, responsavel_id: int, nome: str) -> bool:
        """Remove um responsável"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("DELETE FROM responsaveis WHERE id = %s", (responsavel_id,))
            self.db.conn.commit()
            
            # Log da ação
            auth_manager.log_action(
                1,  # id do usuário, ajuste conforme necessário
                f"Removeu responsável: {nome} (ID: {responsavel_id})",
                "Responsáveis",
                responsavel_id
            )
            
            return True
        except Exception as e:
            self.db.conn.rollback()
            st.error(f"Erro ao remover responsável: {e}")
            return False
    
    def get_status_options(self) -> list[str]:
        """Retorna opções de status"""
        return ['Ativo', 'Inativo']
    
    def get_dashboard_stats(self) -> dict[str, int]:
        """Estatísticas para o dashboard"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN ativo = TRUE THEN 1 ELSE 0 END) as ativos,
                    SUM(CASE WHEN ativo = FALSE THEN 1 ELSE 0 END) as inativos
                FROM responsaveis
            """)
            
            result = cursor.fetchone()
            return {
                'total': result['count'] if result else 0,
                'ativos': result['ativos'] if result else 0,
                'inativos': result['inativos'] if result else 0
            }
        except:
            return {'total': 0, 'ativos': 0, 'inativos': 0}

def show_responsaveis_page():
    """Interface principal dos responsáveis"""
    
    st.title("👥 Gestão de Responsáveis")
    user_data = st.session_state.user_data
    if not auth_manager.check_permission(user_data['perfil'], "read"):
        st.error("❌ Você não tem permissão para acessar esta página.")
        return
    manager = ResponsaveisManager()
    
    # Abas principais
    tab1, tab2, tab3 = st.tabs(["📋 Lista", "➕ Adicionar", "📊 Estatísticas"])
    
    with tab1:
        st.subheader("Lista de Responsáveis")
        
        # Filtros
        with st.expander("🔍 Filtros", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                filtro_nome = st.text_input("Nome")
                filtro_cargo = st.text_input("Cargo")
            with col2:
                filtro_departamento = st.text_input("Departamento")
                filtro_ativo = st.selectbox("Status", ["Todos", "Ativo", "Inativo"])
        
        # Aplicar filtros
        filters = {}
        if filtro_nome:
            filters['nome'] = filtro_nome
        if filtro_cargo:
            filters['cargo'] = filtro_cargo
        if filtro_departamento:
            filters['departamento'] = filtro_departamento
        if filtro_ativo != "Todos":
            filters['ativo'] = 1 if filtro_ativo == "Ativo" else 0
        
        # Buscar responsáveis
        df = manager.get_responsaveis(filters)  # type: ignore
        if not df.empty:
            # Cabeçalho da tabela com ações
            col_header = st.columns([0.8, 2, 1.5, 1.5, 1.2, 1.5, 1, 0.8, 0.8])
            headers = ["Código", "Nome", "Cargo", "Email", "Telefone", "Departamento", "Status", "Editar", "Excluir"]
            for i, h in enumerate(headers):
                with col_header[i]:
                    st.write(f"**{h}**")
            st.write("---")
            
            # Listagem com botões de ação
            for _, row in df.iterrows():
                cols = st.columns([0.8, 2, 1.5, 1.5, 1.2, 1.5, 1, 0.8, 0.8])
                with cols[0]:
                    st.write(row['codigo'] if row['codigo'] else "N/A")
                with cols[1]:
                    st.write(row['nome'])
                with cols[2]:
                    st.write(row['cargo'] if row['cargo'] else "N/A")
                with cols[3]:
                    st.write(row['email'] if row['email'] else "N/A")
                with cols[4]:
                    st.write(row['telefone'] if row['telefone'] else "N/A")
                with cols[5]:
                    st.write(row['departamento'] if row['departamento'] else "N/A")
                with cols[6]:
                    st.write("Ativo" if row['ativo'] else "Inativo")
                with cols[7]:
                    if st.button("✏️", key=f"edit_resp_{row['id']}", help="Editar responsável"):
                        st.session_state[f'edit_mode_resp_{row["id"]}'] = True
                        st.rerun()
                with cols[8]:
                    if st.button("❌", key=f"del_resp_{row['id']}", help="Excluir responsável"):
                        st.session_state[f'confirm_delete_resp_{row["id"]}'] = True
                        st.rerun()
                
                # Modal de confirmação de exclusão
                if st.session_state.get(f'confirm_delete_resp_{row["id"]}', False):
                    st.markdown("---")
                    st.error(f"⚠️ **CONFIRMAÇÃO DE EXCLUSÃO**")
                    st.warning(f"Tem certeza que deseja excluir o responsável **{row['nome']}**?\n\nEsta ação não pode ser desfeita!")
                    
                    col_cancel, col_confirm = st.columns(2)
                    with col_cancel:
                        if st.button("❌ Cancelar", key=f"cancel_del_resp_{row['id']}"):
                            del st.session_state[f'confirm_delete_resp_{row["id"]}']
                            st.rerun()
                    
                    with col_confirm:
                        if st.button("🗑️ Confirmar Exclusão", key=f"confirm_del_resp_{row['id']}", type="primary"):
                            if manager.delete_responsavel(int(row['id']), row['nome']):
                                st.success(f"Responsável {row['nome']} excluído com sucesso!")
                                del st.session_state[f'confirm_delete_resp_{row["id"]}']
                                st.rerun()
                            else:
                                st.error("Erro ao excluir responsável.")
                    st.markdown("---")
                
                # Modal de edição
                if st.session_state.get(f'edit_mode_resp_{row["id"]}', False):
                    with st.expander(f"🔧 Editando: {row['nome']}", expanded=True):
                        with st.form(f"edit_form_resp_{row['id']}"):
                            st.markdown("### Informações do Responsável")
                            col_ed1, col_ed2 = st.columns(2)
                            with col_ed1:
                                novo_codigo = st.text_input("Código", value=row['codigo'] or "", key=f"codigo_edit_resp_{row['id']}")
                                novo_nome = st.text_input("Nome *", value=row['nome'], key=f"nome_edit_resp_{row['id']}")
                                novo_cargo = st.text_input("Cargo", value=row['cargo'] or "", key=f"cargo_edit_resp_{row['id']}")
                                novo_email = st.text_input("Email", value=row['email'] or "", key=f"email_edit_resp_{row['id']}")
                            with col_ed2:
                                novo_telefone = st.text_input("Telefone", value=row['telefone'] or "", key=f"tel_edit_resp_{row['id']}")
                                novo_cpf = st.text_input("CPF", value=row['cpf'] or "", key=f"cpf_edit_resp_{row['id']}")
                                novo_departamento = st.text_input("Departamento", value=row['departamento'] or "", key=f"dep_edit_resp_{row['id']}")
                                novo_ativo = st.selectbox("Status *", ["Ativo", "Inativo"],
                                                         index=0 if row['ativo'] else 1,
                                                         key=f"ativo_edit_resp_{row['id']}")
                            
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.form_submit_button("💾 Salvar", type="primary"):
                                    dados_update: dict[str, Any] = {
                                        'codigo': novo_codigo,
                                        'nome': novo_nome,
                                        'cargo': novo_cargo,
                                        'email': novo_email,
                                        'telefone': novo_telefone,
                                        'cpf': novo_cpf,
                                        'departamento': novo_departamento,
                                        'ativo': novo_ativo == "Ativo"
                                    }
                                    if manager.update_responsavel(int(row['id']), dados_update):
                                        st.success(f"Responsável {novo_nome} atualizado com sucesso!")
                                        del st.session_state[f'edit_mode_resp_{row["id"]}']
                                        st.rerun()
                                    else:
                                        st.error("Erro ao atualizar responsável.")
                            with col_btn2:
                                if st.form_submit_button("❌ Cancelar"):
                                    del st.session_state[f'edit_mode_resp_{row["id"]}']
                                    st.rerun()
                        st.divider()
        else:
            st.info("📭 Nenhum responsável encontrado com os filtros aplicados.")
    
    with tab2:
        if not auth_manager.check_permission(user_data['perfil'], "create"):
            st.error("❌ Você não tem permissão para adicionar responsáveis.")
            return
        st.subheader("Adicionar Novo Responsável")
        
        with st.form("form_responsavel"):
            # Informações básicas
            st.markdown("### Informações Básicas")
            col1, col2 = st.columns(2)
            
            with col1:
                codigo = st.text_input("Código", placeholder="Ex: RESP001")
                nome = st.text_input("Nome Completo *", placeholder="Ex: João da Silva")
                cargo = st.text_input("Cargo *", placeholder="Ex: Engenheiro Civil")
                email = st.text_input("E-mail *", placeholder="joao@empresa.com")
            
            with col2:
                telefone = st.text_input("Telefone *", placeholder="(11) 99999-9999")
                cpf = st.text_input("CPF", placeholder="000.000.000-00")
                departamento = st.text_input("Departamento", placeholder="Ex: Engenharia")
                data_admissao = st.date_input("Data de Admissão", value=None)
            
            # Observações
            observacoes = st.text_area("Observações", placeholder="Informações adicionais")
            
            submitted = st.form_submit_button("💾 Cadastrar Responsável", type="primary")
            
            if submitted:
                # Importar validador
                from modules.validators import DataValidator, VALIDATION_RULES
                
                # Preparar dados para validação
                form_data = {
                    'nome': nome,
                    'cargo': cargo,
                    'email': email,
                    'telefone': telefone,
                    'cpf': cpf
                }
                
                # Validar dados
                is_valid, errors = DataValidator.validate_form_data(form_data, VALIDATION_RULES['responsavel'])
                
                if is_valid:
                    data: dict[str, Any] = {
                        'codigo': codigo,
                        'nome': nome,
                        'cargo': cargo,
                        'email': email,
                        'telefone': telefone,
                        'cpf': cpf,
                        'departamento': departamento,
                        'data_admissao': data_admissao.strftime('%Y-%m-%d') if data_admissao else None,
                        'ativo': True,
                        'observacoes': observacoes
                    }

                    with st.spinner("Cadastrando responsável..."):
                        responsavel_id = manager.create_responsavel(data)
                        if responsavel_id:
                            st.success(f"✅ Responsável '{nome}' cadastrado com sucesso! (ID: {responsavel_id})")
                            st.balloons()  # Efeito visual de sucesso
                            st.rerun()
                        else:
                            st.error("❌ Erro interno ao cadastrar responsável. Tente novamente.")
                else:
                    for error in errors:
                        st.error(f"❌ {error}")
    
    with tab3:
        st.subheader("Estatísticas dos Responsáveis")
        
        stats = manager.get_dashboard_stats()
        
        # Cards de estatísticas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total", stats['total'])
        
        with col2:
            st.metric("Ativos", stats['ativos'])
        
        with col3:
            st.metric("Inativos", stats['inativos'])
        
        # Gráficos
        if stats['total'] > 0:
            df_stats = manager.get_responsaveis()
            
            if not df_stats.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico por status
                    status_data = ['Ativo' if x else 'Inativo' for x in df_stats['ativo']]
                    status_counts = pd.Series(status_data).value_counts()
                    st.plotly_chart(  # type: ignore
                        {
                            'data': [{
                                'type': 'pie',
                                'labels': status_counts.index.tolist(),  # type: ignore
                                'values': status_counts.values.tolist(),  # type: ignore
                                'title': 'Distribuição por Status'  # type: ignore
                            }],
                            'layout': {'title': 'Responsáveis por Status'}  # type: ignore
                        },
                        use_container_width=True  # type: ignore
                    )  # type: ignore
                
                with col2:
                    # Gráfico por departamento
                    dept_counts = df_stats['departamento'].value_counts().head(10)
                    if not dept_counts.empty:
                        st.plotly_chart(  # type: ignore
                            {
                                'data': [{
                                    'type': 'bar',
                                    'x': dept_counts.index.tolist(),  # type: ignore
                                    'y': dept_counts.values.tolist()  # type: ignore
                                }],
                                'layout': {'title': 'Top 10 Departamentos'}  # type: ignore
                            },
                            use_container_width=True  # type: ignore
                        )  # type: ignore

# Instância global
responsaveis_manager = ResponsaveisManager()