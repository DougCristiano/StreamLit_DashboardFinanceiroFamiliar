"""Dívidas tab — debt management with PRICE/SAC amortization."""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from typing import Any, Dict, List
from utils.helpers import salvar_dividas
from utils.finance_models import (
    calcular_parcela_price,
    calcular_parcela_sac,
    gerar_cronograma_price,
    gerar_cronograma_sac,
    calcular_resumo_divida,
)

_CHART_COLORS = {
    "despesa": "#DC2626",
    "text": "#1A1A2E",
    "text_muted": "#64748B",
    "grid": "#E2E8F0",
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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


def render_dividas() -> None:
    """Render debts tab with PRICE/SAC calculations and installment tracking."""
    st.markdown("##### Cadastro de Dívidas e Parcelas")

    with st.form("form_divida", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            nome = st.text_input("Nome da dívida", placeholder="Ex: Cartão Nubank")
            credor = st.text_input("Credor/Banco", placeholder="Ex: Nubank")

        with col2:
            sistema = st.selectbox("Sistema", ["PRICE", "SAC"])
            status = st.selectbox("Status", ["Ativa", "Quitada"])

        with col3:
            valor_principal = st.number_input(
                "Valor principal (R$)", min_value=0.01, value=1000.0, step=100.0, format="%.2f"
            )
            taxa_mensal = st.number_input(
                "Juros mensal (%)", min_value=0.0, value=2.0, step=0.1, format="%.2f"
            )

        with col4:
            n_parcelas = st.number_input(
                "Qtd. parcelas", min_value=1, value=12, step=1, format="%d"
            )
            parcela_atual = st.number_input(
                "Parcela atual", min_value=1, value=1, step=1, format="%d"
            )
            vencimento_dia = st.number_input(
                "Dia vencimento", min_value=1, max_value=31, value=10, step=1
            )

        try:
            if sistema == "PRICE":
                preview_parcela = calcular_parcela_price(
                    valor_principal, taxa_mensal, int(n_parcelas)
                )
            else:
                preview_parcela = calcular_parcela_sac(
                    valor_principal, taxa_mensal, int(n_parcelas),
                    int(min(parcela_atual, n_parcelas)),
                )
            st.caption(f"Prévia da parcela atual: R$ {preview_parcela:,.2f}")
        except ValueError as exc:
            st.caption(f"Prévia indisponível: {exc}")

        submitted = st.form_submit_button(
            "➕ Adicionar Dívida", use_container_width=True, type="primary"
        )

        if submitted:
            if not nome.strip() or not credor.strip():
                st.error("Informe nome da dívida e credor.")
            elif int(parcela_atual) > int(n_parcelas):
                st.error("Parcela atual não pode ser maior que total de parcelas.")
            else:
                nova_divida = {
                    "id": int(datetime.utcnow().timestamp() * 1000000),
                    "nome": nome.strip(),
                    "credor": credor.strip(),
                    "sistema": sistema,
                    "status": status,
                    "valor_principal": float(valor_principal),
                    "taxa_mensal": float(taxa_mensal),
                    "n_parcelas": int(n_parcelas),
                    "parcela_atual": (
                        int(n_parcelas) if status == "Quitada" else int(parcela_atual)
                    ),
                    "vencimento_dia": int(vencimento_dia),
                }
                st.session_state.dividas.append(nova_divida)
                salvar_dividas()
                st.success("Dívida cadastrada com sucesso.")
                st.rerun()

    st.write("---")

    resumo = _resumo_dividas(st.session_state.dividas)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TOTAL EM DÍVIDAS", f"R$ {resumo['total_em_dividas']:,.2f}")
    m2.metric("TOTAL JÁ PAGO", f"R$ {resumo['total_pago']:,.2f}")
    m3.metric("TOTAL RESTANTE", f"R$ {resumo['total_restante']:,.2f}")
    m4.metric("PARCELA MENSAL TOTAL", f"R$ {resumo['parcela_mensal_total']:,.2f}")

    if not st.session_state.dividas:
        st.info("Nenhuma dívida cadastrada ainda.")
        return

    st.markdown("##### Carteira de Dívidas")
    status_options = sorted({item.get("status", "Ativa") for item in st.session_state.dividas})
    credor_options = sorted(
        {item.get("credor", "") for item in st.session_state.dividas if item.get("credor")}
    )

    f1, f2 = st.columns(2)
    with f1:
        filtro_status = st.multiselect("Filtrar por status", status_options, default=status_options)
    with f2:
        filtro_credor = st.multiselect("Filtrar por credor", credor_options)

    rows = []
    for divida in st.session_state.dividas:
        if filtro_status and divida.get("status") not in filtro_status:
            continue
        if filtro_credor and divida.get("credor") not in filtro_credor:
            continue
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

        np_ = int(_safe_float(divida.get("n_parcelas"), 1.0))
        pa_ = int(_safe_float(divida.get("parcela_atual"), 1.0))
        progresso = (pa_ / np_) * 100 if np_ > 0 else 0.0

        rows.append({
            "ID": divida.get("id"),
            "Dívida": divida.get("nome"),
            "Credor": divida.get("credor"),
            "Sistema": divida.get("sistema"),
            "Status": divida.get("status"),
            "Parcela": f"{pa_}/{np_}",
            "Juros (%)": _safe_float(divida.get("taxa_mensal")),
            "Parcela Atual (R$)": metricas["parcela_mensal_atual"],
            "Total Restante (R$)": metricas["total_restante"],
            "Progresso (%)": progresso,
        })

    if rows:
        df_dividas = pd.DataFrame(rows)
        st.dataframe(
            df_dividas,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Parcela Atual (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Total Restante (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Progresso (%)": st.column_config.NumberColumn(format="%.1f%%"),
            },
        )
    else:
        st.info("Nenhuma dívida corresponde aos filtros atuais.")

    st.write("---")
    st.markdown("##### Ações de Parcelas")

    dividas_por_id = {int(item["id"]): item for item in st.session_state.dividas}
    ids = list(dividas_por_id.keys())
    selecionada_id = st.selectbox(
        "Selecione uma dívida",
        ids,
        format_func=lambda x: (
            f"{dividas_por_id[x].get('nome')} - "
            f"{dividas_por_id[x].get('credor')} "
            f"({dividas_por_id[x].get('parcela_atual')}/{dividas_por_id[x].get('n_parcelas')})"
        ),
    )
    divida_sel = dividas_por_id[selecionada_id]

    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button("➡️ Avançar Parcela", use_container_width=True):
            if divida_sel.get("status") == "Quitada":
                st.warning("Esta dívida já está quitada.")
            else:
                atual = int(divida_sel.get("parcela_atual", 1))
                total = int(divida_sel.get("n_parcelas", 1))
                if atual < total:
                    divida_sel["parcela_atual"] = atual + 1
                    if divida_sel["parcela_atual"] >= total:
                        divida_sel["status"] = "Quitada"
                    salvar_dividas()
                    st.success("Parcela avançada com sucesso.")
                    st.rerun()
                else:
                    divida_sel["status"] = "Quitada"
                    salvar_dividas()
                    st.success("Dívida marcada como quitada.")
                    st.rerun()

    with a2:
        if st.button("✅ Marcar Quitada", use_container_width=True):
            divida_sel["status"] = "Quitada"
            divida_sel["parcela_atual"] = int(divida_sel.get("n_parcelas", 1))
            salvar_dividas()
            st.success("Dívida quitada com sucesso.")
            st.rerun()

    with a3:
        if st.button("🗑️ Excluir Dívida", use_container_width=True):
            st.session_state.dividas = [
                item for item in st.session_state.dividas
                if int(item.get("id", -1)) != int(selecionada_id)
            ]
            salvar_dividas()
            st.success("Dívida removida.")
            st.rerun()

    st.write("---")
    st.markdown("##### Cronograma da Dívida Selecionada")
    try:
        sistema_sel = str(divida_sel.get("sistema", "PRICE")).upper()
        if sistema_sel == "SAC":
            cronograma = gerar_cronograma_sac(
                _safe_float(divida_sel.get("valor_principal")),
                _safe_float(divida_sel.get("taxa_mensal")),
                int(_safe_float(divida_sel.get("n_parcelas"), 1.0)),
            )
        else:
            cronograma = gerar_cronograma_price(
                _safe_float(divida_sel.get("valor_principal")),
                _safe_float(divida_sel.get("taxa_mensal")),
                int(_safe_float(divida_sel.get("n_parcelas"), 1.0)),
            )

        df_crono = pd.DataFrame(cronograma)
        if not df_crono.empty:
            df_crono = df_crono.rename(columns={
                "parcela": "Parcela",
                "valor_parcela": "Valor Parcela",
                "juros": "Juros",
                "amortizacao": "Amortização",
                "saldo_devedor": "Saldo Devedor",
            })
            st.dataframe(
                df_crono,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Valor Parcela": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Juros": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Amortização": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Saldo Devedor": st.column_config.NumberColumn(format="R$ %.2f"),
                },
            )

            fig_saldo_divida = px.line(
                df_crono,
                x="Parcela",
                y="Saldo Devedor",
                markers=True,
                color_discrete_sequence=[_CHART_COLORS["despesa"]],
            )
            fig_saldo_divida.update_layout(
                title=dict(text="Evolução do Saldo Devedor", font=dict(size=15), x=0.02),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=30, r=20, t=50, b=30),
            )
            st.plotly_chart(fig_saldo_divida, use_container_width=True)
    except ValueError as exc:
        st.warning(f"Não foi possível gerar cronograma: {exc}")
