
import streamlit as st
import pandas as pd
import numpy as np
import os

cwd = os.getcwd()
st.title(cwd)
path = cwd + "/datasets/deliveries.csv"
data = pd.read_csv(path)
st.write(data)
#print(cwd)


