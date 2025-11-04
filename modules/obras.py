import streamlit as st
import pandas as pd
from datetime import datetime, date
from database.connection import db
from modules.auth import auth_manager

class ObrasManager:
    def __init__(self):
        self.db = db
    
    def create_obra(self, data):
        """Cria uma nova obra/departamento"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("""
                INSERT INTO obras (
                    nome, descricao, endereco, tipo, status,
                    data_inicio, data_fim_prevista, responsavel,
                    orcamento, valor_gasto, observacoes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['nome'], data['descricao'], data['endereco'],
                data['tipo'], data['status'], data['data_inicio'],
                data.get('data_fim_prevista'), data['responsavel'],
                data.get('orcamento'), data.get('valor_gasto', 0),
                data.get('observacoes')
            ))
            
            obra_id = cursor.lastrowid
            self.db.conn.commit()
            
            # Log da ação
            auth_manager.log_action(
                f"Criou obra/departamento: {data['nome']} (ID: {obra_id})",
                "Obras/Departamentos",
                "CREATE"
            )
            
            return obra_id
        except Exception as e:
            self.db.conn.rollback()
            st.error(f"Erro ao criar obra: {e}")
            return None
    
    def get_obras(self, filters=None):
        """Busca obras com filtros"""
        try:
            cursor = self.db.conn.cursor()
            
            query = """
                SELECT 
                    id, nome, descricao, endereco, tipo, status,
                    data_inicio, data_fim_prevista, data_fim_real,
                    responsavel, orcamento, valor_gasto, observacoes,
                    data_criacao
                FROM obras
                WHERE 1=1
            """
            params = []
            
            if filters:
                if filters.get('nome'):
                    query += " AND nome LIKE ?"
                    params.append(f"%{filters['nome']}%")
                if filters.get('tipo'):
                    query += " AND tipo = ?"
                    params.append(filters['tipo'])
                if filters.get('status'):
                    query += " AND status = ?"
                    params.append(filters['status'])
                if filters.get('responsavel'):
                    query += " AND responsavel LIKE ?"
                    params.append(f"%{filters['responsavel']}%")
            
            query += " ORDER BY nome"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            columns = [
                'id', 'nome', 'descricao', 'endereco', 'tipo', 'status',
                'data_inicio', 'data_fim_prevista', 'data_fim_real',
                'responsavel', 'orcamento', 'valor_gasto', 'observacoes',
                'data_criacao'
            ]
            
            return pd.DataFrame(results, columns=columns) if results else pd.DataFrame()
            
        except Exception as e:
            st.error(f"Erro ao buscar obras: {e}")
            return pd.DataFrame()
    
    def update_obra(self, obra_id, data):
        """Atualiza uma obra/departamento"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("""
                UPDATE obras SET
                    nome = ?, descricao = ?, endereco = ?, tipo = ?,
                    status = ?, data_inicio = ?, data_fim_prevista = ?,
                    responsavel = ?, orcamento = ?, valor_gasto = ?,
                    observacoes = ?
                WHERE id = ?
            """, (
                data['nome'], data['descricao'], data['endereco'],
                data['tipo'], data['status'], data['data_inicio'],
                data.get('data_fim_prevista'), data['responsavel'],
                data.get('orcamento'), data.get('valor_gasto'),
                data.get('observacoes'), obra_id
            ))
            
            self.db.conn.commit()
            
            # Log da ação
            auth_manager.log_action(
                f"Atualizou obra/departamento: {data['nome']} (ID: {obra_id})",
                "Obras/Departamentos",
                "UPDATE"
            )
            
            return True
        except Exception as e:
            self.db.conn.rollback()
            st.error(f"Erro ao atualizar obra: {e}")
            return False
    
    def delete_obra(self, obra_id, nome):
        """Remove uma obra/departamento"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("DELETE FROM obras WHERE id = ?", (obra_id,))
            self.db.conn.commit()
            
            # Log da ação
            auth_manager.log_action(
                f"Removeu obra/departamento: {nome} (ID: {obra_id})",
                "Obras/Departamentos",
                "DELETE"
            )
            
            return True
        except Exception as e:
            self.db.conn.rollback()
            st.error(f"Erro ao remover obra: {e}")
            return False
    
    def get_tipos_obra(self):
        """Retorna tipos de obras/departamentos"""
        return ['Obra', 'Departamento', 'Setor', 'Unidade', 'Filial', 'Projeto']
    
    def get_status_options(self):
        """Retorna opções de status"""
        return ['Planejamento', 'Em Andamento', 'Pausada', 'Concluída', 'Cancelada', 'Ativo', 'Inativo']
    
    def get_dashboard_stats(self):
        """Estatísticas para o dashboard"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Ativo' THEN 1 ELSE 0 END) as ativas,
                    SUM(CASE WHEN status = 'Em Andamento' THEN 1 ELSE 0 END) as em_andamento,
                    SUM(CASE WHEN status = 'Concluída' THEN 1 ELSE 0 END) as concluidas,
                    SUM(orcamento) as orcamento_total,
                    SUM(valor_gasto) as valor_gasto_total
                FROM obras
            """)
            
            result = cursor.fetchone()
            return {
                'total': result[0] or 0,
                'ativas': result[1] or 0,
                'em_andamento': result[2] or 0,
                'concluidas': result[3] or 0,
                'orcamento_total': result[4] or 0,
                'valor_gasto_total': result[5] or 0
            }
        except:
            return {
                'total': 0, 'ativas': 0, 'em_andamento': 0, 'concluidas': 0,
                'orcamento_total': 0, 'valor_gasto_total': 0
            }

