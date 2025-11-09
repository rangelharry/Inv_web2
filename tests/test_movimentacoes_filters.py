"""
Testes específicos para cobrir linhas de filtros em get_movimentacoes
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_get_movimentacoes_filtro_item_nome():
    """Teste específico para filtro item_nome (linha 96-98)"""
    with patch('modules.movimentacoes.db') as mock_db:
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value = mock_connection
        
        from modules.movimentacoes import MovimentacoesManager
        manager = MovimentacoesManager()
        
        filters = {'item_nome': 'Cimento'}
        
        with patch('modules.movimentacoes.st'):
            manager.get_movimentacoes(filters)
            
            query = mock_cursor.execute.call_args[0][0]
            params = mock_cursor.execute.call_args[0][1]
            
            assert "i.descricao LIKE %s" in query
            assert "%Cimento%" in params


def test_get_movimentacoes_filtro_obra_origem():
    """Teste específico para filtro obra_origem (linha 102-104)"""
    with patch('modules.movimentacoes.db') as mock_db:
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value = mock_connection
        
        from modules.movimentacoes import MovimentacoesManager
        manager = MovimentacoesManager()
        
        filters = {'obra_origem': 'Obra Norte'}
        
        with patch('modules.movimentacoes.st'):
            manager.get_movimentacoes(filters)
            
            query = mock_cursor.execute.call_args[0][0]
            params = mock_cursor.execute.call_args[0][1]
            
            assert "o1.nome LIKE %s" in query
            assert "%Obra Norte%" in params


def test_get_movimentacoes_filtro_obra_destino():
    """Teste específico para filtro obra_destino (linha 105-107)"""
    with patch('modules.movimentacoes.db') as mock_db:
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value = mock_connection
        
        from modules.movimentacoes import MovimentacoesManager
        manager = MovimentacoesManager()
        
        filters = {'obra_destino': 'Obra Sul'}
        
        with patch('modules.movimentacoes.st'):
            manager.get_movimentacoes(filters)
            
            query = mock_cursor.execute.call_args[0][0]
            params = mock_cursor.execute.call_args[0][1]
            
            assert "o2.nome LIKE %s" in query
            assert "%Obra Sul%" in params


def test_get_movimentacoes_filtro_responsavel_origem():
    """Teste específico para filtro responsavel_origem (linha 108-110)"""
    with patch('modules.movimentacoes.db') as mock_db:
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value = mock_connection
        
        from modules.movimentacoes import MovimentacoesManager
        manager = MovimentacoesManager()
        
        filters = {'responsavel_origem': 'João Silva'}
        
        with patch('modules.movimentacoes.st'):
            manager.get_movimentacoes(filters)
            
            query = mock_cursor.execute.call_args[0][0]
            params = mock_cursor.execute.call_args[0][1]
            
            assert "r1.nome LIKE %s" in query
            assert "%João Silva%" in params


def test_get_movimentacoes_filtro_responsavel_destino():
    """Teste específico para filtro responsavel_destino (linha 111-113)"""
    with patch('modules.movimentacoes.db') as mock_db:
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value = mock_connection
        
        from modules.movimentacoes import MovimentacoesManager
        manager = MovimentacoesManager()
        
        filters = {'responsavel_destino': 'Maria Santos'}
        
        with patch('modules.movimentacoes.st'):
            manager.get_movimentacoes(filters)
            
            query = mock_cursor.execute.call_args[0][0]
            params = mock_cursor.execute.call_args[0][1]
            
            assert "r2.nome LIKE %s" in query
            assert "%Maria Santos%" in params


def test_get_movimentacoes_paginacao():
    """Teste para cobrir paginação completa (linhas não cobertas em paginação)"""
    with patch('modules.movimentacoes.db') as mock_db:
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value = mock_connection
        
        from modules.movimentacoes import MovimentacoesManager
        manager = MovimentacoesManager()
        
        # Testar sem filtro de página (padrão)
        filters = {}
        
        with patch('modules.movimentacoes.st'):
            manager.get_movimentacoes(filters)
            
            # Verificar se tem LIMIT e OFFSET padrão
            query = mock_cursor.execute.call_args[0][0]
            assert "ORDER BY m.data_movimentacao DESC" in query


def test_get_dashboard_stats_sem_rollback():
    """Teste get_dashboard_stats sem rollback (linha 139-156)"""
    with patch('modules.movimentacoes.db') as mock_db:
        # Connection sem rollback
        mock_connection = Mock()
        del mock_connection.rollback  # Remover rollback
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {
            'total_mes': 50,
            'entradas_mes': 30,
            'saidas_mes': 20
        }
        mock_connection.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value = mock_connection
        
        from modules.movimentacoes import MovimentacoesManager
        manager = MovimentacoesManager()
        
        result = manager.get_dashboard_stats()
        
        assert result['total_mes'] == 50
        assert result['entradas_mes'] == 30
        assert result['saidas_mes'] == 20


def test_get_dashboard_stats_excecao_sem_rollback():
    """Teste get_dashboard_stats com exceção e sem rollback (linha 150-156)"""
    with patch('modules.movimentacoes.db') as mock_db:
        # Connection sem rollback
        mock_connection = Mock()
        del mock_connection.rollback  # Remover rollback
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("Erro na query")
        mock_connection.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value = mock_connection
        
        from modules.movimentacoes import MovimentacoesManager
        manager = MovimentacoesManager()
        
        with patch('modules.movimentacoes.st') as mock_st:
            result = manager.get_dashboard_stats()
            
            # Deve retornar valores padrão
            assert result['total_mes'] == 0
            assert result['entradas_mes'] == 0
            assert result['saidas_mes'] == 0
            mock_st.error.assert_called()


def test_get_movimentacoes_sem_rollback():
    """Teste get_movimentacoes sem rollback (linha 76)"""
    with patch('modules.movimentacoes.db') as mock_db:
        # Connection sem rollback
        mock_connection = Mock()
        del mock_connection.rollback  # Remover rollback
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value = mock_connection
        
        from modules.movimentacoes import MovimentacoesManager
        manager = MovimentacoesManager()
        
        with patch('modules.movimentacoes.st'):
            result = manager.get_movimentacoes({})
            
            assert isinstance(result, pd.DataFrame)


def test_create_movimentacao_sem_rollback():
    """Teste create_movimentacao sem rollback (linha 22-23)"""
    with patch('modules.movimentacoes.db') as mock_db:
        # Connection sem rollback
        mock_connection = Mock()
        del mock_connection.rollback  # Remover rollback  
        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [
            {'quantidade_atual': 100},  # get_quantidade_atual
            {'currval': 123}            # currval
        ]
        mock_cursor.execute.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.commit.return_value = None
        mock_db.get_connection.return_value = mock_connection
        
        from modules.movimentacoes import MovimentacoesManager
        manager = MovimentacoesManager()
        
        data = {
            'item_id': 1,
            'tipo': 'Entrada',
            'tipo_item': 'insumo',
            'quantidade': 50,
            'motivo': 'Teste sem rollback'
        }
        
        with patch('modules.movimentacoes.st'):
            result = manager.create_movimentacao(data, 1)
            
            assert result == 123


def test_create_movimentacao_erro_sem_rollback():
    """Teste create_movimentacao com erro e sem rollback (linha 62-69)"""
    with patch('modules.movimentacoes.db') as mock_db:
        # Connection sem rollback
        mock_connection = Mock()
        del mock_connection.rollback  # Remover rollback
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("Erro na query")
        mock_connection.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value = mock_connection
        
        from modules.movimentacoes import MovimentacoesManager
        manager = MovimentacoesManager()
        
        data = {
            'item_id': 1,
            'tipo': 'Entrada',
            'tipo_item': 'insumo',
            'quantidade': 50,
            'motivo': 'Teste erro sem rollback'
        }
        
        with patch('modules.movimentacoes.st') as mock_st:
            result = manager.create_movimentacao(data, 1)
            
            assert result is None
            mock_st.error.assert_called()


def test_get_movimentacoes_com_resultados():
    """Teste para cobrir retorno de DataFrame com dados (linha 119)"""
    with patch('modules.movimentacoes.db') as mock_db:
        mock_connection = Mock()
        mock_cursor = Mock()
        
        # Dados de retorno
        mock_results = [
            {
                'id': 1,
                'data_movimentacao': '2024-01-15 10:30:00',
                'tipo': 'Entrada',
                'quantidade': 100,
                'motivo': 'Compra',
                'obra_origem': 'Fornecedor',
                'obra_destino': 'Obra A',
                'responsavel_origem': 'João',
                'responsavel_destino': 'Maria',
                'valor_unitario': 50.0,
                'observacoes': 'Teste',
                'item_nome': 'Cimento',
                'codigo': 'CIM001',
                'usuario_nome': 'Admin'
            }
        ]
        
        mock_cursor.fetchall.return_value = mock_results
        mock_connection.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value = mock_connection
        
        from modules.movimentacoes import MovimentacoesManager
        manager = MovimentacoesManager()
        
        with patch('modules.movimentacoes.st'):
            result = manager.get_movimentacoes({})
            
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 1
            assert result.iloc[0]['id'] == 1
            assert result.iloc[0]['tipo'] == 'Entrada'


def test_get_movimentacoes_filtros_combinados_completos():
    """Teste com todos os filtros combinados para cobrir todas as linhas"""
    with patch('modules.movimentacoes.db') as mock_db:
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value = mock_connection
        
        from modules.movimentacoes import MovimentacoesManager
        manager = MovimentacoesManager()
        
        # Todos os filtros possíveis
        filters = {
            'item_nome': 'Cimento',
            'tipo': 'Entrada',
            'obra_origem': 'Fornecedor ABC',
            'obra_destino': 'Obra Norte',
            'responsavel_origem': 'João Silva',
            'responsavel_destino': 'Maria Santos',
            'data_inicio': '2024-01-01',
            'data_fim': '2024-01-31'
        }
        
        with patch('modules.movimentacoes.st'):
            result = manager.get_movimentacoes(filters)
            
            query = mock_cursor.execute.call_args[0][0]
            params = mock_cursor.execute.call_args[0][1]
            
            # Verificar que todos os filtros foram aplicados
            assert "i.descricao LIKE %s" in query
            assert "m.tipo = %s" in query
            assert "o1.nome LIKE %s" in query
            assert "o2.nome LIKE %s" in query
            assert "r1.nome LIKE %s" in query
            assert "r2.nome LIKE %s" in query
            assert "m.data_movimentacao::date >= %s" in query
            assert "m.data_movimentacao::date <= %s" in query
            
            assert "%Cimento%" in params
            assert "Entrada" in params
            assert "%Fornecedor ABC%" in params
            assert "%Obra Norte%" in params
            assert "%João Silva%" in params
            assert "%Maria Santos%" in params
            assert "2024-01-01" in params
            assert "2024-01-31" in params


def test_create_movimentacao_commit_sucesso():
    """Teste para cobrir commit bem-sucedido (linha 57)"""
    with patch('modules.movimentacoes.db') as mock_db:
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [
            {'quantidade_atual': 200},  # get_quantidade_atual
            {'currval': 999}            # currval
        ]
        mock_cursor.execute.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.commit.return_value = None  # Commit explícito
        mock_db.get_connection.return_value = mock_connection
        
        from modules.movimentacoes import MovimentacoesManager
        manager = MovimentacoesManager()
        
        data = {
            'item_id': 1,
            'tipo': 'Saída',
            'tipo_item': 'insumo',
            'quantidade': 50,
            'motivo': 'Teste commit sucesso'
        }
        
        with patch('modules.movimentacoes.st'):
            result = manager.create_movimentacao(data, 1)
            
            assert result == 999
            mock_connection.commit.assert_called()


def test_get_dashboard_stats_fetchone_sucesso():
    """Teste para cobrir fetchone bem-sucedido no dashboard (linha 144)"""
    with patch('modules.movimentacoes.db') as mock_db:
        mock_connection = Mock()
        mock_cursor = Mock()
        
        # Mock fetchone com resultado
        mock_cursor.fetchone.return_value = {
            'total_mes': 150,
            'entradas_mes': 90,
            'saidas_mes': 60
        }
        
        mock_connection.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value = mock_connection
        
        from modules.movimentacoes import MovimentacoesManager
        manager = MovimentacoesManager()
        
        result = manager.get_dashboard_stats()
        
        # Verificar que os valores corretos foram retornados
        assert result['total_mes'] == 150
        assert result['entradas_mes'] == 90
        assert result['saidas_mes'] == 60