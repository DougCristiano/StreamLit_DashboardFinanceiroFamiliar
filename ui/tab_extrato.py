"""Extrato tab — filtered transaction viewer with summary metrics."""

import streamlit as st


def render_extrato() -> None:
    """Render detailed transaction view with filters.

    Displays:
    - Date range, type, category, person, and text filters
    - Summary metrics for filtered subset
    - Full filtered transaction table
    """
    df = st.session_state.df_transacoes

    if df is None or df.empty:
        st.info("Nenhuma transação disponível.")
        return

    st.markdown("##### Filtros")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        min_data = df["Data"].min().date()
        max_data = df["Data"].max().date()
        data_inicio = st.date_input("De", min_data, key="ext_di")
        data_fim = st.date_input("Até", max_data, key="ext_df")

    with col_f2:
        tipos = st.multiselect(
            "Tipo", ["Receita", "Despesa"], default=["Receita", "Despesa"]
        )

    with col_f3:
        categorias_disp = sorted(df["Categoria"].unique())
        cats_sel = st.multiselect("Categoria", categorias_disp)

    with col_f4:
        pessoas_disp = sorted(df["Pessoa"].unique())
        pessoas_sel = st.multiselect("Pessoa", pessoas_disp)

    pesquisa = st.text_input(
        "🔍 Pesquisar na descrição", placeholder="Digite para filtrar..."
    )

    # Apply filters
    df_filt = df.copy()
    df_filt["_data"] = df_filt["Data"].dt.date
    df_filt = df_filt[
        (df_filt["_data"] >= data_inicio) & (df_filt["_data"] <= data_fim)
    ]
    if tipos:
        df_filt = df_filt[df_filt["Tipo"].isin(tipos)]
    if cats_sel:
        df_filt = df_filt[df_filt["Categoria"].isin(cats_sel)]
    if pessoas_sel:
        df_filt = df_filt[df_filt["Pessoa"].isin(pessoas_sel)]
    if pesquisa:
        df_filt = df_filt[
            df_filt["Descrição"].str.contains(pesquisa, case=False, na=False)
        ]

    df_filt = df_filt.drop(columns=["_data"])

    st.write(f"**{len(df_filt)} transações encontradas**")

    col_r1, col_r2, col_r3 = st.columns(3)
    receitas_filt = df_filt[df_filt["Tipo"] == "Receita"]["ValorAbs"].sum()
    despesas_filt = df_filt[df_filt["Tipo"] == "Despesa"]["ValorAbs"].sum()
    col_r1.metric("RECEITAS", f"R$ {receitas_filt:,.2f}")
    col_r2.metric("DESPESAS", f"R$ {despesas_filt:,.2f}")
    col_r3.metric("SALDO", f"R$ {receitas_filt - despesas_filt:,.2f}")

    df_show = df_filt[
        ["Data", "Tipo", "Descrição", "Categoria", "Pessoa", "ValorAbs"]
    ].copy()
    df_show.columns = ["Data", "Tipo", "Descrição", "Categoria", "Pessoa", "Valor (R$)"]

    st.dataframe(
        df_show,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Valor (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
        },
    )
