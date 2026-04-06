"""Lançamentos tab — manual transaction entry and history."""

import streamlit as st
from datetime import date
from utils.helpers import salvar_transacoes
from utils.processing import processar_dados


def render_lancamentos() -> None:
    """Render manual transaction entry form and recent history.

    Displays:
    - Form for adding income/expense transactions
    - Recent transactions table (last 20)
    - Danger zone to clear all manual transactions
    """
    st.markdown("##### Novo Lançamento")

    membros = st.session_state.get("membros_familia", ["Família Conjunta"])
    if not membros:
        membros = ["Família Conjunta"]
    categorias = list(st.session_state.categories.keys())

    with st.form("form_lancamento", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            tipo = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
            pessoa = st.selectbox("Pessoa", membros)

        with col2:
            descricao = st.text_input(
                "Descrição", placeholder="Ex: Salário, Conta de Luz"
            )
            valor_str = st.text_input("Valor (R$)", placeholder="Ex: 1500,00")

        with col3:
            data_lanc = st.date_input("Data", date.today())
            if tipo == "Despesa":
                categoria = st.selectbox("Categoria", categorias)
            else:
                categoria = st.text_input(
                    "Fonte da Receita",
                    placeholder="Ex: Salário, Freelance",
                    value="Salário",
                )

        submitted = st.form_submit_button(
            "➕ Adicionar Lançamento", use_container_width=True, type="primary"
        )

        if submitted:
            if descricao and valor_str:
                try:
                    valor = float(valor_str.replace(",", "."))
                    valor_final = valor if tipo == "Receita" else -valor

                    nova_transacao = {
                        "Data": str(data_lanc),
                        "Descrição": descricao,
                        "Valor": valor_final,
                        "Categoria_Manual": (
                            categoria if tipo == "Despesa" else "Receita"
                        ),
                        "Pessoa": pessoa,
                    }

                    st.session_state.transacoes.append(nova_transacao)
                    salvar_transacoes()
                    processar_dados()

                    st.success(
                        f"{'Receita' if tipo == 'Receita' else 'Despesa'} de R$ {valor:,.2f} adicionada!"
                    )
                    st.rerun()
                except ValueError:
                    st.error("Valor inválido. Use apenas números (ex: 1500,50).")
            else:
                st.error("Preencha descrição e valor.")

    st.markdown("##### Transações Recentes")

    df = st.session_state.df_transacoes
    if df is not None and not df.empty:
        df_display = df.head(20)[
            ["Data", "Tipo", "Descrição", "Categoria", "Pessoa", "ValorAbs"]
        ].copy()
        df_display["Data"] = df_display["Data"].dt.strftime("%d/%m/%Y")
        df_display.columns = ["Data", "Tipo", "Descrição", "Categoria", "Pessoa", "Valor (R$)"]

        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Valor (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
            },
        )
    else:
        st.info("Nenhuma transação registrada ainda.")

    with st.expander("⚠️ Zona de Perigo"):
        if st.button("🗑️ Limpar TODAS as transações manuais", type="secondary"):
            st.session_state.transacoes = []
            salvar_transacoes()
            processar_dados()
            st.rerun()
