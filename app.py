import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
import numpy as np
import requests
import time
import random

# ==========================================
# 1. 系統核心設定與超強防封鎖引擎
# ==========================================
st.set_page_config(page_title="全齡智能理財戰情室 Pro Max", layout="wide", page_icon="🚀")

# 建立超級 Session：模擬最擬真的瀏覽器行為
def get_robust_session():
    session = requests.Session()
    # 隨機更換 User-Agent 模擬不同裝置
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ]
    session.headers.update({
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Upgrade-Insecure-Requests": "1"
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

@st.cache_data(ttl=3600) # 縮短快取時間到 1 小時，確診數據新鮮度
def fetch_stock_data_pro(ticker_symbol):
    session = get_robust_session()
    stock = yf.Ticker(ticker_symbol, session=session)
    
    # 分段抓取：先抓歷史價格（最重要）
    hist = stock.history(period="1y")
    
    # 嘗試抓取基本面（這部分最容易被封鎖，所以用 try 包起來）
    info = {}
    try:
        info = stock.info
    except:
        info = {"trailingPE": "無法讀取", "dividendYield": None}
        
    return hist, info

# ==========================================
# 網頁主視覺：使用豐富的標題與樣式
# ==========================================
st.markdown("""
    <style>
    .main-title { font-size: 36px !important; font-weight: 800; color: #1E88E5; text-align: center; }
    .sub-title { font-size: 18px; color: #555; text-align: center; margin-bottom: 30px; }
    </style>
    <div class="main-title">🌟 全齡智能理財與投資決策戰情室</div>
    <div class="sub-title">整合全球數據與 AI 分析，專為 18-65 歲以上投資者打造的導航系統</div>
    """, unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 財富目標試算", 
    "📊 AI 深度診斷 (雙引擎)", 
    "📈 多標績效大PK", 
    "⚖️ 理想資產配置", 
    "💼 我的總資產管理"
])

# ==========================================
# Tab 1: 財富目標試算
# ==========================================
with tab1:
    st.header("🎯 規劃您的財富藍圖")
    col1, col2 = st.columns(2)
    with col1:
        init_inv = st.number_input("💵 目前單筆本金 (元)", value=100000, step=10000)
        mon_inv = st.number_input("🏦 每月定期定額 (元)", value=10000, step=1000)
    with col2:
        inv_years = st.slider("⏳ 投資年限 (年)", 1, 50, 20)
        risk_choice = st.select_slider("🧠 風險承受度", options=["保守型", "穩健型", "積極型"], value="穩健型")
        ret_map = {"保守型": 3.0, "穩健型": 6.0, "積極型": 9.0}
        exp_ret = ret_map[risk_choice]

    if st.button("🔥 立即精算回報", type="primary", use_container_width=True):
        y_data = []
        total_m = total_p = init_inv
        for y in range(1, inv_years + 1):
            total_m = (total_m + mon_inv * 12) * (1 + exp_ret / 100)
            total_p += (mon_inv * 12)
            y_data.append({"年": y, "本金": total_p, "預估總資產": total_m})
        
        df = pd.DataFrame(y_data)
        st.success(f"### 預估第 {inv_years} 年資產將達到： **{total_m:,.0f} 元**")
        st.plotly_chart(px.area(df, x="年", y=["預估總資產", "本金"], title="財富積累曲線", color_discrete_map={"預估總資產": "#00CC96", "本金": "#636EFA"}), use_container_width=True)

# ==========================================
# Tab 2: AI 深度診斷 (核心功能 - 修正紅字問題)
# ==========================================
with tab2:
    st.header("📊 AI 投資策略診斷")
    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        u_input = st.text_input("🔍 輸入股票代號或名稱 (例如: 台積電, 0050, NVDA)", "0050")
    with col_s2:
        mode = st.radio("⚙️ 選擇您的投資流派：", ["🐢 穩健長線 (看趨勢與配息)", "🐇 積極短線 (看動能與指標)"])

    if u_input:
        target = parse_ticker(u_input)
        try:
            with st.spinner(f'正在為您調閱 {target} 的全球實時數據...'):
                # 模擬人類操作延遲，降低被封鎖率
                time.sleep(0.5) 
                hist, info = fetch_stock_data_pro(target)
                
                if not hist.empty:
                    prices = hist['Close'].dropna()
                    now_p = prices.iloc[-1]
                    
                    # 精確指標計算
                    ma5, ma20, ma60 = prices.rolling(5).mean().iloc[-1], prices.rolling(20).mean().iloc[-1], prices.rolling(60).mean().iloc[-1]
                    max_val = prices.max()
                    mdd = (now_p - max_val) / max_val * 100
                    
                    # RSI 計算
                    delta = prices.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                    rsi = (100 - (100 / (1 + (gain / loss)))).iloc[-1]

                    # 數據顯示面板
                    st.markdown(f"### 📋 {target} 診斷報告")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("當前股價", f"{now_p:.2f}")
                    
                    if "穩健長線" in mode:
                        m2.metric("長線位階", "🟢 高於季線" if now_p > ma60 else "🔴 低於季線")
                        m3.metric("本益比", info.get('trailingPE', '數據受限'))
                        m4.metric("歷史回撤", f"{mdd:.1f}%")
                        
                        st.info("💡 **長線 AI 指引：**")
                        if now_p > ma60: st.write("✅ 趨勢仍屬多頭，建議分批加碼或持續定期定額。")
                        else: st.write("⚠️ 目前處於弱勢區，建議保留現金，待股價重回 60 日均線後再行考慮。")
                    else:
                        m2.metric("短線動能", "🔥 強勢" if now_p > ma5 else "❄️ 弱勢")
                        m3.metric("RSI (14日)", f"{rsi:.1f}")
                        m4.metric("月線支撐", f"{ma20:.2f}")
                        
                        st.info("💡 **短線 AI 指引：**")
                        if rsi > 70: st.warning("⚠️ RSI 進入超買區，短線追高風險極大，建議部分獲利了結。")
                        elif rsi < 30: st.success("🎯 RSI 進入超賣區，跌勢可能衰竭，可留意短線反彈契機。")
                        else: st.write("📉 目前處於中性區間，請依照 5 日線與 20 日線扣抵值進行順勢操作。")

                    # 圖表
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=prices.index, y=prices, name='收盤價', line=dict(color='#1f77b4', width=2)))
                    main_ma = ma60 if "長線" in mode else ma5
                    fig.add_trace(go.Scatter(x=prices.index, y=prices.rolling(60 if "長線" in mode else 5).mean(), name='參考趨勢線', line=dict(dash='dash')))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("此代號找不到歷史價格，請確認代號是否正確。")
        except Exception as e:
            st.error(f"⚠️ 數據引擎暫時受阻：{e}。請稍候 10 秒再重新點選分析。")

