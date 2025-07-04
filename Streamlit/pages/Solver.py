import streamlit as st
from streamlit_folium import folium_static
from streamlit.components.v1 import html
import numpy as np
import pandas as pd
import folium
import time
from time import sleep
import openrouteservice
from openrouteservice import convert
import os
import csv
from tqdm import tqdm
import matplotlib.pyplot as plt

from pyvrp import Model, Solution
from pyvrp.stop import MaxRuntime
from pyvrp import Client, Depot, ProblemData, VehicleType, solve as _solve
from pyvrp.plotting import plot_result

@st.cache_data
def load_data(df):
    # Converter colunas de tempo
    #df['ultima_recolha'] = pd.to_timedelta(df['ultima_recolha'], errors='coerce')
    #df['ultima_observacao'] = pd.to_timedelta(df['ultima_observacao'], errors='coerce')

    # Converter a coluna de data e normalizar
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True)
    df['Data'] = df['Data'].dt.normalize()

    # Garantir que os níveis são numéricos
    #df['Nivel_inicio'] = pd.to_numeric(df['Nivel_inicio'], errors='coerce')
    #df['Nivel_fim'] = pd.to_numeric(df['Nivel_fim'], errors='coerce')

    #df['Nivel_inicio'] = df['Nivel_inicio'].fillna(3)
    #df['Nivel_fim'] = df['Nivel_fim'].fillna(3)

    return df

df=pd.read_csv("Data/niveis_inicio_fim.csv", delimiter=';')

@st.cache_data
def load_circuitos():
    pasta = 'Data/circuitos_pontos'
    circuitos = {}

    for nome_ficheiro in os.listdir(pasta):
        caminho_ficheiro = os.path.join(pasta, nome_ficheiro)
        nome_base = os.path.splitext(nome_ficheiro)[0]  # Ex: 'circ_01_pontos'

        # Extrair o número ou "ilhas"
        if 'ilhas' in nome_base:
            nome_circuito = 'Circ_Ilhas'
        else:
            try:
                numero = nome_base.split('_')[1]
                nome_circuito = f'Circuito_{int(numero):02d}'
            except (IndexError, ValueError):
                print(f'[Aviso] Nome inesperado no ficheiro: {nome_ficheiro}')
                continue

        with open(caminho_ficheiro, newline='', encoding='utf-8') as csvfile:
            leitor = csv.DictReader(csvfile)
            dados_circuito = []
            for linha in leitor:
                dados_circuito.append({
                    'id': int(linha['id']),
                    'lat': float(linha['lat']),
                    'lon': float(linha['lon'])
                })
            circuitos[nome_circuito] = dados_circuito

    return circuitos

@st.cache_data
def carregar_matrizes_dist_dos_circuitos(total=12):
    pasta = 'Data/matriz_dist'
    matrizes_dist = {}

    # Carrega circuitos 01 a 12
    for i in range(1, total + 1):
        nome_ficheiro = f"matriz_dist_circ_{i:02d}.csv"
        caminho = os.path.join(pasta, nome_ficheiro)
        if os.path.exists(caminho):
            #usa a primeira coluna como indice
            df = pd.read_csv(caminho, index_col=0)
            print(f"[Info] Carregado: {nome_ficheiro} com dimensões {df.shape}")
            matrizes_dist[f'Circuito_{i:02d}'] = df
        else:
            print(f"[Aviso] Ficheiro não encontrado: {nome_ficheiro}")

    # Carrega o circuito especial "ilhas"
    nome_ilhas = "matriz_dist_circ_ilhas.csv"
    caminho_ilhas = os.path.join(pasta, nome_ilhas)
    if os.path.exists(caminho_ilhas):
        df_ilhas = pd.read_csv(caminho_ilhas, index_col=0)
        print(f"[Info] Carregado: {nome_ilhas} com dimensões {df_ilhas.shape}")
        matrizes_dist["Circ_Ilhas"] = df_ilhas
    else:
        print(f"[Aviso] Ficheiro não encontrado: {nome_ilhas}")

    return matrizes_dist

