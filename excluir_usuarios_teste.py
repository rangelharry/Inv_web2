#!/usr/bin/env python3
"""
Script para excluir usuários de teste do banco de dados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import db

def listar_usuarios():
    """Lista todos os usuários do sistema"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, nome, email, perfil, ativo FROM usuarios ORDER BY id")
        usuarios = cursor.fetchall()
        
        print("=== USUARIOS CADASTRADOS ===")
        for i, usuario in enumerate(usuarios, 1):
            id_user, nome, email, perfil, ativo = usuario
            status = "ATIVO" if ativo else "INATIVO"
            print(f"{i}. ID: {id_user} | Nome: {nome} | Email: {email} | Perfil: {perfil} | Status: {status}")
        
        cursor.close()
        conn.close()
        
        return usuarios
        
    except Exception as e:
        print(f"Erro ao listar usuarios: {e}")
        return []

def excluir_usuario(id_usuario, nome_usuario):
    """Exclui um usuário específico e seus dados relacionados"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Remover permissões
        cursor.execute("DELETE FROM permissoes_modulos WHERE usuario_id = %s", (id_usuario,))
        perms_removidas = cursor.rowcount
        
        # Remover sessões
        cursor.execute("DELETE FROM sessoes WHERE usuario_id = %s", (id_usuario,))
        sessoes_removidas = cursor.rowcount
        
        # Remover usuário
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (id_usuario,))
        usuario_removido = cursor.rowcount
        
        if usuario_removido > 0:
            conn.commit()
            print(f"✓ Usuario '{nome_usuario}' (ID: {id_usuario}) excluido com sucesso!")
            print(f"  - {perms_removidas} permissoes removidas")
            print(f"  - {sessoes_removidas} sessoes removidas")
            return True
        else:
            print(f"✗ Usuario '{nome_usuario}' (ID: {id_usuario}) nao encontrado!")
            return False
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"✗ Erro ao excluir usuario '{nome_usuario}': {e}")
        return False

def main():
    print("=== SCRIPT DE EXCLUSAO DE USUARIOS TESTE ===\n")
    
    # Listar usuários existentes
    usuarios = listar_usuarios()
    
    if not usuarios:
        print("Nenhum usuario encontrado!")
        return
    
    print(f"\nTotal de usuarios: {len(usuarios)}")
    
    # Identificar usuários de teste automaticamente
    usuarios_teste = []
    termos_teste = ['teste', 'test', 'demo', 'example', 'admin', 'temp', 'sample']
    
    for usuario in usuarios:
        id_user, nome, email, perfil, ativo = usuario
        nome_lower = str(nome).lower() if nome else ""
        email_lower = str(email).lower() if email else ""
        
        # Verificar se é usuário de teste
        if any(termo in nome_lower for termo in termos_teste):
            usuarios_teste.append((id_user, nome, email, "nome"))
        elif any(termo in email_lower for termo in termos_teste):
            usuarios_teste.append((id_user, nome, email, "email"))
    
    if usuarios_teste:
        print(f"\n=== USUARIOS DE TESTE IDENTIFICADOS ({len(usuarios_teste)}) ===")
        for i, (id_user, nome, email, motivo) in enumerate(usuarios_teste, 1):
            print(f"{i}. ID: {id_user} | Nome: {nome} | Email: {email} | Motivo: {motivo}")
        
        # Confirmar exclusão
        resposta = input(f"\nDeseja excluir {len(usuarios_teste)} usuarios de teste? (s/N): ").lower()
        
        if resposta == 's':
            print(f"\nExcluindo {len(usuarios_teste)} usuarios de teste...")
            excluidos = 0
            
            for id_user, nome, email, motivo in usuarios_teste:
                if excluir_usuario(id_user, nome):
                    excluidos += 1
            
            print(f"\n=== RESULTADO ===")
            print(f"✓ {excluidos} usuarios de teste excluidos com sucesso!")
            print(f"✓ {len(usuarios) - excluidos} usuarios restantes")
        else:
            print("Operacao cancelada pelo usuario.")
    else:
        print("\n✓ Nenhum usuario de teste identificado automaticamente.")
        
        # Permitir exclusão manual
        resposta = input("\nDeseja excluir algum usuario manualmente? (s/N): ").lower()
        
        if resposta == 's':
            try:
                id_para_excluir = input("Digite o ID do usuario para excluir: ")
                id_para_excluir = int(id_para_excluir)
                
                # Encontrar o usuário
                usuario_encontrado = None
                for usuario in usuarios:
                    if usuario[0] == id_para_excluir:
                        usuario_encontrado = usuario
                        break
                
                if usuario_encontrado:
                    nome_usuario = usuario_encontrado[1]
                    confirmar = input(f"Confirma exclusao de '{nome_usuario}' (ID: {id_para_excluir})? (s/N): ").lower()
                    
                    if confirmar == 's':
                        excluir_usuario(id_para_excluir, nome_usuario)
                    else:
                        print("Exclusao cancelada.")
                else:
                    print(f"Usuario com ID {id_para_excluir} nao encontrado!")
                    
            except ValueError:
                print("ID invalido! Digite apenas numeros.")
            except Exception as e:
                print(f"Erro: {e}")

if __name__ == "__main__":
    main()