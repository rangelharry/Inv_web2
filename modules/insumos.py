"""
Sistema de Inventário Web - Módulo de Gestão de Insumos
CRUD completo com controle de estoque, alertas e filtros avançados
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
from database.connection import db
from modules.auth import auth_manager

class InsumosManager:
    def __init__(self):
        self.conn = db.get_connection()
    
    def get_categorias(self, tipo='insumo'):
        """Busca categorias disponíveis"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT id, nome FROM categorias 
            WHERE tipo = ? AND ativo = 1 
            ORDER BY nome
            """, (tipo,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            st.error(f"Erro ao buscar categorias: {e}")
            return []
    
    def create_insumo(self, dados, user_id):
        """Cria novo insumo"""
        try:
            cursor = self.conn.cursor()
            
            # Verifica se código já existe
            cursor.execute("SELECT id FROM insumos WHERE codigo = ?", (dados['codigo'],))
            if cursor.fetchone():
                return False, "Código já existe"
            
            cursor.execute("""
            INSERT INTO insumos (
                codigo, descricao, categoria_id, unidade, quantidade_atual,
                quantidade_minima, preco_unitario, fornecedor, marca, 
                localizacao, observacoes, data_validade, criado_por
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dados['codigo'], dados['descricao'], dados['categoria_id'],
                dados['unidade'], dados['quantidade_atual'], dados['quantidade_minima'],
                dados['preco_unitario'], dados['fornecedor'], dados['marca'],
                dados['localizacao'], dados['observacoes'], dados['data_validade'], user_id
            ))
            
            insumo_id = cursor.lastrowid
            self.conn.commit()
            
            # Log da ação
            auth_manager.log_action(
                user_id, 'criar', 'insumos', insumo_id,
                f"Insumo criado: {dados['codigo']} - {dados['descricao']}"
            )
            
            return True, "Insumo criado com sucesso"
            
        except Exception as e:
            return False, f"Erro ao criar insumo: {str(e)}"
    
    def update_insumo(self, insumo_id, dados, user_id):
        """Atualiza insumo existente"""
        try:
            cursor = self.conn.cursor()
            
            # Busca dados atuais
            cursor.execute("SELECT * FROM insumos WHERE id = ?", (insumo_id,))
            old_data = dict(cursor.fetchone())
            
            # Verifica se código já existe em outro insumo
            cursor.execute("SELECT id FROM insumos WHERE codigo = ? AND id != ?", (dados['codigo'], insumo_id))
            if cursor.fetchone():
                return False, "Código já existe em outro insumo"
            
            cursor.execute("""
            UPDATE insumos SET 
                codigo = ?, descricao = ?, categoria_id = ?, unidade = ?,
                quantidade_atual = ?, quantidade_minima = ?, preco_unitario = ?,
                fornecedor = ?, marca = ?, localizacao = ?, observacoes = ?,
                data_validade = ?
            WHERE id = ?
            """, (
                dados['codigo'], dados['descricao'], dados['categoria_id'],
                dados['unidade'], dados['quantidade_atual'], dados['quantidade_minima'],
                dados['preco_unitario'], dados['fornecedor'], dados['marca'],
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
    
    def delete_insumo(self, insumo_id, user_id):
        """Remove insumo (soft delete)"""
        try:
            cursor = self.conn.cursor()
            
            # Busca dados do insumo
            cursor.execute("SELECT * FROM insumos WHERE id = ?", (insumo_id,))
            insumo_data = cursor.fetchone()
            
            if not insumo_data:
                return False, "Insumo não encontrado"
            
            cursor.execute("UPDATE insumos SET ativo = 0 WHERE id = ?", (insumo_id,))
            self.conn.commit()
            
            # Log da ação
            auth_manager.log_action(
                user_id, 'excluir', 'insumos', insumo_id,
                f"Insumo removido: {insumo_data['codigo']} - {insumo_data['descricao']}"
            )
            
            return True, f"Insumo {insumo_data['codigo']} removido com sucesso"
            
        except Exception as e:
            return False, f"Erro ao remover insumo: {str(e)}"
    
    def get_insumos(self, filtros=None):
        """Busca insumos com filtros"""
        try:
            cursor = self.conn.cursor()
            
            query = """
            SELECT i.*, c.nome as categoria_nome
            FROM insumos i
            LEFT JOIN categorias c ON i.categoria_id = c.id
            WHERE i.ativo = 1
            """
            params = []
            
            if filtros:
                if filtros.get('categoria_id'):
                    query += " AND i.categoria_id = ?"
                    params.append(filtros['categoria_id'])
                
                if filtros.get('estoque_baixo'):
                    query += " AND i.quantidade_atual <= i.quantidade_minima"
                
                if filtros.get('busca'):
                    query += " AND (i.codigo LIKE ? OR i.descricao LIKE ? OR i.marca LIKE ?)"
                    busca = f"%{filtros['busca']}%"
                    params.extend([busca, busca, busca])
            
            query += " ORDER BY i.codigo"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            st.error(f"Erro ao buscar insumos: {e}")
            return []
    
    def get_insumo_by_id(self, insumo_id):
        """Busca insumo por ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT i.*, c.nome as categoria_nome
            FROM insumos i
            LEFT JOIN categorias c ON i.categoria_id = c.id
            WHERE i.id = ?
            """, (insumo_id,))
            
            result = cursor.fetchone()
            return dict(result) if result else None
            
        except Exception as e:
            st.error(f"Erro ao buscar insumo: {e}")
            return None
    
    def ajustar_estoque(self, insumo_id, quantidade, tipo_movimento, motivo, user_id):
        """Ajusta estoque de insumo"""
        try:
            cursor = self.conn.cursor()
            
            # Busca insumo atual
            cursor.execute("SELECT * FROM insumos WHERE id = ?", (insumo_id,))
            insumo = cursor.fetchone()
            
            if not insumo:
                return False, "Insumo não encontrado"
            
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
                quantidade_atual = ?,
                data_ultima_entrada = CASE WHEN ? = 'entrada' THEN CURRENT_TIMESTAMP ELSE data_ultima_entrada END,
                data_ultima_saida = CASE WHEN ? = 'saida' THEN CURRENT_TIMESTAMP ELSE data_ultima_saida END
            WHERE id = ?
            """, (nova_quantidade, tipo_movimento, tipo_movimento, insumo_id))
            
            # Registra movimentação
            cursor.execute("""
            INSERT INTO movimentacoes (
                tipo, tipo_item, item_id, codigo_item, descricao_item,
                quantidade, unidade, motivo, observacoes, usuario_id
            ) VALUES (?, 'insumo', ?, ?, ?, ?, ?, ?, ?, ?)
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
    can_edit = auth_manager.check_permission(user_data['perfil'], 'update')
    can_create = auth_manager.check_permission(user_data['perfil'], 'create')
    can_delete = auth_manager.check_permission(user_data['perfil'], 'delete')
    
    manager = InsumosManager()
    
    # Tabs principais
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Lista", "➕ Novo Insumo", "📊 Relatórios", "⚙️ Ajustes"])
    
    with tab1:
        st.subheader("📋 Lista de Insumos")
        
        # Filtros
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            categorias = manager.get_categorias()
            categoria_options = [{'id': 0, 'nome': 'Todas as categorias'}] + categorias
            categoria_selected = st.selectbox(
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
        filtros = {}
        if categoria_selected['id'] > 0:
            filtros['categoria_id'] = categoria_selected['id']
        if estoque_baixo:
            filtros['estoque_baixo'] = True
        if busca:
            filtros['busca'] = busca
        
        # Buscar insumos
        insumos = manager.get_insumos(filtros)
        
        if insumos:
            # Estatísticas rápidas
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            total_itens = len(insumos)
            estoque_baixo_count = sum(1 for i in insumos if i['quantidade_atual'] <= i['quantidade_minima'])
            valor_total = sum(i['quantidade_atual'] * (i['preco_unitario'] or 0) for i in insumos)
            sem_estoque = sum(1 for i in insumos if i['quantidade_atual'] == 0)
            
            col_stat1.metric("Total de Itens", total_itens)
            col_stat2.metric("Estoque Baixo", estoque_baixo_count, delta_color="inverse")
            col_stat3.metric("Valor Total", f"R$ {valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            col_stat4.metric("Sem Estoque", sem_estoque, delta_color="inverse")
            
            # Tabela de insumos
            df = pd.DataFrame(insumos)
            
            # Formatação das colunas
            df_display = df.copy()
            df_display['Código'] = df['codigo']
            df_display['Descrição'] = df['descricao']
            df_display['Categoria'] = df['categoria_nome']
            df_display['Atual'] = df['quantidade_atual'].astype(str) + ' ' + df['unidade']
            df_display['Mínimo'] = df['quantidade_minima'].astype(str) + ' ' + df['unidade']
            df_display['Preço Unit.'] = df['preco_unitario'].apply(
                lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if x else '-'
            )
            df_display['Valor Total'] = (df['quantidade_atual'] * df['preco_unitario'].fillna(0)).apply(
                lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if x > 0 else '-'
            )
            
            # Status de estoque
            def get_status_estoque(row):
                if row['quantidade_atual'] == 0:
                    return "🔴 Sem estoque"
                elif row['quantidade_atual'] <= row['quantidade_minima']:
                    return "🟡 Estoque baixo"
                else:
                    return "🟢 Normal"
            
            df_display['Status'] = df.apply(get_status_estoque, axis=1)
            
            # Exibir tabela
            st.dataframe(
                df_display[['Código', 'Descrição', 'Categoria', 'Atual', 'Mínimo', 'Preço Unit.', 'Valor Total', 'Status']],
                use_container_width=True,
                hide_index=True
            )
            
            # Ações em lote (para admins)
            if can_edit or can_delete:
                st.markdown("---")
                st.subheader("⚡ Ações Rápidas")
                
                col_act1, col_act2, col_act3 = st.columns(3)
                
                with col_act1:
                    if st.button("📊 Exportar Lista", use_container_width=True):
                        # Preparar dados para exportação
                        df_export = df[['codigo', 'descricao', 'categoria_nome', 'unidade', 
                                      'quantidade_atual', 'quantidade_minima', 'preco_unitario', 
                                      'fornecedor', 'marca', 'localizacao']]
                        
                        df_export.columns = ['Código', 'Descrição', 'Categoria', 'Unidade',
                                           'Qtd Atual', 'Qtd Mínima', 'Preço Unit.', 
                                           'Fornecedor', 'Marca', 'Localização']
                        
                        csv = df_export.to_csv(index=False, encoding='utf-8-sig')
                        st.download_button(
                            label="💾 Download CSV",
                            data=csv,
                            file_name=f"insumos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                
                with col_act2:
                    if estoque_baixo_count > 0:
                        if st.button(f"⚠️ Ver Estoque Baixo ({estoque_baixo_count})", use_container_width=True):
                            st.session_state.filtro_estoque_baixo = True
                            st.rerun()
                
                with col_act3:
                    if can_create and st.button("➕ Novo Insumo", use_container_width=True):
                        st.session_state.aba_ativa = 1  # Ir para aba de novo insumo
                        st.rerun()
            
        else:
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
                col1, col2 = st.columns(2)
                
                with col1:
                    codigo = st.text_input("* Código", placeholder="INS-0001")
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
                    quantidade_atual = st.number_input("Quantidade Atual", min_value=0.0, value=0.0, step=0.01)
                    quantidade_minima = st.number_input("Quantidade Mínima", min_value=0.0, value=5.0, step=0.01)
                    preco_unitario = st.number_input("Preço Unitário (R$)", min_value=0.0, value=0.0, step=0.01)
                    
                    fornecedor = st.text_input("Fornecedor", placeholder="Nome do fornecedor")
                    marca = st.text_input("Marca", placeholder="Marca do produto")
                    localizacao = st.text_input("Localização", value="Almoxarifado")
                
                data_validade = st.date_input("Data de Validade", value=None)
                observacoes = st.text_area("Observações", placeholder="Informações adicionais...")
                
                st.markdown("**Campos obrigatórios estão marcados com ***")
                
                if st.form_submit_button("💾 Salvar Insumo", use_container_width=True):
                    if codigo and descricao and categoria and unidade:
                        dados = {
                            'codigo': codigo.upper(),
                            'descricao': descricao,
                            'categoria_id': categoria['id'],
                            'unidade': unidade,
                            'quantidade_atual': quantidade_atual,
                            'quantidade_minima': quantidade_minima,
                            'preco_unitario': preco_unitario if preco_unitario > 0 else None,
                            'fornecedor': fornecedor or None,
                            'marca': marca or None,
                            'localizacao': localizacao,
                            'observacoes': observacoes or None,
                            'data_validade': data_validade
                        }
                        
                        success, message = manager.create_insumo(dados, user_data['id'])
                        
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
            st.info("🚧 Módulo de ajustes será implementado na próxima versão!")

# Instância global do manager
insumos_manager = InsumosManager()