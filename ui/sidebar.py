import streamlit as st
import pandas as pd
from datetime import datetime
from utils.helpers import normalizar_texto, save_json, CATEGORIES_FILE
from utils.processing import processar_dados

def render_sidebar():
    """Renderiza a barra lateral completa do aplicativo, incluindo o mapeamento de colunas."""
    
    st.sidebar.selectbox("🎨 Tema do Aplicativo", ["Claro (Padrão)", "Escuro", "Nubank"], key='theme')
    
    st.sidebar.header("Área de Controles")
    
    # --- ETAPA 1: Upload de arquivo ---
    uploaded_file = st.sidebar.file_uploader("Carregue seu extrato (CSV/XLSX)", type=["csv", "xlsx"])

    if uploaded_file is not None:
        # Se um novo arquivo for carregado, armazena-o no state "raw_df" e reinicia o processo
        if st.session_state.get('last_uploaded_file') != uploaded_file.name:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file, sep=',', engine='python', encoding='utf-8')
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.session_state.raw_df = df
                st.session_state.last_uploaded_file = uploaded_file.name
                # Limpa dados antigos para forçar novo mapeamento
                st.session_state.processed_data = None
                st.session_state.df_from_upload = None
                st.rerun()

            except Exception as e:
                st.error(f"Ocorreu um erro ao ler o arquivo: {e}")
                st.session_state.raw_df = None

    # --- ETAPA 2: Mapeamento de Colunas (só aparece se um arquivo foi carregado) ---
    if st.session_state.raw_df is not None:
        st.sidebar.subheader("🔗 Mapeamento das Colunas")
        st.sidebar.info("Selecione as colunas do seu arquivo que correspondem aos campos necessários.")
        
        columns = st.session_state.raw_df.columns.tolist()
        
        # Caixas de seleção para o usuário mapear as colunas
        date_col = st.sidebar.selectbox("Coluna da Data da Transação", options=columns, index=None, placeholder="Selecione a coluna...")
        title_col = st.sidebar.selectbox("Coluna da Descrição (Histórico)", options=columns, index=None, placeholder="Selecione a coluna...")
        amount_col = st.sidebar.selectbox("Coluna do Valor (Montante)", options=columns, index=None, placeholder="Selecione a coluna...")

        if st.sidebar.button("Processar Extrato", type="primary", use_container_width=True):
            if date_col and title_col and amount_col:
                # Cria um novo DataFrame apenas com as colunas mapeadas e com os nomes corretos
                st.session_state.column_map = {'date': date_col, 'title': title_col, 'amount': amount_col}
                
                # Pega as colunas selecionadas do DataFrame original
                df_mapped = st.session_state.raw_df[[date_col, title_col, amount_col]].copy()
                # Renomeia para os nomes padrão que o app espera
                df_mapped.columns = ['date', 'title', 'amount']
                
                # Armazena o DataFrame mapeado para ser processado
                st.session_state.df_from_upload = df_mapped
                
                # Chama a função de processamento que já existe
                processar_dados()
                
                # Limpa o DataFrame "cru" para esconder o menu de mapeamento
                st.session_state.raw_df = None 
                st.rerun()
            else:
                st.sidebar.error("Por favor, mapeie todas as três colunas para continuar.")

    # --- Gerenciador de categorias e Despesas Manuais (continuam como antes) ---
    with st.sidebar.expander("🔧 Gerenciar Categorias", expanded=False):
        # ... (código original sem alterações)
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