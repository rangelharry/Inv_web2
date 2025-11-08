import streamlit as st
import pandas as pd
from datetime import date  # type: ignore
from database.connection import db  # type: ignore
from modules.auth import auth_manager
from typing import Any


class ObrasManager:
    def __init__(self):
        from database.connection import db as db_module
        self.db: Any = db_module

    def create_obra(self, data: dict[str, Any]) -> int | None:
        """Cria uma nova obra/departamento"""
        try:
            cursor = self.db.conn.cursor()  # type: ignore

            cursor.execute("""
                INSERT INTO obras (
                    codigo, nome, endereco, cidade, estado, cep, status,
                    responsavel, telefone, email, observacoes,
                    data_inicio, data_previsao, valor_orcado, valor_gasto, criado_por
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data['codigo'], data['nome'], data.get('endereco', ''),
                data.get('cidade', ''), data.get('estado', ''), data.get('cep', ''),
                data.get('status', 'ativo'), data.get('responsavel', ''),
                data.get('telefone', ''), data.get('email', ''), data.get('observacoes', ''),
                data.get('data_inicio'), data.get('data_previsao'),
                data.get('valor_orcado', 0), data.get('valor_gasto', 0),
                data.get('criado_por')
            ))

            # Recuperar o id da obra criada
            cursor.execute("SELECT currval(pg_get_serial_sequence('obras','id'))")
            result = cursor.fetchone()
            obra_id = result['id'] if result else None
            self.db.conn.commit()  # type: ignore

            # Log da ação
            auth_manager.log_action(
                data.get('criado_por', 1),
                f"Criou obra/departamento: {data['nome']} (ID: {obra_id})",
                "Obras/Departamentos",
                obra_id
            )

            return obra_id
        except Exception as e:
            self.db.conn.rollback()  # type: ignore
            st.error(f"Erro ao criar obra: {e}")
            return None

    def get_obras(self, filters: dict[str, Any] | None = None) -> pd.DataFrame:
        """Busca obras com filtros"""
        try:
            cursor = self.db.conn.cursor()  # type: ignore

            query = """
                SELECT 
                    id, codigo, nome, endereco, cidade, estado, cep, status,
                    responsavel, telefone, email, observacoes,
                    data_inicio, data_previsao, data_conclusao,
                    valor_orcado, valor_gasto, data_criacao
                FROM obras
                WHERE 1=1
            """
            params = []

            if filters:
                if filters.get('nome'):
                    query += " AND nome LIKE %s"
                    params.append(f"%{filters['nome']}%")  # type: ignore
                if filters.get('status'):
                    query += " AND status = %s"
                    params.append(filters['status'])  # type: ignore
                if filters.get('responsavel'):
                    query += " AND responsavel LIKE %s"
                    params.append(f"%{filters['responsavel']}%")  # type: ignore

            query += " ORDER BY nome"

            cursor.execute(query, params)
            results = cursor.fetchall()

            columns = [
                'id', 'codigo', 'nome', 'endereco', 'cidade', 'estado', 'cep', 'status',
                'responsavel', 'telefone', 'email', 'observacoes',
                'data_inicio', 'data_previsao', 'data_conclusao',
                'valor_orcado', 'valor_gasto', 'data_criacao'
            ]

            return pd.DataFrame(results, columns=columns) if results else pd.DataFrame()

        except Exception as e:
            st.error(f"Erro ao buscar obras: {e}")
            return pd.DataFrame()

    def update_obra(self, obra_id: int, data: dict[str, Any]) -> bool:
        """Atualiza uma obra/departamento"""
        try:
            cursor = self.db.conn.cursor()  # type: ignore

            cursor.execute("""
                UPDATE obras SET
                    codigo = %s, nome = %s, endereco = %s, cidade = %s, estado = %s, cep = %s,
                    status = %s, responsavel = %s, telefone = %s, email = %s, observacoes = %s,
                    data_inicio = %s, data_previsao = %s, valor_orcado = %s, valor_gasto = %s
                WHERE id = %s
            """, (
                data['codigo'], data['nome'], data.get('endereco', ''),
                data.get('cidade', ''), data.get('estado', ''), data.get('cep', ''),
                data.get('status', 'ativo'), data.get('responsavel', ''),
                data.get('telefone', ''), data.get('email', ''), data.get('observacoes', ''),
                data.get('data_inicio'), data.get('data_previsao'),
                data.get('valor_orcado', 0), data.get('valor_gasto', 0), obra_id
            ))

            self.db.conn.commit()  # type: ignore

            auth_manager.log_action(
                data.get('criado_por', 1),
                f"Atualizou obra/departamento: {data['nome']} (ID: {obra_id})",
                "Obras/Departamentos",
                obra_id
            )

            return True
        except Exception as e:
            self.db.conn.rollback()  # type: ignore
            st.error(f"Erro ao atualizar obra: {e}")
            return False

    def delete_obra(self, obra_id: int, nome: str) -> bool:
        """Remove uma obra/departamento"""
        try:
            cursor = self.db.conn.cursor()  # type: ignore

            cursor.execute("DELETE FROM obras WHERE id = %s", (obra_id,))
            self.db.conn.commit()  # type: ignore

            auth_manager.log_action(
                1,
                f"Removeu obra/departamento: {nome} (ID: {obra_id})",
                "Obras/Departamentos",
                obra_id
            )
            return True
        except Exception as e:
            self.db.conn.rollback()  # type: ignore
            st.error(f"Erro ao remover obra: {e}")
            return False

    def get_tipos_obra(self) -> list[str]:
        return ['Obra', 'Departamento', 'Setor', 'Unidade', 'Filial', 'Projeto']

    def get_status_options(self) -> list[str]:
        return ['Planejamento', 'Em Andamento', 'Pausada', 'Concluída', 'Cancelada', 'Ativo', 'Inativo']

    def get_dashboard_stats(self) -> dict[str, int]:
        """Estatísticas para o dashboard"""
        try:
            cursor = self.db.conn.cursor()  # type: ignore
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Ativo' THEN 1 ELSE 0 END) as ativas,
                    SUM(CASE WHEN status = 'Em Andamento' THEN 1 ELSE 0 END) as em_andamento,
                    SUM(CASE WHEN status = 'Concluída' THEN 1 ELSE 0 END) as concluidas,
                    SUM(valor_orcado) as orcamento_total,
                    SUM(valor_gasto) as valor_gasto_total
                FROM obras
            """)
            result = cursor.fetchone()
            return {
                'total': result['count'] if result else 0,
                'ativas': result[1] or 0,
                'em_andamento': result[2] or 0,
                'concluidas': result[3] or 0,
                'orcamento_total': result[4] or 0,
                'valor_gasto_total': result[5] or 0
            }
        except:
            return {
                'total': 0, 'ativas': 0, 'em_andamento': 0, 'concluidas': 0,
                'orcamento_total': 0, 'valor_gasto_total': 0
            }


