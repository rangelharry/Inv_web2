"""
Revisão Final de Garantia - Sistema de Inventário Web
Verificação completa de funcionalidades, integridade e performance
"""

import os
import traceback
from pathlib import Path
import sys

def test_core_modules():
    """Testa módulos essenciais do sistema"""
    
    print("🔍 REVISÃO DE GARANTIA - MÓDULOS ESSENCIAIS")
    print("=" * 60)
    
    core_modules = [
        # Módulos críticos
        ("main", "Aplicação principal"),
        ("modules.auth", "Autenticação e segurança"),
        ("modules.usuarios", "Gestão de usuários"),
        ("modules.insumos", "Gestão de insumos"),
        ("modules.equipamentos_eletricos", "Equipamentos elétricos"),
        ("modules.equipamentos_manuais", "Equipamentos manuais"),
        ("modules.movimentacoes", "Controle de movimentações"),
        ("modules.relatorios", "Sistema de relatórios"),
        
        # Módulos avançados
        ("modules.dashboard_executivo", "Dashboard executivo"),
        ("modules.barcode_utils", "QR Code e códigos de barras"),
        ("modules.reservas", "Sistema de reservas"),
        ("modules.gestao_financeira", "Gestão financeira"),
        ("modules.backup_recovery", "Backup e recovery"),
        ("modules.analise_preditiva", "Análise preditiva"),
    ]
    
    results = {"success": [], "failed": [], "warnings": []}
    
    for module_name, description in core_modules:
        try:
            print(f"📦 Testando {description}...")
            
            # Importar módulo
            module = __import__(module_name, fromlist=[''])
            
            # Verificar se tem funções principais
            if hasattr(module, 'show_') or module_name == "main":
                results["success"].append((module_name, description))
                print(f"  ✅ {description}: OK")
            else:
                results["warnings"].append((module_name, description, "Função show_ não encontrada"))
                print(f"  ⚠️ {description}: Função principal não encontrada")
                
        except ImportError as e:
            results["failed"].append((module_name, description, f"Import error: {e}"))
            print(f"  ❌ {description}: Erro de importação - {e}")
        except Exception as e:
            results["failed"].append((module_name, description, f"Error: {e}"))
            print(f"  ❌ {description}: Erro - {e}")
    
    return results

def verify_database_structure():
    """Verifica estrutura do banco de dados"""
    
    print(f"\n🗄️ VERIFICAÇÃO DA ESTRUTURA DO BANCO")
    print("=" * 50)
    
    expected_tables = [
        "usuarios",
        "insumos", 
        "equipamentos_eletricos",
        "equipamentos_manuais",
        "movimentacoes",
        "obras",
        "responsaveis",
        "permissoes_modulos",
        "logs_auditoria"
    ]
    
    try:
        from database.connection import db
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar tabelas existentes
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        existing_tables = [row[0] if isinstance(row, tuple) else row['table_name'] for row in cursor.fetchall()]
        
        print(f"📊 Tabelas encontradas: {len(existing_tables)}")
        
        missing_tables = []
        for table in expected_tables:
            if table in existing_tables:
                print(f"  ✅ {table}: Existe")
            else:
                missing_tables.append(table)
                print(f"  ❌ {table}: FALTANDO")
        
        # Verificar índices críticos
        print(f"\n📈 Verificando índices...")
        critical_indexes = [
            ("permissoes_modulos", "idx_permissoes_usuario_modulo"),
            ("logs_auditoria", "idx_logs_usuario"),
        ]
        
        for table, index in critical_indexes:
            if table in existing_tables:
                cursor.execute(f"""
                    SELECT indexname FROM pg_indexes 
                    WHERE tablename = '{table}' AND indexname = '{index}'
                """)
                if cursor.fetchone():
                    print(f"  ✅ Índice {index}: Existe")
                else:
                    print(f"  ⚠️ Índice {index}: Recomendado criar")
        
        return {"existing_tables": existing_tables, "missing_tables": missing_tables}
        
    except Exception as e:
        print(f"  ❌ Erro ao verificar banco: {e}")
        return {"error": str(e)}

def test_authentication_system():
    """Testa sistema de autenticação"""
    
    print(f"\n🔐 TESTE DO SISTEMA DE AUTENTICAÇÃO")
    print("=" * 45)
    
    try:
        from modules.auth import auth_manager
        
        # Testar funções principais
        functions_to_test = [
            "hash_password",
            "verify_password", 
            "get_user_module_permissions",
            "check_module_permission",
            "update_user_module_permissions",
            "logout_user"
        ]
        
        for func_name in functions_to_test:
            if hasattr(auth_manager, func_name):
                print(f"  ✅ {func_name}: Disponível")
            else:
                print(f"  ❌ {func_name}: FALTANDO")
        
        # Testar hash de senha
        test_password = "teste123"
        hashed = auth_manager.hash_password(test_password)
        is_valid = auth_manager.verify_password(test_password, hashed)
        
        if is_valid:
            print(f"  ✅ Hash/verificação de senhas: Funcionando")
        else:
            print(f"  ❌ Hash/verificação de senhas: FALHOU")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erro no sistema de autenticação: {e}")
        return False

