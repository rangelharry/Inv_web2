"""
Sistema de Inventário Web - Aplicação Principal
Dashboard completo com todas as funcionalidades avançadas
"""

import streamlit as st
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore
from streamlit_option_menu import option_menu  # type: ignore

# Configuração da página
st.set_page_config(
    page_title="Inventário Web",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Dashboard principal
def show_dashboard():
    """Exibe dashboard principal com métricas"""
    st.markdown("""
    <div class="main-header">
        <h1>📊 Dashboard - Visão Geral do Inventário</h1>
        <p>Acompanhe as principais métricas do seu inventário em tempo real</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Buscar dados para métricas
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Métricas principais
        cursor.execute("SELECT COUNT(*) as total FROM insumos WHERE ativo = 1")
        insumos_count = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) as total FROM equipamentos_eletricos WHERE ativo = 1")
        eq_eletricos_count = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) as total FROM equipamentos_manuais WHERE ativo = 1")
        eq_manuais_count = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) as total FROM obras WHERE status = 'ativo'")
        obras_count = cursor.fetchone()[0] or 0
        
        # Valores totais
        cursor.execute("SELECT SUM(quantidade_atual * preco_unitario) as valor FROM insumos WHERE ativo = 1 AND preco_unitario IS NOT NULL")
        valor_insumos = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(valor_compra) as valor FROM equipamentos_eletricos WHERE ativo = 1 AND valor_compra IS NOT NULL")
        valor_eq_eletricos = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(quantitativo * valor) as valor FROM equipamentos_manuais WHERE ativo = 1 AND valor IS NOT NULL")
        valor_eq_manuais = cursor.fetchone()[0] or 0
        
        # Exibir métricas
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
        
        # Valor total geral
        valor_total = valor_insumos + valor_eq_eletricos + valor_eq_manuais
        st.metric("🏆 VALOR TOTAL DO INVENTÁRIO", f"R$ {valor_total:,.2f}", help="Valor total de todo o inventário")
        
        # Alertas de estoque baixo
        cursor.execute("""
            SELECT COUNT(*) FROM insumos 
            WHERE ativo = 1 AND quantidade_atual <= quantidade_minima
        """)
        alertas_insumos = cursor.fetchone()[0] or 0
        
        if alertas_insumos > 0:
            st.warning(f"⚠️ {alertas_insumos} insumo(s) com estoque baixo!")
        
        # Atividade recente
        st.subheader("📈 Atividade Recente")
        cursor.execute("""
            SELECT COUNT(*) as movimentacoes_hoje 
            FROM movimentacoes 
            WHERE DATE(data_movimentacao) = DATE('now')
        """)
        mov_hoje = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) as movimentacoes_semana 
            FROM movimentacoes 
            WHERE DATE(data_movimentacao) >= DATE('now', '-7 days')
        """)
        mov_semana = cursor.fetchone()[0] or 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📊 **{mov_hoje}** movimentações hoje")
        with col2:
            st.info(f"📊 **{mov_semana}** movimentações esta semana")
            
    except Exception as e:
        st.error(f"Erro ao carregar dashboard: {e}")
        import traceback
        st.error(f"Detalhes do erro: {traceback.format_exc()}")

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
                "Configurações"
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
                "gear"
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

if __name__ == "__main__":
    main()