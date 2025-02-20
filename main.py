import pandas as pd
import streamlit as st
import plotly.express as px

# Configuração do Streamlit
st.set_page_config(page_title="Segurança do Trabalho", layout="wide")

# Nova função para carregar os dados do arquivo CSV local
@st.cache_data(show_spinner=False)
def carregar_dados_csv():
    try:
        # Lê o arquivo CSV armazenado localmente (certifique-se de que o arquivo acidentes.csv esteja na mesma pasta)
        df = pd.read_csv("acidentes.csv", encoding="utf-8", delimiter=",")
        return df.to_dict(orient="records")
    except Exception as e:
        st.error(f"Erro ao ler o arquivo acidentes.csv: {e}")
        return None

@st.cache_data(show_spinner=False)
def processar_dados(dados):
    df = pd.DataFrame(dados)

    # Função para limpar e converter o valor do ÔNUS
    def limpar_onus(valor):
        try:
            valor_limpo = str(valor).replace('R$', '').replace('.', '').replace(',', '.').strip()
            return float(valor_limpo)
        except:
            return 0.0

    if 'ÔNUS' in df.columns:
        df['ÔNUS'] = df['ÔNUS'].apply(limpar_onus)
    if 'DIAS AFASTAMENTO' in df.columns:
        df['DIAS AFASTAMENTO'] = pd.to_numeric(df['DIAS AFASTAMENTO'], errors='coerce').fillna(0)

    # Converter datas, se a coluna existir
    if 'DIA DA OCORRÊNCIA' in df.columns:
        df['DIA DA OCORRÊNCIA'] = pd.to_datetime(df['DIA DA OCORRÊNCIA'], dayfirst=True, errors='coerce')

    return df

