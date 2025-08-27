# =======================================================
# 💰 Dashboard Financeiro Familiar — Versão Corrigida
# =======================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import unicodedata
import json
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dashboard Financeiro Familiar",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CONSTANTES E ARQUIVOS ---
CATEGORIES_FILE = "categorias.json"

# --- 3. FUNÇÕES AUXILIARES ---
def normalizar_texto(texto: str) -> str:
    texto = str(texto).lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto

def load_json(file, default: dict) -> dict:
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(file, data: dict):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def categorizar_despesa(descricao, categories):
    desc_norm = normalizar_texto(descricao)
    for categoria, palavras_chave in categories.items():
        if any(palavra in desc_norm for palavra in palavras_chave):
            return categoria
    return "Outros"

def ensure_required_cols(df: pd.DataFrame):
    required = {"date", "title", "amount"}
    if not required.issubset(df.columns):
        st.error(f"Arquivo inválido. É necessário conter as colunas: {required}")
        st.stop()

# --- 4. INICIALIZAÇÃO DO SESSION STATE ---
if 'despesas_manuais' not in st.session_state:
    st.session_state.despesas_manuais = []
if 'rendas_mensais' not in st.session_state:
    st.session_state.rendas_mensais = {}
if 'categories' not in st.session_state:
    st.session_state.categories = load_json(CATEGORIES_FILE, {
        "Alimentação": ["ifood", "restaurante", "mercado", "supermercado", "lanche"],
        "Transporte": ["uber", "99", "transporte", "gasolina", "combustivel", "onibus"],
        "Moradia": ["aluguel", "condominio", "luz", "internet", "agua", "vivo"],
        "Saúde": ["farmacia", "remedio", "medico", "plano de saude", "drog", "cityfarma"],
        "Lazer": ["cinema", "show", "bar", "viagem", "lazer", "netflix", "spotify"],
        "Educação": ["escola", "faculdade", "curso", "livros"],
        "Compras": ["lojas", "roupas", "compras", "amazon", "mercado livre"],
        "Outros": []
    })
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'df_from_upload' not in st.session_state: # NOVO: State para guardar dados do arquivo
    st.session_state.df_from_upload = None
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "📊 Visão Geral Mensal"

if 'orcamento_mensal' not in st.session_state:
    st.session_state.orcamento_mensal = {cat: 0.0 for cat in st.session_state.categories.keys()}
if 'despesas_recorrentes' not in st.session_state:
    st.session_state.despesas_recorrentes = pd.DataFrame(columns=["Descrição", "Valor", "Categoria"])

if 'previsao_renda_fixa' not in st.session_state:
    st.session_state.previsao_renda_fixa = 0.0
if 'previsao_renda_variavel' not in st.session_state:
    st.session_state.previsao_renda_variavel = 0.0
if 'previsao_despesas_fixas' not in st.session_state:
    st.session_state.previsao_despesas_fixas = pd.DataFrame(columns=["Descrição", "Valor"])

default_configs = {
    'theme': "Claro (Padrão)", 'chart_font': "Arial", 'chart_title_size': 22,
    'chart_tick_size': 14, 'chart_insidetext_size': 12, 'chart_legend_size': 14,
    'chart_theme': "streamlit"
}
for key, value in default_configs.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- NOVA FUNÇÃO DE PROCESSAMENTO CENTRALIZADO ---
def processar_dados():
    """
    Combina dados do arquivo carregado e despesas manuais,
    processa-os e armazena em st.session_state.processed_data.
    """
    dfs_to_combine = []

    # Adiciona dados do arquivo se existirem
    if st.session_state.df_from_upload is not None:
        df_extrato = st.session_state.df_from_upload.copy()
        df_extrato.rename(columns={'date': 'Data', 'title': 'Descrição', 'amount': 'Valor'}, inplace=True)
        df_extrato = df_extrato[~df_extrato['Descrição'].str.contains("pagamento recebido", case=False, na=False)]
        dfs_to_combine.append(df_extrato)

    # Adiciona dados manuais se existirem
    if st.session_state.despesas_manuais:
        df_manuais = pd.DataFrame(st.session_state.despesas_manuais)
        dfs_to_combine.append(df_manuais)

    # Se não houver dados, limpa o state e encerra
    if not dfs_to_combine:
        st.session_state.processed_data = None
        return

    # Combina e processa os dados
    df_completo = pd.concat(dfs_to_combine, ignore_index=True)
    df_completo['Data'] = pd.to_datetime(df_completo['Data'], errors='coerce')
    df_completo.dropna(subset=['Data'], inplace=True)
    df_completo['Valor'] = pd.to_numeric(df_completo['Valor'], errors='coerce')
    df_completo.dropna(subset=['Valor'], inplace=True)

    despesas_df = df_completo[df_completo['Valor'] != 0].copy()
    despesas_df['Gastos'] = despesas_df['Valor'].abs()
    despesas_df['Categoria'] = despesas_df['Descrição'].apply(lambda desc: categorizar_despesa(desc, st.session_state.categories))
    despesas_df['AnoMes'] = despesas_df['Data'].dt.to_period('M').astype(str)
    
    st.session_state.processed_data = despesas_df

