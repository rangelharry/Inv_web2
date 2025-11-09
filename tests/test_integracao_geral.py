"""
Testes de integração geral do sistema
"""

import pytest
from unittest.mock import patch, Mock
from datetime import datetime

@pytest.mark.integration
class TestSistemaIntegracaoCompleta:
    """Testes de integração para workflows completos do sistema"""
    
    def test_workflow_inventario_completo(self, test_db):
        """Teste completo do workflow de inventário"""
        with patch('modules.auth.db') as mock_auth_db, \
             patch('modules.insumos.db') as mock_insumos_db, \
             patch('modules.movimentacoes.db') as mock_mov_db, \
             patch('modules.auth.auth_manager') as mock_auth:
            
            # Setup mocks
            mock_auth_db.get_connection.return_value = test_db
            mock_insumos_db.get_connection.return_value = test_db  
            mock_mov_db.get_connection.return_value = test_db
            
            from modules.auth import AuthenticationManager
            from modules.insumos import InsumosManager
            from modules.movimentacoes import MovimentacoesManager
            
            auth_manager = AuthenticationManager()
            insumos_manager = InsumosManager()
            movimentacoes_manager = MovimentacoesManager()
            
            mock_cursor = test_db.cursor.return_value
            
            # 1. Autenticação de usuário
            hashed_password = auth_manager.hash_password("senha123")
            user_data = [1, "Admin", "admin@test.com", hashed_password, "admin", True]
            mock_cursor.fetchone.return_value = user_data
            
            success, message, user_info = auth_manager.authenticate_user(
                "admin@test.com", "senha123"
            )
            assert success is True
            assert user_info is not None
            
            # 2. Criar insumo
            dados_insumo = {
                'codigo': 'TEST001',
                'descricao': 'Insumo Teste',
                'categoria_id': 1,
                'unidade': 'UN',
                'quantidade_atual': 100,
                'quantidade_minima': 10,
                'fornecedor': 'Fornecedor Teste'
            }
            
            mock_cursor.fetchone.return_value = (1,)  # ID do insumo criado
            success, message = insumos_manager.criar_insumo(dados_insumo, 1)
            assert success is True
            
            # 3. Registrar movimentação
            dados_movimentacao = {
                'tipo_item': 'insumo',
                'item_id': 1,
                'tipo_movimento': 'saida',
                'quantidade': 20,
                'motivo': 'Uso em obra',
                'obra_destino_id': 1
            }
            
            mock_cursor.fetchone.side_effect = [
                (100,),  # quantidade atual
                ('TEST001', 'Insumo Teste')  # dados do item
            ]
            
            success, message = movimentacoes_manager.registrar_movimentacao(dados_movimentacao, 1)
            assert success is True
    
    def test_workflow_equipamentos_completo(self, test_db):
        """Teste completo do workflow de equipamentos"""
        with patch('modules.equipamentos_eletricos.db') as mock_db, \
             patch('modules.equipamentos_eletricos.auth_manager') as mock_auth:
            
            mock_db.get_connection.return_value = test_db
            from modules.equipamentos_eletricos import EquipamentosEletricosManager
            
            manager = EquipamentosEletricosManager()
            mock_cursor = test_db.cursor.return_value
            
            # 1. Criar equipamento
            dados_equipamento = {
                'codigo': 'EQ001',
                'descricao': 'Furadeira Industrial',
                'categoria_id': 1,
                'marca': 'Makita',
                'modelo': 'HP2050',
                'estado': 'novo',
                'localizacao': 'Almoxarifado Central'
            }
            
            mock_cursor.fetchone.return_value = (1,)
            success, _ = manager.criar_equipamento(dados_equipamento, 1)
            assert success is True
            
            # 2. Transferir equipamento
            mock_cursor.fetchone.return_value = ('EQ001', 'Furadeira Industrial', 1, 1)
            success, _ = manager.transferir_equipamento(1, 2, 3, 'Transferência obra', 1)
            assert success is True
            
            # 3. Marcar para manutenção  
            mock_cursor.fetchone.return_value = ('EQ001', 'Furadeira Industrial', 'bom')
            success, _ = manager.marcar_para_manutencao(1, 'Manutenção preventiva', 1)
            assert success is True
    
    def test_workflow_subcontratados_completo(self, test_db):
        """Teste completo do workflow de subcontratados"""
        with patch('modules.gestao_subcontratados.db') as mock_db:
            
            mock_db.get_connection.return_value = test_db
            from modules.gestao_subcontratados import SubcontratadosManager
            
            manager = SubcontratadosManager()
            mock_cursor = test_db.cursor.return_value
            
            # 1. Cadastrar subcontratado
            dados_subcontratado = {
                'razao_social': 'Construtora ABC Ltda',
                'cnpj': '12.345.678/0001-90',
                'categoria': 'Construção Civil'
            }
            
            mock_cursor.fetchone.return_value = (1,)
            success, _ = manager.cadastrar_subcontratado(dados_subcontratado)
            assert success is True
            
            # 2. Criar contrato
            dados_contrato = {
                'subcontratado_id': 1,
                'numero_contrato': 'CONT-001/2024',
                'valor_total': 100000.00,
                'data_inicio': '2024-01-01',
                'data_fim': '2024-12-31'
            }
            
            mock_cursor.fetchone.return_value = (1,)
            success, _ = manager.criar_contrato(dados_contrato)
            assert success is True
            
            # 3. Emprestar equipamento
            dados_emprestimo = {
                'subcontratado_id': 1,
                'equipamento_id': 1,
                'data_emprestimo': datetime.now(),
                'responsavel_retirada': 'João Silva'
            }
            
            mock_cursor.fetchone.side_effect = [
                ('EQ001', 'Furadeira', 'disponivel'),
                (1,)
            ]
            
            success, _ = manager.emprestar_equipamento(dados_emprestimo)
            assert success is True
    
    def test_workflow_financeiro_completo(self, test_db):
        """Teste completo do workflow financeiro"""
        with patch('modules.gestao_financeira.db') as mock_db:
            
            mock_db.get_connection.return_value = test_db
            from modules.gestao_financeira import GestaoFinanceiraManager
            
            manager = GestaoFinanceiraManager()
            mock_cursor = test_db.cursor.return_value
            
            # 1. Registrar receita da obra
            dados_receita = {
                'descricao': 'Medição Mensal - Obra A',
                'categoria': 'medicoes',
                'valor': 150000.00,
                'obra_id': 1,
                'cliente': 'Cliente Premium'
            }
            
            mock_cursor.fetchone.return_value = (1,)
            success, _ = manager.registrar_receita(dados_receita)
            assert success is True
            
            # 2. Registrar despesas
            despesas = [
                {'descricao': 'Materiais', 'valor': 50000.00, 'categoria': 'materiais'},
                {'descricao': 'Mão de obra', 'valor': 60000.00, 'categoria': 'mao_obra'},
                {'descricao': 'Equipamentos', 'valor': 20000.00, 'categoria': 'equipamentos'}
            ]
            
            for despesa in despesas:
                mock_cursor.fetchone.return_value = (1,)
                success, _ = manager.registrar_despesa(despesa)
                assert success is True
            
            # 3. Calcular indicadores
            mock_cursor.fetchone.side_effect = [
                (150000.00,),  # receita total
                (130000.00,),  # despesas totais
            ]
            
            roi = manager.calcular_roi_obra(1)
            assert roi > 0  # ROI positivo esperado


