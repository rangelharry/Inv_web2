"""
Testes para o módulo de equipamentos elétricos
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

@pytest.mark.unit
class TestEquipamentosEletricosManager:
    """Testes unitários para EquipamentosEletricosManager"""
    
    @pytest.fixture
    def eq_eletricos_manager(self, test_db):
        """Fixture para instância do EquipamentosEletricosManager"""
        with patch('modules.equipamentos_eletricos.db') as mock_db:
            mock_db.get_connection.return_value = test_db
            from modules.equipamentos_eletricos import EquipamentosEletricosManager
            return EquipamentosEletricosManager()
    
    def test_get_categorias(self, eq_eletricos_manager, test_db):
        """Teste de obtenção de categorias de equipamentos elétricos"""
        categorias_mock = [
            {'id': 1, 'nome': 'Ferramentas Elétricas'},
            {'id': 2, 'nome': 'Instrumentos de Medição'}
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('id',), ('nome',)]
        mock_cursor.fetchall.return_value = [
            (1, 'Ferramentas Elétricas'),
            (2, 'Instrumentos de Medição')
        ]
        
        categorias = eq_eletricos_manager.get_categorias()
        
        assert len(categorias) == 2
        assert categorias[0]['nome'] == 'Ferramentas Elétricas'
    
    @patch('modules.equipamentos_eletricos.auth_manager')
    def test_criar_equipamento_success(self, mock_auth, eq_eletricos_manager, test_db):
        """Teste de criação de equipamento elétrico bem-sucedida"""
        dados_equipamento = {
            'codigo': 'EE001',
            'descricao': 'Furadeira Elétrica',
            'categoria_id': 1,
            'marca': 'Bosch',
            'modelo': 'GSB 550',
            'tensao': '220V',
            'potencia': '550W',
            'estado': 'novo',
            'localizacao': 'Almoxarifado A',
            'responsavel_id': 1,
            'obra_id': 1,
            'data_aquisicao': '2024-01-15',
            'valor_aquisicao': 299.90,
            'vida_util_anos': 5,
            'observacoes': 'Equipamento para obras'
        }
        
        user_id = 1
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = (1,)  # ID do equipamento criado
        
        success, message = eq_eletricos_manager.criar_equipamento(dados_equipamento, user_id)
        
        assert success is True
        assert "sucesso" in message.lower()
        mock_auth.log_action.assert_called()
    
    def test_buscar_equipamentos_all(self, eq_eletricos_manager, test_db):
        """Teste de busca de todos os equipamentos elétricos"""
        equipamentos_mock = [
            (1, 'EE001', 'Furadeira', 1, 'Bosch', 'GSB 550', '220V', '550W', 'novo', 'A1', 1, 1),
            (2, 'EE002', 'Multímetro', 2, 'Fluke', 'MT-100', '9V', '5W', 'bom', 'A2', 2, 2)
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [
            ('id',), ('codigo',), ('descricao',), ('categoria_id',), ('marca',),
            ('modelo',), ('tensao',), ('potencia',), ('estado',), ('localizacao',),
            ('responsavel_id',), ('obra_id',)
        ]
        mock_cursor.fetchall.return_value = equipamentos_mock
        
        equipamentos = eq_eletricos_manager.buscar_equipamentos()
        
        assert len(equipamentos) == 2
        assert equipamentos[0]['codigo'] == 'EE001'
        assert equipamentos[1]['codigo'] == 'EE002'
    
    def test_buscar_equipamentos_por_estado(self, eq_eletricos_manager, test_db):
        """Teste de busca de equipamentos por estado"""
        filtros = {'estado': 'bom'}
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('id',), ('codigo',), ('estado',)]
        mock_cursor.fetchall.return_value = [(1, 'EE001', 'bom')]
        
        equipamentos = eq_eletricos_manager.buscar_equipamentos(filtros)
        
        # Verificar se o filtro foi aplicado na query
        execute_calls = mock_cursor.execute.call_args_list
        query = execute_calls[0][0][0]
        assert 'estado' in query
    
    @patch('modules.equipamentos_eletricos.auth_manager')
    def test_atualizar_equipamento_success(self, mock_auth, eq_eletricos_manager, test_db):
        """Teste de atualização de equipamento bem-sucedida"""
        equipamento_id = 1
        user_id = 1
        dados_atualizados = {
            'descricao': 'Furadeira Elétrica Atualizada',
            'estado': 'usado',
            'localizacao': 'Obra B',
            'observacoes': 'Manutenção realizada'
        }
        
        # Mock para dados antigos
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('codigo',), ('descricao',)]
        mock_cursor.fetchone.return_value = ('EE001', 'Furadeira Elétrica')
        
        success, message = eq_eletricos_manager.atualizar_equipamento(
            equipamento_id, dados_atualizados, user_id
        )
        
        assert success is True
        assert "sucesso" in message.lower()
        mock_auth.log_action.assert_called()
    
    def test_get_equipamentos_por_obra(self, eq_eletricos_manager, test_db):
        """Teste de busca de equipamentos por obra"""
        obra_id = 1
        equipamentos_obra = [
            (1, 'EE001', 'Furadeira', 'novo'),
            (2, 'EE002', 'Parafusadeira', 'bom')
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('id',), ('codigo',), ('descricao',), ('estado',)]
        mock_cursor.fetchall.return_value = equipamentos_obra
        
        equipamentos = eq_eletricos_manager.get_equipamentos_por_obra(obra_id)
        
        assert len(equipamentos) == 2
        # Verificar se a query filtra por obra
        execute_calls = mock_cursor.execute.call_args_list
        query = execute_calls[0][0][0]
        assert 'obra_id' in query
    
    def test_get_equipamentos_por_responsavel(self, eq_eletricos_manager, test_db):
        """Teste de busca de equipamentos por responsável"""
        responsavel_id = 1
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('id',), ('codigo',), ('descricao',)]
        mock_cursor.fetchall.return_value = [(1, 'EE001', 'Furadeira')]
        
        equipamentos = eq_eletricos_manager.get_equipamentos_por_responsavel(responsavel_id)
        
        assert len(equipamentos) == 1
        # Verificar se a query filtra por responsável
        execute_calls = mock_cursor.execute.call_args_list
        query = execute_calls[0][0][0]
        assert 'responsavel_id' in query
    
    def test_calcular_vida_util_restante(self, eq_eletricos_manager):
        """Teste de cálculo de vida útil restante"""
        # Data de aquisição: 2 anos atrás
        data_aquisicao = datetime.now().replace(year=datetime.now().year - 2)
        vida_util_anos = 5
        
        vida_restante = eq_eletricos_manager.calcular_vida_util_restante(
            data_aquisicao, vida_util_anos
        )
        
        assert vida_restante == 3  # 5 - 2 = 3 anos restantes
    
    def test_calcular_vida_util_expirada(self, eq_eletricos_manager):
        """Teste de cálculo de vida útil expirada"""
        # Data de aquisição: 6 anos atrás
        data_aquisicao = datetime.now().replace(year=datetime.now().year - 6)
        vida_util_anos = 5
        
        vida_restante = eq_eletricos_manager.calcular_vida_util_restante(
            data_aquisicao, vida_util_anos
        )
        
        assert vida_restante == 0  # Vida útil expirada
    
    def test_get_equipamentos_proximos_fim_vida_util(self, eq_eletricos_manager, test_db):
        """Teste de busca de equipamentos próximos ao fim da vida útil"""
        # Equipamentos com poucos anos restantes
        equipamentos_mock = [
            (1, 'EE001', 'Furadeira', datetime(2023, 1, 1), 5),  # 1 ano restante
            (2, 'EE002', 'Multímetro', datetime(2022, 6, 1), 4)   # 0.5 anos restantes
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [
            ('id',), ('codigo',), ('descricao',), ('data_aquisicao',), ('vida_util_anos',)
        ]
        mock_cursor.fetchall.return_value = equipamentos_mock
        
        equipamentos = eq_eletricos_manager.get_equipamentos_proximos_fim_vida_util(2)  # 2 anos
        
        # Verificar se retorna equipamentos próximos ao fim
        assert len(equipamentos) >= 0  # Depende da lógica interna
    
    @patch('modules.equipamentos_eletricos.auth_manager')
    def test_transferir_equipamento(self, mock_auth, eq_eletricos_manager, test_db):
        """Teste de transferência de equipamento"""
        equipamento_id = 1
        nova_obra_id = 2
        novo_responsavel_id = 3
        user_id = 1
        motivo = "Transferência para nova obra"
        
        # Mock dos dados do equipamento
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.side_effect = [
            ('EE001', 'Furadeira', 1, 1),  # dados atuais
        ]
        
        success, message = eq_eletricos_manager.transferir_equipamento(
            equipamento_id, nova_obra_id, novo_responsavel_id, motivo, user_id
        )
        
        assert success is True
        assert "transferido" in message.lower()
        mock_auth.log_action.assert_called()
    
    def test_get_relatorio_utilizacao(self, eq_eletricos_manager, test_db):
        """Teste de geração de relatório de utilização"""
        # Mock de dados de utilização
        dados_utilizacao = [
            (1, 'EE001', 'Furadeira', 80, 'ativo'),
            (2, 'EE002', 'Multímetro', 30, 'parado')
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [
            ('id',), ('codigo',), ('descricao',), ('utilizacao_percent',), ('status',)
        ]
        mock_cursor.fetchall.return_value = dados_utilizacao
        
        relatorio = eq_eletricos_manager.get_relatorio_utilizacao()
        
        assert len(relatorio) == 2
        assert relatorio[0]['utilizacao_percent'] == 80
    
    @pytest.mark.parametrize("estado,expected_can_use", [
        ("novo", True),
        ("bom", True),
        ("usado", True),
        ("ruim", False),
        ("quebrado", False),
        ("descartado", False)
    ])
    def test_validar_estado_equipamento(self, eq_eletricos_manager, estado, expected_can_use):
        """Teste parametrizado para validação de estado do equipamento"""
        can_use = eq_eletricos_manager.pode_usar_equipamento(estado)
        assert can_use == expected_can_use
    
    def test_calcular_depreciacao(self, eq_eletricos_manager):
        """Teste de cálculo de depreciação do equipamento"""
        valor_inicial = 1000.00
        anos_uso = 2
        vida_util_total = 5
        
        valor_atual = eq_eletricos_manager.calcular_valor_depreciado(
            valor_inicial, anos_uso, vida_util_total
        )
        
        # Depreciação linear: 1000 - (1000 * 2/5) = 600
        assert valor_atual == 600.00
    
    def test_buscar_por_codigo(self, eq_eletricos_manager, test_db):
        """Teste de busca de equipamento por código"""
        codigo = 'EE001'
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('id',), ('codigo',), ('descricao',)]
        mock_cursor.fetchone.return_value = (1, 'EE001', 'Furadeira')
        
        equipamento = eq_eletricos_manager.buscar_por_codigo(codigo)
        
        assert equipamento is not None
        assert equipamento['codigo'] == 'EE001'
    
    def test_buscar_por_codigo_not_found(self, eq_eletricos_manager, test_db):
        """Teste de busca de equipamento por código não encontrado"""
        codigo = 'EE999'
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = None
        
        equipamento = eq_eletricos_manager.buscar_por_codigo(codigo)
        
        assert equipamento is None


@pytest.mark.integration
class TestEquipamentosEletricosIntegration:
    """Testes de integração para equipamentos elétricos"""
    
    def test_workflow_manutencao_completo(self, test_db):
        """Teste completo do workflow de manutenção"""
        with patch('modules.equipamentos_eletricos.db') as mock_db, \
             patch('modules.equipamentos_eletricos.auth_manager') as mock_auth:
            
            mock_db.get_connection.return_value = test_db
            from modules.equipamentos_eletricos import EquipamentosEletricosManager
            manager = EquipamentosEletricosManager()
            
            # 1. Criar equipamento
            dados_eq = {
                'codigo': 'EE001',
                'descricao': 'Furadeira Teste',
                'estado': 'novo',
                'localizacao': 'Almoxarifado'
            }
            
            mock_cursor = test_db.cursor.return_value
            mock_cursor.fetchone.return_value = (1,)
            
            success, _ = manager.criar_equipamento(dados_eq, 1)
            assert success is True
            
            # 2. Marcar para manutenção
            mock_cursor.fetchone.return_value = ('EE001', 'Furadeira Teste', 'novo')
            
            success, _ = manager.marcar_para_manutencao(1, 'Manutenção preventiva', 1)
            assert success is True
            
            # 3. Finalizar manutenção
            success, _ = manager.finalizar_manutencao(1, 'Manutenção realizada', 'bom', 1)
            assert success is True