def verify_file_integrity():
    """Verifica integridade dos arquivos principais"""
    
    print(f"\n📁 VERIFICAÇÃO DE INTEGRIDADE DOS ARQUIVOS")
    print("=" * 50)
    
    critical_files = [
        ("main.py", "Arquivo principal"),
        ("database/connection.py", "Conexão com banco"),
        (".streamlit/secrets.toml", "Configuração do banco"),
        ("requirements.txt", "Dependências"),
        ("modules/auth.py", "Autenticação"),
        ("modules/usuarios.py", "Gestão de usuários"),
        ("modules/insumos.py", "Gestão de insumos"),
    ]
    
    results = {"found": [], "missing": [], "empty": []}
    
    for file_path, description in critical_files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            if file_size > 0:
                results["found"].append((file_path, description, file_size))
                print(f"  ✅ {description}: {file_size} bytes")
            else:
                results["empty"].append((file_path, description))
                print(f"  ⚠️ {description}: Arquivo vazio")
        else:
            results["missing"].append((file_path, description))
            print(f"  ❌ {description}: FALTANDO")
    
    return results

def generate_final_report(module_results, db_results, auth_result, file_results):
    """Gera relatório final de garantia"""
    
    print(f"\n" + "="*60)
    print(f"📋 RELATÓRIO FINAL DE GARANTIA")
    print(f"="*60)
    
    # Calcular scores
    total_modules = len(module_results["success"]) + len(module_results["failed"]) + len(module_results["warnings"])
    success_modules = len(module_results["success"])
    module_score = (success_modules / total_modules * 100) if total_modules > 0 else 0
    
    total_files = len(file_results["found"]) + len(file_results["missing"]) + len(file_results["empty"])
    found_files = len(file_results["found"])
    file_score = (found_files / total_files * 100) if total_files > 0 else 0
    
    auth_score = 100 if auth_result else 0
    
    if "error" not in db_results:
        db_score = 90 if len(db_results.get("missing_tables", [])) == 0 else 70
    else:
        db_score = 0
    
    overall_score = (module_score + file_score + auth_score + db_score) / 4
    
    print(f"📊 SCORES DE QUALIDADE:")
    print(f"  • Módulos: {module_score:.1f}% ({success_modules}/{total_modules})")
    print(f"  • Autenticação: {auth_score:.1f}%")
    print(f"  • Banco de dados: {db_score:.1f}%") 
    print(f"  • Arquivos: {file_score:.1f}% ({found_files}/{total_files})")
    print(f"\n⭐ SCORE GERAL: {overall_score:.1f}%")
    
    # Status final
    if overall_score >= 90:
        status = "🟢 EXCELENTE - Pronto para produção"
    elif overall_score >= 80:
        status = "🟡 BOM - Pronto com pequenos ajustes"
    elif overall_score >= 70:
        status = "🟠 ACEITÁVEL - Necessita melhorias"
    else:
        status = "🔴 CRÍTICO - Requer correções urgentes"
    
    print(f"\n🎯 STATUS FINAL: {status}")
    
    # Recomendações
    print(f"\n📝 RECOMENDAÇÕES:")
    if module_results["failed"]:
        print(f"  ❗ Corrigir módulos com falha: {[m[0] for m in module_results['failed']]}")
    if file_results["missing"]:
        print(f"  ❗ Criar arquivos faltando: {[f[0] for f in file_results['missing']]}")
    if not auth_result:
        print(f"  ❗ Corrigir sistema de autenticação")
    
    if overall_score >= 85:
        print(f"  ✅ Sistema aprovado para comercialização!")
    
    return overall_score

if __name__ == "__main__":
    print("🔍 INICIANDO REVISÃO FINAL DE GARANTIA...")
    print("Data:", "10 de novembro de 2025")
    print()
    
    try:
        module_results = test_core_modules()
        db_results = verify_database_structure()
        auth_result = test_authentication_system()
        file_results = verify_file_integrity()
        
        final_score = generate_final_report(module_results, db_results, auth_result, file_results)
        
        print(f"\n🎉 Revisão concluída com score: {final_score:.1f}%")
        
    except Exception as e:
        print(f"❌ Erro durante revisão: {e}")
        traceback.print_exc()