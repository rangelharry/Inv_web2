import streamlit as st  # type: ignore
import pandas as pd  # type: ignore
from datetime import datetime, date, timedelta  # type: ignore # noqa: F401
from database.connection import db  # type: ignore
from modules.auth import auth_manager  # type: ignore
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore # noqa: F401
from io import BytesIO  # type: ignore
from typing import Any  # type: ignore # noqa: F401

class RelatoriosManager:
    def __init__(self):
        self.db = db
    
    def gerar_relatorio_inventario_completo(self) -> pd.DataFrame:  # type: ignore
        """Gera relatório completo do inventário"""
        try:
            cursor = self.db.get_connection().cursor()  # type: ignore
            
            query = """
                SELECT 
                    descricao as item, codigo as codigo_patrimonial, 'Insumo' as tipo_item,
                    'Insumo' as categoria, 0 as quantidade_atual, 0 as quantidade_minima,
                    preco_unitario as valor_unitario, 
                    0 as valor_total,
                    localizacao, CASE WHEN ativo = TRUE THEN 'Ativo' ELSE 'Inativo' END as status,
                    unidade as unidade_medida
                FROM insumos
                UNION ALL
                SELECT 
                    nome as item, codigo as codigo_patrimonial, 'Equipamento Elétrico' as tipo_item,
                    'Equipamento Elétrico' as categoria, 1 as quantidade_atual, 0 as quantidade_minima,
                    COALESCE(valor_compra, 0) as valor_unitario, 
                    COALESCE(valor_compra, 0) as valor_total,
                    localizacao, CASE WHEN ativo = TRUE THEN 'Ativo' ELSE 'Inativo' END as status,
                    'un' as unidade_medida
                FROM equipamentos_eletricos
                UNION ALL
                SELECT 
                    descricao as item, codigo as codigo_patrimonial, 'Equipamento Manual' as tipo_item,
                    tipo as categoria, quantitativo as quantidade_atual, 0 as quantidade_minima,
                    COALESCE(valor, 0) as valor_unitario, 
                    (quantitativo * COALESCE(valor, 0)) as valor_total,
                    localizacao, CASE WHEN ativo = TRUE THEN 'Ativo' ELSE 'Inativo' END as status,
                    'un' as unidade_medida
                FROM equipamentos_manuais
                ORDER BY tipo_item, item
            """
            
            cursor.execute(query)  # type: ignore
            results = cursor.fetchall()  # type: ignore
            
            columns = [
                'item', 'codigo_patrimonial', 'tipo_item', 'categoria',
                'quantidade_atual', 'quantidade_minima', 'valor_unitario',
                'valor_total', 'localizacao', 'status', 'unidade_medida'
            ]
            
            return pd.DataFrame(results, columns=columns)  # type: ignore
            
        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")  # type: ignore
            return pd.DataFrame()  # type: ignore
    
    def gerar_relatorio_movimentacoes(self, data_inicio: str, data_fim: str) -> pd.DataFrame:  # type: ignore
        """Gera relatório de movimentações por período"""
        try:
            cursor = self.db.get_connection().cursor()  # type: ignore
            
            query = """
                SELECT 
                    m.data_movimentacao, m.tipo, m.quantidade,
                    m.motivo, m.obra_origem_id as origem, m.obra_destino_id as destino,
                    m.descricao_item, m.codigo_item,
                    u.nome as usuario_nome
                FROM movimentacoes m
                LEFT JOIN usuarios u ON m.usuario_id = u.id
                WHERE m.data_movimentacao::date BETWEEN %s AND %s
                ORDER BY m.data_movimentacao DESC
            """
            
            cursor.execute(query, (data_inicio, data_fim))  # type: ignore
            results = cursor.fetchall()  # type: ignore
            
            columns = [
                'data_movimentacao', 'tipo', 'quantidade',
                'motivo', 'origem', 'destino',
                'descricao_item', 'codigo_item', 'usuario_nome'
            ]
            
            return pd.DataFrame(results, columns=columns)  # type: ignore
            
        except Exception as e:
            st.error(f"Erro ao gerar relatório de movimentações: {e}")  # type: ignore
            return pd.DataFrame()  # type: ignore
    
    def gerar_relatorio_estoque_baixo(self) -> pd.DataFrame:  # type: ignore
        """Gera relatório de itens com estoque baixo"""
        try:
            cursor = self.db.get_connection().cursor()  # type: ignore
            
            query = """
                SELECT 
                    i.descricao as item, 
                    i.codigo as codigo_patrimonial, 
                    COALESCE(c.nome, 'Sem categoria') as categoria, 
                    'Insumo' as tipo_item,
                    i.quantidade_atual, 
                    i.quantidade_minima, 
                    GREATEST(0, i.quantidade_minima - i.quantidade_atual) as deficit,
                    COALESCE(i.preco_unitario, 0) as valor_unitario, 
                    COALESCE(i.localizacao, 'N/A') as localizacao
                FROM insumos i
                LEFT JOIN categorias c ON i.categoria_id = c.id
                WHERE i.ativo = TRUE 
                AND (i.quantidade_atual <= i.quantidade_minima OR i.quantidade_atual = 0)
                ORDER BY deficit DESC, i.quantidade_atual ASC
            """
            
            cursor.execute(query)  # type: ignore
            results = cursor.fetchall()  # type: ignore
            
            # Converter RealDictRow para dict normal
            return pd.DataFrame([dict(row) for row in results])  # type: ignore
            
        except Exception as e:
            st.error(f"Erro ao gerar relatório de estoque baixo: {e}")  # type: ignore
            return pd.DataFrame()  # type: ignore
    
    def exportar_excel(self, df: pd.DataFrame, nome_arquivo: str) -> bytes:  # type: ignore
        """Exporta DataFrame para Excel"""
        buffer = BytesIO()  # type: ignore
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:  # type: ignore
            df.to_excel(writer, sheet_name='Dados', index=False)  # type: ignore
        
        return buffer.getvalue()  # type: ignore

