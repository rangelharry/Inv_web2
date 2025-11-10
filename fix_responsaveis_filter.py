#!/usr/bin/env python3
"""
Script para corrigir filtro de responsáveis ativos em movimentacao_modal.py
"""

import re

def fix_file():
    filename = 'modules/movimentacao_modal.py'
    
    try:
        # Ler o arquivo
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Backup original
        with open(filename + '.bak', 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Aplicar correções
        content = content.replace('{"ativo": 1}', '{"ativo": True}')
        content = content.replace('"ativo": 1', '"ativo": True')
        
        # Adicionar validação de responsáveis vazios
        content = content.replace(
            'responsaveis_options = [""] + [f"{row[\'nome\']} - {row[\'cargo\']}" for _, row in responsaveis_df.iterrows()]',
            '''if not responsaveis_df.empty:
                responsaveis_options = [""] + [f"{row['nome']} - {row['cargo']}" for _, row in responsaveis_df.iterrows()]
            else:
                responsaveis_options = ["Nenhum responsável cadastrado"]'''
        )
        
        # Escrever de volta
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f'✅ Arquivo {filename} corrigido!')
        print('📋 Backup salvo em:', filename + '.bak')
        
    except Exception as e:
        print(f'❌ Erro ao corrigir arquivo: {e}')

if __name__ == '__main__':
    fix_file()