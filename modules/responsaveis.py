import streamlit as st
import pandas as pd
from datetime import datetime, date
from database.connection import db
from modules.auth import auth_manager

class ResponsaveisManager:
    def __init__(self):
        self.db = db
    
    def create_responsavel(self, data):
        """Cria um novo responsável"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("""
                INSERT INTO responsaveis (
                    nome, cargo, email, telefone, cpf, endereco,
                    departamento, setor, data_admissao, status, observacoes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['nome'], data['cargo'], data['email'], data['telefone'],
                data.get('cpf'), data.get('endereco'), data.get('departamento'),
                data.get('setor'), data.get('data_admissao'), data['status'],
                data.get('observacoes')
            ))
            
            responsavel_id = cursor.lastrowid
            self.db.conn.commit()
            
            # Log da ação
            auth_manager.log_action(
                f"Criou responsável: {data['nome']} (ID: {responsavel_id})",
                "Responsáveis",
                "CREATE"
            )
            
            return responsavel_id
        except Exception as e:
            self.db.conn.rollback()
            st.error(f"Erro ao criar responsável: {e}")
            return None
    
    def get_responsaveis(self, filters=None):
        """Busca responsáveis com filtros"""
        try:
            cursor = self.db.conn.cursor()
            
            query = """
                SELECT 
                    id, nome, cargo, email, telefone, cpf, endereco,
                    departamento, setor, data_admissao, status,
                    observacoes, data_criacao
                FROM responsaveis
                WHERE 1=1
            """
            params = []
            
            if filters:
                if filters.get('nome'):
                    query += " AND nome LIKE ?"
                    params.append(f"%{filters['nome']}%")
                if filters.get('cargo'):
                    query += " AND cargo LIKE ?"
                    params.append(f"%{filters['cargo']}%")
                if filters.get('departamento'):
                    query += " AND departamento LIKE ?"
                    params.append(f"%{filters['departamento']}%")
                if filters.get('status'):
                    query += " AND status = ?"
                    params.append(filters['status'])
            
            query += " ORDER BY nome"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            columns = [
                'id', 'nome', 'cargo', 'email', 'telefone', 'cpf', 'endereco',
                'departamento', 'setor', 'data_admissao', 'status',
                'observacoes', 'data_criacao'
            ]
            
            return pd.DataFrame(results, columns=columns) if results else pd.DataFrame()
            
        except Exception as e:
            st.error(f"Erro ao buscar responsáveis: {e}")
            return pd.DataFrame()
    
    def update_responsavel(self, responsavel_id, data):
        """Atualiza um responsável"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("""
                UPDATE responsaveis SET
                    nome = ?, cargo = ?, email = ?, telefone = ?, cpf = ?,
                    endereco = ?, departamento = ?, setor = ?, data_admissao = ?,
                    status = ?, observacoes = ?
                WHERE id = ?
            """, (
                data['nome'], data['cargo'], data['email'], data['telefone'],
                data.get('cpf'), data.get('endereco'), data.get('departamento'),
                data.get('setor'), data.get('data_admissao'), data['status'],
                data.get('observacoes'), responsavel_id
            ))
            
            self.db.conn.commit()
            
            # Log da ação
            auth_manager.log_action(
                f"Atualizou responsável: {data['nome']} (ID: {responsavel_id})",
                "Responsáveis",
                "UPDATE"
            )
            
            return True
        except Exception as e:
            self.db.conn.rollback()
            st.error(f"Erro ao atualizar responsável: {e}")
            return False
    
    def delete_responsavel(self, responsavel_id, nome):
        """Remove um responsável"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("DELETE FROM responsaveis WHERE id = ?", (responsavel_id,))
            self.db.conn.commit()
            
            # Log da ação
            auth_manager.log_action(
                f"Removeu responsável: {nome} (ID: {responsavel_id})",
                "Responsáveis",
                "DELETE"
            )
            
            return True
        except Exception as e:
            self.db.conn.rollback()
            st.error(f"Erro ao remover responsável: {e}")
            return False
    
    def get_status_options(self):
        """Retorna opções de status"""
        return ['Ativo', 'Inativo', 'Férias', 'Licença', 'Afastado']
    
    def get_dashboard_stats(self):
        """Estatísticas para o dashboard"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Ativo' THEN 1 ELSE 0 END) as ativos,
                    SUM(CASE WHEN status = 'Inativo' THEN 1 ELSE 0 END) as inativos,
                    SUM(CASE WHEN status = 'Férias' THEN 1 ELSE 0 END) as ferias,
                    SUM(CASE WHEN status = 'Licença' THEN 1 ELSE 0 END) as licenca
                FROM responsaveis
            """)
            
            result = cursor.fetchone()
            return {
                'total': result[0] or 0,
                'ativos': result[1] or 0,
                'inativos': result[2] or 0,
                'ferias': result[3] or 0,
                'licenca': result[4] or 0
            }
        except:
            return {'total': 0, 'ativos': 0, 'inativos': 0, 'ferias': 0, 'licenca': 0}

