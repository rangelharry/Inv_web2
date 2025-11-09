"""
Testes abrangentes para módulo de insumos com alta cobertura
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, date
import json

class TestInsumosManagerHighCoverage:
    """Testes com foco em alta cobertura para InsumosManager"""
    
    @pytest.fixture
    def insumos_setup(self):
        """Setup completo para testes de insumos"""
        with patch('modules.insumos.db') as mock_db, \
             patch('modules.insumos.auth_manager') as mock_auth, \
             patch('streamlit.error') as mock_st_error, \
             patch('streamlit.success') as mock_st_success:
            
            # Mock da conexão
            mock_connection = Mock()
            mock_cursor = Mock()
            
            # Configurar comportamentos padrão
            mock_cursor.fetchone.return_value = None
            mock_cursor.fetchall.return_value = []
            mock_cursor.execute.return_value = None
            mock_cursor.description = []
            
            mock_connection.cursor.return_value = mock_cursor
            mock_connection.commit.return_value = None
            mock_connection.rollback.return_value = None
            # Configurar comportamento bool da conexão
            type(mock_connection).__bool__ = Mock(return_value=True)
            
            mock_db.get_connection.return_value = mock_connection
            
            from modules.insumos import InsumosManager
            manager = InsumosManager()
            
            return manager, mock_cursor, mock_connection, mock_st_error, mock_st_success
    
    def test_init_success(self, insumos_setup):
        """Testa inicialização bem-sucedida"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        assert manager.db is not None
        mock_connection.rollback.assert_called()  # Garantir que conexão foi limpa
    
    def test_init_with_connection_error(self):
        """Testa inicialização com erro de conexão"""
        with patch('modules.insumos.db') as mock_db, \
             patch('streamlit.error') as mock_st_error:
            
            mock_db.get_connection.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception):
                from modules.insumos import InsumosManager
                InsumosManager()
            
            mock_st_error.assert_called()
    
    def test_get_categorias_success(self, insumos_setup):
        """Testa busca de categorias com sucesso"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        # Mock dos dados
        mock_cursor.description = [['id'], ['nome']]
        mock_cursor.fetchall.return_value = [
            (1, 'Hidráulicos'),
            (2, 'Elétricos'),
            (3, 'Ferragens')
        ]
        
        result = manager.get_categorias()
        
        assert len(result) == 3
        assert result[0]['id'] == 1
        assert result[0]['nome'] == 'Hidráulicos'
        
        # Verificar SQL executado
        mock_cursor.execute.assert_called()
        sql_call = mock_cursor.execute.call_args[0][0]
        assert 'categorias' in sql_call.lower()
        assert 'insumo' in mock_cursor.execute.call_args[0][1]
    
    def test_get_categorias_with_custom_type(self, insumos_setup):
        """Testa busca de categorias com tipo específico"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        mock_cursor.description = [['id'], ['nome']]
        mock_cursor.fetchall.return_value = [(1, 'Equipamentos')]
        
        result = manager.get_categorias('equipamento')
        
        assert len(result) == 1
        assert result[0]['nome'] == 'Equipamentos'
        assert 'equipamento' in mock_cursor.execute.call_args[0][1]
    
    def test_get_categorias_empty_result(self, insumos_setup):
        """Testa busca sem resultados"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        mock_cursor.description = []
        mock_cursor.fetchall.return_value = []
        
        result = manager.get_categorias()
        
        assert len(result) == 0
    
    def test_get_categorias_no_connection(self, insumos_setup):
        """Testa busca com falha de conexão"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        # Mock conexão falhando
        with patch.object(manager.db, 'get_connection', return_value=None):
            result = manager.get_categorias()
            assert len(result) == 0
    
    def test_get_categorias_database_error(self, insumos_setup):
        """Testa busca com erro de banco"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        mock_cursor.execute.side_effect = Exception("Database error")
        
        result = manager.get_categorias()
        
        assert len(result) == 0
    
    def test_create_insumo_success(self, insumos_setup):
        """Testa criação bem-sucedida de insumo"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        # Mocks para validações e criação
        mock_cursor.fetchone.side_effect = [
            None,  # Código não existe
            (123,) # ID do insumo criado
        ]
        
        dados = {
            'codigo': 'TEST001',
            'descricao': 'Item Teste',
            'categoria_id': 1,
            'unidade': 'UN',
            'quantidade_atual': 100,
            'quantidade_minima': 10,
            'preco_unitario': 25.50,
            'fornecedor': 'Fornecedor Teste'
        }
        
        success, message = manager.create_insumo(dados, 1)
        
        assert success is True
        assert "sucesso" in message.lower()
        mock_connection.commit.assert_called()
        
        # Verificar que as queries corretas foram executadas
        assert mock_cursor.execute.call_count >= 2  # Verificação + inserção
    
    def test_create_insumo_duplicate_code(self, insumos_setup):
        """Testa criação com código duplicado"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        # Mock código já existe
        mock_cursor.fetchone.return_value = (1,)
        
        dados = {
            'codigo': 'EXIST001',
            'descricao': 'Item Existente',
            'categoria_id': 1,
            'unidade': 'UN'
        }
        
        success, message = manager.create_insumo(dados, 1)
        
        assert success is False
        assert "já existe" in message.lower()
        mock_connection.commit.assert_not_called()
    
    def test_create_insumo_with_optional_fields(self, insumos_setup):
        """Testa criação com campos opcionais"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        mock_cursor.fetchone.side_effect = [None, (123,)]
        
        dados = {
            'codigo': 'TEST002',
            'descricao': 'Item com campos opcionais',
            'categoria_id': 1,
            'unidade': 'UN',
            'quantidade_atual': 50,
            'quantidade_minima': 5,
            'data_validade': '2025-12-31',
            'localizacao': 'Almoxarifado A',
            'observacoes': 'Item de teste'
        }
        
        success, message = manager.create_insumo(dados, 1)
        
        assert success is True
        mock_connection.commit.assert_called()
    
    def test_create_insumo_database_error(self, insumos_setup):
        """Testa criação com erro de banco"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        mock_cursor.execute.side_effect = Exception("Database error")
        
        dados = {
            'codigo': 'ERROR001',
            'descricao': 'Item com erro',
            'categoria_id': 1,
            'unidade': 'UN'
        }
        
        success, message = manager.create_insumo(dados, 1)
        
        assert success is False
        assert "erro" in message.lower()
        mock_connection.rollback.assert_called()
    
    def test_get_insumos_success(self, insumos_setup):
        """Testa busca de insumos com sucesso"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        # Mock dos dados
        mock_cursor.description = [
            ['id'], ['codigo'], ['descricao'], ['quantidade_atual'], ['unidade']
        ]
        mock_cursor.fetchall.return_value = [
            (1, 'TEST001', 'Item 1', 100, 'UN'),
            (2, 'TEST002', 'Item 2', 50, 'KG')
        ]
        
        result = manager.get_insumos()
        
        assert len(result) == 2
        assert result[0]['codigo'] == 'TEST001'
        assert result[1]['codigo'] == 'TEST002'
    
    def test_get_insumos_with_filters(self, insumos_setup):
        """Testa busca com filtros"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        mock_cursor.description = [['id'], ['codigo'], ['descricao']]
        mock_cursor.fetchall.return_value = [(1, 'TUBO001', 'Tubo PVC')]
        
        filtros = {
            'codigo': 'TUBO',
            'categoria_id': 1,
            'baixo_estoque': True
        }
        
        result = manager.get_insumos(filtros)
        
        assert len(result) == 1
        assert 'TUBO' in result[0]['codigo']
        
        # Verificar que filtros foram aplicados na query
        sql_call = mock_cursor.execute.call_args[0][0]
        assert 'where' in sql_call.lower()
    
    def test_get_insumos_database_error(self, insumos_setup):
        """Testa busca com erro de banco"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        mock_cursor.execute.side_effect = Exception("Database error")
        
        result = manager.get_insumos()
        
        assert len(result) == 0
    
    def test_get_insumo_by_id_success(self, insumos_setup):
        """Testa busca por ID com sucesso"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        mock_cursor.description = [['id'], ['codigo'], ['descricao']]
        mock_cursor.fetchone.return_value = (1, 'TEST001', 'Item Teste')
        
        result = manager.get_insumo_by_id(1)
        
        assert result is not None
        assert result['id'] == 1
        assert result['codigo'] == 'TEST001'
    
    def test_get_insumo_by_id_not_found(self, insumos_setup):
        """Testa busca por ID não encontrado"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        mock_cursor.fetchone.return_value = None
        
        result = manager.get_insumo_by_id(999)
        
        assert result is None
    
    def test_update_insumo_success(self, insumos_setup):
        """Testa atualização bem-sucedida"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        # Mock para verificações e atualização
        mock_cursor.fetchone.side_effect = [
            ('ORIGINAL001',),  # Insumo existe
            None,              # Código não duplicado
            (1,)               # Atualização bem-sucedida
        ]
        
        dados = {
            'codigo': 'UPDATED001',
            'descricao': 'Item atualizado',
            'preco_unitario': 30.00
        }
        
        success, message = manager.update_insumo(1, dados, 1)
        
        assert success is True
        assert "sucesso" in message.lower()
        mock_connection.commit.assert_called()
    
    def test_update_insumo_not_found(self, insumos_setup):
        """Testa atualização de insumo inexistente"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        mock_cursor.fetchone.return_value = None
        
        dados = {'descricao': 'Nova descrição'}
        
        success, message = manager.update_insumo(999, dados, 1)
        
        assert success is False
        assert "não encontrado" in message.lower()
    
    def test_delete_insumo_success(self, insumos_setup):
        """Testa exclusão bem-sucedida"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        # Mock para verificar existência
        mock_cursor.fetchone.return_value = ('TEST001', 'Item a ser deletado')
        
        success, message = manager.delete_insumo(1, 1)
        
        assert success is True
        assert "sucesso" in message.lower()
        mock_connection.commit.assert_called()
    
    def test_delete_insumo_not_found(self, insumos_setup):
        """Testa exclusão de insumo inexistente"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        mock_cursor.fetchone.return_value = None
        
        success, message = manager.delete_insumo(999, 1)
        
        assert success is False
        assert "não encontrado" in message.lower()
    
    def test_ajustar_estoque_entrada(self, insumos_setup):
        """Testa ajuste de estoque - entrada"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        # Mock quantidade atual e atualização
        mock_cursor.fetchone.side_effect = [
            (100,),  # Quantidade atual
            (1,)     # Atualização bem-sucedida
        ]
        
        success, message = manager.ajustar_estoque(1, 50, 'entrada', 'Compra', 1)
        
        assert success is True
        mock_connection.commit.assert_called()
        
        # Verificar que log de movimentação foi criado
        assert mock_cursor.execute.call_count >= 3  # SELECT + UPDATE + LOG
    
    def test_ajustar_estoque_saida_suficiente(self, insumos_setup):
        """Testa ajuste de estoque - saída com quantidade suficiente"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        mock_cursor.fetchone.side_effect = [(100,), (1,)]
        
        success, message = manager.ajustar_estoque(1, 30, 'saida', 'Uso obra', 1)
        
        assert success is True
        mock_connection.commit.assert_called()
    
    def test_ajustar_estoque_saida_insuficiente(self, insumos_setup):
        """Testa ajuste de estoque - saída insuficiente"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        mock_cursor.fetchone.return_value = (10,)  # Quantidade atual baixa
        
        success, message = manager.ajustar_estoque(1, 50, 'saida', 'Uso obra', 1)
        
        assert success is False
        assert "insuficiente" in message.lower()
        mock_connection.commit.assert_not_called()
    
    def test_ajustar_estoque_invalid_quantity(self, insumos_setup):
        """Testa ajuste com quantidade inválida"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        success, message = manager.ajustar_estoque(1, -10, 'entrada', 'Teste', 1)
        
        assert success is False
        assert "quantidade" in message.lower()
    
    def test_ajustar_estoque_database_error(self, insumos_setup):
        """Testa ajuste com erro de banco"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        mock_cursor.execute.side_effect = Exception("Database error")
        
        success, message = manager.ajustar_estoque(1, 10, 'entrada', 'Teste', 1)
        
        assert success is False
        assert "erro" in message.lower()
        mock_connection.rollback.assert_called()
    
    def test_get_dashboard_stats_success(self, insumos_setup):
        """Testa estatísticas do dashboard"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        # Mock diferentes consultas estatísticas
        mock_cursor.fetchone.side_effect = [
            (150,),    # Total insumos
            (25,),     # Baixo estoque
            (1250.75,),# Valor total estoque
            (8,)       # Total tipos/categorias
        ]
        
        stats = manager.get_dashboard_stats()
        
        assert 'total' in stats
        assert 'estoque_baixo' in stats
        assert 'valor_total' in stats
        assert 'tipos' in stats
        
        assert stats['total'] == 150
        assert stats['estoque_baixo'] == 25
        assert stats['valor_total'] == 1250.75
        assert stats['tipos'] == 8
    
    def test_get_dashboard_stats_database_error(self, insumos_setup):
        """Testa estatísticas com erro de banco"""
        manager, mock_cursor, mock_connection, mock_st_error, mock_st_success = insumos_setup
        
        mock_cursor.execute.side_effect = Exception("Database error")
        
        stats = manager.get_dashboard_stats()
        
        # Deve retornar estrutura vazia ou padrão
        assert isinstance(stats, dict)


