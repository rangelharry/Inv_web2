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
            
            # Tabela de manutenções programadas (simplificada)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS manutencoes_programadas (
                id SERIAL PRIMARY KEY,
                equipamento_id INTEGER NOT NULL,
                data_agendada DATE NOT NULL,
                descricao TEXT,
                realizada BOOLEAN DEFAULT FALSE,
                data_realizacao DATE,
                observacoes TEXT,
                responsavel VARCHAR(100),
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Índices para performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_manutencoes_equipamento ON manutencoes_programadas(equipamento_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_manutencoes_data ON manutencoes_programadas(data_agendada)")
            
            conn.commit()
        except Exception as e:
            st.warning(f"Erro ao criar tabelas de manutenção: {e}")

    def agendar_manutencao(self, equipamento_id: int, data: datetime.date, descricao: str) -> None:
        """Agenda nova manutenção preventiva"""
        try:
            if hasattr(self, 'db_manager') and self.db_manager:
                with self.db_manager.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO manutencoes_programadas 
                            (equipamento_id, data_agendada, descricao, realizada)
                            VALUES (%s, %s, %s, FALSE)
                        """, (equipamento_id, data, descricao))
                        conn.commit()
            else:
                # Fallback para dados em memória
                self.manutencoes.append({
                    'equipamento_id': equipamento_id,
                    'data': data,
                    'descricao': descricao,
                    'realizada': False
                })
        except Exception as e:
            st.error(f"Erro ao agendar manutenção: {e}")
            # Fallback para dados em memória
            self.manutencoes.append({
                'equipamento_id': equipamento_id,
                'data': data,
                'descricao': descricao,
                'realizada': False
            })
    
    def get_equipamentos_manutencao(self, busca: str = "") -> List[Dict[str, Any]]:
        """Busca equipamentos disponíveis para manutenção"""
        if not hasattr(self, 'db_manager') or not self.db_manager:
            # Fallback para dados simulados
            equipamentos = [
                {"id": 1, "nome": "Furadeira Industrial", "tipo": "equipamentos_eletricos"},
                {"id": 2, "nome": "Serra Elétrica", "tipo": "equipamentos_eletricos"},
                {"id": 3, "nome": "Martelo", "tipo": "equipamentos_manuais"},
                {"id": 4, "nome": "Chave de Fenda", "tipo": "equipamentos_manuais"}
            ]
            if busca:
                return [eq for eq in equipamentos if busca.lower() in eq['nome'].lower()]
            return equipamentos

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Buscar equipamentos elétricos
                    query_eletricos = """
                        SELECT id, codigo, nome, marca, modelo, status, 
                               'Elétrico' as tipo, 'equipamentos_eletricos' as tabela
                        FROM equipamentos_eletricos 
                        WHERE ativo = TRUE
                    """
                    
                    # Buscar equipamentos manuais  
                    query_manuais = """
                        SELECT id, codigo, nome, marca, modelo, status,
                               'Manual' as tipo, 'equipamentos_manuais' as tabela
                        FROM equipamentos_manuais
                        WHERE ativo = TRUE
                    """
                    
                    params = []
                    if busca:
                        busca_param = f"%{busca}%"
                        query_eletricos += " AND (nome ILIKE %s OR codigo ILIKE %s OR marca ILIKE %s)"
                        query_manuais += " AND (nome ILIKE %s OR codigo ILIKE %s OR marca ILIKE %s)"
                        params = [busca_param, busca_param, busca_param]
                    
                    # Executar queries
                    cursor.execute(query_eletricos, params)
                    equipamentos_eletricos = cursor.fetchall()
                    
                    cursor.execute(query_manuais, params)
                    equipamentos_manuais = cursor.fetchall()
                    
                    equipamentos = []
                    for row in list(equipamentos_eletricos) + list(equipamentos_manuais):
                        if isinstance(row, dict):
                            equipamentos.append(row)
                        else:
                            columns = [desc[0] for desc in cursor.description]
                            equipamentos.append(dict(zip(columns, row)))
            
                    return equipamentos
                    
        except Exception as e:
            st.error(f"Erro ao buscar equipamentos: {e}")
            return []

    def registrar_realizacao(self, equipamento_id: int, data: datetime.date) -> None:
        """Marca manutenção como realizada"""
        try:
            if hasattr(self, 'db_manager') and self.db_manager:
                with self.db_manager.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            UPDATE manutencoes_programadas 
                            SET realizada = TRUE, data_realizacao = CURRENT_DATE
                            WHERE equipamento_id = %s AND data_agendada = %s AND realizada = FALSE
                        """, (equipamento_id, data))
                        conn.commit()
            else:
                # Fallback para dados em memória
                for m in self.manutencoes:
                    if m['equipamento_id'] == equipamento_id and m['data'] == data:
                        m['realizada'] = True
        except Exception as e:
            st.error(f"Erro ao registrar realização: {e}")

    def listar_manutencoes(self, equipamento_id: int = None) -> List[Dict[str, Any]]:
        """Busca manutenções agendadas no banco de dados"""
        if not hasattr(self, 'db_manager') or not self.db_manager:
            return self.manutencoes  # Fallback para dados simulados
            
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    query = """
                        SELECT m.id, m.equipamento_id, m.data_agendada as data, 
                               m.descricao, m.realizada, m.data_realizacao,
                               COALESCE(ee.nome, em.nome) as nome_equipamento,
                               CASE 
                                   WHEN ee.id IS NOT NULL THEN 'Elétrico'
                                   WHEN em.id IS NOT NULL THEN 'Manual'
                                   ELSE 'Desconhecido'
                               END as tipo_equipamento
                        FROM manutencoes_programadas m
                        LEFT JOIN equipamentos_eletricos ee ON m.equipamento_id = ee.id 
                        LEFT JOIN equipamentos_manuais em ON m.equipamento_id = em.id
                    """
                    
                    params = []
                    if equipamento_id:
                        query += " WHERE m.equipamento_id = %s"
                        params.append(equipamento_id)
                    
                    query += " ORDER BY m.data_agendada DESC"
                    cursor.execute(query, params)
                    
                    manutencoes = []
                    for row in cursor.fetchall():
                        if isinstance(row, dict):
                            manutencoes.append(row)
                        else:
                            columns = [desc[0] for desc in cursor.description]
                            manutencoes.append(dict(zip(columns, row)))
                    
                    return manutencoes
                    
        except Exception as e:
            st.error(f"Erro ao listar manutenções: {e}")
            return []

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
            # Busca de equipamentos para manutenção
            st.markdown("**🔍 Buscar Equipamento**")
            search_term = st.text_input("Digite o nome do equipamento:", key="manutencao_search")
            equipamentos = manager.get_equipamentos_manutencao(search_term)
            
            if equipamentos:
                eq_options = {f"{eq['nome']} (ID: {eq['id']}) - {eq['tipo']}": eq for eq in equipamentos}
                eq_selected = st.selectbox("Equipamento:", list(eq_options.keys()), key="manutencao_select")
                eq = eq_options[eq_selected] if eq_selected else None
            else:
                st.warning("Nenhum equipamento encontrado")
                eq = None
        
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
                data_manutencao = manutencao.get('data', manutencao.get('data_agendada', datetime.date.today()))
                if isinstance(data_manutencao, str):
                    data_manutencao = datetime.datetime.strptime(data_manutencao, '%Y-%m-%d').date()
                
                vencida = data_manutencao < datetime.date.today()
                realizada = manutencao.get('realizada', False)
                status_color = "🔴" if vencida and not realizada else "🟢"
                status_text = "Realizada" if realizada else "Pendente"
                
                nome_equipamento = manutencao.get('nome_equipamento', f"Equipamento ID {manutencao.get('equipamento_id', 'N/A')}")
                tipo_equipamento = manutencao.get('tipo_equipamento', manutencao.get('tipo', 'N/A'))
                
                with st.expander(f"{status_color} {nome_equipamento} ({tipo_equipamento}) - {status_text}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Equipamento:** {nome_equipamento}")
                        st.write(f"**Tipo:** {tipo_equipamento}")
                        st.write(f"**Status:** {status_text}")
                    
                    with col2:
                        st.write(f"**Data Agendada:** {data_manutencao}")
                        if vencida and not realizada:
                            st.error("⚠️ Manutenção vencida!")
                        if manutencao.get('data_realizacao'):
                            st.write(f"**Data Realizada:** {manutencao['data_realizacao']}")
                    
                    with col3:
                        descricao = manutencao.get('descricao', 'N/A')
                        st.write(f"**Descrição:** {descricao}")
                        if manutencao.get('observacoes'):
                            st.write(f"**Observações:** {manutencao['observacoes']}")
                    
                    # Botão para marcar como realizada
                    if not realizada:
                        if st.button(f"✅ Marcar como Realizada", key=f"realizada_{i}"):
                            manager.registrar_realizacao(manutencao['equipamento_id'], data_manutencao)
                            st.experimental_rerun()
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
