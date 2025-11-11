import streamlit as st
from typing import Dict, List, Any
from datetime import datetime, date, timedelta
from database.connection import db

class GestaoFinanceiraManager:
    """Gerenciador de custos e análise financeira"""
    
    def calcular_custo_por_hora(self, equipamento_id: int, horas_uso: float) -> float:
        """Calcula custo por hora de utilização"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT valor_compra, vida_util_anos 
                FROM equipamentos_eletricos 
                WHERE id = %s AND ativo = TRUE
            """, (equipamento_id,))
            
            resultado = cursor.fetchone()
            if resultado and resultado['valor_compra'] and resultado['vida_util_anos']:
                # Conversão segura para evitar TypeError
                try:
                    valor_raw = resultado['valor_compra']
                    if valor_raw is None:
                        return 0.0
                    valor_compra = float(str(valor_raw).replace(',', '.'))
                except (ValueError, TypeError):
                    return 0.0
                    
                vida_util_anos = int(resultado['vida_util_anos'])
                
                # Cálculo: valor total / (anos * 365 dias * 8 horas/dia)
                custo_por_hora = valor_compra / (vida_util_anos * 365 * 8)
                return custo_por_hora * horas_uso
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def calcular_depreciacao(self, equipamento_id: int) -> Dict[str, Any]:
        """Calcula depreciação do equipamento"""
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT valor_compra, vida_util_anos, data_aquisicao
                FROM equipamentos_eletricos 
                WHERE id = %s AND ativo = TRUE
            """, (equipamento_id,))
            
            resultado = cursor.fetchone()
            if resultado and all(resultado.values()):
                # Conversão segura para evitar TypeError
                try:
                    valor_raw = resultado['valor_compra']
                    if valor_raw is None:
                        return 0.0
                    valor_compra = float(str(valor_raw).replace(',', '.'))
                except (ValueError, TypeError):
                    return 0.0
                    
                vida_util_anos = int(resultado['vida_util_anos'])
                data_aquisicao = resultado['data_aquisicao']
                
                if isinstance(data_aquisicao, str):
                    data_aquisicao = datetime.strptime(data_aquisicao, '%Y-%m-%d').date()
                
                hoje = date.today()
                dias_uso = (hoje - data_aquisicao).days
                anos_uso = dias_uso / 365.0
                
                depreciacao_anual = valor_compra / vida_util_anos
                depreciacao_acumulada = depreciacao_anual * min(anos_uso, vida_util_anos)
                valor_residual = valor_compra - depreciacao_acumulada
                
                return {
                    'valor_original': valor_compra,
                    'depreciacao_anual': depreciacao_anual,
                    'depreciacao_acumulada': depreciacao_acumulada,
                    'valor_residual': max(0, valor_residual),
                    'anos_uso': anos_uso
                }
            
            return {}
            
        except Exception:
            return {}

def show_analise_roi():
    """Análise de ROI de equipamentos"""
    st.header("📊 Análise de ROI")
    
    manager = GestaoFinanceiraManager()
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nome, valor_compra, vida_util_anos
            FROM equipamentos_eletricos 
            WHERE ativo = TRUE AND valor_compra > 0
            ORDER BY valor_compra DESC
            LIMIT 10
        """)
        
        equipamentos = cursor.fetchall()
        
        if equipamentos:
            st.subheader("Top 10 Equipamentos por Valor")
            
            for eq in equipamentos:
                with st.expander(f"{eq['nome']} - R$ {eq['valor_compra']:,.2f}"):
                    depreciacao = manager.calcular_depreciacao(eq['id'])
                    
                    if depreciacao:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Valor Original", f"R$ {depreciacao['valor_original']:,.2f}")
                        
                        with col2:
                            st.metric("Depreciação Anual", f"R$ {depreciacao['depreciacao_anual']:,.2f}")
                        
                        with col3:
                            st.metric("Valor Residual", f"R$ {depreciacao['valor_residual']:,.2f}")
                        
                        # Barra de progresso da depreciação
                        percentual_depreciado = (depreciacao['depreciacao_acumulada'] / depreciacao['valor_original']) * 100
                        st.progress(min(percentual_depreciado / 100, 1.0))
                        st.caption(f"Depreciação: {percentual_depreciado:.1f}%")
        
    except Exception as e:
        st.error(f"Erro ao carregar análise de ROI: {e}")

def show_controle_custos():
    """Controle de custos por utilização"""
    st.header("💰 Controle de Custos")
    
    manager = GestaoFinanceiraManager()
    
    with st.form("calculo_custo"):
        eq_id = st.number_input("ID do Equipamento", min_value=1, step=1)
        horas = st.number_input("Horas de Utilização", min_value=0.1, step=0.1)
        
        if st.form_submit_button("💵 Calcular Custo"):
            custo = manager.calcular_custo_por_hora(eq_id, horas)
            if custo > 0:
                st.success(f"💰 Custo estimado: R$ {custo:.2f}")
                st.info(f"📊 Custo por hora: R$ {custo/horas:.2f}")
            else:
                st.warning("⚠️ Não foi possível calcular o custo para este equipamento")

def show_gestao_financeira_page():
    """Página principal de gestão financeira"""
    st.title("💰 Gestão Financeira")
    
    show_controle_custos()
    show_analise_roi()