def show_obras_page():
    """Interface principal das obras/departamentos"""
    
    st.title("🏗️ Obras e Departamentos")
    
    if not auth_manager.check_permission("obras", "read"):
        st.error("❌ Você não tem permissão para acessar esta página.")
        return
    
    manager = ObrasManager()
    
    # Abas principais
    tab1, tab2, tab3 = st.tabs(["📋 Lista", "➕ Adicionar", "📊 Estatísticas"])
    
    with tab1:
        st.subheader("Lista de Obras e Departamentos")
        
        # Filtros
        with st.expander("🔍 Filtros", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                filtro_nome = st.text_input("Nome")
                filtro_tipo = st.selectbox("Tipo", ["Todos"] + manager.get_tipos_obra())
            with col2:
                filtro_status = st.selectbox("Status", ["Todos"] + manager.get_status_options())
                filtro_responsavel = st.text_input("Responsável")
        
        # Aplicar filtros
        filters = {}
        if filtro_nome:
            filters['nome'] = filtro_nome
        if filtro_tipo != "Todos":
            filters['tipo'] = filtro_tipo
        if filtro_status != "Todos":
            filters['status'] = filtro_status
        if filtro_responsavel:
            filters['responsavel'] = filtro_responsavel
        
        # Buscar obras
        df = manager.get_obras(filters)
        
        if not df.empty:
            st.dataframe(
                df[['nome', 'tipo', 'status', 'responsavel', 'data_inicio', 'orcamento', 'valor_gasto']],
                column_config={
                    'nome': 'Nome',
                    'tipo': 'Tipo',
                    'status': 'Status',
                    'responsavel': 'Responsável',
                    'data_inicio': 'Data Início',
                    'orcamento': st.column_config.NumberColumn(
                        'Orçamento',
                        format="R$ %.2f"
                    ),
                    'valor_gasto': st.column_config.NumberColumn(
                        'Valor Gasto',
                        format="R$ %.2f"
                    )
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("📭 Nenhuma obra/departamento encontrada com os filtros aplicados.")
    
    with tab2:
        if not auth_manager.check_permission("obras", "create"):
            st.error("❌ Você não tem permissão para adicionar obras.")
            return
        
        st.subheader("Adicionar Nova Obra/Departamento")
        
        with st.form("form_obra"):
            # Informações básicas
            st.markdown("### Informações Básicas")
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome *", placeholder="Ex: Obra Residencial - Bairro X")
                tipo = st.selectbox("Tipo *", manager.get_tipos_obra())
                status = st.selectbox("Status *", manager.get_status_options())
                responsavel = st.text_input("Responsável *", placeholder="Ex: João Silva")
            
            with col2:
                endereco = st.text_area("Endereço", placeholder="Endereço completo")
                data_inicio = st.date_input("Data de Início *", value=date.today())
                data_fim_prevista = st.date_input("Data Fim Prevista", value=None)
            
            # Descrição
            descricao = st.text_area("Descrição", placeholder="Descrição detalhada da obra/departamento")
            
            # Orçamento
            st.markdown("### Orçamento e Custos")
            col1, col2 = st.columns(2)
            
            with col1:
                orcamento = st.number_input("Orçamento (R$)", min_value=0.0, step=0.01)
            
            with col2:
                valor_gasto = st.number_input("Valor Já Gasto (R$)", min_value=0.0, step=0.01)
            
            # Observações
            observacoes = st.text_area("Observações", placeholder="Informações adicionais")
            
            submitted = st.form_submit_button("💾 Cadastrar Obra/Departamento", type="primary")
            
            if submitted:
                if nome and tipo and status and responsavel and data_inicio:
                    data = {
                        'nome': nome,
                        'tipo': tipo,
                        'status': status,
                        'responsavel': responsavel,
                        'endereco': endereco,
                        'data_inicio': data_inicio.strftime('%Y-%m-%d'),
                        'data_fim_prevista': data_fim_prevista.strftime('%Y-%m-%d') if data_fim_prevista else None,
                        'descricao': descricao,
                        'orcamento': orcamento if orcamento > 0 else None,
                        'valor_gasto': valor_gasto,
                        'observacoes': observacoes
                    }
                    
                    obra_id = manager.create_obra(data)
                    if obra_id:
                        st.success(f"✅ Obra/Departamento '{nome}' cadastrada com sucesso! (ID: {obra_id})")
                        st.rerun()
                else:
                    st.error("❌ Preencha todos os campos obrigatórios marcados com *")
    
    with tab3:
        st.subheader("Estatísticas das Obras e Departamentos")
        
        stats = manager.get_dashboard_stats()
        
        # Cards de estatísticas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total", stats['total'])
        
        with col2:
            st.metric("Ativas", stats['ativas'])
        
        with col3:
            st.metric("Em Andamento", stats['em_andamento'])
        
        with col4:
            st.metric("Concluídas", stats['concluidas'])
        
        # Valores
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Orçamento Total", f"R$ {stats['orcamento_total']:,.2f}")
        
        with col2:
            st.metric("Valor Gasto", f"R$ {stats['valor_gasto_total']:,.2f}")
        
        with col3:
            economia = stats['orcamento_total'] - stats['valor_gasto_total']
            st.metric(
                "Saldo", 
                f"R$ {economia:,.2f}",
                delta=f"R$ {economia:,.2f}" if economia >= 0 else None
            )
        
        # Gráficos
        if stats['total'] > 0:
            df_stats = manager.get_obras()
            
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
                            'layout': {'title': 'Obras por Status'}
                        },
                        use_container_width=True
                    )
                
                with col2:
                    # Gráfico por tipo
                    tipo_counts = df_stats['tipo'].value_counts()
                    st.plotly_chart(
                        {
                            'data': [{
                                'type': 'bar',
                                'x': tipo_counts.index.tolist(),
                                'y': tipo_counts.values.tolist()
                            }],
                            'layout': {'title': 'Obras por Tipo'}
                        },
                        use_container_width=True
                    )

# Instância global
obras_manager = ObrasManager()