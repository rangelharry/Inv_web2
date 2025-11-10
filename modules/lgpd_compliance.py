"""
Sistema de LGPD/GDPR Compliance
Gestão de privacidade, consentimento, anonização e relatórios de conformidade
"""

import streamlit as st
import hashlib
import json
from datetime import datetime, timedelta
from database.connection import db
from modules.logs_auditoria import log_acao
from typing import Dict, List, Any
import pandas as pd

class LGPDManager:
    def __init__(self):
        self.criar_tabelas()
    
    def criar_tabelas(self):
        """Cria tabelas necessárias para LGPD/GDPR"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Tabela de consentimentos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS consentimentos_lgpd (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER,
                email VARCHAR(255),
                nome VARCHAR(255),
                tipo_consentimento VARCHAR(100) NOT NULL,
                descricao_consentimento TEXT,
                consentimento_dado BOOLEAN DEFAULT FALSE,
                data_consentimento TIMESTAMP,
                data_revogacao TIMESTAMP,
                ip_origem INET,
                user_agent TEXT,
                versao_termos VARCHAR(50),
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ativo BOOLEAN DEFAULT TRUE
            )
            """)
            
            # Tabela de dados pessoais (mapeamento)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS mapeamento_dados_pessoais (
                id SERIAL PRIMARY KEY,
                tabela VARCHAR(100) NOT NULL,
                campo VARCHAR(100) NOT NULL,
                tipo_dado VARCHAR(50) NOT NULL,
                categoria_titular VARCHAR(50),
                finalidade_processamento TEXT,
                base_legal VARCHAR(100),
                tempo_retencao_dias INTEGER,
                pode_anonimizar BOOLEAN DEFAULT TRUE,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Tabela de solicitações dos titulares
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS solicitacoes_titulares (
                id SERIAL PRIMARY KEY,
                tipo_solicitacao VARCHAR(50) NOT NULL,
                email_titular VARCHAR(255) NOT NULL,
                nome_titular VARCHAR(255),
                descricao_solicitacao TEXT,
                status VARCHAR(50) DEFAULT 'pendente',
                data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_resposta TIMESTAMP,
                resposta_detalhada TEXT,
                responsavel_id INTEGER,
                prazo_legal DATE,
                dados_afetados JSONB
            )
            """)
            
            # Tabela de incidentes de segurança
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS incidentes_seguranca (
                id SERIAL PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                descricao TEXT,
                gravidade VARCHAR(20) DEFAULT 'baixa',
                tipos_dados_afetados TEXT[],
                numero_titulares_afetados INTEGER,
                data_incidente TIMESTAMP,
                data_descoberta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_notificacao_anpd TIMESTAMP,
                data_comunicacao_titulares TIMESTAMP,
                medidas_corretivas TEXT,
                responsavel_id INTEGER,
                status VARCHAR(50) DEFAULT 'investigando',
                notificar_anpd BOOLEAN DEFAULT FALSE,
                notificar_titulares BOOLEAN DEFAULT FALSE
            )
            """)
            
            # Tabela de anonimização
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_anonimizacao (
                id SERIAL PRIMARY KEY,
                tabela_origem VARCHAR(100) NOT NULL,
                campo_origem VARCHAR(100) NOT NULL,
                registro_id INTEGER NOT NULL,
                valor_original_hash VARCHAR(255),
                tecnica_anonimizacao VARCHAR(100),
                data_anonimizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                responsavel_id INTEGER,
                motivo TEXT
            )
            """)
            
            conn.commit()
            
            # Inserir mapeamentos padrão
            self.inserir_mapeamentos_padrao()
            
        except Exception as e:
            st.error(f"Erro ao criar tabelas LGPD: {e}")
    
    def inserir_mapeamentos_padrao(self):
        """Insere mapeamentos padrão de dados pessoais"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se já existem mapeamentos
        cursor.execute("SELECT COUNT(*) FROM mapeamento_dados_pessoais")
        if cursor.fetchone()[0] > 0:
            return
        
        mapeamentos_padrao = [
            {
                'tabela': 'usuarios',
                'campo': 'nome',
                'tipo_dado': 'identificacao_direta',
                'categoria_titular': 'funcionario',
                'finalidade': 'Autenticação e controle de acesso ao sistema',
                'base_legal': 'execucao_contrato',
                'retencao': 2555,  # 7 anos
                'anonimizar': True
            },
            {
                'tabela': 'usuarios', 
                'campo': 'email',
                'tipo_dado': 'identificacao_direta',
                'categoria_titular': 'funcionario',
                'finalidade': 'Autenticação e comunicação',
                'base_legal': 'execucao_contrato',
                'retencao': 2555,
                'anonimizar': True
            },
            {
                'tabela': 'responsaveis',
                'campo': 'nome',
                'tipo_dado': 'identificacao_direta', 
                'categoria_titular': 'funcionario',
                'finalidade': 'Controle de responsabilidade por equipamentos',
                'base_legal': 'execucao_contrato',
                'retencao': 1825,  # 5 anos
                'anonimizar': True
            },
            {
                'tabela': 'logs_auditoria',
                'campo': 'usuario_nome',
                'tipo_dado': 'identificacao_direta',
                'categoria_titular': 'funcionario', 
                'finalidade': 'Auditoria e conformidade',
                'base_legal': 'obrigacao_legal',
                'retencao': 1825,
                'anonimizar': False  # Dados de auditoria podem ter restrições
            }
        ]
        
        for mapeamento in mapeamentos_padrao:
            cursor.execute("""
            INSERT INTO mapeamento_dados_pessoais 
            (tabela, campo, tipo_dado, categoria_titular, finalidade_processamento, 
             base_legal, tempo_retencao_dias, pode_anonimizar)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                mapeamento['tabela'], mapeamento['campo'], mapeamento['tipo_dado'],
                mapeamento['categoria_titular'], mapeamento['finalidade'],
                mapeamento['base_legal'], mapeamento['retencao'], mapeamento['anonimizar']
            ])
        
        conn.commit()
    
    def registrar_consentimento(self, email: str, nome: str, tipo: str, descricao: str, 
                              consentimento: bool, ip: str = "", user_agent: str = ""):
        """Registra consentimento do titular"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO consentimentos_lgpd 
        (email, nome, tipo_consentimento, descricao_consentimento, consentimento_dado,
         data_consentimento, ip_origem, user_agent, versao_termos)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, [
            email, nome, tipo, descricao, consentimento,
            datetime.now() if consentimento else None,
            ip, user_agent, "1.0"
        ])
        
        consentimento_id = cursor.fetchone()[0]
        conn.commit()
        
        log_acao("lgpd", "consentimento", f"Consentimento {tipo} registrado para {email}")
        return consentimento_id
    
    def revogar_consentimento(self, email: str, tipo: str):
        """Revoga consentimento específico"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE consentimentos_lgpd 
        SET consentimento_dado = FALSE, data_revogacao = %s
        WHERE email = %s AND tipo_consentimento = %s AND ativo = TRUE
        """, [datetime.now(), email, tipo])
        
        conn.commit()
        log_acao("lgpd", "revogacao", f"Consentimento {tipo} revogado para {email}")
    
    def criar_solicitacao_titular(self, tipo: str, email: str, nome: str = "", descricao: str = ""):
        """Cria solicitação do titular (acesso, retificação, exclusão, etc.)"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Calcular prazo legal
        prazos = {
            'acesso': 15,
            'retificacao': 15, 
            'exclusao': 15,
            'portabilidade': 15,
            'oposicao': 15,
            'informacao': 15
        }
        
        prazo_dias = prazos.get(tipo, 15)
        prazo_legal = datetime.now().date() + timedelta(days=prazo_dias)
        
        cursor.execute("""
        INSERT INTO solicitacoes_titulares
        (tipo_solicitacao, email_titular, nome_titular, descricao_solicitacao, prazo_legal)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """, [tipo, email, nome, descricao, prazo_legal])
        
        solicitacao_id = cursor.fetchone()[0]
        conn.commit()
        
        log_acao("lgpd", "solicitacao", f"Solicitação de {tipo} criada para {email}")
        return solicitacao_id
    
    def anonimizar_dados(self, tabela: str, campo: str, registro_id: int, motivo: str = ""):
        """Anonimiza dados específicos"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Buscar valor original
            cursor.execute(f"SELECT {campo} FROM {tabela} WHERE id = %s", [registro_id])
            resultado = cursor.fetchone()
            
            if not resultado:
                return False, "Registro não encontrado"
            
            valor_original = resultado[campo]
            valor_hash = hashlib.sha256(str(valor_original).encode()).hexdigest()[:16]
            
            # Gerar valor anonimizado
            if campo in ['nome', 'usuario_nome']:
                valor_anonimizado = f"Usuario_{valor_hash}"
            elif campo in ['email']:
                valor_anonimizado = f"anonimo_{valor_hash}@removido.com"
            else:
                valor_anonimizado = f"[ANONIMIZADO_{valor_hash}]"
            
            # Atualizar registro
            cursor.execute(f"UPDATE {tabela} SET {campo} = %s WHERE id = %s", 
                         [valor_anonimizado, registro_id])
            
            # Registrar no histórico
            cursor.execute("""
            INSERT INTO historico_anonimizacao
            (tabela_origem, campo_origem, registro_id, valor_original_hash, 
             tecnica_anonimizacao, responsavel_id, motivo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [tabela, campo, registro_id, valor_hash, 'pseudonimizacao', 1, motivo])
            
            conn.commit()
            log_acao("lgpd", "anonimizacao", f"Dados anonimizados: {tabela}.{campo} ID {registro_id}")
            
            return True, "Dados anonimizados com sucesso"
            
        except Exception as e:
            conn.rollback()
            return False, f"Erro na anonimização: {e}"
    
    def gerar_relatorio_conformidade(self):
        """Gera relatório de conformidade LGPD"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        relatorio = {
            'data_geracao': datetime.now(),
            'consentimentos': {},
            'solicitacoes': {},
            'incidentes': {},
            'dados_pessoais': {}
        }
        
        # Estatísticas de consentimentos
        cursor.execute("""
        SELECT tipo_consentimento, 
               COUNT(*) as total,
               COUNT(CASE WHEN consentimento_dado = TRUE THEN 1 END) as aceitos,
               COUNT(CASE WHEN data_revogacao IS NOT NULL THEN 1 END) as revogados
        FROM consentimentos_lgpd 
        WHERE ativo = TRUE
        GROUP BY tipo_consentimento
        """)
        
        relatorio['consentimentos'] = {
            row['tipo_consentimento']: {
                'total': row['total'],
                'aceitos': row['aceitos'],
                'revogados': row['revogados']
            }
            for row in cursor.fetchall()
        }
        
        # Estatísticas de solicitações
        cursor.execute("""
        SELECT tipo_solicitacao,
               COUNT(*) as total,
               COUNT(CASE WHEN status = 'pendente' THEN 1 END) as pendentes,
               COUNT(CASE WHEN status = 'atendido' THEN 1 END) as atendidas,
               COUNT(CASE WHEN prazo_legal < CURRENT_DATE AND status = 'pendente' THEN 1 END) as vencidas
        FROM solicitacoes_titulares
        GROUP BY tipo_solicitacao
        """)
        
        relatorio['solicitacoes'] = {
            row['tipo_solicitacao']: {
                'total': row['total'],
                'pendentes': row['pendentes'],
                'atendidas': row['atendidas'],
                'vencidas': row['vencidas']
            }
            for row in cursor.fetchall()
        }
        
        # Estatísticas de incidentes
        cursor.execute("""
        SELECT gravidade,
               COUNT(*) as total,
               COUNT(CASE WHEN notificar_anpd = TRUE THEN 1 END) as reportar_anpd
        FROM incidentes_seguranca
        GROUP BY gravidade
        """)
        
        relatorio['incidentes'] = {
            row['gravidade']: {
                'total': row['total'],
                'reportar_anpd': row['reportar_anpd']
            }
            for row in cursor.fetchall()
        }
        
        return relatorio

