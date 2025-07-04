import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import random
import pydeck as pdk

@st.cache_data
def load():

    df = pd.read_csv("Data/tabela_com_niveis_recolhas.csv", delimiter=';')

    # Tradução dias da semana
    dias_traducao = {
    'Monday': 'segunda-feira',
    'Tuesday': 'terça-feira',
    'Wednesday': 'quarta-feira',
    'Thursday': 'quinta-feira',
    'Friday': 'sexta-feira',
    'Saturday': 'sábado',
    'Sunday': 'domingo'
    }
    
    df_unico = df[["Data do circuito", "Circuito"]].drop_duplicates()
    df_unico["Data do circuito"] = pd.to_datetime(df_unico["Data do circuito"], errors='coerce')

    df_unico["Dia da Semana"] = df_unico["Data do circuito"].dt.day_name().map(dias_traducao)
    dias_ordem = ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo']
    df_unico["Dia da Semana"] = pd.Categorical(df_unico["Dia da Semana"], categories=dias_ordem, ordered=True)

    frequencia = df_unico.groupby(["Circuito", "Dia da Semana"], observed=False).size().reset_index(name="Frequência")
    media_niveis = df.groupby("Circuito")[["Papel", "Embalagens", "Vidro"]].mean().reset_index()

    return frequencia, media_niveis, dias_ordem, df 

frequencia, media_niveis, dias_ordem, df = load()

@st.cache_data
def carregar_dados():
    df_circuitos = pd.read_excel("Data/Circuitos_data_atualizado_12_sem_6394.xlsx")
    df_coords = pd.read_excel("Data/locais.xlsx")
    df_circuitos['Data do circuito'] = pd.to_datetime(df_circuitos['Data do circuito'])

    return df_circuitos, df_coords

df_circuitos, df_coords = carregar_dados()

# === 2. Preparar dados dos circuitos ===
@st.cache_data
def preparar_circuitos():
    dados = {}
    df_coords_indexado = df_coords.set_index("id")
    for circuito in df_circuitos["Nome do circuito"].unique():
        df_circ = df_circuitos[df_circuitos["Nome do circuito"] == circuito]
        pontos_ids = []
        for linha in df_circ["Pontos de passagem"]:
            if isinstance(linha, str):
                pontos_ids.extend(map(int, linha.split(", ")))

        coords = [
            (df_coords_indexado.loc[ponto_id, "longitude"], df_coords_indexado.loc[ponto_id, "latitude"])
            for ponto_id in pontos_ids if ponto_id in df_coords_indexado.index
        ]
        dados[circuito] = {"coords": coords}
    return dados

dados_circuitos = preparar_circuitos()


st.title("Análise de Dados")

# Menu de seleção das secções
secao = st.selectbox("Selecione a secção para visualizar:", [
    "Frequência semanal e médias de enchimento",
    "Distribuição de pontos por número de circuitos",
    "Quantidade de pontos por circuito",
    "Visualização geográfica dos pontos por circuito",
    "Gráficos de um ponto aleatório por circuito",
    "Evolução temporal dos níveis por circuito",
    "Quantidade de lixo recolhido por tipo e circuito vs total",
    "Evolução temporal do lixo recolhido por tipo"
])

