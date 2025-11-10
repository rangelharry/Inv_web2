import os
import sys

# Garantir que o diretório do projeto esteja no path para importar modules locais
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database.connection import db


def get_almoxarifado_id(conn):
    cur = conn.cursor()
    cur.execute("SELECT id FROM obras WHERE codigo = %s", ('ALM-001',))
    res = cur.fetchone()
    if res:
        # pode ser dict (RealDictCursor) ou tupla
        if isinstance(res, dict):
            return res.get('id')
        return res[0]
    # cria a obra
    cur.execute(
        """
        INSERT INTO obras (codigo, nome, status, criado_por)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        ('ALM-001', 'Almoxarifado', 'Ativo', 1)
    )
    res = cur.fetchone()
    if res:
        if isinstance(res, dict):
            return res.get('id')
        return res[0]
    return None


def main():
    conn = db.get_connection()
    cur = conn.cursor()

    alm_id = get_almoxarifado_id(conn)
    print(f"ALMOXARIFADO id = {alm_id}")

    # Atualizar insumos
    cur.execute("UPDATE insumos SET localizacao = %s WHERE localizacao ILIKE %s", ('Almoxarifado - ALM-001', 'Almoxarifado%'))
    updated_insumos = cur.rowcount
    print(f"Insumos atualizados: {updated_insumos}")

    # Atualizar equipamentos eletricos
    cur.execute("UPDATE equipamentos_eletricos SET localizacao = %s, obra_atual_id = %s WHERE localizacao ILIKE %s OR obra_atual_id IS NULL", ('Almoxarifado - ALM-001', alm_id, 'Almoxarifado%'))
    updated_eletricos = cur.rowcount
    print(f"Equipamentos elétricos atualizados: {updated_eletricos}")

    # Atualizar equipamentos manuais
    cur.execute("UPDATE equipamentos_manuais SET localizacao = %s, obra_atual_id = %s WHERE localizacao ILIKE %s OR obra_atual_id IS NULL", ('Almoxarifado - ALM-001', alm_id, 'Almoxarifado%'))
    updated_manuais = cur.rowcount
    print(f"Equipamentos manuais atualizados: {updated_manuais}")

    conn.commit()
    print("Commit realizado com sucesso.")

if __name__ == '__main__':
    main()
