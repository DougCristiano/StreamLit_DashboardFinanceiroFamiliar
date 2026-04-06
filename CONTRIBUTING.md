# Guia de Contribuição

Obrigado por querer contribuir para o Dashboard Financeiro Familiar! 🙏

Este documento fornece diretrizes e instruções para contribuir com o projeto.

## Código de Conduta

- Seja respeitoso com outros contribuidores
- Foque em discussões construtivas
- Reporte bugs de forma clara e objetiva
- Respeite diferentes opiniões

## Como Começar

### Reportar Bugs

1. **Verifique se o bug já foi reportado** — busque em [Issues](https://github.com/seu-usuario/dashboard-financeiro/issues)

2. **Crie uma issue descritiva** com:
   - Título claro do problema
   - Passos para reproduzir
   - Comportamento esperado vs. atual
   - Screenshots (se aplicável)
   - Versão do Python e sistema operacional

**Exemplo:**
```
Título: Upload de CSV com acentos não funciona

Erro ao fazer upload: UnicodeDecodeError
Sistema: Ubuntu 22.04, Python 3.12.13

Passos:
1. Selecionar CSV com coluna "Descrição"
2. Clicar em "Processar Extrato"
3. Erro aparece na barra lateral
```

### Sugerir Melhorias

1. **Descreva a melhoria com detalhes:**
   - Qual é o problema atual?
   - Como sua sugestão o resolve?
   - Exemplos de uso

2. **Crie um Discussion** em vez de Issue para features:
   - Permite discussão colaborativa
   - Não implica comprometimento imediato

## Ambiente de Desenvolvimento

### Setup Inicial

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/dashboard-financeiro.git
cd dashboard-financeiro

# Crie um branch para sua feature
git checkout -b feat/minha-feature

# Setup do ambiente
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows

# Instale dependências
pip install -r requirements.txt
```

### Antes de Cada Commit

Execute a pipeline de qualidade:

```bash
# 1. Formatar código
.venv/bin/black utils/ ui/ app.py tests/

# 2. Verificar linting
.venv/bin/flake8 utils/ ui/ app.py tests/ --ignore=E203,W503,E501

# 3. Verificar tipos
.venv/bin/mypy utils/ ui/ app.py --ignore-missing-imports

# 4. Rodar testes
.venv/bin/pytest tests/ -v

# 5. Opcionalmente, verificar cobertura
.venv/bin/pytest tests/ --cov=utils --cov=ui
```

**Ou, use pre-commit hooks (recomendado):**

```bash
pip install pre-commit
pre-commit install
# Agora as verificações rodam automaticamente antes de commit
```

## Padrões de Código

### Type Hints

**Obrigatório para funções públicas:**

```python
from typing import Dict, List, Optional

def categorizar_despesa(
    descricao: str, 
    categories: Dict[str, List[str]]
) -> str:
    """Categorize expense by description."""
    ...
```

### Docstrings

**Formato Google:**

```python
def processar_dados() -> None:
    """Process uploaded and manual transactions.
    
    Combines file uploads and manual entries, applies type conversions,
    categorizes transactions, stores in st.session_state.df_transacoes.
    
    - Valor > 0 = Receita (Income)
    - Valor < 0 = Despesa (Expense)
    """
    pass
```

### Nomes de Variáveis

- snake_case para variáveis e funções: `categorizar_despesa`
- UPPER_SNAKE_CASE para constantes: `CATEGORIES_FILE`
- PascalCase para classes: `MockSessionState`

### Comprimento de Linhas

Máximo 100 caracteres (aplicado automaticamente por black).

## Estrutura de Testes

### Adicionar Novos Testes

1. **Crie arquivo em `tests/test_novo_modulo.py`**

2. **Use fixtures compartilhadas de `conftest.py`**

3. **Organize em classes por funcionalidade:**

```python
class TestNomeFuncionalidade:
    """Test specific functionality."""
    
    def test_caso_feliz(self):
        """Should do X when Y."""
        input_val = "test"
        result = my_function(input_val)
        assert result == expected
    
    def test_caso_erro(self):
        """Should handle error gracefully."""
        with pytest.raises(ValueError):
            my_function("invalid")
```

4. **Mantenha cobertura acima de 80% para novos código**

### Executar Testes

```bash
# Tudo
pytest tests/

# Específico
pytest tests/test_helpers.py::TestNormalizarTexto::test_lowercase_conversion -v

# Com cobertura
pytest tests/ --cov=utils --cov=ui --cov-report=term-missing
```

## Processo de Pull Request

### 1. Crie um branch com nome descritivo:

```bash
git checkout -b feat/adicionar-feature-x
git checkout -b fix/corrigir-bug-y
git checkout -b docs/melhorar-readme
```

### 2. Commit com mensagens claras (Conventional Commits):

```bash
# Feature
git commit -m "feat: adicionar filtro por pessoa no extrato"

# Bug fix
git commit -m "fix: resolver erro de encoding em CSV com acentos"

# Documentation
git commit -m "docs: melhorar instruções de setup"

# Refactor
git commit -m "refactor: simplificar lógica de categorização"

# Tests
git commit -m "test: adicionar testes para utils.processing"
```

### 3. Push para seu fork:

```bash
git push origin feat/adicionar-feature-x
```

### 4. Abra um Pull Request no GitHub com:

- **Título descritivo** do que foi implementado
- **Descrição** explicando:
  - O problema que resolve
  - Como foi implementado
  - Testes adicionados
  - Breaking changes (se houver)

**Exemplo de PR:**

```markdown
# Adicionar Auto-Detecção de Colunas no Upload

## Problema
Usuários frequentemente mapeiam as colunas incorretamente no upload.

## Solução
Implementar auto-detecção de colunas usando keywords:
- "data", "dt", "date" → Data
- "descrição", "description", "desc" → Descrição
- "valor", "amount", "vlr" → Valor

## Testes
- [x] Adicionados 5 testes em test_processing.py
- [x] Cobertura: 94%
- [x] Passou em testes locais

## Checklist
- [x] Código formatado com black
- [x] Sem erros de linting
- [x] Tipos validados com mypy
- [x] Testes passando
- [x] README atualizado (se necessário)
```

### 5. Responda ao feedback

- Discuta qualquer mudança sugerida
- Faça commits adicionais (não force push)
- Mantenha a conversa respeitosa

### Critério de Aceitação

- ✅ Todos os testes passam
- ✅ Cobertura não diminui
- ✅ Código segue padrões (black, flake8, mypy)
- ✅ Documentação atualizada
- ✅ Sem breaking changes sem discussão

## Áreas de Contribuição

### 🐛 Prioridade Alta

- Corrigir bugs reportados
- Melhorar performance
- Aumentar cobertura de testes

### ✨ Bem-vindo

- Novas features (abra Discussion primeiro)
- Melhorias na UI/UX
- Documentação melhorada
- Exemplos adicionais

### 🚫 Evitar por Enquanto

- Refatoração radical sem plano
- Dependências novas sem discussão
- Mudanças de arquitetura major

## Roadmap

Veja [ROADMAP.md](ROADMAP.md) (se existir) para features planejadas.

## Perguntas?

- 💬 Abra uma Discussion
- 📧 Entre em contato via Issue
- 🐦 Siga o projeto para atualizações

---

**Obrigado por contribuir!** 🎉

Seu trabalho ajuda a melhorar o projeto para todos.
