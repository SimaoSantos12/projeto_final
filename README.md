# 🗑️ Otimização de Rotas de Recolha de Lixo

Este repositório contém o projeto de final de curso de **Engenharia Informática e Telecomunicações**, desenvolvido na **Escola Superior de Tecnologia e Gestão de Lamego** 

## 📋 Descrição

Este projeto tem como objetivo otimizar as rotas de recolha de resíduos sólidos urbanos no município de Cascais, de forma a melhorar a eficiência logística e reduzir o impacto ambiental.

A solução proposta baseia-se em três pilares fundamentais:
1. **Análise de Dados Reais** dos contentores e recolhas.
2. **Modelação Preditiva** dos níveis de enchimento usando Machine Learning.
3. **Otimização de Rotas** com recurso ao **solver PyVRP**.

## 📊 Principais Funcionalidades

- Previsão dos níveis de enchimento dos contentores (papel, embalagens, vidro).
- Otimização de rotas com base em previsões.
- Comparação entre diferentes abordagens (rotas reais vs. preditivas).
- Visualização de resultados através de **dashboards interativos**.
- Cálculo de indicadores como:
  - Quantidade de lixo não recolhido.
  - Distância percorrida.
  - Eficiência das rotas geradas.

## 🧠 Técnicas e Tecnologias

- **Linguagens**: Python
- **Bibliotecas**:
  - `scikit-learn` (Modelos Preditivos)
  - `pandas`, `numpy` (Tratamento de Dados)
  - `matplotlib`, `seaborn` (Visualização)
  - `folium`, `plotly`, `dash` (Dashboard interativo)
  - `PyVRP` (Solver para Vehicle Routing Problem)

## ⚙️ Estrutura do Projeto

📁 data/ # Dados fornecidos pelo município
📁 notebooks/ # Cadernos de análise e desenvolvimento
📁 src/ # Código-fonte modularizado
📁 dashboard/ # Aplicação de visualização dos dados
📄 requirements.txt # Dependências do projeto
📄 README.md # Este ficheiro


## 🔍 Resultados

- O modelo **HistGradientBoostingRegressor** foi o que apresentou melhor desempenho preditivo.
- A utilização das previsões do modelo resultou em:
  - Redução de 3,19% de lixo não recolhido.
  - Redução de cerca de 400 metros em média por rota.
- As **sub-rotas otimizadas** com previsões foram mais eficazes do que aquelas baseadas em médias históricas.

## 📈 Dashboard

Foi desenvolvido um **dashboard interativo** com os seguintes módulos:
- Análise de dados históricos.
- Visualização geográfica dos circuitos.
- Evolução temporal dos níveis de enchimento.
- Comparação entre rotas reais e otimizadas.


## 👨‍💻 Autor

Simão Costa Santos – Nº 25766  
Licenciatura em Engenharia Informática e Telecomunicações  
[ESTGL - Escola Superior de Tecnologia e Gestão de Lamego](https://www.estgl.ipv.pt)

