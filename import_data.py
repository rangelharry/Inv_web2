"""
Script para Importar Dados dos JSONs para o Banco de Dados
Importa equipamentos elétricos, manuais e insumos
"""

import json
import sqlite3  # type: ignore
import sys
import os
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import db

def import_equipamentos_eletricos():
    """Importa equipamentos elétricos do JSON"""
    print("🔄 Importando equipamentos elétricos...")
    
    try:
        # Ler arquivo JSON
        with open('equipamentos_eletricos.json', 'r', encoding='utf-8') as f:
            equipamentos = json.load(f)
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Buscar ID da categoria "Ferramentas Elétricas"
        cursor.execute("SELECT id FROM categorias WHERE nome = 'Ferramentas Elétricas'")
        categoria = cursor.fetchone()
        categoria_id = categoria['id'] if categoria else None
        
        imported_count = 0
        error_count = 0
        
        for eq in equipamentos:
            try:
                # Processar observações (JSON string)
                observacoes_json = eq.get('observacoes', '{}')
                if isinstance(observacoes_json, str):
                    try:
                        obs_data = json.loads(observacoes_json)
                    except:
                        obs_data = {}
                else:
                    obs_data = {}
                
                # Extrair dados das observações
                voltagem = obs_data.get('VOLTAGEM') or obs_data.get('voltagem')  # type: ignore
                potencia = obs_data.get('POTENCIA') or obs_data.get('potencia')  # type: ignore
                data_compra = obs_data.get('DATA COMPRA') or obs_data.get('data_compra')  # type: ignore
                garantia = obs_data.get('GARANTIA') or obs_data.get('garantia')  # type: ignore
                loja = obs_data.get('LOJA') or obs_data.get('loja')  # type: ignore
                
                # Converter data se necessário
                data_compra_date = None
                if data_compra and isinstance(data_compra, (int, float)):
                    try:
                        data_compra_date = datetime.fromtimestamp(data_compra / 1000).date()
                    except:
                        data_compra_date = None
                
                # Inserir equipamento
                cursor.execute("""
                INSERT OR IGNORE INTO equipamentos_eletricos (
                    codigo, nome, categoria_id, marca, modelo, voltagem, potencia,
                    status, localizacao, valor_compra, data_compra, observacoes,
                    fornecedor, ativo, criado_por
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    eq.get('codigo'),
                    eq.get('nome'),
                    categoria_id,
                    eq.get('marca'),
                    eq.get('modelo'),
                    voltagem,
                    potencia,
                    eq.get('status', 'Disponível'),
                    eq.get('localizacao', 'Almoxarifado'),
                    eq.get('valor_compra'),
                    data_compra_date,
                    observacoes_json,
                    loja,
                    1,  # ativo
                    1   # criado pelo admin
                ))  # type: ignore
                
                imported_count += 1
                
            except Exception as e:
                print(f"❌ Erro ao importar equipamento {eq.get('codigo', 'N/A')}: {e}")
                error_count += 1
        
        conn.commit()
        print(f"✅ Equipamentos elétricos importados: {imported_count} sucessos, {error_count} erros")
        
    except Exception as e:
        print(f"❌ Erro geral na importação de equipamentos elétricos: {e}")

def import_equipamentos_manuais():
    """Importa equipamentos manuais do JSON"""
    print("🔄 Importando equipamentos manuais...")
    
    try:
        # Ler arquivo JSON
        with open('equipamentos_manuais.json', 'r', encoding='utf-8') as f:
            equipamentos = json.load(f)
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Buscar ID da categoria "Ferramentas Manuais"
        cursor.execute("SELECT id FROM categorias WHERE nome = 'Ferramentas Manuais'")
        categoria = cursor.fetchone()
        categoria_id = categoria['id'] if categoria else None
        
        imported_count = 0
        error_count = 0
        
        for eq in equipamentos:
            try:
                # Processar observações (JSON string)
                observacoes_json = eq.get('observacoes', '{}')
                if isinstance(observacoes_json, str):
                    try:
                        obs_data = json.loads(observacoes_json)
                    except:
                        obs_data = {}
                else:
                    obs_data = {}
                
                # Extrair dados das observações
                data_compra = obs_data.get('DATA DE COMPRA') or obs_data.get('data_compra')  # type: ignore
                loja = obs_data.get('LOJA') or obs_data.get('loja')  # type: ignore
                
                # Converter data se necessário
                data_compra_date = None
                if data_compra and isinstance(data_compra, (int, float)):
                    try:
                        data_compra_date = datetime.fromtimestamp(data_compra / 1000).date()
                    except:
                        data_compra_date = None
                
                # Inserir equipamento
                cursor.execute("""
                INSERT OR IGNORE INTO equipamentos_manuais (
                    codigo, descricao, tipo, categoria_id, quantitativo, status,
                    estado, marca, localizacao, valor, data_compra, loja,
                    observacoes, ativo, criado_por
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    eq.get('codigo'),
                    eq.get('descricao'),
                    eq.get('tipo'),
                    categoria_id,
                    eq.get('quantitativo', 1),
                    eq.get('status', 'Disponível'),
                    eq.get('estado'),
                    eq.get('marca'),
                    eq.get('localizacao', 'Almoxarifado'),
                    eq.get('valor'),
                    data_compra_date,
                    loja,
                    observacoes_json,
                    1,  # ativo
                    1   # criado pelo admin
                ))  # type: ignore
                
                imported_count += 1
                
            except Exception as e:
                print(f"❌ Erro ao importar equipamento {eq.get('codigo', 'N/A')}: {e}")
                error_count += 1
        
        conn.commit()
        print(f"✅ Equipamentos manuais importados: {imported_count} sucessos, {error_count} erros")
        
    except Exception as e:
        print(f"❌ Erro geral na importação de equipamentos manuais: {e}")

