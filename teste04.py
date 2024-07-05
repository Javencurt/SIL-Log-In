import pandas as pd
import glob
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Configurar a página com layout wide
st.set_page_config(layout="wide")

# Caminho para os arquivos CSV
file_paths = glob.glob('C:\\Users\\jean.avencurt\\Desktop\\Py\\SIL Log-In\\*.csv')

# Lista para armazenar DataFrames
data_frames = []

# Ler cada arquivo CSV e adicioná-lo à lista de DataFrames
for file_path in file_paths:
    try:
        df = pd.read_csv(file_path, encoding='utf-8', delimiter=';')
        data_frames.append(df)
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='latin1', delimiter=';')
        data_frames.append(df)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo {file_path}: {e}")

# Verificar se algum DataFrame foi carregado
if not data_frames:
    st.error("Nenhum dado foi carregado dos arquivos CSV.")
else:
    # Concatenar todos os DataFrames em um único DataFrame
    data = pd.concat(data_frames, ignore_index=True)

# Sidebar para filtragem
st.sidebar.title('Dados')

# Seleção do tipo de filtragem
tipo_filtro = st.sidebar.radio("Filtrar por:", ('Ano', 'Mês'))

# Widget para seleção de ano ou mês
if tipo_filtro == 'Ano':
    anos_disponiveis = ['Todos'] + list(range(2023, 2025))
    ano_selecionado = st.sidebar.selectbox('Selecione o ano', anos_disponiveis)
else:
    mes_selecionado = st.sidebar.selectbox('Selecione o mês', [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ])
    ano_selecionado = st.sidebar.selectbox('Selecione o ano', [2023, 2024])

# Definindo os nomes dos meses
nome_meses = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]

# Converter coluna de data para datetime ('Previsão início atendimento (BRA)')
if 'Previsão início atendimento (BRA)' in data.columns:
    data['Previsão início atendimento (BRA)'] = pd.to_datetime(data['Previsão início atendimento (BRA)'], format='%d/%m/%Y %H:%M:%S', errors='coerce')

# Mapeamento do CNPJ das filiais
mapeamento_CNPJ = {
    '15.245.792/0001-31': 'SMX MTZ',
    '15.245.792/0004-84': 'SMX FOR',
    '15.245.792/0005-65': 'SMX SUA',
    '15.245.792/0006-46': 'SMX SSZ',
    '15.245.792/0003-01': 'SMX CWB',
    '15.245.792/0007-27': 'SMX CXJ'
}

# Adicionar a coluna 'Filial' baseada na coluna 'CNPJ Transportadora'
data['Filial'] = data['CNPJ Transportadora'].map(mapeamento_CNPJ)

# Valores unitários de faturamento por CNPJ
faturamento_por_cnpj = {
        'SMX MTZ': 1500.00,
        'SMX FOR': 850.00,
        'SMX SUA': 900.00,
        'SMX SSZ': 1250.00,
        'SMX CWB': 1500.00,
        'SMX CXJ': 1500.00
    }

# Definição de regional
regionais = {
    'SMX MTZ': 'SUL',
    'SMX FOR': 'NORDESTE',
    'SMX SUA': 'NORDESTE',
    'SMX SSZ': 'SUDESTE',
    'SMX CWB': 'SUL',
    'SMX CXJ': 'SUL'
}

# Adicionar a coluna Região
data['Região'] = data['Filial'].map(regionais)

# Adicionar filtro de regional
if 'Região' in data.columns:
    regional_unica = ['Todos'] + data['Região'].dropna().unique().tolist()
    regional_selecionada = st.sidebar.selectbox('Região', options=regional_unica)
else:
    st.warning('A coluna "Região" não foi encontrada')

# Aplicar o filtro de regional
if regional_selecionada != 'Todos':
    data_filtrado = data[data['Região'] == regional_selecionada]
else:
    data_filtrado = data.copy()

# Filtro de filial de acordo com a regional
filial_filtrada = data_filtrado['Filial'].unique().tolist()
filial_unica = ['Todos'] + filial_filtrada
filial_selecionada = st.sidebar.selectbox('Filial', filial_unica)

# Aplicar o filtro de filial
if filial_selecionada != 'Todos':
    data_filtrado = data_filtrado[data_filtrado['Filial'] == filial_selecionada]