if secao == "Frequência semanal e médias de enchimento":

    st.markdown("---")
    st.subheader("Frequência semanal e média dos níveis de enchimento por circuito")

    for i, circuito in enumerate(media_niveis["Circuito"]):
        dados_frequencia = frequencia[frequencia["Circuito"] == circuito]
        dados_frequencia = dados_frequencia.set_index("Dia da Semana").reindex(dias_ordem, fill_value=0).reset_index()

        cols = st.columns(2)
        with cols[0]:
            st.markdown(f"#### {circuito}")
            fig1 = px.bar(
                dados_frequencia,
                x="Dia da Semana",
                y="Frequência",
                title="Frequência Semanal",
                labels={"Frequência": "Frequência"},
                color_discrete_sequence=["#4a90e2"]
            )
            fig1.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig1, use_container_width=True)

        with cols[1]:
            media_circuito = media_niveis[media_niveis["Circuito"] == circuito]
            medias = {
                "Tipo": ["Papel", "Embalagens", "Vidro"],
                "Média": [
                    media_circuito["Papel"].values[0],
                    media_circuito["Embalagens"].values[0],
                    media_circuito["Vidro"].values[0]
                ]
            }
            df_medias = pd.DataFrame(medias)

            fig2 = px.bar(
                df_medias,
                x="Tipo",
                y="Média",
                title="Média dos Níveis",
                color="Tipo",
                color_discrete_sequence=["#3498db", "#f1c40f", "#2ecc71"]
            )
            fig2.update_layout(yaxis_range=[0, 6], height=300, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig2, use_container_width=True)

elif secao == "Distribuição de pontos por número de circuitos":

    st.markdown("---")
    st.subheader("Distribuição de pontos por número de circuitos")

    locais_por_circuito = df.groupby("local_id")["Circuito"].nunique()
    distribuicao = locais_por_circuito.value_counts().sort_index()

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(distribuicao.index, distribuicao.values, color="mediumseagreen")
    ax.set_xlabel("Número de circuitos distintos")
    ax.set_ylabel("Quantidade de pontos")
    ax.set_title("Distribuição de pontos por número de circuitos")
    ax.set_xticks(distribuicao.index)
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    for bar in bars:
        altura = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            altura + 0.5,
            str(int(altura)),
            ha='center',
            va='bottom',
            fontsize=10,
                fontweight='bold'
        )
    plt.tight_layout()
    st.pyplot(fig)

    st.write("Como é possível observar, existem **915 pontos** no total, sendo que apenas **17** pertencem a mais do que um circuito.")

elif secao == "Quantidade de pontos por circuito":

    st.markdown("---")
    st.subheader("Quantidade de pontos por circuito")

    dados = {
        "Circuito": [
            "Circ. Ilhas", "Circuito 01", "Circuito 02", "Circuito 03", "Circuito 04",
            "Circuito 05", "Circuito 06", "Circuito 07", "Circuito 08", "Circuito 09",
            "Circuito 10", "Circuito 11", "Circuito 12"
        ],
        "Nº de Pontos Únicos": [42, 64, 70, 65, 70, 73, 73, 67, 74, 48, 76, 68, 142]
    }

    df_pontos = pd.DataFrame(dados)
    df_pontos = df_pontos.sort_values("Nº de Pontos Únicos", ascending=False)

    fig = px.bar(
        df_pontos,
        x="Circuito",
        y="Nº de Pontos Únicos",
        text="Nº de Pontos Únicos",
        color="Circuito",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis_title="Circuito",
        yaxis_title="Nº de Pontos",
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        height=500,
        margin=dict(t=50, b=50)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.write(
        "O número de pontos médio por circuito é cerca de **70**. As excessões ocorrem no **Cirucito 12** que regista **142 pontos**, " 
        "o **Circuito 09** com **48 pontos** e o **Circ. Ilhas** com **42 pontos**."
    )


elif secao == "Visualização geográfica dos pontos por circuito":
    st.markdown("---")
    st.subheader("Mapa interativo com pontos dos circuitos")

    circuitos_disponiveis = list(dados_circuitos.keys())
    circuitos_selecionados = st.multiselect(
        "Selecione os circuitos a visualizar no mapa:",
        options=circuitos_disponiveis,
        default=[],
    )

    if not circuitos_selecionados:
        st.info("Selecione ao menos um circuito para visualizar os pontos no mapa.")
    else:
        mapa_df = []

        for circuito in circuitos_selecionados:
            for lon, lat in dados_circuitos[circuito]["coords"]:
                mapa_df.append({
                    "Circuito": circuito,
                    "Latitude": lat,
                    "Longitude": lon
                })

        df_mapa = pd.DataFrame(mapa_df)

                # Cores para os circuitos (RGB)
        cores_disponiveis = [
            [255, 99, 71],    # Tomato
            [30, 144, 255],   # DodgerBlue
            [60, 179, 113],   # MediumSeaGreen
            [255, 215, 0],    # Gold
            [186, 85, 211],   # MediumOrchid
            [255, 140, 0],    # DarkOrange
            [100, 149, 237],  # CornflowerBlue
            [0, 206, 209],    # DarkTurquoise
            [244, 164, 96],   # SandyBrown
            [154, 205, 50],   # YellowGreen
            [255, 105, 180],  # HotPink
            [0, 191, 255],    # DeepSkyBlue
            [147, 112, 219],  # MediumPurple
        ]

        # Atribuir uma cor para cada circuito
        cores_circuitos = {nome: cores_disponiveis[i % len(cores_disponiveis)] for i, nome in enumerate(circuitos_selecionados)}

        # Adicionar cor aos dados
        df_mapa["color"] = df_mapa["Circuito"].map(cores_circuitos)

        # Layer de pontos
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_mapa,
            get_position='[Longitude, Latitude]',
            get_fill_color="color",
            get_radius=25,
            pickable=True,
        )

        # View inicial centrada na média dos pontos
        if not df_mapa.empty:
            view_state = pdk.ViewState(
                latitude=df_mapa["Latitude"].mean(),
                longitude=df_mapa["Longitude"].mean(),
                zoom=12,
                pitch=0,
            )

            # Mapa com camada
            st.pydeck_chart(pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={"text": "{Circuito}"}
            ))


        #st.map(df_mapa, latitude="Latitude", longitude="Longitude", size=10)


