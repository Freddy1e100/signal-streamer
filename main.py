import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from binance.client import Client
from ta.momentum import StochRSIIndicator, RSIIndicator
from datetime import datetime

# Binance public client
client = Client()

# Streamlit UI
st.set_page_config(layout="wide")
st.title("📊 Signal Streamer: Крипто-сигналы на основе технического анализа")

# Настройки
PAIRS = {
    "BTCUSDT": "BTC/USDT",
    "ETHUSDT": "ETH/USDT",
    "SOLUSDT": "SOL/USDT",
    "PAXGUSDT": "PAXG/USDT"
}
TIMEFRAMES = {"15m": "15 минут", "1h": "1 час", "4h": "4 часа", "1d": "1 день"}
tf_choice = st.sidebar.selectbox("⏱️ Выбери таймфрейм", list(TIMEFRAMES.keys()), format_func=lambda x: TIMEFRAMES[x])
show_neutral = st.sidebar.checkbox("Показывать нейтральные сигналы", value=True)
take_pct = st.sidebar.slider("🎯 Take-Profit (%)", 0.5, 10.0, 3.0)
stop_pct = st.sidebar.slider("❌ Stop-Loss (%)", 0.5, 10.0, 3.0)

# Получение данных
def get_binance_data(symbol, interval="1h", limit=150):
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            "Open Time", "Open", "High", "Low", "Close", "Volume",
            "Close Time", "Quote Asset Volume", "Number of Trades",
            "Taker Buy Base", "Taker Buy Quote", "Ignore"
        ])
        df["Open Time"] = pd.to_datetime(df["Open Time"], unit="ms")
        df.set_index("Open Time", inplace=True)
        df = df[["Open", "High", "Low", "Close", "Volume"]].astype(float)
        return df
    except Exception as e:
        return None

# Анализ
def analyze(df):
    rsi = RSIIndicator(close=df["Close"])
    df["RSI"] = rsi.rsi()

    stoch = StochRSIIndicator(close=df["Close"])
    df["StochRSI"] = stoch.stochrsi()

    df.dropna(inplace=True)
    last = df.iloc[-1]

    signal = "⏸️ Нейтрально"
    if last["RSI"] < 30 and last["StochRSI"] < 0.2:
        signal = "✅ LONG"
    elif last["RSI"] > 70 and last["StochRSI"] > 0.8:
        signal = "🔻 SHORT"

    entry_price = round(last["Close"], 2)
    stop = round(entry_price * (1 - stop_pct / 100), 2) if signal == "✅ LONG" else round(entry_price * (1 + stop_pct / 100), 2)
    take = round(entry_price * (1 + take_pct / 100), 2) if signal == "✅ LONG" else round(entry_price * (1 - take_pct / 100), 2)

    # Прогноз направления
    direction = "📈 Вероятен рост" if last["RSI"] > 50 else "📉 Вероятно снижение"
    probability = round(abs(last["RSI"] - 50) / 50 * 100, 1)
    trend = f"🧠 Прогноз: {direction} ({probability}%)"

    return signal, entry_price, stop, take, df, trend

# График
def plot_chart(df, name):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 7), sharex=True, gridspec_kw={'height_ratios': [3, 1, 1]})
    
    # Цена
    ax1.plot(df.index, df["Close"], label="Цена", color="blue")
    ax1.set_title(f"{name} — Цена")
    ax1.grid(True)
    ax1.legend()

    # RSI
    ax2.plot(df.index, df["RSI"], label="RSI", color="orange")
    ax2.axhline(70, color="red", linestyle="--")
    ax2.axhline(30, color="green", linestyle="--")
    ax2.set_ylabel("RSI")
    ax2.grid(True)
    ax2.legend()

    # Stoch RSI
    ax3.plot(df.index, df["StochRSI"], label="Stoch RSI", color="purple")
    ax3.axhline(0.8, color="red", linestyle="--")
    ax3.axhline(0.2, color="green", linestyle="--")
    ax3.set_ylabel("Stoch RSI")
    ax3.grid(True)
    ax3.legend()

    plt.tight_layout()
    st.pyplot(fig)

# Основной цикл по парам
for symbol, name in PAIRS.items():
    df = get_binance_data(symbol, interval=tf_choice, limit=150)
    if df is None or len(df) < 50:
        st.error(f"{name}: Недостаточно данных")
        continue

    signal, entry, sl, tp, df, trend = analyze(df)

    if not show_neutral and signal == "⏸️ Нейтрально":
        continue

    st.markdown(f"---\n### {name}")
    st.markdown(
        f"**Сигнал:** {signal}  \n"
        f"💰 **Цена входа:** `{entry}`  \n"
        f"❌ **Стоп-лосс:** `{sl}`  \n"
        f"🎯 **Тейк-профит:** `{tp}`  \n"
        f"{trend}  \n"
        f"🕒 Время сигнала: `{df.index[-1]}`"
    )

    plot_chart(df, name)
