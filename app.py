"""Dashboard Financeiro Familiar - Main Application.

A Streamlit-based financial management dashboard for families.
Enables tracking of income/expenses, categorization, budgeting, and financial analysis.

Features:
    - Upload bank statements (CSV/XLSX)
    - Manual transaction entry
    - Family member management
    - Expense categorization and analysis
    - Budget planning and recurring expense tracking
    - Financial dashboard with KPIs and visualizations
"""

import streamlit as st
from utils.helpers import initialize_session_state, load_css
from ui.sidebar import render_sidebar
from ui.tabs import (
    render_dashboard,
    render_lancamentos,
    render_familia,
    render_extrato,
    render_configuracoes,
)

# --- Configuração Inicial ---
st.set_page_config(
    page_title="Dashboard Financeiro Familiar",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_session_state()
load_css("styles/main.css")

# --- Layout ---
st.title("👨‍👩‍👧‍👦 Dashboard Financeiro Familiar")

render_sidebar()

# --- Navegação por Tabs ---
tab_dashboard, tab_lancamentos, tab_familia, tab_extrato, tab_config = st.tabs(
    ["📊 Dashboard", "📝 Lançamentos", "👥 Família", "📋 Extrato", "⚙️ Configurações"]
)

with tab_dashboard:
    render_dashboard()

with tab_lancamentos:
    render_lancamentos()

with tab_familia:
    render_familia()

with tab_extrato:
    render_extrato()

with tab_config:
    render_configuracoes()