elif secao == "Gráficos de um ponto aleatório por circuito":

    st.markdown("---")
    st.subheader("Gráficos de um ponto aleatório por Circuito")
    st.subheader("")

    colunas_nivel = {
        "Papel": "Papel",
        "Embalagens": "Embalagens",
        "Vidro": "Vidro"
    }
    colunas_recolha = {
        "Papel": "Recolhido Papel",
        "Embalagens": "Recolhido Embalagens",
        "Vidro": "Recolhido Vidro"
    }

    random.seed(42)
    pontos_por_circuito = {}
    for circuito in df["Circuito"].unique():
        locais = df[df["Circuito"] == circuito]["local_id"].unique()
        if len(locais) > 0:
            pontos_por_circuito[circuito] = random.choice(locais)

    ordem_circuitos = ["Circ. Ilhas"] + [f"Circuito {str(i).zfill(2)}" for i in range(1, 13)]

    for circuito in ordem_circuitos:
        if circuito not in pontos_por_circuito:
            continue

        local_id = pontos_por_circuito[circuito]
        df_local = df[df["local_id"] == local_id]
        df_local["Data do circuito"] = pd.to_datetime(df_local["Data do circuito"])


        st.subheader(f"{circuito} – Ponto {local_id}")

        for nome in colunas_nivel.keys():
            col1, col2, col3 = st.columns(3)

            dados = df_local[colunas_nivel[nome]].dropna().astype(int)
            freq = dados.value_counts().sort_index()
            media = dados.mean()

            fig_hist = go.Figure()
            fig_hist.add_trace(go.Bar(x=freq.index, y=freq.values, marker_color='skyblue'))
            fig_hist.add_vline(x=media, line=dict(color='red', dash='dash'),
                            annotation_text=f"Média = {media:.2f}", annotation_position="top right")
            fig_hist.update_layout(title=f"{nome} - Frequência", xaxis_title="Nível", yaxis_title="Frequência", height=300)

            with col1:
                st.plotly_chart(fig_hist, use_container_width=True, key=f"hist_{circuito}_{local_id}_{nome}")

            ts = df_local[["Data do circuito", colunas_nivel[nome]]].dropna().sort_values("Data do circuito")
            ts[colunas_nivel[nome]] = ts[colunas_nivel[nome]].astype(int)
            media_ts = ts[colunas_nivel[nome]].mean()

            fig_ts = go.Figure()
            fig_ts.add_trace(go.Scatter(x=ts["Data do circuito"], y=ts[colunas_nivel[nome]], mode='lines+markers'))
            fig_ts.add_hline(y=media_ts, line=dict(color='red', dash='dash'),
                                annotation_text=f"Média = {media_ts:.2f}", annotation_position="bottom right")
            fig_ts.update_layout(title=f"{nome} - Série Temporal", xaxis_title="Data", yaxis_title="Nível", height=300)

            with col2:
                st.plotly_chart(fig_ts, use_container_width=True, key=f"ts_{circuito}_{local_id}_{nome}")

            datas = df_local[df_local[colunas_recolha[nome]] == 1][["Data do circuito"]].sort_values("Data do circuito").copy()
            datas["Data do circuito"] = pd.to_datetime(datas["Data do circuito"])
            datas["intervalo_dias"] = datas["Data do circuito"].diff().dt.days
            series = datas["intervalo_dias"].dropna()
            media_int = series.mean()

            fig_int = go.Figure()
            fig_int.add_trace(go.Scatter(x=datas["Data do circuito"].iloc[1:], y=series.values, mode='lines+markers'))
            fig_int.add_hline(y=media_int, line=dict(color='green', dash='dash'),
                            annotation_text=f"Média = {media_int:.1f} dias", annotation_position="bottom right")
            fig_int.update_layout(title=f"{nome} - Intervalo Recolhas", xaxis_title="Data", yaxis_title="Dias", height=300)

            with col3:
                st.plotly_chart(fig_int, use_container_width=True, key=f"int_{circuito}_{local_id}_{nome}")

            st.markdown("---")

        st.divider()
        
    st.write("""
        Com base nestes gráficos, podemos concluir o seguinte:

        - O nível 1 em **Papel** não foi registado.
        - Em relação às recolhas, **Embalagens** e **Papel** apresentam intervalos de recolha mais regulares.
        - O **Vidro** apresenta um espaçamento maior entre recolhas.
        - A quantidade de informação disponível varia por tipo, sendo o **Vidro** o que tem menos dados registados.
        """)

