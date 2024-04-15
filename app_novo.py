import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime
import math

st.set_page_config(page_title='Dashboard',
    layout='wide')

st.title("""
	Dashboard
	""")

@st.cache_resource
def puxa_dados():
    operation = pd.read_excel('Operations 03.26.24.xlsx')
    orders = pd.read_excel('Opern Production Orders 03.26.24.xlsx')
    operation = operation.rename(columns = {'Production Order Number':'PRODUCTION ORDER NO'})
    
    df = orders.merge(operation, on = 'PRODUCTION ORDER NO')
    df['CUSTOMER NAME'] = ""
    df['PRODUCTION ORDER NO'] = df['PRODUCTION ORDER NO'].astype(str)
    df['SALES ORDER NO'] = df['SALES ORDER NO'].astype(str)
    qtd_process = df.groupby('PRODUCTION ORDER NO', as_index = False).agg({'Operation Number' : pd.Series.nunique})
    qtd_process.columns = ['PRODUCTION ORDER NO', 'PROCESS QT']
    df = df.merge(qtd_process, on = 'PRODUCTION ORDER NO')
    df['DELAY'] = (datetime.datetime.today() - df['PW DUE DATE']).dt.days
    df.loc[df['DELAY'] < 0 , 'DELAY'] = 0

    df_work = df.groupby('PRODUCTION ORDER NO', as_index=False).agg({'Work Center' : pd.Series.unique})
    seed = np.random.RandomState(2024)
    df_work['ACTUAL_WORK'] = df_work['Work Center'].apply(lambda x: seed.choice(x))

    df = df.merge(df_work[['PRODUCTION ORDER NO','ACTUAL_WORK']], on = 'PRODUCTION ORDER NO')
    
    df_actual = df.loc[df['Work Center'] == df['ACTUAL_WORK']]
    df_actual['PROCESS_STATUS'] = (df_actual['Operation Number']/10).astype(int).astype(str) + "/" + df_actual['PROCESS QT'].astype(str)
    df = df.merge(df_actual[['PRODUCTION ORDER NO','PROCESS_STATUS']], on = 'PRODUCTION ORDER NO')
    
    df_group = df.groupby(['PRODUCTION ORDER NO','CUSTOMER NAME', 'SALES ORDER NO',"PW POST DATE",'PW DUE DATE','ACTUAL_WORK','PROCESS_STATUS'], as_index= False)[['PROCESS QT','DELAY']].mean()
    
    return df, df_group

df, df_group = puxa_dados()

st.header("Production Order locator")
selected_po = st.selectbox("Select the Production Order:", df_group['PRODUCTION ORDER NO'])
st.dataframe(df_group.loc[df_group['PRODUCTION ORDER NO'] == selected_po],
             column_config={
                 'PW POST DATE': st.column_config.DatetimeColumn(format = "YYYY-MM-DD"),
                 'PW DUE DATE': st.column_config.DatetimeColumn(format = "YYYY-MM-DD")
             }, use_container_width= True)

#Fazendo o tracking da peça
st.write("Process Tracker")
df_selected_po = df.loc[df['PRODUCTION ORDER NO'] == selected_po].reset_index(drop = True)
df_selected_po['status'] = (df_selected_po['Work Center'] == df_selected_po['ACTUAL_WORK'])*1
qtd_colunas_po = math.ceil(df_selected_po.shape[0]/5)
df_selected_po['col'] = ([0,1,2,3,4]*qtd_colunas_po)[:df_selected_po.shape[0]]
colunas_po = st.columns(5)
for i in range(len(colunas_po)):
    aux_po = df_selected_po.query(f'col == {i}').reset_index(drop = True)
    for c in range(aux_po.shape[0]):
        etapa = aux_po.loc[c]['Operation Number']
        etapa = int(etapa/10)
        if aux_po.loc[c]['status'] == 1:
            colunas_po[i].write(f":green[{etapa}: {aux_po.loc[c]['Work Center']}]")
        else:
            colunas_po[i].write(f"{etapa}: {aux_po.loc[c]['Work Center']}")



st.write('')
st.header("Product Priorizer")
st.dataframe(df_group.sort_values(['PW DUE DATE', 'PROCESS QT'], ascending=[True, True]),
             column_config={
                 'PW POST DATE': st.column_config.DatetimeColumn(format = "YYYY-MM-DD"),
                 'PW DUE DATE': st.column_config.DatetimeColumn(format = "YYYY-MM-DD")
             }, use_container_width= True)


st.header("SECTOR STATUS")
#st.dataframe(df_group.groupby('ACTUAL_WORK',as_index= False).size().style.background_gradient(cmap="RdYlGn_r"))
setores = df_group['ACTUAL_WORK'].value_counts().reset_index()
qtd_columns = math.ceil(df_group['ACTUAL_WORK'].nunique()/5)

colunas = st.columns(5)
setores['col'] = np.ceil((setores.index + 1)/qtd_columns) - 1
setores['col'] = ([0,1,2,3,4]*qtd_columns)[:setores.shape[0]]

for i in range(len(colunas)):
    aux = setores.query(f'col == {i}').reset_index(drop = True)
    for c in range(aux.shape[0]):
        colunas[i].write(aux.loc[c]['ACTUAL_WORK'])
        if aux.loc[c]['count'] < 7:
            colunas[i].write(f":green[{str(aux.loc[c]['count'])}]")
        elif aux.loc[c]['count'] < 15:
            colunas[i].write(f":blue[{str(aux.loc[c]['count'])}]")
        else:
            colunas[i].write(f":red[{str(aux.loc[c]['count'])}]")
                
        colunas[i].write('')
        colunas[i].write('')
cortes = [15, 7 , 0]

cores = ['red','yellow','green']

fig = go.Figure()
for i in range(len(cortes)):
    if i == 0:
        aux = setores.query(f'count >= {cortes[i]}')
    elif i == len(cortes) - 1:
        aux = setores.query(f'count < {cortes[i-1]}')
    else:
        aux = setores.query(f'count >= {cortes[i]} & count < {cortes[i-1]}')
    
    fig.add_trace(go.Bar(x = aux['ACTUAL_WORK'], y = aux['count'], marker_color = cores[i]))

st.plotly_chart(fig, use_container_width= True)

st.header("Days of Delay")
delays = df_group.groupby('DELAY', as_index= False).size()
col1, col2, col3 = st.columns(3)
col1.metric('On time', delays.query('DELAY == 0')['size'].sum())
col2.metric('Delayed', delays.query('DELAY != 0')['size'].sum())

fig = go.Figure()
fig.add_trace(go.Bar(x = delays.query('DELAY > 0')['DELAY'], y = delays.query('DELAY > 0')['size']))
fig.update_yaxes(title = 'Quantity')
fig.update_xaxes(title = 'Days of delay')
st.plotly_chart(fig, use_container_width= True)