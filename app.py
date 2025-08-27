import streamlit as st
from utils.helpers import initialize_session_state, load_css
from ui.sidebar import render_sidebar
from ui.tabs import (
    render_visao_geral,
    render_analise_categoria,
    render_extrato_detalhado,
    render_despesas_recorrentes,
    render_orcamento_planejamento,
    render_configuracoes
)

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(
    page_title="Dashboard Financeiro Familiar",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa o session_state (se ainda não foi feito)
initialize_session_state()


# --- 2. CARREGAMENTO DE ESTILOS (CSS) ---
load_css('styles/main.css')
if st.session_state.theme == "Nubank":
    load_css('styles/nubank_theme.css')
elif st.session_state.theme == "Escuro":
    load_css('styles/dark_theme.css')


# --- 3. LAYOUT PRINCIPAL ---
st.title("👨‍👩‍👧‍👦 Dashboard Financeiro Familiar")
st.write("Faça o upload do extrato mensal da família para análise e planeje seus gastos.")

render_sidebar()

# --- 4. NAVEGAÇÃO E CONTEÚDO DAS ABAS ---
tab_options = ["📊 Visão Geral Mensal", "🏷️ Análise por Categoria", "📋 Extrato Detalhado", "🔁 Despesas Recorrentes", "🔮 Orçamento e Planejamento", "⚙️ Configurações"]
st.radio("Navegação", options=tab_options, key="active_tab", horizontal=True, label_visibility="collapsed")

# Dicionário para mapear a aba selecionada para a função que a renderiza
tabs_functions = {
    "📊 Visão Geral Mensal": render_visao_geral,
    "🏷️ Análise por Categoria": render_analise_categoria,
    "📋 Extrato Detalhado": render_extrato_detalhado,
    "🔁 Despesas Recorrentes": render_despesas_recorrentes,
    "🔮 Orçamento e Planejamento": render_orcamento_planejamento,
    "⚙️ Configurações": render_configuracoes,
}

# Verifica se há dados para exibir as abas principais
has_data = st.session_state.get('processed_data') is not None and not st.session_state.processed_data.empty

selected_tab_function = tabs_functions.get(st.session_state.active_tab)

if selected_tab_function in [render_despesas_recorrentes, render_orcamento_planejamento, render_configuracoes]:
    # Estas abas podem ser exibidas mesmo sem dados carregados
    selected_tab_function()
elif has_data:
    # Estas abas dependem de dados
    selected_tab_function()
else:
    # Mensagem padrão se nenhuma aba que depende de dados for selecionada e não houver dados
    st.info("⬅️ Por favor, carregue o extrato da família na barra lateral ou adicione uma despesa manual para iniciar a análise.")