def show_obras_page():
    """Interface principal das obras/departamentos"""
    st.title("🏗️ Obras e Departamentos")

    user_data = st.session_state.user_data
    if not auth_manager.check_permission(user_data['perfil'], "read"):
        st.error("❌ Você não tem permissão para acessar esta página.")
        return

    manager = ObrasManager()
    tab1, tab2, tab3 = st.tabs(["📋 Lista", "➕ Adicionar", "📊 Estatísticas"])

    # ---- TAB 1: LISTA ----
    with tab1:
        st.subheader("Lista de Obras e Departamentos")

        with st.expander("🔍 Filtros", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                filtro_nome = st.text_input("Nome")
                filtro_status = st.selectbox("Status", ["Todos"] + manager.get_status_options())
            with col2:
                filtro_responsavel = st.text_input("Responsável")

        filters = {}
        if filtro_nome:
            filters['nome'] = filtro_nome
        if filtro_status != "Todos":
            filters['status'] = filtro_status
        if filtro_responsavel:
            filters['responsavel'] = filtro_responsavel

        df = manager.get_obras(filters)  # type: ignore
        if not df.empty:
            # Cabeçalho da tabela
            col_header = st.columns([1, 2, 1, 1.5, 1, 1, 1.2, 1.2, 0.8, 0.8])
            headers = ["Código", "Nome", "Status", "Responsável", "Cidade", "Data Início", "Valor Orçado", "Valor Gasto", "Editar", "Excluir"]
            for i, h in enumerate(headers):
                with col_header[i]:
                    st.write(f"**{h}**")
            st.write("---")
            
            # Listagem com botões de ação
            for _, row in df.iterrows():
                cols = st.columns([1, 2, 1, 1.5, 1, 1, 1.2, 1.2, 0.8, 0.8])
                with cols[0]:
                    st.write(row['codigo'])
                with cols[1]:
                    st.write(row['nome'])
                with cols[2]:
                    st.write(row['status'])
                with cols[3]:
                    st.write(row['responsavel'] if row['responsavel'] else "N/A")
                with cols[4]:
                    st.write(row['cidade'] if row['cidade'] else "N/A")
                with cols[5]:
                    st.write(row['data_inicio'] if row['data_inicio'] else "N/A")
                with cols[6]:
                    st.write(f"R$ {row['valor_orcado']:,.2f}" if row['valor_orcado'] else "R$ 0,00")
                with cols[7]:
                    st.write(f"R$ {row['valor_gasto']:,.2f}" if row['valor_gasto'] else "R$ 0,00")
                with cols[8]:
                    if st.button("✏️", key=f"edit_obra_{row['id']}", help="Editar obra"):
                        st.session_state[f'edit_mode_obra_{row["id"]}'] = True
                        st.rerun()
                with cols[9]:
                    if st.button("❌", key=f"del_obra_{row['id']}", help="Excluir obra"):
                        if manager.delete_obra(int(row['id']), row['nome']):
                            st.success(f"Obra {row['nome']} excluída com sucesso!")
                            st.rerun()
                
                # Modal de edição
                if st.session_state.get(f'edit_mode_obra_{row["id"]}', False):
                    with st.expander(f"🔧 Editando: {row['codigo']} - {row['nome']}", expanded=True):
                        with st.form(f"edit_form_obra_{row['id']}"):
                            st.markdown("### Informações Básicas")
                            col_ed1, col_ed2 = st.columns(2)
                            with col_ed1:
                                novo_codigo = st.text_input("Código *", value=row['codigo'], key=f"codigo_edit_{row['id']}")
                                novo_nome = st.text_input("Nome *", value=row['nome'], key=f"nome_edit_{row['id']}")
                                novo_status = st.selectbox("Status *", manager.get_status_options(), 
                                                         index=manager.get_status_options().index(row['status']) if row['status'] in manager.get_status_options() else 0,
                                                         key=f"status_edit_{row['id']}")
                                novo_responsavel = st.text_input("Responsável", value=row['responsavel'] or "", key=f"resp_edit_{row['id']}")
                            with col_ed2:
                                novo_endereco = st.text_input("Endereço", value=row['endereco'] or "", key=f"end_edit_{row['id']}")
                                nova_cidade = st.text_input("Cidade", value=row['cidade'] or "", key=f"cid_edit_{row['id']}")
                                novo_estado = st.text_input("Estado", value=row['estado'] or "", key=f"est_edit_{row['id']}")
                                novo_cep = st.text_input("CEP", value=row['cep'] or "", key=f"cep_edit_{row['id']}")
                            
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.form_submit_button("💾 Salvar", type="primary"):
                                    dados_update: dict[str, Any] = {
                                        'codigo': novo_codigo,
                                        'nome': novo_nome,
                                        'status': novo_status,
                                        'responsavel': novo_responsavel,
                                        'endereco': novo_endereco,
                                        'cidade': nova_cidade,
                                        'estado': novo_estado,
                                        'cep': novo_cep
                                    }
                                    if manager.update_obra(int(row['id']), dados_update):
                                        st.success(f"Obra {novo_codigo} atualizada com sucesso!")
                                        del st.session_state[f'edit_mode_obra_{row["id"]}']
                                        st.rerun()
                                    else:
                                        st.error("Erro ao atualizar obra.")
                            with col_btn2:
                                if st.form_submit_button("❌ Cancelar"):
                                    del st.session_state[f'edit_mode_obra_{row["id"]}']
                                    st.rerun()
                        st.divider()
        else:
            st.info("📭 Nenhuma obra/departamento encontrada com os filtros aplicados.")

    # ---- TAB 2: ADICIONAR ----
    with tab2:
        if not auth_manager.check_permission(user_data['perfil'], "create"):
            st.error("❌ Você não tem permissão para adicionar obras.")
            return

        st.subheader("Adicionar Nova Obra/Departamento")
        with st.form("form_obra"):
            st.markdown("### Informações Básicas")
            col1, col2 = st.columns(2)
            with col1:
                codigo = st.text_input("Código *", placeholder="Ex: OBR-001")
                nome = st.text_input("Nome *", placeholder="Ex: Obra Residencial - Bairro X")
                status = st.selectbox("Status *", manager.get_status_options())
                responsavel = st.text_input("Responsável", placeholder="Ex: João Silva")
            with col2:
                endereco = st.text_input("Endereço", placeholder="Rua, número")
                cidade = st.text_input("Cidade", placeholder="Nome da cidade")
                estado = st.text_input("Estado", placeholder="Ex: SP")
                cep = st.text_input("CEP", placeholder="00000-000")

            st.markdown("### Contato")
            col1, col2 = st.columns(2)
            with col1:
                telefone = st.text_input("Telefone", placeholder="(11) 99999-9999")
            with col2:
                email = st.text_input("Email", placeholder="contato@obra.com")

            st.markdown("### Datas e Orçamento")
            col1, col2, col3 = st.columns(3)
            with col1:
                data_inicio = st.date_input("Data de Início", value=None)
            with col2:
                data_previsao = st.date_input("Data Prevista", value=None)
            with col3:
                valor_orcado = st.number_input("Valor Orçado (R$)", min_value=0.0, step=0.01)

            observacoes = st.text_area("Observações", placeholder="Informações adicionais")

            submitted = st.form_submit_button("💾 Cadastrar Obra/Departamento", type="primary")

            if submitted:
                if not nome or not codigo:
                    st.error("❌ Campos obrigatórios não preenchidos.")
                else:
                    data = {  # type: ignore
                        "codigo": codigo,
                        "nome": nome,
                        "status": status,
                        "responsavel": responsavel,
                        "endereco": endereco,
                        "cidade": cidade,
                        "estado": estado,
                        "cep": cep,
                        "telefone": telefone,
                        "email": email,
                        "data_inicio": data_inicio,
                        "data_previsao": data_previsao,
                        "valor_orcado": valor_orcado,
                        "observacoes": observacoes,
                        "criado_por": user_data['id'],
                    }
                    new_id = manager.create_obra(data)  # type: ignore
                    if new_id:
                        st.success(f"✅ Obra cadastrada com sucesso! (ID: {new_id})")
                        st.rerun()

    # ---- TAB 3: ESTATÍSTICAS ----
    with tab3:
        st.subheader("Estatísticas das Obras e Departamentos")

        stats = manager.get_dashboard_stats()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", stats['total'])
        col2.metric("Ativas", stats['ativas'])
        col3.metric("Em Andamento", stats['em_andamento'])
        col4.metric("Concluídas", stats['concluidas'])

        st.markdown("### Totais Financeiros")
        st.write(f"**Orçamento Total:** R$ {stats['orcamento_total']:,}")
        st.write(f"**Valor Gasto Total:** R$ {stats['valor_gasto_total']:,}")
