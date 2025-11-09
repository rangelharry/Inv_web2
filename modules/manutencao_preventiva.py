import datetime
from typing import List, Dict, Any
import streamlit as st
from database.connection import db
from modules.logs_auditoria import log_acao

# Estrutura simples para manutenção preventiva
class ManutencaoPreventivaManager:
    def __init__(self):
        self.manutencoes = []  # Em produção, usar banco de dados
        self.criar_tabelas()
    
    def criar_tabelas(self):
        """Cria tabelas necessárias para manutenção preventiva"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # Tabela de planos de manutenção
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS planos_manutencao (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                descricao TEXT,
                periodicidade_dias INTEGER NOT NULL,
                tipo_equipamento VARCHAR(20),
                checklist JSONB,
                ativo BOOLEAN DEFAULT TRUE,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Tabela de agendamentos de manutenção
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agendamentos_manutencao (
                id SERIAL PRIMARY KEY,
                plano_id INTEGER REFERENCES planos_manutencao(id),
                equipamento_id INTEGER NOT NULL,
                tipo_equipamento VARCHAR(20) NOT NULL,
                data_agendada DATE NOT NULL,
                data_executada DATE,
                status VARCHAR(20) DEFAULT 'pendente',
                observacoes TEXT,
                responsavel_id INTEGER,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            conn.commit()
        except Exception as e:
            st.warning(f"Erro ao criar tabelas de manutenção: {e}")

    def agendar_manutencao(self, equipamento_id: int, data: datetime.date, descricao: str) -> None:
        self.manutencoes.append({
            'equipamento_id': equipamento_id,
            'data': data,
            'descricao': descricao,
            'realizada': False
        })

    def registrar_realizacao(self, equipamento_id: int, data: datetime.date) -> None:
        for m in self.manutencoes:
            if m['equipamento_id'] == equipamento_id and m['data'] == data:
                m['realizada'] = True

    def listar_manutencoes(self, equipamento_id: int = None) -> List[Dict[str, Any]]:
        if equipamento_id:
            return [m for m in self.manutencoes if m['equipamento_id'] == equipamento_id]
        return self.manutencoes

    def proximas_manutencoes(self, dias_aviso: int = 30) -> List[Dict[str, Any]]:
        hoje = datetime.date.today()
        return [m for m in self.manutencoes if not m['realizada'] and 0 <= (m['data'] - hoje).days <= dias_aviso]

def show_manutencao_page():
    """Exibe página de manutenção preventiva"""
    st.title("🔧 Manutenção Preventiva")
    st.markdown("Sistema de agendamento e controle de manutenções preventivas")
    
    manager = ManutencaoPreventivaManager()
    
    tab1, tab2, tab3 = st.tabs(["📅 Agendar", "📋 Agendamentos", "📊 Dashboard"])
    
    with tab1:
        st.subheader("Agendar Nova Manutenção")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Simular equipamentos disponíveis
            equipamentos = [
                {"id": 1, "nome": "Furadeira Industrial", "tipo": "equipamentos_eletricos"},
                {"id": 2, "nome": "Serra Elétrica", "tipo": "equipamentos_eletricos"},
                {"id": 3, "nome": "Martelo", "tipo": "equipamentos_manuais"},
                {"id": 4, "nome": "Chave de Fenda", "tipo": "equipamentos_manuais"}
            ]
            
            eq_options = {f"{eq['nome']} (ID: {eq['id']})": eq for eq in equipamentos}
            eq_selected = st.selectbox("Equipamento:", list(eq_options.keys()))
            eq = eq_options[eq_selected] if eq_selected else None
        
        with col2:
            data_agendada = st.date_input("Data da Manutenção:", 
                                        value=datetime.date.today() + datetime.timedelta(days=7))
            
            descricao = st.text_area("Descrição da Manutenção:", 
                                   placeholder="Descreva o tipo de manutenção a ser realizada",
                                   height=100)
        
        if st.button("📅 Agendar Manutenção", use_container_width=True):
            if eq and data_agendada and descricao:
                manager.agendar_manutencao(eq['id'], data_agendada, descricao)
                st.success("✅ Manutenção agendada com sucesso!")
            else:
                st.error("❌ Preencha todos os campos obrigatórios")
    
    with tab2:
        st.subheader("Lista de Agendamentos")
        
        manutencoes = manager.listar_manutencoes()
        
        if manutencoes:
            st.write(f"📊 Total de manutenções: {len(manutencoes)}")
            
            for i, manutencao in enumerate(manutencoes):
                # Verificar se está vencida
                vencida = manutencao['data'] < datetime.date.today()
                status_color = "🔴" if vencida and not manutencao['realizada'] else "🟢"
                status_text = "Realizada" if manutencao['realizada'] else "Pendente"
                
                with st.expander(f"{status_color} Manutenção #{i+1} - Equipamento ID {manutencao['equipamento_id']} - {status_text}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Equipamento ID:** {manutencao['equipamento_id']}")
                        st.write(f"**Status:** {status_text}")
                    
                    with col2:
                        st.write(f"**Data Agendada:** {manutencao['data']}")
                        if vencida and not manutencao['realizada']:
                            st.error("⚠️ Manutenção vencida!")
                    
                    with col3:
                        st.write(f"**Descrição:** {manutencao['descricao']}")
                    
                    # Botão para marcar como realizada
                    if not manutencao['realizada']:
                        if st.button(f"✅ Marcar como Realizada", key=f"realizar_{i}"):
                            manager.registrar_realizacao(manutencao['equipamento_id'], manutencao['data'])
                            st.success("Manutenção marcada como realizada!")
                            st.rerun()
        else:
            st.info("ℹ️ Nenhuma manutenção agendada")
    
    with tab3:
        st.subheader("📊 Dashboard de Manutenções")
        
        manutencoes = manager.listar_manutencoes()
        proximas = manager.proximas_manutencoes()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total = len(manutencoes)
            st.metric("Total de Manutenções", total)
        
        with col2:
            pendentes = len([m for m in manutencoes if not m['realizada']])
            st.metric("Pendentes", pendentes)
        
        with col3:
            realizadas = len([m for m in manutencoes if m['realizada']])
            st.metric("Realizadas", realizadas)
        
        with col4:
            st.metric("Próximas (30 dias)", len(proximas))
        
        if proximas:
            st.subheader("🔥 Próximas Manutenções")
            for manutencao in proximas:
                dias_restantes = (manutencao['data'] - datetime.date.today()).days
                st.info(f"📅 Equipamento ID {manutencao['equipamento_id']} - {manutencao['data']} ({dias_restantes} dias)")
        
        if manutencoes:
            st.subheader("📈 Gráfico de Status")
            
            status_data = {"Pendentes": pendentes, "Realizadas": realizadas}
            st.bar_chart(status_data)
