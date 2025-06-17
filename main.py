import streamlit as st import pandas as pd import numpy as np import matplotlib.pyplot as plt from binance.client import Client from ta.momentum import StochRSIIndicator, RSIIndicator from datetime import datetime

Binance без API-ключей

client = Client()

Настройки

PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "PAXGUSDT"] SYMBOL_NAMES = { "BTCUSDT": "BTC/USDT", "ETHUSDT": "ETH/USDT", "SOLUSDT": "SOL/USDT", "PAXGUSDT": "PAXG/USDT" } TIMEFRAMES = { "15m": "15m", "1 час": "1h", "4 часа": "4h", "1 день": "1d" }

Интерфейс

st.set_page_config(layout="wide") st.title("📈 Crypto Signal Streamer") st.markdown("Получай сигналы на основе StochRSI по основным крипто-парам.")

Пользовательские параметры

selected_tf_label = st.sidebar.selectbox("Выбери таймфрейм", list(TIMEFRAMES.keys())) selected_tf = TIMEFRAMES[selected_tf_label] stop_pct = st.sidebar.number_input("Стоп-лосс (%)", value=3.0, step=0.5) take_pct = st.sidebar.number_input("Тейк-профит (%)", value=3.0, step=0.5) show_neutral = st.sidebar.checkbox("Показывать нейтральные", value=True) update_btn = st.sidebar.button("🔄 Обновить данные")

Получение данных с Binance

def get_data(symbol, interval="1h", limit=150): try: raw = client.get_klines(symbol=symbol, interval=interval, limit=limit) df = pd.DataFrame(raw, columns=[ "Open Time", "Open", "High", "Low", "Close", "Volume", "Close Time", "Quote Asset Volume", "Number of Trades", "Taker Buy Base", "Taker Buy Quote", "Ignore" ]) df["Open Time"] = pd.to_datetime(df["Open Time"], unit="ms") df.set_index("Open Time", inplace=True) df = df[["Open", "High", "Low", "Close", "Volume"]].astype(float) return df except Exception as e: return None

Анализ StochRSI

def analyze(df, symbol): try: stoch_rsi = StochRSIIndicator(close=df["Close"]) df["StochRSI"] = stoch_rsi.stochrsi() df["RSI"] = RSIIndicator(close=df["Close"]).rsi() df.dropna(inplace=True)

latest = df.iloc[-1]
    signal = "NEUTRAL"
    if latest["RSI"] < 30 and latest["StochRSI"] < 0.2:
        signal = "LONG"
    elif latest["RSI"] > 70 and latest["StochRSI"] > 0.8:
        signal = "SHORT"

    entry = latest["Close"]
    if signal == "LONG":
        stop = entry * (1 - stop_pct / 100)
        take = entry * (1 + take_pct / 100)
    elif signal == "SHORT":
        stop = entry * (1 + stop_pct / 100)
        take = entry * (1 - take_pct / 100)
    else:
        stop = take = np.nan

    # Отображение
    col = st.container()
    if signal != "NEUTRAL" or show_neutral:
        with col:
            st.markdown(f"### {SYMBOL_NAMES[symbol]}")
            st.markdown(f"""
            <div style="background-color: {'#d1f7c4' if signal=='LONG' else '#ffd1d1' if signal=='SHORT' else '#f0f0f0'};
                        padding: 10px; border-radius: 8px;">
                <strong>{'✅ LONG' if signal == 'LONG' else '🔻 SHORT' if signal == 'SHORT' else '⏸️ NEUTRAL'}</strong><br>
                <strong>Время:</strong> {df.index[-1]}<br>
                <strong>Цена входа:</strong> {entry:.2f}<br>
                <strong>Стоп-лосс:</strong> {stop:.2f} ({stop_pct}%)<br>
                <strong>Тейк-профит:</strong> {take:.2f} ({take_pct}%)
            </div>
            """, unsafe_allow_html=True)

            # График цены + StochRSI
            fig, ax = plt.subplots(2, 1, figsize=(8, 5), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
            df["Close"].plot(ax=ax[0], label="Цена", color="black")
            ax[0].set_title(f"{SYMBOL_NAMES[symbol]} Цена")
            ax[0].legend()

            df["StochRSI"].plot(ax=ax[1], color="purple", label="StochRSI")
            ax[1].axhline(0.8, color='red', linestyle='--')
            ax[1].axhline(0.2, color='green', linestyle='--')
            ax[1].set_ylim(0, 1)
            ax[1].set_title("Stochastic RSI")
            ax[1].legend()

            st.pyplot(fig)

except Exception as e:
    st.error(f"{SYMBOL_NAMES[symbol]} — ошибка анализа: {e}")

Основной цикл

if update_btn or True: for pair in PAIRS: df = get_data(pair, interval=selected_tf) if df is not None: analyze(df, pair) else: st.error(f"❌ Не удалось загрузить данные для {SYMBOL_NAMES[pair]}")

