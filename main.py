import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from binance.client import Client
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator, StochRSIIndicator

# Binance API без ключей
client = Client()

# Доступные таймфреймы Binance
TIMEFRAMES = {
    "15 минут": "15m",
    "1 час": "1h",
    "4 часа": "4h",
    "1 день": "1d"
}

PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "PAXGUSDT"]
SYMBOL_NAMES = {
    "BTCUSDT": "BTC/USDT",
    "ETHUSDT": "ETH/USDT",
    "SOLUSDT": "SOL/USDT",
    "PAXGUSDT": "PAXG/USDT"
}

# === SIDEBAR НАСТРОЙКИ ===
st.sidebar.header("⚙️ Настройки")
timeframe_name = st.sidebar.selectbox("⏱️ Таймфрейм", list(TIMEFRAMES.keys()), index=1)
TIMEFRAME = TIMEFRAMES[timeframe_name]
stop_pct = st.sidebar.slider("📉 Стоп-лосс %", min_value=1, max_value=10, value=3)
take_pct = st.sidebar.slider("🎯 Тейк-профит %", min_value=1, max_value=10, value=3)
hide_neutral = st.sidebar.checkbox("Скрыть нейтральные сигналы", value=False)

# === ЗАГОЛОВОК ===
st.title("📡 Signal Streamer")
st.markdown("Анализ сигналов по ключевым крипто-парам на основе технических индикаторов.")

# === ФУНКЦИЯ ДАННЫХ ===
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

# === АНАЛИЗ И ВИЗУАЛИЗАЦИЯ ===
def analyze(df, symbol):
    try:
        df["EMA"] = EMAIndicator(close=df["Close"], window=50).ema_indicator()
        df["RSI"] = RSIIndicator(close=df["Close"]).rsi()
        df["StochRSI"] = StochRSIIndicator(close=df["Close"]).stochrsi()
        df.dropna(inplace=True)

        latest = df.iloc[-1]
        signal = "Нейтрально"
        if latest["RSI"] < 30 and latest["StochRSI"] < 0.2:
            signal = "LONG"
        elif latest["RSI"] > 70 and latest["StochRSI"] > 0.8:
            signal = "SHORT"

        # Кастомный стоп и тейк
        entry = latest["Close"]
        stop = entry * (1 - stop_pct / 100) if signal == "LONG" else entry * (1 + stop_pct / 100)
        take = entry * (1 + take_pct / 100) if signal == "LONG" else entry * (1 - take_pct / 100)

        # Прогноз уверенности
        score = 0
        if latest["RSI"] < 30: score += 1
        if latest["StochRSI"] < 0.2: score += 1
        if latest["Close"] > latest["EMA"]: score += 1
        confidence = int((score / 3) * 100)

        # Скрытие нейтральных по желанию
        if hide_neutral and signal == "Нейтрально":
            return

        # Цветовая заливка
        bg_color = "#d1f7c4" if signal == "LONG" else "#f8c4c4" if signal == "SHORT" else "#eeeeee"
        emoji = "🟢" if signal == "LONG" else "🔴" if signal == "SHORT" else "⏸️"

        # Визуальный блок сигнала
        st.markdown(
            f"""
            <div style="background-color:{bg_color}; padding:15px; border-radius:10px; line-height:1.6">
                <h3 style="margin-bottom:0;">{emoji} <b>{SYMBOL_NAMES[symbol]} - {signal}</b></h3>
                <p style="margin:0;">🕒 <b>Время:</b> {latest.name.strftime('%Y-%m-%d %H:%M')}</p>
                <p style="margin:0;">💰 <b>Цена входа:</b> {entry:.2f}</p>
                <p style="margin:0;">📉 <b>Стоп:</b> {stop:.2f} &nbsp;&nbsp;&nbsp; 🎯 <b>Тейк:</b> {take:.2f}</p>
                <p style="margin:0;">🤖 <b>Уверенность сигнала:</b> {confidence}%</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # График цены + стохастик RSI
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 4), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        df["Close"].plot(ax=ax1, label="Цена")
        ax1.set_title(f"{SYMBOL_NAMES[symbol]} - Цена")
        ax1.legend()

        df["StochRSI"].plot(ax=ax2, label="StochRSI", color="orange")
        ax2.axhline(0.2, linestyle="--", color="gray", linewidth=1)
        ax2.axhline(0.8, linestyle="--", color="gray", linewidth=1)
        ax2.set_ylim(0, 1)
        ax2.set_title("StochRSI")
        ax2.legend()

        st.pyplot(fig)

    except Exception as e:
        st.error(f"❌ Ошибка при анализе {symbol}: {e}")

# === ОСНОВНОЙ ЦИКЛ ПО ПАРАМ ===
for pair in PAIRS:
    df = get_binance_data(pair, interval=TIMEFRAME, limit=150)
    if df is None or len(df) < 60:
        st.warning(f"⚠️ Недостаточно данных для {SYMBOL_NAMES[pair]}")
    else:
        analyze(df, pair)
