"""
Script para popular banco de dados com dados de teste - CORRIGIDO
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import db
from datetime import datetime, date, timedelta
import random

def get_count_result(cursor_result):
    """Helper para extrair count do resultado"""
    if isinstance(cursor_result, dict):
        return cursor_result.get('count', 0)
    elif isinstance(cursor_result, (list, tuple)):
        return cursor_result[0]
    else:
        return cursor_result

def get_id_result(cursor_result):
    """Helper para extrair id do resultado"""
    if isinstance(cursor_result, dict):
        return cursor_result.get('id', 1)
    elif isinstance(cursor_result, (list, tuple)):
        return cursor_result[0]
    else:
        return cursor_result if cursor_result else 1

def popular_dados_teste():
    """Popula banco com dados de teste"""
    print("=== POPULANDO BANCO COM DADOS DE TESTE ===")
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 1. Popular insumos se estiver vazio
        cursor.execute("SELECT COUNT(*) FROM insumos")
        count_insumos = get_count_result(cursor.fetchone())
        
        if count_insumos == 0:
            print("Populando insumos...")
            
            # Buscar categorias
            cursor.execute("SELECT id FROM categorias WHERE tipo = 'insumo' LIMIT 1")
            categoria_result = cursor.fetchone()
            categoria_id = get_id_result(categoria_result)
            
            insumos_teste = [
                ('INS001', 'Cabo de Rede Cat6', 'TechCorp', 'UND', 100, 20, 150.00, categoria_id),
                ('INS002', 'Conector RJ45', 'NetMax', 'UND', 500, 50, 5.50, categoria_id),
                ('INS003', 'Switch 8 Portas', 'LinkTech', 'UND', 15, 5, 280.00, categoria_id),
                ('INS004', 'Patch Panel 24P', 'DataLink', 'UND', 8, 2, 420.00, categoria_id),
                ('INS005', 'Cabo Fibra Ótica', 'FiberMax', 'M', 1000, 100, 12.80, categoria_id)
            ]
            
            for insumo in insumos_teste:
                cursor.execute("""
                    INSERT INTO insumos (codigo, descricao, marca, unidade, quantidade_atual, quantidade_minima, preco_unitario, categoria_id, ativo, data_criacao)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s)
                """, (*insumo, datetime.now()))
            
            print(f"✅ {len(insumos_teste)} insumos criados")
        
        # 2. Popular equipamentos elétricos
        cursor.execute("SELECT COUNT(*) FROM equipamentos_eletricos")
        count_ee = get_count_result(cursor.fetchone())
        
        if count_ee == 0:
            print("Populando equipamentos elétricos...")
            
            cursor.execute("SELECT id FROM categorias WHERE tipo = 'equipamento' LIMIT 1")
            categoria_result = cursor.fetchone()
            categoria_id = get_id_result(categoria_result)
            
            equipamentos = [
                ('EE001', 'Furadeira Industrial', 'Bosch', 'X1500-PRO', '220V', 1500, 'Ativo', categoria_id),
                ('EE002', 'Compressor de Ar', 'Schulz', 'CSI-8.5', '220V', 2200, 'Ativo', categoria_id),
                ('EE003', 'Esmerilhadeira Angular', 'Makita', 'GA5020', '220V', 1400, 'Ativo', categoria_id),
                ('EE004', 'Serra Circular', 'DeWalt', 'DWE575', '220V', 1600, 'Ativo', categoria_id),
                ('EE005', 'Parafusadeira', 'Black & Decker', 'CD121K', '12V', 12, 'Ativo', categoria_id)
            ]
            
            for eq in equipamentos:
                cursor.execute("""
                    INSERT INTO equipamentos_eletricos (codigo, nome, marca, modelo, tensao, potencia, status, categoria_id, ativo, data_aquisicao)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s)
                """, (*eq, date.today()))
            
            print(f"✅ {len(equipamentos)} equipamentos elétricos criados")
        
        # 3. Popular equipamentos manuais
        cursor.execute("SELECT COUNT(*) FROM equipamentos_manuais")
        count_em = get_count_result(cursor.fetchone())
        
        if count_em == 0:
            print("Populando equipamentos manuais...")
            
            equipamentos_manuais = [
                ('EM001', 'Martelo de Unha', 'Stanley', 'ST-51-104', 'Ativo', categoria_id),
                ('EM002', 'Chave de Fenda 6mm', 'Tramontina', 'TM-43420', 'Ativo', categoria_id),
                ('EM003', 'Alicate Universal', 'Gedore', 'VDE-8140', 'Ativo', categoria_id),
                ('EM004', 'Trena 5 metros', 'Starrett', 'KTS5-19', 'Ativo', categoria_id),
                ('EM005', 'Chave Inglesa 12"', 'Bahco', '8071-12', 'Ativo', categoria_id)
            ]
            
            for eq in equipamentos_manuais:
                cursor.execute("""
                    INSERT INTO equipamentos_manuais (codigo, nome, marca, modelo, status, categoria_id, ativo, data_aquisicao)
                    VALUES (%s, %s, %s, %s, %s, %s, TRUE, %s)
                """, (*eq, date.today()))
            
            print(f"✅ {len(equipamentos_manuais)} equipamentos manuais criados")
        
        # 4. Popular movimentações
        cursor.execute("SELECT COUNT(*) FROM movimentacoes")
        count_mov = get_count_result(cursor.fetchone())
        
        if count_mov == 0:
            print("Populando movimentações...")
            
            # Buscar alguns insumos para criar movimentações
            cursor.execute("SELECT id FROM insumos LIMIT 3")
            insumos_results = cursor.fetchall()
            insumos_ids = [get_id_result(row) for row in insumos_results]
            
            if insumos_ids:
                tipos_mov = ['entrada', 'saida', 'transferencia', 'ajuste']
                
                for i in range(10):
                    insumo_id = random.choice(insumos_ids)
                    tipo = random.choice(tipos_mov)
                    quantidade = random.randint(5, 50)
                    
                    cursor.execute("""
                        INSERT INTO movimentacoes (tipo, insumo_id, equipamento_id, quantidade, observacoes, data_movimentacao, usuario_id)
                        VALUES (%s, %s, NULL, %s, %s, %s, 1)
                    """, (tipo, insumo_id, quantidade, f'Movimentação de teste {i+1}', datetime.now() - timedelta(days=random.randint(1, 30))))
                
                print("✅ 10 movimentações criadas")
        
        # 5. Popular logs de auditoria
        cursor.execute("SELECT COUNT(*) FROM logs_auditoria")
        count_logs = get_count_result(cursor.fetchone())
        
        if count_logs == 0:
            print("Populando logs de auditoria...")
            
            acoes = ['CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN']
            modulos = ['insumos', 'equipamentos', 'usuarios', 'sistema']
            
            for i in range(20):
                acao = random.choice(acoes)
                modulo = random.choice(modulos)
                
                cursor.execute("""
                    INSERT INTO logs_auditoria (modulo, acao, observacoes, usuario_nome, data_acao)
                    VALUES (%s, %s, %s, %s, %s)
                """, (modulo, acao, f'Ação de teste {i+1}', 'Administrador', datetime.now() - timedelta(hours=random.randint(1, 72))))
            
            print("✅ 20 logs de auditoria criados")
        
        # 6. Criar configurações se não existirem
        cursor.execute("SELECT COUNT(*) FROM configuracoes")
        count_config = get_count_result(cursor.fetchone())
        
        if count_config == 0:
            print("Criando configurações...")
            
            configs = [
                ('empresa_nome', 'TechCorp Ltda'),
                ('empresa_cnpj', '12.345.678/0001-90'),
                ('empresa_endereco', 'Rua da Tecnologia, 123'),
                ('empresa_telefone', '(11) 9999-8888'),
                ('empresa_email', 'contato@techcorp.com.br'),
                ('sistema_nome', 'Sistema de Inventário Web'),
                ('backup_automatico', 'true'),
                ('estoque_alerta_minimo', '10')
            ]
            
            for chave, valor in configs:
                cursor.execute("""
                    INSERT INTO configuracoes (chave, valor, descricao, data_criacao)
                    VALUES (%s, %s, %s, %s)
                """, (chave, valor, f'Configuração {chave}', datetime.now()))
            
            print(f"✅ {len(configs)} configurações criadas")
        
        # Commit all changes
        conn.commit()
        print("\n🎉 Banco de dados populado com sucesso!")
        
        # Mostrar estatísticas finais
        cursor.execute("SELECT COUNT(*) FROM insumos")
        print(f"📊 Total insumos: {get_count_result(cursor.fetchone())}")
        
        cursor.execute("SELECT COUNT(*) FROM equipamentos_eletricos")
        print(f"📊 Total equipamentos elétricos: {get_count_result(cursor.fetchone())}")
        
        cursor.execute("SELECT COUNT(*) FROM equipamentos_manuais")
        print(f"📊 Total equipamentos manuais: {get_count_result(cursor.fetchone())}")
        
        cursor.execute("SELECT COUNT(*) FROM movimentacoes")
        print(f"📊 Total movimentações: {get_count_result(cursor.fetchone())}")
        
        cursor.execute("SELECT COUNT(*) FROM logs_auditoria")
        print(f"📊 Total logs: {get_count_result(cursor.fetchone())}")
        
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        print(f"📊 Total usuários: {get_count_result(cursor.fetchone())}")
        
    except Exception as e:
        print(f"❌ Erro ao popular banco: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    popular_dados_teste()