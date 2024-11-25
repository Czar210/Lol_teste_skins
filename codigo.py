import streamlit as st
import pandas as pd
import math
import os

# Arquivos do jogo
game_state_file = "skin_game_state.csv"
game_history_file = "game_history.csv"
champion_data = pd.read_csv('champion_data.csv')

# Configurações iniciais
if not os.path.exists(game_state_file):
    initial_state = {
        "seasonality": [50000],
        "round": [1],
        "champion_saturation": champion_data["Saturação"].tolist()
    }
    pd.DataFrame(initial_state).to_csv(game_state_file, index=False)

if not os.path.exists(game_history_file):
    pd.DataFrame(columns=["round", "total_sales", "net_profit", "new_seasonality"]).to_csv(game_history_file, index=False)

# Carregar estado do jogo
game_state = pd.read_csv(game_state_file)
current_seasonality = game_state["seasonality"].iloc[-1]
current_round = game_state["round"].iloc[-1]
champion_data["Saturação"] = game_state["champion_saturation"]
current_seasonality = 50000

# Interface do jogo
st.title("Gerenciador de Produção de Skins")

# Regras do jogo
st.sidebar.header("Regras do Jogo")
st.sidebar.markdown("""
- **Budget inicial**: Preencha o orçamento inicial disponível para gastar na produção e marketing.
- **Número de skins a serem produzidas**: Escolha quantas skins serão desenvolvidas.
- **Nome da linha de skins**: Dê um nome à sua coleção de skins.
- **Valor do tema (1-5)**: Popularidade do tema escolhido:
    - 1: Baixo investimento (ex: Infernal).
    - 5: Altíssimo investimento (ex: Soul Fighter, Star Guardian).
- **Valor de marketing**: Quantidade do orçamento destinada ao marketing.
- **Campeão**: Escolha o campeão que receberá a skin.
- **Tier da skin**: Raridade da skin, impactando preço e custo:
    - 1: 520 RP
    - 2: 750 RP
    - 3: 975 RP
    - 4: 1350 RP
    - 5: 1820 RP
    - 6: 3250 RP
    - 7: 5430 RP
    - 8: 32430 RP
- **Variáveis invisíveis**:
    - Popularidade (pick rate): Influencia vendas.
    - Saturação: Campeões com muitas skins recentes têm vendas reduzidas.
    - Sazonalidade: Impacta a receptividade geral da linha nas rodadas futuras.
""")

st.sidebar.header(f"Configurações Iniciais (Rodada {current_round})")

# Inputs
budget = st.sidebar.number_input("Budget inicial:", min_value=1000, value=10000, step=100)
num_skins = st.sidebar.number_input("Número de skins a serem produzidas:", min_value=1, value=3, step=1)
skin_line_name = st.sidebar.text_input("Nome da linha de skins:", value="Minha Linha de Skins")
theme_value = st.sidebar.slider("Valor do tema (1-5):", min_value=1, max_value=5, value=3)
marketing_investment = st.sidebar.number_input("Valor de marketing:", min_value=0, max_value=budget, value=0)

# Configuração de Skins
st.header("Configuração das Skins")
tier_production_costs = [1000, 2000, 4000, 8000, 16000, 30000, 60000, 150000]
total_production_cost = 0
skin_choices = []

for i in range(num_skins):
    st.subheader(f"Skin {i + 1}")
    champ = st.selectbox(f"Escolha o campeão para a Skin {i + 1}:", champion_data["Campeões"], key=f"champ_{i}")
    tier = st.slider(f"Tier da Skin {i + 1} (1-8):", min_value=1, max_value=8, value=1, key=f"tier_{i}")
    skin_choices.append({"champion": champ, "tier": tier})
    total_production_cost += tier_production_costs[tier - 1]

# Exibir total de gastos
total_expenses = total_production_cost + marketing_investment
st.sidebar.subheader(f"Gasto Total Planejado: ${total_expenses}")
if total_expenses > budget:
    st.sidebar.error("Cuidado: Gastos excedem o budget!")

# Botão para finalizar
if st.button("Finalizar Escolhas e Calcular Vendas"):
    if total_expenses > budget:
        st.error("Os gastos totais excedem o budget! Ajuste o número de skins, tiers ou marketing.")
    else:
        st.header("Resultados")
        total_sales = 0
        for choice in skin_choices:
            champ_name = choice["champion"]
            tier = choice["tier"]

            champ_data = champion_data[champion_data["Campeões"] == champ_name].iloc[0]
            pick_rate = champ_data["Pick Rate(%)"]
            saturation = champ_data["Saturação"]

            tier_prices = [104, 150, 195, 270, 364, 650, 1086, 6486]
            price = tier_prices[tier - 1] * 6

            sales_multiplier = (1 - math.log1p(saturation) * 0.5) * (1 + math.log1p(theme_value) * 1.2) * pick_rate
            sales = price * sales_multiplier
            sales = min(sales, current_seasonality + marketing_investment * 0.3)
            total_sales += sales * 5

            new_saturation = saturation + tier * 0.1
            champion_data.loc[champion_data["Campeões"] == champ_name, "Saturação"] = new_saturation

        marketing_boost = math.log1p(marketing_investment) * 1.5
        total_sales *= (1 + marketing_boost) * 2
        net_profit = (total_sales - total_expenses) 
        new_seasonality = current_seasonality + marketing_investment * 0.1 - net_profit * 0.05

        # Atualizar estado
        game_state = pd.DataFrame({
            "seasonality": [new_seasonality] * len(champion_data),
            "round": [current_round + 1] * len(champion_data),
            "champion_saturation": champion_data["Saturação"].tolist()
        })
        game_state.to_csv(game_state_file, mode="a", header=False, index=False)

        # Atualizar histórico
        history_data = pd.DataFrame({
            "round": [current_round],
            "total_sales": [total_sales],
            "net_profit": [net_profit],
            "new_seasonality": [new_seasonality]
        })
        history_data.to_csv(game_history_file, mode="a", header=False, index=False)

        st.subheader(f"Total de Vendas Estimadas: ${total_sales:.2f}")
        st.subheader(f"Lucro Líquido: ${net_profit:.2f}")
        st.write(f"Sazonalidade Atualizada: {new_seasonality:.2f}")
        st.success(f"Rodada {current_round} concluída! Atualize a página para iniciar a próxima rodada.")

# Exibir histórico
if os.path.exists(game_history_file):
    game_history = pd.read_csv(game_history_file)
    st.header("Histórico de Rodadas")
    st.table(game_history)
else:
    st.write("Ainda não há histórico de rodadas.")

# Exibir Pick Rate dos Campeões
st.header("Tabela de Pick Rate dos Campeões")
st.table(champion_data[["Campeões", "Pick Rate(%)", "Saturação"]])
