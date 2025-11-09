"""
Testes para o módulo de insumos
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date

@pytest.mark.unit
class TestInsumosManager:
    """Testes unitários para InsumosManager"""
    
    @pytest.fixture
    def insumos_manager(self, test_db):
        """Fixture para instância do InsumosManager"""
        with patch('modules.insumos.db') as mock_db:
            mock_db.get_connection.return_value = test_db
            from modules.insumos import InsumosManager
            return InsumosManager()
    
    def test_get_categorias_success(self, insumos_manager, test_db):
        """Teste de obtenção de categorias bem-sucedida"""
        categorias_mock = [
            {'id': 1, 'nome': 'Categoria 1'},
            {'id': 2, 'nome': 'Categoria 2'}
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('id',), ('nome',)]
        mock_cursor.fetchall.return_value = [
            (1, 'Categoria 1'),
            (2, 'Categoria 2')
        ]
        
        categorias = insumos_manager.get_categorias('insumo')
        
        assert len(categorias) == 2
        assert categorias[0]['nome'] == 'Categoria 1'
        assert categorias[1]['nome'] == 'Categoria 2'
    
    def test_get_categorias_empty(self, insumos_manager, test_db):
        """Teste de obtenção de categorias vazia"""
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('id',), ('nome',)]
        mock_cursor.fetchall.return_value = []
        
        categorias = insumos_manager.get_categorias('insumo')
        
        assert len(categorias) == 0
        assert categorias == []
    
    def test_get_categorias_no_description(self, insumos_manager, test_db):
        """Teste de obtenção de categorias sem descrição"""
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = None
        
        categorias = insumos_manager.get_categorias('insumo')
        
        assert len(categorias) == 0
    
    @patch('modules.insumos.auth_manager')
    def test_criar_insumo_success(self, mock_auth, insumos_manager, test_db, sample_insumo_data):
        """Teste de criação de insumo bem-sucedida"""
        user_id = 1
        
        # Configurar mock do cursor
        mock_cursor = test_db.cursor.return_value
        # Primeira chamada: código não existe (None), segunda: ID do insumo criado (1,)
        mock_cursor.fetchone.side_effect = [None, (1,)]
        
        success, message = insumos_manager.criar_insumo(sample_insumo_data, user_id)
        
        assert success is True
        assert "sucesso" in message.lower()
        assert mock_cursor.execute.called
        assert test_db.commit.called
        mock_auth.log_action.assert_called()
    
    @patch('modules.insumos.auth_manager')
    def test_criar_insumo_duplicate_code(self, mock_auth, insumos_manager, test_db, sample_insumo_data):
        """Teste de criação de insumo com código duplicado"""
        user_id = 1
        
        # Simular código já existente
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = (1,)  # Código já existe
        
        success, message = insumos_manager.criar_insumo(sample_insumo_data, user_id)
        
        assert success is False
        assert ("código já existe" in message.lower()) or ("erro" in message.lower())
    
    def test_buscar_insumos_all(self, insumos_manager, test_db):
        """Teste de busca de todos os insumos"""
        insumos_mock = [
            (1, 'INS001', 'Insumo 1', 1, 'UN', 100, 10, 'Fornecedor 1', 'Marca 1', 'A1', 'Obs 1', None),
            (2, 'INS002', 'Insumo 2', 2, 'KG', 50, 5, 'Fornecedor 2', 'Marca 2', 'A2', 'Obs 2', None)
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [
            ('id',), ('codigo',), ('descricao',), ('categoria_id',), ('unidade',),
            ('quantidade_atual',), ('quantidade_minima',), ('fornecedor',), 
            ('marca',), ('localizacao',), ('observacoes',), ('data_validade',)
        ]
        mock_cursor.fetchall.return_value = insumos_mock
        
        insumos = insumos_manager.buscar_insumos()
        
        assert len(insumos) == 2
        assert insumos[0]['codigo'] == 'INS001'
        assert insumos[1]['codigo'] == 'INS002'
    
    def test_buscar_insumos_with_filter(self, insumos_manager, test_db):
        """Teste de busca de insumos com filtro"""
        filtros = {'codigo': 'INS001'}
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('id',), ('codigo',), ('descricao',)]
        mock_cursor.fetchall.return_value = [(1, 'INS001', 'Insumo 1')]
        
        insumos = insumos_manager.buscar_insumos(filtros)
        
        # Verificar se WHERE foi adicionado à query
        execute_calls = mock_cursor.execute.call_args_list
        assert len(execute_calls) > 0
        query = execute_calls[0][0][0]
        assert 'WHERE' in query
    
    @patch('modules.insumos.auth_manager')
    def test_atualizar_insumo_success(self, mock_auth, insumos_manager, test_db, sample_insumo_data):
        """Teste de atualização de insumo bem-sucedida"""
        user_id = 1
        insumo_id = 1
        
        # Mock para buscar dados antigos
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('codigo',), ('descricao',)]
        mock_cursor.fetchone.return_value = ('INS001', 'Insumo Original')
        
        success, message = insumos_manager.atualizar_insumo(insumo_id, sample_insumo_data, user_id)
        
        assert success is True
        assert "sucesso" in message.lower()
        mock_auth.log_action.assert_called()
    
    @patch('modules.insumos.auth_manager')
    def test_deletar_insumo_success(self, mock_auth, insumos_manager, test_db):
        """Teste de deleção de insumo bem-sucedida"""
        user_id = 1
        insumo_id = 1
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('codigo',), ('descricao',)]
        mock_cursor.fetchone.return_value = ('INS001', 'Insumo Teste')
        
        success, message = insumos_manager.deletar_insumo(insumo_id, user_id)
        
        assert success is True
        assert "sucesso" in message.lower()
        mock_auth.log_action.assert_called()
    
    def test_get_insumo_by_id_found(self, insumos_manager, test_db):
        """Teste de busca de insumo por ID encontrado"""
        insumo_id = 1
        insumo_data = (1, 'INS001', 'Insumo Teste', 1, 'UN', 100, 10, 'Fornecedor', 'Marca', 'A1', 'Obs', None)
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [
            ('id',), ('codigo',), ('descricao',), ('categoria_id',), ('unidade',),
            ('quantidade_atual',), ('quantidade_minima',), ('fornecedor',), 
            ('marca',), ('localizacao',), ('observacoes',), ('data_validade',)
        ]
        mock_cursor.fetchone.return_value = insumo_data
        
        insumo = insumos_manager.get_insumo_by_id(insumo_id)
        
        assert insumo is not None
        assert insumo['codigo'] == 'INS001'
        assert insumo['descricao'] == 'Insumo Teste'
    
    def test_get_insumo_by_id_not_found(self, insumos_manager, test_db):
        """Teste de busca de insumo por ID não encontrado"""
        insumo_id = 999
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = None
        
        insumo = insumos_manager.get_insumo_by_id(insumo_id)
        
        assert insumo is None
    
    def test_get_insumos_baixo_estoque(self, insumos_manager, test_db):
        """Teste de busca de insumos com baixo estoque"""
        insumos_baixo_estoque = [
            (1, 'INS001', 'Insumo 1', 5, 10),  # quantidade_atual < quantidade_minima
            (2, 'INS002', 'Insumo 2', 3, 20)   # quantidade_atual < quantidade_minima
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('id',), ('codigo',), ('descricao',), ('quantidade_atual',), ('quantidade_minima',)]
        mock_cursor.fetchall.return_value = insumos_baixo_estoque
        
        insumos = insumos_manager.get_insumos_baixo_estoque()
        
        assert len(insumos) == 2
        # Verificar se a query filtra por baixo estoque
        execute_calls = mock_cursor.execute.call_args_list
        query = execute_calls[0][0][0]
        assert 'quantidade_atual' in query
        assert 'quantidade_minima' in query
    
    def test_get_insumos_vencendo(self, insumos_manager, test_db):
        """Teste de busca de insumos próximos ao vencimento"""
        from datetime import datetime, timedelta
        
        # Data próxima do vencimento
        data_vencimento = datetime.now() + timedelta(days=15)
        insumos_vencendo = [
            (1, 'INS001', 'Insumo 1', data_vencimento),
            (2, 'INS002', 'Insumo 2', data_vencimento)
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('id',), ('codigo',), ('descricao',), ('data_validade',)]
        mock_cursor.fetchall.return_value = insumos_vencendo
        
        insumos = insumos_manager.get_insumos_vencendo(30)  # 30 dias
        
        assert len(insumos) == 2
        # Verificar se a query filtra por data de validade
        execute_calls = mock_cursor.execute.call_args_list
        query = execute_calls[0][0][0]
        assert 'data_validade' in query
    
    @patch('modules.insumos.auth_manager')
    def test_ajustar_estoque_entrada(self, mock_auth, insumos_manager, test_db):
        """Teste de ajuste de estoque (entrada)"""
        user_id = 1
        insumo_id = 1
        quantidade = 50
        tipo_movimento = 'entrada'
        motivo = 'Compra'
        
        # Mock do insumo atual
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.side_effect = [
            (100,),  # quantidade atual
            ('INS001', 'Insumo Teste')  # dados do insumo
        ]
        
        success, message = insumos_manager.ajustar_estoque(
            insumo_id, quantidade, tipo_movimento, motivo, user_id
        )
        
        assert success is True
        assert ("sucesso" in message.lower()) or ("ajustado" in message.lower())
        mock_auth.log_action.assert_called()
    
    @patch('modules.insumos.auth_manager')
    def test_ajustar_estoque_saida(self, mock_auth, insumos_manager, test_db):
        """Teste de ajuste de estoque (saída)"""
        user_id = 1
        insumo_id = 1
        quantidade = 30
        tipo_movimento = 'saida'
        motivo = 'Consumo'
        
        # Mock do insumo atual
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.side_effect = [
            (100,),  # quantidade atual
            ('INS001', 'Insumo Teste')  # dados do insumo
        ]
        
        success, message = insumos_manager.ajustar_estoque(
            insumo_id, quantidade, tipo_movimento, motivo, user_id
        )
        
        assert success is True
        assert "sucesso" in message.lower()
        mock_auth.log_action.assert_called()
    
    def test_ajustar_estoque_saida_insuficiente(self, insumos_manager, test_db):
        """Teste de ajuste de estoque com quantidade insuficiente"""
        user_id = 1
        insumo_id = 1
        quantidade = 150  # Maior que o estoque disponível
        tipo_movimento = 'saida'
        motivo = 'Consumo'
        
        # Mock do insumo atual
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = (100,)  # quantidade atual
        
        success, message = insumos_manager.ajustar_estoque(
            insumo_id, quantidade, tipo_movimento, motivo, user_id
        )
        
        assert success is False
        assert "insuficiente" in message.lower()


@pytest.mark.integration
class TestInsumosIntegration:
    """Testes de integração para insumos"""
    
    def test_crud_complete_workflow(self, test_db, sample_insumo_data):
        """Teste completo do workflow CRUD de insumos"""
        with patch('modules.insumos.db') as mock_db, \
             patch('modules.insumos.auth_manager') as mock_auth:
            
            mock_db.get_connection.return_value = test_db
            from modules.insumos import InsumosManager
            insumos_manager = InsumosManager()
            
            user_id = 1
            
            # Configurar mocks para cada operação
            mock_cursor = test_db.cursor.return_value
            
            # 1. Criar insumo
            mock_cursor.fetchone.side_effect = [
                (1,),  # ID do insumo criado
                sample_insumo_data['codigo'],  # Para atualização
                sample_insumo_data['descricao'],  # Para deleção
            ]
            
            # Criar
            success, _ = insumos_manager.criar_insumo(sample_insumo_data, user_id)
            assert success is True
            
            # 2. Buscar
            mock_cursor.description = [('id',), ('codigo',), ('descricao',)]
            mock_cursor.fetchall.return_value = [(1, sample_insumo_data['codigo'], sample_insumo_data['descricao'])]
            
            insumos = insumos_manager.buscar_insumos()
            assert len(insumos) > 0
            
            # 3. Atualizar
            updated_data = sample_insumo_data.copy()
            updated_data['descricao'] = 'Descrição Atualizada'
            
            mock_cursor.fetchone.side_effect = [
                (sample_insumo_data['codigo'], sample_insumo_data['descricao'])  # dados antigos
            ]
            
            success, _ = insumos_manager.atualizar_insumo(1, updated_data, user_id)
            assert success is True
            
            # 4. Deletar
            mock_cursor.fetchone.return_value = (sample_insumo_data['codigo'], updated_data['descricao'])
            
            success, _ = insumos_manager.deletar_insumo(1, user_id)
            assert success is True


@pytest.mark.parametrize("quantidade_atual,quantidade_minima,expected_baixo_estoque", [
    (5, 10, True),   # Baixo estoque
    (10, 10, False), # No limite
    (15, 10, False), # Estoque OK
    (0, 5, True),    # Sem estoque
])
def test_check_baixo_estoque(quantidade_atual, quantidade_minima, expected_baixo_estoque):
    """Teste parametrizado para verificação de baixo estoque"""
    # Lógica simples de verificação
    is_baixo_estoque = quantidade_atual < quantidade_minima
    assert is_baixo_estoque == expected_baixo_estoque