import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
import numpy as np
import time
import random

# ==========================================
# 1. 系統核心設定與防封鎖策略
# ==========================================
st.set_page_config(page_title="全齡智能理財戰情室 Pro Max", layout="wide", page_icon="📈")

# 預設常見標的轉換
TICKER_MAP = {
    "台積電": "2330.TW", "0050": "0050.TW", "0056": "0056.TW", "00878": "00878.TW",
    "美債20年": "00679B.TW", "蘋果": "AAPL", "微軟": "MSFT", "輝達": "NVDA", "特斯拉": "TSLA"
}

def parse_ticker(user_input):
    clean_input = str(user_input).strip().upper()
    if clean_input in TICKER_MAP: return TICKER_MAP[clean_input]
    if clean_input.isdigit() and len(clean_input) == 4: return f"{clean_input}.TW"
    return clean_input

@st.cache_data(ttl=3600)
def fetch_data_safe(ticker_symbol):
    """
    使用『延遲重試策略』抓取資料，不使用會報錯的 Session。
    """
    # 隨機延遲 1~3 秒，模擬真人行為，避免被 Yahoo 偵測為機器人
    time.sleep(random.uniform(1.0, 3.0))
    
    try:
        stock = yf.Ticker(ticker_symbol)
        # 優先抓取歷史價格 (最穩定)
        hist = stock.history(period="1y")
        # 嘗試抓取基本面 (不強求，失敗不報錯)
        info = {}
        try:
            info = stock.info
        except:
            info = {"trailingPE": "N/A", "dividendYield": None}
        return hist, info
    except Exception as e:
        return pd.DataFrame(), {"error": str(e)}

# ==========================================
# 網頁視覺標題
# ==========================================
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🌟 終極全齡智能理財與投資決策戰情室</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>系統已更新：自動排除 API 衝突，強化資料抓取穩定性</p>", unsafe_allow_html=True)
st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 1. 財富目標試算", 
    "📊 2. AI 深度診斷 (雙引擎)", 
    "📈 3. 多標績效大PK", 
    "⚖️ 4. 理想資產配置", 
    "💼 5. 我的真實總資產"
])

# ==========================================
# Tab 1: 財富試算
# ==========================================
with tab1:
    st.header("🎯 第一步：精算財富藍圖")
    c1, c2 = st.columns(2)
    with c1:
        init_inv = st.number_input("目前的本金 (元)", value=100000, step=10000)
        mon_inv = st.number_input("每月預計投入 (元)", value=10000, step=1000)
    with c2:
        inv_years = st.slider("預計投資年限", 1, 50, 20)
        risk_lvl = st.select_slider("風險屬性", options=["保守", "穩健", "積極"], value="穩健")
        ret_rate = 3.0 if risk_lvl == "保守" else 6.0 if risk_lvl == "穩健" else 10.0
    
    if st.button("🚀 開始計算", type="primary", use_container_width=True):
        total = init_inv
        history = []
        for y in range(1, inv_years + 1):
            total = (total + mon_inv * 12) * (1 + ret_rate/100)
            history.append({"年": y, "預估資產": total})
        st.success(f"### 🎉 {inv_years} 年後預估身價： **{total:,.0f} 元**")
        st.plotly_chart(px.area(pd.DataFrame(history), x="年", y="預估資產", title="財富成長曲線"), use_container_width=True)

