import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import openrouteservice
import ast  # Para converter string '[0, 5434, 123]' para lista

# ===== 1. Carregamento de dados =====
@st.cache_data
def carregar_dados():
    df_rotas = pd.read_csv("Data/resultados_rotas_cascais.csv", delimiter=";")  # Substitui pelo caminho real
    df_coords = pd.read_excel("Data/locais.xlsx")  # Substitui se for diferente
    # Adicionar manualmente os pontos 0 e 1
    novos_pontos = pd.DataFrame({
        "id": [0, 1],
        "latitude": [38.737235, 38.74494],
        "longitude": [-9.387461, -9.327972]
    })

    # Garantir que a coluna 'id' é do mesmo tipo
    df_coords["id"] = df_coords["id"].astype(int)
    df_coords = pd.concat([df_coords, novos_pontos], ignore_index=True)
    df_coords = df_coords.drop_duplicates(subset="id", keep="last")
    df_coords = df_coords.set_index("id")

    df_rotas["data"] = pd.to_datetime(df_rotas["data"])
    return df_rotas, df_coords

df_rotas, df_coords = carregar_dados()

# ===== 2. Interface de seleção =====
st.title("Rotas Cascais")


data_selecionada = st.date_input("Selecione a data", value=df_rotas["data"].min())
circuitos_disponiveis = df_rotas[df_rotas["data"] == pd.to_datetime(data_selecionada)]["circuito"].unique()


# Criar um dicionário de mapeamento: 'Circuito_01' -> 'Circuito 01'
circuito_display_map = {c: c.replace("_", " ") for c in circuitos_disponiveis}

# Inverter o dicionário: 'Circuito 01' -> 'Circuito_01'
circuito_display_map_inv = {v: k for k, v in circuito_display_map.items()}

nomes_para_mostrar = list(circuito_display_map.values())

# Interface com nomes formatados
circuito_display = st.selectbox("Selecione o circuito:", options=nomes_para_mostrar)

# Obter o nome real usado nos dados
circuito_selecionado = circuito_display_map_inv[circuito_display]


tipos_disponiveis = df_rotas[
    (df_rotas["data"] == pd.to_datetime(data_selecionada)) &
    (df_rotas["circuito"] == circuito_selecionado)
]["tipo"].unique()
tipo_selecionado = st.selectbox("Selecione o tipo de lixo", tipos_disponiveis)

# ===== 3. Obter rota específica =====
filtro = (
    (df_rotas["data"] == pd.to_datetime(data_selecionada)) &
    (df_rotas["circuito"] == circuito_selecionado) &
    (df_rotas["tipo"] == tipo_selecionado)
)

if not df_rotas[filtro].empty:
    linha = df_rotas[filtro].iloc[0]
    rota_ids = ast.literal_eval(linha["rota"])  # Converte string para lista de ints

    # Garantir que a rota começa em 0 (Estaleiro) e termina em 1 (Tratolixo)
    if rota_ids[0] != 0:
        rota_ids = [0] + rota_ids  # adiciona 0 no início, se necessário

    if rota_ids[-1] != 1:
        rota_ids = rota_ids + [1]  # adiciona 1 no final, se necessário

    # Obter coordenadas
    try:
        coords = [(df_coords.loc[pid, "longitude"], df_coords.loc[pid, "latitude"]) for pid in rota_ids]
    except KeyError as e:
        st.error(f"Ponto de ID {e} não encontrado nas coordenadas.")
        st.stop()

    # ===== 4. Função para gerar o mapa com rota =====
   
    def plot_rota_folium(coords, ors_api_key):
        client = openrouteservice.Client(key=ors_api_key)

        def split_coords(coords, max_size=40):
            for i in range(0, len(coords) - 1, max_size - 1):
                yield coords[i:i + max_size]

        def get_full_route_geometry(coords):
            full_route = {"type": "FeatureCollection", "features": []}
            for segment in split_coords(coords):
                result = client.directions(
                    coordinates=segment,
                    profile='driving-car',
                    format='geojson'
                )
                full_route["features"].extend(result["features"])
            return full_route

        route_geojson = get_full_route_geometry(coords)

        m = folium.Map(location=coords[0][::-1], zoom_start=13)
        folium.GeoJson(
            route_geojson,
            name="Rota",
            style_function=lambda feature: {
                'color': '#3388ff',
                'weight': 5,
                'opacity': 0.8
            }
        ).add_to(m)

        for i, (lon, lat) in enumerate(coords):
            if i == 0:
                folium.Marker(
                    [lat, lon],
                    icon=folium.Icon(color="green", icon="play"),
                    tooltip="Estaleiro"
                ).add_to(m)
            elif i == len(coords) - 1:
                folium.Marker(
                    [lat, lon],
                    icon=folium.Icon(color="red", icon="stop"),
                    tooltip="Tratolixo"
                ).add_to(m)
            else:
                folium.CircleMarker(
                    [lat, lon],
                    radius=4,
                    color="blue",
                    fill=True,
                    fill_opacity=0.5,
                    tooltip=f"Ponto {i}"
                ).add_to(m)

        folium.LayerControl().add_to(m)
        return m

    # ===== 5. Exibir o mapa =====
    ORS_API_KEY = "5b3ce3597851110001cf624882d5a1b8d3444c489b1b384e680e6093" 

    #st.write("Primeiro ponto da rota (deve ser ID 0):", rota_ids[0])
    #st.write("Último ponto da rota (deve ser ID 1):", rota_ids[-1])

    mapa = plot_rota_folium(coords, ORS_API_KEY)
    folium_static(mapa, width=800, height=600)

    #col1, = st.columns(1)

    # Aplicar o filtro
    linha_rota = df_rotas[filtro].iloc[0]

    # Extrair os valores
    dist = linha_rota["dist"]  # distância em metros
    tempo = linha_rota["tempo"]  # duração em minutos
    ocupacao_camiao = linha_rota["load"]
    clientes= linha_rota["numclientes"]
    lixo_un = linha_rota["prizes_un"]

    st.subheader("📊 Informações da Rota")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📏 Distância", f"{dist/1000:.2f} km")
        st.metric("📍 Pontos visitados", clientes+1)

    with col2:
        st.metric("🕒 Duração", f"{round(tempo)} min")
        st.metric("🚛 Ocupação", f"{round(ocupacao_camiao)}")

    with col3:
        st.metric("🗑️ Lixo não recolhido", f"{round(lixo_un)}")



else:
    st.warning("Não foram encontradas rotas para os filtros selecionados.")
