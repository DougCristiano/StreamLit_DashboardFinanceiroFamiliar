"""Família tab — family member management and per-person financial summary."""

import streamlit as st
import plotly.express as px
from utils.helpers import save_json, MEMBROS_FILE

_COLORS = {
    "receita": "#16A34A",
    "despesa": "#DC2626",
}


def render_familia() -> None:
    """Render family member management and per-person financial summary.

    Displays:
    - Form to add new family members
    - List of members with per-person balance and delete option
    - Aggregated income/expense/balance table and chart
    """
    st.markdown("##### Membros da Família")

    membros = st.session_state.get("membros_familia", [])

    with st.form("add_membro", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            novo = st.text_input("Nome do novo membro", placeholder="Ex: Douglas, Esposa")
        with col2:
            st.write("")
            add_btn = st.form_submit_button("Adicionar", use_container_width=True)

        if add_btn and novo:
            if novo not in membros:
                membros.append(novo)
                st.session_state.membros_familia = membros
                save_json(MEMBROS_FILE, membros)
                st.success(f"'{novo}' adicionado!")
                st.rerun()
            else:
                st.warning("Membro já existe.")

    if membros:
        for i, membro in enumerate(membros):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown(f"👤 **{membro}**")
            with col2:
                df = st.session_state.df_transacoes
                if df is not None and not df.empty:
                    total_pessoa = df[df["Pessoa"] == membro]["Valor"].sum()
                    color = _COLORS["receita"] if total_pessoa >= 0 else _COLORS["despesa"]
                    st.markdown(
                        f"Saldo: <span style='color:{color}; font-weight:600'>R$ {total_pessoa:,.2f}</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.write("Saldo: --")
            with col3:
                if st.button("Remover", key=f"rm_{i}"):
                    membros.remove(membro)
                    st.session_state.membros_familia = membros
                    save_json(MEMBROS_FILE, membros)
                    st.rerun()
    else:
        st.info("Nenhum membro cadastrado.")

    st.write("---")
    st.markdown("##### Resumo Financeiro por Pessoa")
    df = st.session_state.df_transacoes
    if df is not None and not df.empty:
        resumo = (
            df.groupby(["Pessoa", "Tipo"])["ValorAbs"]
            .sum()
            .unstack(fill_value=0)
            .reset_index()
        )
        if "Receita" not in resumo.columns:
            resumo["Receita"] = 0
        if "Despesa" not in resumo.columns:
            resumo["Despesa"] = 0
        resumo["Saldo"] = resumo["Receita"] - resumo["Despesa"]

        st.dataframe(
            resumo,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Receita": st.column_config.NumberColumn(format="R$ %.2f"),
                "Despesa": st.column_config.NumberColumn(format="R$ %.2f"),
                "Saldo": st.column_config.NumberColumn(format="R$ %.2f"),
            },
        )

        if len(resumo) > 0:
            fig_fam = px.bar(
                resumo,
                x="Pessoa",
                y=["Receita", "Despesa"],
                barmode="group",
                labels={"value": "Valor (R$)", "variable": "", "Pessoa": ""},
                color_discrete_map={
                    "Receita": _COLORS["receita"],
                    "Despesa": _COLORS["despesa"],
                },
            )
            fig_fam.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=30, r=20, t=50, b=30),
                title=dict(text="Receitas vs Despesas por Pessoa", font=dict(size=15), x=0.02),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                bargap=0.25,
            )
            fig_fam.update_traces(marker_line_width=0, marker_cornerradius=4)
            st.plotly_chart(fig_fam, use_container_width=True)
    else:
        st.info("Adicione transações para ver o resumo.")
