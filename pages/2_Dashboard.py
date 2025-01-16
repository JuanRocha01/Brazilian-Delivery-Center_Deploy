#----- Bibliotecas nescessárias para transformação e charts
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from calendar import monthrange

#----- Configurações da página
st.set_page_config(
    page_title="Dashboard",
    layout="wide"
)

#----- Carregando DataFrames nescessários
dict_dfs = st.session_state["data"]

df_channels = dict_dfs["channels"].copy()
df_deliveries = dict_dfs["deliveries"].copy()
df_drivers = dict_dfs["drivers"].copy()
df_hubs = dict_dfs["hubs"].copy()
df_orders = dict_dfs["orders"].copy()
df_payments = dict_dfs["payments"].copy()
df_stores = dict_dfs["stores"].copy()

#----- Limpeza de dados e colunas desnecessários

#----- Sidebar com filtros para o Dashboard
anos = df_orders["order_created_year"].unique()
ano = st.sidebar.multiselect("Ano de Análise", anos, default=anos)

meses = df_orders["order_created_month"].unique()
mes = st.sidebar.selectbox("Mês de Análise",meses)

estados = df_hubs["hub_state"].unique()
estado = st.sidebar.multiselect("Estado(s)",estados, default=estados)

produtos = df_stores["store_segment"].unique()
produto = st.sidebar.multiselect("Produtos de Interesse",produtos, default=produtos)

#----- Construindo a Flat de dados
orders = df_stores.merge(df_hubs, on='hub_id')
orders = orders.merge(df_orders, on='store_id')
orders = orders.merge(df_payments, on='payment_order_id', how='left')

#----- Constantes importantes utilizadas para cálculo

total_days = monthrange(ano[0],mes)[1]
#----- DataFrame para construção dinâmica dos charts
filtered_orders = orders[(orders["order_created_year"].isin(ano)) &
                         (orders["order_created_month"] == mes) &
                         (orders["hub_state"].isin(estado)) &
                         (orders["store_segment"].isin(produto))].copy()

#----- Charts
## 1- Total of orders
### variables
qntd_orders = len(filtered_orders)
mean_orders = qntd_orders/total_days


## 9- waterfall chart of profit components
### variables
#### dict used to create the graph
dict_profit_components = {}
#### Delivery Center get 15% of the total order amount paid by the costumer
filtered_orders["profit_percent_order_amount"]=.15 * filtered_orders["order_amount"]
dict_profit_components["Receita Percentual do Pedido"] = filtered_orders["profit_percent_order_amount"].sum()
#### generating the total profit of plan price paid by the stores
stores_month_year = filtered_orders[["order_created_year",
                                     "order_created_month",
                                     "store_id"]].copy()
grouped_stores_month_year = pd.DataFrame(
    stores_month_year.groupby(["order_created_year",
                               "order_created_month", "store_id"]).nunique())
total_host = grouped_stores_month_year.merge(df_stores,
                                             on="store_id")["store_plan_price"].sum()
dict_profit_components["Receita de Hospedagem do Logista"] = total_host
#### Delivery Center profit of delivery fee 
dict_profit_components["Receita de Taxa de Entrega"] = filtered_orders["order_delivery_fee"].sum()
#### Receita Total da Operação
filtered_orders["RECEITA BRUTA"] = filtered_orders["profit_percent_order_amount"] + filtered_orders["order_delivery_fee"]
dict_profit_components["RECEITA BRUTA"] = sum(
    (dict_profit_components["Receita de Hospedagem do Logista"], dict_profit_components["Receita Percentual do Pedido"], dict_profit_components["Receita de Taxa de Entrega"]))
#### Custo de Entrega é fixo em $5
dict_profit_components["Custo de Entrega"] = -5*len(filtered_orders)
#### Custo de entregador
dict_profit_components["Custo com Entregadores"] = -filtered_orders["order_delivery_cost"].sum()
#### Impostos calculados ficticiamente por uma regra
filtered_orders["order_delivery_cost"].fillna(0,inplace=True)
filtered_orders["taxable_op_profit"] = filtered_orders["profit_percent_order_amount"] + filtered_orders["order_delivery_fee"] - filtered_orders["order_delivery_cost"]
filtered_orders["taxable_op_profit"] = filtered_orders["taxable_op_profit"].apply(lambda x: x-5)
filtered_orders["total_tax"] = filtered_orders["taxable_op_profit"].apply(lambda x: 0 if x<0 else -.27*x)
dict_profit_components["Total em Impostos"] = filtered_orders["total_tax"].sum()
#### Lucro operacional
filtered_orders["profit_aftTaxes"] = filtered_orders["taxable_op_profit"]+filtered_orders["total_tax"]

