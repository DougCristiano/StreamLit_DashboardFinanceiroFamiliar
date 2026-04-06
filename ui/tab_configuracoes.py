"""Configurações tab — categories, budget, recurring expenses, and theme."""

import streamlit as st
import plotly.express as px
from utils.helpers import (
    save_json,
    salvar_orcamento_mensal,
    salvar_despesas_recorrentes,
    CATEGORIES_FILE,
    normalizar_texto,
)

# Available themes: name → CSS variable overrides injected into the page
TEMAS_DISPONIVEIS = {
    "Neutro": "neutro",
    "Claro (Azul)": "claro",
    "Escuro": "escuro",
}


def render_configuracoes() -> None:
    """Render settings tab with categories, budget, recurring expenses, and theme."""
    config_tab1, config_tab2, config_tab3, config_tab4 = st.tabs(
        ["🏷️ Categorias", "💰 Orçamento", "🔁 Recorrentes", "🎨 Tema"]
    )

    with config_tab1:
        _render_categorias()

    with config_tab2:
        _render_orcamento()

    with config_tab3:
        _render_recorrentes()

    with config_tab4:
        _render_tema()


def _render_categorias() -> None:
    """Render category management: add, edit keywords, delete."""
    st.markdown("##### Gerenciar Categorias")

    with st.form("form_nova_cat", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nova_cat = st.text_input("Nome da Nova Categoria", placeholder="Ex: Saúde")
        with col2:
            palavras = st.text_input(
                "Palavras-chave (separadas por vírgula)",
                placeholder="Ex: farmácia, remédio",
            )

        if st.form_submit_button("Adicionar Categoria"):
            if nova_cat and palavras:
                kws = [normalizar_texto(p.strip()) for p in palavras.split(",")]
                st.session_state.categories[nova_cat] = kws
                if nova_cat not in st.session_state.orcamento_mensal:
                    st.session_state.orcamento_mensal[nova_cat] = 0.0
                save_json(CATEGORIES_FILE, st.session_state.categories)
                salvar_orcamento_mensal()
                st.success(f"Categoria '{nova_cat}' adicionada!")
                st.rerun()

    st.write("---")
    st.write("**Categorias Atuais:**")

    for cat in list(st.session_state.categories.keys()):
        if cat == "Outros":
            continue
        col1, col2 = st.columns([4, 1])
        with col1:
            kws_str = ", ".join(st.session_state.categories[cat])
            st.text_input(
                f"**{cat}**", value=kws_str, key=f"kw_{cat}", label_visibility="visible"
            )
        with col2:
            st.write("")
            if st.button("Remover", key=f"del_cat_{cat}"):
                del st.session_state.categories[cat]
                if cat in st.session_state.orcamento_mensal:
                    del st.session_state.orcamento_mensal[cat]
                save_json(CATEGORIES_FILE, st.session_state.categories)
                salvar_orcamento_mensal()
                st.rerun()

    if st.button("💾 Salvar Palavras-chave", use_container_width=True):
        for cat in list(st.session_state.categories.keys()):
            if cat == "Outros":
                continue
            key = f"kw_{cat}"
            if key in st.session_state:
                st.session_state.categories[cat] = [
                    normalizar_texto(p.strip())
                    for p in st.session_state[key].split(",")
                ]
        save_json(CATEGORIES_FILE, st.session_state.categories)
        st.success("Palavras-chave salvas!")


def _render_orcamento() -> None:
    """Render monthly budget per category with actual vs. planned comparison."""
    st.markdown("##### Orçamento Mensal por Categoria")

    for cat in st.session_state.categories.keys():
        col1, col2 = st.columns([3, 1])
        valor_atual = st.session_state.orcamento_mensal.get(cat, 0.0)
        with col1:
            st.text_input(
                f"Orçamento para **{cat}** (R$)",
                value=(
                    "" if valor_atual == 0 else f"{valor_atual:.2f}".replace(".", ",")
                ),
                key=f"orc_{cat}",
            )
        with col2:
            st.write("")
            if st.button("Salvar", key=f"orc_btn_{cat}", use_container_width=True):
                try:
                    val = float(st.session_state[f"orc_{cat}"].replace(",", "."))
                    st.session_state.orcamento_mensal[cat] = val
                    salvar_orcamento_mensal()
                    st.toast(f"Orçamento '{cat}' salvo!", icon="✅")
                except (ValueError, TypeError):
                    st.toast("Valor inválido.", icon="❌")

    total = sum(st.session_state.orcamento_mensal.values())
    st.metric("TOTAL ORÇADO", f"R$ {total:,.2f}")

    df = st.session_state.df_transacoes
    if df is not None and not df.empty:
        df_desp = df[df["Tipo"] == "Despesa"]
        if not df_desp.empty:
            st.write("---")
            st.markdown("##### Orçado vs Real")
            meses = sorted(df_desp["AnoMes"].unique(), reverse=True)
            mes = st.selectbox("Mês", meses)

            gastos_mes = (
                df_desp[df_desp["AnoMes"] == mes].groupby("Categoria")["ValorAbs"].sum()
            )

            rows = []
            for cat, orcado in st.session_state.orcamento_mensal.items():
                if orcado > 0:
                    gasto = gastos_mes.get(cat, 0)
                    rows.append({
                        "Categoria": cat,
                        "Orçado": orcado,
                        "Gasto": gasto,
                        "Saldo": orcado - gasto,
                    })

            if rows:
                import pandas as pd
                df_orc = pd.DataFrame(rows)
                st.dataframe(
                    df_orc,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Orçado": st.column_config.NumberColumn(format="R$ %.2f"),
                        "Gasto": st.column_config.NumberColumn(format="R$ %.2f"),
                        "Saldo": st.column_config.NumberColumn(format="R$ %.2f"),
                    },
                )

                fig_orc = px.bar(
                    df_orc,
                    x="Categoria",
                    y=["Orçado", "Gasto"],
                    barmode="group",
                    labels={"value": "R$", "variable": ""},
                    color_discrete_map={"Orçado": "#4B5563", "Gasto": "#DC2626"},
                )
                fig_orc.update_layout(
                    title=dict(text=f"Orçado vs Real — {mes}", font=dict(size=15), x=0.02),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=30, r=20, t=50, b=30),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                fig_orc.update_traces(marker_line_width=0, marker_cornerradius=4)
                st.plotly_chart(fig_orc, use_container_width=True)


