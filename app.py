import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
import numpy as np

# ==========================================
# 1. 系統核心設定與快取引擎 (確保效能與防呆)
# ==========================================
st.set_page_config(page_title="全齡智能理財戰情室 Pro Max", layout="wide", page_icon="📈")

# 內建常見台美股代號轉換，降低長輩輸入門檻
TICKER_MAP = {
    "台積電": "2330.TW", "0050": "0050.TW", "0056": "0056.TW", "00878": "00878.TW",
    "美債20年": "00679B.TW", "蘋果": "AAPL", "微軟": "MSFT", "輝達": "NVDA", "特斯拉": "TSLA"
}

def parse_ticker(user_input):
    clean_input = str(user_input).strip().upper()
    if clean_input in TICKER_MAP: return TICKER_MAP[clean_input]
    if clean_input.isdigit() and len(clean_input) == 4: return f"{clean_input}.TW"
    return clean_input

@st.cache_data(ttl=43200) # 快取 12 小時，避免頻繁呼叫 API 被封鎖
def fetch_stock_data(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    hist = stock.history(period="1y")
    info = stock.info
    return hist, info

# ==========================================
# 網頁主視覺與標題
# ==========================================
st.title("🌟 終極全齡智能理財與投資決策戰情室")
st.write("結合目標試算、長短線 AI 雙引擎診斷與全資產管理。將複雜的數據，化為最直覺的行動指引。")
st.divider()

# 完整 5 大核心功能分頁
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 1. 財富目標試算", 
    "📊 2. AI 深度診斷 (雙引擎)", 
    "📈 3. 多標的績效大PK", 
    "⚖️ 4. 理想資產配置", 
    "💼 5. 我的真實總資產"
])

# ==========================================
# Tab 1: 財富目標與複利試算 (精算未來身價)
# ==========================================
with tab1:
    st.header("🎯 第一步：精算您的專屬財富藍圖")
    st.write("不知道該存多少錢？輸入現況，系統為您畫出未來的「財富雪球」。")
    
    col_plan1, col_plan2 = st.columns(2)
    with col_plan1:
        st.subheader("📝 資金現況")
        init_inv = st.number_input("1. 目前單筆可投入本金 (元)", value=100000, step=10000, help="現在銀行戶頭裡準備用來投資的閒錢。")
        mon_inv = st.number_input("2. 每月可定期定額投入 (元)", value=10000, step=1000, help="每個月發薪水後，能固定撥出來投資的錢。")
        inv_years = st.slider("3. 預計投資年限 (年)", min_value=1, max_value=50, value=20, help="這筆錢您打算放多久不拿出來用？")
    
    with col_plan2:
        st.subheader("🧭 風險與預期報酬")
        risk_prof = st.selectbox("您面對股市大跌的態度是？", 
            ["保守型 (無法承受虧損，只要比定存好)", "穩健型 (可承受合理波動，追求長期抗通膨)", "積極型 (不怕大起大落，追求資產翻倍)"],
            help="系統將依此設定『預期年化報酬率』。"
        )
        if "保守" in risk_prof: exp_ret = 3.0; st.info("💡 系統套用：保守型預期報酬率 **3%** (適合債券、定存)")
        elif "穩健" in risk_prof: exp_ret = 6.0; st.info("💡 系統套用：穩健型預期報酬率 **6%** (適合全球型大盤 ETF)")
        else: exp_ret = 9.0; st.info("💡 系統套用：積極型預期報酬率 **9%** (適合科技股、成長股)")

    if st.button("🚀 啟動財富藍圖運算", type="primary"):
        y_list, p_list, i_list = [], [], []
        total_m = total_p = init_inv
        for y in range(1, inv_years + 1):
            total_m += (mon_inv * 12); total_p += (mon_inv * 12)
            total_m += total_m * (exp_ret / 100)
            y_list.append(y); p_list.append(total_p); i_list.append(total_m - total_p)
            
        st.success(f"### 🎉 運算完成！{inv_years} 年後預估總資產將達： **{(p_list[-1] + i_list[-1]):,.0f} 元**")
        df_plan = pd.DataFrame({"第幾年": y_list, "辛苦存的本金": p_list, "投資賺的利息 (複利)": i_list})
        fig_plan = px.area(df_plan, x="第幾年", y=["辛苦存的本金", "投資賺的利息 (複利)"], 
                           title="📈 財富成長軌跡預測", color_discrete_sequence=["#1f77b4", "#ff7f0e"])
        st.plotly_chart(fig_plan, use_container_width=True)

