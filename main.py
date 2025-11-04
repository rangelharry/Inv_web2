"""
Sistema de Inventário Web - Aplicação Principal
Dashboard completo com todas as funcionalidades avançadas
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import json
from streamlit_option_menu import option_menu

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
        background: #fef2f2;
        border: 1px solid #fecaca;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .success-card {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
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
    col1, col2, col3 = st.columns([1, 2, 1])
    
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
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.form_submit_button("🚀 Entrar", use_container_width=True):
                    if email and password:
                        success, message, user_data = auth_manager.authenticate_user(email, password)
                        
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.user_data = user_data
                            st.session_state.session_token = auth_manager.create_session(user_data['id'])
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.warning("⚠️ Preencha todos os campos!")
            
            with col_btn2:
                if st.form_submit_button("👤 Primeiro Acesso", use_container_width=True):
                    st.session_state.show_register = True
                    st.rerun()
        
        # Informações do sistema
        with st.expander("ℹ️ Informações do Sistema"):
            st.info("""
            **Credenciais Padrão:**
            - **Email:** admin@inventario.com
            - **Senha:** admin123
            
            **Funcionalidades:**
            - ✅ Dashboard com métricas em tempo real
            - ✅ Gestão completa de insumos
            - ✅ Controle de equipamentos elétricos e manuais
            - ✅ Sistema de movimentações
            - ✅ Relatórios avançados
            - ✅ Auditoria e logs
            - ✅ Gestão de usuários e permissões
            """)

# Página de registro (primeiro acesso)
def show_register_page():
    """Exibe página de registro para primeiro acesso"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="main-header" style="text-align: center;">
            <h1>👤 Primeiro Acesso</h1>
            <p>Crie sua conta no sistema</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("register_form"):
            nome = st.text_input("👤 Nome Completo", placeholder="Seu nome completo")
            email = st.text_input("📧 Email", placeholder="seu.email@exemplo.com")
            password = st.text_input("🔒 Senha", type="password", placeholder="Mínimo 6 caracteres")
            confirm_password = st.text_input("🔒 Confirmar Senha", type="password", placeholder="Digite a senha novamente")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.form_submit_button("✅ Criar Conta", use_container_width=True):
                    if nome and email and password and confirm_password:
                        if password != confirm_password:
                            st.error("❌ As senhas não coincidem!")
                        else:
                            success, message = auth_manager.create_user(nome, email, password, 'usuario')
                            
                            if success:
                                st.success(f"✅ {message}")
                                st.info("👍 Agora você pode fazer login com suas credenciais!")
                                st.session_state.show_register = False
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                    else:
                        st.warning("⚠️ Preencha todos os campos!")
            
            with col_btn2:
                if st.form_submit_button("⬅️ Voltar ao Login", use_container_width=True):
                    st.session_state.show_register = False
                    st.rerun()

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
        total_insumos = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM itens_inventario WHERE tipo_item = 'Equipamento Elétrico'")
        total_eq_eletricos = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM itens_inventario WHERE tipo_item = 'Equipamento Manual'")
        total_eq_manuais = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM obras WHERE status = 'ativo'")
        total_obras = cursor.fetchone()['total']
        
        cursor.execute("SELECT SUM(quantidade_atual * preco_unitario) as valor FROM insumos WHERE ativo = 1 AND preco_unitario IS NOT NULL")
        valor_total_insumos = cursor.fetchone()['valor'] or 0
        
        cursor.execute("SELECT SUM(quantidade_atual * valor_unitario) as valor FROM itens_inventario WHERE tipo_item = 'Equipamento Elétrico' AND valor_unitario IS NOT NULL")
        valor_eq_eletricos = cursor.fetchone()['valor'] or 0
        
        cursor.execute("SELECT SUM(quantidade_atual * valor_unitario) as valor FROM itens_inventario WHERE tipo_item = 'Equipamento Manual' AND valor_unitario IS NOT NULL")
        valor_eq_manuais = cursor.fetchone()['valor'] or 0
        
        valor_total_patrimonio = valor_total_insumos + valor_eq_eletricos + valor_eq_manuais
        
        # Cards de métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📦 Total de Insumos",
                value=f"{total_insumos:,}".replace(',', '.'),
                delta="Itens ativos"
            )
        
        with col2:
            st.metric(
                label="⚡ Equipamentos Elétricos",
                value=f"{total_eq_eletricos:,}".replace(',', '.'),
                delta="Unidades"
            )
        
        with col3:
            st.metric(
                label="🔧 Equipamentos Manuais",
                value=f"{total_eq_manuais:,}".replace(',', '.'),
                delta="Unidades"
            )
        
        with col4:
            st.metric(
                label="🏗️ Obras Ativas",
                value=f"{total_obras:,}".replace(',', '.'),
                delta="Projetos"
            )
        
        # Segunda linha de métricas
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric(
                label="💰 Valor Total Patrimônio",
                value=f"R$ {valor_total_patrimonio:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                delta="Estimativa"
            )
        
        with col6:
            cursor.execute("SELECT COUNT(*) as total FROM insumos WHERE quantidade_atual <= quantidade_minima AND ativo = 1")
            alertas_estoque = cursor.fetchone()['total']
            st.metric(
                label="⚠️ Alertas de Estoque",
                value=f"{alertas_estoque}",
                delta="Itens abaixo do mínimo",
                delta_color="inverse"
            )
        
        with col7:
            cursor.execute("SELECT COUNT(*) as total FROM equipamentos_eletricos WHERE status = 'Manutenção'")
            eq_manutencao = cursor.fetchone()['total']
            st.metric(
                label="🔧 Em Manutenção",
                value=f"{eq_manutencao}",
                delta="Equipamentos",
                delta_color="inverse"
            )
        
        with col8:
            cursor.execute("SELECT COUNT(*) as total FROM movimentacoes WHERE DATE(data_movimentacao) = DATE('now')")
            movimentacoes_hoje = cursor.fetchone()['total']
            st.metric(
                label="📋 Movimentações Hoje",
                value=f"{movimentacoes_hoje}",
                delta="Registros"
            )
        
        st.markdown("---")
        
        # Gráficos
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("📊 Distribuição do Inventário")
            
            # Gráfico de pizza
            labels = ['Insumos', 'Eq. Elétricos', 'Eq. Manuais']
            values = [total_insumos, total_eq_eletricos, total_eq_manuais]
            colors = ['#3b82f6', '#10b981', '#f59e0b']
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker_colors=colors
            )])
            
            fig_pie.update_layout(
                showlegend=True,
                height=400,
                margin=dict(t=50, b=50, l=50, r=50)
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_chart2:
            st.subheader("💰 Valor por Categoria")
            
            # Gráfico de barras
            categorias = ['Insumos', 'Eq. Elétricos', 'Eq. Manuais']
            valores = [valor_total_insumos, valor_eq_eletricos, valor_eq_manuais]
            
            fig_bar = go.Figure(data=[go.Bar(
                x=categorias,
                y=valores,
                marker_color=['#3b82f6', '#10b981', '#f59e0b'],
                text=[f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') for v in valores],
                textposition='auto',
            )])
            
            fig_bar.update_layout(
                title="Valor Estimado do Patrimônio por Categoria",
                xaxis_title="Categorias",
                yaxis_title="Valor (R$)",
                height=400,
                margin=dict(t=50, b=50, l=50, r=50)
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Alertas e notificações
        st.markdown("---")
        
        col_alert1, col_alert2 = st.columns(2)
        
        with col_alert1:
            st.subheader("🚨 Alertas de Estoque Baixo")
            
            cursor.execute("""
            SELECT codigo, descricao, quantidade_atual, quantidade_minima, unidade
            FROM insumos 
            WHERE quantidade_atual <= quantidade_minima AND ativo = 1
            ORDER BY (quantidade_atual/quantidade_minima) ASC
            LIMIT 5
            """)
            
            alertas_estoque_detalhes = cursor.fetchall()
            
            if alertas_estoque_detalhes:
                for alerta in alertas_estoque_detalhes:
                    with st.container():
                        st.markdown(f"""
                        <div class="alert-card">
                            <strong>📦 {alerta['codigo']}</strong><br>
                            {alerta['descricao']}<br>
                            <small>Atual: {alerta['quantidade_atual']} {alerta['unidade']} | 
                            Mínimo: {alerta['quantidade_minima']} {alerta['unidade']}</small>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.success("✅ Todos os estoques estão adequados!")
        
        with col_alert2:
            st.subheader("⚡ Status dos Equipamentos")
            
            cursor.execute("""
            SELECT status, COUNT(*) as quantidade 
            FROM equipamentos_eletricos 
            WHERE ativo = 1 
            GROUP BY status
            """)
            
            status_equipamentos = cursor.fetchall()
            
            for status in status_equipamentos:
                color_class = {
                    'Disponível': 'success-card',
                    'Em uso': 'warning-card',
                    'Manutenção': 'alert-card',
                    'Inativo': 'alert-card',
                    'Danificado': 'alert-card'
                }.get(status['status'], 'success-card')
                
                st.markdown(f"""
                <div class="{color_class}">
                    <strong>⚡ {status['status']}</strong><br>
                    {status['quantidade']} equipamentos
                </div>
                """, unsafe_allow_html=True)
        
        # Últimas movimentações
        st.markdown("---")
        st.subheader("📋 Últimas Movimentações")
        
        cursor.execute("""
        SELECT tipo, tipo_item, codigo_item, descricao_item, quantidade, unidade, 
               data_movimentacao, usuario_id
        FROM movimentacoes 
        ORDER BY data_movimentacao DESC 
        LIMIT 10
        """)
        
        movimentacoes_recentes = cursor.fetchall()
        
        if movimentacoes_recentes:
            df_movimentacoes = pd.DataFrame([dict(mov) for mov in movimentacoes_recentes])
            
            # Formatar dados para exibição
            df_movimentacoes['Data/Hora'] = pd.to_datetime(df_movimentacoes['data_movimentacao']).dt.strftime('%d/%m/%Y %H:%M')
            df_movimentacoes['Tipo'] = df_movimentacoes['tipo'].str.title()
            df_movimentacoes['Item'] = df_movimentacoes['tipo_item'].str.replace('_', ' ').str.title()
            df_movimentacoes['Código'] = df_movimentacoes['codigo_item']
            df_movimentacoes['Descrição'] = df_movimentacoes['descricao_item']
            df_movimentacoes['Qtd'] = df_movimentacoes['quantidade'].astype(str) + ' ' + df_movimentacoes['unidade'].fillna('')
            
            # Exibir tabela
            st.dataframe(
                df_movimentacoes[['Data/Hora', 'Tipo', 'Item', 'Código', 'Descrição', 'Qtd']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("📝 Nenhuma movimentação registrada ainda.")
    
    except Exception as e:
        st.error(f"Erro ao carregar dashboard: {e}")

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
        if st.button("🚪 Sair do Sistema", use_container_width=True):
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
    
    # Verificar se deve mostrar página de registro
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
    
    # Verificar autenticação
    if not check_authentication():
        if st.session_state.show_register:
            show_register_page()
        else:
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
        st.title("👥 Gestão de Usuários")
        st.info("🚧 Módulo em desenvolvimento - será implementado na próxima etapa!")
    elif selected_page == "Configurações":
        st.title("⚙️ Configurações do Sistema")
        st.info("🚧 Módulo em desenvolvimento - será implementado na próxima etapa!")

if __name__ == "__main__":
    main()