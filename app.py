import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title='Dash Dieguin',
    layout='wide')

st.title("""
	Dash Dieguin
	""")

df = pd.read_excel('dados.xlsx')

st.header("Localização de produtos")
produto_selecionado = st.selectbox('Seleciona o produto', df['CD_PRODUTO'].unique())
st.write(df.query(f'CD_PRODUTO == {produto_selecionado}'))


st.header('Quantidade de produtos por setor')
df_usinado = df.query("USINADA == 'SIM'").groupby('SETOR', as_index = False).size()
df_n_usinado = df.query("USINADA == 'NAO'").groupby('SETOR', as_index = False).size()
fig = go.Figure(data=[
    go.Bar(name='USINADO', x= df_usinado['SETOR'], y = df_usinado['size'], marker_color = 'green', textfont_color="white", textposition='inside', text= df_usinado['size']),
    go.Bar(name='NÃO USINADO', x= df_n_usinado['SETOR'], y = df_n_usinado['size'], marker_color ='red', textfont_color="white",textposition='inside', text=df_n_usinado['size'])
])
fig.update_layout(barmode='stack')
fig.update_xaxes(title = 'SETOR')
fig.update_yaxes(title = 'Quantidade')
#fig.update_traces(textposition='inside')
st.plotly_chart(fig, use_container_width = True)

st.header("Quantidade diária de produtos nos setores")
df_aux = df.groupby(['DATA_CHEGADA','SETOR'], as_index = False).size()
fig = go.Figure()
for i in df_aux['SETOR'].unique():
    fig.add_trace(go.Scatter(x = pd.to_datetime(df_aux.query(f'SETOR == "{i}"')['DATA_CHEGADA'], format = "%Y%m%d"), 
                             y = df_aux.query(f'SETOR == "{i}"')['size'], name = i))
fig.update_xaxes(title = 'DATA_CHEGADA')
fig.update_yaxes(title = 'Quantidade')
st.plotly_chart(fig, use_container_width = True)

st.header('Tempo Médio de usinagem')
df_aux = df.dropna().groupby('CD_PRODUTO', as_index=False)['TEMPO_USINAGEM'].mean()
fig = go.Figure()
fig.add_trace(go.Bar(x = df_aux['CD_PRODUTO'], y = df_aux['TEMPO_USINAGEM']))
fig.update_xaxes(title = 'CD_PRODUTO')
fig.update_yaxes(title = 'Tempo usinagem (s)')
st.plotly_chart(fig, use_container_width = True)
