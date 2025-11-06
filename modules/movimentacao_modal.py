import streamlit as st
from typing import Any

def show_movimentacao_entrada_insumo(item_id: int) -> None:
    """Modal específico para ENTRADA de insumos"""
    from modules.movimentacoes import MovimentacoesManager
    from modules.insumos import InsumosManager
    from modules.responsaveis import ResponsaveisManager
    
    insumos_manager = InsumosManager()
    responsaveis_manager = ResponsaveisManager()
    insumos = insumos_manager.get_insumos()
    item: dict[str, Any] | None = next((i for i in insumos if i['id'] == item_id), None)
    user_data = st.session_state.user_data if 'user_data' in st.session_state else None
    
    if not item:
        st.error("❌ Item não encontrado.")
        return
    
    if not user_data or 'id' not in user_data or not isinstance(user_data['id'], int):
        st.error("❌ Usuário não autenticado. Faça login para registrar movimentações.")
        return
    
    manager = MovimentacoesManager()
    st.markdown(f"## ENTRADA: {item['descricao']} ({item['codigo']})")
    st.info(f"📦 Estoque atual: {item['quantidade_atual']} {item['unidade']}")
    
    with st.form("entrada_insumo"):
        col1, col2 = st.columns(2)
        with col1:
            quantidade = st.number_input("Quantidade *", min_value=1, value=1)
        with col2:
            valor_unitario = st.number_input("Valor Unitário (R$)", min_value=0.0, step=0.01)
        
        col3, col4 = st.columns(2)
        with col3:
            local_origem = st.text_input("Local de Origem *", placeholder="De onde vem o material")
            local_destino = item.get('localizacao', 'Almoxarifado')
            st.text_input("Local de Destino (atual) *", value=local_destino, disabled=True)
        
        with col4:
            responsaveis_df = responsaveis_manager.get_responsaveis({"ativo": 1})
            responsaveis_options = [""] + [f"{row['nome']} - {row['cargo']}" for _, row in responsaveis_df.iterrows()]
            responsavel_selecionado = st.selectbox("Responsável *", options=responsaveis_options)
        
        motivo = st.selectbox("Motivo (opcional)", ["", "Compra", "Doação", "Transferência", "Devolução"])
        observacoes = st.text_area("Observações", placeholder="Informações adicionais sobre a movimentação")
        
        if st.form_submit_button("💾 Registrar ENTRADA", type="primary"):
            if not local_origem.strip():
                st.error("❌ Local de Origem é obrigatório!")
                return
            if not responsavel_selecionado.strip():
                st.error("❌ Responsável é obrigatório!")
                return
            
            data: dict[str, Any] = {
                'item_id': item['id'],
                'tipo': 'Entrada',
                'tipo_item': 'insumo',
                'quantidade': quantidade,
                'motivo': motivo if motivo else None,
                'obra_origem_id': None,
                'obra_destino_id': None,
                'responsavel_origem_id': None,
                'responsavel_destino_id': None,
                'valor_unitario': valor_unitario,
                'observacoes': f"Origem: {local_origem} → Destino: {local_destino} | Responsável: {responsavel_selecionado}" + (f" | {observacoes}" if observacoes else "")
            }
            
            usuario_id: int = user_data['id']
            movimentacao_id = manager.create_movimentacao(data, usuario_id)
            if movimentacao_id:
                st.success(f"✅ ENTRADA registrada com sucesso! (ID: {movimentacao_id})")
                st.rerun()
            else:
                st.error("❌ Erro ao registrar entrada.")