# ==========================================
# Tab 2: 單一標的深度診斷 (最精確的長短線雙引擎)
# ==========================================
with tab2:
    st.header("📊 第二步：單一標的 AI 深度診斷")
    st.write("利用真實歷史數據與演算法，提供最客觀的買賣指引。")
    
    col_search1, col_search2 = st.columns([2, 1])
    with col_search1:
        raw_ticker = st.text_input("🔍 輸入標的代號或名稱 (如：台積電, 0050, AAPL)：", "0050")
    with col_search2:
        trade_mode = st.radio("⚙️ 請選擇您的操作屬性 (決定分析邏輯)：", ["🐢 穩健長線 (適合存股/退休/大眾)", "🐇 積極短線 (適合波段/盯盤/交易員)"])

    if raw_ticker:
        real_ticker = parse_ticker(raw_ticker)
        try:
            with st.spinner(f'啟動 {trade_mode[:4]} 分析引擎，抓取最新數據中...'):
                hist, info = fetch_stock_data(real_ticker)
                if not hist.empty and len(hist) > 60:
                    close_prices = hist['Close'].dropna()
                    latest_price = float(close_prices.iloc[-1])
                    
                    # 核心技術指標運算
                    ma5 = close_prices.rolling(window=5).mean().iloc[-1]
                    ma20 = close_prices.rolling(window=20).mean().iloc[-1]
                    ma60 = close_prices.rolling(window=60).mean().iloc[-1]
                    max_dd = ((close_prices / close_prices.cummax()) - 1.0).min() * 100
                    annual_ret = ((latest_price - float(close_prices.iloc[0])) / float(close_prices.iloc[0])) * 100
                    
                    # 14日 RSI 精確運算
                    delta = close_prices.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi_14 = (100 - (100 / (1 + rs))).iloc[-1]

                    st.subheader(f"1. 核心數據儀表板 ({trade_mode[:4]}視角)")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("最新收盤價", f"{latest_price:.2f}")

                    # 根據模式切換精確數據與建議
                    if "穩健長線" in trade_mode:
                        # 🐢 長線模式面板
                        pe_ratio = info.get('trailingPE', 'N/A')
                        if isinstance(pe_ratio, float): pe_ratio = f"{pe_ratio:.2f}"
                        yield_pct = info.get('dividendYield', None)
                        yield_str = f"{yield_pct * 100:.2f}%" if yield_pct else "無配息或無資料"
                        
                        c2.metric("長線趨勢 (vs 60日季線)", "🟢 健康多頭" if latest_price > ma60 else "🔴 弱勢空頭", help="檢視目前價格是否高於過去3個月的平均成本(季線)。")
                        c3.metric("本益比 (P/E 估值)", pe_ratio, help="評估股票有沒有買貴的指標。數字越低通常代表越便宜。ETF通常無此數據。")
                        c4.metric("最大回撤 (壓力測試)", f"{max_dd:.2f}%", help="過去一年內，最慘曾一口氣跌掉多少趴。數字越負代表歷史波動越大。")
                        
                        st.subheader("🤖 2. 系統指引：長線存股與定額策略")
                        if latest_price > ma60:
                            if max_dd > -20: st.success("**🟢 評估結論：安心抱牢 / 適合定期定額**\n\n長線趨勢健康且歷史波動小。非常適合存股族作為核心資產，建議持續定期定額買進。")
                            else: st.info(f"**🟡 評估結論：留意震盪 / 務必分批佈局**\n\n趨勢向上，但過去一年曾發生 {max_dd:.2f}% 的劇烈大跌。不建議單筆重壓，請嚴格執行『分批買進』以分散風險。")
                        else:
                            st.warning("**🔴 評估結論：保守觀望 / 暫緩加碼**\n\n目前長線趨勢偏弱，已跌破生命線。若尚未買進，建議保留現金；若已套牢，請檢視基本面是否惡化，再決定去留。")

                    else:
                        # 🐇 短線模式面板
                        c2.metric("短線動能 (vs 5日均線)", "🔥 強勢" if latest_price > ma5 else "❄️ 轉弱", help="檢視目前價格是否高於過去5天的平均成本。")
                        c3.metric("月線支撐 (20日均線)", f"{ma20:.2f}", help="短線波段的重要防守線。若跌破代表波段可能結束。")
                        c4.metric("RSI (14日相對強弱)", f"{rsi_14:.1f}", help="指標>70代表過熱(容易回檔)；指標<30代表超賣(可能反彈)。")
                        
                        st.subheader("🤖 2. 系統指引：短線波段戰術分析")
                        if rsi_14 > 75:
                            st.error("**🚨 評估結論：極度短線過熱 (高風險預警)**\n\nRSI 顯示買盤過度擁擠。極短線追高風險巨大，隨時有獲利了結賣壓。若有獲利建議逢高減碼，落袋為安。")
                        elif rsi_14 < 30:
                            st.success("**🎯 評估結論：短線超賣區 (跌深反彈契機)**\n\nRSI 進入超賣區，短線殺盤力道可能衰竭。激進投資人可嘗試在設定停損的前提下，輕倉試單搶反彈。")
                        elif latest_price > ma5 and latest_price > ma20:
                            st.info("**📈 評估結論：多頭上攻格局 (順勢操作)**\n\n股價站穩 5 日與 20 日均線之上，動能強勁。建議順勢操作，若未來跌破 5 日均線再考慮出場。")
                        else:
                            st.warning("**⏳ 評估結論：盤整或動能轉弱 (空手觀望)**\n\n目前動能不明確，或已跌破短線重要支撐。建議空手觀望，等待帶量突破均線糾結區再行動。")

                    # 動態生成專業圖表
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=close_prices.index, y=close_prices, mode='lines', name='最新收盤價', line=dict(color='blue')))
                    if "穩健長線" in trade_mode:
                        fig.add_trace(go.Scatter(x=close_prices.index, y=close_prices.rolling(window=60).mean(), mode='lines', name='60日季線(生命線)', line=dict(color='orange', dash='dash')))
                    else:
                        fig.add_trace(go.Scatter(x=close_prices.index, y=close_prices.rolling(window=5).mean(), mode='lines', name='5日均線(短線動能)', line=dict(color='red', dash='dot')))
                        fig.add_trace(go.Scatter(x=close_prices.index, y=close_prices.rolling(window=20).mean(), mode='lines', name='20日月線(波段防守)', line=dict(color='green', dash='dash')))
                    
                    fig.update_layout(title=f"{real_ticker} 過去一年價格走勢 ({trade_mode[:4]})", xaxis_title="日期", yaxis_title="股價", hovermode="x unified")
                    st.plotly_chart(fig, use_container_width=True)
                else: st.warning("找不到足夠的歷史資料來進行精準分析。")
        except Exception as e: st.error(f"資料庫連線異常，請確認代號是否正確。錯誤訊息: {e}")

