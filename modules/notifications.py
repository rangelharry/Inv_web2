import datetime
from typing import List, Dict, Any
import streamlit as st

# Função melhorada para notificar estoque baixo com resumo
def notificar_estoque_baixo(itens: List[Dict[str, Any]], limite: int = 5):
    """Notifica itens com estoque baixo de forma resumida"""
    itens_baixos = []
    
    # Identificar itens com estoque baixo
    for item in itens:
        quantidade = item.get('quantidade_atual', item.get('quantidade', 0))
        if quantidade <= limite:
            itens_baixos.append({
                'nome': item.get('nome', 'Item desconhecido'),
                'quantidade': quantidade,
                'minima': item.get('quantidade_minima', limite)
            })
    
    if not itens_baixos:
        return
    
    # Mostrar resumo
    total_itens = len(itens_baixos)
    
    if total_itens > 0:
        # Container principal com estilo
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if total_itens == 1:
                    st.warning(f"⚠️ **{total_itens} item com estoque baixo**")
                else:
                    st.warning(f"⚠️ **{total_itens} itens com estoque baixo**")
            
            with col2:
                # Botão para expandir detalhes
                if st.button("📋 Ver Detalhes", key="estoque_baixo_detalhes"):
                    st.session_state.show_estoque_baixo = not st.session_state.get('show_estoque_baixo', False)
    
    # Mostrar detalhes se expandido
    if st.session_state.get('show_estoque_baixo', False):
        with st.expander("📦 Detalhes do Estoque Baixo", expanded=True):
            for item in itens_baixos:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.text(f"• {item['nome']}")
                with col2:
                    st.text(f"Atual: {item['quantidade']}")
                with col3:
                    st.text(f"Mín: {item['minima']}")

# Função melhorada para notificar vencimento próximo com resumo
def notificar_vencimento(itens: List[Dict[str, Any]], dias_aviso: int = 30):
    """Notifica itens próximos ao vencimento de forma resumida"""
    hoje = datetime.date.today()
    itens_vencendo = []
    
    # Identificar itens próximos ao vencimento
    for item in itens:
        data_venc = item.get('data_validade') or item.get('data_vencimento')
        if data_venc:
            if isinstance(data_venc, str):
                try:
                    data_venc = datetime.datetime.strptime(data_venc, '%Y-%m-%d').date()
                except Exception:
                    continue
            
            dias_para_vencer = (data_venc - hoje).days
            if 0 <= dias_para_vencer <= dias_aviso:
                itens_vencendo.append({
                    'nome': item.get('nome', 'Item desconhecido'),
                    'dias_para_vencer': dias_para_vencer,
                    'data_vencimento': data_venc.strftime('%d/%m/%Y')
                })
    
    if not itens_vencendo:
        return
    
    # Mostrar resumo
    total_itens = len(itens_vencendo)
    
    if total_itens > 0:
        # Container principal com estilo
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if total_itens == 1:
                    st.info(f"📅 **{total_itens} item próximo ao vencimento**")
                else:
                    st.info(f"📅 **{total_itens} itens próximos ao vencimento**")
            
            with col2:
                # Botão para expandir detalhes
                if st.button("📋 Ver Detalhes", key="vencimento_detalhes"):
                    st.session_state.show_vencimento = not st.session_state.get('show_vencimento', False)
    
    # Mostrar detalhes se expandido
    if st.session_state.get('show_vencimento', False):
        with st.expander("📅 Detalhes dos Vencimentos", expanded=True):
            for item in itens_vencendo:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.text(f"• {item['nome']}")
                with col2:
                    if item['dias_para_vencer'] == 0:
                        st.error("HOJE!")
                    elif item['dias_para_vencer'] <= 7:
                        st.error(f"{item['dias_para_vencer']} dias")
                    else:
                        st.warning(f"{item['dias_para_vencer']} dias")
                with col3:
                    st.text(item['data_vencimento'])

# Exemplo de função para notificar equipamentos próximos ao fim da vida útil
def notificar_vida_util(itens: List[Dict[str, Any]], percentual_aviso: float = 0.9):
    hoje = datetime.date.today()
    for item in itens:
        data_aquisicao = item.get('data_aquisicao')
        vida_util_anos = item.get('vida_util_anos')
        if data_aquisicao and vida_util_anos:
            if isinstance(data_aquisicao, str):
                try:
                    data_aquisicao = datetime.datetime.strptime(data_aquisicao, '%Y-%m-%d').date()
                except Exception:
                    continue
            fim_vida_util = data_aquisicao + datetime.timedelta(days=vida_util_anos*365)
            total_dias = (fim_vida_util - data_aquisicao).days
            dias_passados = (hoje - data_aquisicao).days
            if dias_passados/total_dias >= percentual_aviso:
                st.warning(f"Equipamento próximo ao fim da vida útil: {item.get('nome', 'Item desconhecido')}")
