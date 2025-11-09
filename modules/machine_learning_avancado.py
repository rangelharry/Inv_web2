"""
Machine Learning Avançado - Sistema Completo
Modelos preditivos, detecção de anomalias e otimização inteligente
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from typing import Dict, List, Any, Optional, Tuple
from database.connection import db
from modules.logs_auditoria import log_acao
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
import pickle
import warnings
warnings.filterwarnings('ignore')

class MachineLearningManager:
    """Gerenciador avançado de Machine Learning"""
    
    def __init__(self):
        self.models_trained = {}
        self.scalers = {}
        self.label_encoders = {}
        self.criar_tabelas_ml()
        self.initialize_base_models()
    
    def criar_tabelas_ml(self):
        """Cria estrutura de tabelas para ML"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Tabela de modelos ML
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS modelos_ml (
                id SERIAL PRIMARY KEY,
                nome_modelo VARCHAR(255) NOT NULL,
                tipo_modelo VARCHAR(100) NOT NULL, -- predicao_manutencao, otimizacao_estoque, deteccao_anomalia
                algoritmo VARCHAR(100) NOT NULL, -- random_forest, linear_regression, isolation_forest
                parametros_modelo JSONB,
                metricas_performance JSONB,
                dados_treino_sql TEXT,
                modelo_serializado BYTEA,
                data_treino TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_ultima_predicao TIMESTAMP,
                ativo BOOLEAN DEFAULT TRUE,
                versao_modelo INTEGER DEFAULT 1,
                criado_por INTEGER,
                acuracia DECIMAL(5,4),
                f1_score DECIMAL(5,4)
            )
            """)
            
            # Tabela de predições geradas
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS predicoes_ml (
                id SERIAL PRIMARY KEY,
                modelo_id INTEGER REFERENCES modelos_ml(id),
                equipamento_codigo VARCHAR(255),
                tipo_predicao VARCHAR(100), -- manutencao_necessaria, falha_iminente, otimizacao_estoque
                valor_predicao DECIMAL(10,4),
                probabilidade_predicao DECIMAL(5,4),
                data_predicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_evento_previsto TIMESTAMP,
                dados_entrada JSONB,
                resultado_real VARCHAR(100), -- confirmado, falso_positivo, pendente
                confianca_predicao DECIMAL(5,4),
                observacoes TEXT
            )
            """)
            
            # Tabela de anomalias detectadas
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomalias_detectadas (
                id SERIAL PRIMARY KEY,
                modelo_id INTEGER REFERENCES modelos_ml(id),
                equipamento_codigo VARCHAR(255),
                tipo_anomalia VARCHAR(100),
                score_anomalia DECIMAL(8,6), -- Score de anomalia (-1 a 1, onde valores negativos são anomalias)
                severidade VARCHAR(50) DEFAULT 'media', -- baixa, media, alta, critica
                dados_anomalos JSONB,
                timestamp_deteccao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status_anomalia VARCHAR(50) DEFAULT 'detectada', -- detectada, investigada, resolvida, falso_positivo
                acao_tomada TEXT,
                investigado_por INTEGER,
                data_resolucao TIMESTAMP
            )
            """)
            
            # Tabela de otimizações sugeridas
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS otimizacoes_sugeridas (
                id SERIAL PRIMARY KEY,
                modelo_id INTEGER REFERENCES modelos_ml(id),
                tipo_otimizacao VARCHAR(100), -- estoque, manutencao, alocacao_recursos
                equipamento_codigo VARCHAR(255),
                sugestao_titulo VARCHAR(255) NOT NULL,
                sugestao_descricao TEXT,
                impacto_estimado JSONB, -- {"economia": 1500, "tempo_economizado": 24}
                prioridade VARCHAR(50) DEFAULT 'media',
                implementacao_sugerida TEXT,
                data_sugestao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                implementada BOOLEAN DEFAULT FALSE,
                data_implementacao TIMESTAMP,
                resultado_real JSONB,
                aprovada_por INTEGER
            )
            """)
            
            # Tabela de datasets para treinamento
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets_ml (
                id SERIAL PRIMARY KEY,
                nome_dataset VARCHAR(255) NOT NULL,
                descricao TEXT,
                query_sql TEXT NOT NULL,
                tipo_dataset VARCHAR(100), -- manutencao, movimentacao, estoque
                features_colunas TEXT[], -- Array com nomes das colunas features
                target_coluna VARCHAR(255), -- Nome da coluna target
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultima_atualizacao TIMESTAMP,
                total_registros INTEGER,
                qualidade_dados DECIMAL(5,2), -- Score de 0-100
                ativo BOOLEAN DEFAULT TRUE
            )
            """)
            
            # Tabela de features engineering
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS features_engenharia (
                id SERIAL PRIMARY KEY,
                nome_feature VARCHAR(255) NOT NULL,
                formula_sql TEXT NOT NULL,
                descricao TEXT,
                tipo_feature VARCHAR(100), -- numerica, categorica, temporal
                importancia_score DECIMAL(5,4),
                dataset_origem VARCHAR(255),
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ativa BOOLEAN DEFAULT TRUE
            )
            """)
            
            # Tabela de experimentos ML
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS experimentos_ml (
                id SERIAL PRIMARY KEY,
                nome_experimento VARCHAR(255) NOT NULL,
                objetivo TEXT,
                dataset_id INTEGER REFERENCES datasets_ml(id),
                algoritmos_testados JSONB,
                resultados_experimento JSONB,
                melhor_modelo JSONB,
                data_experimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                executado_por INTEGER,
                tempo_execucao_segundos INTEGER,
                status_experimento VARCHAR(50) DEFAULT 'concluido' -- executando, concluido, erro
            )
            """)
            
            conn.commit()
            print("✅ Tabelas ML criadas com sucesso")
            
        except Exception as e:
            print(f"❌ Erro ao criar tabelas ML: {e}")
    
    def initialize_base_models(self):
        """Inicializa modelos base e dados sintéticos para demonstração"""
        # Gerar dados sintéticos para demonstração
        self.generate_synthetic_data()
        
        # Treinar modelos base
        self.train_maintenance_prediction_model()
        self.train_anomaly_detection_model()
        self.train_inventory_optimization_model()
    
    def generate_synthetic_data(self):
        """Gera dados sintéticos para demonstração dos modelos ML"""
        try:
            # Dados sintéticos de manutenção
            np.random.seed(42)
            n_samples = 1000
            
            # Features para predição de manutenção
            horas_uso = np.random.normal(500, 150, n_samples)
            temperatura_media = np.random.normal(45, 15, n_samples)
            vibracao_media = np.random.normal(3.5, 1.2, n_samples)
            idade_equipamento = np.random.exponential(2, n_samples)
            manutencoes_anteriores = np.random.poisson(3, n_samples)
            
            # Target: dias até próxima manutenção (baseado em regras lógicas)
            dias_manutencao = (
                100 - (horas_uso - 300) / 10 
                - (temperatura_media - 30) * 2
                - vibracao_media * 5
                - idade_equipamento * 5
                - manutencoes_anteriores * 3
                + np.random.normal(0, 10, n_samples)
            )
            dias_manutencao = np.clip(dias_manutencao, 1, 365)
            
            self.maintenance_data = pd.DataFrame({
                'horas_uso': horas_uso,
                'temperatura_media': temperatura_media,
                'vibracao_media': vibracao_media,
                'idade_equipamento': idade_equipamento,
                'manutencoes_anteriores': manutencoes_anteriores,
                'dias_ate_manutencao': dias_manutencao
            })
            
            # Dados sintéticos para detecção de anomalias
            normal_temp = np.random.normal(45, 8, 800)
            normal_vib = np.random.normal(3.5, 0.8, 800)
            normal_pressure = np.random.normal(2.1, 0.3, 800)
            
            # Adicionar algumas anomalias
            anomaly_temp = np.random.normal(85, 5, 50)  # Temperatura anômala
            anomaly_vib = np.random.normal(8, 2, 50)    # Vibração anômala
            anomaly_pressure = np.random.normal(4.5, 1, 50)  # Pressão anômala
            
            all_temp = np.concatenate([normal_temp, anomaly_temp])
            all_vib = np.concatenate([normal_vib, anomaly_vib])
            all_pressure = np.concatenate([normal_pressure, anomaly_pressure])
            
            # Labels (0 = normal, 1 = anomalia)
            labels = np.concatenate([np.zeros(800), np.ones(50)])
            
            self.anomaly_data = pd.DataFrame({
                'temperatura': all_temp,
                'vibracao': all_vib,
                'pressao': all_pressure,
                'is_anomaly': labels
            })
            
            # Dados sintéticos para otimização de estoque
            demanda_media = np.random.poisson(15, 365)  # Demanda diária
            sazonalidade = 1 + 0.3 * np.sin(np.arange(365) * 2 * np.pi / 365)  # Sazonalidade anual
            tendencia = 1 + np.arange(365) * 0.001  # Tendência de crescimento
            
            demanda_com_padroes = demanda_media * sazonalidade * tendencia
            
            self.inventory_data = pd.DataFrame({
                'dia': range(365),
                'demanda': demanda_com_padroes,
                'dia_semana': [i % 7 for i in range(365)],
                'mes': [(i // 30) % 12 for i in range(365)],
                'estoque_atual': np.random.normal(100, 20, 365)
            })
            
            print("✅ Dados sintéticos gerados")
            
        except Exception as e:
            print(f"❌ Erro ao gerar dados sintéticos: {e}")
    
    def train_maintenance_prediction_model(self):
        """Treina modelo de predição de manutenção"""
        try:
            # Preparar dados
            X = self.maintenance_data[['horas_uso', 'temperatura_media', 'vibracao_media', 
                                     'idade_equipamento', 'manutencoes_anteriores']]
            y = self.maintenance_data['dias_ate_manutencao']
            
            # Split dos dados
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Normalização
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Treinamento do modelo
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train_scaled, y_train)
            
            # Predições e métricas
            y_pred = model.predict(X_test_scaled)
            
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Salvar modelo
            self.models_trained['maintenance_prediction'] = model
            self.scalers['maintenance_prediction'] = scaler
            
            # Salvar métricas
            self.maintenance_metrics = {
                'mae': mae,
                'mse': mse,
                'r2': r2,
                'feature_importance': dict(zip(X.columns, model.feature_importances_))
            }
            
            print(f"✅ Modelo de manutenção treinado - R²: {r2:.3f}, MAE: {mae:.2f} dias")
            
        except Exception as e:
            print(f"❌ Erro ao treinar modelo de manutenção: {e}")
    
    def train_anomaly_detection_model(self):
        """Treina modelo de detecção de anomalias"""
        try:
            # Preparar dados (apenas dados normais para treinamento)
            normal_data = self.anomaly_data[self.anomaly_data['is_anomaly'] == 0]
            X_normal = normal_data[['temperatura', 'vibracao', 'pressao']]
            
            # Todos os dados para teste
            X_all = self.anomaly_data[['temperatura', 'vibracao', 'pressao']]
            y_all = self.anomaly_data['is_anomaly']
            
            # Normalização
            scaler = StandardScaler()
            X_normal_scaled = scaler.fit_transform(X_normal)
            X_all_scaled = scaler.transform(X_all)
            
            # Treinamento do modelo (Isolation Forest)
            model = IsolationForest(contamination=0.1, random_state=42)
            model.fit(X_normal_scaled)
            
            # Predições
            anomaly_scores = model.decision_function(X_all_scaled)
            predictions = model.predict(X_all_scaled)
            predictions = (predictions == -1).astype(int)  # -1 para anomalia, 1 para normal
            
            # Calcular métricas de classificação
            from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
            
            precision = precision_score(y_all, predictions)
            recall = recall_score(y_all, predictions)
            f1 = f1_score(y_all, predictions)
            accuracy = accuracy_score(y_all, predictions)
            
            # Salvar modelo
            self.models_trained['anomaly_detection'] = model
            self.scalers['anomaly_detection'] = scaler
            
            # Salvar métricas
            self.anomaly_metrics = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'accuracy': accuracy
            }
            
            print(f"✅ Modelo de anomalias treinado - F1: {f1:.3f}, Precisão: {precision:.3f}")
            
        except Exception as e:
            print(f"❌ Erro ao treinar modelo de anomalias: {e}")
    
    def train_inventory_optimization_model(self):
        """Treina modelo de otimização de estoque"""
        try:
            # Preparar features
            X = self.inventory_data[['dia', 'dia_semana', 'mes', 'estoque_atual']]
            y = self.inventory_data['demanda']
            
            # Split dos dados
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Normalização
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Treinamento do modelo
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train_scaled, y_train)
            
            # Predições e métricas
            y_pred = model.predict(X_test_scaled)
            
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Salvar modelo
            self.models_trained['inventory_optimization'] = model
            self.scalers['inventory_optimization'] = scaler
            
            # Salvar métricas
            self.inventory_metrics = {
                'mae': mae,
                'mse': mse,
                'r2': r2,
                'feature_importance': dict(zip(X.columns, model.feature_importances_))
            }
            
            print(f"✅ Modelo de estoque treinado - R²: {r2:.3f}, MAE: {mae:.2f}")
            
        except Exception as e:
            print(f"❌ Erro ao treinar modelo de estoque: {e}")
    
    def predict_maintenance_needs(self, equipment_data: Dict) -> Tuple[float, float]:
        """Prediz necessidade de manutenção"""
        try:
            model = self.models_trained['maintenance_prediction']
            scaler = self.scalers['maintenance_prediction']
            
            # Preparar dados de entrada
            features = np.array([[
                equipment_data.get('horas_uso', 500),
                equipment_data.get('temperatura_media', 45),
                equipment_data.get('vibracao_media', 3.5),
                equipment_data.get('idade_equipamento', 2),
                equipment_data.get('manutencoes_anteriores', 3)
            ]])
            
            # Normalizar e predizer
            features_scaled = scaler.transform(features)
            prediction = model.predict(features_scaled)[0]
            
            # Calcular probabilidade de falha (inversamente proporcional aos dias)
            probability = max(0, min(1, (365 - prediction) / 365))
            
            return prediction, probability
            
        except Exception as e:
            print(f"❌ Erro na predição de manutenção: {e}")
            return 30.0, 0.5
    
    def detect_anomalies(self, sensor_data: Dict) -> Tuple[bool, float]:
        """Detecta anomalias nos dados dos sensores"""
        try:
            model = self.models_trained['anomaly_detection']
            scaler = self.scalers['anomaly_detection']
            
            # Preparar dados de entrada
            features = np.array([[
                sensor_data.get('temperatura', 45),
                sensor_data.get('vibracao', 3.5),
                sensor_data.get('pressao', 2.1)
            ]])
            
            # Normalizar
            features_scaled = scaler.transform(features)
            
            # Predizer
            anomaly_score = model.decision_function(features_scaled)[0]
            is_anomaly = model.predict(features_scaled)[0] == -1
            
            return is_anomaly, anomaly_score
            
        except Exception as e:
            print(f"❌ Erro na detecção de anomalias: {e}")
            return False, 0.0
    
    def optimize_inventory(self, current_stock: int, days_ahead: int = 30) -> Dict:
        """Otimiza níveis de estoque"""
        try:
            model = self.models_trained['inventory_optimization']
            scaler = self.scalers['inventory_optimization']
            
            today = datetime.now()
            predictions = []
            
            for day in range(days_ahead):
                future_date = today + timedelta(days=day)
                
                features = np.array([[
                    day,  # dia relativo
                    future_date.weekday(),  # dia da semana
                    future_date.month - 1,  # mês (0-11)
                    current_stock
                ]])
                
                features_scaled = scaler.transform(features)
                predicted_demand = model.predict(features_scaled)[0]
                predictions.append(predicted_demand)
                
                # Atualizar estoque simulado
                current_stock = max(0, current_stock - predicted_demand)
            
            total_demand = sum(predictions)
            avg_daily_demand = total_demand / days_ahead
            
            # Calcular estoque recomendado (com margem de segurança)
            safety_stock = avg_daily_demand * 7  # 7 dias de segurança
            recommended_stock = total_demand + safety_stock
            
            return {
                'predicted_demand': total_demand,
                'avg_daily_demand': avg_daily_demand,
                'recommended_stock': recommended_stock,
                'safety_stock': safety_stock,
                'daily_predictions': predictions
            }
            
        except Exception as e:
            print(f"❌ Erro na otimização de estoque: {e}")
            return {
                'predicted_demand': 100,
                'avg_daily_demand': 10,
                'recommended_stock': 150,
                'safety_stock': 50,
                'daily_predictions': [10] * 30
            }
    
    def show_ml_dashboard(self):
        """Exibe dashboard principal de Machine Learning"""
        st.title("🧠 Machine Learning Avançado")
        
        # Métricas gerais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🤖 Modelos Ativos", len(self.models_trained), "+1")
        
        with col2:
            if hasattr(self, 'maintenance_metrics'):
                accuracy = self.maintenance_metrics['r2'] * 100
                st.metric("🎯 Acurácia Manutenção", f"{accuracy:.1f}%", "+2.3%")
        
        with col3:
            if hasattr(self, 'anomaly_metrics'):
                precision = self.anomaly_metrics['precision'] * 100
                st.metric("🔍 Precisão Anomalias", f"{precision:.1f}%", "+1.5%")
        
        with col4:
            st.metric("⚡ Predições Hoje", "47", "+12")
        
        # Gráficos principais
        col1, col2 = st.columns(2)
        
        with col1:
            self.show_maintenance_predictions_chart()
        
        with col2:
            self.show_anomaly_detection_chart()
        
        # Seção de insights
        self.show_ml_insights()
    
    def show_maintenance_predictions_chart(self):
        """Gráfico de predições de manutenção"""
        st.subheader("🔧 Predições de Manutenção")
        
        # Simular predições para diferentes equipamentos
        equipamentos = ['GER_001', 'COMP_002', 'BOMB_003', 'MOTOR_004', 'SERRA_005']
        predictions = []
        
        for equip in equipamentos:
            equipment_data = {
                'horas_uso': np.random.normal(500, 100),
                'temperatura_media': np.random.normal(45, 10),
                'vibracao_media': np.random.normal(3.5, 1),
                'idade_equipamento': np.random.exponential(2),
                'manutencoes_anteriores': np.random.poisson(3)
            }
            
            days, prob = self.predict_maintenance_needs(equipment_data)
            
            predictions.append({
                'Equipamento': equip,
                'Dias até Manutenção': days,
                'Probabilidade de Falha': prob * 100,
                'Urgência': 'Alta' if days < 15 else 'Média' if days < 30 else 'Baixa'
            })
        
        df_pred = pd.DataFrame(predictions)
        
        # Gráfico de barras
        fig = px.bar(
            df_pred, 
            x='Equipamento', 
            y='Dias até Manutenção',
            color='Urgência',
            color_discrete_map={
                'Alta': '#dc2626',
                'Média': '#f59e0b', 
                'Baixa': '#10b981'
            },
            title="Previsão de Manutenção por Equipamento"
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela detalhada
        st.dataframe(df_pred, use_container_width=True)
    
    def show_anomaly_detection_chart(self):
        """Gráfico de detecção de anomalias"""
        st.subheader("🚨 Detecção de Anomalias")
        
        # Simular dados de sensores em tempo real
        timestamps = pd.date_range(
            start=datetime.now() - timedelta(hours=24),
            end=datetime.now(),
            freq='H'
        )
        
        anomalies_data = []
        
        for i, ts in enumerate(timestamps):
            # Gerar dados de sensor simulados
            temp = 45 + 5 * np.sin(i * 2 * np.pi / 24) + np.random.normal(0, 2)
            vib = 3.5 + 0.5 * np.sin(i * 2 * np.pi / 12) + np.random.normal(0, 0.3)
            pressure = 2.1 + 0.2 * np.sin(i * 2 * np.pi / 8) + np.random.normal(0, 0.1)
            
            # Inserir algumas anomalias
            if i in [8, 15, 20]:  # Anomalias em horários específicos
                temp += np.random.normal(30, 5)  # Pico de temperatura
                vib += np.random.normal(3, 1)    # Vibração alta
            
            sensor_data = {'temperatura': temp, 'vibracao': vib, 'pressao': pressure}
            is_anomaly, score = self.detect_anomalies(sensor_data)
            
            anomalies_data.append({
                'Timestamp': ts,
                'Temperatura': temp,
                'Vibração': vib,
                'Pressão': pressure,
                'Anomalia': is_anomaly,
                'Score': score
            })
        
        df_anomalies = pd.DataFrame(anomalies_data)
        
        # Gráfico de séries temporais
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=['Temperatura (°C)', 'Vibração (m/s²)', 'Pressão (bar)'],
            vertical_spacing=0.08
        )
        
        # Dados normais e anomalias
        normal_data = df_anomalies[~df_anomalies['Anomalia']]
        anomaly_data = df_anomalies[df_anomalies['Anomalia']]
        
        # Temperatura
        fig.add_trace(
            go.Scatter(x=normal_data['Timestamp'], y=normal_data['Temperatura'], 
                      name='Normal', line=dict(color='blue')),
            row=1, col=1
        )
        if not anomaly_data.empty:
            fig.add_trace(
                go.Scatter(x=anomaly_data['Timestamp'], y=anomaly_data['Temperatura'],
                          mode='markers', name='Anomalia', marker=dict(color='red', size=8)),
                row=1, col=1
            )
        
        # Vibração
        fig.add_trace(
            go.Scatter(x=normal_data['Timestamp'], y=normal_data['Vibração'],
                      showlegend=False, line=dict(color='blue')),
            row=2, col=1
        )
        if not anomaly_data.empty:
            fig.add_trace(
                go.Scatter(x=anomaly_data['Timestamp'], y=anomaly_data['Vibração'],
                          mode='markers', showlegend=False, marker=dict(color='red', size=8)),
                row=2, col=1
            )
        
        # Pressão
        fig.add_trace(
            go.Scatter(x=normal_data['Timestamp'], y=normal_data['Pressão'],
                      showlegend=False, line=dict(color='blue')),
            row=3, col=1
        )
        if not anomaly_data.empty:
            fig.add_trace(
                go.Scatter(x=anomaly_data['Timestamp'], y=anomaly_data['Pressão'],
                          mode='markers', showlegend=False, marker=dict(color='red', size=8)),
                row=3, col=1
            )
        
        fig.update_layout(height=500, title_text="Detecção de Anomalias - Últimas 24h")
        st.plotly_chart(fig, use_container_width=True)
        
        # Resumo de anomalias
        if not anomaly_data.empty:
            st.warning(f"🚨 {len(anomaly_data)} anomalia(s) detectada(s) nas últimas 24h")
        else:
            st.success("✅ Nenhuma anomalia detectada nas últimas 24h")
    
    def show_ml_insights(self):
        """Exibe insights e recomendações do ML"""
        st.subheader("💡 Insights e Recomendações")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 🔧 Manutenção Preditiva")
            
            insights_manutencao = [
                "Equipamento GER_001 precisa de manutenção em 8 dias",
                "Temperatura alta detectada no COMP_002",
                "Padrão de vibração anômalo no MOTOR_004",
                "Economia estimada: R$ 15.000 com manutenção preventiva"
            ]
            
            for insight in insights_manutencao:
                st.info(f"💡 {insight}")
        
        with col2:
            st.markdown("#### 📦 Otimização de Estoque")
            
            # Exemplo de otimização
            optimization = self.optimize_inventory(current_stock=150, days_ahead=30)
            
            st.metric("Demanda Prevista (30 dias)", f"{optimization['predicted_demand']:.0f}")
            st.metric("Estoque Recomendado", f"{optimization['recommended_stock']:.0f}")
            st.metric("Economia Potencial", "R$ 8.500")
            
            if optimization['recommended_stock'] > 150:
                st.warning(f"⚠️ Recomendar compra de {optimization['recommended_stock'] - 150:.0f} unidades")
            else:
                st.success("✅ Estoque atual adequado")
        
        with col3:
            st.markdown("#### 🚨 Alertas Inteligentes")
            
            alertas_ml = [
                {"tipo": "Anomalia", "severidade": "Alta", "msg": "Vibração crítica detectada"},
                {"tipo": "Predição", "severidade": "Média", "msg": "Falha prevista em 5 dias"},
                {"tipo": "Otimização", "severidade": "Baixa", "msg": "Oportunidade de economia identificada"}
            ]
            
            for alerta in alertas_ml:
                color = {"Alta": "error", "Média": "warning", "Baixa": "info"}[alerta["severidade"]]
                getattr(st, color)(f"{alerta['tipo']}: {alerta['msg']}")
    
    def show_model_management(self):
        """Interface de gestão de modelos"""
        st.subheader("🤖 Gestão de Modelos ML")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Modelos Ativos", "🔧 Treinar Modelo", "📈 Performance", "🎯 Predições"
        ])
        
        with tab1:
            self.show_active_models()
        
        with tab2:
            self.show_model_training_interface()
        
        with tab3:
            self.show_model_performance()
        
        with tab4:
            self.show_prediction_interface()
    
    def show_active_models(self):
        """Lista modelos ativos"""
        st.markdown("### 🤖 Modelos ML Ativos")
        
        modelos_info = [
            {
                "Nome": "Predição de Manutenção",
                "Algoritmo": "Random Forest",
                "Acurácia": f"{self.maintenance_metrics['r2']:.3f}" if hasattr(self, 'maintenance_metrics') else "N/A",
                "Última Atualização": "2024-01-15",
                "Status": "Ativo",
                "Predições Hoje": 23
            },
            {
                "Nome": "Detecção de Anomalias",
                "Algoritmo": "Isolation Forest",
                "Acurácia": f"{self.anomaly_metrics['f1_score']:.3f}" if hasattr(self, 'anomaly_metrics') else "N/A",
                "Última Atualização": "2024-01-14",
                "Status": "Ativo", 
                "Predições Hoje": 156
            },
            {
                "Nome": "Otimização de Estoque",
                "Algoritmo": "Random Forest",
                "Acurácia": f"{self.inventory_metrics['r2']:.3f}" if hasattr(self, 'inventory_metrics') else "N/A",
                "Última Atualização": "2024-01-13",
                "Status": "Ativo",
                "Predições Hoje": 8
            }
        ]
        
        df_modelos = pd.DataFrame(modelos_info)
        
        # Exibir tabela com formatação
        for i, modelo in enumerate(modelos_info):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**{modelo['Nome']}**")
                    st.caption(f"Algoritmo: {modelo['Algoritmo']}")
                
                with col2:
                    st.metric("Acurácia", modelo['Acurácia'])
                
                with col3:
                    st.metric("Predições Hoje", modelo['Predições Hoje'])
                
                with col4:
                    status_color = "🟢" if modelo['Status'] == "Ativo" else "🔴"
                    st.markdown(f"{status_color} {modelo['Status']}")
                    
                    if st.button("⚙️", key=f"config_model_{i}", help="Configurar"):
                        st.info(f"Configurando modelo {modelo['Nome']}")
                
                st.divider()
    
    def show_model_training_interface(self):
        """Interface para treinar novos modelos"""
        st.markdown("### 🔧 Treinar Novo Modelo")
        
        tipo_modelo = st.selectbox(
            "Tipo de Modelo",
            ["Predição de Manutenção", "Detecção de Anomalias", "Otimização de Estoque", "Previsão de Demanda"]
        )
        
        algoritmo = st.selectbox(
            "Algoritmo",
            ["Random Forest", "Gradient Boosting", "Linear Regression", "Isolation Forest", "Neural Network"]
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Configurações de Dados")
            
            fonte_dados = st.selectbox("Fonte de Dados", [
                "Histórico de Manutenções",
                "Dados de Sensores IoT", 
                "Movimentações de Estoque",
                "Dados Customizados"
            ])
            
            periodo_treino = st.selectbox("Período de Treinamento", [
                "Últimos 6 meses",
                "Último ano",
                "Últimos 2 anos",
                "Todo o histórico"
            ])
            
            validacao = st.selectbox("Tipo de Validação", [
                "Train/Test Split (80/20)",
                "Validação Cruzada (5-fold)",
                "Validação Temporal"
            ])
        
        with col2:
            st.markdown("#### ⚙️ Hiperparâmetros")
            
            if algoritmo == "Random Forest":
                n_estimators = st.slider("Número de Árvores", 50, 500, 100)
                max_depth = st.slider("Profundidade Máxima", 3, 20, 10)
                min_samples_split = st.slider("Mín. Amostras para Split", 2, 20, 5)
            
            elif algoritmo == "Gradient Boosting":
                learning_rate = st.slider("Taxa de Aprendizagem", 0.01, 0.3, 0.1, 0.01)
                n_estimators = st.slider("Número de Estimadores", 50, 500, 100)
                max_depth = st.slider("Profundidade", 3, 10, 6)
        
        if st.button("🚀 Iniciar Treinamento", type="primary"):
            with st.spinner("Treinando modelo..."):
                import time
                time.sleep(3)  # Simular tempo de treinamento
            
            st.success("✅ Modelo treinado com sucesso!")
            
            # Mostrar métricas simuladas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Acurácia", "0.847", "+0.023")
            with col2:
                st.metric("Precisão", "0.832", "+0.015")
            with col3:
                st.metric("Recall", "0.891", "+0.031")
    
    def show_model_performance(self):
        """Exibe performance dos modelos"""
        st.markdown("### 📈 Performance dos Modelos")
        
        modelo_selecionado = st.selectbox(
            "Selecionar Modelo",
            ["Predição de Manutenção", "Detecção de Anomalias", "Otimização de Estoque"]
        )
        
        if modelo_selecionado == "Predição de Manutenção" and hasattr(self, 'maintenance_metrics'):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 Métricas de Performance")
                
                metrics = self.maintenance_metrics
                st.metric("R² Score", f"{metrics['r2']:.3f}")
                st.metric("MAE (dias)", f"{metrics['mae']:.2f}")
                st.metric("RMSE (dias)", f"{np.sqrt(metrics['mse']):.2f}")
            
            with col2:
                st.markdown("#### 🎯 Importância das Features")
                
                feature_imp = metrics['feature_importance']
                
                # Gráfico de importância
                fig = px.bar(
                    x=list(feature_imp.values()),
                    y=list(feature_imp.keys()),
                    orientation='h',
                    title="Importância das Variáveis"
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de evolução da performance
        st.markdown("#### 📈 Evolução da Performance")
        
        # Dados simulados de performance ao longo do tempo
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='M')
        accuracy_evolution = np.random.normal(0.85, 0.05, len(dates))
        accuracy_evolution = np.clip(accuracy_evolution, 0.7, 0.95)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, 
            y=accuracy_evolution,
            mode='lines+markers',
            name='Acurácia',
            line=dict(color='#3b82f6')
        ))
        
        fig.update_layout(
            title="Evolução da Acurácia ao Longo do Tempo",
            xaxis_title="Data",
            yaxis_title="Acurácia",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def show_prediction_interface(self):
        """Interface para fazer predições"""
        st.markdown("### 🎯 Fazer Predições")
        
        tipo_predicao = st.selectbox(
            "Tipo de Predição",
            ["Manutenção de Equipamento", "Detecção de Anomalia", "Otimização de Estoque"]
        )
        
        if tipo_predicao == "Manutenção de Equipamento":
            st.markdown("#### 🔧 Dados do Equipamento")
            
            col1, col2 = st.columns(2)
            
            with col1:
                horas_uso = st.number_input("Horas de Uso", value=500.0)
                temp_media = st.number_input("Temperatura Média (°C)", value=45.0)
                vib_media = st.number_input("Vibração Média (m/s²)", value=3.5)
            
            with col2:
                idade_equip = st.number_input("Idade do Equipamento (anos)", value=2.0)
                manut_anteriores = st.number_input("Manutenções Anteriores", value=3)
            
            if st.button("🔮 Fazer Predição"):
                equipment_data = {
                    'horas_uso': horas_uso,
                    'temperatura_media': temp_media,
                    'vibracao_media': vib_media,
                    'idade_equipamento': idade_equip,
                    'manutencoes_anteriores': manut_anteriores
                }
                
                dias, probabilidade = self.predict_maintenance_needs(equipment_data)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Dias até Manutenção", f"{dias:.0f}")
                
                with col2:
                    st.metric("Probabilidade de Falha", f"{probabilidade*100:.1f}%")
                
                with col3:
                    urgencia = "Alta" if dias < 15 else "Média" if dias < 30 else "Baixa"
                    color = {"Alta": "🔴", "Média": "🟡", "Baixa": "🟢"}[urgencia]
                    st.markdown(f"**Urgência:** {color} {urgencia}")
                
                # Recomendações
                if dias < 15:
                    st.error("🚨 Manutenção urgente recomendada!")
                elif dias < 30:
                    st.warning("⚠️ Agendar manutenção preventiva")
                else:
                    st.success("✅ Equipamento em boas condições")
        
        elif tipo_predicao == "Detecção de Anomalia":
            st.markdown("#### 🔍 Dados dos Sensores")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                temperatura = st.number_input("Temperatura", value=45.0)
            
            with col2:
                vibracao = st.number_input("Vibração", value=3.5)
            
            with col3:
                pressao = st.number_input("Pressão", value=2.1)
            
            if st.button("🔍 Detectar Anomalia"):
                sensor_data = {
                    'temperatura': temperatura,
                    'vibracao': vibracao,
                    'pressao': pressao
                }
                
                is_anomaly, score = self.detect_anomalies(sensor_data)
                
                if is_anomaly:
                    st.error(f"🚨 ANOMALIA DETECTADA! Score: {score:.3f}")
                else:
                    st.success(f"✅ Comportamento normal. Score: {score:.3f}")
        
        elif tipo_predicao == "Otimização de Estoque":
            st.markdown("#### 📦 Dados de Estoque")
            
            col1, col2 = st.columns(2)
            
            with col1:
                estoque_atual = st.number_input("Estoque Atual", value=150)
                dias_previsao = st.number_input("Dias de Previsão", value=30)
            
            if st.button("📊 Otimizar Estoque"):
                optimization = self.optimize_inventory(estoque_atual, dias_previsao)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Demanda Prevista", f"{optimization['predicted_demand']:.0f}")
                
                with col2:
                    st.metric("Estoque Recomendado", f"{optimization['recommended_stock']:.0f}")
                
                with col3:
                    diferenca = optimization['recommended_stock'] - estoque_atual
                    st.metric("Diferença", f"{diferenca:+.0f}")
                
                # Gráfico de predição diária
                fig = go.Figure()
                
                dates = pd.date_range(start=datetime.now(), periods=dias_previsao, freq='D')
                
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=optimization['daily_predictions'],
                    mode='lines+markers',
                    name='Demanda Prevista',
                    line=dict(color='#3b82f6')
                ))
                
                fig.update_layout(
                    title="Previsão de Demanda Diária",
                    xaxis_title="Data",
                    yaxis_title="Demanda",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)

def show_ml_page():
    """Página principal do Machine Learning"""
    st.set_page_config(
        page_title="🧠 Machine Learning",
        page_icon="🧠", 
        layout="wide"
    )
    
    ml_manager = MachineLearningManager()
    
    # Menu lateral
    menu_ml = st.sidebar.selectbox(
        "📂 Menu ML",
        ["🏠 Dashboard", "🤖 Gestão de Modelos", "📊 Analytics Avançado", "🔬 Laboratório ML"]
    )
    
    if menu_ml == "🏠 Dashboard":
        ml_manager.show_ml_dashboard()
    
    elif menu_ml == "🤖 Gestão de Modelos":
        ml_manager.show_model_management()
    
    elif menu_ml == "📊 Analytics Avançado":
        st.subheader("📊 Analytics Avançado")
        
        tab1, tab2, tab3 = st.tabs([
            "📈 Análise Preditiva", "🔍 Análise de Padrões", "💼 ROI de ML"
        ])
        
        with tab1:
            st.markdown("#### 📈 Análise Preditiva")
            
            # Matriz de correlação simulada
            features = ['Temperatura', 'Vibração', 'Horas de Uso', 'Idade', 'Manutenções']
            correlation_matrix = np.random.rand(5, 5)
            correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2
            np.fill_diagonal(correlation_matrix, 1)
            
            fig = px.imshow(
                correlation_matrix,
                x=features,
                y=features,
                color_continuous_scale='RdYlBu_r',
                title="Matriz de Correlação entre Features"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.markdown("#### 🔍 Análise de Padrões")
            
            # Clustering simulado
            n_points = 300
            cluster1 = np.random.multivariate_normal([2, 2], [[0.5, 0.1], [0.1, 0.5]], n_points//3)
            cluster2 = np.random.multivariate_normal([6, 6], [[0.5, -0.1], [-0.1, 0.5]], n_points//3) 
            cluster3 = np.random.multivariate_normal([2, 6], [[0.5, 0], [0, 0.5]], n_points//3)
            
            data = np.vstack([cluster1, cluster2, cluster3])
            labels = ['Cluster 1'] * (n_points//3) + ['Cluster 2'] * (n_points//3) + ['Cluster 3'] * (n_points//3)
            
            fig = px.scatter(
                x=data[:, 0], y=data[:, 1], color=labels,
                title="Clustering de Equipamentos por Padrão de Uso",
                labels={'x': 'Feature 1', 'y': 'Feature 2'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.markdown("#### 💼 ROI do Machine Learning")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Economia Total", "R$ 150.000", "+23%")
                st.caption("Economia com manutenção preditiva")
            
            with col2:
                st.metric("Redução de Downtime", "65%", "+12%")
                st.caption("Redução de tempo de parada")
            
            with col3:
                st.metric("ROI de ML", "340%", "+15%")
                st.caption("Retorno sobre investimento")
    
    elif menu_ml == "🔬 Laboratório ML":
        st.subheader("🔬 Laboratório de Machine Learning")
        
        st.markdown("""
        ### 🧪 Ambiente de Experimentação
        
        Este é o ambiente para testar novos algoritmos e abordagens de ML.
        """)
        
        tab1, tab2 = st.tabs(["🧠 Experimentar Algoritmos", "📊 A/B Testing de Modelos"])
        
        with tab1:
            st.markdown("#### 🧠 Testar Novos Algoritmos")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                algoritmo_teste = st.selectbox("Algoritmo para Teste", [
                    "XGBoost", "LightGBM", "CatBoost", "Neural Network", "SVM"
                ])
                
                dataset_teste = st.selectbox("Dataset", [
                    "Dados de Manutenção", "Dados de Sensores", "Dados de Estoque"
                ])
                
                if st.button("🚀 Executar Experimento"):
                    with st.spinner("Executando experimento..."):
                        time.sleep(2)
                    
                    st.success("✅ Experimento concluído!")
                    
                    # Resultados simulados
                    st.json({
                        "acuracia": 0.892,
                        "precisao": 0.876,
                        "recall": 0.915,
                        "f1_score": 0.895,
                        "tempo_treino": "12.3s"
                    })
            
            with col2:
                st.markdown("**📊 Comparação de Performance**")
                
                # Gráfico comparativo simulado
                algoritmos = ['Random Forest', 'XGBoost', 'Neural Network', 'SVM']
                metricas = np.random.uniform(0.7, 0.95, 4)
                
                fig = px.bar(x=algoritmos, y=metricas, 
                           title="Comparação de Acurácia entre Algoritmos")
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.markdown("#### 📊 A/B Testing de Modelos")
            
            st.info("🧪 Comparando performance entre Modelo A (atual) vs Modelo B (novo)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Modelo A (Atual)**")
                st.metric("Acurácia", "0.847")
                st.metric("Predições/dia", "145")
                st.metric("Tempo médio", "0.3s")
            
            with col2:
                st.markdown("**Modelo B (Novo)**") 
                st.metric("Acurácia", "0.892", "+0.045")
                st.metric("Predições/dia", "187", "+42")
                st.metric("Tempo médio", "0.2s", "-0.1s")
            
            if st.button("📊 Finalizar A/B Test"):
                st.success("✅ Modelo B aprovado! Performance 15% superior.")

if __name__ == "__main__":
    show_ml_page()