@st.cache_data
def carregar_matrizes_tempo_dos_circuitos(total=12):
    pasta = 'Data/matriz_tempo'
    matrizes_tempo = {}

    # Carrega circuitos 01 a 12
    for i in range(1, total + 1):
        nome_ficheiro = f"matriz_tempo_circ_{i:02d}.csv"
        caminho = os.path.join(pasta, nome_ficheiro)
        if os.path.exists(caminho):
            df = pd.read_csv(caminho, index_col=0)
            print(f"[Info] Carregado: {nome_ficheiro} com dimensões {df.shape}")
            matrizes_tempo[f'Circuito_{i:02d}'] = df
        else:
            print(f"[Aviso] Ficheiro não encontrado: {nome_ficheiro}")

    # Carrega o circuito especial "ilhas"
    nome_ilhas = "matriz_tempo_circ_ilhas.csv"
    caminho_ilhas = os.path.join(pasta, nome_ilhas)
    if os.path.exists(caminho_ilhas):
        df_ilhas = pd.read_csv(caminho_ilhas, index_col=0)
        print(f"[Info] Carregado: {nome_ilhas} com dimensões {df_ilhas.shape}")
        matrizes_tempo["Circ_Ilhas"] = df_ilhas
    else:
        print(f"[Aviso] Ficheiro não encontrado: {nome_ilhas}")

    return matrizes_tempo


def extrair_demands_inicio(df, data, circuito, tipo, pontos_do_circuito):
    """
    Extrai a lista de demands para os pontos de um circuito específico
    com base no DataFrame com 'Nivel_inicio'.

    Parameters:
        df: DataFrame com colunas ['Data', 'Circuito', 'Tipo', 'local_id', 'Nivel_inicio']
        data: string ou datetime a filtrar (ex: '2023-01-01')
        circuito: nome do circuito (ex: 'Circuito 01')
        tipo: valor da coluna 'Tipo' a filtrar
        pontos_do_circuito: lista de dicionários com 'id', 'lat', 'lon'

    Returns:
        Lista de demands na mesma ordem dos pontos
    """
    df_filtrado = df[
        (df['Data'].dt.date == data) &
        (df['Circuito'] == circuito) &
        (df['Tipo'] == tipo)
    ]

    # Mapeia local_id → Nivel_inicio
    nivel_por_id = dict(zip(df_filtrado['local_id'], df_filtrado['nivel_inicio']))
    #print(nivel_por_id)  # Verificar o conteúdo do dicionário

    # Cria lista de demands na ordem dos pontos
    demands = []
    for ponto in pontos_do_circuito:
        local_id = ponto['id']
        demand = nivel_por_id.get(local_id, 0)  # se não houver, assume 0
        demands.append(demand)

    return demands


def extrair_demands_fim(df, data, circuito, tipo, pontos_do_circuito):
    """
    Extrai a lista de demands para os pontos de um circuito específico
    com base no DataFrame com 'Nivel_inicio'.

    Parameters:
        df: DataFrame com colunas ['Data', 'Circuito', 'Tipo', 'local_id', 'Nivel_inicio']
        data: string ou datetime a filtrar (ex: '2023-01-01')
        circuito: nome do circuito (ex: 'Circuito 01')
        tipo: valor da coluna 'Tipo' a filtrar
        pontos_do_circuito: lista de dicionários com 'id', 'lat', 'lon'

    Returns:
        Lista de demands na mesma ordem dos pontos
    """
    df_filtrado = df[
        (df['Data'].dt.date == data) &
        (df['Circuito'] == circuito) &
        (df['Tipo'] == tipo)
    ]

    # Mapeia local_id → Nivel_inicio
    nivel_por_id = dict(zip(df_filtrado['local_id'], df_filtrado['nivel_fim']))
    #print(nivel_por_id)  # Verificar o conteúdo do dicionário

    # Cria lista de demands na ordem dos pontos
    demands = []
    for ponto in pontos_do_circuito:
        local_id = ponto['id']
        demand = nivel_por_id.get(local_id, 0)  # se não houver, assume 0
        demands.append(demand)

    return demands