# Filtro de data
if 'Previsão início atendimento (BRA)' in data.columns:
    if tipo_filtro == 'Ano' and ano_selecionado != 'Todos':
        data_inicio = pd.to_datetime(f'{ano_selecionado}-01-01 00:00:00')
        data_fim = pd.to_datetime(f'{ano_selecionado}-12-31 23:59:59')
    elif tipo_filtro == 'Mês' and ano_selecionado != 'Todos' and mes_selecionado != 'Todos':
        numero_mes = nome_meses.index(mes_selecionado) + 1
        data_inicio = pd.to_datetime(f'{ano_selecionado}-{numero_mes}-01 00:00:00')
        data_fim = (data_inicio + pd.DateOffset(months=1)) - pd.Timedelta(seconds=1)
    else:
        data_inicio = pd.to_datetime(data['Previsão início atendimento (BRA)'].min())
        data_fim = pd.to_datetime(data['Previsão início atendimento (BRA)'].max())
    
    data_filtrado = data_filtrado[(data_filtrado['Previsão início atendimento (BRA)'] >= data_inicio) & 
                                  (data_filtrado['Previsão início atendimento (BRA)'] <= data_fim)]

# Filtro por Número de programações
cleaned_data = data_filtrado.dropna(subset=['Número da programação'])

# Quantidade de programações
total_programacoes = cleaned_data['Número da programação'].nunique()

# Quantidade de programações canceladas
programacoes_canceladas = cleaned_data[cleaned_data['Situação programação'] == 'CANCELADA']
total_programacoes_canceladas = programacoes_canceladas['Número da programação'].nunique()

# Quantidade de programações atendidas
programacoes_atendidas = cleaned_data[cleaned_data['Situação programação'] != 'CANCELADA']
total_programacoes_atendidas = programacoes_atendidas['Número da programação'].nunique()

# Quantidade de programações atrasadas (não canceladas)
programacoes_atrasadas = cleaned_data[
    (cleaned_data['Situação prazo programação'] == 'Atrasado') & 
    (cleaned_data['Situação programação'] != 'CANCELADA')
    ]
total_programacoes_atrasadas = programacoes_atrasadas['Número da programação'].nunique()

# Calcular faturamento total
if filial_selecionada == 'Todos':
    faturamento_total = sum(cleaned_data['Filial'].map(faturamento_por_cnpj).fillna(0))
else:
    faturamento_total = total_programacoes * faturamento_por_cnpj.get(filial_selecionada, 0)

# Calcular faturamento cancelado
if filial_selecionada == 'Todos':
    faturamento_cancelado = sum(programacoes_canceladas['Filial'].map(faturamento_por_cnpj).fillna(0))
else:
    faturamento_cancelado = total_programacoes_canceladas * faturamento_por_cnpj.get(filial_selecionada, 0)

# Calcular faturamento atendido
faturamento_atendido = faturamento_total - faturamento_cancelado

