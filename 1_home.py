
import streamlit as st
import pandas as pd
import numpy as np
import plotly
import plotly.graph_objects as go
import os


# útil para leitura de grandes bases de dados
# essa @st.cache_data ajuda a "proteger" esses dados
# uma vez executada a função armazenamos ela na cache
@st.cache_data
def load_data():
    cwd = os.getcwd()
    path = os.path.join(cwd, "/datasets/")
    files_list = os.listdir(path)

    files_names = list()
    dict_dfs = dict()

    for file in files_list:
        path_csv = path + file
        files_names.append(file[:-4])
        dict_dfs[files_names[-1]] = pd.read_csv(path_csv, encoding='ISO-8859-1')

    return dict_dfs 

dict_dfs = {
    "channels" : "\GitHub\Brazilian-Delivery-Center_Deploy\datasets\channels.csv",
    "deliveries" : "\GitHub\Brazilian-Delivery-Center_Deploy\datasets\deliveries.csv",
    "drivers": "\GitHub\Brazilian-Delivery-Center_Deploy\datasets\drivers.csv"
}
    
st.session_state["data"] = dict_dfs


# Transformando os dados para o formato datetime
for moment in range(14,22):
    dict_dfs["orders"][dict_dfs["orders"].columns[moment]] = pd.to_datetime(dict_dfs["orders"][dict_dfs["orders"].columns[moment]], format="%m/%d/%Y %I:%M:%S %p", errors='coerce')

dict_dfs["orders"]["prod_time"] =  pd.to_datetime(dict_dfs["orders"]['order_moment_created']) - pd.to_datetime(dict_dfs["orders"]['order_moment_ready']) 
dict_dfs["orders"]['idle_time'] = pd.to_datetime(dict_dfs["orders"]['order_moment_collected']) - pd.to_datetime(dict_dfs["orders"]['order_moment_ready'])
dict_dfs["orders"]['deli_time'] = pd.to_datetime(dict_dfs["orders"]['order_moment_delivering']) - pd.to_datetime(dict_dfs["orders"]['order_moment_collected'])


# Transformando alguns dados em tipo categórico
## Status de Pedido há apenas duas possibilidade
dict_dfs["orders"]["order_status"] = pd.Categorical(dict_dfs["orders"]["order_status"])
## Status de Entrega há apenas 3 estados possíveis
dict_dfs["deliveries"]["delivery_status"] = pd.Categorical(dict_dfs["deliveries"]["delivery_status"])
## Modal e tipo de motoristas há apenas dois tipos
dict_dfs["drivers"]["driver_modal"] = pd.Categorical(dict_dfs["drivers"]["driver_modal"])
dict_dfs["drivers"]["driver_type"] = pd.Categorical(dict_dfs["drivers"]["driver_type"])
## Nome do Canal utilizado, tipo há apenas duas posições
dict_dfs["channels"]["channel_name"] = pd.Categorical(dict_dfs["channels"]["channel_name"])
dict_dfs["channels"]["channel_type"] = pd.Categorical(dict_dfs["channels"]["channel_type"])
## Hub tem info de estado, cidade e nome do hub 
dict_dfs["hubs"]["hub_name"] = pd.Categorical(dict_dfs["hubs"]["hub_name"])
dict_dfs["hubs"]["hub_city"] = pd.Categorical(dict_dfs["hubs"]["hub_city"])
dict_dfs["hubs"]["hub_state"] = pd.Categorical(dict_dfs["hubs"]["hub_state"])
## Métodos e status de pagamento há cerca de 4 opções
dict_dfs["payments"]["payment_method"] = pd.Categorical(dict_dfs["payments"]["payment_method"])
dict_dfs["payments"]["payment_status"] = pd.Categorical(dict_dfs["payments"]["payment_status"])
## Segmento do Lojistas há apenas duas opções
dict_dfs["stores"]["store_name"] = pd.Categorical(dict_dfs["stores"]["store_name"])
dict_dfs["stores"]["store_segment"] = pd.Categorical(dict_dfs["stores"]["store_segment"])
