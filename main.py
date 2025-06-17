import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from binance.client import Client
from ta.momentum import StochRSIIndicator, RSIIndicator

# Binance API (без ключей)
client = Client()

# Настройки пар
PAIRS = {
    "BTCUSDT": "Bitcoin",
    "ETHUSDT": "Ethereum",
    "SOLUSDT": "Solana",
    "PAXGUSDT": "PAX Gold"
}

TIMEFRAMES = {
    "1H": "1h",
    "4H": "4h",
    "1D": "1d"
}

# Интерфейс Streamlit
st.set_page_config(page_title="📈 Crypto Signal Streamer", layout="wide")
st.title("📡 Crypto Signal Streamer")
st.markdown("Получайте торговые сигналы по Stoch RSI и RSI")

# UI фильтры
col1, col2, col3 = st.columns(3)
with col1:
    timeframe = st.selectbox("Таймфрейм", TIMEFRAMES.keys(), index=0)
with col2:
    stop_percent = st.number_input("Стоп-лосс %", min_value=0.5, max_value=10.0, value=3.0)
with col3:
    take_percent = st.number_input("Тейк-профит %", min_value=0.5, max_value=10.0, value=3.0)

show_neutral = st.checkbox("Показывать нейтральные сигналы", value=True)

# Получение исторических данных
def get_data(symbol, interval="1h", limit=150):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        "Open Time", "Open", "High", "Low", "Close", "Volume",
        "Close Time", "Quote Asset Volume", "Number of Trades",
        "Taker buy base", "Taker buy quote", "Ignore"
    ])
    df["Open Time"] = pd.to_datetime(df["Open Time"], unit='ms')
    df.set_index("Open Time", inplace=True)
    df = df[["Open", "High", "Low", "Close", "Volume"]].astype(float)
    return df

# Анализ данных
def analyze(df):
    rsi = RSIIndicator(close=df["Close"])
    stoch = StochRSIIndicator(close=df["Close"])

    df["RSI"] = rsi.rsi()
    df["StochRSI"] = stoch.stochrsi()
    df.dropna(inplace=True)

    last = df.iloc[-1]
    close_price = last["Close"]

    signal = "⏸️ Нейтрально"
    if last["RSI"] < 30 and last["StochRSI"] < 0.2:
        signal = "✅ LONG"
    elif last["RSI"] > 70 and last["StochRSI"] > 0.8:
        signal = "🔻 SHORT"

    if signal == "✅ LONG":
        stop_loss = round(close_price * (1 - stop_percent / 100), 2)
        take_profit = round(close_price * (1 + take_percent / 100), 2)
    elif signal == "🔻 SHORT":
        stop_loss = round(close_price * (1 + stop_percent / 100), 2)
        take_profit = round(close_price * (1 - take_percent / 100), 2)
    else:
        stop_loss = take_profit = close_price

    return signal, round(close_price, 2), stop_loss, take_profit, df

# Визуализация графика
def plot_chart(df, name):
    fig, ax1 = plt.subplots(figsize=(10, 4))
    ax2 = ax1.twinx()

    ax1.plot(df.index, df["Close"], label="Цена", color="white", linewidth=1.5)
    ax2.plot(df.index, df["StochRSI"], label="StochRSI", color="orange", linestyle="--")

    ax1.set_ylabel("Цена", color="white")
    ax2.set_ylabel("StochRSI", color="orange")

    ax1.grid(True, alpha=0.3)
    ax1.set_title(name)
    fig.tight_layout()
    st.pyplot(fig)

# Основной цикл по парам
for symbol, name in PAIRS.items():
    df = get_data(symbol, interval=TIMEFRAMES[timeframe])

    if len(df) < 50:
        continue

    signal, entry, sl, tp, df = analyze(df)

    if not show_neutral and signal == "⏸️ Нейтрально":
        continue

    st.markdown(f"---\n### {name} ({symbol})")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📊 Сигнал", signal)
    col2.metric("💰 Цена входа", f"{entry}$")
    col3.metric("📍 Стоп-лосс", f"{sl}$")
    col4.metric("🎯 Тейк-профит", f"{tp}$")

    plot_chart(df, f"{name} ({symbol})")
