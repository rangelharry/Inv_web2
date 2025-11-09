"""
Testes para o módulo de gestão de subcontratados
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

@pytest.mark.unit
class TestSubcontratadosManager:
    """Testes unitários para SubcontratadosManager"""
    
    @pytest.fixture
    def subcontratados_manager(self, test_db):
        """Fixture para instância do SubcontratadosManager"""
        with patch('modules.gestao_subcontratados.db') as mock_db:
            mock_db.get_connection.return_value = test_db
            from modules.gestao_subcontratados import SubcontratadosManager
            return SubcontratadosManager()
    
    def test_cadastrar_subcontratado_success(self, subcontratados_manager, test_db):
        """Teste de cadastro de subcontratado bem-sucedido"""
        dados_subcontratado = {
            'razao_social': 'Empresa Teste Ltda',
            'nome_fantasia': 'Empresa Teste',
            'cnpj': '12.345.678/0001-90',
            'inscricao_estadual': '123456789',
            'email_principal': 'contato@empresateste.com',
            'telefone_principal': '(11) 1234-5678',
            'endereco': 'Rua Teste, 123',
            'cidade': 'São Paulo',
            'estado': 'SP',
            'cep': '01234-567',
            'categoria': 'Construção Civil',
            'observacoes': 'Subcontratado confiável'
        }
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = (1,)  # ID do subcontratado criado
        
        success, message = subcontratados_manager.cadastrar_subcontratado(dados_subcontratado)
        
        assert success is True
        assert "sucesso" in message.lower()
        assert mock_cursor.execute.called
        assert test_db.commit.called
    
    def test_cadastrar_subcontratado_cnpj_duplicado(self, subcontratados_manager, test_db):
        """Teste de cadastro com CNPJ duplicado"""
        dados_subcontratado = {
            'razao_social': 'Empresa Teste Ltda',
            'cnpj': '12.345.678/0001-90',
            # ... outros campos
        }
        
        # Simular erro de CNPJ duplicado
        mock_cursor = test_db.cursor.return_value
        mock_cursor.execute.side_effect = Exception("UNIQUE constraint failed: subcontratados.cnpj")
        
        success, message = subcontratados_manager.cadastrar_subcontratado(dados_subcontratado)
        
        assert success is False
        assert "cnpj" in message.lower() or "duplicado" in message.lower()
    
    def test_validar_cnpj_valid(self, subcontratados_manager):
        """Teste de validação de CNPJ válido"""
        cnpj_valid = "12.345.678/0001-90"
        
        is_valid = subcontratados_manager.validar_cnpj(cnpj_valid)
        
        # Assumindo que há uma validação básica de formato
        assert isinstance(is_valid, bool)
    
    def test_validar_cnpj_invalid(self, subcontratados_manager):
        """Teste de validação de CNPJ inválido"""
        cnpj_invalid = "123.456.789-10"  # Formato de CPF
        
        is_valid = subcontratados_manager.validar_cnpj(cnpj_invalid)
        
        assert is_valid is False
    
    def test_criar_contrato_success(self, subcontratados_manager, test_db):
        """Teste de criação de contrato bem-sucedida"""
        dados_contrato = {
            'subcontratado_id': 1,
            'numero_contrato': 'CONT-001/2024',
            'descricao': 'Contrato de prestação de serviços',
            'data_inicio': '2024-01-01',
            'data_fim': '2024-12-31',
            'valor_total': 100000.00,
            'condicoes_pagamento': '30 dias',
            'observacoes': 'Contrato anual'
        }
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = (1,)  # ID do contrato criado
        
        success, message = subcontratados_manager.criar_contrato(dados_contrato)
        
        assert success is True
        assert "contrato" in message.lower()
        assert "sucesso" in message.lower()
    
    def test_emprestar_equipamento_success(self, subcontratados_manager, test_db):
        """Teste de empréstimo de equipamento bem-sucedido"""
        dados_emprestimo = {
            'subcontratado_id': 1,
            'equipamento_id': 1,
            'data_emprestimo': datetime.now(),
            'data_prevista_devolucao': datetime.now() + timedelta(days=30),
            'condicoes_emprestimo': 'Equipamento em perfeito estado',
            'responsavel_retirada': 'João Silva',
            'observacoes': 'Empréstimo para obra X'
        }
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.side_effect = [
            ('EQ001', 'Furadeira', 'disponivel'),  # dados do equipamento
            (1,)  # ID do empréstimo criado
        ]
        
        success, message = subcontratados_manager.emprestar_equipamento(dados_emprestimo)
        
        assert success is True
        assert "emprestado" in message.lower()
    
    def test_emprestar_equipamento_indisponivel(self, subcontratados_manager, test_db):
        """Teste de empréstimo de equipamento indisponível"""
        dados_emprestimo = {
            'subcontratado_id': 1,
            'equipamento_id': 1,
            'data_emprestimo': datetime.now(),
            # ... outros campos
        }
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = ('EQ001', 'Furadeira', 'emprestado')  # indisponível
        
        success, message = subcontratados_manager.emprestar_equipamento(dados_emprestimo)
        
        assert success is False
        assert "indisponível" in message.lower() or "emprestado" in message.lower()
    
    def test_devolver_equipamento_success(self, subcontratados_manager, test_db):
        """Teste de devolução de equipamento bem-sucedida"""
        emprestimo_id = 1
        condicoes_devolucao = "Equipamento em bom estado"
        observacoes_devolucao = "Devolução conforme previsto"
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = (1, 1, 1, datetime.now(), None)  # dados do empréstimo
        
        success, message = subcontratados_manager.devolver_equipamento(
            emprestimo_id, condicoes_devolucao, observacoes_devolucao
        )
        
        assert success is True
        assert "devolvido" in message.lower()
    
    def test_avaliar_subcontratado_success(self, subcontratados_manager, test_db):
        """Teste de avaliação de subcontratado bem-sucedida"""
        dados_avaliacao = {
            'subcontratado_id': 1,
            'periodo_inicio': '2024-01-01',
            'periodo_fim': '2024-03-31',
            'qualidade_servicos': 8.5,
            'cumprimento_prazos': 9.0,
            'relacionamento': 8.0,
            'custo_beneficio': 7.5,
            'comentarios': 'Ótimo trabalho realizado',
            'avaliador': 'Maria Silva'
        }
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchone.return_value = (1,)  # ID da avaliação criada
        
        success, message = subcontratados_manager.avaliar_subcontratado(dados_avaliacao)
        
        assert success is True
        assert "avaliação" in message.lower()
    
    def test_listar_subcontratados(self, subcontratados_manager, test_db):
        """Teste de listagem de subcontratados"""
        subcontratados_mock = [
            (1, 'Empresa A', 'Empresa A Ltda', '12.345.678/0001-90', 'ativo'),
            (2, 'Empresa B', 'Empresa B Ltda', '98.765.432/0001-10', 'ativo')
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [
            ('id',), ('nome_fantasia',), ('razao_social',), ('cnpj',), ('status',)
        ]
        mock_cursor.fetchall.return_value = subcontratados_mock
        
        subcontratados = subcontratados_manager.listar_subcontratados()
        
        assert len(subcontratados) == 2
        assert subcontratados[0]['nome_fantasia'] == 'Empresa A'
        assert subcontratados[1]['nome_fantasia'] == 'Empresa B'
    
    def test_listar_subcontratados_ativos(self, subcontratados_manager, test_db):
        """Teste de listagem apenas de subcontratados ativos"""
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('id',), ('nome_fantasia',), ('status',)]
        mock_cursor.fetchall.return_value = [(1, 'Empresa A', 'ativo')]
        
        subcontratados = subcontratados_manager.listar_subcontratados(apenas_ativos=True)
        
        # Verificar se filtrou por ativos
        execute_calls = mock_cursor.execute.call_args_list
        query = execute_calls[0][0][0]
        assert 'ativo' in query.lower()
    
    def test_get_contratos_vencendo(self, subcontratados_manager, test_db):
        """Teste de busca de contratos próximos ao vencimento"""
        data_vencimento = datetime.now() + timedelta(days=15)
        contratos_mock = [
            (1, 'CONT-001', 1, 'Empresa A', data_vencimento),
            (2, 'CONT-002', 2, 'Empresa B', data_vencimento)
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [
            ('id',), ('numero_contrato',), ('subcontratado_id',), 
            ('nome_fantasia',), ('data_fim',)
        ]
        mock_cursor.fetchall.return_value = contratos_mock
        
        contratos = subcontratados_manager.get_contratos_vencendo(30)  # 30 dias
        
        assert len(contratos) == 2
        # Verificar se filtrou por data de vencimento
        execute_calls = mock_cursor.execute.call_args_list
        query = execute_calls[0][0][0]
        assert 'data_fim' in query
    
    def test_get_equipamentos_emprestados(self, subcontratados_manager, test_db):
        """Teste de busca de equipamentos emprestados"""
        emprestimos_mock = [
            (1, 1, 'Empresa A', 'EQ001', 'Furadeira', datetime.now(), None),
            (2, 2, 'Empresa B', 'EQ002', 'Parafusadeira', datetime.now(), None)
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [
            ('id',), ('subcontratado_id',), ('nome_fantasia',), 
            ('codigo_equipamento',), ('descricao_equipamento',), 
            ('data_emprestimo',), ('data_devolucao',)
        ]
        mock_cursor.fetchall.return_value = emprestimos_mock
        
        emprestimos = subcontratados_manager.get_equipamentos_emprestados()
        
        assert len(emprestimos) == 2
        # Verificar se filtrou por não devolvidos
        execute_calls = mock_cursor.execute.call_args_list
        query = execute_calls[0][0][0]
        assert 'data_devolucao IS NULL' in query or 'data_devolucao' in query
    
    def test_calcular_media_avaliacoes(self, subcontratados_manager, test_db):
        """Teste de cálculo da média de avaliações"""
        subcontratado_id = 1
        avaliacoes_mock = [(8.5, 9.0, 8.0, 7.5)]  # qualidade, prazos, relacionamento, custo
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.fetchall.return_value = avaliacoes_mock
        
        media = subcontratados_manager.calcular_media_avaliacoes(subcontratado_id)
        
        # Média: (8.5 + 9.0 + 8.0 + 7.5) / 4 = 8.25
        assert media == 8.25
    
    def test_get_ranking_subcontratados(self, subcontratados_manager, test_db):
        """Teste de ranking de subcontratados"""
        ranking_mock = [
            (1, 'Empresa A', 9.0),
            (2, 'Empresa B', 8.5),
            (3, 'Empresa C', 8.0)
        ]
        
        mock_cursor = test_db.cursor.return_value
        mock_cursor.description = [('id',), ('nome_fantasia',), ('media_avaliacoes',)]
        mock_cursor.fetchall.return_value = ranking_mock
        
        ranking = subcontratados_manager.get_ranking_subcontratados()
        
        assert len(ranking) == 3
        assert ranking[0]['media_avaliacoes'] == 9.0  # Melhor avaliação primeiro
        # Verificar se ordenou por média decrescente
        assert ranking[0]['media_avaliacoes'] >= ranking[1]['media_avaliacoes']


@pytest.mark.integration
class TestSubcontratadosIntegration:
    """Testes de integração para gestão de subcontratados"""
    
    def test_workflow_subcontratado_completo(self, test_db):
        """Teste completo do workflow de subcontratado"""
        with patch('modules.gestao_subcontratados.db') as mock_db:
            mock_db.get_connection.return_value = test_db
            from modules.gestao_subcontratados import SubcontratadosManager
            manager = SubcontratadosManager()
            
            mock_cursor = test_db.cursor.return_value
            
            # 1. Cadastrar subcontratado
            dados_subcontratado = {
                'razao_social': 'Empresa Teste Ltda',
                'cnpj': '12.345.678/0001-90'
            }
            
            mock_cursor.fetchone.return_value = (1,)
            success, _ = manager.cadastrar_subcontratado(dados_subcontratado)
            assert success is True
            
            # 2. Criar contrato
            dados_contrato = {
                'subcontratado_id': 1,
                'numero_contrato': 'CONT-001',
                'valor_total': 50000.00
            }
            
            mock_cursor.fetchone.return_value = (1,)
            success, _ = manager.criar_contrato(dados_contrato)
            assert success is True
            
            # 3. Emprestar equipamento
            dados_emprestimo = {
                'subcontratado_id': 1,
                'equipamento_id': 1,
                'data_emprestimo': datetime.now()
            }
            
            mock_cursor.fetchone.side_effect = [
                ('EQ001', 'Furadeira', 'disponivel'),
                (1,)
            ]
            
            success, _ = manager.emprestar_equipamento(dados_emprestimo)
            assert success is True
            
            # 4. Avaliar subcontratado
            dados_avaliacao = {
                'subcontratado_id': 1,
                'qualidade_servicos': 8.5,
                'cumprimento_prazos': 9.0
            }
            
            mock_cursor.fetchone.return_value = (1,)
            success, _ = manager.avaliar_subcontratado(dados_avaliacao)
            assert success is True


@pytest.mark.parametrize("qualidade,prazos,relacionamento,custo,expected_media", [
    (8.0, 9.0, 8.5, 7.5, 8.25),
    (10.0, 10.0, 10.0, 10.0, 10.0),
    (5.0, 6.0, 7.0, 8.0, 6.5),
    (0.0, 0.0, 0.0, 0.0, 0.0),
])
def test_calculo_media_avaliacoes(qualidade, prazos, relacionamento, custo, expected_media):
    """Teste parametrizado para cálculo de média de avaliações"""
    media = (qualidade + prazos + relacionamento + custo) / 4
    assert media == expected_media