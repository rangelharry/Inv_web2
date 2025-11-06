import streamlit as st
from typing import Any

def show_movimentacao_modal_insumo(item_id: int) -> None:
    from modules.movimentacoes import MovimentacoesManager  # type: ignore
    from modules.insumos import InsumosManager
    insumos_manager = InsumosManager()
    insumos = insumos_manager.get_insumos()
    item: dict[str, Any] | None = next((i for i in insumos if i['id'] == item_id), None)
    user_data = st.session_state.user_data if 'user_data' in st.session_state else None
    if not item:
        st.error("❌ Item não encontrado.")
        return
    if not user_data or 'id' not in user_data or not isinstance(user_data['id'], int):
        st.error("❌ Usuário não autenticado. Faça login para registrar movimentações.")
        return
    manager = MovimentacoesManager()  # type: ignore
    st.markdown(f"## Movimentar: {item['descricao']} ({item['codigo']})")
    st.info(f"📦 Estoque atual: {item['quantidade_atual']} {item['unidade']}")
    with st.form("modal_movimentacao_insumo"):
        # Primeira linha - Tipo e Quantidade
        col1, col2 = st.columns(2)
        with col1:
            tipo = st.selectbox("Tipo de Movimentação *", ["Entrada", "Saída"])
        with col2:
            quantidade = st.number_input("Quantidade *", min_value=1, value=1, max_value=item['quantidade_atual'] if tipo == "Saída" else None)
        
        # Segunda linha - Origem/Destino e Responsável  
        col3, col4 = st.columns(2)
        with col3:
            local_atual = item.get('localizacao', 'Almoxarifado')
            if tipo == "Entrada":
                st.text_input("Local de Destino (atual) *", value=local_atual, disabled=True, help="Local onde o material será armazenado")
                local_movimentacao = st.text_input("Local de Origem *", placeholder="De onde vem o material")
            else:
                st.text_input("Local de Origem (atual) *", value=local_atual, disabled=True, help="Local atual do material")
                local_movimentacao = st.text_input("Local de Destino *", placeholder="Para onde vai o material")
        with col4:
            responsavel = st.text_input("Responsável *", placeholder="Nome do responsável pela movimentação")
        
        # Terceira linha - Motivo e Valor
        col5, col6 = st.columns(2)
        with col5:
            motivo = st.selectbox("Motivo (opcional)", ["", "Compra", "Doação", "Transferência", "Devolução", "Consumo", "Venda", "Perda", "Manutenção", "Empréstimo"])
        with col6:
            valor_unitario = None
            if tipo == "Entrada":
                valor_unitario = st.number_input("Valor Unitário (R$)", min_value=0.0, step=0.01)
        
        observacoes = st.text_area("Observações", placeholder="Informações adicionais sobre a movimentação")
        submitted = st.form_submit_button("💾 Registrar Movimentação", type="primary")
        if submitted:
            # Validação dos campos obrigatórios
            if not local_movimentacao or not local_movimentacao.strip():
                st.error("❌ Campo de local é obrigatório!")
                return
            if not responsavel or not responsavel.strip():
                st.error("❌ Campo 'Responsável' é obrigatório!")
                return
            if quantidade <= 0:
                st.error("❌ Quantidade deve ser maior que zero!")
                return
            if tipo == "Saída" and quantidade > item['quantidade_atual']:
                st.error(f"❌ Quantidade insuficiente! Estoque atual: {item['quantidade_atual']}")
                return
                
            # Preparar informações da movimentação
            local_atual = item.get('localizacao', 'Almoxarifado')
            if tipo == "Entrada":
                info_local = f"Origem: {local_movimentacao} → Destino: {local_atual}"
            else:
                info_local = f"Origem: {local_atual} → Destino: {local_movimentacao}"
                
            data: dict[str, Any] = {
                'item_id': item['id'],
                'tipo': tipo,
                'tipo_item': 'insumo',
                'quantidade': quantidade,
                'motivo': motivo if motivo else None,
                'obra_origem_id': None,
                'obra_destino_id': None,
                'responsavel_origem_id': None,
                'responsavel_destino_id': None,
                'valor_unitario': valor_unitario if valor_unitario else None,
                'observacoes': f"{info_local} | Responsável: {responsavel}" + (f" | {observacoes}" if observacoes else "")
            }
            usuario_id: int = user_data['id']
            movimentacao_id = manager.create_movimentacao(data, usuario_id)
            if movimentacao_id:
                st.success(f"✅ Movimentação registrada com sucesso! (ID: {movimentacao_id})")
                st.rerun()
            else:
                st.error("❌ Erro ao registrar movimentação.")

