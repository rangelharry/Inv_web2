"""
Script para criação de índices específicos com colunas corretas
"""

from database.connection import db

def create_correct_indexes():
    """Cria índices com nomes de colunas corretos"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Índices baseados na estrutura real das tabelas
        indexes = [
            # Índices para insumos
            "CREATE INDEX IF NOT EXISTS idx_insumos_codigo ON insumos(codigo)",
            "CREATE INDEX IF NOT EXISTS idx_insumos_categoria_id ON insumos(categoria_id)",
            "CREATE INDEX IF NOT EXISTS idx_insumos_localizacao ON insumos(localizacao)",
            "CREATE INDEX IF NOT EXISTS idx_insumos_fornecedor ON insumos(fornecedor)",
            "CREATE INDEX IF NOT EXISTS idx_insumos_quantidade ON insumos(quantidade_atual)",
            "CREATE INDEX IF NOT EXISTS idx_insumos_critico ON insumos(quantidade_atual, quantidade_minima)",
            
            # Índices para equipamentos elétricos
            "CREATE INDEX IF NOT EXISTS idx_ee_codigo ON equipamentos_eletricos(codigo)",
            "CREATE INDEX IF NOT EXISTS idx_ee_categoria_id ON equipamentos_eletricos(categoria_id)",
            "CREATE INDEX IF NOT EXISTS idx_ee_status ON equipamentos_eletricos(status)",
            "CREATE INDEX IF NOT EXISTS idx_ee_localizacao ON equipamentos_eletricos(localizacao)",
            "CREATE INDEX IF NOT EXISTS idx_ee_obra ON equipamentos_eletricos(obra_atual_id)",
            "CREATE INDEX IF NOT EXISTS idx_ee_responsavel ON equipamentos_eletricos(responsavel_atual_id)",
            
            # Índices para equipamentos manuais
            "CREATE INDEX IF NOT EXISTS idx_em_codigo ON equipamentos_manuais(codigo)",
            "CREATE INDEX IF NOT EXISTS idx_em_categoria_id ON equipamentos_manuais(categoria_id)",
            "CREATE INDEX IF NOT EXISTS idx_em_status ON equipamentos_manuais(status)",
            "CREATE INDEX IF NOT EXISTS idx_em_estado ON equipamentos_manuais(estado)",
            "CREATE INDEX IF NOT EXISTS idx_em_localizacao ON equipamentos_manuais(localizacao)",
            "CREATE INDEX IF NOT EXISTS idx_em_obra ON equipamentos_manuais(obra_atual_id)",
            
            # Índices para movimentações
            "CREATE INDEX IF NOT EXISTS idx_mov_data ON movimentacoes(data_movimentacao)",
            "CREATE INDEX IF NOT EXISTS idx_mov_tipo ON movimentacoes(tipo)",
            "CREATE INDEX IF NOT EXISTS idx_mov_tipo_item ON movimentacoes(tipo_item)",
            "CREATE INDEX IF NOT EXISTS idx_mov_item_id ON movimentacoes(item_id)",
            "CREATE INDEX IF NOT EXISTS idx_mov_usuario ON movimentacoes(usuario_id)",
            "CREATE INDEX IF NOT EXISTS idx_mov_status ON movimentacoes(status)",
            "CREATE INDEX IF NOT EXISTS idx_mov_data_tipo ON movimentacoes(data_movimentacao, tipo)",
            
            # Índices para permissões
            "CREATE INDEX IF NOT EXISTS idx_perm_usuario_modulo ON permissoes_modulos(usuario_id, modulo)",
            "CREATE INDEX IF NOT EXISTS idx_perm_acesso ON permissoes_modulos(usuario_id) WHERE acesso = true",
            
            # Índices para usuários
            "CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_perfil ON usuarios(perfil)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_ativo ON usuarios(id) WHERE ativo = true"
        ]
        
        print("Criando índices otimizados com colunas corretas...")
        created_count = 0
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                created_count += 1
                index_name = index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'unknown'
                print(f"✓ Índice criado: {index_name}")
            except Exception as e:
                print(f"✗ Erro ao criar índice: {index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'unknown'} - {e}")
                # Continuar mesmo com erro em um índice
                pass
        
        conn.commit()
        print(f"\n✅ Total de índices criados com sucesso: {created_count}")
        return True
        
    except Exception as e:
        print(f"❌ Erro geral ao criar índices: {e}")
        return False

if __name__ == "__main__":
    create_correct_indexes()