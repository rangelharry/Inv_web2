import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database.connection import db

def get_count_result(cursor_result):
    """Helper para tratar resultados do PostgreSQL que podem ser dict ou tuple"""
    if cursor_result is None:
        return 0
    if isinstance(cursor_result, dict):
        # Se for dict, pegar o primeiro valor
        return list(cursor_result.values())[0] if cursor_result.values() else 0
    elif isinstance(cursor_result, (tuple, list)):
        # Se for tuple/list, pegar o primeiro elemento
        return cursor_result[0] if cursor_result else 0
    else:
        # Se for um valor direto
        return cursor_result

def get_dict_result(cursor_result, columns):
    """Helper para converter resultados do cursor em dict"""
    if isinstance(cursor_result, dict):
        return cursor_result
    elif isinstance(cursor_result, (tuple, list)):
        return dict(zip(columns, cursor_result))
    return {}

def show_dashboard_executivo():
    """Dashboard executivo com KPIs avançados"""
    st.title("📊 Dashboard Executivo")
    
    # Métricas de utilização de equipamentos
    st.header("⚡ Utilização de Equipamentos")
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # KPI: Taxa de utilização - Usando consulta mais simples
        cursor.execute("SELECT COUNT(*) FROM equipamentos_eletricos WHERE ativo = TRUE")
        total_equipamentos = get_count_result(cursor.fetchone())
        
        cursor.execute("SELECT COUNT(DISTINCT equipamento_id) FROM movimentacoes WHERE data_movimentacao >= CURRENT_DATE - INTERVAL '30 days'")
        equipamentos_utilizados = get_count_result(cursor.fetchone())
        
        taxa_util = (equipamentos_utilizados / total_equipamentos * 100) if total_equipamentos > 0 else 0
        
        # KPI: Equipamentos mais utilizados
        cursor.execute("""
            SELECT ee.nome, COUNT(m.id) as movimentacoes
            FROM equipamentos_eletricos ee
            LEFT JOIN movimentacoes m ON ee.id = m.equipamento_id AND m.data_movimentacao >= CURRENT_DATE - INTERVAL '30 days'
            WHERE ee.ativo = TRUE
            GROUP BY ee.id, ee.nome
            ORDER BY movimentacoes DESC
            LIMIT 5
        """)
        rows = cursor.fetchall()
        
        mais_utilizados = []
        for row in rows:
            if isinstance(row, dict):
                mais_utilizados.append(row)
            else:
                columns = [desc[0] for desc in cursor.description]
                mais_utilizados.append(dict(zip(columns, row)))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📈 Taxa de Utilização (30 dias)", f"{taxa_util:.1f}%")
        with col2:
            st.metric("🔧 Equipamentos Ativos", total_equipamentos)
        with col3:
            avg_mov = sum(eq.get('movimentacoes', 0) for eq in mais_utilizados) / len(mais_utilizados) if mais_utilizados else 0
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
        
        # Verificar se tabela obras existe
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'obras'
        """)
        
        if cursor.fetchone():
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
            rows = cursor.fetchall()
            
            custos_obra = []
            for row in rows:
                if isinstance(row, dict):
                    custos_obra.append(row)
                else:
                    columns = [desc[0] for desc in cursor.description]
                    custos_obra.append(dict(zip(columns, row)))
            
            if custos_obra:
                df_custos = pd.DataFrame(custos_obra)
                fig_custos = px.pie(df_custos, values='custo_equipamentos', names='nome',
                                   title="Distribuição de Custos por Obra")
                st.plotly_chart(fig_custos, use_container_width=True)
            else:
                st.info("📊 Nenhuma obra encontrada para análise de custos")
        else:
            # Mostrar análise simples de equipamentos
            cursor.execute("""
                SELECT COUNT(*) as total_equipamentos,
                       SUM(COALESCE(valor_compra, 0)) as valor_total
                FROM equipamentos_eletricos 
                WHERE ativo = TRUE
            """)
            result = cursor.fetchone()
            total_eq = get_count_result(cursor.execute("SELECT COUNT(*) FROM equipamentos_eletricos WHERE ativo = TRUE") or cursor.fetchone())
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🔧 Total de Equipamentos", total_eq)
            with col2:
                st.metric("💰 Valor Total Estimado", "R$ 0,00")
                
            st.info("📋 Sistema configurado para análise básica de equipamentos")
        
    except Exception as e:
        st.error(f"Erro ao carregar análise de custos: {e}")
        st.info("📊 Dados de custos não disponíveis")

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
        rows = cursor.fetchall()
        
        insumos_status = []
        for row in rows:
            if isinstance(row, dict):
                insumos_status.append(row)
            else:
                columns = [desc[0] for desc in cursor.description]
                insumos_status.append(dict(zip(columns, row)))
        
        if insumos_status:
            df_insumos = pd.DataFrame(insumos_status)
            fig_insumos = px.bar(df_insumos, x='nome', y='quantidade_atual',
                               color='status_estoque',
                               title="Status de Estoque - Top 10 Menores Quantidades")
            fig_insumos.update_xaxis(tickangle=45)
            st.plotly_chart(fig_insumos, use_container_width=True)
            
            # Métricas adicionais
            criticos = len([i for i in insumos_status if i.get('status_estoque') == 'Crítico'])
            baixos = len([i for i in insumos_status if i.get('status_estoque') == 'Baixo'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🚨 Estoque Crítico", criticos)
            with col2:
                st.metric("⚠️ Estoque Baixo", baixos)
            with col3:
                st.metric("📦 Total Analisado", len(insumos_status))
        else:
            st.info("📊 Nenhum dado de insumos disponível para análise")
        
    except Exception as e:
        st.error(f"Erro ao carregar tendências: {e}")
        st.info("📈 Dados de tendências não disponíveis")

# Função principal do dashboard executivo
def show_dashboard_executivo_page():
    """Página principal do dashboard executivo"""
    show_dashboard_executivo()
    show_analise_custos()
    show_tendencias_insumos()