# --- 5. TÍTULO E DESCRIÇÃO ---
st.title("👨‍👩‍👧‍👦 Dashboard Financeiro Familiar")
st.write("Faça o upload do extrato mensal da família para análise e planeje seus gastos.")

# --- 6. BARRA LATERAL ---
st.session_state.theme = st.sidebar.selectbox(
    "🎨 Tema do Aplicativo",
    ["Claro (Padrão)", "Escuro", "Nubank"]
)

# ... (o restante do código CSS permanece o mesmo)
green_button_css = """
<style>
div.stButton > button[kind="secondary"] {
    background-color: #4CAF50;
    color: white;
    border: 1px solid #4CAF50;
}
div.stButton > button[kind="secondary"]:hover {
    background-color: #45a049;
    color: white;
    border-color: #45a049;
}
div.stButton > button[kind="secondary"]:active {
    background-color: #3e8e41;
    color: white;
    border-color: #3e8e41;
}
div.stButton > button[kind="secondary"]:focus:not(:active) {
    border-color: #4CAF50;
    color: white;
}
</style>
"""

nubank_theme_css = """
<style>
.stApp { background-color: #6A00A8; color: #FFFFFF !important; }
[data-testid="stSidebar"] { background-color: #4B0076; }
h1, h2, h3, h4, h5, h6, p, label, .st-emotion-cache-16txtl3 { color: #FFFFFF !important; }
[data-testid="stHeader"] { background-color: transparent; }
</style>
"""
dark_theme_css = """
<style>
.stApp { background-color: #0E1117; color: #FAFAFA !important; }
h1, h2, h3, h4, h5, h6, .st-emotion-cache-16txtl3 { color: #FAFAFA !important; }
[data-testid="stHeader"] { background-color: transparent; }
[data-testid="stSidebar"] { background-color: #1E1E1E; }
p, label, .st-emotion-cache-1y4p88q { color: #FAFAFA !important; }
.st-emotion-cache-ue6h4q, .st-emotion-cache-ltfnpr, [data-testid="stTextInput"] input { color: #FFFFFF !important; }
.st-emotion-cache-7ym5gk, .st-emotion-cache-1r6slb0 { background-color: #262730; }
[data-testid="stForm"] [data-testid="stButton"] button, [data-testid="stSidebar"] [data-testid="stButton"] button {
    background-color: #31333F; color: #FAFAFA; border: 1px solid #31333F;
}
[data-testid="stForm"] [data-testid="stButton"] button:hover, [data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    background-color: #404251; border-color: #404251;
}
</style>
"""

if st.session_state.theme == "Nubank":
    st.markdown(nubank_theme_css, unsafe_allow_html=True)
elif st.session_state.theme == "Escuro":
    st.markdown(dark_theme_css, unsafe_allow_html=True)


st.sidebar.header("Área de Controles")
uploaded_file = st.sidebar.file_uploader("Carregue seu extrato (CSV/XLSX)", type=["csv", "xlsx"])

