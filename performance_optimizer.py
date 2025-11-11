"""
Sistema de Otimização de Performance
Análise e aplicação de melhorias de performance
"""

import streamlit as st
import psycopg2
import time
from database.connection import db
from typing import Dict, List, Any
import pandas as pd

class PerformanceOptimizer:
    """Otimizador de performance do sistema"""
    
    def __init__(self):
        self.db = db
        
    def analyze_database_performance(self) -> Dict[str, Any]:
        """Analisa performance do banco de dados"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            analysis = {}
            
            # 1. Verificar queries mais lentas
            cursor.execute("""
                SELECT query, mean_exec_time, calls, total_exec_time
                FROM pg_stat_statements 
                WHERE mean_exec_time > 100
                ORDER BY mean_exec_time DESC
                LIMIT 10
            """)
            slow_queries = cursor.fetchall()
            analysis['slow_queries'] = slow_queries
            
            # 2. Verificar tamanho das tabelas
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """)
            table_sizes = cursor.fetchall()
            analysis['table_sizes'] = table_sizes
            
            # 3. Verificar índices ausentes
            cursor.execute("""
                SELECT schemaname, tablename, attname, n_distinct, correlation
                FROM pg_stats
                WHERE schemaname = 'public'
                AND n_distinct > 100
                AND correlation < 0.1
            """)
            missing_indexes = cursor.fetchall()
            analysis['potential_indexes'] = missing_indexes
            
            # 4. Conexões ativas
            cursor.execute("""
                SELECT count(*) as active_connections
                FROM pg_stat_activity 
                WHERE state = 'active'
            """)
            active_connections = cursor.fetchone()[0]
            analysis['active_connections'] = active_connections
            
            return analysis
            
        except Exception as e:
            print(f"Erro na análise: {e}")
            return {}
    
    def create_performance_indexes(self) -> bool:
        """Cria índices otimizados para performance"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Usar CREATE INDEX normal em vez de CONCURRENTLY para Neon
            indexes = [
                # Índices para insumos
                "CREATE INDEX IF NOT EXISTS idx_insumos_categoria ON insumos(categoria)",
                "CREATE INDEX IF NOT EXISTS idx_insumos_codigo ON insumos(codigo)",
                "CREATE INDEX IF NOT EXISTS idx_insumos_localizacao ON insumos(localizacao)",
                "CREATE INDEX IF NOT EXISTS idx_insumos_fornecedor ON insumos(fornecedor)",
                
                # Índices para equipamentos elétricos
                "CREATE INDEX IF NOT EXISTS idx_ee_categoria ON equipamentos_eletricos(categoria)",
                "CREATE INDEX IF NOT EXISTS idx_ee_estado ON equipamentos_eletricos(estado)",
                "CREATE INDEX IF NOT EXISTS idx_ee_localizacao ON equipamentos_eletricos(localizacao_atual)",
                "CREATE INDEX IF NOT EXISTS idx_ee_responsavel ON equipamentos_eletricos(responsavel_atual)",
                
                # Índices para equipamentos manuais
                "CREATE INDEX IF NOT EXISTS idx_em_categoria ON equipamentos_manuais(categoria)",
                "CREATE INDEX IF NOT EXISTS idx_em_estado ON equipamentos_manuais(estado)",
                "CREATE INDEX IF NOT EXISTS idx_em_localizacao ON equipamentos_manuais(localizacao_atual)",
                
                # Índices para movimentações
                "CREATE INDEX IF NOT EXISTS idx_mov_data ON movimentacoes(data_movimentacao)",
                "CREATE INDEX IF NOT EXISTS idx_mov_tipo ON movimentacoes(tipo)",
                "CREATE INDEX IF NOT EXISTS idx_mov_item ON movimentacoes(item_id)",
                "CREATE INDEX IF NOT EXISTS idx_mov_usuario ON movimentacoes(usuario_responsavel)",
                
                # Índices para permissões
                "CREATE INDEX IF NOT EXISTS idx_perm_usuario_modulo ON permissoes_modulos(usuario_id, modulo)",
                "CREATE INDEX IF NOT EXISTS idx_perm_acesso ON permissoes_modulos(usuario_id) WHERE acesso = true",
                
                # Índices para usuários
                "CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email)",
                "CREATE INDEX IF NOT EXISTS idx_usuarios_perfil ON usuarios(perfil)",
                "CREATE INDEX IF NOT EXISTS idx_usuarios_ativo ON usuarios(id) WHERE ativo = true"
            ]
            
            print("Criando índices de performance...")
            created_count = 0
            
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                    created_count += 1
                    print(f"✓ Índice criado: {index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'unknown'}")
                except Exception as e:
                    print(f"✗ Erro ao criar índice: {e}")
            
            conn.commit()
            print(f"Total de índices criados: {created_count}")
            return True
            
        except Exception as e:
            print(f"Erro ao criar índices: {e}")
            return False
    
    def optimize_database_settings(self) -> bool:
        """Otimiza configurações do banco de dados"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Atualizar estatísticas das tabelas
            tables = ['insumos', 'equipamentos_eletricos', 'equipamentos_manuais', 
                     'movimentacoes', 'usuarios', 'permissoes_modulos']
            
            for table in tables:
                cursor.execute(f"ANALYZE {table}")
                print(f"✓ Estatísticas atualizadas para: {table}")
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Erro ao otimizar configurações: {e}")
            return False
    
    def create_materialized_views(self) -> bool:
        """Cria views materializadas para consultas frequentes"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # View para dashboard - estatísticas gerais (usando colunas corretas)
            dashboard_view = """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_stats AS
            SELECT 
                (SELECT COUNT(*) FROM insumos) as total_insumos,
                (SELECT COUNT(*) FROM equipamentos_eletricos) as total_ee,
                (SELECT COUNT(*) FROM equipamentos_manuais) as total_em,
                (SELECT COUNT(*) FROM insumos WHERE quantidade_atual <= quantidade_minima) as itens_criticos,
                (SELECT SUM(quantidade_atual * COALESCE(preco_unitario, 0)) FROM insumos) as valor_total_estoque,
                (SELECT COUNT(*) FROM movimentacoes WHERE DATE(data_movimentacao) = CURRENT_DATE) as movimentacoes_hoje,
                CURRENT_TIMESTAMP as last_updated
            """
            
            # View para relatórios de movimentações (usando colunas corretas)
            mov_view = """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_movimentacoes_resumo AS
            SELECT 
                DATE(data_movimentacao) as data,
                tipo,
                tipo_item,
                COUNT(*) as total_movimentacoes,
                SUM(quantidade) as total_quantidade
            FROM movimentacoes 
            WHERE data_movimentacao >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(data_movimentacao), tipo, tipo_item
            ORDER BY data DESC
            """
            
            # View para estoque crítico (usando colunas corretas)
            estoque_view = """
            CREATE MATERIALIZED VIEW IF NOT EXISTS mv_estoque_critico AS
            SELECT 
                id,
                descricao as nome,
                codigo,
                quantidade_atual as quantidade,
                quantidade_minima as estoque_minimo,
                localizacao,
                CASE 
                    WHEN quantidade_atual = 0 THEN 'CRÍTICO'
                    WHEN quantidade_atual <= quantidade_minima * 0.5 THEN 'URGENTE'
                    WHEN quantidade_atual <= quantidade_minima THEN 'BAIXO'
                    ELSE 'OK'
                END as status_estoque
            FROM insumos
            WHERE quantidade_atual <= quantidade_minima
            ORDER BY (quantidade_atual / NULLIF(quantidade_minima, 0)) ASC
            """
            
            views = [
                ("Dashboard Stats", dashboard_view),
                ("Movimentações Resumo", mov_view),
                ("Estoque Crítico", estoque_view)
            ]
            
            for view_name, view_sql in views:
                try:
                    # Extrair nome da view do SQL
                    view_table_name = view_sql.split('VIEW IF NOT EXISTS')[1].split('AS')[0].strip()
                    cursor.execute(f"DROP MATERIALIZED VIEW IF EXISTS {view_table_name}")
                    cursor.execute(view_sql)
                    conn.commit()
                    print(f"✓ View materializada criada: {view_name}")
                except Exception as e:
                    print(f"✗ Erro ao criar view {view_name}: {e}")
                    conn.rollback()
            
            return True
            
        except Exception as e:
            print(f"Erro ao criar views: {e}")
            return False
    
    def setup_auto_refresh_views(self) -> bool:
        """Configura refresh automático das views materializadas"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Função para refresh das views
            refresh_function = """
            CREATE OR REPLACE FUNCTION refresh_materialized_views()
            RETURNS void AS $$
            BEGIN
                REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_stats;
                REFRESH MATERIALIZED VIEW CONCURRENTLY mv_movimentacoes_resumo;
                REFRESH MATERIALIZED VIEW CONCURRENTLY mv_estoque_critico;
            EXCEPTION WHEN OTHERS THEN
                -- Log erro mas não falha
                RAISE NOTICE 'Erro ao atualizar views: %', SQLERRM;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            cursor.execute(refresh_function)
            conn.commit()
            print("✓ Função de refresh configurada")
            
            return True
            
        except Exception as e:
            print(f"Erro ao configurar auto-refresh: {e}")
            return False
    
    def clean_old_data(self) -> bool:
        """Remove dados antigos desnecessários"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Limpar movimentações muito antigas (mais de 2 anos)
            cursor.execute("""
                DELETE FROM movimentacoes 
                WHERE data_movimentacao < CURRENT_DATE - INTERVAL '2 years'
            """)
            deleted_mov = cursor.rowcount
            
            conn.commit()
            print(f"✓ Removidas {deleted_mov} movimentações antigas")
            
            return True
            
        except Exception as e:
            print(f"Erro ao limpar dados: {e}")
            return False

