import datetime
from typing import List, Dict, Any
import streamlit as st
from database.connection import db
from modules.logs_auditoria import log_acao

# Estrutura simples para reservas
class ReservaManager:
    def __init__(self):
        self.reservas = []  # Em produção, usar banco de dados
        self.criar_tabela_reservas()
    
    def criar_tabela_reservas(self):
        """Cria tabela de reservas se não existir"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            query = """
            CREATE TABLE IF NOT EXISTS reservas (
                id SERIAL PRIMARY KEY,
                tipo_equipamento VARCHAR(20) NOT NULL,
                equipamento_id INTEGER NOT NULL,
                usuario_id INTEGER NOT NULL,
                data_inicio TIMESTAMP NOT NULL,
                data_fim TIMESTAMP NOT NULL,
                observacoes TEXT,
                status VARCHAR(20) DEFAULT 'ativa',
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            cursor.execute(query)
            conn.commit()
        except Exception as e:
            st.warning(f"Erro ao criar tabela de reservas: {e}")

    def reservar(self, equipamento_id: int, usuario: str, data_inicio: datetime.date, data_fim: datetime.date) -> bool:
        # Verifica conflito
        for r in self.reservas:
            if r['equipamento_id'] == equipamento_id and not (data_fim < r['data_inicio'] or data_inicio > r['data_fim']):
                return False  # Conflito
        self.reservas.append({
            'equipamento_id': equipamento_id,
            'usuario': usuario,
            'data_inicio': data_inicio,
            'data_fim': data_fim
        })
        return True

    def listar_reservas(self, equipamento_id: int = None) -> List[Dict[str, Any]]:
        if equipamento_id:
            return [r for r in self.reservas if r['equipamento_id'] == equipamento_id]
        return self.reservas
    
    def get_equipamentos_disponiveis(self, tipo_equipamento: str, busca: str = "") -> List[Dict[str, Any]]:
        """Busca equipamentos disponíveis para reserva"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            if tipo_equipamento == "equipamentos_eletricos":
                query = """
                    SELECT id, codigo, nome, marca, modelo, status
                    FROM equipamentos_eletricos 
                    WHERE ativo = TRUE AND status = 'Disponível'
                """
                params = []
                
                if busca:
                    query += " AND (nome ILIKE %s OR codigo ILIKE %s OR marca ILIKE %s)"
                    busca_param = f"%{busca}%"
                    params.extend([busca_param, busca_param, busca_param])
                    
                query += " ORDER BY nome"
                cursor.execute(query, params)
                
            else:  # equipamentos_manuais
                query = """
                    SELECT id, codigo, descricao as nome, marca, '' as modelo, status
                    FROM equipamentos_manuais 
                    WHERE ativo = TRUE AND status = 'Disponível'
                """
                params = []
                
                if busca:
                    query += " AND (descricao ILIKE %s OR codigo ILIKE %s OR marca ILIKE %s)"
                    busca_param = f"%{busca}%"
                    params.extend([busca_param, busca_param, busca_param])
                    
                query += " ORDER BY descricao"
                cursor.execute(query, params)
            
            equipamentos = []
            for row in cursor.fetchall():
                if isinstance(row, dict):
                    equipamentos.append(row)
                else:
                    # Se for tuple, converter para dict
                    columns = [desc[0] for desc in cursor.description]
                    equipamentos.append(dict(zip(columns, row)))
            
            return equipamentos
            
        except Exception as e:
            st.error(f"Erro ao buscar equipamentos: {e}")
            return []

    def calendario_disponibilidade(self, equipamento_id: int, mes: int, ano: int) -> List[Dict[str, Any]]:
        reservas = self.listar_reservas(equipamento_id)
        return [r for r in reservas if r['data_inicio'].month == mes and r['data_inicio'].year == ano]

def show_reservas_page():
    """Exibe página de gestão de reservas"""
    st.title("📅 Sistema de Reservas")
    st.markdown("Gerencie reservas de equipamentos com controle de conflitos")
    
    manager = ReservaManager()
    
    tab1, tab2, tab3 = st.tabs(["➕ Nova Reserva", "📋 Listar Reservas", "📊 Dashboard"])
    
    with tab1:
        st.subheader("Criar Nova Reserva")
        
        col1, col2 = st.columns(2)
        
        with col1:
            tipo_eq = st.selectbox("Tipo de Equipamento:", 
                                 ["equipamentos_eletricos", "equipamentos_manuais"])
            
            # Campo de busca
            busca_equipamento = st.text_input("🔍 Buscar equipamento:", 
                                            placeholder="Digite nome, código ou marca...")
            
            # Buscar equipamentos reais do banco
            equipamentos = manager.get_equipamentos_disponiveis(tipo_eq, busca_equipamento)
            
            if equipamentos:
                equipamento_options = {f"{eq.get('nome', eq.get('codigo', 'N/A'))} ({eq.get('codigo', 'N/A')})": eq['id'] 
                                     for eq in equipamentos}
                equipamento_selecionado = st.selectbox("Equipamento:", 
                                                      list(equipamento_options.keys()))
                equipamento_id = equipamento_options.get(equipamento_selecionado, 1)
            else:
                st.warning("Nenhum equipamento encontrado para os critérios de busca.")
                equipamento_id = None
        
        with col2:
            data_inicio = st.date_input("Data Início:", 
                                      value=datetime.date.today() + datetime.timedelta(days=1))
            
            data_fim = st.date_input("Data Fim:", 
                                   value=datetime.date.today() + datetime.timedelta(days=2))
            
            usuario = st.text_input("Usuário:", placeholder="Nome do usuário")
        
        if st.button("📅 Criar Reserva", use_container_width=True):
            if equipamento_id and data_inicio and data_fim and usuario:
                if data_fim >= data_inicio:
                    sucesso = manager.reservar(equipamento_id, usuario, data_inicio, data_fim)
                    
                    if sucesso:
                        st.success("✅ Reserva criada com sucesso!")
                    else:
                        st.error("❌ Conflito de agendamento! Equipamento já reservado neste período.")
                else:
                    st.error("❌ Data fim deve ser igual ou posterior à data início")
            else:
                st.error("❌ Preencha todos os campos obrigatórios")
    
    with tab2:
        st.subheader("Lista de Reservas")
        
        reservas = manager.listar_reservas()
        
        if reservas:
            st.write(f"📊 Total de reservas: {len(reservas)}")
            
            for i, reserva in enumerate(reservas):
                with st.expander(f"Reserva #{i+1} - Equipamento ID {reserva['equipamento_id']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Usuário:** {reserva['usuario']}")
                        st.write(f"**Equipamento ID:** {reserva['equipamento_id']}")
                    
                    with col2:
                        st.write(f"**Início:** {reserva['data_inicio']}")
                        st.write(f"**Fim:** {reserva['data_fim']}")
        else:
            st.info("ℹ️ Nenhuma reserva encontrada")
    
    with tab3:
        st.subheader("📊 Dashboard de Reservas")
        
        reservas = manager.listar_reservas()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Reservas", len(reservas))
        
        with col2:
            # Calcular reservas ativas hoje
            hoje = datetime.date.today()
            reservas_ativas = [r for r in reservas 
                             if r['data_inicio'] <= hoje <= r['data_fim']]
            st.metric("Reservas Ativas Hoje", len(reservas_ativas))
        
        with col3:
            # Calcular próximas reservas (próximos 7 dias)
            proxima_semana = hoje + datetime.timedelta(days=7)
            proximas_reservas = [r for r in reservas 
                               if hoje <= r['data_inicio'] <= proxima_semana]
            st.metric("Próximas (7 dias)", len(proximas_reservas))
        
        if reservas:
            st.subheader("📈 Gráfico de Reservas por Equipamento")
            
            # Contar reservas por equipamento
            equipamentos_count = {}
            for reserva in reservas:
                eq_id = reserva['equipamento_id']
                equipamentos_count[eq_id] = equipamentos_count.get(eq_id, 0) + 1
            
            if equipamentos_count:
                st.bar_chart(equipamentos_count)