with st.sidebar.expander("🔧 Gerenciar Categorias", expanded=False):
    st.write("Adicione, remova ou edite suas categorias e palavras-chave.")
    with st.form("form_nova_categoria", clear_on_submit=True):
        nova_categoria = st.text_input("Nome da Nova Categoria",placeholder="Ex: Saúde")
        palavras_chave_str = st.text_input("Palavras-chave (separadas por vírgula)",placeholder="Ex: farmácia,remédio,medico")
        add_cat_submit = st.form_submit_button("Adicionar Categoria")
        if add_cat_submit and nova_categoria and palavras_chave_str:
            palavras_chave = [normalizar_texto(p.strip()) for p in palavras_chave_str.split(',')]
            st.session_state.categories[nova_categoria] = palavras_chave
            save_json(CATEGORIES_FILE, st.session_state.categories)
            st.success(f"Categoria '{nova_categoria}' adicionada!")
            st.rerun()
    st.write("---")
    st.write("**Categorias Atuais:**")
    for categoria in list(st.session_state.categories.keys()):
        if categoria == "Outros": continue
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{categoria}**")
            keywords_str = ", ".join(st.session_state.categories[categoria])
            new_keywords_str = st.text_input("Palavras-chave", value=keywords_str, key=f"kw_{categoria}")
            st.session_state.categories[categoria] = [normalizar_texto(p.strip()) for p in new_keywords_str.split(",")]
        with col2:
            if st.button("Remover", key=f"del_{categoria}"):
                del st.session_state.categories[categoria]
                save_json(CATEGORIES_FILE, st.session_state.categories)
                st.rerun()
    if st.button("Salvar Alterações nas Palavras-chave"):
        save_json(CATEGORIES_FILE, st.session_state.categories)
        st.success("Alterações salvas com sucesso!")
        st.rerun()

st.sidebar.subheader("Adicionar Despesa Manual")
with st.sidebar.form("form_despesa_manual", clear_on_submit=True):
    desc_manual = st.text_input("Descrição da Despesa",placeholder="Ex: Jantar no restaurante")
    valor_manual_str = st.text_input("Valor da Despesa",placeholder="Ex: 25,50")
    submitted = st.form_submit_button("Adicionar")
    if submitted and desc_manual and valor_manual_str:
        try:
            valor_manual = float(valor_manual_str.replace(",", "."))
            # ALTERADO: A lógica agora chama a função de processamento
            st.session_state.despesas_manuais.append({"Data": datetime.now(), "Descrição": desc_manual, "Valor": -valor_manual})
            processar_dados() # Chama a função para reprocessar tudo
            st.sidebar.success("Despesa adicionada!")
            st.rerun() # Roda o app de novo para atualizar a tela
        except ValueError:
            st.sidebar.error("Valor inválido. Por favor, insira apenas números.")

# --- 7. PROCESSAMENTO DOS DADOS ---
# ALTERADO: A lógica de processamento foi movida para a função `processar_dados`
# e é chamada aqui apenas quando um novo arquivo é carregado.
if uploaded_file is not None:
    # Verifica se o arquivo é diferente do último carregado para não reprocessar sem necessidade
    if st.session_state.get('last_uploaded_file') != uploaded_file.name:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_extrato = pd.read_csv(uploaded_file, sep=',', engine='python', encoding='utf-8')
            else:
                df_extrato = pd.read_excel(uploaded_file)
            
            ensure_required_cols(df_extrato)
            st.session_state.df_from_upload = df_extrato # Armazena o DF bruto
            st.session_state.last_uploaded_file = uploaded_file.name
            processar_dados() # Chama a função para processar os dados
            st.rerun() # Garante que a interface seja atualizada com os novos dados
            
        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
            st.session_state.df_from_upload = None
            st.session_state.processed_data = None
            st.session_state.last_uploaded_file = None

# --- 8. ABAS ---
tab_options = ["📊 Visão Geral Mensal", "🏷️ Análise por Categoria", "📋 Extrato Detalhado", "🔁 Despesas Recorrentes", "🔮 Orçamento e Planejamento", "⚙️ Configurações"]
st.radio("Navegação", options=tab_options, key="active_tab", horizontal=True, label_visibility="collapsed")


