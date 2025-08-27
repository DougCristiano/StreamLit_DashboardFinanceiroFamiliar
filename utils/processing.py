import streamlit as st
import pandas as pd
from utils.helpers import categorizar_despesa

def processar_dados():
    """
    Combina dados do arquivo carregado e despesas manuais,
    processa-os e armazena em st.session_state.processed_data.
    """
    dfs_to_combine = []

    if st.session_state.df_from_upload is not None:
        df_extrato = st.session_state.df_from_upload.copy()
        df_extrato.rename(columns={'date': 'Data', 'title': 'Descrição', 'amount': 'Valor'}, inplace=True)
        df_extrato = df_extrato[~df_extrato['Descrição'].str.contains("pagamento recebido", case=False, na=False)]
        dfs_to_combine.append(df_extrato)

    if st.session_state.despesas_manuais:
        df_manuais = pd.DataFrame(st.session_state.despesas_manuais)
        dfs_to_combine.append(df_manuais)

    if not dfs_to_combine:
        st.session_state.processed_data = None
        return

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