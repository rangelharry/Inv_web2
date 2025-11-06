# 📦 Sistema de Inventário Web

Sistema completo de gestão de inventário desenvolvido em Python com Streamlit.

## 🚀 Funcionalidades

### 📋 Gestão de Inventário
- **Insumos**: Controle de materiais consumíveis
- **Equipamentos Elétricos**: Gestão de equipamentos elétricos
- **Equipamentos Manuais**: Controle de ferramentas manuais

### 📊 Movimentações
- **Entrada**: Registro de chegada de materiais/equipamentos
- **Saída**: Controle de saída para obras/departamentos
- **Histórico completo**: Rastreamento de todas as movimentações

### 🏗️ Gestão Operacional
- **Obras**: Cadastro e controle de obras/projetos
- **Responsáveis**: Gestão de responsáveis pelas movimentações
- **Relatórios**: Relatórios detalhados e dashboards

### 👥 Sistema de Usuários
- **Autenticação segura**: Login com criptografia bcrypt
- **Perfis de acesso**: Diferentes níveis de permissão
- **Logs de auditoria**: Registro de todas as ações

## 🛠️ Tecnologias

- **Python 3.11+**
- **Streamlit**: Interface web responsiva
- **SQLite**: Banco de dados
- **Pandas**: Manipulação de dados
- **Plotly**: Gráficos interativos
- **bcrypt**: Criptografia de senhas

## 📦 Instalação

### Pré-requisitos
- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)

### Passos de instalação

1. **Clone o repositório**
```bash
git clone https://github.com/rangelharry/Inv_web2.git
cd Inv_web2
```

2. **Crie um ambiente virtual**
```bash
python -m venv .venv
```

3. **Ative o ambiente virtual**

Windows:
```bash
.venv\Scripts\activate
```

Linux/Mac:
```bash
source .venv/bin/activate
```

4. **Instale as dependências**
```bash
pip install -r requirements.txt
```

5. **Execute a aplicação**
```bash
streamlit run main.py
```

## 🌐 Deploy

### Streamlit Cloud

1. **Faça fork do repositório** no GitHub
2. **Acesse** [share.streamlit.io](https://share.streamlit.io)
3. **Conecte sua conta GitHub**
4. **Selecione o repositório** `Inv_web2`
5. **Defina o arquivo principal** como `main.py`
6. **Deploy automático**

### Heroku

1. **Instale o Heroku CLI**
2. **Faça login**
```bash
heroku login
```

3. **Crie uma nova app**
```bash
heroku create seu-app-inventario
```

4. **Configure as variáveis de ambiente**
```bash
heroku config:set PYTHONPATH=.
```

5. **Deploy**
```bash
git push heroku main
```

## 📊 Dashboard

O sistema inclui um dashboard completo com:

- **Métricas gerais**: Total de itens, movimentações, obras ativas
- **Gráficos interativos**: Distribuição de equipamentos, movimentações por tipo
- **Alertas**: Itens com estoque baixo
- **Ações rápidas**: Acesso direto às funcionalidades principais

## 🔐 Acesso Padrão

**Usuário**: admin@inventario.com  
**Senha**: admin123

## 📁 Estrutura do Projeto

```
Inv_web2/
├── main.py                 # Aplicação principal
├── requirements.txt        # Dependências
├── Procfile               # Configuração Heroku
├── setup.sh               # Script de setup
├── .streamlit/
│   └── config.toml        # Configuração Streamlit
├── database/
│   ├── __init__.py
│   ├── connection.py      # Conexão SQLite
│   └── schema.py          # Estrutura do banco
├── modules/
│   ├── auth.py            # Autenticação
│   ├── insumos.py         # Gestão de insumos
│   ├── equipamentos_eletricos.py
│   ├── equipamentos_manuais.py
│   ├── movimentacoes.py   # Movimentações
│   ├── movimentacao_modal.py  # Modais de movimentação
│   ├── obras.py           # Gestão de obras
│   ├── responsaveis.py    # Gestão de responsáveis
│   ├── relatorios.py      # Relatórios
│   ├── logs_auditoria.py  # Logs do sistema
│   └── usuarios.py        # Gestão de usuários
└── data/                  # Dados iniciais (JSON)
```

## 🤝 Contribuição

1. **Faça um fork** do projeto
2. **Crie uma branch** para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit suas mudanças** (`git commit -m 'Add some AmazingFeature'`)
4. **Push para a branch** (`git push origin feature/AmazingFeature`)
5. **Abra um Pull Request**

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Contato

**Desenvolvedor**: Harry Rangel  
**GitHub**: [@rangelharry](https://github.com/rangelharry)

---

⭐ Se este projeto foi útil para você, considere dar uma estrela no repositório!