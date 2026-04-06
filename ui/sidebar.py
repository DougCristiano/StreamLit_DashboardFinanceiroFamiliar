"""Sidebar component for file upload and column mapping.

Handles CSV/XLSX file uploads, column mapping interface, and data processing trigger.
"""

import streamlit as st
import pandas as pd
from utils.processing import processar_dados


def render_sidebar() -> None:
    """Render sidebar with file upload and column mapping interface.

    Displays:
    - File uploader for CSV/XLSX statements
    - Column mapping selection interface
    - Transaction count metric
    """

    st.sidebar.markdown("##### 📂 Importar Extrato")
    st.sidebar.caption("Carregue seu extrato bancário (CSV/XLSX)")
    uploaded_file = st.sidebar.file_uploader(
        "Selecione um arquivo",
        type=["csv", "xlsx"],
        label_visibility="collapsed",
        help="Arquivos aceitos: CSV, XLSX (máx. 10 MB)",
    )

    if uploaded_file is not None:
        # Check file size
        if uploaded_file.size > 10 * 1024 * 1024:  # 10 MB limit
            st.sidebar.error("❌ Arquivo muito grande (máximo 10 MB)")
            st.session_state.raw_df = None
        elif st.session_state.get("last_uploaded_file") != uploaded_file.name:
            try:
                with st.sidebar.spinner("📥 Carregando arquivo..."):
                    if uploaded_file.name.endswith(".csv"):
                        df = pd.read_csv(
                            uploaded_file, sep=",", engine="python", encoding="utf-8"
                        )
                    else:
                        df = pd.read_excel(uploaded_file)

                    if df.empty:
                        st.sidebar.error("❌ Arquivo vazio")
                        st.session_state.raw_df = None
                    else:
                        st.session_state.raw_df = df
                        st.session_state.last_uploaded_file = uploaded_file.name
                        st.session_state.df_from_upload = None
                        st.sidebar.success(
                            f"✅ {uploaded_file.name} carregado ({len(df)} linhas)"
                        )
                        st.rerun()

            except Exception as e:
                st.sidebar.error(f"❌ Erro ao ler: {str(e)[:100]}")
                st.session_state.raw_df = None

    if st.session_state.raw_df is not None:
        st.sidebar.subheader("🔗 Mapeamento das Colunas")
        st.sidebar.info(
            "Identifique as colunas do seu arquivo que correspondem aos campos requeridos."
        )

        columns = st.session_state.raw_df.columns.tolist()

        # Helper function to auto-detect columns
        def _auto_detect_columns():
            """Try to auto-detect column mappings based on common keywords."""
            date_keywords = ["data", "date", "dia", "dt"]
            desc_keywords = [
                "descrição",
                "description",
                "desc",
                "transação",
                "operação",
            ]
            amount_keywords = ["valor", "amount", "vlr", "montante"]

            detected = {"date": None, "title": None, "amount": None}
            cols_lower = [c.lower() for c in columns]

            for keyword in date_keywords:
                matches = [columns[i] for i, c in enumerate(cols_lower) if keyword in c]
                if matches:
                    detected["date"] = matches[0]
                    break

            for keyword in desc_keywords:
                matches = [columns[i] for i, c in enumerate(cols_lower) if keyword in c]
                if matches:
                    detected["title"] = matches[0]
                    break

            for keyword in amount_keywords:
                matches = [columns[i] for i, c in enumerate(cols_lower) if keyword in c]
                if matches:
                    detected["amount"] = matches[0]
                    break

            return detected

        auto_detected = _auto_detect_columns()

        date_col = st.sidebar.selectbox(
            "📅 Coluna da Data",
            options=columns,
            index=(
                columns.index(auto_detected["date"])
                if auto_detected["date"] and auto_detected["date"] in columns
                else None
            ),
            placeholder="Selecione...",
        )
        title_col = st.sidebar.selectbox(
            "📝 Coluna da Descrição",
            options=columns,
            index=(
                columns.index(auto_detected["title"])
                if auto_detected["title"] and auto_detected["title"] in columns
                else None
            ),
            placeholder="Selecione...",
        )
        amount_col = st.sidebar.selectbox(
            "💰 Coluna do Valor",
            options=columns,
            index=(
                columns.index(auto_detected["amount"])
                if auto_detected["amount"] and auto_detected["amount"] in columns
                else None
            ),
            placeholder="Selecione...",
        )

        # Preview of selected columns
        if date_col and title_col and amount_col:
            with st.sidebar.expander("👁️ Pré-visualização", expanded=False):
                preview_cols = [date_col, title_col, amount_col]
                preview_df = st.session_state.raw_df[preview_cols].head(3).copy()
                st.dataframe(preview_df, use_container_width=True, hide_index=True)

        if st.sidebar.button(
            "▶️ Processar Extrato", type="primary", use_container_width=True
        ):
            if date_col and title_col and amount_col:
                with st.sidebar.spinner("⏳ Processando..."):
                    try:
                        st.session_state.column_map = {
                            "date": date_col,
                            "title": title_col,
                            "amount": amount_col,
                        }
                        df_mapped = st.session_state.raw_df[
                            [date_col, title_col, amount_col]
                        ].copy()
                        df_mapped.columns = ["date", "title", "amount"]
                        st.session_state.df_from_upload = df_mapped
                        processar_dados()
                        st.session_state.raw_df = None
                        st.sidebar.success("✅ Extrato processado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.sidebar.error(f"❌ Erro ao processar: {str(e)[:100]}")
            else:
                st.sidebar.error("⚠️ Mapeie as três colunas para continuar.")

    # Info resumo
    st.sidebar.write("---")
    n_transacoes = 0
    if st.session_state.df_transacoes is not None:
        n_transacoes = len(st.session_state.df_transacoes)
    st.sidebar.metric("Total de Transações", n_transacoes)