def construir_instance(circuito, pontos, matrizes_dist_dict, matrizes_tempo_dict, demands, capacidade):
    coords = [[p['lon'], p['lat']] for p in pontos]
    num_locs = len(coords)
    instance = {
        "coords": coords,
        "demands": demands,
        "prize": [beta * d / sum(demands)   for d in demands],  # ← CORRIGIDO AQUI
        "service_time": [5] * num_locs,
        "capacity": capacidade,
        "cost_matrix": matrizes_dist_dict[circuito].to_numpy() / dist_scale ,
        "time_matrix": matrizes_tempo_dict[circuito].to_numpy(),
        "start_depot_idx": 0,
        "end_depot_idx": 1
    }

    return instance

@st.cache_data
def scale(data, scaling_factor):
    arr = np.array(data, dtype=float)  # converte input para array numpy float
    arr = arr * scaling_factor          # multiplica valores, não o tamanho
    arr = np.where(np.isfinite(arr), arr, 0)  # trata NaN ou inf substituindo por 0
    #arr = arr.round().astype(int)       # arredonda e converte para int
    if arr.size == 1:
        return arr.item()               # retorna escalar se só tiver um elemento
    return arr

def instance2data(instance: dict, scaling_factor: int) -> ProblemData:
    """
    Converte uma instância genérica para o formato ProblemData do PyVRP,
    preparada para problemas com clientes opcionais (PCVRP).
    """


    # Converter DataFrames para listas, se necessário
    #if isinstance(instance["cost_matrix"], pd.DataFrame):
    #    instance["cost_matrix"] = instance["cost_matrix"].values.tolist()
    #if isinstance(instance["time_matrix"], pd.DataFrame):
    #    instance["time_matrix"] = instance["time_matrix"].values.tolist()

    # Aplicar escala
    coords = scale(instance["coords"], scaling_factor)
    demands = scale(instance["demands"], scaling_factor)
    prize = scale(instance["prize"], scaling_factor)
    service = scale(instance["service_time"], scaling_factor)
    capacity = [scale(instance["capacity"], scaling_factor)]
    matrix = scale(instance["cost_matrix"], scaling_factor)
    matrix_time = scale(instance["time_matrix"], scaling_factor)

    num_locs = len(coords)
    start_depot_idx = instance.get("start_depot_idx", 0)
    end_depot_idx = instance.get("end_depot_idx", 1)

    # Verificar índices de depósitos
    if start_depot_idx < 0 or start_depot_idx >= num_locs:
        raise ValueError(f"Início do depósito inválido: {start_depot_idx}")
    if end_depot_idx < 0 or end_depot_idx >= num_locs:
        raise ValueError(f"Fim do depósito inválido: {end_depot_idx}")

    # Criar depósitos
    depots = [Depot(x=coords[start_depot_idx][0], y=coords[start_depot_idx][1])]
    if start_depot_idx != end_depot_idx:
        depots.append(Depot(x=coords[end_depot_idx][0], y=coords[end_depot_idx][1]))

    # Criar clientes opcionais (com prize)
    clients = []
    for idx in range(num_locs):
        if idx not in [start_depot_idx, end_depot_idx]:
            clients.append(Client(
                x=coords[idx][0],
                y=coords[idx][1],
                pickup=[demands[idx]],
                prize=prize[idx],
                service_duration=service[idx],
                required=False,  # ← ESSENCIAL para PCVRP
            ))

    # Tipo de veículo
    vehicle_types = [
        VehicleType(
            num_available=1,
            max_duration=420*PYVRP_SCALING_FACTOR,
            capacity=capacity,
            start_depot=start_depot_idx,
            end_depot=end_depot_idx,
        )
    ]

    # Verificação da matriz
    expected_size = num_locs
    if matrix.shape != (expected_size, expected_size):
        raise ValueError(f"Shape inconsistente: matriz {matrix.shape}, esperava {(expected_size, expected_size)}")

    # Debug info
    print("→ Matrix shape:", matrix.shape)
    print("→ Num clients:", len(clients))
    print("→ Num depots:", len(depots))
    print("→ Total demand:", sum(demands))
    print("Prize: ", prize)
    print("Demands: ", demands)
    print("→ Expected matrix size:", expected_size)
    print("OPAAAA", matrix)
    print("OLAAA", matrix_time)

    return ProblemData(clients, depots, vehicle_types, [matrix], [matrix_time])


