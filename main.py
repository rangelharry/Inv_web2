"""
Sistema de Inventário Web - Aplicação Principal
Dashboard completo com todas as funcionalidades avançadas
"""

import streamlit as st
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore
from streamlit_option_menu import option_menu  # type: ignore
from typing import Dict, Union

# Tipo para métricas do dashboard
MetricsData = Dict[str, Dict[str, Union[int, float]]]

# Configuração da página
st.set_page_config(
    page_title="Inventário Web",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para melhorar o visual das notificações
st.markdown("""
<style>
    /* Estilo para containers de notificações */
    .notification-container {
        background: rgba(255,255,255,0.05);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #ff6b6b;
    }
    
    .notification-success {
        border-left-color: #51cf66;
    }
    
    .notification-warning {
        border-left-color: #ffd43b;
    }
    
    .notification-info {
        border-left-color: #74c0fc;
    }
    
    /* Melhorar espaçamento das métricas */
    .metric-container {
        background: rgba(255,255,255,0.02);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.25rem 0;
    }
    
    /* Estilo para botões de detalhes */
    .stButton > button {
        width: 100%;
        border-radius: 20px;
        border: none;
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# Importações dos módulos
try:
    from database.connection import db
    from modules.auth import auth_manager
    from modules.equipamentos_eletricos import show_equipamentos_eletricos_page
    from modules.equipamentos_manuais import show_equipamentos_manuais_page
    from modules.movimentacoes import show_movimentacoes_page
    from modules.obras import show_obras_page
    from modules.responsaveis import show_responsaveis_page
    from modules.logs_auditoria import show_logs_auditoria_page
    from modules.relatorios import show_relatorios_page
    from modules.usuarios import show_usuarios_page
    from modules.configuracoes import show_configuracoes_page
    from modules.notifications import notificar_estoque_baixo, notificar_vencimento, notificar_vida_util
except ImportError as e:
    st.error(f"Erro ao importar módulos: {e}")
    st.stop()

# CSS customizado para melhorar a interface
def load_css():
    st.markdown("""
    <style>
    /* Tema principal */
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #3b82f6;
        margin-bottom: 1rem;
    }
    
    .alert-card {
        background: #f87171;
        border: 1px solid #b91c1c;
        color: #1a1a1a;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: 500;
    }
    
    .success-card {
        background: #bbf7d0;
        border: 1px solid #059669;
        color: #1a1a1a;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: 500;
    }
    
    .warning-card {
        background: #fffbeb;
        border: 1px solid #fde68a;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    /* Sidebar customizada */
    .css-1d391kg {
        background: linear-gradient(180deg, #1e3a8a 0%, #3b82f6 100%);
    }
    
    /* Botões customizados */
    .stButton button {
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Tabelas */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Métricas */
    .metric {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Animações */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    </style>
    """, unsafe_allow_html=True)

# Função para verificar autenticação
def check_authentication():
    """Verifica se o usuário está autenticado"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    
    return st.session_state.authenticated

# Página de login
def show_login_page():
    """Exibe página de login"""
    _, col2, _ = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="main-header" style="text-align: center;">
            <h1>📦 Sistema de Inventário Web</h1>
            <p>Faça login para acessar o sistema</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="seu.email@exemplo.com")
            password = st.text_input("🔒 Senha", type="password", placeholder="Sua senha")
            
            if st.form_submit_button("🚀 Entrar", use_container_width=True):
                if email and password:
                    success, message, user_data = auth_manager.authenticate_user(email, password)
                    
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user = user_data  # Salvar dados do usuário na sessão
                        st.session_state.user_data = user_data
                        if user_data and 'id' in user_data:
                            st.session_state.session_token = auth_manager.create_session(user_data['id'])
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.warning("⚠️ Preencha todos os campos!")
        
        # Informações do sistema
        with st.expander("ℹ️ Informações do Sistema"):
            st.info("""
            
            **Funcionalidades:**
            - ✅ Dashboard com métricas em tempo real
            - ✅ Gestão completa de insumos
            - ✅ Controle de equipamentos elétricos e manuais
            - ✅ Sistema de movimentações
            - ✅ Relatórios avançados
            - ✅ Auditoria e logs
            - ✅ Gestão de usuários e permissões
            """)

# Removida função de registro público - apenas administradores podem criar usuários

# Cache para métricas do dashboard
@st.cache_data(ttl=60)  # Cache por 60 segundos
def get_dashboard_metrics() -> MetricsData:
    """Busca métricas do dashboard com cache"""
    conn = db.get_connection()
    # Garantir que a conexão esteja limpa
    if hasattr(conn, 'rollback'):
        conn.rollback()  # type: ignore
    
    cursor = conn.cursor()
    
    metrics: MetricsData = {}
    
    try:
        # Métricas principais em uma query otimizada
        cursor.execute("""
            SELECT 
                'insumos' as tipo,
                COUNT(*) as total,
                SUM(CASE WHEN quantidade_atual <= quantidade_minima THEN 1 ELSE 0 END) as alertas,
                SUM(quantidade_atual * preco_unitario) as valor_total
            FROM insumos WHERE ativo = TRUE
            UNION ALL
            SELECT 
                'equipamentos_eletricos' as tipo,
                COUNT(*) as total,
                0 as alertas,
                SUM(COALESCE(valor_compra, 0)) as valor_total
            FROM equipamentos_eletricos WHERE ativo = TRUE
            UNION ALL
            SELECT 
                'equipamentos_manuais' as tipo,
                COUNT(*) as total,
                0 as alertas,
                SUM(quantitativo * COALESCE(valor, 0)) as valor_total
            FROM equipamentos_manuais WHERE ativo = TRUE
            UNION ALL
            SELECT 
                'obras' as tipo,
                COUNT(*) as total,
                0 as alertas,
                0 as valor_total
            FROM obras WHERE status = 'ativo'
        """)
        
        results = cursor.fetchall()
        for row in results:
            # Tratar resultados do PostgreSQL de forma robusta
            if isinstance(row, dict):
                tipo = row.get('tipo')
                total = row.get('total', 0) 
                alertas = row.get('alertas', 0)
                valor = row.get('valor_total', 0)
            else:
                # Se for tuple, converter usando cursor.description
                columns = [desc[0] for desc in cursor.description]
                row_dict = dict(zip(columns, row))
                tipo = row_dict.get('tipo')
                total = row_dict.get('total', 0)
                alertas = row_dict.get('alertas', 0)
                valor = row_dict.get('valor_total', 0)
                
            if tipo:
                metrics[tipo] = {
                    'total': total or 0,
                    'alertas': alertas or 0,
                    'valor_total': valor or 0
                }
        
        # Movimentações recentes
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN data_movimentacao::date = CURRENT_DATE THEN 1 END) as hoje,
                COUNT(CASE WHEN data_movimentacao >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as semana
            FROM movimentacoes
        """)
        mov_result = cursor.fetchone()
        metrics['movimentacoes'] = {
            'hoje': mov_result['hoje'] if mov_result else 0,
            'semana': mov_result['semana'] if mov_result else 0
        }
        
        return metrics
        
    except Exception as e:
        # Fazer rollback explícito para limpar o estado da transação
        if hasattr(conn, 'rollback'):
            conn.rollback()  # type: ignore
        st.error(f"Erro ao buscar métricas: {e}")
        return {}

# Dashboard principal
def show_dashboard():
    """Exibe dashboard principal com métricas"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 Dashboard - Visão Geral do Inventário</h1>
        <p>Acompanhe as principais métricas do seu inventário em tempo real</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Botão para atualizar cache
    col_refresh, col_auto = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Atualizar", help="Atualizar métricas"):
            st.cache_data.clear()
            st.rerun()
    
    with col_auto:
        st.caption("📊 Métricas atualizadas automaticamente a cada minuto")
    
    # Buscar dados com cache
    with st.spinner("Carregando métricas do dashboard..."):
        metrics = get_dashboard_metrics()
    
    if not metrics:
        st.error("❌ Não foi possível carregar as métricas do dashboard.")
        return
    
    # Extrair dados das métricas
    insumos_count: int = int(metrics.get('insumos', {}).get('total', 0))
    eq_eletricos_count: int = int(metrics.get('equipamentos_eletricos', {}).get('total', 0))
    eq_manuais_count: int = int(metrics.get('equipamentos_manuais', {}).get('total', 0))
    obras_count: int = int(metrics.get('obras', {}).get('total', 0))
    
    valor_insumos: float = float(metrics.get('insumos', {}).get('valor_total', 0))
    valor_eq_eletricos: float = float(metrics.get('equipamentos_eletricos', {}).get('valor_total', 0))
    valor_eq_manuais: float = float(metrics.get('equipamentos_manuais', {}).get('valor_total', 0))
    
    alertas_insumos: int = int(metrics.get('insumos', {}).get('alertas', 0))
    mov_hoje: int = int(metrics.get('movimentacoes', {}).get('hoje', 0))
    mov_semana: int = int(metrics.get('movimentacoes', {}).get('semana', 0))
    
    # Exibir métricas principais
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📦 Insumos", f"{insumos_count:,}", help="Total de insumos ativos")
    with col2:
        st.metric("⚡ Equip. Elétricos", f"{eq_eletricos_count:,}", help="Total de equipamentos elétricos ativos")
    with col3:
        st.metric("🔧 Equip. Manuais", f"{eq_manuais_count:,}", help="Total de equipamentos manuais ativos")
    with col4:
        st.metric("🏢 Obras Ativas", f"{obras_count:,}", help="Total de obras/departamentos ativos")

    # Segunda linha de métricas - Valores
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Valor Insumos", f"R$ {valor_insumos:,.2f}", help="Valor total do estoque de insumos")
    with col2:
        st.metric("💰 Valor Eq. Elétricos", f"R$ {valor_eq_eletricos:,.2f}", help="Valor total dos equipamentos elétricos")
    with col3:
        st.metric("💰 Valor Eq. Manuais", f"R$ {valor_eq_manuais:,.2f}", help="Valor total dos equipamentos manuais")

    # Valor total geral com variação
    valor_total: float = valor_insumos + valor_eq_eletricos + valor_eq_manuais
    st.metric(
        "🏆 VALOR TOTAL DO INVENTÁRIO", 
        f"R$ {valor_total:,.2f}", 
        help="Valor total de todo o inventário"
    )

    # Seção de Notificações com melhor organização
    st.subheader("🚨 Alertas e Notificações")
    
    # Notificações operacionais (estoque baixo, vencimento, vida útil)
    # Buscar dados detalhados dos insumos e equipamentos para notificação
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Função helper para converter resultados PostgreSQL
        def convert_results_to_dict(results, cursor):
            if not results:
                return []
            converted = []
            for row in results:
                if isinstance(row, dict):
                    converted.append(row)
                else:
                    # Se for tuple, converter usando cursor.description
                    columns = [desc[0] for desc in cursor.description]
                    converted.append(dict(zip(columns, row)))
            return converted
        
        # Insumos
        cursor.execute("SELECT descricao as nome, quantidade_atual, quantidade_minima, data_validade FROM insumos WHERE ativo = TRUE")
        insumos = convert_results_to_dict(cursor.fetchall(), cursor)
        
        # Container organizado para notificações
        with st.container():
            # Verificar se há notificações antes de exibir
            notificar_estoque_baixo(insumos, limite=5)
            notificar_vencimento(insumos, dias_aviso=30)
            
            # Se não houver alertas, mostrar mensagem positiva
            if not any(item.get('quantidade_atual', 0) <= 5 for item in insumos):
                if not any(True for item in insumos if item.get('data_validade')):  # Se não há itens com data de validade para verificar
                    st.success("✅ **Nenhum alerta no momento** - Todos os estoques estão em níveis adequados")
        
        # Equipamentos Elétricos
        cursor.execute("SELECT nome, data_compra FROM equipamentos_eletricos WHERE ativo = TRUE")
        eq_eletricos = convert_results_to_dict(cursor.fetchall(), cursor)
        # notificar_vida_util(eq_eletricos, percentual_aviso=0.9)  # Comentado - coluna vida_util_anos não existe
        
        # Equipamentos Manuais
        cursor.execute("SELECT descricao as nome, data_compra FROM equipamentos_manuais WHERE ativo = TRUE")
        eq_manuais = convert_results_to_dict(cursor.fetchall(), cursor)
        # notificar_vida_util(eq_manuais, percentual_aviso=0.9)  # Comentado - coluna vida_util_anos não existe
    except Exception as e:
        st.error(f"❌ Erro ao carregar notificações: {e}")

    # Atividade recente
    st.subheader("📈 Atividade Recente")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Hoje", f"{mov_hoje}", help="Movimentações realizadas hoje")
    with col2:
        st.metric("📊 Esta Semana", f"{mov_semana}", help="Movimentações dos últimos 7 dias")
    with col3:
        # Calcular média diária da semana
        media_diaria: float = mov_semana / 7 if mov_semana > 0 else 0
        st.metric("📊 Média Diária", f"{media_diaria:.1f}", help="Média de movimentações por dia na semana")

# Sidebar com menu de navegação
def show_sidebar():
    """Exibe sidebar com menu de navegação"""
    with st.sidebar:
        # Informações do usuário
        if st.session_state.authenticated:
            user_data = st.session_state.user_data
            
            st.markdown(f"""
            <div style="padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 10px; margin-bottom: 1rem;">
                <h4 style="color: white; margin: 0;">👤 {user_data['nome']}</h4>
                <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.9rem;">
                    {user_data['perfil'].title()} | {user_data['email']}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Menu principal
        selected = option_menu(
            menu_title="📦 Inventário Web",
            options=[
                "Dashboard",
                "Insumos", 
                "Equipamentos Elétricos",
                "Equipamentos Manuais",
                "Movimentações",
                "Obras/Departamentos",
                "Responsáveis",
                "Relatórios",
                "Logs de Auditoria",
                "Usuários",
                "Configurações",
                "QR/Códigos de Barras",
                "Reservas",
                "Manutenção Preventiva",
                "Dashboard Executivo",
                "Localização",
                "Gestão Financeira",
                "Análise Preditiva",
                "Gestão de Subcontratados",
                "Relatórios Customizáveis",
                "Métricas Performance",
                "Backup e Recovery",
                "LGPD/Compliance",
                "Orçamentos e Cotações",
                "Sistema de Faturamento",
                "Integração ERP/SAP"
            ],
            icons=[
                "speedometer2",
                "box-seam", 
                "lightning-charge",
                "tools",
                "arrow-left-right",
                "building",
                "people",
                "graph-up",
                "journal-text",
                "person-gear",
                "gear",
                "qr-code",
                "calendar-check",
                "wrench-adjustable",
                "bar-chart",
                "geo-alt",
                "calculator",
                "robot",
                "file-earmark-text",
                "speedometer",
                "shield-check",
                "shield-lock",
                "currency-exchange",
                "receipt",
                "diagram-3"
            ],
            menu_icon="boxes",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "white", "font-size": "16px"}, 
                "nav-link": {
                    "font-size": "14px", 
                    "text-align": "left", 
                    "margin":"0px", 
                    "color": "white",
                    "--hover-color": "rgba(255,255,255,0.1)"
                },
                "nav-link-selected": {"background-color": "rgba(255,255,255,0.2)"},
            }
        )
        
        st.markdown("---")
        
        # Botão de logout
        if st.button("🚪 Sair do Sistema", width='stretch'):
            if 'session_token' in st.session_state:
                auth_manager.logout_user(token=st.session_state.session_token)
            
            # Limpar session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            st.rerun()
        
        return selected

# Função principal
def main():
    """Função principal da aplicação"""
    # Carregar CSS
    load_css()
    
    # Verificar autenticação - apenas página de login
    if not check_authentication():
        show_login_page()
        return
    
    # Usuário autenticado - mostrar aplicação
    selected_page = show_sidebar()
    
    # Roteamento de páginas
    if selected_page == "Dashboard":
        show_dashboard()
    elif selected_page == "Insumos":
        from modules.insumos import show_insumos_page
        show_insumos_page()
    elif selected_page == "Equipamentos Elétricos":
        show_equipamentos_eletricos_page()
    elif selected_page == "Equipamentos Manuais":
        show_equipamentos_manuais_page()
    elif selected_page == "Movimentações":
        show_movimentacoes_page()
    elif selected_page == "Obras/Departamentos":
        show_obras_page()
    elif selected_page == "Responsáveis":
        show_responsaveis_page()
    elif selected_page == "Relatórios":
        show_relatorios_page()
    elif selected_page == "Logs de Auditoria":
        show_logs_auditoria_page()
    elif selected_page == "Usuários":
        show_usuarios_page()
    elif selected_page == "Configurações":
        show_configuracoes_page()
    elif selected_page == "QR/Códigos de Barras":
        from modules.barcode_utils import show_barcode_page
        show_barcode_page()
    elif selected_page == "Reservas":
        from modules.reservas import show_reservas_page
        show_reservas_page()
    elif selected_page == "Manutenção Preventiva":
        from modules.manutencao_preventiva import show_manutencao_page
        show_manutencao_page()
    elif selected_page == "Dashboard Executivo":
        from modules.dashboard_executivo import show_dashboard_executivo_page
        show_dashboard_executivo_page()
    elif selected_page == "Localização":
        from modules.controle_localizacao import show_localizacao_page
        show_localizacao_page()
    elif selected_page == "Gestão Financeira":
        from modules.gestao_financeira import show_gestao_financeira_page
        show_gestao_financeira_page()
    elif selected_page == "Análise Preditiva":
        from modules.analise_preditiva import show_analise_preditiva_page
        show_analise_preditiva_page()
    elif selected_page == "Gestão de Subcontratados":
        from modules.gestao_subcontratados import show_subcontratados_page
        show_subcontratados_page()
    elif selected_page == "Relatórios Customizáveis":
        from modules.relatorios_customizaveis import show_relatorios_customizaveis_page
        show_relatorios_customizaveis_page()
    elif selected_page == "Métricas Performance":
        from modules.metricas_performance import show_metricas_performance_page
        show_metricas_performance_page()
    elif selected_page == "Backup e Recovery":
        from modules.backup_recovery import show_backup_recovery_page
        show_backup_recovery_page()
    elif selected_page == "LGPD/Compliance":
        from modules.lgpd_compliance import show_lgpd_compliance_page
        show_lgpd_compliance_page()
    elif selected_page == "Orçamentos e Cotações":
        from modules.orcamentos_cotacoes import show_orcamentos_cotacoes_page
        show_orcamentos_cotacoes_page()
    elif selected_page == "Sistema de Faturamento":
        from modules.sistema_faturamento import show_faturamento_page
        show_faturamento_page()
    elif selected_page == "Integração ERP/SAP":
        from modules.integracao_erp import show_erp_integration_page
        show_erp_integration_page()

if __name__ == "__main__":
    main()