import streamlit as st
import plotly.express as px
import pandas as pd
import yfinance as yf
import numpy as np

# ==========================================
# 系統設定與快取機制
# ==========================================
st.set_page_config(page_title="智能投資分析與資產管理台", layout="wide")

TICKER_MAP = {
    "台積電": "2330.TW", "0050": "0050.TW", "0056": "0056.TW", "00878": "00878.TW",
    "美債20年": "00679B.TW", "蘋果": "AAPL", "微軟": "MSFT"
}

def parse_ticker(user_input):
    clean_input = str(user_input).strip().upper()
    if clean_input in TICKER_MAP: return TICKER_MAP[clean_input]
    if clean_input.isdigit() and len(clean_input) == 4: return f"{clean_input}.TW"
    return clean_input

@st.cache_data(ttl=43200)
def fetch_stock_data(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    hist = stock.history(period="1y")
    return hist

# ==========================================
# 網頁主體
# ==========================================
st.title("🚀 智能投資分析與資產管理系統")
st.write("從單一標的診斷，到您的全資產庫存統整，打造個人專屬戰情室。")
st.divider()

tab1, tab2, tab3 = st.tabs(["📊 潛力標的診斷", "🎯 理想資產配置", "💼 我的真實庫存與配置"])

# ==========================================
# Tab 1: 潛力標的診斷 (維持快取與防呆)
# ==========================================
with tab1:
    st.header("📊 單一標的深度診斷")
    raw_ticker = st.text_input("🔍 請輸入您想查詢的標的 (如 台積電, AAPL)：", "0050")
    if raw_ticker:
        real_ticker = parse_ticker(raw_ticker)
        try:
            with st.spinner(f'抓取 {real_ticker} 數據中...'):
                hist = fetch_stock_data(real_ticker)
                if not hist.empty and len(hist) > 60:
                    close_prices = hist['Close'].dropna()
                    latest_price = float(close_prices.iloc[-1])
                    annual_return = ((latest_price - float(close_prices.iloc[0])) / float(close_prices.iloc[0])) * 100
                    ma60 = close_prices.rolling(window=60).mean().iloc[-1]
                    trend = "🟢 偏多" if latest_price > ma60 else "🔴 偏空"
                    max_drawdown = ((close_prices / close_prices.cummax()) - 1.0).min() * 100
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("最新收盤價", f"{latest_price:.2f}")
                    c2.metric("趨勢 (vs季線)", trend)
                    c3.metric("近一年報酬", f"{annual_return:.2f}%")
                    c4.metric("最大回撤", f"{max_drawdown:.2f}%", delta_color="inverse")
                    
                    fig = px.line(close_prices.reset_index(), x='Date', y='Close', title=f"{real_ticker} 走勢")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("找不到資料或上市未滿一年。")
        except:
            st.error("系統連線異常。")

# ==========================================
# Tab 2: 理想資產配置測驗
# ==========================================
with tab2:
    st.header("🎯 您的「理想」資產配置藍圖")
    col1, col2 = st.columns(2)
    with col1:
        age = st.slider("您的年齡是？", 18, 80, 30)
    with col2:
        risk = st.selectbox("面對組合下跌 20% 的反應？", ["全部停損 (保守)", "保留現金 (穩健)", "加碼買進 (積極)"])

    if "積極" in risk and age < 40:
        alloc = {"資產類別": ["股票型", "債券型", "現金/定存"], "建議比例(%)": [70, 20, 10]}
    elif "穩健" in risk:
        alloc = {"資產類別": ["股票型", "債券型", "現金/定存"], "建議比例(%)": [50, 30, 20]}
    else:
        alloc = {"資產類別": ["股票型", "債券型", "現金/定存"], "建議比例(%)": [20, 50, 30]}

    df_alloc = pd.DataFrame(alloc)
    fig_ideal = px.pie(df_alloc, values='建議比例(%)', names='資產類別', title="系統建議您的理想配置", hole=0.4)
    st.plotly_chart(fig_ideal, use_container_width=True)

# ==========================================
# Tab 3: 我的真實庫存與配置 (✨ 核心升級)
# ==========================================
with tab3:
    st.header("💼 我的真實庫存與資產健檢")
    st.write("請輸入您實際持有的所有資產。**若為傳統基金或未上市債券（無代號），請隨意輸入名稱，系統會自動以您輸入的成本計價。**")

    # 建立預設表格，加入「資產類別」欄位
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = pd.DataFrame({
            "自訂名稱或代號": ["0050.TW", "AAPL", "安聯收益成長基金", "美國公債"],
            "資產類別": ["股票型", "股票型", "基金型", "債券型"],
            "持有單位數": [1000, 50, 2000, 10],
            "平均單位成本": [130.0, 150.0, 15.5, 100.0]
        })

    # 使用 st.data_editor 並設定下拉選單
    edited_df = st.data_editor(
        st.session_state.portfolio, 
        num_rows="dynamic", 
        use_container_width=True,
        hide_index=True,
        column_config={
            "資產類別": st.column_config.SelectboxColumn(
                "資產類別", 
                help="請選擇資產屬性", 
                options=["股票型", "債券型", "基金型", "現金/定存", "其他"],
                required=True
            )
        }
    )

    if st.button("🔄 結算最新總資產與配置", type="primary"):
        valid_df = edited_df[(edited_df["自訂名稱或代號"].str.strip() != "") & (edited_df["持有單位數"] > 0)].copy()
        
        if valid_df.empty:
            st.warning("請先輸入有效的庫存資料。")
        else:
            with st.spinner("正在連線結算您的多重資產..."):
                results = []
                total_cost_all = 0
                total_value_all = 0

                for index, row in valid_df.iterrows():
                    name_or_ticker = str(row["自訂名稱或代號"]).strip()
                    asset_class = row["資產類別"]
                    shares = row["持有單位數"]
                    avg_cost = row["平均單位成本"]
                    
                    # 嘗試抓取最新報價
                    current_price = avg_cost # 預設為成本價 (用來對付抓不到的傳統基金或債券)
                    is_live = False
                    
                    real_ticker = parse_ticker(name_or_ticker)
                    try:
                        ticker_data = yf.Ticker(real_ticker).history(period="1d")
                        if not ticker_data.empty:
                            current_price = float(ticker_data['Close'].iloc[-1])
                            is_live = True
                    except:
                        pass # 抓不到就默默使用成本價
                    
                    total_cost = shares * avg_cost
                    current_value = shares * current_price
                    profit_loss = current_value - total_cost
                    
                    total_cost_all += total_cost
                    total_value_all += current_value
                    
                    results.append({
                        "標的": name_or_ticker,
                        "類別": asset_class,
                        "最新報價": f"{current_price:.2f} {'(即時)' if is_live else '(手動)'}",
                        "總成本": total_cost,
                        "目前市值": current_value,
                        "未實現損益": profit_loss
                    })

                # --- 1. 顯示總結儀表板 ---
                st.subheader("🏦 您的真實資產總結")
                total_pl = total_value_all - total_cost_all
                total_pl_percent = (total_pl / total_cost_all) * 100 if total_cost_all > 0 else 0
                
                c1, c2, c3 = st.columns(3)
                c1.metric("總投入資金", f"{total_cost_all:,.0f}")
                c2.metric("目前總市值", f"{total_value_all:,.0f}")
                c3.metric("總未實現損益", f"{total_pl:,.0f}", f"{total_pl_percent:.2f}%")

                # --- 2. 顯示真實資產佔比圖表 (解決使用者的核心痛點) ---
                st.subheader("⚖️ 您的「真實」資產配置檢視")
                results_df = pd.DataFrame(results)
                
                # 將相同「資產類別」的市值加總
                allocation_df = results_df.groupby('類別', as_index=False)['目前市值'].sum()
                
                col_chart1, col_chart2 = st.columns(2)
                with col_chart1:
                    fig_real_alloc = px.pie(allocation_df, values='目前市值', names='類別', title="您的『實際』資產類別佔比", hole=0.4)
                    st.plotly_chart(fig_real_alloc, use_container_width=True)
                
                with col_chart2:
                    fig_real_detail = px.pie(results_df, values='目前市值', names='標的', title="您的『個股/單一標的』佔比")
                    st.plotly_chart(fig_real_detail, use_container_width=True)

                # --- 3. 顯示明細 ---
                st.markdown("**詳細庫存損益表**")
                st.dataframe(results_df.style.format({
                    "總成本": "{:,.0f}", "目前市值": "{:,.0f}", "未實現損益": "{:,.0f}"
                }), use_container_width=True)

st.divider()
st.caption("🚨 **免責聲明**：本系統為統整輔助工具。標註為 (即時) 之報價來自 Yahoo Finance，標註為 (手動) 則以您輸入之成本計算。資料僅供參考。")
