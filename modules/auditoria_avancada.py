"""
Sistema de Auditoria Avançada - Logs Detalhados
Captura todas as ações do sistema com contexto completo
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json
import traceback
from database.connection import db
from modules.auth import auth_manager

class AuditoriaAvancada:
    def __init__(self):
        self.db = db
        self._criar_tabelas_auditoria()
    
    def _criar_tabelas_auditoria(self):
        """Cria tabelas de auditoria se não existirem"""
        try:
            conn = self.db.get_connection()
            if not conn:
                return
            
            cursor = conn.cursor()
            
            # Tabela principal de auditoria
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auditoria_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usuario_id INTEGER REFERENCES usuarios(id),
                    usuario_nome VARCHAR(255),
                    usuario_email VARCHAR(255),
                    usuario_perfil VARCHAR(50),
                    sessao_id VARCHAR(255),
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    modulo VARCHAR(100) NOT NULL,
                    acao VARCHAR(100) NOT NULL,
                    entidade VARCHAR(100),
                    entidade_id INTEGER,
                    dados_antes JSONB,
                    dados_depois JSONB,
                    dados_contexto JSONB,
                    resultado VARCHAR(20) DEFAULT 'sucesso',
                    erro_detalhes TEXT,
                    tempo_execucao_ms INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de sessões de auditoria
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auditoria_sessoes (
                    id SERIAL PRIMARY KEY,
                    usuario_id INTEGER REFERENCES usuarios(id),
                    sessao_id VARCHAR(255) UNIQUE,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    inicio_sessao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fim_sessao TIMESTAMP,
                    ativa BOOLEAN DEFAULT TRUE,
                    total_acoes INTEGER DEFAULT 0,
                    ultima_atividade TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela de tentativas de acesso
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auditoria_acessos (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    email VARCHAR(255),
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    resultado VARCHAR(20), -- 'sucesso', 'falha', 'bloqueado'
                    motivo_falha TEXT,
                    tentativas_consecutivas INTEGER DEFAULT 1
                )
            """)
            
            # Índices para performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_logs_timestamp ON auditoria_logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_logs_usuario ON auditoria_logs(usuario_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_logs_modulo ON auditoria_logs(modulo)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_logs_acao ON auditoria_logs(acao)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_sessoes_usuario ON auditoria_sessoes(usuario_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_acessos_email ON auditoria_acessos(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_acessos_timestamp ON auditoria_acessos(timestamp)")
            
            conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Erro ao criar tabelas de auditoria: {e}")
    
    def registrar_acao(self, 
                      modulo: str,
                      acao: str,
                      entidade: Optional[str] = None,
                      entidade_id: Optional[int] = None,
                      dados_antes: Optional[Dict] = None,
                      dados_depois: Optional[Dict] = None,
                      dados_contexto: Optional[Dict] = None,
                      resultado: str = 'sucesso',
                      erro_detalhes: Optional[str] = None,
                      tempo_execucao_ms: Optional[int] = None):
        """
        Registra uma ação no log de auditoria
        
        Args:
            modulo: Módulo do sistema (ex: 'movimentacoes', 'usuarios')
            acao: Ação realizada (ex: 'criar', 'editar', 'excluir')
            entidade: Tipo de entidade (ex: 'insumo', 'equipamento')
            entidade_id: ID da entidade afetada
            dados_antes: Estado antes da alteração
            dados_depois: Estado depois da alteração
            dados_contexto: Dados adicionais de contexto
            resultado: 'sucesso' ou 'erro'
            erro_detalhes: Detalhes do erro se houver
            tempo_execucao_ms: Tempo de execução em millisegundos
        """
        try:
            conn = self.db.get_connection()
            if not conn:
                return
            
            cursor = conn.cursor()
            
            # Obter dados do usuário atual
            user_data = auth_manager.get_user_data()
            
            # Obter dados da sessão (simulado - em produção viria do request)
            import uuid
            sessao_id = str(uuid.uuid4())[:8]  # Simplificado
            ip_address = "127.0.0.1"  # Em produção, pegar do request
            user_agent = "Streamlit App"  # Em produção, pegar do request
            
            cursor.execute("""
                INSERT INTO auditoria_logs (
                    usuario_id, usuario_nome, usuario_email, usuario_perfil,
                    sessao_id, ip_address, user_agent,
                    modulo, acao, entidade, entidade_id,
                    dados_antes, dados_depois, dados_contexto,
                    resultado, erro_detalhes, tempo_execucao_ms
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_data.get('id') if user_data else None,
                user_data.get('nome') if user_data else 'Sistema',
                user_data.get('email') if user_data else None,
                user_data.get('perfil') if user_data else None,
                sessao_id,
                ip_address,
                user_agent,
                modulo,
                acao,
                entidade,
                entidade_id,
                json.dumps(dados_antes) if dados_antes else None,
                json.dumps(dados_depois) if dados_depois else None,
                json.dumps(dados_contexto) if dados_contexto else None,
                resultado,
                erro_detalhes,
                tempo_execucao_ms
            ))
            
            conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Erro ao registrar auditoria: {e}")
    
    def registrar_tentativa_acesso(self, email: str, resultado: str, motivo_falha: str = None):
        """Registra tentativas de login"""
        try:
            conn = self.db.get_connection()
            if not conn:
                return
            
            cursor = conn.cursor()
            
            # Contar tentativas consecutivas
            cursor.execute("""
                SELECT COUNT(*) FROM auditoria_acessos 
                WHERE email = %s AND resultado = 'falha' 
                AND timestamp > NOW() - INTERVAL '15 minutes'
            """, (email,))
            
            tentativas = cursor.fetchone()[0] if cursor.rowcount > 0 else 0
            
            cursor.execute("""
                INSERT INTO auditoria_acessos (
                    email, ip_address, user_agent, resultado, 
                    motivo_falha, tentativas_consecutivas
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                email,
                "127.0.0.1",  # Em produção, pegar do request
                "Streamlit App",  # Em produção, pegar do request
                resultado,
                motivo_falha,
                tentativas + 1 if resultado == 'falha' else 0
            ))
            
            conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Erro ao registrar tentativa de acesso: {e}")
    
    def get_logs_auditoria(self, filtros: Dict = None) -> pd.DataFrame:
        """Busca logs de auditoria com filtros"""
        try:
            conn = self.db.get_connection()
            if not conn:
                return pd.DataFrame()
            
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    id, timestamp, usuario_nome, usuario_email, usuario_perfil,
                    modulo, acao, entidade, entidade_id,
                    resultado, erro_detalhes, tempo_execucao_ms,
                    ip_address, user_agent
                FROM auditoria_logs
                WHERE 1=1
            """
            params = []
            
            if filtros:
                if filtros.get('data_inicio'):
                    query += " AND timestamp >= %s"
                    params.append(filtros['data_inicio'])
                
                if filtros.get('data_fim'):
                    query += " AND timestamp <= %s"
                    params.append(filtros['data_fim'])
                
                if filtros.get('usuario'):
                    query += " AND usuario_nome ILIKE %s"
                    params.append(f"%{filtros['usuario']}%")
                
                if filtros.get('modulo'):
                    query += " AND modulo = %s"
                    params.append(filtros['modulo'])
                
                if filtros.get('acao'):
                    query += " AND acao = %s"
                    params.append(filtros['acao'])
                
                if filtros.get('resultado'):
                    query += " AND resultado = %s"
                    params.append(filtros['resultado'])
            
            query += " ORDER BY timestamp DESC LIMIT 1000"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if results:
                columns = [desc[0] for desc in cursor.description]
                return pd.DataFrame([dict(zip(columns, row)) for row in results])
            
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"Erro ao buscar logs de auditoria: {e}")
            return pd.DataFrame()
    
    def get_estatisticas_auditoria(self) -> Dict:
        """Retorna estatísticas de auditoria"""
        try:
            conn = self.db.get_connection()
            if not conn:
                return {}
            
            cursor = conn.cursor()
            
            # Verificar se a tabela existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'auditoria_logs'
                )
            """)
            
            if not cursor.fetchone()[0]:
                # Criar tabela se não existir
                self._criar_tabelas_auditoria()
                return {
                    'total_logs': 0,
                    'sucessos': 0,
                    'erros': 0,
                    'usuarios_ativos': 0,
                    'logs_24h': 0,
                    'top_modulos': [],
                    'top_acoes': []
                }
            
            # Estatísticas gerais
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_logs,
                    COUNT(CASE WHEN resultado = 'sucesso' THEN 1 END) as sucessos,
                    COUNT(CASE WHEN resultado = 'erro' THEN 1 END) as erros,
                    COUNT(DISTINCT usuario_id) as usuarios_ativos,
                    COUNT(CASE WHEN timestamp > NOW() - INTERVAL '24 hours' THEN 1 END) as logs_24h
                FROM auditoria_logs
            """)
            
            stats = cursor.fetchone()
            
            # Top módulos
            cursor.execute("""
                SELECT modulo, COUNT(*) as count
                FROM auditoria_logs
                WHERE timestamp > NOW() - INTERVAL '7 days'
                GROUP BY modulo
                ORDER BY count DESC
                LIMIT 10
            """)
            
            top_modulos = cursor.fetchall()
            
            # Top ações
            cursor.execute("""
                SELECT acao, COUNT(*) as count
                FROM auditoria_logs
                WHERE timestamp > NOW() - INTERVAL '7 days'
                GROUP BY acao
                ORDER BY count DESC
                LIMIT 10
            """)
            
            top_acoes = cursor.fetchall()
            
            return {
                'total_logs': stats[0] if stats else 0,
                'sucessos': stats[1] if stats else 0,
                'erros': stats[2] if stats else 0,
                'usuarios_ativos': stats[3] if stats else 0,
                'logs_24h': stats[4] if stats else 0,
                'top_modulos': [{'modulo': row[0], 'count': row[1]} for row in top_modulos],
                'top_acoes': [{'acao': row[0], 'count': row[1]} for row in top_acoes]
            }
            
        except Exception as e:
            st.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def exportar_logs(self, filtros: Dict = None, formato: str = 'csv') -> str:
        """Exporta logs de auditoria"""
        try:
            df = self.get_logs_auditoria(filtros)
            
            if df.empty:
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if formato == 'csv':
                filename = f"auditoria_logs_{timestamp}.csv"
                filepath = f"backups/{filename}"
                df.to_csv(filepath, index=False, encoding='utf-8')
            elif formato == 'json':
                filename = f"auditoria_logs_{timestamp}.json"
                filepath = f"backups/{filename}"
                df.to_json(filepath, orient='records', date_format='iso')
            
            return filepath
            
        except Exception as e:
            st.error(f"Erro ao exportar logs: {e}")
            return None

# Decorador para auditoria automática
def auditar_acao(modulo: str, acao: str, entidade: str = None):
    """Decorador para auditoria automática de funções"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            auditoria = AuditoriaAvancada()
            
            try:
                start_time = datetime.now()
                
                # Capturar dados antes (se aplicável)
                dados_antes = None
                if entidade and len(args) > 1 and isinstance(args[1], (int, str)):
                    # Tentar capturar estado antes da alteração
                    pass
                
                # Executar função
                resultado = func(*args, **kwargs)
                
                # Calcular tempo de execução
                tempo_execucao = (datetime.now() - start_time).total_seconds() * 1000
                
                # Registrar sucesso
                auditoria.registrar_acao(
                    modulo=modulo,
                    acao=acao,
                    entidade=entidade,
                    dados_contexto={'args': str(args), 'kwargs': str(kwargs)},
                    resultado='sucesso',
                    tempo_execucao_ms=int(tempo_execucao)
                )
                
                return resultado
                
            except Exception as e:
                # Registrar erro
                tempo_execucao = (datetime.now() - start_time).total_seconds() * 1000
                
                auditoria.registrar_acao(
                    modulo=modulo,
                    acao=acao,
                    entidade=entidade,
                    dados_contexto={'args': str(args), 'kwargs': str(kwargs)},
                    resultado='erro',
                    erro_detalhes=str(e),
                    tempo_execucao_ms=int(tempo_execucao)
                )
                
                raise e
                
        return wrapper
    return decorator

