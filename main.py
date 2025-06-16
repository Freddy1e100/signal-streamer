import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
from binance.client import Client
from ta.momentum import StochRSIIndicator
import datetime

# Binance API — public
client = Client()

# Настройки интерфейса
st.set_page_config(page_title="Crypto Signals", layout="wide")
st.title("📈 Крипто сигналы")

# Выбор таймфрейма
timeframe = st.selectbox("Выберите таймфрейм", ["1h", "4h", "1d"])
interval_map = {
    "1h": Client.KLINE_INTERVAL_1HOUR,
    "4h": Client.KLINE_INTERVAL_4HOUR,
    "1d": Client.KLINE_INTERVAL_1DAY,
}

# Кнопка обновления
if st.button("🔄 Обновить данные"):
    st.experimental_rerun()

# Показывать ли нейтральные сигналы
show_neutral = st.checkbox("Показывать нейтральные сигналы", value=True)

# Пары для анализа
symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "PAXGUSDT"]

def get_data(symbol, interval, lookback="100"):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=int(lookback))
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df.astype(float)
    return df

def analyze(df):
    stoch_rsi = StochRSIIndicator(df['close'], window=14, smooth1=3, smooth2=3)
    df['stoch_rsi'] = stoch_rsi.stochrsi_k()
    latest = df.iloc[-1]
    signal = "Нейтрально"
    if latest['stoch_rsi'] < 0.2:
        signal = "LONG"
    elif latest['stoch_rsi'] > 0.8:
        signal = "SHORT"
    return signal, latest

def plot_chart(df, symbol):
    fig, ax1 = plt.subplots(figsize=(10, 4))

    ax1.set_title(f"{symbol} — Цена и Stoch RSI")
    ax1.plot(df.index, df['close'], label='Цена', color='black')
    ax1.set_ylabel("Цена")

    ax2 = ax1.twinx()
    ax2.plot(df.index, df['stoch_rsi'], label='Stoch RSI', color='purple', alpha=0.6)
    ax2.set_ylabel("Stoch RSI", color='purple')
    ax2.tick_params(axis='y', labelcolor='purple')
    ax2.set_ylim(0, 1)

    fig.tight_layout()
    return fig

# Основной цикл по валютным парам
for symbol in symbols:
    df = get_data(symbol, interval_map[timeframe])
    signal, latest = analyze(df)

    if not show_neutral and signal == "Нейтрально":
        continue

    # Отображение блока сигнала
    st.subheader(f"{symbol.replace('USDT', '')}/USDT ({timeframe})")

    if signal == "LONG":
        bg_color = "#d1f7c4"
        emoji = "🟢"
    elif signal == "SHORT":
        bg_color = "#f8c4c4"
        emoji = "🔴"
    else:
        bg_color = "#eeeeee"
        emoji = "⏸️"

    with st.container():
        st.markdown(
            f"""
            <div style="background-color:{bg_color}; padding:10px; border-radius:10px">
            <h4>{emoji} <b>{signal}</b></h4>
            <p>⏰ Время: {latest.name.strftime('%Y-%m-%d %H:%M:%S')}<br>
            💰 Вход: {latest['close']:.2f}<br>
            📍 Стоп: {latest['close']*1.03:.2f} 🎯 Тейк: {latest['close']*0.97:.2f}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.pyplot(plot_chart(df, symbol))
