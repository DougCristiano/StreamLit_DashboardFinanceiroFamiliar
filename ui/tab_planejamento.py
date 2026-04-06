"""Planejamento tab — 50/30/20 budget rule and Dreams Goal Manager.

The 50/30/20 rule divides net income into:
  - 50% Necessidades (needs): housing, utilities, food, health, transport
  - 30% Desejos (wants): entertainment, shopping, subscriptions
  - 20% Poupança/Dívidas (savings/debts)

The Dreams Manager uses compound interest (FV annuity formula) to simulate
how long it takes to reach a financial goal given monthly contributions and
an expected return rate, then plots the growth curve.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, List
from utils.finance_models import simular_meta_sonhos

# --- Category → 50/30/20 bucket mapping ---
# Users can adjust this in session state (future feature).
_DEFAULT_BUCKET_MAP: Dict[str, str] = {
    "Moradia": "Necessidades",
    "Alimentação": "Necessidades",
    "Saúde": "Necessidades",
    "Transporte": "Necessidades",
    "Educação": "Necessidades",
    "Lazer": "Desejos",
    "Compras": "Desejos",
    "Outros": "Desejos",
    "Receita": "Receita",  # excluded from analysis
}

_BUCKET_COLORS = {
    "Necessidades": "#4B5563",   # neutral gray
    "Desejos": "#EA580C",        # warm orange
    "Poupança/Dívidas": "#16A34A",  # green
}

_LIMITS = {"Necessidades": 50.0, "Desejos": 30.0, "Poupança/Dívidas": 20.0}


def _get_bucket_map() -> Dict[str, str]:
    """Return the current category-to-bucket mapping from session state."""
    cats = st.session_state.get("categories", {})
    mapping = dict(_DEFAULT_BUCKET_MAP)
    # Ensure new user-created categories default to "Desejos"
    for cat in cats:
        if cat not in mapping:
            mapping[cat] = "Desejos"
    return mapping


def _calcular_analise_5030_20(
    renda_liquida: float,
    df_despesas: pd.DataFrame,
    bucket_map: Dict[str, str],
) -> pd.DataFrame:
    """Compute planned vs. actual spending per 50/30/20 bucket.

    Args:
        renda_liquida: Monthly net income entered by user.
        df_despesas: DataFrame with expense transactions for selected month.
        bucket_map: Category → bucket name mapping.

    Returns:
        DataFrame with columns: Grupo, Limite (%), Limite (R$), Gasto (R$), Saldo (R$), % Renda.
    """
    if renda_liquida <= 0:
        return pd.DataFrame()

    # Map categories to buckets
    df = df_despesas.copy()
    df["Grupo"] = df["Categoria"].map(bucket_map).fillna("Desejos")
    df = df[df["Grupo"] != "Receita"]

    gastos_por_grupo = df.groupby("Grupo")["ValorAbs"].sum()

    rows = []
    for bucket, pct in _LIMITS.items():
        limite_rs = renda_liquida * pct / 100
        gasto = gastos_por_grupo.get(bucket, 0.0)
        saldo = limite_rs - gasto
        pct_renda = (gasto / renda_liquida) * 100 if renda_liquida > 0 else 0.0
        rows.append({
            "Grupo": bucket,
            "Limite (%)": pct,
            "Limite (R$)": limite_rs,
            "Gasto (R$)": gasto,
            "Saldo (R$)": saldo,
            "% Renda": pct_renda,
        })

    return pd.DataFrame(rows)


def render_planejamento() -> None:
    """Render the planning tab with 50/30/20 analysis and Dreams Manager."""
    tab_5030, tab_sonhos = st.tabs(["📊 Regra 50/30/20", "🌟 Gerenciador de Sonhos"])

    with tab_5030:
        _render_5030_20()

    with tab_sonhos:
        _render_gerenciador_sonhos()


# ────────────────────────────────────────────────────────────────
# 50/30/20 SECTION
# ────────────────────────────────────────────────────────────────

def _render_5030_20() -> None:
    """Render 50/30/20 budget analysis."""
    st.markdown("##### Regra 50/30/20 — Divisão da Renda")
    st.caption(
        "Informe sua renda líquida mensal para ver como seus gastos se distribuem "
        "nas três categorias da regra 50/30/20."
    )

    col_input, col_info = st.columns([2, 3])

    with col_input:
        renda_liquida = st.number_input(
            "Renda líquida mensal (R$)",
            min_value=0.0,
            value=float(st.session_state.get("renda_liquida", 0.0)),
            step=500.0,
            format="%.2f",
            help="Soma de todos os salários e rendimentos após impostos.",
        )
        if renda_liquida != st.session_state.get("renda_liquida", 0.0):
            st.session_state.renda_liquida = renda_liquida

    with col_info:
        st.markdown("""
        | Grupo | Limite | O que inclui |
        |---|---|---|
        | **Necessidades** | 50% | Moradia, Alimentação, Saúde, Transporte |
        | **Desejos** | 30% | Lazer, Compras, Assinaturas |
        | **Poupança/Dívidas** | 20% | Investimentos, parcelas, reserva |
        """)

    if renda_liquida <= 0:
        st.info("Informe sua renda líquida acima para ver a análise.")
        return

    df = st.session_state.df_transacoes
    df_despesas_all = None
    mes_selecionado = None

    if df is not None and not df.empty:
        df_desp = df[df["Tipo"] == "Despesa"]
        if not df_desp.empty:
            meses = sorted(df_desp["AnoMes"].unique(), reverse=True)
            mes_selecionado = st.selectbox("Mês de referência", meses, key="plan_mes")
            df_despesas_all = df_desp[df_desp["AnoMes"] == mes_selecionado]

    # ── Bucket mapping editor ──
    with st.expander("⚙️ Ajustar classificação das categorias"):
        bucket_map = _get_bucket_map()
        bucket_opcoes = ["Necessidades", "Desejos", "Poupança/Dívidas"]
        cats_editaveis = [c for c in st.session_state.get("categories", {}) if c != "Outros" and c != "Receita"]
        for cat in cats_editaveis:
            atual = bucket_map.get(cat, "Desejos")
            novo = st.selectbox(
                cat,
                bucket_opcoes,
                index=bucket_opcoes.index(atual) if atual in bucket_opcoes else 1,
                key=f"bucket_{cat}",
            )
            bucket_map[cat] = novo
        st.session_state.bucket_map = bucket_map

    # Always resolve the current bucket_map (expander runs regardless of expanded state)
    bucket_map = st.session_state.get("bucket_map", _get_bucket_map())

    # ── Planned allocation (no actual data needed) ──
    st.write("---")
    st.markdown("##### Alocação Planejada")
    col_p1, col_p2, col_p3 = st.columns(3)
    col_p1.metric("Necessidades (50%)", f"R$ {renda_liquida * 0.50:,.2f}")
    col_p2.metric("Desejos (30%)", f"R$ {renda_liquida * 0.30:,.2f}")
    col_p3.metric("Poupança/Dívidas (20%)", f"R$ {renda_liquida * 0.20:,.2f}")

    # ── Pie chart: planned allocation ──
    df_pie = pd.DataFrame({
        "Grupo": list(_LIMITS.keys()),
        "Valor": [renda_liquida * p / 100 for p in _LIMITS.values()],
    })
    fig_pie = px.pie(
        df_pie,
        names="Grupo",
        values="Valor",
        hole=0.55,
        color="Grupo",
        color_discrete_map=_BUCKET_COLORS,
    )
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        title=dict(text="Divisão ideal da renda", font=dict(size=14), x=0.02),
    )
    fig_pie.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont_size=12,
        marker_line_width=2,
        marker_line_color="white",
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # ── Actual analysis ──
    if df_despesas_all is not None and not df_despesas_all.empty:
        st.write("---")
        st.markdown(f"##### Real vs. Planejado — {mes_selecionado}")

        df_analise = _calcular_analise_5030_20(renda_liquida, df_despesas_all, bucket_map)

        if not df_analise.empty:
            # Alerts
            for _, row in df_analise.iterrows():
                excesso = row["Gasto (R$)"] - row["Limite (R$)"]
                if excesso > 0:
                    pct_excesso = (excesso / row["Limite (R$)"]) * 100
                    st.warning(
                        f"⚠️ **{row['Grupo']}**: você gastou R$ {excesso:,.2f} acima "
                        f"do limite ({pct_excesso:.1f}% a mais)."
                    )
                else:
                    sobra = -excesso
                    st.success(
                        f"✅ **{row['Grupo']}**: dentro do limite — sobram R$ {sobra:,.2f}."
                    )

            # KPIs
            k1, k2, k3 = st.columns(3)
            for col, (_, row) in zip([k1, k2, k3], df_analise.iterrows()):
                saldo = row["Saldo (R$)"]
                delta_color = "normal" if saldo >= 0 else "inverse"
                col.metric(
                    row["Grupo"],
                    f"R$ {row['Gasto (R$)']:,.2f}",
                    delta=f"R$ {saldo:,.2f} {'restante' if saldo >= 0 else 'excedido'}",
                    delta_color=delta_color,
                )

            # Grouped bar chart: Limite vs Gasto
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                name="Limite",
                x=df_analise["Grupo"],
                y=df_analise["Limite (R$)"],
                marker_color=["rgba(75,85,99,0.3)", "rgba(234,88,12,0.3)", "rgba(22,163,74,0.3)"],
                marker_line_color=["#4B5563", "#EA580C", "#16A34A"],
                marker_line_width=2,
            ))
            fig_bar.add_trace(go.Bar(
                name="Gasto Real",
                x=df_analise["Grupo"],
                y=df_analise["Gasto (R$)"],
                marker_color=[
                    _BUCKET_COLORS.get(g, "#4B5563") for g in df_analise["Grupo"]
                ],
                marker_cornerradius=4,
            ))
            fig_bar.update_layout(
                barmode="group",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=30, r=20, t=50, b=30),
                title=dict(text="Limite vs. Gasto Real por Grupo", font=dict(size=15), x=0.02),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                yaxis=dict(tickprefix="R$ ", gridcolor="#E2E8F0"),
                bargap=0.3,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # Detail table
            df_show = df_analise.copy()
            st.dataframe(
                df_show,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Limite (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Gasto (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Saldo (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                    "% Renda": st.column_config.NumberColumn(format="%.1f%%"),
                    "Limite (%)": st.column_config.NumberColumn(format="%.0f%%"),
                },
            )

            # Poupança/Dívidas note
            total_dividas_mensal = sum(
                d.get("parcela_mensal_total", 0)
                for d in [_parcela_mensal_dividas()]
            )
            st.caption(
                f"💡 A parcela de **Poupança/Dívidas** inclui investimentos e "
                f"parcelas de dívidas. Valor atual das parcelas mensais: "
                f"R$ {total_dividas_mensal:,.2f}."
            )
    else:
        st.info(
            "Adicione transações na aba **Lançamentos** para ver a análise real dos seus gastos."
        )


def _parcela_mensal_dividas() -> Dict[str, float]:
    """Return total monthly debt installments from session state."""
    from utils.finance_models import calcular_resumo_divida

    def _safe_float(v, d=0.0):
        try:
            return float(v)
        except (TypeError, ValueError):
            return d

    total = 0.0
    for divida in st.session_state.get("dividas", []):
        if str(divida.get("status", "Ativa")).lower() == "quitada":
            continue
        try:
            m = calcular_resumo_divida(
                valor_principal=_safe_float(divida.get("valor_principal")),
                taxa_mensal=_safe_float(divida.get("taxa_mensal")),
                n_parcelas=int(_safe_float(divida.get("n_parcelas"), 1)),
                parcela_atual=int(_safe_float(divida.get("parcela_atual"), 1)),
                sistema=str(divida.get("sistema", "PRICE")),
                status=str(divida.get("status", "Ativa")),
            )
            total += m["parcela_mensal_atual"]
        except ValueError:
            continue
    return {"parcela_mensal_total": total}


# ────────────────────────────────────────────────────────────────
# GERENCIADOR DE SONHOS
# ────────────────────────────────────────────────────────────────

def _render_gerenciador_sonhos() -> None:
    """Render Dreams Goal Manager with compound interest simulator.

    Formula used (FV of annuity):
        FV = P × ((1 + r)^n - 1) / r

    Where:
        FV = Future Value (goal)
        P  = Monthly contribution
        r  = Monthly interest rate (decimal)
        n  = Number of months (solved iteratively)
    """
    st.markdown("##### Gerenciador de Sonhos")
    st.caption(
        "Descubra quanto tempo leva para realizar um sonho investindo mensalmente. "
        "A simulação usa a fórmula de juros compostos sobre aportes mensais."
    )

    with st.form("form_sonho"):
        col1, col2, col3 = st.columns(3)

        with col1:
            nome_sonho = st.text_input(
                "Nome do Sonho", placeholder="Ex: Viagem ao Japão, Entrada do Apartamento"
            )
            fv = st.number_input(
                "Meta (FV) — Valor Total (R$)",
                min_value=1.0,
                value=50000.0,
                step=1000.0,
                format="%.2f",
                help="Quanto você precisa juntar no total.",
            )

        with col2:
            p = st.number_input(
                "Aporte Mensal (P) — R$",
                min_value=0.0,
                value=500.0,
                step=50.0,
                format="%.2f",
                help="Quanto você vai guardar por mês.",
            )
            saldo_inicial = st.number_input(
                "Saldo Inicial já acumulado (R$)",
                min_value=0.0,
                value=0.0,
                step=100.0,
                format="%.2f",
                help="Quanto você já tem guardado para este sonho.",
            )

        with col3:
            taxa_mensal = st.number_input(
                "Taxa de Juros Mensal (r) — %",
                min_value=0.0,
                value=0.8,
                step=0.1,
                format="%.2f",
                help="Rentabilidade mensal esperada (ex: 0.8% ≈ Tesouro Selic).",
            )
            st.markdown("**Referências de taxa:**")
            st.caption("0.8%/mês ≈ Tesouro Selic  \n1.0%/mês ≈ CDB 120% CDI  \n1.5%/mês ≈ renda variável")

        simular = st.form_submit_button("🚀 Simular", use_container_width=True, type="primary")

    if simular or st.session_state.get("_ultimo_sonho"):
        if simular:
            st.session_state._ultimo_sonho = {
                "nome": nome_sonho or "Meu Sonho",
                "fv": fv,
                "p": p,
                "saldo_inicial": saldo_inicial,
                "taxa_mensal": taxa_mensal,
            }

        dados = st.session_state.get("_ultimo_sonho", {})
        if not dados:
            return

        try:
            resultado = simular_meta_sonhos(
                fv=dados["fv"],
                p=dados["p"],
                taxa_mensal=dados["taxa_mensal"],
                saldo_inicial=dados["saldo_inicial"],
            )
        except ValueError as exc:
            st.error(f"Erro na simulação: {exc}")
            return

        st.write("---")
        nome_exib = dados.get("nome", "Meu Sonho")

        if resultado["atingido"]:
            meses = resultado["meses"]
            anos = resultado["anos"]
            st.success(
                f"🎯 **{nome_exib}**: você atingirá sua meta em "
                f"**{meses} meses** ({anos:.1f} anos)!"
            )
        else:
            st.warning(
                f"⚠️ Com R$ {dados['p']:,.2f}/mês e {dados['taxa_mensal']:.2f}%/mês, "
                f"a meta de R$ {dados['fv']:,.2f} não é atingida em 50 anos. "
                "Aumente o aporte ou a taxa esperada."
            )

        # KPI cards
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Meta", f"R$ {dados['fv']:,.2f}")
        k2.metric(
            "Prazo",
            f"{resultado['meses']} meses" if resultado["atingido"] else "50+ anos",
        )
        k3.metric("Total Aportado", f"R$ {resultado['total_aportado']:,.2f}")
        k4.metric(
            "Juros Gerados",
            f"R$ {resultado['juros_gerados']:,.2f}",
            delta=f"{(resultado['juros_gerados'] / dados['fv'] * 100):.1f}% da meta",
            delta_color="normal",
        )

        # Growth curve
        df_curva = pd.DataFrame(resultado["curva"])
        df_curva["Meta"] = dados["fv"]

        fig = go.Figure()

        # Aporte acumulado line (area)
        aportes = [
            dados["saldo_inicial"] + dados["p"] * m
            for m in df_curva["mes"]
        ]
        fig.add_trace(go.Scatter(
            x=df_curva["mes"],
            y=aportes,
            name="Só aportes (sem juros)",
            line=dict(color="#94A3B8", width=1.5, dash="dot"),
            hovertemplate="Mês %{x}<br>Sem juros: R$ %{y:,.2f}<extra></extra>",
        ))

        # Compound growth area
        fig.add_trace(go.Scatter(
            x=df_curva["mes"],
            y=df_curva["saldo"],
            name="Com juros compostos",
            line=dict(color="#16A34A", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(22,163,74,0.08)",
            hovertemplate="Mês %{x}<br>Saldo: R$ %{y:,.2f}<extra></extra>",
        ))

        # Goal line
        fig.add_trace(go.Scatter(
            x=df_curva["mes"],
            y=df_curva["Meta"],
            name=f"Meta: R$ {dados['fv']:,.2f}",
            line=dict(color="#DC2626", width=1.5, dash="dash"),
            hovertemplate="Meta: R$ %{y:,.2f}<extra></extra>",
        ))

        # Mark intersection
        if resultado["atingido"]:
            fig.add_vline(
                x=resultado["meses"],
                line_width=1,
                line_dash="dot",
                line_color="#EA580C",
                annotation_text=f"  Mês {resultado['meses']}",
                annotation_position="top right",
            )

        fig.update_layout(
            title=dict(
                text=f"Curva de crescimento — {nome_exib}",
                font=dict(size=15),
                x=0.02,
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=30, r=20, t=60, b=30),
            xaxis=dict(
                title="Meses",
                gridcolor="#E2E8F0",
                tickfont=dict(size=11),
            ),
            yaxis=dict(
                title="Saldo (R$)",
                tickprefix="R$ ",
                gridcolor="#E2E8F0",
                tickfont=dict(size=11),
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=11),
            ),
            hoverlabel=dict(bgcolor="white", font_size=12),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Storytelling text
        if resultado["atingido"]:
            juros_pct = (resultado["juros_gerados"] / dados["fv"]) * 100
            st.info(
                f"📖 **Data Storytelling:** Dos R$ {dados['fv']:,.2f} necessários para "
                f"**{nome_exib}**, você precisará aportar R$ {resultado['total_aportado']:,.2f} "
                f"e os juros compostos farão o resto — gerando R$ {resultado['juros_gerados']:,.2f} "
                f"({juros_pct:.1f}% do total). Comece hoje: cada mês de atraso aumenta o esforço necessário."
            )

        # Sensitivity table: vary monthly contribution
        st.write("---")
        st.markdown("##### Tabela de Sensibilidade — variação do aporte mensal")
        st.caption("Veja como mudar o aporte impacta o prazo.")

        base_p = dados["p"]
        variacoes = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        sens_rows = []
        for fator in variacoes:
            p_var = base_p * fator
            if p_var <= 0:
                continue
            try:
                r = simular_meta_sonhos(
                    fv=dados["fv"],
                    p=p_var,
                    taxa_mensal=dados["taxa_mensal"],
                    saldo_inicial=dados["saldo_inicial"],
                )
                sens_rows.append({
                    "Aporte Mensal": p_var,
                    "Meses": r["meses"] if r["atingido"] else ">600",
                    "Anos": f"{r['anos']:.1f}" if r["atingido"] else ">50",
                    "Total Aportado": r["total_aportado"] if r["atingido"] else None,
                    "Juros Gerados": r["juros_gerados"] if r["atingido"] else None,
                })
            except ValueError:
                continue

        if sens_rows:
            df_sens = pd.DataFrame(sens_rows)
            st.dataframe(
                df_sens,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Aporte Mensal": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Total Aportado": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Juros Gerados": st.column_config.NumberColumn(format="R$ %.2f"),
                },
            )
    else:
        st.info("Preencha os campos acima e clique em **Simular** para ver a projeção.")