# Interface Streamlit
def show_auditoria_interface():
    """Interface principal de auditoria"""
    st.title("🔍 Auditoria Completa - Logs Detalhados")
    
    auditoria = AuditoriaAvancada()
    
    # Abas
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📋 Logs", "🔐 Acessos", "📤 Exportar"])
    
    with tab1:
        st.header("Dashboard de Auditoria")
        
        stats = auditoria.get_estatisticas_auditoria()
        
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Logs", stats.get('total_logs', 0))
            with col2:
                st.metric("Sucessos", stats.get('sucessos', 0))
            with col3:
                st.metric("Erros", stats.get('erros', 0))
            with col4:
                st.metric("Logs 24h", stats.get('logs_24h', 0))
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Top Módulos (7 dias)")
                if stats.get('top_modulos'):
                    df_modulos = pd.DataFrame(stats['top_modulos'])
                    st.bar_chart(df_modulos.set_index('modulo'))
            
            with col2:
                st.subheader("Top Ações (7 dias)")
                if stats.get('top_acoes'):
                    df_acoes = pd.DataFrame(stats['top_acoes'])
                    st.bar_chart(df_acoes.set_index('acao'))
    
    with tab2:
        st.header("Logs de Auditoria")
        
        # Filtros
        with st.expander("🔍 Filtros", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                data_inicio = st.date_input("Data Início")
                modulo_filter = st.selectbox("Módulo", ["Todos", "movimentacoes", "usuarios", "insumos", "equipamentos"])
            
            with col2:
                data_fim = st.date_input("Data Fim")
                acao_filter = st.selectbox("Ação", ["Todas", "criar", "editar", "excluir", "login", "logout"])
            
            with col3:
                usuario_filter = st.text_input("Usuário")
                resultado_filter = st.selectbox("Resultado", ["Todos", "sucesso", "erro"])
        
        # Buscar logs
        filtros = {}
        if data_inicio:
            filtros['data_inicio'] = data_inicio
        if data_fim:
            filtros['data_fim'] = data_fim
        if modulo_filter != "Todos":
            filtros['modulo'] = modulo_filter
        if acao_filter != "Todas":
            filtros['acao'] = acao_filter
        if usuario_filter:
            filtros['usuario'] = usuario_filter
        if resultado_filter != "Todos":
            filtros['resultado'] = resultado_filter
        
        df_logs = auditoria.get_logs_auditoria(filtros)
        
        if not df_logs.empty:
            st.dataframe(
                df_logs,
                use_container_width=True,
                column_config={
                    "timestamp": st.column_config.DatetimeColumn("Data/Hora"),
                    "usuario_nome": "Usuário",
                    "modulo": "Módulo",
                    "acao": "Ação",
                    "entidade": "Entidade",
                    "resultado": st.column_config.SelectboxColumn("Resultado", options=["sucesso", "erro"])
                }
            )
        else:
            st.info("Nenhum log encontrado com os filtros aplicados")
    
    with tab3:
        st.header("Tentativas de Acesso")
        st.info("Funcionalidade em desenvolvimento - Logs de tentativas de login")
    
    with tab4:
        st.header("Exportar Logs")
        
        col1, col2 = st.columns(2)
        
        with col1:
            formato_export = st.selectbox("Formato", ["csv", "json"])
            periodo_export = st.selectbox("Período", ["Últimos 7 dias", "Últimos 30 dias", "Personalizado"])
        
        with col2:
            if st.button("📤 Exportar Logs", type="primary"):
                # Aplicar filtros de período
                filtros_export = {}
                if periodo_export == "Últimos 7 dias":
                    filtros_export['data_inicio'] = datetime.now() - timedelta(days=7)
                elif periodo_export == "Últimos 30 dias":
                    filtros_export['data_inicio'] = datetime.now() - timedelta(days=30)
                
                filepath = auditoria.exportar_logs(filtros_export, formato_export)
                
                if filepath:
                    st.success(f"Logs exportados para: {filepath}")
                else:
                    st.error("Erro ao exportar logs")

if __name__ == "__main__":
    show_auditoria_interface()