# ==========================================
# Tab 3: 多標的績效大PK (尋找最強勢資產)
# ==========================================
with tab3:
    st.header("📈 第三步：多標的績效大PK")
    st.write("想知道買哪一檔比較賺？輸入代號直接比對過去一年的真實漲跌幅。")
    tickers_input = st.text_input("🔍 輸入多檔代號 (用逗號隔開，如: 台積電, 0050, 0056, AAPL)", "台積電, 0050, 美債20年")
    if tickers_input:
        t_list = [parse_ticker(t.strip()) for t in tickers_input.split(",") if t.strip()]
        try:
            with st.spinner('精算相對績效中...'):
                data = yf.download(t_list, period="1y")['Close']
                if not data.empty:
                    if isinstance(data, pd.Series): data = data.to_frame(name=t_list[0])
                    data = data.dropna(how='all')
                    # 起點全部設為 100 基準點，方便直接看出誰賺得多
                    m_data = ((data / data.iloc[0]) * 100).reset_index().melt(id_vars=['Date'], var_name='標的', value_name='相對表現 (基準點:100)')
                    fig_pk = px.line(m_data, x='Date', y='相對表現 (基準點:100)', color='標的', title="過去一年誰最會漲？ (起點皆為100)")
                    st.plotly_chart(fig_pk, use_container_width=True)
        except: st.error("計算發生錯誤，請確認輸入的代號皆有效。")

# ==========================================
# Tab 4: 理想資產配置 (AI 策略建議)
# ==========================================
with tab4:
    st.header("⚖️ 第四步：理想資產配置建議")
    st.write("沒有穩賺不賠的單一股票，只有最適合您的資產配置。")
    c_alloc1, c_alloc2 = st.columns(2)
    with c_alloc1:
        age = st.slider("1. 您的年齡是？", 18, 80, 35, help="通常年紀越輕，可承受風險的股票比例可以越高。")
        risk = st.selectbox("2. 面對投資組合下跌 20% 的反應？", ["全部停損出場 (極度保守)", "保留現金不動作 (穩健)", "開心加碼買進 (積極)"])
    
    # 嚴謹的配置演算法
    if "積極" in risk and age < 40: alloc = {"資產類別": ["股票型 (攻擊)", "債券型 (防禦)", "現金 (備用金)"], "建議比例(%)": [70, 20, 10]}
    elif "極度保守" in risk or age > 65: alloc = {"資產類別": ["股票型 (攻擊)", "債券型 (防禦)", "現金 (備用金)"], "建議比例(%)": [20, 50, 30]}
    else: alloc = {"資產類別": ["股票型 (攻擊)", "債券型 (防禦)", "現金 (備用金)"], "建議比例(%)": [50, 30, 20]}
    
    with c_alloc2:
        st.plotly_chart(px.pie(pd.DataFrame(alloc), values='建議比例(%)', names='資產類別', title="系統精算之理想配置圓餅圖", hole=0.4), use_container_width=True)