def solution2action(solution: Solution) -> list[int]:
    """
    Converte uma solução do PyVRP para a representação de ações (tour gigante),
    incluindo explicitamente os índices de depósito inicial e final.
    """
    action = []
    
    for route in solution.routes():
        # Adicionar o depósito inicial
        action.append(route.start_depot())
        
        # Adicionar as visitas dos clientes
        action.extend(route.visits())
        
        # Adicionar o depósito final
        action.append(route.end_depot())
        
    return action


def solve(instance, max_runtime, **kwargs):
    data = instance2data(instance, PYVRP_SCALING_FACTOR)
    stop = MaxRuntime(max_runtime)
    result = _solve(data, stop, **kwargs) # A função de resolução retorna um Result
    solution = result.best # A melhor solução está no atributo 'best'
    cost = result.cost() / PYVRP_SCALING_FACTOR # Assumindo que 'cost' é um atributo da Solution
    #print("→ Prize total recolhido:", solution.prize())
    #print("→ Custo (distância total):", solution.cost())
    
    return solution, cost

@st.cache_data
def plot_solution(instance, solution):
    #import matplotlib.pyplot as plt

    coords = instance["coords"]
    start_depot = instance.get("start_depot_idx", 0)
    end_depot = instance.get("end_depot_idx", 1)
    routes = solution.routes()

    plt.figure(figsize=(10, 8))

    # Clientes
    xs, ys = zip(*coords)
    plt.scatter(xs, ys, c="gray", label="Clientes", zorder=2)

    # Depósitos
    plt.scatter(*coords[start_depot], c="green", s=100, marker="s", label="Depósito Início", zorder=3)
    if end_depot != start_depot:
        plt.scatter(*coords[end_depot], c="red", s=100, marker="X", label="Depósito Fim", zorder=3)

    # Desenhar rotas
    for route in routes:
        # Inserir depósito de início e fim
        full_route = [start_depot] + route.visits() + [end_depot]  # Use visits() para obter os índices dos clientes
        route_coords = [coords[i] for i in full_route]
        xs, ys = zip(*route_coords)
        plt.plot(xs, ys, marker="o", zorder=1)

    plt.title("Rotas com ligação aos depósitos")
    plt.legend()
    plt.grid(True)
    plt.axis("equal")
    plt.show()


