import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from database.connection import db

class MetricsPerformanceManager:
    """Sistema de métricas de performance e KPIs operacionais"""
    
    def calcular_tempo_utilizacao(self, equipamento_id: int, dias: int = 30) -> Dict[str, Any]:
        """Calcula tempo de utilização de equipamento"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            data_inicio = datetime.now() - timedelta(days=dias)
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_movimentacoes,
                    COUNT(DISTINCT DATE(data_movimentacao)) as dias_utilizados,
                    MIN(data_movimentacao) as primeira_utilizacao,
                    MAX(data_movimentacao) as ultima_utilizacao
                FROM movimentacoes 
                WHERE equipamento_id = %s 
                    AND data_movimentacao >= %s
            """, (equipamento_id, data_inicio))
            
            resultado = cursor.fetchone()
            
            if not resultado or resultado['total_movimentacoes'] == 0:
                return {
                    'tempo_utilizacao_dias': 0,
                    'taxa_utilizacao': 0,
                    'movimentacoes_por_dia': 0,
                    'status': 'sem_uso'
                }
            
            dias_utilizados = resultado['dias_utilizados']
            total_movimentacoes = resultado['total_movimentacoes']
            
            # Taxa de utilização (dias usados / dias totais do período)
            taxa_utilizacao = (dias_utilizados / dias) * 100
            
            # Movimentações por dia
            movimentacoes_por_dia = total_movimentacoes / max(dias_utilizados, 1)
            
            # Classificação de performance
            if taxa_utilizacao >= 70:
                status = 'alto_uso'
            elif taxa_utilizacao >= 30:
                status = 'uso_moderado'
            else:
                status = 'baixo_uso'
            
            return {
                'tempo_utilizacao_dias': dias_utilizados,
                'taxa_utilizacao': round(taxa_utilizacao, 2),
                'movimentacoes_por_dia': round(movimentacoes_por_dia, 2),
                'total_movimentacoes': total_movimentacoes,
                'status': status,
                'primeira_utilizacao': resultado['primeira_utilizacao'],
                'ultima_utilizacao': resultado['ultima_utilizacao']
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def calcular_eficiencia_obra(self, obra_id: int) -> Dict[str, Any]:
        """Calcula eficiência operacional por obra"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Equipamentos alocados na obra
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT m.equipamento_id) as equipamentos_utilizados,
                    COUNT(*) as total_movimentacoes,
                    AVG(EXTRACT(EPOCH FROM (m.data_movimentacao - m.data_movimentacao))) as tempo_medio_operacao
                FROM movimentacoes m
                WHERE m.obra_id = %s
                    AND m.data_movimentacao >= CURRENT_DATE - INTERVAL '30 days'
            """, (obra_id,))
            
            movimentacoes = cursor.fetchone()
            
            # Custos de equipamentos na obra
            cursor.execute("""
                SELECT 
                    SUM(COALESCE(ee.valor_compra, 0)) as valor_total_equipamentos,
                    AVG(COALESCE(ee.valor_compra, 0)) as valor_medio_equipamento
                FROM movimentacoes m
                JOIN equipamentos_eletricos ee ON m.equipamento_id = ee.id
                WHERE m.obra_id = %s
                    AND m.data_movimentacao >= CURRENT_DATE - INTERVAL '30 days'
            """, (obra_id,))
            
            custos = cursor.fetchone()
            
            equipamentos_utilizados = movimentacoes['equipamentos_utilizados'] or 0
            total_movimentacoes = movimentacoes['total_movimentacoes'] or 0
            valor_total = custos['valor_total_equipamentos'] or 0
            
            # Cálculo de eficiência
            if equipamentos_utilizados > 0:
                movimentacoes_por_equipamento = total_movimentacoes / equipamentos_utilizados
                custo_por_movimentacao = valor_total / max(total_movimentacoes, 1)
            else:
                movimentacoes_por_equipamento = 0
                custo_por_movimentacao = 0
            
            # Classificação de eficiência
            if movimentacoes_por_equipamento >= 10:
                classificacao = 'alta_eficiencia'
            elif movimentacoes_por_equipamento >= 5:
                classificacao = 'eficiencia_moderada'
            else:
                classificacao = 'baixa_eficiencia'
            
            return {
                'equipamentos_utilizados': equipamentos_utilizados,
                'total_movimentacoes': total_movimentacoes,
                'movimentacoes_por_equipamento': round(movimentacoes_por_equipamento, 2),
                'valor_total_equipamentos': valor_total,
                'custo_por_movimentacao': round(custo_por_movimentacao, 2),
                'classificacao': classificacao
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def calcular_roi_equipamento(self, equipamento_id: int) -> Dict[str, Any]:
        """Calcula ROI de equipamento"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Dados básicos do equipamento
            cursor.execute("""
                SELECT 
                    nome,
                    valor_compra,
                    data_aquisicao,
                    vida_util_anos
                FROM equipamentos_eletricos 
                WHERE id = %s AND ativo = TRUE
            """, (equipamento_id,))
            
            equipamento = cursor.fetchone()
            
            if not equipamento:
                return {'erro': 'Equipamento não encontrado'}
            
            valor_compra = equipamento['valor_compra'] or 0
            data_aquisicao = equipamento['data_aquisicao']
            vida_util_anos = equipamento['vida_util_anos'] or 5
            
            if valor_compra == 0:
                return {'erro': 'Valor de compra não informado'}
            
            # Calcular idade do equipamento
            if isinstance(data_aquisicao, str):
                data_aquisicao = datetime.strptime(data_aquisicao, '%Y-%m-%d').date()
            
            idade_dias = (datetime.now().date() - data_aquisicao).days
            idade_anos = idade_dias / 365.25
            
            # Frequência de uso
            cursor.execute("""
                SELECT COUNT(*) as total_usos
                FROM movimentacoes 
                WHERE equipamento_id = %s
            """, (equipamento_id,))
            
            uso = cursor.fetchone()
            total_usos = uso['total_usos'] or 0
            
            # Cálculos de ROI
            depreciacao_atual = min((idade_anos / vida_util_anos) * valor_compra, valor_compra)
            valor_residual = valor_compra - depreciacao_atual
            
            # ROI baseado em uso
            if idade_anos > 0:
                usos_por_ano = total_usos / idade_anos
                custo_por_uso = valor_compra / max(total_usos, 1)
            else:
                usos_por_ano = 0
                custo_por_uso = valor_compra
            
            # Classificação de ROI
            if usos_por_ano >= 50:  # Mais de 50 usos por ano
                classificacao_roi = 'excelente'
            elif usos_por_ano >= 20:
                classificacao_roi = 'bom'
            elif usos_por_ano >= 10:
                classificacao_roi = 'regular'
            else:
                classificacao_roi = 'ruim'
            
            return {
                'nome': equipamento['nome'],
                'valor_compra': valor_compra,
                'idade_anos': round(idade_anos, 2),
                'total_usos': total_usos,
                'usos_por_ano': round(usos_por_ano, 2),
                'custo_por_uso': round(custo_por_uso, 2),
                'depreciacao_atual': round(depreciacao_atual, 2),
                'valor_residual': round(valor_residual, 2),
                'percentual_depreciacao': round((depreciacao_atual / valor_compra) * 100, 2),
                'classificacao_roi': classificacao_roi
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def dashboard_performance_geral(self) -> Dict[str, Any]:
        """Dashboard geral de performance"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # KPIs gerais
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT ee.id) as total_equipamentos,
                    COUNT(DISTINCT m.equipamento_id) as equipamentos_em_uso,
                    COUNT(*) as total_movimentacoes_30d,
                    AVG(ee.valor_compra) as valor_medio_equipamento
                FROM equipamentos_eletricos ee
                LEFT JOIN movimentacoes m ON ee.id = m.equipamento_id 
                    AND m.data_movimentacao >= CURRENT_DATE - INTERVAL '30 days'
                WHERE ee.ativo = TRUE
            """)
            
            kpis = cursor.fetchone()
            
            total_equipamentos = kpis['total_equipamentos'] or 0
            equipamentos_em_uso = kpis['equipamentos_em_uso'] or 0
            
            # Taxa de utilização geral
            if total_equipamentos > 0:
                taxa_utilizacao_geral = (equipamentos_em_uso / total_equipamentos) * 100
            else:
                taxa_utilizacao_geral = 0
            
            # Equipamentos mais utilizados
            cursor.execute("""
                SELECT 
                    ee.nome,
                    COUNT(m.id) as movimentacoes
                FROM equipamentos_eletricos ee
                LEFT JOIN movimentacoes m ON ee.id = m.equipamento_id
                    AND m.data_movimentacao >= CURRENT_DATE - INTERVAL '30 days'
                WHERE ee.ativo = TRUE
                GROUP BY ee.id, ee.nome
                ORDER BY movimentacoes DESC
                LIMIT 5
            """)
            
            top_equipamentos = cursor.fetchall()
            
            return {
                'total_equipamentos': total_equipamentos,
                'equipamentos_em_uso': equipamentos_em_uso,
                'taxa_utilizacao_geral': round(taxa_utilizacao_geral, 2),
                'total_movimentacoes_30d': kpis['total_movimentacoes_30d'] or 0,
                'valor_medio_equipamento': round(kpis['valor_medio_equipamento'] or 0, 2),
                'top_equipamentos': list(top_equipamentos)
            }
            
        except Exception as e:
            return {'erro': str(e)}

def show_metricas_performance_page():
    """Interface do sistema de métricas de performance"""
    st.title("⚡ Métricas de Performance")
    
    manager = MetricsPerformanceManager()
    
    # Dashboard geral
    st.header("📊 Dashboard Geral de Performance")
    
    dashboard = manager.dashboard_performance_geral()
    
    if 'erro' in dashboard:
        st.error(f"Erro ao carregar dashboard: {dashboard['erro']}")
    else:
        # KPIs principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Equipamentos", dashboard['total_equipamentos'])
        
        with col2:
            st.metric("Em Uso (30 dias)", dashboard['equipamentos_em_uso'])
        
        with col3:
            st.metric("Taxa de Utilização", f"{dashboard['taxa_utilizacao_geral']:.1f}%")
        
        with col4:
            st.metric("Movimentações (30d)", dashboard['total_movimentacoes_30d'])
        
        # Gráfico de equipamentos mais utilizados
        if dashboard['top_equipamentos']:
            df_top = pd.DataFrame(dashboard['top_equipamentos'])
            fig = px.bar(
                df_top,
                x='movimentacoes',
                y='nome',
                orientation='h',
                title="Top 5 Equipamentos Mais Utilizados (30 dias)"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Seção de análise individual por equipamento
    st.header("🔍 Análise Individual de Equipamento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        equipamento_id = st.number_input("ID do Equipamento", min_value=1, step=1)
    
    with col2:
        dias_analise = st.number_input("Período de Análise (dias)", min_value=1, max_value=365, value=30)
    
    if st.button("📈 Analisar Performance"):
        # Tempo de utilização
        utilizacao = manager.calcular_tempo_utilizacao(equipamento_id, dias_analise)
        
        if 'erro' in utilizacao:
            st.error(f"Erro: {utilizacao['erro']}")
        else:
            st.subheader("⏱️ Métricas de Utilização")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Taxa de Utilização", f"{utilizacao['taxa_utilizacao']:.1f}%")
            
            with col2:
                st.metric("Dias Utilizados", utilizacao['tempo_utilizacao_dias'])
            
            with col3:
                st.metric("Movimentações/Dia", f"{utilizacao['movimentacoes_por_dia']:.1f}")
            
            # Status de uso
            status_colors = {
                'alto_uso': '🟢',
                'uso_moderado': '🟡',
                'baixo_uso': '🔴',
                'sem_uso': '⚫'
            }
            
            status_labels = {
                'alto_uso': 'Alto Uso',
                'uso_moderado': 'Uso Moderado',
                'baixo_uso': 'Baixo Uso',
                'sem_uso': 'Sem Uso'
            }
            
            st.info(f"Status: {status_colors.get(utilizacao['status'], '⚪')} {status_labels.get(utilizacao['status'], 'Desconhecido')}")
        
        # ROI do equipamento
        roi = manager.calcular_roi_equipamento(equipamento_id)
        
        if 'erro' in roi:
            st.warning(f"ROI: {roi['erro']}")
        else:
            st.subheader("💰 Análise de ROI")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Valor de Compra", f"R$ {roi['valor_compra']:,.2f}")
            
            with col2:
                st.metric("Custo por Uso", f"R$ {roi['custo_por_uso']:,.2f}")
            
            with col3:
                st.metric("Usos por Ano", f"{roi['usos_por_ano']:.1f}")
            
            with col4:
                st.metric("Valor Residual", f"R$ {roi['valor_residual']:,.2f}")
            
            # Indicador de ROI
            roi_colors = {
                'excelente': '🟢',
                'bom': '🟡',
                'regular': '🟠',
                'ruim': '🔴'
            }
            
            st.info(f"**{roi['nome']}** - ROI: {roi_colors.get(roi['classificacao_roi'], '⚪')} {roi['classificacao_roi'].title()}")
            
            # Gráfico de depreciação
            fig_depreciacao = go.Figure()
            
            fig_depreciacao.add_trace(go.Indicator(
                mode="gauge+number",
                value=roi['percentual_depreciacao'],
                title={'text': "Depreciação (%)"},
                gauge={'axis': {'range': [None, 100]},
                       'bar': {'color': "darkred"},
                       'steps': [{'range': [0, 50], 'color': "lightgray"},
                                 {'range': [50, 80], 'color': "gray"}],
                       'threshold': {'line': {'color': "red", 'width': 4},
                                     'thickness': 0.75, 'value': 90}}
            ))
            
            st.plotly_chart(fig_depreciacao, use_container_width=True)
    
    # Análise por obra
    st.header("🏗️ Eficiência por Obra")
    
    obra_id = st.number_input("ID da Obra", min_value=1, step=1, key="obra")
    
    if st.button("📊 Analisar Eficiência da Obra"):
        eficiencia = manager.calcular_eficiencia_obra(obra_id)
        
        if 'erro' in eficiencia:
            st.error(f"Erro: {eficiencia['erro']}")
        else:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Equipamentos Utilizados", eficiencia['equipamentos_utilizados'])
            
            with col2:
                st.metric("Movimentações/Equipamento", f"{eficiencia['movimentacoes_por_equipamento']:.1f}")
            
            with col3:
                st.metric("Custo por Movimentação", f"R$ {eficiencia['custo_por_movimentacao']:,.2f}")
            
            # Classificação de eficiência
            eficiencia_colors = {
                'alta_eficiencia': '🟢',
                'eficiencia_moderada': '🟡',
                'baixa_eficiencia': '🔴'
            }
            
            eficiencia_labels = {
                'alta_eficiencia': 'Alta Eficiência',
                'eficiencia_moderada': 'Eficiência Moderada',
                'baixa_eficiencia': 'Baixa Eficiência'
            }
            
            classificacao = eficiencia['classificacao']
            st.info(f"Classificação: {eficiencia_colors.get(classificacao, '⚪')} {eficiencia_labels.get(classificacao, 'Desconhecida')}")