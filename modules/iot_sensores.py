"""
IoT e Sensores - Sistema Completo
Integração com dispositivos IoT, monitoramento de sensores e telemetria
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import time
import threading
import asyncio
from typing import Dict, List, Any, Optional
from database.connection import db
from modules.logs_auditoria import log_acao
import random
import paho.mqtt.client as mqtt

class IoTManager:
    """Gerenciador completo de IoT e Sensores"""
    
    def __init__(self):
        self.mqtt_client = None
        self.dispositivos_conectados = {}
        self.alertas_ativos = []
        self.criar_tabelas_iot()
        self.inicializar_mqtt()
    
    def criar_tabelas_iot(self):
        """Cria estrutura de tabelas para IoT"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Tabela de dispositivos IoT
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS dispositivos_iot (
                id SERIAL PRIMARY KEY,
                device_id VARCHAR(255) UNIQUE NOT NULL,
                nome VARCHAR(255) NOT NULL,
                tipo_dispositivo VARCHAR(100) NOT NULL, -- sensor_temp, sensor_umidade, beacon, rfid, etc
                localizacao VARCHAR(255),
                equipamento_associado_codigo VARCHAR(255),
                configuracao_json JSONB,
                status_conexao VARCHAR(50) DEFAULT 'offline',
                ultima_comunicacao TIMESTAMP,
                frequencia_leitura INTEGER DEFAULT 60, -- em segundos
                limites_operacionais JSONB,
                data_instalacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ativo BOOLEAN DEFAULT TRUE
            )
            """)
            
            # Tabela de dados de sensores
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS dados_sensores (
                id SERIAL PRIMARY KEY,
                device_id VARCHAR(255) NOT NULL,
                timestamp_leitura TIMESTAMP NOT NULL,
                tipo_sensor VARCHAR(100) NOT NULL,
                valor_numerico DECIMAL(15,6),
                valor_texto VARCHAR(255),
                valor_json JSONB,
                unidade_medida VARCHAR(50),
                qualidade_sinal INTEGER, -- 0-100
                bateria_nivel INTEGER,  -- 0-100
                temperatura_dispositivo DECIMAL(8,2),
                localizacao_gps JSONB,
                processado BOOLEAN DEFAULT FALSE,
                INDEX idx_device_timestamp (device_id, timestamp_leitura),
                INDEX idx_timestamp (timestamp_leitura),
                INDEX idx_processado (processado)
            )
            """)
            
            # Tabela de alertas IoT
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS alertas_iot (
                id SERIAL PRIMARY KEY,
                device_id VARCHAR(255) NOT NULL,
                tipo_alerta VARCHAR(100) NOT NULL, -- temperatura_alta, bateria_baixa, dispositivo_offline
                severidade VARCHAR(50) DEFAULT 'medio', -- baixo, medio, alto, critico
                titulo VARCHAR(255) NOT NULL,
                descricao TEXT,
                valor_detectado VARCHAR(255),
                limite_configurado VARCHAR(255),
                timestamp_alerta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                timestamp_reconhecimento TIMESTAMP,
                reconhecido_por INTEGER,
                status_alerta VARCHAR(50) DEFAULT 'ativo', -- ativo, reconhecido, resolvido
                acoes_tomadas TEXT,
                equipamento_afetado VARCHAR(255)
            )
            """)
            
            # Tabela de regras de monitoramento
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS regras_monitoramento (
                id SERIAL PRIMARY KEY,
                nome_regra VARCHAR(255) NOT NULL,
                device_id VARCHAR(255),
                tipo_sensor VARCHAR(100),
                condicao_sql TEXT NOT NULL, -- Ex: valor_numerico > 50
                tipo_alerta VARCHAR(100) NOT NULL,
                severidade VARCHAR(50) DEFAULT 'medio',
                acao_automatica VARCHAR(255), -- email, sms, webhook, etc
                ativo BOOLEAN DEFAULT TRUE,
                parametros_acao JSONB,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                criado_por INTEGER
            )
            """)
            
            # Tabela de dashboards personalizados
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS dashboards_iot (
                id SERIAL PRIMARY KEY,
                nome_dashboard VARCHAR(255) NOT NULL,
                usuario_id INTEGER NOT NULL,
                configuracao_widgets JSONB NOT NULL,
                layout_config JSONB,
                dispositivos_inclusos TEXT[],
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                compartilhado BOOLEAN DEFAULT FALSE
            )
            """)
            
            # Tabela de comandos remotos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS comandos_remotos (
                id SERIAL PRIMARY KEY,
                device_id VARCHAR(255) NOT NULL,
                comando VARCHAR(255) NOT NULL,
                parametros JSONB,
                enviado_por INTEGER NOT NULL,
                timestamp_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                timestamp_execucao TIMESTAMP,
                status_comando VARCHAR(50) DEFAULT 'pendente', -- pendente, executado, erro, timeout
                resposta_dispositivo TEXT,
                erro_execucao TEXT
            )
            """)
            
            # Tabela de manutenção preditiva IoT
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS manutencao_preditiva_iot (
                id SERIAL PRIMARY KEY,
                equipamento_codigo VARCHAR(255) NOT NULL,
                device_id VARCHAR(255),
                tipo_predicao VARCHAR(100) NOT NULL, -- falha_bateria, desgaste_sensor, etc
                probabilidade_falha DECIMAL(5,2), -- 0-100%
                tempo_estimado_falha INTEGER, -- em dias
                indicadores_utilizados JSONB,
                data_predicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                acao_recomendada TEXT,
                urgencia_manutencao VARCHAR(50), -- baixa, media, alta, critica
                status_predicao VARCHAR(50) DEFAULT 'ativo' -- ativo, verificado, falso_positivo
            )
            """)
            
            conn.commit()
            print("✅ Tabelas IoT criadas com sucesso")
            
        except Exception as e:
            print(f"❌ Erro ao criar tabelas IoT: {e}")
    
    def inicializar_mqtt(self):
        """Inicializa cliente MQTT para comunicação IoT"""
        try:
            self.mqtt_client = mqtt.Client()
            
            # Callbacks MQTT
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            
            # Em ambiente de produção, conectar ao broker MQTT real
            # self.mqtt_client.connect("broker.hivemq.com", 1883, 60)
            # self.mqtt_client.loop_start()
            
            print("✅ Cliente MQTT inicializado")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar MQTT: {e}")
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback de conexão MQTT"""
        if rc == 0:
            print("✅ Conectado ao broker MQTT")
            # Inscrever-se nos tópicos
            client.subscribe("inventario/+/sensores/+")
            client.subscribe("inventario/+/alertas/+")
            client.subscribe("inventario/+/status")
        else:
            print(f"❌ Falha na conexão MQTT: {rc}")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Processa mensagens MQTT recebidas"""
        try:
            topic_parts = msg.topic.split('/')
            device_id = topic_parts[1]
            message_type = topic_parts[2]
            
            payload = json.loads(msg.payload.decode())
            
            if message_type == "sensores":
                self.processar_dados_sensor(device_id, payload)
            elif message_type == "alertas":
                self.processar_alerta_dispositivo(device_id, payload)
            elif message_type == "status":
                self.atualizar_status_dispositivo(device_id, payload)
                
        except Exception as e:
            print(f"❌ Erro ao processar mensagem MQTT: {e}")
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """Callback de desconexão MQTT"""
        print(f"🔌 Desconectado do broker MQTT: {rc}")
    
    def processar_dados_sensor(self, device_id: str, dados: Dict):
        """Processa dados recebidos de sensores"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Inserir dados do sensor
            cursor.execute("""
            INSERT INTO dados_sensores 
            (device_id, timestamp_leitura, tipo_sensor, valor_numerico, valor_texto, 
             valor_json, unidade_medida, qualidade_sinal, bateria_nivel, temperatura_dispositivo, localizacao_gps)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                device_id,
                dados.get('timestamp', datetime.now()),
                dados.get('tipo_sensor'),
                dados.get('valor_numerico'),
                dados.get('valor_texto'),
                json.dumps(dados.get('valor_json')) if dados.get('valor_json') else None,
                dados.get('unidade'),
                dados.get('qualidade_sinal', 100),
                dados.get('bateria', 100),
                dados.get('temperatura_dispositivo'),
                json.dumps(dados.get('gps')) if dados.get('gps') else None
            ])
            
            # Atualizar última comunicação do dispositivo
            cursor.execute("""
            UPDATE dispositivos_iot 
            SET ultima_comunicacao = %s, status_conexao = 'online'
            WHERE device_id = %s
            """, [datetime.now(), device_id])
            
            conn.commit()
            
            # Verificar regras de monitoramento
            self.verificar_regras_monitoramento(device_id, dados)
            
        except Exception as e:
            print(f"❌ Erro ao processar dados do sensor {device_id}: {e}")
    
    def verificar_regras_monitoramento(self, device_id: str, dados: Dict):
        """Verifica regras de monitoramento e gera alertas se necessário"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Buscar regras ativas para o dispositivo
            cursor.execute("""
            SELECT * FROM regras_monitoramento 
            WHERE (device_id = %s OR device_id IS NULL) 
            AND (tipo_sensor = %s OR tipo_sensor IS NULL)
            AND ativo = TRUE
            """, [device_id, dados.get('tipo_sensor')])
            
            regras = cursor.fetchall()
            
            for regra in regras:
                # Avaliar condição da regra
                if self.avaliar_condicao_regra(regra['condicao_sql'], dados):
                    self.gerar_alerta_automatico(device_id, regra, dados)
                    
        except Exception as e:
            print(f"❌ Erro ao verificar regras: {e}")
    
    def avaliar_condicao_regra(self, condicao_sql: str, dados: Dict) -> bool:
        """Avalia condição SQL da regra contra os dados recebidos"""
        try:
            # Substituir variáveis na condição
            valor_numerico = dados.get('valor_numerico', 0)
            valor_texto = dados.get('valor_texto', '')
            bateria = dados.get('bateria', 100)
            qualidade_sinal = dados.get('qualidade_sinal', 100)
            
            # Evaluar condição de forma segura
            condicao_formatada = condicao_sql.replace('valor_numerico', str(valor_numerico))
            condicao_formatada = condicao_formatada.replace('bateria', str(bateria))
            condicao_formatada = condicao_formatada.replace('qualidade_sinal', str(qualidade_sinal))
            
            # Lista de operadores permitidos (segurança)
            operadores_permitidos = ['>', '<', '>=', '<=', '==', '!=', 'and', 'or']
            
            # Verificação básica de segurança
            for char in ['import', 'exec', 'eval', '__']:
                if char in condicao_formatada.lower():
                    return False
            
            return eval(condicao_formatada)
            
        except Exception as e:
            print(f"❌ Erro ao avaliar condição: {e}")
            return False
    
    def gerar_alerta_automatico(self, device_id: str, regra: Dict, dados: Dict):
        """Gera alerta automático baseado em regra"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Verificar se já existe alerta similar recente
            cursor.execute("""
            SELECT COUNT(*) as count FROM alertas_iot 
            WHERE device_id = %s AND tipo_alerta = %s 
            AND timestamp_alerta >= %s AND status_alerta = 'ativo'
            """, [device_id, regra['tipo_alerta'], datetime.now() - timedelta(hours=1)])
            
            if cursor.fetchone()['count'] > 0:
                return  # Já existe alerta similar recente
            
            # Criar alerta
            cursor.execute("""
            INSERT INTO alertas_iot 
            (device_id, tipo_alerta, severidade, titulo, descricao, valor_detectado, limite_configurado)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [
                device_id,
                regra['tipo_alerta'],
                regra['severidade'],
                f"Alerta {regra['nome_regra']}",
                f"Regra '{regra['nome_regra']}' acionada para dispositivo {device_id}",
                str(dados.get('valor_numerico', dados.get('valor_texto', ''))),
                regra['condicao_sql']
            ])
            
            conn.commit()
            
            # Executar ação automática se configurada
            if regra['acao_automatica']:
                self.executar_acao_automatica(regra, device_id, dados)
            
        except Exception as e:
            print(f"❌ Erro ao gerar alerta: {e}")
    
    def executar_acao_automatica(self, regra: Dict, device_id: str, dados: Dict):
        """Executa ação automática configurada na regra"""
        try:
            acao = regra['acao_automatica']
            parametros = regra.get('parametros_acao', {})
            
            if acao == 'email':
                self.enviar_email_alerta(device_id, regra, dados, parametros)
            elif acao == 'webhook':
                self.enviar_webhook_alerta(device_id, regra, dados, parametros)
            elif acao == 'comando_remoto':
                self.enviar_comando_remoto(device_id, parametros.get('comando'), parametros.get('parametros'))
                
        except Exception as e:
            print(f"❌ Erro ao executar ação automática: {e}")
    
    def simular_dispositivos_iot(self) -> List[Dict]:
        """Simula dados de dispositivos IoT para demonstração"""
        dispositivos_simulados = [
            {
                'device_id': 'TEMP_001',
                'nome': 'Sensor Temperatura - Gerador Principal',
                'tipo_dispositivo': 'sensor_temperatura',
                'localizacao': 'Obra Centro - Gerador',
                'valor_numerico': random.uniform(20.0, 85.0),
                'unidade': '°C',
                'bateria': random.randint(70, 100),
                'qualidade_sinal': random.randint(80, 100)
            },
            {
                'device_id': 'HUM_002', 
                'nome': 'Sensor Umidade - Depósito Ferramentas',
                'tipo_dispositivo': 'sensor_umidade',
                'localizacao': 'Depósito Central',
                'valor_numerico': random.uniform(30.0, 90.0),
                'unidade': '%',
                'bateria': random.randint(60, 100),
                'qualidade_sinal': random.randint(75, 100)
            },
            {
                'device_id': 'VIB_003',
                'nome': 'Sensor Vibração - Compressor',
                'tipo_dispositivo': 'sensor_vibracao',
                'localizacao': 'Obra Norte - Área Técnica',
                'valor_numerico': random.uniform(0.0, 15.0),
                'unidade': 'm/s²',
                'bateria': random.randint(80, 100),
                'qualidade_sinal': random.randint(85, 100)
            },
            {
                'device_id': 'RFID_004',
                'nome': 'Leitor RFID - Entrada Principal',
                'tipo_dispositivo': 'rfid_reader',
                'localizacao': 'Portão Principal',
                'valor_texto': f'TAG_{random.randint(1000, 9999)}',
                'bateria': random.randint(85, 100),
                'qualidade_sinal': random.randint(90, 100)
            },
            {
                'device_id': 'GPS_005',
                'nome': 'Rastreador GPS - Caminhão 01',
                'tipo_dispositivo': 'gps_tracker',
                'localizacao': 'Veículo Móvel',
                'gps': {'lat': -23.5505 + random.uniform(-0.1, 0.1), 'lng': -46.6333 + random.uniform(-0.1, 0.1)},
                'bateria': random.randint(50, 100),
                'qualidade_sinal': random.randint(70, 100)
            },
            {
                'device_id': 'ENERGY_006',
                'nome': 'Medidor Energia - Painel Principal',
                'tipo_dispositivo': 'medidor_energia',
                'localizacao': 'Quadro Elétrico Principal',
                'valor_numerico': random.uniform(100.0, 500.0),
                'unidade': 'kWh',
                'bateria': 100,  # Alimentado pela rede
                'qualidade_sinal': random.randint(95, 100)
            }
        ]
        
        return dispositivos_simulados
    
    def show_iot_dashboard(self):
        """Exibe dashboard principal de IoT"""
        st.title("🌐 IoT e Sensores - Dashboard")
        
        # Métricas em tempo real
        col1, col2, col3, col4 = st.columns(4)
        
        dispositivos_simulados = self.simular_dispositivos_iot()
        
        with col1:
            st.metric("📡 Dispositivos Ativos", len(dispositivos_simulados), "+2")
        
        with col2:
            dispositivos_online = len([d for d in dispositivos_simulados if d['qualidade_sinal'] > 70])
            st.metric("🟢 Online", dispositivos_online, "+1")
        
        with col3:
            alertas_ativos = random.randint(0, 3)
            st.metric("⚠️ Alertas Ativos", alertas_ativos, "-1")
        
        with col4:
            avg_bateria = np.mean([d['bateria'] for d in dispositivos_simulados])
            st.metric("🔋 Bateria Média", f"{avg_bateria:.1f}%", "+2.3%")
        
        # Mapa de dispositivos em tempo real
        self.show_device_map(dispositivos_simulados)
        
        # Gráficos de monitoramento
        self.show_monitoring_charts(dispositivos_simulados)
    
    def show_device_map(self, dispositivos: List[Dict]):
        """Exibe mapa com localização dos dispositivos"""
        st.subheader("🗺️ Mapa de Dispositivos IoT")
        
        # Criar dados para o mapa
        map_data = []
        for device in dispositivos:
            if 'gps' in device:
                map_data.append({
                    'lat': device['gps']['lat'],
                    'lon': device['gps']['lng'],
                    'device_id': device['device_id'],
                    'nome': device['nome'],
                    'status': 'online' if device['qualidade_sinal'] > 70 else 'offline',
                    'bateria': device['bateria']
                })
            else:
                # Coordenadas simuladas para dispositivos fixos
                map_data.append({
                    'lat': -23.5505 + random.uniform(-0.05, 0.05),
                    'lon': -46.6333 + random.uniform(-0.05, 0.05),
                    'device_id': device['device_id'],
                    'nome': device['nome'],
                    'status': 'online' if device['qualidade_sinal'] > 70 else 'offline',
                    'bateria': device['bateria']
                })
        
        if map_data:
            df_map = pd.DataFrame(map_data)
            
            # Configurar cores baseadas no status
            df_map['color'] = df_map['status'].map({
                'online': '#10b981',
                'offline': '#dc2626'
            })
            
            # Criar mapa com Plotly
            fig = px.scatter_mapbox(
                df_map,
                lat='lat',
                lon='lon',
                color='status',
                size='bateria',
                hover_name='device_id',
                hover_data=['nome', 'bateria'],
                color_discrete_map={'online': '#10b981', 'offline': '#dc2626'},
                size_max=20,
                zoom=10,
                title="Localização em Tempo Real dos Dispositivos IoT"
            )
            
            fig.update_layout(
                mapbox_style="open-street-map",
                height=500,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def show_monitoring_charts(self, dispositivos: List[Dict]):
        """Exibe gráficos de monitoramento em tempo real"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Sensores em Tempo Real")
            
            # Gráfico de temperatura e umidade
            sensores_temp_hum = [d for d in dispositivos if 'valor_numerico' in d and d['tipo_dispositivo'] in ['sensor_temperatura', 'sensor_umidade']]
            
            if sensores_temp_hum:
                fig_sensors = go.Figure()
                
                for sensor in sensores_temp_hum:
                    fig_sensors.add_trace(go.Scatter(
                        x=[datetime.now()],
                        y=[sensor['valor_numerico']],
                        mode='markers+text',
                        name=sensor['nome'],
                        text=[f"{sensor['valor_numerico']:.1f} {sensor['unidade']}"],
                        textposition="top center",
                        marker=dict(
                            size=15,
                            color='red' if sensor['tipo_dispositivo'] == 'sensor_temperatura' else 'blue'
                        )
                    ))
                
                fig_sensors.update_layout(
                    title="Leituras Atuais de Temperatura e Umidade",
                    xaxis_title="Tempo",
                    yaxis_title="Valor",
                    height=350
                )
                
                st.plotly_chart(fig_sensors, use_container_width=True)
        
        with col2:
            st.subheader("🔋 Status das Baterias")
            
            # Gráfico de bateria
            device_names = [d['device_id'] for d in dispositivos]
            battery_levels = [d['bateria'] for d in dispositivos]
            
            fig_battery = go.Figure(data=[
                go.Bar(
                    x=device_names,
                    y=battery_levels,
                    marker_color=['red' if b < 20 else 'orange' if b < 50 else 'green' for b in battery_levels],
                    text=[f'{b}%' for b in battery_levels],
                    textposition='auto',
                )
            ])
            
            fig_battery.update_layout(
                title="Níveis de Bateria dos Dispositivos",
                xaxis_title="Dispositivo",
                yaxis_title="Bateria (%)",
                height=350,
                yaxis=dict(range=[0, 100])
            )
            
            st.plotly_chart(fig_battery, use_container_width=True)
        
        # Histórico de dados simulado
        st.subheader("📈 Histórico de Dados (24h)")
        self.show_historical_data()
    
    def show_historical_data(self):
        """Exibe gráfico de dados históricos simulados"""
        # Gerar dados históricos simulados
        time_points = pd.date_range(start=datetime.now() - timedelta(hours=24), end=datetime.now(), freq='H')
        
        temp_data = [25 + 10 * np.sin(i * 2 * np.pi / 24) + random.uniform(-2, 2) for i in range(len(time_points))]
        hum_data = [60 + 15 * np.sin(i * 2 * np.pi / 24 + np.pi) + random.uniform(-5, 5) for i in range(len(time_points))]
        vib_data = [5 + 3 * abs(np.sin(i * 2 * np.pi / 12)) + random.uniform(-1, 1) for i in range(len(time_points))]
        
        fig_historical = make_subplots(
            rows=3, cols=1,
            subplot_titles=('Temperatura (°C)', 'Umidade (%)', 'Vibração (m/s²)'),
            vertical_spacing=0.08
        )
        
        fig_historical.add_trace(
            go.Scatter(x=time_points, y=temp_data, name='Temperatura', line=dict(color='red')),
            row=1, col=1
        )
        
        fig_historical.add_trace(
            go.Scatter(x=time_points, y=hum_data, name='Umidade', line=dict(color='blue')),
            row=2, col=1
        )
        
        fig_historical.add_trace(
            go.Scatter(x=time_points, y=vib_data, name='Vibração', line=dict(color='orange')),
            row=3, col=1
        )
        
        fig_historical.update_layout(
            height=600,
            showlegend=False,
            title_text="Tendências dos Sensores nas Últimas 24 Horas"
        )
        
        st.plotly_chart(fig_historical, use_container_width=True)
    
    def show_device_management(self):
        """Interface de gestão de dispositivos"""
        st.subheader("📱 Gestão de Dispositivos IoT")
        
        tab1, tab2, tab3 = st.tabs(["📋 Lista Dispositivos", "➕ Adicionar Dispositivo", "⚙️ Configurações"])
        
        with tab1:
            dispositivos = self.simular_dispositivos_iot()
            
            st.markdown("### 📡 Dispositivos Conectados")
            
            for device in dispositivos:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    
                    with col1:
                        status_icon = "🟢" if device['qualidade_sinal'] > 70 else "🟡" if device['qualidade_sinal'] > 40 else "🔴"
                        st.markdown(f"**{status_icon} {device['nome']}**")
                        st.caption(f"ID: {device['device_id']} | Local: {device['localizacao']}")
                    
                    with col2:
                        if 'valor_numerico' in device:
                            st.metric("Valor Atual", f"{device['valor_numerico']:.1f} {device['unidade']}")
                        else:
                            st.metric("Status", "Ativo")
                    
                    with col3:
                        st.metric("Bateria", f"{device['bateria']}%")
                        st.metric("Sinal", f"{device['qualidade_sinal']}%")
                    
                    with col4:
                        if st.button("⚙️", key=f"config_{device['device_id']}", help="Configurar dispositivo"):
                            st.session_state[f'configuring_{device["device_id"]}'] = True
                        
                        if st.button("📊", key=f"details_{device['device_id']}", help="Ver detalhes"):
                            self.show_device_details(device)
                    
                    st.divider()
        
        with tab2:
            self.show_add_device_form()
        
        with tab3:
            self.show_device_configurations()
    
    def show_add_device_form(self):
        """Formulário para adicionar novo dispositivo"""
        st.markdown("### ➕ Registrar Novo Dispositivo IoT")
        
        with st.form("add_device_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                device_id = st.text_input("Device ID *", placeholder="Exemplo: TEMP_007")
                nome_device = st.text_input("Nome do Dispositivo *", placeholder="Sensor Temperatura - Área X")
                tipo_device = st.selectbox("Tipo do Dispositivo", [
                    "sensor_temperatura", "sensor_umidade", "sensor_vibracao",
                    "rfid_reader", "gps_tracker", "medidor_energia",
                    "beacon_bluetooth", "camera_monitoring", "sensor_pressao"
                ])
            
            with col2:
                localizacao = st.text_input("Localização", placeholder="Obra Norte - Setor A")
                equipamento_associado = st.text_input("Equipamento Associado", placeholder="Código do equipamento")
                frequencia_leitura = st.number_input("Frequência de Leitura (segundos)", min_value=1, value=60)
            
            st.markdown("#### ⚙️ Configurações Avançadas")
            
            col3, col4 = st.columns(2)
            
            with col3:
                limites_config = st.text_area(
                    "Limites Operacionais (JSON)",
                    placeholder='{"min_valor": 0, "max_valor": 100, "alerta_bateria": 20}',
                    height=100
                )
            
            with col4:
                config_adicional = st.text_area(
                    "Configuração Adicional (JSON)",
                    placeholder='{"calibracao": 1.0, "offset": 0.0}',
                    height=100
                )
            
            submitted = st.form_submit_button("📱 Registrar Dispositivo", type="primary")
            
            if submitted:
                if device_id and nome_device:
                    self.register_new_device(device_id, nome_device, tipo_device, localizacao, 
                                           equipamento_associado, frequencia_leitura, 
                                           limites_config, config_adicional)
                else:
                    st.error("❌ Device ID e Nome são obrigatórios")
    
    def register_new_device(self, device_id: str, nome: str, tipo: str, localizacao: str,
                          equipamento: str, frequencia: int, limites: str, config: str):
        """Registra novo dispositivo no banco"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Validar JSONs
            limites_json = None
            config_json = None
            
            if limites:
                try:
                    limites_json = json.loads(limites)
                except json.JSONDecodeError:
                    st.error("❌ Formato JSON inválido nos limites operacionais")
                    return
            
            if config:
                try:
                    config_json = json.loads(config)
                except json.JSONDecodeError:
                    st.error("❌ Formato JSON inválido na configuração adicional")
                    return
            
            cursor.execute("""
            INSERT INTO dispositivos_iot 
            (device_id, nome, tipo_dispositivo, localizacao, equipamento_associado_codigo,
             configuracao_json, frequencia_leitura, limites_operacionais)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                device_id, nome, tipo, localizacao, equipamento,
                json.dumps(config_json) if config_json else None,
                frequencia,
                json.dumps(limites_json) if limites_json else None
            ])
            
            conn.commit()
            
            st.success(f"✅ Dispositivo {device_id} registrado com sucesso!")
            log_acao("iot", "device_register", f"Dispositivo {device_id} registrado")
            
        except Exception as e:
            st.error(f"❌ Erro ao registrar dispositivo: {e}")
    
    def show_device_configurations(self):
        """Interface de configurações de dispositivos"""
        st.markdown("### ⚙️ Configurações Globais IoT")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📡 Configurações de Conectividade")
            
            mqtt_broker = st.text_input("Broker MQTT", value="broker.hivemq.com")
            mqtt_port = st.number_input("Porta MQTT", value=1883)
            mqtt_username = st.text_input("Usuário MQTT")
            mqtt_password = st.text_input("Senha MQTT", type="password")
            
            if st.button("🔄 Reconectar MQTT"):
                st.info("🔄 Reconectando ao broker MQTT...")
                # Lógica de reconexão aqui
        
        with col2:
            st.markdown("#### ⚠️ Configurações de Alertas")
            
            alerta_bateria_baixa = st.slider("Alerta Bateria Baixa (%)", 0, 50, 20)
            alerta_sinal_fraco = st.slider("Alerta Sinal Fraco (%)", 0, 100, 30)
            timeout_dispositivo = st.number_input("Timeout Dispositivo (minutos)", value=15)
            
            email_alertas = st.text_input("Email para Alertas", placeholder="admin@empresa.com")
    
    def show_device_details(self, device: Dict):
        """Exibe detalhes específicos de um dispositivo"""
        with st.expander(f"📊 Detalhes: {device['nome']}", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**📋 Informações Básicas**")
                st.write(f"**ID:** {device['device_id']}")
                st.write(f"**Tipo:** {device['tipo_dispositivo']}")
                st.write(f"**Local:** {device['localizacao']}")
            
            with col2:
                st.markdown("**📊 Status Atual**")
                st.write(f"**Bateria:** {device['bateria']}%")
                st.write(f"**Sinal:** {device['qualidade_sinal']}%")
                if 'valor_numerico' in device:
                    st.write(f"**Valor:** {device['valor_numerico']:.1f} {device['unidade']}")
            
            with col3:
                st.markdown("**🔧 Ações Disponíveis**")
                
                if st.button(f"📤 Comando Remoto", key=f"cmd_{device['device_id']}"):
                    self.show_remote_command_interface(device['device_id'])
                
                if st.button(f"📈 Histórico Detalhado", key=f"hist_{device['device_id']}"):
                    self.show_device_history(device['device_id'])
                
                if st.button(f"🔧 Configurar", key=f"cfg_{device['device_id']}"):
                    self.show_device_specific_config(device)
    
    def show_remote_command_interface(self, device_id: str):
        """Interface para envio de comandos remotos"""
        st.markdown(f"### 📤 Comando Remoto - {device_id}")
        
        comando_predefinido = st.selectbox(
            "Comando Predefinido",
            ["", "restart", "calibrate", "sleep", "wakeup", "reset_config", "update_firmware"]
        )
        
        comando_customizado = st.text_input("Comando Personalizado")
        parametros = st.text_area("Parâmetros (JSON)", placeholder='{"duration": 60, "mode": "low_power"}')
        
        if st.button("📤 Enviar Comando"):
            comando_final = comando_predefinido or comando_customizado
            if comando_final:
                self.send_remote_command(device_id, comando_final, parametros)
            else:
                st.error("❌ Selecione ou digite um comando")
    
    def send_remote_command(self, device_id: str, comando: str, parametros: str):
        """Envia comando remoto para dispositivo"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Validar parâmetros JSON se fornecidos
            parametros_json = None
            if parametros:
                try:
                    parametros_json = json.loads(parametros)
                except json.JSONDecodeError:
                    st.error("❌ Formato JSON inválido nos parâmetros")
                    return
            
            # Registrar comando
            cursor.execute("""
            INSERT INTO comandos_remotos (device_id, comando, parametros, enviado_por)
            VALUES (%s, %s, %s, %s)
            """, [device_id, comando, json.dumps(parametros_json) if parametros_json else None, 1])
            
            conn.commit()
            
            # Simular envio MQTT
            if self.mqtt_client:
                topic = f"inventario/{device_id}/comandos"
                payload = {
                    'comando': comando,
                    'parametros': parametros_json,
                    'timestamp': datetime.now().isoformat()
                }
                
                # self.mqtt_client.publish(topic, json.dumps(payload))
            
            st.success(f"✅ Comando '{comando}' enviado para {device_id}")
            log_acao("iot", "remote_command", f"Comando {comando} enviado para {device_id}")
            
        except Exception as e:
            st.error(f"❌ Erro ao enviar comando: {e}")
    
    def show_alerts_management(self):
        """Interface de gestão de alertas IoT"""
        st.subheader("⚠️ Gestão de Alertas IoT")
        
        tab1, tab2, tab3 = st.tabs(["🚨 Alertas Ativos", "📋 Histórico", "⚙️ Regras"])
        
        with tab1:
            self.show_active_alerts()
        
        with tab2:
            self.show_alerts_history()
        
        with tab3:
            self.show_monitoring_rules()
    
    def show_active_alerts(self):
        """Exibe alertas ativos"""
        st.markdown("### 🚨 Alertas Ativos do Sistema")
        
        # Simular alguns alertas ativos
        alertas_simulados = [
            {
                'id': 1,
                'device_id': 'TEMP_001',
                'tipo_alerta': 'temperatura_alta',
                'severidade': 'alto',
                'titulo': 'Temperatura Crítica Detectada',
                'descricao': 'Sensor registrou temperatura de 89°C no gerador principal',
                'valor_detectado': '89.3°C',
                'timestamp_alerta': datetime.now() - timedelta(minutes=15)
            },
            {
                'id': 2,
                'device_id': 'VIB_003',
                'tipo_alerta': 'vibracao_anomala',
                'severidade': 'medio',
                'titulo': 'Vibração Anômala Detectada',
                'descricao': 'Padrão de vibração irregular no compressor',
                'valor_detectado': '12.8 m/s²',
                'timestamp_alerta': datetime.now() - timedelta(hours=2)
            },
            {
                'id': 3,
                'device_id': 'HUM_002',
                'tipo_alerta': 'bateria_baixa',
                'severidade': 'baixo',
                'titulo': 'Bateria Baixa',
                'descricao': 'Nível de bateria abaixo do limite configurado',
                'valor_detectado': '18%',
                'timestamp_alerta': datetime.now() - timedelta(hours=5)
            }
        ]
        
        for alerta in alertas_simulados:
            severidade_color = {
                'critico': '#dc2626',
                'alto': '#f59e0b', 
                'medio': '#3b82f6',
                'baixo': '#10b981'
            }
            
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 4, 2, 1])
                
                with col1:
                    st.markdown(f"""
                    <div style="background: {severidade_color[alerta['severidade']]}; 
                                color: white; padding: 0.5rem; border-radius: 5px; 
                                text-align: center; font-weight: bold;">
                        {alerta['severidade'].upper()}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"**{alerta['titulo']}**")
                    st.caption(f"Dispositivo: {alerta['device_id']} | Valor: {alerta['valor_detectado']}")
                    st.caption(f"{alerta['descricao']}")
                
                with col3:
                    tempo_decorrido = datetime.now() - alerta['timestamp_alerta']
                    horas = int(tempo_decorrido.total_seconds() // 3600)
                    minutos = int((tempo_decorrido.total_seconds() % 3600) // 60)
                    
                    if horas > 0:
                        st.caption(f"⏰ {horas}h {minutos}m atrás")
                    else:
                        st.caption(f"⏰ {minutos}m atrás")
                
                with col4:
                    if st.button("✅", key=f"ack_{alerta['id']}", help="Reconhecer"):
                        st.success("Alerta reconhecido!")
                    
                    if st.button("❌", key=f"dismiss_{alerta['id']}", help="Descartar"):
                        st.info("Alerta descartado")
                
                st.divider()
    
    def show_monitoring_rules(self):
        """Interface de configuração de regras de monitoramento"""
        st.markdown("### ⚙️ Regras de Monitoramento")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### 📋 Regras Ativas")
            
            # Exibir regras existentes simuladas
            regras_simuladas = [
                {
                    'nome_regra': 'Temperatura Crítica',
                    'condicao_sql': 'valor_numerico > 80',
                    'tipo_alerta': 'temperatura_alta',
                    'severidade': 'alto',
                    'acao_automatica': 'email',
                    'ativo': True
                },
                {
                    'nome_regra': 'Bateria Baixa',
                    'condicao_sql': 'bateria < 20',
                    'tipo_alerta': 'bateria_baixa',
                    'severidade': 'medio',
                    'acao_automatica': 'webhook',
                    'ativo': True
                },
                {
                    'nome_regra': 'Sinal Fraco',
                    'condicao_sql': 'qualidade_sinal < 30',
                    'tipo_alerta': 'sinal_fraco',
                    'severidade': 'baixo',
                    'acao_automatica': None,
                    'ativo': False
                }
            ]
            
            for i, regra in enumerate(regras_simuladas):
                with st.expander(f"📏 {regra['nome_regra']}", expanded=False):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.write(f"**Condição:** `{regra['condicao_sql']}`")
                        st.write(f"**Severidade:** {regra['severidade']}")
                        st.write(f"**Status:** {'✅ Ativa' if regra['ativo'] else '⏸️ Inativa'}")
                    
                    with col_b:
                        st.write(f"**Tipo Alerta:** {regra['tipo_alerta']}")
                        st.write(f"**Ação:** {regra['acao_automatica'] or 'Nenhuma'}")
                        
                        if st.button(f"{'⏸️ Desativar' if regra['ativo'] else '▶️ Ativar'}", 
                                   key=f"toggle_rule_{i}"):
                            st.rerun()
        
        with col2:
            st.markdown("#### ➕ Nova Regra")
            
            with st.form("nova_regra"):
                nome_regra = st.text_input("Nome da Regra")
                
                dispositivo_target = st.selectbox("Dispositivo", ["Todos", "TEMP_001", "HUM_002", "VIB_003"])
                
                tipo_condicao = st.selectbox("Tipo de Condição", [
                    "valor_numerico > X",
                    "valor_numerico < X", 
                    "bateria < X",
                    "qualidade_sinal < X"
                ])
                
                valor_limite = st.number_input("Valor Limite", value=50.0)
                
                severidade = st.selectbox("Severidade", ["baixo", "medio", "alto", "critico"])
                
                acao_auto = st.selectbox("Ação Automática", ["Nenhuma", "email", "webhook", "comando_remoto"])
                
                submitted = st.form_submit_button("➕ Criar Regra")
                
                if submitted and nome_regra:
                    condicao_sql = tipo_condicao.replace("X", str(valor_limite))
                    st.success(f"✅ Regra '{nome_regra}' criada com sucesso!")
                    log_acao("iot", "rule_create", f"Regra {nome_regra} criada")

def show_iot_page():
    """Página principal do sistema IoT"""
    st.set_page_config(
        page_title="🌐 IoT e Sensores", 
        page_icon="🌐",
        layout="wide"
    )
    
    iot_manager = IoTManager()
    
    st.title("🌐 Sistema IoT e Sensores")
    
    # Menu lateral
    menu_iot = st.sidebar.selectbox(
        "📂 Menu IoT",
        ["🏠 Dashboard", "📱 Dispositivos", "⚠️ Alertas", "📊 Analytics", "⚙️ Configurações"]
    )
    
    if menu_iot == "🏠 Dashboard":
        iot_manager.show_iot_dashboard()
    
    elif menu_iot == "📱 Dispositivos":
        iot_manager.show_device_management()
    
    elif menu_iot == "⚠️ Alertas":
        iot_manager.show_alerts_management()
    
    elif menu_iot == "📊 Analytics":
        st.subheader("📊 Analytics IoT")
        
        # Aqui seria integrado com módulo de analytics avançado
        st.info("🚧 Analytics avançado em desenvolvimento")
        
        # Preview de analytics
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📈 Tendências")
            st.line_chart(pd.DataFrame({
                'Temperatura': np.random.randn(100).cumsum(),
                'Umidade': np.random.randn(100).cumsum(),
                'Vibração': np.random.randn(100).cumsum()
            }))
        
        with col2:
            st.markdown("#### 🔋 Eficiência Energética")
            st.bar_chart(pd.DataFrame({
                'Consumo kWh': [120, 98, 145, 132, 89, 167, 143]
            }, index=['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dom']))
    
    elif menu_iot == "⚙️ Configurações":
        st.subheader("⚙️ Configurações do Sistema IoT")
        
        tab1, tab2, tab3 = st.tabs(["🔧 Geral", "🌐 Conectividade", "📧 Notificações"])
        
        with tab1:
            st.markdown("#### 🔧 Configurações Gerais")
            
            auto_discovery = st.checkbox("Auto-descoberta de dispositivos", value=True)
            data_retention = st.slider("Retenção de dados (dias)", 7, 365, 90)
            backup_frequency = st.selectbox("Frequência de backup", ["Diário", "Semanal", "Mensal"])
        
        with tab2:
            st.markdown("#### 🌐 Configurações de Conectividade")
            iot_manager.show_device_configurations()
        
        with tab3:
            st.markdown("#### 📧 Configurações de Notificações")
            
            email_enabled = st.checkbox("Ativar notificações por email", value=True)
            webhook_enabled = st.checkbox("Ativar webhooks", value=False)
            
            if email_enabled:
                smtp_server = st.text_input("Servidor SMTP", value="smtp.gmail.com")
                smtp_port = st.number_input("Porta SMTP", value=587)
                smtp_user = st.text_input("Usuário SMTP")
                smtp_password = st.text_input("Senha SMTP", type="password")

if __name__ == "__main__":
    show_iot_page()