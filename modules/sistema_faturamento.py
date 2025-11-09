"""
Sistema de Faturamento
Gestão completa de faturamento, cobrança, controle de pagamentos e relatórios fiscais
"""

import streamlit as st
from datetime import datetime, timedelta
from database.connection import db
from modules.logs_auditoria import log_acao
import pandas as pd
from typing import Dict, List, Any, Optional
import plotly.express as px
import plotly.graph_objects as go

class FaturamentoManager:
    def __init__(self):
        self.criar_tabelas()
    
    def criar_tabelas(self):
        """Cria tabelas necessárias para o sistema de faturamento"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Tabela de clientes
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes_faturamento (
                id SERIAL PRIMARY KEY,
                nome_fantasia VARCHAR(255) NOT NULL,
                razao_social VARCHAR(255),
                tipo_pessoa CHAR(2) CHECK (tipo_pessoa IN ('PF', 'PJ')),
                cpf_cnpj VARCHAR(18) UNIQUE,
                inscricao_estadual VARCHAR(50),
                inscricao_municipal VARCHAR(50),
                endereco_logradouro VARCHAR(255),
                endereco_numero VARCHAR(20),
                endereco_complemento VARCHAR(100),
                endereco_bairro VARCHAR(100),
                endereco_cidade VARCHAR(100),
                endereco_estado VARCHAR(2),
                endereco_cep VARCHAR(10),
                telefone VARCHAR(20),
                email VARCHAR(255),
                contato_responsavel VARCHAR(255),
                prazo_pagamento_padrao INTEGER DEFAULT 30,
                limite_credito DECIMAL(15,2) DEFAULT 0,
                regime_tributario VARCHAR(50),
                observacoes TEXT,
                ativo BOOLEAN DEFAULT TRUE,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Tabela de produtos/serviços para faturamento
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos_servicos (
                id SERIAL PRIMARY KEY,
                codigo VARCHAR(50) UNIQUE NOT NULL,
                descricao VARCHAR(255) NOT NULL,
                tipo VARCHAR(20) CHECK (tipo IN ('produto', 'servico')),
                unidade_medida VARCHAR(20),
                preco_unitario DECIMAL(15,2),
                codigo_ncm VARCHAR(20),
                codigo_cest VARCHAR(20),
                cfop_padrao VARCHAR(10),
                cst_icms VARCHAR(10),
                cst_ipi VARCHAR(10),
                cst_pis VARCHAR(10),
                cst_cofins VARCHAR(10),
                aliquota_icms DECIMAL(5,2) DEFAULT 0,
                aliquota_ipi DECIMAL(5,2) DEFAULT 0,
                aliquota_pis DECIMAL(5,2) DEFAULT 0,
                aliquota_cofins DECIMAL(5,2) DEFAULT 0,
                conta_contabil VARCHAR(20),
                observacoes TEXT,
                ativo BOOLEAN DEFAULT TRUE,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Tabela de notas fiscais
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS notas_fiscais (
                id SERIAL PRIMARY KEY,
                numero_nf BIGINT NOT NULL,
                serie VARCHAR(10) DEFAULT '001',
                tipo_nf VARCHAR(20) CHECK (tipo_nf IN ('saida', 'entrada')),
                modelo_nf VARCHAR(10) DEFAULT '55',
                cliente_id INTEGER REFERENCES clientes_faturamento(id),
                data_emissao DATE DEFAULT CURRENT_DATE,
                data_saida TIMESTAMP,
                natureza_operacao VARCHAR(100),
                valor_produtos DECIMAL(15,2) DEFAULT 0,
                valor_servicos DECIMAL(15,2) DEFAULT 0,
                valor_desconto DECIMAL(15,2) DEFAULT 0,
                valor_frete DECIMAL(15,2) DEFAULT 0,
                valor_seguro DECIMAL(15,2) DEFAULT 0,
                outras_despesas DECIMAL(15,2) DEFAULT 0,
                base_calculo_icms DECIMAL(15,2) DEFAULT 0,
                valor_icms DECIMAL(15,2) DEFAULT 0,
                base_calculo_icms_st DECIMAL(15,2) DEFAULT 0,
                valor_icms_st DECIMAL(15,2) DEFAULT 0,
                valor_ipi DECIMAL(15,2) DEFAULT 0,
                valor_pis DECIMAL(15,2) DEFAULT 0,
                valor_cofins DECIMAL(15,2) DEFAULT 0,
                valor_total DECIMAL(15,2) DEFAULT 0,
                status_nf VARCHAR(50) DEFAULT 'rascunho',
                chave_acesso VARCHAR(44),
                numero_protocolo VARCHAR(50),
                xml_nf TEXT,
                observacoes TEXT,
                usuario_emissao_id INTEGER,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_cancelamento TIMESTAMP,
                motivo_cancelamento TEXT
            )
            """)
            
            # Tabela de itens das notas fiscais
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS itens_nota_fiscal (
                id SERIAL PRIMARY KEY,
                nota_fiscal_id INTEGER REFERENCES notas_fiscais(id),
                produto_servico_id INTEGER REFERENCES produtos_servicos(id),
                numero_item INTEGER NOT NULL,
                codigo_produto VARCHAR(50),
                descricao VARCHAR(255),
                cfop VARCHAR(10),
                unidade_comercial VARCHAR(20),
                quantidade_comercial DECIMAL(15,3),
                valor_unitario_comercial DECIMAL(15,2),
                valor_total_bruto DECIMAL(15,2),
                unidade_tributavel VARCHAR(20),
                quantidade_tributavel DECIMAL(15,3),
                valor_unitario_tributavel DECIMAL(15,2),
                valor_desconto_item DECIMAL(15,2) DEFAULT 0,
                valor_frete_item DECIMAL(15,2) DEFAULT 0,
                valor_seguro_item DECIMAL(15,2) DEFAULT 0,
                outras_despesas_item DECIMAL(15,2) DEFAULT 0,
                compoe_valor_total BOOLEAN DEFAULT TRUE,
                valor_total_item DECIMAL(15,2),
                -- Impostos do item
                cst_icms VARCHAR(10),
                origem_mercadoria VARCHAR(2),
                modalidade_bc_icms VARCHAR(2),
                base_calculo_icms_item DECIMAL(15,2) DEFAULT 0,
                aliquota_icms_item DECIMAL(5,2) DEFAULT 0,
                valor_icms_item DECIMAL(15,2) DEFAULT 0,
                cst_ipi VARCHAR(10),
                classe_enquadramento_ipi VARCHAR(10),
                codigo_produto_anp VARCHAR(20),
                base_calculo_ipi DECIMAL(15,2) DEFAULT 0,
                aliquota_ipi_item DECIMAL(5,2) DEFAULT 0,
                valor_ipi_item DECIMAL(15,2) DEFAULT 0,
                cst_pis VARCHAR(10),
                base_calculo_pis DECIMAL(15,2) DEFAULT 0,
                aliquota_pis_item DECIMAL(5,2) DEFAULT 0,
                valor_pis_item DECIMAL(15,2) DEFAULT 0,
                cst_cofins VARCHAR(10),
                base_calculo_cofins DECIMAL(15,2) DEFAULT 0,
                aliquota_cofins_item DECIMAL(5,2) DEFAULT 0,
                valor_cofins_item DECIMAL(15,2) DEFAULT 0
            )
            """)
            
            # Tabela de controle de cobrança
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS contas_receber (
                id SERIAL PRIMARY KEY,
                nota_fiscal_id INTEGER REFERENCES notas_fiscais(id),
                cliente_id INTEGER REFERENCES clientes_faturamento(id),
                numero_titulo VARCHAR(50),
                parcela INTEGER DEFAULT 1,
                total_parcelas INTEGER DEFAULT 1,
                valor_original DECIMAL(15,2),
                valor_atual DECIMAL(15,2),
                data_emissao DATE DEFAULT CURRENT_DATE,
                data_vencimento DATE NOT NULL,
                data_pagamento DATE,
                forma_pagamento VARCHAR(50),
                valor_pago DECIMAL(15,2) DEFAULT 0,
                valor_desconto DECIMAL(15,2) DEFAULT 0,
                valor_juros DECIMAL(15,2) DEFAULT 0,
                valor_multa DECIMAL(15,2) DEFAULT 0,
                observacoes TEXT,
                status VARCHAR(50) DEFAULT 'pendente',
                dias_atraso INTEGER DEFAULT 0,
                usuario_baixa_id INTEGER,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Tabela de histórico de cobrança
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_cobranca (
                id SERIAL PRIMARY KEY,
                conta_receber_id INTEGER REFERENCES contas_receber(id),
                data_acao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tipo_acao VARCHAR(50),
                descricao TEXT,
                valor_acao DECIMAL(15,2),
                usuario_id INTEGER,
                observacoes TEXT
            )
            """)
            
            # Tabela de configurações fiscais
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes_fiscais (
                id SERIAL PRIMARY KEY,
                chave VARCHAR(100) UNIQUE NOT NULL,
                valor TEXT,
                descricao TEXT,
                tipo_dado VARCHAR(20) DEFAULT 'string',
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario_atualizacao_id INTEGER
            )
            """)
            
            conn.commit()
            
            # Inserir configurações padrão
            self.inserir_configuracoes_padrao()
            self.inserir_dados_exemplo()
            
        except Exception as e:
            st.error(f"Erro ao criar tabelas de faturamento: {e}")
    
    def inserir_configuracoes_padrao(self):
        """Insere configurações fiscais padrão"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        configuracoes = [
            ('numeracao_nf_inicio', '1', 'Número inicial para numeração de NF'),
            ('serie_nf_padrao', '001', 'Série padrão para NF'),
            ('natureza_operacao_padrao', 'Venda de mercadoria', 'Natureza de operação padrão'),
            ('regime_tributario_empresa', 'Simples Nacional', 'Regime tributário da empresa'),
            ('cfop_venda_estadual', '5102', 'CFOP para vendas dentro do estado'),
            ('cfop_venda_interestadual', '6102', 'CFOP para vendas fora do estado'),
            ('aliquota_icms_interna', '18.00', 'Alíquota ICMS interna padrão'),
            ('prazo_pagamento_padrao', '30', 'Prazo de pagamento padrão em dias'),
            ('taxa_juros_mensal', '1.00', 'Taxa de juros mensal para atraso'),
            ('percentual_multa', '2.00', 'Percentual de multa por atraso')
        ]
        
        for chave, valor, descricao in configuracoes:
            cursor.execute("""
            INSERT INTO configuracoes_fiscais (chave, valor, descricao)
            VALUES (%s, %s, %s)
            ON CONFLICT (chave) DO NOTHING
            """, [chave, valor, descricao])
        
        conn.commit()
    
    def inserir_dados_exemplo(self):
        """Insere dados de exemplo para demonstração"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se já existem clientes
        cursor.execute("SELECT COUNT(*) FROM clientes_faturamento")
        if cursor.fetchone()[0] > 0:
            return
        
        # Inserir clientes exemplo
        clientes_exemplo = [
            {
                'nome_fantasia': 'Construção Silva & Cia',
                'razao_social': 'Silva Construções Ltda',
                'tipo_pessoa': 'PJ',
                'cpf_cnpj': '12.345.678/0001-90',
                'email': 'financeiro@silvaconst.com.br',
                'telefone': '(11) 99999-1111',
                'cidade': 'São Paulo',
                'estado': 'SP'
            },
            {
                'nome_fantasia': 'Obras Brasileiras',
                'razao_social': 'Obras Brasileiras Empreendimentos SA',
                'tipo_pessoa': 'PJ',
                'cpf_cnpj': '98.765.432/0001-10',
                'email': 'compras@obrasbrasileiras.com.br',
                'telefone': '(21) 88888-2222',
                'cidade': 'Rio de Janeiro',
                'estado': 'RJ'
            }
        ]
        
        for cliente in clientes_exemplo:
            cursor.execute("""
            INSERT INTO clientes_faturamento 
            (nome_fantasia, razao_social, tipo_pessoa, cpf_cnpj, email, telefone, endereco_cidade, endereco_estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                cliente['nome_fantasia'], cliente['razao_social'], cliente['tipo_pessoa'],
                cliente['cpf_cnpj'], cliente['email'], cliente['telefone'],
                cliente['cidade'], cliente['estado']
            ])
        
        # Inserir produtos/serviços exemplo
        produtos_exemplo = [
            {
                'codigo': 'FERT001',
                'descricao': 'Furadeira Elétrica Profissional',
                'tipo': 'produto',
                'preco': 450.00,
                'unidade': 'UN'
            },
            {
                'codigo': 'SERV001',
                'descricao': 'Serviço de Instalação Elétrica',
                'tipo': 'servico',
                'preco': 120.00,
                'unidade': 'HR'
            },
            {
                'codigo': 'MAT001',
                'descricao': 'Cimento Portland CP-II',
                'tipo': 'produto',
                'preco': 25.50,
                'unidade': 'SC'
            }
        ]
        
        for produto in produtos_exemplo:
            cursor.execute("""
            INSERT INTO produtos_servicos 
            (codigo, descricao, tipo, unidade_medida, preco_unitario)
            VALUES (%s, %s, %s, %s, %s)
            """, [
                produto['codigo'], produto['descricao'], produto['tipo'],
                produto['unidade'], produto['preco']
            ])
        
        conn.commit()
    
    def criar_cliente(self, dados: Dict[str, Any]) -> int:
        """Cria novo cliente"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO clientes_faturamento 
        (nome_fantasia, razao_social, tipo_pessoa, cpf_cnpj, inscricao_estadual,
         endereco_logradouro, endereco_numero, endereco_bairro, endereco_cidade,
         endereco_estado, endereco_cep, telefone, email, contato_responsavel,
         prazo_pagamento_padrao, limite_credito, regime_tributario, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, [
            dados['nome_fantasia'], dados.get('razao_social', ''),
            dados['tipo_pessoa'], dados.get('cpf_cnpj', ''),
            dados.get('inscricao_estadual', ''), dados.get('endereco_logradouro', ''),
            dados.get('endereco_numero', ''), dados.get('endereco_bairro', ''),
            dados.get('endereco_cidade', ''), dados.get('endereco_estado', ''),
            dados.get('endereco_cep', ''), dados.get('telefone', ''),
            dados.get('email', ''), dados.get('contato_responsavel', ''),
            dados.get('prazo_pagamento', 30), dados.get('limite_credito', 0),
            dados.get('regime_tributario', ''), dados.get('observacoes', '')
        ])
        
        cliente_id = cursor.fetchone()[0]
        conn.commit()
        
        log_acao("faturamento", "criar_cliente", f"Cliente criado: {dados['nome_fantasia']}")
        return cliente_id
    
    def criar_produto_servico(self, dados: Dict[str, Any]) -> int:
        """Cria novo produto/serviço"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO produtos_servicos
        (codigo, descricao, tipo, unidade_medida, preco_unitario, codigo_ncm,
         cfop_padrao, cst_icms, aliquota_icms, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, [
            dados['codigo'], dados['descricao'], dados['tipo'],
            dados['unidade_medida'], dados['preco_unitario'],
            dados.get('codigo_ncm', ''), dados.get('cfop_padrao', ''),
            dados.get('cst_icms', ''), dados.get('aliquota_icms', 0),
            dados.get('observacoes', '')
        ])
        
        produto_id = cursor.fetchone()[0]
        conn.commit()
        
        log_acao("faturamento", "criar_produto", f"Produto/Serviço criado: {dados['descricao']}")
        return produto_id
    
    def obter_proximo_numero_nf(self) -> int:
        """Obtém próximo número de NF"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(numero_nf) FROM notas_fiscais")
        ultimo_numero = cursor.fetchone()[0]
        
        if ultimo_numero is None:
            cursor.execute("SELECT valor FROM configuracoes_fiscais WHERE chave = 'numeracao_nf_inicio'")
            resultado = cursor.fetchone()
            return int(resultado[0]) if resultado else 1
        
        return ultimo_numero + 1
    
    def criar_nota_fiscal(self, dados: Dict[str, Any]) -> int:
        """Cria nova nota fiscal"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Calcular valores totais
        valor_produtos = sum(item['valor_total'] for item in dados['itens'] if dados['itens'])
        valor_total = valor_produtos + dados.get('valor_frete', 0) - dados.get('valor_desconto', 0)
        
        cursor.execute("""
        INSERT INTO notas_fiscais
        (numero_nf, serie, tipo_nf, cliente_id, data_emissao, natureza_operacao,
         valor_produtos, valor_desconto, valor_frete, valor_total, usuario_emissao_id, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, [
            dados['numero_nf'], dados.get('serie', '001'), dados.get('tipo_nf', 'saida'),
            dados['cliente_id'], dados.get('data_emissao', datetime.now().date()),
            dados.get('natureza_operacao', 'Venda de mercadoria'),
            valor_produtos, dados.get('valor_desconto', 0), dados.get('valor_frete', 0),
            valor_total, dados.get('usuario_id', 1), dados.get('observacoes', '')
        ])
        
        nota_id = cursor.fetchone()[0]
        
        # Inserir itens
        for i, item in enumerate(dados.get('itens', []), 1):
            cursor.execute("""
            INSERT INTO itens_nota_fiscal
            (nota_fiscal_id, produto_servico_id, numero_item, codigo_produto, descricao,
             cfop, unidade_comercial, quantidade_comercial, valor_unitario_comercial,
             valor_total_bruto, valor_total_item)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                nota_id, item['produto_id'], i, item['codigo'], item['descricao'],
                item.get('cfop', '5102'), item['unidade'], item['quantidade'],
                item['valor_unitario'], item['valor_total'], item['valor_total']
            ])
        
        conn.commit()
        
        # Criar conta a receber
        if dados.get('gerar_cobranca', True):
            self.criar_conta_receber(nota_id, dados['cliente_id'], valor_total, dados.get('prazo_pagamento', 30))
        
        log_acao("faturamento", "criar_nf", f"Nota fiscal {dados['numero_nf']} criada")
        return nota_id
    
    def criar_conta_receber(self, nota_fiscal_id: int, cliente_id: int, valor: float, prazo_dias: int):
        """Cria conta a receber"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        data_vencimento = datetime.now().date() + timedelta(days=prazo_dias)
        
        cursor.execute("""
        SELECT numero_nf FROM notas_fiscais WHERE id = %s
        """, [nota_fiscal_id])
        numero_nf = cursor.fetchone()[0]
        
        cursor.execute("""
        INSERT INTO contas_receber
        (nota_fiscal_id, cliente_id, numero_titulo, valor_original, valor_atual, data_vencimento)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, [nota_fiscal_id, cliente_id, f"NF-{numero_nf}", valor, valor, data_vencimento])
        
        conn.commit()
    
    def baixar_conta_receber(self, conta_id: int, dados_baixa: Dict[str, Any]):
        """Realiza baixa de conta a receber"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Atualizar conta
        cursor.execute("""
        UPDATE contas_receber 
        SET data_pagamento = %s, valor_pago = %s, valor_desconto = %s,
            valor_juros = %s, valor_multa = %s, forma_pagamento = %s,
            status = 'pago', observacoes = %s, usuario_baixa_id = %s
        WHERE id = %s
        """, [
            dados_baixa['data_pagamento'], dados_baixa['valor_pago'],
            dados_baixa.get('valor_desconto', 0), dados_baixa.get('valor_juros', 0),
            dados_baixa.get('valor_multa', 0), dados_baixa['forma_pagamento'],
            dados_baixa.get('observacoes', ''), dados_baixa.get('usuario_id', 1), conta_id
        ])
        
        # Registrar no histórico
        cursor.execute("""
        INSERT INTO historico_cobranca 
        (conta_receber_id, tipo_acao, descricao, valor_acao, usuario_id)
        VALUES (%s, 'baixa', %s, %s, %s)
        """, [
            conta_id, f"Pagamento recebido via {dados_baixa['forma_pagamento']}",
            dados_baixa['valor_pago'], dados_baixa.get('usuario_id', 1)
        ])
        
        conn.commit()
        
        log_acao("faturamento", "baixar_conta", f"Conta {conta_id} baixada")
    
    def calcular_juros_multa(self, conta_id: int) -> Dict[str, float]:
        """Calcula juros e multa para conta em atraso"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT valor_atual, data_vencimento, dias_atraso
        FROM contas_receber 
        WHERE id = %s AND status = 'pendente'
        """, [conta_id])
        
        conta = cursor.fetchone()
        if not conta:
            return {'juros': 0, 'multa': 0}
        
        valor_original = conta['valor_atual']
        dias_atraso = (datetime.now().date() - conta['data_vencimento']).days
        
        if dias_atraso <= 0:
            return {'juros': 0, 'multa': 0}
        
        # Buscar configurações
        cursor.execute("SELECT valor FROM configuracoes_fiscais WHERE chave = 'taxa_juros_mensal'")
        taxa_juros = float(cursor.fetchone()[0]) / 100
        
        cursor.execute("SELECT valor FROM configuracoes_fiscais WHERE chave = 'percentual_multa'")
        perc_multa = float(cursor.fetchone()[0]) / 100
        
        # Calcular juros (proporcional aos dias)
        juros = valor_original * (taxa_juros / 30) * dias_atraso
        
        # Multa aplicada apenas uma vez
        multa = valor_original * perc_multa if dias_atraso > 0 else 0
        
        return {'juros': round(juros, 2), 'multa': round(multa, 2)}
    
    def atualizar_contas_em_atraso(self):
        """Atualiza dados de contas em atraso"""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE contas_receber 
        SET dias_atraso = CASE 
            WHEN CURRENT_DATE > data_vencimento THEN CURRENT_DATE - data_vencimento
            ELSE 0
        END
        WHERE status = 'pendente'
        """)
        
        conn.commit()

