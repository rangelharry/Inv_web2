import streamlit as st
import pandas as pd
from datetime import datetime, date
from database.connection import db
from modules.auth import auth_manager

class EquipamentosManuaisManager:
    def __init__(self):
        self.db = db
    
    def create_equipamento(self, data):
        """Cria um novo equipamento manual"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("""
                INSERT INTO categorias (nome, tipo, descricao) 
                VALUES (?, ?, ?)
            """, (data['categoria'], 'Equipamento Manual', data.get('descricao_categoria', '')))
            categoria_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO itens_inventario (
                    categoria_id, nome, descricao, codigo_patrimonial,
                    valor_unitario, quantidade_atual, quantidade_minima,
                    unidade_medida, localizacao, status, tipo_item,
                    marca, modelo, numero_serie, data_aquisicao,
                    vida_util_anos, observacoes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                categoria_id, data['nome'], data['descricao'], data['codigo_patrimonial'],
                data['valor_unitario'], data['quantidade_atual'], data['quantidade_minima'],
                data['unidade_medida'], data['localizacao'], data['status'], 'Equipamento Manual',
                data['marca'], data['modelo'], data['numero_serie'], data['data_aquisicao'],
                data['vida_util_anos'], data['observacoes']
            ))
            
            equipamento_id = cursor.lastrowid
            self.db.conn.commit()
            
            # Log da ação
            auth_manager.log_action(
                f"Criou equipamento manual: {data['nome']} (ID: {equipamento_id})",
                "Equipamentos Manuais",
                "CREATE"
            )
            
            return equipamento_id
        except Exception as e:
            self.db.conn.rollback()
            st.error(f"Erro ao criar equipamento: {e}")
            return None
    
    def get_equipamentos(self, filters=None):
        """Busca equipamentos manuais com filtros"""
        try:
            cursor = self.db.conn.cursor()
            
            query = """
                SELECT 
                    i.id, i.nome, i.descricao, i.codigo_patrimonial,
                    i.valor_unitario, i.quantidade_atual, i.quantidade_minima,
                    i.unidade_medida, i.localizacao, i.status,
                    i.marca, i.modelo, i.numero_serie, i.data_aquisicao,
                    i.vida_util_anos, i.observacoes,
                    c.nome as categoria_nome
                FROM itens_inventario i
                LEFT JOIN categorias c ON i.categoria_id = c.id
                WHERE i.tipo_item = 'Equipamento Manual'
            """
            params = []
            
            if filters:
                if filters.get('nome'):
                    query += " AND i.nome LIKE ?"
                    params.append(f"%{filters['nome']}%")
                if filters.get('categoria'):
                    query += " AND c.nome = ?"
                    params.append(filters['categoria'])
                if filters.get('status'):
                    query += " AND i.status = ?"
                    params.append(filters['status'])
                if filters.get('marca'):
                    query += " AND i.marca LIKE ?"
                    params.append(f"%{filters['marca']}%")
                if filters.get('localizacao'):
                    query += " AND i.localizacao LIKE ?"
                    params.append(f"%{filters['localizacao']}%")
            
            query += " ORDER BY i.nome"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            columns = [
                'id', 'nome', 'descricao', 'codigo_patrimonial', 'valor_unitario',
                'quantidade_atual', 'quantidade_minima', 'unidade_medida',
                'localizacao', 'status', 'marca', 'modelo', 'numero_serie',
                'data_aquisicao', 'vida_util_anos', 'observacoes', 'categoria_nome'
            ]
            
            return pd.DataFrame(results, columns=columns) if results else pd.DataFrame()
            
        except Exception as e:
            st.error(f"Erro ao buscar equipamentos: {e}")
            return pd.DataFrame()
    
    def update_equipamento(self, equipamento_id, data):
        """Atualiza um equipamento manual"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("""
                UPDATE itens_inventario SET
                    nome = ?, descricao = ?, codigo_patrimonial = ?,
                    valor_unitario = ?, quantidade_atual = ?, quantidade_minima = ?,
                    unidade_medida = ?, localizacao = ?, status = ?,
                    marca = ?, modelo = ?, numero_serie = ?, data_aquisicao = ?,
                    vida_util_anos = ?, observacoes = ?
                WHERE id = ?
            """, (
                data['nome'], data['descricao'], data['codigo_patrimonial'],
                data['valor_unitario'], data['quantidade_atual'], data['quantidade_minima'],
                data['unidade_medida'], data['localizacao'], data['status'],
                data['marca'], data['modelo'], data['numero_serie'], data['data_aquisicao'],
                data['vida_util_anos'], data['observacoes'], equipamento_id
            ))
            
            self.db.conn.commit()
            
            # Log da ação
            auth_manager.log_action(
                f"Atualizou equipamento manual: {data['nome']} (ID: {equipamento_id})",
                "Equipamentos Manuais",
                "UPDATE"
            )
            
            return True
        except Exception as e:
            self.db.conn.rollback()
            st.error(f"Erro ao atualizar equipamento: {e}")
            return False
    
    def delete_equipamento(self, equipamento_id, nome):
        """Remove um equipamento manual"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("DELETE FROM itens_inventario WHERE id = ?", (equipamento_id,))
            self.db.conn.commit()
            
            # Log da ação
            auth_manager.log_action(
                f"Removeu equipamento manual: {nome} (ID: {equipamento_id})",
                "Equipamentos Manuais",
                "DELETE"
            )
            
            return True
        except Exception as e:
            self.db.conn.rollback()
            st.error(f"Erro ao remover equipamento: {e}")
            return False
    
    def get_categorias(self):
        """Busca categorias de equipamentos manuais"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT DISTINCT c.nome 
                FROM categorias c
                JOIN itens_inventario i ON c.id = i.categoria_id
                WHERE i.tipo_item = 'Equipamento Manual'
                ORDER BY c.nome
            """)
            return [row[0] for row in cursor.fetchall()]
        except:
            return []
    
    def get_status_options(self):
        """Retorna opções de status para equipamentos"""
        return ['Ativo', 'Inativo', 'Manutenção', 'Disponível', 'Em Uso', 'Danificado', 'Emprestado']
    
    def get_dashboard_stats(self):
        """Estatísticas para o dashboard"""
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Ativo' THEN 1 ELSE 0 END) as ativos,
                    SUM(CASE WHEN status = 'Disponível' THEN 1 ELSE 0 END) as disponiveis,
                    SUM(CASE WHEN status = 'Em Uso' THEN 1 ELSE 0 END) as em_uso,
                    SUM(valor_unitario * quantidade_atual) as valor_total
                FROM itens_inventario 
                WHERE tipo_item = 'Equipamento Manual'
            """)
            
            result = cursor.fetchone()
            return {
                'total': result[0] or 0,
                'ativos': result[1] or 0,
                'disponiveis': result[2] or 0,
                'em_uso': result[3] or 0,
                'valor_total': result[4] or 0
            }
        except:
            return {'total': 0, 'ativos': 0, 'disponiveis': 0, 'em_uso': 0, 'valor_total': 0}

def show_equipamentos_manuais_page():
    """Interface principal dos equipamentos manuais"""
    
    st.title("🔧 Equipamentos Manuais")
    
    if not auth_manager.check_permission("equipamentos_manuais", "read"):
        st.error("❌ Você não tem permissão para acessar esta página.")
        return
    
    manager = EquipamentosManuaisManager()
    
    # Abas principais
    tab1, tab2, tab3 = st.tabs(["📋 Lista", "➕ Adicionar", "📊 Estatísticas"])
    
    with tab1:
        st.subheader("Lista de Equipamentos Manuais")
        
        # Filtros
        with st.expander("🔍 Filtros", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                filtro_nome = st.text_input("Nome do Equipamento")
                filtro_categoria = st.selectbox(
                    "Categoria", 
                    ["Todas"] + manager.get_categorias()
                )
            with col2:
                filtro_status = st.selectbox(
                    "Status", 
                    ["Todos"] + manager.get_status_options()
                )
                filtro_marca = st.text_input("Marca")
            with col3:
                filtro_localizacao = st.text_input("Localização")
        
        # Aplicar filtros
        filters = {}
        if filtro_nome:
            filters['nome'] = filtro_nome
        if filtro_categoria != "Todas":
            filters['categoria'] = filtro_categoria
        if filtro_status != "Todos":
            filters['status'] = filtro_status
        if filtro_marca:
            filters['marca'] = filtro_marca
        if filtro_localizacao:
            filters['localizacao'] = filtro_localizacao
        
        # Buscar equipamentos
        df = manager.get_equipamentos(filters)
        
        if not df.empty:
            # Configurar exibição do dataframe
            st.dataframe(
                df[['nome', 'categoria_nome', 'marca', 'modelo', 'localizacao', 
                   'status', 'quantidade_atual', 'valor_unitario']],
                column_config={
                    'nome': 'Nome',
                    'categoria_nome': 'Categoria',
                    'marca': 'Marca',
                    'modelo': 'Modelo',
                    'localizacao': 'Localização',
                    'status': 'Status',
                    'quantidade_atual': 'Quantidade',
                    'valor_unitario': st.column_config.NumberColumn(
                        'Valor Unitário',
                        format="R$ %.2f"
                    )
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Ações em lote
            if auth_manager.check_permission("equipamentos_manuais", "update"):
                st.subheader("Ações")
                
                selected_ids = st.multiselect(
                    "Selecionar equipamentos para ação:",
                    options=df['id'].tolist(),
                    format_func=lambda x: df[df['id'] == x]['nome'].iloc[0]
                )
                
                if selected_ids:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✅ Marcar Disponível"):
                            for eq_id in selected_ids:
                                eq_data = df[df['id'] == eq_id].iloc[0].to_dict()
                                eq_data['status'] = 'Disponível'
                                manager.update_equipamento(eq_id, eq_data)
                            st.success("Equipamentos marcados como disponíveis!")
                            st.rerun()
                    
                    with col2:
                        if st.button("🔧 Marcar para Manutenção"):
                            for eq_id in selected_ids:
                                eq_data = df[df['id'] == eq_id].iloc[0].to_dict()
                                eq_data['status'] = 'Manutenção'
                                manager.update_equipamento(eq_id, eq_data)
                            st.success("Equipamentos marcados para manutenção!")
                            st.rerun()
                    
                    with col3:
                        if auth_manager.check_permission("equipamentos_manuais", "delete"):
                            if st.button("🗑️ Remover Selecionados", type="secondary"):
                                for eq_id in selected_ids:
                                    nome = df[df['id'] == eq_id]['nome'].iloc[0]
                                    manager.delete_equipamento(eq_id, nome)
                                st.success("Equipamentos removidos!")
                                st.rerun()
        else:
            st.info("📭 Nenhum equipamento encontrado com os filtros aplicados.")
    
    with tab2:
        if not auth_manager.check_permission("equipamentos_manuais", "create"):
            st.error("❌ Você não tem permissão para adicionar equipamentos.")
            return
        
        st.subheader("Adicionar Novo Equipamento Manual")
        
        with st.form("form_equipamento_manual"):
            # Informações básicas
            st.markdown("### Informações Básicas")
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome do Equipamento *", placeholder="Ex: Furadeira")
                categoria = st.text_input("Categoria *", placeholder="Ex: Ferramentas Elétricas")
                codigo = st.text_input("Código Patrimonial", placeholder="EM001")
                marca = st.text_input("Marca", placeholder="Ex: Bosch")
                modelo = st.text_input("Modelo", placeholder="Ex: GSB 450 RE")
                numero_serie = st.text_input("Número de Série")
            
            with col2:
                descricao = st.text_area("Descrição", placeholder="Descrição detalhada do equipamento")
                localizacao = st.text_input("Localização *", placeholder="Ex: Almoxarifado - Prateleira A")
                status = st.selectbox("Status *", manager.get_status_options())
                unidade_medida = st.selectbox("Unidade", ["UN", "PC", "JG", "KT"])
                quantidade_atual = st.number_input("Quantidade Atual *", min_value=0, value=1)
                quantidade_minima = st.number_input("Quantidade Mínima", min_value=0, value=1)
            
            # Especificações e valores
            st.markdown("### Especificações e Valores")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                valor_unitario = st.number_input("Valor Unitário (R$) *", min_value=0.0, step=0.01)
            
            with col2:
                data_aquisicao = st.date_input("Data de Aquisição", value=date.today())
            
            with col3:
                vida_util = st.number_input("Vida Útil (anos)", min_value=1, value=5)
            
            # Observações
            st.markdown("### Observações")
            observacoes = st.text_area(
                "Observações",
                placeholder="Informações adicionais sobre o equipamento, estado de conservação, etc.",
                height=100
            )
            
            submitted = st.form_submit_button("💾 Cadastrar Equipamento", type="primary")
            
            if submitted:
                if nome and categoria and localizacao and valor_unitario:
                    data = {
                        'nome': nome,
                        'categoria': categoria,
                        'descricao': descricao,
                        'codigo_patrimonial': codigo,
                        'marca': marca,
                        'modelo': modelo,
                        'numero_serie': numero_serie,
                        'localizacao': localizacao,
                        'status': status,
                        'unidade_medida': unidade_medida,
                        'quantidade_atual': quantidade_atual,
                        'quantidade_minima': quantidade_minima,
                        'valor_unitario': valor_unitario,
                        'vida_util_anos': vida_util,
                        'data_aquisicao': data_aquisicao.strftime('%Y-%m-%d'),
                        'observacoes': observacoes
                    }
                    
                    equipamento_id = manager.create_equipamento(data)
                    if equipamento_id:
                        st.success(f"✅ Equipamento '{nome}' cadastrado com sucesso! (ID: {equipamento_id})")
                        st.rerun()
                else:
                    st.error("❌ Preencha todos os campos obrigatórios marcados com *")
    
    with tab3:
        st.subheader("Estatísticas dos Equipamentos Manuais")
        
        stats = manager.get_dashboard_stats()
        
        # Cards de estatísticas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Equipamentos", stats['total'])
        
        with col2:
            st.metric("Equipamentos Ativos", stats['ativos'])
        
        with col3:
            st.metric("Disponíveis", stats['disponiveis'])
        
        with col4:
            st.metric("Em Uso", stats['em_uso'])
        
        # Valor total
        st.metric("Valor Total dos Equipamentos", f"R$ {stats['valor_total']:,.2f}")
        
        # Gráficos
        if stats['total'] > 0:
            df_stats = manager.get_equipamentos()
            
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
                            'layout': {'title': 'Equipamentos por Status'}
                        },
                        use_container_width=True
                    )
                
                with col2:
                    # Gráfico por categoria
                    categoria_counts = df_stats['categoria_nome'].value_counts()
                    st.plotly_chart(
                        {
                            'data': [{
                                'type': 'bar',
                                'x': categoria_counts.index.tolist(),
                                'y': categoria_counts.values.tolist()
                            }],
                            'layout': {'title': 'Equipamentos por Categoria'}
                        },
                        use_container_width=True
                    )

# Instância global
equipamentos_manuais_manager = EquipamentosManuaisManager()