def show_lgpd_compliance_page():
    """Exibe página de conformidade LGPD/GDPR"""
    st.title("🔒 LGPD/GDPR Compliance")
    st.markdown("Sistema de gestão de privacidade e proteção de dados pessoais")
    
    manager = LGPDManager()
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Dashboard", "✅ Consentimentos", "📝 Solicitações", 
        "🚨 Incidentes", "🔒 Anonimização", "📊 Relatórios"
    ])
    
    with tab1:
        st.subheader("📊 Dashboard LGPD/GDPR")
        
        # Gerar relatório de conformidade
        relatorio = manager.gerar_relatorio_conformidade()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_consentimentos = sum(info['total'] for info in relatorio['consentimentos'].values())
            st.metric("Total Consentimentos", total_consentimentos)
        
        with col2:
            total_solicitacoes = sum(info['total'] for info in relatorio['solicitacoes'].values())
            st.metric("Solicitações Titulares", total_solicitacoes)
        
        with col3:
            pendentes = sum(info['pendentes'] for info in relatorio['solicitacoes'].values())
            st.metric("Solicitações Pendentes", pendentes, delta=f"-{pendentes}")
        
        with col4:
            incidentes = sum(info['total'] for info in relatorio['incidentes'].values())
            st.metric("Incidentes Registrados", incidentes)
        
        # Alertas de conformidade
        st.subheader("⚠️ Alertas de Conformidade")
        
        vencidas = sum(info['vencidas'] for info in relatorio['solicitacoes'].values())
        if vencidas > 0:
            st.error(f"🚨 {vencidas} solicitações estão vencidas! Prazo legal ultrapassado.")
        
        incidentes_anpd = sum(info['reportar_anpd'] for info in relatorio['incidentes'].values())
        if incidentes_anpd > 0:
            st.warning(f"📢 {incidentes_anpd} incidentes precisam ser reportados à ANPD.")
        
        if vencidas == 0 and incidentes_anpd == 0:
            st.success("✅ Sistema em conformidade com prazos legais!")
    
    with tab2:
        st.subheader("✅ Gestão de Consentimentos")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("**Registrar Novo Consentimento**")
            
            email = st.text_input("Email do Titular:", key="email_titular_consulta")
            nome = st.text_input("Nome do Titular:", key="nome_titular_consulta")
            
            tipo_consentimento = st.selectbox("Tipo de Consentimento:", [
                "coleta_dados_funcionais",
                "marketing_comunicacao", 
                "compartilhamento_terceiros",
                "cookies_analytics",
                "tratamento_dados_sensíveis"
            ])
            
            descricao = st.text_area("Descrição/Finalidade:", 
                                   placeholder="Descreva a finalidade do tratamento")
            
            consentimento_dado = st.checkbox("Consentimento foi dado?")
            
            if st.button("📝 Registrar Consentimento"):
                if email and nome:
                    consentimento_id = manager.registrar_consentimento(
                        email, nome, tipo_consentimento, descricao, consentimento_dado
                    )
                    st.success(f"✅ Consentimento registrado! ID: {consentimento_id}")
                else:
                    st.error("❌ Preencha email e nome")
        
        with col2:
            st.write("**Revogar Consentimento**")
            
            email_revogacao = st.text_input("Email para Revogação:", key="revogacao")
            tipo_revogacao = st.selectbox("Tipo a Revogar:", [
                "coleta_dados_funcionais",
                "marketing_comunicacao",
                "compartilhamento_terceiros", 
                "cookies_analytics",
                "tratamento_dados_sensíveis"
            ], key="tipo_revogacao")
            
            if st.button("🚫 Revogar Consentimento"):
                if email_revogacao:
                    manager.revogar_consentimento(email_revogacao, tipo_revogacao)
                    st.success("✅ Consentimento revogado!")
                else:
                    st.error("❌ Informe o email")
        
        # Listar consentimentos
        st.subheader("📋 Consentimentos Registrados")
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM consentimentos_lgpd 
        WHERE ativo = TRUE 
        ORDER BY data_criacao DESC 
        LIMIT 10
        """)
        
        consentimentos = cursor.fetchall()
        
        if consentimentos:
            for consentimento in consentimentos:
                status_icon = "✅" if consentimento['consentimento_dado'] else "❌"
                revogado = "🚫 REVOGADO" if consentimento['data_revogacao'] else ""
                
                with st.expander(f"{status_icon} {consentimento['tipo_consentimento']} - {consentimento['email']} {revogado}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Email:** {consentimento['email']}")
                        st.write(f"**Nome:** {consentimento['nome']}")
                        st.write(f"**Tipo:** {consentimento['tipo_consentimento']}")
                    
                    with col2:
                        st.write(f"**Consentimento:** {'Dado' if consentimento['consentimento_dado'] else 'Negado'}")
                        st.write(f"**Data:** {consentimento['data_consentimento'] or 'N/A'}")
                        if consentimento['data_revogacao']:
                            st.write(f"**Revogado em:** {consentimento['data_revogacao']}")
        else:
            st.info("ℹ️ Nenhum consentimento registrado")
    
    with tab3:
        st.subheader("📝 Solicitações dos Titulares")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("**Nova Solicitação**")
            
            tipo_solicitacao = st.selectbox("Tipo de Solicitação:", [
                "acesso",
                "retificacao", 
                "exclusao",
                "portabilidade",
                "oposicao",
                "informacao"
            ])
            
            email_titular = st.text_input("Email do Titular:", key="email_titular_solicitacao")
            nome_titular = st.text_input("Nome do Titular:", key="nome_titular_solicitacao")
            descricao_solicitacao = st.text_area("Descrição da Solicitação:", key="desc_solicitacao")
            
            if st.button("📝 Criar Solicitação"):
                if email_titular:
                    solicitacao_id = manager.criar_solicitacao_titular(
                        tipo_solicitacao, email_titular, nome_titular, descricao_solicitacao
                    )
                    st.success(f"✅ Solicitação criada! ID: {solicitacao_id}")
                else:
                    st.error("❌ Informe o email")
        
        with col2:
            st.write("**Prazos Legais (LGPD)**")
            st.info("""
            📅 **Prazos para resposta:**
            - Acesso aos dados: 15 dias
            - Retificação: 15 dias  
            - Exclusão: 15 dias
            - Portabilidade: 15 dias
            - Oposição: 15 dias
            - Informações: 15 dias
            
            ⚠️ **Importante:** Prazos podem ser prorrogados por mais 15 dias mediante justificativa.
            """)
        
        # Listar solicitações
        st.subheader("📋 Solicitações Pendentes")
        
        cursor.execute("""
        SELECT * FROM solicitacoes_titulares 
        WHERE status = 'pendente'
        ORDER BY prazo_legal ASC
        """)
        
        solicitacoes = cursor.fetchall()
        
        if solicitacoes:
            for solicitacao in solicitacoes:
                prazo_vencido = solicitacao['prazo_legal'] < datetime.now().date()
                status_icon = "🚨" if prazo_vencido else "📅"
                
                with st.expander(f"{status_icon} {solicitacao['tipo_solicitacao'].title()} - {solicitacao['email_titular']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Tipo:** {solicitacao['tipo_solicitacao']}")
                        st.write(f"**Email:** {solicitacao['email_titular']}")
                        st.write(f"**Nome:** {solicitacao['nome_titular']}")
                    
                    with col2:
                        st.write(f"**Prazo Legal:** {solicitacao['prazo_legal']}")
                        st.write(f"**Status:** {solicitacao['status']}")
                        
                        if prazo_vencido:
                            st.error("⚠️ PRAZO VENCIDO!")
                    
                    if solicitacao['descricao_solicitacao']:
                        st.write(f"**Descrição:** {solicitacao['descricao_solicitacao']}")
        else:
            st.success("✅ Nenhuma solicitação pendente!")
    
    with tab4:
        st.subheader("🚨 Gestão de Incidentes de Segurança")
        st.info("Registre incidentes que afetem dados pessoais conforme Art. 48 da LGPD")
        
        # Formulário para novo incidente
        with st.form("novo_incidente"):
            st.write("**Registrar Novo Incidente**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                titulo = st.text_input("Título do Incidente:", key="titulo_incidente")
                gravidade = st.selectbox("Gravidade:", ["baixa", "media", "alta", "critica"])
                numero_afetados = st.number_input("Número de Titulares Afetados:", min_value=0, step=1)
            
            with col2:
                data_incidente = st.date_input("Data do Incidente:")
                notificar_anpd = st.checkbox("Requer notificação à ANPD?")
                notificar_titulares = st.checkbox("Requer comunicação aos titulares?")
            
            descricao = st.text_area("Descrição do Incidente:")
            tipos_dados = st.multiselect("Tipos de Dados Afetados:", [
                "nome", "email", "cpf", "telefone", "endereco", 
                "dados_financeiros", "dados_sensíveis", "outros"
            ])
            
            medidas_corretivas = st.text_area("Medidas Corretivas Adotadas:")
            
            if st.form_submit_button("🚨 Registrar Incidente"):
                if titulo and descricao:
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                    INSERT INTO incidentes_seguranca
                    (titulo, descricao, gravidade, tipos_dados_afetados, numero_titulares_afetados,
                     data_incidente, medidas_corretivas, notificar_anpd, notificar_titulares)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """, [
                        titulo, descricao, gravidade, tipos_dados, numero_afetados,
                        data_incidente, medidas_corretivas, notificar_anpd, notificar_titulares
                    ])
                    
                    incidente_id = cursor.fetchone()[0]
                    conn.commit()
                    
                    st.success(f"✅ Incidente registrado! ID: {incidente_id}")
                    
                    if notificar_anpd:
                        st.warning("⚠️ Lembre-se: Notificação à ANPD deve ser feita em até 72 horas!")
                else:
                    st.error("❌ Preencha título e descrição")
    
    with tab5:
        st.subheader("🔒 Anonimização de Dados")
        st.warning("⚠️ Ação irreversível! Use apenas quando legalmente necessário.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Buscar mapeamentos de dados pessoais
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT tabela, campo FROM mapeamento_dados_pessoais WHERE pode_anonimizar = TRUE")
            mapeamentos = cursor.fetchall()
            
            if mapeamentos:
                opcoes = [f"{m['tabela']}.{m['campo']}" for m in mapeamentos]
                campo_selecionado = st.selectbox("Campo a Anonimizar:", opcoes)
                
                if campo_selecionado:
                    tabela, campo = campo_selecionado.split('.')
                    
                    registro_id = st.number_input(f"ID do Registro ({tabela}):", min_value=1, step=1)
                    motivo = st.text_area("Motivo da Anonimização:")
                    
                    if st.button("🔒 Anonimizar Dados"):
                        if registro_id and motivo:
                            sucesso, mensagem = manager.anonimizar_dados(tabela, campo, registro_id, motivo)
                            
                            if sucesso:
                                st.success(mensagem)
                            else:
                                st.error(mensagem)
                        else:
                            st.error("❌ Preencha ID e motivo")
            else:
                st.info("ℹ️ Nenhum campo configurado para anonimização")
        
        with col2:
            st.write("**Histórico de Anonimizações**")
            
            cursor.execute("""
            SELECT * FROM historico_anonimizacao 
            ORDER BY data_anonimizacao DESC 
            LIMIT 10
            """)
            
            historico = cursor.fetchall()
            
            if historico:
                for item in historico:
                    with st.expander(f"🔒 {item['tabela_origem']}.{item['campo_origem']} - {item['data_anonimizacao'].date()}"):
                        st.write(f"**Registro ID:** {item['registro_id']}")
                        st.write(f"**Técnica:** {item['tecnica_anonimizacao']}")
                        st.write(f"**Data:** {item['data_anonimizacao']}")
                        if item['motivo']:
                            st.write(f"**Motivo:** {item['motivo']}")
            else:
                st.info("ℹ️ Nenhuma anonimização realizada")
    
    with tab6:
        st.subheader("📊 Relatórios de Conformidade")
        
        if st.button("📋 Gerar Relatório de Conformidade"):
            relatorio = manager.gerar_relatorio_conformidade()
            
            st.json(relatorio)
            
            # Opção de download
            relatorio_str = json.dumps(relatorio, indent=2, default=str)
            st.download_button(
                "💾 Download Relatório JSON",
                relatorio_str,
                file_name=f"relatorio_lgpd_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        st.subheader("📋 Registros de Processamento (Art. 37 LGPD)")
        
        cursor.execute("SELECT * FROM mapeamento_dados_pessoais ORDER BY tabela, campo")
        mapeamentos = cursor.fetchall()
        
        if mapeamentos:
            df_mapeamentos = pd.DataFrame(mapeamentos)
            st.dataframe(df_mapeamentos, use_container_width=True)
            
            # Download CSV
            csv = df_mapeamentos.to_csv(index=False)
            st.download_button(
                "💾 Download Registros CSV",
                csv,
                file_name=f"registros_processamento_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("ℹ️ Nenhum mapeamento de dados pessoais encontrado")

if __name__ == "__main__":
    show_lgpd_compliance_page()