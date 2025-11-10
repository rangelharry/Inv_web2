import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.connection import db

try:
    conn = db.get_connection()
    cursor = conn.cursor()
    
    print("Criando tabela permissoes_modulos...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS permissoes_modulos (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
            modulo TEXT NOT NULL,
            acesso BOOLEAN DEFAULT FALSE,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(usuario_id, modulo)
        );
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_permissoes_usuario_modulo 
        ON permissoes_modulos(usuario_id, modulo);
    """)
    
    conn.commit()
    print("✅ Tabela permissoes_modulos criada com sucesso!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    if 'conn' in locals():
        conn.rollback()