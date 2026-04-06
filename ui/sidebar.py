"""Sidebar component for file upload and column mapping.

Handles CSV/XLSX file uploads, column mapping interface, and data processing trigger.
"""

import streamlit as st
import pandas as pd
from utils.helpers import salvar_transacoes_importadas
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
                        df_mapped = st.session_state.raw_df[
                            [date_col, title_col, amount_col]
                        ].copy()
                        df_mapped.columns = ["Data", "Descrição", "Valor"]
                        df_mapped["Pessoa"] = "Arquivo"
                        df_mapped["Categoria_Manual"] = None

                        importados = st.session_state.get("transacoes_importadas", [])

                        def _row_key(row: dict) -> tuple:
                            valor_raw = str(row.get("Valor", "0")).replace(",", ".")
                            valor_num = pd.to_numeric(valor_raw, errors="coerce")
                            return (
                                str(row.get("Data", "")).strip(),
                                str(row.get("Descrição", "")).strip().lower(),
                                float(valor_num) if pd.notna(valor_num) else 0.0,
                            )

                        existing_keys = {_row_key(item) for item in importados}
                        novos = 0

                        for row in df_mapped.to_dict("records"):
                            key = _row_key(row)
                            if key not in existing_keys:
                                importados.append(row)
                                existing_keys.add(key)
                                novos += 1

                        st.session_state.transacoes_importadas = importados
                        salvar_transacoes_importadas()
                        st.session_state.df_from_upload = None
                        processar_dados()
                        st.session_state.raw_df = None
                        st.sidebar.success(
                            f"✅ Extrato processado com sucesso! Novos registros: {novos}"
                        )
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
    st.sidebar.caption("💾 Seus dados são salvos automaticamente neste dispositivo.")

    n_importadas = len(st.session_state.get("transacoes_importadas", []))
    st.sidebar.metric("Transações Importadas", n_importadas)

    if n_importadas > 0 and st.sidebar.button(
        "🗑️ Limpar Importadas", use_container_width=True
    ):
        st.session_state.transacoes_importadas = []
        salvar_transacoes_importadas()
        processar_dados()
        st.sidebar.success("Transações importadas foram removidas.")
        st.rerun()
