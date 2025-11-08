import streamlit as st
import pandas as pd
from datetime import datetime  # type: ignore
from database.connection import db
from modules.auth import auth_manager
from typing import Any

class EquipamentosEletricosManager:
    def __init__(self):
        self.db: Any = db

    def create_equipamento(self, data: dict[str, Any]) -> int | None:
        """Cria um novo equipamento elétrico"""
        try:
            # Garantir que a conexão esteja limpa
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            
            cursor = self.db.get_connection().cursor()  # type: ignore
            cursor.execute("""
                INSERT INTO equipamentos_eletricos (
                    codigo, nome, marca, modelo, numero_serie, voltagem, potencia, 
                    status, localizacao, valor_compra, observacoes, ativo, criado_por
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data.get('codigo', ''),
                data['nome'],
                data.get('marca', ''),
                data.get('modelo', ''),
                data.get('numero_serie', ''),
                data.get('voltagem', ''),
                data.get('potencia', ''),
                data.get('status', 'Disponível'),
                data.get('localizacao', 'Almoxarifado'),
                data.get('valor_compra', 0.0),
                data.get('observacoes', ''),
                1,  # ativo
                1   # criado_por (usuário admin padrão)
            ))
            # Recuperar o id do equipamento criado
            cursor.execute("SELECT currval(pg_get_serial_sequence('equipamentos_eletricos','id'))")
            result = cursor.fetchone()
            equipamento_id = result['id'] if result else None
            self.db.get_connection().commit()  # type: ignore
            
            # Log da ação
            auth_manager.log_action(
                1,  # id do usuário
                f"Criou equipamento elétrico: {data['nome']} (ID: {equipamento_id})",
                "Equipamentos Elétricos",
                equipamento_id
            )
            
            return equipamento_id
        except Exception as e:
            # Fazer rollback explícito para limpar o estado da transação
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            st.error(f"Erro ao criar equipamento: {e}")
            return None
    
    def get_equipamentos(self, filters: dict[str, Any] | None = None) -> pd.DataFrame:
        """Busca equipamentos elétricos com filtros"""
        try:
            # Garantir que a conexão esteja limpa
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            
            cursor = self.db.get_connection().cursor()  # type: ignore
            query = """SELECT id, codigo, nome, marca, modelo, status, localizacao, valor_compra, \
                       voltagem, potencia, numero_serie, observacoes FROM equipamentos_eletricos WHERE ativo = TRUE"""
            params: list[Any] = []
            
            if filters:
                if filters.get('nome'):
                    query += " AND nome LIKE %s"
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
                    
            query += " ORDER BY nome"
            
            cursor.execute(query, params)  # type: ignore
            results = cursor.fetchall()
            
            columns = ['id', 'codigo', 'nome', 'marca', 'modelo', 'status', 'localizacao', 'valor_compra', \
                      'voltagem', 'potencia', 'numero_serie', 'observacoes']
            return pd.DataFrame(results, columns=columns) if results else pd.DataFrame()
            
        except Exception as e:
            # Fazer rollback explícito para limpar o estado da transação
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            st.error(f"Erro ao buscar equipamentos: {e}")
            return pd.DataFrame()
    
    def update_equipamento(self, equipamento_id: int, data: dict[str, Any]) -> bool:
        """Atualiza um equipamento elétrico"""
        try:
            # Garantir que a conexão esteja limpa
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            
            cursor = self.db.get_connection().cursor()  # type: ignore
            
            cursor.execute("""
                UPDATE equipamentos_eletricos SET
                    codigo = %s, nome = %s, marca = %s, modelo = %s, numero_serie = %s,
                    voltagem = %s, potencia = %s, status = %s, localizacao = %s, 
                    valor_compra = %s, observacoes = %s
                WHERE id = %s
            """, (
                data.get('codigo', ''),
                data['nome'],
                data.get('marca', ''),
                data.get('modelo', ''),
                data.get('numero_serie', ''),
                data.get('voltagem', ''),
                data.get('potencia', ''),
                data.get('status', 'Disponível'),
                data.get('localizacao', 'Almoxarifado'),
                data.get('valor_compra', 0.0),
                data.get('observacoes', ''),
                equipamento_id
            ))
            
            self.db.get_connection().commit()  # type: ignore
            
            # Log da ação
            auth_manager.log_action(
                1,  # id do usuário
                f"Atualizou equipamento elétrico: {data['nome']} (ID: {equipamento_id})",
                "Equipamentos Elétricos",
                equipamento_id
            )
            
            return True
        except Exception as e:
            # Fazer rollback explícito para limpar o estado da transação
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            st.error(f"Erro ao atualizar equipamento: {e}")
            return False
    
    def delete_equipamento(self, equipamento_id: int, nome: str) -> bool:
        """Remove um equipamento elétrico"""
        try:
            # Garantir que a conexão esteja limpa
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            
            cursor = self.db.get_connection().cursor()  # type: ignore
            
            cursor.execute("DELETE FROM equipamentos_eletricos WHERE id = %s", (equipamento_id,))
            self.db.get_connection().commit()  # type: ignore
            
            # Log da ação
            auth_manager.log_action(
                1,  # id do usuário
                f"Removeu equipamento elétrico: {nome} (ID: {equipamento_id})",
                "Equipamentos Elétricos",
                equipamento_id
            )
            
            return True
        except Exception as e:
            # Fazer rollback explícito para limpar o estado da transação
            if hasattr(self.db.get_connection(), 'rollback'):
                self.db.get_connection().rollback()  # type: ignore
            st.error(f"Erro ao remover equipamento: {e}")
            return False
    
    def get_categorias(self) -> list[str]:
        """Busca categorias de equipamentos elétricos da tabela categorias"""
        try:
            cursor = self.db.get_connection().cursor()  # type: ignore
            cursor.execute("""
                SELECT c.nome FROM categorias c 
                WHERE c.tipo = 'equipamento_eletrico' OR c.tipo IS NULL
                ORDER BY c.nome
            """)
            return [row[0] for row in cursor.fetchall()]
        except:
            return ['Ferramentas Elétricas', 'Motores', 'Equipamentos de Medição']
    
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
                    SUM(CASE WHEN valor_compra IS NOT NULL THEN valor_compra ELSE 0 END) as valor_total
                FROM equipamentos_eletricos
            """)
            result = cursor.fetchone()
            return {
                'total': result['count'] if result else 0,
                'disponiveis': result[1] or 0,
                'manutencao': result[2] or 0,
                'valor_total': result[3] or 0
            }
        except:
            return {'total': 0, 'disponiveis': 0, 'manutencao': 0, 'valor_total': 0}