# Verificar se o tipo de filtro selecionado é 'Ano'
if tipo_filtro == 'Ano':
    # Calcular o faturamento atendido para cada mês do ano selecionado
    if ano_selecionado != 'Todos':
        faturamento_por_mes = {}
        nome_meses = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        for mes_numero, nome_mes in enumerate(nome_meses, start=1):
            data_inicio_mes = pd.to_datetime(f'{ano_selecionado}-{mes_numero}-01 00:00:00')
            data_fim_mes = (data_inicio_mes + pd.DateOffset(months=1)) - pd.Timedelta(seconds=1)
            data_filtrado_mes = data_filtrado[(data_filtrado['Previsão início atendimento (BRA)'] >= data_inicio_mes) & 
                                               (data_filtrado['Previsão início atendimento (BRA)'] <= data_fim_mes)]
            faturamento_atendido_mes = data_filtrado_mes['Filial'].map(faturamento_por_cnpj).fillna(0).sum()
            faturamento_por_mes[(ano_selecionado, mes_numero)] = faturamento_atendido_mes

        # Criar DataFrame com os valores de faturamento atendido por mês
        df_faturamento_por_mes = pd.DataFrame(list(faturamento_por_mes.items()), columns=['Ano_Mês', 'Faturamento Atendido'])
        df_faturamento_por_mes[['Ano', 'Mês']] = pd.DataFrame(df_faturamento_por_mes['Ano_Mês'].tolist(), index=df_faturamento_por_mes.index)
        df_faturamento_por_mes['Nome Mês'] = df_faturamento_por_mes['Mês'].apply(lambda x: nome_meses[x-1])  # Adiciona o nome do mês

        # Plotar o gráfico de barras
        fig_faturamento_mes = px.bar(
            df_faturamento_por_mes, 
            x='Nome Mês', 
            y='Faturamento Atendido', 
            text='Faturamento Atendido', 
            labels={'Faturamento Atendido': 'Faturamento Atendido (R$)'}
        )

    else:
        # Calcular o faturamento atendido para cada mês de todos os anos selecionados
        faturamento_por_mes = {}
        for ano in anos_disponiveis[1:]:
            for mes_numero, nome_mes in enumerate(nome_meses, start=1):
                data_inicio_mes = pd.to_datetime(f'{ano}-{mes_numero}-01 00:00:00')
                data_fim_mes = (data_inicio_mes + pd.DateOffset(months=1)) - pd.Timedelta(seconds=1)
                data_filtrado_mes = data_filtrado[(data_filtrado['Previsão início atendimento (BRA)'] >= data_inicio_mes) & 
                                                   (data_filtrado['Previsão início atendimento (BRA)'] <= data_fim_mes)]
                faturamento_atendido_mes = data_filtrado_mes['Filial'].map(faturamento_por_cnpj).fillna(0).sum()
                faturamento_por_mes[(ano, mes_numero)] = faturamento_atendido_mes

        # Criar DataFrame com os valores de faturamento atendido por mês
        df_faturamento_por_mes = pd.DataFrame(list(faturamento_por_mes.items()), columns=['Ano_Mês', 'Faturamento Atendido'])
        df_faturamento_por_mes[['Ano', 'Mês']] = pd.DataFrame(df_faturamento_por_mes['Ano_Mês'].tolist(), index=df_faturamento_por_mes.index)
        df_faturamento_por_mes['Nome Mês'] = df_faturamento_por_mes['Mês'].apply(lambda x: nome_meses[x-1])  # Adiciona o nome do mês

        # Plotar o gráfico de barras
        fig_faturamento_mes = px.bar(
            df_faturamento_por_mes, 
            x='Nome Mês', 
            y='Faturamento Atendido', 
            text='Faturamento Atendido', 
            labels={'Faturamento Atendido': 'Faturamento Atendido (R$)'},
            color='Ano'  # Adiciona uma cor diferente para cada ano
        )

