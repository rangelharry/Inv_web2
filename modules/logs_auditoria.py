import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database.connection import db
from modules.auth import auth_manager

class LogsAuditoriaManager:
    def __init__(self):
        self.db = db
    
    def get_logs(self, filters=None):
        """Busca logs de auditoria com filtros"""
        try:
            cursor = self.db.conn.cursor()
            
            query = """
                SELECT 
                    l.id, l.data_acao, l.acao, l.modulo, l.tipo_acao,
                    l.detalhes, u.nome as usuario_nome, u.email as usuario_email
                FROM logs_auditoria l
                LEFT JOIN usuarios u ON l.usuario_id = u.id
                WHERE 1=1
            """
            params = []
            
            if filters:
                if filters.get('usuario'):
                    query += " AND u.nome LIKE ?"
                    params.append(f"%{filters['usuario']}%")
                if filters.get('modulo'):
                    query += " AND l.modulo = ?"
                    params.append(filters['modulo'])
                if filters.get('tipo_acao'):
                    query += " AND l.tipo_acao = ?"
                    params.append(filters['tipo_acao'])
                if filters.get('data_inicio'):
                    query += " AND DATE(l.data_acao) >= ?"
                    params.append(filters['data_inicio'])
                if filters.get('data_fim'):
                    query += " AND DATE(l.data_acao) <= ?"
                    params.append(filters['data_fim'])
            
            query += " ORDER BY l.data_acao DESC LIMIT 1000"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            columns = [
                'id', 'data_acao', 'acao', 'modulo', 'tipo_acao',
                'detalhes', 'usuario_nome', 'usuario_email'
            ]
            
            return pd.DataFrame(results, columns=columns) if results else pd.DataFrame()
            
        except Exception as e:
            st.error(f"Erro ao buscar logs: {e}")
            return pd.DataFrame()
    
    def get_modulos_disponiveis(self):
        """Busca módulos disponíveis nos logs"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT DISTINCT modulo FROM logs_auditoria ORDER BY modulo")
            return [row[0] for row in cursor.fetchall()]
        except:
            return []
    
    def get_tipos_acao(self):
        """Retorna tipos de ação disponíveis"""
        return ['CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT']
    
    def get_dashboard_stats(self):
        """Estatísticas para o dashboard"""
        try:
            cursor = self.db.conn.cursor()
            
            # Logs das últimas 24h
            cursor.execute("""
                SELECT COUNT(*) FROM logs_auditoria 
                WHERE datetime(data_acao) >= datetime('now', '-24 hours')
            """)
            logs_24h = cursor.fetchone()[0]
            
            # Logs da última semana
            cursor.execute("""
                SELECT COUNT(*) FROM logs_auditoria 
                WHERE datetime(data_acao) >= datetime('now', '-7 days')
            """)
            logs_semana = cursor.fetchone()[0]
            
            # Módulo mais ativo
            cursor.execute("""
                SELECT modulo, COUNT(*) as total FROM logs_auditoria 
                WHERE datetime(data_acao) >= datetime('now', '-7 days')
                GROUP BY modulo ORDER BY total DESC LIMIT 1
            """)
            modulo_ativo = cursor.fetchone()
            
            # Usuário mais ativo
            cursor.execute("""
                SELECT u.nome, COUNT(*) as total FROM logs_auditoria l
                JOIN usuarios u ON l.usuario_id = u.id
                WHERE datetime(l.data_acao) >= datetime('now', '-7 days')
                GROUP BY u.nome ORDER BY total DESC LIMIT 1
            """)
            usuario_ativo = cursor.fetchone()
            
            return {
                'logs_24h': logs_24h or 0,
                'logs_semana': logs_semana or 0,
                'modulo_ativo': modulo_ativo[0] if modulo_ativo else 'N/A',
                'usuario_ativo': usuario_ativo[0] if usuario_ativo else 'N/A'
            }
        except Exception as e:
            st.error(f"Erro ao calcular estatísticas: {e}")
            return {
                'logs_24h': 0, 'logs_semana': 0,
                'modulo_ativo': 'N/A', 'usuario_ativo': 'N/A'
            }

def show_logs_auditoria_page():
    """Interface principal dos logs de auditoria"""
    
    st.title("📋 Logs de Auditoria")
    
    if not auth_manager.check_permission("logs", "read"):
        st.error("❌ Você não tem permissão para acessar esta página.")
        return
    
    manager = LogsAuditoriaManager()
    
    # Abas principais
    tab1, tab2, tab3 = st.tabs(["📋 Logs", "📊 Estatísticas", "🔍 Análise"])
    
    with tab1:
        st.subheader("Logs de Auditoria do Sistema")
        
        # Filtros
        with st.expander("🔍 Filtros Avançados", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                filtro_usuario = st.text_input("Usuário")
                filtro_modulo = st.selectbox(
                    "Módulo", 
                    ["Todos"] + manager.get_modulos_disponiveis()
                )
            with col2:
                filtro_tipo = st.selectbox(
                    "Tipo de Ação", 
                    ["Todos"] + manager.get_tipos_acao()
                )
                filtro_data_inicio = st.date_input(
                    "Data Início", 
                    value=date.today() - timedelta(days=7)
                )
            with col3:
                filtro_data_fim = st.date_input("Data Fim", value=date.today())
        
        # Aplicar filtros
        filters = {}
        if filtro_usuario:
            filters['usuario'] = filtro_usuario
        if filtro_modulo != "Todos":
            filters['modulo'] = filtro_modulo
        if filtro_tipo != "Todos":
            filters['tipo_acao'] = filtro_tipo
        if filtro_data_inicio:
            filters['data_inicio'] = filtro_data_inicio.strftime('%Y-%m-%d')
        if filtro_data_fim:
            filters['data_fim'] = filtro_data_fim.strftime('%Y-%m-%d')
        
        # Buscar logs
        df = manager.get_logs(filters)
        
        if not df.empty:
            # Formatação de data
            df['data_formatada'] = pd.to_datetime(df['data_acao']).dt.strftime('%d/%m/%Y %H:%M:%S')
            
            st.dataframe(
                df[['data_formatada', 'usuario_nome', 'modulo', 'tipo_acao', 'acao']],
                column_config={
                    'data_formatada': 'Data/Hora',
                    'usuario_nome': 'Usuário',
                    'modulo': 'Módulo',
                    'tipo_acao': 'Tipo',
                    'acao': 'Ação'
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Detalhes do log selecionado
            st.subheader("Detalhes dos Logs")
            selected_log = st.selectbox(
                "Selecione um log para ver detalhes:",
                options=range(len(df)),
                format_func=lambda x: f"{df.iloc[x]['data_formatada']} - {df.iloc[x]['usuario_nome']} - {df.iloc[x]['acao']}"
            )
            
            if selected_log is not None:
                log_details = df.iloc[selected_log]
                st.info(f"**Detalhes:** {log_details['detalhes'] or 'Nenhum detalhe adicional'}")
        else:
            st.info("📭 Nenhum log encontrado com os filtros aplicados.")
    
    with tab2:
        st.subheader("Estatísticas dos Logs")
        
        stats = manager.get_dashboard_stats()
        
        # Cards de estatísticas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Logs (24h)", stats['logs_24h'])
        
        with col2:
            st.metric("Logs (Semana)", stats['logs_semana'])
        
        with col3:
            st.metric("Módulo Mais Ativo", stats['modulo_ativo'])
        
        with col4:
            st.metric("Usuário Mais Ativo", stats['usuario_ativo'])
        
        # Gráficos
        df_stats = manager.get_logs()
        
        if not df_stats.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico por módulo
                modulo_counts = df_stats['modulo'].value_counts().head(10)
                st.plotly_chart(
                    {
                        'data': [{
                            'type': 'bar',
                            'x': modulo_counts.values.tolist(),
                            'y': modulo_counts.index.tolist(),
                            'orientation': 'h'
                        }],
                        'layout': {
                            'title': 'Atividade por Módulo',
                            'xaxis': {'title': 'Quantidade'},
                            'yaxis': {'title': 'Módulo'}
                        }
                    },
                    use_container_width=True
                )
            
            with col2:
                # Gráfico por tipo de ação
                tipo_counts = df_stats['tipo_acao'].value_counts()
                st.plotly_chart(
                    {
                        'data': [{
                            'type': 'pie',
                            'labels': tipo_counts.index.tolist(),
                            'values': tipo_counts.values.tolist()
                        }],
                        'layout': {'title': 'Distribuição por Tipo de Ação'}
                    },
                    use_container_width=True
                )
    
    with tab3:
        st.subheader("Análise de Atividade")
        
        df_analysis = manager.get_logs({
            'data_inicio': (date.today() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'data_fim': date.today().strftime('%Y-%m-%d')
        })
        
        if not df_analysis.empty:
            # Atividade por usuário
            st.markdown("### 👤 Atividade por Usuário (Últimos 30 dias)")
            user_activity = df_analysis.groupby('usuario_nome').agg({
                'id': 'count',
                'tipo_acao': lambda x: x.value_counts().to_dict()
            }).rename(columns={'id': 'total_acoes'})
            
            st.dataframe(
                user_activity.sort_values('total_acoes', ascending=False),
                column_config={
                    'total_acoes': 'Total de Ações',
                    'tipo_acao': 'Tipos de Ação'
                },
                use_container_width=True
            )
            
            # Atividade por horário
            st.markdown("### 🕐 Atividade por Horário")
            df_analysis['hora'] = pd.to_datetime(df_analysis['data_acao']).dt.hour
            hourly_activity = df_analysis.groupby('hora').size()
            
            st.plotly_chart(
                {
                    'data': [{
                        'type': 'bar',
                        'x': hourly_activity.index.tolist(),
                        'y': hourly_activity.values.tolist()
                    }],
                    'layout': {
                        'title': 'Atividade por Horário do Dia',
                        'xaxis': {'title': 'Hora'},
                        'yaxis': {'title': 'Número de Ações'}
                    }
                },
                use_container_width=True
            )
        else:
            st.info("📊 Dados insuficientes para análise.")

# Instância global
logs_auditoria_manager = LogsAuditoriaManager()