# ==========================================
# Tab 3: 多標績效大PK
# ==========================================
with tab3:
    st.header("📈 多標的績效大PK")
    pk_input = st.text_input("🔍 輸入多檔代號 (例如: 2330.TW, 0050.TW, AAPL)", "2330.TW, 0050.TW, 0056.TW")
    if pk_input:
        with st.spinner('正在比對數據...'):
            tk_list = [t.strip().upper() for t in pk_input.split(",")]
            pk_data = yf.download(tk_list, period="1y", session=get_robust_session())['Close']
            if not pk_data.empty:
                norm_data = (pk_data / pk_data.iloc[0]) * 100
                st.plotly_chart(px.line(norm_data, title="過去一年相對累積報酬率 (起點為100)"), use_container_width=True)

# ==========================================
# Tab 4: 理想資產配置
# ==========================================
with tab4:
    st.header("⚖️ 全齡資產配置建議")
    u_age = st.number_input("您的年齡", 18, 100, 35)
    u_risk = st.radio("您的投資心態", ["極度保守 (怕虧損)", "中規中矩 (想超前通膨)", "積極進取 (拼資產翻倍)"])
    
    if u_risk == "積極進取" and u_age < 45: shares, bonds, cash = 75, 20, 5
    elif u_risk == "極度保守" or u_age > 60: shares, bonds, cash = 20, 60, 20
    else: shares, bonds, cash = 50, 40, 10
    
    st.plotly_chart(px.pie(values=[shares, bonds, cash], names=["股票", "債券", "現金"], hole=0.5, title="AI 建議資產比例"), use_container_width=True)

# ==========================================
# Tab 5: 我的總資產管理 (強化穩定性)
# ==========================================
with tab5:
    st.header("💼 我的真實總資產")
    if 'my_assets' not in st.session_state:
        st.session_state.my_assets = pd.DataFrame({"標的": ["0050.TW", "現金"], "類別": ["股票", "現金"], "數量": [100.0, 1.0], "成本價": [130.0, 10000.0]})
    
    edited_df = st.data_editor(st.session_state.my_assets, num_rows="dynamic", use_container_width=True)

    if st.button("🔄 同步最新報價並結算", type="primary"):
        total_value = 0
        for _, row in edited_df.iterrows():
            curr_p = row["成本價"]
            if row["類別"] == "股票":
                try:
                    d = yf.Ticker(row["標的"], session=get_robust_session()).history(period="1d")
                    if not d.empty: curr_p = d['Close'].iloc[-1]
                except: pass
            total_value += row["數量"] * curr_p
        st.balloons()
        st.metric("估算總身價 (TWD)", f"{total_value:,.0f}")

st.divider()
st.caption("🚨 免責聲明：本系統數據源自 Yahoo Finance，僅供學習與決策輔助，不構成投資建議。投資必定有風險，請使用者依個人財務狀況審慎評估。")
