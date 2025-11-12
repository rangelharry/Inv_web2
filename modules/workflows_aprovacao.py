"""
Sistema de Workflows de Aprovação
Fluxos configuráveis para aprovação de movimentações, compras e requisições
"""

import streamlit as st
from datetime import datetime, timedelta
from database.connection import db
from modules.logs_auditoria import log_acao
import pandas as pd
from typing import Dict, List, Any, Optional
import json
import plotly.express as px
import plotly.graph_objects as go
from enum import Enum

class TipoWorkflow(Enum):
    MOVIMENTACAO = "movimentacao"
    COMPRA = "compra"
    REQUISICAO = "requisicao"
    MANUTENCAO = "manutencao"
    RESERVA = "reserva"

class StatusAprovacao(Enum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    REJEITADO = "rejeitado"
    CANCELADO = "cancelado"

class WorkflowManager:
    def __init__(self):
        self.criar_tabelas()
    
    def criar_tabelas(self):
        """Cria tabelas necessárias para workflows de aprovação"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Tabela de tipos de workflow
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipos_workflow (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) UNIQUE NOT NULL,
                descricao TEXT,
                tipo_entidade VARCHAR(50) NOT NULL,
                ativo BOOLEAN DEFAULT TRUE,
                requer_aprovacao BOOLEAN DEFAULT TRUE,
                valor_minimo_aprovacao DECIMAL(15,2) DEFAULT 0,
                dias_expiracao INTEGER DEFAULT 7,
                aprovacao_automatica BOOLEAN DEFAULT FALSE,
                configuracao_json JSONB,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario_criacao_id INTEGER
            )
            """)
            
            # Tabela de níveis de aprovação
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS niveis_aprovacao (
                id SERIAL PRIMARY KEY,
                tipo_workflow_id INTEGER REFERENCES tipos_workflow(id),
                nivel INTEGER NOT NULL,
                nome_nivel VARCHAR(100) NOT NULL,
                descricao TEXT,
                obrigatorio BOOLEAN DEFAULT TRUE,
                podem_aprovar INTEGER[], -- IDs dos usuários que podem aprovar
                grupos_aprovacao TEXT[], -- Grupos que podem aprovar
                valor_limite DECIMAL(15,2),
                prazo_aprovacao_horas INTEGER DEFAULT 48,
                aprovacao_automatica_apos_prazo BOOLEAN DEFAULT FALSE,
                escalacao_usuario_id INTEGER,
                condicoes_aprovacao JSONB,
                ativo BOOLEAN DEFAULT TRUE
            )
            """)
            
            # Tabela de solicitações de aprovação
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS solicitacoes_aprovacao (
                id SERIAL PRIMARY KEY,
                tipo_workflow_id INTEGER REFERENCES tipos_workflow(id),
                codigo_solicitacao VARCHAR(50) UNIQUE NOT NULL,
                titulo VARCHAR(255) NOT NULL,
                descricao TEXT,
                entidade_origem VARCHAR(50), -- 'movimentacao', 'compra', etc.
                id_entidade_origem INTEGER,
                valor_total DECIMAL(15,2) DEFAULT 0,
                prioridade VARCHAR(20) DEFAULT 'normal',
                dados_solicitacao JSONB,
                anexos TEXT[],
                usuario_solicitante_id INTEGER NOT NULL,
                data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_limite DATE,
                status_geral VARCHAR(50) DEFAULT 'pendente',
                nivel_atual INTEGER DEFAULT 1,
                observacoes TEXT,
                data_finalizacao TIMESTAMP,
                usuario_finalizacao_id INTEGER,
                motivo_finalizacao TEXT
            )
            """)
            
            # Tabela de aprovações individuais por nível
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS aprovacoes_niveis (
                id SERIAL PRIMARY KEY,
                solicitacao_id INTEGER REFERENCES solicitacoes_aprovacao(id),
                nivel_aprovacao_id INTEGER REFERENCES niveis_aprovacao(id),
                nivel INTEGER NOT NULL,
                usuario_aprovador_id INTEGER,
                data_aprovacao TIMESTAMP,
                status VARCHAR(50) DEFAULT 'pendente',
                comentarios TEXT,
                anexos_aprovacao TEXT[],
                delegado_por_id INTEGER,
                data_escalacao TIMESTAMP,
                notificado BOOLEAN DEFAULT FALSE,
                data_notificacao TIMESTAMP
            )
            """)
            
            # Tabela de histórico de ações
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_workflows (
                id SERIAL PRIMARY KEY,
                solicitacao_id INTEGER REFERENCES solicitacoes_aprovacao(id),
                usuario_id INTEGER NOT NULL,
                acao VARCHAR(100) NOT NULL,
                nivel_anterior INTEGER,
                nivel_novo INTEGER,
                status_anterior VARCHAR(50),
                status_novo VARCHAR(50),
                comentarios TEXT,
                dados_acao JSONB,
                data_acao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_usuario INET
            )
            """)
            
            # Tabela de delegações
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS delegacoes_aprovacao (
                id SERIAL PRIMARY KEY,
                usuario_delegante_id INTEGER NOT NULL,
                usuario_delegado_id INTEGER NOT NULL,
                tipo_workflow_id INTEGER REFERENCES tipos_workflow(id),
                nivel_aprovacao_id INTEGER REFERENCES niveis_aprovacao(id),
                data_inicio DATE DEFAULT CURRENT_DATE,
                data_fim DATE,
                motivo TEXT,
                ativo BOOLEAN DEFAULT TRUE,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Tabela de notificações de workflow
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS notificacoes_workflow (
                id SERIAL PRIMARY KEY,
                solicitacao_id INTEGER REFERENCES solicitacoes_aprovacao(id),
                usuario_destinatario_id INTEGER NOT NULL,
                tipo_notificacao VARCHAR(50) NOT NULL,
                titulo VARCHAR(255),
                mensagem TEXT,
                data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_leitura TIMESTAMP,
                canal VARCHAR(50) DEFAULT 'sistema',
                tentativas_envio INTEGER DEFAULT 1,
                sucesso_envio BOOLEAN DEFAULT TRUE
            )
            """)
            
            conn.commit()
            
            # Inserir dados de exemplo
            self.inserir_workflows_exemplo()
            
        except Exception as e:
            st.error(f"Erro ao criar tabelas de workflows: {e}")
    
    def inserir_workflows_exemplo(self):
        """Insere tipos de workflow de exemplo"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se já existem workflows
        cursor.execute("SELECT COUNT(*) FROM tipos_workflow")
        if cursor.fetchone()[0] > 0:
            return
        
        workflows_exemplo = [
            {
                'nome': 'Aprovação de Movimentações Alto Valor',
                'descricao': 'Aprovação para movimentações acima de R$ 5.000',
                'tipo_entidade': 'movimentacao',
                'valor_minimo': 5000.00,
                'dias_expiracao': 5
            },
            {
                'nome': 'Aprovação de Compras',
                'descricao': 'Aprovação para todas as compras de equipamentos',
                'tipo_entidade': 'compra',
                'valor_minimo': 1000.00,
                'dias_expiracao': 7
            },
            {
                'nome': 'Requisição de Equipamentos',
                'descricao': 'Aprovação para requisições de equipamentos especiais',
                'tipo_entidade': 'requisicao',
                'valor_minimo': 0.00,
                'dias_expiracao': 3
            },
            {
                'nome': 'Aprovação de Manutenção Corretiva',
                'descricao': 'Aprovação para manutenções não programadas',
                'tipo_entidade': 'manutencao',
                'valor_minimo': 2000.00,
                'dias_expiracao': 2
            }
        ]
        
        for workflow in workflows_exemplo:
            cursor.execute("""
            INSERT INTO tipos_workflow 
            (nome, descricao, tipo_entidade, valor_minimo_aprovacao, dias_expiracao, usuario_criacao_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """, [
                workflow['nome'], workflow['descricao'], workflow['tipo_entidade'],
                workflow['valor_minimo'], workflow['dias_expiracao'], 1
            ])
            
            workflow_id = cursor.fetchone()[0]
            
            # Inserir níveis de aprovação para cada workflow
            niveis = [
                {
                    'nivel': 1,
                    'nome': 'Supervisão',
                    'descricao': 'Aprovação do supervisor direto',
                    'prazo': 24,
                    'podem_aprovar': [2, 3]  # IDs dos supervisores
                },
                {
                    'nivel': 2,
                    'nome': 'Gerência',
                    'descricao': 'Aprovação da gerência',
                    'prazo': 48,
                    'podem_aprovar': [4, 5]  # IDs dos gerentes
                }
            ]
            
            # Para compras acima de R$ 10.000, adicionar nível diretor
            if workflow['valor_minimo'] >= 5000:
                niveis.append({
                    'nivel': 3,
                    'nome': 'Diretoria',
                    'descricao': 'Aprovação da diretoria',
                    'prazo': 72,
                    'podem_aprovar': [6]  # ID do diretor
                })
            
            for nivel in niveis:
                cursor.execute("""
                INSERT INTO niveis_aprovacao
                (tipo_workflow_id, nivel, nome_nivel, descricao, podem_aprovar, 
                 prazo_aprovacao_horas)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, [
                    workflow_id, nivel['nivel'], nivel['nome'], nivel['descricao'],
                    nivel['podem_aprovar'], nivel['prazo']
                ])
        
        conn.commit()
    
    def criar_solicitacao_aprovacao(self, dados: Dict[str, Any]) -> int:
        """Cria nova solicitação de aprovação"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Gerar código único
        codigo = self.gerar_codigo_solicitacao(dados['tipo_workflow_id'])
        
        cursor.execute("""
        INSERT INTO solicitacoes_aprovacao
        (tipo_workflow_id, codigo_solicitacao, titulo, descricao, entidade_origem,
         id_entidade_origem, valor_total, prioridade, dados_solicitacao,
         usuario_solicitante_id, data_limite, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, [
            dados['tipo_workflow_id'], codigo, dados['titulo'], dados['descricao'],
            dados.get('entidade_origem'), dados.get('id_entidade_origem'),
            dados.get('valor_total', 0), dados.get('prioridade', 'normal'),
            json.dumps(dados.get('dados_adicionais', {})),
            dados['usuario_solicitante_id'], 
            datetime.now().date() + timedelta(days=dados.get('dias_limite', 7)),
            dados.get('observacoes', '')
        ])
        
        solicitacao_id = cursor.fetchone()[0]
        
        # Criar aprovações para todos os níveis
        self.criar_aprovacoes_niveis(solicitacao_id, dados['tipo_workflow_id'])
        
        # Registrar no histórico
        self.registrar_historico(solicitacao_id, dados['usuario_solicitante_id'],
                               'criacao', 0, 1, None, 'pendente', 
                               f"Solicitação criada: {dados['titulo']}")
        
        # Notificar primeiro nível
        self.notificar_aprovadores(solicitacao_id, 1)
        
        conn.commit()
        
        log_acao("workflow", "criar_solicitacao", f"Solicitação {codigo} criada")
        return solicitacao_id
    
    def gerar_codigo_solicitacao(self, tipo_workflow_id: int) -> str:
        """Gera código único para solicitação"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Buscar prefixo do tipo de workflow
        cursor.execute("SELECT tipo_entidade FROM tipos_workflow WHERE id = %s", [tipo_workflow_id])
        tipo_entidade = cursor.fetchone()[0]
        
        prefixos = {
            'movimentacao': 'MOV',
            'compra': 'COM',
            'requisicao': 'REQ',
            'manutencao': 'MAN',
            'reserva': 'RES'
        }
        
        prefixo = prefixos.get(tipo_entidade, 'SOL')
        ano_mes = datetime.now().strftime('%Y%m')
        
        # Buscar próximo número sequencial
        cursor.execute("""
        SELECT MAX(CAST(SUBSTRING(codigo_solicitacao FROM '[0-9]+$') AS INTEGER))
        FROM solicitacoes_aprovacao 
        WHERE codigo_solicitacao ILIKE %s
        """, [f"{prefixo}{ano_mes}%"])
        
        ultimo_numero = cursor.fetchone()[0] or 0
        proximo_numero = ultimo_numero + 1
        
        return f"{prefixo}{ano_mes}{proximo_numero:04d}"
    
    def criar_aprovacoes_niveis(self, solicitacao_id: int, tipo_workflow_id: int):
        """Cria registros de aprovação para todos os níveis"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id, nivel FROM niveis_aprovacao 
        WHERE tipo_workflow_id = %s AND ativo = TRUE
        ORDER BY nivel
        """, [tipo_workflow_id])
        
        niveis = cursor.fetchall()
        
        for nivel in niveis:
            cursor.execute("""
            INSERT INTO aprovacoes_niveis 
            (solicitacao_id, nivel_aprovacao_id, nivel)
            VALUES (%s, %s, %s)
            """, [solicitacao_id, nivel['id'], nivel['nivel']])
    
    def processar_aprovacao(self, solicitacao_id: int, usuario_id: int, acao: str, comentarios: str = ""):
        """Processa aprovação ou rejeição de uma solicitação"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Buscar dados da solicitação
            cursor.execute("""
            SELECT s.*, t.nome as tipo_workflow
            FROM solicitacoes_aprovacao s
            JOIN tipos_workflow t ON s.tipo_workflow_id = t.id
            WHERE s.id = %s
            """, [solicitacao_id])
            
            solicitacao = cursor.fetchone()
            
            if not solicitacao or solicitacao['status_geral'] != 'pendente':
                raise ValueError("Solicitação não encontrada ou já processada")
            
            # Verificar se usuário pode aprovar no nível atual
            cursor.execute("""
            SELECT an.* FROM aprovacoes_niveis an
            JOIN niveis_aprovacao na ON an.nivel_aprovacao_id = na.id
            WHERE an.solicitacao_id = %s AND an.nivel = %s AND an.status = 'pendente'
            AND (%s = ANY(na.podem_aprovar) OR EXISTS (
                SELECT 1 FROM delegacoes_aprovacao d 
                WHERE d.usuario_delegado_id = %s AND d.nivel_aprovacao_id = na.id 
                AND d.ativo = TRUE AND (d.data_fim IS NULL OR d.data_fim >= CURRENT_DATE)
            ))
            """, [solicitacao_id, solicitacao['nivel_atual'], usuario_id, usuario_id])
            
            aprovacao_nivel = cursor.fetchone()
            
            if not aprovacao_nivel:
                raise ValueError("Usuário não tem permissão para aprovar neste nível")
            
            # Processar ação
            if acao == 'aprovar':
                self._processar_aprovacao(solicitacao_id, aprovacao_nivel, usuario_id, comentarios)
            elif acao == 'rejeitar':
                self._processar_rejeicao(solicitacao_id, aprovacao_nivel, usuario_id, comentarios)
            else:
                raise ValueError("Ação inválida")
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise
    
    def _processar_aprovacao(self, solicitacao_id: int, aprovacao_nivel: Dict, usuario_id: int, comentarios: str):
        """Processa aprovação de um nível"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Atualizar aprovação do nível
        cursor.execute("""
        UPDATE aprovacoes_niveis 
        SET status = 'aprovado', usuario_aprovador_id = %s, 
            data_aprovacao = CURRENT_TIMESTAMP, comentarios = %s
        WHERE id = %s
        """, [usuario_id, comentarios, aprovacao_nivel['id']])
        
        # Verificar se há próximo nível
        cursor.execute("""
        SELECT MAX(nivel) FROM niveis_aprovacao na
        JOIN tipos_workflow tw ON na.tipo_workflow_id = tw.id
        JOIN solicitacoes_aprovacao sa ON sa.tipo_workflow_id = tw.id
        WHERE sa.id = %s AND na.ativo = TRUE
        """, [solicitacao_id])
        
        max_nivel = cursor.fetchone()[0]
        nivel_atual = aprovacao_nivel['nivel']
        
        if nivel_atual >= max_nivel:
            # Última aprovação - finalizar solicitação
            cursor.execute("""
            UPDATE solicitacoes_aprovacao 
            SET status_geral = 'aprovado', data_finalizacao = CURRENT_TIMESTAMP,
                usuario_finalizacao_id = %s, motivo_finalizacao = %s
            WHERE id = %s
            """, [usuario_id, f"Aprovado no nível {nivel_atual}: {comentarios}", solicitacao_id])
            
            self.registrar_historico(solicitacao_id, usuario_id, 'finalizacao', 
                                   nivel_atual, nivel_atual, 'pendente', 'aprovado',
                                   f"Solicitação totalmente aprovada: {comentarios}")
            
            # Notificar solicitante
            self.notificar_finalizacao(solicitacao_id, 'aprovado')
            
        else:
            # Avançar para próximo nível
            proximo_nivel = nivel_atual + 1
            cursor.execute("""
            UPDATE solicitacoes_aprovacao 
            SET nivel_atual = %s
            WHERE id = %s
            """, [proximo_nivel, solicitacao_id])
            
            self.registrar_historico(solicitacao_id, usuario_id, 'aprovacao_nivel',
                                   nivel_atual, proximo_nivel, 'pendente', 'pendente',
                                   f"Aprovado nível {nivel_atual}: {comentarios}")
            
            # Notificar próximo nível
            self.notificar_aprovadores(solicitacao_id, proximo_nivel)
    
    def _processar_rejeicao(self, solicitacao_id: int, aprovacao_nivel: Dict, usuario_id: int, comentarios: str):
        """Processa rejeição da solicitação"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Atualizar aprovação do nível
        cursor.execute("""
        UPDATE aprovacoes_niveis 
        SET status = 'rejeitado', usuario_aprovador_id = %s,
            data_aprovacao = CURRENT_TIMESTAMP, comentarios = %s
        WHERE id = %s
        """, [usuario_id, comentarios, aprovacao_nivel['id']])
        
        # Rejeitar solicitação inteira
        cursor.execute("""
        UPDATE solicitacoes_aprovacao 
        SET status_geral = 'rejeitado', data_finalizacao = CURRENT_TIMESTAMP,
            usuario_finalizacao_id = %s, motivo_finalizacao = %s
        WHERE id = %s
        """, [usuario_id, f"Rejeitado no nível {aprovacao_nivel['nivel']}: {comentarios}", solicitacao_id])
        
        self.registrar_historico(solicitacao_id, usuario_id, 'rejeicao',
                               aprovacao_nivel['nivel'], 0, 'pendente', 'rejeitado',
                               f"Rejeitado: {comentarios}")
        
        # Notificar solicitante
        self.notificar_finalizacao(solicitacao_id, 'rejeitado')
    
    def registrar_historico(self, solicitacao_id: int, usuario_id: int, acao: str,
                           nivel_anterior: int, nivel_novo: int, status_anterior: str,
                           status_novo: str, comentarios: str):
        """Registra ação no histórico"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO historico_workflows
        (solicitacao_id, usuario_id, acao, nivel_anterior, nivel_novo,
         status_anterior, status_novo, comentarios)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, [solicitacao_id, usuario_id, acao, nivel_anterior, nivel_novo,
              status_anterior, status_novo, comentarios])
    
    def notificar_aprovadores(self, solicitacao_id: int, nivel: int):
        """Notifica aprovadores do nível especificado"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Buscar aprovadores do nível
        cursor.execute("""
        SELECT DISTINCT unnest(na.podem_aprovar) as usuario_id, sa.titulo, sa.codigo_solicitacao
        FROM niveis_aprovacao na
        JOIN tipos_workflow tw ON na.tipo_workflow_id = tw.id
        JOIN solicitacoes_aprovacao sa ON sa.tipo_workflow_id = tw.id
        WHERE sa.id = %s AND na.nivel = %s AND na.ativo = TRUE
        """, [solicitacao_id, nivel])
        
        aprovadores = cursor.fetchall()
        
        for aprovador in aprovadores:
            cursor.execute("""
            INSERT INTO notificacoes_workflow
            (solicitacao_id, usuario_destinatario_id, tipo_notificacao, titulo, mensagem)
            VALUES (%s, %s, %s, %s, %s)
            """, [
                solicitacao_id, aprovador['usuario_id'], 'pendente_aprovacao',
                f"Aprovação Pendente: {aprovador['codigo_solicitacao']}",
                f"A solicitação '{aprovador['titulo']}' aguarda sua aprovação no nível {nivel}."
            ])
    
    def notificar_finalizacao(self, solicitacao_id: int, status_final: str):
        """Notifica solicitante sobre finalização"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT usuario_solicitante_id, titulo, codigo_solicitacao
        FROM solicitacoes_aprovacao WHERE id = %s
        """, [solicitacao_id])
        
        solicitacao = cursor.fetchone()
        
        if solicitacao:
            cursor.execute("""
            INSERT INTO notificacoes_workflow
            (solicitacao_id, usuario_destinatario_id, tipo_notificacao, titulo, mensagem)
            VALUES (%s, %s, %s, %s, %s)
            """, [
                solicitacao_id, solicitacao['usuario_solicitante_id'], f'solicitacao_{status_final}',
                f"Solicitação {status_final.title()}: {solicitacao['codigo_solicitacao']}",
                f"Sua solicitação '{solicitacao['titulo']}' foi {status_final}."
            ])
    
    def verificar_solicitacoes_expiradas(self):
        """Verifica e processa solicitações expiradas"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE solicitacoes_aprovacao 
        SET status_geral = 'cancelado', data_finalizacao = CURRENT_TIMESTAMP,
            motivo_finalizacao = 'Solicitação expirada por prazo'
        WHERE status_geral = 'pendente' AND data_limite < CURRENT_DATE
        RETURNING id, codigo_solicitacao
        """)
        
        expiradas = cursor.fetchall()
        
        for solicitacao in expiradas:
            self.registrar_historico(solicitacao['id'], 1, 'expiracao', 0, 0,
                                   'pendente', 'cancelado', 'Solicitação expirada automaticamente')
        
        conn.commit()
        return len(expiradas)

def show_workflows_aprovacao_page():
    """Exibe página de workflows de aprovação"""
    st.title("🔄 Sistema de Workflows de Aprovação")
    st.markdown("Fluxos configuráveis para aprovação de movimentações, compras e requisições")
    
    manager = WorkflowManager()
    
    # Verificar solicitações expiradas
    expiradas = manager.verificar_solicitacoes_expiradas()
    if expiradas > 0:
        st.warning(f"⚠️ {expiradas} solicitação(ões) expirada(s) foram canceladas automaticamente")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard", "📝 Nova Solicitação", "⏳ Pendentes", 
        "✅ Minhas Aprovações", "📋 Histórico", "⚙️ Configurações"
    ])
    
    with tab1:
        st.subheader("📊 Dashboard de Workflows")
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cursor.execute("SELECT COUNT(*) FROM solicitacoes_aprovacao WHERE status_geral = 'pendente'")
            pendentes = cursor.fetchone()[0]
            st.metric("Pendentes", pendentes)
        
        with col2:
            cursor.execute("""
            SELECT COUNT(*) FROM solicitacoes_aprovacao 
            WHERE data_solicitacao >= CURRENT_DATE - INTERVAL '7 days'
            """)
            semana = cursor.fetchone()[0]
            st.metric("Esta Semana", semana)
        
        with col3:
            cursor.execute("""
            SELECT COUNT(*) FROM solicitacoes_aprovacao 
            WHERE status_geral = 'aprovado' AND EXTRACT(MONTH FROM data_finalizacao) = EXTRACT(MONTH FROM CURRENT_DATE)
            """)
            aprovadas_mes = cursor.fetchone()[0]
            st.metric("Aprovadas (Mês)", aprovadas_mes)
        
        with col4:
            cursor.execute("""
            SELECT ROUND(AVG(EXTRACT(EPOCH FROM (data_finalizacao - data_solicitacao))/3600), 1)
            FROM solicitacoes_aprovacao 
            WHERE status_geral IN ('aprovado', 'rejeitado') AND data_finalizacao IS NOT NULL
            """)
            tempo_medio = cursor.fetchone()[0] or 0
            st.metric("Tempo Médio (h)", f"{tempo_medio}")
        
        # Gráfico de solicitações por status
        cursor.execute("""
        SELECT status_geral, COUNT(*) as total
        FROM solicitacoes_aprovacao
        WHERE data_solicitacao >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY status_geral
        """)
        
        status_data = cursor.fetchall()
        
        if status_data:
            df_status = pd.DataFrame(status_data, columns=['status', 'total'])
            fig1 = px.pie(df_status, values='total', names='status',
                         title='Distribuição por Status (30 dias)')
            st.plotly_chart(fig1, use_container_width=True)
        
        # Solicitações urgentes
        cursor.execute("""
        SELECT codigo_solicitacao, titulo, prioridade, data_limite, 
               CURRENT_DATE - data_limite as dias_atraso
        FROM solicitacoes_aprovacao 
        WHERE status_geral = 'pendente' AND (prioridade = 'alta' OR data_limite <= CURRENT_DATE + INTERVAL '2 days')
        ORDER BY data_limite
        """)
        
        urgentes = cursor.fetchall()
        
        if urgentes:
            st.subheader("🚨 Solicitações Urgentes")
            for solicitacao in urgentes:
                if solicitacao['dias_atraso'] and solicitacao['dias_atraso'] > 0:
                    st.error(f"🔴 **{solicitacao['codigo_solicitacao']}** - {solicitacao['titulo']} (VENCIDA há {solicitacao['dias_atraso']} dias)")
                else:
                    st.warning(f"⚡ **{solicitacao['codigo_solicitacao']}** - {solicitacao['titulo']} (Vence: {solicitacao['data_limite']})")
    
    with tab2:
        st.subheader("📝 Nova Solicitação de Aprovação")
        
        with st.form("nova_solicitacao"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Buscar tipos de workflow
                cursor.execute("SELECT id, nome, descricao FROM tipos_workflow WHERE ativo = TRUE")
                tipos = cursor.fetchall()
                
                if tipos:
                    tipo_opcoes = {f"{t.nome}": t.id for t in tipos}
                    tipo_selecionado = st.selectbox("Tipo de Workflow*:", list(tipo_opcoes.keys()))
                    
                    titulo = st.text_input("Título da Solicitação*:")
                    valor_total = st.number_input("Valor Total (R$):", min_value=0.0, step=100.0)
                else:
                    st.error("❌ Nenhum tipo de workflow configurado")
                    tipo_selecionado = None
            
            with col2:
                prioridade = st.selectbox("Prioridade:", ["normal", "alta", "baixa"])
                
                # Buscar obras para associação
                cursor.execute("SELECT id, nome FROM obras WHERE status = 'ativo'")
                obras = cursor.fetchall()
                obra_opcoes = {f"{o.nome}": o.id for o in obras} if obras else {}
                obra_selecionada = st.selectbox("Obra/Projeto:", ["Nenhuma"] + list(obra_opcoes.keys()))
            
            descricao = st.text_area("Descrição/Justificativa*:", height=100)
            
            # Dados adicionais específicos por tipo
            dados_adicionais = {}
            
            if tipo_selecionado:
                st.subheader("📋 Dados Específicos")
                
                # Buscar configurações específicas do tipo
                tipo_id = tipo_opcoes[tipo_selecionado]
                cursor.execute("SELECT tipo_entidade FROM tipos_workflow WHERE id = %s", [tipo_id])
                tipo_entidade = cursor.fetchone()[0]
                
                if tipo_entidade == 'movimentacao':
                    col_mov1, col_mov2 = st.columns(2)
                    with col_mov1:
                        dados_adicionais['tipo_movimentacao'] = st.selectbox("Tipo:", ["saida", "entrada", "transferencia"])
                        dados_adicionais['equipamento_id'] = st.number_input("ID Equipamento:", min_value=1, step=1)
                    with col_mov2:
                        dados_adicionais['quantidade'] = st.number_input("Quantidade:", min_value=1, step=1)
                        dados_adicionais['motivo'] = st.text_input("Motivo da Movimentação:")
                
                elif tipo_entidade == 'compra':
                    col_comp1, col_comp2 = st.columns(2)
                    with col_comp1:
                        dados_adicionais['fornecedor'] = st.text_input("Fornecedor:")
                        dados_adicionais['prazo_entrega'] = st.number_input("Prazo Entrega (dias):", min_value=1, value=30)
                    with col_comp2:
                        dados_adicionais['forma_pagamento'] = st.selectbox("Forma Pagamento:", ["À vista", "30 dias", "60 dias", "90 dias"])
                        dados_adicionais['urgente'] = st.checkbox("Compra Urgente")
            
            observacoes = st.text_area("Observações Adicionais:")
            
            if st.form_submit_button("📤 Enviar para Aprovação"):
                if tipo_selecionado and titulo and descricao:
                    try:
                        dados_solicitacao = {
                            'tipo_workflow_id': tipo_opcoes[tipo_selecionado],
                            'titulo': titulo,
                            'descricao': descricao,
                            'valor_total': valor_total,
                            'prioridade': prioridade,
                            'dados_adicionais': dados_adicionais,
                            'observacoes': observacoes,
                            'usuario_solicitante_id': 1,  # Em produção, pegar do session
                            'id_entidade_origem': obra_opcoes.get(obra_selecionada) if obra_selecionada != "Nenhuma" else None
                        }
                        
                        solicitacao_id = manager.criar_solicitacao_aprovacao(dados_solicitacao)
                        st.success(f"✅ Solicitação enviada para aprovação! ID: {solicitacao_id}")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao criar solicitação: {e}")
                else:
                    st.error("❌ Preencha os campos obrigatórios")
    
    with tab3:
        st.subheader("⏳ Solicitações Pendentes")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cursor.execute("SELECT DISTINCT nome FROM tipos_workflow WHERE ativo = TRUE")
            tipos_filtro = [row[0] for row in cursor.fetchall()]
            tipo_filtro = st.selectbox("Filtrar por Tipo:", ["Todos"] + tipos_filtro)
        
        with col2:
            prioridade_filtro = st.selectbox("Filtrar por Prioridade:", ["Todas", "alta", "normal", "baixa"])
        
        with col3:
            cursor.execute("SELECT DISTINCT nivel_atual FROM solicitacoes_aprovacao WHERE status_geral = 'pendente'")
            niveis = [row[0] for row in cursor.fetchall()]
            nivel_filtro = st.selectbox("Filtrar por Nível:", ["Todos"] + [f"Nível {n}" for n in sorted(niveis)])
        
        # Query das solicitações pendentes
        query = """
        SELECT s.*, t.nome as tipo_workflow, 
               u.nome as solicitante_nome,
               EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - s.data_solicitacao))/3600 as horas_pendente
        FROM solicitacoes_aprovacao s
        JOIN tipos_workflow t ON s.tipo_workflow_id = t.id
        LEFT JOIN usuarios u ON s.usuario_solicitante_id = u.id
        WHERE s.status_geral = 'pendente'
        """
        params = []
        
        if tipo_filtro != "Todos":
            query += " AND t.nome = %s"
            params.append(tipo_filtro)
        
        if prioridade_filtro != "Todas":
            query += " AND s.prioridade = %s"
            params.append(prioridade_filtro)
        
        if nivel_filtro != "Todos":
            nivel_num = int(nivel_filtro.split()[1])
            query += " AND s.nivel_atual = %s"
            params.append(nivel_num)
        
        query += " ORDER BY s.prioridade DESC, s.data_solicitacao ASC"
        
        cursor.execute(query, params)
        pendentes = cursor.fetchall()
        
        if pendentes:
            for solicitacao in pendentes:
                # Determinar urgência
                if solicitacao['prioridade'] == 'alta' or (solicitacao['data_limite'] and 
                    solicitacao['data_limite'] <= datetime.now().date()):
                    urgencia_icon = "🔴"
                elif solicitacao['horas_pendente'] > 48:
                    urgencia_icon = "🟡"
                else:
                    urgencia_icon = "🟢"
                
                with st.expander(f"{urgencia_icon} {solicitacao['codigo_solicitacao']} - {solicitacao['titulo']} (Nível {solicitacao['nivel_atual']})"):
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.write(f"**Tipo:** {solicitacao['tipo_workflow']}")
                        st.write(f"**Solicitante:** {solicitacao['solicitante_nome'] or 'N/A'}")
                        st.write(f"**Data:** {solicitacao['data_solicitacao'].strftime('%d/%m/%Y %H:%M')}")
                    
                    with col_b:
                        st.write(f"**Prioridade:** {solicitacao['prioridade'].title()}")
                        st.write(f"**Valor:** R$ {solicitacao['valor_total']:,.2f}")
                        st.write(f"**Limite:** {solicitacao['data_limite']}")
                    
                    with col_c:
                        st.write(f"**Nível Atual:** {solicitacao['nivel_atual']}")
                        st.write(f"**Pendente há:** {solicitacao['horas_pendente']:.1f}h")
                    
                    st.write(f"**Descrição:** {solicitacao['descricao']}")
                    
                    if solicitacao['dados_solicitacao']:
                        dados = json.loads(solicitacao['dados_solicitacao'])
                        if dados:
                            st.write("**Dados Específicos:**")
                            st.json(dados)
        else:
            st.info("ℹ️ Nenhuma solicitação pendente")
    
    with tab4:
        st.subheader("✅ Minhas Aprovações")
        
        # Simular usuário logado (em produção, pegar do session)
        usuario_atual_id = st.selectbox("Simular Usuário:", [1, 2, 3, 4, 5, 6], 
                                       format_func=lambda x: f"Usuário {x}")
        
        # Buscar aprovações pendentes para o usuário
        cursor.execute("""
        SELECT DISTINCT s.*, t.nome as tipo_workflow, na.nome_nivel,
               u.nome as solicitante_nome, an.comentarios as comentarios_nivel
        FROM solicitacoes_aprovacao s
        JOIN tipos_workflow t ON s.tipo_workflow_id = t.id
        JOIN aprovacoes_niveis an ON s.id = an.solicitacao_id
        JOIN niveis_aprovacao na ON an.nivel_aprovacao_id = na.id
        LEFT JOIN usuarios u ON s.usuario_solicitante_id = u.id
        WHERE s.status_geral = 'pendente' 
        AND an.nivel = s.nivel_atual 
        AND an.status = 'pendente'
        AND (%s = ANY(na.podem_aprovar) OR EXISTS (
            SELECT 1 FROM delegacoes_aprovacao d 
            WHERE d.usuario_delegado_id = %s AND d.nivel_aprovacao_id = na.id 
            AND d.ativo = TRUE AND (d.data_fim IS NULL OR d.data_fim >= CURRENT_DATE)
        ))
        ORDER BY s.prioridade DESC, s.data_solicitacao ASC
        """, [usuario_atual_id, usuario_atual_id])
        
        minhas_aprovacoes = cursor.fetchall()
        
        if minhas_aprovacoes:
            for solicitacao in minhas_aprovacoes:
                with st.expander(f"📋 {solicitacao['codigo_solicitacao']} - {solicitacao['titulo']} ({solicitacao['nome_nivel']})"):
                    col_a, col_b = st.columns([2, 1])
                    
                    with col_a:
                        st.write(f"**Tipo:** {solicitacao['tipo_workflow']}")
                        st.write(f"**Solicitante:** {solicitacao['solicitante_nome'] or 'N/A'}")
                        st.write(f"**Valor:** R$ {solicitacao['valor_total']:,.2f}")
                        st.write(f"**Prioridade:** {solicitacao['prioridade'].title()}")
                        st.write(f"**Descrição:** {solicitacao['descricao']}")
                        
                        if solicitacao['dados_solicitacao']:
                            dados = json.loads(solicitacao['dados_solicitacao'])
                            if dados:
                                st.write("**Detalhes Específicos:**")
                                for chave, valor in dados.items():
                                    st.write(f"- **{chave.replace('_', ' ').title()}:** {valor}")
                    
                    with col_b:
                        st.write("**🎯 Ação de Aprovação**")
                        
                        comentarios = st.text_area("Comentários:", 
                                                  key=f"comment_{solicitacao['id']}")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            if st.button("✅ Aprovar", key=f"apr_{solicitacao['id']}"):
                                try:
                                    manager.processar_aprovacao(solicitacao['id'], usuario_atual_id, 
                                                              'aprovar', comentarios)
                                    st.success("✅ Solicitação aprovada!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Erro: {e}")
                        
                        with col_btn2:
                            if st.button("❌ Rejeitar", key=f"rej_{solicitacao['id']}"):
                                if comentarios.strip():
                                    try:
                                        manager.processar_aprovacao(solicitacao['id'], usuario_atual_id,
                                                                  'rejeitar', comentarios)
                                        st.success("✅ Solicitação rejeitada!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Erro: {e}")
                                else:
                                    st.error("❌ Comentário obrigatório para rejeição")
        else:
            st.info("ℹ️ Nenhuma aprovação pendente para você")
        
        # Histórico das minhas aprovações
        st.subheader("📜 Histórico das Minhas Aprovações")
        
        cursor.execute("""
        SELECT s.codigo_solicitacao, s.titulo, an.status, an.data_aprovacao,
               an.comentarios, t.nome as tipo_workflow
        FROM aprovacoes_niveis an
        JOIN solicitacoes_aprovacao s ON an.solicitacao_id = s.id
        JOIN tipos_workflow t ON s.tipo_workflow_id = t.id
        WHERE an.usuario_aprovador_id = %s
        ORDER BY an.data_aprovacao DESC
        LIMIT 10
        """, [usuario_atual_id])
        
        historico = cursor.fetchall()
        
        if historico:
            for item in historico:
                status_icon = "✅" if item['status'] == 'aprovado' else "❌"
                st.write(f"{status_icon} **{item['codigo_solicitacao']}** - {item['titulo']} ({item['data_aprovacao'].strftime('%d/%m/%Y %H:%M')})")
                if item['comentarios']:
                    st.write(f"   💭 {item['comentarios']}")
        else:
            st.info("ℹ️ Nenhum histórico de aprovações")
    
    with tab5:
        st.subheader("📋 Histórico Completo")
        
        # Filtros para histórico
        col1, col2, col3 = st.columns(3)
        
        with col1:
            periodo = st.selectbox("Período:", ["7 dias", "30 dias", "90 dias", "Todos"])
        
        with col2:
            status_hist = st.selectbox("Status:", ["Todos", "pendente", "aprovado", "rejeitado", "cancelado"])
        
        with col3:
            cursor.execute("SELECT DISTINCT nome FROM tipos_workflow")
            tipos_hist = [row[0] for row in cursor.fetchall()]
            tipo_hist = st.selectbox("Tipo:", ["Todos"] + tipos_hist)
        
        # Query do histórico
        query_hist = """
        SELECT s.*, t.nome as tipo_workflow, u.nome as solicitante_nome
        FROM solicitacoes_aprovacao s
        JOIN tipos_workflow t ON s.tipo_workflow_id = t.id
        LEFT JOIN usuarios u ON s.usuario_solicitante_id = u.id
        WHERE 1=1
        """
        params_hist = []
        
        if periodo != "Todos":
            dias = int(periodo.split()[0])
            query_hist += " AND s.data_solicitacao >= CURRENT_DATE - INTERVAL '%s days'"
            params_hist.append(dias)
        
        if status_hist != "Todos":
            query_hist += " AND s.status_geral = %s"
            params_hist.append(status_hist)
        
        if tipo_hist != "Todos":
            query_hist += " AND t.nome = %s"
            params_hist.append(tipo_hist)
        
        query_hist += " ORDER BY s.data_solicitacao DESC LIMIT 50"
        
        cursor.execute(query_hist, params_hist)
        historico_completo = cursor.fetchall()
        
        if historico_completo:
            for solicitacao in historico_completo:
                status_color = {
                    'pendente': '🟡',
                    'aprovado': '🟢', 
                    'rejeitado': '🔴',
                    'cancelado': '⚪'
                }.get(solicitacao['status_geral'], '❓')
                
                with st.expander(f"{status_color} {solicitacao['codigo_solicitacao']} - {solicitacao['titulo']} ({solicitacao['status_geral'].upper()})"):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.write(f"**Tipo:** {solicitacao['tipo_workflow']}")
                        st.write(f"**Solicitante:** {solicitacao['solicitante_nome'] or 'N/A'}")
                        st.write(f"**Data Solicitação:** {solicitacao['data_solicitacao'].strftime('%d/%m/%Y %H:%M')}")
                        if solicitacao['data_finalizacao']:
                            st.write(f"**Data Finalização:** {solicitacao['data_finalizacao'].strftime('%d/%m/%Y %H:%M')}")
                    
                    with col_b:
                        st.write(f"**Valor:** R$ {solicitacao['valor_total']:,.2f}")
                        st.write(f"**Prioridade:** {solicitacao['prioridade'].title()}")
                        if solicitacao['motivo_finalizacao']:
                            st.write(f"**Motivo:** {solicitacao['motivo_finalizacao']}")
                    
                    st.write(f"**Descrição:** {solicitacao['descricao']}")
                    
                    # Mostrar timeline do workflow
                    if st.button("📊 Ver Timeline", key=f"timeline_{solicitacao['id']}"):
                        st.session_state[f'show_timeline_{solicitacao["id"]}'] = True
                    
                    if st.session_state.get(f'show_timeline_{solicitacao["id"]}', False):
                        cursor.execute("""
                        SELECT h.*, u.nome as usuario_nome
                        FROM historico_workflows h
                        LEFT JOIN usuarios u ON h.usuario_id = u.id
                        WHERE h.solicitacao_id = %s
                        ORDER BY h.data_acao
                        """, [solicitacao['id']])
                        
                        timeline = cursor.fetchall()
                        
                        st.write("**📅 Timeline:**")
                        for evento in timeline:
                            st.write(f"• **{evento['data_acao'].strftime('%d/%m %H:%M')}** - {evento['acao'].title()} por {evento['usuario_nome'] or 'Sistema'}")
                            if evento['comentarios']:
                                st.write(f"  💭 {evento['comentarios']}")
        else:
            st.info("ℹ️ Nenhum registro encontrado")
    
    with tab6:
        st.subheader("⚙️ Configurações de Workflows")
        
        # Gestão de tipos de workflow
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**Tipos de Workflow Configurados**")
            
            cursor.execute("SELECT * FROM tipos_workflow ORDER BY nome")
            workflows = cursor.fetchall()
            
            if workflows:
                for workflow in workflows:
                    with st.expander(f"🔧 {workflow['nome']} - {workflow['tipo_entidade']}"):
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            st.write(f"**Descrição:** {workflow['descricao']}")
                            st.write(f"**Valor Mínimo:** R$ {workflow['valor_minimo_aprovacao']:,.2f}")
                            st.write(f"**Prazo:** {workflow['dias_expiracao']} dias")
                        
                        with col_b:
                            st.write(f"**Ativo:** {'Sim' if workflow['ativo'] else 'Não'}")
                            st.write(f"**Aprovação Automática:** {'Sim' if workflow['aprovacao_automatica'] else 'Não'}")
                        
                        # Mostrar níveis de aprovação
                        cursor.execute("""
                        SELECT * FROM niveis_aprovacao 
                        WHERE tipo_workflow_id = %s AND ativo = TRUE
                        ORDER BY nivel
                        """, [workflow['id']])
                        
                        niveis = cursor.fetchall()
                        
                        if niveis:
                            st.write("**Níveis de Aprovação:**")
                            for nivel in niveis:
                                st.write(f"• **Nível {nivel['nivel']}:** {nivel['nome_nivel']} ({nivel['prazo_aprovacao_horas']}h)")
                                if nivel['podem_aprovar']:
                                    st.write(f"  👥 Aprovadores: {nivel['podem_aprovar']}")
            else:
                st.info("ℹ️ Nenhum workflow configurado")
        
        with col2:
            st.write("**Novo Tipo de Workflow**")
            
            with st.form("novo_workflow"):
                nome_workflow = st.text_input("Nome*:")
                descricao_workflow = st.text_area("Descrição:")
                tipo_entidade = st.selectbox("Tipo Entidade:", [
                    "movimentacao", "compra", "requisicao", "manutencao", "reserva"
                ])
                
                valor_minimo = st.number_input("Valor Mínimo (R$):", min_value=0.0, step=100.0)
                dias_expiracao = st.number_input("Dias para Expirar:", min_value=1, value=7)
                
                if st.form_submit_button("➕ Criar Workflow"):
                    if nome_workflow:
                        try:
                            cursor.execute("""
                            INSERT INTO tipos_workflow
                            (nome, descricao, tipo_entidade, valor_minimo_aprovacao, 
                             dias_expiracao, usuario_criacao_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """, [nome_workflow, descricao_workflow, tipo_entidade,
                                  valor_minimo, dias_expiracao, 1])
                            
                            conn.commit()
                            st.success("✅ Workflow criado!")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Erro: {e}")
                    else:
                        st.error("❌ Preencha o nome")
        
        # Estatísticas de performance
        st.subheader("📊 Estatísticas de Performance")
        
        cursor.execute("""
        SELECT 
            t.nome,
            COUNT(s.id) as total_solicitacoes,
            COUNT(CASE WHEN s.status_geral = 'aprovado' THEN 1 END) as aprovadas,
            COUNT(CASE WHEN s.status_geral = 'rejeitado' THEN 1 END) as rejeitadas,
            ROUND(AVG(EXTRACT(EPOCH FROM (s.data_finalizacao - s.data_solicitacao))/3600), 1) as tempo_medio_horas
        FROM tipos_workflow t
        LEFT JOIN solicitacoes_aprovacao s ON t.id = s.tipo_workflow_id
        WHERE s.data_solicitacao >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY t.id, t.nome
        ORDER BY total_solicitacoes DESC
        """)
        
        stats = cursor.fetchall()
        
        if stats:
            df_stats = pd.DataFrame(stats)
            
            # Gráfico de performance
            fig = px.bar(df_stats, x='nome', y=['aprovadas', 'rejeitadas'],
                        title='Performance por Tipo de Workflow (30 dias)')
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabela de estatísticas
            st.dataframe(df_stats, use_container_width=True)
        else:
            st.info("ℹ️ Dados insuficientes para estatísticas")

if __name__ == "__main__":
    show_workflows_aprovacao_page()