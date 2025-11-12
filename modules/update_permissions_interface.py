"""
Interface para Atualizar Permissões dos Novos Módulos
Use este módulo no Streamlit para atualizar permissões
"""

import streamlit as st
from database.connection import db

def show_update_permissions_interface():
    """Interface para atualizar permissões dos usuários"""
    st.title("🔐 Atualizar Permissões - Novos Módulos")
    
    st.info("Esta interface atualiza as permissões dos usuários para os novos módulos de **Auditoria Completa** e **Backup Automático**.")
    
    try:
        conn = db.get_connection()
        if not conn:
            st.error("Erro ao conectar com o banco de dados")
            return
        
        cursor = conn.cursor()
        
        # Verificar usuários existentes
        cursor.execute("SELECT id, nome, perfil FROM usuarios WHERE ativo = TRUE")
        usuarios = cursor.fetchall()
        
        if not usuarios:
            st.warning("Nenhum usuário encontrado")
            return
        
        st.subheader("👥 Usuários Existentes")
        
        # Mostrar usuários atuais
        for usuario in usuarios:
            if isinstance(usuario, dict):
                user_id = usuario['id']
                nome = usuario['nome']
                perfil = usuario['perfil']
            else:
                user_id = usuario[0]
                nome = usuario[1]
                perfil = usuario[2]
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{nome}**")
            with col2:
                st.write(f"Perfil: {perfil}")
            with col3:
                # Definir permissões baseado no perfil
                if perfil == 'admin':
                    auditoria = "✅ Sim"
                    backup = "✅ Sim"
                elif perfil == 'gestor':
                    auditoria = "✅ Sim"
                    backup = "❌ Não"
                else:
                    auditoria = "❌ Não"
                    backup = "❌ Não"
                
                st.write(f"Auditoria: {auditoria}")
                st.write(f"Backup: {backup}")
        
        st.divider()
        
        # Botão para atualizar permissões
        if st.button("🔄 Atualizar Permissões dos Usuários", type="primary"):
            with st.spinner("Atualizando permissões..."):
                
                # 1. Criar tabela de permissões se não existir
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS permissoes_modulos (
                        id SERIAL PRIMARY KEY,
                        usuario_id INTEGER REFERENCES usuarios(id),
                        modulo VARCHAR(100) NOT NULL,
                        acesso BOOLEAN DEFAULT TRUE,
                        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(usuario_id, modulo)
                    )
                """)
                
                # 2. Novos módulos
                novos_modulos = ['auditoria_avancada', 'backup_automatico']
                
                # 3. Atualizar permissões
                success_count = 0
                
                for usuario in usuarios:
                    if isinstance(usuario, dict):
                        user_id = usuario['id']
                        perfil = usuario['perfil']
                    else:
                        user_id = usuario[0]
                        perfil = usuario[2]
                    
                    for modulo in novos_modulos:
                        # Definir acesso baseado no perfil
                        if perfil == 'admin':
                            acesso = True
                        elif perfil == 'gestor':
                            acesso = True if modulo == 'auditoria_avancada' else False
                        else:
                            acesso = False
                        
                        # Inserir ou atualizar
                        cursor.execute("""
                            INSERT INTO permissoes_modulos (usuario_id, modulo, acesso)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (usuario_id, modulo) 
                            DO UPDATE SET acesso = EXCLUDED.acesso
                        """, (user_id, modulo, acesso))
                        
                        success_count += 1
                
                conn.commit()
                
                st.success(f"✅ Permissões atualizadas! {success_count} registros processados.")
                
                # Mostrar resumo das permissões
                st.subheader("📋 Resumo das Permissões Aplicadas")
                
                cursor.execute("""
                    SELECT u.nome, u.perfil, p.modulo, p.acesso
                    FROM usuarios u
                    JOIN permissoes_modulos p ON u.id = p.usuario_id
                    WHERE p.modulo IN ('auditoria_avancada', 'backup_automatico')
                    ORDER BY u.nome, p.modulo
                """)
                
                permissoes = cursor.fetchall()
                
                if permissoes:
                    for perm in permissoes:
                        if isinstance(perm, dict):
                            nome = perm['nome']
                            perfil = perm['perfil']
                            modulo = perm['modulo']
                            acesso = perm['acesso']
                        else:
                            nome = perm[0]
                            perfil = perm[1]
                            modulo = perm[2]
                            acesso = perm[3]
                        
                        modulo_nome = "Auditoria Completa" if modulo == 'auditoria_avancada' else "Backup Automático"
                        status = "✅ Permitido" if acesso else "❌ Negado"
                        
                        st.write(f"**{nome}** ({perfil}) → {modulo_nome}: {status}")
                
                st.info("🔄 **Reinicie a aplicação** para que as novas permissões tenham efeito.")
        
        cursor.close()
        
    except Exception as e:
        st.error(f"Erro ao atualizar permissões: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    show_update_permissions_interface()