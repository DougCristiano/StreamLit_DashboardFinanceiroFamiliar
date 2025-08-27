import streamlit as st
import json
import os
import unicodedata
import pandas as pd
from pathlib import Path

# Constante para o arquivo de categorias
CATEGORIES_FILE = "categorias.json"

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
        
def load_css(file_path):
    """Carrega um arquivo CSS e o injeta no app Streamlit."""
    try:
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"Arquivo CSS não encontrado em: {file_path}")

def initialize_session_state():
    """Inicializa todas as variáveis necessárias no st.session_state."""
    
    # Categorias e dados
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
    if 'despesas_manuais' not in st.session_state:
        st.session_state.despesas_manuais = []
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'df_from_upload' not in st.session_state:
        st.session_state.df_from_upload = None
    
    # --- NOVO: States para o mapeamento de colunas ---
    if 'raw_df' not in st.session_state:
        st.session_state.raw_df = None # Guarda o DataFrame antes do mapeamento
    if 'column_map' not in st.session_state:
        st.session_state.column_map = {'date': None, 'title': None, 'amount': None}
        
    # Navegação
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "📊 Visão Geral Mensal"
        
    # Planejamento e Orçamento
    if 'rendas_mensais' not in st.session_state:
        st.session_state.rendas_mensais = {}
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

    # Configurações de aparência
    default_configs = {
        'theme': "Claro (Padrão)", 'chart_font': "Arial", 'chart_title_size': 22,
        'chart_tick_size': 14, 'chart_insidetext_size': 12, 'chart_legend_size': 14,
        'chart_theme': "streamlit"
    }
    for key, value in default_configs.items():
        if key not in st.session_state:
            st.session_state[key] = value
    """Inicializa todas as variáveis necessárias no st.session_state."""
    
    # Categorias e dados
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
    if 'despesas_manuais' not in st.session_state:
        st.session_state.despesas_manuais = []
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'df_from_upload' not in st.session_state:
        st.session_state.df_from_upload = None
        
    # Navegação
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "📊 Visão Geral Mensal"
        
    # Planejamento e Orçamento
    if 'rendas_mensais' not in st.session_state:
        st.session_state.rendas_mensais = {}
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

    # Configurações de aparência
    default_configs = {
        'theme': "Claro (Padrão)", 'chart_font': "Arial", 'chart_title_size': 22,
        'chart_tick_size': 14, 'chart_insidetext_size': 12, 'chart_legend_size': 14,
        'chart_theme': "streamlit"
    }
    for key, value in default_configs.items():
        if key not in st.session_state:
            st.session_state[key] = value