def import_insumos():
    """Importa insumos do JSON"""
    print("🔄 Importando insumos...")
    
    try:
        # Ler arquivo JSON
        with open('insumos.json', 'r', encoding='utf-8') as f:
            insumos = json.load(f)
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        imported_count = 0
        error_count = 0
        
        # Mapeamento de categorias
        categoria_mapping = {
            'Hidráulica': 'Hidráulica',
            'Elétrica': 'Elétrica',
            'Civil': 'Civil',
            'Acabamentos': 'Acabamentos',
            'E.P.I.': 'E.P.I.',
            'Pintura': 'Pintura',
            'Limpeza': 'Limpeza',
            'Lubrificação': 'Lubrificação',
            'Incêndio': 'Incêndio',
            'Forro': 'Forro',
            'Outros': 'Outros'
        }
        
        for insumo in insumos:
            try:
                # Processar observações (JSON string)
                observacoes_json = insumo.get('observacoes', '{}')
                if isinstance(observacoes_json, str):
                    try:
                        obs_data = json.loads(observacoes_json)
                    except:
                        obs_data = {}
                else:
                    obs_data = {}
                
                # Buscar categoria
                categoria_nome = categoria_mapping.get(insumo.get('categoria'), 'Outros')
                cursor.execute("SELECT id FROM categorias WHERE nome = ?", (categoria_nome,))
                categoria = cursor.fetchone()
                categoria_id = categoria['id'] if categoria else None
                
                # Extrair dados das observações
                marca = obs_data.get('MARCA') or obs_data.get('marca')  # type: ignore
                status_validade = obs_data.get('STATUS/VALIDADE') or obs_data.get('status_validade')  # type: ignore
                
                # Processar validade se for timestamp
                data_validade = None
                if status_validade and isinstance(status_validade, (int, float)):
                    try:
                        data_validade = datetime.fromtimestamp(status_validade / 1000).date()
                    except:
                        data_validade = None
                
                # Inserir insumo
                cursor.execute("""
                INSERT OR IGNORE INTO insumos (
                    codigo, descricao, categoria_id, unidade, quantidade_atual,
                    quantidade_minima, preco_unitario, marca, localizacao,
                    observacoes, data_validade, ativo, criado_por
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    insumo.get('codigo'),
                    insumo.get('descricao'),
                    categoria_id,
                    insumo.get('unidade', 'UND'),
                    insumo.get('quantidade_atual', 0),
                    insumo.get('quantidade_minima', 5),
                    insumo.get('preco_unitario'),
                    marca,
                    insumo.get('localizacao', 'Almoxarifado'),
                    observacoes_json,
                    data_validade,
                    1,  # ativo
                    1   # criado pelo admin
                ))  # type: ignore
                
                imported_count += 1
                
            except Exception as e:
                print(f"❌ Erro ao importar insumo {insumo.get('codigo', 'N/A')}: {e}")
                error_count += 1
        
        conn.commit()
        print(f"✅ Insumos importados: {imported_count} sucessos, {error_count} erros")
        
    except Exception as e:
        print(f"❌ Erro geral na importação de insumos: {e}")

def main():
    """Função principal de importação"""
    print("🚀 Iniciando importação de dados dos JSONs...")
    print("=" * 50)
    
    # Verificar se os arquivos existem
    arquivos = ['equipamentos_eletricos.json', 'equipamentos_manuais.json', 'insumos.json']
    
    for arquivo in arquivos:
        if not os.path.exists(arquivo):
            print(f"❌ Arquivo {arquivo} não encontrado!")
            return
    
    # Importar dados
    try:
        import_equipamentos_eletricos()
        print()
        import_equipamentos_manuais()
        print()
        import_insumos()
        
        print()
        print("=" * 50)
        print("✅ Importação concluída com sucesso!")
        print("📊 Acesse o sistema web para visualizar os dados importados.")
        
    except Exception as e:
        print(f"❌ Erro na importação: {e}")

if __name__ == "__main__":
    main()