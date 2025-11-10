"""
Sistema de Orçamentos e Cotações
Gestão completa de cotações, comparação de fornecedores e histórico de preços
"""

import streamlit as st
from datetime import datetime, timedelta
from database.connection import db
from modules.logs_auditoria import log_acao
import pandas as pd
from typing import Dict, List, Any
import plotly.express as px
import plotly.graph_objects as go

def get_count_result(cursor_result):
    """Helper para extrair count/valor do resultado do cursor PostgreSQL"""
    if not cursor_result:
        return 0
    if isinstance(cursor_result, dict):
        return cursor_result.get('count', cursor_result.get('id', 0))
    elif isinstance(cursor_result, (list, tuple)):
        return cursor_result[0] if cursor_result else 0
    else:
        return cursor_result

class OrcamentosManager:
    def __init__(self):
        self.criar_tabelas()
    
    def criar_tabelas(self):
        """Cria tabelas necessárias para orçamentos e cotações"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Tabela de fornecedores
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS fornecedores (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                cnpj VARCHAR(18) UNIQUE,
                razao_social VARCHAR(255),
                email VARCHAR(255),
                telefone VARCHAR(20),
                endereco TEXT,
                cidade VARCHAR(100),
                estado VARCHAR(2),
                cep VARCHAR(10),
                contato_responsavel VARCHAR(255),
                especialidades TEXT[],
                avaliacao_qualidade INTEGER DEFAULT 5,
                prazo_entrega_padrao INTEGER DEFAULT 7,
                condicoes_pagamento VARCHAR(100),
                observacoes TEXT,
                ativo BOOLEAN DEFAULT TRUE,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Tabela de solicitações de cotação
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS solicitacoes_cotacao (
                id SERIAL PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                descricao TEXT,
                tipo_produto VARCHAR(100),
                categoria VARCHAR(100),
                especificacoes JSONB,
                quantidade DECIMAL(10,3),
                unidade_medida VARCHAR(20),
                prazo_entrega_desejado DATE,
                orcamento_maximo DECIMAL(15,2),
                usuario_solicitante_id INTEGER,
                obra_destino_id INTEGER,
                urgencia VARCHAR(20) DEFAULT 'normal',
                status VARCHAR(50) DEFAULT 'rascunho',
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_abertura TIMESTAMP,
                data_fechamento TIMESTAMP,
                cotacao_vencedora_id INTEGER,
                observacoes TEXT
            )
            """)
            
            # Tabela de cotações recebidas
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS cotacoes_recebidas (
                id SERIAL PRIMARY KEY,
                solicitacao_id INTEGER REFERENCES solicitacoes_cotacao(id),
                fornecedor_id INTEGER REFERENCES fornecedores(id),
                preco_unitario DECIMAL(15,2),
                preco_total DECIMAL(15,2),
                prazo_entrega INTEGER,
                condicoes_pagamento VARCHAR(100),
                validade_cotacao INTEGER DEFAULT 30,
                observacoes TEXT,
                qualidade_estimada INTEGER DEFAULT 5,
                confiabilidade_fornecedor INTEGER DEFAULT 5,
                score_total DECIMAL(5,2),
                data_cotacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_validade DATE,
                status VARCHAR(50) DEFAULT 'ativa',
                desconto_percentual DECIMAL(5,2) DEFAULT 0,
                impostos_inclusos BOOLEAN DEFAULT TRUE,
                frete_incluido BOOLEAN DEFAULT FALSE,
                valor_frete DECIMAL(10,2) DEFAULT 0
            )
            """)
            
            # Tabela de histórico de preços
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_precos (
                id SERIAL PRIMARY KEY,
                tipo_produto VARCHAR(100),
                categoria VARCHAR(100),
                descricao_produto TEXT,
                fornecedor_id INTEGER REFERENCES fornecedores(id),
                preco_unitario DECIMAL(15,2),
                unidade_medida VARCHAR(20),
                data_cotacao DATE,
                origem VARCHAR(50),
                origem_id INTEGER,
                qualidade INTEGER DEFAULT 5,
                observacoes TEXT
            )
            """)
            
            # Tabela de contratos firmados
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS contratos_fornecedores (
                id SERIAL PRIMARY KEY,
                fornecedor_id INTEGER REFERENCES fornecedores(id),
                solicitacao_id INTEGER REFERENCES solicitacoes_cotacao(id),
                cotacao_id INTEGER REFERENCES cotacoes_recebidas(id),
                numero_contrato VARCHAR(100),
                valor_total DECIMAL(15,2),
                data_assinatura DATE,
                data_inicio DATE,
                data_fim_prevista DATE,
                status VARCHAR(50) DEFAULT 'ativo',
                tipo_contrato VARCHAR(50),
                condicoes_especiais TEXT,
                multas_atrasos DECIMAL(10,2),
                bonificacoes DECIMAL(10,2),
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            conn.commit()
            
            # Inserir dados de exemplo
            self.inserir_fornecedores_exemplo()
            
        except Exception as e:
            st.error(f"Erro ao criar tabelas de orçamentos: {e}")
    
    def inserir_fornecedores_exemplo(self):
        """Insere fornecedores de exemplo"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se já existem fornecedores
        cursor.execute("SELECT COUNT(*) FROM fornecedores")
        if cursor.fetchone()[0] > 0:
            return
        
        fornecedores_exemplo = [
            {
                'nome': 'TecnoFerramentas Ltda',
                'cnpj': '12.345.678/0001-90',
                'razao_social': 'TecnoFerramentas Equipamentos Ltda',
                'email': 'vendas@tecnoferramentas.com.br',
                'telefone': '(11) 99999-1111',
                'cidade': 'São Paulo',
                'estado': 'SP',
                'especialidades': ['ferramentas_eletricas', 'equipamentos_construcao'],
                'avaliacao': 9,
                'prazo': 3,
                'condicoes': '30/60 dias'
            },
            {
                'nome': 'InsumoMax Distribuidora',
                'cnpj': '98.765.432/0001-10',
                'razao_social': 'InsumoMax Distribuidora de Materiais SA',
                'email': 'cotacoes@insumomax.com.br',
                'telefone': '(21) 88888-2222',
                'cidade': 'Rio de Janeiro',
                'estado': 'RJ',
                'especialidades': ['insumos_construcao', 'materiais_eletricos'],
                'avaliacao': 8,
                'prazo': 5,
                'condicoes': 'À vista c/ desconto'
            },
            {
                'nome': 'EquipaConstrução',
                'cnpj': '11.222.333/0001-44',
                'razao_social': 'EquipaConstrução Equipamentos Ltda',
                'email': 'vendas@equipaconstrucao.com.br',
                'telefone': '(31) 77777-3333',
                'cidade': 'Belo Horizonte',
                'estado': 'MG',
                'especialidades': ['equipamentos_pesados', 'locacao_equipamentos'],
                'avaliacao': 7,
                'prazo': 7,
                'condicoes': '15/30/45 dias'
            }
        ]
        
        for fornecedor in fornecedores_exemplo:
            cursor.execute("""
            INSERT INTO fornecedores 
            (nome, cnpj, razao_social, email, telefone, cidade, estado,
             especialidades, avaliacao_qualidade, prazo_entrega_padrao, condicoes_pagamento)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                fornecedor['nome'], fornecedor['cnpj'], fornecedor['razao_social'],
                fornecedor['email'], fornecedor['telefone'], fornecedor['cidade'],
                fornecedor['estado'], fornecedor['especialidades'], fornecedor['avaliacao'],
                fornecedor['prazo'], fornecedor['condicoes']
            ])
        
        conn.commit()
    
    def criar_solicitacao_cotacao(self, dados: Dict[str, Any]):
        """Cria nova solicitação de cotação"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO solicitacoes_cotacao
        (titulo, descricao, tipo_produto, categoria, especificacoes, quantidade,
         unidade_medida, prazo_entrega_desejado, orcamento_maximo, usuario_solicitante_id,
         obra_destino_id, urgencia)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, [
            dados['titulo'], dados['descricao'], dados['tipo_produto'],
            dados['categoria'], dados.get('especificacoes', {}), dados['quantidade'],
            dados['unidade_medida'], dados['prazo_entrega'], dados.get('orcamento_maximo'),
            dados.get('usuario_id', 1), dados.get('obra_id'), dados.get('urgencia', 'normal')
        ])
        
        solicitacao_id = cursor.fetchone()[0]
        conn.commit()
        
        log_acao("orcamentos", "criar_solicitacao", f"Solicitação de cotação criada: {dados['titulo']}")
        return solicitacao_id
    
    def abrir_cotacao(self, solicitacao_id: int, fornecedores_selecionados: List[int]):
        """Abre cotação para fornecedores selecionados"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Atualizar status da solicitação
        cursor.execute("""
        UPDATE solicitacoes_cotacao 
        SET status = 'aberta', data_abertura = %s
        WHERE id = %s
        """, [datetime.now(), solicitacao_id])
        
        # Registrar envio para fornecedores
        for fornecedor_id in fornecedores_selecionados:
            # Aqui normalmente seria enviado email/notificação para o fornecedor
            log_acao("orcamentos", "enviar_cotacao", 
                    f"Cotação {solicitacao_id} enviada para fornecedor {fornecedor_id}")
        
        conn.commit()
        return True
    
    def registrar_cotacao_recebida(self, dados: Dict[str, Any]):
        """Registra cotação recebida de fornecedor"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Calcular score total (qualidade + confiabilidade + preço)
        score = self.calcular_score_cotacao(dados)
        
        cursor.execute("""
        INSERT INTO cotacoes_recebidas
        (solicitacao_id, fornecedor_id, preco_unitario, preco_total, prazo_entrega,
         condicoes_pagamento, validade_cotacao, observacoes, qualidade_estimada,
         confiabilidade_fornecedor, score_total, data_validade, desconto_percentual,
         impostos_inclusos, frete_incluido, valor_frete)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, [
            dados['solicitacao_id'], dados['fornecedor_id'], dados['preco_unitario'],
            dados['preco_total'], dados['prazo_entrega'], dados['condicoes_pagamento'],
            dados.get('validade', 30), dados.get('observacoes', ''),
            dados.get('qualidade', 5), dados.get('confiabilidade', 5),
            score, datetime.now().date() + timedelta(days=dados.get('validade', 30)),
            dados.get('desconto', 0), dados.get('impostos_inclusos', True),
            dados.get('frete_incluido', False), dados.get('valor_frete', 0)
        ])
        
        cotacao_id = cursor.fetchone()[0]
        
        # Registrar no histórico de preços
        cursor.execute("""
        INSERT INTO historico_precos
        (tipo_produto, categoria, descricao_produto, fornecedor_id, preco_unitario,
         unidade_medida, data_cotacao, origem, origem_id)
        SELECT tipo_produto, categoria, descricao, %s, %s, unidade_medida, CURRENT_DATE, 'cotacao', %s
        FROM solicitacoes_cotacao WHERE id = %s
        """, [dados['fornecedor_id'], dados['preco_unitario'], cotacao_id, dados['solicitacao_id']])
        
        conn.commit()
        
        log_acao("orcamentos", "receber_cotacao", f"Cotação recebida de fornecedor {dados['fornecedor_id']}")
        return cotacao_id
    
    def calcular_score_cotacao(self, dados: Dict[str, Any]) -> float:
        """Calcula score da cotação baseado em múltiplos critérios"""
        # Score baseado em: preço (40%), qualidade (30%), prazo (20%), confiabilidade (10%)
        
        # Para demonstração, usando valores fixos
        # Em produção, seria baseado em histórico e comparação com outras cotações
        
        score_qualidade = dados.get('qualidade', 5) * 3.0  # 30% do peso
        score_confiabilidade = dados.get('confiabilidade', 5) * 1.0  # 10% do peso
        score_prazo = max(0, (30 - dados['prazo_entrega'])) * 0.2  # 20% do peso (melhor prazo = maior score)
        
        # Score de preço seria calculado comparando com outras cotações
        score_preco = 4.0  # Simplificado para demonstração
        
        score_total = score_qualidade + score_confiabilidade + score_prazo + score_preco
        return min(10.0, score_total)  # Limite máximo de 10
    
    def comparar_cotacoes(self, solicitacao_id: int):
        """Gera comparativo de cotações"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT c.*, f.nome as fornecedor_nome, f.avaliacao_qualidade, f.cidade, f.estado
        FROM cotacoes_recebidas c
        JOIN fornecedores f ON c.fornecedor_id = f.id
        WHERE c.solicitacao_id = %s AND c.status = 'ativa'
        ORDER BY c.score_total DESC
        """, [solicitacao_id])
        
        return cursor.fetchall()
    
    def selecionar_cotacao_vencedora(self, solicitacao_id: int, cotacao_id: int, motivo: str = ""):
        """Seleciona cotação vencedora"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Atualizar solicitação
        cursor.execute("""
        UPDATE solicitacoes_cotacao 
        SET status = 'fechada', data_fechamento = %s, cotacao_vencedora_id = %s,
            observacoes = %s
        WHERE id = %s
        """, [datetime.now(), cotacao_id, motivo, solicitacao_id])
        
        # Atualizar status das cotações
        cursor.execute("""
        UPDATE cotacoes_recebidas 
        SET status = CASE 
            WHEN id = %s THEN 'vencedora'
            ELSE 'perdedora'
        END
        WHERE solicitacao_id = %s
        """, [cotacao_id, solicitacao_id])
        
        conn.commit()
        
        log_acao("orcamentos", "selecionar_vencedora", f"Cotação {cotacao_id} selecionada como vencedora")
        return True

def show_orcamentos_cotacoes_page():
    """Exibe página de orçamentos e cotações"""
    st.title("💰 Orçamentos e Cotações")
    st.markdown("Sistema completo de cotações, comparação de fornecedores e histórico de preços")
    
    manager = OrcamentosManager()
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Dashboard", "📝 Nova Solicitação", "📋 Cotações Abertas", 
        "🏢 Fornecedores", "📈 Histórico Preços", "🎯 Comparativos"
    ])
    
    with tab1:
        st.subheader("📊 Dashboard de Cotações")
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cursor.execute("SELECT COUNT(*) FROM solicitacoes_cotacao")
            result = cursor.fetchone()
            total_solicitacoes = result['count'] if isinstance(result, dict) else (result[0] if result else 0)
            st.metric("Total Solicitações", total_solicitacoes)
        
        with col2:
            cursor.execute("SELECT COUNT(*) FROM solicitacoes_cotacao WHERE status = 'aberta'")
            result = cursor.fetchone()
            abertas = result['count'] if isinstance(result, dict) else (result[0] if result else 0)
            st.metric("Cotações Abertas", abertas)
        
        with col3:
            cursor.execute("SELECT COUNT(*) FROM cotacoes_recebidas WHERE status = 'ativa'")
            result = cursor.fetchone()
            recebidas = get_count_result(result)
            st.metric("Cotações Recebidas", recebidas)
        
        with col4:
            cursor.execute("SELECT COUNT(*) FROM fornecedores WHERE ativo = TRUE")
            result = cursor.fetchone()
            fornecedores = get_count_result(result)
            st.metric("Fornecedores Ativos", fornecedores)
        
        # Gráfico de cotações por mês
        cursor.execute("""
        SELECT DATE_TRUNC('month', data_criacao) as mes, COUNT(*) as total
        FROM solicitacoes_cotacao
        WHERE data_criacao >= CURRENT_DATE - INTERVAL '6 months'
        GROUP BY mes
        ORDER BY mes
        """)
        
        dados_grafico = cursor.fetchall()
        
        if dados_grafico:
            df_grafico = pd.DataFrame(dados_grafico, columns=['mes', 'total'])
            fig = px.line(df_grafico, x='mes', y='total', 
                         title='Solicitações de Cotação por Mês')
            st.plotly_chart(fig, use_container_width=True)
        
        # Solicitações urgentes
        cursor.execute("""
        SELECT titulo, urgencia, data_criacao, status
        FROM solicitacoes_cotacao 
        WHERE urgencia = 'alta' AND status IN ('rascunho', 'aberta')
        ORDER BY data_criacao DESC
        """)
        
        urgentes = cursor.fetchall()
        
        if urgentes:
            st.subheader("🚨 Solicitações Urgentes")
            for solicitacao in urgentes:
                st.warning(f"⚡ **{solicitacao['titulo']}** - Status: {solicitacao['status']} - {solicitacao['data_criacao'].date()}")
    
    with tab2:
        st.subheader("📝 Nova Solicitação de Cotação")
        
        with st.form("nova_solicitacao"):
            col1, col2 = st.columns(2)
            
            with col1:
                titulo = st.text_input("Título da Solicitação*:")
                tipo_produto = st.selectbox("Tipo de Produto:", [
                    "equipamento_eletrico", "equipamento_manual", "insumo_construcao",
                    "material_eletrico", "ferramenta", "epi", "outro"
                ])
                categoria = st.text_input("Categoria/Subcategoria:")
                quantidade = st.number_input("Quantidade*:", min_value=0.001, step=0.001, format="%.3f")
                unidade_medida = st.selectbox("Unidade:", [
                    "un", "kg", "m", "m2", "m3", "l", "cx", "pc", "par"
                ])
            
            with col2:
                prazo_entrega = st.date_input("Prazo de Entrega Desejado:",
                                            value=datetime.now().date() + timedelta(days=15))
                orcamento_maximo = st.number_input("Orçamento Máximo (R$):", 
                                                 min_value=0.0, step=100.0)
                urgencia = st.selectbox("Urgência:", ["baixa", "normal", "alta"])
                
                # Buscar obras para destino
                cursor.execute("SELECT id, nome FROM obras WHERE status = 'ativo'")
                obras = cursor.fetchall()
                obra_options = {f"{obra['nome']} (ID: {obra['id']})": obra['id'] for obra in obras}
                obra_selected = st.selectbox("Obra Destino:", ["Nenhuma"] + list(obra_options.keys()))
                obra_id = obra_options.get(obra_selected)
            
            descricao = st.text_area("Descrição Detalhada*:", height=100)
            especificacoes_json = st.text_area("Especificações Técnicas (JSON):", 
                                             placeholder='{"marca": "preferida", "modelo": "específico"}')
            
            if st.form_submit_button("📝 Criar Solicitação"):
                if titulo and descricao and quantidade > 0:
                    try:
                        especificacoes = {}
                        if especificacoes_json.strip():
                            especificacoes = eval(especificacoes_json)  # Em produção, usar json.loads
                        
                        dados_solicitacao = {
                            'titulo': titulo,
                            'descricao': descricao,
                            'tipo_produto': tipo_produto,
                            'categoria': categoria,
                            'especificacoes': especificacoes,
                            'quantidade': quantidade,
                            'unidade_medida': unidade_medida,
                            'prazo_entrega': prazo_entrega,
                            'orcamento_maximo': orcamento_maximo if orcamento_maximo > 0 else None,
                            'urgencia': urgencia,
                            'obra_id': obra_id,
                            'usuario_id': 1  # Em produção, pegar do session
                        }
                        
                        solicitacao_id = manager.criar_solicitacao_cotacao(dados_solicitacao)
                        st.success(f"✅ Solicitação criada com sucesso! ID: {solicitacao_id}")
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao criar solicitação: {e}")
                else:
                    st.error("❌ Preencha os campos obrigatórios")
    
    with tab3:
        st.subheader("📋 Gerenciar Cotações Abertas")
        
        # Listar solicitações em rascunho para abrir
        cursor.execute("""
        SELECT * FROM solicitacoes_cotacao 
        WHERE status IN ('rascunho', 'aberta')
        ORDER BY data_criacao DESC
        """)
        
        solicitacoes = cursor.fetchall()
        
        if solicitacoes:
            for solicitacao in solicitacoes:
                with st.expander(f"📋 {solicitacao['titulo']} - {solicitacao['status'].upper()}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Tipo:** {solicitacao['tipo_produto']}")
                        st.write(f"**Quantidade:** {solicitacao['quantidade']} {solicitacao['unidade_medida']}")
                        st.write(f"**Urgência:** {solicitacao['urgencia']}")
                    
                    with col2:
                        st.write(f"**Prazo:** {solicitacao['prazo_entrega_desejado']}")
                        if solicitacao['orcamento_maximo']:
                            st.write(f"**Orçamento Máx:** R$ {solicitacao['orcamento_maximo']:,.2f}")
                        st.write(f"**Criado em:** {solicitacao['data_criacao'].date()}")
                    
                    with col3:
                        st.write(f"**Status:** {solicitacao['status']}")
                        if solicitacao['data_abertura']:
                            st.write(f"**Aberto em:** {solicitacao['data_abertura'].date()}")
                    
                    st.write(f"**Descrição:** {solicitacao['descricao']}")
                    
                    # Ações disponíveis
                    if solicitacao['status'] == 'rascunho':
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            # Selecionar fornecedores
                            cursor.execute("SELECT id, nome FROM fornecedores WHERE ativo = TRUE")
                            fornecedores = cursor.fetchall()
                            
                            fornecedor_options = {f.nome: f.id for f in fornecedores}
                            fornecedores_selecionados = st.multiselect(
                                "Selecionar Fornecedores:",
                                list(fornecedor_options.keys()),
                                key=f"fornecedores_{solicitacao['id']}"
                            )
                        
                        with col_b:
                            if st.button("🚀 Abrir Cotação", key=f"abrir_{solicitacao['id']}"):
                                if fornecedores_selecionados:
                                    fornecedor_ids = [fornecedor_options[nome] for nome in fornecedores_selecionados]
                                    manager.abrir_cotacao(solicitacao['id'], fornecedor_ids)
                                    st.success("✅ Cotação aberta para fornecedores!")
                                    st.rerun()
                                else:
                                    st.error("❌ Selecione pelo menos um fornecedor")
                    
                    elif solicitacao['status'] == 'aberta':
                        # Registrar cotação recebida
                        with st.form(f"cotacao_{solicitacao['id']}"):
                            st.write("**Registrar Cotação Recebida**")
                            
                            col_a, col_b, col_c = st.columns(3)
                            
                            with col_a:
                                cursor.execute("SELECT id, nome FROM fornecedores WHERE ativo = TRUE")
                                fornecedores = cursor.fetchall()
                                fornecedor_opcoes = {f.nome: f.id for f in fornecedores}
                                fornecedor_nome = st.selectbox("Fornecedor:", 
                                                             list(fornecedor_opcoes.keys()),
                                                             key=f"forn_{solicitacao['id']}")
                                
                                preco_unitario = st.number_input("Preço Unitário (R$):", 
                                                               min_value=0.01, step=0.01,
                                                               key=f"preco_{solicitacao['id']}")
                            
                            with col_b:
                                preco_total = st.number_input("Preço Total (R$):", 
                                                            value=preco_unitario * float(solicitacao['quantidade']),
                                                            key=f"total_{solicitacao['id']}")
                                
                                prazo_entrega = st.number_input("Prazo Entrega (dias):", 
                                                              min_value=1, step=1,
                                                              key=f"prazo_{solicitacao['id']}")
                            
                            with col_c:
                                condicoes_pagamento = st.text_input("Condições Pagamento:",
                                                                   placeholder="30/60 dias",
                                                                   key=f"cond_{solicitacao['id']}")
                                
                                qualidade_estimada = st.slider("Qualidade Estimada:", 1, 10, 5,
                                                              key=f"qual_{solicitacao['id']}")
                            
                            observacoes_cotacao = st.text_area("Observações:",
                                                             key=f"obs_{solicitacao['id']}")
                            
                            if st.form_submit_button("💾 Registrar Cotação"):
                                dados_cotacao = {
                                    'solicitacao_id': solicitacao['id'],
                                    'fornecedor_id': fornecedor_opcoes[fornecedor_nome],
                                    'preco_unitario': preco_unitario,
                                    'preco_total': preco_total,
                                    'prazo_entrega': prazo_entrega,
                                    'condicoes_pagamento': condicoes_pagamento,
                                    'qualidade': qualidade_estimada,
                                    'observacoes': observacoes_cotacao
                                }
                                
                                cotacao_id = manager.registrar_cotacao_recebida(dados_cotacao)
                                st.success(f"✅ Cotação registrada! ID: {cotacao_id}")
                                st.rerun()
                        
                        # Botão para comparar cotações se houver cotações recebidas
                        cursor.execute("SELECT COUNT(*) FROM cotacoes_recebidas WHERE solicitacao_id = %s", 
                                     [solicitacao['id']])
                        num_cotacoes = cursor.fetchone()[0]
                        
                        if num_cotacoes > 0:
                            if st.button(f"📊 Comparar Cotações ({num_cotacoes})", 
                                       key=f"comp_{solicitacao['id']}"):
                                st.session_state[f'comparar_{solicitacao["id"]}'] = True
                        
                        # Mostrar comparativo se solicitado
                        if st.session_state.get(f'comparar_{solicitacao["id"]}', False):
                            st.subheader(f"📊 Comparativo - {solicitacao['titulo']}")
                            
                            cotacoes = manager.comparar_cotacoes(solicitacao['id'])
                            
                            if cotacoes:
                                # Criar DataFrame para melhor visualização
                                dados_comparativo = []
                                for cotacao in cotacoes:
                                    dados_comparativo.append({
                                        'Fornecedor': cotacao['fornecedor_nome'],
                                        'Preço Unit. (R$)': f"{cotacao['preco_unitario']:,.2f}",
                                        'Preço Total (R$)': f"{cotacao['preco_total']:,.2f}",
                                        'Prazo (dias)': cotacao['prazo_entrega'],
                                        'Score Total': f"{cotacao['score_total']:.1f}",
                                        'Condições': cotacao['condicoes_pagamento'],
                                        'Cidade': f"{cotacao['cidade']}/{cotacao['estado']}"
                                    })
                                
                                df_comparativo = pd.DataFrame(dados_comparativo)
                                st.dataframe(df_comparativo, use_container_width=True)
                                
                                # Selecionar vencedora
                                st.subheader("🏆 Selecionar Cotação Vencedora")
                                
                                cotacao_vencedora = st.selectbox(
                                    "Cotação Vencedora:",
                                    [f"{c['fornecedor_nome']} - R$ {c['preco_total']:,.2f}" 
                                     for c in cotacoes],
                                    key=f"venc_{solicitacao['id']}"
                                )
                                
                                motivo_selecao = st.text_area("Motivo da Seleção:",
                                                            key=f"motivo_{solicitacao['id']}")
                                
                                if st.button("🏆 Confirmar Seleção", key=f"conf_{solicitacao['id']}"):
                                    # Encontrar ID da cotação selecionada
                                    indice = [f"{c['fornecedor_nome']} - R$ {c['preco_total']:,.2f}" 
                                             for c in cotacoes].index(cotacao_vencedora)
                                    cotacao_id = cotacoes[indice]['id']
                                    
                                    manager.selecionar_cotacao_vencedora(
                                        solicitacao['id'], cotacao_id, motivo_selecao
                                    )
                                    st.success("✅ Cotação vencedora selecionada!")
                                    st.rerun()
        else:
            st.info("ℹ️ Nenhuma solicitação encontrada")
    
    with tab4:
        st.subheader("🏢 Gestão de Fornecedores")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**Fornecedores Cadastrados**")
            
            cursor.execute("SELECT * FROM fornecedores WHERE ativo = TRUE ORDER BY nome")
            fornecedores = cursor.fetchall()
            
            if fornecedores:
                for fornecedor in fornecedores:
                    with st.expander(f"🏢 {fornecedor['nome']} - {fornecedor['cidade']}/{fornecedor['estado']}"):
                        col_a, col_b, col_c = st.columns(3)
                        
                        with col_a:
                            st.write(f"**CNPJ:** {fornecedor['cnpj']}")
                            st.write(f"**Email:** {fornecedor['email']}")
                            st.write(f"**Telefone:** {fornecedor['telefone']}")
                        
                        with col_b:
                            st.write(f"**Avaliação:** {fornecedor['avaliacao_qualidade']}/10")
                            st.write(f"**Prazo Padrão:** {fornecedor['prazo_entrega_padrao']} dias")
                            st.write(f"**Condições:** {fornecedor['condicoes_pagamento']}")
                        
                        with col_c:
                            if fornecedor['especialidades']:
                                st.write(f"**Especialidades:** {', '.join(fornecedor['especialidades'])}")
                            if fornecedor['observacoes']:
                                st.write(f"**Obs:** {fornecedor['observacoes']}")
        
        with col2:
            st.write("**Cadastrar Novo Fornecedor**")
            
            with st.form("novo_fornecedor"):
                nome = st.text_input("Nome*:")
                cnpj = st.text_input("CNPJ:")
                email = st.text_input("Email:")
                telefone = st.text_input("Telefone:")
                cidade = st.text_input("Cidade:")
                estado = st.text_input("Estado (UF):", max_chars=2)
                
                especialidades = st.multiselect("Especialidades:", [
                    "ferramentas_eletricas", "equipamentos_construcao", 
                    "insumos_construcao", "materiais_eletricos",
                    "equipamentos_pesados", "locacao_equipamentos", "epi"
                ])
                
                if st.form_submit_button("➕ Cadastrar"):
                    if nome:
                        cursor.execute("""
                        INSERT INTO fornecedores (nome, cnpj, email, telefone, cidade, estado, especialidades)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, [nome, cnpj, email, telefone, cidade, estado, especialidades])
                        
                        conn.commit()
                        st.success("✅ Fornecedor cadastrado!")
                        st.rerun()
                    else:
                        st.error("❌ Preencha o nome")
    
    with tab5:
        st.subheader("📈 Histórico de Preços")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Filtros
            cursor.execute("SELECT DISTINCT tipo_produto FROM historico_precos ORDER BY tipo_produto")
            tipos = [row[0] for row in cursor.fetchall()]
            
            tipo_filtro = st.selectbox("Filtrar por Tipo:", ["Todos"] + tipos)
            
            data_inicio = st.date_input("Data Início:", 
                                      value=datetime.now().date() - timedelta(days=90))
            data_fim = st.date_input("Data Fim:", value=datetime.now().date())
        
        with col2:
            cursor.execute("SELECT DISTINCT categoria FROM historico_precos WHERE categoria IS NOT NULL ORDER BY categoria")
            categorias = [row[0] for row in cursor.fetchall()]
            
            categoria_filtro = st.selectbox("Filtrar por Categoria:", ["Todas"] + categorias)
        
        # Consultar histórico
        query = """
        SELECT h.*, f.nome as fornecedor_nome
        FROM historico_precos h
        JOIN fornecedores f ON h.fornecedor_id = f.id
        WHERE h.data_cotacao BETWEEN %s AND %s
        """
        params = [data_inicio, data_fim]
        
        if tipo_filtro != "Todos":
            query += " AND h.tipo_produto = %s"
            params.append(tipo_filtro)
        
        if categoria_filtro != "Todas":
            query += " AND h.categoria = %s"
            params.append(categoria_filtro)
        
        query += " ORDER BY h.data_cotacao DESC"
        
        cursor.execute(query, params)
        historico = cursor.fetchall()
        
        if historico:
            # Gráfico de evolução de preços
            df_historico = pd.DataFrame(historico)
            
            if len(df_historico) > 1:
                fig = px.scatter(df_historico, x='data_cotacao', y='preco_unitario',
                               color='fornecedor_nome', size='qualidade',
                               title='Evolução de Preços por Fornecedor',
                               hover_data=['descricao_produto'])
                st.plotly_chart(fig, use_container_width=True)
            
            # Tabela de histórico
            st.subheader("📋 Detalhes do Histórico")
            
            for item in historico[:20]:  # Limitar a 20 itens
                with st.expander(f"💰 {item['descricao_produto']} - R$ {item['preco_unitario']:,.2f} ({item['data_cotacao']})"):
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.write(f"**Fornecedor:** {item['fornecedor_nome']}")
                        st.write(f"**Tipo:** {item['tipo_produto']}")
                        st.write(f"**Categoria:** {item['categoria']}")
                    
                    with col_b:
                        st.write(f"**Preço:** R$ {item['preco_unitario']:,.2f} / {item['unidade_medida']}")
                        st.write(f"**Qualidade:** {item['qualidade']}/10")
                        st.write(f"**Data:** {item['data_cotacao']}")
        else:
            st.info("ℹ️ Nenhum histórico encontrado para os filtros selecionados")
    
    with tab6:
        st.subheader("🎯 Análise Comparativa de Fornecedores")
        
        # Análise de performance por fornecedor
        cursor.execute("""
        SELECT 
            f.nome,
            f.avaliacao_qualidade,
            COUNT(c.id) as total_cotacoes,
            AVG(c.preco_unitario) as preco_medio,
            AVG(c.prazo_entrega) as prazo_medio,
            COUNT(CASE WHEN c.status = 'vencedora' THEN 1 END) as cotacoes_vencidas,
            AVG(c.score_total) as score_medio
        FROM fornecedores f
        LEFT JOIN cotacoes_recebidas c ON f.id = c.fornecedor_id
        WHERE f.ativo = TRUE
        GROUP BY f.id, f.nome, f.avaliacao_qualidade
        HAVING COUNT(c.id) > 0
        ORDER BY score_medio DESC
        """)
        
        performance = cursor.fetchall()
        
        if performance:
            # Gráfico de performance
            df_performance = pd.DataFrame(performance)
            
            # Gráfico scatter: score vs preço médio
            fig = px.scatter(df_performance, x='preco_medio', y='score_medio',
                           size='total_cotacoes', color='prazo_medio',
                           hover_name='nome',
                           title='Performance dos Fornecedores: Score vs Preço Médio')
            st.plotly_chart(fig, use_container_width=True)
            
            # Ranking de fornecedores
            st.subheader("🏆 Ranking de Fornecedores")
            
            for i, fornecedor in enumerate(performance, 1):
                taxa_sucesso = (fornecedor['cotacoes_vencidas'] / fornecedor['total_cotacoes']) * 100
                
                with st.expander(f"#{i} {fornecedor['nome']} - Score: {fornecedor['score_medio']:.1f}"):
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.metric("Total Cotações", fornecedor['total_cotacoes'])
                        st.metric("Cotações Vencidas", fornecedor['cotacoes_vencidas'])
                    
                    with col_b:
                        st.metric("Taxa Sucesso", f"{taxa_sucesso:.1f}%")
                        st.metric("Preço Médio", f"R$ {fornecedor['preco_medio']:,.2f}")
                    
                    with col_c:
                        st.metric("Prazo Médio", f"{fornecedor['prazo_medio']:.0f} dias")
                        st.metric("Score Médio", f"{fornecedor['score_medio']:.1f}/10")
        else:
            st.info("ℹ️ Dados insuficientes para análise comparativa")

if __name__ == "__main__":
    show_orcamentos_cotacoes_page()