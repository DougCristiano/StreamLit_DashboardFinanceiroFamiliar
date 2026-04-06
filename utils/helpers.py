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
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
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

    if "df_transacoes" not in st.session_state:
        st.session_state.df_transacoes = None

    if "df_from_upload" not in st.session_state:
        st.session_state.df_from_upload = None

    if "raw_df" not in st.session_state:
        st.session_state.raw_df = None

    if "column_map" not in st.session_state:
        st.session_state.column_map = {"date": None, "title": None, "amount": None}

    if "orcamento_mensal" not in st.session_state:
        st.session_state.orcamento_mensal = {
            cat: 0.0 for cat in st.session_state.categories.keys()
        }

    if "despesas_recorrentes" not in st.session_state:
        st.session_state.despesas_recorrentes = pd.DataFrame(
            columns=["Descrição", "Valor", "Categoria"]
        )
