import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from ta.momentum import RSIIndicator
from datetime import datetime

# 🎨 Configurações gerais
st.set_page_config(page_title="Dashboard Cripto", layout="wide")
sns.set(style='whitegrid')

st.title('🚀 Dashboard de Criptomoedas - BTC & ETH com Indicadores')

# 🚀 Função para buscar dados da Binance
@st.cache_data(ttl=3600)
def get_klines(symbol, interval, limit=500):
    url = 'https://api.binance.com/api/v3/klines'
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    response = requests.get(url, params=params)
    data = response.json()

    df = pd.DataFrame(data, columns=[
        'Open Time', 'Open', 'High', 'Low', 'Close', 'Volume',
        'Close Time', 'Quote Asset Volume', 'Number of Trades',
        'Taker Buy Base Asset Volume', 'Taker Buy Quote Asset Volume', 'Ignore'
    ])

    df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')
    df['Close Time'] = pd.to_datetime(df['Close Time'], unit='ms')
    numeric = ['Open', 'High', 'Low', 'Close', 'Volume']
    df[numeric] = df[numeric].astype(float)
    df['hour'] = df['Open Time'].dt.hour

    # 📈 Adicionando indicadores técnicos
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()

    rsi = RSIIndicator(close=df['Close'], window=14)
    df['RSI'] = rsi.rsi()

    return df

# 🚨 Função para alerta via Telegram
def send_telegram_alert(message):
    token = st.secrets.get("TELEGRAM_TOKEN")
    chat_id = st.secrets.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        st.success('✅ Alerta enviado via Telegram!')
    else:
        st.error('❌ Erro ao enviar alerta.')

# 🔧 Sidebar
st.sidebar.header('⚙️ Configurações')
interval = st.sidebar.selectbox('Intervalo', ['1h', '30m', '15m', '5m'], index=0)
limit = st.sidebar.slider('Velas', 100, 1000, 500)

# Carregar dados
btc = get_klines('BTCUSDT', interval, limit)
eth = get_klines('ETHUSDT', interval, limit)

# Tabs
tab1, tab2 = st.tabs(['📊 Bitcoin (BTC)', '📊 Ethereum (ETH)'])

# 🎯 Função de análise
def show_analysis(df, name):
    st.subheader(f'{name} - Últimos {limit} candles ({interval})')

    st.dataframe(df[['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume']].tail(10))

    col1, col2 = st.columns(2)

    with col1:
        st.subheader('📈 Gráfico de Preço + Médias')
        fig, ax = plt.subplots()
        ax.plot(df['Open Time'], df['Close'], label='Fechamento', color='blue')
        ax.plot(df['Open Time'], df['SMA_20'], label='SMA 20', color='orange')
        ax.plot(df['Open Time'], df['SMA_50'], label='SMA 50', color='magenta')
        ax.set_xlabel('Tempo')
        ax.set_ylabel('Preço (USDT)')
        ax.legend()
        st.pyplot(fig)

    with col2:
        st.subheader('📊 Volume')
        fig, ax = plt.subplots()
        ax.bar(df['Open Time'], df['Volume'], color='lightgreen')
        ax.set_xlabel('Tempo')
        ax.set_ylabel('Volume')
        st.pyplot(fig)

    # RSI Plot
    st.subheader('📉 RSI (Índice de Força Relativa)')
    fig, ax = plt.subplots()
    ax.plot(df['Open Time'], df['RSI'], label='RSI', color='purple')
    ax.axhline(70, color='red', linestyle='--')
    ax.axhline(30, color='green', linestyle='--')
    ax.set_title('RSI')
    ax.legend()
    st.pyplot(fig)

    # 📊 Análise de melhores horários
    st.subheader('⏰ Análise por Hora (UTC)')
    hourly = df.groupby('hour').agg({
        'Open': 'mean', 'High': 'mean', 'Low': 'mean', 'Close': 'mean', 'Volume': 'mean'
    }).reset_index()

    fig, ax = plt.subplots()
    sns.lineplot(x='hour', y='Close', data=hourly, label='Fechamento', ax=ax)
    sns.lineplot(x='hour', y='High', data=hourly, label='Máxima', ax=ax)
    sns.lineplot(x='hour', y='Low', data=hourly, label='Mínima', ax=ax)
    ax.set_title('Preço Médio por Hora (UTC)')
    ax.set_xticks(range(0, 24))
    st.pyplot(fig)

    # 🔔 Alertas de melhores horários
    best_buy_hour = hourly.loc[hourly['Low'].idxmin(), 'hour']
    best_sell_hour = hourly.loc[hourly['High'].idxmax(), 'hour']

    st.info(f'🔽 Melhor hora média para **COMPRA**: {int(best_buy_hour)}h UTC')
    st.success(f'🔼 Melhor hora média para **VENDA**: {int(best_sell_hour)}h UTC')

    # ✔️ Sistema de Alerta
    if st.button(f'🚨 Enviar alerta Telegram para {name}'):
        latest = df.iloc[-1]
        message = (
            f'🚀 {name} Alerta\n'
            f'Último preço: {latest["Close"]}\n'
            f'RSI: {latest["RSI"]:.2f}\n'
            f'Melhor hora média para compra: {int(best_buy_hour)}h UTC\n'
            f'Melhor hora média para venda: {int(best_sell_hour)}h UTC\n'
            f'Dashboard: {st.secrets.get("DASHBOARD_URL")}'
        )
        send_telegram_alert(message)

# Mostrar tabs
with tab1:
    show_analysis(btc, 'Bitcoin (BTC)')

with tab2:
    show_analysis(eth, 'Ethereum (ETH)')
