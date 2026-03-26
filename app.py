import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
import numpy as np
import requests

# ==========================================
# 1. 系統核心設定與防封鎖機制 (解決 Rate Limit 問題)
# ==========================================
st.set_page_config(page_title="全齡智能理財戰情室 Pro Max", layout="wide", page_icon="📈")

# 建立一個全局 Session 並偽裝成一般瀏覽器，避免被 Yahoo Finance 封鎖
def get_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    return session

TICKER_MAP = {
    "台積電": "2330.TW", "0050": "0050.TW", "0056": "0056.TW", "00878": "00878.TW",
    "美債20年": "00679B.TW", "蘋果": "AAPL", "微軟": "MSFT", "輝達": "NVDA", "特斯拉": "TSLA"
}

def parse_ticker(user_input):
    clean_input = str(user_input).strip().upper()
    if clean_input in TICKER_MAP: return TICKER_MAP[clean_input]
    if clean_input.isdigit() and len(clean_input) == 4: return f"{clean_input}.TW"
    return clean_input

@st.cache_data(ttl=43200) # 快取 12 小時
def fetch_stock_data(ticker_symbol):
    session = get_session()
    stock = yf.Ticker(ticker_symbol, session=session)
    hist = stock.history(period="1y")
    info = stock.info
    return hist, info

# ==========================================
# 網頁主視覺
# ==========================================
st.title("🌟 終極全齡智能理財與投資決策戰情室")
st.write("已啟動防封鎖引擎。本系統為您整合目標試算、長短線雙引擎診斷與全資產管理。")
st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 1. 財富目標試算", 
    "📊 2. AI 深度診斷 (雙引擎)", 
    "📈 3. 多標的績效大PK", 
    "⚖️ 4. 理想資產配置", 
    "💼 5. 我的真實總資產"
])

# ==========================================
# Tab 1: 財富目標與複利試算
# ==========================================
with tab1:
    st.header("🎯 第一步：精算您的專屬財富藍圖")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        init_inv = st.number_input("1. 目前單筆本金 (元)", value=100000, step=10000)
        mon_inv = st.number_input("2. 每月定期定額 (元)", value=10000, step=1000)
        inv_years = st.slider("3. 預計投資年限 (年)", 1, 50, 20)
    with col_p2:
        risk_prof = st.selectbox("您的風險屬性？", ["保守型 (3%)", "穩健型 (6%)", "積極型 (9%)"])
        exp_ret = 3.0 if "保守" in risk_prof else 6.0 if "穩健" in risk_prof else 9.0
    
    if st.button("🚀 啟動財富藍圖運算", type="primary"):
        y_list, p_list, i_list = [], [], []
        total_m = total_p = init_inv
        for y in range(1, inv_years + 1):
            total_m += (mon_inv * 12); total_p += (mon_inv * 12)
            total_m += total_m * (exp_ret / 100)
            y_list.append(y); p_list.append(total_p); i_list.append(total_m - total_p)
        st.success(f"### 🎉 {inv_years} 年後預估總資產： **{total_m:,.0f} 元**")
        fig_plan = px.area(pd.DataFrame({"年": y_list, "本金": p_list, "複利": i_list}), x="年", y=["本金", "複利"], title="📈 財富成長軌跡")
        st.plotly_chart(fig_plan, use_container_width=True)