def plot_large_folium_route(coords_start, coords_end, coords_sub, ors_api_key, start_depot_idx=0, end_depot_idx=1, levels_start=None, levels_end=None, levels_sub=None):
    # Se não for fornecido, o índice do depósito de fim é o último ponto da lista de coordenadas
    
    end_depot_idx_i = len(coords_start) - 1
    end_depot_idx_f = len(coords_end) - 1
    end_depot_idx_s = len(coords_sub) - 1

    client = openrouteservice.Client(key=ors_api_key)

    def split_coords(coords, max_size=40):
        # Divide as coordenadas em segmentos
        for i in range(0, len(coords) - 1, max_size - 1):
            yield coords[i:i + max_size]

    def get_full_route_geometry(coords):
        full_route = {
            "type": "FeatureCollection",
            "features": [],
        }

        for segment in split_coords(coords):
            result = client.directions(
                coordinates=segment,
                profile='driving-car',
                format='geojson'
            )
            full_route["features"].extend(result["features"])

        return full_route

    # Obter a geometria da rota para o início
    route_start = get_full_route_geometry(coords_start)
    # Obter a geometria da rota para o fim
    route_end = get_full_route_geometry(coords_end)
    route_sub= get_full_route_geometry(coords_sub)

    # Criar o mapa
    m = folium.Map(location=coords_start[start_depot_idx][::-1], zoom_start=13)

    # Criar grupos para a rota de início e fim
    route_start_group = folium.FeatureGroup(name="Início")
    route_end_group = folium.FeatureGroup(name="Fim")
    route_sub_group = folium.FeatureGroup(name="SubRota")

    # Adicionar a geometria da rota ao grupo "Início" com a cor laranja
    folium.GeoJson(
        route_start,
        name="Início",
        style_function=lambda feature: {
            'color': '#00cc44',  # Cor da linha da rota
            'weight': 4,        # Espessura da linha
            'opacity': 1        # Opacidade da linha
        }
    ).add_to(route_start_group)

    # Adicionar a geometria da rota ao grupo "Fim"
    folium.GeoJson(route_end, name="Fim").add_to(route_end_group)

    folium.GeoJson(
        route_sub,
        name="SubRota",
        style_function=lambda feature: {
            'color': '#D93E50',  # Cor da linha da rota
            'weight': 4,        # Espessura da linha
            'opacity': 1        # Opacidade da linha
        }
    ).add_to(route_sub_group)

    # Adicionar marcadores para os pontos de cada rota (separados para início e fim)
    # Marcadores para a rota "Início"
    for i, (lon, lat) in enumerate(coords_start):
        level = levels_start[i] if levels_start else "N/A"  # Nível para o ponto
        if i == start_depot_idx:
            folium.Marker(
                [lat, lon],
                icon=folium.Icon(color="green", icon="play"),
                tooltip=f"Estaleiro"
            ).add_to(route_start_group)
        elif i == end_depot_idx_i:
            folium.Marker(
                [lat, lon],
                icon=folium.Icon(color="red", icon="stop"),
                tooltip=f"TratoLixo"
            ).add_to(route_start_group)
        else:
            folium.CircleMarker(
                [lat, lon],
                radius=4,
                color="green",  # Cor dos pontos da rota de início
                fill=True,
                fill_color="green",  # Cor de preenchimento dos pontos
                fill_opacity=0.3,
                tooltip=f"Ponto {i}, Nível {level}"
            ).add_to(route_start_group)

    # Marcadores para a rota "Fim"
    for i, (lon, lat) in enumerate(coords_end):
        level = levels_end[i] if levels_end else "N/A"  # Nível para o ponto
        if i == start_depot_idx:
            folium.Marker(
                [lat, lon],
                icon=folium.Icon(color="green", icon="play"),
                tooltip=f"Estaleiro"
            ).add_to(route_end_group)
        elif i == end_depot_idx_f:
            folium.Marker(
                [lat, lon],
                icon=folium.Icon(color="red", icon="stop"),
                tooltip=f"TratoLixo"
            ).add_to(route_end_group)
        else:
            folium.CircleMarker(
                [lat, lon],
                radius=4,
                color="blue",  # Cor dos pontos da rota de fim
                fill=True,
                fill_color="blue",  # Cor de preenchimento dos pontos
                fill_opacity=0.6,
                tooltip=f"Ponto {i}, Nível {level}"
            ).add_to(route_end_group)

    #Marcadores para a subRota
    for i, (lon, lat) in enumerate(coords_sub):
        level = levels_sub[i] if levels_sub else "N/A"  # Nível para o ponto
        if i == start_depot_idx:
            folium.Marker(
                [lat, lon],
                icon=folium.Icon(color="green", icon="play"),
                tooltip=f"Estaleiro"
            ).add_to(route_sub_group)
        elif i == end_depot_idx_s:
            folium.Marker(
                [lat, lon],
                icon=folium.Icon(color="red", icon="stop"),
                tooltip=f"TratoLixo"
            ).add_to(route_sub_group)
        else:
            folium.CircleMarker(
                [lat, lon],
                radius=4,
                color="#A40517",  # Cor dos pontos da rota de sub
                fill=True,
                fill_color="#A40517",  # Cor de preenchimento dos pontos
                fill_opacity=0.3,
                tooltip=f"Ponto {i}, Nível {level}"
            ).add_to(route_sub_group)    

    # Adicionar os grupos ao mapa
    route_start_group.add_to(m)
    route_end_group.add_to(m)
    route_sub_group.add_to(m)

    # Adicionar o controle de layers para alternar entre as rotas
    folium.LayerControl().add_to(m)

    return m

