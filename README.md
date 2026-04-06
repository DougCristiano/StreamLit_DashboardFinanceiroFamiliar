# Dashboard Financeiro Familiar

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![Tests](https://img.shields.io/badge/tests-27%20passed-brightgreen.svg)](https://github.com/your-repo/tests)
[![Code Coverage](https://img.shields.io/badge/coverage-94%25%20(utils)-brightgreen.svg)](htmlcov/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Aplicativo interativo em Python com **Streamlit** para gerenciar e analisar finanças familiares de forma simples e visual.

## ✨ Destaques

- 📊 **Dashboard Profissional** — KPIs em tempo real, gráficos interativos com Plotly
- 📥 **Upload Inteligente** — Auto-detecção de colunas em extratos CSV/XLSX
- 🏷️ **Categorização Automática** — Classificação inteligente de despesas
- 👥 **Gestão Familiar** — Rastreamento de gastos por membro
- 💰 **Orçamento** — Planejamento mensal com análise orçado vs. real
- 🔁 **Despesas Recorrentes** — Controle de assinaturas e contas fixas
- 🎨 **Interface Refinada** — Tema light profissional, responsivo
- ✅ **Testes Automatizados** — Suite de 27 testes unitários com 94% coverage

## 📋 Abas da Aplicação

| Aba | Descrição |
|-----|-----------|
| **📊 Dashboard** | Visão geral com KPIs: receitas, despesas, saldo e saldo acumulado |
| **📝 Lançamentos** | Entrada manual de transações com histórico recente |
| **👥 Família** | Gerenciamento de membros familiares e resumo financeiro |
| **📋 Extrato** | Tabela completa com filtros avançados (data, tipo, categoria, pessoa, busca) |
| **⚙️ Configurações** | Gerenciamento de categorias, orçamento mensal e despesas recorrentes |

## 🚀 Quick Start

### Pré-requisitos
- Python 3.12+
- pip ou pipenv

### Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/seu-usuario/dashboard-financeiro.git
   cd dashboard-financeiro
   ```

2. **Crie um ambiente virtual:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate  # Windows
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Execute a aplicação:**
   ```bash
   streamlit run app.py
   ```

   O app será aberto em `http://localhost:8501` 🎉

### Usando `mise` (Opcional)

Se preferir gerenciar versões do Python automaticamente:

```bash
curl https://mise.run | sh
mise use python@3.12
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 📁 Estrutura do Projeto

```
.
├── app.py                      # Ponto de entrada da aplicação
├── requirements.txt            # Dependências (versões fixadas)
├── pytest.ini                  # Configuração de testes
├── .editorconfig               # Padronização de IDE
├── .pre-commit-config.yaml     # Git hooks automáticos
├── rules.md                    # Guias e convenções de código
├── README.md                   # Este arquivo
├── CONTRIBUTING.md             # Guia de contribuição
│
├── ui/                         # Componentes Streamlit
│   ├── __init__.py
│   ├── sidebar.py              # Upload de arquivo e mapeamento
│   └── tabs.py                 # Dashboard, lançamentos, família, extrato, config
│
├── utils/                      # Lógica de negócio
│   ├── __init__.py
│   ├── helpers.py              # Funções utilitárias (normalização, JSON, categorização)
│   └── processing.py           # Pipeline de processamento de dados
│
├── styles/                     # CSS e temas
│   └── main.css                # Tema profissional light com dark mode support
│
├── tests/                      # Suite de testes
│   ├── __init__.py
│   ├── conftest.py             # Fixtures e configuração
│   ├── test_helpers.py         # Testes para utils.helpers (18 testes)
│   └── test_processing.py      # Testes para utils.processing (9 testes)
│
├── htmlcov/                    # Relatório de cobertura (gerado)
└── .venv/                      # Ambiente virtual (não versionado)
```

## 🔧 Desenvolvimento

### Dependências de Desenvolvimento

Ferramentas para código quality já estão no `requirements.txt`:

```bash
black             # Formatação automática
flake8            # Linting
mypy              # Type checking
pytest            # Framework de testes
pytest-cov        # Cobertura de testes
```

### Fluxo de Desenvolvimento

1. **Formatar código:**
   ```bash
   .venv/bin/black utils/ ui/ app.py
   ```

2. **Validar linting (sem E501 - linha comprida):**
   ```bash
   .venv/bin/flake8 utils/ ui/ app.py --ignore=E203,W503,E501
   ```

3. **Verificar tipos:**
   ```bash
   .venv/bin/mypy utils/ ui/ app.py --ignore-missing-imports
   ```

4. **Rodar testes:**
   ```bash
   .venv/bin/pytest tests/ -v
   ```

5. **Ver cobertura de testes:**
   ```bash
   .venv/bin/pytest tests/ --cov=utils --cov=ui --cov-report=html
   # Abre htmlcov/index.html no navegador
   ```

6. **Configurar pre-commit hooks (recomendado):**
   ```bash
   pip install pre-commit
   pre-commit install
   # Executa automaticamente black, flake8, mypy antes de commits
   ```

### Padrões de Código

- **Estilo:** PEP 8 com black (100 caracteres por linha)
- **Type Hints:** Obrigatório para funções públicas
- **Docstrings:** Google style format
- **Commits:** Usar conventional commits (feat:, fix:, docs:, etc)

Veja [rules.md](rules.md) para detalhes completos.

## 🧪 Testes

Suite de 27 testes automatizados cobrindo:

- ✅ Normalização de texto (5 testes)
- ✅ Operações JSON (4 testes)
- ✅ Categorização de despesas (9 testes)
- ✅ Processamento de dados (9 testes)

### Executar testes:

```bash
# Todos os testes
pytest tests/

# Com cobertura
pytest tests/ --cov=utils --cov=ui --cov-report=html

# Testes específicos
pytest tests/test_helpers.py::TestNormalizarTexto -v
```

### Resultado Esperado:

```
======================== 27 passed in 0.38s ========================
Coverage: 94% em utils/processing.py, 55% em utils/helpers.py
```

## 📊 Dados e Privacidade

- **Armazenamento Local:** Todos os dados (transações, categorias, membros) são salvos em JSON local
- **Nenhuma API Externa:** O app funciona totalmente offline
- **⚠️ Aviso de Segurança:** Para dados financeiros reais, considere:
  - Usar banco de dados criptografado
  - Adicionar autenticação multi-usuário
  - Implementar criptografia de dados sensíveis
  - Fazer backup regularmente

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'streamlit'"
```bash
# Reinstale dependências
pip install -r requirements.txt
```

### Erro: "Port 8501 already in use"
```bash
# Use outra porta
streamlit run app.py --server.port 8502
```

### Dados não aparecem após upload
1. Certifique-se que o CSV/XLSX tem as colunas corretas
2. Verifique se a data está em formato válido (YYYY-MM-DD ou semelhante)
3. Veja a seção "Pré-visualização" na barra lateral

## 🤝 Contribuindo

Contribuições são bem-vindas! Veja [CONTRIBUTING.md](CONTRIBUTING.md) para:

- Como reportar bugs
- Como sugerir features
- Como fazer pull requests
- Padrões de código

## 📝 Licença

Este projeto está sob a licença [MIT](LICENSE).

## 📞 Suporte

- 📖 Abra uma [issue](https://github.com/seu-usuario/dashboard-financeiro/issues)
- 💬 Discuta no [discussions](https://github.com/seu-usuario/dashboard-financeiro/discussions)


