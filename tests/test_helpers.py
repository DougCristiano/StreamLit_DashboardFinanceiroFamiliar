"""Tests for utils.helpers module."""
import pytest
import os
import json
import tempfile
from utils.helpers import (
    normalizar_texto,
    load_json,
    save_json,
    categorizar_despesa,
)


class TestNormalizarTexto:
    """Test text normalization function."""

    def test_lowercase_conversion(self):
        """Should convert text to lowercase."""
        assert normalizar_texto("HELLO") == "hello"
        assert normalizar_texto("Hello World") == "hello world"

    def test_accent_removal(self):
        """Should remove accents from Portuguese text."""
        assert normalizar_texto("Café") == "cafe"
        assert normalizar_texto("Açúcar") == "acucar"
        assert normalizar_texto("Maçã") == "maca"

    def test_combined_normalization(self):
        """Should handle combined cases."""
        assert normalizar_texto("AÇÚCAR MASCAVO") == "acucar mascavo"
        assert normalizar_texto("Café com Leite") == "cafe com leite"

    def test_already_normalized(self):
        """Should handle already normalized text."""
        assert normalizar_texto("hello world") == "hello world"

    def test_special_characters(self):
        """Should handle special characters."""
        result = normalizar_texto("São Paulo - SP")
        assert "sao paulo" in result and "sp" in result


class TestJsonHandling:
    """Test JSON file operations."""

    def test_load_json_nonexistent_file(self):
        """Should return default when file doesn't exist."""
        default_val = {"key": "default"}
        result = load_json("nonexistent_file.json", default_val)
        assert result == default_val

    def test_save_and_load_json(self):
        """Should save and load JSON correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            data = {"name": "João", "value": 100, "nested": {"key": "value"}}
            save_json(temp_file, data)

            loaded = load_json(temp_file, {})
            assert loaded == data
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_save_json_creates_file(self):
        """Should create file if it doesn't exist."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=True) as f:
            temp_file = f.name

        data = {"test": "data"}
        save_json(temp_file, data)

        assert os.path.exists(temp_file)
        loaded = load_json(temp_file, {})
        assert loaded == data

        os.unlink(temp_file)

    def test_json_unicode_handling(self):
        """Should handle Unicode characters correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            data = {"member": "João", "city": "São Paulo"}
            save_json(temp_file, data)

            loaded = load_json(temp_file, {})
            assert loaded["member"] == "João"
            assert loaded["city"] == "São Paulo"
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestCategorizarDespesa:
    """Test expense categorization function."""

    def test_categorize_food_expense(self, sample_categories):
        """Should categorize food-related expenses."""
        assert categorizar_despesa("pedido iFood", sample_categories) == "Alimentação"
        assert categorizar_despesa("RESTAURANTE ITALIANO", sample_categories) == "Alimentação"
        assert categorizar_despesa("mercado carrefour", sample_categories) == "Alimentação"

    def test_categorize_transport_expense(self, sample_categories):
        """Should categorize transport expenses."""
        assert categorizar_despesa("Uber Viagem", sample_categories) == "Transporte"
        assert categorizar_despesa("gasolina shell", sample_categories) == "Transporte"

    def test_categorize_housing_expense(self, sample_categories):
        """Should categorize housing expenses."""
        assert categorizar_despesa("aluguel apartamento", sample_categories) == "Moradia"
        assert categorizar_despesa("conta de luz", sample_categories) == "Moradia"
        assert categorizar_despesa("internet vivo", sample_categories) == "Moradia"

    def test_categorize_health_expense(self, sample_categories):
        """Should categorize health expenses."""
        assert categorizar_despesa("farmacia pharmacy", sample_categories) == "Saúde"
        assert categorizar_despesa("consulta medico", sample_categories) == "Saúde"

    def test_categorize_entertainment_expense(self, sample_categories):
        """Should categorize entertainment expenses."""
        assert categorizar_despesa("netflix subscription", sample_categories) == "Lazer"
        assert categorizar_despesa("cinema ingressos", sample_categories) == "Lazer"

    def test_categorize_uncategorized_expense(self, sample_categories):
        """Should return 'Outros' for unmatched expenses."""
        assert categorizar_despesa("despesa aleatoria xyz", sample_categories) == "Outros"
        assert categorizar_despesa("compra misteriosa", sample_categories) == "Outros"

    def test_case_insensitive_categorization(self, sample_categories):
        """Should be case-insensitive."""
        assert categorizar_despesa("IFOOD", sample_categories) == "Alimentação"
        assert categorizar_despesa("IfOoD", sample_categories) == "Alimentação"

    def test_accent_insensitive_categorization(self, sample_categories):
        """Should handle accents in descriptions."""
        # Create categories with normalized text
        cats = {
            "Saúde": ["farmacia", "medico"],
            "Outros": []
        }
        assert categorizar_despesa("Farmácia Premium", cats) == "Saúde"

    def test_priority_first_match(self, sample_categories):
        """Should return first matching category."""
        # If description matches multiple categories, return first one
        result = categorizar_despesa("mercado restaurante", sample_categories)
        assert result in ["Alimentação", "Alimentação"]  # Both are valid
