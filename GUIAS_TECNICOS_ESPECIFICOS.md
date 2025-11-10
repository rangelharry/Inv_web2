# 🛠️ GUIAS TÉCNICOS ESPECÍFICOS
## Cenários de Uso e Implementação - Sistema de Inventário Web

---

## 📋 ÍNDICE

1. [Guia de Implementação](#implementacao)
2. [Configuração de Ambiente](#ambiente)
3. [Cenários de Uso Comum](#cenarios)
4. [Troubleshooting](#troubleshooting)
5. [Manutenção e Backup](#manutencao)
6. [Customização](#customizacao)
7. [Integração com ERPs](#erp)
8. [Migração de Dados](#migracao)

---

## 🚀 GUIA DE IMPLEMENTAÇÃO {#implementacao}

### 🎯 **Pré-requisitos do Sistema:**

#### **💻 Hardware Mínimo:**
```
📊 ESPECIFICAÇÕES MÍNIMAS:
├── 🖥️ CPU: 2 cores, 2.0 GHz
├── 💾 RAM: 4 GB
├── 💽 Storage: 20 GB SSD
├── 🌐 Internet: 10 Mbps
└── 👥 Usuários: Até 10 simultâneos

📊 ESPECIFICAÇÕES RECOMENDADAS:
├── 🖥️ CPU: 4 cores, 3.0 GHz
├── 💾 RAM: 8 GB
├── 💽 Storage: 100 GB SSD
├── 🌐 Internet: 50 Mbps
└── 👥 Usuários: Até 50 simultâneos
```

#### **🔧 Software Necessário:**

```bash
# 1. Python 3.11+ (OBRIGATÓRIO)
python --version
# Deve retornar: Python 3.11.0 ou superior

# 2. Git (para deployment)
git --version

# 3. PostgreSQL (se local) ou acesso ao Neon
psql --version
```

### 📦 **Instalação Passo-a-Passo:**

#### **🚀 Método 1: Instalação Completa**

```bash
# 1. Clone o repositório
git clone [URL_DO_REPOSITORIO]
cd sistema-inventario

# 2. Criar ambiente virtual
python -m venv venv

# 3. Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Instalar dependências
pip install -r requirements.txt

# 5. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# 6. Configurar banco de dados
python setup_database.py

# 7. Criar usuário administrador inicial
python create_admin_user.py

# 8. Executar aplicação
streamlit run main.py
```

#### **🔧 Configuração do Banco:**

```python
# setup_database.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def setup_database():
    """
    CONFIGURAÇÃO AUTOMÁTICA DO BANCO:
    
    1. Conectar ao PostgreSQL
    2. Criar tabelas necessárias
    3. Inserir dados padrão
    4. Configurar índices
    5. Validar instalação
    """
    
    # Conectar ao banco
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432)
    )
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Criar tabelas
    tables_sql = [
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            perfil TEXT DEFAULT 'usuario',
            ativo BOOLEAN DEFAULT true,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # ... outras tabelas
    ]
    
    for sql in tables_sql:
        cursor.execute(sql)
    
    # Criar índices
    indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email)",
        "CREATE INDEX IF NOT EXISTS idx_insumos_codigo ON insumos(codigo)",
        # ... outros índices
    ]
    
    for sql in indexes_sql:
        cursor.execute(sql)
    
    conn.commit()
    print("✅ Banco de dados configurado com sucesso!")

if __name__ == "__main__":
    setup_database()
```

---

## ⚙️ CONFIGURAÇÃO DE AMBIENTE {#ambiente}

### 🔐 **Arquivo .env (Configurações):**

```bash
# .env - CONFIGURAÇÕES DO SISTEMA

# ============ BANCO DE DADOS ============
DB_HOST=ep-billowing-lake-a54qm9qo.us-east-2.aws.neon.tech
DB_NAME=sistema_inventario
DB_USER=sistema_inventario_owner
DB_PASSWORD=sua_senha_aqui
DB_PORT=5432

# ============ APLICAÇÃO ============
APP_NAME=Sistema de Inventário Web
APP_VERSION=1.0.0
DEBUG_MODE=False
SECRET_KEY=sua_chave_secreta_super_forte_aqui

# ============ STREAMLIT ============
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# ============ SEGURANÇA ============
BCRYPT_ROUNDS=12
SESSION_TIMEOUT_HOURS=8
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_TIME_MINUTES=15

# ============ EMAIL (OPCIONAL) ============
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_de_app
EMAIL_FROM=sistema@suaempresa.com.br

# ============ BACKUP ============
BACKUP_FREQUENCY_HOURS=24
BACKUP_RETENTION_DAYS=30
BACKUP_PATH=/backup/inventario/

# ============ LOGS ============
LOG_LEVEL=INFO
LOG_FILE=logs/sistema.log
LOG_MAX_SIZE_MB=100
LOG_BACKUP_COUNT=5

# ============ PERFORMANCE ============
CACHE_TTL_SECONDS=300
MAX_CONNECTIONS_POOL=20
QUERY_TIMEOUT_SECONDS=30

# ============ FEATURES ============
ENABLE_API=True
ENABLE_WEBHOOKS=True
ENABLE_PREDICTIONS=True
ENABLE_ADVANCED_REPORTS=True
```

### 🎛️ **Configuração Streamlit:**

```toml
# .streamlit/config.toml
[global]
developmentMode = false
showWarningOnDirectExecution = false

[server]
port = 8501
enableCORS = true
enableXsrfProtection = true
maxUploadSize = 50

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[logger]
level = "info"
messageFormat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

---

## 🎯 CENÁRIOS DE USO COMUM {#cenarios}

### 🏗️ **Cenário 1: Empresa de Construção Civil**

#### **📋 Configuração Específica:**

```python
# config/construcao_civil.py
CONFIGURACAO_CONSTRUCAO = {
    "categorias_insumos": [
        "Cimento e Argamassa",
        "Materiais Hidráulicos",
        "Materiais Elétricos",
        "Ferragens",
        "Madeiras",
        "Tintas e Vernizes",
        "Equipamentos de Segurança"
    ],
    
    "tipos_movimentacao": [
        "Saída para Obra",
        "Retorno de Obra",
        "Transferência entre Obras",
        "Consumo Direto",
        "Devolução para Fornecedor"
    ],
    
    "campos_adicionais": {
        "insumos": ["numero_obra", "responsavel_obra", "centro_custo"],
        "movimentacoes": ["obra_origem", "obra_destino", "veiculo_transporte"]
    },
    
    "relatorios_especificos": [
        "Consumo por Obra",
        "Transferências entre Obras",
        "Custo de Material por m²",
        "Análise de Desperdício",
        "Previsão de Compras por Obra"
    ]
}

def configurar_empresa_construcao():
    """
    IMPLEMENTAÇÃO PARA CONSTRUÇÃO CIVIL:
    
    1. Criar categorias específicas
    2. Configurar campos de obra
    3. Setup de relatórios especializados
    4. Configurar alertas de projeto
    """
    
    # Inserir categorias padrão
    for categoria in CONFIGURACAO_CONSTRUCAO["categorias_insumos"]:
        db.execute("""
            INSERT INTO categorias_insumos (nome, ativo) 
            VALUES (%s, true) ON CONFLICT DO NOTHING
        """, (categoria,))
    
    # Configurar campos customizados
    add_custom_fields("insumos", CONFIGURACAO_CONSTRUCAO["campos_adicionais"]["insumos"])
    
    print("✅ Configuração para Construção Civil aplicada!")
```

#### **📊 Dashboard Específico:**

```python
def dashboard_construcao_civil():
    """
    DASHBOARD ESPECIALIZADO - CONSTRUÇÃO CIVIL
    """
    
    st.title("🏗️ Dashboard - Construção Civil")
    
    # Métricas por Obra
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_obras = get_total_obras_ativas()
        st.metric("Obras Ativas", total_obras)
    
    with col2:
        consumo_mes = get_consumo_total_mes()
        st.metric("Consumo Mês", f"R$ {consumo_mes:,.2f}")
    
    with col3:
        materiais_criticos = get_materiais_criticos()
        st.metric("Materiais Críticos", materiais_criticos, delta=-2)
    
    with col4:
        economia_mes = get_economia_mes()
        st.metric("Economia Mês", f"R$ {economia_mes:,.2f}", delta=economia_mes)
    
    # Gráfico de Consumo por Obra
    fig_consumo = create_chart_consumo_por_obra()
    st.plotly_chart(fig_consumo, use_container_width=True)
    
    # Top 5 Materiais Mais Consumidos
    col_left, col_right = st.columns(2)
    
    with col_left:
        top_materiais = get_top_materiais_consumidos()
        st.subheader("🔝 Top 5 Materiais")
        for material in top_materiais:
            st.write(f"• {material['nome']}: {material['quantidade']} {material['unidade']}")
    
    with col_right:
        obras_alertas = get_obras_com_alertas()
        st.subheader("⚠️ Obras com Alertas")
        for obra in obras_alertas:
            st.warning(f"**{obra['nome']}**: {obra['alerta']}")
```

### 🏭 **Cenário 2: Indústria Manufatureira**

#### **⚙️ Configuração Industrial:**

```python
CONFIGURACAO_INDUSTRIA = {
    "tipos_equipamento": [
        "Máquinas de Produção",
        "Equipamentos de Teste",
        "Ferramentas de Precisão",
        "Instrumentos de Medição",
        "Equipamentos de Segurança"
    ],
    
    "status_equipamento": [
        "Operacional",
        "Manutenção Preventiva",
        "Manutenção Corretiva", 
        "Calibração",
        "Fora de Operação"
    ],
    
    "campos_manutencao": [
        "proxima_manutencao",
        "horas_operacao",
        "ultima_calibracao",
        "certificado_calibracao"
    ],
    
    "alertas_especiais": {
        "calibracao_vencendo": 30,  # dias
        "manutencao_atrasada": 7,   # dias
        "horas_limite": 8000        # horas
    }
}

def setup_industria():
    """
    CONFIGURAÇÃO PARA INDÚSTRIA MANUFATUREIRA:
    
    - Controle rigoroso de calibração
    - Rastreabilidade completa
    - Alertas de manutenção
    - Gestão de vida útil
    """
    
    # Adicionar campos de manutenção
    alter_statements = [
        """
        ALTER TABLE equipamentos_eletricos 
        ADD COLUMN IF NOT EXISTS proxima_manutencao DATE,
        ADD COLUMN IF NOT EXISTS horas_operacao INTEGER DEFAULT 0,
        ADD COLUMN IF NOT EXISTS ultima_calibracao DATE,
        ADD COLUMN IF NOT EXISTS certificado_calibracao TEXT
        """,
        """
        CREATE TABLE IF NOT EXISTS historico_manutencao (
            id SERIAL PRIMARY KEY,
            equipamento_id INTEGER,
            tipo_manutencao TEXT,
            data_manutencao DATE,
            responsavel TEXT,
            observacoes TEXT,
            custo DECIMAL(10,2)
        )
        """
    ]
    
    for sql in alter_statements:
        db.execute(sql)
```

### 🏥 **Cenário 3: Ambiente Hospitalar**

#### **🏥 Configuração Hospitalar:**

```python
CONFIGURACAO_HOSPITAL = {
    "setores": [
        "UTI",
        "Centro Cirúrgico", 
        "Pronto Socorro",
        "Internação",
        "Farmácia",
        "Laboratório",
        "Radiologia",
        "Almoxarifado"
    ],
    
    "tipos_material": [
        "Medicamentos",
        "Material Cirúrgico",
        "Equipamentos Médicos",
        "Material de Consumo",
        "EPI Hospitalar",
        "Material de Limpeza"
    ],
    
    "campos_obrigatorios": [
        "lote",
        "validade", 
        "registro_anvisa",
        "setor_responsavel"
    ],
    
    "alertas_criticos": {
        "medicamento_vencido": 0,
        "medicamento_vencendo": 30,
        "material_esteril": 15,
        "estoque_critico_uti": 24  # horas
    }
}

def configurar_ambiente_hospitalar():
    """
    CONFIGURAÇÃO HOSPITALAR:
    
    - Controle rigoroso de validade
    - Rastreabilidade por lote
    - Alertas críticos por setor
    - Controle ANVISA
    """
    
    # Campos obrigatórios para ambiente hospitalar
    hospital_fields = """
        ALTER TABLE insumos 
        ADD COLUMN IF NOT EXISTS lote TEXT,
        ADD COLUMN IF NOT EXISTS data_validade DATE,
        ADD COLUMN IF NOT EXISTS registro_anvisa TEXT,
        ADD COLUMN IF NOT EXISTS setor_responsavel TEXT,
        ADD COLUMN IF NOT EXISTS categoria_risco TEXT,
        ADD COLUMN IF NOT EXISTS temperatura_armazenamento TEXT
    """
    
    db.execute(hospital_fields)
    
    # Trigger para alertas de validade
    trigger_validade = """
    CREATE OR REPLACE FUNCTION check_validade_medicamentos()
    RETURNS trigger AS $$
    BEGIN
        IF NEW.data_validade <= CURRENT_DATE + INTERVAL '30 days' 
           AND NEW.categoria = 'Medicamentos' THEN
            INSERT INTO alertas_sistema (
                tipo, item_id, mensagem, prioridade
            ) VALUES (
                'validade_proxima',
                NEW.id,
                'Medicamento ' || NEW.nome || ' vence em: ' || NEW.data_validade,
                CASE WHEN NEW.data_validade <= CURRENT_DATE THEN 'CRITICA'
                     ELSE 'ALTA' END
            );
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    
    CREATE TRIGGER trigger_validade_medicamentos
        AFTER INSERT OR UPDATE ON insumos
        FOR EACH ROW 
        EXECUTE FUNCTION check_validade_medicamentos();
    """
    
    db.execute(trigger_validade)
```

---

## 🔧 TROUBLESHOOTING {#troubleshooting}

### ⚠️ **Problemas Comuns e Soluções:**

#### **🔌 Erro de Conexão com Banco:**

```python
# diagnostico_banco.py
import psycopg2
import os

def diagnosticar_conexao_banco():
    """
    DIAGNÓSTICO COMPLETO DE CONEXÃO:
    
    Verifica todos os aspectos da conexão com PostgreSQL
    """
    
    print("🔍 DIAGNÓSTICO DE CONEXÃO COM BANCO DE DADOS")
    print("=" * 50)
    
    # Verificar variáveis de ambiente
    env_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mascarar senha
            display_value = '***' if 'PASSWORD' in var else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NÃO CONFIGURADO")
            return False
    
    # Testar conectividade
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432),
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ CONEXÃO OK - PostgreSQL: {version}")
        
        # Verificar tabelas essenciais
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        tabelas = [row[0] for row in cursor.fetchall()]
        tabelas_essenciais = ['usuarios', 'insumos', 'movimentacoes']
        
        for tabela in tabelas_essenciais:
            if tabela in tabelas:
                print(f"✅ Tabela '{tabela}' encontrada")
            else:
                print(f"❌ Tabela '{tabela}' AUSENTE")
        
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ ERRO DE CONEXÃO: {e}")
        print("\n🔧 POSSÍVEIS SOLUÇÕES:")
        print("1. Verificar se o host está correto")
        print("2. Confirmar usuário e senha") 
        print("3. Verificar se o banco existe")
        print("4. Testar conectividade de rede")
        return False
    
    except Exception as e:
        print(f"❌ ERRO INESPERADO: {e}")
        return False

if __name__ == "__main__":
    diagnosticar_conexao_banco()
```

#### **💾 Problema de Permissões:**

```python
def diagnosticar_permissoes():
    """
    DIAGNÓSTICO DE PERMISSÕES:
    
    Identifica e corrige problemas de permissões de usuário
    """
    
    print("🔐 DIAGNÓSTICO DE PERMISSÕES")
    print("=" * 30)
    
    # Verificar se existem usuários
    users_count = db.query("SELECT COUNT(*) FROM usuarios")[0][0]
    print(f"📊 Total de usuários: {users_count}")
    
    if users_count == 0:
        print("⚠️  Nenhum usuário encontrado!")
        criar_usuario_admin = input("Criar usuário admin? (s/n): ")
        if criar_usuario_admin.lower() == 's':
            create_default_admin_user()
        return
    
    # Verificar permissões
    users_without_permissions = db.query("""
        SELECT u.id, u.nome, u.email 
        FROM usuarios u
        LEFT JOIN permissoes_modulos p ON u.id = p.usuario_id
        WHERE p.usuario_id IS NULL
    """)
    
    if users_without_permissions:
        print("⚠️  Usuários sem permissões configuradas:")
        for user in users_without_permissions:
            print(f"   - {user[1]} ({user[2]})")
        
        configurar = input("Configurar permissões padrão? (s/n): ")
        if configurar.lower() == 's':
            fix_user_permissions()
    else:
        print("✅ Todos os usuários têm permissões configuradas")

def fix_user_permissions():
    """
    CORREÇÃO AUTOMÁTICA DE PERMISSÕES:
    """
    
    usuarios = db.query("SELECT id, perfil FROM usuarios")
    
    for user_id, perfil in usuarios:
        # Permissões padrão por perfil
        if perfil == 'admin':
            modules = get_all_modules()
            permissions = {mod: True for mod in modules}
        elif perfil == 'gestor':
            permissions = get_gestor_permissions()
        else:
            permissions = get_usuario_permissions()
        
        # Inserir permissões
        for module, access in permissions.items():
            db.execute("""
                INSERT INTO permissoes_modulos (usuario_id, modulo, acesso)
                VALUES (%s, %s, %s)
                ON CONFLICT (usuario_id, modulo) 
                DO UPDATE SET acesso = EXCLUDED.acesso
            """, (user_id, module, access))
    
    print("✅ Permissões configuradas com sucesso!")
```

#### **📊 Problemas de Performance:**

```python
def otimizar_performance():
    """
    OTIMIZAÇÃO AUTOMÁTICA DE PERFORMANCE:
    
    Executa várias otimizações no banco e aplicação
    """
    
    print("🚀 OTIMIZAÇÃO DE PERFORMANCE")
    print("=" * 35)
    
    optimizations = [
        ("Analisar estatísticas do banco", "ANALYZE;"),
        ("Reindexar tabelas principais", "REINDEX TABLE insumos; REINDEX TABLE movimentacoes;"),
        ("Limpar dados antigos", """
            DELETE FROM logs_auditoria 
            WHERE timestamp_acao < NOW() - INTERVAL '90 days'
        """),
        ("Atualizar estatísticas", """
            UPDATE pg_stat_user_tables SET n_tup_ins=0, n_tup_upd=0, n_tup_del=0;
        """)
    ]
    
    for desc, sql in optimizations:
        try:
            print(f"🔧 {desc}...")
            db.execute(sql)
            print("   ✅ Concluído")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    # Verificar queries lentas
    slow_queries = db.query("""
        SELECT query, mean_time, calls
        FROM pg_stat_statements 
        WHERE mean_time > 1000
        ORDER BY mean_time DESC
        LIMIT 5
    """)
    
    if slow_queries:
        print("\n⚠️  Queries mais lentas:")
        for query, time, calls in slow_queries:
            print(f"   - {time:.2f}ms ({calls} calls): {query[:50]}...")
```

---

## 🔄 MANUTENÇÃO E BACKUP {#manutencao}

### 💾 **Sistema de Backup Automático:**

```python
# backup_system.py
import os
import subprocess
import datetime
import boto3
from pathlib import Path

class BackupManager:
    """
    GERENCIADOR DE BACKUPS:
    
    - Backup automático diário
    - Retenção configurável
    - Upload para cloud (AWS S3)
    - Verificação de integridade
    """
    
    def __init__(self):
        self.backup_dir = Path(os.getenv('BACKUP_PATH', './backups'))
        self.retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
        
    def create_database_backup(self):
        """
        BACKUP COMPLETO DO BANCO:
        """
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"inventario_backup_{timestamp}.sql"
        backup_path = self.backup_dir / backup_filename
        
        # Criar diretório se não existir
        self.backup_dir.mkdir(exist_ok=True)
        
        # Comando pg_dump
        cmd = [
            'pg_dump',
            f"--host={os.getenv('DB_HOST')}",
            f"--port={os.getenv('DB_PORT', '5432')}",
            f"--username={os.getenv('DB_USER')}",
            f"--dbname={os.getenv('DB_NAME')}",
            '--no-password',
            '--verbose',
            '--clean',
            '--if-exists',
            f"--file={backup_path}"
        ]
        
        # Definir senha via ambiente
        env = os.environ.copy()
        env['PGPASSWORD'] = os.getenv('DB_PASSWORD')
        
        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Backup criado: {backup_filename}")
                
                # Comprimir backup
                compressed_path = self.compress_backup(backup_path)
                
                # Upload para cloud (se configurado)
                if os.getenv('AWS_S3_BUCKET'):
                    self.upload_to_s3(compressed_path)
                
                return compressed_path
            else:
                print(f"❌ Erro no backup: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao criar backup: {e}")
            return None
    
    def compress_backup(self, backup_path):
        """
        COMPRESSÃO DO BACKUP:
        """
        import gzip
        
        compressed_path = backup_path.with_suffix('.sql.gz')
        
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                f_out.writelines(f_in)
        
        # Remover arquivo original
        backup_path.unlink()
        
        print(f"📦 Backup comprimido: {compressed_path.name}")
        return compressed_path
    
    def upload_to_s3(self, file_path):
        """
        UPLOAD PARA AWS S3:
        """
        try:
            s3_client = boto3.client('s3')
            bucket = os.getenv('AWS_S3_BUCKET')
            key = f"inventario/backups/{file_path.name}"
            
            s3_client.upload_file(str(file_path), bucket, key)
            print(f"☁️  Upload S3 concluído: s3://{bucket}/{key}")
            
        except Exception as e:
            print(f"❌ Erro no upload S3: {e}")
    
    def cleanup_old_backups(self):
        """
        LIMPEZA DE BACKUPS ANTIGOS:
        """
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.retention_days)
        
        removed_count = 0
        for backup_file in self.backup_dir.glob("inventario_backup_*.sql.gz"):
            # Extrair timestamp do nome
            timestamp_str = backup_file.stem.split('_')[-2] + '_' + backup_file.stem.split('_')[-1]
            
            try:
                backup_date = datetime.datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                if backup_date < cutoff_date:
                    backup_file.unlink()
                    removed_count += 1
                    print(f"🗑️  Removido backup antigo: {backup_file.name}")
            except:
                pass  # Ignorar arquivos com nome inválido
        
        print(f"🧹 Limpeza concluída: {removed_count} backups removidos")
    
    def restore_backup(self, backup_path):
        """
        RESTAURAÇÃO DE BACKUP:
        """
        import gzip
        
        print("⚠️  ATENÇÃO: Esta operação irá SOBRESCREVER todos os dados!")
        confirm = input("Confirmar restauração? Digite 'CONFIRMO': ")
        
        if confirm != 'CONFIRMO':
            print("❌ Restauração cancelada")
            return False
        
        try:
            # Descomprimir se necessário
            if backup_path.suffix == '.gz':
                with gzip.open(backup_path, 'rb') as f_in:
                    sql_content = f_in.read().decode('utf-8')
            else:
                with open(backup_path, 'r') as f:
                    sql_content = f.read()
            
            # Executar restauração
            cmd = [
                'psql',
                f"--host={os.getenv('DB_HOST')}",
                f"--port={os.getenv('DB_PORT', '5432')}",
                f"--username={os.getenv('DB_USER')}",
                f"--dbname={os.getenv('DB_NAME')}",
                '--no-password'
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = os.getenv('DB_PASSWORD')
            
            process = subprocess.run(
                cmd, 
                input=sql_content, 
                text=True, 
                env=env,
                capture_output=True
            )
            
            if process.returncode == 0:
                print("✅ Backup restaurado com sucesso!")
                return True
            else:
                print(f"❌ Erro na restauração: {process.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao restaurar backup: {e}")
            return False

# Agendamento automático de backups
def setup_automated_backup():
    """
    CONFIGURAÇÃO DE BACKUP AUTOMÁTICO:
    
    Configura backup automático usando cron (Linux) ou Task Scheduler (Windows)
    """
    
    backup_manager = BackupManager()
    
    # Executar backup
    backup_path = backup_manager.create_database_backup()
    
    if backup_path:
        # Limpar backups antigos
        backup_manager.cleanup_old_backups()
        print("🎯 Backup automático concluído!")
    else:
        print("❌ Falha no backup automático!")

if __name__ == "__main__":
    setup_automated_backup()
```

### 📊 **Monitoramento de Sistema:**

```python
# monitoring.py
import psutil
import psycopg2
import time
import datetime

class SystemMonitor:
    """
    MONITORAMENTO DO SISTEMA:
    
    - Performance da aplicação
    - Uso de recursos
    - Health checks
    - Alertas automáticos
    """
    
    def check_system_health(self):
        """
        VERIFICAÇÃO COMPLETA DE SAÚDE DO SISTEMA:
        """
        
        health_report = {
            'timestamp': datetime.datetime.now(),
            'database': self.check_database_health(),
            'system': self.check_system_resources(),
            'application': self.check_application_health()
        }
        
        return health_report
    
    def check_database_health(self):
        """
        HEALTH CHECK DO BANCO DE DADOS:
        """
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            
            # Verificar conectividade
            start_time = time.time()
            cursor.execute("SELECT 1")
            response_time = time.time() - start_time
            
            # Verificar tamanho do banco
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """)
            db_size = cursor.fetchone()[0]
            
            # Verificar conexões ativas
            cursor.execute("""
                SELECT count(*) FROM pg_stat_activity 
                WHERE state = 'active'
            """)
            active_connections = cursor.fetchone()[0]
            
            # Verificar locks
            cursor.execute("""
                SELECT count(*) FROM pg_locks 
                WHERE granted = false
            """)
            blocked_queries = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'status': 'healthy',
                'response_time': response_time,
                'database_size': db_size,
                'active_connections': active_connections,
                'blocked_queries': blocked_queries
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_system_resources(self):
        """
        VERIFICAÇÃO DE RECURSOS DO SISTEMA:
        """
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memória
        memory = psutil.virtual_memory()
        
        # Disco
        disk = psutil.disk_usage('/')
        
        # Rede
        network = psutil.net_io_counters()
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free / (1024**3),
            'network_bytes_sent': network.bytes_sent,
            'network_bytes_recv': network.bytes_recv
        }
    
    def check_application_health(self):
        """
        VERIFICAÇÃO DE SAÚDE DA APLICAÇÃO:
        """
        
        try:
            # Verificar se Streamlit está respondendo
            import requests
            response = requests.get('http://localhost:8501', timeout=5)
            
            app_status = 'healthy' if response.status_code == 200 else 'unhealthy'
            
            # Verificar logs de erro recentes
            recent_errors = self.check_recent_errors()
            
            return {
                'status': app_status,
                'response_code': response.status_code,
                'recent_errors': recent_errors
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def generate_health_report(self):
        """
        GERAR RELATÓRIO COMPLETO DE SAÚDE:
        """
        
        health = self.check_system_health()
        
        print("🏥 RELATÓRIO DE SAÚDE DO SISTEMA")
        print("=" * 40)
        print(f"📅 Timestamp: {health['timestamp']}")
        
        # Banco de dados
        db_health = health['database']
        if db_health['status'] == 'healthy':
            print(f"✅ Banco: {db_health['status']}")
            print(f"   ⏱️  Tempo resposta: {db_health['response_time']:.3f}s")
            print(f"   💾 Tamanho: {db_health['database_size']}")
            print(f"   🔗 Conexões ativas: {db_health['active_connections']}")
        else:
            print(f"❌ Banco: {db_health['status']}")
            print(f"   🚨 Erro: {db_health['error']}")
        
        # Sistema
        sys_health = health['system']
        print(f"🖥️  CPU: {sys_health['cpu_percent']:.1f}%")
        print(f"💾 Memória: {sys_health['memory_percent']:.1f}% ({sys_health['memory_available_gb']:.1f} GB livres)")
        print(f"💽 Disco: {sys_health['disk_percent']:.1f}% ({sys_health['disk_free_gb']:.1f} GB livres)")
        
        # Aplicação
        app_health = health['application']
        print(f"🌐 Aplicação: {app_health['status']}")
        
        return health

if __name__ == "__main__":
    monitor = SystemMonitor()
    monitor.generate_health_report()
```

---

## 🎨 CUSTOMIZAÇÃO {#customizacao}

### 🎯 **Personalização de Interface:**

```python
# customization.py
import streamlit as st
import json

class InterfaceCustomizer:
    """
    CUSTOMIZADOR DE INTERFACE:
    
    Permite personalizar cores, logos, textos e layout
    sem modificar código fonte.
    """
    
    def __init__(self):
        self.config_file = "custom_config.json"
        self.load_custom_config()
    
    def load_custom_config(self):
        """
        CARREGAR CONFIGURAÇÕES PERSONALIZADAS:
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = self.get_default_config()
            self.save_config()
    
    def get_default_config(self):
        """
        CONFIGURAÇÕES PADRÃO:
        """
        return {
            "empresa": {
                "nome": "Sua Empresa",
                "logo_url": "",
                "cores": {
                    "primaria": "#1f77b4",
                    "secundaria": "#ff7f0e", 
                    "fundo": "#ffffff",
                    "texto": "#262730"
                }
            },
            "interface": {
                "titulo": "Sistema de Inventário",
                "subtitulo": "Gestão Inteligente de Estoque",
                "sidebar_width": 300,
                "mostrar_metricas_sidebar": True
            },
            "funcionalidades": {
                "habilitar_api": True,
                "habilitar_relatorios_avancados": True,
                "habilitar_predicoes": True,
                "habilitar_qr_codes": True
            },
            "dashboard": {
                "metricas_principais": [
                    "total_itens",
                    "valor_estoque", 
                    "itens_criticos",
                    "movimentacoes_hoje"
                ],
                "graficos_padrao": [
                    "movimentacoes_tempo",
                    "top_categorias",
                    "alertas_estoque"
                ]
            }
        }
    
    def apply_custom_theme(self):
        """
        APLICAR TEMA PERSONALIZADO:
        """
        cores = self.config["empresa"]["cores"]
        
        # CSS customizado
        custom_css = f"""
        <style>
            .stApp {{
                background-color: {cores["fundo"]};
                color: {cores["texto"]};
            }}
            
            .sidebar .sidebar-content {{
                width: {self.config["interface"]["sidebar_width"]}px;
                background-color: {cores["secundaria"]}10;
            }}
            
            .metric-card {{
                background: linear-gradient(90deg, {cores["primaria"]} 0%, {cores["secundaria"]} 100%);
                color: white;
                padding: 1rem;
                border-radius: 8px;
                margin: 0.5rem 0;
            }}
            
            .custom-header {{
                background: {cores["primaria"]};
                color: white;
                padding: 1rem;
                border-radius: 8px;
                text-align: center;
                margin-bottom: 2rem;
            }}
        </style>
        """
        
        st.markdown(custom_css, unsafe_allow_html=True)
    
    def show_custom_header(self):
        """
        CABEÇALHO PERSONALIZADO:
        """
        empresa = self.config["empresa"]
        interface = self.config["interface"]
        
        if empresa["logo_url"]:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(empresa["logo_url"], width=200)
        
        st.markdown(f"""
        <div class="custom-header">
            <h1>{interface["titulo"]}</h1>
            <p>{interface["subtitulo"]} - {empresa["nome"]}</p>
        </div>
        """, unsafe_allow_html=True)

def setup_custom_interface():
    """
    CONFIGURAR INTERFACE PERSONALIZADA:
    
    Interface para configuração visual sem código
    """
    
    st.title("🎨 Customização de Interface")
    
    customizer = InterfaceCustomizer()
    
    with st.expander("🏢 Configurações da Empresa"):
        nome_empresa = st.text_input(
            "Nome da Empresa", 
            value=customizer.config["empresa"]["nome"]
        )
        
        logo_url = st.text_input(
            "URL do Logo", 
            value=customizer.config["empresa"]["logo_url"]
        )
        
        if logo_url:
            try:
                st.image(logo_url, width=200, caption="Preview do Logo")
            except:
                st.error("URL do logo inválida")
    
    with st.expander("🎨 Cores do Sistema"):
        col1, col2 = st.columns(2)
        
        with col1:
            cor_primaria = st.color_picker(
                "Cor Primária",
                value=customizer.config["empresa"]["cores"]["primaria"]
            )
            
            cor_fundo = st.color_picker(
                "Cor de Fundo",
                value=customizer.config["empresa"]["cores"]["fundo"]
            )
        
        with col2:
            cor_secundaria = st.color_picker(
                "Cor Secundária", 
                value=customizer.config["empresa"]["cores"]["secundaria"]
            )
            
            cor_texto = st.color_picker(
                "Cor do Texto",
                value=customizer.config["empresa"]["cores"]["texto"]
            )
    
    with st.expander("⚙️ Configurações da Interface"):
        titulo = st.text_input(
            "Título do Sistema",
            value=customizer.config["interface"]["titulo"]
        )
        
        subtitulo = st.text_input(
            "Subtítulo",
            value=customizer.config["interface"]["subtitulo"]
        )
        
        sidebar_width = st.slider(
            "Largura da Sidebar",
            min_value=250,
            max_value=400,
            value=customizer.config["interface"]["sidebar_width"]
        )
    
    if st.button("💾 Salvar Configurações"):
        # Atualizar configurações
        customizer.config["empresa"]["nome"] = nome_empresa
        customizer.config["empresa"]["logo_url"] = logo_url
        customizer.config["empresa"]["cores"] = {
            "primaria": cor_primaria,
            "secundaria": cor_secundaria,
            "fundo": cor_fundo,
            "texto": cor_texto
        }
        customizer.config["interface"]["titulo"] = titulo
        customizer.config["interface"]["subtitulo"] = subtitulo
        customizer.config["interface"]["sidebar_width"] = sidebar_width
        
        # Salvar arquivo
        customizer.save_config()
        
        st.success("✅ Configurações salvas! Recarregue a página para ver as mudanças.")
```

---

**📚 Este guia contém implementações práticas para cenários reais de uso do sistema. Cada seção fornece código funcional que pode ser adaptado conforme necessário.**