def show_movimentacao_saida_insumo(item_id: int) -> None:
    """Modal específico para SAÍDA de insumos"""
    from modules.movimentacoes import MovimentacoesManager
    from modules.insumos import InsumosManager
    from modules.responsaveis import ResponsaveisManager
    from modules.obras import ObrasManager
    
    insumos_manager = InsumosManager()
    responsaveis_manager = ResponsaveisManager()
    obras_manager = ObrasManager()
    insumos = insumos_manager.get_insumos()
    item: dict[str, Any] | None = next((i for i in insumos if i['id'] == item_id), None)
    user_data = st.session_state.user_data if 'user_data' in st.session_state else None
    
    if not item:
        st.error("❌ Item não encontrado.")
        return
    
    if not user_data or 'id' not in user_data or not isinstance(user_data['id'], int):
        st.error("❌ Usuário não autenticado. Faça login para registrar movimentações.")
        return
    
    manager = MovimentacoesManager()
    st.markdown(f"## SAÍDA: {item['descricao']} ({item['codigo']})")
    st.info(f"📦 Estoque atual: {item['quantidade_atual']} {item['unidade']}")
    
    with st.form("saida_insumo"):
        quantidade = st.number_input("Quantidade *", min_value=1, value=1, max_value=item['quantidade_atual'])
        
        col1, col2 = st.columns(2)
        with col1:
            local_origem = item.get('localizacao', 'Almoxarifado')
            st.text_input("Local de Origem (atual) *", value=local_origem, disabled=True)
            
            obras_df = obras_manager.get_obras({"status": "ativo"})
            obras_options = [""] + [f"{row['nome']} - {row['codigo']}" for _, row in obras_df.iterrows()]
            local_destino = st.selectbox("Local de Destino *", options=obras_options,
                                       help="Selecione a obra/departamento de destino")
        
        with col2:
            responsaveis_df = responsaveis_manager.get_responsaveis({"ativo": 1})
            responsaveis_options = [""] + [f"{row['nome']} - {row['cargo']}" for _, row in responsaveis_df.iterrows()]
            responsavel_selecionado = st.selectbox("Responsável *", options=responsaveis_options)
        
        motivo = st.selectbox("Motivo (opcional)", ["", "Consumo", "Transferência", "Venda", "Perda"])
        observacoes = st.text_area("Observações", placeholder="Informações adicionais sobre a movimentação")
        
        if st.form_submit_button("💾 Registrar SAÍDA", type="primary"):
            if not local_destino.strip():
                st.error("❌ Local de Destino é obrigatório!")
                return
            if not responsavel_selecionado.strip():
                st.error("❌ Responsável é obrigatório!")
                return
            if quantidade > item['quantidade_atual']:
                st.error(f"❌ Quantidade insuficiente! Estoque atual: {item['quantidade_atual']}")
                return
            
            data: dict[str, Any] = {
                'item_id': item['id'],
                'tipo': 'Saída',
                'tipo_item': 'insumo',
                'quantidade': quantidade,
                'motivo': motivo if motivo else None,
                'obra_origem_id': None,
                'obra_destino_id': None,
                'responsavel_origem_id': None,
                'responsavel_destino_id': None,
                'valor_unitario': None,
                'observacoes': f"Origem: {local_origem} → Destino: {local_destino} | Responsável: {responsavel_selecionado}" + (f" | {observacoes}" if observacoes else "")
            }
            
            usuario_id: int = user_data['id']
            movimentacao_id = manager.create_movimentacao(data, usuario_id)
            if movimentacao_id:
                st.success(f"✅ SAÍDA registrada com sucesso! (ID: {movimentacao_id})")
                st.rerun()
            else:
                st.error("❌ Erro ao registrar saída.")


def show_movimentacao_modal_insumo(item_id: int) -> None:
    """Modal principal que permite escolher entre entrada e saída"""
    st.markdown("## Selecione o tipo de movimentação:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 ENTRADA", use_container_width=True, type="primary"):
            st.session_state.modal_type = "entrada"
            
    with col2:
        if st.button("📤 SAÍDA", use_container_width=True, type="secondary"):
            st.session_state.modal_type = "saida"
    
    # Mostrar o modal apropriado baseado na seleção
    if hasattr(st.session_state, 'modal_type'):
        if st.session_state.modal_type == "entrada":
            show_movimentacao_entrada_insumo(item_id)
        elif st.session_state.modal_type == "saida":
            show_movimentacao_saida_insumo(item_id)


