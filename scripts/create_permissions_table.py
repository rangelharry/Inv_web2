import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.connection import db

def create_permissions_table():
    """Cria tabela de permissões por módulo"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se a tabela já existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'permissoes_modulos'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("Criando tabela permissoes_modulos...")
            cursor.execute("""
                CREATE TABLE permissoes_modulos (
                    id SERIAL PRIMARY KEY,
                    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
                    modulo TEXT NOT NULL,
                    acesso BOOLEAN DEFAULT FALSE,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(usuario_id, modulo)
                );
            """)
            
            # Criar índices para performance
            cursor.execute("""
                CREATE INDEX idx_permissoes_usuario_modulo 
                ON permissoes_modulos(usuario_id, modulo);
            """)
            
            conn.commit()
            print("✅ Tabela permissoes_modulos criada com sucesso!")
            
            # Inserir permissões padrão para usuários existentes
            print("Configurando permissões padrão...")
            
            # Admin tem acesso a tudo
            cursor.execute("""
                SELECT id FROM usuarios WHERE perfil = 'admin'
            """)
            admin_users = cursor.fetchall()
            
            modulos = [
                'dashboard', 'insumos', 'equipamentos_eletricos', 'equipamentos_manuais',
                'movimentacoes', 'obras_departamentos', 'responsaveis', 'relatorios',
                'logs_auditoria', 'usuarios', 'configuracoes', 'qr_codigos',
                'reservas', 'manutencao_preventiva', 'dashboard_executivo',
                'localizacao', 'gestao_financeira', 'analise_preditiva'
            ]
            
            for admin in admin_users:
                admin_id = admin[0] if isinstance(admin, (tuple, list)) else admin['id']
                for modulo in modulos:
                    cursor.execute("""
                        INSERT INTO permissoes_modulos (usuario_id, modulo, acesso)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (usuario_id, modulo) DO NOTHING
                    """, (admin_id, modulo, True))
            
            # Gestores têm acesso limitado
            cursor.execute("""
                SELECT id FROM usuarios WHERE perfil = 'gestor'
            """)
            gestor_users = cursor.fetchall()
            
            modulos_gestor = [
                'dashboard', 'insumos', 'equipamentos_eletricos', 'equipamentos_manuais',
                'movimentacoes', 'obras_departamentos', 'responsaveis', 'relatorios'
            ]
            
            for gestor in gestor_users:
                gestor_id = gestor[0] if isinstance(gestor, (tuple, list)) else gestor['id']
                for modulo in modulos_gestor:
                    cursor.execute("""
                        INSERT INTO permissoes_modulos (usuario_id, modulo, acesso)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (usuario_id, modulo) DO NOTHING
                    """, (gestor_id, modulo, True))
            
            # Usuários normais têm acesso básico
            cursor.execute("""
                SELECT id FROM usuarios WHERE perfil = 'usuario'
            """)
            usuario_users = cursor.fetchall()
            
            modulos_usuario = ['dashboard', 'insumos', 'equipamentos_eletricos', 'equipamentos_manuais']
            
            for usuario in usuario_users:
                usuario_id = usuario[0] if isinstance(usuario, (tuple, list)) else usuario['id']
                for modulo in modulos_usuario:
                    cursor.execute("""
                        INSERT INTO permissoes_modulos (usuario_id, modulo, acesso)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (usuario_id, modulo) DO NOTHING
                    """, (usuario_id, modulo, True))
            
            conn.commit()
            print("✅ Permissões padrão configuradas!")
            
        else:
            print("✅ Tabela permissoes_modulos já existe!")
            
    except Exception as e:
        print(f"❌ Erro ao criar tabela: {e}")
        conn.rollback()

if __name__ == '__main__':
    create_permissions_table()