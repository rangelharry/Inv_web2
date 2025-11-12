"""
Script para atualizar permissões de usuários com novos módulos
Auditoria Avançada e Backup Automático
"""
import os
import sys
sys.path.insert(0, r'e:\GITHUB\Inv_web2')

try:
    from database.connection import db
    
    print("=== ATUALIZANDO PERMISSÕES DOS USUÁRIOS ===\n")
    
    conn = db.get_connection()
    if not conn:
        print("❌ Erro: Não foi possível conectar ao banco")
        exit(1)
    
    cursor = conn.cursor()
    
    # 1. Verificar se tabela de permissões existe
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'permissoes_modulos'
        )
    """)
    
    tabela_existe = cursor.fetchone()[0]
    
    if not tabela_existe:
        print("📝 Criando tabela de permissões...")
        cursor.execute("""
            CREATE TABLE permissoes_modulos (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER REFERENCES usuarios(id),
                modulo VARCHAR(100) NOT NULL,
                acesso BOOLEAN DEFAULT TRUE,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(usuario_id, modulo)
            )
        """)
        print("✅ Tabela de permissões criada")
    
    # 2. Buscar todos os usuários
    cursor.execute("SELECT id, nome, perfil FROM usuarios WHERE ativo = TRUE")
    usuarios = cursor.fetchall()
    
    print(f"📋 Encontrados {len(usuarios)} usuários ativos")
    
    # 3. Novos módulos para adicionar
    novos_modulos = [
        'auditoria_avancada',  # Auditoria Completa
        'backup_automatico'    # Backup Automático
    ]
    
    # 4. Atualizar permissões por usuário
    for usuario in usuarios:
        if isinstance(usuario, dict):
            user_id = usuario['id']
            nome = usuario['nome']
            perfil = usuario['perfil']
        else:
            user_id = usuario[0]
            nome = usuario[1]
            perfil = usuario[2]
        
        print(f"\n👤 Atualizando usuário: {nome} (Perfil: {perfil})")
        
        for modulo in novos_modulos:
            # Definir acesso baseado no perfil
            if perfil == 'admin':
                acesso = True  # Admin tem acesso a tudo
            elif perfil == 'gestor':
                # Gestor tem acesso à auditoria mas não ao backup
                acesso = True if modulo == 'auditoria_avancada' else False
            else:
                acesso = False  # Usuário comum não tem acesso
            
            # Inserir ou atualizar permissão
            cursor.execute("""
                INSERT INTO permissoes_modulos (usuario_id, modulo, acesso)
                VALUES (%s, %s, %s)
                ON CONFLICT (usuario_id, modulo) 
                DO UPDATE SET acesso = EXCLUDED.acesso
            """, (user_id, modulo, acesso))
            
            status = "✅ Permitido" if acesso else "❌ Negado"
            print(f"   {modulo}: {status}")
    
    # 5. Verificar permissões atualizadas
    print("\n📊 RESUMO DAS PERMISSÕES:")
    cursor.execute("""
        SELECT u.nome, u.perfil, p.modulo, p.acesso
        FROM usuarios u
        JOIN permissoes_modulos p ON u.id = p.usuario_id
        WHERE p.modulo IN ('auditoria_avancada', 'backup_automatico')
        ORDER BY u.nome, p.modulo
    """)
    
    permissoes = cursor.fetchall()
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
        
        status = "✅" if acesso else "❌"
        print(f"{status} {nome} ({perfil}) → {modulo}")
    
    # Confirmar alterações
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n🎉 PERMISSÕES ATUALIZADAS COM SUCESSO!")
    print("\nℹ️ Regras aplicadas:")
    print("   👑 Admin: Acesso completo a Auditoria + Backup")
    print("   👨‍💼 Gestor: Acesso apenas à Auditoria")
    print("   👤 Usuário: Sem acesso aos novos módulos")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    if 'conn' in locals():
        conn.rollback()
        conn.close()