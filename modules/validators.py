"""
Sistema de Inventário Web - Módulo de Validação
Validações centralizadas para garantir integridade dos dados
"""

import re
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime

class ValidationError(Exception):
    """Exceção customizada para erros de validação"""
    pass

class DataValidator:
    """Classe para validação de dados do sistema"""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """
        Valida formato de email
        
        Args:
            email: Email a ser validado
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not email or not email.strip():
            return False, "Email é obrigatório"
        
        email = email.strip()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return False, "Formato de email inválido"
        
        if len(email) > 255:
            return False, "Email muito longo (máximo 255 caracteres)"
        
        return True, None
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
        """
        Valida formato de telefone brasileiro
        
        Args:
            phone: Telefone a ser validado
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not phone or not phone.strip():
            return False, "Telefone é obrigatório"
        
        phone = phone.strip()
        # Remove caracteres especiais para validação
        phone_clean = re.sub(r'[^\d]', '', phone)
        
        # Valida se tem 10 ou 11 dígitos
        if len(phone_clean) not in [10, 11]:
            return False, "Telefone deve ter 10 ou 11 dígitos"
        
        # Valida formato básico
        pattern = r'^\(?([0-9]{2})\)?[-. ]?([0-9]{4,5})[-. ]?([0-9]{4})$'
        if not re.match(pattern, phone):
            return False, "Formato de telefone inválido. Use: (11) 99999-9999"
        
        return True, None
    
    @staticmethod
    def validate_cpf(cpf: str) -> Tuple[bool, Optional[str]]:
        """
        Valida CPF brasileiro
        
        Args:
            cpf: CPF a ser validado
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not cpf:
            return True, None  # CPF é opcional
        
        cpf = cpf.strip()
        # Remove caracteres especiais
        cpf_clean = re.sub(r'[^\d]', '', cpf)
        
        if len(cpf_clean) != 11:
            return False, "CPF deve ter 11 dígitos"
        
        # Verifica se todos os dígitos são iguais
        if cpf_clean == cpf_clean[0] * 11:
            return False, "CPF inválido"
        
        # Algoritmo de validação do CPF
        def validate_cpf_algorithm(cpf_digits: str) -> bool:
            # Primeiro dígito verificador
            sum1 = sum(int(cpf_digits[i]) * (10 - i) for i in range(9))
            digit1 = 11 - (sum1 % 11)
            if digit1 >= 10:
                digit1 = 0
            
            # Segundo dígito verificador
            sum2 = sum(int(cpf_digits[i]) * (11 - i) for i in range(10))
            digit2 = 11 - (sum2 % 11)
            if digit2 >= 10:
                digit2 = 0
            
            return int(cpf_digits[9]) == digit1 and int(cpf_digits[10]) == digit2
        
        if not validate_cpf_algorithm(cpf_clean):
            return False, "CPF inválido"
        
        return True, None
    
    @staticmethod
    def validate_required_string(value: str, field_name: str, min_length: int = 1, max_length: int = 255) -> Tuple[bool, Optional[str]]:
        """
        Valida campo de texto obrigatório
        
        Args:
            value: Valor a ser validado
            field_name: Nome do campo para mensagem de erro
            min_length: Comprimento mínimo
            max_length: Comprimento máximo
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not value or not value.strip():
            return False, f"{field_name} é obrigatório"
        
        value = value.strip()
        
        if len(value) < min_length:
            return False, f"{field_name} deve ter pelo menos {min_length} caractere(s)"
        
        if len(value) > max_length:
            return False, f"{field_name} deve ter no máximo {max_length} caracteres"
        
        return True, None
    
    @staticmethod
    def validate_positive_number(value: Any, field_name: str, allow_zero: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Valida número positivo
        
        Args:
            value: Valor a ser validado
            field_name: Nome do campo para mensagem de erro
            allow_zero: Se permite zero
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            num = float(value) if value is not None else 0
        except (ValueError, TypeError):
            return False, f"{field_name} deve ser um número válido"
        
        if not allow_zero and num <= 0:
            return False, f"{field_name} deve ser maior que zero"
        elif allow_zero and num < 0:
            return False, f"{field_name} não pode ser negativo"
        
        return True, None
    
    @staticmethod
    def validate_date(date_str: str, field_name: str, required: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Valida data no formato YYYY-MM-DD
        
        Args:
            date_str: Data em string
            field_name: Nome do campo para mensagem de erro
            required: Se é obrigatório
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not date_str or not date_str.strip():
            if required:
                return False, f"{field_name} é obrigatório"
            return True, None
        
        try:
            datetime.strptime(date_str.strip(), '%Y-%m-%d')
            return True, None
        except ValueError:
            return False, f"{field_name} deve estar no formato YYYY-MM-DD"
    
    @staticmethod
    def validate_codigo(codigo: str, field_name: str = "Código") -> Tuple[bool, Optional[str]]:
        """
        Valida código do sistema (ex: INS-001, EQ-001)
        
        Args:
            codigo: Código a ser validado
            field_name: Nome do campo para mensagem de erro
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not codigo or not codigo.strip():
            return False, f"{field_name} é obrigatório"
        
        codigo = codigo.strip().upper()
        
        # Valida formato básico: 2-3 letras, hífen, 3-4 números
        pattern = r'^[A-Z]{2,3}-\d{3,4}$'
        if not re.match(pattern, codigo):
            return False, f"{field_name} deve estar no formato ABC-001 ou AB-0001"
        
        return True, None
    
    @staticmethod
    def validate_form_data(data: Dict[str, Any], validation_rules: Dict[str, Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Valida dados de formulário com base em regras
        
        Args:
            data: Dados do formulário
            validation_rules: Regras de validação
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        errors: List[str] = []
        
        for field_name, rules in validation_rules.items():
            field_value = data.get(field_name)
            field_display_name = rules.get('display_name', field_name)
            
            # Verificar se é obrigatório
            if rules.get('required', False):
                is_valid, error = DataValidator.validate_required_string(
                    str(field_value or ''), 
                    field_display_name,
                    rules.get('min_length', 1),
                    rules.get('max_length', 255)
                )
                if not is_valid and error is not None:
                    errors.append(error)
                    continue
            
            # Validações específicas por tipo
            field_type = rules.get('type')
            
            if field_type == 'email' and field_value:
                is_valid, error = DataValidator.validate_email(str(field_value))
                if not is_valid and error is not None:
                    errors.append(error)
            
            elif field_type == 'phone' and field_value:
                is_valid, error = DataValidator.validate_phone(str(field_value))
                if not is_valid and error is not None:
                    errors.append(error)
            
            elif field_type == 'cpf' and field_value:
                is_valid, error = DataValidator.validate_cpf(str(field_value))
                if not is_valid and error is not None:
                    errors.append(error)
            
            elif field_type == 'number' and field_value is not None:
                is_valid, error = DataValidator.validate_positive_number(
                    field_value,
                    field_display_name,
                    rules.get('allow_zero', True)
                )
                if not is_valid and error is not None:
                    errors.append(error)
            
            elif field_type == 'date' and field_value:
                is_valid, error = DataValidator.validate_date(
                    str(field_value),
                    field_display_name,
                    rules.get('required', False)
                )
                if not is_valid and error is not None:
                    errors.append(error)
            
            elif field_type == 'codigo' and field_value:
                is_valid, error = DataValidator.validate_codigo(
                    str(field_value),
                    field_display_name
                )
                if not is_valid and error is not None:
                    errors.append(error)
        
        return len(errors) == 0, errors

# Regras de validação predefinidas para entidades do sistema
VALIDATION_RULES: Dict[str, Dict[str, Dict[str, Any]]] = {
    'usuario': {
        'nome': {
            'required': True,
            'type': 'string',
            'display_name': 'Nome',
            'min_length': 2,
            'max_length': 100
        },
        'email': {
            'required': True,
            'type': 'email',
            'display_name': 'Email'
        },
        'password': {
            'required': True,
            'type': 'string',
            'display_name': 'Senha',
            'min_length': 6,
            'max_length': 50
        }
    },
    'responsavel': {
        'nome': {
            'required': True,
            'type': 'string',
            'display_name': 'Nome',
            'min_length': 2,
            'max_length': 100
        },
        'cargo': {
            'required': True,
            'type': 'string',
            'display_name': 'Cargo',
            'min_length': 2,
            'max_length': 100
        },
        'email': {
            'required': True,
            'type': 'email',
            'display_name': 'Email'
        },
        'telefone': {
            'required': True,
            'type': 'phone',
            'display_name': 'Telefone'
        },
        'cpf': {
            'required': False,
            'type': 'cpf',
            'display_name': 'CPF'
        }
    },
    'insumo': {
        'descricao': {
            'required': True,
            'type': 'string',
            'display_name': 'Descrição',
            'min_length': 2,
            'max_length': 255
        },
        'codigo': {
            'required': True,
            'type': 'codigo',
            'display_name': 'Código'
        },
        'preco_unitario': {
            'required': True,
            'type': 'number',
            'display_name': 'Preço Unitário',
            'allow_zero': False
        }
    }
}