# --- 9. CONTEÚDO DAS ABAS ---
# ALTERADO: A condição agora verifica se 'processed_data' não é nulo E não está vazio.
# Isso garante que o dashboard apareça mesmo que haja apenas despesas manuais.
if st.session_state.active_tab == "⚙️ Configurações":
    # ... (código da aba Configurações permanece o mesmo)
    st.header("⚙️ Configurações de Aparência")
    st.subheader("Estilo dos Gráficos")
    st.session_state.chart_theme = st.selectbox(
        "Selecione o tema para os gráficos",
        options=["streamlit", "plotly_white", "plotly_dark", "ggplot2", "seaborn"],
        index=["streamlit", "plotly_white", "plotly_dark", "ggplot2", "seaborn"].index(st.session_state.chart_theme)
    )
    st.subheader("Fontes dos Gráficos")
    st.session_state.chart_font = st.selectbox(
        "Selecione a fonte para os gráficos",
        options=["Arial", "Verdana", "Georgia", "Times New Roman", "Courier New"],
        index=["Arial", "Verdana", "Georgia", "Times New Roman", "Courier New"].index(st.session_state.chart_font)
    )
    st.session_state.chart_title_size = st.slider(
        "Tamanho da fonte do título", min_value=12, max_value=30, value=st.session_state.chart_title_size
    )
    st.session_state.chart_tick_size = st.slider(
        "Tamanho da fonte dos eixos (X e Y)", min_value=8, max_value=20, value=st.session_state.chart_tick_size
    )
    st.session_state.chart_insidetext_size = st.slider(
        "Tamanho da fonte do texto interno (barras/pizza)", min_value=8, max_value=20, value=st.session_state.chart_insidetext_size
    )
    st.session_state.chart_legend_size = st.slider(
        "Tamanho da fonte da legenda", min_value=8, max_value=20, value=st.session_state.chart_legend_size
    )
    st.write("---")
    if st.button("Restaurar Padrões Visuais"):
        for key, value in default_configs.items():
            if key != 'theme':
                st.session_state[key] = value
        st.success("Configurações visuais restauradas para o padrão!")
        st.rerun()

elif st.session_state.active_tab == "🔁 Despesas Recorrentes":
    # ... (código da aba Despesas Recorrentes permanece o mesmo)
    st.header("🔁 Despesas Recorrentes")
    st.write("Cadastre aqui suas assinaturas e despesas que se repetem todos os meses. Elas serão usadas no planejamento do orçamento.")

    st.session_state.despesas_recorrentes = st.data_editor(
        st.session_state.despesas_recorrentes,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Descrição": st.column_config.TextColumn("Descrição da Despesa", required=True),
            "Valor": st.column_config.NumberColumn("Valor Mensal (R$)", required=True, min_value=0, format="R$ %.2f"),
            "Categoria": st.column_config.SelectboxColumn("Categoria", options=sorted(st.session_state.categories.keys()), required=True)
        }
    )
    total_recorrente = st.session_state.despesas_recorrentes['Valor'].sum()
    st.metric("Total de Despesas Recorrentes Mensais", f"R$ {total_recorrente:,.2f}")

