"""
Sistema de Inventário Web - Conexão com Banco de Dados SQLite
Autor: Desenvolvido com todas as funcionalidades avançadas
Data: 2025
"""

import sqlite3
import bcrypt
import os

class DatabaseConnection:
    def __init__(self, db_path: str = "database/inventario.db"):
        self.db_path = db_path
        self.conn = None
        self.create_database()
        self.create_tables()
        self.create_default_user()
    
    def create_database(self):
        """Cria o banco de dados se não existir"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
    
    def get_connection(self):
        """Retorna uma conexão com o banco"""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def create_tables(self):
        cursor = self.get_connection().cursor()
        
        # Tabela de usuários
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            perfil TEXT DEFAULT 'usuario', -- 'admin', 'gestor', 'usuario'
            ativo BOOLEAN DEFAULT 1,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            ultimo_login DATETIME
        )
        """)
        
        # Tabela de sessões
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            token TEXT UNIQUE,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_expiracao DATETIME,
            ativo BOOLEAN DEFAULT 1,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
        """)
        
        # Tabela de obras/departamentos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS obras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            endereco TEXT,
            cidade TEXT,
            estado TEXT,
            cep TEXT,
            status TEXT DEFAULT 'ativo', -- 'ativo', 'concluido', 'pausado'
            responsavel TEXT,
            telefone TEXT,
            email TEXT,
            observacoes TEXT,
            data_inicio DATE,
            data_previsao DATE,
            data_conclusao DATE,
            valor_orcado REAL,
            valor_gasto REAL DEFAULT 0,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            criado_por INTEGER,
            FOREIGN KEY (criado_por) REFERENCES usuarios (id)
        )
        """)
        
        # Tabela de responsáveis
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS responsaveis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE,
            telefone TEXT,
            email TEXT,
            cargo TEXT,
            departamento TEXT,
            obra_id INTEGER,
            ativo BOOLEAN DEFAULT 1,
            observacoes TEXT,
            data_admissao DATE,
            data_demissao DATE,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            criado_por INTEGER,
            FOREIGN KEY (obra_id) REFERENCES obras (id),
            FOREIGN KEY (criado_por) REFERENCES usuarios (id)
        )
        """)
        
        # Tabela de categorias
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            descricao TEXT,
            tipo TEXT, -- 'insumo', 'equipamento_eletrico', 'equipamento_manual'
            cor TEXT DEFAULT '#007ACC',
            ativo BOOLEAN DEFAULT 1,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabela de insumos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS insumos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            descricao TEXT NOT NULL,
            categoria_id INTEGER,
            unidade TEXT NOT NULL,
            quantidade_atual REAL DEFAULT 0,
            quantidade_minima REAL DEFAULT 0,
            preco_unitario REAL,
            preco_ultima_compra REAL,
            fornecedor TEXT,
            marca TEXT,
            localizacao TEXT DEFAULT 'Almoxarifado',
            observacoes TEXT,
            status_validade TEXT, -- 'vencido', 'proximo_vencimento', 'dentro_prazo'
            data_validade DATE,
            data_ultima_entrada DATE,
            data_ultima_saida DATE,
            ativo BOOLEAN DEFAULT 1,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            criado_por INTEGER,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id),
            FOREIGN KEY (criado_por) REFERENCES usuarios (id)
        )
        """)
        
        # Tabela de equipamentos elétricos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipamentos_eletricos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            categoria_id INTEGER,
            marca TEXT,
            modelo TEXT,
            numero_serie TEXT,
            voltagem TEXT,
            potencia TEXT,
            status TEXT DEFAULT 'Disponível', -- 'Disponível', 'Em uso', 'Manutenção', 'Inativo', 'Danificado'
            localizacao TEXT DEFAULT 'Almoxarifado',
            obra_atual_id INTEGER,
            responsavel_atual_id INTEGER,
            valor_compra REAL,
            data_compra DATE,
            data_garantia DATE,
            fornecedor TEXT,
            nota_fiscal TEXT,
            observacoes TEXT,
            historico_manutencao TEXT,
            proxima_manutencao DATE,
            ativo BOOLEAN DEFAULT 1,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            criado_por INTEGER,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id),
            FOREIGN KEY (obra_atual_id) REFERENCES obras (id),
            FOREIGN KEY (responsavel_atual_id) REFERENCES responsaveis (id),
            FOREIGN KEY (criado_por) REFERENCES usuarios (id)
        )
        """)
        
        # Tabela de equipamentos manuais
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipamentos_manuais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            descricao TEXT NOT NULL,
            tipo TEXT,
            categoria_id INTEGER,
            quantitativo INTEGER DEFAULT 1,
            status TEXT DEFAULT 'Disponível', -- 'Disponível', 'Em uso', 'Manutenção', 'Inativo', 'Danificado'
            estado TEXT, -- 'Novo', 'Usado - Bom Estado', 'Usado - Regular', 'Ruim'
            marca TEXT,
            localizacao TEXT DEFAULT 'Almoxarifado',
            obra_atual_id INTEGER,
            responsavel_atual_id INTEGER,
            valor REAL,
            data_compra DATE,
            loja TEXT,
            observacoes TEXT,
            ativo BOOLEAN DEFAULT 1,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            criado_por INTEGER,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id),
            FOREIGN KEY (obra_atual_id) REFERENCES obras (id),
            FOREIGN KEY (responsavel_atual_id) REFERENCES responsaveis (id),
            FOREIGN KEY (criado_por) REFERENCES usuarios (id)
        )
        """)
        
        # Tabela de movimentações
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL, -- 'entrada', 'saida', 'transferencia', 'devolucao', 'baixa'
            tipo_item TEXT NOT NULL, -- 'insumo', 'equipamento_eletrico', 'equipamento_manual'
            item_id INTEGER NOT NULL,
            codigo_item TEXT,
            descricao_item TEXT,
            quantidade REAL,
            unidade TEXT,
            obra_origem_id INTEGER,
            obra_destino_id INTEGER,
            responsavel_origem_id INTEGER,
            responsavel_destino_id INTEGER,
            valor_unitario REAL,
            valor_total REAL,
            motivo TEXT,
            observacoes TEXT,
            documento TEXT, -- número da nota fiscal ou documento
            data_movimentacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_previsao_retorno DATE,
            status TEXT DEFAULT 'concluida', -- 'pendente', 'concluida', 'cancelada'
            usuario_id INTEGER NOT NULL,
            FOREIGN KEY (obra_origem_id) REFERENCES obras (id),
            FOREIGN KEY (obra_destino_id) REFERENCES obras (id),
            FOREIGN KEY (responsavel_origem_id) REFERENCES responsaveis (id),
            FOREIGN KEY (responsavel_destino_id) REFERENCES responsaveis (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
        """)
        
        # Tabela de alertas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL, -- 'estoque_baixo', 'vencimento', 'manutencao', 'garantia'
            titulo TEXT NOT NULL,
            mensagem TEXT NOT NULL,
            prioridade TEXT DEFAULT 'media', -- 'baixa', 'media', 'alta', 'critica'
            tipo_item TEXT, -- 'insumo', 'equipamento_eletrico', 'equipamento_manual'
            item_id INTEGER,
            codigo_item TEXT,
            lido BOOLEAN DEFAULT 0,
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_vencimento DATE,
            usuario_id INTEGER,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
        """)
        
        # Tabela de logs de auditoria
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs_auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            usuario_nome TEXT,
            acao TEXT NOT NULL, -- 'criar', 'editar', 'excluir', 'visualizar', 'login', 'logout'
            modulo TEXT NOT NULL, -- 'usuarios', 'insumos', 'equipamentos', 'movimentacoes', etc
            item_tipo TEXT,
            item_id INTEGER,
            item_codigo TEXT,
            dados_anteriores TEXT, -- JSON com dados antes da alteração
            dados_novos TEXT, -- JSON com dados após alteração
            ip_address TEXT,
            user_agent TEXT,
            observacoes TEXT,
            data_acao DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabela de configurações do sistema
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chave TEXT UNIQUE NOT NULL,
            valor TEXT,
            descricao TEXT,
            tipo TEXT DEFAULT 'text', -- 'text', 'number', 'boolean', 'json'
            categoria TEXT DEFAULT 'geral',
            data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            atualizado_por INTEGER,
            FOREIGN KEY (atualizado_por) REFERENCES usuarios (id)
        )
        """)
        
        # Tabela de anexos/documentos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS anexos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_arquivo TEXT NOT NULL,
            nome_original TEXT NOT NULL,
            tipo_arquivo TEXT,
            tamanho INTEGER,
            caminho TEXT NOT NULL,
            tipo_vinculo TEXT, -- 'insumo', 'equipamento_eletrico', 'equipamento_manual', 'obra', 'responsavel'
            vinculo_id INTEGER,
            descricao TEXT,
            data_upload DATETIME DEFAULT CURRENT_TIMESTAMP,
            usuario_upload INTEGER,
            FOREIGN KEY (usuario_upload) REFERENCES usuarios (id)
        )
        """)
        
        if self.conn:
            self.conn.commit()
        self.create_default_categories()
        print("Todas as tabelas foram criadas com sucesso!")
    
    def create_default_categories(self):
        cursor = self.get_connection().cursor()
        
        categorias_padrao = [
            ('Hidráulica', 'Materiais e conexões hidráulicas', 'insumo', '#0066CC'),
            ('Elétrica', 'Materiais e equipamentos elétricos', 'insumo', '#FF6600'),
            ('Civil', 'Materiais de construção civil', 'insumo', '#996633'),
            ('Acabamentos', 'Materiais de acabamento e revestimento', 'insumo', '#9966CC'),
            ('E.P.I.', 'Equipamentos de Proteção Individual', 'insumo', '#FF0000'),
            ('Pintura', 'Materiais para pintura', 'insumo', '#00CC66'),
            ('Limpeza', 'Materiais de limpeza', 'insumo', '#66CCFF'),
            ('Lubrificação', 'Óleos e graxas', 'insumo', '#FFD700'),
            ('Incêndio', 'Equipamentos de combate a incêndio', 'insumo', '#DC143C'),
            ('Forro', 'Materiais para forro', 'insumo', '#DDA0DD'),
            ('Outros', 'Outros materiais diversos', 'insumo', '#808080'),
            ('Ferramentas Elétricas', 'Equipamentos elétricos', 'equipamento_eletrico', '#FF4500'),
            ('Ferramentas Manuais', 'Equipamentos manuais', 'equipamento_manual', '#228B22')
        ]
        
        for nome, descricao, tipo, cor in categorias_padrao:
            try:
                cursor.execute("""
                INSERT OR IGNORE INTO categorias (nome, descricao, tipo, cor)
                VALUES (?, ?, ?, ?)
                """, (nome, descricao, tipo, cor))
            except Exception as e:
                print(f"Erro ao criar categoria {nome}: {e}")
        
        if self.conn:
            self.conn.commit()
    
    def create_default_user(self):
        cursor = self.get_connection().cursor()
        
        # Verifica se já existe usuário admin
        cursor.execute("SELECT id FROM usuarios WHERE email = ?", ('admin@inventario.com',))
        if cursor.fetchone():
            return
        
        # Cria senha hash para 'admin123'
        password = 'admin123'
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("""
        INSERT INTO usuarios (nome, email, password_hash, perfil, ativo)
        VALUES (?, ?, ?, ?, ?)
        """, ('Administrador', 'admin@inventario.com', password_hash, 'admin', 1))
        
        if self.conn:
            self.conn.commit()
        print("✅ Usuário administrador padrão criado!")
        print("   Email: admin@inventario.com")
        print("   Senha: admin123")
    
    def insert_configuracoes_padrao(self):
        cursor = self.get_connection().cursor()
        
        configs_padrao = [
            ('nome_empresa', 'Inventário Web', 'Nome da empresa/sistema', 'text', 'geral'),
            ('logo_empresa', '', 'URL ou caminho do logo', 'text', 'geral'),
            ('email_notificacao', 'admin@inventario.com', 'Email para notificações', 'text', 'notificacoes'),
            ('dias_alerta_vencimento', '30', 'Dias antes do vencimento para alertar', 'number', 'alertas'),
            ('estoque_minimo_padrao', '5', 'Quantidade mínima padrão de estoque', 'number', 'estoque'),
            ('backup_automatico', 'true', 'Ativar backup automático', 'boolean', 'sistema'),
            ('tema_padrao', 'light', 'Tema padrão da interface', 'text', 'interface'),
            ('moeda', 'BRL', 'Moeda padrão do sistema', 'text', 'geral')
        ]
        
        for chave, valor, descricao, tipo, categoria in configs_padrao:
            cursor.execute("""
            INSERT OR IGNORE INTO configuracoes (chave, valor, descricao, tipo, categoria)
            VALUES (?, ?, ?, ?, ?)
            """, (chave, valor, descricao, tipo, categoria))
        
        if self.conn:
            self.conn.commit()
    
    def close_connection(self):
        if self.conn:
            self.conn.close()
            self.conn = None

# Instância global do banco de dados
db = DatabaseConnection()