@pytest.mark.slow
class TestPerformanceIntegracao:
    """Testes de performance para operações críticas"""
    
    def test_performance_busca_insumos(self, test_db):
        """Teste de performance para busca de insumos com grandes volumes"""
        with patch('modules.insumos.db') as mock_db:
            mock_db.get_connection.return_value = test_db
            from modules.insumos import InsumosManager
            
            manager = InsumosManager()
            mock_cursor = test_db.cursor.return_value
            
            # Simular grande quantidade de insumos
            large_dataset = [(i, f'INS{i:04d}', f'Insumo {i}') for i in range(1000)]
            mock_cursor.description = [('id',), ('codigo',), ('descricao',)]
            mock_cursor.fetchall.return_value = large_dataset
            
            import time
            start_time = time.time()
            
            insumos = manager.buscar_insumos()
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            assert len(insumos) == 1000
            assert execution_time < 1.0  # Deve executar em menos de 1 segundo
    
    def test_performance_movimentacoes_bulk(self, test_db):
        """Teste de performance para movimentações em lote"""
        with patch('modules.movimentacoes.db') as mock_db, \
             patch('modules.movimentacoes.auth_manager'):
            
            mock_db.get_connection.return_value = test_db
            from modules.movimentacoes import MovimentacoesManager
            
            manager = MovimentacoesManager()
            mock_cursor = test_db.cursor.return_value
            
            # Simular processamento de múltiplas movimentações
            mock_cursor.fetchone.side_effect = [
                (1000,), ('TEST001', 'Item Teste')
            ] * 100  # 100 movimentações
            
            import time
            start_time = time.time()
            
            # Simular 100 movimentações
            for i in range(100):
                dados = {
                    'tipo_item': 'insumo',
                    'item_id': 1,
                    'tipo_movimento': 'entrada',
                    'quantidade': 10,
                    'motivo': f'Movimentação {i}'
                }
                
                success, _ = manager.registrar_movimentacao(dados, 1)
                assert success is True
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            assert execution_time < 5.0  # Deve processar 100 movimentações em menos de 5s


@pytest.mark.database
class TestIntegracaoBancoDados:
    """Testes de integração específicos para banco de dados (mocks)"""
    
    def test_transacao_completa_rollback(self, test_db):
        """Teste de rollback em transação com erro"""
        with patch('modules.insumos.db') as mock_db, \
             patch('modules.insumos.auth_manager'):
            
            mock_db.get_connection.return_value = test_db
            from modules.insumos import InsumosManager
            
            manager = InsumosManager()
            mock_cursor = test_db.cursor.return_value
            
            # Simular erro durante execução
            mock_cursor.execute.side_effect = Exception("Constraint violation")
            
            dados_insumo = {
                'codigo': 'ERR001',
                'descricao': 'Item com erro'
            }
            
            success, message = manager.criar_insumo(dados_insumo, 1)
            
            assert success is False
            assert "erro" in message.lower()
            # Verificar se rollback foi chamado
            assert test_db.rollback.called
    
    def test_conexao_multiplas_operacoes(self, test_db):
        """Teste de múltiplas operações com mesma conexão"""
        with patch('modules.auth.db') as mock_db:
            mock_db.get_connection.return_value = test_db
            from modules.auth import AuthenticationManager
            
            auth_manager = AuthenticationManager()
            mock_cursor = test_db.cursor.return_value
            
            # Múltiplas operações sequenciais
            operacoes = [
                ('criar_usuario', ('João', 'joao@test.com', 'Senha123@')),
                ('criar_usuario', ('Maria', 'maria@test.com', 'Senha456@')),
                ('criar_usuario', ('Pedro', 'pedro@test.com', 'Senha789@'))
            ]
            
            mock_cursor.fetchone.return_value = (1,)
            
            for operacao, params in operacoes:
                if operacao == 'criar_usuario':
                    success, _ = auth_manager.create_user(*params)
                    assert success is True
            
            # Verificar se a conexão foi reutilizada
            assert mock_db.get_connection.call_count >= 3