st.markdown("""
    <style>
        /* Reduz margens horizontais da área principal */
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        /* Expande a largura da página */
        .main {
            max-width: 100% !important;
        }
    </style>
""", unsafe_allow_html=True)


ORS_API_KEY = "5b3ce3597851110001cf624882d5a1b8d3444c489b1b384e680e6093"
PYVRP_SCALING_FACTOR = 1_000_000
beta = 10
dist_scale = 20000


df=load_data(df)
circuitos=load_circuitos()
circuitos_matrizes_dist = carregar_matrizes_dist_dos_circuitos()
circuitos_matrizes_tempo = carregar_matrizes_tempo_dos_circuitos()


st.title("Solver - PyVRP")



# Obter lista de datas únicas disponíveis, já convertidas para `datetime.date`
datas_disponiveis = sorted(df['Data'].dt.date.unique())

# Verifica se há datas válidas para o usuário escolher
if datas_disponiveis:
    data_selecionada = st.date_input("Selecione a data:", value=datas_disponiveis[0], min_value=min(datas_disponiveis), max_value=max(datas_disponiveis))
    df_filtrado_por_data = df[df['Data'].dt.date == data_selecionada]

    #st.write("Dados filtrados para a data selecionada:")
    #st.dataframe(df_filtrado_por_data)
else:
    st.warning("Não foram encontradas datas válidas no DataFrame.")



#data_selecionada = st.date_input("Selecione a data:", value=datas_disponiveis[0].date())

# Filtrar o DataFrame com base na data selecionada
#df_filtrado_por_data = df[df['Data'] == pd.to_datetime(data_selecionada)]
df_filtrado_data = df[df['Data'].dt.date == data_selecionada]


# Obter os circuitos únicos para a data selecionada
circuitos_disponiveis = df_filtrado_por_data['Circuito'].unique()

# Criar o selectbox dos circuitos com as opções filtradas
circuito_escolhido = st.selectbox(
    "Selecione o circuito:",
    options=["Selecione o circuito"] + list(circuitos_disponiveis)
)

while circuito_escolhido == "Selecione o circuito":
    st.info("Por favor, selecione um circuito para continuar.")
    sleep(60)
 
    # Garantir que o circuito escolhido não seja vazio
    if circuito_escolhido != "Selecione o circuito":
        break

if circuito_escolhido in circuitos:
    pontos_do_circuito = circuitos[circuito_escolhido]
        # Aqui você pode processar `pontos_do_circuito` conforme necessário
else:
    st.warning("Circuito selecionado não encontrado.")




df_filtrado_circuito = df_filtrado_data[df_filtrado_data['Circuito'] == circuito_escolhido]

tipos_disponiveis = sorted(df_filtrado_circuito['Tipo'].dropna().unique())

tipo_escolhido = st.selectbox(
    "Selecione o tipo:",
    options=["Selecione o tipo"] + list(tipos_disponiveis)
)


while tipo_escolhido is "Selecione o tipo":
    st.info("Por favor, selecione um tipo para continuar.")
    sleep(60)
 
    # Garantir que o tipo escolhido não seja vazio
    if tipo_escolhido is not "Selecione o tipo":
        break


