import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database.connection import db
from modules.auth import auth_manager
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

class RelatoriosManager:
    def __init__(self):
        self.db = db
    
    def gerar_relatorio_inventario_completo(self):
        """Gera relatório completo do inventário"""
        try:
            cursor = self.db.conn.cursor()
            
            query = """
                SELECT 
                    i.nome as item, i.codigo_patrimonial, i.tipo_item,
                    c.nome as categoria, i.quantidade_atual, i.quantidade_minima,
                    i.valor_unitario, (i.quantidade_atual * i.valor_unitario) as valor_total,
                    i.localizacao, i.status, i.unidade_medida
                FROM itens_inventario i
                LEFT JOIN categorias c ON i.categoria_id = c.id
                UNION ALL
                SELECT 
                    nome as item, codigo as codigo_patrimonial, 'Insumo' as tipo_item,
                    categoria, quantidade_atual, quantidade_minima,
                    preco_unitario as valor_unitario, 
                    (quantidade_atual * preco_unitario) as valor_total,
                    localizacao, CASE WHEN ativo = 1 THEN 'Ativo' ELSE 'Inativo' END as status,
                    unidade as unidade_medida
                FROM insumos
                ORDER BY tipo_item, item
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            columns = [
                'item', 'codigo_patrimonial', 'tipo_item', 'categoria',
                'quantidade_atual', 'quantidade_minima', 'valor_unitario',
                'valor_total', 'localizacao', 'status', 'unidade_medida'
            ]
            
            return pd.DataFrame(results, columns=columns)
            
        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")
            return pd.DataFrame()
    
    def gerar_relatorio_movimentacoes(self, data_inicio, data_fim):
        """Gera relatório de movimentações por período"""
        try:
            cursor = self.db.conn.cursor()
            
            query = """
                SELECT 
                    m.data_movimentacao, m.tipo_movimentacao, m.quantidade,
                    m.motivo, m.origem, m.destino, m.valor_unitario,
                    i.nome as item_nome, i.codigo_patrimonial,
                    u.nome as usuario_nome
                FROM movimentacoes_estoque m
                LEFT JOIN itens_inventario i ON m.item_id = i.id
                LEFT JOIN usuarios u ON m.usuario_id = u.id
                WHERE DATE(m.data_movimentacao) BETWEEN ? AND ?
                ORDER BY m.data_movimentacao DESC
            """
            
            cursor.execute(query, (data_inicio, data_fim))
            results = cursor.fetchall()
            
            columns = [
                'data_movimentacao', 'tipo_movimentacao', 'quantidade',
                'motivo', 'origem', 'destino', 'valor_unitario',
                'item_nome', 'codigo_patrimonial', 'usuario_nome'
            ]
            
            return pd.DataFrame(results, columns=columns)
            
        except Exception as e:
            st.error(f"Erro ao gerar relatório de movimentações: {e}")
            return pd.DataFrame()
    
    def gerar_relatorio_estoque_baixo(self):
        """Gera relatório de itens com estoque baixo"""
        try:
            cursor = self.db.conn.cursor()
            
            query = """
                SELECT 
                    nome as item, codigo_patrimonial, categoria, tipo_item,
                    quantidade_atual, quantidade_minima, 
                    (quantidade_minima - quantidade_atual) as deficit,
                    valor_unitario, localizacao
                FROM (
                    SELECT 
                        i.nome, i.codigo_patrimonial, c.nome as categoria, i.tipo_item,
                        i.quantidade_atual, i.quantidade_minima, i.valor_unitario,
                        i.localizacao
                    FROM itens_inventario i
                    LEFT JOIN categorias c ON i.categoria_id = c.id
                    WHERE i.quantidade_atual <= i.quantidade_minima
                    UNION ALL
                    SELECT 
                        nome, codigo as codigo_patrimonial, categoria, 'Insumo' as tipo_item,
                        quantidade_atual, quantidade_minima, preco_unitario as valor_unitario,
                        localizacao
                    FROM insumos
                    WHERE quantidade_atual <= quantidade_minima AND ativo = 1
                ) 
                ORDER BY (quantidade_minima - quantidade_atual) DESC
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            columns = [
                'item', 'codigo_patrimonial', 'categoria', 'tipo_item',
                'quantidade_atual', 'quantidade_minima', 'deficit',
                'valor_unitario', 'localizacao'
            ]
            
            return pd.DataFrame(results, columns=columns)
            
        except Exception as e:
            st.error(f"Erro ao gerar relatório de estoque baixo: {e}")
            return pd.DataFrame()
    
    def exportar_excel(self, df, nome_arquivo):
        """Exporta DataFrame para Excel"""
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Dados', index=False)
        
        return buffer.getvalue()

