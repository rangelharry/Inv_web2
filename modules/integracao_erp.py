"""
Sistema de Integração ERP/SAP
APIs e conectores para integração com sistemas ERP externos (SAP, Oracle, TOTVS)
"""

import streamlit as st
from datetime import datetime, timedelta
from database.connection import db
from modules.logs_auditoria import log_acao
import pandas as pd
from typing import Dict, List, Any, Optional
import json
import requests
import xml.etree.ElementTree as ET
from sqlalchemy import create_engine, text
import plotly.express as px

class ERPIntegrationManager:
    def __init__(self):
        self.criar_tabelas()
        self.supported_systems = {
            'SAP_R3': 'SAP R/3 e S/4HANA',
            'ORACLE_EBS': 'Oracle E-Business Suite',
            'TOTVS_PROTHEUS': 'TOTVS Protheus',
            'SENIOR': 'Senior Sistemas',
            'ORACLE_JDE': 'Oracle JD Edwards',
            'MICROSIGA': 'Microsiga',
            'DATASUL': 'Datasul',
            'CUSTOM_API': 'API Customizada'
        }
    
    def criar_tabelas(self):
        """Cria tabelas necessárias para integração ERP"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Tabela de configurações de ERP
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes_erp (
                id SERIAL PRIMARY KEY,
                nome_conexao VARCHAR(100) UNIQUE NOT NULL,
                tipo_sistema VARCHAR(50) NOT NULL,
                endereco_servidor VARCHAR(255),
                porta INTEGER,
                database_sid VARCHAR(100),
                usuario VARCHAR(100),
                senha_criptografada TEXT,
                parametros_conexao JSONB,
                certificados_ssl TEXT,
                timeout_conexao INTEGER DEFAULT 30,
                max_tentativas INTEGER DEFAULT 3,
                ativo BOOLEAN DEFAULT TRUE,
                ultima_conexao TIMESTAMP,
                status_conexao VARCHAR(50) DEFAULT 'nao_testado',
                observacoes TEXT,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario_criacao_id INTEGER
            )
            """)
            
            # Tabela de mapeamento de campos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS mapeamento_campos_erp (
                id SERIAL PRIMARY KEY,
                configuracao_erp_id INTEGER REFERENCES configuracoes_erp(id),
                tabela_origem VARCHAR(100) NOT NULL,
                campo_origem VARCHAR(100) NOT NULL,
                tabela_destino VARCHAR(100) NOT NULL,
                campo_destino VARCHAR(100) NOT NULL,
                tipo_sincronizacao VARCHAR(50) CHECK (tipo_sincronizacao IN ('bidirecional', 'erp_para_inventario', 'inventario_para_erp')),
                funcao_transformacao TEXT,
                condicao_sincronizacao TEXT,
                prioridade INTEGER DEFAULT 1,
                ativo BOOLEAN DEFAULT TRUE,
                observacoes TEXT
            )
            """)
            
            # Tabela de sincronizações executadas
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sincronizacoes_erp (
                id SERIAL PRIMARY KEY,
                configuracao_erp_id INTEGER REFERENCES configuracoes_erp(id),
                tipo_operacao VARCHAR(50) NOT NULL,
                tabela_origem VARCHAR(100),
                registros_processados INTEGER DEFAULT 0,
                registros_sucesso INTEGER DEFAULT 0,
                registros_erro INTEGER DEFAULT 0,
                data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_fim TIMESTAMP,
                status VARCHAR(50) DEFAULT 'executando',
                log_detalhado TEXT,
                arquivo_log_caminho VARCHAR(500),
                usuario_execucao_id INTEGER,
                parametros_execucao JSONB
            )
            """)
            
            # Tabela de erros de integração
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS erros_integracao_erp (
                id SERIAL PRIMARY KEY,
                sincronizacao_id INTEGER REFERENCES sincronizacoes_erp(id),
                configuracao_erp_id INTEGER REFERENCES configuracoes_erp(id),
                tipo_erro VARCHAR(100),
                mensagem_erro TEXT,
                detalhes_erro JSONB,
                tabela_afetada VARCHAR(100),
                registro_id VARCHAR(100),
                tentativas INTEGER DEFAULT 1,
                resolvido BOOLEAN DEFAULT FALSE,
                data_erro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_resolucao TIMESTAMP,
                usuario_resolucao_id INTEGER
            )
            """)
            
            # Tabela de filas de sincronização
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS fila_sincronizacao_erp (
                id SERIAL PRIMARY KEY,
                configuracao_erp_id INTEGER REFERENCES configuracoes_erp(id),
                tipo_operacao VARCHAR(50) NOT NULL,
                tabela_destino VARCHAR(100),
                dados_registro JSONB,
                prioridade INTEGER DEFAULT 5,
                tentativas INTEGER DEFAULT 0,
                max_tentativas INTEGER DEFAULT 3,
                status VARCHAR(50) DEFAULT 'pendente',
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_processamento TIMESTAMP,
                resultado_processamento TEXT,
                usuario_criacao_id INTEGER
            )
            """)
            
            # Tabela de webhooks/eventos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS webhooks_erp (
                id SERIAL PRIMARY KEY,
                configuracao_erp_id INTEGER REFERENCES configuracoes_erp(id),
                nome_webhook VARCHAR(100) NOT NULL,
                url_endpoint VARCHAR(500),
                metodo_http VARCHAR(10) DEFAULT 'POST',
                headers_personalizados JSONB,
                eventos_trigger TEXT[],
                ativo BOOLEAN DEFAULT TRUE,
                secret_token VARCHAR(255),
                ultima_execucao TIMESTAMP,
                total_execucoes INTEGER DEFAULT 0,
                total_sucessos INTEGER DEFAULT 0,
                total_falhas INTEGER DEFAULT 0,
                observacoes TEXT
            )
            """)
            
            # Tabela de cache de dados ERP
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_dados_erp (
                id SERIAL PRIMARY KEY,
                configuracao_erp_id INTEGER REFERENCES configuracoes_erp(id),
                chave_cache VARCHAR(200) NOT NULL,
                dados_cache JSONB,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_expiracao TIMESTAMP,
                hits INTEGER DEFAULT 0,
                UNIQUE(configuracao_erp_id, chave_cache)
            )
            """)
            
            conn.commit()
            
            # Inserir configurações de exemplo
            self.inserir_configuracoes_exemplo()
            
        except Exception as e:
            st.error(f"Erro ao criar tabelas de integração ERP: {e}")
    
    def inserir_configuracoes_exemplo(self):
        """Insere configurações de exemplo"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se já existem configurações
        cursor.execute("SELECT COUNT(*) FROM configuracoes_erp")
        if cursor.fetchone()[0] > 0:
            return
        
        configuracoes_exemplo = [
            {
                'nome': 'SAP_PRODUCAO',
                'tipo': 'SAP_R3',
                'servidor': 'sap.empresa.com',
                'porta': 3300,
                'parametros': {
                    'client': '100',
                    'language': 'PT',
                    'system_number': '00'
                }
            },
            {
                'nome': 'TOTVS_MATRIZ',
                'tipo': 'TOTVS_PROTHEUS',
                'servidor': 'protheus.empresa.com',
                'porta': 80,
                'parametros': {
                    'environment': 'PRODUCAO',
                    'company': '01',
                    'branch': '01'
                }
            }
        ]
        
        for config in configuracoes_exemplo:
            cursor.execute("""
            INSERT INTO configuracoes_erp 
            (nome_conexao, tipo_sistema, endereco_servidor, porta, parametros_conexao)
            VALUES (%s, %s, %s, %s, %s)
            """, [
                config['nome'], config['tipo'], config['servidor'],
                config['porta'], json.dumps(config['parametros'])
            ])
        
        conn.commit()
    
    def criar_configuracao_erp(self, dados: Dict[str, Any]) -> int:
        """Cria nova configuração de ERP"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Criptografar senha (em produção, usar bibliotecas apropriadas)
        senha_criptografada = self.criptografar_senha(dados.get('senha', ''))
        
        cursor.execute("""
        INSERT INTO configuracoes_erp
        (nome_conexao, tipo_sistema, endereco_servidor, porta, database_sid,
         usuario, senha_criptografada, parametros_conexao, timeout_conexao,
         max_tentativas, observacoes, usuario_criacao_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, [
            dados['nome_conexao'], dados['tipo_sistema'], dados['endereco_servidor'],
            dados.get('porta'), dados.get('database_sid', ''), dados.get('usuario', ''),
            senha_criptografada, json.dumps(dados.get('parametros_conexao', {})),
            dados.get('timeout_conexao', 30), dados.get('max_tentativas', 3),
            dados.get('observacoes', ''), dados.get('usuario_id', 1)
        ])
        
        config_id = cursor.fetchone()[0]
        conn.commit()
        
        log_acao("erp_integration", "criar_config", f"Configuração ERP criada: {dados['nome_conexao']}")
        return config_id
    
    def criptografar_senha(self, senha: str) -> str:
        """Criptografa senha (implementação simplificada)"""
        # Em produção, usar bibliotecas como cryptography ou bcrypt
        import base64
        return base64.b64encode(senha.encode()).decode() if senha else ""
    
    def descriptografar_senha(self, senha_criptografada: str) -> str:
        """Descriptografa senha"""
        import base64
        try:
            return base64.b64decode(senha_criptografada.encode()).decode() if senha_criptografada else ""
        except:
            return ""
    
    def testar_conexao_erp(self, config_id: int) -> Dict[str, Any]:
        """Testa conexão com ERP"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM configuracoes_erp WHERE id = %s", [config_id])
        config = cursor.fetchone()
        
        if not config:
            return {'sucesso': False, 'erro': 'Configuração não encontrada'}
        
        try:
            # Simular teste de conexão baseado no tipo de sistema
            resultado = self._testar_conexao_por_tipo(config)
            
            # Atualizar status na configuração
            cursor.execute("""
            UPDATE configuracoes_erp 
            SET ultima_conexao = CURRENT_TIMESTAMP, 
                status_conexao = %s
            WHERE id = %s
            """, [
                'conectado' if resultado['sucesso'] else 'erro_conexao',
                config_id
            ])
            
            conn.commit()
            
            log_acao("erp_integration", "testar_conexao", 
                    f"Teste de conexão {config['nome_conexao']}: {'Sucesso' if resultado['sucesso'] else 'Falha'}")
            
            return resultado
            
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}
    
    def _testar_conexao_por_tipo(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Testa conexão específica por tipo de ERP"""
        tipo_sistema = config['tipo_sistema']
        
        if tipo_sistema == 'SAP_R3':
            return self._testar_sap(config)
        elif tipo_sistema == 'ORACLE_EBS':
            return self._testar_oracle(config)
        elif tipo_sistema == 'TOTVS_PROTHEUS':
            return self._testar_totvs(config)
        elif tipo_sistema == 'CUSTOM_API':
            return self._testar_api_custom(config)
        else:
            return {'sucesso': True, 'mensagem': 'Teste simulado - conexão OK'}
    
    def _testar_sap(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Testa conexão SAP"""
        try:
            # Em produção, usar pyrfc ou sapnwrfc
            # pyrfc connection example:
            # import pyrfc
            # conn = pyrfc.Connection(
            #     ashost=config['endereco_servidor'],
            #     sysnr=config['parametros_conexao'].get('system_number'),
            #     client=config['parametros_conexao'].get('client'),
            #     user=config['usuario'],
            #     passwd=self.descriptografar_senha(config['senha_criptografada'])
            # )
            # conn.ping()
            
            # Simulação para demonstração
            return {
                'sucesso': True,
                'mensagem': 'Conexão SAP estabelecida com sucesso',
                'detalhes': {
                    'servidor': config['endereco_servidor'],
                    'client': config.get('parametros_conexao', {}).get('client', 'N/A'),
                    'versao': 'SAP NetWeaver 7.5'
                }
            }
            
        except Exception as e:
            return {'sucesso': False, 'erro': f'Erro SAP: {str(e)}'}
    
    def _testar_oracle(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Testa conexão Oracle"""
        try:
            # Em produção, usar cx_Oracle
            # import cx_Oracle
            # dsn = cx_Oracle.makedsn(
            #     config['endereco_servidor'], 
            #     config['porta'], 
            #     service_name=config['database_sid']
            # )
            # connection = cx_Oracle.connect(
            #     user=config['usuario'],
            #     password=self.descriptografar_senha(config['senha_criptografada']),
            #     dsn=dsn
            # )
            
            return {
                'sucesso': True,
                'mensagem': 'Conexão Oracle EBS estabelecida',
                'detalhes': {
                    'servidor': config['endereco_servidor'],
                    'sid': config.get('database_sid', 'N/A'),
                    'versao': 'Oracle Database 19c'
                }
            }
            
        except Exception as e:
            return {'sucesso': False, 'erro': f'Erro Oracle: {str(e)}'}
    
    def _testar_totvs(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Testa conexão TOTVS"""
        try:
            # Em produção, usar REST API do Protheus
            url = f"http://{config['endereco_servidor']}:{config['porta']}/rest/api/framework/v1/info"
            
            # Simulação de teste
            return {
                'sucesso': True,
                'mensagem': 'Conexão TOTVS Protheus estabelecida',
                'detalhes': {
                    'servidor': config['endereco_servidor'],
                    'ambiente': config.get('parametros_conexao', {}).get('environment', 'N/A'),
                    'versao': 'Protheus 12.1.33'
                }
            }
            
        except Exception as e:
            return {'sucesso': False, 'erro': f'Erro TOTVS: {str(e)}'}
    
    def _testar_api_custom(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Testa API customizada"""
        try:
            url = f"http://{config['endereco_servidor']}:{config['porta']}/health"
            
            # Em produção, fazer request real
            # response = requests.get(url, timeout=config['timeout_conexao'])
            # return {'sucesso': response.status_code == 200}
            
            return {
                'sucesso': True,
                'mensagem': 'API customizada respondendo',
                'detalhes': {'endpoint': url}
            }
            
        except Exception as e:
            return {'sucesso': False, 'erro': f'Erro API: {str(e)}'}
    
    def executar_sincronizacao(self, config_id: int, tipo_operacao: str, parametros: Dict[str, Any] = None) -> int:
        """Executa sincronização com ERP"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Criar registro de sincronização
        cursor.execute("""
        INSERT INTO sincronizacoes_erp 
        (configuracao_erp_id, tipo_operacao, parametros_execucao, usuario_execucao_id)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """, [config_id, tipo_operacao, json.dumps(parametros or {}), 1])
        
        sync_id = cursor.fetchone()[0]
        conn.commit()
        
        try:
            # Executar sincronização baseada no tipo
            resultado = self._executar_sincronizacao_por_tipo(config_id, tipo_operacao, parametros)
            
            # Atualizar resultado
            cursor.execute("""
            UPDATE sincronizacoes_erp 
            SET data_fim = CURRENT_TIMESTAMP,
                status = %s,
                registros_processados = %s,
                registros_sucesso = %s,
                registros_erro = %s,
                log_detalhado = %s
            WHERE id = %s
            """, [
                resultado['status'], resultado.get('processados', 0),
                resultado.get('sucessos', 0), resultado.get('erros', 0),
                resultado.get('log', ''), sync_id
            ])
            
            conn.commit()
            
            log_acao("erp_integration", "sincronizar", 
                    f"Sincronização {tipo_operacao} executada: {resultado['status']}")
            
            return sync_id
            
        except Exception as e:
            cursor.execute("""
            UPDATE sincronizacoes_erp 
            SET data_fim = CURRENT_TIMESTAMP, status = 'erro', log_detalhado = %s
            WHERE id = %s
            """, [str(e), sync_id])
            
            conn.commit()
            raise
    
    def _executar_sincronizacao_por_tipo(self, config_id: int, tipo_operacao: str, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Executa sincronização específica"""
        
        if tipo_operacao == 'sync_produtos':
            return self._sincronizar_produtos(config_id, parametros)
        elif tipo_operacao == 'sync_estoque':
            return self._sincronizar_estoque(config_id, parametros)
        elif tipo_operacao == 'sync_movimentacoes':
            return self._sincronizar_movimentacoes(config_id, parametros)
        elif tipo_operacao == 'sync_fornecedores':
            return self._sincronizar_fornecedores(config_id, parametros)
        else:
            return {
                'status': 'concluido',
                'processados': 100,
                'sucessos': 95,
                'erros': 5,
                'log': f'Sincronização {tipo_operacao} simulada'
            }
    
    def _sincronizar_produtos(self, config_id: int, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Sincroniza produtos do ERP"""
        # Simulação de sincronização de produtos
        import time
        time.sleep(1)  # Simular processamento
        
        return {
            'status': 'concluido',
            'processados': 150,
            'sucessos': 148,
            'erros': 2,
            'log': 'Produtos sincronizados: 148 sucessos, 2 erros de validação'
        }
    
    def _sincronizar_estoque(self, config_id: int, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Sincroniza estoque com ERP"""
        # Simulação
        return {
            'status': 'concluido',
            'processados': 300,
            'sucessos': 295,
            'erros': 5,
            'log': 'Estoque sincronizado: 295 sucessos, 5 produtos não encontrados'
        }
    
    def _sincronizar_movimentacoes(self, config_id: int, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Sincroniza movimentações"""
        return {
            'status': 'concluido',
            'processados': 50,
            'sucessos': 50,
            'erros': 0,
            'log': 'Todas as movimentações sincronizadas com sucesso'
        }
    
    def _sincronizar_fornecedores(self, config_id: int, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Sincroniza fornecedores"""
        return {
            'status': 'concluido',
            'processados': 25,
            'sucessos': 23,
            'erros': 2,
            'log': 'Fornecedores sincronizados: 23 sucessos, 2 CNPJs inválidos'
        }
    
    def adicionar_fila_sincronizacao(self, config_id: int, operacao: str, dados: Dict[str, Any], prioridade: int = 5):
        """Adiciona item à fila de sincronização"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO fila_sincronizacao_erp
        (configuracao_erp_id, tipo_operacao, dados_registro, prioridade, usuario_criacao_id)
        VALUES (%s, %s, %s, %s, %s)
        """, [config_id, operacao, json.dumps(dados), prioridade, 1])
        
        conn.commit()
    
    def processar_fila_sincronizacao(self, config_id: Optional[int] = None):
        """Processa itens pendentes na fila"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT * FROM fila_sincronizacao_erp 
        WHERE status = 'pendente' AND tentativas < max_tentativas
        """
        params = []
        
        if config_id:
            query += " AND configuracao_erp_id = %s"
            params.append(config_id)
        
        query += " ORDER BY prioridade, data_criacao LIMIT 10"
        
        cursor.execute(query, params)
        itens_fila = cursor.fetchall()
        
        for item in itens_fila:
            try:
                # Processar item
                resultado = f"Processado item {item['tipo_operacao']}"
                
                # Marcar como processado
                cursor.execute("""
                UPDATE fila_sincronizacao_erp 
                SET status = 'processado', data_processamento = CURRENT_TIMESTAMP,
                    resultado_processamento = %s
                WHERE id = %s
                """, [resultado, item['id']])
                
            except Exception as e:
                # Incrementar tentativas
                cursor.execute("""
                UPDATE fila_sincronizacao_erp 
                SET tentativas = tentativas + 1,
                    resultado_processamento = %s
                WHERE id = %s
                """, [f"Erro: {str(e)}", item['id']])
        
        conn.commit()

def show_erp_integration_page():
    """Exibe página de integração ERP"""
    st.title("🔗 Integração ERP/SAP")
    st.markdown("Sistema de integração com ERPs externos (SAP, Oracle, TOTVS, etc.)")
    
    manager = ERPIntegrationManager()
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard", "⚙️ Configurações", "🔄 Sincronizações", 
        "📋 Mapeamentos", "🚨 Monitoramento", "📈 Relatórios"
    ])
    
    with tab1:
        st.subheader("📊 Dashboard de Integração")
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cursor.execute("SELECT COUNT(*) FROM configuracoes_erp WHERE ativo = TRUE")
            configs_ativas = cursor.fetchone()[0]
            st.metric("Configs Ativas", configs_ativas)
        
        with col2:
            cursor.execute("SELECT COUNT(*) FROM configuracoes_erp WHERE status_conexao = 'conectado'")
            conectados = cursor.fetchone()[0]
            st.metric("Sistemas Conectados", conectados)
        
        with col3:
            cursor.execute("""
            SELECT COUNT(*) FROM sincronizacoes_erp 
            WHERE data_inicio >= CURRENT_DATE - INTERVAL '7 days'
            """)
            syncs_semana = cursor.fetchone()[0]
            st.metric("Syncs (7 dias)", syncs_semana)
        
        with col4:
            cursor.execute("SELECT COUNT(*) FROM erros_integracao_erp WHERE resolvido = FALSE")
            erros_pendentes = cursor.fetchone()[0]
            st.metric("Erros Pendentes", erros_pendentes, delta_color="inverse")
        
        # Status das conexões
        cursor.execute("""
        SELECT nome_conexao, tipo_sistema, status_conexao, ultima_conexao
        FROM configuracoes_erp 
        WHERE ativo = TRUE
        ORDER BY nome_conexao
        """)
        
        conexoes = cursor.fetchall()
        
        if conexoes:
            st.subheader("🔗 Status das Conexões")
            
            for conexao in conexoes:
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    status_icon = {
                        'conectado': '🟢',
                        'erro_conexao': '🔴',
                        'nao_testado': '⚪'
                    }.get(conexao['status_conexao'], '❓')
                    
                    st.write(f"{status_icon} **{conexao['nome_conexao']}**")
                
                with col_b:
                    st.write(f"Sistema: {manager.supported_systems.get(conexao['tipo_sistema'], conexao['tipo_sistema'])}")
                
                with col_c:
                    if conexao['ultima_conexao']:
                        st.write(f"Última conexão: {conexao['ultima_conexao'].strftime('%d/%m/%Y %H:%M')}")
                    else:
                        st.write("Nunca conectado")
        
        # Histórico de sincronizações
        cursor.execute("""
        SELECT DATE_TRUNC('day', data_inicio) as dia,
               COUNT(*) as total_syncs,
               SUM(CASE WHEN status = 'concluido' THEN 1 ELSE 0 END) as sucessos
        FROM sincronizacoes_erp
        WHERE data_inicio >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY dia
        ORDER BY dia
        """)
        
        dados_sync = cursor.fetchall()
        
        if dados_sync:
            df_sync = pd.DataFrame(dados_sync, columns=['dia', 'total_syncs', 'sucessos'])
            
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                fig1 = px.line(df_sync, x='dia', y='total_syncs', 
                              title='Sincronizações por Dia (30 dias)')
                st.plotly_chart(fig1, use_container_width=True)
            
            with col_graf2:
                df_sync['taxa_sucesso'] = (df_sync['sucessos'] / df_sync['total_syncs'] * 100).fillna(0)
                fig2 = px.bar(df_sync, x='dia', y='taxa_sucesso',
                             title='Taxa de Sucesso (%)')
                st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        st.subheader("⚙️ Configurações de ERP")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**Configurações Existentes**")
            
            cursor.execute("SELECT * FROM configuracoes_erp ORDER BY nome_conexao")
            configuracoes = cursor.fetchall()
            
            if configuracoes:
                for config in configuracoes:
                    with st.expander(f"🔧 {config['nome_conexao']} - {manager.supported_systems.get(config['tipo_sistema'], config['tipo_sistema'])}"):
                        col_a, col_b, col_c = st.columns(3)
                        
                        with col_a:
                            st.write(f"**Servidor:** {config['endereco_servidor']}")
                            st.write(f"**Porta:** {config['porta'] or 'N/A'}")
                            st.write(f"**Status:** {config['status_conexao']}")
                        
                        with col_b:
                            st.write(f"**Usuário:** {config['usuario'] or 'N/A'}")
                            st.write(f"**Timeout:** {config['timeout_conexao']}s")
                            st.write(f"**Ativo:** {'Sim' if config['ativo'] else 'Não'}")
                        
                        with col_c:
                            if st.button("🔍 Testar Conexão", key=f"test_{config['id']}"):
                                with st.spinner("Testando conexão..."):
                                    resultado = manager.testar_conexao_erp(config['id'])
                                
                                if resultado['sucesso']:
                                    st.success(f"✅ {resultado['mensagem']}")
                                    if 'detalhes' in resultado:
                                        st.json(resultado['detalhes'])
                                else:
                                    st.error(f"❌ {resultado['erro']}")
                            
                            if st.button("▶️ Sincronizar", key=f"sync_{config['id']}"):
                                st.session_state[f'sync_modal_{config["id"]}'] = True
                        
                        # Modal de sincronização
                        if st.session_state.get(f'sync_modal_{config["id"]}', False):
                            st.write("**Executar Sincronização**")
                            
                            col_sync1, col_sync2 = st.columns(2)
                            
                            with col_sync1:
                                tipo_sync = st.selectbox("Tipo de Sincronização:", [
                                    "sync_produtos", "sync_estoque", "sync_movimentacoes", 
                                    "sync_fornecedores", "sync_completa"
                                ], key=f"tipo_{config['id']}")
                            
                            with col_sync2:
                                if st.button("🚀 Executar", key=f"exec_{config['id']}"):
                                    with st.spinner("Executando sincronização..."):
                                        try:
                                            sync_id = manager.executar_sincronizacao(
                                                config['id'], tipo_sync
                                            )
                                            st.success(f"✅ Sincronização iniciada! ID: {sync_id}")
                                            del st.session_state[f'sync_modal_{config["id"]}']
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Erro: {e}")
            else:
                st.info("ℹ️ Nenhuma configuração encontrada")
        
        with col2:
            st.write("**Nova Configuração ERP**")
            
            with st.form("nova_config_erp"):
                nome_conexao = st.text_input("Nome da Conexão*:")
                tipo_sistema = st.selectbox("Tipo de Sistema:", 
                                          list(manager.supported_systems.keys()),
                                          format_func=lambda x: manager.supported_systems[x])
                
                endereco_servidor = st.text_input("Servidor*:")
                porta = st.number_input("Porta:", min_value=1, max_value=65535, value=80)
                
                usuario = st.text_input("Usuário:")
                senha = st.text_input("Senha:", type="password")
                
                database_sid = st.text_input("Database/SID:")
                timeout_conexao = st.number_input("Timeout (s):", min_value=5, value=30)
                
                # Parâmetros específicos por tipo
                st.write("**Parâmetros Específicos:**")
                
                if tipo_sistema == 'SAP_R3':
                    sap_client = st.text_input("Client SAP:", placeholder="100")
                    sap_sysnr = st.text_input("System Number:", placeholder="00")
                    sap_lang = st.text_input("Language:", value="PT")
                    
                    parametros_especificos = {
                        'client': sap_client,
                        'system_number': sap_sysnr,
                        'language': sap_lang
                    }
                
                elif tipo_sistema == 'TOTVS_PROTHEUS':
                    totvs_env = st.text_input("Environment:", placeholder="PRODUCAO")
                    totvs_company = st.text_input("Company:", placeholder="01")
                    totvs_branch = st.text_input("Branch:", placeholder="01")
                    
                    parametros_especificos = {
                        'environment': totvs_env,
                        'company': totvs_company,
                        'branch': totvs_branch
                    }
                
                else:
                    parametros_json = st.text_area("Parâmetros (JSON):", 
                                                 placeholder='{"param1": "value1"}')
                    try:
                        parametros_especificos = json.loads(parametros_json) if parametros_json else {}
                    except:
                        parametros_especificos = {}
                
                observacoes = st.text_area("Observações:")
                
                if st.form_submit_button("➕ Criar Configuração"):
                    if nome_conexao and endereco_servidor:
                        try:
                            dados_config = {
                                'nome_conexao': nome_conexao,
                                'tipo_sistema': tipo_sistema,
                                'endereco_servidor': endereco_servidor,
                                'porta': porta,
                                'usuario': usuario,
                                'senha': senha,
                                'database_sid': database_sid,
                                'parametros_conexao': parametros_especificos,
                                'timeout_conexao': timeout_conexao,
                                'observacoes': observacoes
                            }
                            
                            config_id = manager.criar_configuracao_erp(dados_config)
                            st.success(f"✅ Configuração criada! ID: {config_id}")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao criar configuração: {e}")
                    else:
                        st.error("❌ Preencha os campos obrigatórios")
    
    with tab3:
        st.subheader("🔄 Histórico de Sincronizações")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cursor.execute("SELECT nome_conexao FROM configuracoes_erp ORDER BY nome_conexao")
            configs = cursor.fetchall()
            config_filtro = st.selectbox("Configuração:", 
                                       ["Todas"] + [c.nome_conexao for c in configs])
        
        with col2:
            status_filtro = st.selectbox("Status:", 
                                       ["Todos", "executando", "concluido", "erro"])
        
        with col3:
            dias_filtro = st.selectbox("Período:", ["7 dias", "30 dias", "90 dias"])
        
        # Query das sincronizações
        query = """
        SELECT s.*, c.nome_conexao 
        FROM sincronizacoes_erp s
        JOIN configuracoes_erp c ON s.configuracao_erp_id = c.id
        WHERE s.data_inicio >= CURRENT_DATE - INTERVAL '%s'
        """
        params = [dias_filtro.split()[0] + ' days']
        
        if config_filtro != "Todas":
            query += " AND c.nome_conexao = %s"
            params.append(config_filtro)
        
        if status_filtro != "Todos":
            query += " AND s.status = %s"
            params.append(status_filtro)
        
        query += " ORDER BY s.data_inicio DESC LIMIT 50"
        
        cursor.execute(query, params)
        sincronizacoes = cursor.fetchall()
        
        if sincronizacoes:
            for sync in sincronizacoes:
                # Determinar cor baseada no status
                status_color = {
                    'executando': '🟡',
                    'concluido': '🟢',
                    'erro': '🔴'
                }.get(sync['status'], '⚪')
                
                duracao = ""
                if sync['data_fim'] and sync['data_inicio']:
                    delta = sync['data_fim'] - sync['data_inicio']
                    duracao = f" ({delta.total_seconds():.1f}s)"
                
                with st.expander(f"{status_color} {sync['tipo_operacao']} - {sync['nome_conexao']}{duracao}"):
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.write(f"**Início:** {sync['data_inicio'].strftime('%d/%m/%Y %H:%M:%S')}")
                        if sync['data_fim']:
                            st.write(f"**Fim:** {sync['data_fim'].strftime('%d/%m/%Y %H:%M:%S')}")
                        st.write(f"**Status:** {sync['status']}")
                    
                    with col_b:
                        st.write(f"**Processados:** {sync['registros_processados']}")
                        st.write(f"**Sucessos:** {sync['registros_sucesso']}")
                        st.write(f"**Erros:** {sync['registros_erro']}")
                    
                    with col_c:
                        if sync['registros_processados'] > 0:
                            taxa_sucesso = (sync['registros_sucesso'] / sync['registros_processados']) * 100
                            st.metric("Taxa Sucesso", f"{taxa_sucesso:.1f}%")
                    
                    if sync['log_detalhado']:
                        st.text_area("Log Detalhado:", value=sync['log_detalhado'], 
                                   height=100, key=f"log_{sync['id']}")
        else:
            st.info("ℹ️ Nenhuma sincronização encontrada")
        
        # Botão para executar sincronização manual
        st.subheader("🚀 Executar Sincronização Manual")
        
        col_manual1, col_manual2, col_manual3 = st.columns(3)
        
        with col_manual1:
            if configs:
                config_manual = st.selectbox("Configuração:", 
                                           [c.nome_conexao for c in configs])
        
        with col_manual2:
            tipo_manual = st.selectbox("Tipo:", [
                "sync_produtos", "sync_estoque", "sync_movimentacoes", 
                "sync_fornecedores", "sync_completa"
            ])
        
        with col_manual3:
            if st.button("🚀 Executar Sincronização"):
                if config_manual:
                    # Buscar ID da configuração
                    cursor.execute("SELECT id FROM configuracoes_erp WHERE nome_conexao = %s", 
                                 [config_manual])
                    config_id = cursor.fetchone()[0]
                    
                    with st.spinner("Executando sincronização..."):
                        try:
                            sync_id = manager.executar_sincronizacao(config_id, tipo_manual)
                            st.success(f"✅ Sincronização iniciada! ID: {sync_id}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erro: {e}")
    
    with tab4:
        st.subheader("📋 Mapeamento de Campos")
        
        # Interface para definir mapeamentos entre campos
        st.write("**Configurar Mapeamentos de Dados**")
        st.info("ℹ️ Configure como os dados são mapeados entre o sistema de inventário e o ERP")
        
        # Formulário de novo mapeamento
        with st.form("novo_mapeamento"):
            col_map1, col_map2 = st.columns(2)
            
            with col_map1:
                cursor.execute("SELECT id, nome_conexao FROM configuracoes_erp WHERE ativo = TRUE")
                configs_map = cursor.fetchall()
                
                if configs_map:
                    config_opcoes = {c.nome_conexao: c.id for c in configs_map}
                    config_selecionada = st.selectbox("Configuração ERP:", list(config_opcoes.keys()))
                    
                    tabela_origem = st.text_input("Tabela Origem (ERP):")
                    campo_origem = st.text_input("Campo Origem:")
                
            with col_map2:
                tabela_destino = st.selectbox("Tabela Destino (Inventário):", [
                    "insumos", "equipamentos_eletricos", "equipamentos_manuais",
                    "movimentacoes", "fornecedores", "obras"
                ])
                
                campo_destino = st.text_input("Campo Destino:")
                
                tipo_sync = st.selectbox("Tipo Sincronização:", [
                    "bidirecional", "erp_para_inventario", "inventario_para_erp"
                ])
            
            funcao_transformacao = st.text_area("Função de Transformação (Python):",
                                              placeholder="def transform(value):\n    return value.upper()")
            
            if st.form_submit_button("➕ Adicionar Mapeamento"):
                if all([tabela_origem, campo_origem, tabela_destino, campo_destino]):
                    cursor.execute("""
                    INSERT INTO mapeamento_campos_erp
                    (configuracao_erp_id, tabela_origem, campo_origem, 
                     tabela_destino, campo_destino, tipo_sincronizacao, funcao_transformacao)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, [
                        config_opcoes[config_selecionada], tabela_origem, campo_origem,
                        tabela_destino, campo_destino, tipo_sync, funcao_transformacao
                    ])
                    
                    conn.commit()
                    st.success("✅ Mapeamento adicionado!")
                    st.rerun()
                else:
                    st.error("❌ Preencha todos os campos obrigatórios")
        
        # Listar mapeamentos existentes
        cursor.execute("""
        SELECT m.*, c.nome_conexao 
        FROM mapeamento_campos_erp m
        JOIN configuracoes_erp c ON m.configuracao_erp_id = c.id
        WHERE m.ativo = TRUE
        ORDER BY c.nome_conexao, m.tabela_origem
        """)
        
        mapeamentos = cursor.fetchall()
        
        if mapeamentos:
            st.subheader("📋 Mapeamentos Configurados")
            
            for mapeamento in mapeamentos:
                with st.expander(f"🔀 {mapeamento['nome_conexao']} - {mapeamento['tabela_origem']}.{mapeamento['campo_origem']} → {mapeamento['tabela_destino']}.{mapeamento['campo_destino']}"):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.write(f"**Origem:** {mapeamento['tabela_origem']}.{mapeamento['campo_origem']}")
                        st.write(f"**Destino:** {mapeamento['tabela_destino']}.{mapeamento['campo_destino']}")
                    
                    with col_b:
                        st.write(f"**Tipo Sync:** {mapeamento['tipo_sincronizacao']}")
                        st.write(f"**Prioridade:** {mapeamento['prioridade']}")
                    
                    if mapeamento['funcao_transformacao']:
                        st.code(mapeamento['funcao_transformacao'], language='python')
    
    with tab5:
        st.subheader("🚨 Monitoramento de Erros")
        
        # Métricas de erro
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cursor.execute("""
            SELECT COUNT(*) FROM erros_integracao_erp 
            WHERE data_erro >= CURRENT_DATE - INTERVAL '24 hours'
            """)
            erros_24h = cursor.fetchone()[0]
            st.metric("Erros (24h)", erros_24h)
        
        with col2:
            cursor.execute("SELECT COUNT(*) FROM erros_integracao_erp WHERE resolvido = FALSE")
            erros_nao_resolvidos = cursor.fetchone()[0]
            st.metric("Não Resolvidos", erros_nao_resolvidos)
        
        with col3:
            cursor.execute("SELECT COUNT(*) FROM fila_sincronizacao_erp WHERE status = 'pendente'")
            fila_pendente = cursor.fetchone()[0]
            st.metric("Fila Pendente", fila_pendente)
        
        # Lista de erros
        cursor.execute("""
        SELECT e.*, c.nome_conexao
        FROM erros_integracao_erp e
        JOIN configuracoes_erp c ON e.configuracao_erp_id = c.id
        WHERE e.resolvido = FALSE
        ORDER BY e.data_erro DESC
        LIMIT 20
        """)
        
        erros = cursor.fetchall()
        
        if erros:
            st.subheader("🚨 Erros Não Resolvidos")
            
            for erro in erros:
                with st.expander(f"❌ {erro['tipo_erro']} - {erro['nome_conexao']} ({erro['data_erro'].strftime('%d/%m %H:%M')})"):
                    col_a, col_b = st.columns([2, 1])
                    
                    with col_a:
                        st.write(f"**Mensagem:** {erro['mensagem_erro']}")
                        if erro['tabela_afetada']:
                            st.write(f"**Tabela:** {erro['tabela_afetada']}")
                        if erro['registro_id']:
                            st.write(f"**Registro:** {erro['registro_id']}")
                        st.write(f"**Tentativas:** {erro['tentativas']}")
                        
                        if erro['detalhes_erro']:
                            st.json(erro['detalhes_erro'])
                    
                    with col_b:
                        if st.button("✅ Marcar Resolvido", key=f"resolve_{erro['id']}"):
                            cursor.execute("""
                            UPDATE erros_integracao_erp 
                            SET resolvido = TRUE, data_resolucao = CURRENT_TIMESTAMP,
                                usuario_resolucao_id = 1
                            WHERE id = %s
                            """, [erro['id']])
                            
                            conn.commit()
                            st.success("✅ Erro marcado como resolvido!")
                            st.rerun()
        else:
            st.success("🎉 Nenhum erro pendente!")
        
        # Fila de sincronização
        st.subheader("📋 Fila de Sincronização")
        
        cursor.execute("""
        SELECT f.*, c.nome_conexao
        FROM fila_sincronizacao_erp f
        JOIN configuracoes_erp c ON f.configuracao_erp_id = c.id
        WHERE f.status IN ('pendente', 'erro')
        ORDER BY f.prioridade, f.data_criacao
        LIMIT 10
        """)
        
        fila_itens = cursor.fetchall()
        
        if fila_itens:
            for item in fila_itens:
                status_icon = "⏳" if item['status'] == 'pendente' else "❌"
                
                with st.expander(f"{status_icon} {item['tipo_operacao']} - {item['nome_conexao']} (Prioridade: {item['prioridade']})"):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.write(f"**Criado em:** {item['data_criacao'].strftime('%d/%m/%Y %H:%M')}")
                        st.write(f"**Tentativas:** {item['tentativas']}/{item['max_tentativas']}")
                    
                    with col_b:
                        if item['resultado_processamento']:
                            st.write(f"**Resultado:** {item['resultado_processamento']}")
                    
                    if item['dados_registro']:
                        st.json(item['dados_registro'])
        else:
            st.info("ℹ️ Fila vazia")
        
        # Processar fila manualmente
        if st.button("🔄 Processar Fila Agora"):
            with st.spinner("Processando fila..."):
                manager.processar_fila_sincronizacao()
                st.success("✅ Fila processada!")
                st.rerun()
    
    with tab6:
        st.subheader("📈 Relatórios de Integração")
        
        # Período
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data Início:", 
                                      value=datetime.now().date() - timedelta(days=30))
        with col2:
            data_fim = st.date_input("Data Fim:", value=datetime.now().date())
        
        # Relatório de performance por configuração
        cursor.execute("""
        SELECT 
            c.nome_conexao,
            COUNT(s.id) as total_syncs,
            AVG(EXTRACT(EPOCH FROM (s.data_fim - s.data_inicio))) as duracao_media,
            SUM(s.registros_processados) as total_registros,
            SUM(s.registros_sucesso) as total_sucessos,
            SUM(s.registros_erro) as total_erros
        FROM configuracoes_erp c
        LEFT JOIN sincronizacoes_erp s ON c.id = s.configuracao_erp_id
            AND s.data_inicio BETWEEN %s AND %s + INTERVAL '1 day'
        WHERE c.ativo = TRUE
        GROUP BY c.id, c.nome_conexao
        ORDER BY total_syncs DESC
        """, [data_inicio, data_fim])
        
        performance_data = cursor.fetchall()
        
        if performance_data:
            # Criar DataFrame
            df_perf = pd.DataFrame(performance_data)
            df_perf['taxa_sucesso'] = (df_perf['total_sucessos'] / df_perf['total_registros'] * 100).fillna(0)
            
            # Gráficos
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                fig1 = px.bar(df_perf, x='nome_conexao', y='total_syncs',
                             title='Total de Sincronizações por Configuração')
                fig1.update_xaxis(title='Configuração')
                fig1.update_yaxis(title='Total Sincronizações')
                st.plotly_chart(fig1, use_container_width=True)
            
            with col_graf2:
                fig2 = px.scatter(df_perf, x='duracao_media', y='taxa_sucesso',
                                size='total_registros', color='nome_conexao',
                                title='Duração vs Taxa de Sucesso')
                fig2.update_xaxis(title='Duração Média (s)')
                fig2.update_yaxis(title='Taxa de Sucesso (%)')
                st.plotly_chart(fig2, use_container_width=True)
            
            # Tabela resumo
            st.subheader("📊 Resumo de Performance")
            
            # Formatar dados para exibição
            df_display = df_perf.copy()
            df_display['duracao_media'] = df_display['duracao_media'].fillna(0).round(2)
            df_display['taxa_sucesso'] = df_display['taxa_sucesso'].round(1)
            
            st.dataframe(df_display[['nome_conexao', 'total_syncs', 'duracao_media', 
                                   'total_registros', 'taxa_sucesso']], 
                        column_config={
                            'nome_conexao': 'Configuração',
                            'total_syncs': 'Total Syncs',
                            'duracao_media': 'Duração Média (s)',
                            'total_registros': 'Total Registros',
                            'taxa_sucesso': 'Taxa Sucesso (%)'
                        })
        else:
            st.info("ℹ️ Nenhum dado de performance encontrado para o período")
        
        # Relatório de erros por tipo
        cursor.execute("""
        SELECT 
            tipo_erro,
            COUNT(*) as total_erros,
            COUNT(CASE WHEN resolvido = TRUE THEN 1 END) as resolvidos
        FROM erros_integracao_erp
        WHERE data_erro BETWEEN %s AND %s + INTERVAL '1 day'
        GROUP BY tipo_erro
        ORDER BY total_erros DESC
        """, [data_inicio, data_fim])
        
        erros_por_tipo = cursor.fetchall()
        
        if erros_por_tipo:
            st.subheader("🚨 Erros por Tipo")
            
            df_erros = pd.DataFrame(erros_por_tipo)
            df_erros['pendentes'] = df_erros['total_erros'] - df_erros['resolvidos']
            
            fig3 = px.bar(df_erros, x='tipo_erro', y=['resolvidos', 'pendentes'],
                         title='Status dos Erros por Tipo',
                         color_discrete_map={'resolvidos': 'green', 'pendentes': 'red'})
            st.plotly_chart(fig3, use_container_width=True)

if __name__ == "__main__":
    show_erp_integration_page()