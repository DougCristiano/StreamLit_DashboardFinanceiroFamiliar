"""Tab components for Dashboard Financeiro Familiar.

Provides render functions for each main dashboard tab:
- Dashboard: Financial overview with KPIs and charts
- Lançamentos: Manual transaction entry
- Família: Family member management
- Extrato: Detailed transaction viewing and filtering
- Configurações: Settings and customization
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from typing import Dict
from utils.helpers import (
    save_json,
    salvar_transacoes,
    MEMBROS_FILE,
    CATEGORIES_FILE,
    normalizar_texto,
)
from utils.processing import processar_dados

# ============================================================
# THEME CONFIG — Power BI Dark
# ============================================================

COLORS = {
    "receita": "#16A34A",
    "despesa": "#DC2626",
    "saldo": "#1565C0",
    "accent": "#EA580C",
    "purple": "#7C3AED",
    "cyan": "#0891B2",
    "text": "#1A1A2E",
    "text_muted": "#64748B",
    "grid": "#E2E8F0",
    "card_bg": "#FFFFFF",
}

CHART_PALETTE = [
    "#1565C0",
    "#16A34A",
    "#EA580C",
    "#DC2626",
    "#7C3AED",
    "#0891B2",
    "#D97706",
    "#4338CA",
    "#BE185D",
    "#78716C",
]


def _chart_layout(title: str = "") -> Dict:
    """Return standard light layout dictionary for Plotly charts.

    Args:
        title: Chart title.

    Returns:
        Dictionary with Plotly layout configuration.
    """
    return dict(
        title=dict(
            text=title,
            font=dict(
                size=15, color=COLORS["text"], family="Inter, Segoe UI, sans-serif"
            ),
            x=0.02,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color=COLORS["text_muted"], family="Inter, Segoe UI, sans-serif", size=12
        ),
        legend=dict(
            font=dict(size=11, color=COLORS["text_muted"]),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=30, r=20, t=50, b=30),
        xaxis=dict(
            gridcolor=COLORS["grid"],
            gridwidth=0.5,
            tickfont=dict(size=11, color=COLORS["text_muted"]),
            linecolor=COLORS["grid"],
            zeroline=False,
        ),
        yaxis=dict(
            gridcolor=COLORS["grid"],
            gridwidth=0.5,
            tickfont=dict(size=11, color=COLORS["text_muted"]),
            linecolor=COLORS["grid"],
            zeroline=False,
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Inter, Segoe UI, sans-serif",
            font_color=COLORS["text"],
            bordercolor=COLORS["grid"],
        ),
        bargap=0.25,
    )


# ============================================================
# 1. DASHBOARD — Financial Overview
# ============================================================


def render_dashboard() -> None:
    """Render main financial dashboard with KPIs and visualizations.

    Displays:
    - KPI cards: Total income, expenses, balance, transaction count
    - Monthly income vs expense bar chart
    - Expense distribution pie chart
    - Cumulative balance line chart
    - Top 5 expenses and spending by family member
    """
    df = st.session_state.df_transacoes

    if df is None or df.empty:
        st.info(
            "📊 Adicione transações na aba **Lançamentos** ou importe um extrato pela barra lateral para ver o dashboard."
        )
        return

    df_receitas = df[df["Tipo"] == "Receita"]
    df_despesas = df[df["Tipo"] == "Despesa"]

    total_receitas = df_receitas["ValorAbs"].sum()
    total_despesas = df_despesas["ValorAbs"].sum()
    saldo = total_receitas - total_despesas
    n_transacoes = len(df)

    # --- KPI Cards ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("RECEITAS", f"R$ {total_receitas:,.2f}")
    col2.metric("DESPESAS", f"R$ {total_despesas:,.2f}")

    saldo_delta = f"R$ {abs(saldo):,.2f}"
    col3.metric(
        "SALDO",
        f"R$ {saldo:,.2f}",
        delta=saldo_delta if saldo >= 0 else f"-{saldo_delta}",
        delta_color="normal",
    )
    col4.metric("TRANSAÇÕES", f"{n_transacoes}")

    # --- Row 1: Bar + Donut ---
    col_chart1, col_chart2 = st.columns([3, 2])

    with col_chart1:
        resumo_mensal = df.groupby(["AnoMes", "Tipo"])["ValorAbs"].sum().reset_index()
        resumo_mensal = resumo_mensal.sort_values("AnoMes")

        fig_mensal = px.bar(
            resumo_mensal,
            x="AnoMes",
            y="ValorAbs",
            color="Tipo",
            barmode="group",
            labels={"ValorAbs": "Valor (R$)", "AnoMes": ""},
            color_discrete_map={
                "Receita": COLORS["receita"],
                "Despesa": COLORS["despesa"],
            },
        )
        fig_mensal.update_layout(**_chart_layout("Receitas vs Despesas por Mês"))
        fig_mensal.update_traces(marker_line_width=0, marker_cornerradius=4)
        st.plotly_chart(fig_mensal, use_container_width=True)

    with col_chart2:
        if not df_despesas.empty:
            gastos_cat = (
                df_despesas.groupby("Categoria")["ValorAbs"].sum().reset_index()
            )
            gastos_cat = gastos_cat.sort_values("ValorAbs", ascending=False)

            fig_pizza = px.pie(
                gastos_cat,
                names="Categoria",
                values="ValorAbs",
                hole=0.55,
                color_discrete_sequence=CHART_PALETTE,
            )
            layout = _chart_layout("Despesas por Categoria")
            layout["showlegend"] = True
            layout["legend"] = dict(
                font=dict(size=10, color=COLORS["text_muted"]),
                bgcolor="rgba(0,0,0,0)",
                borderwidth=0,
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05,
            )
            fig_pizza.update_layout(**layout)
            fig_pizza.update_traces(
                textposition="inside",
                textinfo="percent",
                textfont_size=11,
                textfont_color="white",
                marker_line_width=2,
                marker_line_color=COLORS["card"],
            )
            st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.info("Nenhuma despesa registrada.")

    # --- Row 2: Saldo Acumulado ---
    df_sorted = df.sort_values("Data")
    df_sorted["SaldoAcumulado"] = df_sorted["Valor"].cumsum()

    fig_saldo = go.Figure()
    fig_saldo.add_trace(
        go.Scatter(
            x=df_sorted["Data"],
            y=df_sorted["SaldoAcumulado"],
            mode="lines",
            name="Saldo",
            line=dict(color=COLORS["saldo"], width=2.5),
            fill="tozeroy",
            fillcolor="rgba(21, 101, 192, 0.08)",
            hovertemplate="%{x|%d/%m/%Y}<br>R$ %{y:,.2f}<extra></extra>",
        )
    )
    fig_saldo.update_layout(**_chart_layout("Evolução do Saldo"))
    fig_saldo.update_layout(yaxis_tickprefix="R$ ")
    st.plotly_chart(fig_saldo, use_container_width=True)

    # --- Row 3: Top 5 + Gastos por Pessoa ---
    if not df_despesas.empty:
        col_t1, col_t2 = st.columns(2)

        with col_t1:
            st.markdown("##### 🏆 Top 5 Maiores Despesas")
            top5 = df_despesas.nlargest(5, "ValorAbs")[
                ["Data", "Descrição", "Categoria", "Pessoa", "ValorAbs"]
            ].copy()
            top5["Data"] = top5["Data"].dt.strftime("%d/%m/%Y")
            top5.columns = ["Data", "Descrição", "Categoria", "Pessoa", "Valor (R$)"]
            st.dataframe(top5, use_container_width=True, hide_index=True)

        with col_t2:
            gastos_pessoa = (
                df_despesas.groupby("Pessoa")["ValorAbs"].sum().reset_index()
            )
            gastos_pessoa.columns = ["Pessoa", "Total"]
            gastos_pessoa = gastos_pessoa.sort_values("Total", ascending=True)

            fig_pessoa = px.bar(
                gastos_pessoa,
                x="Total",
                y="Pessoa",
                orientation="h",
                labels={"Total": "", "Pessoa": ""},
                color_discrete_sequence=[COLORS["accent"]],
                text_auto=".2s",
            )
            fig_pessoa.update_layout(**_chart_layout("Despesas por Pessoa"))
            fig_pessoa.update_traces(
                marker_line_width=0,
                marker_cornerradius=4,
                textfont_size=11,
                textfont_color=COLORS["text_muted"],
                textposition="outside",
            )
            st.plotly_chart(fig_pessoa, use_container_width=True)


# ============================================================
# 2. LANÇAMENTOS — Manual Transaction Entry
# ============================================================


def render_lancamentos() -> None:
    """Render manual transaction entry form and history.

    Displays:
    - Form for adding new transactions (expense/income)
    - Recent transactions table
    - Danger zone for clearing all manual transactions
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

    # --- Tabela de transações recentes ---
    st.markdown("##### Transações Recentes")

    df = st.session_state.df_transacoes
    if df is not None and not df.empty:
        df_display = df.head(20)[
            ["Data", "Tipo", "Descrição", "Categoria", "Pessoa", "ValorAbs"]
        ].copy()
        df_display["Data"] = df_display["Data"].dt.strftime("%d/%m/%Y")
        df_display.columns = [
            "Data",
            "Tipo",
            "Descrição",
            "Categoria",
            "Pessoa",
            "Valor (R$)",
        ]

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

    # --- Botão limpar ---
    with st.expander("⚠️ Zona de Perigo"):
        if st.button("🗑️ Limpar TODAS as transações manuais", type="secondary"):
            st.session_state.transacoes = []
            salvar_transacoes()
            processar_dados()
            st.rerun()