def show_relatorios_page():
    """Interface principal dos relatórios"""
    
    st.title("📊 Sistema de Relatórios")
    
    if not auth_manager.check_permission("relatorios", "read"):
        st.error("❌ Você não tem permissão para acessar esta página.")
        return
    
    manager = RelatoriosManager()
    
    # Abas principais
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Inventário Completo", 
        "📦 Movimentações", 
        "⚠️ Estoque Baixo",
        "📈 Dashboard Executivo"
    ])
    
    with tab1:
        st.subheader("Relatório Completo do Inventário")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info("💡 Este relatório inclui todos os itens cadastrados no sistema: equipamentos elétricos, manuais e insumos.")
        
        with col2:
            if st.button("🔄 Gerar Relatório", type="primary"):
                with st.spinner("Gerando relatório..."):
                    df_inventario = manager.gerar_relatorio_inventario_completo()
                    st.session_state.df_inventario = df_inventario
        
        if 'df_inventario' in st.session_state and not st.session_state.df_inventario.empty:
            df = st.session_state.df_inventario
            
            # Estatísticas resumo
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Itens", len(df))
            
            with col2:
                valor_total = df['valor_total'].fillna(0).sum()
                st.metric("Valor Total", f"R$ {valor_total:,.2f}")
            
            with col3:
                itens_baixo_estoque = len(df[df['quantidade_atual'] <= df['quantidade_minima']])
                st.metric("Estoque Baixo", itens_baixo_estoque)
            
            with col4:
                tipos_unicos = df['tipo_item'].nunique()
                st.metric("Tipos de Itens", tipos_unicos)
            
            # Filtros
            with st.expander("🔍 Filtros"):
                col1, col2 = st.columns(2)
                with col1:
                    tipo_filtro = st.multiselect("Tipo de Item", df['tipo_item'].unique())
                    categoria_filtro = st.multiselect("Categoria", df['categoria'].unique())
                
                with col2:
                    status_filtro = st.multiselect("Status", df['status'].unique())
            
            # Aplicar filtros
            df_filtrado = df.copy()
            if tipo_filtro:
                df_filtrado = df_filtrado[df_filtrado['tipo_item'].isin(tipo_filtro)]
            if categoria_filtro:
                df_filtrado = df_filtrado[df_filtrado['categoria'].isin(categoria_filtro)]
            if status_filtro:
                df_filtrado = df_filtrado[df_filtrado['status'].isin(status_filtro)]
            
            # Exibir dados
            st.dataframe(
                df_filtrado,
                column_config={
                    'valor_unitario': st.column_config.NumberColumn('Valor Unit.', format="R$ %.2f"),
                    'valor_total': st.column_config.NumberColumn('Valor Total', format="R$ %.2f")
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Botão de download
            excel_data = manager.exportar_excel(df_filtrado, 'inventario_completo')
            st.download_button(
                label="📥 Download Excel",
                data=excel_data,
                file_name=f"inventario_completo_{date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with tab2:
        st.subheader("Relatório de Movimentações")
        
        # Seleção de período
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            data_inicio = st.date_input(
                "Data Início", 
                value=date.today() - timedelta(days=30)
            )
        
        with col2:
            data_fim = st.date_input("Data Fim", value=date.today())
        
        with col3:
            if st.button("🔄 Gerar", type="primary", key="btn_movimentacoes"):
                with st.spinner("Gerando relatório..."):
                    df_mov = manager.gerar_relatorio_movimentacoes(
                        data_inicio.strftime('%Y-%m-%d'),
                        data_fim.strftime('%Y-%m-%d')
                    )
                    st.session_state.df_movimentacoes = df_mov
        
        if 'df_movimentacoes' in st.session_state and not st.session_state.df_movimentacoes.empty:
            df = st.session_state.df_movimentacoes
            
            # Estatísticas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Movimentações", len(df))
            
            with col2:
                entradas = len(df[df['tipo_movimentacao'] == 'Entrada'])
                st.metric("Entradas", entradas)
            
            with col3:
                saidas = len(df[df['tipo_movimentacao'] == 'Saída'])
                st.metric("Saídas", saidas)
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    df, 
                    names='tipo_movimentacao',
                    title="Movimentações por Tipo"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                motivo_counts = df['motivo'].value_counts().head(5)
                fig = px.bar(
                    x=motivo_counts.values,
                    y=motivo_counts.index,
                    orientation='h',
                    title="Top 5 Motivos"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Tabela de dados
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Download
            excel_data = manager.exportar_excel(df, 'movimentacoes')
            st.download_button(
                label="📥 Download Excel",
                data=excel_data,
                file_name=f"movimentacoes_{data_inicio}_{data_fim}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with tab3:
        st.subheader("Relatório de Estoque Baixo")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.warning("⚠️ Itens que atingiram ou estão abaixo do estoque mínimo")
        
        with col2:
            if st.button("🔄 Atualizar", type="primary", key="btn_estoque_baixo"):
                with st.spinner("Analisando estoques..."):
                    df_baixo = manager.gerar_relatorio_estoque_baixo()
                    st.session_state.df_estoque_baixo = df_baixo
        
        if 'df_estoque_baixo' in st.session_state and not st.session_state.df_estoque_baixo.empty:
            df = st.session_state.df_estoque_baixo
            
            # Alertas críticos
            itens_criticos = df[df['deficit'] >= 0]
            if not itens_criticos.empty:
                st.error(f"🚨 {len(itens_criticos)} itens precisam de reposição urgente!")
            
            # Estatísticas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Itens em Alerta", len(df))
            
            with col2:
                valor_reposicao = (df['deficit'] * df['valor_unitario']).fillna(0).sum()
                st.metric("Valor para Reposição", f"R$ {valor_reposicao:,.2f}")
            
            with col3:
                categorias_afetadas = df['categoria'].nunique()
                st.metric("Categorias Afetadas", categorias_afetadas)
            
            # Gráfico
            fig = px.bar(
                df.head(10),
                x='deficit',
                y='item',
                orientation='h',
                title="Top 10 Itens com Maior Déficit",
                color='deficit',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela
            st.dataframe(
                df,
                column_config={
                    'valor_unitario': st.column_config.NumberColumn('Valor Unit.', format="R$ %.2f")
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Download
            excel_data = manager.exportar_excel(df, 'estoque_baixo')
            st.download_button(
                label="📥 Download Excel",
                data=excel_data,
                file_name=f"estoque_baixo_{date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.success("✅ Todos os itens estão com estoque adequado!")
    
    with tab4:
        st.subheader("Dashboard Executivo")
        
        # Gerar dados para dashboard
        df_inventario = manager.gerar_relatorio_inventario_completo()
        
        if not df_inventario.empty:
            # KPIs principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_itens = len(df_inventario)
                st.metric("📦 Total de Itens", f"{total_itens:,}")
            
            with col2:
                valor_total = df_inventario['valor_total'].fillna(0).sum()
                st.metric("💰 Valor Total do Inventário", f"R$ {valor_total:,.2f}")
            
            with col3:
                itens_ativos = len(df_inventario[df_inventario['status'] == 'Ativo'])
                percentual_ativo = (itens_ativos / total_itens * 100) if total_itens > 0 else 0
                st.metric("✅ Itens Ativos", f"{itens_ativos:,} ({percentual_ativo:.1f}%)")
            
            with col4:
                estoque_baixo = len(df_inventario[
                    df_inventario['quantidade_atual'] <= df_inventario['quantidade_minima']
                ])
                st.metric("⚠️ Alertas de Estoque", estoque_baixo)
            
            # Gráficos executivos
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribuição de valor por categoria
                valor_categoria = df_inventario.groupby('categoria')['valor_total'].sum().sort_values(ascending=False).head(8)
                
                fig = px.pie(
                    values=valor_categoria.values,
                    names=valor_categoria.index,
                    title="Distribuição de Valor por Categoria"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Itens por tipo
                tipo_counts = df_inventario['tipo_item'].value_counts()
                
                fig = px.bar(
                    x=tipo_counts.index,
                    y=tipo_counts.values,
                    title="Quantidade de Itens por Tipo"
                )
                fig.update_layout(xaxis_title="Tipo", yaxis_title="Quantidade")
                st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.info("📊 Carregue os dados do inventário para visualizar o dashboard executivo.")

# Instância global
relatorios_manager = RelatoriosManager()