# Funções similares para equipamentos elétricos
def show_movimentacao_modal_equipamento_eletrico(item_id: int) -> None:
    """Modal principal para equipamentos elétricos"""
    st.markdown("## Selecione o tipo de movimentação:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 ENTRADA", use_container_width=True, type="primary"):
            st.session_state.modal_type_eletrico = "entrada"
            
    with col2:
        if st.button("📤 SAÍDA", use_container_width=True, type="secondary"):
            st.session_state.modal_type_eletrico = "saida"
    
    if hasattr(st.session_state, 'modal_type_eletrico'):
        if st.session_state.modal_type_eletrico == "entrada":
            show_movimentacao_entrada_equipamento_eletrico(item_id)
        elif st.session_state.modal_type_eletrico == "saida":
            show_movimentacao_saida_equipamento_eletrico(item_id)


def show_movimentacao_entrada_equipamento_eletrico(item_id: int) -> None:
    """Modal específico para ENTRADA de equipamentos elétricos"""
    from modules.movimentacoes import MovimentacoesManager
    from modules.equipamentos_eletricos import EquipamentosEletricosManager
    from modules.responsaveis import ResponsaveisManager
    import pandas as pd
    
    eq_manager = EquipamentosEletricosManager()
    responsaveis_manager = ResponsaveisManager()
    equipamentos: pd.DataFrame = eq_manager.get_equipamentos()
    item: dict[str, Any] | None = dict(equipamentos[equipamentos['id'] == item_id].iloc[0].to_dict()) if not equipamentos.empty else None
    user_data = st.session_state.user_data if 'user_data' in st.session_state else None
    
    if item is None:
        st.error("❌ Equipamento não encontrado.")
        return
    
    if not user_data or 'id' not in user_data or not isinstance(user_data['id'], int):
        st.error("❌ Usuário não autenticado. Faça login para registrar movimentações.")
        return
    
    manager = MovimentacoesManager()
    st.markdown(f"## ENTRADA: {item['nome']} ({item['codigo']})")
    st.info(f"📍 Localização atual: {item['localizacao']} | Status: {item['status']}")
    
    with st.form("entrada_eletrico"):
        col1, col2 = st.columns(2)
        with col1:
            local_origem = st.text_input("Local de Origem *", placeholder="De onde vem o equipamento")
            local_destino = item.get('localizacao', 'Almoxarifado')
            st.text_input("Local de Destino (atual) *", value=local_destino, disabled=True)
        
        with col2:
            responsaveis_df = responsaveis_manager.get_responsaveis({"ativo": 1})
            responsaveis_options = [""] + [f"{row['nome']} - {row['cargo']}" for _, row in responsaveis_df.iterrows()]
            responsavel_selecionado = st.selectbox("Responsável *", options=responsaveis_options)
        
        motivo = st.selectbox("Motivo (opcional)", ["", "Transferência", "Devolução", "Manutenção"])
        observacoes = st.text_area("Observações", placeholder="Informações adicionais sobre a movimentação")
        
        if st.form_submit_button("💾 Registrar ENTRADA", type="primary"):
            if not local_origem.strip():
                st.error("❌ Local de Origem é obrigatório!")
                return
            if not responsavel_selecionado.strip():
                st.error("❌ Responsável é obrigatório!")
                return
            
            data: dict[str, Any] = {
                'item_id': item['id'],
                'tipo': 'Entrada',
                'tipo_item': 'equipamento_eletrico',
                'quantidade': 1,
                'motivo': motivo if motivo else None,
                'obra_origem_id': None,
                'obra_destino_id': None,
                'responsavel_origem_id': None,
                'responsavel_destino_id': None,
                'valor_unitario': None,
                'observacoes': f"Origem: {local_origem} → Destino: {local_destino} | Responsável: {responsavel_selecionado}" + (f" | {observacoes}" if observacoes else "")
            }
            
            usuario_id: int = user_data['id']
            movimentacao_id = manager.create_movimentacao(data, usuario_id)
            if movimentacao_id:
                st.success(f"✅ ENTRADA registrada com sucesso! (ID: {movimentacao_id})")
                st.rerun()
            else:
                st.error("❌ Erro ao registrar entrada.")


