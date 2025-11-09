import os
import shutil
import subprocess
import schedule
import time
import zipfile
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import streamlit as st
from database.connection import db

class BackupRecoveryManager:
    """Sistema de backup automático e disaster recovery"""
    
    def __init__(self):
        self.backup_dir = "backups"
        self.config_file = "backup_config.json"
        self.max_backups = 30  # Manter 30 backups
        self.ensure_backup_directory()
        
    def ensure_backup_directory(self):
        """Garante que o diretório de backup existe"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_database_backup(self) -> Dict[str, Any]:
        """Cria backup do banco de dados PostgreSQL"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"db_backup_{timestamp}.sql"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Comando pg_dump (ajuste conforme sua configuração)
            cmd = [
                "pg_dump",
                "--host=localhost",
                "--port=5432",
                "--username=postgres",
                "--dbname=inventario_web",
                "--file=" + backup_path,
                "--verbose"
            ]
            
            # Executar backup
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Comprimir backup
                zip_path = backup_path + ".zip"
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(backup_path, backup_filename)
                
                # Remover arquivo SQL não comprimido
                os.remove(backup_path)
                
                file_size = os.path.getsize(zip_path) / (1024 * 1024)  # MB
                
                return {
                    'sucesso': True,
                    'arquivo': zip_path,
                    'timestamp': timestamp,
                    'tamanho_mb': round(file_size, 2),
                    'tipo': 'database'
                }
            else:
                return {
                    'sucesso': False,
                    'erro': result.stderr or 'Erro desconhecido no backup'
                }
                
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def create_files_backup(self) -> Dict[str, Any]:
        """Cria backup dos arquivos do sistema"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"files_backup_{timestamp}.zip"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Arquivos e diretórios para backup
            items_to_backup = [
                "modules/",
                "database/",
                "static/",
                "main.py",
                "requirements.txt",
                "api_rest.py"
            ]
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for item in items_to_backup:
                    if os.path.exists(item):
                        if os.path.isfile(item):
                            zipf.write(item)
                        elif os.path.isdir(item):
                            for root, dirs, files in os.walk(item):
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    zipf.write(file_path)
            
            file_size = os.path.getsize(backup_path) / (1024 * 1024)  # MB
            
            return {
                'sucesso': True,
                'arquivo': backup_path,
                'timestamp': timestamp,
                'tamanho_mb': round(file_size, 2),
                'tipo': 'files'
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def create_full_backup(self) -> Dict[str, Any]:
        """Cria backup completo (banco + arquivos)"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup do banco
            db_backup = self.create_database_backup()
            if not db_backup['sucesso']:
                return db_backup
            
            # Backup dos arquivos
            files_backup = self.create_files_backup()
            if not files_backup['sucesso']:
                return files_backup
            
            # Backup completo em um único arquivo
            full_backup_filename = f"full_backup_{timestamp}.zip"
            full_backup_path = os.path.join(self.backup_dir, full_backup_filename)
            
            with zipfile.ZipFile(full_backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Adicionar backup do banco
                zipf.write(db_backup['arquivo'], os.path.basename(db_backup['arquivo']))
                
                # Adicionar backup dos arquivos
                zipf.write(files_backup['arquivo'], os.path.basename(files_backup['arquivo']))
                
                # Adicionar metadados
                metadata = {
                    'timestamp': timestamp,
                    'db_backup': db_backup,
                    'files_backup': files_backup,
                    'created_at': datetime.now().isoformat()
                }
                
                zipf.writestr('backup_metadata.json', json.dumps(metadata, indent=2))
            
            # Remover backups individuais
            os.remove(db_backup['arquivo'])
            os.remove(files_backup['arquivo'])
            
            file_size = os.path.getsize(full_backup_path) / (1024 * 1024)  # MB
            
            # Limpar backups antigos
            self.cleanup_old_backups()
            
            return {
                'sucesso': True,
                'arquivo': full_backup_path,
                'timestamp': timestamp,
                'tamanho_mb': round(file_size, 2),
                'tipo': 'full',
                'metadata': metadata
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """Lista todos os backups disponíveis"""
        try:
            backups = []
            
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.zip'):
                    filepath = os.path.join(self.backup_dir, filename)
                    file_size = os.path.getsize(filepath) / (1024 * 1024)
                    modification_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    # Determinar tipo do backup
                    if filename.startswith('full_backup_'):
                        tipo = 'full'
                    elif filename.startswith('db_backup_'):
                        tipo = 'database'
                    elif filename.startswith('files_backup_'):
                        tipo = 'files'
                    else:
                        tipo = 'unknown'
                    
                    backups.append({
                        'arquivo': filename,
                        'caminho': filepath,
                        'tamanho_mb': round(file_size, 2),
                        'data_criacao': modification_time,
                        'tipo': tipo,
                        'idade_dias': (datetime.now() - modification_time).days
                    })
            
            # Ordenar por data de criação (mais recente primeiro)
            backups.sort(key=lambda x: x['data_criacao'], reverse=True)
            
            return backups
            
        except Exception as e:
            st.error(f"Erro ao listar backups: {e}")
            return []
    
    def cleanup_old_backups(self):
        """Remove backups antigos mantendo apenas os mais recentes"""
        try:
            backups = self.list_backups()
            
            if len(backups) > self.max_backups:
                # Remover backups mais antigos
                for backup in backups[self.max_backups:]:
                    os.remove(backup['caminho'])
                    
        except Exception as e:
            print(f"Erro na limpeza de backups: {e}")
    
    def restore_database(self, backup_path: str) -> Dict[str, Any]:
        """Restaura banco de dados a partir de backup"""
        try:
            # Extrair arquivo SQL do backup
            temp_dir = "temp_restore"
            os.makedirs(temp_dir, exist_ok=True)
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Encontrar arquivo SQL
            sql_files = [f for f in os.listdir(temp_dir) if f.endswith('.sql')]
            if not sql_files:
                return {'sucesso': False, 'erro': 'Arquivo SQL não encontrado no backup'}
            
            sql_file = os.path.join(temp_dir, sql_files[0])
            
            # Comando de restore
            cmd = [
                "psql",
                "--host=localhost",
                "--port=5432",
                "--username=postgres",
                "--dbname=inventario_web",
                "--file=" + sql_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Limpar arquivos temporários
            shutil.rmtree(temp_dir)
            
            if result.returncode == 0:
                return {
                    'sucesso': True,
                    'mensagem': 'Banco de dados restaurado com sucesso'
                }
            else:
                return {
                    'sucesso': False,
                    'erro': result.stderr or 'Erro desconhecido na restauração'
                }
                
        except Exception as e:
            return {
                'sucesso': False,
                'erro': str(e)
            }
    
    def schedule_automatic_backups(self):
        """Agenda backups automáticos"""
        # Backup completo diário às 2h da manhã
        schedule.every().day.at("02:00").do(self.create_full_backup)
        
        # Backup apenas do banco a cada 6 horas
        schedule.every(6).hours.do(self.create_database_backup)
        
        # Executar scheduler em thread separada (para produção)
        # Em ambiente de desenvolvimento, pode ser executado manualmente
        
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas dos backups"""
        try:
            backups = self.list_backups()
            
            if not backups:
                return {
                    'total_backups': 0,
                    'tamanho_total_mb': 0,
                    'backup_mais_recente': None,
                    'backup_mais_antigo': None
                }
            
            tamanho_total = sum(backup['tamanho_mb'] for backup in backups)
            
            return {
                'total_backups': len(backups),
                'tamanho_total_mb': round(tamanho_total, 2),
                'backup_mais_recente': backups[0],
                'backup_mais_antigo': backups[-1],
                'tipos_backup': {
                    'full': len([b for b in backups if b['tipo'] == 'full']),
                    'database': len([b for b in backups if b['tipo'] == 'database']),
                    'files': len([b for b in backups if b['tipo'] == 'files'])
                }
            }
            
        except Exception as e:
            return {'erro': str(e)}

def show_backup_recovery_page():
    """Interface do sistema de backup e recovery"""
    st.title("💾 Backup e Disaster Recovery")
    
    manager = BackupRecoveryManager()
    
    # Tabs para diferentes seções
    tab1, tab2, tab3, tab4 = st.tabs(["🔧 Criar Backup", "📋 Backups Disponíveis", "🔄 Restaurar", "📊 Estatísticas"])
    
    with tab1:
        st.header("🔧 Criar Novo Backup")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Backup Completo", help="Backup do banco + arquivos"):
                with st.spinner("Criando backup completo..."):
                    resultado = manager.create_full_backup()
                    
                    if resultado['sucesso']:
                        st.success(f"✅ Backup criado: {resultado['arquivo']}")
                        st.info(f"📊 Tamanho: {resultado['tamanho_mb']} MB")
                    else:
                        st.error(f"❌ Erro: {resultado['erro']}")
        
        with col2:
            if st.button("🗄️ Backup Banco", help="Apenas banco de dados"):
                with st.spinner("Criando backup do banco..."):
                    resultado = manager.create_database_backup()
                    
                    if resultado['sucesso']:
                        st.success(f"✅ Backup criado: {resultado['arquivo']}")
                        st.info(f"📊 Tamanho: {resultado['tamanho_mb']} MB")
                    else:
                        st.error(f"❌ Erro: {resultado['erro']}")
        
        with col3:
            if st.button("📁 Backup Arquivos", help="Apenas arquivos do sistema"):
                with st.spinner("Criando backup dos arquivos..."):
                    resultado = manager.create_files_backup()
                    
                    if resultado['sucesso']:
                        st.success(f"✅ Backup criado: {resultado['arquivo']}")
                        st.info(f"📊 Tamanho: {resultado['tamanho_mb']} MB")
                    else:
                        st.error(f"❌ Erro: {resultado['erro']}")
    
    with tab2:
        st.header("📋 Backups Disponíveis")
        
        backups = manager.list_backups()
        
        if not backups:
            st.warning("⚠️ Nenhum backup encontrado")
        else:
            # Tabela de backups
            df_backups = pd.DataFrame(backups)
            df_backups['data_criacao'] = pd.to_datetime(df_backups['data_criacao'])
            
            st.dataframe(
                df_backups[['arquivo', 'tipo', 'tamanho_mb', 'data_criacao', 'idade_dias']],
                use_container_width=True
            )
            
            # Opção de download
            st.subheader("📥 Download de Backup")
            backup_selecionado = st.selectbox(
                "Selecione um backup para download",
                options=[b['arquivo'] for b in backups]
            )
            
            if backup_selecionado:
                backup_info = next(b for b in backups if b['arquivo'] == backup_selecionado)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"📊 Tamanho: {backup_info['tamanho_mb']} MB")
                with col2:
                    st.info(f"📅 Criado: {backup_info['data_criacao'].strftime('%d/%m/%Y %H:%M')}")
                
                try:
                    with open(backup_info['caminho'], "rb") as file:
                        st.download_button(
                            label="📥 Download Backup",
                            data=file.read(),
                            file_name=backup_selecionado,
                            mime="application/zip"
                        )
                except Exception as e:
                    st.error(f"Erro ao preparar download: {e}")
    
    with tab3:
        st.header("🔄 Restaurar Sistema")
        
        st.warning("⚠️ **ATENÇÃO:** A restauração irá substituir os dados atuais!")
        
        backups = manager.list_backups()
        db_backups = [b for b in backups if b['tipo'] in ['database', 'full']]
        
        if not db_backups:
            st.error("❌ Nenhum backup de banco de dados disponível")
        else:
            backup_para_restore = st.selectbox(
                "Selecione backup para restauração",
                options=[b['arquivo'] for b in db_backups],
                key="restore"
            )
            
            if backup_para_restore:
                backup_info = next(b for b in db_backups if b['arquivo'] == backup_para_restore)
                
                st.info(f"""
                **Backup Selecionado:**
                - 📄 Arquivo: {backup_info['arquivo']}
                - 📊 Tamanho: {backup_info['tamanho_mb']} MB
                - 📅 Data: {backup_info['data_criacao'].strftime('%d/%m/%Y %H:%M')}
                - 🏷️ Tipo: {backup_info['tipo']}
                """)
                
                confirmar = st.checkbox("🔒 Confirmo que desejo restaurar este backup")
                
                if confirmar and st.button("🔄 Executar Restauração", type="primary"):
                    with st.spinner("Restaurando banco de dados..."):
                        resultado = manager.restore_database(backup_info['caminho'])
                        
                        if resultado['sucesso']:
                            st.success("✅ Banco de dados restaurado com sucesso!")
                            st.info("🔄 Recomenda-se reiniciar o sistema")
                        else:
                            st.error(f"❌ Erro na restauração: {resultado['erro']}")
    
    with tab4:
        st.header("📊 Estatísticas de Backup")
        
        stats = manager.get_backup_statistics()
        
        if 'erro' in stats:
            st.error(f"Erro ao carregar estatísticas: {stats['erro']}")
        else:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Backups", stats['total_backups'])
            
            with col2:
                st.metric("Tamanho Total", f"{stats['tamanho_total_mb']} MB")
            
            with col3:
                if stats['backup_mais_recente']:
                    dias_ultimo = stats['backup_mais_recente']['idade_dias']
                    st.metric("Último Backup", f"{dias_ultimo} dias atrás")
            
            # Gráfico de tipos de backup
            if stats['total_backups'] > 0:
                tipos = stats['tipos_backup']
                fig = px.pie(
                    values=list(tipos.values()),
                    names=list(tipos.keys()),
                    title="Distribuição por Tipo de Backup"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Configuração de backup automático
            st.subheader("⚙️ Configuração Automática")
            
            st.info("""
            **Backup Automático Configurado:**
            - 🕐 Backup completo: Diariamente às 2h
            - 🕕 Backup banco: A cada 6 horas
            - 🗑️ Limpeza automática: Mantém 30 backups
            """)
            
            if st.button("🔄 Ativar Scheduler"):
                try:
                    manager.schedule_automatic_backups()
                    st.success("✅ Scheduler de backup ativado!")
                    st.info("ℹ️ Para produção, execute em processo separado")
                except Exception as e:
                    st.error(f"Erro ao ativar scheduler: {e}")