"""
Configurações para deployment
Detecta automaticamente se está rodando localmente ou na nuvem
"""
import os
import streamlit as st

# Detectar ambiente
IS_LOCAL = os.getenv('STREAMLIT_SHARING') is None and os.getenv('HEROKU') is None

def get_database_path():
    """Retorna o caminho do banco de dados baseado no ambiente"""
    if IS_LOCAL:
        return "inventory.db"
    else:
        # Em produção, usar banco em memória ou caminho temporário
        return "/tmp/inventory.db" if os.path.exists("/tmp") else "inventory.db"

def get_secret(key_path, default_value=None):
    """Obtém segredos do Streamlit Cloud ou variáveis de ambiente"""
    try:
        if hasattr(st, 'secrets'):
            # Navegue através do caminho de chaves (ex: "database.url")
            keys = key_path.split('.')
            value = st.secrets
            for key in keys:
                value = value[key]
            return value
    except:
        pass
    
    # Fallback para variáveis de ambiente
    env_key = key_path.replace('.', '_').upper()
    return os.getenv(env_key, default_value)

def is_production():
    """Verifica se está rodando em produção"""
    return not IS_LOCAL

def get_app_url():
    """Retorna a URL base da aplicação"""
    if IS_LOCAL:
        return "http://localhost:8501"
    else:
        # Para Streamlit Cloud, a URL é fornecida automaticamente
        return os.getenv('STREAMLIT_SERVER_BASE_URL', 'https://sua-app.streamlit.app')