import streamlit as st
import pandas as pd
from datetime import datetime
from utils.helpers import normalizar_texto, save_json, ensure_required_cols, CATEGORIES_FILE
from utils.processing import processar_dados

def render_sidebar():
    """Renderiza a barra lateral completa do aplicativo."""
    
    st.sidebar.selectbox("🎨 Tema do Aplicativo", ["Claro (Padrão)", "Escuro", "Nubank"], key='theme')
    
    st.sidebar.header("Área de Controles")
    
    # Upload de arquivo
    uploaded_file = st.sidebar.file_uploader("Carregue seu extrato (CSV/XLSX)", type=["csv", "xlsx"])
    if uploaded_file is not None:
        if st.session_state.get('last_uploaded_file') != uploaded_file.name:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_extrato = pd.read_csv(uploaded_file, sep=',', engine='python', encoding='utf-8')
                else:
                    df_extrato = pd.read_excel(uploaded_file)
                
                ensure_required_cols(df_extrato)
                st.session_state.df_from_upload = df_extrato
                st.session_state.last_uploaded_file = uploaded_file.name
                processar_dados()
                st.rerun()
                
            except Exception as e:
                st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
                st.session_state.df_from_upload = None
                st.session_state.processed_data = None
                st.session_state.last_uploaded_file = None

    # Gerenciador de categorias
    with st.sidebar.expander("🔧 Gerenciar Categorias", expanded=False):
        # Formulário para nova categoria
        with st.form("form_nova_categoria", clear_on_submit=True):
            nova_categoria = st.text_input("Nome da Nova Categoria", placeholder="Ex: Saúde")
            palavras_chave_str = st.text_input("Palavras-chave (separadas por vírgula)", placeholder="Ex: farmácia,remédio,medico")
            if st.form_submit_button("Adicionar Categoria"):
                if nova_categoria and palavras_chave_str:
                    palavras_chave = [normalizar_texto(p.strip()) for p in palavras_chave_str.split(',')]
                    st.session_state.categories[nova_categoria] = palavras_chave
                    save_json(CATEGORIES_FILE, st.session_state.categories)
                    st.success(f"Categoria '{nova_categoria}' adicionada!")
                    st.rerun()
        
        # Edição de categorias existentes
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

    # Adicionar despesa manual
    st.sidebar.subheader("Adicionar Despesa Manual")
    with st.sidebar.form("form_despesa_manual", clear_on_submit=True):
        desc_manual = st.text_input("Descrição da Despesa", placeholder="Ex: Jantar no restaurante")
        valor_manual_str = st.text_input("Valor da Despesa", placeholder="Ex: 25,50")
        if st.form_submit_button("Adicionar"):
            if desc_manual and valor_manual_str:
                try:
                    valor_manual = float(valor_manual_str.replace(",", "."))
                    st.session_state.despesas_manuais.append({"Data": datetime.now(), "Descrição": desc_manual, "Valor": -valor_manual})
                    processar_dados()
                    st.sidebar.success("Despesa adicionada!")
                    st.rerun()
                except ValueError:
                    st.sidebar.error("Valor inválido. Por favor, insira apenas números.")
                    
    # Inserir renda mensal (só aparece se houver dados)
    if st.session_state.get('processed_data') is not None and not st.session_state.processed_data.empty:
        despesas_df = st.session_state.processed_data
        st.sidebar.subheader("Inserir Renda do Mês Analisado")
        with st.sidebar.form("form_rendas"):
            meses_unicos = sorted(despesas_df['AnoMes'].unique())
            rendas_inputs = {}
            for mes in meses_unicos:
                valor_atual = st.session_state.rendas_mensais.get(mes, "0.00")
                rendas_inputs[mes] = st.text_input(f"Renda para {mes}", value=str(valor_atual), key=f"renda_{mes}")
            if st.form_submit_button("Salvar Renda"):
                try:
                    for mes, valor_str in rendas_inputs.items():
                        st.session_state.rendas_mensais[mes] = float(valor_str.replace(",", "."))
                    st.sidebar.success("Renda salva com sucesso!")
                except ValueError:
                    st.sidebar.error("Valor inválido. Use apenas números.")