elif st.session_state.active_tab == "🔮 Orçamento e Planejamento":
    # ... (código da aba Orçamento e Planejamento, com uma pequena correção de segurança)
    st.header("🔮 Orçamento e Planejamento Mensal")

    with st.expander("Defina o Orçamento Mensal por Categoria", expanded=True):
        st.markdown(green_button_css, unsafe_allow_html=True)
        for categoria in st.session_state.categories.keys():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text_input(placeholder="Digite o valor",
                    label=f"Orçamento para **{categoria}** (R$)",
                    value="" if st.session_state.orcamento_mensal.get(categoria, 0.0) == 0.0 else f"{st.session_state.orcamento_mensal.get(categoria, 0.0):.2f}".replace('.', ','),
                    key=f"orc_input_{categoria}",
                )
            with col2:
                st.write("") 
                st.write("")
                if st.button("Salvar", key=f"orc_btn_{categoria}", use_container_width=True):
                    valor_str = st.session_state[f"orc_input_{categoria}"]
                    try:
                        new_value = float(valor_str.replace(",", "."))
                        st.session_state.orcamento_mensal[categoria] = new_value
                        st.toast(f"Orçamento para '{categoria}' salvo!", icon="✅")
                        st.rerun()
                    except ValueError:
                        st.toast(f"Valor inválido para '{categoria}'. Use apenas números.", icon="❌")
        
        st.write("---")
        total_orcado = sum(st.session_state.orcamento_mensal.values())
        st.metric("Total Orçado para Despesas", f"R$ {total_orcado:,.2f}")

    st.write("---")
    
    # Adicionada verificação para evitar erro se processed_data for None
    if st.session_state.get('processed_data') is not None and not st.session_state.processed_data.empty:
        st.subheader("Análise do Orçamento vs. Gastos Reais")
        df_analise = st.session_state.processed_data
        meses_disponiveis = sorted(df_analise['AnoMes'].unique(), reverse=True)
        if meses_disponiveis:
            mes_analise = st.selectbox("Selecione o mês para comparar com o orçamento:", options=meses_disponiveis)
            gastos_mes = df_analise[df_analise['AnoMes'] == mes_analise]
            gastos_reais_cat = gastos_mes.groupby('Categoria')['Gastos'].sum()

            df_orcamento = pd.DataFrame(list(st.session_state.orcamento_mensal.items()), columns=['Categoria', 'Orçado'])
            df_orcamento = df_orcamento[df_orcamento['Orçado'] > 0]
            df_orcamento['Gasto'] = df_orcamento['Categoria'].map(gastos_reais_cat).fillna(0)
            df_orcamento['Saldo'] = df_orcamento['Orçado'] - df_orcamento['Gasto']
            
            st.dataframe(df_orcamento.style.format({'Orçado': 'R$ {:,.2f}', 'Gasto': 'R$ {:,.2f}', 'Saldo': 'R$ {:,.2f}'}), use_container_width=True)

            fig_orcamento = px.bar(
                df_orcamento, x='Categoria', y=['Orçado', 'Gasto'],
                title=f'Orçado vs. Gasto Real em {mes_analise}',
                barmode='group', template=st.session_state.chart_theme,
                labels={'value': 'Valor (R$)', 'variable': 'Tipo'}
            )
            font_color = "black" if st.session_state.theme == "Claro (Padrão)" else "white"
            fig_orcamento.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=font_color)
            st.plotly_chart(fig_orcamento, use_container_width=True)
        else:
            st.info("Nenhum mês para análise. Carregue um extrato ou adicione despesas.")

    st.write("---")

    st.subheader("Planejamento de Rendas e Despesas")
    st.markdown(green_button_css, unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Entradas Previstas**")
        
        sub_col1, sub_col2 = st.columns([3, 1])
        with sub_col1:
            renda_fixa_valor_atual = st.session_state.previsao_renda_fixa
            st.text_input(
                "Salários / Rendas Fixas (R$)",
                value="" if renda_fixa_valor_atual == 0.0 else f"{renda_fixa_valor_atual:.2f}".replace('.', ','),
                key="renda_fixa_input",
                placeholder="Digite o valor"
            )
        with sub_col2:
            st.write("")
            if st.button("Salvar", key="renda_fixa_btn", use_container_width=True):
                valor_str = st.session_state.renda_fixa_input
                if not valor_str:
                    st.session_state.previsao_renda_fixa = 0.0
                    st.toast("Renda fixa salva como R$ 0,00.", icon="✅")
                    st.rerun()
                else:
                    try:
                        new_value = float(valor_str.replace(",", "."))
                        st.session_state.previsao_renda_fixa = new_value
                        st.toast("Renda fixa salva!", icon="✅")
                        st.rerun()
                    except ValueError:
                        st.toast("Valor inválido para renda fixa.", icon="❌")

        sub_col3, sub_col4 = st.columns([3, 1])
        with sub_col3:
            renda_variavel_valor_atual = st.session_state.previsao_renda_variavel
            st.text_input(
                "Outras Rendas / Renda Variável (R$)",
                value="" if renda_variavel_valor_atual == 0.0 else f"{renda_variavel_valor_atual:.2f}".replace('.', ','),
                key="renda_variavel_input",
                placeholder="Digite o valor"
            )
        with sub_col4:
            st.write("")
            if st.button("Salvar", key="renda_variavel_btn", use_container_width=True):
                valor_str = st.session_state.renda_variavel_input
                if not valor_str:
                    st.session_state.previsao_renda_variavel = 0.0
                    st.toast("Renda variável salva como R$ 0,00.", icon="✅")
                    st.rerun()
                else:
                    try:
                        new_value = float(valor_str.replace(",", "."))
                        st.session_state.previsao_renda_variavel = new_value
                        st.toast("Renda variável salva!", icon="✅")
                        st.rerun()
                    except ValueError:
                        st.toast("Valor inválido para renda variável.", icon="❌")

    with col2:
        st.write("**Outras Despesas Fixas (Não Recorrentes)**")
        st.session_state.previsao_despesas_fixas = st.data_editor(
            st.session_state.previsao_despesas_fixas, num_rows="dynamic", use_container_width=True,
            column_config={
                "Descrição": st.column_config.TextColumn("Descrição", required=True),
                "Valor": st.column_config.NumberColumn("Valor (R$)", required=True, min_value=0, format="R$ %.2f")
            }
        )
    
    st.subheader("Resultado do Planejamento")
    total_entradas = st.session_state.previsao_renda_fixa + st.session_state.previsao_renda_variavel
    total_despesas_recorrentes = st.session_state.despesas_recorrentes['Valor'].sum()
    total_despesas_fixas = st.session_state.previsao_despesas_fixas['Valor'].sum()
    total_despesas_planejadas = total_despesas_recorrentes + total_despesas_fixas
    saldo_previsto = total_entradas - total_despesas_planejadas
    
    colA, colB, colC, colD = st.columns(4)
    colA.metric("Total de Entradas", f"R$ {total_entradas:,.2f}")
    colB.metric("Despesas Recorrentes", f"R$ {total_despesas_recorrentes:,.2f}")
    colC.metric("Outras Despesas Fixas", f"R$ {total_despesas_fixas:,.2f}")
    colD.metric("SALDO PREVISTO", f"R$ {saldo_previsto:,.2f}")

    if saldo_previsto < 0:
        st.error(f"Atenção: Suas despesas planejadas (R$ {total_despesas_planejadas:,.2f}) são maiores que suas entradas.")
    else:
        st.success(f"Com base no planejamento, você terá R$ {saldo_previsto:,.2f} disponíveis para as despesas variáveis (dentro do orçamento).")

elif st.session_state.get('processed_data') is not None and not st.session_state.processed_data.empty:
    despesas_df = st.session_state.processed_data
    
    # ... (o restante do código das abas principais permanece o mesmo, com uma pequena correção de bug na linha 621)
    st.sidebar.subheader("Inserir Renda do Mês Analisado")
    with st.sidebar.form("form_rendas"):
        meses_unicos = sorted(despesas_df['AnoMes'].unique())
        rendas_inputs = {}
        for mes in meses_unicos:
            valor_atual = st.session_state.rendas_mensais.get(mes, "0.00")
            rendas_inputs[mes] = st.text_input(f"Renda para {mes}", value=str(valor_atual), key=f"renda_{mes}")
        submitted_rendas = st.form_submit_button("Salvar Renda")
        if submitted_rendas:
            try:
                for mes, valor_str in rendas_inputs.items():
                    st.session_state.rendas_mensais[mes] = float(valor_str.replace(",", "."))
                st.sidebar.success("Renda salva com sucesso!")
            except ValueError:
                st.sidebar.error("Valor inválido. Use apenas números.")
    
    gastos_mensais = despesas_df.groupby('AnoMes')['Gastos'].sum().reset_index()
    df_rendas = pd.DataFrame(list(st.session_state.rendas_mensais.items()), columns=['AnoMes', 'Receitas'])
    dados_mensais = pd.merge(gastos_mensais, df_rendas, on='AnoMes', how='outer').fillna(0)
    dados_mensais['Saldo'] = dados_mensais['Receitas'] - dados_mensais['Gastos']
    dados_mensais = dados_mensais.sort_values("AnoMes")

    font_color = "black" if st.session_state.theme == "Claro (Padrão)" else "white"

    if st.session_state.active_tab == "📊 Visão Geral Mensal":
        st.header("Resumo Financeiro Mensal")
        total_receitas = dados_mensais['Receitas'].sum()
        total_gastos = dados_mensais['Gastos'].sum()
        saldo_total = total_receitas - total_gastos
        col1, col2, col3 = st.columns(3)
        col1.metric("Receita Total do Período", f"R$ {total_receitas:,.2f}")
        col2.metric("Despesa Total do Período", f"R$ {total_gastos:,.2f}")
        col3.metric("Saldo Final do Período", f"R$ {saldo_total:,.2f}")
        
        fig_mensal = px.bar(dados_mensais, x='AnoMes', y=['Receitas', 'Gastos', 'Saldo'], title='Receitas, Despesas e Saldo por Mês', barmode='group', template=st.session_state.chart_theme)
        fig_mensal.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=font_color,
            font_family=st.session_state.chart_font, title_font_size=st.session_state.chart_title_size,
            xaxis=dict(tickfont=dict(size=st.session_state.chart_tick_size)),
            yaxis=dict(tickfont=dict(size=st.session_state.chart_tick_size)), # Correção de bug: _state para st.session_state
            legend=dict(font=dict(size=st.session_state.chart_legend_size))
        )
        st.plotly_chart(fig_mensal, use_container_width=True)

    elif st.session_state.active_tab == "🏷️ Análise por Categoria":
        st.header("Análise Detalhada por Categoria")
        tipo_grafico = st.selectbox("Escolha o tipo de análise:", ["Visão Geral por Categoria", "Distribuição Mensal"])
        if tipo_grafico == "Visão Geral por Categoria":
            st.subheader("Total Gasto por Categoria (Todo o Período)")
            gastos_por_categoria_total = despesas_df.groupby('Categoria')['Gastos'].sum().sort_values(ascending=False).reset_index()
            fig_total_categorias = px.bar(
                gastos_por_categoria_total, x='Gastos', y='Categoria', orientation='h',
                title='Total Gasto por Categoria', text_auto='.2s', color='Categoria',
                color_discrete_sequence=px.colors.qualitative.Vivid, template=st.session_state.chart_theme
            )
            fig_total_categorias.update_traces(textfont_size=st.session_state.chart_insidetext_size)
            fig_total_categorias.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=font_color,
                showlegend=False, font_family=st.session_state.chart_font, title_font_size=st.session_state.chart_title_size,
                xaxis=dict(tickfont=dict(size=st.session_state.chart_tick_size)),
                yaxis={'categoryorder':'total ascending', 'tickfont': {'size': st.session_state.chart_tick_size}}
            )
            st.plotly_chart(fig_total_categorias, use_container_width=True)
        elif tipo_grafico == "Distribuição Mensal":
            st.subheader("Distribuição de Gastos por Mês")
            meses_unicos = sorted(despesas_df['AnoMes'].unique())
            mes_sel = st.selectbox('Selecione um Mês para Análise', options=meses_unicos, key="mes_categoria")
            gastos_categoria_mes = despesas_df[despesas_df['AnoMes'] == mes_sel].groupby('Categoria')['Gastos'].sum().reset_index()
            if not gastos_categoria_mes.empty:
                fig_categorias_mes = px.pie(
                    gastos_categoria_mes, names='Categoria', values='Gastos',
                    title=f'Distribuição de Gastos em {mes_sel}', hole=0.4,
                    template=st.session_state.chart_theme
                )
                fig_categorias_mes.update_traces(textfont_size=st.session_state.chart_insidetext_size)
                fig_categorias_mes.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=font_color,
                    font_family=st.session_state.chart_font, title_font_size=st.session_state.chart_title_size,
                    legend=dict(font=dict(size=st.session_state.chart_legend_size))
                )
                st.plotly_chart(fig_categorias_mes, use_container_width=True)
            else:
                st.warning(f"Não há dados de despesas para {mes_sel}.")

    elif st.session_state.active_tab == "📋 Extrato Detalhado":
        st.header("Extrato Detalhado e Edição")
        with st.expander("ℹ️ Como usar os filtros e a tabela interativa"):
            st.markdown("""
            - **Filtros e Pesquisa:** Utilize os campos para filtrar as transações.
            - **Ordenar:** Escolha uma coluna e a ordem para organizar os dados.
            - **Editar Categoria:** Clique duas vezes na célula "Categoria".
            - **Deletar Transações:** Marque a caixa na coluna "Deletar".
            - **Salvar:** Clique no botão **"✅ Aplicar Alterações"** para salvar.
            """)
        
        termo_pesquisa = st.text_input("Pesquisar por Descrição")
        min_data = despesas_df['Data'].min().date()
        max_data = despesas_df['Data'].max().date()
        col_data1, col_data2 = st.columns(2)
        data_inicio = col_data1.date_input("Data de Início", min_data, key="data_inicio")
        data_fim = col_data2.date_input("Data de Fim", max_data, key="data_fim")
        categorias_disponiveis = sorted(despesas_df['Categoria'].unique())
        categorias_selecionadas = st.multiselect("Filtrar por Categoria(s)", options=categorias_disponiveis)
        min_gasto = float(despesas_df['Gastos'].min()) if not despesas_df.empty else 0.0
        max_gasto = float(despesas_df['Gastos'].max()) if not despesas_df.empty else 1.0
        intervalo_gasto = st.slider("Filtrar por Valor do Gasto (R$)", min_value=min_gasto, max_value=max_gasto, value=(min_gasto, max_gasto))

        df_filtrado = despesas_df.copy()
        df_filtrado['Data_Filtro'] = df_filtrado['Data'].dt.date
        df_filtrado = df_filtrado[(df_filtrado['Data_Filtro'] >= data_inicio) & (df_filtrado['Data_Filtro'] <= data_fim) & (df_filtrado['Gastos'] >= intervalo_gasto[0]) & (df_filtrado['Gastos'] <= intervalo_gasto[1])]
        if categorias_selecionadas: df_filtrado = df_filtrado[df_filtrado['Categoria'].isin(categorias_selecionadas)]
        if termo_pesquisa: df_filtrado = df_filtrado[df_filtrado['Descrição'].str.contains(termo_pesquisa, case=False, na=False)]

        st.write("---")
        col_sort1, col_sort2 = st.columns(2)
        sort_column = col_sort1.selectbox("Ordenar por", options=df_filtrado.columns.tolist(), index=df_filtrado.columns.tolist().index('Data'))
        sort_order = col_sort2.selectbox("Ordem", options=["Decrescente", "Crescente"])
        df_filtrado = df_filtrado.sort_values(by=sort_column, ascending=(sort_order == "Crescente"))
        
        st.write(f"**Exibindo {len(df_filtrado)} transações.**")
        
        df_editavel = df_filtrado.copy()
        df_editavel["Deletar"] = False
        colunas_editor = {
            "Deletar": st.column_config.CheckboxColumn("Deletar?", default=False),
            "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
            "Descrição": st.column_config.TextColumn("Descrição"),
            "Categoria": st.column_config.SelectboxColumn("Categoria", options=sorted(st.session_state.categories.keys()), required=True),
            "Gastos": st.column_config.NumberColumn("Gasto (R$)", format="R$ %.2f")
        }
        df_editado = st.data_editor(df_editavel, column_config=colunas_editor, use_container_width=True, hide_index=True, key="data_editor")
        
        if st.button("✅ Aplicar Alterações e Exclusões", type="primary"):
            indices_para_deletar = df_editado[df_editado["Deletar"] == True].index
            df_principal = st.session_state.processed_data
            df_principal.drop(indices_para_deletar, inplace=True, errors='ignore')
            df_sem_deletados = df_editado[df_editado["Deletar"] == False]
            df_principal.update(df_sem_deletados)
            st.session_state.processed_data = df_principal
            st.success("Alterações aplicadas com sucesso!")
            st.rerun()

else:
    st.info("⬅️ Por favor, carregue o extrato da família na barra lateral ou adicione uma despesa manual para iniciar a análise.")