@pytest.mark.integration
class TestInsumosIntegrationHighCoverage:
    """Testes de integração abrangentes para insumos"""
    
    def test_complete_insumo_workflow(self):
        """Testa workflow completo de insumo"""
        with patch('modules.insumos.db') as mock_db, \
             patch('modules.insumos.auth_manager'):
            
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_db.get_connection.return_value = mock_connection
            
            from modules.insumos import InsumosManager
            manager = InsumosManager()
            
            # 1. Criar insumo
            mock_cursor.fetchone.side_effect = [None, (1,)]
            dados = {
                'codigo': 'WORKFLOW001',
                'descricao': 'Item Workflow',
                'categoria_id': 1,
                'unidade': 'UN',
                'quantidade_atual': 100,
                'quantidade_minima': 10
            }
            success, _ = manager.create_insumo(dados, 1)
            assert success is True
            
            # 2. Buscar insumo criado
            mock_cursor.description = [['id'], ['codigo'], ['descricao']]
            mock_cursor.fetchone.return_value = (1, 'WORKFLOW001', 'Item Workflow')
            insumo = manager.get_insumo_by_id(1)
            assert insumo is not None
            
            # 3. Ajustar estoque
            mock_cursor.fetchone.side_effect = [(100,), (1,)]
            success, _ = manager.ajustar_estoque(1, 50, 'entrada', 'Reposição', 1)
            assert success is True
            
            # 4. Atualizar dados
            mock_cursor.fetchone.side_effect = [
                ('WORKFLOW001',), None, (1,)
            ]
            success, _ = manager.update_insumo(1, {'descricao': 'Item Atualizado'}, 1)
            assert success is True
            
            # 5. Buscar estatísticas
            mock_cursor.fetchone.side_effect = [(1,), (0,), (150.0,), (1,)]
            stats = manager.get_dashboard_stats()
            assert stats['total'] == 1
    
    def test_error_handling_workflow(self):
        """Testa tratamento de erros em workflow"""
        with patch('modules.insumos.db') as mock_db:
            
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_db.get_connection.return_value = mock_connection
            
            from modules.insumos import InsumosManager
            manager = InsumosManager()
            
            # 1. Erro na criação
            mock_cursor.execute.side_effect = Exception("Database error")
            success, message = manager.create_insumo({'codigo': 'ERR001'}, 1)
            assert success is False
            assert "erro" in message.lower()
            mock_connection.rollback.assert_called()
            
            # 2. Reset mocks para próximo teste
            mock_cursor.reset_mock()
            mock_connection.reset_mock()
            mock_cursor.execute.side_effect = Exception("Database error")
            
            # 3. Erro na busca
            result = manager.get_insumos()
            assert len(result) == 0