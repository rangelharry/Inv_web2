"""
Sistema de Inventário Web - Módulo de Gestão de Insumos
CRUD completo com controle de estoque, alertas e filtros avançados
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date  # type: ignore
import json  # type: ignore
from database.connection import db
from modules.auth import auth_manager
from typing import Any

class InsumosManager:
    def __init__(self):
        self.conn = db.get_connection()

    def get_categorias(self, tipo: str = 'insumo') -> list[dict[str, Any]]:
        """Busca categorias disponíveis"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT id, nome FROM categorias 
            WHERE tipo = %s AND ativo = TRUE 
            ORDER BY nome
            """, (tipo,))
            return [dict(zip([desc[0] for desc in cursor.description], row)) for row in cursor.fetchall()]
        except Exception as e:
            st.error(f"Erro ao buscar categorias: {e}")
            return []
    
    def create_insumo(self, dados: dict[str, Any], user_id: int) -> tuple[bool, str]:
        """Cria novo insumo"""
        try:
            cursor = self.conn.cursor()
            # Verifica se código já existe
            cursor.execute("SELECT id FROM insumos WHERE codigo = %s", (dados['codigo'],))
            if cursor.fetchone():
                return False, "Código já existe"
            cursor.execute("""
            INSERT INTO insumos (
                codigo, descricao, categoria_id, unidade, quantidade_atual,
                quantidade_minima, fornecedor, marca, 
                localizacao, observacoes, data_validade, criado_por
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                dados['codigo'], dados['descricao'], dados['categoria_id'],
                dados['unidade'], dados['quantidade_atual'], dados['quantidade_minima'],
                dados['fornecedor'], dados['marca'],
                dados['localizacao'], dados['observacoes'], dados['data_validade'], user_id
            ))
            cursor.execute("SELECT id FROM insumos WHERE codigo = %s", (dados['codigo'],))
            result = cursor.fetchone()
            insumo_id = result['id'] if result else None
            self.conn.commit()
            # Log da ação
            auth_manager.log_action(
                user_id, 'criar', 'insumos', insumo_id,
                f"Insumo criado: {dados['codigo']} - {dados['descricao']}"
            )
            return True, "Insumo criado com sucesso"
        except Exception as e:
            return False, f"Erro ao criar insumo: {str(e)}"
    
    def update_insumo(self, insumo_id: int, dados: dict[str, Any], user_id: int) -> tuple[bool, str]:
        """Atualiza insumo existente"""
        try:
            cursor = self.conn.cursor()
            # Busca dados atuais
            cursor.execute("SELECT * FROM insumos WHERE id = %s", (insumo_id,))
            old_data = dict(zip([desc[0] for desc in cursor.description], cursor.fetchone()))
            # Verifica se código já existe em outro insumo
            cursor.execute("SELECT id FROM insumos WHERE codigo = %s AND id != %s", (dados['codigo'], insumo_id))
            if cursor.fetchone():
                return False, "Código já existe em outro insumo"
            cursor.execute("""
            UPDATE insumos SET 
                codigo = %s, descricao = %s, categoria_id = %s, unidade = %s,
                quantidade_atual = %s, quantidade_minima = %s,
                fornecedor = %s, marca = %s, localizacao = %s, observacoes = %s,
                data_validade = %s
            WHERE id = %s
            """, (
                dados['codigo'], dados['descricao'], dados['categoria_id'],
                dados['unidade'], dados['quantidade_atual'], dados['quantidade_minima'],
                dados['fornecedor'], dados['marca'],
                dados['localizacao'], dados['observacoes'], dados['data_validade'], insumo_id
            ))
            self.conn.commit()
            # Log da ação
            auth_manager.log_action(
                user_id, 'editar', 'insumos', insumo_id,
                f"Insumo atualizado: {dados['codigo']} - {dados['descricao']}",
                str(old_data), str(dados)
            )
            return True, "Insumo atualizado com sucesso"
        except Exception as e:
            return False, f"Erro ao atualizar insumo: {str(e)}"
    
    def delete_insumo(self, insumo_id: int, user_id: int) -> tuple[bool, str]:
        """Remove insumo (soft delete)"""
        try:
            cursor = self.conn.cursor()
            # Busca dados do insumo
            cursor.execute("SELECT * FROM insumos WHERE id = %s", (insumo_id,))
            row = cursor.fetchone()
            if not row:
                return False, "Insumo não encontrado"
            insumo_data = dict(zip([desc[0] for desc in cursor.description], row))
            cursor.execute("UPDATE insumos SET ativo = FALSE WHERE id = %s", (insumo_id,))
            self.conn.commit()
            # Log da ação
            auth_manager.log_action(
                user_id, 'excluir', 'insumos', insumo_id,
                f"Insumo removido: {insumo_data['codigo']} - {insumo_data['descricao']}"
            )
            return True, f"Insumo {insumo_data['codigo']} removido com sucesso"
        except Exception as e:
            return False, f"Erro ao remover insumo: {str(e)}"
    
    def get_insumos(self, filtros: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Busca insumos com filtros"""
        try:
            # Garantir que a conexão esteja limpa
            if hasattr(self.conn, 'rollback'):
                self.conn.rollback()  # type: ignore
            
            cursor = self.conn.cursor()
            query = """
            SELECT i.*, c.nome as categoria_nome
            FROM insumos i
            LEFT JOIN categorias c ON i.categoria_id = c.id
            WHERE i.ativo = TRUE
            """
            params: list[Any] = []
            if filtros:
                if filtros.get('categoria_id'):
                    query += " AND i.categoria_id = %s"
                    params.append(filtros['categoria_id'])
                if filtros.get('estoque_baixo'):
                    query += " AND i.quantidade_atual <= i.quantidade_minima"
                if filtros.get('busca'):
                    query += " AND (i.codigo LIKE %s OR i.descricao LIKE %s OR i.marca LIKE %s)"
                    busca = f"%{filtros['busca']}%"
                    params.extend([busca, busca, busca])  # type: ignore
            query += " ORDER BY i.codigo"
            cursor.execute(query, params)  # type: ignore
            return [dict(zip([desc[0] for desc in cursor.description], row)) for row in cursor.fetchall()]
        except Exception as e:
            # Fazer rollback explícito para limpar o estado da transação
            if hasattr(self.conn, 'rollback'):
                self.conn.rollback()  # type: ignore
            st.error(f"Erro ao buscar insumos: {e}")
            return []
    
    def get_insumo_by_id(self, insumo_id: int) -> dict[str, Any] | None:
        """Busca insumo por ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT i.*, c.nome as categoria_nome
            FROM insumos i
            LEFT JOIN categorias c ON i.categoria_id = c.id
            WHERE i.id = %s
            """, (insumo_id,))
            result = cursor.fetchone()
            return dict(zip([desc[0] for desc in cursor.description], result)) if result else None
        except Exception as e:
            st.error(f"Erro ao buscar insumo: {e}")
            return None
    
    def ajustar_estoque(self, insumo_id: int, quantidade: float, tipo_movimento: str, motivo: str, user_id: int) -> tuple[bool, str]:
        """Ajusta estoque de insumo"""
        try:
            cursor = self.conn.cursor()
            # Busca insumo atual
            cursor.execute("SELECT * FROM insumos WHERE id = %s", (insumo_id,))
            row = cursor.fetchone()
            if not row:
                return False, "Insumo não encontrado"
            insumo = dict(zip([desc[0] for desc in cursor.description], row))
            quantidade_atual = insumo['quantidade_atual']
            if tipo_movimento == 'entrada':
                nova_quantidade = quantidade_atual + quantidade
            else:  # saida
                if quantidade_atual < quantidade:
                    return False, "Quantidade insuficiente em estoque"
                nova_quantidade = quantidade_atual - quantidade
            # Atualiza estoque
            cursor.execute("""
            UPDATE insumos SET 
                quantidade_atual = %s,
                data_ultima_entrada = CASE WHEN %s = 'entrada' THEN CURRENT_TIMESTAMP ELSE data_ultima_entrada END,
                data_ultima_saida = CASE WHEN %s = 'saida' THEN CURRENT_TIMESTAMP ELSE data_ultima_saida END
            WHERE id = %s
            """, (nova_quantidade, tipo_movimento, tipo_movimento, insumo_id))
            # Registra movimentação
            cursor.execute("""
            INSERT INTO movimentacoes (
                tipo, tipo_item, item_id, codigo_item, descricao_item,
                quantidade, unidade, motivo, observacoes, usuario_id
            ) VALUES (%s, 'insumo', %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                tipo_movimento, insumo_id, insumo['codigo'], insumo['descricao'],
                quantidade, insumo['unidade'], motivo, f"Ajuste de estoque: {motivo}", user_id
            ))
            self.conn.commit()
            # Log da ação
            auth_manager.log_action(
                user_id, 'editar', 'insumos', insumo_id,
                f"Ajuste de estoque - {tipo_movimento}: {quantidade} {insumo['unidade']} - {motivo}"
            )
            return True, f"Estoque ajustado: {nova_quantidade} {insumo['unidade']}"
        except Exception as e:
            return False, f"Erro ao ajustar estoque: {str(e)}"

