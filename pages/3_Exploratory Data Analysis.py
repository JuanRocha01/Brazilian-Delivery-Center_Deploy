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
filtered_orders["MÊS"] = filtered_orders["order_created_month"].apply(lambda x: calendar.month_name[x])
#-----
    # Analisando as informações disponíveis
##------ Crescimento de Número de Pedidos
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
df_hub_store = df_stores.merge(df_hubs, on="hub_id")
total_host = {}
for i in range(1,5):
    monthly_hosted = grouped_stores_month_year[grouped_stores_month_year.index.get_level_values(1).isin([i])]
    total_host[i] = df_hub_store.merge(monthly_hosted,
                                             on="store_id")
k = 1
hub_monthly_plan = pd.DataFrame()
for i in n_pedidos["MÊS"]:
    hub_monthly_plan[i] = pd.DataFrame(total_host[k].groupby("hub_city", observed=False)["store_plan_price"].sum())
    k += 1
opProfit_city = pd.pivot_table(data=filtered_orders, values="profit_aftTaxes", index=["hub_city"], columns=["order_created_month"], aggfunc='sum', observed=False)

meses_in = {}
for i in opProfit_city.columns:
    meses_in[i] = calendar.month_name[i]
opProfit_city=opProfit_city.rename(columns=meses_in)
opProfit_city=opProfit_city + hub_monthly_plan

for city in opProfit_city.index:
    print(city)

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
f_box_tkmedio_segment.add_traces(go.Box(x=tkmedio_hub["FOOD"], marker_color="red", name="Alimentação"))
f_box_tkmedio_segment.add_traces(go.Box(x=tkmedio_hub["GOOD"], marker_color="blue", name="Produtos"))
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
            y=df_profit_hub_monthly["FOOD"],x= df_profit_hub_monthly["hub_city"],name="Alimentação",
            marker_color="red", 
                        ))
f_box_profit_city.add_traces(
        go.Box(
            y=df_profit_hub_monthly["GOOD"],x= df_profit_hub_monthly["hub_city"],name="Produto",


            marker_color="blue", 
                        ))
f_box_profit_city.update_layout(title="Distribuição do Lucro Unitário Médio de Entregas de Comida por Cidade", boxmode='group')

tkmedio_hub_monthly = pd.pivot_table(data=filtered_orders, values="RECEITA BRUTA", index=["MÊS","hub_name"], columns=["store_segment"], aggfunc='sum', observed=False) / pd.pivot_table(data=filtered_orders, values="RECEITA BRUTA", index=["MÊS","hub_name"], columns=["store_segment"], aggfunc='count', observed=False)


    # Regiões Perigosas
hubs_baixo_lucro = pd.DataFrame(profit_hub_monthly[profit_hub_monthly["FOOD"]<1]["FOOD"].reset_index())
hubs_baixo_lucro = hubs_baixo_lucro.merge(df_hubs, on="hub_name")[["MÊS","hub_city","hub_name","FOOD"]]
hubs_baixo_lucro = hubs_baixo_lucro.sort_values(by="hub_city")

####------ Markdown ----------------------------------------------------------------------------------
st.title("Análise Exploratória de Dados")
st.subheader("Explorando a performance econômica")

st.markdown("""
Com o objetivo de identificar potenciais problemas de rentabilidade e gerar insights aos stakeholders interessados, há uma análise exploratória das informações disponibilizadas pelo banco de dados responsável com o seguinte modelo relacional: Apesar de termos as informações de cada pedido, fornecedor e entregador separados por região e hub, os dados devem ser devidamente tratados e ainda precisamos calcular o lucro da operação. 
""")
st.image("https://api-club-file.cb.hotmart.com/public/v5/files/1b61c3c1-846f-4037-9e48-9277f551f429")
st.markdown("""
Analisando o número de pedidos podemos ver claramente uma elevação no período de março de 2021, início do lockdown no Brasil em razão da pandemia de COVID-19.
""")
st.plotly_chart(f_qntd_pedidos)
st.markdown("""
Observe também que apesar de termos as informações de cada pedido, fornecedor e entregador separados por região e hub, os dados devem ser devidamente tratados e ainda precisamos calcular as receitas e custos operacionais para saber o lucro gerencial da operação e começar a análise das medidas. 
Para clarificar os cálculos, temos que realizar a seguinte fórmula:
            
$$Lucro Op. = Receita Op. - Custo Op.$$

Sendo que:

$$ReceitaOp. = PercentualdVenda + AlugueldHospedagem + feeEntrega$$

$$PercentualdVenda$$: 15% do valor do pedido
            
$$AlugueldHospedagem$$: Valor fixo pago pelo lojista
            
$$feeEntrega$$: Parte do custo de entrega pago pelo cliente
            
e
            
$$CustoOp. = CustodEntrega + KFixoPedido + Impostos$$

$$CustodEntrega$$: Valor Variável pago ao entregador
            
$$KFixoPedido$$: Custo médio operacional por pedido realizado é $5 reais
            
$$Impostos$$: Impostos devidos ao governo pela operação do Delivery Center
            
Assim, observamos uma elevação do lucro operacional seguindo a mesma tendência do aumento de pedidos
""")
st.plotly_chart(f_bar_monthprofit)
st.markdown("""
Apesar disso, quando observamos a composição do lucro por estado temos uma visão clara que há regiões dando prejuízo e como todos os custos variam de acordo com a operação essa perspectiva de aumento de pedidos gera uma expectativa de prejuízo ainda maior.""")
st.plotly_chart(f_bar_cityprofit)

total_food_orders = filtered_orders.groupby("store_segment",observed=False)["store_id"].count().loc["FOOD"]
total_good_orders = filtered_orders.groupby("store_segment",observed=False)["store_id"].count().loc["GOOD"]


st.markdown(f"""
Temos como direcional estratégico uma média maior que $1 de lucro por pedido, e fazendo uma rápida análise vemos que nosso segmento mais lucrativo é o de entrega de produtos que representa {round(100*total_good_orders/len(filtered_orders), 1)}% dos pedidos realizados, já o ramo de entrega de alimentos possui hubs operando com lucro unitário médio abaixo do direcional ou até negativos!
""")
st.plotly_chart(f_box_tkmedio_segment)
st.markdown("""Buscando desvendar possíveis detratores de lucro, olhemos a distribuição do lucro unitário médio das cidades percebemos rapidamente que:
            
    1° Apesar de possuir o maior lucro médio unitário, o segmento de produtos possui o maior desvio padrão

    2° O segmento de entrega de alimentos em Curitiba opera em prejuízo
            """)
st.plotly_chart(f_box_profit_city)

col1, col2 = st.columns(2)
with col1:
    st.write("Hubs que merecem atenção",hubs_baixo_lucro)

st.markdown("""Sendo eles: """)
    ## Composição Geral de Lucro

with col2:
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

    hubs = filtered_orders_c["hub_name"].unique()
    hub = st.multiselect("Hubs de Interesse de Analise", hubs, default=hubs)


# grafico de cascata -------------
dict_profit_components = {}
dict_profit_components["Receita Percentual do Pedido"] = filtered_orders_c["profit_percent_order_amount"].sum()
dict_profit_components["Receita de Hospedagem do Logista"] = hub_monthly_plan.loc[cidade][mes].sum().sum()
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
# %%
