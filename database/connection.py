"""
Sistema de Inventário Web - Conexão com Banco de Dados PostgreSQL
Autor: Desenvolvido com todas as funcionalidades avançadas
Data: 2025
"""

import psycopg2
import psycopg2.extras
import bcrypt
import os
import streamlit as st

class DatabaseConnection:
    def __init__(self, connection_string: str | None = None):
        self.connection_string = connection_string or self.get_connection_string()
        self.conn = None
        self.create_connection()
        self.create_tables()
        self.create_default_user()
    
    def get_connection_string(self):
        """Obtém a string de conexão dos secrets ou variável de ambiente"""
        if hasattr(st, 'secrets') and 'DATABASE_URL' in st.secrets:
            return st.secrets['DATABASE_URL']
        elif 'DATABASE_URL' in os.environ:
            return os.environ['DATABASE_URL']
        else:
            # Fallback para desenvolvimento local
            return "postgresql://postgres:password@localhost:5432/inventario"
    
    def create_connection(self):
        """Cria a conexão com PostgreSQL"""
        try:
            # Adiciona configurações mais robustas para a conexão
            self.conn = psycopg2.connect(
                self.connection_string,
                cursor_factory=psycopg2.extras.RealDictCursor,
                connect_timeout=30,
                keepalives_idle=600,
                keepalives_interval=30,
                keepalives_count=3
            )
            self.conn.autocommit = False
            print("✅ Conexão com PostgreSQL estabelecida!")
        except Exception as e:
            print(f"❌ Erro ao conectar com PostgreSQL: {e}")
            raise
    
    def get_connection(self):
        """Retorna uma conexão com o banco, recriando se necessário"""
        try:
            # Verifica se a conexão está ativa
            if not self.conn or self.conn.closed:
                print("🔄 Reconectando ao PostgreSQL...")
                self.create_connection()
            else:
                # Fazer rollback de qualquer transação abortada antes de testar
                try:
                    self.conn.rollback()
                except:
                    pass
                
                # Testa a conexão com um ping simples
                cursor = self.conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return self.conn
        except (psycopg2.OperationalError, psycopg2.InterfaceError, psycopg2.errors.InFailedSqlTransaction) as e:
            print(f"🔄 Conexão perdida, reconectando: {e}")
            self.create_connection()
            return self.conn
    
    def create_tables(self):
        conn = self.get_connection()
        if conn is None:
            raise Exception("Conexão com o banco de dados não está disponível.")
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            perfil TEXT DEFAULT 'usuario', -- 'admin', 'gestor', 'usuario'
            ativo BOOLEAN DEFAULT true,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultimo_login TIMESTAMP
        )
        """)
        
        # Tabela de sessões
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessoes (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER REFERENCES usuarios(id),
            token TEXT UNIQUE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_expiracao TIMESTAMP,
            ativo BOOLEAN DEFAULT true
        )
        """)
        
        # Tabela de obras/departamentos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS obras (
            id SERIAL PRIMARY KEY,
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
            valor_orcado DECIMAL(12,2),
            valor_gasto DECIMAL(12,2) DEFAULT 0,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            criado_por INTEGER REFERENCES usuarios(id)
        )
        """)
        
        # Tabela de responsáveis
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS responsaveis (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE,
            telefone TEXT,
            email TEXT,
            cargo TEXT,
            departamento TEXT,
            obra_id INTEGER REFERENCES obras(id),
            ativo BOOLEAN DEFAULT true,
            observacoes TEXT,
            data_admissao DATE,
            data_demissao DATE,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            criado_por INTEGER REFERENCES usuarios(id)
        )
        """)
        
        # Tabela de categorias
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id SERIAL PRIMARY KEY,
            nome TEXT UNIQUE NOT NULL,
            descricao TEXT,
            tipo TEXT, -- 'insumo', 'equipamento_eletrico', 'equipamento_manual'
            cor TEXT DEFAULT '#007ACC',
            ativo BOOLEAN DEFAULT true,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabela de insumos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS insumos (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            descricao TEXT NOT NULL,
            categoria_id INTEGER REFERENCES categorias(id),
            unidade TEXT NOT NULL,
            quantidade_atual DECIMAL(10,3) DEFAULT 0,
            quantidade_minima DECIMAL(10,3) DEFAULT 0,
            preco_unitario DECIMAL(10,2),
            preco_ultima_compra DECIMAL(10,2),
            fornecedor TEXT,
            marca TEXT,
            localizacao TEXT DEFAULT 'Almoxarifado',
            observacoes TEXT,
            status_validade TEXT, -- 'vencido', 'proximo_vencimento', 'dentro_prazo'
            data_validade DATE,
            data_ultima_entrada DATE,
            data_ultima_saida DATE,
            ativo BOOLEAN DEFAULT true,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            criado_por INTEGER REFERENCES usuarios(id)
        )
        """)
        
        # Tabela de equipamentos elétricos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipamentos_eletricos (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            categoria_id INTEGER REFERENCES categorias(id),
            marca TEXT,
            modelo TEXT,
            numero_serie TEXT,
            voltagem TEXT,
            potencia TEXT,
            status TEXT DEFAULT 'Disponível', -- 'Disponível', 'Em uso', 'Manutenção', 'Inativo', 'Danificado'
            localizacao TEXT DEFAULT 'Almoxarifado',
            obra_atual_id INTEGER REFERENCES obras(id),
            responsavel_atual_id INTEGER REFERENCES responsaveis(id),
            valor_compra DECIMAL(10,2),
            data_compra DATE,
            data_garantia DATE,
            fornecedor TEXT,
            nota_fiscal TEXT,
            observacoes TEXT,
            historico_manutencao TEXT,
            proxima_manutencao DATE,
            ativo BOOLEAN DEFAULT true,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            criado_por INTEGER REFERENCES usuarios(id)
        )
        """)
        
        # Tabela de equipamentos manuais
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipamentos_manuais (
            id SERIAL PRIMARY KEY,
            codigo TEXT UNIQUE NOT NULL,
            descricao TEXT NOT NULL,
            tipo TEXT,
            categoria_id INTEGER REFERENCES categorias(id),
            quantitativo INTEGER DEFAULT 1,
            status TEXT DEFAULT 'Disponível', -- 'Disponível', 'Em uso', 'Manutenção', 'Inativo', 'Danificado'
            estado TEXT, -- 'Novo', 'Usado - Bom Estado', 'Usado - Regular', 'Ruim'
            marca TEXT,
            localizacao TEXT DEFAULT 'Almoxarifado',
            obra_atual_id INTEGER REFERENCES obras(id),
            responsavel_atual_id INTEGER REFERENCES responsaveis(id),
            valor DECIMAL(10,2),
            data_compra DATE,
            loja TEXT,
            observacoes TEXT,
            ativo BOOLEAN DEFAULT true,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            criado_por INTEGER REFERENCES usuarios(id)
        )
        """)
        
        # Tabela de movimentações
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id SERIAL PRIMARY KEY,
            tipo TEXT NOT NULL, -- 'entrada', 'saida', 'transferencia', 'devolucao', 'baixa'
            tipo_item TEXT NOT NULL, -- 'insumo', 'equipamento_eletrico', 'equipamento_manual'
            item_id INTEGER NOT NULL,
            codigo_item TEXT,
            descricao_item TEXT,
            quantidade DECIMAL(10,3),
            unidade TEXT,
            obra_origem_id INTEGER REFERENCES obras(id),
            obra_destino_id INTEGER REFERENCES obras(id),
            responsavel_origem_id INTEGER REFERENCES responsaveis(id),
            responsavel_destino_id INTEGER REFERENCES responsaveis(id),
            valor_unitario DECIMAL(10,2),
            valor_total DECIMAL(12,2),
            motivo TEXT,
            observacoes TEXT,
            documento TEXT, -- número da nota fiscal ou documento
            data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_previsao_retorno DATE,
            status TEXT DEFAULT 'concluida', -- 'pendente', 'concluida', 'cancelada'
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id)
        )
        """)
        
        # Tabela de alertas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alertas (
            id SERIAL PRIMARY KEY,
            tipo TEXT NOT NULL, -- 'estoque_baixo', 'vencimento', 'manutencao', 'garantia'
            titulo TEXT NOT NULL,
            mensagem TEXT NOT NULL,
            prioridade TEXT DEFAULT 'media', -- 'baixa', 'media', 'alta', 'critica'
            tipo_item TEXT, -- 'insumo', 'equipamento_eletrico', 'equipamento_manual'
            item_id INTEGER,
            codigo_item TEXT,
            lido BOOLEAN DEFAULT false,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_vencimento DATE,
            usuario_id INTEGER REFERENCES usuarios(id)
        )
        """)
        
        # Tabela de logs de auditoria
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs_auditoria (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
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
            data_acao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Tabela de configurações do sistema
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            id SERIAL PRIMARY KEY,
            chave TEXT UNIQUE NOT NULL,
            valor TEXT,
            descricao TEXT,
            tipo TEXT DEFAULT 'text', -- 'text', 'number', 'boolean', 'json'
            categoria TEXT DEFAULT 'geral',
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_por INTEGER REFERENCES usuarios(id)
        )
        """)
        
        # Tabela de anexos/documentos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS anexos (
            id SERIAL PRIMARY KEY,
            nome_arquivo TEXT NOT NULL,
            nome_original TEXT NOT NULL,
            tipo_arquivo TEXT,
            tamanho INTEGER,
            caminho TEXT NOT NULL,
            tipo_vinculo TEXT, -- 'insumo', 'equipamento_eletrico', 'equipamento_manual', 'obra', 'responsavel'
            vinculo_id INTEGER,
            descricao TEXT,
            data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usuario_upload INTEGER REFERENCES usuarios(id)
        )
        """)
        
        if self.conn:
            self.conn.commit()
        self.create_default_categories()
        print("✅ Todas as tabelas PostgreSQL foram criadas com sucesso!")
    
    def create_default_categories(self):
        conn = self.get_connection()
        if conn is None:
            raise Exception("Conexão com o banco de dados não está disponível.")
        cursor = conn.cursor()
        
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
                INSERT INTO categorias (nome, descricao, tipo, cor)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (nome) DO NOTHING
                """, (nome, descricao, tipo, cor))
            except Exception as e:
                print(f"Erro ao criar categoria {nome}: {e}")
        
        if self.conn:
            self.conn.commit()
    
    def create_default_user(self):
        conn = self.get_connection()
        if conn is None:
            raise Exception("Conexão com o banco de dados não está disponível.")
        cursor = conn.cursor()
        
        # Verifica se já existe usuário admin
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", ('admin@inventario.com',))
        if cursor.fetchone():
            return
        
        # Cria senha hash para 'admin123'
        password = 'admin123'
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("""
        INSERT INTO usuarios (nome, email, password_hash, perfil, ativo)
        VALUES (%s, %s, %s, %s, %s)
        """, ('Administrador', 'admin@inventario.com', password_hash, 'admin', True))
        
        if self.conn:
            self.conn.commit()
        print("✅ Usuário administrador padrão criado!")
        print("   Email: admin@inventario.com")
        print("   Senha: admin123")
    
    def close_connection(self):
        if self.conn and not self.conn.closed:
            self.conn.close()
            self.conn = None

# Instância global do banco de dados
db = DatabaseConnection()