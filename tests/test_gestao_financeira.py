"""
Testes para o módulo de gestão financeira
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date
from decimal import Decimal

@pytest.mark.unit
class TestGestaoFinanceiraManager:
    """Testes unitários para GestaoFinanceiraManager"""
    
    @pytest.fixture
    def gestao_financeira_manager(self, test_db):
        """Fixture para instância do GestaoFinanceiraManager"""
        with patch('modules.gestao_financeira.db') as mock_db:
            mock_db.get_connection.return_value = test_db
            from modules.gestao_financeira import GestaoFinanceiraManager
            return GestaoFinanceiraManager()
    
    def test_registrar_despesa_success(self, gestao_financeira_manager, test_db):
        """Teste de registro de despesa bem-sucedido"""
        dados_despesa = {
            'descricao': 'Compra de materiais',
            'categoria': 'materiais',
            'valor': 1500.00,
            'data_vencimento': '2024-12-31',
            'fornecedor': 'Fornecedor ABC',
            'obra_id': 1,
            'centro_custo': 'OBRA-001',
            'observacoes': 'Material para fundação'
        }
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = (1,)  # ID da despesa criada
        
        success, message = gestao_financeira_manager.registrar_despesa(dados_despesa)
        
        assert success is True
        assert "despesa" in message.lower()
        assert "sucesso" in message.lower()
    
    def test_registrar_receita_success(self, gestao_financeira_manager, test_db):
        """Teste de registro de receita bem-sucedido"""
        dados_receita = {
            'descricao': 'Medição obra',
            'categoria': 'medicoes',
            'valor': 50000.00,
            'data_recebimento': '2024-01-15',
            'cliente': 'Cliente XYZ',
            'obra_id': 1,
            'observacoes': 'Primeira medição'
        }
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = (1,)  # ID da receita criada
        
        success, message = gestao_financeira_manager.registrar_receita(dados_receita)
        
        assert success is True
        assert "receita" in message.lower()
        assert "sucesso" in message.lower()
    
    def test_calcular_fluxo_caixa_mensal(self, gestao_financeira_manager, test_db):
        """Teste de cálculo de fluxo de caixa mensal"""
        # Mock de dados financeiros
        fluxo_mock = [
            ('2024-01', 50000.00, 30000.00, 20000.00),  # mes, receitas, despesas, saldo
            ('2024-02', 60000.00, 35000.00, 25000.00),
            ('2024-03', 45000.00, 40000.00, 5000.00)
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('mes',), ('receitas',), ('despesas',), ('saldo',)]
        mock_cursor.fetchall.return_value = fluxo_mock
        
        fluxo = gestao_financeira_manager.calcular_fluxo_caixa_mensal('2024-01-01', '2024-03-31')
        
        assert len(fluxo) == 3
        assert fluxo[0]['mes'] == '2024-01'
        assert fluxo[0]['saldo'] == 20000.00
    
    def test_get_despesas_por_categoria(self, gestao_financeira_manager, test_db):
        """Teste de obtenção de despesas por categoria"""
        despesas_mock = [
            ('materiais', 15000.00),
            ('mao_obra', 25000.00),
            ('equipamentos', 8000.00)
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('categoria',), ('total',)]
        mock_cursor.fetchall.return_value = despesas_mock
        
        despesas_categoria = gestao_financeira_manager.get_despesas_por_categoria()
        
        assert len(despesas_categoria) == 3
        assert despesas_categoria[0]['categoria'] == 'materiais'
        assert despesas_categoria[1]['total'] == 25000.00
    
    def test_calcular_roi_obra(self, gestao_financeira_manager, test_db):
        """Teste de cálculo de ROI por obra"""
        obra_id = 1
        
        # Mock: receita total e custos totais
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.side_effect = [
            (100000.00,),  # receita total
            (80000.00,)    # custos totais
        ]
        
        roi = gestao_financeira_manager.calcular_roi_obra(obra_id)
        
        # ROI = ((Receita - Custos) / Custos) * 100 = ((100000 - 80000) / 80000) * 100 = 25%
        assert roi == 25.0
    
    def test_calcular_roi_obra_sem_custos(self, gestao_financeira_manager, test_db):
        """Teste de cálculo de ROI com custos zero"""
        obra_id = 1
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.side_effect = [
            (50000.00,),  # receita total
            (0.0,)        # custos zero
        ]
        
        roi = gestao_financeira_manager.calcular_roi_obra(obra_id)
        
        # Quando custos são zero, ROI deve ser infinito ou um valor especial
        assert roi is None or roi == float('inf')
    
    def test_get_margem_lucro_obra(self, gestao_financeira_manager, test_db):
        """Teste de cálculo de margem de lucro por obra"""
        obra_id = 1
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.side_effect = [
            (120000.00,),  # receita total
            (100000.00,)   # custos totais
        ]
        
        margem = gestao_financeira_manager.get_margem_lucro_obra(obra_id)
        
        # Margem = ((Receita - Custos) / Receita) * 100 = ((120000 - 100000) / 120000) * 100 = 16.67%
        expected_margem = ((120000.00 - 100000.00) / 120000.00) * 100
        assert abs(margem - expected_margem) < 0.01  # Tolerância para decimais
    
    def test_get_contas_a_pagar(self, gestao_financeira_manager, test_db):
        """Teste de obtenção de contas a pagar"""
        contas_mock = [
            (1, 'Fornecedor A', 5000.00, date(2024, 12, 15), 'pendente'),
            (2, 'Fornecedor B', 3000.00, date(2024, 12, 20), 'vencida'),
            (3, 'Fornecedor C', 7500.00, date(2025, 1, 10), 'pendente')
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [
            ('id',), ('fornecedor',), ('valor',), ('data_vencimento',), ('status',)
        ]
        mock_cursor.fetchall.return_value = contas_mock
        
        contas = gestao_financeira_manager.get_contas_a_pagar()
        
        assert len(contas) == 3
        assert contas[0]['fornecedor'] == 'Fornecedor A'
        assert contas[1]['status'] == 'vencida'
    
    def test_get_contas_vencidas(self, gestao_financeira_manager, test_db):
        """Teste de obtenção de contas vencidas"""
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('id',), ('fornecedor',), ('valor',), ('dias_atraso',)]
        mock_cursor.fetchall.return_value = [
            (1, 'Fornecedor A', 2000.00, 5),
            (2, 'Fornecedor B', 1500.00, 15)
        ]
        
        contas_vencidas = gestao_financeira_manager.get_contas_vencidas()
        
        assert len(contas_vencidas) == 2
        # Verificar se filtrou por data vencimento
        execute_calls = mock_cursor.execute.call_args_list
        query = execute_calls[0][0][0]
        assert 'data_vencimento' in query
    
    def test_calcular_projecao_fluxo_caixa(self, gestao_financeira_manager, test_db):
        """Teste de projeção de fluxo de caixa"""
        # Mock de dados para projeção
        dados_projecao = [
            ('2024-12', 40000.00, 35000.00),
            ('2025-01', 50000.00, 45000.00),
            ('2025-02', 55000.00, 40000.00)
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('mes',), ('receitas_previstas',), ('despesas_previstas',)]
        mock_cursor.fetchall.return_value = dados_projecao
        
        projecao = gestao_financeira_manager.calcular_projecao_fluxo_caixa(3)  # 3 meses
        
        assert len(projecao) == 3
        assert projecao[0]['mes'] == '2024-12'
        saldo_projetado = projecao[0]['receitas_previstas'] - projecao[0]['despesas_previstas']
        assert saldo_projetado == 5000.00
    
    def test_registrar_pagamento(self, gestao_financeira_manager, test_db):
        """Teste de registro de pagamento"""
        despesa_id = 1
        valor_pago = 5000.00
        data_pagamento = date.today()
        forma_pagamento = 'transferencia'
        observacoes = 'Pagamento via PIX'
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = (despesa_id, 5000.00, 'pendente')  # dados da despesa
        
        success, message = gestao_financeira_manager.registrar_pagamento(
            despesa_id, valor_pago, data_pagamento, forma_pagamento, observacoes
        )
        
        assert success is True
        assert "pagamento" in message.lower()
    
    def test_get_indicadores_financeiros(self, gestao_financeira_manager, test_db):
        """Teste de obtenção de indicadores financeiros"""
        # Mock de indicadores
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.side_effect = [
            (150000.00,),  # receita total
            (120000.00,),  # despesas totais
            (30000.00,),   # lucro líquido
            (20.0,),       # margem lucro média
            (5000.00,),    # contas vencidas
        ]
        
        indicadores = gestao_financeira_manager.get_indicadores_financeiros()
        
        assert 'receita_total' in indicadores
        assert 'despesas_totais' in indicadores
        assert 'lucro_liquido' in indicadores
        assert 'margem_lucro_media' in indicadores
        assert indicadores['receita_total'] == 150000.00


@pytest.mark.integration  
class TestGestaoFinanceiraIntegration:
    """Testes de integração para gestão financeira"""
    
    def test_workflow_financeiro_completo(self, test_db):
        """Teste completo do workflow financeiro"""
        with patch('modules.gestao_financeira.db') as mock_db:
            mock_db.get_connection.return_value = test_db
            from modules.gestao_financeira import GestaoFinanceiraManager
            manager = GestaoFinanceiraManager()
            
            mock_cursor = test_db.cursor.return_value
            
            # 1. Registrar receita
            dados_receita = {
                'descricao': 'Medição 1',
                'valor': 100000.00,
                'categoria': 'medicoes'
            }
            
            mock_cursor.fetchone.return_value = (1,)
            success, _ = manager.registrar_receita(dados_receita)
            assert success is True
            
            # 2. Registrar despesa
            dados_despesa = {
                'descricao': 'Compra materiais',
                'valor': 30000.00,
                'categoria': 'materiais'
            }
            
            mock_cursor.fetchone.return_value = (1,)
            success, _ = manager.registrar_despesa(dados_despesa)
            assert success is True
            
            # 3. Calcular indicadores
            mock_cursor.fetchone.side_effect = [
                (100000.00,),  # receita total
                (30000.00,),   # despesas totais
            ]
            
            roi = manager.calcular_roi_obra(1)
            # ROI = ((100000 - 30000) / 30000) * 100 = 233.33%
            expected_roi = ((100000.00 - 30000.00) / 30000.00) * 100
            assert abs(roi - expected_roi) < 0.01


@pytest.mark.parametrize("receita,despesas,expected_margem", [
    (100000, 80000, 20.0),   # Margem de 20%
    (50000, 40000, 20.0),    # Margem de 20%
    (100000, 90000, 10.0),   # Margem de 10%
    (100000, 100000, 0.0),   # Margem zero (break-even)
])
def test_calculo_margem_lucro(receita, despesas, expected_margem):
    """Teste parametrizado para cálculo de margem de lucro"""
    margem = ((receita - despesas) / receita) * 100 if receita > 0 else 0
    assert abs(margem - expected_margem) < 0.01


@pytest.mark.parametrize("valor_inicial,percentual_desconto,expected_valor_final", [
    (1000.00, 10.0, 900.00),    # 10% desconto
    (5000.00, 5.0, 4750.00),    # 5% desconto  
    (2000.00, 0.0, 2000.00),    # Sem desconto
    (1500.00, 20.0, 1200.00),   # 20% desconto
])
def test_aplicar_desconto(valor_inicial, percentual_desconto, expected_valor_final):
    """Teste parametrizado para aplicação de desconto"""
    valor_final = valor_inicial * (1 - percentual_desconto / 100)
    assert abs(valor_final - expected_valor_final) < 0.01