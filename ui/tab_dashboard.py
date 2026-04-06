"""Dashboard tab — financial overview with KPIs, charts, and Data Storytelling.

Sections:
1. KPI cards: income, expenses, balance, transaction count
2. Data Storytelling: dynamic narrative text based on actual data
3. Monthly income vs expense bar chart
4. Horizontal bar chart: spending by category (the "fast read" chart)
5. Cumulative balance line chart
6. Top 5 expenses + spending by person
7. 50/30/20 quick summary (if renda_liquida is set)
8. Debts and investments KPIs
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Any, Dict, List
from utils.finance_models import calcular_resumo_divida, calcular_rentabilidade, calcular_progresso_meta

# ── Color palette (theme-agnostic; accent colors stay semantic) ──
COLORS = {
    "receita": "#16A34A",
    "despesa": "#DC2626",
    "saldo": "#4B5563",
    "accent": "#EA580C",
    "purple": "#7C3AED",
    "cyan": "#0891B2",
    "text": "#1A1A2E",
    "text_muted": "#64748B",
    "grid": "#E2E8F0",
    "card_bg": "#FFFFFF",
}

CHART_PALETTE = [
    "#4B5563", "#16A34A", "#EA580C", "#DC2626",
    "#7C3AED", "#0891B2", "#D97706", "#4338CA",
    "#BE185D", "#78716C",
]


def _chart_layout(title: str = "") -> Dict:
    return dict(
        title=dict(
            text=title,
            font=dict(size=15, color=COLORS["text"], family="Inter, Segoe UI, sans-serif"),
            x=0.02,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_muted"], family="Inter, Segoe UI, sans-serif", size=12),
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


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _render_kpi(col, label: str, value: str, delta: str = "", color: str = "#4B5563") -> None:
    """Render a KPI card with label, value, and optional delta on the same line."""
    if delta:
        st.write(f"""
        <div style="background: #F8F9FA; border: 1px solid #E5E7EB; border-radius: 12px;
                    padding: 16px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
            <div style="font-size: 0.7rem; color: #9CA3AF; text-transform: uppercase;
                        letter-spacing: 0.08em; font-weight: 600; margin-bottom: 4px;">{label}</div>
            <div style="display: flex; align-items: baseline; gap: 8px;">
                <span style="font-size: 1.4rem; font-weight: 700; color: #111827;">{value}</span>
                <span style="font-size: 0.9rem; color: #16A34A; font-weight: 500;">{delta}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col.metric(label, value)


def _resumo_dividas(dividas: List[Dict[str, Any]]) -> Dict[str, float]:
    resumo = {
        "total_em_dividas": 0.0,
        "total_pago": 0.0,
        "total_restante": 0.0,
        "parcela_mensal_total": 0.0,
        "qtd_ativas": 0.0,
    }
    for divida in dividas:
        try:
            metricas = calcular_resumo_divida(
                valor_principal=_safe_float(divida.get("valor_principal")),
                taxa_mensal=_safe_float(divida.get("taxa_mensal")),
                n_parcelas=int(_safe_float(divida.get("n_parcelas"), 1.0)),
                parcela_atual=int(_safe_float(divida.get("parcela_atual"), 1.0)),
                sistema=str(divida.get("sistema", "PRICE")),
                status=str(divida.get("status", "Ativa")),
            )
        except ValueError:
            continue
        resumo["total_em_dividas"] += metricas["total_final"]
        resumo["total_pago"] += metricas["total_pago"]
        resumo["total_restante"] += metricas["total_restante"]
        resumo["parcela_mensal_total"] += metricas["parcela_mensal_atual"]
        if str(divida.get("status", "Ativa")).lower() == "ativa":
            resumo["qtd_ativas"] += 1
    return resumo