def show_equipamentos_eletricos_page():
    """Interface principal dos equipamentos elétricos"""
    
    st.title("⚡ Equipamentos Elétricos")
    user_data = st.session_state.user_data
    if not auth_manager.check_permission(user_data['perfil'], "read"):
        st.error("❌ Você não tem permissão para acessar esta página.")
        return
    manager = EquipamentosEletricosManager()
    
    # Abas principais
    tab1, tab2, tab3 = st.tabs(["📋 Lista", "➕ Adicionar", "📊 Estatísticas"])
    
    with tab1:
        st.subheader("Lista de Equipamentos Elétricos")
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
            disponiveis = sum(1 for _, r in df.iterrows() if r['status'] == 'Disponível')
            em_uso = sum(1 for _, r in df.iterrows() if r['status'] == 'Em Uso')
            manutencao = sum(1 for _, r in df.iterrows() if r['status'] == 'Manutenção')
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            col_stat1.metric("Total de Equipamentos", total_eq)
            col_stat2.metric("Disponíveis", disponiveis)
            col_stat3.metric("Em Uso", em_uso)
            col_stat4.metric("Em Manutenção", manutencao)

            # Paginação
            num_rows = st.selectbox("Linhas por página:", options=[10, 20, 30, 50, 100], index=2)
            total_pages = (len(df) - 1) // num_rows + 1
            if 'page_eq' not in st.session_state:
                st.session_state.page_eq = 1
            if st.session_state.page_eq > total_pages:
                st.session_state.page_eq = total_pages
            if st.session_state.page_eq < 1:
                st.session_state.page_eq = 1
            page = st.session_state.page_eq
            start_idx = (page - 1) * num_rows
            end_idx = start_idx + num_rows
            df_paginado = df.iloc[start_idx:end_idx]

            # Cabeçalho da tabela
            col_header = st.columns([0.8, 1.5, 1.2, 1.2, 1, 1, 1, 1, 1, 1, 1, 1])
            headers = ["Código", "Nome", "Marca", "Modelo", "Status", "Localização", "Valor Compra", "Voltagem", "Potência", "Editar", "Mover", "Ação"]
            for i, h in enumerate(headers):
                with col_header[i]:
                    st.write(f"**{h}**")
            st.write("---")

            # Exibir tabela com botões de edição
            for idx, row in df_paginado.iterrows():
                with st.container():
                    cols = st.columns([0.8, 1.5, 1.2, 1.2, 1, 1, 1, 1, 1, 1, 1, 1])
                    with cols[0]:
                        st.write(f"**{row['codigo']}**")
                    with cols[1]:
                        st.write(row['nome'])
                    with cols[2]:
                        st.write(row['marca'])
                    with cols[3]:
                        st.write(row['modelo'])
                    with cols[4]:
                        st.write(row['status'])
                    with cols[5]:
                        localizacao = row['localizacao'] if row['localizacao'] else 'Almoxarifado'
                        st.markdown(f'''<span style="position:relative;cursor:pointer;" title="Localização atual: {localizacao}">{localizacao} <span style='color:#888'>&#9432;</span></span>''', unsafe_allow_html=True)
                    with cols[6]:
                        if row['valor_compra'] is not None:
                            st.write(f"R$ {row['valor_compra']:,.2f}")
                        else:
                            st.write("N/A")
                    with cols[7]:
                        st.write(row['voltagem'])
                    with cols[8]:
                        st.write(row['potencia'])
                    with cols[9]:
                        if st.button("✏️", key=f"edit_eq_{row['id']}_{idx}", help="Editar equipamento"):
                            st.session_state[f'edit_mode_eq_{row["id"]}'] = True
                            st.rerun()
                    with cols[10]:
                        if st.button("📦", key=f"move_eq_{row['id']}_{idx}", help="Movimentar equipamento"):
                            # Fecha todos os outros modais de movimentação
                            for k in list(st.session_state.keys()):
                                if isinstance(k, str) and k.startswith("move_mode_eq_") and k != f"move_mode_eq_{row['id']}":
                                    st.session_state[k] = False
                            st.session_state[f"move_mode_eq_{row['id']}"] = True
                            st.rerun()
                    with cols[11]:
                        if st.button("❌", key=f"del_eq_{row['id']}_{idx}", help="Excluir equipamento"):
                            st.session_state[f'confirm_delete_eq_{row["id"]}'] = True
                            st.rerun()
                
                # Modal de confirmação de exclusão
                if st.session_state.get(f'confirm_delete_eq_{row["id"]}', False):
                    st.markdown("---")
                    st.error(f"⚠️ **CONFIRMAÇÃO DE EXCLUSÃO**")
                    st.warning(f"Tem certeza que deseja excluir o equipamento **{row['nome']}** (Código: {row['codigo']})?\n\nEsta ação não pode ser desfeita!")
                    
                    col_cancel, col_confirm = st.columns(2)
                    with col_cancel:
                        if st.button("❌ Cancelar", key=f"cancel_del_eq_{row['id']}"):
                            del st.session_state[f'confirm_delete_eq_{row["id"]}']
                            st.rerun()
                    
                    with col_confirm:
                        if st.button("🗑️ Confirmar Exclusão", key=f"confirm_del_eq_{row['id']}", type="primary"):
                            if manager.delete_equipamento(int(row['id']), row['nome']):
                                st.success(f"Equipamento {row['nome']} removido com sucesso!")
                                del st.session_state[f'confirm_delete_eq_{row["id"]}']
                                st.rerun()
                            else:
                                st.error("Erro ao excluir equipamento.")
                    st.markdown("---")

                # Modal de edição
                if st.session_state.get(f'edit_mode_eq_{row["id"]}', False):
                    with st.expander(f"🔧 Editando: {row['codigo']} - {row['nome']}", expanded=True):
                        col_ed1, col_ed2 = st.columns(2)
                        with col_ed1:
                            novo_nome = st.text_input("Nome:", value=row['nome'], key=f"nome_eq_{row['id']}")
                            nova_marca = st.text_input("Marca:", value=row['marca'], key=f"marca_eq_{row['id']}")
                            novo_modelo = st.text_input("Modelo:", value=row['modelo'], key=f"modelo_eq_{row['id']}")
                            novo_numero_serie = st.text_input("Número de Série:", value=row['numero_serie'], key=f"numserie_eq_{row['id']}")
                            nova_voltagem = st.text_input("Voltagem:", value=row['voltagem'], key=f"voltagem_eq_{row['id']}")
                            nova_potencia = st.text_input("Potência:", value=row['potencia'], key=f"potencia_eq_{row['id']}")
                        with col_ed2:
                            novo_status = st.selectbox("Status:", manager.get_status_options(), index=manager.get_status_options().index(row['status']) if row['status'] in manager.get_status_options() else 0, key=f"status_eq_{row['id']}")
                            nova_localizacao = st.text_input("Localização:", value=row['localizacao'], key=f"localizacao_eq_{row['id']}")
                            novo_valor_compra = st.number_input("Valor Compra:", min_value=0.0, value=float(row['valor_compra']), key=f"valorcompra_eq_{row['id']}")
                            novas_observacoes = st.text_area("Observações:", value=row['observacoes'], key=f"obs_eq_{row['id']}")

                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("💾 Salvar", key=f"save_eq_{row['id']}", type="primary"):
                                dados_update: dict[str, Any] = {
                                    'codigo': row['codigo'],
                                    'nome': novo_nome,
                                    'marca': nova_marca,
                                    'modelo': novo_modelo,
                                    'numero_serie': novo_numero_serie,
                                    'voltagem': nova_voltagem,
                                    'potencia': nova_potencia,
                                    'status': novo_status,
                                    'localizacao': nova_localizacao,
                                    'valor_compra': float(novo_valor_compra),
                                    'observacoes': novas_observacoes
                                }
                                success = manager.update_equipamento(int(row['id']), dados_update)  # type: ignore
                                if success:
                                    st.success(f"Equipamento {row['codigo']} atualizado com sucesso!")
                                    del st.session_state[f'edit_mode_eq_{row["id"]}']
                                    st.rerun()
                                else:
                                    st.error("Erro ao atualizar equipamento.")
                        with col_btn2:
                            if st.button("❌ Cancelar", key=f"cancel_eq_{row['id']}"):
                                del st.session_state[f"edit_mode_eq_{row['id']}"]
                                st.rerun()
                    st.divider()
                
                # Modal de movimentação
                if st.session_state.get(f'move_mode_eq_{row["id"]}', False):
                    from modules.movimentacao_modal import show_movimentacao_modal_equipamento_eletrico  # type: ignore
                    show_movimentacao_modal_equipamento_eletrico(int(row['id']))
                    
                    # Botão para fechar o modal
                    if st.button("❌ Fechar", key=f"close_move_eq_{row['id']}"):
                        del st.session_state[f'move_mode_eq_{row["id"]}']
                        st.session_state['modal_type_eletrico'] = None
                        st.session_state['last_modal_item_id_eletrico'] = None
                        st.rerun()
                    
                    st.divider()

            # Navegação com botões
            if total_pages > 1:
                col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns([1, 1, 2, 1, 1])
                with col_nav1:
                    if st.button("⏮️ Primeira", key="primeira_eq") and page > 1:
                        st.session_state.page_eq = 1
                        st.rerun()
                with col_nav2:
                    if st.button("⬅️ Anterior", key="anterior_eq") and page > 1:
                        st.session_state.page_eq = page - 1
                        st.rerun()
                with col_nav3:
                    st.write(f"Página {page} de {total_pages}")
                with col_nav4:
                    if st.button("➡️ Próxima", key="proxima_eq") and page < total_pages:
                        st.session_state.page_eq = page + 1
                        st.rerun()
                with col_nav5:
                    if st.button("⏭️ Última", key="ultima_eq") and page < total_pages:
                        st.session_state.page_eq = total_pages
                        st.rerun()

            # Botão de atualizar
            if st.button("🔄 Atualizar", key="atualizar_eq", width='stretch'):
                st.rerun()
        else:
            st.info("📭 Nenhum equipamento encontrado com os filtros aplicados.")
    
    with tab2:
        if not auth_manager.check_permission(user_data['perfil'], "create"):
            st.error("❌ Você não tem permissão para adicionar equipamentos.")
            return
            
        st.subheader("Adicionar Novo Equipamento Elétrico")
        with st.form("form_equipamento"):
            # Buscar equipamentos existentes para gerar código sequencial
            equipamentos_existentes = manager.get_equipamentos()
            ultimo_codigo = "EQ-0001"
            if not equipamentos_existentes.empty:
                codigos = [str(eq['codigo']) for _, eq in equipamentos_existentes.iterrows() if str(eq['codigo']).startswith("EQ-")]
                numeros = []
                for cod in codigos:
                    try:
                        numeros.append(int(cod.replace("EQ-", "")))  # type: ignore
                    except:
                        pass
                if numeros:
                    proximo_num: int = max(numeros) + 1  # type: ignore
                    ultimo_codigo = f"EQ-{proximo_num:04d}"
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("* Código", value=ultimo_codigo, disabled=True)
                codigo = ultimo_codigo
                nome = st.text_input("Nome do Equipamento *", placeholder="Ex: Motor Elétrico")
                marca = st.text_input("Marca", placeholder="Ex: WEG")
                modelo = st.text_input("Modelo", placeholder="Ex: W22")
                numero_serie = st.text_input("Número de Série", placeholder="Ex: ABC123")
                voltagem = st.text_input("Voltagem", placeholder="Ex: 220V")
            with col2:
                potencia = st.text_input("Potência", placeholder="Ex: 1000W")
                status = st.selectbox("Status", manager.get_status_options())
                localizacao = st.text_input("Localização", placeholder="Ex: Almoxarifado")
                valor_compra = st.number_input("Valor de Compra", min_value=0.0, step=0.01)
                observacoes = st.text_area("Observações", placeholder="Observações gerais")

            submitted = st.form_submit_button("💾 Cadastrar Equipamento", type="primary")

            if submitted:
                if nome:
                    data: dict[str, Any] = {
                        'codigo': codigo,
                        'nome': nome,
                        'marca': marca,
                        'modelo': modelo,
                        'numero_serie': numero_serie,
                        'voltagem': voltagem,
                        'potencia': potencia,
                        'status': status,
                        'localizacao': localizacao,
                        'valor_compra': valor_compra,
                        'observacoes': observacoes
                    }
                    equipamento_id = manager.create_equipamento(data)  # type: ignore
                    if equipamento_id:
                        st.success(f"✅ Equipamento '{nome}' cadastrado com sucesso! (ID: {equipamento_id})")
                        st.rerun()
                else:
                    st.error("❌ Preencha o nome do equipamento!")
    
    with tab3:
        st.subheader("📊 Estatísticas dos Equipamentos Elétricos")
        
        stats = manager.get_dashboard_stats()
        
        # Cards de estatísticas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Equipamentos", stats['total'])
        
        with col2:
            st.metric("Equipamentos Disponíveis", stats['disponiveis'])
        
        with col3:
            st.metric("Em Manutenção", stats['manutencao'])
        
        with col4:
            st.metric("Valor Total", f"R$ {stats['valor_total']:,.2f}")