def dashboard():
    st.title("Estatísticas de Acidente de Trabalho")

    # Agora os dados são carregados a partir do arquivo CSV local
    dados = carregar_dados_csv()
    if not dados:
        return
    df = processar_dados(dados)

    # Seção de Métricas
    st.subheader("Indicadores Principais")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Acidentes", len(df))
    with col2:
        total_dias = int(df['DIAS AFASTAMENTO'].sum()) if 'DIAS AFASTAMENTO' in df.columns else 0
        st.metric("Total Dias Afastados", total_dias)
    with col3:
        total_onus = df['ÔNUS'].sum() if 'ÔNUS' in df.columns else 0
        parte_inteira = int(total_onus)
        parte_decimal = f"{total_onus - parte_inteira:.2f}".split('.')[-1]
        valor_formatado = f"R$ {parte_inteira:,}".replace(',', '.') + f",{parte_decimal}"
        st.metric("Total de Ônus", valor_formatado)

    st.divider()
    st.subheader("Classificação de Acidentes")
    col8, col9 = st.columns(2)

    # Gráfico de Barras - Tipo de Acidente
    with col8:
        if 'TIPO DE ACIDENTE' in df.columns:
            st.write("**Tipos de Acidente Mais Frequentes**")
            df_tipo = df[df['TIPO DE ACIDENTE'] != '']
            tipo_counts = (
                df_tipo['TIPO DE ACIDENTE']
                .value_counts()
                .nlargest(10)
                .reset_index()
            )
            tipo_counts.columns = ['Tipo', 'Quantidade']
            fig = px.bar(
                tipo_counts,
                x='Quantidade',
                y='Tipo',
                orientation='h',
                labels={'Quantidade': 'Quantidade', 'Tipo': ''},
                color='Quantidade',
                color_continuous_scale='Blues'
            )
            fig.update_layout(showlegend=False, yaxis={'categoryorder': 'total ascending'}, height=500)
            st.plotly_chart(fig, use_container_width=True)

    # Gráfico de Pizza - Nexo Causal
    with col9:
        if 'NEXO CAUSAL' in df.columns:
            st.write("**Distribuição por Nexo Causal**")
            df_nexo = df[df['NEXO CAUSAL'] != '']
            nexo_counts = df_nexo['NEXO CAUSAL'].value_counts()
            fig = px.pie(
                names=nexo_counts.index,
                values=nexo_counts.values,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_traces(textposition='inside', textinfo='percent+label', hole=0.3)
            fig.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Distribuições Demográficas")
    col4, col5 = st.columns(2)

    # Gráfico de Pizza - Gênero
    with col4:
        if 'GÊNERO' in df.columns:
            st.write("**Distribuição por Gênero**")
            genero_counts = (
                df['GÊNERO']
                .value_counts()
                .reset_index()
            )
            genero_counts.columns = ['Gênero', 'Quantidade']
            color_map = {'Feminino': '#FF69B4', 'Masculino': '#1E90FF'}
            fig = px.pie(
                genero_counts,
                values='Quantidade',
                names='Gênero',
                color='Gênero',
                color_discrete_map=color_map
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    # Gráfico de Barras - Turno
    with col5:
        if 'TURNO' in df.columns:
            st.write("**Distribuição por Turno**")
            turnos_validos = ['Matutino', 'Vespertino', 'Noturno']
            df_turnos = df[df['TURNO'].isin(turnos_validos)]
            turno_counts = df_turnos['TURNO'].value_counts()
            st.bar_chart(turno_counts, height=300)

    st.divider()
    st.subheader("Evolução Temporal das Ocorrências")
    if 'DIA DA OCORRÊNCIA' in df.columns:
        df_data = df.dropna(subset=['DIA DA OCORRÊNCIA']).copy()
        df_data['Período'] = df_data['DIA DA OCORRÊNCIA'].dt.to_period('M').dt.strftime('%Y-%m')
        evolucao = df_data.groupby('Período').size().reset_index(name='Acidentes')
        fig = px.line(
            evolucao,
            x='Período',
            y='Acidentes',
            title='Evolução Mensal',
            markers=True,
            labels={'Período': 'Mês/Ano', 'Acidentes': 'Acidentes'}
        )
        fig.update_layout(xaxis=dict(tickangle=-45), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Coluna 'DIA DA OCORRÊNCIA' não encontrada")

    st.divider()
    st.subheader("Análise Institucional")
    col6, col7 = st.columns(2)

    # Gráfico de Barras Horizontais - Função
    with col6:
        if 'FUNÇÃO' in df.columns:
            st.write("**Funções com Mais Acidentes**")
            top_funcoes = (
                df['FUNÇÃO']
                .value_counts()
                .nlargest(10)
                .reset_index()
            )
            top_funcoes.columns = ['Função', 'Quantidade']
            fig = px.bar(
                top_funcoes,
                x='Quantidade',
                y='Função',
                orientation='h',
                color='Quantidade',
                text='Quantidade',
                color_continuous_scale='Blues'
            )
            fig.update_layout(showlegend=False, yaxis={'categoryorder': 'total ascending'}, height=400)
            st.plotly_chart(fig, use_container_width=True)

    # Gráfico de Pizza - Secretaria
    with col7:
        if 'SECRETARIA' in df.columns:
            st.write("**Distribuição por Secretaria**")
            secretaria_counts = (
                df['SECRETARIA']
                .value_counts()
                .reset_index()
            )
            secretaria_counts.columns = ['Secretaria', 'Quantidade']
            fig = px.pie(
                secretaria_counts,
                values='Quantidade',
                names='Secretaria',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Todos os Dados")
    def formatar_nat(valor):
        try:
            return f"{int(valor):,.0f}".replace(",", ".")
        except:
            return valor

    styled_df = df.style.format({
        'NAT': formatar_nat,
        'ÔNUS': lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if x > 0 else "R$ 0,00"
    })

    st.dataframe(styled_df, use_container_width=True, height=400)

def medidas_propostas():
    st.title("Estatísticas do Gerenciamento de Riscos")
    st.write("Esta seção apresenta as medidas propostas advindas dos Programas de Gerenciamento de Riscos (PGR) NR nº 01 - EM CONSTRUÇÃO.")
    st.markdown("""
    ## Medidas Propostas

    - Evolução dos quantidade de PGR x Mês/Ano.
    - Contagem de locais com PGR.
    - Contagem de PGR x Secretaria.
    - Contagem de riscos x secretaria.
    - Contagem das Medidas de Prevenção Total.
    - Contagem das Medidas de Prevenção x secretaria.
    - Contagem de EPIs Especificados.
    """)
    st.write("Mais informações e detalhes serão adicionados futuramente.")

def main():
    st.sidebar.title("SMRH-DSO - Menu")
    pagina = st.sidebar.radio("Selecione a Página", ("Acidentes de Trabalho", "Gerenciamento de Riscos"))
    if pagina == "Acidentes de Trabalho":
        dashboard()
    else:
        medidas_propostas()

if __name__ == "__main__":
    main()