elif secao ==  "Evolução temporal dos níveis por circuito":
    st.markdown("---")
    st.subheader("Evolução Temporal dos Níveis de Enchimento por Circuito e dia")

    tipos_materiais = ["Papel", "Embalagens", "Vidro"]
    circuitos_ordenados = ["Circ. Ilhas"] + [f"Circuito {str(i).zfill(2)}" for i in range(1, 13)]

    # Conversão única da data
    df["Data do circuito"] = pd.to_datetime(df["Data do circuito"])

    for tipo in tipos_materiais:
        st.markdown(f"### {tipo}")
        for circuito in circuitos_ordenados:
            df_filtrado = df[df["Circuito"] == circuito][["Data do circuito", "local_id", tipo]].dropna()
            if df_filtrado.empty:
                continue

            df_media = df_filtrado.groupby("Data do circuito")[tipo].mean().reset_index()
            df_media[tipo] = df_media[tipo].astype(float)
            df_media = df_media.sort_values("Data do circuito")  # <- Ordenação

            fig = px.line(
                df_media,
                x="Data do circuito",
                y=tipo,
                title=f"{circuito} – Evolução Temporal ({tipo})",
                markers=True,
                labels={tipo: "Média do Nível por dia"},
                line_shape="linear"
            )
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)

        st.divider()