def show_movimentacao_modal_equipamento_eletrico(item_id: int) -> None:
    from modules.movimentacoes import MovimentacoesManager  # type: ignore
    from modules.equipamentos_eletricos import EquipamentosEletricosManager
    import pandas as pd
    eq_manager = EquipamentosEletricosManager()
    equipamentos: pd.DataFrame = eq_manager.get_equipamentos()
    item: dict[str, Any] | None = dict(equipamentos[equipamentos['id'] == item_id].iloc[0].to_dict()) if not equipamentos.empty else None  # type: ignore
    user_data = st.session_state.user_data if 'user_data' in st.session_state else None
    if item is None:
        st.error("❌ Equipamento não encontrado.")
        return
    if not user_data or 'id' not in user_data or not isinstance(user_data['id'], int):
        st.error("❌ Usuário não autenticado. Faça login para registrar movimentações.")
        return
    manager = MovimentacoesManager()
    st.markdown(f"## Movimentar: {item['nome']} ({item['codigo']})")
    st.info(f"📍 Localização atual: {item['localizacao']} | Status: {item['status']}")
    with st.form("modal_movimentacao_eletrico"):
        # Primeira linha - Tipo de Movimentação
        tipo = st.selectbox("Tipo de Movimentação *", ["Entrada", "Saída"])
        
        # Segunda linha - Origem/Destino e Responsável  
        col1, col2 = st.columns(2)
        with col1:
            local_atual = item.get('localizacao', 'Almoxarifado')
            if tipo == "Entrada":
                st.text_input("Local de Destino (atual) *", value=local_atual, disabled=True, help="Local onde o equipamento será armazenado")
                local_movimentacao = st.text_input("Local de Origem *", placeholder="De onde vem o equipamento")
            else:
                st.text_input("Local de Origem (atual) *", value=local_atual, disabled=True, help="Local atual do equipamento")
                local_movimentacao = st.text_input("Local de Destino *", placeholder="Para onde vai o equipamento")
        with col2:
            responsavel = st.text_input("Responsável *", placeholder="Nome do responsável pela movimentação")
        
        # Terceira linha - Motivo
        motivo = st.selectbox("Motivo (opcional)", ["", "Transferência", "Devolução", "Manutenção", "Empréstimo", "Perda"])
        observacoes = st.text_area("Observações", placeholder="Informações adicionais sobre a movimentação")
        submitted = st.form_submit_button("💾 Registrar Movimentação", type="primary")
        if submitted:
            # Validação dos campos obrigatórios
            if not local_movimentacao or not local_movimentacao.strip():
                st.error("❌ Campo de local é obrigatório!")
                return
            if not responsavel or not responsavel.strip():
                st.error("❌ Campo 'Responsável' é obrigatório!")
                return
                
            # Preparar informações da movimentação
            local_atual = item.get('localizacao', 'Almoxarifado')
            if tipo == "Entrada":
                info_local = f"Origem: {local_movimentacao} → Destino: {local_atual}"
            else:
                info_local = f"Origem: {local_atual} → Destino: {local_movimentacao}"
                
            data: dict[str, Any] = {
                'item_id': item['id'],
                'tipo': tipo,
                'tipo_item': 'equipamento_eletrico',
                'quantidade': 1,
                'motivo': motivo if motivo else None,
                'obra_origem_id': None,
                'obra_destino_id': None,
                'responsavel_origem_id': None,
                'responsavel_destino_id': None,
                'valor_unitario': None,
                'observacoes': f"{info_local} | Responsável: {responsavel}" + (f" | {observacoes}" if observacoes else "")
            }
            usuario_id: int = user_data['id']
            movimentacao_id = manager.create_movimentacao(data, usuario_id)
            if movimentacao_id:
                st.success(f"✅ Movimentação registrada com sucesso! (ID: {movimentacao_id})")
                st.rerun()
            else:
                st.error("❌ Erro ao registrar movimentação.")

