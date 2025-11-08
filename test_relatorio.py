#!/usr/bin/env python3
"""Teste do módulo de relatórios"""

from modules.relatorios import RelatoriosManager
import pandas as pd

def test_relatorio_estoque_baixo():
    print("=== TESTE DO RELATÓRIO DE ESTOQUE BAIXO ===")
    
    try:
        manager = RelatoriosManager()
        df = manager.gerar_relatorio_estoque_baixo()
        
        print(f"DataFrame criado: {type(df)}")
        print(f"Número de linhas: {len(df)}")
        print(f"Número de colunas: {len(df.columns) if hasattr(df, 'columns') else 'N/A'}")
        
        if not df.empty:
            print("Colunas do DataFrame:")
            for col in df.columns:
                print(f"  - {col}")
            
            print("\\nPrimeiras 3 linhas:")
            print(df.head(3).to_string())
            
            # Testar se tem dados válidos para gráfico
            if 'deficit' in df.columns and 'item' in df.columns:
                print(f"\\nDados válidos para gráfico:")
                print(f"  - Déficits não nulos: {df['deficit'].notna().sum()}")
                print(f"  - Maior déficit: {df['deficit'].max()}")
                print(f"  - Menor déficit: {df['deficit'].min()}")
            
            print("✅ Relatório de estoque baixo funcionando!")
        else:
            print("⚠️ DataFrame vazio - pode indicar que não há itens com estoque baixo")
            
    except Exception as e:
        print(f"❌ Erro no relatório de estoque baixo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_relatorio_estoque_baixo()