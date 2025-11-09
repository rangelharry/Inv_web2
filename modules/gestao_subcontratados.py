"""
Gestão Avançada de Subcontratados
Sistema completo para gestão de terceirizados, controle de equipamentos emprestados e contratos
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from typing import Dict, List, Any, Optional
from database.connection import db
from modules.logs_auditoria import log_acao

class SubcontratadosManager:
    """Gerenciador avançado de subcontratados"""
    
    def __init__(self):
        self.criar_tabelas_subcontratados()
    
    def criar_tabelas_subcontratados(self):
        """Cria estrutura completa de tabelas para gestão de subcontratados"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Tabela principal de subcontratados
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS subcontratados (
                id SERIAL PRIMARY KEY,
                razao_social VARCHAR(255) NOT NULL,
                nome_fantasia VARCHAR(255),
                cnpj VARCHAR(18) UNIQUE NOT NULL,
                inscricao_estadual VARCHAR(20),
                inscricao_municipal VARCHAR(20),
                
                -- Dados de contato
                email_principal VARCHAR(255),
                telefone_principal VARCHAR(20),
                telefone_secundario VARCHAR(20),
                site VARCHAR(255),
                
                -- Endereço
                endereco TEXT,
                numero VARCHAR(10),
                complemento VARCHAR(100),
                bairro VARCHAR(100),
                cidade VARCHAR(100),
                estado VARCHAR(2),
                cep VARCHAR(10),
                
                -- Dados do responsável
                responsavel_nome VARCHAR(255),
                responsavel_cargo VARCHAR(100),
                responsavel_email VARCHAR(255),
                responsavel_telefone VARCHAR(20),
                
                -- Especialidades e capacidades
                especialidades TEXT[], -- Array de especialidades
                area_atuacao TEXT[],
                capacidade_funcionarios INTEGER,
                equipamentos_proprios TEXT[],
                certificacoes TEXT[],
                
                -- Avaliações e scoring
                avaliacao_geral DECIMAL(3,2) DEFAULT 0.00, -- 0.00 a 10.00
                score_qualidade INTEGER DEFAULT 5, -- 1 a 10
                score_pontualidade INTEGER DEFAULT 5,
                score_comunicacao INTEGER DEFAULT 5,
                score_seguranca INTEGER DEFAULT 5,
                score_custo_beneficio INTEGER DEFAULT 5,
                
                -- Status e configurações
                status_aprovacao VARCHAR(50) DEFAULT 'pendente', -- pendente, aprovado, suspenso, inativo
                nivel_confianca VARCHAR(50) DEFAULT 'medio', -- baixo, medio, alto, critico
                limite_valor_projeto DECIMAL(15,2),
                pode_trabalhar_sozinho BOOLEAN DEFAULT FALSE,
                requer_supervisao BOOLEAN DEFAULT TRUE,
                
                -- Datas e controle
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_ultima_atualizacao TIMESTAMP,
                data_ultima_avaliacao TIMESTAMP,
                cadastrado_por INTEGER,
                ativo BOOLEAN DEFAULT TRUE,
                
                -- Observações e notas
                observacoes TEXT,
                restricoes TEXT
            )
            """)
            
            # Tabela de contratos com subcontratados
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS contratos_subcontratados (
                id SERIAL PRIMARY KEY,
                numero_contrato VARCHAR(100) UNIQUE NOT NULL,
                subcontratado_id INTEGER REFERENCES subcontratados(id),
                obra_id INTEGER, -- Referência para obras
                
                -- Dados do contrato
                tipo_contrato VARCHAR(100), -- empreitada_global, administracao, locacao_equipamentos, servicos
                descricao_servicos TEXT NOT NULL,
                valor_total DECIMAL(15,2),
                valor_inicial DECIMAL(15,2),
                valor_atual DECIMAL(15,2),
                moeda VARCHAR(10) DEFAULT 'BRL',
                
                -- Prazos
                data_inicio DATE NOT NULL,
                data_fim_prevista DATE NOT NULL,
                data_fim_real DATE,
                prazo_execucao_dias INTEGER,
                
                -- Status e controle
                status_contrato VARCHAR(50) DEFAULT 'em_negociacao', -- em_negociacao, assinado, em_execucao, suspenso, finalizado, cancelado
                percentual_execucao DECIMAL(5,2) DEFAULT 0.00,
                
                -- Condições comerciais
                forma_pagamento VARCHAR(100),
                prazo_pagamento_dias INTEGER DEFAULT 30,
                retencao_percentual DECIMAL(5,2) DEFAULT 0.00,
                multa_atraso_diaria DECIMAL(10,2),
                bonus_antecipacao DECIMAL(10,2),
                
                -- Garantias e seguros
                tipo_garantia VARCHAR(100), -- caucao, fianca, seguro
                valor_garantia DECIMAL(15,2),
                data_vencimento_garantia DATE,
                seguro_responsabilidade_civil BOOLEAN DEFAULT FALSE,
                valor_seguro DECIMAL(15,2),
                
                -- Documentos e anexos
                caminho_contrato VARCHAR(500),
                documentos_anexos JSONB,
                
                -- Auditoria
                data_assinatura DATE,
                assinado_por INTEGER,
                aprovado_por INTEGER,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                criado_por INTEGER,
                ultima_atualizacao TIMESTAMP,
                observacoes TEXT
            )
            """)
            
            # Tabela de empréstimo de equipamentos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS emprestimos_equipamentos (
                id SERIAL PRIMARY KEY,
                subcontratado_id INTEGER REFERENCES subcontratados(id),
                contrato_id INTEGER REFERENCES contratos_subcontratados(id),
                
                -- Dados do equipamento
                equipamento_codigo VARCHAR(255),
                equipamento_nome VARCHAR(255) NOT NULL,
                tipo_equipamento VARCHAR(100),
                marca VARCHAR(100),
                modelo VARCHAR(100),
                numero_serie VARCHAR(100),
                
                -- Dados do empréstimo
                data_emprestimo DATE NOT NULL,
                data_devolucao_prevista DATE NOT NULL,
                data_devolucao_real DATE,
                responsavel_entrega VARCHAR(255),
                responsavel_recebimento VARCHAR(255),
                
                -- Estado do equipamento
                estado_entrega VARCHAR(100), -- excelente, bom, regular, ruim
                estado_devolucao VARCHAR(100),
                observacoes_entrega TEXT,
                observacoes_devolucao TEXT,
                fotos_entrega TEXT[], -- URLs das fotos
                fotos_devolucao TEXT[],
                
                -- Valores e seguros
                valor_equipamento DECIMAL(15,2),
                valor_caucao DECIMAL(15,2),
                seguro_contratado BOOLEAN DEFAULT FALSE,
                numero_apolice VARCHAR(100),
                
                -- Status e controle
                status_emprestimo VARCHAR(50) DEFAULT 'ativo', -- ativo, devolvido, em_atraso, perdido, danificado
                dias_atraso INTEGER DEFAULT 0,
                multa_atraso DECIMAL(10,2) DEFAULT 0.00,
                
                -- Manutenção durante empréstimo
                manutencoes_realizadas JSONB,
                custos_manutencao DECIMAL(10,2) DEFAULT 0.00,
                
                -- Localização
                localizacao_atual VARCHAR(255),
                coordenadas_gps JSONB,
                
                -- Auditoria
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                criado_por INTEGER,
                ultima_atualizacao TIMESTAMP
            )
            """)
            
            # Tabela de avaliações de desempenho
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS avaliacoes_subcontratados (
                id SERIAL PRIMARY KEY,
                subcontratado_id INTEGER REFERENCES subcontratados(id),
                contrato_id INTEGER REFERENCES contratos_subcontratados(id),
                obra_id INTEGER,
                
                -- Período da avaliação
                data_inicio_periodo DATE NOT NULL,
                data_fim_periodo DATE NOT NULL,
                tipo_avaliacao VARCHAR(100), -- mensal, trimestral, pos_obra, extraordinaria
                
                -- Critérios de avaliação (1 a 10)
                qualidade_servico INTEGER,
                cumprimento_prazo INTEGER,
                organizacao_canteiro INTEGER,
                comunicacao INTEGER,
                seguranca_trabalho INTEGER,
                relacionamento_equipe INTEGER,
                resolucao_problemas INTEGER,
                custo_beneficio INTEGER,
                inovacao_melhorias INTEGER,
                
                -- Pontuação geral
                pontuacao_total DECIMAL(5,2),
                classificacao VARCHAR(50), -- excelente, bom, regular, insatisfatorio
                
                -- Comentários detalhados
                pontos_fortes TEXT,
                pontos_melhoria TEXT,
                observacoes_gerais TEXT,
                recomendacoes TEXT,
                
                -- Ocorrências
                ocorrencias_seguranca INTEGER DEFAULT 0,
                ocorrencias_qualidade INTEGER DEFAULT 0,
                reclamacoes_recebidas INTEGER DEFAULT 0,
                
                -- Renovação de contrato
                recomenda_renovacao BOOLEAN,
                justificativa_renovacao TEXT,
                
                -- Auditoria
                avaliado_por INTEGER,
                aprovado_por INTEGER,
                data_avaliacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_aprovacao TIMESTAMP
            )
            """)
            
            # Tabela de medições e pagamentos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS medicoes_subcontratados (
                id SERIAL PRIMARY KEY,
                contrato_id INTEGER REFERENCES contratos_subcontratados(id),
                numero_medicao INTEGER NOT NULL,
                
                -- Período da medição
                data_inicio_periodo DATE NOT NULL,
                data_fim_periodo DATE NOT NULL,
                data_medicao DATE NOT NULL,
                
                -- Valores
                valor_servicos_executados DECIMAL(15,2),
                percentual_executado DECIMAL(5,2),
                valor_acumulado_periodo DECIMAL(15,2),
                valor_total_acumulado DECIMAL(15,2),
                
                -- Descontos e acréscimos
                valor_retencoes DECIMAL(15,2) DEFAULT 0.00,
                valor_multas DECIMAL(15,2) DEFAULT 0.00,
                valor_bonus DECIMAL(15,2) DEFAULT 0.00,
                valor_reajustes DECIMAL(15,2) DEFAULT 0.00,
                
                -- Valor final
                valor_liquido_pagamento DECIMAL(15,2),
                
                -- Status
                status_medicao VARCHAR(50) DEFAULT 'em_analise', -- em_analise, aprovada, paga, contestada
                
                -- Documentação
                memorial_descritivo TEXT,
                observacoes TEXT,
                anexos_comprobatorios TEXT[],
                
                -- Aprovação e pagamento
                medido_por INTEGER,
                aprovado_por INTEGER,
                data_aprovacao TIMESTAMP,
                data_pagamento TIMESTAMP,
                numero_nota_fiscal VARCHAR(100),
                
                -- Auditoria
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                criado_por INTEGER
            )
            """)
            
            # Tabela de documentos e certificações
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS documentos_subcontratados (
                id SERIAL PRIMARY KEY,
                subcontratado_id INTEGER REFERENCES subcontratados(id),
                
                -- Tipo e dados do documento
                tipo_documento VARCHAR(100), -- alvara, certificado, licenca, seguro, etc
                nome_documento VARCHAR(255) NOT NULL,
                numero_documento VARCHAR(100),
                orgao_emissor VARCHAR(255),
                
                -- Validade
                data_emissao DATE,
                data_vencimento DATE,
                dias_alerta_vencimento INTEGER DEFAULT 30,
                
                -- Status
                status_documento VARCHAR(50) DEFAULT 'valido', -- valido, vencido, em_renovacao, pendente
                obrigatorio BOOLEAN DEFAULT FALSE,
                
                -- Arquivo
                caminho_arquivo VARCHAR(500),
                tamanho_arquivo INTEGER,
                tipo_arquivo VARCHAR(10),
                
                -- Verificação
                verificado BOOLEAN DEFAULT FALSE,
                verificado_por INTEGER,
                data_verificacao TIMESTAMP,
                observacoes_verificacao TEXT,
                
                -- Auditoria
                data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                enviado_por INTEGER
            )
            """)
            
            # Tabela de histórico de ocorrências
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ocorrencias_subcontratados (
                id SERIAL PRIMARY KEY,
                subcontratado_id INTEGER REFERENCES subcontratados(id),
                contrato_id INTEGER REFERENCES contratos_subcontratados(id),
                
                -- Dados da ocorrência
                tipo_ocorrencia VARCHAR(100), -- acidente, atraso, qualidade, reclamacao, elogio
                severidade VARCHAR(50), -- baixa, media, alta, critica
                titulo VARCHAR(255) NOT NULL,
                descricao TEXT NOT NULL,
                
                -- Local e pessoas envolvidas
                local_ocorrencia VARCHAR(255),
                pessoas_envolvidas TEXT[],
                testemunhas TEXT[],
                
                -- Ações tomadas
                acao_imediata TEXT,
                acao_corretiva TEXT,
                acao_preventiva TEXT,
                prazo_correcao DATE,
                
                -- Status
                status_ocorrencia VARCHAR(50) DEFAULT 'aberta', -- aberta, em_andamento, resolvida, fechada
                responsavel_resolucao INTEGER,
                data_resolucao TIMESTAMP,
                
                -- Impactos
                impacto_prazo INTEGER, -- dias de atraso
                impacto_custo DECIMAL(15,2),
                impacto_qualidade VARCHAR(100),
                
                -- Documentação
                evidencias TEXT[], -- fotos, documentos
                numero_boletim VARCHAR(100), -- BO, CAT, etc
                
                -- Auditoria
                data_ocorrencia TIMESTAMP NOT NULL,
                reportado_por INTEGER,
                data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            conn.commit()
            print("✅ Tabelas de subcontratados criadas com sucesso")
            
        except Exception as e:
            print(f"❌ Erro ao criar tabelas de subcontratados: {e}")
    
    def cadastrar_subcontratado(self, dados: Dict[str, Any]) -> bool:
        """Cadastra novo subcontratado"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO subcontratados 
            (razao_social, nome_fantasia, cnpj, email_principal, telefone_principal,
             endereco, cidade, estado, cep, responsavel_nome, responsavel_email,
             responsavel_telefone, especialidades, area_atuacao, capacidade_funcionarios,
             observacoes, cadastrado_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """, [
                dados['razao_social'], dados.get('nome_fantasia'),
                dados['cnpj'], dados.get('email_principal'),
                dados.get('telefone_principal'), dados.get('endereco'),
                dados.get('cidade'), dados.get('estado'), dados.get('cep'),
                dados.get('responsavel_nome'), dados.get('responsavel_email'),
                dados.get('responsavel_telefone'), dados.get('especialidades', []),
                dados.get('area_atuacao', []), dados.get('capacidade_funcionarios'),
                dados.get('observacoes'), dados.get('cadastrado_por', 1)
            ])
            
            subcontratado_id = cursor.fetchone()[0]
            conn.commit()
            
            log_acao("subcontratados", "cadastro", f"Subcontratado {dados['razao_social']} cadastrado")
            return subcontratado_id
            
        except Exception as e:
            st.error(f"❌ Erro ao cadastrar subcontratado: {e}")
            return False
    
    def criar_contrato(self, dados: Dict[str, Any]) -> bool:
        """Cria novo contrato com subcontratado"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO contratos_subcontratados 
            (numero_contrato, subcontratado_id, tipo_contrato, descricao_servicos,
             valor_total, data_inicio, data_fim_prevista, forma_pagamento,
             prazo_pagamento_dias, criado_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """, [
                dados['numero_contrato'], dados['subcontratado_id'],
                dados['tipo_contrato'], dados['descricao_servicos'],
                dados['valor_total'], dados['data_inicio'],
                dados['data_fim_prevista'], dados['forma_pagamento'],
                dados['prazo_pagamento_dias'], dados.get('criado_por', 1)
            ])
            
            contrato_id = cursor.fetchone()[0]
            conn.commit()
            
            log_acao("subcontratados", "contrato_criado", f"Contrato {dados['numero_contrato']} criado")
            return contrato_id
            
        except Exception as e:
            st.error(f"❌ Erro ao criar contrato: {e}")
            return False
    
    def emprestar_equipamento(self, dados: Dict[str, Any]) -> bool:
        """Registra empréstimo de equipamento para subcontratado"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO emprestimos_equipamentos 
            (subcontratado_id, contrato_id, equipamento_codigo, equipamento_nome,
             data_emprestimo, data_devolucao_prevista, responsavel_entrega,
             estado_entrega, valor_equipamento, valor_caucao, criado_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """, [
                dados['subcontratado_id'], dados.get('contrato_id'),
                dados['equipamento_codigo'], dados['equipamento_nome'],
                dados['data_emprestimo'], dados['data_devolucao_prevista'],
                dados['responsavel_entrega'], dados['estado_entrega'],
                dados.get('valor_equipamento'), dados.get('valor_caucao'),
                dados.get('criado_por', 1)
            ])
            
            emprestimo_id = cursor.fetchone()[0]
            conn.commit()
            
            log_acao("subcontratados", "emprestimo", 
                    f"Equipamento {dados['equipamento_codigo']} emprestado")
            return emprestimo_id
            
        except Exception as e:
            st.error(f"❌ Erro ao registrar empréstimo: {e}")
            return False
    
    def avaliar_subcontratado(self, dados: Dict[str, Any]) -> bool:
        """Registra avaliação de desempenho do subcontratado"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Calcular pontuação total
            criterios = [
                dados.get('qualidade_servico', 5),
                dados.get('cumprimento_prazo', 5),
                dados.get('comunicacao', 5),
                dados.get('seguranca_trabalho', 5),
                dados.get('custo_beneficio', 5)
            ]
            
            pontuacao_total = sum(criterios) / len(criterios)
            
            # Determinar classificação
            if pontuacao_total >= 8.5:
                classificacao = "excelente"
            elif pontuacao_total >= 7.0:
                classificacao = "bom"
            elif pontuacao_total >= 5.0:
                classificacao = "regular"
            else:
                classificacao = "insatisfatorio"
            
            cursor.execute("""
            INSERT INTO avaliacoes_subcontratados 
            (subcontratado_id, contrato_id, data_inicio_periodo, data_fim_periodo,
             qualidade_servico, cumprimento_prazo, comunicacao, seguranca_trabalho,
             custo_beneficio, pontuacao_total, classificacao, pontos_fortes,
             pontos_melhoria, recomenda_renovacao, avaliado_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                dados['subcontratado_id'], dados.get('contrato_id'),
                dados['data_inicio_periodo'], dados['data_fim_periodo'],
                dados.get('qualidade_servico'), dados.get('cumprimento_prazo'),
                dados.get('comunicacao'), dados.get('seguranca_trabalho'),
                dados.get('custo_beneficio'), pontuacao_total, classificacao,
                dados.get('pontos_fortes'), dados.get('pontos_melhoria'),
                dados.get('recomenda_renovacao', True), dados.get('avaliado_por', 1)
            ])
            
            # Atualizar avaliação geral do subcontratado
            cursor.execute("""
            UPDATE subcontratados 
            SET avaliacao_geral = (
                SELECT AVG(pontuacao_total) 
                FROM avaliacoes_subcontratados 
                WHERE subcontratado_id = %s
            ),
            data_ultima_avaliacao = CURRENT_TIMESTAMP
            WHERE id = %s
            """, [dados['subcontratado_id'], dados['subcontratado_id']])
            
            conn.commit()
            
            log_acao("subcontratados", "avaliacao", 
                    f"Avaliação registrada - Pontuação: {pontuacao_total:.2f}")
            return True
            
        except Exception as e:
            st.error(f"❌ Erro ao registrar avaliação: {e}")
            return False
    
    def listar_subcontratados(self, filtros: Dict[str, Any] = None) -> List[Dict]:
        """Lista subcontratados com filtros"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT s.*, 
                   COUNT(c.id) as total_contratos,
                   COUNT(e.id) as total_emprestimos,
                   AVG(a.pontuacao_total) as media_avaliacoes
            FROM subcontratados s
            LEFT JOIN contratos_subcontratados c ON s.id = c.subcontratado_id
            LEFT JOIN emprestimos_equipamentos e ON s.id = e.subcontratado_id
            LEFT JOIN avaliacoes_subcontratados a ON s.id = a.subcontratado_id
            WHERE s.ativo = TRUE
            """
            
            params = []
            
            if filtros:
                if filtros.get('status_aprovacao'):
                    query += " AND s.status_aprovacao = %s"
                    params.append(filtros['status_aprovacao'])
                
                if filtros.get('especialidade'):
                    query += " AND %s = ANY(s.especialidades)"
                    params.append(filtros['especialidade'])
                
                if filtros.get('avaliacao_minima'):
                    query += " AND s.avaliacao_geral >= %s"
                    params.append(filtros['avaliacao_minima'])
            
            query += " GROUP BY s.id ORDER BY s.razao_social"
            
            cursor.execute(query, params)
            return cursor.fetchall()
            
        except Exception as e:
            st.error(f"❌ Erro ao listar subcontratados: {e}")
            return []
    
    def show_subcontratados_dashboard(self):
        """Exibe dashboard principal de subcontratados"""
        st.title("🏢 Gestão de Subcontratados")
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Subcontratados Ativos", "24", "+2")
        
        with col2:
            st.metric("📋 Contratos Ativos", "18", "+1")
        
        with col3:
            st.metric("📦 Equipamentos Emprestados", "42", "+5")
        
        with col4:
            st.metric("⭐ Avaliação Média", "8.2", "+0.3")
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            self.show_avaliacoes_chart()
        
        with col2:
            self.show_contratos_status_chart()
        
        # Lista de alertas
        self.show_alertas_subcontratados()
    
    def show_avaliacoes_chart(self):
        """Gráfico de avaliações dos subcontratados"""
        st.subheader("📊 Avaliações por Subcontratado")
        
        # Dados simulados
        subcontratados = ['Construtora A', 'Empresa B', 'Terceirizada C', 'Parceira D', 'Fornecedor E']
        avaliacoes = [8.5, 7.2, 9.1, 6.8, 8.0]
        
        fig = px.bar(
            x=subcontratados,
            y=avaliacoes,
            color=avaliacoes,
            color_continuous_scale='RdYlGn',
            title="Avaliações de Desempenho"
        )
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def show_contratos_status_chart(self):
        """Gráfico de status dos contratos"""
        st.subheader("📈 Status dos Contratos")
        
        status_data = {
            'Status': ['Em Execução', 'Assinados', 'Em Negociação', 'Finalizados'],
            'Quantidade': [8, 5, 3, 7]
        }
        
        fig = px.pie(
            values=status_data['Quantidade'],
            names=status_data['Status'],
            title="Distribuição por Status"
        )
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def show_alertas_subcontratados(self):
        """Exibe alertas importantes"""
        st.subheader("⚠️ Alertas e Pendências")
        
        alertas = [
            {"tipo": "Documento Vencido", "subcontratado": "Construtora A", "prioridade": "Alta"},
            {"tipo": "Contrato Vencendo", "subcontratado": "Empresa B", "prioridade": "Média"},
            {"tipo": "Equipamento em Atraso", "subcontratado": "Terceirizada C", "prioridade": "Alta"},
            {"tipo": "Avaliação Pendente", "subcontratado": "Parceira D", "prioridade": "Baixa"}
        ]
        
        for alerta in alertas:
            color = {"Alta": "error", "Média": "warning", "Baixa": "info"}[alerta["prioridade"]]
            getattr(st, color)(f"{alerta['tipo']}: {alerta['subcontratado']}")