dict_profit_components["LUCRO OPERACIONAL"] = sum((dict_profit_components["RECEITA BRUTA"], dict_profit_components["Custo de Entrega"], dict_profit_components["Custo com Entregadores"], dict_profit_components["Total em Impostos"]))

## 2- Total Operational Profit
nopat = dict_profit_components["LUCRO OPERACIONAL"]
## 3- Total Operational Cost
op_costs = sum((dict_profit_components["Custo com Entregadores"], dict_profit_components["Custo de Entrega"]))
## 4- pie chart with delivered and cancelled orders
cancelled_orders = filtered_orders["order_status"].value_counts()

## 5 - Quantidade de pedidos com o percentual dos hubs responsáveis



## 6- bar chart of profit by hub

df_hospedag = grouped_stores_month_year.merge(df_stores,
                                             on="store_id")[["hub_id","store_plan_price"]]
hosp_hub = df_hospedag.groupby("hub_id").sum()
hosp_hub = hosp_hub.merge(df_hubs, on="hub_id")

df_hub_profit = filtered_orders[["hub_name",
                                 "profit_aftTaxes"]].copy()
hub_profit = df_hub_profit.groupby("hub_name").sum()
hub_profit = hub_profit.merge(hosp_hub, on="hub_name")
hub_profit["lucro_hub"] = hub_profit["profit_aftTaxes"] + hub_profit["store_plan_price"]

hub_profit = hub_profit.set_index("hub_name")

hub_lucrativo = hub_profit[hub_profit["lucro_hub"]>0]["lucro_hub"].sort_values(ascending=False).copy()
hub_prejuizo = -hub_profit[hub_profit["lucro_hub"]<=0]["lucro_hub"].sort_values(ascending=True).copy()

if len(hub_lucrativo)>3:
    y_lucro_hub = hub_lucrativo.iloc[0:3].copy()
    y_lucro_hub.loc["RESTANTE"] = hub_lucrativo.iloc[3:].sum()
else:
    y_lucro_hub = hub_lucrativo.copy()

if len(hub_prejuizo)>3:
    y_prejuizo_hub = -hub_prejuizo.iloc[0:3].copy()
    y_prejuizo_hub.loc["RESTANTE"] = -hub_prejuizo.iloc[3:].sum()
else:
    y_prejuizo_hub = -hub_prejuizo.copy()

## 7- TKM by city

df_ticket_medio = filtered_orders[["hub_city",
                                   "store_segment",
                                   "RECEITA BRUTA"]].copy()
by_city_TKM_count = df_ticket_medio.groupby(["hub_city","store_segment"],observed=False).count().copy()
by_city_TKM_sum = df_ticket_medio.groupby(["hub_city","store_segment"], observed=False).sum().copy()
by_city_TKM = by_city_TKM_sum / by_city_TKM_count


## 8- vertical bar chart of mean time by city

df_tempos_movimentos = filtered_orders[["hub_city",
                                 "prod_time",
                                 "idle_time",
                                 "deli_time"]].copy()
city_tempo_mov_sum = df_tempos_movimentos.groupby("hub_city", observed=False).sum()
city_tempo_mov_count = df_tempos_movimentos.groupby("hub_city", observed=False).count()
city_tempo_mov = city_tempo_mov_sum / city_tempo_mov_count

## 9- horizontal bar chart of mean-cycle of order by city

#----- CHARTS
### 1.
### 2.
### 3.
### 4. pie chart with cancelled and finished orders

blue_red = ["darkblue", "#8B0000"]
pie_canceledorders = go.Figure(
    data=[go.Pie(
        labels=cancelled_orders.index,
        values=cancelled_orders,
        hole=.4,
        pull=[0,.2],
        marker=dict(colors=blue_red)
    )])
