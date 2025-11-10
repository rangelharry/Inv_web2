import streamlit as st
import pandas as pd
from datetime import datetime  # type: ignore
from database.connection import db
from modules.auth import auth_manager
from typing import Any

def safe_float_convert(value: Any, default: float = 0.0) -> float:
    """Converte valor para float de forma segura, tratando strings como '-' """
    if value is None or value == '' or value == '-':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

class EquipamentosManuaisManager:
    def __init__(self):
        self.db: Any = db

    def create_equipamento(self, data: dict[str, Any]) -> int | None:
        """Cria um novo equipamento manual"""
        try:
            # Garantir que a conexão esteja limpa
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            
            cursor = self.db.get_connection().cursor()  # type: ignore
            cursor.execute("""
                INSERT INTO equipamentos_manuais (
                    codigo, descricao, tipo, marca, status, localizacao, 
                    quantitativo, valor, observacoes, ativo, criado_por
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data.get('codigo', ''),
                data['nome'],  # nome vai para descricao
                data.get('tipo', ''),
                data.get('marca', ''),
                data.get('status', 'Disponível'),
                data.get('localizacao', 'Almoxarifado'),
                data.get('quantitativo', 1),
                data.get('valor', 0.0),
                data.get('observacoes', ''),
                1,  # ativo
                1   # criado_por (usuário admin padrão)
            ))
            # Recuperar o id do equipamento criado
            cursor.execute("SELECT currval(pg_get_serial_sequence('equipamentos_manuais','id'))")
            result = cursor.fetchone()
            equipamento_id = result['id'] if result else None
            self.db.get_connection().commit()  # type: ignore
            
            # Log da ação
            auth_manager.log_action(
                1,  # user_id
                'criar', 'equipamentos_manuais', equipamento_id,
                f"Equipamento manual criado: {data['nome']} (ID: {equipamento_id})"
            )
            
            return equipamento_id
        except Exception as e:
            # Fazer rollback explícito para limpar o estado da transação
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            st.error(f"Erro ao criar equipamento: {e}")
            return None
    
    def get_equipamentos(self, filters: dict[str, Any] | None = None) -> pd.DataFrame:
        """Busca equipamentos manuais com filtros"""
        try:
            # Garantir que a conexão esteja limpa
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            
            cursor = self.db.get_connection().cursor()  # type: ignore
            query = """SELECT id, codigo, descricao as nome, marca, status, estado, localizacao, \
                       quantitativo, tipo, valor, data_compra, loja, observacoes \
                       FROM equipamentos_manuais WHERE ativo = TRUE"""
            params: list[Any] = []
            
            if filters:
                if filters.get('nome'):
                    query += " AND descricao LIKE %s"
                    params.append(f"%{filters['nome']}%")
                if filters.get('categoria'):
                    query += " AND categoria_id = %s"
                    params.append(filters['categoria'])
                if filters.get('status'):
                    query += " AND status = %s"
                    params.append(filters['status'])
                if filters.get('marca'):
                    query += " AND marca LIKE %s"
                    params.append(f"%{filters['marca']}%")
                if filters.get('localizacao'):
                    query += " AND localizacao LIKE %s"
                    params.append(f"%{filters['localizacao']}%")
                    
            query += " ORDER BY descricao"
            
            cursor.execute(query, params)  # type: ignore
            results = cursor.fetchall()
            
            # Usar as colunas da query
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(results, columns=columns) if results else pd.DataFrame()
            return df
            
        except Exception as e:
            # Fazer rollback explícito para limpar o estado da transação
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            st.error(f"Erro ao buscar equipamentos: {e}")
            return pd.DataFrame()
    
    def update_equipamento(self, equipamento_id: int, data: dict[str, Any]) -> bool:
        """Atualiza um equipamento manual"""
        try:
            # Garantir que a conexão esteja limpa
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            
            cursor = self.db.get_connection().cursor()  # type: ignore
            
            cursor.execute("""
                UPDATE equipamentos_manuais SET
                    codigo = %s, descricao = %s, marca = %s, tipo = %s, status = %s,
                    localizacao = %s, quantitativo = %s, valor = %s, observacoes = %s
                WHERE id = %s
            """, (
                data.get('codigo', ''),
                data['nome'],  # nome vai para descricao
                data.get('marca', ''),
                data.get('tipo', ''),
                data.get('status', 'Disponível'),
                data.get('localizacao', 'Almoxarifado'),
                data.get('quantitativo', 1),
                data.get('valor', 0.0),
                data.get('observacoes', ''),
                equipamento_id
            ))
            
            self.db.get_connection().commit()  # type: ignore
            
            # Log da ação
            auth_manager.log_action(
                1,  # user_id
                'editar', 'equipamentos_manuais', equipamento_id,
                f"Equipamento manual atualizado: {data['nome']} (ID: {equipamento_id})"
            )
            
            return True
        except Exception as e:
            # Fazer rollback explícito para limpar o estado da transação
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            st.error(f"Erro ao atualizar equipamento: {e}")
            return False
    
    def delete_equipamento(self, equipamento_id: int, nome: str) -> bool:
        """Remove um equipamento manual"""
        try:
            # Garantir que a conexão esteja limpa
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            
            cursor = self.db.get_connection().cursor()  # type: ignore
            
            cursor.execute("DELETE FROM equipamentos_manuais WHERE id = %s", (equipamento_id,))
            self.db.get_connection().commit()  # type: ignore
            
            # Log da ação
            auth_manager.log_action(
                1,  # user_id
                'excluir', 'equipamentos_manuais', equipamento_id,
                f"Equipamento manual removido: {nome} (ID: {equipamento_id})"
            )
            
            return True
        except Exception as e:
            # Fazer rollback explícito para limpar o estado da transação
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            st.error(f"Erro ao remover equipamento: {e}")
            return False
    
    def get_categorias(self) -> list[str]:
        """Busca categorias de equipamentos manuais da tabela categorias"""
        try:
            # Garantir que a conexão esteja limpa
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            
            cursor = self.db.get_connection().cursor()  # type: ignore
            cursor.execute("""
                SELECT c.nome FROM categorias c 
                WHERE c.tipo = 'equipamento_manual' OR c.tipo IS NULL
                ORDER BY c.nome
            """)
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            # Fazer rollback explícito para limpar o estado da transação
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            return ['Ferramentas Manuais', 'Equipamentos de Medição', 'Ferramentas de Corte']
    
    def get_status_options(self) -> list[str]:
        """Retorna opções de status para equipamentos"""
        return ['Disponível', 'Em Uso', 'Manutenção', 'Danificado', 'Inativo']
    
    def get_dashboard_stats(self) -> dict[str, Any]:
        """Estatísticas para o dashboard"""
        try:
            cursor = self.db.get_connection().cursor()  # type: ignore
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Disponível' THEN 1 ELSE 0 END) as disponiveis,
                    SUM(CASE WHEN status = 'Manutenção' THEN 1 ELSE 0 END) as manutencao,
                    SUM(CASE WHEN status = 'Em Uso' THEN 1 ELSE 0 END) as em_uso,
                    SUM(CASE WHEN valor_compra IS NOT NULL THEN valor_compra ELSE 0 END) as valor_total
                FROM equipamentos_manuais WHERE ativo = TRUE
            """)
            result = cursor.fetchone()
            return {
                'total': result['count'] if result else 0,
                'disponiveis': result[1] or 0,
                'manutencao': result[2] or 0,
                'em_uso': result[3] or 0,
                'valor_total': result[4] or 0
            }
        except:
            return {'total': 0, 'disponiveis': 0, 'manutencao': 0, 'em_uso': 0, 'valor_total': 0}

