import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import warnings
warnings.filterwarnings("ignore")

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QuantX · F&O Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  /* ── Global Reset ── */
  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0E1117;
    color: #E0E0E0;
  }
  .stApp { background-color: #0E1117; }

  /* ── Hide Streamlit Chrome ── */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 1.5rem 2rem 2rem 2rem; max-width: 100%; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: #13161E;
    border-right: 1px solid #1E2330;
  }
  [data-testid="stSidebar"] .css-1d391kg { padding-top: 1rem; }

  /* ── Wordmark ── */
  .quantx-wordmark {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #FFFFFF;
    line-height: 1;
    margin-bottom: 0.15rem;
  }
  .quantx-wordmark span { color: #00FFA3; }
  .quantx-tagline {
    font-size: 0.68rem;
    color: #555E78;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 500;
    margin-bottom: 1.6rem;
  }

  /* ── Metric Cards ── */
  .metric-card {
    background: #13161E;
    border: 1px solid #1E2330;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    position: relative;
    overflow: hidden;
  }
  .metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #00FFA3 0%, transparent 100%);
    opacity: 0.6;
  }
  .metric-card.sell-card::before {
    background: linear-gradient(90deg, #FF4B4B 0%, transparent 100%);
  }
  .metric-card.neutral-card::before {
    background: linear-gradient(90deg, #5B6BFF 0%, transparent 100%);
  }
  .metric-label {
    font-size: 0.67rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #555E78;
    margin-bottom: 0.4rem;
  }
  .metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.45rem;
    font-weight: 700;
    color: #FFFFFF;
    line-height: 1;
  }
  .metric-sub {
    font-size: 0.72rem;
    color: #555E78;
    margin-top: 0.3rem;
    font-weight: 400;
  }
  .signal-buy  { color: #00FFA3 !important; }
  .signal-sell { color: #FF4B4B !important; }
  .signal-none { color: #5B6BFF !important; }

  /* ── Section Headers ── */
  .section-header {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #555E78;
    border-bottom: 1px solid #1E2330;
    padding-bottom: 0.4rem;
    margin-bottom: 0.8rem;
    margin-top: 1.2rem;
  }

  /* ── Pivot Table ── */
  .pivot-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
  }
  .pivot-table td, .pivot-table th {
    padding: 0.55rem 0.8rem;
    border-bottom: 1px solid #1A1E2A;
    text-align: right;
  }
  .pivot-table th {
    color: #555E78;
    font-size: 0.65rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    text-align: left;
  }
  .pivot-table td:first-child { text-align: left; color: #777E9A; }
  .r-level { color: #FF4B4B; }
  .s-level { color: #00FFA3; }
  .p-level { color: #5B6BFF; }

  /* ── Trade Log ── */
  .trade-log-entry {
    background: #13161E;
    border: 1px solid #1E2330;
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .trade-log-time {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #555E78;
  }
  .trade-log-signal {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
  }
  .trade-log-signal.buy  { background: rgba(0,255,163,0.12); color: #00FFA3; }
  .trade-log-signal.sell { background: rgba(255,75,75,0.12);  color: #FF4B4B; }
  .trade-log-price {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #E0E0E0;
  }

  /* ── Kill Switch ── */
  .kill-switch-off {
    background: rgba(255,75,75,0.08);
    border: 1px solid #FF4B4B44;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    font-size: 0.75rem;
    color: #FF4B4B;
    text-align: center;
    font-weight: 600;
    letter-spacing: 0.06em;
    margin-top: 0.5rem;
  }
  .kill-switch-on {
    background: rgba(0,255,163,0.08);
    border: 1px solid #00FFA344;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    font-size: 0.75rem;
    color: #00FFA3;
    text-align: center;
    font-weight: 600;
    letter-spacing: 0.06em;
    margin-top: 0.5rem;
  }

  /* ── Status Badge ── */
  .status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  .status-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #00FFA3;
    box-shadow: 0 0 6px #00FFA3;
    animation: pulse 2s infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  /* ── Selectbox / Slider Overrides ── */
  [data-testid="stSelectbox"] > div > div,
  [data-testid="stRadio"] label {
    color: #E0E0E0 !important;
  }
  .stSelectbox [data-baseweb="select"] > div {
    background-color: #1A1E2A !important;
    border-color: #1E2330 !important;
  }
  div[data-testid="stMarkdownContainer"] p { color: #E0E0E0; }

  /* ── Divider ── */
  hr { border-color: #1E2330 !important; }
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTS ──────────────────────────────────────────────────────────────────
INDICES = {
    "NIFTY 50":    "^NSEI",
    "BANK NIFTY":  "^NSEBANK",
    "FIN NIFTY":   "^CNXFIN",
    "SENSEX":      "^BSESN",
    "BSE BANKEX":  "BSE-BANKEX.BO",
}
TIMEFRAMES = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "60m"}
TF_PERIODS  = {"1m": "1d",  "5m": "3d",  "15m": "5d",  "1h": "30d"}

# ─── DATA FETCHING ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=30, show_spinner=False)
def fetch_data(ticker: str, interval: str) -> pd.DataFrame:
    period = TF_PERIODS.get(interval, "5d")
    df = yf.download(ticker, period=period, interval=interval,
                     auto_adjust=True, progress=False)
    if df is None or df.empty:
        return pd.DataFrame()
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    df.dropna(inplace=True)
    return df

@st.cache_data(ttl=60, show_spinner=False)
def fetch_prev_day_ohlc(ticker: str) -> dict:
    df = yf.download(ticker, period="5d", interval="1d",
                     auto_adjust=True, progress=False)
    if df is None or df.empty or len(df) < 2:
        return {}
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    row = df.iloc[-2]
    return {
        "high":  float(row["High"]),
        "low":   float(row["Low"]),
        "close": float(row["Close"]),
    }

# ─── PIVOT CALCULATIONS ──────────────────────────────────────────────────────────
def calculate_pivots(ohlc: dict) -> dict:
    if not ohlc:
        return {}
    H, L, C = ohlc["high"], ohlc["low"], ohlc["close"]
    rng = H - L
    P  = (H + L + C) / 3
    R1 = P + 0.382 * rng
    R2 = P + 0.618 * rng
    S1 = P - 0.382 * rng
    S2 = P - 0.618 * rng
    return {"S2": S2, "S1": S1, "P": P, "R1": R1, "R2": R2}

# ─── INDICATOR CALCULATIONS ──────────────────────────────────────────────────────
def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 22:
        return df
    df = df.copy()
    df["EMA9"]  = ta.ema(df["Close"], length=9)
    df["EMA21"] = ta.ema(df["Close"], length=21)
    df["RSI"]   = ta.rsi(df["Close"], length=14)
    atr_df      = ta.atr(df["High"], df["Low"], df["Close"], length=14)
    df["ATR"]   = atr_df
    return df

# ─── SIGNAL GENERATION ───────────────────────────────────────────────────────────
def generate_signal(df: pd.DataFrame, kill_switch: bool) -> dict:
    default = {"signal": "NONE", "entry": None, "sl": None, "target": None,
                "rsi": None, "atr": None, "ema9": None, "ema21": None}
    if kill_switch or df.empty or len(df) < 22:
        return default
    row = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else row

    try:
        close  = float(row["Close"])
        ema9   = float(row["EMA9"])
        ema21  = float(row["EMA21"])
        rsi    = float(row["RSI"])
        atr    = float(row["ATR"])
        prev_h = float(prev["High"])
        prev_l = float(prev["Low"])
    except Exception:
        return default

    if pd.isna(ema9) or pd.isna(ema21) or pd.isna(rsi) or pd.isna(atr):
        return default

    signal = "NONE"
    sl = target = None

    # BUY
    if (close > ema9 and ema9 > ema21 and rsi > 60 and close > prev_h):
        signal = "BUY"
        sl     = close - 1.5 * atr
        target = close + 2 * (close - sl)

    # SELL
    elif (close < ema9 and ema9 < ema21 and rsi < 40 and close < prev_l):
        signal = "SELL"
        sl     = close + 1.5 * atr
        target = close - 2 * (sl - close)

    return {
        "signal": signal, "entry": close,
        "sl": sl, "target": target,
        "rsi": rsi, "atr": atr, "ema9": ema9, "ema21": ema21,
    }

# ─── CHART ───────────────────────────────────────────────────────────────────────
def build_chart(df: pd.DataFrame, pivots: dict, sig: dict, label: str) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.04,
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        increasing=dict(line=dict(color="#00FFA3", width=1),
                        fillcolor="rgba(0,255,163,0.55)"),
        decreasing=dict(line=dict(color="#FF4B4B", width=1),
                        fillcolor="rgba(255,75,75,0.55)"),
        name="Price", showlegend=False,
    ), row=1, col=1)

    # EMAs
    if "EMA9" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["EMA9"],
            line=dict(color="#FFD700", width=1.2),
            name="EMA 9", hoverinfo="skip",
        ), row=1, col=1)
    if "EMA21" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["EMA21"],
            line=dict(color="#AA80FF", width=1.2),
            name="EMA 21", hoverinfo="skip",
        ), row=1, col=1)

    # Pivot S/R lines
    pivot_styles = {
        "R2": ("#FF4B4B", "dash"),
        "R1": ("#FF8080", "dot"),
        "P":  ("#5B6BFF", "dash"),
        "S1": ("#80FFC8", "dot"),
        "S2": ("#00FFA3", "dash"),
    }
    for lvl, val in pivots.items():
        color, dash = pivot_styles.get(lvl, ("#888", "dash"))
        fig.add_hline(
            y=val, line=dict(color=color, width=0.8, dash=dash),
            annotation_text=f" {lvl} {val:,.0f}",
            annotation_font=dict(color=color, size=10),
            annotation_position="right",
            row=1, col=1,
        )

    # RSI subplot
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["RSI"],
            line=dict(color="#00FFA3", width=1.2),
            name="RSI", fill="tozeroy",
            fillcolor="rgba(0,255,163,0.06)",
        ), row=2, col=1)
        for level, color in [(60, "#00FFA3"), (40, "#FF4B4B"), (50, "#333C55")]:
            fig.add_hline(y=level, line=dict(color=color, width=0.6, dash="dot"),
                          row=2, col=1)

    # Layout
    fig.update_layout(
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        font=dict(family="JetBrains Mono, monospace", color="#777E9A", size=11),
        margin=dict(l=10, r=80, t=30, b=10),
        legend=dict(
            bgcolor="#13161E", bordercolor="#1E2330", borderwidth=1,
            font=dict(size=10, color="#E0E0E0"),
            x=0.01, y=0.98,
        ),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#13161E", bordercolor="#1E2330",
                        font=dict(color="#E0E0E0", size=11)),
    )
    fig.update_xaxes(
        gridcolor="#1A1E2A", showgrid=True,
        zeroline=False, showspikes=True, spikecolor="#333C55",
        spikedash="dot", spikethickness=1,
    )
    fig.update_yaxes(
        gridcolor="#1A1E2A", showgrid=True, zeroline=False,
        tickformat=",.0f",
    )
    fig.update_yaxes(title_text="RSI", row=2, col=1,
                     tickformat=".0f", range=[0, 100])
    return fig

# ─── TRADE LOG ───────────────────────────────────────────────────────────────────
def update_trade_log(sig: dict, index_name: str):
    if "trade_log" not in st.session_state:
        st.session_state.trade_log = []
    if sig["signal"] != "NONE" and sig["entry"] is not None:
        entry = {
            "time":   datetime.now().strftime("%H:%M:%S"),
            "index":  index_name,
            "signal": sig["signal"],
            "entry":  sig["entry"],
            "sl":     sig["sl"],
            "target": sig["target"],
        }
        # Avoid duplicate consecutive logs
        if not st.session_state.trade_log or \
           st.session_state.trade_log[-1]["signal"] != sig["signal"] or \
           st.session_state.trade_log[-1]["index"] != index_name:
            st.session_state.trade_log.insert(0, entry)
            st.session_state.trade_log = st.session_state.trade_log[:10]

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="quantx-wordmark">Quant<span>X</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="quantx-tagline">F&O Intelligence Terminal</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Market Index</div>', unsafe_allow_html=True)
    selected_label = st.selectbox("", list(INDICES.keys()), label_visibility="collapsed")
    ticker = INDICES[selected_label]

    st.markdown('<div class="section-header">Timeframe</div>', unsafe_allow_html=True)
    tf_label = st.radio("", list(TIMEFRAMES.keys()), horizontal=True, label_visibility="collapsed")
    interval = TIMEFRAMES[tf_label]

    st.markdown('<div class="section-header">Kill Switch</div>', unsafe_allow_html=True)
    kill_switch = st.toggle("Halt All Signals", value=False)
    if kill_switch:
        st.markdown('<div class="kill-switch-off">⛔ TRADING HALTED</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="kill-switch-on">✅ SIGNALS ACTIVE</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">Auto Refresh</div>', unsafe_allow_html=True)
    refresh_sec = st.slider("Interval (sec)", 15, 120, 30, 5, label_visibility="collapsed")
    if AUTOREFRESH_AVAILABLE:
        count = st_autorefresh(interval=refresh_sec * 1000, key="autorefresh")

    st.markdown("---")
    now = datetime.now()
    mkt_open  = now.replace(hour=9, minute=15, second=0, microsecond=0)
    mkt_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    is_open   = mkt_open <= now <= mkt_close and now.weekday() < 5

    dot = "🟢" if is_open else "🔴"
    status_text = "LIVE" if is_open else "CLOSED"
    st.markdown(
        f'<div class="status-badge">'
        f'<span class="status-dot" style="background:{"#00FFA3" if is_open else "#FF4B4B"};'
        f'box-shadow:0 0 6px {"#00FFA3" if is_open else "#FF4B4B"}"></span>'
        f'<span style="color:{"#00FFA3" if is_open else "#FF4B4B"};font-size:0.7rem;'
        f'font-weight:700;letter-spacing:0.1em">NSE {status_text}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="font-size:0.66rem;color:#555E78;margin-top:0.3rem">'
        f'{now.strftime("%d %b %Y · %H:%M:%S")}</p>',
        unsafe_allow_html=True,
    )

# ─── FETCH & COMPUTE ────────────────────────────────────────────────────────────
with st.spinner("Fetching live data…"):
    df_raw  = fetch_data(ticker, interval)
    prev_d  = fetch_prev_day_ohlc(ticker)

if df_raw.empty:
    st.error("⚠️ No data returned. Market may be closed or the ticker is unavailable.")
    st.stop()

df_ind = calculate_indicators(df_raw)
pivots = calculate_pivots(prev_d)
sig    = generate_signal(df_ind, kill_switch)
update_trade_log(sig, selected_label)

# Current metrics
try:
    ltp        = float(df_ind["Close"].iloc[-1])
    open_price = float(df_ind["Open"].iloc[0])
    day_chg    = ltp - open_price
    day_chg_pct = (day_chg / open_price * 100) if open_price else 0
    volatility = float(df_ind["ATR"].iloc[-1]) if "ATR" in df_ind.columns else 0.0
except Exception:
    ltp = open_price = day_chg = day_chg_pct = volatility = 0.0

# ─── TOP METRIC CARDS ────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

with c1:
    chg_color = "#00FFA3" if day_chg >= 0 else "#FF4B4B"
    chg_arrow = "▲" if day_chg >= 0 else "▼"
    st.markdown(f"""
    <div class="metric-card neutral-card">
      <div class="metric-label">LTP · {selected_label}</div>
      <div class="metric-value">₹{ltp:,.2f}</div>
      <div class="metric-sub" style="color:{chg_color}">
        {chg_arrow} {abs(day_chg):,.2f} ({abs(day_chg_pct):.2f}%) today
      </div>
    </div>""", unsafe_allow_html=True)

with c2:
    s = sig["signal"]
    sc = "signal-buy" if s == "BUY" else ("signal-sell" if s == "SELL" else "signal-none")
    card_cls = "metric-card" if s == "BUY" else ("sell-card metric-card" if s == "SELL" else "neutral-card metric-card")
    icon = "🔼" if s == "BUY" else ("🔽" if s == "SELL" else "⏸")
    rsi_val = f"RSI {sig['rsi']:.1f}" if sig['rsi'] else "—"
    st.markdown(f"""
    <div class="{card_cls}">
      <div class="metric-label">Signal · {tf_label}</div>
      <div class="metric-value {sc}">{icon} {s}</div>
      <div class="metric-sub">{rsi_val} · EMA confluence</div>
    </div>""", unsafe_allow_html=True)

with c3:
    sl_val  = f"₹{sig['sl']:,.2f}" if sig['sl'] else "—"
    sl_pct  = (abs(ltp - sig['sl']) / ltp * 100) if sig['sl'] and ltp else 0
    sl_color = "#FF4B4B" if sig['sl'] else "#555E78"
    st.markdown(f"""
    <div class="metric-card sell-card">
      <div class="metric-label">Stop Loss · 1.5× ATR</div>
      <div class="metric-value" style="color:{sl_color}">{sl_val}</div>
      <div class="metric-sub">Risk: {sl_pct:.2f}% · ATR {volatility:,.1f}</div>
    </div>""", unsafe_allow_html=True)

with c4:
    tgt_val = f"₹{sig['target']:,.2f}" if sig['target'] else "—"
    rr_dist = abs(sig['target'] - ltp) if sig['target'] and ltp else 0
    tgt_color = "#00FFA3" if sig['target'] else "#555E78"
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">Target · 1:2 R/R</div>
      <div class="metric-value" style="color:{tgt_color}">{tgt_val}</div>
      <div class="metric-sub">Reward: ₹{rr_dist:,.2f} potential</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── MAIN CHART ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Price Action · Candlestick with S/R Overlays</div>',
            unsafe_allow_html=True)
fig = build_chart(df_ind, pivots, sig, selected_label)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ─── BOTTOM ROW ─────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.markdown('<div class="section-header">Fibonacci Pivot Levels</div>', unsafe_allow_html=True)
    if pivots:
        rows_html = ""
        level_meta = {
            "R2": ("Resistance 2", "r-level"),
            "R1": ("Resistance 1", "r-level"),
            "P":  ("Pivot",        "p-level"),
            "S1": ("Support 1",    "s-level"),
            "S2": ("Support 2",    "s-level"),
        }
        for k in ["R2", "R1", "P", "S1", "S2"]:
            v = pivots.get(k, 0)
            name, cls = level_meta[k]
            diff     = ((v - ltp) / ltp * 100) if ltp else 0
            diff_str = f"+{diff:.2f}%" if diff > 0 else f"{diff:.2f}%"
            rows_html += f"""
            <tr>
              <td>{name}</td>
              <td class="{cls}"><b>{k}</b></td>
              <td class="{cls}">₹{v:,.2f}</td>
              <td style="color:#555E78">{diff_str}</td>
            </tr>"""
        st.markdown(f"""
        <table class="pivot-table">
          <thead><tr>
            <th>Level</th><th>Label</th><th>Price</th><th>vs LTP</th>
          </tr></thead>
          <tbody>{rows_html}</tbody>
        </table>""", unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#555E78;font-size:0.8rem">Pivot data unavailable.</p>',
                    unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="section-header">Live Trade Log · Last 5 Signals</div>',
                unsafe_allow_html=True)
    log = st.session_state.get("trade_log", [])
    if not log:
        st.markdown(
            '<p style="color:#555E78;font-size:0.8rem;padding:0.5rem 0">'
            'No signals generated yet. Waiting for confluence…</p>',
            unsafe_allow_html=True)
    else:
        for entry in log[:5]:
            sc    = "buy" if entry["signal"] == "BUY" else "sell"
            sl_s  = f"SL ₹{entry['sl']:,.2f}" if entry['sl'] else ""
            tgt_s = f"· T ₹{entry['target']:,.2f}" if entry['target'] else ""
            st.markdown(f"""
            <div class="trade-log-entry">
              <div>
                <div class="trade-log-time">{entry['time']} · {entry['index']}</div>
                <div class="trade-log-price">₹{entry['entry']:,.2f} &nbsp; <span style="color:#555E78;font-size:0.7rem">{sl_s} {tgt_s}</span></div>
              </div>
              <span class="trade-log-signal {sc}">{entry['signal']}</span>
            </div>""", unsafe_allow_html=True)
