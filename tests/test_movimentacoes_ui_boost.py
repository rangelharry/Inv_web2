"""
Testes específicos para aumentar cobertura para 80%
Foco nas linhas de UI 202-370 que não estão sendo cobertas
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import pandas as pd
import sys
import os
from datetime import date

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_ui_historico_com_dataframe_completo():
    """Teste específico para cobrir exibição de dataframe com dados"""
    with patch('modules.movimentacoes.st') as mock_st, \
         patch('modules.movimentacoes.auth_manager') as mock_auth, \
         patch('modules.movimentacoes.MovimentacoesManager') as mock_manager_class:
        
        # Setup básico
        mock_st.session_state.user_data = {'perfil': 'admin', 'id': 1}
        mock_auth.check_permission.return_value = True
        
        # DataFrame com dados para forçar o caminho "not df.empty"
        mock_df = pd.DataFrame([{
            'data_movimentacao': '2024-01-15 10:30:00',
            'tipo': 'Entrada',
            'item_nome': 'Cimento Portland',
            'quantidade': 100,
            'obra_origem': 'Fornecedor ABC',
            'obra_destino': 'Obra Central',
            'motivo': 'Compra mensal',
            'usuario_nome': 'João Silva'
        }])
        
        mock_manager = Mock()
        mock_manager.get_movimentacoes.return_value = mock_df
        mock_manager.get_dashboard_stats.return_value = {'total_mes': 1, 'entradas_mes': 1, 'saidas_mes': 0}
        mock_manager_class.return_value = mock_manager
        
        # Mock das tabs
        mock_tab1 = MagicMock()
        mock_tab2 = MagicMock()
        mock_tab3 = MagicMock()
        mock_st.tabs.return_value = (mock_tab1, mock_tab2, mock_tab3)
        
        # Mock dos filtros (vazios para forçar busca sem filtros)
        mock_st.text_input.return_value = ""
        mock_st.selectbox.return_value = "Todos"
        mock_st.date_input.return_value = None
        mock_st.columns.return_value = [Mock(), Mock(), Mock()]
        mock_st.expander.return_value.__enter__ = Mock()
        mock_st.expander.return_value.__exit__ = Mock()
        
        # Executar função
        from modules.movimentacoes import show_movimentacoes_page
        show_movimentacoes_page()
        
        # Verificar que dataframe foi chamado (linha 226-244)
        mock_st.dataframe.assert_called()
        # Verificar que busca foi feita
        mock_manager.get_movimentacoes.assert_called()


def test_ui_historico_sem_dados():
    """Teste para cobrir mensagem quando DataFrame está vazio"""
    with patch('modules.movimentacoes.st') as mock_st, \
         patch('modules.movimentacoes.auth_manager') as mock_auth, \
         patch('modules.movimentacoes.MovimentacoesManager') as mock_manager_class:
        
        # Setup básico
        mock_st.session_state.user_data = {'perfil': 'admin', 'id': 1}
        mock_auth.check_permission.return_value = True
        
        # DataFrame VAZIO para forçar o else na linha 246
        mock_df = pd.DataFrame()
        
        mock_manager = Mock()
        mock_manager.get_movimentacoes.return_value = mock_df
        mock_manager.get_dashboard_stats.return_value = {'total_mes': 0, 'entradas_mes': 0, 'saidas_mes': 0}
        mock_manager_class.return_value = mock_manager
        
        # Mock das tabs
        mock_tab1 = MagicMock()
        mock_tab2 = MagicMock()
        mock_tab3 = MagicMock()
        mock_st.tabs.return_value = (mock_tab1, mock_tab2, mock_tab3)
        
        # Mock dos componentes
        mock_st.text_input.return_value = ""
        mock_st.selectbox.return_value = "Todos"
        mock_st.date_input.return_value = None
        mock_st.columns.return_value = [Mock(), Mock(), Mock()]
        mock_st.expander.return_value.__enter__ = Mock()
        mock_st.expander.return_value.__exit__ = Mock()
        
        # Executar função
        from modules.movimentacoes import show_movimentacoes_page
        show_movimentacoes_page()
        
        # Verificar que a mensagem de "nenhuma movimentação encontrada" foi exibida (linha 246)
        mock_st.info.assert_called_with("📭 Nenhuma movimentação encontrada com os filtros aplicados.")


def test_ui_nova_movimentacao_insumos_com_dados():
    """Teste para cobrir o caminho de insumos com dados (linhas 258-274)"""
    with patch('modules.movimentacoes.st') as mock_st, \
         patch('modules.movimentacoes.auth_manager') as mock_auth, \
         patch('modules.movimentacoes.MovimentacoesManager') as mock_mov_manager, \
         patch('modules.insumos.InsumosManager') as mock_insumos_manager_class, \
         patch('modules.movimentacao_modal.show_movimentacao_modal_insumo') as mock_modal:
        
        # Setup básico
        mock_st.session_state.user_data = {'perfil': 'admin', 'id': 1}
        mock_auth.check_permission.return_value = True
        
        # Manager principal
        mock_manager = Mock()
        mock_manager.get_movimentacoes.return_value = pd.DataFrame()
        mock_manager.get_dashboard_stats.return_value = {'total_mes': 0, 'entradas_mes': 0, 'saidas_mes': 0}
        mock_mov_manager.return_value = mock_manager
        
        # Insumos COM DADOS
        mock_insumos = [
            {
                'id': 1,
                'descricao': 'Cimento Portland CP-II',
                'codigo': 'CIM001',
                'quantidade_atual': 500,
                'unidade': 'kg'
            },
            {
                'id': 2,
                'descricao': 'Areia Média',
                'codigo': 'ARE001', 
                'quantidade_atual': 10,
                'unidade': 'm³'
            }
        ]
        
        mock_insumos_mgr = Mock()
        mock_insumos_mgr.get_insumos.return_value = mock_insumos
        mock_insumos_manager_class.return_value = mock_insumos_mgr
        
        # Mock das tabs
        mock_tab1 = MagicMock()
        mock_tab2 = MagicMock()
        mock_tab3 = MagicMock()
        mock_st.tabs.return_value = (mock_tab1, mock_tab2, mock_tab3)
        
        # Configurar para entrar no caminho "Insumos"
        mock_st.selectbox.side_effect = lambda label, options, **kwargs: {
            "Tipo": "Todos",
            "Movimentação de:": "Insumos"
        }.get(label, options[0] if options else "")
        
        mock_st.text_input.return_value = ""
        mock_st.date_input.return_value = None
        mock_st.columns.return_value = [Mock(), Mock(), Mock(), Mock()]
        mock_st.expander.return_value.__enter__ = Mock()
        mock_st.expander.return_value.__exit__ = Mock()
        
        # Mock para simular clique no botão
        mock_st.button.return_value = True  # Simular clique
        
        # Executar função
        from modules.movimentacoes import show_movimentacoes_page
        show_movimentacoes_page()
        
        # Verificar que os insumos foram buscados
        mock_insumos_mgr.get_insumos.assert_called()
        # Verificar que o modal foi chamado
        mock_modal.assert_called()


def test_ui_nova_movimentacao_insumos_sem_dados():
    """Teste para cobrir warning quando não há insumos (linha 275)"""
    with patch('modules.movimentacoes.st') as mock_st, \
         patch('modules.movimentacoes.auth_manager') as mock_auth, \
         patch('modules.movimentacoes.MovimentacoesManager') as mock_mov_manager, \
         patch('modules.insumos.InsumosManager') as mock_insumos_manager_class:
        
        # Setup básico
        mock_st.session_state.user_data = {'perfil': 'admin', 'id': 1}
        mock_auth.check_permission.return_value = True
        
        # Manager principal
        mock_manager = Mock()
        mock_manager.get_movimentacoes.return_value = pd.DataFrame()
        mock_manager.get_dashboard_stats.return_value = {'total_mes': 0, 'entradas_mes': 0, 'saidas_mes': 0}
        mock_mov_manager.return_value = mock_manager
        
        # Insumos SEM DADOS (lista vazia)
        mock_insumos_mgr = Mock()
        mock_insumos_mgr.get_insumos.return_value = []  # Lista vazia!
        mock_insumos_manager_class.return_value = mock_insumos_mgr
        
        # Mock das tabs
        mock_tab1 = MagicMock()
        mock_tab2 = MagicMock()
        mock_tab3 = MagicMock()
        mock_st.tabs.return_value = (mock_tab1, mock_tab2, mock_tab3)
        
        # Configurar para entrar no caminho "Insumos"
        mock_st.selectbox.side_effect = lambda label, options, **kwargs: {
            "Tipo": "Todos",
            "Movimentação de:": "Insumos"
        }.get(label, options[0] if options else "")
        
        mock_st.text_input.return_value = ""
        mock_st.date_input.return_value = None
        mock_st.columns.return_value = [Mock(), Mock(), Mock(), Mock()]
        mock_st.expander.return_value.__enter__ = Mock()
        mock_st.expander.return_value.__exit__ = Mock()
        
        # Executar função
        from modules.movimentacoes import show_movimentacoes_page
        show_movimentacoes_page()
        
        # Verificar que o warning foi exibido (linha 275)
        mock_st.warning.assert_called_with("⚠️ Nenhum insumo cadastrado.")


def test_ui_equipamentos_eletricos_com_dados():
    """Teste para cobrir equipamentos elétricos com dados (linhas 277-293)"""
    with patch('modules.movimentacoes.st') as mock_st, \
         patch('modules.movimentacoes.auth_manager') as mock_auth, \
         patch('modules.movimentacoes.MovimentacoesManager') as mock_mov_manager, \
         patch('modules.equipamentos_eletricos.EquipamentosEletricosManager') as mock_eq_manager_class, \
         patch('modules.movimentacao_modal.show_movimentacao_modal_equipamento_eletrico') as mock_modal:
        
        # Setup básico  
        mock_st.session_state.user_data = {'perfil': 'admin', 'id': 1}
        mock_auth.check_permission.return_value = True
        
        # Manager principal
        mock_manager = Mock()
        mock_manager.get_movimentacoes.return_value = pd.DataFrame()
        mock_manager.get_dashboard_stats.return_value = {'total_mes': 0, 'entradas_mes': 0, 'saidas_mes': 0}
        mock_mov_manager.return_value = mock_manager
        
        # Equipamentos COM DADOS
        mock_equipamentos = pd.DataFrame([
            {
                'id': 1,
                'nome': 'Multimetro Digital FLUKE',
                'codigo': 'MUL001',
                'localizacao': 'Almoxarifado Central',
                'status': 'Disponível'
            },
            {
                'id': 2,
                'nome': 'Furadeira de Impacto',
                'codigo': 'FUR001',
                'localizacao': 'Obra Norte',
                'status': 'Em uso'
            }
        ])
        
        mock_eq_mgr = Mock()
        mock_eq_mgr.get_equipamentos.return_value = mock_equipamentos
        mock_eq_manager_class.return_value = mock_eq_mgr
        
        # Mock das tabs
        mock_tab1 = MagicMock()
        mock_tab2 = MagicMock()
        mock_tab3 = MagicMock()
        mock_st.tabs.return_value = (mock_tab1, mock_tab2, mock_tab3)
        
        # Configurar para entrar no caminho "Equipamentos Elétricos"
        mock_st.selectbox.side_effect = lambda label, options, **kwargs: {
            "Tipo": "Todos", 
            "Movimentação de:": "Equipamentos Elétricos"
        }.get(label, options[0] if options else "")
        
        mock_st.text_input.return_value = ""
        mock_st.date_input.return_value = None
        mock_st.columns.return_value = [Mock(), Mock(), Mock(), Mock(), Mock()]  # 5 colunas para equipamentos elétricos
        mock_st.expander.return_value.__enter__ = Mock()
        mock_st.expander.return_value.__exit__ = Mock()
        mock_st.button.return_value = True  # Simular clique
        
        # Executar função
        from modules.movimentacoes import show_movimentacoes_page
        show_movimentacoes_page()
        
        # Verificar que os equipamentos foram buscados
        mock_eq_mgr.get_equipamentos.assert_called()
        # Verificar que o modal foi chamado
        mock_modal.assert_called()


def test_ui_equipamentos_eletricos_sem_dados():
    """Teste para cobrir warning quando não há equipamentos elétricos (linha 294)"""
    with patch('modules.movimentacoes.st') as mock_st, \
         patch('modules.movimentacoes.auth_manager') as mock_auth, \
         patch('modules.movimentacoes.MovimentacoesManager') as mock_mov_manager, \
         patch('modules.equipamentos_eletricos.EquipamentosEletricosManager') as mock_eq_manager_class:
        
        # Setup básico
        mock_st.session_state.user_data = {'perfil': 'admin', 'id': 1}
        mock_auth.check_permission.return_value = True
        
        # Manager principal
        mock_manager = Mock()
        mock_manager.get_movimentacoes.return_value = pd.DataFrame()
        mock_manager.get_dashboard_stats.return_value = {'total_mes': 0, 'entradas_mes': 0, 'saidas_mes': 0}
        mock_mov_manager.return_value = mock_manager
        
        # Equipamentos SEM DADOS (DataFrame vazio)
        mock_eq_mgr = Mock()
        mock_eq_mgr.get_equipamentos.return_value = pd.DataFrame()  # DataFrame vazio!
        mock_eq_manager_class.return_value = mock_eq_mgr
        
        # Mock das tabs
        mock_tab1 = MagicMock()
        mock_tab2 = MagicMock()
        mock_tab3 = MagicMock()
        mock_st.tabs.return_value = (mock_tab1, mock_tab2, mock_tab3)
        
        # Configurar para entrar no caminho "Equipamentos Elétricos"
        mock_st.selectbox.side_effect = lambda label, options, **kwargs: {
            "Tipo": "Todos",
            "Movimentação de:": "Equipamentos Elétricos"
        }.get(label, options[0] if options else "")
        
        mock_st.text_input.return_value = ""
        mock_st.date_input.return_value = None
        mock_st.columns.return_value = [Mock(), Mock(), Mock(), Mock(), Mock()]
        mock_st.expander.return_value.__enter__ = Mock()
        mock_st.expander.return_value.__exit__ = Mock()
        
        # Executar função
        from modules.movimentacoes import show_movimentacoes_page
        show_movimentacoes_page()
        
        # Verificar que o warning foi exibido (linha 294)
        mock_st.warning.assert_called_with("⚠️ Nenhum equipamento elétrico cadastrado.")


def test_ui_equipamentos_manuais_com_dados():
    """Teste para cobrir equipamentos manuais com dados (linhas 296-312)"""
    with patch('modules.movimentacoes.st') as mock_st, \
         patch('modules.movimentacoes.auth_manager') as mock_auth, \
         patch('modules.movimentacoes.MovimentacoesManager') as mock_mov_manager, \
         patch('modules.equipamentos_manuais.EquipamentosManuaisManager') as mock_eq_manager_class, \
         patch('modules.movimentacao_modal.show_movimentacao_modal_equipamento_manual') as mock_modal:
        
        # Setup básico
        mock_st.session_state.user_data = {'perfil': 'admin', 'id': 1}
        mock_auth.check_permission.return_value = True
        
        # Manager principal
        mock_manager = Mock()
        mock_manager.get_movimentacoes.return_value = pd.DataFrame()
        mock_manager.get_dashboard_stats.return_value = {'total_mes': 0, 'entradas_mes': 0, 'saidas_mes': 0}
        mock_mov_manager.return_value = mock_manager
        
        # Equipamentos manuais COM DADOS
        mock_equipamentos = pd.DataFrame([
            {
                'id': 1,
                'nome': 'Martelo de Unha 25oz',
                'codigo': 'MAR001',
                'localizacao': 'Obra Sul',
                'status': 'Em uso'
            }
        ])
        
        mock_eq_mgr = Mock()
        mock_eq_mgr.get_equipamentos.return_value = mock_equipamentos
        mock_eq_manager_class.return_value = mock_eq_mgr
        
        # Mock das tabs
        mock_tab1 = MagicMock()
        mock_tab2 = MagicMock()
        mock_tab3 = MagicMock()
        mock_st.tabs.return_value = (mock_tab1, mock_tab2, mock_tab3)
        
        # Configurar para entrar no caminho "Equipamentos Manuais"
        mock_st.selectbox.side_effect = lambda label, options, **kwargs: {
            "Tipo": "Todos",
            "Movimentação de:": "Equipamentos Manuais"
        }.get(label, options[0] if options else "")
        
        mock_st.text_input.return_value = ""
        mock_st.date_input.return_value = None
        mock_st.columns.return_value = [Mock(), Mock(), Mock(), Mock(), Mock()]  # 5 colunas
        mock_st.expander.return_value.__enter__ = Mock()
        mock_st.expander.return_value.__exit__ = Mock()
        mock_st.button.return_value = True  # Simular clique
        
        # Executar função
        from modules.movimentacoes import show_movimentacoes_page
        show_movimentacoes_page()
        
        # Verificar que os equipamentos foram buscados
        mock_eq_mgr.get_equipamentos.assert_called()
        # Verificar que o modal foi chamado
        mock_modal.assert_called()


def test_ui_filtros_preenchidos():
    """Teste para cobrir aplicação de filtros preenchidos (linhas 212-225)"""
    with patch('modules.movimentacoes.st') as mock_st, \
         patch('modules.movimentacoes.auth_manager') as mock_auth, \
         patch('modules.movimentacoes.MovimentacoesManager') as mock_manager_class:
        
        # Setup básico
        mock_st.session_state.user_data = {'perfil': 'admin', 'id': 1}
        mock_auth.check_permission.return_value = True
        
        mock_manager = Mock()
        mock_manager.get_movimentacoes.return_value = pd.DataFrame()
        mock_manager.get_dashboard_stats.return_value = {'total_mes': 0, 'entradas_mes': 0, 'saidas_mes': 0}
        mock_manager_class.return_value = mock_manager
        
        # Mock das tabs
        mock_tab1 = MagicMock()
        mock_tab2 = MagicMock()
        mock_tab3 = MagicMock()
        mock_st.tabs.return_value = (mock_tab1, mock_tab2, mock_tab3)
        
        # FILTROS PREENCHIDOS para forçar todas as condições if (linhas 213-225)
        mock_st.text_input.side_effect = lambda label, **kwargs: {
            "Nome do Item": "Cimento",
            "Origem": "Fornecedor ABC", 
            "Destino": "Obra Central"
        }.get(label, "")
        
        mock_st.selectbox.side_effect = lambda label, options, **kwargs: {
            "Tipo": "Entrada"
        }.get(label, options[0] if options else "")
        
        mock_st.date_input.side_effect = lambda label, **kwargs: {
            "Data Início": date(2024, 1, 1),
            "Data Fim": date(2024, 1, 31)
        }.get(label, None)
        
        mock_st.columns.return_value = [Mock(), Mock(), Mock()]
        mock_st.expander.return_value.__enter__ = Mock()
        mock_st.expander.return_value.__exit__ = Mock()
        
        # Executar função
        from modules.movimentacoes import show_movimentacoes_page
        show_movimentacoes_page()
        
        # Verificar que get_movimentacoes foi chamado com filtros
        mock_manager.get_movimentacoes.assert_called()
        call_args = mock_manager.get_movimentacoes.call_args
        if call_args and call_args[0]:
            filters = call_args[0][0]
            # Deve ter aplicado vários filtros
            assert len(filters) > 0
        
        
def test_ui_permissao_negada_create():
    """Teste para cobrir negação de permissão create na tab2 (linhas 249-251)"""
    with patch('modules.movimentacoes.st') as mock_st, \
         patch('modules.movimentacoes.auth_manager') as mock_auth, \
         patch('modules.movimentacoes.MovimentacoesManager') as mock_manager_class:
        
        # Setup básico
        mock_st.session_state.user_data = {'perfil': 'viewer', 'id': 1}
        
        # Permitir read mas negar create
        def check_permission_side_effect(perfil, acao):
            if acao == "read":
                return True
            elif acao == "create":
                return False
            return False
            
        mock_auth.check_permission.side_effect = check_permission_side_effect
        
        mock_manager = Mock()
        mock_manager.get_movimentacoes.return_value = pd.DataFrame()
        mock_manager.get_dashboard_stats.return_value = {'total_mes': 0, 'entradas_mes': 0, 'saidas_mes': 0}
        mock_manager_class.return_value = mock_manager
        
        # Mock das tabs
        mock_tab1 = MagicMock()
        mock_tab2 = MagicMock()
        mock_tab3 = MagicMock()
        mock_st.tabs.return_value = (mock_tab1, mock_tab2, mock_tab3)
        
        # Mock dos componentes básicos
        mock_st.text_input.return_value = ""
        mock_st.selectbox.return_value = "Todos"
        mock_st.date_input.return_value = None
        mock_st.columns.return_value = [Mock(), Mock(), Mock()]
        mock_st.expander.return_value.__enter__ = Mock()
        mock_st.expander.return_value.__exit__ = Mock()
        
        # Executar função
        from modules.movimentacoes import show_movimentacoes_page
        show_movimentacoes_page()
        
        # Verificar que a mensagem de erro foi exibida (linha 250)
        mock_st.error.assert_called_with("❌ Você não tem permissão para criar movimentações.")