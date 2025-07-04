import streamlit as st

# Definir o título da página
#st.set_page_config(page_title="Gestão de Resíduos - Cascais", layout="wide")

# Título principal
st.title("Aprendizagem por reforço para otimização de rotas de recolha de lixo")

# Introdução geral
st.markdown("""
Bem-vindo à aplicação desenvolvida para otimizar a **recolha de resíduos baseada em dados do município de Cascais**.  
Esta ferramenta integra várias componentes analíticas e operacionais que ajudam a compreender, planear e simular as operações de recolha de lixo de forma mais eficiente.

---

##  Módulos da Aplicação
""")
st.write("")
# Analise de Dados
st.subheader("📊 1. Análise de Dados")
st.markdown("""
Neste módulo é apresentada uma amostra da análise exploratória realizada sobre os dados reais de recolha de resíduos em Cascais.  
São explorados padrões de enchimento, frequências de recolha e intervalos de recolha para os pontos dos vários circuitos.
""")

st.write("")
# Visualização das Rotas
st.subheader("🗺️ 2. Visualização das Rotas Reais")
st.markdown("""
Com base nos dados históricos, mostramos as rotas que os camiões de recolha realizaram.  
Esta visualização permite perceber a cobertura geográfica, os pontos em que as rotas passaram e possíveis ineficiências nos trajetos.
""")

st.write("")
# Solver com PyVRP
st.subheader("🧠 3. Otimização de Rotas (Solver)")
st.markdown("""
Usando o **PyVRP**, um solver especializado para problemas de rotas com veículos, são geradas novas rotas otimizadas em distância e quantidade de lixo não recolhida.  
Estas rotas são baseadas em dados organizados previamente, tendo em conta restrições reais como capacidade dos camiões e tempo de trabalho.
""")

st.write("")
# Simulador
#st.subheader("🧪 4. Simulador de Enchimento e Recolha")
#st.markdown("""
#Este módulo permite simular diferentes cenários de enchimento dos contentores.  
#Com base nesses níveis, é gerada uma rota recomendada de recolha para maximizar a eficiência e reduzir custos.
#""")

# Rodapé
st.markdown("---")
st.info("Navege pelos menus laterais para explorar cada módulo da aplicação.")
