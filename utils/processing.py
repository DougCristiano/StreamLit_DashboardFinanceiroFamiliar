"""Data processing module for Dashboard Financeiro Familiar.

Handles combining uploaded data and manual transactions, type conversion,
categorization, and DataFrame aggregation.
"""

import streamlit as st
import pandas as pd
from utils.helpers import categorizar_despesa


def processar_dados() -> None:
    """Combine uploaded and manual transactions into unified DataFrame.

    Merges data from file uploads and manual entries, applies type conversions,
    categorizes transactions, and stores result in st.session_state.df_transacoes.

    Each row contains: Data, Descrição, Valor, Tipo, Categoria, Pessoa, AnoMes.
    - Valor > 0 = Receita (Income)
    - Valor < 0 = Despesa (Expense)
    """
    dfs = []

    # 1. Dados do arquivo enviado pelo usuário
    if st.session_state.df_from_upload is not None:
        df_upload = st.session_state.df_from_upload.copy()
        df_upload.rename(
            columns={"date": "Data", "title": "Descrição", "amount": "Valor"},
            inplace=True,
        )
        df_upload["Pessoa"] = "Arquivo"
        df_upload["Categoria_Manual"] = None
        dfs.append(df_upload)

    # 2. Transações manuais
    if st.session_state.transacoes:
        df_manual = pd.DataFrame(st.session_state.transacoes)
        dfs.append(df_manual)

    # 3. Transações importadas persistidas
    if st.session_state.get("transacoes_importadas"):
        df_importadas = pd.DataFrame(st.session_state.transacoes_importadas)
        dfs.append(df_importadas)

    if not dfs:
        st.session_state.df_transacoes = None
        return

    df = pd.concat(dfs, ignore_index=True)

    # Converter tipos
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df.dropna(subset=["Data"], inplace=True)
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
    df.dropna(subset=["Valor"], inplace=True)
    df = df[df["Valor"] != 0]

    # Tipo: Receita ou Despesa
    df["Tipo"] = df["Valor"].apply(lambda v: "Receita" if v > 0 else "Despesa")

    # Valor absoluto para facilitar gráficos
    df["ValorAbs"] = df["Valor"].abs()

    # AnoMes
    df["AnoMes"] = df["Data"].dt.to_period("M").astype(str)

    # Categoria
    if "Categoria_Manual" in df.columns:
        df["Categoria"] = df.apply(
            lambda row: (
                row["Categoria_Manual"]
                if pd.notnull(row.get("Categoria_Manual"))
                and row.get("Categoria_Manual") != ""
                else (
                    "Receita"
                    if row["Tipo"] == "Receita"
                    else categorizar_despesa(
                        row["Descrição"], st.session_state.categories
                    )
                )
            ),
            axis=1,
        )
    else:
        df["Categoria"] = df.apply(
            lambda row: (
                "Receita"
                if row["Tipo"] == "Receita"
                else categorizar_despesa(row["Descrição"], st.session_state.categories)
            ),
            axis=1,
        )

    # Pessoa
    if "Pessoa" not in df.columns:
        df["Pessoa"] = "Não informada"
    df["Pessoa"] = df["Pessoa"].fillna("Não informada")

    # Limpar colunas temporárias
    df.drop(columns=["Categoria_Manual"], errors="ignore", inplace=True)

    st.session_state.df_transacoes = df.sort_values(
        "Data", ascending=False
    ).reset_index(drop=True)