def show_equipamentos_manuais_page():
    """Interface principal dos equipamentos manuais"""
    
    st.title("🔧 Equipamentos Manuais")
    user_data = st.session_state.user_data
    if not auth_manager.check_permission(user_data['perfil'], "read"):
        st.error("❌ Você não tem permissão para acessar esta página.")
        return
    manager = EquipamentosManuaisManager()
    
    # Abas principais
    tab1, tab2, tab3 = st.tabs(["📋 Lista", "➕ Adicionar", "📊 Estatísticas"])
    
    with tab1:
        st.subheader("Lista de Equipamentos Manuais")
        # Filtros
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            filtro_nome = st.text_input("Nome do Equipamento")
        with col2:
            filtro_categoria = st.selectbox("Categoria", ["Todas"] + manager.get_categorias())
        with col3:
            filtro_status = st.selectbox("Status", ["Todos"] + manager.get_status_options())
        with col4:
            filtro_marca = st.text_input("Marca")

        # Aplicar filtros
        filters: dict[str, Any] = {}
        if filtro_nome:
            filters['nome'] = filtro_nome
        if filtro_categoria != "Todas":
            filters['categoria'] = filtro_categoria
        if filtro_status != "Todos":
            filters['status'] = filtro_status
        if filtro_marca:
            filters['marca'] = filtro_marca

        # Buscar equipamentos
        equipamentos = manager.get_equipamentos(filters)  # type: ignore
        df = equipamentos.copy() if not equipamentos.empty else pd.DataFrame()

        if not df.empty:
            # Estatísticas rápidas
            total_eq = len(df)
            disponiveis = sum(1 for _, r in df.iterrows() if (r['status'] or 'Disponível') == 'Disponível')
            em_uso = sum(1 for _, r in df.iterrows() if (r['status'] or '') == 'Em Uso')
            manutencao = sum(1 for _, r in df.iterrows() if (r['status'] or '') == 'Manutenção')
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            col_stat1.metric("Total de Equipamentos", total_eq)
            col_stat2.metric("Disponíveis", disponiveis)
            col_stat3.metric("Em Uso", em_uso)
            col_stat4.metric("Em Manutenção", manutencao)

            # Paginação
            num_rows = st.selectbox("Linhas por página:", options=[10, 20, 30, 50, 100], index=2)
            total_pages = (len(df) - 1) // num_rows + 1
            if 'page_em' not in st.session_state:
                st.session_state.page_em = 1
            if st.session_state.page_em > total_pages:
                st.session_state.page_em = total_pages
            if st.session_state.page_em < 1:
                st.session_state.page_em = 1
            page = st.session_state.page_em
            start_idx = (page - 1) * num_rows
            end_idx = start_idx + num_rows
            df_paginado = df.iloc[start_idx:end_idx]

            # Cabeçalho da tabela com barra de rolagem horizontal
            with st.container():
                st.write("**Tabela de Equipamentos Manuais** (Use a barra de rolagem horizontal para ver todas as colunas)")
                
                # Exibir equipamentos com botões de ação
            # Botões de ação para cada equipamento
            for idx, row in df_paginado.iterrows():
                col1, col2, col3, col4 = st.columns([6, 1, 1, 1])
                with col1:
                    localizacao = row['localizacao'] if row['localizacao'] else 'Almoxarifado'
                    st.markdown(f"""
                    **{row['codigo']}** - {row['nome']}  
                    📍 <span style='position:relative;cursor:pointer;' title='Localização atual: {localizacao}'>{localizacao} <span style='color:#888'>&#9432;</span></span> | 
                    🏷️ {row['marca'] if row['marca'] else 'N/A'} | 
                    📊 {row['status'] if row['status'] else 'Disponível'} | 
                    � Qtd: {row['quantitativo'] if row['quantitativo'] else '1'} | 
                    �💰 R$ {safe_float_convert(row['valor']):,.2f}
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("✏️ Editar", key=f"edit_em_{row['id']}_{idx}", help="Editar equipamento"):
                        st.session_state[f'edit_mode_em_{row["id"]}'] = True
                        st.rerun()
                with col3:
                    if st.button("📦 Mover", key=f"move_em_{row['id']}_{idx}", help="Movimentar equipamento"):
                        # Fecha todos os outros modais de movimentação
                        for k in list(st.session_state.keys()):
                            if isinstance(k, str) and k.startswith("move_mode_em_") and k != f"move_mode_em_{row['id']}":
                                st.session_state[k] = False
                        st.session_state[f"move_mode_em_{row['id']}"] = True
                        st.rerun()
                with col4:
                    if st.button("❌ Excluir", key=f"del_em_{row['id']}_{idx}", help="Excluir equipamento"):
                        if manager.delete_equipamento(int(row['id']), row['nome']):
                            st.success(f"Equipamento {row['nome']} removido com sucesso!")
                            st.rerun()

                # Modal de edição
                if st.session_state.get(f'edit_mode_em_{row["id"]}', False):
                    with st.expander(f"🔧 Editando: {row['codigo']} - {row['nome']}", expanded=True):
                        col_ed1, col_ed2 = st.columns(2)
                        with col_ed1:
                            novo_nome = st.text_input("Descrição:", value=row['nome'], key=f"nome_em_{row['id']}")
                            nova_marca = st.text_input("Marca:", value=row['marca'] if row['marca'] else '', key=f"marca_em_{row['id']}")
                            novo_tipo = st.text_input("Tipo:", value=row['tipo'] if row['tipo'] else '', key=f"tipo_em_{row['id']}")
                            novo_quantitativo = st.number_input("Quantidade:", min_value=1, value=int(row['quantitativo']) if row['quantitativo'] else 1, key=f"qtd_em_{row['id']}")
                        with col_ed2:
                            novo_status = st.selectbox("Status:", manager.get_status_options(), index=manager.get_status_options().index(row['status']) if row['status'] in manager.get_status_options() else 0, key=f"status_em_{row['id']}")
                            nova_localizacao = st.text_input("Localização:", value=row['localizacao'] if row['localizacao'] else '', key=f"localizacao_em_{row['id']}")
                            novo_valor = st.number_input("Valor:", min_value=0.0, value=safe_float_convert(row['valor']), key=f"valor_em_{row['id']}")
                        novas_observacoes = st.text_area("Observações:", value=row['observacoes'] if row['observacoes'] else '', key=f"obs_em_{row['id']}")

                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("💾 Salvar", key=f"save_em_{row['id']}", type="primary"):
                                dados_update: dict[str, Any] = {
                                    'codigo': row['codigo'],
                                    'nome': novo_nome,
                                    'marca': nova_marca,
                                    'tipo': novo_tipo,
                                    'status': novo_status,
                                    'localizacao': nova_localizacao,
                                    'quantitativo': novo_quantitativo,
                                    'valor': float(novo_valor),
                                    'observacoes': novas_observacoes
                                }
                                success = manager.update_equipamento(int(row['id']), dados_update)  # type: ignore
                                if success:
                                    st.success(f"Equipamento {row['codigo']} atualizado com sucesso!")
                                    del st.session_state[f"edit_mode_em_{row['id']}"]
                                    st.rerun()
                                else:
                                    st.error("Erro ao atualizar equipamento.")
                        with col_btn2:
                            if st.button("❌ Cancelar", key=f"cancel_em_{row['id']}"):
                                del st.session_state[f"edit_mode_em_{row['id']}"]
                                st.rerun()
                
                # Modal de movimentação
                if st.session_state.get(f'move_mode_em_{row["id"]}', False):
                    from modules.movimentacao_modal import show_movimentacao_modal_equipamento_manual  # type: ignore
                    show_movimentacao_modal_equipamento_manual(int(row['id']))
                    
                    # Botão para fechar o modal
                    if st.button("❌ Fechar", key=f"close_move_em_{row['id']}"):
                        del st.session_state[f'move_mode_em_{row["id"]}']
                        st.session_state['modal_type_manual'] = None
                        st.session_state['last_modal_item_id_manual'] = None
                        st.rerun()
                
                # Separador visual entre equipamentos
                st.markdown("---")

            # Navegação com botões
            if total_pages > 1:
                col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns([1, 1, 2, 1, 1])
                with col_nav1:
                    if st.button("⏮️ Primeira", key="primeira_em") and page > 1:
                        st.session_state.page_em = 1
                        st.rerun()
                with col_nav2:
                    if st.button("⬅️ Anterior", key="anterior_em") and page > 1:
                        st.session_state.page_em = page - 1
                        st.rerun()
                with col_nav3:
                    st.write(f"Página {page} de {total_pages}")
                with col_nav4:
                    if st.button("➡️ Próxima", key="proxima_em") and page < total_pages:
                        st.session_state.page_em = page + 1
                        st.rerun()
                with col_nav5:
                    if st.button("⏭️ Última", key="ultima_em") and page < total_pages:
                        st.session_state.page_em = total_pages
                        st.rerun()

            # Botão de atualizar
            if st.button("🔄 Atualizar", key="atualizar_em", width='stretch'):
                st.rerun()
        else:
            st.info("📭 Nenhum equipamento encontrado com os filtros aplicados.")
    
    with tab2:
        if not auth_manager.check_permission(user_data['perfil'], "create"):
            st.error("❌ Você não tem permissão para adicionar equipamentos.")
            return
            
        st.subheader("Adicionar Novo Equipamento Manual")
        
        with st.form("form_equipamento", clear_on_submit=True):
            # Buscar equipamentos existentes para gerar código sequencial
            equipamentos_existentes = manager.get_equipamentos()
            ultimo_codigo = "MAN-0001"
            if not equipamentos_existentes.empty:
                codigos = [str(eq['codigo']) for _, eq in equipamentos_existentes.iterrows() if str(eq['codigo']).startswith("MAN-")]
                numeros = []
                for cod in codigos:
                    try:
                        numeros.append(int(cod.replace("MAN-", "")))  # type: ignore
                    except:
                        pass
                if numeros:
                    proximo_num: int = max(numeros) + 1  # type: ignore
                    ultimo_codigo = f"MAN-{proximo_num:04d}"
            
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("* Código", value=ultimo_codigo, disabled=True, key="form_eq_manual_codigo")
                codigo = ultimo_codigo
                nome = st.text_input("Nome do Equipamento *", placeholder="Ex: Furadeira", key="form_eq_manual_nome")
                marca = st.text_input("Marca", placeholder="Ex: Bosch", key="form_eq_manual_marca")
                tipo = st.text_input("Tipo", placeholder="Ex: Ferramenta Manual", key="form_eq_manual_tipo")
                quantitativo = st.number_input("Quantidade", min_value=1, value=1, step=1, key="form_eq_manual_qtd")
            with col2:
                status = st.selectbox("Status", manager.get_status_options(), key="form_eq_manual_status")
                localizacao = st.text_input("Localização", placeholder="Ex: Almoxarifado", key="form_eq_manual_localizacao")
                valor = st.number_input("Valor", min_value=0.0, step=0.01, key="form_eq_manual_valor")
            observacoes = st.text_area("Observações", placeholder="Observações gerais", key="form_eq_manual_obs")
            
            submitted = st.form_submit_button("💾 Cadastrar Equipamento", type="primary")
            
            if submitted:
                if nome:
                    data: dict[str, Any] = {
                        'codigo': codigo,
                        'nome': nome,
                        'marca': marca,
                        'tipo': tipo,
                        'status': status,
                        'localizacao': localizacao,
                        'quantitativo': quantitativo,
                        'valor': valor,
                        'observacoes': observacoes
                    }
                    equipamento_id = manager.create_equipamento(data)  # type: ignore
                    if equipamento_id:
                        st.success(f"✅ Equipamento '{nome}' cadastrado com sucesso! (ID: {equipamento_id})")
                        # Limpar formulário após sucesso
                        for key in list(st.session_state.keys()):
                            if key.startswith('form_eq_manual_'):
                                del st.session_state[key]
                        st.rerun()
                else:
                    st.error("❌ Preencha o nome do equipamento!")
    
    with tab3:
        st.subheader("📊 Estatísticas dos Equipamentos Manuais")
        
        stats = manager.get_dashboard_stats()
        
        # Cards de estatísticas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Equipamentos", stats['total'])
        
        with col2:
            st.metric("Equipamentos Disponíveis", stats['disponiveis'])
        
        with col3:
            st.metric("Em Uso", stats['em_uso'])
        
        with col4:
            st.metric("Valor Total", f"R$ {stats['valor_total']:,.2f}")

# Instância global
equipamentos_manuais_manager = EquipamentosManuaisManager()
