import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database.connection import db

def show_dashboard_executivo():
    """Dashboard executivo com KPIs avançados"""
    st.title("📊 Dashboard Executivo")
    
    # Métricas de utilização de equipamentos
    st.header("⚡ Utilização de Equipamentos")
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # KPI: Taxa de utilização
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT m.equipamento_id) * 100.0 / 
                (SELECT COUNT(*) FROM equipamentos_eletricos WHERE ativo = TRUE) as taxa_utilizacao
            FROM movimentacoes m 
            WHERE m.data_movimentacao >= CURRENT_DATE - INTERVAL '30 days'
        """)
        taxa_util = cursor.fetchone()['taxa_utilizacao'] or 0
        
        # KPI: Equipamentos mais utilizados
        cursor.execute("""
            SELECT ee.nome, COUNT(m.id) as movimentacoes
            FROM equipamentos_eletricos ee
            LEFT JOIN movimentacoes m ON ee.id = m.equipamento_id
            WHERE ee.ativo = TRUE AND m.data_movimentacao >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY ee.id, ee.nome
            ORDER BY movimentacoes DESC
            LIMIT 5
        """)
        mais_utilizados = cursor.fetchall()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📈 Taxa de Utilização (30 dias)", f"{taxa_util:.1f}%")
        with col2:
            total_eq = len(mais_utilizados)
            st.metric("🔧 Equipamentos Ativos", total_eq)
        with col3:
            avg_mov = sum(eq['movimentacoes'] for eq in mais_utilizados) / len(mais_utilizados) if mais_utilizados else 0
            st.metric("📊 Média Movimentações", f"{avg_mov:.1f}")
        
        # Gráfico de equipamentos mais utilizados
        if mais_utilizados:
            df_util = pd.DataFrame(mais_utilizados)
            fig_util = px.bar(df_util, x='movimentacoes', y='nome', orientation='h',
                             title="Top 5 Equipamentos Mais Utilizados")
            st.plotly_chart(fig_util, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao carregar métricas: {e}")

def show_analise_custos():
    """Análise de custos por obra/projeto"""
    st.header("💰 Análise de Custos")
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Custo por obra
        cursor.execute("""
            SELECT o.nome, 
                   SUM(COALESCE(ee.valor_compra, 0)) as custo_equipamentos,
                   COUNT(DISTINCT m.equipamento_id) as qtd_equipamentos
            FROM obras o
            LEFT JOIN movimentacoes m ON o.id = m.obra_id
            LEFT JOIN equipamentos_eletricos ee ON m.equipamento_id = ee.id
            WHERE o.status = 'ativo'
            GROUP BY o.id, o.nome
            ORDER BY custo_equipamentos DESC
        """)
        custos_obra = cursor.fetchall()
        
        if custos_obra:
            df_custos = pd.DataFrame(custos_obra)
            fig_custos = px.pie(df_custos, values='custo_equipamentos', names='nome',
                               title="Distribuição de Custos por Obra")
            st.plotly_chart(fig_custos, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao carregar análise de custos: {e}")

def show_tendencias_insumos():
    """Tendências de consumo de insumos"""
    st.header("📈 Tendências de Consumo")
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Insumos com maior rotatividade
        cursor.execute("""
            SELECT i.nome, i.quantidade_atual, i.quantidade_minima,
                   CASE WHEN i.quantidade_atual <= i.quantidade_minima THEN 'Crítico'
                        WHEN i.quantidade_atual <= i.quantidade_minima * 2 THEN 'Baixo'
                        ELSE 'Normal' END as status_estoque
            FROM insumos i
            WHERE i.ativo = TRUE
            ORDER BY i.quantidade_atual ASC
            LIMIT 10
        """)
        insumos_status = cursor.fetchall()
        
        if insumos_status:
            df_insumos = pd.DataFrame(insumos_status)
            fig_insumos = px.bar(df_insumos, x='nome', y='quantidade_atual',
                               color='status_estoque',
                               title="Status de Estoque - Top 10 Menores Quantidades")
            fig_insumos.update_xaxis(tickangle=45)
            st.plotly_chart(fig_insumos, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao carregar tendências: {e}")

# Função principal do dashboard executivo
def show_dashboard_executivo_page():
    """Página principal do dashboard executivo"""
    show_dashboard_executivo()
    show_analise_custos()
    show_tendencias_insumos()