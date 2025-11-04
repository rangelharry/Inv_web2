import streamlit as st
import pandas as pd
from datetime import datetime, date
from database.connection import db
from modules.auth import auth_manager

class MovimentacoesManager:
    def __init__(self):
        self.db = db
    
    def create_movimentacao(self, data):
        """Cria uma nova movimentação"""
        try:
            cursor = self.db.conn.cursor()
            
            # Verifica se há quantidade suficiente para saída
            if data['tipo_movimentacao'] == 'Saída':
                cursor.execute("""
                    SELECT quantidade_atual FROM itens_inventario WHERE id = ?
                """, (data['item_id'],))
                item = cursor.fetchone()
                if not item or item['quantidade_atual'] < data['quantidade']:
                    st.error(f"❌ Quantidade insuficiente! Disponível: {item['quantidade_atual'] if item else 0}")
                    return None
            
            cursor.execute("""
                INSERT INTO movimentacoes_estoque (
                    item_id, tipo_movimentacao, quantidade, motivo,
                    origem, destino, responsavel_origem, responsavel_destino,
                    valor_unitario, observacoes, usuario_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['item_id'], data['tipo_movimentacao'], data['quantidade'],
                data['motivo'], data['origem'], data['destino'],
                data.get('responsavel_origem'), data.get('responsavel_destino'),
                data.get('valor_unitario'), data.get('observacoes'),
                st.session_state.get('user_id')
            ))
            
            movimentacao_id = cursor.lastrowid
            
            # Atualiza estoque do item
            if data['tipo_movimentacao'] == 'Entrada':
                cursor.execute("""
                    UPDATE itens_inventario 
                    SET quantidade_atual = quantidade_atual + ?
                    WHERE id = ?
                """, (data['quantidade'], data['item_id']))
            else:  # Saída
                cursor.execute("""
                    UPDATE itens_inventario 
                    SET quantidade_atual = quantidade_atual - ?
                    WHERE id = ?
                """, (data['quantidade'], data['item_id']))
            
            self.db.conn.commit()
            
            # Log da ação
            auth_manager.log_action(
                f"Criou movimentação: {data['tipo_movimentacao']} - {data['quantidade']} unidades (ID: {movimentacao_id})",
                "Movimentações",
                "CREATE"
            )
            
            return movimentacao_id
        except Exception as e:
            self.db.conn.rollback()
            st.error(f"Erro ao criar movimentação: {e}")
            return None
    
    def get_movimentacoes(self, filters=None):
        """Busca movimentações com filtros"""
        try:
            cursor = self.db.conn.cursor()
            
            query = """
                SELECT 
                    m.id, m.data_movimentacao, m.tipo_movimentacao, 
                    m.quantidade, m.motivo, m.origem, m.destino,
                    m.responsavel_origem, m.responsavel_destino,
                    m.valor_unitario, m.observacoes,
                    i.nome as item_nome, i.codigo_patrimonial,
                    u.nome as usuario_nome
                FROM movimentacoes_estoque m
                LEFT JOIN itens_inventario i ON m.item_id = i.id
                LEFT JOIN usuarios u ON m.usuario_id = u.id
                WHERE 1=1
            """
            params = []
            
            if filters:
                if filters.get('item_nome'):
                    query += " AND i.nome LIKE ?"
                    params.append(f"%{filters['item_nome']}%")
                if filters.get('tipo_movimentacao'):
                    query += " AND m.tipo_movimentacao = ?"
                    params.append(filters['tipo_movimentacao'])
                if filters.get('origem'):
                    query += " AND m.origem LIKE ?"
                    params.append(f"%{filters['origem']}%")
                if filters.get('destino'):
                    query += " AND m.destino LIKE ?"
                    params.append(f"%{filters['destino']}%")
                if filters.get('data_inicio'):
                    query += " AND DATE(m.data_movimentacao) >= ?"
                    params.append(filters['data_inicio'])
                if filters.get('data_fim'):
                    query += " AND DATE(m.data_movimentacao) <= ?"
                    params.append(filters['data_fim'])
            
            query += " ORDER BY m.data_movimentacao DESC"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            columns = [
                'id', 'data_movimentacao', 'tipo_movimentacao', 'quantidade',
                'motivo', 'origem', 'destino', 'responsavel_origem',
                'responsavel_destino', 'valor_unitario', 'observacoes',
                'item_nome', 'codigo_patrimonial', 'usuario_nome'
            ]
            
            return pd.DataFrame(results, columns=columns) if results else pd.DataFrame()
            
        except Exception as e:
            st.error(f"Erro ao buscar movimentações: {e}")
            return pd.DataFrame()
    
    def get_items_para_movimentacao(self):
        """Busca itens disponíveis para movimentação"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT id, nome, codigo_patrimonial, quantidade_atual, unidade_medida
                FROM itens_inventario 
                ORDER BY nome
            """)
            return cursor.fetchall()
        except:
            return []
    
    def get_dashboard_stats(self):
        """Estatísticas para o dashboard"""
        try:
            cursor = self.db.conn.cursor()
            
            # Movimentações do mês atual
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN tipo_movimentacao = 'Entrada' THEN 1 ELSE 0 END) as entradas,
                    SUM(CASE WHEN tipo_movimentacao = 'Saída' THEN 1 ELSE 0 END) as saidas
                FROM movimentacoes_estoque 
                WHERE strftime('%Y-%m', data_movimentacao) = strftime('%Y-%m', 'now')
            """)
            
            result = cursor.fetchone()
            return {
                'total_mes': result[0] or 0,
                'entradas_mes': result[1] or 0,
                'saidas_mes': result[2] or 0
            }
        except:
            return {'total_mes': 0, 'entradas_mes': 0, 'saidas_mes': 0}

