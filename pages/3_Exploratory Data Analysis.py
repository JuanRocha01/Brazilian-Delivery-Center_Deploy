#----- Bibliotecas nescessárias para transformação e charts
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly._subplots import make_subplots
import calendar
import io

#----- Configurações da página
st.set_page_config(
    page_title="EDA - Análise Exploratória",
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
filtered_orders["MÊS"] = filtered_orders["order_created_month"].apply(lambda x: calendar.month_name[x])
#-----
    # Analisando as informações disponíveis
##------ Crescimento de Número de Pedidos
qntd_pedidos = pd.pivot_table(data=filtered_orders,values='order_id' ,columns=['order_created_month'], index=['store_segment'], aggfunc='count',observed=False)

meses_in = {}
for i in qntd_pedidos.columns:
    meses_in[i] = calendar.month_name[i]
qntd_pedidos=qntd_pedidos.rename(columns=meses_in)

f_qntd_pedidos = go.Figure()
f_qntd_pedidos.add_trace( go.Scatter(
    x = qntd_pedidos.columns,
    y = qntd_pedidos.loc["GOOD"],
    name="Mercado",
    fill = 'tozeroy',
    marker=dict(color='#5D69B1', size=8),
                  line=dict(color='#52BCA3', width=1)
))

f_qntd_pedidos.add_trace( go.Scatter(
    x = qntd_pedidos.columns,
    y = qntd_pedidos.loc["FOOD"],
    name= "Restaurante",
    fill = 'tonexty',
    marker=dict(color='#ba181b', size=8),
                  line=dict(color='#e5383b', width=1),
))

n_pedidos = pd.DataFrame(df_orders.groupby("order_created_month")["order_id"].nunique())
n_pedidos["n_mes"] = n_pedidos.index
n_pedidos["MÊS"] = n_pedidos["n_mes"].apply(lambda x: calendar.month_name[x])

f_qntd_pedidos.update_yaxes(rangemode="tozero")
f_qntd_pedidos.update_layout(title="Número de Pedidos em 2021")

##------- Crescimento de Pedidos por cidade
qntd_pedidos_city = pd.pivot_table(data=filtered_orders,values='order_id' ,columns=['order_created_month'], index=['hub_city','store_segment'], aggfunc='count',observed=False)

meses_in = {}
for i in qntd_pedidos_city.columns:
    meses_in[i] = calendar.month_name[i]
qntd_pedidos_city=qntd_pedidos_city.rename(columns=meses_in)

cities = filtered_orders["hub_city"].unique()
f_qntd_pedidos_cities = make_subplots(rows=2, cols=2, subplot_titles=cities)

i = 0
for r in range(1,3):
    for c in range(1,3):
        f_qntd_pedidos_cities.add_trace(go.Scatter(
            x = qntd_pedidos_city.loc[cities[i]].columns,
            y = qntd_pedidos_city.loc[cities[i]].loc["GOOD"],
            name="Mercado",
            fill = 'tozeroy',
            marker=dict(color='#5D69B1', size=8),
                  line=dict(color='#52BCA3', width=1),
            ),
            row=r,
            col=c
        )
        f_qntd_pedidos_cities.add_trace( go.Scatter(
            x = qntd_pedidos_city.loc[cities[i]].columns,
            y = qntd_pedidos_city.loc[cities[i]].loc["FOOD"],
            name= "Restaurante",
            fill = 'tonexty',
            marker=dict(color='#ba181b', size=8),
                        line=dict(color='#e5383b', width=1),
            ),
            row=r,
            col=c
        )
        i += 1
f_qntd_pedidos_cities.update_layout(showlegend=False, title="Evolução do Número de Pedidos por Cidade")
##------  Crescimento do Lucro ao mês
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

    ## Lucro por estado
f_bar_monthprofit = go.Figure(data=go.Bar(
    x=n_pedidos["MÊS"],
    y=opProfit_month["Operational Profit"],
    marker_color= cmap_4ptop
))
f_bar_monthprofit.update_layout(title="Lucro Operacional Mensal")

##------  Lucro por estado

stores_month_year_b = filtered_orders[["order_created_month","MÊS","store_id"]].copy()
grouped_stores_month_year_b = stores_month_year_b.groupby(["order_created_month","MÊS","store_id"]).nunique().reset_index()
grouped_stores_month_year_b = grouped_stores_month_year_b.merge(df_stores, on='store_id')
grouped_stores_month_year_b = grouped_stores_month_year_b.merge(df_hubs, on="hub_id")
hub_monthly_plan = pd.pivot_table(data=grouped_stores_month_year_b, values="store_plan_price", index="hub_city", columns="order_created_month", aggfunc="sum", observed=False)

opProfit_city = pd.pivot_table(data=filtered_orders, values="profit_aftTaxes", index=["hub_city"], columns=["order_created_month"], aggfunc='sum', observed=False)

opProfit_city=opProfit_city + hub_monthly_plan

meses_in = {}
for i in opProfit_city.columns:
    meses_in[i] = calendar.month_name[i]
opProfit_city=opProfit_city.rename(columns=meses_in)

bar_cityprofit = []
k = 0
for month in opProfit_city.columns:
    bar_cityprofit.append(
        go.Bar(x=opProfit_city.index, y=opProfit_city[month], name=month, marker_color=cmap_4ptop[k]))
    k += 1

f_bar_cityprofit=go.Figure(
    data=bar_cityprofit)


#------- Ticket Médio

tkmedio_hub = pd.pivot_table(data=filtered_orders, values="profit_aftTaxes", index=["hub_name"], columns=["store_segment"], aggfunc='sum', observed=False) / pd.pivot_table(data=filtered_orders, values="RECEITA BRUTA", index=["hub_name"], columns=["store_segment"], aggfunc='count', observed=False)

f_box_tkmedio_segment = go.Figure()
f_box_tkmedio_segment.add_traces(go.Box(x=tkmedio_hub["FOOD"], marker_color="#e5383b", name="Restaurante"))
f_box_tkmedio_segment.add_traces(go.Box(x=tkmedio_hub["GOOD"], marker_color="#52BCA3", name="Mercado"))
f_box_tkmedio_segment.add_vline(x=0)
#f_box_tkmedio_segment.add_vline(x=6)
f_box_tkmedio_segment.update_layout(title="Distribuição do Lucro Unitário Médio por Segmento")

    # Lucro unit com mês segmentado
profit_hub_monthly = pd.pivot_table(data=filtered_orders, values="profit_aftTaxes", index=["MÊS","hub_name"], columns=["store_segment"], aggfunc='sum', observed=False) / pd.pivot_table(data=filtered_orders, values="RECEITA BRUTA", index=["MÊS","hub_name"], columns=["store_segment"], aggfunc='count', observed=False)

df_profit_hub_monthly = pd.DataFrame(profit_hub_monthly.reset_index())

df_profit_hub_monthly = df_profit_hub_monthly.merge(df_hubs, on="hub_name")[["MÊS","hub_name","FOOD","GOOD", "hub_city"]]

f_box_profit_city = go.Figure()
df_profit_hub_monthly = df_profit_hub_monthly[df_profit_hub_monthly["GOOD"]<=40]
f_box_profit_city.add_traces(
        go.Box(
            y=df_profit_hub_monthly["FOOD"],x= df_profit_hub_monthly["hub_city"],name="Restaurante",
            marker_color="#e5383b", 
                        ))
f_box_profit_city.add_traces(
        go.Box(
            y=df_profit_hub_monthly["GOOD"],x= df_profit_hub_monthly["hub_city"],name="Mercado",
            marker_color="#52BCA3", 
                        ))
f_box_profit_city.update_layout(title="Distribuição do Lucro Unitário Médio de Entregas de Comida por Cidade", boxmode='group')

tkmedio_hub_monthly = pd.pivot_table(data=filtered_orders, values="RECEITA BRUTA", index=["MÊS","hub_name"], columns=["store_segment"], aggfunc='sum', observed=False) / pd.pivot_table(data=filtered_orders, values="RECEITA BRUTA", index=["MÊS","hub_name"], columns=["store_segment"], aggfunc='count', observed=False)


    # Regiões Perigosas
hubs_baixo_lucro = pd.DataFrame(profit_hub_monthly[profit_hub_monthly["FOOD"]<1]["FOOD"].reset_index())
hubs_baixo_lucro = hubs_baixo_lucro.merge(df_hubs, on="hub_name")[["MÊS","hub_city","hub_name","FOOD"]]
hubs_baixo_lucro = hubs_baixo_lucro.sort_values(by="hub_city")

####------ Markdown ----------------------------------------------------------------------------------
st.title("Análise Exploratória de Dados")
st.subheader("Problema Objetivo")

st.markdown("""
Com o objetivo de identificar potenciais problemas de rentabilidade e gerar insights aos stakeholders interessados, há uma análise exploratória das informações disponibilizadas pelo banco de dados responsável com o seguinte modelo relacional: Apesar de termos as informações de cada pedido, fornecedor e entregador separados por região e hub, os dados devem ser devidamente tratados e ainda precisamos calcular o lucro da operação. 
""")
st.image("https://api-club-file.cb.hotmart.com/public/v5/files/1b61c3c1-846f-4037-9e48-9277f551f429")

st.subheader("Explorando as Tabelas e Formatos")

col1, col2, col3 = st.columns(3)

with col1:
    st.dataframe(df_channels, height=120)
    st.dataframe(df_stores, height=120)
with col2:
    st.dataframe(df_deliveries, height=120)
    st.dataframe(df_payments, height=120)
with col3:
    st.dataframe(df_drivers, height=120)
    st.dataframe(df_hubs, height=120)
st.dataframe(df_orders, height=120)

st.markdown("""
Analisando o número de pedidos podemos ver claramente uma elevação no período de março de 2021, início do lockdown no Brasil em razão da pandemia de COVID-19.
""")
st.plotly_chart(f_qntd_pedidos)
st.markdown("""
Observe também que apesar de termos as informações de cada pedido, fornecedor e entregador separados por região e hub, os dados devem ser devidamente tratados e ainda precisamos calcular as receitas e custos operacionais para saber o lucro gerencial da operação e começar a análise das medidas. 

Os componentes de receita do negócio são os 15% do valor do pedido, a taxa de entrega e a mensalidade de hospedagem pago pelo lojista. Já os custos da operação são compostos pelo custo de 5 reais por pedido com entregadores, o custo variável da operação de entrega e os encargos.
                        
Com a tabela abaixo podemos perceber que apesar do lucro seguir a mesma tendência do número de pedidos a queda brusca de $100k no mês de abril acende um alerta sobre a volatilidade das margens da empresa.
""")
st.plotly_chart(f_bar_monthprofit)
st.markdown("""
Quando observamos a composição do lucro por estado temos uma visão clara que há regiões dando prejuízo e como todos os custos variam de acordo com a operação essa perspectiva de aumento de pedidos gera uma expectativa de prejuízo ainda maior.""")
f_bar_cityprofit.update_layout(title='Lucro Operacional Segmentado por Cidade')
st.plotly_chart(f_bar_cityprofit)
st.plotly_chart(f_qntd_pedidos_cities)

total_food_orders = filtered_orders.groupby("store_segment",observed=False)["store_id"].count().loc["FOOD"]
total_good_orders = filtered_orders.groupby("store_segment",observed=False)["store_id"].count().loc["GOOD"]


st.markdown(f"""
Tendo como direcional estratégico uma média maior que $1 de lucro por pedido, e fazendo uma rápida análise vemos que nosso segmento mais lucrativo é o de entrega de produtos que representa {round(100*total_good_orders/len(filtered_orders), 1)}% dos pedidos realizados, já o ramo de entrega de alimentos possui hubs operando com lucro unitário médio abaixo do direcional ou até negativos!
""")
st.plotly_chart(f_box_tkmedio_segment)
st.markdown("""Buscando desvendar possíveis detratores de lucro, olhemos a distribuição do lucro unitário médio das cidades percebemos rapidamente que:
            
    1° Apesar de possuir o maior lucro médio unitário, o segmento de produtos de mercado possui o maior desvio padrão já que a quantidade e valor dos componentes da entrega variam bastante

    2° O segmento de entrega de alimentos em Curitiba opera totalmente em prejuízo
    
    
            """)
st.plotly_chart(f_box_profit_city)

col1, col2 = st.columns(2)
with col1:
    meses = filtered_orders["MÊS"].unique()
    mes = st.multiselect("Mês de Análise",meses, default=meses)

    cidades = df_hubs["hub_city"].unique()
    cidade = st.multiselect("Estado(s)",cidades, default="CURITIBA")

    produtos = df_stores["store_segment"].unique()
    produto = st.multiselect("Produtos de Interesse",produtos, default="FOOD")

    filtered_orders_c = filtered_orders[
            (filtered_orders["MÊS"].isin(mes)) &
            (filtered_orders["hub_city"].isin(cidade)) &
            (filtered_orders["store_segment"].isin(produto))].copy()

with col2:
    hubs = filtered_orders_c["hub_name"].unique()
    hub = st.selectbox("Hubs de Interesse de Analise", hubs)
    filtered_orders_c = filtered_orders_c[filtered_orders_c["hub_name"]==hub]

hub_monthly_plan = pd.pivot_table(data=grouped_stores_month_year_b, values="store_plan_price", index="hub_name", columns="order_created_month", aggfunc="sum", observed=False)


meses_in = {}
for i in hub_monthly_plan.columns:
    meses_in[i] = calendar.month_name[i]
hub_monthly_plan=hub_monthly_plan.rename(columns=meses_in)


st.markdown("""Para investigar melhor quais os detratores de lucro, criei o seguinte gráfico interativo de cascata que mostra a composição de lucro de acordo com os filtros acima selecionados:""")
# grafico de cascata -------------
dict_profit_components = {}
dict_profit_components["Receita Percentual do Pedido"] = filtered_orders_c["profit_percent_order_amount"].sum()
dict_profit_components["Receita de Hospedagem do Logista"] = hub_monthly_plan.loc[hub][mes].sum().sum()
dict_profit_components["Receita de Taxa de Entrega"] = filtered_orders_c["order_delivery_fee"].sum()
dict_profit_components["RECEITA BRUTA"] = sum(
    (dict_profit_components["Receita de Hospedagem do Logista"], dict_profit_components["Receita Percentual do Pedido"], dict_profit_components["Receita de Taxa de Entrega"]))
#### Custo de Entrega é fixo em $5
dict_profit_components["Custo de Entrega"] = -5*len(filtered_orders_c)
#### Custo de entregador
dict_profit_components["Fee de Entrega"] = -filtered_orders_c["order_delivery_cost"].sum()
dict_profit_components["Total em Impostos"] = filtered_orders_c["total_tax"].sum()
dict_profit_components["LUCRO OPERACIONAL"] = sum((dict_profit_components["RECEITA BRUTA"], dict_profit_components["Custo de Entrega"], dict_profit_components["Fee de Entrega"], dict_profit_components["Total em Impostos"]))
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
                'Fee de<br>Entrega', 
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
    height=600,
    margin=dict(
        l=50,
        r=50,
        b=100,
        t=100,
        pad=4
    ),
    xaxis=dict(tickfont=dict(size=12, color='gray'),
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



st.plotly_chart(waterfall_fig, height=500)
st.markdown("""A partir disso torna-se claro como a margem realizada de 15% do valor do pedido é insuficiente para cobrir os custos operacionais da região, principalmente por conta do custo unitário de entrega (5$). A titulo de curiosidade, abaixo temos a lista dos hubs que em algum momento não cumpriram o direcional estratégico""")
st.write(hubs_baixo_lucro)


# %%