def show_subcontratados_page():
    """Página principal de gestão de subcontratados"""
    st.set_page_config(
        page_title="🏢 Gestão de Subcontratados",
        page_icon="🏢",
        layout="wide"
    )
    
    manager = SubcontratadosManager()
    
    # Menu lateral
    menu = st.sidebar.selectbox(
        "📂 Menu",
        ["🏠 Dashboard", "👥 Subcontratados", "📋 Contratos", "📦 Empréstimos", 
         "⭐ Avaliações", "📄 Documentos", "🚨 Ocorrências", "💰 Medições"]
    )
    
    if menu == "🏠 Dashboard":
        manager.show_subcontratados_dashboard()
    
    elif menu == "👥 Subcontratados":
        st.subheader("👥 Gestão de Subcontratados")
        
        tab1, tab2, tab3 = st.tabs(["📋 Lista", "➕ Cadastrar", "🔍 Filtros"])
        
        with tab1:
            st.markdown("### 📋 Subcontratados Cadastrados")
            
            # Tabela simulada
            data = {
                'Razão Social': ['Construtora ABC Ltda', 'Empresa XYZ S/A', 'Terceirizada 123'],
                'CNPJ': ['11.222.333/0001-44', '55.666.777/0001-88', '99.888.777/0001-66'],
                'Especialidade': ['Construção Civil', 'Elétrica', 'Hidráulica'],
                'Avaliação': [8.5, 7.2, 9.1],
                'Status': ['Aprovado', 'Aprovado', 'Pendente']
            }
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        
        with tab2:
            st.markdown("### ➕ Cadastrar Novo Subcontratado")
            
            with st.form("novo_subcontratado"):
                col1, col2 = st.columns(2)
                
                with col1:
                    razao_social = st.text_input("Razão Social *")
                    nome_fantasia = st.text_input("Nome Fantasia")
                    cnpj = st.text_input("CNPJ *")
                    email = st.text_input("E-mail Principal")
                
                with col2:
                    telefone = st.text_input("Telefone Principal")
                    cidade = st.text_input("Cidade")
                    estado = st.selectbox("Estado", ["SP", "RJ", "MG", "RS"])
                    cep = st.text_input("CEP")
                
                especialidades = st.multiselect(
                    "Especialidades",
                    ["Construção Civil", "Elétrica", "Hidráulica", "Pintura", 
                     "Carpintaria", "Serralheria", "Paisagismo"]
                )
                
                endereco = st.text_area("Endereço Completo")
                observacoes = st.text_area("Observações")
                
                submitted = st.form_submit_button("💾 Cadastrar", type="primary")
                
                if submitted and razao_social and cnpj:
                    dados = {
                        'razao_social': razao_social,
                        'nome_fantasia': nome_fantasia,
                        'cnpj': cnpj,
                        'email_principal': email,
                        'telefone_principal': telefone,
                        'endereco': endereco,
                        'cidade': cidade,
                        'estado': estado,
                        'cep': cep,
                        'especialidades': especialidades,
                        'observacoes': observacoes
                    }
                    
                    if manager.cadastrar_subcontratado(dados):
                        st.success("✅ Subcontratado cadastrado com sucesso!")
                        st.rerun()
        
        with tab3:
            st.markdown("### 🔍 Filtros de Busca")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_filter = st.selectbox("Status", ["Todos", "Aprovado", "Pendente", "Suspenso"])
            
            with col2:
                especialidade_filter = st.selectbox("Especialidade", 
                    ["Todas", "Construção Civil", "Elétrica", "Hidráulica"])
            
            with col3:
                avaliacao_filter = st.slider("Avaliação Mínima", 0.0, 10.0, 0.0)
            
            if st.button("🔍 Aplicar Filtros"):
                st.info("Filtros aplicados com sucesso!")
    
    elif menu == "📋 Contratos":
        st.subheader("📋 Gestão de Contratos")
        
        tab1, tab2 = st.tabs(["📊 Dashboard Contratos", "➕ Novo Contrato"])
        
        with tab1:
            # Métricas de contratos
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Contratos", "23")
            
            with col2:
                st.metric("Em Execução", "8")
            
            with col3:
                st.metric("Valor Total", "R$ 2.3M")
            
            with col4:
                st.metric("Vencendo em 30 dias", "3")
            
            # Lista de contratos
            st.markdown("### 📋 Contratos Ativos")
            
            contratos_data = {
                'Número': ['CT-2024-001', 'CT-2024-002', 'CT-2024-003'],
                'Subcontratado': ['Construtora ABC', 'Empresa XYZ', 'Terceirizada 123'],
                'Valor': ['R$ 850.000', 'R$ 320.000', 'R$ 180.000'],
                'Status': ['Em Execução', 'Assinado', 'Em Execução'],
                'Vencimento': ['2024-12-31', '2025-03-15', '2024-11-30']
            }
            
            df_contratos = pd.DataFrame(contratos_data)
            st.dataframe(df_contratos, use_container_width=True)
        
        with tab2:
            st.markdown("### ➕ Criar Novo Contrato")
            
            with st.form("novo_contrato"):
                col1, col2 = st.columns(2)
                
                with col1:
                    numero_contrato = st.text_input("Número do Contrato *")
                    subcontratado = st.selectbox("Subcontratado", ["Construtora ABC", "Empresa XYZ"])
                    tipo_contrato = st.selectbox("Tipo de Contrato", 
                        ["Empreitada Global", "Administração", "Locação de Equipamentos"])
                    valor_total = st.number_input("Valor Total (R$)", min_value=0.0)
                
                with col2:
                    data_inicio = st.date_input("Data de Início")
                    data_fim = st.date_input("Data de Fim Prevista")
                    forma_pagamento = st.selectbox("Forma de Pagamento", 
                        ["À Vista", "30 dias", "60 dias", "Parcelado"])
                    prazo_pagamento = st.number_input("Prazo de Pagamento (dias)", value=30)
                
                descricao_servicos = st.text_area("Descrição dos Serviços *", height=100)
                
                submitted = st.form_submit_button("📋 Criar Contrato", type="primary")
                
                if submitted and numero_contrato and descricao_servicos:
                    st.success("✅ Contrato criado com sucesso!")
    
    elif menu == "📦 Empréstimos":
        st.subheader("📦 Gestão de Empréstimos")
        
        tab1, tab2, tab3 = st.tabs(["📋 Empréstimos Ativos", "➕ Novo Empréstimo", "📊 Relatórios"])
        
        with tab1:
            st.markdown("### 📦 Equipamentos Emprestados")
            
            emprestimos_data = {
                'Equipamento': ['Betoneira 400L', 'Furadeira Industrial', 'Gerador 5kVA'],
                'Subcontratado': ['Construtora ABC', 'Empresa XYZ', 'Terceirizada 123'],
                'Data Empréstimo': ['2024-10-01', '2024-10-15', '2024-11-01'],
                'Devolução Prevista': ['2024-12-01', '2024-11-30', '2024-12-15'],
                'Status': ['No Prazo', 'Em Atraso', 'No Prazo']
            }
            
            df_emprestimos = pd.DataFrame(emprestimos_data)
            st.dataframe(df_emprestimos, use_container_width=True)
        
        with tab2:
            st.markdown("### ➕ Registrar Novo Empréstimo")
            
            with st.form("novo_emprestimo"):
                col1, col2 = st.columns(2)
                
                with col1:
                    equipamento_codigo = st.text_input("Código do Equipamento *")
                    equipamento_nome = st.text_input("Nome do Equipamento *")
                    subcontratado_emp = st.selectbox("Subcontratado", ["Construtora ABC", "Empresa XYZ"])
                
                with col2:
                    data_emprestimo = st.date_input("Data do Empréstimo")
                    data_devolucao = st.date_input("Data de Devolução Prevista")
                    responsavel = st.text_input("Responsável pela Entrega")
                
                estado_entrega = st.selectbox("Estado do Equipamento", 
                    ["Excelente", "Bom", "Regular", "Ruim"])
                valor_equipamento = st.number_input("Valor do Equipamento (R$)", min_value=0.0)
                valor_caucao = st.number_input("Valor da Caução (R$)", min_value=0.0)
                
                observacoes_emp = st.text_area("Observações da Entrega")
                
                submitted = st.form_submit_button("📦 Registrar Empréstimo", type="primary")
                
                if submitted and equipamento_codigo and equipamento_nome:
                    st.success("✅ Empréstimo registrado com sucesso!")
    
    elif menu == "⭐ Avaliações":
        st.subheader("⭐ Sistema de Avaliações")
        
        tab1, tab2 = st.tabs(["📊 Ranking", "➕ Nova Avaliação"])
        
        with tab1:
            st.markdown("### 🏆 Ranking de Subcontratados")
            
            ranking_data = {
                'Posição': [1, 2, 3, 4, 5],
                'Subcontratado': ['Terceirizada 123', 'Construtora ABC', 'Empresa XYZ', 'Parceira D', 'Fornecedor E'],
                'Avaliação Geral': [9.1, 8.5, 7.2, 6.8, 6.5],
                'Total de Projetos': [15, 23, 18, 8, 12],
                'Classificação': ['Excelente', 'Excelente', 'Bom', 'Regular', 'Regular']
            }
            
            df_ranking = pd.DataFrame(ranking_data)
            st.dataframe(df_ranking, use_container_width=True)
        
        with tab2:
            st.markdown("### ⭐ Avaliar Subcontratado")
            
            with st.form("nova_avaliacao"):
                subcontratado_aval = st.selectbox("Subcontratado", ["Construtora ABC", "Empresa XYZ"])
                periodo_inicio = st.date_input("Início do Período")
                periodo_fim = st.date_input("Fim do Período")
                
                st.markdown("#### 📊 Critérios de Avaliação (1 a 10)")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    qualidade = st.slider("Qualidade do Serviço", 1, 10, 5)
                    prazo = st.slider("Cumprimento de Prazo", 1, 10, 5)
                    comunicacao = st.slider("Comunicação", 1, 10, 5)
                
                with col2:
                    seguranca = st.slider("Segurança do Trabalho", 1, 10, 5)
                    custo = st.slider("Custo-Benefício", 1, 10, 5)
                
                pontos_fortes = st.text_area("Pontos Fortes")
                pontos_melhoria = st.text_area("Pontos de Melhoria")
                recomenda = st.checkbox("Recomenda para renovação de contrato", value=True)
                
                submitted = st.form_submit_button("⭐ Salvar Avaliação", type="primary")
                
                if submitted:
                    media = (qualidade + prazo + comunicacao + seguranca + custo) / 5
                    st.success(f"✅ Avaliação registrada! Média: {media:.1f}")

if __name__ == "__main__":
    show_subcontratados_page()