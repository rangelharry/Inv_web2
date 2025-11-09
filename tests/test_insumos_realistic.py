"""
Testes abrangentes para o módulo de insumos com alta cobertura
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, date

class TestInsumosManagerReal:
    """Testes baseados na interface real do InsumosManager com alta cobertura"""
    
    @pytest.fixture
    def insumos_manager_with_mock(self):
        """Fixture com mock completo e realístico do banco"""
        with patch('modules.insumos.db') as mock_db, \
             patch('modules.insumos.auth_manager') as mock_auth, \
             patch('streamlit.session_state', new_callable=dict) as mock_session:
            
            # Configurar mock da conexão
            mock_connection = Mock()
            mock_cursor = Mock()
            
            # Configurar comportamento do cursor
            mock_cursor.fetchone.return_value = None
            mock_cursor.fetchall.return_value = []
            mock_cursor.execute.return_value = None
            mock_cursor.description = []
            
            # Configurar comportamento da conexão
            mock_connection.cursor.return_value = mock_cursor
            mock_connection.commit.return_value = None
            mock_connection.rollback.return_value = None
            mock_connection.__enter__.return_value = mock_connection
            mock_connection.__exit__.return_value = None
            
            # Configurar comportamento do db
            mock_db.get_connection.return_value = mock_connection
            
            from modules.insumos import InsumosManager
            return InsumosManager(), mock_cursor, mock_connection
    
    def test_get_categorias_success(self, insumos_manager_with_mock):
        """Testa busca de categorias com sucesso"""
        insumos_manager, mock_cursor, mock_connection = insumos_manager_with_mock
        
        # Mock dos dados das categorias
        mock_cursor.description = [['id'], ['nome']]
        mock_cursor.fetchall.return_value = [
            (1, 'Materiais Hidráulicos'),
            (2, 'Materiais Elétricos'),
            (3, 'Ferragens')
        ]
        
        categorias = insumos_manager.get_categorias()
        
        assert len(categorias) == 3
        assert categorias[0]['nome'] == 'Materiais Hidráulicos'
        assert categorias[1]['nome'] == 'Materiais Elétricos'
        assert categorias[2]['nome'] == 'Ferragens'
        
        # Verificar que a query foi executada corretamente
        mock_cursor.execute.assert_called_once()
    
    def test_get_categorias_empty(self, insumos_manager_with_mock):
        """Testa busca de categorias sem resultados"""
        insumos_manager, mock_cursor, mock_connection = insumos_manager_with_mock
        
        mock_cursor.description = []
        mock_cursor.fetchall.return_value = []
        
        categorias = insumos_manager.get_categorias()
        
        assert len(categorias) == 0
    
    def test_get_categorias_database_error(self, insumos_manager_with_mock):
        """Testa busca de categorias com erro de banco"""
        insumos_manager, mock_cursor, mock_connection = insumos_manager_with_mock
        
        mock_cursor.execute.side_effect = Exception("Database error")
        
        categorias = insumos_manager.get_categorias()
        
        assert len(categorias) == 0
    
    def test_get_categorias_with_type_filter(self, insumos_manager_with_mock):
        """Testa busca de categorias com filtro por tipo"""
        insumos_manager, mock_cursor, mock_connection = insumos_manager_with_mock
        
        mock_cursor.description = [['id'], ['nome']]
        mock_cursor.fetchall.return_value = [(1, 'Equipamentos')]
        
        categorias = insumos_manager.get_categorias('equipamento')
        
        assert len(categorias) == 1
        assert categorias[0]['nome'] == 'Equipamentos'
        
        # Verificar que o parâmetro foi passado corretamente
        args, kwargs = mock_cursor.execute.call_args
        assert 'equipamento' in args[1]
    
    def test_create_insumo_success(self, insumos_manager_with_mock):
        """Testa criação bem-sucedida de insumo"""
        insumos_manager, mock_cursor, mock_connection = insumos_manager_with_mock
        
        # Mock para verificar código único e criação
        mock_cursor.fetchone.side_effect = [
            None,  # Código não existe
            (123,) # ID do insumo criado
        ]
        
        dados_insumo = {
            'codigo': 'TEST001',
            'descricao': 'Tubo PVC 100mm',
            'categoria_id': 1,
            'unidade': 'UN',
            'quantidade_atual': 100,
            'quantidade_minima': 10,
            'fornecedor': 'Fornecedor Teste',
            'preco_unitario': 25.50,
            'data_validade': '2025-12-31'
        }
        
        success, message = insumos_manager.create_insumo(dados_insumo, 1)
        
        assert success is True
        assert "sucesso" in message.lower()
        assert mock_cursor.execute.call_count == 2  # Verificar código + inserir
        mock_connection.commit.assert_called_once()
    
    def test_create_insumo_missing_required_fields(self, insumos_manager_with_mock):
        """Testa criação com campos obrigatórios faltando"""
        insumos_manager, mock_cursor, mock_connection = insumos_manager_with_mock
        
        # Dados incompletos
        dados_insumo = {
            'codigo': 'TEST001'
            # Faltando campos obrigatórios
        }
        
        success, message = insumos_manager.create_insumo(dados_insumo, 1)
        
        assert success is False
        # Não deve tentar executar query se dados estão incompletos
        mock_connection.commit.assert_not_called()
    
    def test_create_insumo_invalid_quantity(self, insumos_manager_with_mock):
        """Testa criação com quantidade inválida"""
        insumos_manager, mock_cursor, mock_connection = insumos_manager_with_mock
        
        dados_insumo = {
            'codigo': 'TEST001',
            'descricao': 'Tubo PVC 100mm',
            'categoria_id': 1,
            'unidade': 'UN',
            'quantidade_atual': -10,  # Quantidade negativa
            'quantidade_minima': 10,
        }
        
        success, message = insumos_manager.create_insumo(dados_insumo, 1)
        
        assert success is False
        assert "quantidade" in message.lower() or "negativ" in message.lower()
    
    def test_create_insumo_duplicate_code(self, insumos_manager_with_mock, test_db):
        """Testa criação com código duplicado"""
        mock_cursor = test_db.cursor.return_value
        
        # Mock para código já existente
        mock_cursor.fetchone.return_value = (1,)  # Código já existe
        
        dados_insumo = {
            'codigo': 'EXIST001',
            'descricao': 'Item Existente',
            'categoria_id': 1,
            'unidade': 'UN'
        }
        
        success, message = insumos_manager_with_mock.create_insumo(dados_insumo, 1)
        
        assert success is False
        assert "já existe" in message.lower() or "duplicado" in message.lower()
    
    def test_get_insumos_all(self, insumos_manager_with_mock, test_db):
        """Testa busca de todos os insumos"""
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [
            ('id',), ('codigo',), ('descricao',), ('quantidade_atual',)
        ]
        mock_cursor.fetchall.return_value = [
            (1, 'TEST001', 'Tubo PVC', 100),
            (2, 'TEST002', 'Conexão PVC', 50)
        ]
        
        insumos = insumos_manager_with_mock.get_insumos()
        
        assert len(insumos) == 2
        assert insumos[0]['codigo'] == 'TEST001'
        assert insumos[1]['codigo'] == 'TEST002'
    
    def test_get_insumos_with_filter(self, insumos_manager_with_mock, test_db):
        """Testa busca com filtros"""
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('id',), ('codigo',), ('descricao',)]
        mock_cursor.fetchall.return_value = [
            (1, 'TUBO001', 'Tubo PVC 50mm')
        ]
        
        filtros = {
            'codigo': 'TUBO',
            'categoria_id': 1
        }
        
        insumos = insumos_manager_with_mock.get_insumos(filtros)
        
        assert len(insumos) == 1
        assert 'TUBO' in insumos[0]['codigo']
    
    def test_update_insumo_success(self, insumos_manager_with_mock, test_db):
        """Testa atualização bem-sucedida de insumo"""
        mock_cursor = test_db.cursor.return_value
        
        # Mock para verificar se insumo existe e código não duplicado
        mock_cursor.fetchone.side_effect = [
            ('TEST001',),  # Insumo existe
            None,          # Código não duplicado (ou é o mesmo)
            (1,)           # Atualização bem-sucedida
        ]
        
        dados_atualizados = {
            'codigo': 'TEST001_UPDATED',
            'descricao': 'Tubo PVC Atualizado',
            'quantidade_minima': 15
        }
        
        success, message = insumos_manager_with_mock.update_insumo(1, dados_atualizados, 1)
        
        assert success is True
    
    def test_delete_insumo_success(self, insumos_manager_with_mock, test_db):
        """Testa exclusão bem-sucedida de insumo"""
        mock_cursor = test_db.cursor.return_value
        
        # Mock para verificar se insumo existe
        mock_cursor.fetchone.return_value = ('TEST001', 'Tubo PVC')
        
        success, message = insumos_manager_with_mock.delete_insumo(1, 1)
        
        assert success is True
        assert "sucesso" in message.lower()
    
    def test_get_insumo_by_id_found(self, insumos_manager_with_mock, test_db):
        """Testa busca de insumo por ID encontrado"""
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [
            ('id',), ('codigo',), ('descricao',), ('quantidade_atual',)
        ]
        mock_cursor.fetchone.return_value = (1, 'TEST001', 'Tubo PVC', 100)
        
        insumo = insumos_manager_with_mock.get_insumo_by_id(1)
        
        assert insumo is not None
        assert insumo['id'] == 1
        assert insumo['codigo'] == 'TEST001'
    
    def test_get_insumo_by_id_not_found(self, insumos_manager_with_mock, test_db):
        """Testa busca de insumo por ID não encontrado"""
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = None
        
        insumo = insumos_manager_with_mock.get_insumo_by_id(999)
        
        assert insumo is None
    
    def test_ajustar_estoque_entrada(self, insumos_manager_with_mock, test_db):
        """Testa ajuste de estoque - entrada"""
        mock_cursor = test_db.cursor.return_value
        
        # Mock para buscar quantidade atual e atualizar
        mock_cursor.fetchone.side_effect = [
            (100,),  # Quantidade atual
            (1,)     # Atualização bem-sucedida
        ]
        
        success, message = insumos_manager_with_mock.ajustar_estoque(
            insumo_id=1,
            quantidade=50,
            tipo_movimento='entrada',
            motivo='Compra',
            user_id=1
        )
        
        assert success is True
    
    def test_ajustar_estoque_saida_suficiente(self, insumos_manager_with_mock, test_db):
        """Testa ajuste de estoque - saída com quantidade suficiente"""
        mock_cursor = test_db.cursor.return_value
        
        # Mock para quantidade atual suficiente
        mock_cursor.fetchone.side_effect = [
            (100,),  # Quantidade atual
            (1,)     # Atualização bem-sucedida
        ]
        
        success, message = insumos_manager_with_mock.ajustar_estoque(
            insumo_id=1,
            quantidade=30,
            tipo_movimento='saida',
            motivo='Uso em obra',
            user_id=1
        )
        
        assert success is True
    
    def test_ajustar_estoque_saida_insuficiente(self, insumos_manager_with_mock, test_db):
        """Testa ajuste de estoque - saída com quantidade insuficiente"""
        mock_cursor = test_db.cursor.return_value
        
        # Mock para quantidade insuficiente
        mock_cursor.fetchone.return_value = (10,)  # Quantidade atual
        
        success, message = insumos_manager_with_mock.ajustar_estoque(
            insumo_id=1,
            quantidade=50,  # Tentativa de retirar mais que disponível
            tipo_movimento='saida',
            motivo='Uso em obra',
            user_id=1
        )
        
        assert success is False
        assert "insuficiente" in message.lower()
    
    def test_get_dashboard_stats(self, insumos_manager_with_mock, test_db):
        """Testa estatísticas do dashboard"""
        mock_cursor = test_db.cursor.return_value
        
        # Mock para diferentes consultas de estatísticas
        mock_cursor.fetchone.side_effect = [
            (100,),  # Total de insumos
            (15,),   # Insumos com baixo estoque
            (5,),    # Insumos vencendo
            (1500.50,)  # Valor total do estoque
        ]
        
        stats = insumos_manager_with_mock.get_dashboard_stats()
        
        assert 'total_insumos' in stats
        assert 'baixo_estoque' in stats
        assert 'vencendo' in stats
        assert 'valor_total' in stats


@pytest.mark.integration
class TestInsumosIntegrationReal:
    """Testes de integração realísticos para insumos"""
    
    def test_crud_complete_workflow(self, test_db):
        """Testa fluxo CRUD completo"""
        with patch('modules.insumos.db') as mock_db, \
             patch('modules.insumos.auth_manager'):
            
            mock_db.get_connection.return_value = test_db
            from modules.insumos import InsumosManager
            
            manager = InsumosManager()
            mock_cursor = test_db.cursor.return_value
            
            # 1. Criar insumo
            mock_cursor.fetchone.side_effect = [None, (1,)]
            dados = {
                'codigo': 'CRUD001',
                'descricao': 'Item CRUD Teste',
                'categoria_id': 1,
                'unidade': 'UN'
            }
            success, _ = manager.create_insumo(dados, 1)
            assert success is True
            
            # 2. Buscar insumo criado
            mock_cursor.description = [('id',), ('codigo',), ('descricao',)]
            mock_cursor.fetchone.return_value = (1, 'CRUD001', 'Item CRUD Teste')
            insumo = manager.get_insumo_by_id(1)
            assert insumo is not None
            
            # 3. Atualizar insumo
            mock_cursor.fetchone.side_effect = [
                ('CRUD001',), None, (1,)
            ]
            dados_update = {'descricao': 'Item CRUD Atualizado'}
            success, _ = manager.update_insumo(1, dados_update, 1)
            assert success is True
            
            # 4. Ajustar estoque
            mock_cursor.fetchone.side_effect = [(0,), (1,)]
            success, _ = manager.ajustar_estoque(1, 100, 'entrada', 'Estoque inicial', 1)
            assert success is True
            
            # 5. Deletar insumo
            mock_cursor.fetchone.return_value = ('CRUD001', 'Item CRUD')
            success, _ = manager.delete_insumo(1, 1)
            assert success is True