# ==========================================
# Tab 5: 我的真實總資產管理 (精確追蹤現況)
# ==========================================
with tab5:
    st.header("💼 第五步：我的真實總資產與部位管理")
    st.markdown("將您散落在各銀行的股票、基金、定存輸入下方表格。系統將**即時抓取最新報價**，為您結算真實身價。")
    st.markdown("📱 *手機用戶小提醒：請左右滑動下方表格以完整填寫資料。*")

    # 預設範例資料
    if 'port' not in st.session_state:
        st.session_state.port = pd.DataFrame({
            "資產名稱(如 0050)": ["0050.TW", "儲蓄險/定存", "台積電"],
            "資產類別": ["股票型", "現金", "股票型"],
            "持有數量(股/單位)": [1000, 1, 500],
            "買進平均成本(元)": [130.0, 500000.0, 500.0]
        })
    
    # 互動式資料表
    e_df = st.data_editor(
        st.session_state.port, num_rows="dynamic", use_container_width=True, hide_index=True,
        column_config={"資產類別": st.column_config.SelectboxColumn("資產類別", options=["股票型", "債券型", "基金型", "現金", "其他"], required=True)}
    )

    if st.button("🔄 一鍵抓取最新報價並結算總身價", type="primary"):
        v_df = e_df[(e_df["資產名稱(如 0050)"].str.strip() != "") & (e_df["持有數量(股/單位)"] > 0)].copy()
        if not v_df.empty:
            with st.spinner("正在連線全球資料庫，為您統整全資產..."):
                res, tot_val, tot_cost = [], 0, 0
                for _, r in v_df.iterrows():
                    nm, cls, sh, cst = str(r["資產名稱(如 0050)"]).strip(), r["資產類別"], r["持有數量(股/單位)"], r["買進平均成本(元)"]
                    
                    pr = cst # 預設價格等於成本 (適用於現金或抓不到的基金)
                    real_t = parse_ticker(nm)
                    try:
                        td = yf.Ticker(real_t).history(period="1d")
                        if not td.empty: pr = float(td['Close'].iloc[-1])
                    except: pass # 若抓不到即時報價，自動忽略並使用成本計算
                    
                    val = sh * pr
                    cost_basis = sh * cst
                    tot_val += val
                    tot_cost += cost_basis
                    res.append({"標的": nm, "類別": cls, "目前總市值": val, "未實現損益": val - cost_basis})
                
                # 顯示精確結果
                st.success(f"### 🏦 您目前的真實總身價預估為： **{tot_val:,.0f} 元**")
                profit_loss = tot_val - tot_cost
                if profit_loss >= 0: st.info(f"📈 帳面總獲利： +{profit_loss:,.0f} 元")
                else: st.warning(f"📉 帳面總虧損： {profit_loss:,.0f} 元")
                
                # 繪製真實資產圓餅圖
                res_df = pd.DataFrame(res)
                c1, c2 = st.columns(2)
                with c1: st.plotly_chart(px.pie(res_df.groupby('類別', as_index=False)['目前總市值'].sum(), values='目前總市值', names='類別', title="您的『真實』風險配置佔比", hole=0.4), use_container_width=True)
                with c2: st.plotly_chart(px.pie(res_df, values='目前總市值', names='標的', title="單一資產佔比 (檢視是否過度重壓)"), use_container_width=True)

st.divider()
st.caption("🚨 **【極度重要之免責聲明】**：本系統所有運算皆基於 Yahoo Finance 提供之免費延遲歷史數據與固定數學演算法。系統提示之「健康多頭」、「極度過熱」等皆為技術面統計描述，**絕對不構成任何實質之投資建議、推薦或保證獲利**。技術指標(含 RSI、均線)皆無法預測未來突發之總體經濟事件或公司基本面惡化。真實金融市場極具風險，請使用者務必自行審慎評估，並自負盈虧責任。")
