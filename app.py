"""Dashboard Financeiro Familiar - Main Application.

A Streamlit-based financial management dashboard for families.
Enables tracking of income/expenses, categorization, budgeting, and financial analysis.

Features:
    - Upload bank statements (CSV/XLSX)
    - Manual transaction entry
    - Family member management
    - Expense categorization and analysis
    - Debt tracking with installments (PRICE/SAC)
    - Investment tracking and reserve goals
    - Budget planning (50/30/20 rule)
    - Dreams Goal Manager (compound interest simulator)
    - Financial dashboard with KPIs, storytelling, and visualizations
    - Development mode with realistic sample data
"""

import streamlit as st
from utils.helpers import initialize_session_state, load_css
from utils.processing import processar_dados
from ui.sidebar import render_sidebar
from ui.tab_dashboard import render_dashboard
from ui.tab_lancamentos import render_lancamentos
from ui.tab_familia import render_familia
from ui.tab_extrato import render_extrato
from ui.tab_dividas import render_dividas
from ui.tab_investimentos import render_investimentos
from ui.tab_planejamento import render_planejamento
from ui.tab_configuracoes import render_configuracoes

# ── Theme CSS blocks injected into the page ──────────────────────────────────
_TEMA_CSS: dict[str, str] = {
    "Neutro": """
        :root {
            --accent: #4B5563 !important;
            --accent-light: #F3F4F6 !important;
            --accent-hover: #374151 !important;
        }
        .stTabs [aria-selected="true"] {
            background: #4B5563 !important;
        }
        [data-testid="stFormSubmitButton"] > button {
            background: #4B5563 !important;
        }
    """,
    "Claro (Azul)": """
        :root {
            --accent: #1565C0 !important;
            --accent-light: #E3F2FD !important;
            --accent-hover: #1E88E5 !important;
        }
        .stTabs [aria-selected="true"] {
            background: #1565C0 !important;
        }
        [data-testid="stFormSubmitButton"] > button {
            background: #1565C0 !important;
        }
    """,
    "Escuro": """
        :root {
            --bg-page: #0F172A !important;
            --bg-white: #1E293B !important;
            --bg-sidebar: #1E293B !important;
            --bg-card: #334155 !important;
            --bg-card-hover: #475569 !important;
            --bg-input: #1E293B !important;
            --text-dark: #F1F5F9 !important;
            --text-body: #CBD5E1 !important;
            --text-muted: #94A3B8 !important;
            --text-label: #CBD5E1 !important;
            --border: #475569 !important;
            --border-light: #334155 !important;
            --accent: #60A5FA !important;
            --accent-light: rgba(96,165,250,0.1) !important;
            --accent-hover: #93C5FD !important;
        }
        .stTabs [aria-selected="true"] {
            background: #60A5FA !important;
            color: #0F172A !important;
        }
        [data-testid="stApp"] {
            background-color: #0F172A !important;
        }
        [data-testid="stFormSubmitButton"] > button {
            background: #60A5FA !important;
            color: #0F172A !important;
        }
    """,
}

# ── App setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Financeiro Familiar",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_session_state()

# Rebuild df_transacoes from persisted data on startup
if st.session_state.df_transacoes is None and (
    st.session_state.get("transacoes")
    or st.session_state.get("transacoes_importadas")
    or st.session_state.get("df_from_upload") is not None
):
    processar_dados()

# ── Base CSS + theme overlay ─────────────────────────────────────────────────
load_css("styles/main.css")

tema_atual = st.session_state.get("tema", "Neutro")
tema_css = _TEMA_CSS.get(tema_atual, _TEMA_CSS["Neutro"])
st.markdown(f"<style>{tema_css}</style>", unsafe_allow_html=True)

# ── Dev mode: load sample data ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("---")
    with st.expander("🛠️ Modo Desenvolvimento", expanded=False):
        st.caption("Carrega dados simulados realistas para testar o dashboard sem arquivos reais.")
        if st.button("▶️ Carregar dados de exemplo", use_container_width=True):
            from utils.dev_data import (
                gerar_transacoes_exemplo,
                gerar_dividas_exemplo,
                gerar_investimentos_exemplo,
                gerar_metas_exemplo,
            )
            membros = st.session_state.get("membros_familia", ["Douglas", "Família Conjunta"])
            st.session_state.transacoes = gerar_transacoes_exemplo(membros=membros, meses=3)
            st.session_state.dividas = gerar_dividas_exemplo()
            st.session_state.investimentos = gerar_investimentos_exemplo()
            st.session_state.metas_reserva = gerar_metas_exemplo()
            if "renda_liquida" not in st.session_state or st.session_state.renda_liquida == 0.0:
                st.session_state.renda_liquida = 10000.0
            processar_dados()
            st.success("Dados de exemplo carregados!")
            st.rerun()

        if st.button("🗑️ Limpar dados de exemplo", use_container_width=True, type="secondary"):
            st.session_state.transacoes = []
            st.session_state.transacoes_importadas = []
            st.session_state.dividas = []
            st.session_state.investimentos = []
            st.session_state.metas_reserva = []
            st.session_state.df_from_upload = None
            st.session_state.df_transacoes = None
            st.session_state.renda_liquida = 0.0
            st.rerun()

# ── Title ────────────────────────────────────────────────────────────────────
st.title("👨‍👩‍👧‍👦 Dashboard Financeiro Familiar")

render_sidebar()

# ── Navigation tabs ──────────────────────────────────────────────────────────
(
    tab_dashboard,
    tab_lancamentos,
    tab_familia,
    tab_extrato,
    tab_planejamento,
    tab_dividas,
    tab_investimentos,
    tab_config,
) = st.tabs(
    [
        "📊 Dashboard",
        "📝 Lançamentos",
        "👥 Família",
        "📋 Extrato",
        "🎯 Planejamento",
        "💳 Dívidas",
        "📈 Investimentos",
        "⚙️ Configurações",
    ]
)

with tab_dashboard:
    render_dashboard()

with tab_lancamentos:
    render_lancamentos()

with tab_familia:
    render_familia()

with tab_extrato:
    render_extrato()

with tab_planejamento:
    render_planejamento()

with tab_dividas:
    render_dividas()

with tab_investimentos:
    render_investimentos()

with tab_config:
    render_configuracoes()