# ============================================================
# 3. FAMÍLIA — Family Member Management
# ============================================================


def render_familia() -> None:
    """Render family member management interface.

    Displays:
    - Form to add new family members
    - List of current family members with delete option
    """
    st.markdown("##### Membros da Família")

    membros = st.session_state.get("membros_familia", [])

    with st.form("add_membro", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            novo = st.text_input(
                "Nome do novo membro", placeholder="Ex: Douglas, Esposa"
            )
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

    # Lista de membros
    if membros:
        for i, membro in enumerate(membros):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown(f"👤 **{membro}**")
            with col2:
                df = st.session_state.df_transacoes
                if df is not None and not df.empty:
                    total_pessoa = df[df["Pessoa"] == membro]["Valor"].sum()
                    color = (
                        COLORS["receita"] if total_pessoa >= 0 else COLORS["despesa"]
                    )
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

    # --- Resumo por pessoa ---
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

        # Chart
        if len(resumo) > 0:
            fig_fam = px.bar(
                resumo,
                x="Pessoa",
                y=["Receita", "Despesa"],
                barmode="group",
                labels={"value": "Valor (R$)", "variable": "", "Pessoa": ""},
                color_discrete_map={
                    "Receita": COLORS["receita"],
                    "Despesa": COLORS["despesa"],
                },
            )
            fig_fam.update_layout(**_chart_layout("Receitas vs Despesas por Pessoa"))
            fig_fam.update_traces(marker_line_width=0, marker_cornerradius=4)
            st.plotly_chart(fig_fam, use_container_width=True)
    else:
        st.info("Adicione transações para ver o resumo.")


# ============================================================
# 4. EXTRATO — Detailed Transaction View
# ============================================================


def render_extrato() -> None:
    """Render detailed transaction view with filtering options.

    Displays:
    - Date range filter
    - Transaction type filter (Income/Expense)
    - Category filter
    - Person filter
    - Description search
    - Filtered transaction table with summary metrics
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

    # Aplicar filtros
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

    df_filt.drop(columns=["_data"], inplace=True)

    st.write(f"**{len(df_filt)} transações encontradas**")

    # Resumo do filtro
    col_r1, col_r2, col_r3 = st.columns(3)
    receitas_filt = df_filt[df_filt["Tipo"] == "Receita"]["ValorAbs"].sum()
    despesas_filt = df_filt[df_filt["Tipo"] == "Despesa"]["ValorAbs"].sum()
    col_r1.metric("RECEITAS", f"R$ {receitas_filt:,.2f}")
    col_r2.metric("DESPESAS", f"R$ {despesas_filt:,.2f}")
    col_r3.metric("SALDO", f"R$ {receitas_filt - despesas_filt:,.2f}")

    # Tabela
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


# ============================================================
# 5. CONFIGURAÇÕES — Categories, Budget, Recurring
# ============================================================


def render_configuracoes() -> None:
    """Render settings tab with three sub-sections.

    Displays:
    - Category management interface
    - Monthly budget configuration
    - Recurring expenses tracking
    """
    config_tab1, config_tab2, config_tab3 = st.tabs(
        ["🏷️ Categorias", "💰 Orçamento", "🔁 Recorrentes"]
    )

    with config_tab1:
        _render_categorias()

    with config_tab2:
        _render_orcamento()

    with config_tab3:
        _render_recorrentes()


def _render_categorias() -> None:
    """Render category management interface.

    Allows adding, editing, and deleting expense categories with keywords.
    """
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
                save_json(CATEGORIES_FILE, st.session_state.categories)
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
                save_json(CATEGORIES_FILE, st.session_state.categories)
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
    """Render budget configuration and analysis interface.

    Allows setting monthly budget per category and comparing against actual spending.
    """
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
                    st.toast(f"Orçamento '{cat}' salvo!", icon="✅")
                except (ValueError, TypeError):
                    st.toast("Valor inválido.", icon="❌")

    total = sum(st.session_state.orcamento_mensal.values())
    st.metric("TOTAL ORÇADO", f"R$ {total:,.2f}")

    # Análise vs Real
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
                    rows.append(
                        {
                            "Categoria": cat,
                            "Orçado": orcado,
                            "Gasto": gasto,
                            "Saldo": orcado - gasto,
                        }
                    )

            if rows:
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
                    color_discrete_map={
                        "Orçado": COLORS["saldo"],
                        "Gasto": COLORS["despesa"],
                    },
                )
                fig_orc.update_layout(**_chart_layout(f"Orçado vs Real — {mes}"))
                fig_orc.update_traces(marker_line_width=0, marker_cornerradius=4)
                st.plotly_chart(fig_orc, use_container_width=True)


def _render_recorrentes() -> None:
    """Render recurring expenses management interface.

    Allows tracking subscriptions, utilities, and other fixed monthly expenses.
    """
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
    total = st.session_state.despesas_recorrentes["Valor"].sum()
    st.metric("TOTAL RECORRENTE", f"R$ {total:,.2f}")