# Calcular o faturamento cancelado por mês
if tipo_filtro == 'Ano':
    if ano_selecionado != 'Todos':
        faturamento_cancelado_por_mes = {}
        for mes_numero, nome_mes in enumerate(nome_meses, start=1):
            data_inicio_mes = pd.to_datetime(f'{ano_selecionado}-{mes_numero}-01 00:00:00')
            data_fim_mes = (data_inicio_mes + pd.DateOffset(months=1)) - pd.Timedelta(seconds=1)
            data_filtrado_mes = data_filtrado[(data_filtrado['Previsão início atendimento (BRA)'] >= data_inicio_mes) & 
                                               (data_filtrado['Previsão início atendimento (BRA)'] <= data_fim_mes) &
                                               (data_filtrado['Situação programação'] == 'CANCELADA')]
            faturamento_cancelado_mes = data_filtrado_mes['Filial'].map(faturamento_por_cnpj).fillna(0).sum()
            faturamento_cancelado_por_mes[(ano_selecionado, mes_numero)] = faturamento_cancelado_mes

        # Criar DataFrame com os valores de faturamento cancelado por mês
        df_faturamento_cancelado_por_mes = pd.DataFrame(list(faturamento_cancelado_por_mes.items()), columns=['Ano_Mês', 'Faturamento Cancelado'])
        df_faturamento_cancelado_por_mes[['Ano', 'Mês']] = pd.DataFrame(df_faturamento_cancelado_por_mes['Ano_Mês'].tolist(), index=df_faturamento_cancelado_por_mes.index)
        df_faturamento_cancelado_por_mes['Nome Mês'] = df_faturamento_cancelado_por_mes['Mês'].apply(lambda x: nome_meses[x-1])  # Adiciona o nome do mês

        # Plotar o gráfico de barras para faturamento cancelado por mês
        fig_faturamento_cancelado_mes = px.bar(
            df_faturamento_cancelado_por_mes, 
            x='Nome Mês', 
            y='Faturamento Cancelado', 
            text='Faturamento Cancelado', 
            labels={'Faturamento Cancelado': 'Faturamento Cancelado (R$)'}
        )

    else:
        # Calcular o faturamento cancelado para cada mês de todos os anos selecionados
        faturamento_cancelado_por_mes = {}
        for ano in anos_disponiveis[1:]:
            for mes_numero, nome_mes in enumerate(nome_meses, start=1):
                data_inicio_mes = pd.to_datetime(f'{ano}-{mes_numero}-01 00:00:00')
                data_fim_mes = (data_inicio_mes + pd.DateOffset(months=1)) - pd.Timedelta(seconds=1)
                data_filtrado_mes = data_filtrado[(data_filtrado['Previsão início atendimento (BRA)'] >= data_inicio_mes) & 
                                                   (data_filtrado['Previsão início atendimento (BRA)'] <= data_fim_mes) &
                                                   (data_filtrado['Situação programação'] == 'CANCELADA')]
                faturamento_cancelado_mes = data_filtrado_mes['Filial'].map(faturamento_por_cnpj).fillna(0).sum()
                faturamento_cancelado_por_mes[(ano, mes_numero)] = faturamento_cancelado_mes

        # Criar DataFrame com os valores de faturamento cancelado por mês
        df_faturamento_cancelado_por_mes = pd.DataFrame(list(faturamento_cancelado_por_mes.items()), columns=['Ano_Mês', 'Faturamento Cancelado'])
        df_faturamento_cancelado_por_mes[['Ano', 'Mês']] = pd.DataFrame(df_faturamento_cancelado_por_mes['Ano_Mês'].tolist(), index=df_faturamento_cancelado_por_mes.index)
        df_faturamento_cancelado_por_mes['Nome Mês'] = df_faturamento_cancelado_por_mes['Mês'].apply(lambda x: nome_meses[x-1])  # Adiciona o nome do mês

        # Plotar o gráfico de barras para faturamento cancelado por mês
        fig_faturamento_cancelado_mes = px.bar(
            df_faturamento_cancelado_por_mes, 
            x='Nome Mês', 
            y='Faturamento Cancelado', 
            text='Faturamento Cancelado', 
            labels={'Faturamento Cancelado': 'Faturamento Cancelado (R$)'},
            color='Ano'  # Adiciona uma cor diferente para cada ano
        )

    # Dividindo o layout em duas colunas para os gráficos de barras
    col1, col2 = st.columns(2)

    # Plotar o gráfico de barras para faturamento atendido por mês
    col1.subheader('Faturamento Atendido por Mês')
    col1.plotly_chart(fig_faturamento_mes)

    # Plotar o gráfico de barras para faturamento cancelado por mês
    col2.subheader('Faturamento Cancelado por Mês')
    col2.plotly_chart(fig_faturamento_cancelado_mes)

