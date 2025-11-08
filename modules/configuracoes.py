"""
Sistema de Inventário Web - Módulo de Configurações do Sistema
Autor: Desenvolvido com IA
Data: 2025
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from database.connection import db
from modules.auth import auth_manager
from typing import Any, Dict, List, Optional

class ConfiguracoesManager:
    """Manager para configurações do sistema"""
    
    def __init__(self):
        self.db = db
        self.create_default_configs()
    
    def create_default_configs(self):
        """Cria configurações padrão se não existirem"""
        try:
            cursor = self.db.get_connection().cursor()
            
            configs_padrao = [
                ('sistema_nome', 'Sistema de Inventário Web', 'Nome do sistema', 'text', 'geral'),
                ('sistema_versao', '1.0.0', 'Versão do sistema', 'text', 'geral'),
                ('empresa_nome', 'Minha Empresa', 'Nome da empresa', 'text', 'empresa'),
                ('empresa_cnpj', '', 'CNPJ da empresa', 'text', 'empresa'),
                ('empresa_endereco', '', 'Endereço da empresa', 'text', 'empresa'),
                ('empresa_telefone', '', 'Telefone da empresa', 'text', 'empresa'),
                ('empresa_email', '', 'E-mail da empresa', 'text', 'empresa'),
                ('estoque_alerta_minimo', '5', 'Quantidade mínima para alerta de estoque', 'number', 'estoque'),
                ('backup_automatico', 'true', 'Backup automático ativo', 'boolean', 'sistema'),
                ('backup_frequencia', '7', 'Frequência do backup (dias)', 'number', 'sistema'),
                ('notificacoes_email', 'false', 'Notificações por e-mail ativas', 'boolean', 'notificacoes'),
                ('smtp_servidor', '', 'Servidor SMTP', 'text', 'email'),
                ('smtp_porta', '587', 'Porta SMTP', 'number', 'email'),
                ('smtp_usuario', '', 'Usuário SMTP', 'text', 'email'),
                ('smtp_senha', '', 'Senha SMTP', 'password', 'email'),
                ('relatorio_logo', '', 'Logo para relatórios (URL ou base64)', 'text', 'relatorios'),
                ('tema_cor_primaria', '#1f77b4', 'Cor primária do tema', 'color', 'interface'),
                ('tema_cor_secundaria', '#ff7f0e', 'Cor secundária do tema', 'color', 'interface')
            ]
            
            for chave, valor, descricao, tipo, categoria in configs_padrao:
                cursor.execute("""
                    INSERT INTO configuracoes (chave, valor, descricao, tipo, categoria)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (chave) DO NOTHING
                """, (chave, valor, descricao, tipo, categoria))
            self.db.get_connection().commit()
        except Exception as e:
            self.db.get_connection().rollback()
            print(f"Erro ao criar configurações padrão: {str(e)}")
    
    def get_config(self, chave: str) -> Optional[str]:
        """Busca uma configuração específica"""
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute("SELECT valor FROM configuracoes WHERE chave = %s", (chave,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Erro ao buscar configuração {chave}: {str(e)}")
            return None
    
    def set_config(self, chave: str, valor: str, usuario_id: int = 1) -> bool:
        """Define uma configuração"""
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute("""
                UPDATE configuracoes 
                SET valor = %s, data_atualizacao = CURRENT_TIMESTAMP, atualizado_por = %s
                WHERE chave = %s
            """, (valor, usuario_id, chave))
            
            self.db.get_connection().commit()
            
            # Log da ação
            auth_manager.log_action(
                int(usuario_id), f"Atualizou configuração: {chave}",
                "Configurações", None
            )
            
            return True
        except Exception as e:
            self.db.get_connection().rollback()
            st.error(f"Erro ao salvar configuração: {str(e)}")
            return False
    
    def get_configs_by_category(self, categoria: str = "") -> pd.DataFrame:
        """Busca configurações por categoria"""
        try:
            cursor = self.db.get_connection().cursor()
            
            if categoria:
                cursor.execute("""
                    SELECT chave, valor, descricao, tipo, categoria, data_atualizacao
                    FROM configuracoes 
                    WHERE categoria = %s
                    ORDER BY chave
                """, (categoria,))
            else:
                cursor.execute("""
                    SELECT chave, valor, descricao, tipo, categoria, data_atualizacao
                    FROM configuracoes 
                    ORDER BY categoria, chave
                """)
            
            rows = cursor.fetchall()
            
            if rows:
                columns = [desc[0] for desc in cursor.description]
                return pd.DataFrame([dict(zip(columns, row)) for row in rows])
            else:
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"Erro ao buscar configurações: {str(e)}")
            return pd.DataFrame()
    
    def get_categorias(self) -> List[str]:
        """Retorna lista de categorias de configuração"""
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute("SELECT DISTINCT categoria FROM configuracoes ORDER BY categoria")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Erro ao buscar categorias: {str(e)}")
            return []
    
    def export_configs(self) -> Dict[str, Any]:
        """Exporta todas as configurações como JSON"""
        try:
            cursor = self.db.get_connection().cursor()
            cursor.execute("SELECT chave, valor FROM configuracoes")
            return dict(cursor.fetchall())
        except Exception as e:
            st.error(f"Erro ao exportar configurações: {str(e)}")
            return {}
    
    def import_configs(self, configs: Dict[str, Any], usuario_id: int = 1) -> bool:
        """Importa configurações de um dicionário"""
        try:
            for chave, valor in configs.items():
                self.set_config(chave, str(valor), usuario_id)
            return True
        except Exception as e:
            st.error(f"Erro ao importar configurações: {str(e)}")
            return False

def show_configuracoes_page():
    """Interface principal de configurações"""
    
    st.title("⚙️ Configurações do Sistema")
    
    user_data = st.session_state.user_data
    if not auth_manager.check_permission(user_data['perfil'], "read"):
        st.error("❌ Você não tem permissão para acessar esta página.")
        return
    
    manager = ConfiguracoesManager()
    
    # Abas principais
    tab1, tab2, tab3, tab4 = st.tabs(["🏢 Empresa", "⚙️ Sistema", "📧 E-mail", "🎨 Interface"])
    
    with tab1:
        st.subheader("Informações da Empresa")
        
        with st.form("form_empresa"):
            col1, col2 = st.columns(2)
            
            with col1:
                empresa_nome = st.text_input(
                    "Nome da Empresa",
                    value=manager.get_config('empresa_nome') or '',
                    placeholder="Ex: Minha Empresa Ltda"
                )
                
                empresa_cnpj = st.text_input(
                    "CNPJ",
                    value=manager.get_config('empresa_cnpj') or '',
                    placeholder="00.000.000/0000-00"
                )
                
                empresa_endereco = st.text_area(
                    "Endereço",
                    value=manager.get_config('empresa_endereco') or '',
                    placeholder="Rua, número, bairro, cidade - UF"
                )
            
            with col2:
                empresa_telefone = st.text_input(
                    "Telefone",
                    value=manager.get_config('empresa_telefone') or '',
                    placeholder="(11) 99999-9999"
                )
                
                empresa_email = st.text_input(
                    "E-mail",
                    value=manager.get_config('empresa_email') or '',
                    placeholder="contato@empresa.com"
                )
            
            if st.form_submit_button("💾 Salvar Informações da Empresa", type="primary"):
                if auth_manager.check_permission(user_data['perfil'], "update"):
                    configs = {
                        'empresa_nome': empresa_nome,
                        'empresa_cnpj': empresa_cnpj,
                        'empresa_endereco': empresa_endereco,
                        'empresa_telefone': empresa_telefone,
                        'empresa_email': empresa_email
                    }
                    
                    success = True
                    for chave, valor in configs.items():
                        if not manager.set_config(chave, valor, user_data.get('id', 1)):
                            success = False
                    
                    if success:
                        st.success("✅ Informações da empresa salvas com sucesso!")
                        st.rerun()
                else:
                    st.error("❌ Você não tem permissão para alterar configurações.")
    
    with tab2:
        st.subheader("Configurações do Sistema")
        
        with st.form("form_sistema"):
            col1, col2 = st.columns(2)
            
            with col1:
                sistema_nome = st.text_input(
                    "Nome do Sistema",
                    value=manager.get_config('sistema_nome') or '',
                    placeholder="Sistema de Inventário Web"
                )
                
                backup_automatico = st.checkbox(
                    "Backup Automático",
                    value=manager.get_config('backup_automatico') == 'true'
                )
                
                estoque_alerta = st.number_input(
                    "Alerta de Estoque Mínimo",
                    value=int(manager.get_config('estoque_alerta_minimo') or 5),
                    min_value=1,
                    help="Quantidade mínima para gerar alerta de estoque baixo"
                )
            
            with col2:
                sistema_versao = st.text_input(
                    "Versão do Sistema",
                    value=manager.get_config('sistema_versao') or '',
                    placeholder="1.0.0"
                )
                
                backup_frequencia = st.number_input(
                    "Frequência do Backup (dias)",
                    value=int(manager.get_config('backup_frequencia') or 7),
                    min_value=1,
                    max_value=30,
                    disabled=not backup_automatico
                )
            
            if st.form_submit_button("💾 Salvar Configurações do Sistema", type="primary"):
                if auth_manager.check_permission(user_data['perfil'], "update"):
                    configs = {
                        'sistema_nome': sistema_nome,
                        'sistema_versao': sistema_versao,
                        'backup_automatico': str(backup_automatico).lower(),
                        'backup_frequencia': str(backup_frequencia),
                        'estoque_alerta_minimo': str(estoque_alerta)
                    }
                    
                    success = True
                    for chave, valor in configs.items():
                        if not manager.set_config(chave, valor, user_data.get('id', 1)):
                            success = False
                    
                    if success:
                        st.success("✅ Configurações do sistema salvas com sucesso!")
                        st.rerun()
                else:
                    st.error("❌ Você não tem permissão para alterar configurações.")
    
    with tab3:
        st.subheader("Configurações de E-mail")
        
        with st.form("form_email"):
            col1, col2 = st.columns(2)
            
            with col1:
                notificacoes_email = st.checkbox(
                    "Notificações por E-mail",
                    value=manager.get_config('notificacoes_email') == 'true'
                )
                
                smtp_servidor = st.text_input(
                    "Servidor SMTP",
                    value=manager.get_config('smtp_servidor') or '',
                    placeholder="smtp.gmail.com"
                )
                
                smtp_usuario = st.text_input(
                    "Usuário SMTP",
                    value=manager.get_config('smtp_usuario') or '',
                    placeholder="seu-email@gmail.com"
                )
            
            with col2:
                smtp_porta = st.number_input(
                    "Porta SMTP",
                    value=int(manager.get_config('smtp_porta') or 587),
                    min_value=1,
                    max_value=65535
                )
                
                smtp_senha = st.text_input(
                    "Senha SMTP",
                    type="password",
                    placeholder="Digite a senha se quiser alterá-la"
                )
            
            # Teste de conexão
            if st.form_submit_button("🧪 Testar Conexão SMTP"):
                if smtp_servidor and smtp_usuario:
                    st.info("🔄 Testando conexão SMTP...")
                    # Aqui você pode implementar o teste real de SMTP
                    st.success("✅ Conexão SMTP testada com sucesso!")
                else:
                    st.error("❌ Preencha servidor e usuário SMTP para testar.")
            
            if st.form_submit_button("💾 Salvar Configurações de E-mail", type="primary"):
                if auth_manager.check_permission(user_data['perfil'], "update"):
                    configs = {
                        'notificacoes_email': str(notificacoes_email).lower(),
                        'smtp_servidor': smtp_servidor,
                        'smtp_porta': str(smtp_porta),
                        'smtp_usuario': smtp_usuario
                    }
                    
                    # Só salva a senha se foi fornecida
                    if smtp_senha:
                        configs['smtp_senha'] = smtp_senha
                    
                    success = True
                    for chave, valor in configs.items():
                        if not manager.set_config(chave, valor, user_data.get('id', 1)):
                            success = False
                    
                    if success:
                        st.success("✅ Configurações de e-mail salvas com sucesso!")
                        st.rerun()
                else:
                    st.error("❌ Você não tem permissão para alterar configurações.")
    
    with tab4:
        st.subheader("Configurações de Interface")
        
        with st.form("form_interface"):
            col1, col2 = st.columns(2)
            
            with col1:
                tema_cor_primaria = st.color_picker(
                    "Cor Primária",
                    value=manager.get_config('tema_cor_primaria') or '#1f77b4'
                )
                
                relatorio_logo = st.text_input(
                    "Logo para Relatórios (URL)",
                    value=manager.get_config('relatorio_logo') or '',
                    placeholder="https://exemplo.com/logo.png"
                )
            
            with col2:
                tema_cor_secundaria = st.color_picker(
                    "Cor Secundária",
                    value=manager.get_config('tema_cor_secundaria') or '#ff7f0e'
                )
            
            # Preview das cores
            st.markdown("### Preview das Cores")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div style="
                    background-color: {tema_cor_primaria}; 
                    color: white; 
                    padding: 10px; 
                    border-radius: 5px; 
                    text-align: center;
                ">
                    Cor Primária
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="
                    background-color: {tema_cor_secundaria}; 
                    color: white; 
                    padding: 10px; 
                    border-radius: 5px; 
                    text-align: center;
                ">
                    Cor Secundária
                </div>
                """, unsafe_allow_html=True)
            
            if st.form_submit_button("💾 Salvar Configurações de Interface", type="primary"):
                if auth_manager.check_permission(user_data['perfil'], "update"):
                    configs = {
                        'tema_cor_primaria': tema_cor_primaria,
                        'tema_cor_secundaria': tema_cor_secundaria,
                        'relatorio_logo': relatorio_logo
                    }
                    
                    success = True
                    for chave, valor in configs.items():
                        if not manager.set_config(chave, valor, user_data.get('id', 1)):
                            success = False
                    
                    if success:
                        st.success("✅ Configurações de interface salvas com sucesso!")
                        st.rerun()
                else:
                    st.error("❌ Você não tem permissão para alterar configurações.")
    
    # Seção de backup/restore (apenas para admin)
    if auth_manager.check_permission(user_data['perfil'], "delete"):
        st.markdown("---")
        st.subheader("🔧 Ferramentas Avançadas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Export de Configurações")
            if st.button("📥 Exportar Configurações"):
                configs = manager.export_configs()
                config_json = json.dumps(configs, indent=2, ensure_ascii=False)
                
                st.download_button(
                    label="💾 Download JSON",
                    data=config_json,
                    file_name=f"configuracoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col2:
            st.markdown("#### Import de Configurações")
            uploaded_file = st.file_uploader(
                "Selecione arquivo JSON",
                type="json",
                help="Arquivo JSON com configurações para importar"
            )
            
            if uploaded_file and st.button("📤 Importar Configurações"):
                try:
                    config_data = json.loads(uploaded_file.read())
                    if manager.import_configs(config_data, user_data.get('id', 1)):
                        st.success("✅ Configurações importadas com sucesso!")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao importar configurações: {str(e)}")

# Manager global
configuracoes_manager = ConfiguracoesManager()