def show_faturamento_page():
    """Exibe página do sistema de faturamento"""
    st.title("💰 Sistema de Faturamento")
    st.markdown("Gestão completa de faturamento, cobrança e controle fiscal")
    
    manager = FaturamentoManager()
    
    # Atualizar contas em atraso
    manager.atualizar_contas_em_atraso()
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Dashboard", "👥 Clientes", "📦 Produtos/Serviços", 
        "📄 Notas Fiscais", "💳 Contas a Receber", "📈 Relatórios", "⚙️ Configurações"
    ])
    
    with tab1:
        st.subheader("📊 Dashboard de Faturamento")
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cursor.execute("SELECT COUNT(*) FROM notas_fiscais WHERE EXTRACT(MONTH FROM data_emissao) = EXTRACT(MONTH FROM CURRENT_DATE)")
            nfs_mes = cursor.fetchone()[0]
            st.metric("NFs do Mês", nfs_mes)
        
        with col2:
            cursor.execute("SELECT COALESCE(SUM(valor_total), 0) FROM notas_fiscais WHERE EXTRACT(MONTH FROM data_emissao) = EXTRACT(MONTH FROM CURRENT_DATE)")
            faturamento_mes = cursor.fetchone()[0]
            st.metric("Faturamento Mês", f"R$ {faturamento_mes:,.2f}")
        
        with col3:
            cursor.execute("SELECT COUNT(*) FROM contas_receber WHERE status = 'pendente'")
            contas_pendentes = cursor.fetchone()[0]
            st.metric("Contas Pendentes", contas_pendentes)
        
        with col4:
            cursor.execute("SELECT COUNT(*) FROM contas_receber WHERE status = 'pendente' AND data_vencimento < CURRENT_DATE")
            contas_vencidas = cursor.fetchone()[0]
            st.metric("Contas Vencidas", contas_vencidas, delta_color="inverse")
        
        # Gráfico de faturamento
        cursor.execute("""
        SELECT DATE_TRUNC('month', data_emissao) as mes, 
               COALESCE(SUM(valor_total), 0) as total
        FROM notas_fiscais
        WHERE data_emissao >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY mes
        ORDER BY mes
        """)
        
        dados_faturamento = cursor.fetchall()
        
        if dados_faturamento:
            df_faturamento = pd.DataFrame(dados_faturamento, columns=['mes', 'total'])
            fig = px.line(df_faturamento, x='mes', y='total', 
                         title='Evolução do Faturamento (12 meses)')
            fig.update_traces(line_color='#1f77b4', line_width=3)
            st.plotly_chart(fig, use_container_width=True)
        
        # Contas vencidas - alertas
        cursor.execute("""
        SELECT cr.numero_titulo, cf.nome_fantasia, cr.valor_atual, cr.data_vencimento, cr.dias_atraso
        FROM contas_receber cr
        JOIN clientes_faturamento cf ON cr.cliente_id = cf.id
        WHERE cr.status = 'pendente' AND cr.data_vencimento < CURRENT_DATE
        ORDER BY cr.dias_atraso DESC
        LIMIT 10
        """)
        
        contas_vencidas_dados = cursor.fetchall()
        
        if contas_vencidas_dados:
            st.subheader("🚨 Contas Vencidas")
            for conta in contas_vencidas_dados:
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.error(f"**{conta['numero_titulo']}** - {conta['nome_fantasia']}")
                with col_b:
                    st.write(f"Valor: R$ {conta['valor_atual']:,.2f}")
                with col_c:
                    st.write(f"Atraso: {conta['dias_atraso']} dias")
    
    with tab2:
        st.subheader("👥 Gestão de Clientes")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**Clientes Cadastrados**")
            
            cursor.execute("""
            SELECT * FROM clientes_faturamento 
            WHERE ativo = TRUE 
            ORDER BY nome_fantasia
            """)
            clientes = cursor.fetchall()
            
            if clientes:
                for cliente in clientes:
                    with st.expander(f"👤 {cliente['nome_fantasia']} - {cliente['endereco_cidade']}/{cliente['endereco_estado']}"):
                        col_a, col_b, col_c = st.columns(3)
                        
                        with col_a:
                            st.write(f"**Razão Social:** {cliente['razao_social'] or 'N/A'}")
                            st.write(f"**Tipo:** {'Pessoa Jurídica' if cliente['tipo_pessoa'] == 'PJ' else 'Pessoa Física'}")
                            st.write(f"**CPF/CNPJ:** {cliente['cpf_cnpj'] or 'N/A'}")
                        
                        with col_b:
                            st.write(f"**Email:** {cliente['email'] or 'N/A'}")
                            st.write(f"**Telefone:** {cliente['telefone'] or 'N/A'}")
                            st.write(f"**Prazo Pagto:** {cliente['prazo_pagamento_padrao']} dias")
                        
                        with col_c:
                            if cliente['limite_credito']:
                                st.write(f"**Limite Crédito:** R$ {cliente['limite_credito']:,.2f}")
                            if cliente['regime_tributario']:
                                st.write(f"**Regime:** {cliente['regime_tributario']}")
                            
                            # Mostrar resumo financeiro
                            cursor.execute("""
                            SELECT COUNT(*) as total_nfs, COALESCE(SUM(valor_total), 0) as total_faturado
                            FROM notas_fiscais WHERE cliente_id = %s
                            """, [cliente['id']])
                            resumo = cursor.fetchone()
                            
                            st.write(f"**NFs Emitidas:** {resumo['total_nfs']}")
                            st.write(f"**Total Faturado:** R$ {resumo['total_faturado']:,.2f}")
            else:
                st.info("ℹ️ Nenhum cliente cadastrado")
        
        with col2:
            st.write("**Cadastrar Novo Cliente**")
            
            with st.form("novo_cliente"):
                nome_fantasia = st.text_input("Nome Fantasia*:")
                razao_social = st.text_input("Razão Social:")
                tipo_pessoa = st.selectbox("Tipo:", ["PJ", "PF"])
                cpf_cnpj = st.text_input("CPF/CNPJ:")
                
                email = st.text_input("Email:")
                telefone = st.text_input("Telefone:")
                
                endereco_logradouro = st.text_input("Logradouro:")
                col_end1, col_end2 = st.columns(2)
                with col_end1:
                    endereco_cidade = st.text_input("Cidade:")
                with col_end2:
                    endereco_estado = st.text_input("UF:", max_chars=2)
                
                prazo_pagamento = st.number_input("Prazo Pagamento (dias):", 
                                                min_value=1, value=30)
                limite_credito = st.number_input("Limite de Crédito (R$):", 
                                               min_value=0.0, step=100.0)
                
                if st.form_submit_button("➕ Cadastrar Cliente"):
                    if nome_fantasia:
                        try:
                            dados_cliente = {
                                'nome_fantasia': nome_fantasia,
                                'razao_social': razao_social,
                                'tipo_pessoa': tipo_pessoa,
                                'cpf_cnpj': cpf_cnpj,
                                'email': email,
                                'telefone': telefone,
                                'endereco_logradouro': endereco_logradouro,
                                'endereco_cidade': endereco_cidade,
                                'endereco_estado': endereco_estado,
                                'prazo_pagamento': prazo_pagamento,
                                'limite_credito': limite_credito
                            }
                            
                            cliente_id = manager.criar_cliente(dados_cliente)
                            st.success(f"✅ Cliente cadastrado! ID: {cliente_id}")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao cadastrar cliente: {e}")
                    else:
                        st.error("❌ Preencha o nome fantasia")
    
    with tab3:
        st.subheader("📦 Produtos e Serviços")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            cursor.execute("SELECT * FROM produtos_servicos WHERE ativo = TRUE ORDER BY descricao")
            produtos = cursor.fetchall()
            
            if produtos:
                for produto in produtos:
                    with st.expander(f"📦 {produto['codigo']} - {produto['descricao']}"):
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            st.write(f"**Tipo:** {'Produto' if produto['tipo'] == 'produto' else 'Serviço'}")
                            st.write(f"**Unidade:** {produto['unidade_medida']}")
                            st.write(f"**Preço:** R$ {produto['preco_unitario']:,.2f}")
                        
                        with col_b:
                            if produto['codigo_ncm']:
                                st.write(f"**NCM:** {produto['codigo_ncm']}")
                            if produto['cfop_padrao']:
                                st.write(f"**CFOP:** {produto['cfop_padrao']}")
                            if produto['aliquota_icms']:
                                st.write(f"**ICMS:** {produto['aliquota_icms']}%")
        
        with col2:
            st.write("**Cadastrar Produto/Serviço**")
            
            with st.form("novo_produto"):
                codigo = st.text_input("Código*:")
                descricao = st.text_input("Descrição*:")
                tipo = st.selectbox("Tipo:", ["produto", "servico"])
                unidade_medida = st.selectbox("Unidade:", [
                    "UN", "KG", "M", "M2", "M3", "L", "HR", "PC", "CX", "SC"
                ])
                preco_unitario = st.number_input("Preço Unitário (R$)*:", 
                                               min_value=0.01, step=0.01)
                
                if st.form_submit_button("➕ Cadastrar"):
                    if codigo and descricao and preco_unitario > 0:
                        try:
                            dados_produto = {
                                'codigo': codigo,
                                'descricao': descricao,
                                'tipo': tipo,
                                'unidade_medida': unidade_medida,
                                'preco_unitario': preco_unitario
                            }
                            
                            produto_id = manager.criar_produto_servico(dados_produto)
                            st.success(f"✅ Produto/Serviço cadastrado! ID: {produto_id}")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao cadastrar: {e}")
                    else:
                        st.error("❌ Preencha os campos obrigatórios")
    
    with tab4:
        st.subheader("📄 Emissão de Notas Fiscais")
        
        # Formulário de nova NF
        with st.form("nova_nf"):
            st.write("**Nova Nota Fiscal**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                numero_nf = manager.obter_proximo_numero_nf()
                st.number_input("Número NF:", value=numero_nf, disabled=True)
                
                cursor.execute("SELECT id, nome_fantasia FROM clientes_faturamento WHERE ativo = TRUE")
                clientes = cursor.fetchall()
                cliente_opcoes = {f"{c.nome_fantasia}": c.id for c in clientes}
                cliente_selecionado = st.selectbox("Cliente*:", list(cliente_opcoes.keys()))
                
            with col2:
                data_emissao = st.date_input("Data Emissão:", value=datetime.now().date())
                natureza_operacao = st.text_input("Natureza da Operação:", 
                                                value="Venda de mercadoria")
            
            with col3:
                serie = st.text_input("Série:", value="001")
                
            st.subheader("Itens da Nota Fiscal")
            
            # Buscar produtos
            cursor.execute("SELECT id, codigo, descricao, preco_unitario, unidade_medida FROM produtos_servicos WHERE ativo = TRUE")
            produtos = cursor.fetchall()
            
            # Usar session_state para manter itens
            if 'itens_nf' not in st.session_state:
                st.session_state.itens_nf = []
            
            # Adicionar item
            col_item1, col_item2, col_item3, col_item4 = st.columns(4)
            
            with col_item1:
                produto_opcoes = {f"{p.codigo} - {p.descricao}": p for p in produtos}
                produto_selecionado = st.selectbox("Produto/Serviço:", 
                                                  ["Selecione..."] + list(produto_opcoes.keys()))
            
            with col_item2:
                quantidade = st.number_input("Quantidade:", min_value=0.001, step=0.001, format="%.3f")
            
            with col_item3:
                if produto_selecionado != "Selecione...":
                    produto = produto_opcoes[produto_selecionado]
                    valor_unitario = st.number_input("Valor Unitário (R$):", 
                                                   value=float(produto.preco_unitario), 
                                                   min_value=0.01, step=0.01)
                else:
                    valor_unitario = st.number_input("Valor Unitário (R$):", 
                                                   min_value=0.01, step=0.01)
            
            with col_item4:
                valor_total_item = quantidade * valor_unitario
                st.write(f"**Total:** R$ {valor_total_item:,.2f}")
                
                if st.button("➕ Adicionar Item"):
                    if produto_selecionado != "Selecione..." and quantidade > 0:
                        produto = produto_opcoes[produto_selecionado]
                        item = {
                            'produto_id': produto.id,
                            'codigo': produto.codigo,
                            'descricao': produto.descricao,
                            'unidade': produto.unidade_medida,
                            'quantidade': quantidade,
                            'valor_unitario': valor_unitario,
                            'valor_total': valor_total_item
                        }
                        st.session_state.itens_nf.append(item)
                        st.rerun()
            
            # Mostrar itens adicionados
            if st.session_state.itens_nf:
                st.write("**Itens Adicionados:**")
                for i, item in enumerate(st.session_state.itens_nf):
                    col_a, col_b, col_c = st.columns([3, 2, 1])
                    with col_a:
                        st.write(f"{item['codigo']} - {item['descricao']}")
                    with col_b:
                        st.write(f"Qtd: {item['quantidade']} {item['unidade']} × R$ {item['valor_unitario']:,.2f}")
                    with col_c:
                        if st.button("🗑️", key=f"remove_{i}"):
                            st.session_state.itens_nf.pop(i)
                            st.rerun()
                
                # Totais
                valor_total_produtos = sum(item['valor_total'] for item in st.session_state.itens_nf)
                
                col_total1, col_total2, col_total3 = st.columns(3)
                with col_total1:
                    valor_desconto = st.number_input("Desconto (R$):", min_value=0.0, step=10.0)
                with col_total2:
                    valor_frete = st.number_input("Frete (R$):", min_value=0.0, step=10.0)
                with col_total3:
                    valor_total_nf = valor_total_produtos - valor_desconto + valor_frete
                    st.write(f"**TOTAL NF:** R$ {valor_total_nf:,.2f}")
            
            observacoes = st.text_area("Observações:")
            
            if st.form_submit_button("📄 Emitir Nota Fiscal"):
                if cliente_selecionado and st.session_state.itens_nf:
                    try:
                        dados_nf = {
                            'numero_nf': numero_nf,
                            'serie': serie,
                            'cliente_id': cliente_opcoes[cliente_selecionado],
                            'data_emissao': data_emissao,
                            'natureza_operacao': natureza_operacao,
                            'valor_desconto': valor_desconto,
                            'valor_frete': valor_frete,
                            'itens': st.session_state.itens_nf,
                            'observacoes': observacoes
                        }
                        
                        nota_id = manager.criar_nota_fiscal(dados_nf)
                        st.success(f"✅ Nota Fiscal {numero_nf} emitida com sucesso! ID: {nota_id}")
                        
                        # Limpar itens
                        st.session_state.itens_nf = []
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao emitir NF: {e}")
                else:
                    st.error("❌ Selecione cliente e adicione pelo menos um item")
        
        # Listar NFs emitidas
        st.subheader("📋 Notas Fiscais Emitidas")
        
        cursor.execute("""
        SELECT nf.numero_nf, nf.serie, nf.data_emissao, cf.nome_fantasia,
               nf.valor_total, nf.status_nf
        FROM notas_fiscais nf
        JOIN clientes_faturamento cf ON nf.cliente_id = cf.id
        ORDER BY nf.data_criacao DESC
        LIMIT 20
        """)
        
        nfs_emitidas = cursor.fetchall()
        
        if nfs_emitidas:
            for nf in nfs_emitidas:
                with st.expander(f"📄 NF {nf['numero_nf']}/{nf['serie']} - {nf['nome_fantasia']} - R$ {nf['valor_total']:,.2f}"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Data Emissão:** {nf['data_emissao']}")
                        st.write(f"**Cliente:** {nf['nome_fantasia']}")
                    with col_b:
                        st.write(f"**Valor:** R$ {nf['valor_total']:,.2f}")
                        st.write(f"**Status:** {nf['status_nf']}")
    
    with tab5:
        st.subheader("💳 Contas a Receber")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filtro = st.selectbox("Status:", ["Todos", "pendente", "pago", "vencido"])
        
        # Query base
        query = """
        SELECT cr.*, cf.nome_fantasia, nf.numero_nf
        FROM contas_receber cr
        JOIN clientes_faturamento cf ON cr.cliente_id = cf.id
        LEFT JOIN notas_fiscais nf ON cr.nota_fiscal_id = nf.id
        """
        
        if status_filtro != "Todos":
            if status_filtro == "vencido":
                query += " WHERE cr.status = 'pendente' AND cr.data_vencimento < CURRENT_DATE"
            else:
                query += f" WHERE cr.status = '{status_filtro}'"
        
        query += " ORDER BY cr.data_vencimento ASC"
        
        cursor.execute(query)
        contas = cursor.fetchall()
        
        if contas:
            for conta in contas:
                # Calcular juros e multa se em atraso
                juros_multa = {'juros': 0, 'multa': 0}
                if conta['status'] == 'pendente' and conta['data_vencimento'] < datetime.now().date():
                    juros_multa = manager.calcular_juros_multa(conta['id'])
                
                valor_total_conta = conta['valor_atual'] + juros_multa['juros'] + juros_multa['multa']
                
                # Determinar cor do expander baseado no status
                status_color = "🔴" if conta['status'] == 'pendente' and conta['data_vencimento'] < datetime.now().date() else "🟡" if conta['status'] == 'pendente' else "🟢"
                
                with st.expander(f"{status_color} {conta['numero_titulo']} - {conta['nome_fantasia']} - R$ {valor_total_conta:,.2f}"):
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.write(f"**Valor Original:** R$ {conta['valor_original']:,.2f}")
                        st.write(f"**Data Vencimento:** {conta['data_vencimento']}")
                        st.write(f"**Status:** {conta['status']}")
                    
                    with col_b:
                        if conta['dias_atraso'] > 0:
                            st.write(f"**Dias Atraso:** {conta['dias_atraso']}")
                            if juros_multa['juros'] > 0:
                                st.write(f"**Juros:** R$ {juros_multa['juros']:,.2f}")
                            if juros_multa['multa'] > 0:
                                st.write(f"**Multa:** R$ {juros_multa['multa']:,.2f}")
                        
                        if conta['data_pagamento']:
                            st.write(f"**Data Pagamento:** {conta['data_pagamento']}")
                            st.write(f"**Valor Pago:** R$ {conta['valor_pago']:,.2f}")
                    
                    with col_c:
                        if conta['status'] == 'pendente':
                            st.write(f"**Total a Receber:** R$ {valor_total_conta:,.2f}")
                            
                            # Botão para baixar conta
                            if st.button("💰 Baixar Conta", key=f"baixar_{conta['id']}"):
                                st.session_state[f'baixar_conta_{conta["id"]}'] = True
                    
                    # Formulário de baixa (se solicitado)
                    if st.session_state.get(f'baixar_conta_{conta["id"]}', False):
                        with st.form(f"baixa_{conta['id']}"):
                            st.write("**Registrar Pagamento**")
                            
                            col_baixa1, col_baixa2 = st.columns(2)
                            
                            with col_baixa1:
                                data_pagamento = st.date_input("Data Pagamento:", 
                                                             value=datetime.now().date())
                                valor_pago = st.number_input("Valor Pago (R$):", 
                                                           value=valor_total_conta,
                                                           min_value=0.01, step=0.01)
                            
                            with col_baixa2:
                                forma_pagamento = st.selectbox("Forma Pagamento:", [
                                    "Dinheiro", "PIX", "Transferência", "Boleto", "Cartão", "Cheque"
                                ])
                                valor_desconto = st.number_input("Desconto (R$):", 
                                                                min_value=0.0, step=0.01)
                            
                            obs_baixa = st.text_area("Observações:")
                            
                            if st.form_submit_button("💾 Confirmar Baixa"):
                                try:
                                    dados_baixa = {
                                        'data_pagamento': data_pagamento,
                                        'valor_pago': valor_pago,
                                        'valor_desconto': valor_desconto,
                                        'valor_juros': juros_multa['juros'],
                                        'valor_multa': juros_multa['multa'],
                                        'forma_pagamento': forma_pagamento,
                                        'observacoes': obs_baixa
                                    }
                                    
                                    manager.baixar_conta_receber(conta['id'], dados_baixa)
                                    st.success("✅ Conta baixada com sucesso!")
                                    
                                    # Limpar session state
                                    del st.session_state[f'baixar_conta_{conta["id"]}']
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ Erro ao baixar conta: {e}")
        else:
            st.info("ℹ️ Nenhuma conta encontrada")
    
    with tab6:
        st.subheader("📈 Relatórios Financeiros")
        
        # Período para relatórios
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data Início:", 
                                      value=datetime.now().date().replace(day=1))
        with col2:
            data_fim = st.date_input("Data Fim:", value=datetime.now().date())
        
        # Relatório de faturamento
        cursor.execute("""
        SELECT 
            DATE_TRUNC('month', data_emissao) as mes,
            COUNT(*) as qtd_nfs,
            SUM(valor_total) as faturamento_total
        FROM notas_fiscais 
        WHERE data_emissao BETWEEN %s AND %s
        GROUP BY mes
        ORDER BY mes
        """, [data_inicio, data_fim])
        
        dados_faturamento = cursor.fetchall()
        
        if dados_faturamento:
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                df_fat = pd.DataFrame(dados_faturamento)
                fig1 = px.bar(df_fat, x='mes', y='faturamento_total', 
                             title='Faturamento por Mês')
                st.plotly_chart(fig1, use_container_width=True)
            
            with col_graf2:
                fig2 = px.line(df_fat, x='mes', y='qtd_nfs', 
                              title='Quantidade de NFs por Mês')
                st.plotly_chart(fig2, use_container_width=True)
        
        # Relatório de recebimento
        cursor.execute("""
        SELECT 
            DATE_TRUNC('month', data_pagamento) as mes,
            COUNT(*) as qtd_recebimentos,
            SUM(valor_pago) as valor_recebido
        FROM contas_receber 
        WHERE status = 'pago' AND data_pagamento BETWEEN %s AND %s
        GROUP BY mes
        ORDER BY mes
        """, [data_inicio, data_fim])
        
        dados_recebimento = cursor.fetchall()
        
        if dados_recebimento:
            st.subheader("💰 Recebimentos Realizados")
            df_receb = pd.DataFrame(dados_recebimento)
            
            fig3 = px.bar(df_receb, x='mes', y='valor_recebido',
                         title='Recebimentos por Mês', color_discrete_sequence=['green'])
            st.plotly_chart(fig3, use_container_width=True)
        
        # Resumo de contas a receber
        cursor.execute("""
        SELECT 
            status,
            COUNT(*) as quantidade,
            SUM(valor_atual) as valor_total
        FROM contas_receber 
        GROUP BY status
        """)
        
        resumo_contas = cursor.fetchall()
        
        if resumo_contas:
            st.subheader("📊 Resumo de Contas a Receber")
            
            for item in resumo_contas:
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    st.metric(f"Contas {item['status'].title()}", item['quantidade'])
                with col_res2:
                    st.metric(f"Valor {item['status'].title()}", f"R$ {item['valor_total']:,.2f}")
    
    with tab7:
        st.subheader("⚙️ Configurações Fiscais")
        
        cursor.execute("SELECT * FROM configuracoes_fiscais ORDER BY chave")
        configuracoes = cursor.fetchall()
        
        if configuracoes:
            for config in configuracoes:
                with st.expander(f"⚙️ {config['chave']} - {config['descricao']}"):
                    novo_valor = st.text_input("Valor:", value=config['valor'], 
                                             key=f"config_{config['id']}")
                    
                    if st.button("💾 Atualizar", key=f"update_{config['id']}"):
                        cursor.execute("""
                        UPDATE configuracoes_fiscais 
                        SET valor = %s, data_atualizacao = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """, [novo_valor, config['id']])
                        
                        conn.commit()
                        st.success("✅ Configuração atualizada!")
                        st.rerun()

if __name__ == "__main__":
    show_faturamento_page()