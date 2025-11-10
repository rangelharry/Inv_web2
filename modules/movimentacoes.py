
import streamlit as st
import pandas as pd
from datetime import datetime
from database.connection import db
from modules.auth import auth_manager
from typing import Any
# Imports dos modais
from modules.movimentacao_modal import (
    show_movimentacao_modal_insumo,  # type: ignore
    show_movimentacao_modal_equipamento_eletrico,  # type: ignore
    show_movimentacao_modal_equipamento_manual  # type: ignore
)


# Classe MovimentacoesManager
class MovimentacoesManager:
    def __init__(self):
        self.db = db

    def create_movimentacao(self, data: dict[str, Any], usuario_id: int) -> int | None:
        """Cria uma nova movimentação"""
        try:
            conn = self.db.get_connection()
            if not conn:
                return None
                
            # Garantir que a conexão esteja limpa
            if hasattr(conn, 'rollback'):
                conn.rollback()
            
            cursor = conn.cursor()
                
            # Verifica se há quantidade suficiente para saída (apenas para insumos)
            if data['tipo'] == 'Saída' and data.get('tipo_item') == 'insumo':
                cursor.execute("""
                    SELECT quantidade_atual FROM insumos WHERE id = %s AND ativo = TRUE
                """, (data['item_id'],))
                result = cursor.fetchone()
                
                if result:
                    # Tratamento robusto para diferentes tipos de resultado
                    if isinstance(result, dict):
                        quantidade_atual = result.get('quantidade_atual', 0)
                    else:
                        quantidade_atual = result[0] if result else 0
                else:
                    quantidade_atual = 0
                    
                if quantidade_atual < data['quantidade']:
                    st.error(f"❌ Quantidade insuficiente! Disponível: {quantidade_atual}")
                    return None
                    
            # Inserção da movimentação
            cursor.execute(
                """
                INSERT INTO movimentacoes (
                    item_id, tipo, tipo_item, quantidade, motivo,
                    obra_origem_id, obra_destino_id,
                    responsavel_origem_id, responsavel_destino_id,
                    valor_unitario, observacoes, data_movimentacao, usuario_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    data['item_id'], data['tipo'], data['tipo_item'], data['quantidade'],
                    data.get('motivo'),
                    data.get('obra_origem_id'), data.get('obra_destino_id'),
                    data.get('responsavel_origem_id'), data.get('responsavel_destino_id'),
                    data.get('valor_unitario'), data.get('observacoes'), 
                    datetime.now(), usuario_id
                )
            )
            
            # Recuperar o ID da movimentação criada
            result = cursor.fetchone()
            movimentacao_id = None
            
            if result:
                if isinstance(result, dict):
                    movimentacao_id = result.get('id')
                else:
                    movimentacao_id = result[0] if result else None
                    
            conn.commit()
            
            # Atualizar estoque se for movimentação de insumo
            if data.get('tipo_item') == 'insumo' and movimentacao_id:
                self._atualizar_estoque_insumo(data['item_id'], data['quantidade'], data['tipo'])
            
            return movimentacao_id
            
        except Exception as e:
            # Fazer rollback explícito para limpar o estado da transação
            conn = self.db.get_connection()
            if conn and hasattr(conn, 'rollback'):
                conn.rollback()
            st.error(f"Erro ao registrar movimentação: {e}")
            return None
    
    def _atualizar_estoque_insumo(self, item_id: int, quantidade: int, tipo: str) -> None:
        """Atualiza estoque do insumo após movimentação"""
        try:
            conn = self.db.get_connection()
            if not conn:
                return
                
            cursor = conn.cursor()
            
            if tipo == 'Entrada':
                cursor.execute("""
                    UPDATE insumos 
                    SET quantidade_atual = quantidade_atual + %s,
                        data_ultima_entrada = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (quantidade, item_id))
            elif tipo == 'Saída':
                cursor.execute("""
                    UPDATE insumos 
                    SET quantidade_atual = quantidade_atual - %s,
                        data_ultima_saida = CURRENT_TIMESTAMP
                    WHERE id = %s AND quantidade_atual >= %s
                """, (quantidade, item_id, quantidade))
                
            conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
            st.error(f"Erro ao atualizar estoque: {e}")

    def get_movimentacoes(self, filters: dict[str, Any]) -> pd.DataFrame:
        """Busca movimentações conforme filtros"""
        try:
            conn = self.db.get_connection()
            if not conn:
                return pd.DataFrame()
                
            # Garantir que a conexão esteja limpa
            if hasattr(conn, 'rollback'):
                conn.rollback()
            
            cursor = conn.cursor()
            
            query = """
                SELECT m.id, m.data_movimentacao, m.tipo, m.quantidade, m.motivo,
                       o1.nome as obra_origem, o2.nome as obra_destino,
                       r1.nome as responsavel_origem, r2.nome as responsavel_destino,
                       m.valor_unitario, m.observacoes,
                       COALESCE(i.descricao, ee.nome, em.descricao) as item_nome, 
                       COALESCE(i.codigo, ee.codigo, em.codigo) as codigo, 
                       u.nome as usuario_nome,
                       m.tipo_item
                FROM movimentacoes m
                LEFT JOIN insumos i ON m.item_id = i.id AND m.tipo_item = 'insumo'
                LEFT JOIN equipamentos_eletricos ee ON m.item_id = ee.id AND m.tipo_item = 'equipamento_eletrico'
                LEFT JOIN equipamentos_manuais em ON m.item_id = em.id AND m.tipo_item = 'equipamento_manual'
                LEFT JOIN obras o1 ON m.obra_origem_id = o1.id
                LEFT JOIN obras o2 ON m.obra_destino_id = o2.id
                LEFT JOIN responsaveis r1 ON m.responsavel_origem_id = r1.id
                LEFT JOIN responsaveis r2 ON m.responsavel_destino_id = r2.id
                LEFT JOIN usuarios u ON m.usuario_id = u.id
                WHERE 1=1
            """
            params: list[Any] = []
            
            if filters.get('item_nome'):
                query += """ AND (
                    i.descricao LIKE %s OR 
                    ee.nome LIKE %s OR 
                    em.descricao LIKE %s
                )"""
                busca = f"%{filters['item_nome']}%"
                params.extend([busca, busca, busca])
                
            if filters.get('tipo'):
                query += " AND m.tipo = %s"
                params.append(filters['tipo'])
                
            if filters.get('obra_origem'):
                query += " AND o1.nome LIKE %s"
                params.append(f"%{filters['obra_origem']}%")
                
            if filters.get('obra_destino'):
                query += " AND o2.nome LIKE %s"
                params.append(f"%{filters['obra_destino']}%")
                
            if filters.get('responsavel_origem'):
                query += " AND r1.nome LIKE %s"
                params.append(f"%{filters['responsavel_origem']}%")
                
            if filters.get('responsavel_destino'):
                query += " AND r2.nome LIKE %s"
                params.append(f"%{filters['responsavel_destino']}%")
                
            if filters.get('data_inicio'):
                query += " AND m.data_movimentacao::date >= %s"
                params.append(filters['data_inicio'])
                
            if filters.get('data_fim'):
                query += " AND m.data_movimentacao::date <= %s"
                params.append(filters['data_fim'])
                
            query += " ORDER BY m.data_movimentacao DESC"
            cursor.execute(query, params)  # type: ignore
            results = cursor.fetchall()
            
            if not results:
                return pd.DataFrame()
                
            # Tratamento robusto de resultados
            movimentacoes = []
            for row in results:
                if isinstance(row, dict):
                    movimentacoes.append(dict(row))
                else:
                    columns = [desc[0] for desc in cursor.description]
                    movimentacoes.append(dict(zip(columns, row)))
                    
            return pd.DataFrame(movimentacoes)
            
        except Exception as e:
            # Fazer rollback explícito para limpar o estado da transação
            conn = self.db.get_connection()
            if conn and hasattr(conn, 'rollback'):
                conn.rollback()
            st.error(f"Erro ao buscar movimentações: {e}")
            return pd.DataFrame()

    def get_items_para_movimentacao(self) -> list[dict[str, Any]]:
        """Busca itens disponíveis para movimentação"""
        try:
            conn = self.db.get_connection()
            if not conn:
                return []
                
            # Garantir que a conexão esteja limpa
            if hasattr(conn, 'rollback'):
                conn.rollback()
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, descricao, codigo, quantidade_atual, unidade
                FROM insumos 
                WHERE ativo = TRUE
                ORDER BY descricao
            """)
            
            results = cursor.fetchall()
            if not results:
                return []
                
            # Tratamento robusto de resultados
            items = []
            for row in results:
                if isinstance(row, dict):
                    items.append(dict(row))
                else:
                    columns = [desc[0] for desc in cursor.description]
                    items.append(dict(zip(columns, row)))
                    
            return items
            
        except Exception as e:
            # Fazer rollback explícito para limpar o estado da transação
            conn = self.db.get_connection()
            if conn and hasattr(conn, 'rollback'):
                conn.rollback()
            st.error(f"Erro ao buscar itens: {e}")
            return []

    def get_dashboard_stats(self) -> dict[str, int]:
        """Estatísticas para o dashboard"""
        try:
            cursor = conn.cursor() if conn else None
            if not cursor:
                return None

            # Movimentações do mês atual
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN tipo = 'Entrada' THEN 1 ELSE 0 END) as entradas,
                    SUM(CASE WHEN tipo = 'Saída' THEN 1 ELSE 0 END) as saidas
                FROM movimentacoes 
                WHERE DATE_TRUNC('month', data_movimentacao) = DATE_TRUNC('month', CURRENT_DATE)
            """)

            result = cursor.fetchone()
            return {
                'total_mes': result.get('count', 0) if result and hasattr(result, 'get') else 0,
                'entradas_mes': result['entradas'] if result else 0,
                'saidas_mes': result['saidas'] if result else 0
            }
        except:
            return {'total_mes': 0, 'entradas_mes': 0, 'saidas_mes': 0}

