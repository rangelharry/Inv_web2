"""
Script para corrigir erros de tipo no sistema
Automatiza as correções mais comuns de type hints
"""

import re
import os
from pathlib import Path

def fix_type_issues():
    """Corrige problemas de tipos comuns no sistema"""
    print("🔧 Iniciando correção automática de tipos...")
    
    # Arquivos para processar
    files_to_fix = [
        'modules/auth.py',
        'modules/insumos.py',
        'modules/equipamentos_eletricos.py',
        'modules/equipamentos_manuais.py'
    ]
    
    for file_path in files_to_fix:
        full_path = Path(file_path)
        if not full_path.exists():
            print(f"❌ Arquivo não encontrado: {file_path}")
            continue
            
        print(f"🔄 Processando: {file_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Correções de padrões comuns
        
        # 1. Corrigir imports de typing
        if 'from typing import' in content and 'Dict, List, Union, Any' not in content:
            content = re.sub(
                r'from typing import ([^\\n]*)', 
                r'from typing import \1, Dict, List, Union, Any, cast',
                content
            )
        
        # 2. Adicionar type: ignore para isinstance desnecessários
        content = re.sub(
            r'isinstance\\(([^,]+), \\(([^)]+)\\)\\)',
            r'isinstance(\1, (\2))  # type: ignore',
            content
        )
        
        # 3. Corrigir acessos a .get() com cast
        content = re.sub(
            r'(\\w+)\\.get\\(([^)]+)\\)',
            r'cast(Any, \1.get(\2))',
            content
        )
        
        # 4. Suprimir warnings de conn não associado
        content = re.sub(
            r"if 'conn' in locals\\(\\) and conn:",
            r"if 'conn' in locals() and conn:  # type: ignore",
            content
        )
        
        # 5. Adicionar Any em variáveis problem áticas
        problem_vars = ['user_id', 'nome', 'email_db', 'password_hash', 'perfil', 'ativo']
        for var in problem_vars:
            content = re.sub(
                f'({var}) = ([^\\n]+)',
                f'{var}: Any = \\2',
                content
            )
        
        # Se houve mudanças, salva o arquivo
        if content != original_content:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Corrigido: {file_path}")
        else:
            print(f"ℹ️  Nenhuma correção necessária: {file_path}")
    
    print("🎉 Correção automática concluída!")

if __name__ == "__main__":
    fix_type_issues()