# ==========================================
# Tab 2: 單一標的深度診斷 (核心 AI 建議)
# ==========================================
with tab2:
    st.header("📊 第二步：單一標的 AI 深度診斷")
    c_s1, c_s2 = st.columns([2, 1])
    with c_s1:
        raw_ticker = st.text_input("🔍 輸入標的代號或名稱：", "0050")
    with c_s2:
        trade_mode = st.radio("⚙️ 操作屬性：", ["🐢 穩健長線 (適合存股/退休)", "🐇 積極短線 (適合波段/盯盤)"])

    if raw_ticker:
        real_ticker = parse_ticker(raw_ticker)
        try:
            with st.spinner('數據計算中...'):
                hist, info = fetch_stock_data(real_ticker)
                if not hist.empty:
                    close_prices = hist['Close'].dropna()
                    latest_price = float(close_prices.iloc[-1])
                    
                    # 計算指標
                    ma5, ma20, ma60 = close_prices.rolling(5).mean().iloc[-1], close_prices.rolling(20).mean().iloc[-1], close_prices.rolling(60).mean().iloc[-1]
                    max_dd = ((close_prices / close_prices.cummax()) - 1.0).min() * 100
                    
                    delta = close_prices.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                    rsi_14 = (100 - (100 / (1 + (gain / loss)))).iloc[-1]

                    st.subheader(f"1. 核心數據儀表板 ({trade_mode[:2]})")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("最新收盤價", f"{latest_price:.2f}")
                    
                    if "穩健長線" in trade_mode:
                        yield_pct = info.get('dividendYield', None)
                        yield_str = f"{yield_pct * 100:.2f}%" if yield_pct else "N/A"
                        m2.metric("長線趨勢", "🟢 多頭" if latest_price > ma60 else "🔴 空頭")
                        m3.metric("本益比", info.get('trailingPE', 'N/A'))
                        m4.metric("近一年殖利率", yield_str)
                        
                        st.subheader("🤖 2. 系統指引：長線投資策略")
                        if latest_price > ma60: st.success("**🟢 安心續抱**：長線趨勢強勁，適合持續定期定額。")
                        else: st.warning("**🔴 保守觀望**：價格跌破生命線，建議等待止穩再補貨。")
                    else:
                        m2.metric("短線動能", "🔥 強勢" if latest_price > ma5 else "❄️ 轉弱")
                        m3.metric("RSI (14日)", f"{rsi_14:.1f}")
                        m4.metric("月線支撐", f"{ma20:.2f}")
                        
                        st.subheader("🤖 2. 系統指引：短線波段戰術")
                        if rsi_14 > 70: st.error("**🚨 警戒**：短線過熱，不宜追高。")
                        elif rsi_14 < 30: st.success("**🎯 契機**：跌入超賣區，反彈機會大。")
                        else: st.info("**📈 持續**：動能穩定，依均線操作。")

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=close_prices.index, y=close_prices, name='收盤價'))
                    line_ma = ma60 if "長線" in trade_mode else ma5
                    fig.add_trace(go.Scatter(x=close_prices.index, y=close_prices.rolling(60 if "長線" in trade_mode else 5).mean(), name='參考均線'))
                    st.plotly_chart(fig, use_container_width=True)
                else: st.warning("找不到資料。")
        except: st.error("資料獲取失敗，請重新整理或檢查代號。")

# ==========================================
# Tab 3: 多標的績效大PK
# ==========================================
with tab3:
    st.header("📈 第三步：多標的績效大PK")
    tk_in = st.text_input("🔍 輸入多檔代號 (用逗號隔開)：", "台積電, 0050, AAPL")
    if tk_in:
        t_list = [parse_ticker(t.strip()) for t in tk_in.split(",") if t.strip()]
        try:
            with st.spinner('計算中...'):
                data = yf.download(t_list, period="1y", session=get_session())['Close']
                if not data.empty:
                    data_norm = (data / data.iloc[0]) * 100
                    st.plotly_chart(px.line(data_norm, title="過去一年相對表現 (基準100)"), use_container_width=True)
        except: st.error("PK 資料抓取失敗。")

# ==========================================
# Tab 4: 理想資產配置
# ==========================================
with tab4:
    st.header("⚖️ 第四步：理想資產配置建議")
    u_age = st.slider("年齡", 18, 80, 30)
    u_risk = st.selectbox("承受大跌能力？", ["低", "中", "高"])
    if u_risk == "高" and u_age < 40: alloc = [70, 20, 10]
    elif u_risk == "低" or u_age > 60: alloc = [20, 50, 30]
    else: alloc = [50, 30, 20]
    st.plotly_chart(px.pie(values=alloc, names=["股票", "債券", "現金"], hole=0.4), use_container_width=True)

# ==========================================
# Tab 5: 我的真實總資產
# ==========================================
with tab5:
    st.header("💼 第五步：我的真實總資產管理")
    if 'p' not in st.session_state:
        st.session_state.p = pd.DataFrame({"名稱": ["0050.TW", "現金"], "類別": ["股票型", "現金"], "數量": [100.0, 1.0], "成本": [130.0, 10000.0]})
    
    e_df = st.data_editor(st.session_state.p, num_rows="dynamic", use_container_width=True)

    if st.button("🔄 一鍵結算身價", type="primary"):
        with st.spinner("更新報價中..."):
            res, total = [], 0
            for _, r in e_df.iterrows():
                try:
                    p_now = r["成本"]
                    if r["類別"] == "股票型":
                        ticker = parse_ticker(str(r["名稱"]))
                        d = yf.Ticker(ticker, session=get_session()).history(period="1d")
                        if not d.empty: p_now = d['Close'].iloc[-1]
                    val = r["數量"] * p_now
                    total += val
                    res.append({"標的": r["名稱"], "市值": val})
                except: pass
            st.success(f"### 🏦 總資產結算： **{total:,.0f} 元**")
            st.plotly_chart(px.pie(pd.DataFrame(res), values="市值", names="標的"), use_container_width=True)

st.divider()
st.caption("🚨 **免責聲明**：本系統採用 Yahoo Finance 免費數據，僅供參考，不代表投資建議。投資必定有風險，請審慎評估。")
