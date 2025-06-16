import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from binance.client import Client
from ta.momentum import RSIIndicator, StochRSIIndicator

# Binance API
client = Client()

# Константы
PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "PAXGUSDT"]
SYMBOL_NAMES = {
    "BTCUSDT": "BTC/USDT",
    "ETHUSDT": "ETH/USDT",
    "SOLUSDT": "SOL/USDT",
    "PAXGUSDT": "PAXG/USDT"
}
TIMEFRAMES = ["15m", "1h", "4h", "1d"]
LIMIT = 150

# Заголовок
st.title("📊 Крипто-сигналы (Binance)")

# Панель управления
selected_tf = st.selectbox("Выберите таймфрейм:", TIMEFRAMES, index=1)
hide_neutral = st.checkbox("Скрыть нейтральные сигналы")

# Получение данных с Binance
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
    except Exception:
        return None

# Анализ сигналов
def analyze(df, symbol):
    rsi = RSIIndicator(close=df["Close"])
    df["RSI"] = rsi.rsi()

    stoch = StochRSIIndicator(close=df["Close"])
    df["StochRSI"] = stoch.stochrsi()

    df.dropna(inplace=True)
    last = df.iloc[-1]

    signal = "⏸️ Нейтрально"
    bgcolor = "#f0f0f0"
    if last["RSI"] < 30 and last["StochRSI"] < 0.2:
        signal = "🟩 ✅ LONG"
        bgcolor = "#d4f4dd"
    elif last["RSI"] > 70 and last["StochRSI"] > 0.8:
        signal = "🟥 🔻 SHORT"
        bgcolor = "#f8d2d2"

    if hide_neutral and "Нейтрально" in signal:
        return

    entry_price = round(last["Close"], 2)
    stop_loss = round(entry_price * (0.97 if "LONG" in signal else 1.03), 2)
    take_profit = round(entry_price * (1.03 if "LONG" in signal else 0.97), 2)

    # Блок сигнала
    with st.container():
        st.markdown(f"## {SYMBOL_NAMES[symbol]} ({selected_tf})")
        st.markdown(
            f"""
            <div style="background-color:{bgcolor};padding:10px;border-radius:10px;">
                <b>{signal}</b><br>
                ⏱️ Время: {df.index[-1]}<br>
                💰 Вход: {entry_price}<br>
                📍 Стоп: {stop_loss} 🎯 Тейк: {take_profit}
            </div>
            """, unsafe_allow_html=True
        )

        # График: цена + Stoch RSI
        fig, ax1 = plt.subplots(figsize=(7, 3))
        ax1.plot(df.index, df["Close"], color="black", label="Цена")
        ax1.set_ylabel("Цена", color="black")

        ax2 = ax1.twinx()
        ax2.plot(df.index, df["StochRSI"], color="purple", alpha=0.5, label="StochRSI")
        ax2.set_ylabel("Stoch RSI", color="purple")
        ax2.set_ylim(0, 1)

        fig.suptitle(f"{SYMBOL_NAMES[symbol]} — Цена и Stoch RSI")
        fig.tight_layout()
        st.pyplot(fig)

# Основной цикл
for pair in PAIRS:
    df = get_binance_data(pair, interval=selected_tf, limit=LIMIT)
    if df is not None and len(df) >= 60:
        analyze(df, pair)
    else:
        st.markdown(f"## {SYMBOL_NAMES[pair]}")
        st.error("❌ Недостаточно данных")