def show_movimentacao_saida_equipamento_eletrico(item_id: int) -> None:
    """Modal específico para SAÍDA de equipamentos elétricos"""
    from modules.movimentacoes import MovimentacoesManager
    from modules.equipamentos_eletricos import EquipamentosEletricosManager
    from modules.responsaveis import ResponsaveisManager
    from modules.obras import ObrasManager
    import pandas as pd
    
    eq_manager = EquipamentosEletricosManager()
    responsaveis_manager = ResponsaveisManager()
    obras_manager = ObrasManager()
    equipamentos: pd.DataFrame = eq_manager.get_equipamentos()
    item: dict[str, Any] | None = dict(equipamentos[equipamentos['id'] == item_id].iloc[0].to_dict()) if not equipamentos.empty else None
    user_data = st.session_state.user_data if 'user_data' in st.session_state else None
    
    if item is None:
        st.error("❌ Equipamento não encontrado.")
        return
    
    if not user_data or 'id' not in user_data or not isinstance(user_data['id'], int):
        st.error("❌ Usuário não autenticado. Faça login para registrar movimentações.")
        return
    
    manager = MovimentacoesManager()
    st.markdown(f"## SAÍDA: {item['nome']} ({item['codigo']})")
    st.info(f"📍 Localização atual: {item['localizacao']} | Status: {item['status']}")
    
    with st.form("saida_eletrico"):
        col1, col2 = st.columns(2)
        with col1:
            local_origem = item.get('localizacao', 'Almoxarifado')
            st.text_input("Local de Origem (atual) *", value=local_origem, disabled=True)
            
            obras_df = obras_manager.get_obras({"status": "ativo"})
            obras_options = [""] + [f"{row['nome']} - {row['codigo']}" for _, row in obras_df.iterrows()]
            local_destino = st.selectbox("Local de Destino *", options=obras_options,
                                       help="Selecione a obra/departamento de destino")
        
        with col2:
            responsaveis_df = responsaveis_manager.get_responsaveis({"ativo": 1})
            responsaveis_options = [""] + [f"{row['nome']} - {row['cargo']}" for _, row in responsaveis_df.iterrows()]
            responsavel_selecionado = st.selectbox("Responsável *", options=responsaveis_options)
        
        motivo = st.selectbox("Motivo (opcional)", ["", "Transferência", "Empréstimo", "Manutenção", "Perda"])
        observacoes = st.text_area("Observações", placeholder="Informações adicionais sobre a movimentação")
        
        if st.form_submit_button("💾 Registrar SAÍDA", type="primary"):
            if not local_destino.strip():
                st.error("❌ Local de Destino é obrigatório!")
                return
            if not responsavel_selecionado.strip():
                st.error("❌ Responsável é obrigatório!")
                return
            
            data: dict[str, Any] = {
                'item_id': item['id'],
                'tipo': 'Saída',
                'tipo_item': 'equipamento_eletrico',
                'quantidade': 1,
                'motivo': motivo if motivo else None,
                'obra_origem_id': None,
                'obra_destino_id': None,
                'responsavel_origem_id': None,
                'responsavel_destino_id': None,
                'valor_unitario': None,
                'observacoes': f"Origem: {local_origem} → Destino: {local_destino} | Responsável: {responsavel_selecionado}" + (f" | {observacoes}" if observacoes else "")
            }
            
            usuario_id: int = user_data['id']
            movimentacao_id = manager.create_movimentacao(data, usuario_id)
            if movimentacao_id:
                st.success(f"✅ SAÍDA registrada com sucesso! (ID: {movimentacao_id})")
                st.rerun()
            else:
                st.error("❌ Erro ao registrar saída.")


