import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Dashboard Cripto", layout="wide")
st.title('📈 Dashboard de Criptomoedas - Bitcoin & Ethereum')

# Função para obter dados da Binance
@st.cache_data(ttl=3600)  # Cache por 1 hora
def get_klines(symbol, interval, limit=100):
    url = 'https://api.binance.com/api/v3/klines'
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    response = requests.get(url, params=params)
    data = response.json()

    df = pd.DataFrame(data, columns=[
        'Open Time', 'Open', 'High', 'Low', 'Close', 'Volume',
        'Close Time', 'Quote Asset Volume', 'Number of Trades',
        'Taker Buy Base Asset Volume', 'Taker Buy Quote Asset Volume', 'Ignore'
    ])

    df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')
    df['Close Time'] = pd.to_datetime(df['Close Time'], unit='ms')
    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    df[numeric_cols] = df[numeric_cols].astype(float)

    df['hour'] = df['Open Time'].dt.hour
    return df

# Sidebar
st.sidebar.header('⚙️ Configurações')
interval = st.sidebar.selectbox('Intervalo de Tempo', ['1h', '30m', '15m', '5m'], index=0)
limit = st.sidebar.slider('Quantas velas carregar?', min_value=50, max_value=1000, value=200)

# Carregar dados
btc = get_klines('BTCUSDT', interval, limit)
eth = get_klines('ETHUSDT', interval, limit)

# Tabs
tab1, tab2 = st.tabs(['📊 Bitcoin (BTC)', '📊 Ethereum (ETH)'])

# Função para gráficos
def show_analysis(df, name):
    st.subheader(f'{name} - Últimos {limit} candles ({interval})')
    
    st.dataframe(df[['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume']].tail(10))

    col1, col2 = st.columns(2)

    with col1:
        st.subheader('Gráfico de Preço')
        fig, ax = plt.subplots()
        ax.plot(df['Open Time'], df['Close'], label='Preço de Fechamento')
        ax.set_xlabel('Tempo')
        ax.set_ylabel('Preço (USDT)')
        ax.legend()
        st.pyplot(fig)

    with col2:
        st.subheader('Volume')
        fig, ax = plt.subplots()
        ax.bar(df['Open Time'], df['Volume'], color='orange')
        ax.set_xlabel('Tempo')
        ax.set_ylabel('Volume')
        st.pyplot(fig)

    st.subheader('📈 Análise por Hora do Dia')
    hourly = df.groupby('hour').agg({
        'Open': 'mean',
        'High': 'mean',
        'Low': 'mean',
        'Close': 'mean',
        'Volume': 'mean'
    }).reset_index()

    fig, ax = plt.subplots()
    sns.lineplot(x='hour', y='Close', data=hourly, label='Fechamento', ax=ax)
    sns.lineplot(x='hour', y='High', data=hourly, label='Máxima', ax=ax)
    sns.lineplot(x='hour', y='Low', data=hourly, label='Mínima', ax=ax)
    ax.set_title('Preço Médio por Hora (UTC)')
    ax.set_xticks(range(0, 24))
    st.pyplot(fig)

    # Alertas
    best_buy_hour = hourly.loc[hourly['Low'].idxmin(), 'hour']
    best_sell_hour = hourly.loc[hourly['High'].idxmax(), 'hour']

    st.info(f'🔽 Melhor horário médio para **COMPRA**: {int(best_buy_hour)}h UTC')
    st.success(f'🔼 Melhor horário médio para **VENDA**: {int(best_sell_hour)}h UTC')

# Mostrar tabs
with tab1:
    show_analysis(btc, 'Bitcoin (BTC)')

with tab2:
    show_analysis(eth, 'Ethereum (ETH)')