def show_movimentacao_modal_equipamento_manual(item_id: int) -> None:
    from modules.movimentacoes import MovimentacoesManager  # type: ignore
    from modules.equipamentos_manuais import EquipamentosManuaisManager
    import pandas as pd
    eq_manager = EquipamentosManuaisManager()
    equipamentos: pd.DataFrame = eq_manager.get_equipamentos()
    item: dict[str, Any] | None = dict(equipamentos[equipamentos['id'] == item_id].iloc[0].to_dict()) if not equipamentos.empty else None  # type: ignore
    user_data = st.session_state.user_data if 'user_data' in st.session_state else None
    if item is None:
        st.error("❌ Equipamento não encontrado.")
        return
    if not user_data or 'id' not in user_data or not isinstance(user_data['id'], int):
        st.error("❌ Usuário não autenticado. Faça login para registrar movimentações.")
        return
    manager = MovimentacoesManager()
    st.markdown(f"## Movimentar: {item['nome']} ({item['codigo']})")
    st.info(f"📍 Localização atual: {item['localizacao']} | Status: {item['status']}")
    with st.form("modal_movimentacao_manual"):
        # Primeira linha - Tipo e Quantidade
        col1, col2 = st.columns(2)
        with col1:
            tipo = st.selectbox("Tipo de Movimentação *", ["Entrada", "Saída"])
        with col2:
            quantidade_atual = item.get('quantitativo', 1)
            quantidade = st.number_input("Quantidade *", min_value=1, value=1, max_value=quantidade_atual if tipo == "Saída" else None)
        
        # Segunda linha - Origem/Destino e Responsável  
        col3, col4 = st.columns(2)
        with col3:
            local_atual = item.get('localizacao', 'Almoxarifado')
            if tipo == "Entrada":
                st.text_input("Local de Destino (atual) *", value=local_atual, disabled=True, help="Local onde o equipamento será armazenado")
                local_movimentacao = st.text_input("Local de Origem *", placeholder="De onde vem o equipamento")
            else:
                st.text_input("Local de Origem (atual) *", value=local_atual, disabled=True, help="Local atual do equipamento")
                local_movimentacao = st.text_input("Local de Destino *", placeholder="Para onde vai o equipamento")
        with col4:
            responsavel = st.text_input("Responsável *", placeholder="Nome do responsável pela movimentação")
        
        # Terceira linha - Motivo
        motivo = st.selectbox("Motivo (opcional)", ["", "Transferência", "Devolução", "Manutenção", "Empréstimo", "Perda"])
        observacoes = st.text_area("Observações", placeholder="Informações adicionais sobre a movimentação")
        submitted = st.form_submit_button("💾 Registrar Movimentação", type="primary")
        if submitted:
            # Validação dos campos obrigatórios
            if not local_movimentacao or not local_movimentacao.strip():
                st.error("❌ Campo de local é obrigatório!")
                return
            if not responsavel or not responsavel.strip():
                st.error("❌ Campo 'Responsável' é obrigatório!")
                return
            if quantidade <= 0:
                st.error("❌ Quantidade deve ser maior que zero!")
                return
            quantidade_atual = item.get('quantitativo', 1)
            if tipo == "Saída" and quantidade > quantidade_atual:
                st.error(f"❌ Quantidade insuficiente! Quantidade atual: {quantidade_atual}")
                return
                
            # Preparar informações da movimentação
            local_atual = item.get('localizacao', 'Almoxarifado')
            if tipo == "Entrada":
                info_local = f"Origem: {local_movimentacao} → Destino: {local_atual}"
            else:
                info_local = f"Origem: {local_atual} → Destino: {local_movimentacao}"
                
            data: dict[str, Any] = {
                'item_id': item['id'],
                'tipo': tipo,
                'tipo_item': 'equipamento_manual',
                'quantidade': quantidade,
                'motivo': motivo if motivo else None,
                'obra_origem_id': None,
                'obra_destino_id': None,
                'responsavel_origem_id': None,
                'responsavel_destino_id': None,
                'valor_unitario': None,
                'observacoes': f"{info_local} | Responsável: {responsavel}" + (f" | {observacoes}" if observacoes else "")
            }
            usuario_id: int = user_data['id']
            movimentacao_id = manager.create_movimentacao(data, usuario_id)
            if movimentacao_id:
                st.success(f"✅ Movimentação registrada com sucesso! (ID: {movimentacao_id})")
                st.rerun()
            else:
                st.error("❌ Erro ao registrar movimentação.")