# Função para equipamentos manuais
def show_movimentacao_modal_equipamento_manual(item_id: int) -> None:
    """Modal principal para equipamentos manuais"""
    st.markdown("## Selecione o tipo de movimentação:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 ENTRADA", use_container_width=True, type="primary"):
            st.session_state.modal_type_manual = "entrada"
            
    with col2:
        if st.button("📤 SAÍDA", use_container_width=True, type="secondary"):
            st.session_state.modal_type_manual = "saida"
    
    if hasattr(st.session_state, 'modal_type_manual'):
        if st.session_state.modal_type_manual == "entrada":
            show_movimentacao_entrada_equipamento_manual(item_id)
        elif st.session_state.modal_type_manual == "saida":
            show_movimentacao_saida_equipamento_manual(item_id)


def show_movimentacao_entrada_equipamento_manual(item_id: int) -> None:
    """Modal específico para ENTRADA de equipamentos manuais"""
    from modules.movimentacoes import MovimentacoesManager
    from modules.equipamentos_manuais import EquipamentosManuaisManager
    from modules.responsaveis import ResponsaveisManager
    import pandas as pd
    
    eq_manager = EquipamentosManuaisManager()
    responsaveis_manager = ResponsaveisManager()
    equipamentos: pd.DataFrame = eq_manager.get_equipamentos()
    item: dict[str, Any] | None = dict(equipamentos[equipamentos['id'] == item_id].iloc[0].to_dict()) if not equipamentos.empty else None
    user_data = st.session_state.user_data if 'user_data' in st.session_state else None
    
    if item is None:
        st.error("❌ Equipamento não encontrado.")
        return
    
    if not user_data or 'id' not in user_data or not isinstance(user_data['id'], int):
        st.error("❌ Usuário não autenticado. Faça login para registrar movimentações.")
        return
    
    manager = MovimentacoesManager()
    st.markdown(f"## ENTRADA: {item['nome']} ({item['codigo']})")
    st.info(f"📍 Localização atual: {item['localizacao']} | Status: {item['status']}")
    
    with st.form("entrada_manual"):
        quantidade = st.number_input("Quantidade *", min_value=1, value=1)
        
        col1, col2 = st.columns(2)
        with col1:
            local_origem = st.text_input("Local de Origem *", placeholder="De onde vem o equipamento")
            local_destino = item.get('localizacao', 'Almoxarifado')
            st.text_input("Local de Destino (atual) *", value=local_destino, disabled=True)
        
        with col2:
            responsaveis_df = responsaveis_manager.get_responsaveis({"ativo": 1})
            responsaveis_options = [""] + [f"{row['nome']} - {row['cargo']}" for _, row in responsaveis_df.iterrows()]
            responsavel_selecionado = st.selectbox("Responsável *", options=responsaveis_options)
        
        motivo = st.selectbox("Motivo (opcional)", ["", "Transferência", "Devolução", "Manutenção"])
        observacoes = st.text_area("Observações", placeholder="Informações adicionais sobre a movimentação")
        
        if st.form_submit_button("💾 Registrar ENTRADA", type="primary"):
            if not local_origem.strip():
                st.error("❌ Local de Origem é obrigatório!")
                return
            if not responsavel_selecionado.strip():
                st.error("❌ Responsável é obrigatório!")
                return
            
            data: dict[str, Any] = {
                'item_id': item['id'],
                'tipo': 'Entrada',
                'tipo_item': 'equipamento_manual',
                'quantidade': quantidade,
                'motivo': motivo if motivo else None,
                'obra_origem_id': None,
                'obra_destino_id': None,
                'responsavel_origem_id': None,
                'responsavel_destino_id': None,
                'valor_unitario': None,
                'observacoes': f"Origem: {local_origem} → Destino: {local_destino} | Responsável: {responsavel_selecionado}" + (f" | {observacoes}" if observacoes else "")
            }
            
            usuario_id: int = user_data['id']
            movimentacao_id = manager.create_movimentacao(data, usuario_id)
            if movimentacao_id:
                st.success(f"✅ ENTRADA registrada com sucesso! (ID: {movimentacao_id})")
                st.rerun()
            else:
                st.error("❌ Erro ao registrar entrada.")


