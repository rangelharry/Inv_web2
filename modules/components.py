"""
Sistema de Inventário Web - Componentes Reutilizáveis
Componentes de UI comuns para melhorar a experiência do usuário
"""

import streamlit as st
from typing import Any

def confirmation_dialog(
    message: str, 
    confirm_text: str = "Confirmar",
    cancel_text: str = "Cancelar",
    danger: bool = True,
    key: str = "confirm_dialog"
) -> bool:
    """
    Modal de confirmação para ações importantes
    
    Args:
        message: Mensagem de confirmação
        confirm_text: Texto do botão de confirmação
        cancel_text: Texto do botão de cancelamento
        danger: Se True, usa estilo de perigo (vermelho)
        key: Chave única para o componente
    
    Returns:
        bool: True se confirmado, False caso contrário
    """
    # Usar columns para centralizar o modal
    _, col2, _ = st.columns([1, 2, 1])
    
    with col2:
        st.warning(f"⚠️ {message}")
        
        col_cancel, col_confirm = st.columns(2)
        
        with col_cancel:
            if st.button(cancel_text, key=f"{key}_cancel", use_container_width=True):
                return False
        
        with col_confirm:
            button_type = "primary" if not danger else "primary"
            if st.button(
                confirm_text, 
                key=f"{key}_confirm", 
                type=button_type,
                use_container_width=True
            ):
                return True
    
    return False

def delete_confirmation_dialog(
    item_name: str,
    item_type: str = "item",
    key: str = "delete_confirm"
) -> bool:
    """
    Modal específico para confirmação de exclusão
    
    Args:
        item_name: Nome do item a ser excluído
        item_type: Tipo do item (ex: "responsável", "equipamento")
        key: Chave única para o componente
    
    Returns:
        bool: True se confirmado, False caso contrário
    """
    message = f"Tem certeza que deseja excluir o {item_type} '{item_name}'?\n\nEsta ação não pode ser desfeita!"
    
    return confirmation_dialog(
        message=message,
        confirm_text="🗑️ Excluir",
        cancel_text="❌ Cancelar",
        danger=True,
        key=key
    )

def loading_spinner(text: str = "Carregando..."):
    """
    Spinner de carregamento com texto customizado
    
    Args:
        text: Texto a ser exibido durante o carregamento
    """
    return st.spinner(text)

def success_message(message: str, duration: int = 3):
    """
    Mensagem de sucesso com auto-dismiss
    
    Args:
        message: Mensagem de sucesso
        duration: Duração em segundos (não implementado no Streamlit)
    """
    st.success(f"✅ {message}")

def error_message(message: str):
    """
    Mensagem de erro padronizada
    
    Args:
        message: Mensagem de erro
    """
    st.error(f"❌ {message}")

def warning_message(message: str):
    """
    Mensagem de aviso padronizada
    
    Args:
        message: Mensagem de aviso
    """
    st.warning(f"⚠️ {message}")

def info_message(message: str):
    """
    Mensagem de informação padronizada
    
    Args:
        message: Mensagem de informação
    """
    st.info(f"ℹ️ {message}")

def validate_required_fields(fields: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Valida campos obrigatórios
    
    Args:
        fields: Dicionário com nome do campo como chave e valor como value
    
    Returns:
        tuple: (is_valid, list_of_errors)
    """
    errors: list[str] = []
    
    for field_name, field_value in fields.items():
        if not field_value or (isinstance(field_value, str) and field_value.strip() == ""):
            errors.append(f"Campo '{field_name}' é obrigatório")
    
    return len(errors) == 0, errors

def validate_email(email: str) -> bool:
    """
    Valida formato de email
    
    Args:
        email: Email a ser validado
    
    Returns:
        bool: True se válido, False caso contrário
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """
    Valida formato de telefone brasileiro
    
    Args:
        phone: Telefone a ser validado
    
    Returns:
        bool: True se válido, False caso contrário
    """
    import re
    # Aceita formatos: (11) 99999-9999, 11999999999, etc.
    pattern = r'^\(?([0-9]{2})\)?[-. ]?([0-9]{4,5})[-. ]?([0-9]{4})$'
    return re.match(pattern, phone) is not None

def format_currency(value: float) -> str:
    """
    Formata valor como moeda brasileira
    
    Args:
        value: Valor numérico
    
    Returns:
        str: Valor formatado como R$ X.XXX,XX
    """
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def safe_float_input(
    label: str, 
    value: float = 0.0, 
    min_value: float = 0.0,
    format_str: str = "%.2f",
    **kwargs: Any
) -> float:
    """
    Input numérico seguro que trata erros de conversão
    
    Args:
        label: Label do input
        value: Valor padrão
        min_value: Valor mínimo
        format_str: Formato de exibição
        **kwargs: Outros argumentos para st.number_input
    
    Returns:
        float: Valor digitado ou 0.0 em caso de erro
    """
    try:
        return st.number_input(
            label,
            value=value,
            min_value=min_value,
            format=format_str,
            **kwargs
        )
    except (ValueError, TypeError):
        return 0.0

def pagination_controls(
    total_items: int,
    items_per_page: int = 20,
    current_page: int = 1
) -> tuple[int, int, int]:
    """
    Controles de paginação
    
    Args:
        total_items: Total de itens
        items_per_page: Itens por página
        current_page: Página atual
    
    Returns:
        tuple: (current_page, offset, total_pages)
    """
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("⏮️ Primeiro", disabled=current_page <= 1):
            current_page = 1
    
    with col2:
        if st.button("◀️ Anterior", disabled=current_page <= 1):
            current_page = max(1, current_page - 1)
    
    with col3:
        st.write(f"Página {current_page} de {total_pages} ({total_items} itens)")
    
    with col4:
        if st.button("▶️ Próximo", disabled=current_page >= total_pages):
            current_page = min(total_pages, current_page + 1)
    
    with col5:
        if st.button("⏭️ Último", disabled=current_page >= total_pages):
            current_page = total_pages
    
    offset = (current_page - 1) * items_per_page
    
    return current_page, offset, total_pages