with st.spinner("A calcular rota..."):

    data=data_selecionada
    circuito=circuito_escolhido
    tipo=tipo_escolhido
    capacidade=120
    pontos_do_circuito = circuitos[circuito]

    demands_inicio = extrair_demands_inicio(df, data = data, circuito=circuito, tipo=tipo, pontos_do_circuito=pontos_do_circuito)
    #print("OLAAAA",demands_inicio)


    instance_inicio = construir_instance(
        circuito=circuito,
        pontos=pontos_do_circuito,
        matrizes_dist_dict=circuitos_matrizes_dist,
        matrizes_tempo_dict=circuitos_matrizes_tempo,
        demands=demands_inicio,
        capacidade=capacidade
    )


    solution_inicio, cost_inicio= solve(instance_inicio, max_runtime=10)
    #st.write("Custo de inicio (distância):", cost_inicio)

    actions_inicio = solution2action(solution_inicio)


    demands_fim = extrair_demands_fim(df, data= data, circuito=circuito, tipo=tipo, pontos_do_circuito=pontos_do_circuito)

    instance_fim = construir_instance(
        circuito=circuito,
        pontos=pontos_do_circuito,
        matrizes_dist_dict=circuitos_matrizes_dist,
        matrizes_tempo_dict=circuitos_matrizes_tempo,
        demands=demands_fim,
        capacidade=capacidade
    )

    solution_fim, cost_fim = solve(instance_fim, max_runtime=10)
    #st.write("Custo de fim (distância):", cost_fim)

    actions_fim = solution2action(solution_fim)


##VALIDADOR
variavel_fim=instance_fim["demands"]
circuito_esc_dist=circuitos_matrizes_dist[circuito]
circuito_esc_tempo=circuitos_matrizes_tempo[circuito]
circuito_esc_tempo.index = circuito_esc_tempo.index.astype(int)
circuito_esc_tempo.columns = circuito_esc_tempo.columns.astype(int)
circuito_esc_dist.index = circuito_esc_dist.index.astype(int)
circuito_esc_dist.columns = circuito_esc_dist.columns.astype(int)
service_time = 5
sub_rota = [actions_inicio[0]]  # incluir o depósito inicial
tempo = 0
dist = 0
curr_load = 0
cap = 120

for k in range(1, len(actions_inicio)-1):
    serv_ant = actions_inicio[k - 1]
    serv = actions_inicio[k]
    #print(serv)
    demanda = variavel_fim[serv]
    print("O ponto é", serv)
    print("A sua demanda é", demanda)

    print(f"curr_load: {curr_load} ({type(curr_load)})")
    print(f"demanda: {demanda} ({type(demanda)})")
    print(f"capacidade: {cap} ({type(cap)})")
    print(f"soma: {curr_load + demanda}")
    print(f"Condição: {curr_load + demanda <= cap}")
    if curr_load + demanda <= cap:
        curr_load += demanda
        sub_rota.append(serv)
        tempo += circuito_esc_tempo.iloc[serv_ant, serv]
        tempo += service_time
        dist += circuito_esc_dist.iloc[serv_ant, serv]
            
            
    else:
        print("AAAAAA",curr_load)
        carga_possivel = cap - curr_load

        if carga_possivel > 0:
            print("A carga é",carga_possivel)
            curr_load += carga_possivel
            variavel_fim[serv] -= carga_possivel
            ficou = variavel_fim[serv]
            #sub_rota.append(serv)
            tempo += circuito_esc_tempo.iloc[serv_ant, serv]
            tempo += service_time
            dist += circuito_esc_dist.iloc[serv_ant, serv]
            break
# Finaliza a rota
sub_rota.append(actions_inicio[-1])
tempo += circuito_esc_tempo.iloc[serv, actions_inicio[-1]]
dist += circuito_esc_dist.iloc[serv, actions_inicio[-1]]

numclientes=len(sub_rota) -2
prizes_un=sum(variavel_fim)-curr_load
prizes_rec=curr_load

###FIM VALIDADOR


