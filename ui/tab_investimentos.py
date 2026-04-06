"""Investimentos tab — portfolio tracking and reserve goals."""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from typing import Any, Dict, List
from utils.helpers import salvar_investimentos, salvar_metas_reserva
from utils.finance_models import calcular_rentabilidade, calcular_progresso_meta

_PALETTE = [
    "#4B5563", "#16A34A", "#EA580C", "#DC2626",
    "#7C3AED", "#0891B2", "#D97706", "#4338CA",
]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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
        valor_meta = _safe_float(meta.get("valor_meta"))
        valor_atual = _safe_float(meta.get("valor_atual"))
        if valor_meta > 0:
            try:
                progressos.append(calcular_progresso_meta(valor_atual, valor_meta))
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


def render_investimentos() -> None:
    """Render investments tab with portfolio and reserve goals tracking."""
    st.markdown("##### Investimentos e Dinheiro Guardado")

    with st.form("form_investimento", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            tipo = st.selectbox(
                "Tipo", ["Poupança", "CDB", "Tesouro", "Ações", "FII", "Cripto", "Outro"]
            )
            instituicao = st.text_input("Instituição", placeholder="Ex: XP, Itaú")

        with col2:
            valor_aplicado = st.number_input(
                "Valor aplicado (R$)", min_value=0.01, value=1000.0, step=100.0, format="%.2f"
            )
            valor_atual = st.number_input(
                "Valor atual (R$)", min_value=0.0, value=1000.0, step=100.0, format="%.2f"
            )

        with col3:
            aporte_mensal = st.number_input(
                "Aporte mensal (R$)", min_value=0.0, value=0.0, step=50.0, format="%.2f"
            )
            data_aplicacao = st.date_input("Data da aplicação", value=date.today())

        with col4:
            liquidez = st.selectbox(
                "Liquidez", ["Imediata", "D+1", "D+2", "D+30", "No vencimento"]
            )
            objetivo = st.text_input("Objetivo", placeholder="Ex: Reserva emergência")

        try:
            prev_rent = calcular_rentabilidade(valor_aplicado, valor_atual)
            st.caption(
                f"Prévia de rentabilidade: R$ {prev_rent['lucro']:,.2f} ({prev_rent['rentabilidade_percentual']:.2f}%)"
            )
        except ValueError as exc:
            st.caption(f"Prévia indisponível: {exc}")

        submitted = st.form_submit_button(
            "➕ Adicionar Investimento", use_container_width=True, type="primary"
        )

        if submitted:
            if not instituicao.strip() or not objetivo.strip():
                st.error("Informe instituição e objetivo do investimento.")
            else:
                novo_investimento = {
                    "id": int(datetime.utcnow().timestamp() * 1000000),
                    "tipo": tipo,
                    "instituicao": instituicao.strip(),
                    "valor_aplicado": float(valor_aplicado),
                    "valor_atual": float(valor_atual),
                    "aporte_mensal": float(aporte_mensal),
                    "data_aplicacao": str(data_aplicacao),
                    "objetivo": objetivo.strip(),
                    "liquidez": liquidez,
                }
                st.session_state.investimentos.append(novo_investimento)
                salvar_investimentos()
                st.success("Investimento adicionado com sucesso.")
                st.rerun()

    st.write("---")

    resumo = _resumo_investimentos(
        st.session_state.investimentos, st.session_state.metas_reserva
    )
    mi1, mi2, mi3 = st.columns(3)
    mi1.metric("PATRIMÔNIO ATUAL", f"R$ {resumo['patrimonio_atual']:,.2f}")
    mi2.metric(
        "RENTABILIDADE TOTAL",
        f"R$ {resumo['rentabilidade_reais']:,.2f}",
        delta=f"{resumo['rentabilidade_percentual']:.2f}%",
        delta_color="normal",
    )
    mi3.metric("PROGRESSO MÉDIO METAS", f"{resumo['progresso_medio_metas']:.1f}%")

    st.markdown("##### Carteira de Investimentos")
    if st.session_state.investimentos:
        rows = []
        for inv in st.session_state.investimentos:
            try:
                rent = calcular_rentabilidade(
                    _safe_float(inv.get("valor_aplicado")),
                    _safe_float(inv.get("valor_atual")),
                )
            except ValueError:
                continue

            rows.append({
                "ID": inv.get("id"),
                "Tipo": inv.get("tipo"),
                "Instituição": inv.get("instituicao"),
                "Objetivo": inv.get("objetivo"),
                "Liquidez": inv.get("liquidez"),
                "Valor Aplicado (R$)": _safe_float(inv.get("valor_aplicado")),
                "Valor Atual (R$)": _safe_float(inv.get("valor_atual")),
                "Aporte Mensal (R$)": _safe_float(inv.get("aporte_mensal")),
                "Rentabilidade (R$)": rent["lucro"],
                "Rentabilidade (%)": rent["rentabilidade_percentual"],
            })

        df_inv = pd.DataFrame(rows)
        st.dataframe(
            df_inv,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Valor Aplicado (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Valor Atual (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Aporte Mensal (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Rentabilidade (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Rentabilidade (%)": st.column_config.NumberColumn(format="%.2f%%"),
            },
        )

        fig_tipo = px.bar(
            df_inv,
            x="Tipo",
            y="Valor Atual (R$)",
            color="Tipo",
            color_discrete_sequence=_PALETTE,
        )
        fig_tipo.update_layout(
            title=dict(text="Distribuição por Tipo de Investimento", font=dict(size=15), x=0.02),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=30, r=20, t=50, b=30),
            showlegend=False,
        )
        st.plotly_chart(fig_tipo, use_container_width=True)

        inv_by_id = {int(item["id"]): item for item in st.session_state.investimentos}
        inv_sel_id = st.selectbox(
            "Selecione investimento para atualizar/remover",
            list(inv_by_id.keys()),
            format_func=lambda x: (
                f"{inv_by_id[x].get('tipo')} - {inv_by_id[x].get('instituicao')} "
                f"({inv_by_id[x].get('objetivo')})"
            ),
            key="inv_select_acao",
        )
        valor_atual_novo = st.number_input(
            "Novo valor atual (R$)",
            min_value=0.0,
            value=_safe_float(inv_by_id[inv_sel_id].get("valor_atual")),
            step=100.0,
            format="%.2f",
            key="inv_valor_atual_novo",
        )

        ai1, ai2 = st.columns(2)
        with ai1:
            if st.button("💾 Atualizar Valor Atual", use_container_width=True):
                inv_by_id[inv_sel_id]["valor_atual"] = float(valor_atual_novo)
                salvar_investimentos()
                st.success("Valor atualizado com sucesso.")
                st.rerun()
        with ai2:
            if st.button("🗑️ Remover Investimento", use_container_width=True):
                st.session_state.investimentos = [
                    item for item in st.session_state.investimentos
                    if int(item.get("id", -1)) != int(inv_sel_id)
                ]
                salvar_investimentos()
                st.success("Investimento removido.")
                st.rerun()
    else:
        st.info("Nenhum investimento cadastrado ainda.")

    st.write("---")
    st.markdown("##### Metas de Reserva")

    with st.form("form_meta_reserva", clear_on_submit=True):
        g1, g2, g3 = st.columns(3)
        with g1:
            objetivo_meta = st.text_input("Objetivo da meta", placeholder="Ex: Reserva de emergência")
        with g2:
            valor_meta = st.number_input(
                "Valor da meta (R$)", min_value=0.01, value=5000.0, step=500.0, format="%.2f"
            )
        with g3:
            valor_atual_meta = st.number_input(
                "Valor atual acumulado (R$)", min_value=0.0, value=0.0, step=100.0, format="%.2f"
            )

        submitted_meta = st.form_submit_button(
            "🎯 Adicionar Meta", use_container_width=True, type="primary"
        )
        if submitted_meta:
            if not objetivo_meta.strip():
                st.error("Informe o objetivo da meta.")
            else:
                nova_meta = {
                    "id": int(datetime.utcnow().timestamp() * 1000000),
                    "objetivo": objetivo_meta.strip(),
                    "valor_meta": float(valor_meta),
                    "valor_atual": float(valor_atual_meta),
                }
                st.session_state.metas_reserva.append(nova_meta)
                salvar_metas_reserva()
                st.success("Meta adicionada com sucesso.")
                st.rerun()

    if st.session_state.metas_reserva:
        metas_rows = []
        for meta in st.session_state.metas_reserva:
            try:
                progresso = calcular_progresso_meta(
                    _safe_float(meta.get("valor_atual")),
                    _safe_float(meta.get("valor_meta")),
                )
            except ValueError:
                progresso = 0.0

            metas_rows.append({
                "ID": meta.get("id"),
                "Objetivo": meta.get("objetivo"),
                "Valor Atual (R$)": _safe_float(meta.get("valor_atual")),
                "Valor Meta (R$)": _safe_float(meta.get("valor_meta")),
                "Progresso (%)": progresso,
            })

        df_metas = pd.DataFrame(metas_rows)
        st.dataframe(
            df_metas,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Valor Atual (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Valor Meta (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Progresso (%)": st.column_config.NumberColumn(format="%.2f%%"),
            },
        )

        fig_metas = px.bar(
            df_metas,
            x="Objetivo",
            y="Progresso (%)",
            color="Progresso (%)",
            color_continuous_scale=["#DC2626", "#EA580C", "#16A34A"],
        )
        fig_metas.update_layout(
            title=dict(text="Progresso das Metas de Reserva", font=dict(size=15), x=0.02),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=30, r=20, t=50, b=30),
        )
        st.plotly_chart(fig_metas, use_container_width=True)

        metas_by_id = {int(item["id"]): item for item in st.session_state.metas_reserva}
        meta_sel_id = st.selectbox(
            "Selecione meta para atualizar/remover",
            list(metas_by_id.keys()),
            format_func=lambda x: metas_by_id[x].get("objetivo", "Meta"),
            key="meta_select_acao",
        )
        novo_valor_meta_atual = st.number_input(
            "Novo valor atual da meta (R$)",
            min_value=0.0,
            value=_safe_float(metas_by_id[meta_sel_id].get("valor_atual")),
            step=100.0,
            format="%.2f",
            key="meta_valor_atual_novo",
        )

        gm1, gm2 = st.columns(2)
        with gm1:
            if st.button("💾 Atualizar Progresso da Meta", use_container_width=True):
                metas_by_id[meta_sel_id]["valor_atual"] = float(novo_valor_meta_atual)
                salvar_metas_reserva()
                st.success("Meta atualizada com sucesso.")
                st.rerun()
        with gm2:
            if st.button("🗑️ Remover Meta", use_container_width=True):
                st.session_state.metas_reserva = [
                    item for item in st.session_state.metas_reserva
                    if int(item.get("id", -1)) != int(meta_sel_id)
                ]
                salvar_metas_reserva()
                st.success("Meta removida.")
                st.rerun()
    else:
        st.info("Nenhuma meta de reserva cadastrada ainda.")
