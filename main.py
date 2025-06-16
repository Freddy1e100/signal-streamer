import streamlit as st
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
from binance.client import Client
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator, StochRSIIndicator

# Настройки Binance (без API-ключей, публичный доступ)
client = Client()

# Пары и параметры
PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "PAXGUSDT"]
SYMBOL_NAMES = {
    "BTCUSDT": "BTC/USDT",
    "ETHUSDT": "ETH/USDT",
    "SOLUSDT": "SOL/USDT",
    "PAXGUSDT": "PAXG/USDT"
}
TIMEFRAME = "1h"
LIMIT = 150

st.set_page_config(page_title="Signal Streamer", layout="wide")
st.title("📈 Signal Streamer — Крипто-сигналы")
st.markdown("Получай простые технические сигналы по ключевым парам на Binance.")

if st.button("🔄 Обновить сигналы"):
    st.experimental_rerun()

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

def analyze(df, symbol):
    try:
        ema = EMAIndicator(close=df["Close"], window=50)
        df["EMA50"] = ema.ema_indicator()

        rsi = RSIIndicator(close=df["Close"])
        df["RSI"] = rsi.rsi()

        stoch = StochRSIIndicator(close=df["Close"])
        df["StochRSI"] = stoch.stochrsi()

        df.dropna(inplace=True)
        last = df.iloc[-1]

        signal = "⏸️ Нейтрально"
        bg_color = "#F0F2F6"
        if last["RSI"] < 30 and last["StochRSI"] < 0.2 and last["Close"] > last["EMA50"]:
            signal = "🟢 **LONG**"
            bg_color = "#d1fadf"
        elif last["RSI"] > 70 and last["StochRSI"] > 0.8 and last["Close"] < last["EMA50"]:
            signal = "🔴 **SHORT**"
            bg_color = "#ffd6d6"

        entry_price = round(last["Close"], 2)
        stop_loss = round(entry_price * (0.97 if "LONG" in signal else 1.03), 2)
        take_profit = round(entry_price * (1.03 if "LONG" in signal else 0.97), 2)

        with st.container():
            st.markdown(f"### {SYMBOL_NAMES[symbol]}")
            col1, col2 = st.columns([2, 3])
            with col1:
                st.markdown(f"""
                <div style="background-color: {bg_color}; padding: 10px; border-radius: 10px;">
                    <h4>{signal}</h4>
                    ⏱️ Время: {df.index[-1]}  
                    💰 Вход: {entry_price}  
                    📍 Стоп: {stop_loss}  
                    🎯 Тейк: {take_profit}
                </div>
                """, unsafe_allow_html=True)
            with col2:
                fig, ax = plt.subplots(figsize=(6, 3))
                df["Close"].plot(ax=ax, label="Цена", color='black')
                df["EMA50"].plot(ax=ax, label="EMA50", color='orange')
                ax.set_title(f"{SYMBOL_NAMES[symbol]} — Цена и EMA50")
                ax.legend()
                st.pyplot(fig)

    except Exception as e:
        st.markdown(f"### {SYMBOL_NAMES[symbol]}")
        st.error(f"Ошибка: {e}")

for pair in PAIRS:
    df = get_binance_data(pair, interval=TIMEFRAME, limit=LIMIT)
    if df is None or len(df) < 60:
        st.markdown(f"### {SYMBOL_NAMES[pair]}")
        st.error("❌ Недостаточно данных")
    else:
        analyze(df, pair)