levels_start=[instance_inicio["demands"][i] for i in actions_inicio]
levels_end=[instance_fim["demands"][i] for i in actions_fim]
levels_sub=[instance_fim["demands"][i] for i in sub_rota]

coords_start = [instance_inicio["coords"][i] for i in actions_inicio]
coords_end = [instance_fim["coords"][i] for i in actions_fim]
coords_sub= [instance_inicio["coords"][i] for i in sub_rota]

mapa = plot_large_folium_route(coords_start, coords_end, coords_sub, ORS_API_KEY, levels_start=levels_start, levels_end=levels_end, levels_sub=levels_sub)
folium_static(mapa, width=800, height=600)

st.markdown(f"### Nº de Pontos do {circuito_escolhido} - {len(pontos_do_circuito) - 2}")


col1, spacer1, col2, spacer2, col3 = st.columns([3, 0.5, 3, 0.5, 3])

#st.markdown(f"### ✅ Nº de Pontos do ", circuito_escolhido, ":", {len(pontos_do_circuito) - 2})

dist_i= solution_inicio.distance() / PYVRP_SCALING_FACTOR * dist_scale
tempo_i=solution_inicio.duration() / PYVRP_SCALING_FACTOR
clientes_i=solution_inicio.num_clients()
aaa=solution_inicio.prizes()*sum(demands_inicio)/ (beta * PYVRP_SCALING_FACTOR)
ocupacao_camiao_inicio=capacidade-(capacidade-aaa)
lixo_nao_i=solution_inicio.uncollected_prizes()*sum(demands_inicio) / (beta*PYVRP_SCALING_FACTOR)

dist_f= solution_fim.distance() / PYVRP_SCALING_FACTOR * dist_scale
tempo_f=solution_fim.duration() / PYVRP_SCALING_FACTOR
clientes_f=solution_fim.num_clients()
bbb=solution_fim.prizes()*sum(demands_fim) / (beta*PYVRP_SCALING_FACTOR)
ocupacao_camiao_fim=capacidade-(capacidade-bbb)
lixo_nao_f=solution_fim.uncollected_prizes()*sum(demands_fim) / (beta*PYVRP_SCALING_FACTOR)

with col1:
    st.subheader("Rota de Início")
    st.write("📏 Distância:", f"{dist_i / 1000:.2f} km")
    st.write("🕒 Duração:", f"{round(tempo_i)} minutos")
    st.write(f"📍 Pontos visitados: {clientes_i}")
    st.write(f"🗑️ Quantidade de lixo não recolhido: {round(lixo_nao_i)}")
    st.write(f"🚛 Ocupação total do camião: {round(ocupacao_camiao_inicio)}")

with col2:
    st.subheader("Rota de Fim")
    st.write("📏 Distância:", f"{dist_f / 1000:.2f} km")
    st.write("🕒 Duração:", f"{round(tempo_f)} minutos")
    st.write(f"📍 Pontos visitados: {clientes_f}")
    st.write(f"🗑️ Quantidade de lixo não recolhido: {round(lixo_nao_f)}")
    st.write(f"🚛 Ocupação total do camião: {round(ocupacao_camiao_fim)}")

with col3:
    st.subheader("Sub Rota")
    st.write("📏 Distância:", f"{dist / 1000:.2f} km")
    st.write("🕒 Duração:", f"{round(tempo)} minutos")
    st.write(f"📍 Pontos visitados: {numclientes}")
    st.write(f"🗑️ Quantidade de lixo não recolhido: {round(prizes_un)}")
    st.write(f"🚛 Ocupação total do camião: {round(prizes_rec)}")

st.markdown("""
> ℹ️ **Nota:** O objetivo do solver é recolher o maior número de pontos enquanto otimiza a distância percorrida e a quantidade de lixo não recolhido com base na capacidade do camião, que está limitada a **120 unidades**.  
> Ao selecionar os pontos para compor a rota, o algoritmo tenta **minimizar a distancia e o lixo não recolhido** — mas a ordem de recolha desses pontos **não depende do nível**.
""")