import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION ---
SYMBOLS = {
    "NIFTY 50": "^NSEI",
    "BANK NIFTY": "^NSEBANK",
    "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
    "SENSEX": "^BSESN"
}

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    div[data-testid="metric-container"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        padding: 10px;
        border-radius: 10px;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- APP LOGIC ---
def get_data(ticker, interval, period="5d"):
    data = yf.download(ticker, period=period, interval=interval, progress=False)
    return data

def main():
    st.title("⚡ QUANT-X: Indian F&O Terminal")
    
    # Auto Refresh Every 30 Seconds
    st_autorefresh(interval=30000, key="datarefresh")

    # Sidebar
    selected_name = st.sidebar.selectbox("Market Index", list(SYMBOLS.keys()))
    ticker = SYMBOLS[selected_name]
    timeframe = st.sidebar.radio("Timeframe", ["1m", "5m", "15m", "1h"], index=1)

    # Fetch Data
    df = get_data(ticker, timeframe)
    daily_df = get_data(ticker, "1d", period="2d")
    
    if not df.empty and len(daily_df) >= 2:
        # Calculate Technicals
        df['EMA_9'] = ta.ema(df['Close'], length=9)
        df['EMA_21'] = ta.ema(df['Close'], length=21)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        # Fibonacci Pivots
        prev_day = daily_df.iloc[-2]
        high, low, close = prev_day['High'], prev_day['Low'], prev_day['Close']
        p = (high + low + close) / 3
        r1 = p + 0.382 * (high - low)
        r2 = p + 0.618 * (high - low)
        s1 = p - 0.382 * (high - low)
        s2 = p - 0.618 * (high - low)

        # Signal Logic
        ltp = df['Close'].iloc[-1]
        rsi_val = df['RSI'].iloc[-1]
        atr_val = df['ATR'].iloc[-1]
        
        if df['EMA_9'].iloc[-1] > df['EMA_21'].iloc[-1] and rsi_val > 55:
            signal = "BUY"
            color = "#00FFA3"
            sl = ltp - (1.5 * atr_val)
            tgt = ltp + (3 * atr_val)
        elif df['EMA_9'].iloc[-1] < df['EMA_21'].iloc[-1] and rsi_val < 45:
            signal = "SELL"
            color = "#FF4B4B"
            sl = ltp + (1.5 * atr_val)
            tgt = ltp - (3 * atr_val)
        else:
            signal = "NEUTRAL"
            color = "gray"
            sl, tgt = 0, 0

        # UI: Top Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("LTP", f"₹{ltp:,.2f}")
        m2.metric("Signal", signal)
        m3.metric("Stoploss", f"{sl:.2f}")
        m4.metric("Target", f"{tgt:.2f}")

        # UI: Chart
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price")])
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_9'], line=dict(color='#00d2ff', width=1), name="EMA 9"))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_21'], line=dict(color='#ff9ff3', width=1), name="EMA 21"))
        
        # S/R Lines
        for level, name, col in zip([r2, r1, s1, s2], ["R2", "R1", "S1", "S2"], ["red", "orange", "lightgreen", "green"]):
            fig.add_hline(y=level, line_dash="dash", line_color=col, annotation_text=name)

        fig.update_layout(template="plotly_dark", height=600, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # Pivot Table Sidebar
        st.sidebar.subheader("Fibonacci Levels")
        st.sidebar.table(pd.DataFrame({
            "Level": ["R2", "R1", "Pivot", "S1", "S2"],
            "Price": [r2, r1, p, s1, s2]
        }))

if __name__ == "__main__":
    main()
