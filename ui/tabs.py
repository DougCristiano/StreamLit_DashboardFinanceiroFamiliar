import streamlit as st
import pandas as pd
import plotly.express as px

# --- Funções para renderizar cada aba ---

def render_visao_geral():
    despesas_df = st.session_state.processed_data
    gastos_mensais = despesas_df.groupby('AnoMes')['Gastos'].sum().reset_index()
    df_rendas = pd.DataFrame(list(st.session_state.rendas_mensais.items()), columns=['AnoMes', 'Receitas'])
    dados_mensais = pd.merge(gastos_mensais, df_rendas, on='AnoMes', how='outer').fillna(0)
    dados_mensais['Saldo'] = dados_mensais['Receitas'] - dados_mensais['Gastos']
    dados_mensais = dados_mensais.sort_values("AnoMes")

    font_color = "black" if st.session_state.theme == "Claro (Padrão)" else "white"

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
        yaxis=dict(tickfont=dict(size=st.session_state.chart_tick_size)),
        legend=dict(font=dict(size=st.session_state.chart_legend_size))
    )
    st.plotly_chart(fig_mensal, use_container_width=True)


def render_analise_categoria():
    despesas_df = st.session_state.processed_data
    font_color = "black" if st.session_state.theme == "Claro (Padrão)" else "white"
    
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


def render_extrato_detalhado():
    despesas_df = st.session_state.processed_data
    
    st.header("Extrato Detalhado e Edição")
    with st.expander("ℹ️ Como usar os filtros e a tabela interativa"):
        st.markdown("""
        - **Filtros e Pesquisa:** Utilize os campos para filtrar as transações.
        - **Ordenar:** Escolha uma coluna e a ordem para organizar os dados.
        - **Editar Categoria:** Clique duas vezes na célula "Categoria".
        - **Deletar Transações:** Marque a caixa na coluna "Deletar".
        - **Salvar:** Clique no botão **"✅ Aplicar Alterações"** para salvar.
        """)
    
    # Filtros
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
    if max_gasto < min_gasto or max_gasto == min_gasto:
        max_gasto = 99999.99
    if min_gasto < 0:
        min_gasto = 0.0
    intervalo_gasto = st.slider("Filtrar por Valor do Gasto (R$)", min_value=min_gasto, max_value=max_gasto, value=(min_gasto, max_gasto))

    # Aplicação dos filtros
    df_filtrado = despesas_df.copy()
    df_filtrado['Data_Filtro'] = df_filtrado['Data'].dt.date
    df_filtrado = df_filtrado[(df_filtrado['Data_Filtro'] >= data_inicio) & (df_filtrado['Data_Filtro'] <= data_fim) & (df_filtrado['Gastos'] >= intervalo_gasto[0]) & (df_filtrado['Gastos'] <= intervalo_gasto[1])]
    if categorias_selecionadas: df_filtrado = df_filtrado[df_filtrado['Categoria'].isin(categorias_selecionadas)]
    if termo_pesquisa: df_filtrado = df_filtrado[df_filtrado['Descrição'].str.contains(termo_pesquisa, case=False, na=False)]

    # Ordenação
    st.write("---")
    col_sort1, col_sort2 = st.columns(2)
    sort_column = col_sort1.selectbox("Ordenar por", options=df_filtrado.columns.tolist(), index=df_filtrado.columns.tolist().index('Data'))
    sort_order = col_sort2.selectbox("Ordem", options=["Decrescente", "Crescente"])
    df_filtrado = df_filtrado.sort_values(by=sort_column, ascending=(sort_order == "Crescente"))
    
    st.write(f"**Exibindo {len(df_filtrado)} transações.**")
    
    # Editor de dados
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

def render_despesas_recorrentes():
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

def render_orcamento_planejamento():
    st.header("🔮 Orçamento e Planejamento Mensal")

    with st.expander("Defina o Orçamento Mensal por Categoria", expanded=True):
        for categoria in st.session_state.categories.keys():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text_input(
                    label=f"Orçamento para **{categoria}** (R$)",
                    value="" if st.session_state.orcamento_mensal.get(categoria, 0.0) == 0.0 else f"{st.session_state.orcamento_mensal.get(categoria, 0.0):.2f}".replace('.', ','),
                    key=f"orc_input_{categoria}"
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
                    except (ValueError, TypeError):
                        st.toast(f"Valor inválido para '{categoria}'. Use apenas números.", icon="❌")
        
        st.write("---")
        total_orcado = sum(st.session_state.orcamento_mensal.values())
        st.metric("Total Orçado para Despesas", f"R$ {total_orcado:,.2f}")
    
    st.write("---")
    
    # Análise Orçamento vs. Real
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

            fig_orcamento = px.bar(df_orcamento, x='Categoria', y=['Orçado', 'Gasto'], title=f'Orçado vs. Gasto Real em {mes_analise}', barmode='group', template=st.session_state.chart_theme)
            font_color = "black" if st.session_state.theme == "Claro (Padrão)" else "white"
            fig_orcamento.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=font_color)
            st.plotly_chart(fig_orcamento, use_container_width=True)
            
    st.write("---")

    # Planejamento Futuro
    st.subheader("Planejamento de Rendas e Despesas")
    col1, col2 = st.columns(2)
    # ... (O restante da lógica de planejamento continua aqui, igual ao original)
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
                try:
                    new_value = float(valor_str.replace(",", ".")) if valor_str else 0.0
                    st.session_state.previsao_renda_fixa = new_value
                    st.toast("Renda fixa salva!", icon="✅")
                except (ValueError, TypeError):
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
                try:
                    new_value = float(valor_str.replace(",", ".")) if valor_str else 0.0
                    st.session_state.previsao_renda_variavel = new_value
                    st.toast("Renda variável salva!", icon="✅")
                except (ValueError, TypeError):
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
        
def render_configuracoes():
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
    st.session_state.chart_title_size = st.slider( "Tamanho da fonte do título", 12, 30, st.session_state.chart_title_size)
    st.session_state.chart_tick_size = st.slider("Tamanho da fonte dos eixos (X e Y)", 8, 20, st.session_state.chart_tick_size)
    st.session_state.chart_insidetext_size = st.slider("Tamanho da fonte do texto interno (barras/pizza)", 8, 20, st.session_state.chart_insidetext_size)
    st.session_state.chart_legend_size = st.slider("Tamanho da fonte da legenda", 8, 20, st.session_state.chart_legend_size)
    
    st.write("---")
    if st.button("Restaurar Padrões Visuais"):
        default_configs = {
            'chart_font': "Arial", 'chart_title_size': 22,
            'chart_tick_size': 14, 'chart_insidetext_size': 12, 'chart_legend_size': 14,
            'chart_theme': "streamlit"
        }
        for key, value in default_configs.items():
            st.session_state[key] = value
        st.success("Configurações visuais restauradas para o padrão!")
        st.rerun()