import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
from database.connection import db

class RelatoriosCustomizaveisManager:
    """Sistema de relatórios customizáveis com templates"""
    
    def __init__(self):
        self.templates_disponiveis = {
            'insumos_estoque': {
                'nome': 'Relatório de Estoque de Insumos',
                'descricao': 'Análise completa do estoque atual',
                'query': '''
                    SELECT 
                        i.codigo,
                        i.nome,
                        i.quantidade_atual,
                        i.quantidade_minima,
                        i.preco_unitario,
                        i.quantidade_atual * i.preco_unitario as valor_total,
                        CASE 
                            WHEN i.quantidade_atual <= i.quantidade_minima THEN 'Crítico'
                            WHEN i.quantidade_atual <= i.quantidade_minima * 1.5 THEN 'Baixo'
                            ELSE 'Normal'
                        END as status_estoque
                    FROM insumos i
                    WHERE i.ativo = TRUE
                    ORDER BY status_estoque DESC, i.quantidade_atual ASC
                ''',
                'colunas': ['codigo', 'nome', 'quantidade_atual', 'quantidade_minima', 'preco_unitario', 'valor_total', 'status_estoque'],
                'graficos': ['status_estoque', 'valor_total']
            },
            'equipamentos_utilizacao': {
                'nome': 'Relatório de Utilização de Equipamentos',
                'descricao': 'Análise de uso e movimentação de equipamentos',
                'query': '''
                    SELECT 
                        ee.nome,
                        ee.codigo,
                        COUNT(m.id) as total_movimentacoes,
                        MAX(m.data_movimentacao) as ultima_utilizacao,
                        ee.valor_compra,
                        DATE_PART('year', AGE(NOW(), ee.data_aquisicao)) as idade_anos
                    FROM equipamentos_eletricos ee
                    LEFT JOIN movimentacoes m ON ee.id = m.equipamento_id
                    WHERE ee.ativo = TRUE
                    GROUP BY ee.id, ee.nome, ee.codigo, ee.valor_compra, ee.data_aquisicao
                    ORDER BY total_movimentacoes DESC
                ''',
                'colunas': ['nome', 'codigo', 'total_movimentacoes', 'ultima_utilizacao', 'valor_compra', 'idade_anos'],
                'graficos': ['total_movimentacoes', 'idade_anos']
            },
            'movimentacoes_periodo': {
                'nome': 'Relatório de Movimentações por Período',
                'descricao': 'Análise de movimentações em período específico',
                'query': '''
                    SELECT 
                        DATE(m.data_movimentacao) as data,
                        m.tipo_movimentacao,
                        COUNT(*) as quantidade_movimentacoes,
                        u.nome as usuario
                    FROM movimentacoes m
                    JOIN usuarios u ON m.usuario_id = u.id
                    WHERE m.data_movimentacao >= CURRENT_DATE - INTERVAL '{dias} days'
                    GROUP BY DATE(m.data_movimentacao), m.tipo_movimentacao, u.nome
                    ORDER BY data DESC
                ''',
                'parametros': {'dias': 30},
                'colunas': ['data', 'tipo_movimentacao', 'quantidade_movimentacoes', 'usuario'],
                'graficos': ['quantidade_movimentacoes', 'tipo_movimentacao']
            }
        }
    
    def listar_templates(self) -> List[Dict[str, Any]]:
        """Lista templates disponíveis"""
        return [
            {
                'id': key,
                'nome': template['nome'],
                'descricao': template['descricao']
            }
            for key, template in self.templates_disponiveis.items()
        ]
    
    def gerar_relatorio(self, template_id: str, parametros: Dict[str, Any] = None) -> Dict[str, Any]:
        """Gera relatório baseado no template"""
        try:
            if template_id not in self.templates_disponiveis:
                return {'erro': 'Template não encontrado'}
            
            template = self.templates_disponiveis[template_id]
            query = template['query']
            
            # Aplicar parâmetros se houver
            if parametros and 'parametros' in template:
                for param, valor in parametros.items():
                    query = query.replace(f'{{{param}}}', str(valor))
            elif 'parametros' in template:
                # Usar valores padrão
                for param, valor in template['parametros'].items():
                    query = query.replace(f'{{{param}}}', str(valor))
            
            conn = db.get_connection()
            
            # Executar query
            df = pd.read_sql(query, conn)
            
            if df.empty:
                return {
                    'sucesso': True,
                    'dados': [],
                    'total_registros': 0,
                    'mensagem': 'Nenhum dado encontrado para os critérios especificados'
                }
            
            return {
                'sucesso': True,
                'dados': df.to_dict('records'),
                'dataframe': df,
                'total_registros': len(df),
                'colunas': template['colunas'],
                'graficos_sugeridos': template.get('graficos', []),
                'template_info': {
                    'nome': template['nome'],
                    'descricao': template['descricao']
                }
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def criar_template_customizado(self, nome: str, query: str, colunas: List[str]) -> Dict[str, Any]:
        """Cria template customizado"""
        try:
            template_id = nome.lower().replace(' ', '_')
            
            # Validação básica da query
            if not query.strip().upper().startswith('SELECT'):
                return {'erro': 'Query deve começar com SELECT'}
            
            self.templates_disponiveis[template_id] = {
                'nome': nome,
                'descricao': f'Template customizado: {nome}',
                'query': query,
                'colunas': colunas,
                'graficos': [],
                'customizado': True
            }
            
            return {
                'sucesso': True,
                'template_id': template_id,
                'mensagem': 'Template customizado criado com sucesso'
            }
            
        except Exception as e:
            return {'erro': str(e)}

def mostrar_relatorio_dados(dados_relatorio: Dict[str, Any]):
    """Exibe dados do relatório"""
    if not dados_relatorio['sucesso']:
        st.error(f"Erro ao gerar relatório: {dados_relatorio['erro']}")
        return
    
    info = dados_relatorio['template_info']
    st.subheader(f"📊 {info['nome']}")
    st.write(info['descricao'])
    
    if dados_relatorio['total_registros'] == 0:
        st.warning(dados_relatorio['mensagem'])
        return
    
    # Exibir métricas
    st.metric("Total de Registros", dados_relatorio['total_registros'])
    
    # Tabela de dados
    df = dados_relatorio['dataframe']
    st.subheader("📋 Dados")
    st.dataframe(df, use_container_width=True)
    
    # Gráficos sugeridos
    if dados_relatorio['graficos_sugeridos']:
        st.subheader("📈 Visualizações")
        
        for coluna in dados_relatorio['graficos_sugeridos']:
            if coluna in df.columns:
                if df[coluna].dtype in ['object', 'category']:
                    # Gráfico de barras para dados categóricos
                    valor_counts = df[coluna].value_counts()
                    fig = px.bar(
                        x=valor_counts.index,
                        y=valor_counts.values,
                        title=f"Distribuição de {coluna.title()}"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                elif df[coluna].dtype in ['int64', 'float64']:
                    # Histograma para dados numéricos
                    fig = px.histogram(
                        df,
                        x=coluna,
                        title=f"Distribuição de {coluna.title()}"
                    )
                    st.plotly_chart(fig, use_container_width=True)

def show_relatorios_customizaveis_page():
    """Interface do sistema de relatórios customizáveis"""
    st.title("📊 Relatórios Customizáveis")
    
    manager = RelatoriosCustomizaveisManager()
    
    # Tabs para diferentes seções
    tab1, tab2, tab3 = st.tabs(["🔧 Gerar Relatório", "📝 Template Customizado", "📚 Templates Disponíveis"])
    
    with tab1:
        st.header("🔧 Gerar Relatório")
        
        templates = manager.listar_templates()
        template_opcoes = {t['nome']: t['id'] for t in templates}
        
        template_selecionado = st.selectbox(
            "Selecione um Template",
            options=list(template_opcoes.keys())
        )
        
        if template_selecionado:
            template_id = template_opcoes[template_selecionado]
            
            # Parâmetros específicos para alguns templates
            parametros = {}
            if template_id == 'movimentacoes_periodo':
                dias = st.number_input("Número de dias para análise", min_value=1, max_value=365, value=30)
                parametros['dias'] = dias
            
            if st.button("📊 Gerar Relatório"):
                with st.spinner("Gerando relatório..."):
                    dados_relatorio = manager.gerar_relatorio(template_id, parametros)
                    mostrar_relatorio_dados(dados_relatorio)
    
    with tab2:
        st.header("📝 Criar Template Customizado")
        
        with st.form("template_customizado"):
            nome_template = st.text_input("Nome do Template")
            
            st.write("**Query SQL:**")
            query_customizada = st.text_area(
                "Digite a query SQL",
                height=200,
                placeholder="SELECT * FROM insumos WHERE ativo = TRUE"
            )
            
            colunas_esperadas = st.text_input(
                "Colunas esperadas (separadas por vírgula)",
                placeholder="id,nome,quantidade,preco"
            )
            
            if st.form_submit_button("💾 Criar Template"):
                if nome_template and query_customizada and colunas_esperadas:
                    colunas = [col.strip() for col in colunas_esperadas.split(',')]
                    resultado = manager.criar_template_customizado(nome_template, query_customizada, colunas)
                    
                    if resultado.get('sucesso'):
                        st.success(resultado['mensagem'])
                    else:
                        st.error(resultado['erro'])
                else:
                    st.warning("Preencha todos os campos obrigatórios")
    
    with tab3:
        st.header("📚 Templates Disponíveis")
        
        templates = manager.listar_templates()
        
        for template in templates:
            with st.expander(f"📋 {template['nome']}"):
                st.write(f"**Descrição:** {template['descricao']}")
                st.write(f"**ID:** {template['id']}")
                
                # Botão para gerar relatório rápido
                if st.button(f"🚀 Gerar Agora", key=f"quick_{template['id']}"):
                    dados_relatorio = manager.gerar_relatorio(template['id'])
                    mostrar_relatorio_dados(dados_relatorio)