# Exibir indicadores com st.metric dentro de caixas
st.markdown("<h2 style='text-align: center;'>SIL Log-In</h2>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    with st.container():
        st.markdown("<div style='padding: 10px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9;'>", unsafe_allow_html=True)
        st.metric("Programações Recebidas", total_programacoes)
        st.metric("Faturamento Estimado", f"R$ {faturamento_total:,.2f}")
        st.markdown("</div>", unsafe_allow_html=True)

with col2:
    with st.container():
        st.markdown("<div style='padding: 10px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9;'>", unsafe_allow_html=True)
        st.metric("Programações Canceladas", total_programacoes_canceladas)
        st.metric("Faturamento Cancelado", f"R$ {faturamento_cancelado:,.2f}")
        st.markdown("</div>", unsafe_allow_html=True)

with col3:
    with st.container():
        st.markdown("<div style='padding: 10px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9;'>", unsafe_allow_html=True)
        st.metric("Programações Atendidas", total_programacoes_atendidas)
        st.metric("Faturamento Atendido", f'R$ {faturamento_atendido:,.2f}')
        st.markdown("</div>", unsafe_allow_html=True)

st.warning(f'{total_programacoes_atrasadas} programações atrasadas.')

st.error(f'Penalização: R$ {faturamento_atendido * 0.02:,.2f}')

# Dividindo o layout em duas colunas para gráficos
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

# Gráfico para visualizar a contagem de tipos de operações
if 'Tipo de programação' in cleaned_data.columns:
    cleaned_data_nao_canceladas = cleaned_data[cleaned_data['Situação programação'] != 'CANCELADA']
    fig_tipos_operacao = px.pie(cleaned_data_nao_canceladas, names='Tipo de programação', title='Tipos de Operação')
    fig_tipos_operacao.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
    col1.plotly_chart(fig_tipos_operacao)
else:
    col1.warning("A coluna 'Tipo de programação' não foi encontrada no dataframe.")

# Gráfico para visualizar o status do prazo das operações (excluindo programações canceladas)
if 'Situação prazo programação' in cleaned_data.columns:
    # Filtrar as programações que não estão canceladas
    cleaned_data_nao_canceladas = cleaned_data[cleaned_data['Situação programação'] != 'CANCELADA']
    fig_prazo_operacoes = px.pie(
        cleaned_data_nao_canceladas,
        names='Situação prazo programação',
        title='Pontualidade',
        color='Situação prazo programação',
        color_discrete_map={
            'No prazo': 'green',
            'Atrasado': 'red'
        }
    )
    fig_prazo_operacoes.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
    col2.plotly_chart(fig_prazo_operacoes)
else:
    col2.warning("A coluna 'Situação prazo programação' não foi encontrada no dataframe.")

# Gráfico para visualizar o faturamento atendido por filial
if filial_selecionada == 'Todos':
    # Calcular o faturamento atendido por filial
    faturamento_por_filial = data_filtrado.groupby('Filial')['Filial'].apply(lambda x: x.map(faturamento_por_cnpj).fillna(0).sum())

    # Verificar se há dados disponíveis para plotagem
    if not faturamento_por_filial.empty:
        # Resetar o índice do DataFrame resultante
        df_faturamento_por_filial = faturamento_por_filial.reset_index(name='Faturamento Atendido')
        
        # Renomear colunas para o gráfico
        df_faturamento_por_filial.columns = ['Filial', 'Faturamento Atendido']
        
        # Calcular o faturamento total atendido para o período selecionado
        faturamento_total_periodo = df_faturamento_por_filial['Faturamento Atendido'].sum()
        
        # Adicionar uma coluna com a porcentagem de faturamento atendido para cada filial
        df_faturamento_por_filial['Porcentagem'] = df_faturamento_por_filial['Faturamento Atendido'] / faturamento_total_periodo * 100
        
        # Plotar o gráfico de pizza
        fig_faturamento_filial = px.pie(
            df_faturamento_por_filial, 
            names='Filial',
            values='Porcentagem',
            title=f'Atendimento por Filial'
        )
        fig_faturamento_filial.update_traces(textinfo='percent+label')
        fig_faturamento_filial.update_layout(showlegend=True, legend=dict(orientation='h', yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
        col3.plotly_chart(fig_faturamento_filial)
    else:
        st.info("Não há dados disponíveis para as transportadoras selecionadas neste período.")

# Gráfico para visualizar a quantidade de programações atrasadas por filial
if filial_selecionada == 'Todos':

    if 'Situação prazo programação' in data_filtrado.columns:
        programacoes_atrasadas_por_filial = data_filtrado[data_filtrado['Situação prazo programação'] == 'Atrasado'].groupby('Filial').size()
        if not programacoes_atrasadas_por_filial.empty:
            fig_programacoes_atrasadas = px.bar(
                programacoes_atrasadas_por_filial, 
                x=programacoes_atrasadas_por_filial.index, 
                y=programacoes_atrasadas_por_filial.values, 
                text=programacoes_atrasadas_por_filial.values,
                labels={'x': 'Filial', 'y': 'Programações Atrasadas'}
            )
            fig_programacoes_atrasadas.update_traces(texttemplate='%{text}', textposition='outside')
            fig_programacoes_atrasadas.update_layout(title='Atrasos por Filial', xaxis_title='', yaxis_title='')
            col4.plotly_chart(fig_programacoes_atrasadas)
        else:
            col4.info("Não há programações atrasadas para as transportadoras selecionadas neste período.")
    else:
        col4.warning("A coluna 'Situação prazo programação' não foi encontrada no dataframe.")

