import psycopg2
import sys

def excluir_usuarios_teste():
    conn_str = "postgresql://neondb_owner:npg_3MA2EfyzKIqn@ep-green-bread-adwnbwg4-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    
    try:
        conn = psycopg2.connect(conn_str)
        cursor = conn.cursor()
        
        # Listar usuários atuais
        cursor.execute("SELECT id, nome, email, perfil FROM usuarios ORDER BY id")
        usuarios = cursor.fetchall()
        
        print("=== USUARIOS ATUAIS ===")
        for u in usuarios:
            print(f"ID: {u[0]} | Nome: {u[1]} | Email: {u[2]} | Perfil: {u[3]}")
        
        # Identificar usuários de teste
        usuarios_teste = []
        for u in usuarios:
            nome_lower = str(u[1]).lower()
            email_lower = str(u[2]).lower()
            if any(termo in nome_lower for termo in ['teste', 'test']):
                usuarios_teste.append(u)
            elif any(termo in email_lower for termo in ['teste', 'test']):
                usuarios_teste.append(u)
        
        print(f"\n=== USUARIOS DE TESTE IDENTIFICADOS ({len(usuarios_teste)}) ===")
        for u in usuarios_teste:
            print(f"ID: {u[0]} | Nome: {u[1]} | Email: {u[2]}")
        
        # Excluir cada usuário de teste
        for u in usuarios_teste:
            id_user = u[0]
            nome = u[1]
            
            try:
                print(f"\nExcluindo usuario: {nome} (ID: {id_user})")
                
                # 1. Remover permissões
                cursor.execute("DELETE FROM permissoes_modulos WHERE usuario_id = %s", (id_user,))
                perms_removidas = cursor.rowcount
                print(f"  - Permissoes removidas: {perms_removidas}")
                
                # 2. Remover sessões  
                cursor.execute("DELETE FROM sessoes WHERE usuario_id = %s", (id_user,))
                sessoes_removidas = cursor.rowcount
                print(f"  - Sessoes removidas: {sessoes_removidas}")
                
                # 3. Verificar se há movimentações
                cursor.execute("SELECT COUNT(*) FROM movimentacoes WHERE usuario_id = %s", (id_user,))
                mov_count = cursor.fetchone()[0]
                
                if mov_count > 0:
                    print(f"  - AVISO: Usuario tem {mov_count} movimentacoes associadas")
                    print("  - Definindo usuario como inativo em vez de excluir")
                    cursor.execute("UPDATE usuarios SET ativo = false WHERE id = %s", (id_user,))
                else:
                    # 4. Excluir usuário
                    cursor.execute("DELETE FROM usuarios WHERE id = %s", (id_user,))
                    print(f"  - Usuario excluido completamente")
                
            except Exception as e:
                print(f"  - ERRO: {e}")
                continue
        
        # Confirmar mudanças
        conn.commit()
        print("\n=== OPERACAO CONCLUIDA ===")
        
        # Verificar resultado
        cursor.execute("SELECT id, nome, email, ativo FROM usuarios ORDER BY id")
        usuarios_finais = cursor.fetchall()
        
        print(f"\nUsuarios finais ({len(usuarios_finais)}):")
        for u in usuarios_finais:
            status = "ATIVO" if u[3] else "INATIVO"
            print(f"  ID: {u[0]} | {u[1]} | {u[2]} | {status}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Erro geral: {e}")

if __name__ == "__main__":
    excluir_usuarios_teste()