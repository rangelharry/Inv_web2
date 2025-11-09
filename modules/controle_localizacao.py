import streamlit as st
from typing import Dict, List, Any
from datetime import datetime, timedelta
from database.connection import db

class LocalizacaoManager:
    """Gerenciador de localização e rastreamento de equipamentos"""
    
    def __init__(self):
        self.localizacoes = []  # Em produção, usar banco de dados
    
    def registrar_localizacao(self, equipamento_id: int, latitude: float, longitude: float, 
                            endereco: str = "", responsavel: str = "") -> bool:
        """Registra nova localização do equipamento"""
        try:
            self.localizacoes.append({
                'equipamento_id': equipamento_id,
                'latitude': latitude,
                'longitude': longitude,
                'endereco': endereco,
                'responsavel': responsavel,
                'timestamp': datetime.now(),
                'ativo': True
            })
            return True
        except Exception:
            return False
    
    def obter_localizacao_atual(self, equipamento_id: int) -> Dict[str, Any] | None:
        """Obtém localização atual do equipamento"""
        localizacoes_eq = [loc for loc in self.localizacoes 
                          if loc['equipamento_id'] == equipamento_id and loc['ativo']]
        if localizacoes_eq:
            return max(localizacoes_eq, key=lambda x: x['timestamp'])
        return None
    
    def historico_movimentacoes(self, equipamento_id: int, dias: int = 30) -> List[Dict[str, Any]]:
        """Histórico de movimentações do equipamento"""
        data_limite = datetime.now() - timedelta(days=dias)
        return [loc for loc in self.localizacoes 
                if loc['equipamento_id'] == equipamento_id and loc['timestamp'] >= data_limite]

def show_localizacao_page():
    """Página de controle de localização"""
    st.title("📍 Controle de Localização")
    
    manager = LocalizacaoManager()
    
    # Seção de registro de localização
    st.header("📌 Registrar Localização")
    with st.form("registro_localizacao"):
        eq_id = st.number_input("ID do Equipamento", min_value=1, step=1)
        lat = st.number_input("Latitude", format="%.6f")
        lng = st.number_input("Longitude", format="%.6f")
        endereco = st.text_input("Endereço")
        responsavel = st.text_input("Responsável")
        
        if st.form_submit_button("📍 Registrar Localização"):
            if manager.registrar_localizacao(eq_id, lat, lng, endereco, responsavel):
                st.success("✅ Localização registrada com sucesso!")
            else:
                st.error("❌ Erro ao registrar localização")
    
    # Seção de consulta
    st.header("🔍 Consultar Localização")
    eq_consulta = st.number_input("ID do Equipamento para Consulta", min_value=1, step=1, key="consulta")
    
    if st.button("🔍 Buscar"):
        loc_atual = manager.obter_localizacao_atual(eq_consulta)
        if loc_atual:
            st.success(f"📍 Localização atual do equipamento {eq_consulta}:")
            st.write(f"**Coordenadas:** {loc_atual['latitude']}, {loc_atual['longitude']}")
            st.write(f"**Endereço:** {loc_atual['endereco']}")
            st.write(f"**Responsável:** {loc_atual['responsavel']}")
            st.write(f"**Última atualização:** {loc_atual['timestamp']}")
        else:
            st.warning("⚠️ Nenhuma localização encontrada para este equipamento")