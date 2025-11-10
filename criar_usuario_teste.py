"""
Script para criar usuário de teste com permissões limitadas
Utiliza a mesma configuração de banco do sistema principal
"""

import bcrypt
import os
import streamlit as st
from database.connection import db

def create_test_user():
    """Cria usuário de teste com permissões limitadas"""
    try:
        # Usar a mesma conexão do sistema
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Dados do usuário de teste
        nome = "Usuário Teste"
        email = "teste@exemplo.com"
        senha = "teste123"
        perfil = "usuario"
        
        # Hash da senha
        password_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
        
        # Verificar se já existe
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"Usuário já existe com ID: {existing_user['id']}")
            user_id = existing_user['id']
        else:
            # Criar usuário
            cursor.execute("""
                INSERT INTO usuarios (nome, email, password_hash, perfil, ativo, data_criacao)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id
            """, (nome, email, password_hash.decode('utf-8'), perfil, True))
            
            user_id = cursor.fetchone()['id']
            print(f"Usuário criado com ID: {user_id}")
        
        # Limpar permissões existentes
        cursor.execute("DELETE FROM permissoes_modulos WHERE usuario_id = %s", (user_id,))
        
        # Definir permissões limitadas (apenas equipamentos elétricos e movimentação)
        permissoes = [
            (user_id, 'equipamentos_eletricos', True),
            (user_id, 'movimentacao', True)
        ]
        
        cursor.executemany("""
            INSERT INTO permissoes_modulos (usuario_id, modulo, acesso, criado_em)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        """, permissoes)
        
        # Confirmar alterações
        conn.commit()
        
        print("✅ Usuário de teste criado com sucesso!")
        print(f"📧 Email: {email}")
        print(f"🔑 Senha: {senha}")
        print("🔒 Permissões: Equipamentos Elétricos e Movimentação")
        
        # Verificar permissões
        cursor.execute("""
            SELECT modulo FROM permissoes_modulos 
            WHERE usuario_id = %s
        """, (user_id,))
        
        permissoes_db = cursor.fetchall()
        print(f"📋 Módulos permitidos: {[p['modulo'] for p in permissoes_db]}")
        
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()

if __name__ == "__main__":
    create_test_user()