# ==========================================
# Tab 2: AI 診斷 (核心修正區)
# ==========================================
with tab2:
    st.header("📊 第二步：AI 深度診斷")
    cs1, cs2 = st.columns([2, 1])
    with cs1:
        u_in = st.text_input("🔍 代號或名稱：", "0050")
    with cs2:
        mode = st.radio("⚙️ 模式：", ["🐢 穩健長線", "🐇 積極短線"])

    if u_in:
        t_id = parse_ticker(u_in)
        with st.spinner(f'正在為您與全球資料庫進行安全連線...'):
            hist, info = fetch_data_safe(t_id)
            
            if not hist.empty:
                prices = hist['Close']
                cur_p = float(prices.iloc[-1])
                ma5, ma20, ma60 = prices.rolling(5).mean().iloc[-1], prices.rolling(20).mean().iloc[-1], prices.rolling(60).mean().iloc[-1]
                
                # RSI 計算
                delta = prices.diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rsi = (100 - (100 / (1 + (gain / loss)))).iloc[-1]

                st.subheader(f"📋 {t_id} 分析面板")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("最新價", f"{cur_p:.2f}")
                
                if "長線" in mode:
                    m2.metric("趨勢位階", "🟢 強勢" if cur_p > ma60 else "🔴 偏弱")
                    m3.metric("本益比", info.get('trailingPE', 'N/A'))
                    m4.metric("一年最高", f"{prices.max():.1f}")
                    st.info(f"🤖 **長線指引：** {'✅ 適合分批佈局' if cur_p > ma60 else '⚠️ 建議耐心觀望'}")
                else:
                    m2.metric("RSI (14D)", f"{rsi:.1f}")
                    m3.metric("月線支撐", f"{ma20:.2f}")
                    m4.metric("今日震幅", f"{((prices.iloc[-1]/prices.iloc[-2]-1)*100):.2f}%")
                    st.info(f"🤖 **短線指引：** {'🚨 過熱請注意' if rsi > 70 else '🎯 跌深反彈中' if rsi < 30 else '📈 動能平穩'}")

                fig = px.line(prices, title=f"{t_id} 年度走勢圖")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("❌ 資料獲取失敗。Yahoo 伺服器忙碌中，請間隔 10 秒後再點擊一次，或更換代號試試。")

# ==========================================
# Tab 3: PK 比較
# ==========================================
with tab3:
    st.header("📈 第三步：多標的績效 PK")
    pk_in = st.text_input("輸入多個代號 (用逗號隔開)：", "2330.TW, 0050.TW, AAPL")
    if pk_in:
        with st.spinner('進行對比分析中...'):
            try:
                # PK 比較也加入延遲防止被封鎖
                time.sleep(2)
                t_list = [t.strip().upper() for t in pk_in.split(",")]
                pk_data = yf.download(t_list, period="1y")['Close']
                if not pk_data.empty:
                    norm_pk = (pk_data / pk_data.iloc[0]) * 100
                    st.plotly_chart(px.line(norm_pk, title="一年漲跌幅對照 (起點為100)"), use_container_width=True)
            except:
                st.warning("PK 數據獲取異常，請縮減標的數量後再試。")

# ==========================================
# Tab 4: 資產配置
# ==========================================
with tab4:
    st.header("⚖️ 第四步：AI 理想配置建議")
    u_age = st.slider("您的年齡？", 18, 90, 35)
    u_risk = st.radio("面對大跌的心態？", ["睡不著覺", "有點擔心", "沒感覺繼續買"])
    
    if u_risk == "沒感覺繼續買": s, b, c = (80-u_age/2), (u_age/2), 10
    elif u_risk == "睡不著覺": s, b, c = 20, 50, 30
    else: s, b, c = 50, 40, 10
    
    st.plotly_chart(px.pie(values=[s, b, c], names=["股票", "債券", "現金"], hole=0.4), use_container_width=True)

# ==========================================
# Tab 5: 真實總資產 (穩定版)
# ==========================================
with tab5:
    st.header("💼 第五步：我的真實總資產結算")
    if 'data' not in st.session_state:
        st.session_state.data = pd.DataFrame({"標的": ["0050.TW", "現金"], "類別": ["股票", "現金"], "數量": [10.0, 1.0], "買進單價": [130.0, 50000.0]})
    
    e_df = st.data_editor(st.session_state.data, num_rows="dynamic", use_container_width=True)

    if st.button("💹 一鍵更新現值並計算", type="primary"):
        with st.spinner("更新數據中..."):
            total_val = 0
            for _, r in e_df.iterrows():
                p = r["買進單價"]
                if r["類別"] == "股票":
                    try:
                        time.sleep(0.5)
                        d = yf.Ticker(r["標的"]).history(period="1d")
                        if not d.empty: p = d['Close'].iloc[-1]
                    except: pass
                total_val += r["數量"] * p
            st.metric("📊 預估總資產 (TWD)", f"{total_val:,.0f}")
            st.balloons()

st.divider()
st.caption("🚨 免責聲明：本系統數據由 Yahoo Finance 提供。數據抓取可能因伺服器負載受限，結果僅供參考。投資必有風險。")