# Interface Streamlit para gestão de insumos
def show_insumos_page():
    """Exibe página de gestão de insumos"""
    st.title("📦 Gestão de Insumos")
    
    # Verificar permissões
    user_data = st.session_state.user_data
    can_edit = True  # Permitir edição para todos os usuários
    can_create = auth_manager.check_permission(user_data['perfil'], 'create')
    can_delete = auth_manager.check_permission(user_data['perfil'], 'delete')  # type: ignore
    
    manager = InsumosManager()
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Lista", "➕ Novo Insumo", "📊 Relatórios", "⚙️ Ajustes"])
    
    with tab1:
        st.subheader("📋 Lista de Insumos")
        
        # Filtros
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            categorias = manager.get_categorias()
            categoria_options: list[dict[str, Any]] = [{'id': 0, 'nome': 'Todas as categorias'}] + categorias  # type: ignore
            categoria_selected: dict[str, Any] = st.selectbox(
                "Categoria",
                options=categoria_options,
                format_func=lambda x: x['nome']
            )
        
        with col2:
            estoque_baixo = st.checkbox("Apenas estoque baixo")
        
        with col3:
            busca = st.text_input("🔍 Buscar", placeholder="Código, descrição ou marca...")
        
        with col4:
            if st.button("🔄 Atualizar Lista"):
                st.rerun()
        
        # Aplicar filtros
    filtros: dict[str, Any] = {}
    if categoria_selected['id'] > 0:
        filtros['categoria_id'] = categoria_selected['id']
    if estoque_baixo:
        filtros['estoque_baixo'] = True
    if busca:
        filtros['busca'] = busca

    # Buscar insumos
    insumos = manager.get_insumos(filtros)  # type: ignore

    if insumos:
            # Estatísticas rápidas
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            total_itens = len(insumos)
            estoque_baixo_count = sum(1 for i in insumos if i['quantidade_atual'] <= i['quantidade_minima'])
            sem_estoque = sum(1 for i in insumos if i['quantidade_atual'] == 0)
            col_stat1.metric("Total de Itens", total_itens)
            col_stat2.metric("Estoque Baixo", estoque_baixo_count, delta_color="inverse")
            col_stat3.metric("Sem Estoque", sem_estoque, delta_color="inverse")

            # Tabela de insumos
            df = pd.DataFrame(insumos)
            df_display = df.copy()
            df_display['Código'] = df['codigo']
            df_display['Descrição'] = df['descricao']
            df_display['Categoria'] = df['categoria_nome']
            df_display['Atual'] = df['quantidade_atual'].astype(str) + ' ' + df['unidade']
            df_display['Mínimo'] = df['quantidade_minima'].astype(str) + ' ' + df['unidade']
            def get_status_estoque_completo(row: pd.Series) -> str:
                if row['quantidade_atual'] == 0:
                    return "🔴 Sem estoque"
                elif row['quantidade_atual'] <= row['quantidade_minima']:
                    return "🟡 Estoque baixo"
                else:
                    return "🟢 Normal"
            df_display['Status'] = df.apply(get_status_estoque_completo, axis=1)  # type: ignore

            st.write("### Lista de Insumos")
            num_rows = st.selectbox(
                "Linhas por página:",
                options=[10, 20, 30, 50, 100],
                index=2
            )
            
            # Exibir a tabela de insumos
            total_pages = (len(insumos) - 1) // num_rows + 1
            
            # Inicializar página no session_state se não existir
            if 'page' not in st.session_state:
                st.session_state.page = 1
            
            # Garantir que a página está no intervalo válido
            if st.session_state.page > total_pages:
                st.session_state.page = total_pages
            if st.session_state.page < 1:
                st.session_state.page = 1
                
            page = st.session_state.page
            
            start_idx = (page - 1) * num_rows
            end_idx = start_idx + num_rows
            df_paginado = df_display.iloc[start_idx:end_idx]
            
            # Preparar DataFrame para exibição com status
            df_exibicao = df_paginado.copy()
            df_exibicao['Status'] = df_exibicao.apply(get_status_estoque_completo, axis=1)  # type: ignore
            
            # Cabeçalho da tabela
            col_header1, col_header2, col_header3, col_header4, col_header5, col_header6, col_header7, col_header8, col_header9 = st.columns([0.8, 1.5, 2, 1.2, 1, 1, 0.8, 0.8, 0.8])
            
            with col_header1:
                st.write("**Código**")
            with col_header2:
                st.write("**Descrição**")
            with col_header3:
                st.write("**Categoria**")
            with col_header4:
                st.write("**Qtd. Atual**")
            with col_header5:
                st.write("**Qtd. Mínima**")
            with col_header6:
                st.write("**Status**")
            with col_header7:
                st.write("**Editar**")
            with col_header8:
                st.write("**Mover**")
            with col_header9:
                st.write("**Excluir**")
            
            st.write("---")
            
            # Exibir tabela com informações e botões de edição
            for idx, row in df_exibicao.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([0.8, 1.5, 2, 1.2, 1, 1, 0.8, 0.8, 0.8])
                    
                    with col1:
                        st.write(f"**{row['codigo']}**")
                    
                    with col2:
                        st.write(row['descricao'])
                    
                    with col3:
                        st.write(row['categoria_nome'])
                    
                    with col4:
                        st.write(f"{row['quantidade_atual']} {row['unidade']}")
                    
                    with col5:
                        st.write(f"{row['quantidade_minima']} {row['unidade']}")
                    
                    with col6:
                        st.write(row['Status'])
                    
                    with col7:
                        if st.button("✏️", key=f"edit_{row['id']}_{idx}", help="Editar insumo"):
                            st.session_state[f'edit_mode_{row["id"]}'] = True
                            st.rerun()
                    
                    with col8:
                        if st.button("📦", key=f"move_{row['id']}_{idx}", help="Movimentar insumo"):
                            # Fecha todos os outros modais de movimentação
                            for k in list(st.session_state.keys()):
                                if isinstance(k, str) and k.startswith("move_mode_") and k != f"move_mode_{row['id']}":
                                    st.session_state[k] = False
                            st.session_state[f"move_mode_{row['id']}"] = True
                            st.rerun()
                    
                    with col9:
                        if st.button("❌", key=f"del_{row['id']}_{idx}", help="Excluir insumo"):
                            st.session_state[f'confirm_delete_insumo_{row["id"]}'] = True
                            st.rerun()
                
                # Modal de confirmação de exclusão
                if st.session_state.get(f'confirm_delete_insumo_{row["id"]}', False):
                    st.markdown("---")
                    st.error(f"⚠️ **CONFIRMAÇÃO DE EXCLUSÃO**")
                    st.warning(f"Tem certeza que deseja excluir o insumo **{row['descricao']}** (Código: {row['codigo']})?\n\nEsta ação não pode ser desfeita!")
                    
                    col_cancel, col_confirm = st.columns(2)
                    with col_cancel:
                        if st.button("❌ Cancelar", key=f"cancel_del_insumo_{row['id']}"):
                            del st.session_state[f'confirm_delete_insumo_{row["id"]}']
                            st.rerun()
                    
                    with col_confirm:
                        if st.button("🗑️ Confirmar Exclusão", key=f"confirm_del_insumo_{row['id']}", type="primary"):
                            success, message = manager.delete_insumo(int(row['id']), user_data['id'])  # type: ignore
                            if success:
                                st.success(f"✅ {message}")
                                del st.session_state[f'confirm_delete_insumo_{row["id"]}']
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                    st.markdown("---")
                
                # Modal de edição
                if st.session_state.get(f'edit_mode_{row["id"]}', False):
                    with st.expander(f"🔧 Editando: {row['codigo']} - {row['descricao']}", expanded=True):
                        # Buscar categorias para o seletor
                        categorias = manager.get_categorias()
                        
                        if categorias:
                            categoria_opcoes = {cat['nome']: cat['id'] for cat in categorias}
                            categoria_nomes = list(categoria_opcoes.keys())
                            categoria_atual_nome = row['categoria_nome']
                            
                            # Encontrar índice da categoria atual
                            try:
                                categoria_index = categoria_nomes.index(categoria_atual_nome)
                            except ValueError:
                                categoria_index = 0
                        else:
                            categoria_opcoes = {"Sem categoria": 1}
                            categoria_nomes = ["Sem categoria"]
                            categoria_index = 0
                        
                        # Primeira linha - Descrição completa
                        nova_descricao = st.text_input("Descrição:", value=row['descricao'], key=f"desc_{row['id']}_{idx}")
                        
                        # Segunda linha - Categoria e informações
                        col_info1, col_info2 = st.columns(2)
                        with col_info1:
                            nova_categoria = st.selectbox(
                                "Categoria:", 
                                options=categoria_nomes,
                                index=categoria_index,
                                key=f"cat_{row['id']}_{idx}"
                            )
                        with col_info2:
                            st.write(f"**Código:** {row['codigo']}")
                            st.write(f"**Unidade:** {row['unidade']}")
                        
                        # Terceira linha - Quantidades
                        col_qtd1, col_qtd2 = st.columns(2)
                        with col_qtd1:
                            nova_qtd_atual = st.number_input("Quantidade Atual:", min_value=0, value=int(row['quantidade_atual']), key=f"atual_{row['id']}_{idx}")
                        
                        with col_qtd2:
                            nova_qtd_min = st.number_input("Quantidade Mínima:", min_value=0, value=int(row['quantidade_minima']), key=f"min_{row['id']}_{idx}")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        
                        with col_btn1:
                            if st.button("💾 Salvar", key=f"save_{row['id']}_{idx}", type="primary"):
                                # Preparar dados para atualização
                                dados_update: dict[str, Any] = {
                                    'codigo': row['codigo'],
                                    'descricao': nova_descricao,
                                    'categoria_id': categoria_opcoes[nova_categoria],
                                    'unidade': row['unidade'],
                                    'quantidade_atual': int(nova_qtd_atual),
                                    'quantidade_minima': int(nova_qtd_min),
                                    'fornecedor': row['fornecedor'],
                                    'marca': row['marca'],
                                    'localizacao': row['localizacao'],
                                    'observacoes': row['observacoes'],
                                    'data_validade': row['data_validade']
                                }
                                
                                success, message = manager.update_insumo(int(row['id']), dados_update, user_data['id'])  # type: ignore
                                if success:
                                    st.success(f"Insumo {row['codigo']} atualizado com sucesso!")
                                    del st.session_state[f'edit_mode_{row["id"]}']
                                    st.rerun()
                                else:
                                    st.error(f"Erro ao atualizar insumo: {message}")
                        
                        with col_btn2:
                            if st.button("❌ Cancelar", key=f"cancel_{row['id']}_{idx}"):
                                del st.session_state[f'edit_mode_{row["id"]}']
                                st.rerun()
                    
                    st.divider()
                
                # Modal de movimentação
                if st.session_state.get(f'move_mode_{row["id"]}', False):
                    from modules.movimentacao_modal import show_movimentacao_modal_insumo  # type: ignore
                    show_movimentacao_modal_insumo(int(row['id']))
                    
                    # Botão para fechar o modal
                    if st.button("❌ Fechar", key=f"close_move_{row['id']}_{idx}"):
                        del st.session_state[f'move_mode_{row["id"]}']
                        st.session_state['modal_type'] = None
                        st.session_state['last_modal_item_id'] = None
                        st.rerun()
                    
                    st.divider()
            
            # Navegação com botões
            if total_pages > 1:
                col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns([1, 1, 2, 1, 1])
                
                with col_nav1:
                    if st.button("⏮️ Primeira") and page > 1:
                        st.session_state.page = 1
                        st.rerun()
                
                with col_nav2:
                    if st.button("⬅️ Anterior") and page > 1:
                        st.session_state.page = page - 1
                        st.rerun()
                
                with col_nav3:
                    st.write(f"Página {page} de {total_pages}")
                
                with col_nav4:
                    if st.button("➡️ Próxima") and page < total_pages:
                        st.session_state.page = page + 1
                        st.rerun()
                
                with col_nav5:
                    if st.button("⏭️ Última") and page < total_pages:
                        st.session_state.page = total_pages
                        st.rerun()
            
            # Botões de ação para insumos
            col_act1, col_act2, col_act3 = st.columns(3)
            
            with col_act1:
                if st.button("🔄 Atualizar", width='stretch'):
                    st.rerun()
            
            with col_act2:
                if estoque_baixo_count > 0:
                    if st.button(f"⚠️ Ver Estoque Baixo ({estoque_baixo_count})", width='stretch'):
                        st.session_state.filtro_estoque_baixo = True
                        st.rerun()
            
            with col_act3:
                if can_create and st.button("➕ Novo Insumo", width='stretch'):
                    st.session_state.aba_ativa = 1  # Ir para aba de novo insumo
                    st.rerun()
        
    # Caso não haja insumos
    if not insumos:
        st.info("📝 Nenhum insumo encontrado com os filtros aplicados.")
        if can_create:
            if st.button("➕ Cadastrar Primeiro Insumo"):
                st.session_state.aba_ativa = 1
                st.rerun()
    
    with tab2:
        if not can_create:
            st.warning("⚠️ Você não tem permissão para criar insumos.")
        else:
            st.subheader("➕ Cadastrar Novo Insumo")
            
            with st.form("form_novo_insumo"):
                insumos_existentes = manager.get_insumos()
                ultimo_codigo = "INS-0001"
                if insumos_existentes:
                    codigos = [i['codigo'] for i in insumos_existentes if i['codigo'].startswith("INS-")]
                    numeros = []
                    for cod in codigos:
                        try:
                            numeros.append(int(cod.replace("INS-", "")))  # type: ignore
                        except:
                            pass
                    if numeros:
                        proximo_num: int = max(numeros) + 1  # type: ignore
                        ultimo_codigo = f"INS-{proximo_num:04d}"
                col1, col2 = st.columns(2)
                with col1:
                    codigo = st.text_input("* Código", value=ultimo_codigo)
                    descricao = st.text_area("* Descrição", placeholder="Descrição detalhada do insumo")
                    categorias = manager.get_categorias()
                    if categorias:
                        categoria = st.selectbox(
                            "* Categoria",
                            options=categorias,
                            format_func=lambda x: x['nome']
                        )
                    else:
                        st.error("Nenhuma categoria disponível. Cadastre categorias primeiro.")
                        categoria = None
                    unidade = st.selectbox("* Unidade", ['UND', 'KG', 'L', 'M', 'M²', 'M³', 'PCT', 'CX', 'GL', 'TON'])
                with col2:
                    quantidade_atual = st.number_input("Quantidade Atual", min_value=0, value=0, step=1, format="%d")
                    quantidade_minima = st.number_input("Quantidade Mínima", min_value=0, value=5, step=1, format="%d")
                    fornecedor = st.text_input("Fornecedor", placeholder="Nome do fornecedor")
                    marca = st.text_input("Marca", placeholder="Marca do produto")
                    localizacao = st.text_input("Localização", value="Almoxarifado")
                data_validade = st.date_input("Data de Validade", value=None)
                observacoes = st.text_area("Observações", placeholder="Informações adicionais...")
                st.markdown("**Campos obrigatórios estão marcados com ***")
                if st.form_submit_button("💾 Salvar Insumo", width='stretch'):
                    if codigo and descricao and categoria and unidade:
                        dados: dict[str, Any] = {
                            'codigo': codigo.upper(),
                            'descricao': descricao,
                            'categoria_id': categoria['id'],
                            'unidade': unidade,
                            'quantidade_atual': quantidade_atual,
                            'quantidade_minima': quantidade_minima,
                            'fornecedor': fornecedor or None,
                            'marca': marca or None,
                            'localizacao': localizacao,
                            'observacoes': observacoes or None,
                            'data_validade': data_validade
                        }
                        success, message = manager.create_insumo(dados, user_data['id'])  # type: ignore
                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                            # Limpar formulário
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    else:
                        st.error("❌ Preencha todos os campos obrigatórios!")

    with tab3:
        st.subheader("📊 Relatórios de Insumos")
        st.info("🚧 Módulo de relatórios será implementado na próxima versão!")

    with tab4:
        if not can_edit:
            st.warning("⚠️ Você não tem permissão para ajustar estoques.")
        else:
            st.subheader("⚙️ Ajustes de Estoque")
            st.info("� Módulo de ajustes será implementado na próxima versão!")



# Instanciar o manager
insumos_manager = InsumosManager()