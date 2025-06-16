import streamlit as st
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
from binance.client import Client
from ta.momentum import RSIIndicator, StochRSIIndicator

# Настройки Binance (без ключей)
client = Client()

# Пары для анализа
PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "PAXGUSDT"]
SYMBOL_NAMES = {
    "BTCUSDT": "BTC/USDT",
    "ETHUSDT": "ETH/USDT",
    "SOLUSDT": "SOL/USDT",
    "PAXGUSDT": "PAXG/USDT"
}
TIMEFRAME = "1h"
LIMIT = 150

# Интерфейс
st.set_page_config(page_title="Crypto Signals", layout="wide")
st.title("📈 Крипто-сигналы (Binance)")
st.markdown("Получай простые технические сигналы по ключевым парам.")

refresh = st.button("🔄 Обновить сигналы")

# Получение исторических данных
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

# Анализ пары
def analyze(df, symbol):
    try:
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
        stop_loss = round(entry_price * (0.97 if signal == "✅ LONG" else 1.03), 2)
        take_profit = round(entry_price * (1.03 if signal == "✅ LONG" else 0.97), 2)

        # График цены и StochRSI
        fig, ax1 = plt.subplots(figsize=(7, 4))
        ax2 = ax1.twinx()

        df["Close"].plot(ax=ax1, color="black", label="Цена")
        df["StochRSI"].plot(ax=ax2, color="purple", label="StochRSI", alpha=0.6)

        ax1.set_ylabel("Цена", color="black")
        ax2.set_ylabel("StochRSI", color="purple")
        ax2.axhline(0.8, color='red', linestyle='--', linewidth=1)
        ax2.axhline(0.2, color='green', linestyle='--', linewidth=1)
        ax2.set_ylim(0, 1)

        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='upper left')
        ax1.grid(True)
        ax1.set_title(f"{SYMBOL_NAMES[symbol]} — Цена и Stoch RSI")

        # Вывод
        st.pyplot(fig)
        with st.container():
            st.markdown(f"### {SYMBOL_NAMES[symbol]}")
            st.markdown(f"""
            **{signal}**  
            ⏱️ Время сигнала: `{df.index[-1]}`  
            💰 Цена входа: `{entry_price}`  
            📍 Стоп-лосс: `{stop_loss}`  
            🎯 Тейк-профит: `{take_profit}`
            """)
    except Exception as e:
        st.markdown(f"### {SYMBOL_NAMES[symbol]}")
        st.error(f"Ошибка: {e}")

# Основной вывод
if refresh or True:
    for pair in PAIRS:
        df = get_binance_data(pair, interval=TIMEFRAME, limit=LIMIT)
        if df is None or len(df) < 60:
            st.markdown(f"### {SYMBOL_NAMES[pair]}")
            st.error("❌ Недостаточно данных")
        else:
            analyze(df, pair)