pie_canceledorders.update_layout(title=dict(
        text="Relação de Pedidos Entregues"))


### 5. 

### 6.
green_pallet = ["#007542", "#3AA346", "#78D23D", "#ded9ba"] 
red_pallet = [ '#8B0000', '#FF2400', '#FF4433',"#ded9ba"]

hub_p_nopat = pd.DataFrame(
    {
        "LUCRO": list("1") * len(y_lucro_hub),
        "hubs": y_lucro_hub,
        "colors": green_pallet[0:len(y_lucro_hub)]
    }
)
hub_n_nopat = pd.DataFrame(
    {
        "PREJUÍZO": list("1") * len(y_prejuizo_hub),
        "hub": y_prejuizo_hub,
        "colors": red_pallet[0:len(y_prejuizo_hub)] 
    }
)
bars_hub_lucro=[]
k=0
hubs_lucrativos = pd.DataFrame(y_lucro_hub)
for i in hubs_lucrativos.index:
    bars_hub_lucro.append(
        go.Bar(
          name=i,
          x= ['LUCRO'],
          y= hubs_lucrativos.loc[i],
          marker=dict(color=green_pallet[k]),
          text=f"{i}"
          #text=f"${round(hubs_lucrativos.loc[i,"lucro_hub"]/1000,2)}k ({round(100*hubs_lucrativos.loc[i,"lucro_hub"]/hubs_lucrativos["lucro_hub"].sum())}%), {i}"
        )
    )
    k=k+1
hub_prejuizo = pd.DataFrame(-y_prejuizo_hub)
bars_hub_prej=[]
k=0
for i in hub_prejuizo.index:
    bars_hub_prej.append(
        go.Bar(
          name=i,
          x= ['PREJUIZO'],
          y= hub_prejuizo.loc[i],
          marker=dict(color=red_pallet[k]),
          text=f"{i}"
          #text=f"${round(hub_prejuizo.loc[i,"lucro_hub"]/1000,2)}k ({round(100*hub_prejuizo.loc[i,"lucro_hub"]/hub_prejuizo["lucro_hub"].sum())}%), {i}"
        )
    )
    k=k+1
bar_lucro = go.Figure(data=bars_hub_lucro)
bar_preju = go.Figure(data=bars_hub_prej)
bar_proft_hubs = go.Figure(data=bar_lucro.data+bar_preju.data)
bar_proft_hubs.update_layout(barmode='stack', title=dict(
        text="Lucro Por HUB"), showlegend=False)
#st.plotly_chart(bar_proft_hubs)

### 7. Bar chart of TKM by city
bars_TKM = go.Figure(data=[
    go.Bar(name=by_city_TKM.index.get_level_values(1).unique()[0],
           x=by_city_TKM.index.get_level_values(0).unique(),
           y=by_city_TKM.query("store_segment == 'FOOD'")["RECEITA BRUTA"],
           marker=dict(color="#8B0000")),
    
    go.Bar(name=by_city_TKM.index.get_level_values(1).unique()[1],
           x=by_city_TKM.index.get_level_values(0).unique(),
           y=by_city_TKM.query("store_segment == 'GOOD'")["RECEITA BRUTA"],
           marker=dict(color='#FF2400'))
    ])
bars_TKM.update_layout(title=dict(text="Ticket Médio por Cidade"))
#st.plotly_chart(bars_TKM)