def run_performance_optimization():
    """Executa otimização completa de performance"""
    print("🚀 INICIANDO OTIMIZAÇÃO DE PERFORMANCE")
    print("=" * 50)
    
    optimizer = PerformanceOptimizer()
    
    # 1. Análise inicial
    print("\n1. 📊 Analisando performance atual...")
    analysis = optimizer.analyze_database_performance()
    
    if analysis.get('active_connections', 0) > 20:
        print("⚠️  Muitas conexões ativas detectadas!")
    
    # 2. Criação de índices
    print("\n2. 📝 Criando índices otimizados...")
    if optimizer.create_performance_indexes():
        print("✅ Índices criados com sucesso!")
    else:
        print("❌ Erro ao criar índices")
    
    # 3. Otimização do banco
    print("\n3. ⚙️ Otimizando configurações do banco...")
    if optimizer.optimize_database_settings():
        print("✅ Configurações otimizadas!")
    else:
        print("❌ Erro na otimização")
    
    # 4. Views materializadas
    print("\n4. 📊 Criando views materializadas...")
    if optimizer.create_materialized_views():
        print("✅ Views materializadas criadas!")
    else:
        print("❌ Erro ao criar views")
    
    # 5. Auto-refresh
    print("\n5. 🔄 Configurando auto-refresh...")
    if optimizer.setup_auto_refresh_views():
        print("✅ Auto-refresh configurado!")
    else:
        print("❌ Erro no auto-refresh")
    
    # 6. Limpeza
    print("\n6. 🧹 Limpando dados antigos...")
    if optimizer.clean_old_data():
        print("✅ Dados antigos removidos!")
    else:
        print("❌ Erro na limpeza")
    
    print("\n🎉 OTIMIZAÇÃO CONCLUÍDA!")
    print("💡 Reinicie o sistema para aplicar todas as melhorias.")

if __name__ == "__main__":
    run_performance_optimization()