elif secao == "Quantidade de lixo recolhido por tipo e circuito vs total":

    st.markdown("---")
    st.subheader("Quantidade de lixo recolhido por tipo e por circuito")

    # Definições
    colunas_recolhido = {
        "Papel": "Recolhido Papel",
        "Embalagens": "Recolhido Embalagens",
        "Vidro": "Recolhido Vidro"
    }

    # Parte 1: Barras por tipo e circuito
    #st.markdown("### Por Circuito e Tipo")

    dados_recolha = df.groupby("Circuito")[[col for col in colunas_recolhido.values()]].sum().reset_index()
    dados_recolha = dados_recolha.rename(columns={
        "Recolhido Papel": "Papel",
        "Recolhido Embalagens": "Embalagens",
        "Recolhido Vidro": "Vidro"
    })

    df_melt = dados_recolha.melt(id_vars="Circuito", var_name="Tipo", value_name="Quantidade Recolhida")
    ordem_circuitos = ["Circ. Ilhas"] + [f"Circuito {str(i).zfill(2)}" for i in range(1, 13)]
    df_melt["Circuito"] = pd.Categorical(df_melt["Circuito"], categories=ordem_circuitos, ordered=True)
    df_melt = df_melt.sort_values("Circuito")

    fig_barras = px.bar(
        df_melt,
        x="Circuito",
        y="Quantidade Recolhida",
        color="Tipo",
        barmode="group",  # ou "group" se quiser lado a lado
        title="Quantidade de lixo recolhido por tipo e circuito",
        color_discrete_sequence=["#3498db", "#f1c40f", "#2ecc71"]
    )
    fig_barras.update_layout(
        height=500,
        xaxis_title="Circuito",
        yaxis_title="Total de Lixo Recolhido",
        margin=dict(t=50, b=50)
    )

    st.plotly_chart(fig_barras, use_container_width=True)

    # Parte 2: Totais por tipo
    st.markdown("### Total Geral por Tipo de Resíduo")

    totais = df_melt.groupby("Tipo")["Quantidade Recolhida"].sum().reset_index()

    fig_pizza = px.pie(
        totais,
        names="Tipo",
        values="Quantidade Recolhida",
        title="Proporção total de lixo recolhido por tipo",
        color_discrete_sequence=["#3498db", "#f1c40f", "#2ecc71"]
    )
    fig_pizza.update_traces(textposition='inside', textinfo='percent+label')

    st.plotly_chart(fig_pizza, use_container_width=True)

elif secao == "Evolução temporal do lixo recolhido por tipo":
    st.markdown("---")
    st.subheader("Evolução Temporal do Lixo Recolhido por Tipo")

    colunas_recolhido = {
        "Papel": "Recolhido Papel",
        "Embalagens": "Recolhido Embalagens",
        "Vidro": "Recolhido Vidro"
    }

    df_recolhido_tempo = df.copy()
    df_recolhido_tempo["Data do circuito"] = pd.to_datetime(df_recolhido_tempo["Data do circuito"])

    # Agrupar por data e somar a quantidade recolhida para cada tipo
    dados_recolhido_diario = df_recolhido_tempo.groupby("Data do circuito")[[col for col in colunas_recolhido.values()]].sum().reset_index()

    # Renomear as colunas para melhor visualização nos gráficos
    dados_recolhido_diario = dados_recolhido_diario.rename(columns={
        "Recolhido Papel": "Papel",
        "Recolhido Embalagens": "Embalagens",
        "Recolhido Vidro": "Vidro"
    })

    # Criar um gráfico de linha para cada tipo de material
    for tipo, col_df in colunas_recolhido.items():
        fig = px.line(
            dados_recolhido_diario,
            x="Data do circuito",
            y=tipo,
            title=f"Evolução Temporal do lixo recolhido de {tipo}",
            markers=True,
            labels={tipo: f"Quantidade de {tipo} Recolhida"},
            line_shape="linear",
            color_discrete_sequence=["#3498db"] if tipo == "Papel" else ["#f1c40f"] if tipo == "Embalagens" else ["#2ecc71"]
        )
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)
        st.divider()

