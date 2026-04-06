"""Utilities module for Dashboard Financeiro Familiar.

Provides helper functions for text processing, JSON management, expense categorization,
CSS loading, and Streamlit session state initialization.
"""

import streamlit as st
import json
import os
import unicodedata
import pandas as pd
from typing import Any, Dict, List

# --- File Constants ---
CATEGORIES_FILE: str = "categorias.json"
MEMBROS_FILE: str = "membros.json"
TRANSACOES_FILE: str = "transacoes.json"
TRANSACOES_IMPORTADAS_FILE: str = "transacoes_importadas.json"
DIVIDAS_FILE: str = "dividas.json"
INVESTIMENTOS_FILE: str = "investimentos.json"
METAS_RESERVA_FILE: str = "metas_reserva.json"
ORCAMENTO_FILE: str = "orcamento_mensal.json"
RECORRENTES_FILE: str = "despesas_recorrentes.json"

# --- Utility Functions ---


def normalizar_texto(texto: str) -> str:
    """Normalize text to lowercase and remove accents.

    Args:
        texto: Text to normalize.

    Returns:
        Normalized text without accents, in lowercase.
    """
    texto = str(texto).lower()
    texto = "".join(
        c
        for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return texto


def load_json(file: str, default: Any) -> Any:
    """Load JSON file, returning default if not found.

    Args:
        file: Path to JSON file.
        default: Default value to return if file doesn't exist.

    Returns:
        Parsed JSON content or default value.
    """
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default
    return default


def save_json(file: str, data: Any) -> None:
    """Save data to JSON file with pretty printing.

    Args:
        file: Path to JSON file.
        data: Data to serialize and save.
    """
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def categorizar_despesa(descricao: str, categories: Dict[str, List[str]]) -> str:
    """Categorize expense description using keyword matching.

    Args:
        descricao: Transaction description/title.
        categories: Dictionary mapping category names to keyword lists.

    Returns:
        Matched category name, or 'Outros' (Others) if no match found.
    """
    desc_norm = normalizar_texto(descricao)
    for categoria, palavras_chave in categories.items():
        if any(palavra in desc_norm for palavra in palavras_chave):
            return categoria
    return "Outros"


def load_css(file_path: str) -> None:
    """Load and inject CSS from file into Streamlit app.

    Args:
        file_path: Path to CSS file.
    """
    try:
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def salvar_transacoes() -> None:
    """Persist manual transactions to disk from session state."""
    save_json(TRANSACOES_FILE, st.session_state.transacoes)


def carregar_transacoes() -> List[Dict[str, Any]]:
    """Load manual transactions from disk.

    Returns:
        List of transaction dictionaries from transacoes.json.
    """
    return load_json(TRANSACOES_FILE, [])


def salvar_transacoes_importadas() -> None:
    """Persist imported transactions list to disk from session state."""
    save_json(TRANSACOES_IMPORTADAS_FILE, st.session_state.transacoes_importadas)


def carregar_transacoes_importadas() -> List[Dict[str, Any]]:
    """Load imported transactions from disk.

    Returns:
        List of imported transaction dictionaries.
    """
    return load_json(TRANSACOES_IMPORTADAS_FILE, [])


def salvar_orcamento_mensal() -> None:
    """Persist monthly budget dictionary to disk from session state."""
    save_json(ORCAMENTO_FILE, st.session_state.orcamento_mensal)


def carregar_orcamento_mensal() -> Dict[str, float]:
    """Load monthly budget dictionary from disk.

    Returns:
        Dictionary with category budgets.
    """
    data = load_json(ORCAMENTO_FILE, {})
    if not isinstance(data, dict):
        return {}
    output: Dict[str, float] = {}
    for key, value in data.items():
        try:
            output[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return output


def salvar_despesas_recorrentes() -> None:
    """Persist recurring expenses table to disk from session state."""
    records = st.session_state.despesas_recorrentes.to_dict("records")
    save_json(RECORRENTES_FILE, records)


def carregar_despesas_recorrentes() -> pd.DataFrame:
    """Load recurring expenses table from disk.

    Returns:
        DataFrame with recurring expenses columns.
    """
    records = load_json(RECORRENTES_FILE, [])
    if not isinstance(records, list):
        records = []
    df = pd.DataFrame(records)
    expected_cols = ["Descrição", "Valor", "Categoria"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = pd.NA
    return df[expected_cols]


def salvar_dividas() -> None:
    """Persist debts list to disk from session state."""
    save_json(DIVIDAS_FILE, st.session_state.dividas)


def carregar_dividas() -> List[Dict[str, Any]]:
    """Load debts list from disk.

    Returns:
        List of debt dictionaries from dividas.json.
    """
    return load_json(DIVIDAS_FILE, [])


def salvar_investimentos() -> None:
    """Persist investments list to disk from session state."""
    save_json(INVESTIMENTOS_FILE, st.session_state.investimentos)


def carregar_investimentos() -> List[Dict[str, Any]]:
    """Load investments list from disk.

    Returns:
        List of investment dictionaries from investimentos.json.
    """
    return load_json(INVESTIMENTOS_FILE, [])


def salvar_metas_reserva() -> None:
    """Persist reserve goals list to disk from session state."""
    save_json(METAS_RESERVA_FILE, st.session_state.metas_reserva)


def carregar_metas_reserva() -> List[Dict[str, Any]]:
    """Load reserve goals list from disk.

    Returns:
        List of reserve goal dictionaries from metas_reserva.json.
    """
    return load_json(METAS_RESERVA_FILE, [])


def initialize_session_state() -> None:
    """Initialize all required session state variables.

    Sets up default dictionaries and DataFrames for categories, family members,
    transactions, and data processing. Called once at app startup.
    """

    if "categories" not in st.session_state:
        st.session_state.categories = load_json(
            CATEGORIES_FILE,
            {
                "Alimentação": [
                    "ifood",
                    "restaurante",
                    "mercado",
                    "supermercado",
                    "lanche",
                ],
                "Transporte": [
                    "uber",
                    "99",
                    "transporte",
                    "gasolina",
                    "combustivel",
                    "onibus",
                ],
                "Moradia": ["aluguel", "condominio", "luz", "internet", "agua", "vivo"],
                "Saúde": [
                    "farmacia",
                    "remedio",
                    "medico",
                    "plano de saude",
                    "drog",
                    "cityfarma",
                ],
                "Lazer": [
                    "cinema",
                    "show",
                    "bar",
                    "viagem",
                    "lazer",
                    "netflix",
                    "spotify",
                ],
                "Educação": ["escola", "faculdade", "curso", "livros"],
                "Compras": ["lojas", "roupas", "compras", "amazon", "mercado livre"],
                "Outros": [],
            },
        )

    if "membros_familia" not in st.session_state:
        st.session_state.membros_familia = load_json(MEMBROS_FILE, ["Família Conjunta"])

    if "transacoes" not in st.session_state:
        st.session_state.transacoes = carregar_transacoes()

    if "transacoes_importadas" not in st.session_state:
        st.session_state.transacoes_importadas = carregar_transacoes_importadas()

    if "dividas" not in st.session_state:
        st.session_state.dividas = carregar_dividas()

    if "investimentos" not in st.session_state:
        st.session_state.investimentos = carregar_investimentos()

    if "metas_reserva" not in st.session_state:
        st.session_state.metas_reserva = carregar_metas_reserva()

    if "df_transacoes" not in st.session_state:
        st.session_state.df_transacoes = None

    if "df_from_upload" not in st.session_state:
        st.session_state.df_from_upload = None

    if "raw_df" not in st.session_state:
        st.session_state.raw_df = None

    if "column_map" not in st.session_state:
        st.session_state.column_map = {"date": None, "title": None, "amount": None}

    if "orcamento_mensal" not in st.session_state:
        default_orcamento = {cat: 0.0 for cat in st.session_state.categories.keys()}
        saved_orcamento = carregar_orcamento_mensal()
        default_orcamento.update(saved_orcamento)
        st.session_state.orcamento_mensal = default_orcamento

    if "despesas_recorrentes" not in st.session_state:
        st.session_state.despesas_recorrentes = carregar_despesas_recorrentes()

    if "_despesas_recorrentes_snapshot" not in st.session_state:
        st.session_state._despesas_recorrentes_snapshot = (
            st.session_state.despesas_recorrentes.to_dict("records")
        )

    if "renda_liquida" not in st.session_state:
        st.session_state.renda_liquida = 0.0

    if "tema" not in st.session_state:
        st.session_state.tema = "Neutro"

    if "bucket_map" not in st.session_state:
        st.session_state.bucket_map = {}

    if "_ultimo_sonho" not in st.session_state:
        st.session_state._ultimo_sonho = {}
