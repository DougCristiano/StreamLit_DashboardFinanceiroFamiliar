"""Shared test fixtures and configuration."""
import pytest
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_categories():
    """Sample category dictionary for testing."""
    return {
        "Alimentação": ["ifood", "restaurante", "mercado", "supermercado"],
        "Transporte": ["uber", "99", "gasolina", "combustivel"],
        "Moradia": ["aluguel", "condominio", "luz", "internet"],
        "Saúde": ["farmacia", "medico", "plano de saude"],
        "Lazer": ["cinema", "show", "bar", "netflix"],
        "Outros": []
    }


@pytest.fixture
def sample_transactions():
    """Sample transaction data for testing."""
    return [
        {
            "Data": "2024-01-01",
            "Descrição": "iFood Delivery",
            "Valor": -50.00,
            "Categoria_Manual": None,
            "Pessoa": "João"
        },
        {
            "Data": "2024-01-02",
            "Descrição": "Salário",
            "Valor": 3000.00,
            "Categoria_Manual": "Receita",
            "Pessoa": "João"
        },
        {
            "Data": "2024-01-03",
            "Descrição": "Aluguel Apartamento",
            "Valor": -1200.00,
            "Categoria_Manual": None,
            "Pessoa": "Família"
        }
    ]