# Função principal da página
def show_movimentacoes_page():
    """Interface principal das movimentações"""
    
    st.title("📦 Movimentações")

    user_data = st.session_state.user_data
    if not auth_manager.check_permission(user_data['perfil'], "read"):
        st.error("❌ Você não tem permissão para acessar esta página.")
        return
    manager = MovimentacoesManager()

    # Abas principais
    tab1, tab2, tab3 = st.tabs(["📋 Histórico", "➕ Nova Movimentação", "📊 Relatórios"])

    with tab1:
        st.subheader("Histórico de Movimentações")

        # Filtros
        with st.expander("🔍 Filtros", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                filtro_item = st.text_input("Nome do Item")
                filtro_tipo = st.selectbox("Tipo", ["Todos", "Entrada", "Saída"])
            with col2:
                filtro_obra_origem = st.text_input("Origem")
                filtro_obra_destino = st.text_input("Destino")
            with col3:
                filtro_data_inicio = st.date_input("Data Início", value=None)
                filtro_data_fim = st.date_input("Data Fim", value=None)

        # Aplicar filtros
        filters = {}
        if filtro_item:
            filters['item_nome'] = filtro_item
        if filtro_tipo != "Todos":
            filters['tipo'] = filtro_tipo
        if filtro_obra_origem:
            filters['obra_origem'] = filtro_obra_origem
        if filtro_obra_destino:
            filters['obra_destino'] = filtro_obra_destino
        if filtro_data_inicio:
            filters['data_inicio'] = filtro_data_inicio.strftime('%Y-%m-%d')
        if filtro_data_fim:
            filters['data_fim'] = filtro_data_fim.strftime('%Y-%m-%d')

        # Buscar movimentações
        df = manager.get_movimentacoes(filters)  # type: ignore
        if not df.empty:
            st.dataframe(  # type: ignore
                df[['data_movimentacao', 'tipo', 'item_nome',
                   'quantidade', 'obra_origem', 'obra_destino', 'motivo', 'usuario_nome']],
                column_config={
                    'data_movimentacao': 'Data/Hora',
                    'tipo': 'Tipo',
                    'item_nome': 'Item',
                    'quantidade': 'Quantidade',
                    'obra_origem': 'Origem',
                    'obra_destino': 'Destino',
                    'motivo': 'Motivo',
                    'usuario_nome': 'Usuário'
                },
                width='stretch',
                hide_index=True
            )
        else:
            st.info("📭 Nenhuma movimentação encontrada com os filtros aplicados.")

    with tab2:
        if not auth_manager.check_permission(user_data['perfil'], "create"):
            st.error("❌ Você não tem permissão para criar movimentações.")
            return
        st.subheader("Nova Movimentação")
        categoria_mov = st.selectbox(
            "Movimentação de:",
            ["Insumos", "Equipamentos Elétricos", "Equipamentos Manuais"],
            key="categoria_movimentacao"
        )

        # Modal de movimentação rápida para cada tipo
        if categoria_mov == "Insumos":
            from modules.insumos import InsumosManager
            insumos_manager = InsumosManager()
            insumos = insumos_manager.get_insumos()
            if insumos:
                st.markdown("#### 📦 Insumos - Movimentação Rápida")
                st.info("💡 Clique em 'Movimentar' para abrir o modal com campos completos (destino, responsável e quantidade)")
                for idx, item in enumerate(insumos):
                    col1, col2, col3, col4 = st.columns([4,2,2,2])
                    with col1:
                        st.write(f"**{item['descricao']}** ({item['codigo']})")
                    with col2:
                        st.write(f"Estoque: {item['quantidade_atual']} {item['unidade']}")
                    with col3:
                        st.write(f"ID: {item['id']}")
                    with col4:
                        if st.button(f"📦 Movimentar", key=f"movimentar_insumo_{item['id']}_{idx}", help="Abrir modal de movimentação rápida"):
                            from modules.movimentacao_modal import show_movimentacao_modal_insumo
                            show_movimentacao_modal_insumo(item['id'])
            else:
                st.warning("⚠️ Nenhum insumo cadastrado.")

        elif categoria_mov == "Equipamentos Elétricos":
            from modules.equipamentos_eletricos import EquipamentosEletricosManager
            eq_manager = EquipamentosEletricosManager()
            equipamentos = eq_manager.get_equipamentos()
            if not equipamentos.empty:
                st.markdown("#### ⚡ Equipamentos Elétricos - Movimentação Rápida")
                st.info("💡 Clique em 'Movimentar' para abrir o modal com campos completos (destino e responsável)")
                for _, row in equipamentos.iterrows():
                    col1, col2, col3, col4, col5 = st.columns([4,2,2,2,2])
                    with col1:
                        st.write(f"**{row['nome']}** ({row['codigo']})")
                    with col2:
                        st.write(f"Localização: {row['localizacao']}")
                    with col3:
                        st.write(f"Status: {row['status']}")
                    with col4:
                        st.write(f"ID: {row['id']}")
                    with col5:
                        if st.button(f"⚡ Movimentar", key=f"movimentar_eletrico_{row['id']}", help="Abrir modal de movimentação rápida"):
                            from modules.movimentacao_modal import show_movimentacao_modal_equipamento_eletrico
                            show_movimentacao_modal_equipamento_eletrico(row['id'])
            else:
                st.warning("⚠️ Nenhum equipamento elétrico cadastrado.")

        elif categoria_mov == "Equipamentos Manuais":
            from modules.equipamentos_manuais import EquipamentosManuaisManager
            eq_manager = EquipamentosManuaisManager()
            equipamentos = eq_manager.get_equipamentos()
            if not equipamentos.empty:
                st.markdown("#### 🔧 Equipamentos Manuais - Movimentação Rápida")
                st.info("💡 Clique em 'Movimentar' para abrir o modal com campos completos (destino, responsável e quantidade)")
                for _, row in equipamentos.iterrows():
                    col1, col2, col3, col4, col5 = st.columns([4,2,2,2,2])
                    with col1:
                        st.write(f"**{row['nome']}** ({row['codigo']})")
                    with col2:
                        st.write(f"Localização: {row['localizacao']}")
                    with col3:
                        st.write(f"Status: {row['status']}")
                    with col4:
                        st.write(f"ID: {row['id']}")
                    with col5:
                        if st.button(f"🔧 Movimentar", key=f"movimentar_manual_{row['id']}", help="Abrir modal de movimentação rápida"):
                            from modules.movimentacao_modal import show_movimentacao_modal_equipamento_manual
                            show_movimentacao_modal_equipamento_manual(row['id'])
            else:
                st.warning("⚠️ Nenhum equipamento manual cadastrado.")

    # Relatórios (aba 3)
    with tab3:
        st.subheader("Relatórios de Movimentações")
        df_stats = manager.get_movimentacoes({})
        if not df_stats.empty:
            col1, col2 = st.columns(2)
            with col1:
                tipo_counts = df_stats['tipo'].value_counts()
                st.plotly_chart(  # type: ignore
                    {
                        'data': [{
                            'type': 'pie',
                            'labels': tipo_counts.index.tolist(),
                            'values': tipo_counts.values.tolist(),  # type: ignore
                            'title': 'Movimentações por Tipo'
                        }],
                        'layout': {'title': 'Distribuição por Tipo'}
                    },
                    width='stretch'
                )
            with col2:
                motivo_counts = df_stats['motivo'].value_counts().head(10)
                st.plotly_chart(  # type: ignore
                    {
                        'data': [{
                            'type': 'bar',
                            'x': motivo_counts.values.tolist(),  # type: ignore
                            'y': motivo_counts.index.tolist(),
                            'orientation': 'h'
                        }],
                        'layout': {
                            'title': 'Top 10 Motivos',
                            'xaxis': {'title': 'Quantidade'},
                            'yaxis': {'title': 'Motivo'}
                        }
                    },
                    width='stretch'
                )
        else:
            st.info("Nenhuma movimentação encontrada para relatório.")

# Instância global
movimentacoes_manager = MovimentacoesManager()