### 8.
prod_min = (-city_tempo_mov["prod_time"].apply(lambda x: x.total_seconds())//60)
deli_min = (city_tempo_mov["deli_time"].apply(lambda x: x.total_seconds())//60)
idle_min = (city_tempo_mov["idle_time"].apply(lambda x: x.total_seconds())//60)
deli_min = deli_min + idle_min
deli_min.fillna(0)
prod_min.fillna(0)
prod_time = prod_min.apply(lambda x: f"{x}min")
deli_time = deli_min.apply(lambda x: f"{x}min")
bars_mean_time_city = go.Figure(data=[
    go.Bar(
        name = "Tempo de Produção",
        y=city_tempo_mov.index,
        x=city_tempo_mov["prod_time"],
        orientation='h',
        marker=dict(color="palegreen"),
        offsetgroup=0,
        textposition = "auto",
        text=prod_time
        ),
    go.Bar(
        name = "Tempo de Espera",
        y=city_tempo_mov.index,
        x=city_tempo_mov["idle_time"],
        orientation='h',
        marker=dict(color='papayawhip'),
        offsetgroup=0,
        base=0
        ),
    go.Bar(
        name = "Tempo de Entrega",
        y=city_tempo_mov.index,
        x=city_tempo_mov["deli_time"],
        orientation='h',
        offsetgroup=0,
        marker=dict(color='peachpuff'),
        base=city_tempo_mov["idle_time"],
        text=deli_time,
        textposition = "auto"
        )
    ])
bars_mean_time_city.update_xaxes(visible=False)
bars_mean_time_city.add_vline(x=0, line_width=2, line_dash='dash',
                        line_color="gray", opacity=.5)
bars_mean_time_city.update_layout(title="Tempo Médio de Espera pelo Usuário")
#st.plotly_chart(bars_mean_time_city)

### 9. Waterfall Chart
dict_profit_relative = dict_profit_components.copy()
dict_profit_relative["RECEITA BRUTA"] = 0
dict_profit_relative["LUCRO OPERACIONAL"] = 0
measures_waterfall =[]
for v in dict_profit_relative:
    if dict_profit_relative[v] == 0:
        measures_waterfall.append("total")
    else:
        measures_waterfall.append("relative")

text_waterfall = []
for v in dict_profit_relative:
    if dict_profit_components["LUCRO OPERACIONAL"]>2000000:
        text_waterfall.append(str(round(dict_profit_components[v]/1000000,2))+"M")
    else:
        text_waterfall.append(str(round(dict_profit_components[v]/1000,2))+"k")


x_waterfall = list(dict_profit_relative.keys())
y_waterfall = list(dict_profit_relative.values())

    ###### Os textos em plotly são lidos como pseudoHTML
    ###### por tal razão "\n" não funcionará para quebra de linha
    ###### devendo utilizar o <br>
x_ticks_vals = ['Receita<br>Percentual<br>do Pedido',
                'Receita de<br>Hospedagem<br>do Logista',
                'Receita da<br>Taxa de<br>Entrega', 
                'RECEITA<br>BRUTA', 
                'Custo de<br>Entrega', 
                'Custo com<br>Entregadores', 
                'Total em<br>Impostos', 
                'LUCRO<br>OPERACIONAL']

waterfall_fig = go.Figure(go.Waterfall(
    name = "(+\=\-)", orientation = "v",
    measure = measures_waterfall,
    x = x_waterfall,
    y = y_waterfall,
    connector = {"line":{"color":"rgb(63, 63, 63)"}},
    decreasing = {"marker":{"color":"#8B0000"}},
    increasing = {"marker":{"color":"darkgreen"}},
    totals = {"marker":{"color":"darkgray"}},
    textposition = "auto",
    text = text_waterfall,
))
waterfall_fig.update_layout(
    autosize=True,
    width=1300,
    height=400,
    margin=dict(
        l=50,
        r=50,
        b=100,
        t=100,
        pad=4
    ),
    xaxis=dict(tickfont=dict(size=12, color='#000000'),
               tickmode = 'array',
               tickvals = list(dict_profit_components.keys()),
               ticktext = x_ticks_vals,
               tickangle= 0),
    font_family="Open Sans",
    title = "Composição do Lucro Operacional",
    showlegend = True
)
waterfall_fig.add_hline(y=0, line_width=2, line_dash='dash',
                        line_color="gray", opacity=.5)

#st.plotly_chart(waterfall_fig, height=500)

#-------- DASH GRID
st.divider()
col11, col12, col13, col14 = st.columns(4)
with col14:
    st.plotly_chart(pie_canceledorders)

st.divider()
col21, col22 = st.columns(2)
with col21:
    st.plotly_chart(bar_proft_hubs)
with col22:
    st.plotly_chart(bars_mean_time_city)
st.divider()
st.plotly_chart(bars_TKM)
st.divider()
st.plotly_chart(waterfall_fig, height=500)
