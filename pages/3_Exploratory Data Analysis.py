#----- Bibliotecas nescessárias para transformação e charts
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import calendar

#----- Configurações da página
st.set_page_config(
    page_title="Dashboard",
    layout="wide"
)
#----- color pallettes
cmap_4ptop = ["#9381ff", "#b8b8ff", "#ffeedd", "#ffd8be"]

#----- Carregando DataFrames nescessários
dict_dfs = st.session_state["data"]

df_channels = dict_dfs["channels"].copy()
df_deliveries = dict_dfs["deliveries"].copy()
df_drivers = dict_dfs["drivers"].copy()
df_hubs = dict_dfs["hubs"].copy()
df_orders = dict_dfs["orders"].copy()
df_payments = dict_dfs["payments"].copy()
df_stores = dict_dfs["stores"].copy()

#----- flat de dados
orders = df_stores.merge(df_hubs, on='hub_id')
orders = orders.merge(df_orders, on='store_id')
orders = orders.merge(df_payments, on='payment_order_id', how='left')

filtered_orders = orders.copy()

#-----
    # Analisando as informações disponíveis
        ## Crescimento de Número de Pedidos
n_pedidos = pd.DataFrame(df_orders.groupby("order_created_month")["order_id"].nunique())
n_pedidos["n_mes"] = n_pedidos.index
n_pedidos["MÊS"] = n_pedidos["n_mes"].apply(lambda x: calendar.month_name[x])
f_qntd_pedidos = go.Figure(data=go.Scatter(
    x=n_pedidos["MÊS"],
    y=n_pedidos["order_id"],
    text=n_pedidos["order_id"],
    textposition="top right",
    marker=dict(color='#5D69B1', size=8),
                  line=dict(color='#52BCA3', width=1)
))
f_qntd_pedidos.update_yaxes(rangemode="tozero")
f_qntd_pedidos.update_layout(title="Número de Pedidos em 2021")

        ## Crescimento do Lucro ao mês
            ### Delivery Center get 15% of the total order amount paid by the costumer
filtered_orders["profit_percent_order_amount"]=.15 * filtered_orders["order_amount"]
            ### generating the total profit of plan price paid by the stores monthly
stores_month_year = filtered_orders[["order_created_year",
                                     "order_created_month",
                                     "store_id"]].copy()
grouped_stores_month_year = pd.DataFrame(
    stores_month_year.groupby(["order_created_year",
                               "order_created_month", "store_id"]).nunique())
total_host = []
for i in range(1,5):
    monthly_hosted = grouped_stores_month_year[grouped_stores_month_year.index.get_level_values(1).isin([i])]
    total_host.append(df_stores.merge(monthly_hosted,
                                             on="store_id")["store_plan_price"].sum())
            ### Receita Total da Operação
filtered_orders["RECEITA BRUTA"] = filtered_orders["profit_percent_order_amount"] + filtered_orders["order_delivery_fee"]
            ### Delivery Center profit of delivery fee and cost 
filtered_orders["order_delivery_spread"] = filtered_orders["order_delivery_fee"] - filtered_orders["order_delivery_cost"]
            ### Operational profit before taxes
filtered_orders["order_delivery_cost"].fillna(0,inplace=True)
filtered_orders["taxable_op_profit"] = filtered_orders["profit_percent_order_amount"] + filtered_orders["order_delivery_fee"] - filtered_orders["order_delivery_cost"]
filtered_orders["taxable_op_profit"] = filtered_orders["taxable_op_profit"].apply(lambda x: x-5)
            ### Tax paid by delivery
filtered_orders["total_tax"] = filtered_orders["taxable_op_profit"].apply(lambda x: 0 if x<0 else -.27*x)
            ### operational profit
filtered_orders["profit_aftTaxes"] = filtered_orders["taxable_op_profit"]+filtered_orders["total_tax"]
opProfit_month = pd.DataFrame(filtered_orders.groupby("order_created_month")["profit_aftTaxes"].sum())
opProfit_month["host_price"]  = total_host
opProfit_month["Operational Profit"] = opProfit_month["host_price"] + opProfit_month["profit_aftTaxes"]

f_bar_monthprofit = go.Figure(data=go.Bar(
    x=n_pedidos["MÊS"],
    y=opProfit_month["Operational Profit"],
    marker_color= cmap_4ptop
))
f_bar_monthprofit.update_layout(title="Lucro Operacional Mensal")

####------ Markdown ----------------------------------------------------------------------------------
st.title("Análise Exploratória de Dados")
st.subheader("Explorando a performance econômica")
st.markdown("""
Com o objetivo de identificar potenciais problemas de rentabilidade e gerar insights aos stakeholders interessados, há uma análise exploratória das informações disponibilizadas pelo banco de dados responsável com o seguinte modelo relacional: Apesar de termos as informações de cada pedido, fornecedor e entregador separados por região e hub, os dados devem ser devidamente tratados e ainda precisamos calcular o lucro da operação. 
""")
st.image("https://api-club-file.cb.hotmart.com/public/v5/files/1b61c3c1-846f-4037-9e48-9277f551f429")
st.markdown("""
Observe que apesar de termos as informações de cada pedido, fornecedor e entregador separados por região e hub, os dados devem ser devidamente tratados e ainda precisamos calcular as receitas e custos operacionais para saber o lucro gerencial da operação. 
""")
st.plotly_chart(f_qntd_pedidos)
st.plotly_chart(f_bar_monthprofit)