def show_movimentacoes_page():
    """Interface principal das movimentações"""
    
    st.title("📋 Sistema de Movimentações")
    
    if not auth_manager.check_permission("movimentacoes", "read"):
        st.error("❌ Você não tem permissão para acessar esta página.")
        return
    
    manager = MovimentacoesManager()
    
    # Abas principais
    tab1, tab2, tab3 = st.tabs(["📋 Histórico", "➕ Nova Movimentação", "📊 Relatórios"])
    
    with tab1:
        st.subheader("Histórico de Movimentações")
        
        # Filtros
        with st.expander("🔍 Filtros", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                filtro_item = st.text_input("Nome do Item")
                filtro_tipo = st.selectbox("Tipo", ["Todos", "Entrada", "Saída"])
            with col2:
                filtro_origem = st.text_input("Origem")
                filtro_destino = st.text_input("Destino")
            with col3:
                filtro_data_inicio = st.date_input("Data Início", value=None)
                filtro_data_fim = st.date_input("Data Fim", value=None)
        
        # Aplicar filtros
        filters = {}
        if filtro_item:
            filters['item_nome'] = filtro_item
        if filtro_tipo != "Todos":
            filters['tipo_movimentacao'] = filtro_tipo
        if filtro_origem:
            filters['origem'] = filtro_origem
        if filtro_destino:
            filters['destino'] = filtro_destino
        if filtro_data_inicio:
            filters['data_inicio'] = filtro_data_inicio.strftime('%Y-%m-%d')
        if filtro_data_fim:
            filters['data_fim'] = filtro_data_fim.strftime('%Y-%m-%d')
        
        # Buscar movimentações
        df = manager.get_movimentacoes(filters)
        
        if not df.empty:
            st.dataframe(
                df[['data_movimentacao', 'tipo_movimentacao', 'item_nome', 
                   'quantidade', 'origem', 'destino', 'motivo', 'usuario_nome']],
                column_config={
                    'data_movimentacao': 'Data/Hora',
                    'tipo_movimentacao': 'Tipo',
                    'item_nome': 'Item',
                    'quantidade': 'Quantidade',
                    'origem': 'Origem',
                    'destino': 'Destino',
                    'motivo': 'Motivo',
                    'usuario_nome': 'Usuário'
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("📭 Nenhuma movimentação encontrada com os filtros aplicados.")
    
    with tab2:
        if not auth_manager.check_permission("movimentacoes", "create"):
            st.error("❌ Você não tem permissão para criar movimentações.")
            return
        
        st.subheader("Nova Movimentação")
        
        with st.form("form_movimentacao"):
            # Seleção do item
            st.markdown("### Seleção do Item")
            items = manager.get_items_para_movimentacao()
            
            if items:
                item_options = {f"{item[1]} ({item[2]})": item[0] for item in items}
                selected_item = st.selectbox("Item *", options=list(item_options.keys()))
                item_id = item_options[selected_item] if selected_item else None
                
                # Mostrar estoque atual
                if item_id:
                    item_atual = next(item for item in items if item[0] == item_id)
                    st.info(f"📦 Estoque atual: **{item_atual[3]}** {item_atual[4]}")
            else:
                st.warning("⚠️ Nenhum item disponível para movimentação.")
                item_id = None
            
            # Dados da movimentação
            st.markdown("### Dados da Movimentação")
            col1, col2 = st.columns(2)
            
            with col1:
                tipo_movimentacao = st.selectbox("Tipo de Movimentação *", ["Entrada", "Saída"])
                quantidade = st.number_input("Quantidade *", min_value=1, value=1)
                motivo = st.selectbox("Motivo *", [
                    "Compra", "Doação", "Transferência", "Devolução",
                    "Consumo", "Venda", "Perda", "Manutenção", "Empréstimo"
                ])
            
            with col2:
                origem = st.text_input("Origem *", placeholder="Ex: Fornecedor, Almoxarifado")
                destino = st.text_input("Destino *", placeholder="Ex: Obra, Setor, Cliente")
                valor_unitario = st.number_input("Valor Unitário (R$)", min_value=0.0, step=0.01)
            
            # Responsáveis
            st.markdown("### Responsáveis")
            col1, col2 = st.columns(2)
            
            with col1:
                responsavel_origem = st.text_input("Responsável Origem")
            
            with col2:
                responsavel_destino = st.text_input("Responsável Destino")
            
            # Observações
            observacoes = st.text_area("Observações", placeholder="Informações adicionais sobre a movimentação")
            
            submitted = st.form_submit_button("💾 Registrar Movimentação", type="primary")
            
            if submitted:
                if item_id and quantidade and motivo and origem and destino:
                    data = {
                        'item_id': item_id,
                        'tipo_movimentacao': tipo_movimentacao,
                        'quantidade': quantidade,
                        'motivo': motivo,
                        'origem': origem,
                        'destino': destino,
                        'responsavel_origem': responsavel_origem,
                        'responsavel_destino': responsavel_destino,
                        'valor_unitario': valor_unitario if valor_unitario > 0 else None,
                        'observacoes': observacoes
                    }
                    
                    movimentacao_id = manager.create_movimentacao(data)
                    if movimentacao_id:
                        st.success(f"✅ Movimentação registrada com sucesso! (ID: {movimentacao_id})")
                        st.rerun()
                else:
                    st.error("❌ Preencha todos os campos obrigatórios marcados com *")
    
    with tab3:
        st.subheader("Relatórios de Movimentações")
        
        stats = manager.get_dashboard_stats()
        
        # Cards de estatísticas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Movimentações (Mês)", stats['total_mes'])
        
        with col2:
            st.metric("Entradas (Mês)", stats['entradas_mes'])
        
        with col3:
            st.metric("Saídas (Mês)", stats['saidas_mes'])
        
        # Gráficos
        df_stats = manager.get_movimentacoes()
        
        if not df_stats.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico por tipo
                tipo_counts = df_stats['tipo_movimentacao'].value_counts()
                st.plotly_chart(
                    {
                        'data': [{
                            'type': 'pie',
                            'labels': tipo_counts.index.tolist(),
                            'values': tipo_counts.values.tolist(),
                            'title': 'Movimentações por Tipo'
                        }],
                        'layout': {'title': 'Distribuição por Tipo'}
                    },
                    use_container_width=True
                )
            
            with col2:
                # Gráfico por motivo
                motivo_counts = df_stats['motivo'].value_counts().head(10)
                st.plotly_chart(
                    {
                        'data': [{
                            'type': 'bar',
                            'x': motivo_counts.values.tolist(),
                            'y': motivo_counts.index.tolist(),
                            'orientation': 'h'
                        }],
                        'layout': {
                            'title': 'Top 10 Motivos',
                            'xaxis': {'title': 'Quantidade'},
                            'yaxis': {'title': 'Motivo'}
                        }
                    },
                    use_container_width=True
                )

# Instância global
movimentacoes_manager = MovimentacoesManager()