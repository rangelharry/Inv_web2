import datetime
from typing import List, Dict, Any
import streamlit as st

# Exemplo de função para notificar estoque baixo
def notificar_estoque_baixo(itens: List[Dict[str, Any]], limite: int = 5):
    for item in itens:
        if item.get('quantidade', 0) <= limite:
            st.warning(f"Estoque baixo: {item.get('nome', 'Item desconhecido')} (Qtd: {item.get('quantidade', 0)})")

# Exemplo de função para notificar vencimento próximo
def notificar_vencimento(itens: List[Dict[str, Any]], dias_aviso: int = 30):
    hoje = datetime.date.today()
    for item in itens:
        data_venc = item.get('data_vencimento')
        if data_venc:
            if isinstance(data_venc, str):
                try:
                    data_venc = datetime.datetime.strptime(data_venc, '%Y-%m-%d').date()
                except Exception:
                    continue
            dias_para_vencer = (data_venc - hoje).days
            if 0 <= dias_para_vencer <= dias_aviso:
                st.info(f"Vencimento próximo: {item.get('nome', 'Item desconhecido')} em {dias_para_vencer} dias")

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
