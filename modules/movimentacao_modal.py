import streamlit as st
from typing import Any

def verificar_disponibilidade_insumo(item_id: int, quantidade_solicitada: int) -> tuple[bool, str]:
    """Verifica se há estoque suficiente para o insumo"""
    from modules.insumos import InsumosManager
    
    try:
        insumos_manager = InsumosManager()
        insumos = insumos_manager.get_insumos()
        item = next((i for i in insumos if i['id'] == item_id), None)
        
        if not item:
            return False, "❌ Item não encontrado."
        
        estoque_atual = item.get('quantidade_atual', 0)
        
        if estoque_atual <= 0:
            return False, f"❌ **SEM ESTOQUE**: O item '{item['descricao']}' não possui estoque disponível."
        
        if quantidade_solicitada > estoque_atual:
            return False, f"❌ **ESTOQUE INSUFICIENTE**: Solicitado {quantidade_solicitada}, disponível apenas {estoque_atual} {item.get('unidade', 'un')}."
        
        return True, f"✅ Estoque suficiente: {estoque_atual} {item.get('unidade', 'un')} disponível."
        
    except Exception as e:
        return False, f"❌ Erro ao verificar estoque: {str(e)}"

def verificar_disponibilidade_equipamento(item_id: int, tipo: str) -> tuple[bool, str]:
    """Verifica se o equipamento está disponível para movimentação"""
    from modules.movimentacoes import MovimentacoesManager
    
    try:
        movimentacoes_manager = MovimentacoesManager()
        
        # Buscar última movimentação do equipamento
        if tipo == 'eletrico':
            from modules.equipamentos_eletricos import EquipamentosEletricosManager
            eq_manager = EquipamentosEletricosManager()
            equipamentos = eq_manager.get_equipamentos()
            item = dict(equipamentos[equipamentos['id'] == item_id].iloc[0].to_dict()) if not equipamentos.empty and len(equipamentos[equipamentos['id'] == item_id]) > 0 else None
        else:  # manual
            from modules.equipamentos_manuais import EquipamentosManuaisManager
            eq_manager = EquipamentosManuaisManager()
            equipamentos = eq_manager.get_equipamentos()
            item = dict(equipamentos[equipamentos['id'] == item_id].iloc[0].to_dict()) if not equipamentos.empty and len(equipamentos[equipamentos['id'] == item_id]) > 0 else None
        
        if not item:
            return False, "❌ Equipamento não encontrado."
        
        # Verificar se está em uso analisando as movimentações
        ultima_movimentacao = movimentacoes_manager.get_ultima_movimentacao_equipamento(item_id, tipo)
        
        if ultima_movimentacao and ultima_movimentacao.get('tipo_movimentacao') == 'saida':
            obra_atual = ultima_movimentacao.get('local_destino', 'Local não informado')
            return False, f"❌ **EQUIPAMENTO EM USO**: O equipamento '{item.get('nome', 'N/A')}' está atualmente em uso na obra: **{obra_atual}**."
        
        return True, f"✅ Equipamento '{item.get('nome', 'N/A')}' disponível para movimentação."
        
    except Exception as e:
        return False, f"❌ Erro ao verificar disponibilidade: {str(e)}"

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
            responsaveis_df = responsaveis_manager.get_responsaveis({"ativo": True})
            if not responsaveis_df.empty:
                responsaveis_options = [""] + [f"{row['nome']} - {row['cargo']}" for _, row in responsaveis_df.iterrows()]
            else:
                responsaveis_options = ["Nenhum responsável cadastrado"]
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
                st.session_state.pop('modal_type', None)  # Fecha o modal após sucesso
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
    
    # **VERIFICAÇÃO DE ESTOQUE ANTES DE MOSTRAR O FORMULÁRIO**
    estoque_atual = item.get('quantidade_atual', 0)
    if estoque_atual <= 0:
        st.error(f"❌ **SEM ESTOQUE DISPONÍVEL**")
        st.warning(f"O item '{item['descricao']}' não possui estoque para movimentação de saída.")
        st.info("💡 Para registrar entrada de estoque, use o botão 'ENTRADA' deste item.")
        return
    
    st.info(f"📦 Estoque atual: {item['quantidade_atual']} {item['unidade']}")
    
    with st.form("saida_insumo"):
        quantidade = st.number_input("Quantidade *", min_value=1, value=1, max_value=int(estoque_atual))
        
        # **VALIDAÇÃO EM TEMPO REAL DA QUANTIDADE**
        if quantidade > estoque_atual:
            st.error(f"❌ Quantidade solicitada ({quantidade}) excede o estoque disponível ({estoque_atual})!")
        
        col1, col2 = st.columns(2)
        with col1:
            local_origem = item.get('localizacao', 'Almoxarifado')
            st.text_input("Local de Origem (atual) *", value=local_origem, disabled=True)
            # Buscar todas as obras (sem filtrar por status) para mostrar como opções de destino
            obras_df = obras_manager.get_obras()
            obras_options = [""] + [f"{row['nome']} - {row['codigo']}" for _, row in obras_df.iterrows()]
            local_destino = st.selectbox("Local de Destino *", options=obras_options,
                                       help="Selecione a obra/departamento de destino")
            # Pega o ID da obra de destino
            obra_destino_id = None
            if local_destino:
                for _, row in obras_df.iterrows():
                    if f"{row['nome']} - {row['codigo']}" == local_destino:
                        obra_destino_id = row['id']
                        break
        with col2:
            responsaveis_df = responsaveis_manager.get_responsaveis({"ativo": True})
            if not responsaveis_df.empty:
                responsaveis_options = [""] + [f"{row['nome']} - {row['cargo']}" for _, row in responsaveis_df.iterrows()]
            else:
                responsaveis_options = ["Nenhum responsável cadastrado"]
            responsavel_selecionado = st.selectbox("Responsável *", options=responsaveis_options)
            # Pega o ID do responsável
            responsavel_destino_id = None
            if responsavel_selecionado and responsavel_selecionado != "Nenhum responsável cadastrado":
                for _, row in responsaveis_df.iterrows():
                    if f"{row['nome']} - {row['cargo']}" == responsavel_selecionado:
                        responsavel_destino_id = row['id']
                        break

        motivo = st.selectbox("Motivo (opcional)", ["", "Consumo", "Transferência", "Venda", "Perda"])
        observacoes = st.text_area("Observações", placeholder="Informações adicionais sobre a movimentação")

        submitted = st.form_submit_button("💾 Registrar SAÍDA", type="primary")
        if submitted:
            # **VALIDAÇÃO FINAL DE ESTOQUE**
            disponivel, msg_estoque = verificar_disponibilidade_insumo(item_id, quantidade)
            if not disponivel:
                st.error(msg_estoque)
                return
            
            if not local_destino.strip():
                st.error("❌ Local de Destino é obrigatório!")
                return
            if not responsavel_selecionado.strip():
                st.error("❌ Responsável é obrigatório!")
                return

            data: dict[str, Any] = {
                'item_id': item['id'],
                'tipo': 'Saída',
                'tipo_item': 'insumo',
                'quantidade': quantidade,
                'motivo': motivo if motivo else None,
                'obra_origem_id': None,  # Almoxarifado não tem ID, pode ser None
                'obra_destino_id': obra_destino_id,
                'responsavel_origem_id': None,
                'responsavel_destino_id': responsavel_destino_id,
                'valor_unitario': None,
                'observacoes': f"Origem: {local_origem} → Destino: {local_destino} | Responsável: {responsavel_selecionado}" + (f" | {observacoes}" if observacoes else "")
            }

            usuario_id: int = user_data['id']
            movimentacao_id = manager.create_movimentacao(data, usuario_id)
            if movimentacao_id:
                st.success(f"✅ SAÍDA registrada com sucesso! (ID: {movimentacao_id})")
                st.session_state.pop('modal_type', None)  # Limpa seleção do modal
                st.rerun()
            else:
                st.error("❌ Erro ao registrar saída.")