def show_movimentacao_saida_equipamento_manual(item_id: int) -> None:
    """Modal específico para SAÍDA de equipamentos manuais"""
    from modules.movimentacoes import MovimentacoesManager
    from modules.equipamentos_manuais import EquipamentosManuaisManager
    from modules.responsaveis import ResponsaveisManager
    from modules.obras import ObrasManager
    import pandas as pd
    
    eq_manager = EquipamentosManuaisManager()
    responsaveis_manager = ResponsaveisManager()
    obras_manager = ObrasManager()
    equipamentos: pd.DataFrame = eq_manager.get_equipamentos()
    item: dict[str, Any] | None = dict(equipamentos[equipamentos['id'] == item_id].iloc[0].to_dict()) if not equipamentos.empty else None
    user_data = st.session_state.user_data if 'user_data' in st.session_state else None
    
    if item is None:
        st.error("❌ Equipamento não encontrado.")
        return
    
    if not user_data or 'id' not in user_data or not isinstance(user_data['id'], int):
        st.error("❌ Usuário não autenticado. Faça login para registrar movimentações.")
        return
    
    manager = MovimentacoesManager()
    st.markdown(f"## SAÍDA: {item['nome']} ({item['codigo']})")
    st.info(f"📍 Localização atual: {item['localizacao']} | Status: {item['status']}")
    
    with st.form("saida_manual"):
        quantidade_atual = item.get('quantitativo', 1)
        quantidade = st.number_input("Quantidade *", min_value=1, value=1, max_value=quantidade_atual)
        
        col1, col2 = st.columns(2)
        with col1:
            local_origem = item.get('localizacao', 'Almoxarifado')
            st.text_input("Local de Origem (atual) *", value=local_origem, disabled=True)
            
            obras_df = obras_manager.get_obras({"status": "ativo"})
            obras_options = [""] + [f"{row['nome']} - {row['codigo']}" for _, row in obras_df.iterrows()]
            local_destino = st.selectbox("Local de Destino *", options=obras_options,
                                       help="Selecione a obra/departamento de destino")
        
        with col2:
            responsaveis_df = responsaveis_manager.get_responsaveis({"ativo": 1})
            responsaveis_options = [""] + [f"{row['nome']} - {row['cargo']}" for _, row in responsaveis_df.iterrows()]
            responsavel_selecionado = st.selectbox("Responsável *", options=responsaveis_options)
        
        motivo = st.selectbox("Motivo (opcional)", ["", "Transferência", "Empréstimo", "Manutenção", "Perda"])
        observacoes = st.text_area("Observações", placeholder="Informações adicionais sobre a movimentação")
        
        if st.form_submit_button("💾 Registrar SAÍDA", type="primary"):
            if not local_destino.strip():
                st.error("❌ Local de Destino é obrigatório!")
                return
            if not responsavel_selecionado.strip():
                st.error("❌ Responsável é obrigatório!")
                return
            if quantidade > quantidade_atual:
                st.error(f"❌ Quantidade insuficiente! Quantidade atual: {quantidade_atual}")
                return
            
            data: dict[str, Any] = {
                'item_id': item['id'],
                'tipo': 'Saída',
                'tipo_item': 'equipamento_manual',
                'quantidade': quantidade,
                'motivo': motivo if motivo else None,
                'obra_origem_id': None,
                'obra_destino_id': None,
                'responsavel_origem_id': None,
                'responsavel_destino_id': None,
                'valor_unitario': None,
                'observacoes': f"Origem: {local_origem} → Destino: {local_destino} | Responsável: {responsavel_selecionado}" + (f" | {observacoes}" if observacoes else "")
            }
            
            usuario_id: int = user_data['id']
            movimentacao_id = manager.create_movimentacao(data, usuario_id)
            if movimentacao_id:
                st.success(f"✅ SAÍDA registrada com sucesso! (ID: {movimentacao_id})")
                st.rerun()
            else:
                st.error("❌ Erro ao registrar saída.")