def _render_recorrentes() -> None:
    """Render recurring expenses management with auto-save."""
    st.markdown("##### Despesas Recorrentes")
    st.write("Cadastre assinaturas e contas fixas mensais.")

    st.session_state.despesas_recorrentes = st.data_editor(
        st.session_state.despesas_recorrentes,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Descrição": st.column_config.TextColumn("Descrição", required=True),
            "Valor": st.column_config.NumberColumn(
                "Valor Mensal (R$)", required=True, min_value=0, format="R$ %.2f"
            ),
            "Categoria": st.column_config.SelectboxColumn(
                "Categoria",
                options=sorted(st.session_state.categories.keys()),
                required=True,
            ),
        },
    )

    snapshot_atual = st.session_state.despesas_recorrentes.to_dict("records")
    if snapshot_atual != st.session_state.get("_despesas_recorrentes_snapshot", []):
        salvar_despesas_recorrentes()
        st.session_state._despesas_recorrentes_snapshot = snapshot_atual

    total = st.session_state.despesas_recorrentes["Valor"].sum()
    st.metric("TOTAL RECORRENTE", f"R$ {total:,.2f}")
    st.caption("Salvamento automático ativado para despesas recorrentes.")


def _render_tema() -> None:
    """Render theme selector — changes are applied on next interaction."""
    st.markdown("##### Aparência")
    st.caption(
        "Selecione o tema visual do dashboard. A mudança é aplicada imediatamente."
    )

    tema_atual = st.session_state.get("tema", "Neutro")
    opcoes = list(TEMAS_DISPONIVEIS.keys())

    tema_selecionado = st.radio(
        "Tema",
        opcoes,
        index=opcoes.index(tema_atual) if tema_atual in opcoes else 0,
        horizontal=True,
    )

    if tema_selecionado != tema_atual:
        st.session_state.tema = tema_selecionado
        st.rerun()

    st.write("---")
    st.caption(
        "**Neutro** — tons de cinza, sem cor dominante  \n"
        "**Claro (Azul)** — tema original com destaque azul  \n"
        "**Escuro** — fundo escuro para uso noturno"
    )
