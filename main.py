import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from binance.client import Client
from ta.momentum import StochRSIIndicator, RSIIndicator
from datetime import datetime

# Binance client (без ключей, публичный)
client = Client()

# Настройки
PAIRS = {
    "BTCUSDT": "BTC/USDT",
    "ETHUSDT": "ETH/USDT",
    "SOLUSDT": "SOL/USDT",
    "PAXGUSDT": "PAXG/USDT"
}
TIMEFRAMES = {
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d"
}

# Streamlit UI
st.set_page_config(page_title="Crypto Signal Streamer", layout="wide")
st.title("📡 Крипто-сигналы")

col1, col2, col3 = st.columns(3)
timeframe = col1.selectbox("⏱️ Таймфрейм", list(TIMEFRAMES.keys()), index=1)
sl_percent = col2.number_input("❌ Стоп-лосс %", min_value=0.1, max_value=20.0, value=3.0, step=0.1)
tp_percent = col3.number_input("🎯 Тейк-профит %", min_value=0.1, max_value=50.0, value=5.0, step=0.1)

# Получение исторических данных с Binance
@st.cache_data(ttl=300)
def get_data(symbol, interval="1h", limit=200):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        "Open Time", "Open", "High", "Low", "Close", "Volume",
        "Close Time", "Quote Volume", "Trades", "TB Base", "TB Quote", "Ignore"
    ])
    df["Open Time"] = pd.to_datetime(df["Open Time"], unit="ms")
    df.set_index("Open Time", inplace=True)
    df = df[["Open", "High", "Low", "Close", "Volume"]].astype(float)
    return df

# Анализ сигнала
def analyze(df):
    stoch = StochRSIIndicator(close=df["Close"])
    df["StochRSI"] = stoch.stochrsi()
    rsi = RSIIndicator(close=df["Close"])
    df["RSI"] = rsi.rsi()
    df.dropna(inplace=True)

    last = df.iloc[-1]
    signal = "⏸️ Нейтрально"
    if last["RSI"] < 30 and last["StochRSI"] < 0.2:
        signal = "✅ LONG"
    elif last["RSI"] > 70 and last["StochRSI"] > 0.8:
        signal = "🔻 SHORT"

    entry_price = round(last["Close"], 2)
    stop_loss = round(entry_price * (1 - sl_percent / 100) if signal == "✅ LONG" else entry_price * (1 + sl_percent / 100), 2)
    take_profit = round(entry_price * (1 + tp_percent / 100) if signal == "✅ LONG" else entry_price * (1 - tp_percent / 100), 2)

    # Прогноз тренда (условный)
    trend_score = 0.5 + (0.5 * (last["StochRSI"] - 0.5)) + (0.5 * (last["RSI"] - 50) / 100)
    trend_score = max(0, min(1, trend_score))
    trend_text = f"📊 Прогноз тренда: {'вверх' if trend_score > 0.55 else 'вниз' if trend_score < 0.45 else 'боковик'} ({round(trend_score*100)}%)"

    return signal, entry_price, stop_loss, take_profit, df, trend_text

# Отображение сигналов
for symbol, name in PAIRS.items():
    st.markdown(f"---\n### {name}")
    df = get_data(symbol, interval=TIMEFRAMES[timeframe])

    if len(df) < 50:
        st.warning("Недостаточно данных для анализа")
        continue

    signal, entry, sl, tp, df, trend = analyze(df)

    # Вывод текста
    st.markdown(
        f"**Сигнал:** {signal}  \n"
        f"💰 **Цена входа:** `{entry}`  \n"
        f"❌ **Стоп-лосс:** `{sl}`  \n"
        f"🎯 **Тейк-профит:** `{tp}`  \n"
        f"{trend}  \n"
        f"🕒 Время сигнала: `{df.index[-1]}`"
    )

    # График
    fig, ax = plt.subplots(2, 1, figsize=(10, 5), gridspec_kw={'height_ratios': [3, 1]})
    df["Close"].plot(ax=ax[0], label="Цена", color="black")
    ax[0].set_title(f"{name} Цена")
    ax[0].legend()

    df["StochRSI"].plot(ax=ax[1], label="StochRSI", color="purple")
    df["RSI"].plot(ax=ax[1], label="RSI", color="green", alpha=0.6)
    ax[1].axhline(0.2, linestyle="--", color="red", alpha=0.3)
    ax[1].axhline(0.8, linestyle="--", color="red", alpha=0.3)
    ax[1].legend()
    ax[1].set_ylim(0, 100)
    ax[1].set_title("Осцилляторы (StochRSI + RSI)")
    st.pyplot(fig)