def show_relatorios_page():  # type: ignore
    """Interface principal dos relatórios"""
    
    st.title("📊 Sistema de Relatórios")  # type: ignore
    user_data = st.session_state.user_data  # type: ignore
    if not auth_manager.check_permission(user_data['perfil'], "read"):  # type: ignore
        st.error("❌ Você não tem permissão para acessar esta página.")  # type: ignore
        return
    manager = RelatoriosManager()  # type: ignore
    
    # Abas principais
    tab1, tab2, tab3, tab4 = st.tabs([  # type: ignore
        "📋 Inventário Completo", 
        "📦 Movimentações", 
        "⚠️ Estoque Baixo",
        "📈 Dashboard Executivo"
    ])  # type: ignore
    
    with tab1:
        st.subheader("Relatório Completo do Inventário")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info("💡 Este relatório inclui todos os itens cadastrados no sistema: equipamentos elétricos, manuais e insumos.")  # type: ignore
        
        with col2:
            if st.button("🔄 Gerar Relatório", type="primary"):  # type: ignore
                with st.spinner("Gerando relatório..."):  # type: ignore
                    df_inventario = manager.gerar_relatorio_inventario_completo()  # type: ignore
                    st.session_state.df_inventario = df_inventario  # type: ignore
        
        if 'df_inventario' in st.session_state and not st.session_state.df_inventario.empty:  # type: ignore
            df = st.session_state.df_inventario  # type: ignore
            
            # Estatísticas resumo
            col1, col2, col3, col4 = st.columns(4)  # type: ignore
            
            with col1:
                st.metric("Total de Itens", len(df))  # type: ignore
            
            with col2:
                valor_total = df['valor_total'].fillna(0).sum()  # type: ignore
                st.metric("Valor Total", f"R$ {valor_total:,.2f}")  # type: ignore
            
            with col3:
                itens_baixo_estoque = len(df[df['quantidade_atual'] <= df['quantidade_minima']])  # type: ignore
                st.metric("Estoque Baixo", itens_baixo_estoque)  # type: ignore
            
            with col4:
                tipos_unicos = df['tipo_item'].nunique()  # type: ignore
                st.metric("Tipos de Itens", tipos_unicos)  # type: ignore
            
            # Filtros
            with st.expander("🔍 Filtros"):  # type: ignore
                col1, col2 = st.columns(2)  # type: ignore
                with col1:
                    tipo_filtro = st.multiselect("Tipo de Item", df['tipo_item'].unique())  # type: ignore
                    categoria_filtro = st.multiselect("Categoria", df['categoria'].unique())  # type: ignore
                
                with col2:
                    status_filtro = st.multiselect("Status", df['status'].unique())  # type: ignore
            
            # Aplicar filtros
            df_filtrado = df.copy()  # type: ignore
            if tipo_filtro:
                df_filtrado = df_filtrado[df_filtrado['tipo_item'].isin(tipo_filtro)]  # type: ignore
            if categoria_filtro:
                df_filtrado = df_filtrado[df_filtrado['categoria'].isin(categoria_filtro)]  # type: ignore
            if status_filtro:
                df_filtrado = df_filtrado[df_filtrado['status'].isin(status_filtro)]  # type: ignore
            
            # Exibir dados
            st.dataframe(  # type: ignore
                df_filtrado,  # type: ignore
                column_config={  # type: ignore
                    'valor_unitario': st.column_config.NumberColumn('Valor Unit.', format="R$ %.2f"),  # type: ignore
                    'valor_total': st.column_config.NumberColumn('Valor Total', format="R$ %.2f")  # type: ignore
                },  # type: ignore
                width='stretch',  # type: ignore
                hide_index=True  # type: ignore
            )  # type: ignore
            
            # Botão de download
            excel_data = manager.exportar_excel(df_filtrado, 'inventario_completo')  # type: ignore
            st.download_button(  # type: ignore
                label="📥 Download Excel",  # type: ignore
                data=excel_data,  # type: ignore
                file_name=f"inventario_completo_{date.today().strftime('%Y%m%d')}.xlsx",  # type: ignore
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"  # type: ignore
            )  # type: ignore
    
    with tab2:
        st.subheader("Relatório de Movimentações")  # type: ignore
        
        # Seleção de período
        col1, col2, col3 = st.columns([2, 2, 1])  # type: ignore
        
        with col1:
            data_inicio = st.date_input(  # type: ignore
                "Data Início",  # type: ignore
                value=date.today() - timedelta(days=30)  # type: ignore
            )  # type: ignore
        
        with col2:
            data_fim = st.date_input("Data Fim", value=date.today())  # type: ignore
        
        with col3:
            if st.button("🔄 Gerar", type="primary", key="btn_movimentacoes"):  # type: ignore
                with st.spinner("Gerando relatório..."):  # type: ignore
                    df_mov = manager.gerar_relatorio_movimentacoes(  # type: ignore
                        data_inicio.strftime('%Y-%m-%d'),  # type: ignore
                        data_fim.strftime('%Y-%m-%d')  # type: ignore
                    )  # type: ignore
                    st.session_state.df_movimentacoes = df_mov  # type: ignore
        
        if 'df_movimentacoes' in st.session_state and not st.session_state.df_movimentacoes.empty:  # type: ignore
            df = st.session_state.df_movimentacoes  # type: ignore
            
            # Estatísticas
            col1, col2, col3 = st.columns(3)  # type: ignore
            
            with col1:
                st.metric("Total Movimentações", len(df))  # type: ignore
            
            with col2:
                entradas = len(df[df['tipo'] == 'Entrada'])  # type: ignore
                st.metric("Entradas", entradas)  # type: ignore
            
            with col3:
                saidas = len(df[df['tipo'] == 'Saída'])  # type: ignore
                st.metric("Saídas", saidas)  # type: ignore
            
            # Gráficos
            col1, col2 = st.columns(2)  # type: ignore
            
            with col1:
                if not df.empty and 'tipo' in df.columns:  # type: ignore
                    tipo_values = df['tipo'].value_counts()  # type: ignore
                    if len(tipo_values) > 0:  # type: ignore
                        fig = px.pie(  # type: ignore
                                df,  # type: ignore
                            names='tipo',  # type: ignore
                            title="Movimentações por Tipo"  # type: ignore
                        )  # type: ignore
                        st.plotly_chart(fig, width='stretch')  # type: ignore
                    else:
                        st.info("📊 Não há dados de tipos para exibir.")  # type: ignore
                else:
                    st.info("📊 Dados insuficientes para gráfico de tipos.")  # type: ignore
            
            with col2:
                if not df.empty and 'motivo' in df.columns:  # type: ignore
                    motivo_counts = df['motivo'].value_counts().head(5)  # type: ignore
                    if len(motivo_counts) > 0:  # type: ignore
                        fig = px.bar(  # type: ignore
                                x=motivo_counts.values,  # type: ignore
                            y=motivo_counts.index,  # type: ignore
                            orientation='h',  # type: ignore
                            title="Top 5 Motivos"  # type: ignore
                        )  # type: ignore
                        st.plotly_chart(fig, width='stretch')  # type: ignore
                    else:
                        st.info("📊 Não há dados de motivos para exibir.")  # type: ignore
                else:
                    st.info("📊 Dados insuficientes para gráfico de motivos.")  # type: ignore
            
            # Tabela de dados
            st.dataframe(df, width='stretch', hide_index=True)  # type: ignore
            
            # Download
            excel_data = manager.exportar_excel(df, 'movimentacoes')  # type: ignore
            st.download_button(  # type: ignore
                label="📥 Download Excel",  # type: ignore
                data=excel_data,  # type: ignore
                file_name=f"movimentacoes_{data_inicio}_{data_fim}.xlsx",  # type: ignore
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"  # type: ignore
            )  # type: ignore
    
    with tab3:
        st.subheader("Relatório de Estoque Baixo")  # type: ignore
        
        col1, col2 = st.columns([3, 1])  # type: ignore
        
        with col1:
            st.warning("⚠️ Itens que atingiram ou estão abaixo do estoque mínimo")  # type: ignore
        
        with col2:
            if st.button("🔄 Atualizar", type="primary", key="btn_estoque_baixo"):  # type: ignore
                with st.spinner("Analisando estoques..."):  # type: ignore
                    df_baixo = manager.gerar_relatorio_estoque_baixo()  # type: ignore
                    st.session_state.df_estoque_baixo = df_baixo  # type: ignore
        
        if 'df_estoque_baixo' in st.session_state and not st.session_state.df_estoque_baixo.empty:  # type: ignore
            df = st.session_state.df_estoque_baixo  # type: ignore
            
            # Alertas críticos
            itens_criticos = df[df['deficit'] >= 0]  # type: ignore
            if not itens_criticos.empty:  # type: ignore
                st.error(f"🚨 {len(itens_criticos)} itens precisam de reposição urgente!")  # type: ignore
            
            # Estatísticas
            col1, col2, col3 = st.columns(3)  # type: ignore
            
            with col1:
                st.metric("Itens em Alerta", len(df))  # type: ignore
            
            with col2:
                valor_reposicao = (df['deficit'] * df['valor_unitario']).fillna(0).sum()  # type: ignore
                st.metric("Valor para Reposição", f"R$ {valor_reposicao:,.2f}")  # type: ignore
            
            with col3:
                categorias_afetadas = df['categoria'].nunique()  # type: ignore
                st.metric("Categorias Afetadas", categorias_afetadas)  # type: ignore
            
            # Gráfico
            if len(df) > 0:  # type: ignore
                # Verificar se há dados válidos para o gráfico
                df_grafico = df.head(10)  # type: ignore
                if not df_grafico.empty and 'deficit' in df_grafico.columns and 'item' in df_grafico.columns:  # type: ignore
                    # Verificar se há valores válidos na coluna deficit
                    if df_grafico['deficit'].notna().any():  # type: ignore
                        fig = px.bar(  # type: ignore
                            df_grafico,  # type: ignore
                            x='deficit',  # type: ignore
                            y='item',  # type: ignore
                            orientation='h',  # type: ignore
                            title="Top 10 Itens com Maior Déficit",  # type: ignore
                            color='deficit',  # type: ignore
                            color_continuous_scale='Reds'  # type: ignore
                        )  # type: ignore
                        st.plotly_chart(fig, width='stretch')  # type: ignore
                    else:
                        st.info("📊 Não há dados de déficit válidos para exibir o gráfico.")  # type: ignore
                else:
                    st.info("📊 Dados insuficientes para gerar o gráfico.")  # type: ignore
            else:
                st.info("📊 Nenhum item com estoque baixo encontrado.")  # type: ignore
            
            # Tabela
            st.dataframe(  # type: ignore
                df,  # type: ignore
                column_config={  # type: ignore
                    'valor_unitario': st.column_config.NumberColumn('Valor Unit.', format="R$ %.2f")  # type: ignore
                },  # type: ignore
                width='stretch',  # type: ignore
                hide_index=True  # type: ignore
            )  # type: ignore
            
            # Download
            excel_data = manager.exportar_excel(df, 'estoque_baixo')  # type: ignore
            st.download_button(  # type: ignore
                label="📥 Download Excel",  # type: ignore
                data=excel_data,  # type: ignore
                file_name=f"estoque_baixo_{date.today().strftime('%Y%m%d')}.xlsx",  # type: ignore
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"  # type: ignore
            )  # type: ignore
        else:
            st.success("✅ Todos os itens estão com estoque adequado!")  # type: ignore
    
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
                valor_total = df_inventario['valor_total'].fillna(0).sum()  # type: ignore
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
                if not df_inventario.empty and 'categoria' in df_inventario.columns and 'valor_total' in df_inventario.columns:  # type: ignore
                    valor_categoria = df_inventario.groupby('categoria')['valor_total'].sum().sort_values(ascending=False).head(8)  # type: ignore
                    if len(valor_categoria) > 0 and valor_categoria.sum() > 0:  # type: ignore
                        fig = px.pie(  # type: ignore
                            values=valor_categoria.values,  # type: ignore
                            names=valor_categoria.index,  # type: ignore
                            title="Distribuição de Valor por Categoria"  # type: ignore
                        )  # type: ignore
                        st.plotly_chart(fig, width='stretch')  # type: ignore
                    else:
                        st.info("📊 Não há dados de valor por categoria para exibir.")  # type: ignore
                else:
                    st.info("📊 Dados insuficientes para gráfico de categorias.")  # type: ignore
            
            with col2:
                # Itens por tipo
                if not df_inventario.empty and 'tipo_item' in df_inventario.columns:  # type: ignore
                    tipo_counts = df_inventario['tipo_item'].value_counts()  # type: ignore
                    if len(tipo_counts) > 0:  # type: ignore
                        fig = px.bar(  # type: ignore
                            x=tipo_counts.index,  # type: ignore
                            y=tipo_counts.values,  # type: ignore
                            title="Quantidade de Itens por Tipo"  # type: ignore
                        )  # type: ignore
                        fig.update_layout(xaxis_title="Tipo", yaxis_title="Quantidade")  # type: ignore
                        st.plotly_chart(fig, width='stretch')  # type: ignore
                    else:
                        st.info("📊 Não há dados de tipos para exibir.")  # type: ignore
                else:
                    st.info("📊 Dados insuficientes para gráfico de tipos.")  # type: ignore
        
        else:
            st.info("📊 Carregue os dados do inventário para visualizar o dashboard executivo.")

# Instância global
relatorios_manager = RelatoriosManager()