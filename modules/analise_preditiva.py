import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from database.connection import db
import streamlit as st

class AnalisePreditivaManager:
    """Sistema de análise preditiva para otimização de estoque e compras"""
    
    def __init__(self):
        self.modelo_consumo = None
        self.modelo_demanda = None
    
    def carregar_dados_historicos(self, item_id: int, dias: int = 90) -> pd.DataFrame:
        """Carrega dados históricos de movimentação"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            data_limite = datetime.now() - timedelta(days=dias)
            
            cursor.execute("""
                SELECT 
                    DATE(data_movimentacao) as data,
                    SUM(quantidade) as quantidade_consumida,
                    COUNT(*) as num_movimentacoes
                FROM movimentacoes 
                WHERE insumo_id = %s 
                    AND tipo_movimentacao = 'saida'
                    AND data_movimentacao >= %s
                GROUP BY DATE(data_movimentacao)
                ORDER BY data
            """, (item_id, data_limite))
            
            dados = cursor.fetchall()
            
            if not dados:
                return pd.DataFrame()
                
            df = pd.DataFrame(dados)
            df['data'] = pd.to_datetime(df['data'])
            return df
            
        except Exception as e:
            st.error(f"Erro ao carregar dados históricos: {e}")
            return pd.DataFrame()
    
    def prever_consumo(self, item_id: int, dias_previsao: int = 30) -> Dict[str, Any]:
        """Prevê consumo futuro baseado em dados históricos"""
        try:
            df = self.carregar_dados_historicos(item_id)
            
            if df.empty or len(df) < 7:  # Mínimo 7 dias de dados
                return {
                    'previsao_media': 0,
                    'confianca': 'baixa',
                    'recomendacao': 'Dados insuficientes para previsão'
                }
            
            # Preparar dados para ML
            df['dias_desde_inicio'] = (df['data'] - df['data'].min()).dt.days
            X = df[['dias_desde_inicio']].values
            y = df['quantidade_consumida'].values
            
            # Treinar modelo simples de regressão linear
            modelo = LinearRegression()
            modelo.fit(X, y)
            
            # Fazer previsão para os próximos dias
            dias_futuros = np.array([[df['dias_desde_inicio'].max() + i + 1] for i in range(dias_previsao)])
            previsao = modelo.predict(dias_futuros)
            
            consumo_total_previsto = max(0, np.sum(previsao))
            consumo_medio_diario = consumo_total_previsto / dias_previsao
            
            # Calcular confiança baseada na variação dos dados
            variacao = np.std(y) / np.mean(y) if np.mean(y) > 0 else 1
            confianca = 'alta' if variacao < 0.3 else 'media' if variacao < 0.6 else 'baixa'
            
            return {
                'previsao_total': round(consumo_total_previsto, 2),
                'previsao_media_diaria': round(consumo_medio_diario, 2),
                'confianca': confianca,
                'variacao': round(variacao, 2),
                'dias_analisados': len(df)
            }
            
        except Exception as e:
            return {
                'erro': str(e),
                'previsao_total': 0,
                'confianca': 'erro'
            }
    
    def otimizar_compras(self, item_id: int) -> Dict[str, Any]:
        """Otimiza quantidade de compra baseada em previsão"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Buscar dados atuais do item
            cursor.execute("""
                SELECT quantidade_atual, quantidade_minima, preco_unitario, nome
                FROM insumos 
                WHERE id = %s AND ativo = TRUE
            """, (item_id,))
            
            item = cursor.fetchone()
            if not item:
                return {'erro': 'Item não encontrado'}
            
            estoque_atual = item['quantidade_atual']
            estoque_minimo = item['quantidade_minima']
            preco_unitario = item['preco_unitario']
            nome = item['nome']
            
            # Previsão de consumo para 30 dias
            previsao = self.prever_consumo(item_id, 30)
            consumo_previsto = previsao.get('previsao_total', 0)
            
            # Calcular necessidade de compra
            necessidade = max(0, consumo_previsto + estoque_minimo - estoque_atual)
            
            # Sugerir quantidade com margem de segurança baseada na confiança
            margem_seguranca = {
                'alta': 1.1,
                'media': 1.2,
                'baixa': 1.3
            }
            
            confianca = previsao.get('confianca', 'baixa')
            quantidade_sugerida = necessidade * margem_seguranca.get(confianca, 1.2)
            custo_estimado = quantidade_sugerida * preco_unitario
            
            return {
                'nome': nome,
                'estoque_atual': estoque_atual,
                'consumo_previsto_30d': round(consumo_previsto, 2),
                'necessidade_compra': round(necessidade, 2),
                'quantidade_sugerida': round(quantidade_sugerida, 2),
                'custo_estimado': round(custo_estimado, 2),
                'confianca': confianca,
                'prioridade': 'alta' if estoque_atual <= estoque_minimo else 'media'
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def detectar_anomalias(self, item_id: int) -> Dict[str, Any]:
        """Detecta padrões anômalos de consumo"""
        try:
            df = self.carregar_dados_historicos(item_id, 60)
            
            if df.empty or len(df) < 10:
                return {'anomalias': [], 'status': 'dados_insuficientes'}
            
            # Calcular média e desvio padrão
            media = df['quantidade_consumida'].mean()
            desvio = df['quantidade_consumida'].std()
            
            # Detectar outliers (valores > 2 desvios da média)
            limite_superior = media + 2 * desvio
            limite_inferior = max(0, media - 2 * desvio)
            
            anomalias = df[
                (df['quantidade_consumida'] > limite_superior) | 
                (df['quantidade_consumida'] < limite_inferior)
            ]
            
            return {
                'total_anomalias': len(anomalias),
                'anomalias': anomalias.to_dict('records') if not anomalias.empty else [],
                'consumo_medio': round(media, 2),
                'limite_superior': round(limite_superior, 2),
                'limite_inferior': round(limite_inferior, 2)
            }
            
        except Exception as e:
            return {'erro': str(e)}

def show_analise_preditiva_page():
    """Interface do sistema de análise preditiva"""
    st.title("🔮 Análise Preditiva")
    
    manager = AnalisePreditivaManager()
    
    # Seção de previsão de consumo
    st.header("📈 Previsão de Consumo")
    
    col1, col2 = st.columns(2)
    with col1:
        item_id = st.number_input("ID do Insumo", min_value=1, step=1)
    with col2:
        dias_previsao = st.number_input("Dias para Previsão", min_value=7, max_value=90, value=30)
    
    if st.button("🔍 Gerar Previsão"):
        previsao = manager.prever_consumo(item_id, dias_previsao)
        
        if 'erro' in previsao:
            st.error(f"Erro: {previsao['erro']}")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Consumo Total Previsto", f"{previsao['previsao_total']:.2f}")
            with col2:
                st.metric("Consumo Médio Diário", f"{previsao['previsao_media_diaria']:.2f}")
            with col3:
                confianca_color = {
                    'alta': '🟢',
                    'media': '🟡', 
                    'baixa': '🔴'
                }
                st.metric("Confiança", f"{confianca_color.get(previsao['confianca'], '⚪')} {previsao['confianca'].title()}")
    
    # Seção de otimização de compras
    st.header("🛒 Otimização de Compras")
    
    item_otimizar = st.number_input("ID do Insumo para Otimizar", min_value=1, step=1, key="otimizar")
    
    if st.button("💡 Calcular Recomendação"):
        otimizacao = manager.otimizar_compras(item_otimizar)
        
        if 'erro' in otimizacao:
            st.error(f"Erro: {otimizacao['erro']}")
        else:
            st.success(f"**Recomendação para: {otimizacao['nome']}**")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Estoque Atual", otimizacao['estoque_atual'])
            with col2:
                st.metric("Consumo Previsto (30d)", f"{otimizacao['consumo_previsto_30d']:.2f}")
            with col3:
                st.metric("Quantidade Sugerida", f"{otimizacao['quantidade_sugerida']:.2f}")
            with col4:
                st.metric("Custo Estimado", f"R$ {otimizacao['custo_estimado']:.2f}")
            
            # Indicador de prioridade
            if otimizacao['prioridade'] == 'alta':
                st.error("🚨 **PRIORIDADE ALTA** - Estoque abaixo do mínimo!")
            else:
                st.info("📊 Compra recomendada para manter estoque adequado")
    
    # Seção de detecção de anomalias
    st.header("⚠️ Detecção de Anomalias")
    
    item_anomalia = st.number_input("ID do Insumo para Análise", min_value=1, step=1, key="anomalia")
    
    if st.button("🔍 Detectar Anomalias"):
        anomalias = manager.detectar_anomalias(item_anomalia)
        
        if 'erro' in anomalias:
            st.error(f"Erro: {anomalias['erro']}")
        elif anomalias['status'] == 'dados_insuficientes':
            st.warning("⚠️ Dados insuficientes para análise de anomalias")
        else:
            if anomalias['total_anomalias'] > 0:
                st.warning(f"⚠️ {anomalias['total_anomalias']} anomalia(s) detectada(s)")
                
                if anomalias['anomalias']:
                    df_anomalias = pd.DataFrame(anomalias['anomalias'])
                    st.dataframe(df_anomalias)
            else:
                st.success("✅ Nenhuma anomalia detectada no padrão de consumo")
            
            # Mostrar estatísticas
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📊 Consumo médio: {anomalias['consumo_medio']:.2f}")
            with col2:
                st.info(f"📈 Limite superior: {anomalias['limite_superior']:.2f}")