def show_movimentacao_modal_insumo(item_id: int) -> None:
    """Modal principal que permite escolher entre entrada e saída"""
    st.markdown("## Selecione o tipo de movimentação:")
    
    # Limpa seleção ao abrir o modal para este item
    if st.session_state.get('last_modal_item_id') != item_id:
        st.session_state['modal_type'] = None
        st.session_state['last_modal_item_id'] = item_id
    tipo_selecionado = st.session_state.get('modal_type', None)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 ENTRADA", use_container_width=True, type="primary" if tipo_selecionado == "entrada" else "secondary", key=f"entrada_{item_id}"):
            st.session_state.modal_type = "entrada"
            st.rerun()
    with col2:
        if st.button("📤 SAÍDA", use_container_width=True, type="primary" if tipo_selecionado == "saida" else "secondary", key=f"saida_{item_id}"):
            st.session_state.modal_type = "saida"
            st.rerun()
    if tipo_selecionado == "entrada":
        show_movimentacao_entrada_insumo(item_id)
    elif tipo_selecionado == "saida":
        show_movimentacao_saida_insumo(item_id)


# Funções similares para equipamentos elétricos
def show_movimentacao_modal_equipamento_eletrico(item_id: int) -> None:
    """Modal principal para equipamentos elétricos"""
    st.markdown("## Selecione o tipo de movimentação:")
    
    if st.session_state.get('last_modal_item_id_eletrico') != item_id:
        st.session_state['modal_type_eletrico'] = None
        st.session_state['last_modal_item_id_eletrico'] = item_id
    tipo_selecionado = st.session_state.get('modal_type_eletrico', None)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 ENTRADA", use_container_width=True, type="primary" if tipo_selecionado == "entrada" else "secondary"):
            st.session_state.modal_type_eletrico = "entrada"
            st.rerun()
    with col2:
        if st.button("📤 SAÍDA", use_container_width=True, type="primary" if tipo_selecionado == "saida" else "secondary"):
            st.session_state.modal_type_eletrico = "saida"
            st.rerun()
    if tipo_selecionado == "entrada":
        show_movimentacao_entrada_equipamento_eletrico(item_id)
    elif tipo_selecionado == "saida":
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
            responsaveis_df = responsaveis_manager.get_responsaveis({"ativo": True})
            if not responsaveis_df.empty:
                responsaveis_options = [""] + [f"{row['nome']} - {row['cargo']}" for _, row in responsaveis_df.iterrows()]
            else:
                responsaveis_options = ["Nenhum responsável cadastrado"]
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
    
    # **VERIFICAÇÃO DE DISPONIBILIDADE ANTES DE MOSTRAR O FORMULÁRIO**
    disponivel, msg_disponibilidade = verificar_disponibilidade_equipamento(item_id, 'eletrico')
    if not disponivel:
        st.error(msg_disponibilidade)
        st.info("💡 Para registrar retorno à disponibilidade, use o botão 'ENTRADA' deste equipamento.")
        return
    
    st.success(msg_disponibilidade)
    st.info(f"📍 Localização atual: {item['localizacao']} | Status: {item['status']}")
    
    with st.form("saida_eletrico"):
        col1, col2 = st.columns(2)
        with col1:
            local_origem = item.get('localizacao', 'Almoxarifado')
            st.text_input("Local de Origem (atual) *", value=local_origem, disabled=True)
            
            # Buscar todas as obras (sem filtrar por status) para mostrar como opções de destino
            obras_df = obras_manager.get_obras()
            obras_options = [""] + [f"{row['nome']} - {row['codigo']}" for _, row in obras_df.iterrows()]
            local_destino = st.selectbox("Local de Destino *", options=obras_options,
                                       help="Selecione a obra/departamento de destino")
        
        with col2:
            responsaveis_df = responsaveis_manager.get_responsaveis({"ativo": True})
            if not responsaveis_df.empty:
                responsaveis_options = [""] + [f"{row['nome']} - {row['cargo']}" for _, row in responsaveis_df.iterrows()]
            else:
                responsaveis_options = ["Nenhum responsável cadastrado"]
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
                st.session_state.pop('modal_type_eletrico', None)  # Fecha o modal após sucesso
                st.rerun()
            else:
                st.error("❌ Erro ao registrar saída.")


