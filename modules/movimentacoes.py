
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
    
    def get_ultima_movimentacao_equipamento(self, equipamento_id: int, tipo_equipamento: str) -> dict[str, Any] | None:
        """Busca a última movimentação de um equipamento específico"""
        try:
            conn = self.db.get_connection()
            if not conn:
                return None
                
            cursor = conn.cursor()
            
            # Buscar última movimentação do equipamento
            cursor.execute("""
                SELECT 
                    tipo_movimentacao, 
                    local_origem, 
                    local_destino,
                    data_movimentacao,
                    motivo
                FROM movimentacoes 
                WHERE item_id = %s AND tipo = %s
                ORDER BY data_movimentacao DESC, id DESC
                LIMIT 1
            """, (equipamento_id, f'Equipamento {tipo_equipamento.capitalize()}'))
            
            result = cursor.fetchone()
            
            if result:
                if isinstance(result, dict):
                    return result
                else:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, result))
            
            return None
            
        except Exception as e:
            st.error(f"Erro ao buscar última movimentação: {e}")
            return None
    
    def create_devolucao(self, movimentacao_original_id: int, tipo_devolucao: str, 
                        quantidade_devolvida: int = None, motivo: str = "", 
                        nova_obra_id: int = None, usuario_id: int = None) -> tuple[bool, str]:
        """
        Cria devolução de movimentação
        
        Args:
            movimentacao_original_id: ID da movimentação original
            tipo_devolucao: 'total', 'parcial', 'transferencia'
            quantidade_devolvida: Quantidade devolvida (para insumos)
            motivo: Motivo da devolução
            nova_obra_id: ID da nova obra (para transferências)
            usuario_id: ID do usuário que está fazendo a devolução
        """
        try:
            conn = self.db.get_connection()
            if not conn:
                return False, "Erro de conexão com o banco"
                
            cursor = conn.cursor()
            
            # 1. Buscar movimentação original
            cursor.execute("""
                SELECT * FROM movimentacoes WHERE id = %s
            """, (movimentacao_original_id,))
            
            mov_original = cursor.fetchone()
            if not mov_original:
                return False, "Movimentação original não encontrada"
            
            # Converter para dict se necessário
            if not isinstance(mov_original, dict):
                columns = [desc[0] for desc in cursor.description]
                mov_original = dict(zip(columns, mov_original))
            
            # 2. Validações
            if mov_original['tipo_movimentacao'] != 'saida':
                return False, "Só é possível devolver movimentações de saída"
            
            # 3. Determinar quantidade a devolver
            qtd_original = mov_original.get('quantidade', 1)
            if tipo_devolucao == 'total' or mov_original['tipo'] not in ['Insumo']:
                qtd_devolver = qtd_original
            else:  # parcial para insumos
                qtd_devolver = quantidade_devolvida or qtd_original
                if qtd_devolver > qtd_original:
                    return False, f"Quantidade inválida. Original: {qtd_original}, solicitado: {qtd_devolver}"
            
            # 4. Determinar destino
            if tipo_devolucao == 'transferencia' and nova_obra_id:
                local_destino = f"Obra ID: {nova_obra_id}"
            else:
                local_destino = mov_original.get('local_origem', 'Estoque')
            
            # 5. Criar registro de devolução
            dados_devolucao = {
                'item_id': mov_original['item_id'],
                'tipo': mov_original['tipo'],
                'tipo_item': mov_original.get('tipo_item', ''),
                'tipo_movimentacao': 'entrada' if tipo_devolucao != 'transferencia' else 'saida',
                'quantidade': qtd_devolver,
                'local_origem': mov_original.get('local_destino', ''),
                'local_destino': local_destino,
                'motivo': f"DEVOLUÇÃO {tipo_devolucao.upper()}: {motivo}",
                'observacoes': f"Devolução da movimentação #{movimentacao_original_id}",
                'movimentacao_origem_id': movimentacao_original_id,
                'obra_origem_id': mov_original.get('obra_destino_id'),
                'obra_destino_id': nova_obra_id if tipo_devolucao == 'transferencia' else mov_original.get('obra_origem_id'),
                'responsavel_origem_id': mov_original.get('responsavel_destino_id'),
                'responsavel_destino_id': mov_original.get('responsavel_origem_id'),
                'valor_unitario': mov_original.get('valor_unitario')
            }
            
            # 6. Registrar devolução
            mov_id = self.create_movimentacao(dados_devolucao, usuario_id)
            if not mov_id:
                return False, "Erro ao criar registro de devolução"
            
            # 7. Atualizar estoques/disponibilidade
            resultado_estoque = self._atualizar_estoque_devolucao(
                mov_original, qtd_devolver, tipo_devolucao, nova_obra_id
            )
            
            if not resultado_estoque[0]:
                # Reverter criação da movimentação
                cursor.execute("DELETE FROM movimentacoes WHERE id = %s", (mov_id,))
                conn.commit()
                return False, f"Erro ao atualizar estoque: {resultado_estoque[1]}"
            
            conn.commit()
            return True, f"Devolução registrada com sucesso! ID: {mov_id}"
            
        except Exception as e:
            try:
                conn.rollback()
            except:
                pass
            return False, f"Erro ao processar devolução: {str(e)}"
    
    def _atualizar_estoque_devolucao(self, mov_original: dict, quantidade: int, 
                                   tipo_devolucao: str, nova_obra_id: int = None) -> tuple[bool, str]:
        """Atualiza estoque após devolução"""
        try:
            if mov_original['tipo'] == 'Insumo' and tipo_devolucao != 'transferencia':
                # Devolver ao estoque
                from modules.insumos import InsumosManager
                insumos_manager = InsumosManager()
                
                # Aumentar estoque
                conn = self.db.get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE insumos 
                    SET quantidade_atual = quantidade_atual + %s 
                    WHERE id = %s
                """, (quantidade, mov_original['item_id']))
                
                return True, "Estoque atualizado"
            
            # Para equipamentos ou transferências, não há atualização de estoque
            # A disponibilidade é determinada pela última movimentação
            return True, "Disponibilidade atualizada"
            
        except Exception as e:
            return False, f"Erro ao atualizar estoque: {str(e)}"

def _show_modal_devolucao(mov_id: int, row: dict, manager: MovimentacoesManager, user_data: dict):
    """Modal para devolução/transferência"""
    
    st.markdown(f"### Movimentação Original")
    st.info(f"📦 **{row['item_nome']}** | Quantidade: **{row.get('quantidade', 1)}** | "
            f"Origem: **{row.get('obra_origem', 'N/A')}** → Destino: **{row.get('obra_destino', 'N/A')}**")
    
    # Tipo de operação
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Devolução Total", key=f"dev_total_{mov_id}", use_container_width=True):
            st.session_state[f'tipo_operacao_{mov_id}'] = 'total'
            st.rerun()
    
    with col2:
        # Só para insumos
        if row.get('tipo') == 'Insumo':
            if st.button("📦 Devolução Parcial", key=f"dev_parcial_{mov_id}", use_container_width=True):
                st.session_state[f'tipo_operacao_{mov_id}'] = 'parcial'
                st.rerun()
        else:
            st.write("—")
    
    with col3:
        if st.button("🔀 Transferir para Obra", key=f"transferir_{mov_id}", use_container_width=True):
            st.session_state[f'tipo_operacao_{mov_id}'] = 'transferencia'
            st.rerun()
    
    # Formulário baseado no tipo selecionado
    tipo_operacao = st.session_state.get(f'tipo_operacao_{mov_id}')
    
    if tipo_operacao:
        st.markdown(f"#### {tipo_operacao.title()}")
        
        with st.form(f"form_devolucao_{mov_id}"):
            quantidade_devolver = None
            nova_obra_id = None
            
            if tipo_operacao == 'parcial':
                st.markdown("**Quantidade a Devolver:**")
                quantidade_original = row.get('quantidade', 1)
                quantidade_devolver = st.number_input(
                    "Quantidade", 
                    min_value=1, 
                    max_value=int(quantidade_original), 
                    value=int(quantidade_original//2),
                    key=f"qtd_dev_{mov_id}"
                )
                st.caption(f"Original: {quantidade_original} | Restante na obra: {quantidade_original - quantidade_devolver}")
            
            elif tipo_operacao == 'transferencia':
                from modules.obras import ObrasManager
                obras_manager = ObrasManager()
                obras_df = obras_manager.get_obras()
                
                if not obras_df.empty:
                    obras_options = [f"{obra['nome']} - {obra['codigo']}" for _, obra in obras_df.iterrows()]
                    obra_selecionada = st.selectbox("Nova Obra de Destino", obras_options, key=f"obra_dest_{mov_id}")
                    
                    if obra_selecionada:
                        for _, obra in obras_df.iterrows():
                            if f"{obra['nome']} - {obra['codigo']}" == obra_selecionada:
                                nova_obra_id = obra['id']
                                break
                
                if row.get('tipo') == 'Insumo':
                    quantidade_original = row.get('quantidade', 1)
                    quantidade_devolver = st.number_input(
                        "Quantidade a Transferir", 
                        min_value=1, 
                        max_value=int(quantidade_original), 
                        value=int(quantidade_original),
                        key=f"qtd_transf_{mov_id}"
                    )
            
            motivo = st.text_area(
                "Motivo da operação", 
                placeholder="Descreva o motivo da devolução/transferência...",
                key=f"motivo_dev_{mov_id}"
            )
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.form_submit_button("✅ Confirmar", type="primary"):
                    # Executar operação
                    sucesso, mensagem = manager.create_devolucao(
                        movimentacao_original_id=mov_id,
                        tipo_devolucao=tipo_operacao,
                        quantidade_devolvida=quantidade_devolver,
                        motivo=motivo,
                        nova_obra_id=nova_obra_id,
                        usuario_id=user_data['id']
                    )
                    
                    if sucesso:
                        st.success(mensagem)
                        # Limpar estado
                        for key in list(st.session_state.keys()):
                            if str(mov_id) in key and ('modal_devolucao' in key or 'tipo_operacao' in key):
                                del st.session_state[key]
                        st.rerun()
                    else:
                        st.error(mensagem)
            
            with col_btn2:
                if st.form_submit_button("❌ Cancelar"):
                    # Limpar estado
                    for key in list(st.session_state.keys()):
                        if str(mov_id) in key and ('modal_devolucao' in key or 'tipo_operacao' in key):
                            del st.session_state[key]
                    st.rerun()

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
            st.info(f"📋 {len(df)} movimentações encontradas")
            
            # Cabeçalho da tabela
            cols = st.columns([2, 1.5, 3, 1, 2, 2, 2, 1.5])
            with cols[0]:
                st.markdown("**Data/Hora**")
            with cols[1]:
                st.markdown("**Tipo**")
            with cols[2]:
                st.markdown("**Item**")
            with cols[3]:
                st.markdown("**Qtd**")
            with cols[4]:
                st.markdown("**Origem**")
            with cols[5]:
                st.markdown("**Destino**")
            with cols[6]:
                st.markdown("**Motivo**")
            with cols[7]:
                st.markdown("**Ações**")
            
            st.divider()
            
            # Iterar sobre as movimentações
            for idx, row in df.iterrows():
                cols = st.columns([2, 1.5, 3, 1, 2, 2, 2, 1.5])
                
                with cols[0]:
                    data_str = str(row['data_movimentacao'])[:16] if row['data_movimentacao'] else 'N/A'
                    st.write(data_str)
                    
                with cols[1]:
                    tipo_icon = "📥" if row.get('tipo_movimentacao') == 'entrada' else "📤"
                    st.write(f"{tipo_icon} {row['tipo']}")
                    
                with cols[2]:
                    st.write(f"**{row['item_nome']}**")
                    
                with cols[3]:
                    qtd = row.get('quantidade', 1)
                    st.write(f"{qtd}")
                    
                with cols[4]:
                    origem = row.get('obra_origem', 'N/A')
                    st.write(origem[:20] + "..." if len(str(origem)) > 20 else str(origem))
                    
                with cols[5]:
                    destino = row.get('obra_destino', 'N/A')
                    st.write(destino[:20] + "..." if len(str(destino)) > 20 else str(destino))
                    
                with cols[6]:
                    motivo = row.get('motivo', 'N/A')
                    st.write(motivo[:15] + "..." if len(str(motivo)) > 15 else str(motivo))
                    
                with cols[7]:
                    # Botões de ação
                    mov_id = row.get('id')
                    tipo_mov = row.get('tipo_movimentacao', 'saida')
                    
                    # Só mostra botão de devolução para saídas que não são devoluções
                    if (tipo_mov == 'saida' and 
                        not row.get('motivo', '').startswith('DEVOLUÇÃO') and
                        auth_manager.check_permission(user_data['perfil'], "update")):
                        
                        if st.button("🔄", key=f"devolver_{mov_id}_{idx}", 
                                   help="Devolver/Transferir", use_container_width=True):
                            st.session_state[f'modal_devolucao_{mov_id}'] = True
                            st.rerun()
                    else:
                        st.write("—")
                
                # Modal de devolução
                if st.session_state.get(f'modal_devolucao_{mov_id}', False):
                    with st.expander(f"🔄 Devolução/Transferência - {row['item_nome']}", expanded=True):
                        _show_modal_devolucao(mov_id, row, manager, user_data)
                
                st.divider()
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