def _resumo_investimentos(
    investimentos: List[Dict[str, Any]], metas_reserva: List[Dict[str, Any]]
) -> Dict[str, float]:
    total_aplicado = sum(_safe_float(inv.get("valor_aplicado")) for inv in investimentos)
    patrimonio_atual = sum(_safe_float(inv.get("valor_atual")) for inv in investimentos)
    rentabilidade = (
        calcular_rentabilidade(total_aplicado, patrimonio_atual)
        if total_aplicado > 0
        else {"lucro": 0.0, "rentabilidade_percentual": 0.0}
    )
    progressos = []
    for meta in metas_reserva:
        vm = _safe_float(meta.get("valor_meta"))
        va = _safe_float(meta.get("valor_atual"))
        if vm > 0:
            try:
                progressos.append(calcular_progresso_meta(va, vm))
            except ValueError:
                continue
    progresso_medio = sum(progressos) / len(progressos) if progressos else 0.0
    return {
        "patrimonio_atual": patrimonio_atual,
        "total_aplicado": total_aplicado,
        "rentabilidade_reais": rentabilidade["lucro"],
        "rentabilidade_percentual": rentabilidade["rentabilidade_percentual"],
        "progresso_medio_metas": progresso_medio,
    }


def _gerar_storytelling(df: pd.DataFrame, total_despesas: float, total_receitas: float) -> str:
    """Generate dynamic narrative text based on transaction data.

    Args:
        df: Full transactions DataFrame.
        total_despesas: Total absolute expenses.
        total_receitas: Total absolute income.

    Returns:
        Markdown-formatted narrative string.
    """
    lines = []
    df_desp = df[df["Tipo"] == "Despesa"]

    # Top category
    if not df_desp.empty:
        gastos_cat = df_desp.groupby("Categoria")["ValorAbs"].sum()
        top_cat = gastos_cat.idxmax()
        top_val = gastos_cat.max()
        pct_cat = (top_val / total_despesas * 100) if total_despesas > 0 else 0
        lines.append(
            f"🔍 Sua maior despesa é **{top_cat}**, representando "
            f"**{pct_cat:.1f}%** do total gasto (R$ {top_val:,.2f})."
        )

    # Balance health
    if total_receitas > 0:
        taxa_poupanca = ((total_receitas - total_despesas) / total_receitas) * 100
        if taxa_poupanca >= 20:
            lines.append(
                f"✅ Parabéns! Você está poupando **{taxa_poupanca:.1f}%** da sua renda — "
                "acima da meta de 20% da regra 50/30/20."
            )
        elif taxa_poupanca >= 0:
            lines.append(
                f"⚠️ Sua taxa de poupança é de **{taxa_poupanca:.1f}%**. "
                "O ideal é manter acima de 20%."
            )
        else:
            deficit = total_despesas - total_receitas
            lines.append(
                f"🚨 Atenção: suas despesas superam a renda em **R$ {deficit:,.2f}**. "
                "Revise os gastos da categoria com maior peso."
            )

    # Month-over-month comparison
    meses = sorted(df["AnoMes"].unique())
    if len(meses) >= 2:
        mes_atual = meses[-1]
        mes_anterior = meses[-2]
        desp_atual = df[(df["AnoMes"] == mes_atual) & (df["Tipo"] == "Despesa")]["ValorAbs"].sum()
        desp_anterior = df[(df["AnoMes"] == mes_anterior) & (df["Tipo"] == "Despesa")]["ValorAbs"].sum()
        if desp_anterior > 0:
            variacao = ((desp_atual - desp_anterior) / desp_anterior) * 100
            if variacao > 0:
                lines.append(
                    f"📈 Seus gastos em **{mes_atual}** foram "
                    f"**{variacao:.1f}% maiores** que em {mes_anterior} "
                    f"(+R$ {desp_atual - desp_anterior:,.2f})."
                )
            else:
                lines.append(
                    f"📉 Ótimo! Seus gastos em **{mes_atual}** foram "
                    f"**{abs(variacao):.1f}% menores** que em {mes_anterior} "
                    f"(-R$ {desp_anterior - desp_atual:,.2f})."
                )

    # Top single expense
    if not df_desp.empty:
        top_row = df_desp.nlargest(1, "ValorAbs").iloc[0]
        lines.append(
            f"💸 Maior transação individual: **{top_row['Descrição']}** "
            f"(R$ {top_row['ValorAbs']:,.2f})."
        )

    return "  \n".join(lines) if lines else ""