# Função para equipamentos manuais
def show_movimentacao_modal_equipamento_manual(item_id: int) -> None:
    """Modal principal para equipamentos manuais"""
    st.markdown("## Selecione o tipo de movimentação:")
    
    if st.session_state.get('last_modal_item_id_manual') != item_id:
        st.session_state['modal_type_manual'] = None
        st.session_state['last_modal_item_id_manual'] = item_id
    tipo_selecionado = st.session_state.get('modal_type_manual', None)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 ENTRADA", use_container_width=True, type="primary" if tipo_selecionado == "entrada" else "secondary"):
            st.session_state.modal_type_manual = "entrada"
            st.rerun()
    with col2:
        if st.button("📤 SAÍDA", use_container_width=True, type="primary" if tipo_selecionado == "saida" else "secondary"):
            st.session_state.modal_type_manual = "saida"
            st.rerun()
    if tipo_selecionado == "entrada":
        show_movimentacao_entrada_equipamento_manual(item_id)
    elif tipo_selecionado == "saida":
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
            responsaveis_df = responsaveis_manager.get_responsaveis({"ativo": True})
            if not responsaveis_df.empty:
                responsaveis_options = [""] + [f"{row['nome']} - {row['cargo']}" for _, row in responsaveis_df.iterrows()]
            else:
                responsaveis_options = ["Nenhum responsável cadastrado"]
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
    
    # **VERIFICAÇÃO DE DISPONIBILIDADE ANTES DE MOSTRAR O FORMULÁRIO**
    disponivel, msg_disponibilidade = verificar_disponibilidade_equipamento(item_id, 'manual')
    if not disponivel:
        st.error(msg_disponibilidade)
        st.info("💡 Para registrar retorno à disponibilidade, use o botão 'ENTRADA' deste equipamento.")
        return
    
    st.success(msg_disponibilidade)
    st.info(f"📍 Localização atual: {item['localizacao']} | Status: {item['status']}")
    
    with st.form("saida_manual"):
        quantidade_atual = item.get('quantitativo', 1)
        quantidade = st.number_input("Quantidade *", min_value=1, value=1, max_value=quantidade_atual)
        
        col1, col2 = st.columns(2)
        with col1:
            local_origem = item.get('localizacao', 'Almoxarifado')
            st.text_input("Local de Origem (atual) *", value=local_origem, disabled=True)
            
            # Buscar todas as obras (sem filtrar por status) para mostrar como opções de destino
            obras_df = obras_manager.get_obras()
            obras_options = [""] + [f"{row['nome']} - {row['codigo']}" for _, row in obras_df.iterrows()]
            local_destino = st.selectbox("Local de Destino *", options=obras_options,
                                       help="Selecione a obra/departamento de destino")
        
        with col2:
            responsaveis_df = responsaveis_manager.get_responsaveis({"ativo": True})
            if not responsaveis_df.empty:
                responsaveis_options = [""] + [f"{row['nome']} - {row['cargo']}" for _, row in responsaveis_df.iterrows()]
            else:
                responsaveis_options = ["Nenhum responsável cadastrado"]
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
                st.session_state.pop('modal_type_manual', None)  # Fecha o modal após sucesso
                st.rerun()
            else:
                st.error("❌ Erro ao registrar saída.")
