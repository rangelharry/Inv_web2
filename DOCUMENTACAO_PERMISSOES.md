# 🔐 Sistema de Permissões Granulares - Inventário Web

## 📋 Visão Geral

O Sistema de Inventário Web agora possui um **sistema de controle de acesso granular** que permite configurar individualmente quais módulos cada usuário pode acessar. Isso proporciona maior segurança e controle sobre as funcionalidades do sistema.

## 🏗️ Arquitetura do Sistema

### 📊 Estrutura do Banco de Dados

```sql
CREATE TABLE permissoes_modulos (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
    modulo TEXT NOT NULL,
    acesso BOOLEAN DEFAULT FALSE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(usuario_id, modulo)
);
```

### 🔧 Componentes Principais

1. **Tabela `permissoes_modulos`**: Armazena as permissões específicas de cada usuário
2. **AuthenticationManager** (`auth.py`): Gerencia autenticação e verificação de permissões
3. **Interface de Usuários** (`usuarios.py`): Formulários para configurar permissões
4. **Menu Inteligente** (`main.py`): Filtra opções baseado nas permissões

## 🎯 Funcionalidades

### ✅ **O que o Sistema Faz:**

- ✅ **Controle Granular**: Cada usuário pode ter acesso a módulos específicos
- ✅ **Menu Dinâmico**: O menu lateral mostra apenas os módulos permitidos
- ✅ **Interface Amigável**: Checkboxes para selecionar módulos na criação/edição de usuários
- ✅ **Segurança**: Bloqueio de acesso a módulos não autorizados
- ✅ **Dashboard Universal**: Dashboard sempre acessível para todos os usuários
- ✅ **Perfis Padrão**: Permissões automáticas baseadas no perfil do usuário

### 📋 **Módulos Disponíveis:**

1. **Dashboard** (sempre acessível)
2. **Insumos**
3. **Equipamentos Elétricos**
4. **Equipamentos Manuais**
5. **Movimentação**
6. **Obras/Departamentos**
7. **Responsáveis**
8. **Relatórios**
9. **Logs de Auditoria**
10. **Usuários**
11. **Configurações**
12. **QR/Códigos de Barras**
13. **Reservas**
14. **Manutenção Preventiva**
15. **Dashboard Executivo**
16. **Localização**
17. **Gestão Financeira**
18. **Análise Preditiva**
19. **Gestão de Subcontratados**
20. **Relatórios Customizáveis**
21. **Métricas Performance**
22. **Backup e Recovery**
23. **LGPD/Compliance**
24. **Orçamentos e Cotações**
25. **Sistema de Faturamento**
26. **Integração ERP/SAP**

## 👥 Como Usar

### 🆕 **Criando Usuário com Permissões Específicas:**

1. **Acesse o módulo "Usuários"** (apenas admins e gestores)
2. **Clique em "Novo Usuário"**
3. **Preencha os dados básicos** (nome, email, senha, perfil)
4. **Na seção "Permissões de Acesso aos Módulos"**:
   - Marque os checkboxes dos módulos que o usuário deve acessar
   - As permissões padrão são aplicadas automaticamente baseadas no perfil
5. **Clique em "Criar Usuário"**

### ✏️ **Editando Permissões de Usuário Existente:**

1. **Na lista de usuários**, clique no botão **"✏️"** 
2. **Ajuste as permissões** marcando/desmarcando os módulos
3. **Clique em "💾 Salvar"**

### 👀 **Verificando Permissões:**

- O **menu lateral** mostra apenas os módulos permitidos para o usuário logado
- **Admins** sempre veem todos os módulos
- **Dashboard** está sempre disponível para todos

## 🧪 Exemplo Prático

### 📝 **Caso de Uso: "Usuário Teste"**

Criamos um usuário de exemplo com permissões limitadas:

```
📧 Email: teste@exemplo.com
🔑 Senha: teste123
🔒 Permissões: Equipamentos Elétricos e Movimentação
```

**Resultado esperado:**
- ✅ **Dashboard**: Sempre acessível
- ✅ **Equipamentos Elétricos**: PERMITIDO
- ✅ **Movimentação**: PERMITIDO  
- ❌ **Usuários**: NEGADO
- ❌ **Relatórios**: NEGADO
- ❌ **Insumos**: NEGADO

## 🔧 API de Desenvolvimento

### 📚 **Funções Principais:**

```python
# Verificar se usuário tem acesso a um módulo
auth_manager.check_module_permission(user_id, 'equipamentos_eletricos')

# Obter todas as permissões de um usuário  
permissions = auth_manager.get_user_module_permissions(user_id)

# Atualizar permissões de usuário
auth_manager.update_user_module_permissions(user_id, {
    'equipamentos_eletricos': True,
    'movimentacao': True,
    'usuarios': False
})
```

### 🎯 **Perfis e Permissões Padrão:**

- **Admin**: Acesso total a todos os módulos
- **Gestor**: Acesso a módulos operacionais e relatórios
- **Usuário**: Acesso básico (Dashboard, Insumos, Equipamentos)

## 🛡️ Segurança

### 🔒 **Características de Segurança:**

1. **Validação no Backend**: Permissões verificadas no servidor
2. **Menu Filtrado**: Interface mostra apenas opções autorizadas
3. **Fallback Seguro**: Em caso de erro, acesso é negado
4. **Dashboard Universal**: Mantém acesso básico para todos
5. **Auditoria**: Todas as operações são registradas

## 🚀 Benefícios

### ✨ **Vantagens do Sistema:**

1. **🎯 Segurança Aprimorada**: Controle fino sobre acesso às funcionalidades
2. **👥 Gestão Simplificada**: Interface intuitiva para configurar permissões  
3. **⚡ Performance**: Menu otimizado mostra apenas opções relevantes
4. **🔄 Flexibilidade**: Permissões podem ser alteradas a qualquer momento
5. **📊 Controle Total**: Administradores têm visão completa das permissões
6. **🛡️ Conformidade**: Atende requisitos de segurança e auditoria

## 🔧 Scripts de Utilidade

### 📝 **Scripts Disponíveis:**

```bash
# Criar usuário de teste
python criar_usuario_teste.py

# Verificar permissões de usuário
python testar_permissoes.py

# Criar tabela de permissões
python scripts/create_table_simple.py
```

## 📈 Implementação Bem-Sucedida

✅ **Status**: **IMPLEMENTADO E TESTADO**  
✅ **Banco**: Conectado ao PostgreSQL na nuvem (Neon)  
✅ **Interface**: Formulários funcionais para gerenciar permissões  
✅ **Segurança**: Controle de acesso ativo e validado  
✅ **Teste**: Usuário limitado criado e testado com sucesso  

---

**Desenvolvido para o Sistema de Inventário Web**  
**Data: Novembro 2025**  
**Status: ✅ Produção**