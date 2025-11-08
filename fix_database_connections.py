#!/usr/bin/env python3
"""Script para corrigir todas as conexões de banco nos módulos"""

import os
import re

# Lista de arquivos para corrigir
modules_to_fix = [
    'modules/insumos.py',
    'modules/equipamentos_eletricos.py', 
    'modules/movimentacoes.py',
    'modules/obras.py',
    'modules/responsaveis.py',
    'modules/logs_auditoria.py',
    'modules/usuarios.py'
]

def fix_database_connections():
    for module_path in modules_to_fix:
        if os.path.exists(module_path):
            print(f"Corrigindo {module_path}...")
            
            # Ler arquivo
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Substituições
            content = content.replace('self.db.conn', 'self.db.get_connection()')
            content = content.replace('self.conn', 'conn')
            
            # Padrão para corrigir as definições de cursor
            # Antes: cursor = self.conn.cursor()
            # Depois: conn = self.db.get_connection(); cursor = conn.cursor()
            content = re.sub(
                r'cursor = conn\.cursor\(\)',
                'conn = self.db.get_connection()\\n            cursor = conn.cursor()',
                content
            )
            
            # Corrigir commits e rollbacks
            content = content.replace('conn.commit()', 'conn.commit()')
            content = content.replace('conn.rollback()', 'conn.rollback()')
            
            # Escrever arquivo corrigido
            with open(module_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ {module_path} corrigido")
        else:
            print(f"❌ Arquivo {module_path} não encontrado")

if __name__ == "__main__":
    print("=== CORREÇÃO AUTOMÁTICA DE CONEXÕES DE BANCO ===")
    fix_database_connections()
    print("✅ Correção concluída!")