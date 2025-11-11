"""
Sistema de Cache para melhorar performance do Streamlit
"""

import streamlit as st
import pandas as pd
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional
from database.connection import db

class StreamlitCache:
    """Cache personalizado para otimizar consultas frequentes"""
    
    def __init__(self):
        self.db = db
    
    @staticmethod
    def cache_data(ttl: int = 300):
        """Decorator para cache de dados com TTL (Time To Live)"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Criar chave única baseada na função e argumentos
                cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
                
                # Verificar se existe cache válido
                if cache_key in st.session_state:
                    cached_data, timestamp = st.session_state[cache_key]
                    if time.time() - timestamp < ttl:
                        return cached_data
                
                # Executar função e cachear resultado
                result = func(*args, **kwargs)
                st.session_state[cache_key] = (result, time.time())
                return result
            
            return wrapper
        return decorator
    
    @staticmethod
    @st.cache_data(ttl=300)  # Cache por 5 minutos
    def get_dashboard_stats() -> Dict[str, Any]:
        """Busca estatísticas do dashboard com cache"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Verificar se existe a view materializada
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'mv_dashboard_stats'
                )
            """)
            
            view_exists = cursor.fetchone()[0]
            
            if view_exists:
                # Usar view materializada se existe
                cursor.execute("SELECT * FROM mv_dashboard_stats")
                result = cursor.fetchone()
                if result:
                    return {
                        'total_insumos': result[0] if isinstance(result, tuple) else result['total_insumos'],
                        'total_ee': result[1] if isinstance(result, tuple) else result['total_ee'],
                        'total_em': result[2] if isinstance(result, tuple) else result['total_em'],
                        'itens_criticos': result[3] if isinstance(result, tuple) else result['itens_criticos'],
                        'valor_total_estoque': result[4] if isinstance(result, tuple) else result['valor_total_estoque'],
                        'movimentacoes_hoje': result[5] if isinstance(result, tuple) else result['movimentacoes_hoje']
                    }
            
            # Fallback para consultas individuais
            stats = {}
            
            # Helper para extrair resultado de forma segura
            def safe_result(result, column_name='count', default=0):
                if result is None:
                    return default
                # Se for RealDictRow, acessar por nome
                if hasattr(result, 'get'):
                    return result.get(column_name, default)
                # Se for tuple/list, usar índice
                if hasattr(result, '__getitem__') and len(result) > 0:
                    return result[0] if result[0] is not None else default
                return default
            
            # Total de insumos ATIVOS
            cursor.execute("SELECT COUNT(*) FROM insumos WHERE ativo = TRUE")
            stats['total_insumos'] = safe_result(cursor.fetchone())
            
            # Total de equipamentos elétricos ATIVOS
            cursor.execute("SELECT COUNT(*) FROM equipamentos_eletricos WHERE ativo = TRUE")
            stats['total_ee'] = safe_result(cursor.fetchone())
            
            # Total de equipamentos manuais ATIVOS
            cursor.execute("SELECT COUNT(*) FROM equipamentos_manuais WHERE ativo = TRUE")
            stats['total_em'] = safe_result(cursor.fetchone())
            
            # Itens críticos (apenas ativos)
            cursor.execute("SELECT COUNT(*) FROM insumos WHERE ativo = TRUE AND quantidade_atual <= quantidade_minima")
            stats['itens_criticos'] = safe_result(cursor.fetchone())
            
            # Valor total do estoque (apenas ativos)
            cursor.execute("SELECT COALESCE(SUM(quantidade_atual * preco_unitario), 0) as sum FROM insumos WHERE ativo = TRUE")
            stats['valor_total_estoque'] = safe_result(cursor.fetchone(), 'sum')
            
            # Movimentações hoje
            cursor.execute("SELECT COUNT(*) FROM movimentacoes WHERE DATE(data_movimentacao) = CURRENT_DATE")
            stats['movimentacoes_hoje'] = safe_result(cursor.fetchone())
            
            return stats
            
        except Exception as e:
            print(f"Erro ao buscar estatísticas: {e}")
            return {
                'total_insumos': 0,
                'total_ee': 0,
                'total_em': 0,
                'itens_criticos': 0,
                'valor_total_estoque': 0,
                'movimentacoes_hoje': 0
            }
    
    @staticmethod
    @st.cache_data(ttl=600)  # Cache por 10 minutos
    def get_items_criticos() -> pd.DataFrame:
        """Busca itens com estoque crítico"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Verificar se existe view materializada
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'mv_estoque_critico'
                )
            """)
            
            result = cursor.fetchone()
            view_exists = result[0] if isinstance(result, (tuple, list)) else result.get('exists', False)
            
            if view_exists:
                # Usar view materializada
                cursor.execute("SELECT * FROM mv_estoque_critico")
            else:
                # Consulta direta
                query = """
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
                cursor.execute(query)
            
            # Converter resultados para DataFrame manualmente
            results = cursor.fetchall()
            if results:
                columns = [desc[0] for desc in cursor.description]
                data = []
                for row in results:
                    if isinstance(row, dict):
                        data.append(row)
                    else:
                        data.append(dict(zip(columns, row)))
                
                return pd.DataFrame(data)
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"Erro ao buscar itens críticos: {e}")
            return pd.DataFrame()
    
    @staticmethod
    @st.cache_data(ttl=1800)  # Cache por 30 minutos
    def get_movimentacoes_resumo(days: int = 30) -> pd.DataFrame:
        """Busca resumo de movimentações dos últimos N dias"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            query = """
            SELECT 
                DATE(data_movimentacao) as data,
                tipo,
                tipo_item,
                COUNT(*) as total_movimentacoes,
                SUM(quantidade) as total_quantidade
            FROM movimentacoes 
            WHERE data_movimentacao >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(data_movimentacao), tipo, tipo_item
            ORDER BY data DESC
            """
            
            return pd.read_sql(query, conn, params=[days])
            
        except Exception as e:
            print(f"Erro ao buscar resumo de movimentações: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def clear_cache():
        """Limpa todo o cache da sessão"""
        # Limpar cache do Streamlit
        st.cache_data.clear()
        
        # Limpar cache da sessão
        keys_to_remove = [key for key in st.session_state.keys() if 'cache' in key.lower()]
        for key in keys_to_remove:
            del st.session_state[key]
    
    @staticmethod
    def refresh_materialized_views():
        """Força refresh das views materializadas"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            views = ['mv_dashboard_stats', 'mv_estoque_critico', 'mv_movimentacoes_resumo']
            
            for view in views:
                try:
                    cursor.execute(f"REFRESH MATERIALIZED VIEW {view}")
                    print(f"✓ View {view} atualizada")
                except Exception as e:
                    print(f"✗ Erro ao atualizar {view}: {e}")
            
            conn.commit()
            # Limpar cache após refresh
            StreamlitCache.clear_cache()
            
        except Exception as e:
            print(f"Erro no refresh das views: {e}")

# Decorators utilitários
def performance_monitor(func: Callable) -> Callable:
    """Decorator para monitorar performance de funções"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        if execution_time > 1.0:  # Alertar se > 1 segundo
            print(f"⚠️ Função lenta: {func.__name__} ({execution_time:.2f}s)")
        
        return result
    
    return wrapper

def lazy_load(func: Callable) -> Callable:
    """Decorator para carregamento lazy de dados pesados"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Verificar se dados já estão carregados na sessão
        cache_key = f"lazy_{func.__name__}"
        
        if cache_key not in st.session_state:
            with st.spinner(f"Carregando {func.__name__}..."):
                st.session_state[cache_key] = func(*args, **kwargs)
        
        return st.session_state[cache_key]
    
    return wrapper