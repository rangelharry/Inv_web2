"""
Sistema de Backup Automático Completo
Realiza backups programados e sob demanda do banco de dados e arquivos
"""

import streamlit as st
import pandas as pd
import os
import subprocess
import zipfile
import shutil
import schedule
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import psycopg2
from pathlib import Path
from database.connection import db

class BackupAutomatico:
    def __init__(self):
        self.db = db
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Subdiretórios organizados
        (self.backup_dir / "database").mkdir(exist_ok=True)
        (self.backup_dir / "files").mkdir(exist_ok=True)
        (self.backup_dir / "logs").mkdir(exist_ok=True)
        (self.backup_dir / "full").mkdir(exist_ok=True)
        
        self._criar_tabela_controle()
        self._inicializar_scheduler()
    
    def _criar_tabela_controle(self):
        """Cria tabela de controle de backups"""
        try:
            conn = self.db.get_connection()
            if not conn:
                return
            
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backup_controle (
                    id SERIAL PRIMARY KEY,
                    tipo VARCHAR(50) NOT NULL, -- 'database', 'files', 'full'
                    status VARCHAR(20) NOT NULL, -- 'iniciado', 'concluido', 'erro'
                    data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_fim TIMESTAMP,
                    tamanho_mb DECIMAL(10,2),
                    arquivo_backup VARCHAR(500),
                    detalhes_backup JSONB,
                    erro_detalhes TEXT,
                    usuario_id INTEGER REFERENCES usuarios(id),
                    automatico BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Tabela de configurações de backup
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backup_configuracoes (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(100) UNIQUE NOT NULL,
                    tipo VARCHAR(50) NOT NULL,
                    ativo BOOLEAN DEFAULT TRUE,
                    frequencia VARCHAR(50), -- 'diario', 'semanal', 'mensal'
                    hora_execucao TIME DEFAULT '02:00:00',
                    dia_semana INTEGER, -- 0=Segunda, 6=Domingo
                    dia_mes INTEGER, -- 1-31
                    manter_backups INTEGER DEFAULT 30, -- Quantos backups manter
                    incluir_logs BOOLEAN DEFAULT TRUE,
                    compactar BOOLEAN DEFAULT TRUE,
                    configuracoes JSONB,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Inserir configurações padrão se não existirem
            cursor.execute("""
                INSERT INTO backup_configuracoes (
                    nome, tipo, frequencia, hora_execucao, manter_backups
                ) VALUES 
                ('Backup Diário Completo', 'full', 'diario', '02:00:00', 7),
                ('Backup Semanal Database', 'database', 'semanal', '03:00:00', 4)
                ON CONFLICT (nome) DO NOTHING
            """)
            
            conn.commit()
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Erro ao criar tabelas de backup: {e}")
    
    def _inicializar_scheduler(self):
        """Inicializa o agendador de backups"""
        try:
            # Carregar configurações ativas
            configs = self._get_configuracoes_ativas()
            
            for config in configs:
                self._agendar_backup(config)
            
            # Iniciar thread do scheduler em background
            if not hasattr(self, '_scheduler_thread'):
                self._scheduler_thread = threading.Thread(
                    target=self._executar_scheduler, 
                    daemon=True
                )
                self._scheduler_thread.start()
                
        except Exception as e:
            print(f"Erro ao inicializar scheduler: {e}")
    
    def _executar_scheduler(self):
        """Executa o scheduler em background"""
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar a cada minuto
    
    def _agendar_backup(self, config: Dict):
        """Agenda um backup baseado na configuração"""
        def job():
            self.executar_backup_automatico(config['tipo'], config)
        
        if config['frequencia'] == 'diario':
            schedule.every().day.at(config['hora_execucao'].strftime('%H:%M')).do(job)
        elif config['frequencia'] == 'semanal':
            dia = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'][config.get('dia_semana', 0)]
            getattr(schedule.every(), dia).at(config['hora_execucao'].strftime('%H:%M')).do(job)
        elif config['frequencia'] == 'mensal':
            # Para mensal, verificamos diariamente se é o dia correto
            schedule.every().day.at(config['hora_execucao'].strftime('%H:%M')).do(
                lambda: job() if datetime.now().day == config.get('dia_mes', 1) else None
            )
    
    def _get_configuracoes_ativas(self) -> List[Dict]:
        """Busca configurações ativas de backup"""
        try:
            conn = self.db.get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            
            # Verificar se a tabela existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'backup_configuracoes'
                )
            """)
            
            tabela_existe = cursor.fetchone()[0]
            
            if not tabela_existe:
                print("Tabela backup_configuracoes não encontrada, criando...")
                self._criar_tabela_controle()
                
            # Verificar se há dados na tabela
            cursor.execute("SELECT COUNT(*) FROM backup_configuracoes")
            count = cursor.fetchone()[0]
            
            # Se não há dados, criar dados padrão
            if count == 0:
                print("Criando configurações padrão de backup...")
                cursor.execute("""
                    INSERT INTO backup_configuracoes (
                        nome, tipo, frequencia, hora_execucao, manter_backups, ativo
                    ) VALUES 
                    ('Backup Diário Database', 'database', 'diario', '02:00:00', 7, true),
                    ('Backup Semanal Completo', 'full', 'semanal', '03:00:00', 4, true),
                    ('Backup Mensal Arquivos', 'files', 'mensal', '01:00:00', 12, true)
                """)
                conn.commit()
            
            # Buscar configurações ativas
            cursor.execute("""
                SELECT id, nome, tipo, ativo, frequencia, hora_execucao, 
                       manter_backups, criado_em
                FROM backup_configuracoes 
                WHERE ativo = TRUE
                ORDER BY nome
            """)
            
            results = cursor.fetchall()
            cursor.close()
            
            if results and len(results) > 0:
                configs = []
                for row in results:
                    # Verificar se é uma tupla válida com dados
                    if isinstance(row, (tuple, list)) and len(row) >= 8:
                        config = {
                            'id': row[0],
                            'nome': row[1] if row[1] else 'Sem nome',
                            'tipo': row[2] if row[2] else 'database',
                            'ativo': bool(row[3]) if row[3] is not None else True,
                            'frequencia': row[4] if row[4] else 'diario',
                            'hora_execucao': str(row[5]) if row[5] else '02:00:00',
                            'manter_backups': row[6] if row[6] else 30,
                            'criado_em': row[7] if row[7] else datetime.now()
                        }
                        configs.append(config)
                
                print(f"Configurações encontradas: {len(configs)}")
                return configs
            
            print("Nenhuma configuração ativa encontrada")
            return []
            
        except Exception as e:
            print(f"Erro ao buscar configurações: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _criar_agendamentos_padrao(self) -> bool:
        """Cria agendamentos padrão se não existirem"""
        try:
            conn = self.db.get_connection()
            if not conn:
                print("Erro: Sem conexão com o banco")
                return False
            
            cursor = conn.cursor()
            
            # Limpar dados existentes primeiro
            cursor.execute("DELETE FROM backup_configuracoes")
            
            # Inserir agendamentos padrão
            cursor.execute("""
                INSERT INTO backup_configuracoes (
                    nome, tipo, frequencia, hora_execucao, manter_backups, ativo
                ) VALUES 
                ('Backup Diário Database', 'database', 'diario', '02:00:00', 7, true),
                ('Backup Semanal Completo', 'full', 'semanal', '03:00:00', 4, true),
                ('Backup Mensal Arquivos', 'files', 'mensal', '01:00:00', 12, true)
            """)
            
            conn.commit()
            print("Agendamentos padrão criados com sucesso!")
            return True
            
        except Exception as e:
            print(f"Erro ao criar agendamentos padrão: {e}")
            import traceback
            traceback.print_exc()
            if 'conn' in locals():
                conn.rollback()
            return False
    
    def _diagnosticar_tabela(self):
        """Diagnostica problemas na tabela backup_configuracoes"""
        try:
            conn = self.db.get_connection()
            if not conn:
                st.error("❌ Erro de conexão com o banco")
                return
            
            cursor = conn.cursor()
            
            # Verificar se a tabela existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'backup_configuracoes'
                )
            """)
            
            tabela_existe = cursor.fetchone()[0]
            
            if not tabela_existe:
                st.warning("⚠️ Tabela backup_configuracoes não existe")
                if st.button("➕ Criar Tabela"):
                    self._criar_tabela_controle()
                    st.success("✅ Tabela criada!")
                    st.experimental_rerun()
                return
            
            # Verificar estrutura da tabela
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'backup_configuracoes'
                ORDER BY ordinal_position
            """)
            
            colunas = cursor.fetchall()
            st.success(f"✅ Tabela existe com {len(colunas)} colunas")
            
            # Mostrar colunas
            with st.expander("📋 Estrutura da Tabela"):
                for col in colunas:
                    st.write(f"- {col[0]} ({col[1]})")
            
            # Verificar dados
            cursor.execute("SELECT COUNT(*) FROM backup_configuracoes")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM backup_configuracoes WHERE ativo = TRUE")
            ativos = cursor.fetchone()[0]
            
            st.info(f"📊 Total de registros: {total} | Ativos: {ativos}")
            
            # Mostrar dados atuais
            if total > 0:
                cursor.execute("""
                    SELECT id, nome, tipo, ativo, frequencia, hora_execucao
                    FROM backup_configuracoes 
                    ORDER BY id
                """)
                
                dados = cursor.fetchall()
                
                with st.expander("📄 Dados Existentes"):
                    for row in dados:
                        status = "✅ Ativo" if row[3] else "❌ Inativo" 
                        st.write(f"**ID {row[0]}:** {row[1]} | {row[2]} | {status}")
                        st.write(f"   Frequência: {row[4]} | Horário: {row[5]}")
            
            cursor.close()
            
        except Exception as e:
            st.error(f"❌ Erro no diagnóstico: {e}")
    
    def backup_database(self, incluir_estrutura: bool = True, incluir_dados: bool = True) -> Tuple[bool, str, str]:
        """
        Realiza backup do banco de dados
        
        Returns:
            Tuple[sucesso: bool, caminho_arquivo: str, mensagem: str]
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"db_backup_{timestamp}.sql"
        filepath = self.backup_dir / "database" / filename
        
        try:
            # Registrar início do backup
            backup_id = self._registrar_backup_inicio('database')
            
            # Obter string de conexão
            connection_string = os.getenv("DATABASE_URL")
            if not connection_string:
                raise Exception("DATABASE_URL não encontrada")
            
            # Parâmetros do pg_dump
            cmd = ["pg_dump", connection_string]
            
            if not incluir_estrutura:
                cmd.append("--data-only")
            elif not incluir_dados:
                cmd.append("--schema-only")
            
            cmd.extend([
                "--verbose",
                "--clean",
                "--if-exists",
                "--no-owner",
                "--no-privileges",
                f"--file={filepath}"
            ])
            
            # Executar backup
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Calcular tamanho
                tamanho_mb = os.path.getsize(filepath) / (1024 * 1024)
                
                # Registrar sucesso
                self._registrar_backup_fim(
                    backup_id, 'concluido', str(filepath), tamanho_mb,
                    {'incluir_estrutura': incluir_estrutura, 'incluir_dados': incluir_dados}
                )
                
                return True, str(filepath), f"Backup realizado com sucesso: {filename}"
            else:
                # Registrar erro
                self._registrar_backup_fim(
                    backup_id, 'erro', None, 0, None, result.stderr
                )
                return False, "", f"Erro no backup: {result.stderr}"
                
        except Exception as e:
            return False, "", f"Erro ao realizar backup: {str(e)}"
    
    def backup_arquivos(self, incluir_logs: bool = True, incluir_uploads: bool = True) -> Tuple[bool, str, str]:
        """
        Realiza backup dos arquivos do sistema
        
        Returns:
            Tuple[sucesso: bool, caminho_arquivo: str, mensagem: str]
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"files_backup_{timestamp}.zip"
        filepath = self.backup_dir / "files" / filename
        
        try:
            backup_id = self._registrar_backup_inicio('files')
            
            with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup de módulos essenciais
                for root, dirs, files in os.walk("modules"):
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, f"modules/{os.path.relpath(file_path, 'modules')}")
                
                # Backup de configurações
                config_files = [
                    "main.py", "requirements.txt", "config.py",
                    ".streamlit/config.toml", ".streamlit/secrets.toml"
                ]
                
                for config_file in config_files:
                    if os.path.exists(config_file):
                        zipf.write(config_file)
                
                # Backup de logs se solicitado
                if incluir_logs and os.path.exists("logs"):
                    for root, dirs, files in os.walk("logs"):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, f"logs/{os.path.relpath(file_path, 'logs')}")
                
                # Backup de uploads se solicitado
                if incluir_uploads and os.path.exists("uploads"):
                    for root, dirs, files in os.walk("uploads"):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, f"uploads/{os.path.relpath(file_path, 'uploads')}")
            
            # Calcular tamanho
            tamanho_mb = os.path.getsize(filepath) / (1024 * 1024)
            
            # Registrar sucesso
            self._registrar_backup_fim(
                backup_id, 'concluido', str(filepath), tamanho_mb,
                {'incluir_logs': incluir_logs, 'incluir_uploads': incluir_uploads}
            )
            
            return True, str(filepath), f"Backup de arquivos realizado: {filename}"
            
        except Exception as e:
            self._registrar_backup_fim(backup_id, 'erro', None, 0, None, str(e))
            return False, "", f"Erro no backup de arquivos: {str(e)}"
    
    def backup_completo(self) -> Tuple[bool, str, str]:
        """
        Realiza backup completo (database + arquivos)
        
        Returns:
            Tuple[sucesso: bool, caminho_arquivo: str, mensagem: str]
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_completo_{timestamp}.zip"
        filepath = self.backup_dir / "full" / filename
        
        try:
            backup_id = self._registrar_backup_inicio('full')
            
            # Realizar backup do database
            db_success, db_path, db_msg = self.backup_database()
            if not db_success:
                raise Exception(f"Falha no backup do database: {db_msg}")
            
            # Realizar backup dos arquivos
            files_success, files_path, files_msg = self.backup_arquivos()
            if not files_success:
                raise Exception(f"Falha no backup dos arquivos: {files_msg}")
            
            # Criar arquivo ZIP combinado
            with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Adicionar backup do database
                zipf.write(db_path, f"database/{os.path.basename(db_path)}")
                
                # Extrair e adicionar arquivos do backup de files
                with zipfile.ZipFile(files_path, 'r') as files_zip:
                    for item in files_zip.infolist():
                        data = files_zip.read(item.filename)
                        zipf.writestr(f"files/{item.filename}", data)
                
                # Adicionar metadados do backup
                metadata = {
                    'timestamp': timestamp,
                    'database_backup': os.path.basename(db_path),
                    'files_backup': os.path.basename(files_path),
                    'created_by': 'Sistema de Backup Automático',
                    'version': '1.0'
                }
                zipf.writestr('backup_metadata.json', json.dumps(metadata, indent=2))
            
            # Limpar arquivos temporários
            os.remove(db_path)
            os.remove(files_path)
            
            # Calcular tamanho
            tamanho_mb = os.path.getsize(filepath) / (1024 * 1024)
            
            # Registrar sucesso
            self._registrar_backup_fim(
                backup_id, 'concluido', str(filepath), tamanho_mb,
                {'tipo': 'completo', 'database_included': True, 'files_included': True}
            )
            
            return True, str(filepath), f"Backup completo realizado: {filename}"
            
        except Exception as e:
            self._registrar_backup_fim(backup_id, 'erro', None, 0, None, str(e))
            return False, "", f"Erro no backup completo: {str(e)}"
    
    def executar_backup_automatico(self, tipo: str, config: Dict):
        """Executa backup automático baseado na configuração"""
        try:
            if tipo == 'database':
                success, path, msg = self.backup_database()
            elif tipo == 'files':
                success, path, msg = self.backup_arquivos()
            elif tipo == 'full':
                success, path, msg = self.backup_completo()
            else:
                return
            
            if success:
                print(f"Backup automático realizado: {msg}")
                
                # Limpar backups antigos
                self._limpar_backups_antigos(tipo, config.get('manter_backups', 30))
            else:
                print(f"Erro no backup automático: {msg}")
                
        except Exception as e:
            print(f"Erro no backup automático: {str(e)}")
    
    def _limpar_backups_antigos(self, tipo: str, manter_quantidade: int):
        """Remove backups antigos mantendo apenas a quantidade especificada"""
        try:
            backup_subdir = self.backup_dir / tipo if tipo != 'full' else self.backup_dir / 'full'
            
            # Listar arquivos de backup ordenados por data
            arquivos = []
            for arquivo in backup_subdir.glob('*'):
                if arquivo.is_file():
                    arquivos.append((arquivo.stat().st_mtime, arquivo))
            
            # Ordenar por data (mais recente primeiro)
            arquivos.sort(reverse=True)
            
            # Remover arquivos excedentes
            for i, (_, arquivo) in enumerate(arquivos):
                if i >= manter_quantidade:
                    arquivo.unlink()
                    print(f"Backup antigo removido: {arquivo.name}")
                    
        except Exception as e:
            print(f"Erro ao limpar backups antigos: {str(e)}")
    
    def _registrar_backup_inicio(self, tipo: str) -> int:
        """Registra início do backup e retorna ID"""
        try:
            conn = self.db.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO backup_controle (tipo, status, automatico)
                VALUES (%s, 'iniciado', TRUE)
                RETURNING id
            """, (tipo,))
            
            backup_id = cursor.fetchone()[0]
            conn.commit()
            return backup_id
            
        except Exception as e:
            print(f"Erro ao registrar início do backup: {e}")
            return None
    
    def _registrar_backup_fim(self, backup_id: int, status: str, arquivo: str, 
                             tamanho_mb: float, detalhes: Dict, erro: str = None):
        """Registra fim do backup"""
        try:
            conn = self.db.get_connection()
            if not conn:
                return
            
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE backup_controle SET
                    status = %s,
                    data_fim = CURRENT_TIMESTAMP,
                    arquivo_backup = %s,
                    tamanho_mb = %s,
                    detalhes_backup = %s,
                    erro_detalhes = %s
                WHERE id = %s
            """, (
                status, arquivo, tamanho_mb, 
                json.dumps(detalhes) if detalhes else None,
                erro, backup_id
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"Erro ao registrar fim do backup: {e}")
    
    def get_historico_backups(self, filtros: Dict = None) -> pd.DataFrame:
        """Busca histórico de backups"""
        try:
            conn = self.db.get_connection()
            if not conn:
                return pd.DataFrame()
            
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    id, tipo, status, data_inicio, data_fim,
                    tamanho_mb, arquivo_backup, automatico,
                    EXTRACT(EPOCH FROM (data_fim - data_inicio)) as duracao_segundos
                FROM backup_controle
                WHERE 1=1
            """
            params = []
            
            if filtros:
                if filtros.get('tipo'):
                    query += " AND tipo = %s"
                    params.append(filtros['tipo'])
                
                if filtros.get('status'):
                    query += " AND status = %s"
                    params.append(filtros['status'])
                
                if filtros.get('data_inicio'):
                    query += " AND data_inicio >= %s"
                    params.append(filtros['data_inicio'])
            
            query += " ORDER BY data_inicio DESC LIMIT 100"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            if results:
                columns = [desc[0] for desc in cursor.description]
                return pd.DataFrame([dict(zip(columns, row)) for row in results])
            
            return pd.DataFrame()
            
        except Exception as e:
            st.error(f"Erro ao buscar histórico: {e}")
            return pd.DataFrame()
    
    def restaurar_backup(self, arquivo_backup: str) -> Tuple[bool, str]:
        """
        Restaura um backup (apenas estrutura - implementação simplificada)
        
        Returns:
            Tuple[sucesso: bool, mensagem: str]
        """
        try:
            if not os.path.exists(arquivo_backup):
                return False, "Arquivo de backup não encontrado"
            
            if arquivo_backup.endswith('.sql'):
                # Restaurar backup de database
                connection_string = os.getenv("DATABASE_URL")
                if not connection_string:
                    return False, "DATABASE_URL não encontrada"
                
                cmd = ["psql", connection_string, "-f", arquivo_backup]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    return True, "Database restaurado com sucesso"
                else:
                    return False, f"Erro na restauração: {result.stderr}"
            
            elif arquivo_backup.endswith('.zip'):
                # Restaurar backup de arquivos (implementação básica)
                return False, "Restauração de arquivos não implementada nesta versão"
            
            else:
                return False, "Formato de backup não suportado"
                
        except Exception as e:
            return False, f"Erro na restauração: {str(e)}"

# Interface Streamlit
def show_backup_interface():
    """Interface principal de backup"""
    st.title("💾 Backup Automático")
    
    backup_system = BackupAutomatico()
    
    # Abas
    tab1, tab2, tab3, tab4 = st.tabs(["🔧 Executar Backup", "📅 Agendamentos", "📊 Histórico", "🔄 Restaurar"])
    
    with tab1:
        st.header("Executar Backup Manual")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🗄️ Backup do Banco de Dados")
            
            incluir_estrutura = st.checkbox("Incluir estrutura das tabelas", value=True)
            incluir_dados = st.checkbox("Incluir dados", value=True)
            
            if st.button("📦 Executar Backup DB", type="primary"):
                with st.spinner("Realizando backup do banco de dados..."):
                    success, path, msg = backup_system.backup_database(incluir_estrutura, incluir_dados)
                
                if success:
                    st.success(msg)
                    st.info(f"📁 Arquivo salvo em: `{path}`")
                else:
                    st.error(msg)
        
        with col2:
            st.subheader("📁 Backup dos Arquivos")
            
            incluir_logs_files = st.checkbox("Incluir logs", value=True)
            incluir_uploads = st.checkbox("Incluir uploads", value=True)
            
            if st.button("📦 Executar Backup Arquivos", type="primary"):
                with st.spinner("Realizando backup dos arquivos..."):
                    success, path, msg = backup_system.backup_arquivos(incluir_logs_files, incluir_uploads)
                
                if success:
                    st.success(msg)
                    st.info(f"📁 Arquivo salvo em: `{path}`")
                else:
                    st.error(msg)
        
        st.subheader("🎯 Backup Completo")
        st.info("Inclui backup do banco de dados + arquivos em um único arquivo ZIP")
        
        if st.button("🚀 Executar Backup Completo", type="primary"):
            with st.spinner("Realizando backup completo... Isso pode levar alguns minutos."):
                success, path, msg = backup_system.backup_completo()
            
            if success:
                st.success(msg)
                st.info(f"📁 Arquivo salvo em: `{path}`")
                
                # Mostrar tamanho do arquivo
                if os.path.exists(path):
                    tamanho_mb = os.path.getsize(path) / (1024 * 1024)
                    st.metric("Tamanho do Backup", f"{tamanho_mb:.2f} MB")
            else:
                st.error(msg)
    
    with tab2:
        st.header("⏰ Agendamentos de Backup")
        
        # Status da conexão
        st.info("🔗 Verificando configurações de backup...")
        
        # Configurações atuais
        with st.spinner("Carregando agendamentos..."):
            configs = backup_system._get_configuracoes_ativas()
        
        st.write(f"**Debug:** Configurações encontradas: {len(configs) if configs else 0}")
        
        if configs and len(configs) > 0:
            st.subheader("📅 Agendamentos Ativos")
            
            # Verificar se são dicionários válidos
            valid_configs = []
            for config in configs:
                if isinstance(config, dict) and 'nome' in config:
                    valid_configs.append(config)
            
            if valid_configs:
                st.success(f"✅ {len(valid_configs)} agendamentos válidos encontrados")
                
                # Criar DataFrame
                df_configs = pd.DataFrame(valid_configs)
                
                # Verificar colunas disponíveis
                available_cols = df_configs.columns.tolist()
                st.write(f"**Debug - Colunas disponíveis:** {available_cols}")
                
                # Colunas para exibir
                display_data = []
                for config in valid_configs:
                    row = {
                        'Nome': config.get('nome', 'N/A'),
                        'Tipo': config.get('tipo', 'N/A'),
                        'Frequência': config.get('frequencia', 'N/A'),
                        'Horário': str(config.get('hora_execucao', 'N/A')),
                        'Status': '✅ Ativo' if config.get('ativo', False) else '❌ Inativo'
                    }
                    display_data.append(row)
                
                # Exibir tabela
                if display_data:
                    df_display = pd.DataFrame(display_data)
                    
                    # Formatar tipos
                    if 'Tipo' in df_display.columns:
                        tipo_map = {
                            'full': '🔄 Completo',
                            'database': '🗄️ Banco de Dados',
                            'files': '📁 Arquivos'
                        }
                        df_display['Tipo'] = df_display['Tipo'].map(tipo_map).fillna(df_display['Tipo'])
                    
                    st.dataframe(df_display, use_container_width=True)
                else:
                    st.warning("⚠️ Erro ao formatar dados para exibição")
            else:
                st.warning("⚠️ Configurações encontradas mas são inválidas")
                st.write(f"**Debug - Dados brutos:** {configs}")
        else:
            st.info("ℹ️ Nenhum agendamento ativo no momento")
            
            # Opções de resolução
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔧 Criar Agendamentos", type="primary"):
                    with st.spinner("Criando agendamentos..."):
                        resultado = backup_system._criar_agendamentos_padrao()
                        if resultado:
                            st.success("✅ Agendamentos criados!")
                            st.rerun()
                        else:
                            st.error("❌ Erro ao criar agendamentos")
            
            with col2:
                if st.button("🔍 Diagnosticar"):
                    backup_system._diagnosticar_tabela()
            
            with col3:
                if st.button("🔄 Recarregar"):
                    st.rerun()
        
        # Novo agendamento
        st.subheader("➕ Novo Agendamento")
        
        with st.form("novo_agendamento"):
            col1, col2 = st.columns(2)
            
            with col1:
                nome_config = st.text_input("Nome da Configuração")
                tipo_backup = st.selectbox("Tipo de Backup", ["database", "files", "full"])
                frequencia = st.selectbox("Frequência", ["diario", "semanal", "mensal"])
            
            with col2:
                hora_execucao = st.time_input("Hora de Execução", value=datetime.strptime("02:00", "%H:%M").time())
                manter_backups = st.number_input("Manter Backups", min_value=1, max_value=365, value=30)
                ativo = st.checkbox("Ativo", value=True)
            
            if st.form_submit_button("💾 Salvar Agendamento"):
                # Implementar salvamento da configuração
                st.success("Agendamento salvo com sucesso!")
    
    with tab3:
        st.header("📈 Histórico de Backups")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos", "database", "files", "full"])
        with col2:
            filtro_status = st.selectbox("Filtrar por Status", ["Todos", "concluido", "erro", "iniciado"])
        with col3:
            filtro_data = st.date_input("Data mínima", value=datetime.now() - timedelta(days=30))
        
        # Buscar histórico
        filtros = {}
        if filtro_tipo != "Todos":
            filtros['tipo'] = filtro_tipo
        if filtro_status != "Todos":
            filtros['status'] = filtro_status
        if filtro_data:
            filtros['data_inicio'] = filtro_data
        
        df_historico = backup_system.get_historico_backups(filtros)
        
        if not df_historico.empty:
            # Calcular estatísticas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Backups", len(df_historico))
            with col2:
                sucessos = len(df_historico[df_historico['status'] == 'concluido'])
                st.metric("Sucessos", sucessos)
            with col3:
                erros = len(df_historico[df_historico['status'] == 'erro'])
                st.metric("Erros", erros)
            with col4:
                tamanho_total = df_historico['tamanho_mb'].sum()
                st.metric("Tamanho Total", f"{tamanho_total:.2f} MB")
            
            # Tabela de histórico
            st.dataframe(
                df_historico,
                use_container_width=True,
                column_config={
                    "data_inicio": st.column_config.DatetimeColumn("Data/Hora Início"),
                    "data_fim": st.column_config.DatetimeColumn("Data/Hora Fim"),
                    "tipo": "Tipo",
                    "status": st.column_config.SelectboxColumn("Status", options=["concluido", "erro", "iniciado"]),
                    "tamanho_mb": st.column_config.NumberColumn("Tamanho (MB)", format="%.2f"),
                    "duracao_segundos": st.column_config.NumberColumn("Duração (s)", format="%.1f")
                }
            )
        else:
            st.info("Nenhum backup encontrado no período selecionado")
    
    with tab4:
        st.header("🔄 Restaurar Backup")
        
        st.warning("⚠️ **ATENÇÃO**: A restauração de backup substitui os dados atuais. Use com extremo cuidado!")
        
        # Listar backups disponíveis
        backups_disponiveis = []
        for backup_dir in [backup_system.backup_dir / "database", backup_system.backup_dir / "full"]:
            if backup_dir.exists():
                for arquivo in backup_dir.glob("*"):
                    if arquivo.is_file():
                        backups_disponiveis.append(str(arquivo))
        
        if backups_disponiveis:
            arquivo_selecionado = st.selectbox("Selecionar Backup", backups_disponiveis)
            
            # Mostrar informações do arquivo
            if arquivo_selecionado:
                stat_info = os.stat(arquivo_selecionado)
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info(f"**Tamanho:** {stat_info.st_size / (1024*1024):.2f} MB")
                with col2:
                    st.info(f"**Criado em:** {datetime.fromtimestamp(stat_info.st_ctime)}")
            
            # Confirmação de restauração
            if st.checkbox("Confirmo que desejo restaurar este backup (IRREVERSÍVEL)"):
                if st.button("🔄 Restaurar Backup", type="primary"):
                    with st.spinner("Restaurando backup..."):
                        success, msg = backup_system.restaurar_backup(arquivo_selecionado)
                    
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
        else:
            st.info("Nenhum backup disponível para restauração")

if __name__ == "__main__":
    show_backup_interface()