def render_dashboard() -> None:
    """Render financial overview dashboard."""
    df = st.session_state.df_transacoes
    dividas = st.session_state.get("dividas", [])
    investimentos = st.session_state.get("investimentos", [])
    metas_reserva = st.session_state.get("metas_reserva", [])

    # ── Debts & investments KPIs ──
    resumo_dividas = _resumo_dividas(dividas)
    resumo_investimentos = _resumo_investimentos(investimentos, metas_reserva)

    st.markdown("##### 💼 Dívidas e Patrimônio")
    col_d1, col_d2, col_d3, col_d4, col_d5 = st.columns(5)
    with col_d1:
        col_d1.metric("DÍVIDA TOTAL", f"R$ {resumo_dividas['total_em_dividas']:,.2f}")
    with col_d2:
        col_d2.metric("JÁ PAGO", f"R$ {resumo_dividas['total_pago']:,.2f}")
    with col_d3:
        col_d3.metric("RESTANTE", f"R$ {resumo_dividas['total_restante']:,.2f}")
    with col_d4:
        col_d4.metric("PARCELA MENSAL", f"R$ {resumo_dividas['parcela_mensal_total']:,.2f}")
    with col_d5:
        patrimonio = resumo_investimentos['patrimonio_atual']
        rentabilidade = resumo_investimentos['rentabilidade_percentual']
        _render_kpi(
            col_d5,
            "PATRIMÔNIO",
            f"R$ {patrimonio:,.2f}",
            f"↑ {rentabilidade:.2f}%"
        )

    st.write("---")

    if df is None or df.empty:
        st.info(
            "📊 Adicione transações na aba **Lançamentos** ou importe um extrato "
            "pela barra lateral para ver os gráficos."
        )
        return

    df_receitas = df[df["Tipo"] == "Receita"]
    df_despesas = df[df["Tipo"] == "Despesa"]

    total_receitas = df_receitas["ValorAbs"].sum()
    total_despesas = df_despesas["ValorAbs"].sum()
    saldo = total_receitas - total_despesas
    n_transacoes = len(df)

    # ── KPI cards ──
    st.markdown("##### 📊 Fluxo de Caixa")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        col1.metric("RECEITAS", f"R$ {total_receitas:,.2f}")
    with col2:
        col2.metric("DESPESAS", f"R$ {total_despesas:,.2f}")
    with col3:
        saldo_delta = f"R$ {abs(saldo):,.2f}"
        delta_str = f"{'↑' if saldo >= 0 else '↓'} {saldo_delta}"
        _render_kpi(col3, "SALDO", f"R$ {saldo:,.2f}", delta_str)
    with col4:
        col4.metric("TRANSAÇÕES", f"{n_transacoes}")

    # ── Data Storytelling ──
    storytelling = _gerar_storytelling(df, total_despesas, total_receitas)
    if storytelling:
        st.write("---")
        st.markdown("##### 📖 O que os seus dados dizem")
        st.info(storytelling)

    # ── Row 1: Monthly bar + Horizontal category bar ──
    st.write("---")
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
            color_discrete_map={"Receita": COLORS["receita"], "Despesa": COLORS["despesa"]},
        )
        fig_mensal.update_layout(**_chart_layout("Receitas vs Despesas por Mês"))
        fig_mensal.update_traces(marker_line_width=0, marker_cornerradius=4)
        st.plotly_chart(fig_mensal, use_container_width=True)

    with col_chart2:
        if not df_despesas.empty:
            gastos_cat = (
                df_despesas.groupby("Categoria")["ValorAbs"].sum().reset_index()
            )
            gastos_cat = gastos_cat.sort_values("ValorAbs", ascending=True)
            gastos_cat["pct"] = (gastos_cat["ValorAbs"] / total_despesas * 100).round(1)
            gastos_cat["label"] = gastos_cat.apply(
                lambda r: f"R$ {r['ValorAbs']:,.0f} ({r['pct']}%)", axis=1
            )

            fig_hbar = px.bar(
                gastos_cat,
                x="ValorAbs",
                y="Categoria",
                orientation="h",
                labels={"ValorAbs": "", "Categoria": ""},
                color_discrete_sequence=[COLORS["saldo"]],
                text="label",
            )
            layout = _chart_layout("Gastos por Categoria")
            layout["xaxis"]["showgrid"] = False
            layout["xaxis"]["showticklabels"] = False
            fig_hbar.update_layout(**layout)
            fig_hbar.update_traces(
                marker_line_width=0,
                marker_cornerradius=4,
                textposition="outside",
                textfont_size=10,
                textfont_color=COLORS["text_muted"],
            )
            st.plotly_chart(fig_hbar, use_container_width=True)
        else:
            st.info("Nenhuma despesa registrada.")

    # ── Cumulative balance ──
    df_sorted = df.sort_values("Data")
    df_sorted["SaldoAcumulado"] = df_sorted["Valor"].cumsum()

    fig_saldo = go.Figure()
    fig_saldo.add_trace(go.Scatter(
        x=df_sorted["Data"],
        y=df_sorted["SaldoAcumulado"],
        mode="lines",
        name="Saldo",
        line=dict(color=COLORS["saldo"], width=2.5),
        fill="tozeroy",
        fillcolor="rgba(75,85,99,0.07)",
        hovertemplate="%{x|%d/%m/%Y}<br>R$ %{y:,.2f}<extra></extra>",
    ))
    fig_saldo.update_layout(**_chart_layout("Evolução do Saldo Acumulado"))
    fig_saldo.update_layout(yaxis_tickprefix="R$ ")
    st.plotly_chart(fig_saldo, use_container_width=True)

    # ── Top 5 + by person ──
    if not df_despesas.empty:
        col_t1, col_t2 = st.columns(2)

        with col_t1:
            st.markdown("##### Top 5 Maiores Despesas")
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

    # ── 50/30/20 quick summary (if renda set) ──
    renda = st.session_state.get("renda_liquida", 0.0)
    if renda and renda > 0 and not df_despesas.empty:
        st.write("---")
        st.markdown("##### 📐 Resumo 50/30/20 — Mês mais recente")

        from ui.tab_planejamento import _calcular_analise_5030_20, _get_bucket_map

        mes_recente = df_despesas["AnoMes"].max()
        df_mes = df_despesas[df_despesas["AnoMes"] == mes_recente]
        bucket_map = st.session_state.get("bucket_map", _get_bucket_map())
        df_analise = _calcular_analise_5030_20(renda, df_mes, bucket_map)

        if not df_analise.empty:
            b1, b2, b3 = st.columns(3)
            for col, (_, row) in zip([b1, b2, b3], df_analise.iterrows()):
                saldo_b = row["Saldo (R$)"]
                status = "ok" if saldo_b >= 0 else "excedido"
                delta_str = f"R$ {abs(saldo_b):,.2f} {status}"
                with col:
                    _render_kpi(
                        col,
                        f"{row['Grupo']} ({row['Limite (%)']:.0f}%)",
                        f"R$ {row['Gasto (R$)']:,.2f}",
                        delta_str
                    )
            st.caption(
                f"Referência: renda líquida de R$ {renda:,.2f} | mês: {mes_recente}. "
                "Ajuste em **Planejamento → 50/30/20**."
            )