def show_responsaveis_page():
    """Interface principal dos responsáveis"""
    
    st.title("👥 Gestão de Responsáveis")
    
    if not auth_manager.check_permission("responsaveis", "read"):
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
                filtro_status = st.selectbox("Status", ["Todos"] + manager.get_status_options())
        
        # Aplicar filtros
        filters = {}
        if filtro_nome:
            filters['nome'] = filtro_nome
        if filtro_cargo:
            filters['cargo'] = filtro_cargo
        if filtro_departamento:
            filters['departamento'] = filtro_departamento
        if filtro_status != "Todos":
            filters['status'] = filtro_status
        
        # Buscar responsáveis
        df = manager.get_responsaveis(filters)
        
        if not df.empty:
            st.dataframe(
                df[['nome', 'cargo', 'email', 'telefone', 'departamento', 'setor', 'status']],
                column_config={
                    'nome': 'Nome',
                    'cargo': 'Cargo',
                    'email': 'E-mail',
                    'telefone': 'Telefone',
                    'departamento': 'Departamento',
                    'setor': 'Setor',
                    'status': 'Status'
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("📭 Nenhum responsável encontrado com os filtros aplicados.")
    
    with tab2:
        if not auth_manager.check_permission("responsaveis", "create"):
            st.error("❌ Você não tem permissão para adicionar responsáveis.")
            return
        
        st.subheader("Adicionar Novo Responsável")
        
        with st.form("form_responsavel"):
            # Informações básicas
            st.markdown("### Informações Básicas")
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome Completo *", placeholder="Ex: João da Silva")
                cargo = st.text_input("Cargo *", placeholder="Ex: Engenheiro Civil")
                email = st.text_input("E-mail *", placeholder="joao@empresa.com")
                telefone = st.text_input("Telefone *", placeholder="(11) 99999-9999")
            
            with col2:
                cpf = st.text_input("CPF", placeholder="000.000.000-00")
                status = st.selectbox("Status *", manager.get_status_options())
                data_admissao = st.date_input("Data de Admissão", value=None)
            
            # Endereço
            endereco = st.text_area("Endereço", placeholder="Endereço completo")
            
            # Departamento e Setor
            st.markdown("### Lotação")
            col1, col2 = st.columns(2)
            
            with col1:
                departamento = st.text_input("Departamento", placeholder="Ex: Engenharia")
            
            with col2:
                setor = st.text_input("Setor", placeholder="Ex: Projetos")
            
            # Observações
            observacoes = st.text_area("Observações", placeholder="Informações adicionais")
            
            submitted = st.form_submit_button("💾 Cadastrar Responsável", type="primary")
            
            if submitted:
                if nome and cargo and email and telefone and status:
                    data = {
                        'nome': nome,
                        'cargo': cargo,
                        'email': email,
                        'telefone': telefone,
                        'cpf': cpf,
                        'endereco': endereco,
                        'departamento': departamento,
                        'setor': setor,
                        'data_admissao': data_admissao.strftime('%Y-%m-%d') if data_admissao else None,
                        'status': status,
                        'observacoes': observacoes
                    }
                    
                    responsavel_id = manager.create_responsavel(data)
                    if responsavel_id:
                        st.success(f"✅ Responsável '{nome}' cadastrado com sucesso! (ID: {responsavel_id})")
                        st.rerun()
                else:
                    st.error("❌ Preencha todos os campos obrigatórios marcados com *")
    
    with tab3:
        st.subheader("Estatísticas dos Responsáveis")
        
        stats = manager.get_dashboard_stats()
        
        # Cards de estatísticas
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total", stats['total'])
        
        with col2:
            st.metric("Ativos", stats['ativos'])
        
        with col3:
            st.metric("Inativos", stats['inativos'])
        
        with col4:
            st.metric("Férias", stats['ferias'])
        
        with col5:
            st.metric("Licença", stats['licenca'])
        
        # Gráficos
        if stats['total'] > 0:
            df_stats = manager.get_responsaveis()
            
            if not df_stats.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Gráfico por status
                    status_counts = df_stats['status'].value_counts()
                    st.plotly_chart(
                        {
                            'data': [{
                                'type': 'pie',
                                'labels': status_counts.index.tolist(),
                                'values': status_counts.values.tolist(),
                                'title': 'Distribuição por Status'
                            }],
                            'layout': {'title': 'Responsáveis por Status'}
                        },
                        use_container_width=True
                    )
                
                with col2:
                    # Gráfico por departamento
                    dept_counts = df_stats['departamento'].value_counts().head(10)
                    if not dept_counts.empty:
                        st.plotly_chart(
                            {
                                'data': [{
                                    'type': 'bar',
                                    'x': dept_counts.index.tolist(),
                                    'y': dept_counts.values.tolist()
                                }],
                                'layout': {'title': 'Top 10 Departamentos'}
                            },
                            use_container_width=True
                        )

# Instância global
responsaveis_manager = ResponsaveisManager()