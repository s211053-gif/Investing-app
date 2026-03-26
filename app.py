import streamlit as st
import plotly.express as px
import pandas as pd
import yfinance as yf
import numpy as np

# 1. 設定網頁排版 (適合平板的全寬模式)
st.set_page_config(page_title="最強投資決策系統 Pro Max", layout="wide")

st.title("🚀 最強投資決策輔助系統 Pro Max")
st.write("結合資產配置、風險診斷與相對績效比較，幫助您做出最理性的投資決策。")
st.divider()

# 使用 Tab 分頁讓平板畫面保持乾淨
tab1, tab2, tab3 = st.tabs(["1️⃣ 專屬資產配置", "2️⃣ 單一標的深度診斷", "3️⃣ 多標的績效大PK"])

# ==========================================
# Tab 1: 風險屬性評估與資產配置
# ==========================================
with tab1:
    st.header("🛡️ 您的專屬資產配置")
    col1, col2 = st.columns(2)
    with col1:
        age = st.slider("您的年齡是？", 18, 80, 30)
    with col2:
        risk_tolerance = st.selectbox("面對投資組合下跌 20% 的反應？", ["全部停損 (保守)", "保留現金 (穩健)", "加碼買進 (積極)"])

    # 邏輯判定配置比例
    if "積極" in risk_tolerance and age < 40:
        allocation = {"資產類別": ["全球股票 ETF", "新興市場股票", "債券"], "比例(%)": [60, 30, 10]}
    elif "穩健" in risk_tolerance:
        allocation = {"資產類別": ["全球股票 ETF", "投資級債券", "現金"], "比例(%)": [50, 30, 20]}
    else:
        allocation = {"資產類別": ["政府債券", "高股息股票", "定存"], "比例(%)": [60, 20, 20]}

    df_alloc = pd.DataFrame(allocation)
    fig_pie = px.pie(df_alloc, values='比例(%)', names='資產類別', hole=0.4)
    fig_pie.update_layout(height=350, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_pie, use_container_width=True)

# ==========================================
# Tab 2: 單一標的深度診斷 (決策儀表板)
# ==========================================
with tab2:
    st.header("📊 單一標的深度診斷")
    st.write("檢視標的的真實風險、趨勢與波動率。")
    
    ticker_single = st.text_input("🔍 請輸入單一標的代號 (如 0050.TW 或 AAPL)", "0050.TW", key="single_ticker")
    
    if ticker_single:
        try:
            with st.spinner(f'正在為您抓取 {ticker_single} 的深度決策數據...'):
                stock_data = yf.download(ticker_single.strip(), period="1y")
                
                if stock_data.empty:
                    st.warning("⚠️ 找不到該代號的資料，請確認輸入格式。")
                else:
                    # 處理 yfinance 可能返回的資料結構
                    if isinstance(stock_data.columns, pd.MultiIndex):
                        close_prices = stock_data['Close'].iloc[:, 0].dropna()
                    else:
                        close_prices = stock_data['Close'].dropna()
                    
                    if len(close_prices) > 60: # 確保有足夠數據計算季線
                        # --- 核心數據計算 ---
                        latest_price = float(close_prices.iloc[-1])
                        first_price = float(close_prices.iloc[0])
                        annual_return = ((latest_price - first_price) / first_price) * 100
                        
                        # 季線 (60日均線)
                        ma60 = close_prices.rolling(window=60).mean().iloc[-1]
                        trend_status = "🟢 偏多 (站上季線)" if latest_price > ma60 else "🔴 偏空 (跌破季線)"
                        
                        # 最大回撤 (Max Drawdown)
                        roll_max = close_prices.cummax()
                        drawdown = (close_prices / roll_max) - 1.0
                        max_drawdown = drawdown.min() * 100
                        
                        # 年化波動率
                        daily_pct_change = close_prices.pct_change().dropna()
                        volatility = daily_pct_change.std() * np.sqrt(252) * 100

                        # --- 顯示決策儀表板 ---
                        col_a, col_b, col_c, col_d = st.columns(4)
                        with col_a:
                            st.metric(label="最新收盤價", value=f"{latest_price:.2f}")
                        with col_b:
                            st.metric(label="近一年報酬率", value=f"{annual_return:.2f}%", delta=f"{annual_return:.2f}%")
                        with col_c:
                            st.metric(label="最大回撤 (最慘跌幅)", value=f"{max_drawdown:.2f}%", delta="風險指標", delta_color="inverse")
                        with col_d:
                            st.metric(label="目前趨勢 (vs 60日季線)", value=trend_status)

                        st.info(f"💡 **決策輔助提示**：該標的近一年年化波動率為 **{volatility:.2f}%**。若最大回撤超過您的心理承受力，建議降低資金配置。")

                        # 繪製單一走勢圖
                        chart_data = close_prices.reset_index()
                        chart_data.columns = ['Date', 'Close']
                        fig_single = px.line(chart_data, x='Date', y='Close', title=f"{ticker_single} 近一年歷史走勢")
                        st.plotly_chart(fig_single, use_container_width=True)
                    else:
                        st.warning("⚠️ 該標的上市時間不足，無法計算完整決策數據。")
                        
        except Exception as e:
            st.error(f"抓取資料時發生錯誤，請確認代號。錯誤細節：{e}")

# ==========================================
# Tab 3: 多標的相對績效 PK
# ==========================================
with tab3:
    st.header("📈 多標的績效大PK (基準化比較)")
    st.write("將多檔股票放在同一個起跑點 (100)，一眼看出誰的報酬率最有利。")

    tickers_input = st.text_input(
        "🔍 輸入多檔代號 (請用半形逗號隔開)", 
        "0050.TW, 2330.TW, 2317.TW",
        key="multi_ticker"
    )

    if tickers_input:
        ticker_list = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
        
        try:
            with st.spinner('正在計算相對績效...'):
                data = yf.download(ticker_list, period="1y")['Close']
                
                if data.empty:
                    st.warning("⚠️ 抓不到資料，請確認代號。")
                else:
                    # 如果只有單一標的，把它轉回 DataFrame 確保格式一致
                    if isinstance(data, pd.Series):
                        data = data.to_frame(name=ticker_list[0])
                    
                    # 清理缺失值，避免計算錯誤
                    data = data.dropna(how='all')
                    
                    # 將所有股票第一天的價格設為 100
                    normalized_data = (data / data.iloc[0]) * 100
                    normalized_data = normalized_data.reset_index()
                    melted_data = normalized_data.melt(id_vars=['Date'], var_name='標的代號', value_name='相對報酬表現 (起點=100)')
                    
                    # 繪製相對績效圖
                    fig_multi = px.line(
                        melted_data, x='Date', y='相對報酬表現 (起點=100)', color='標的代號',
                        title="近一年相對績效走勢 (數值 > 100 代表獲利)"
                    )
                    fig_multi.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="起跑點 / 損益兩平")
                    st.plotly_chart(fig_multi, use_container_width=True)
                    
                    # 排行榜
                    st.subheader("🏆 最終報酬率排行榜")
                    returns = ((data.iloc[-1] - data.iloc[0]) / data.iloc[0]) * 100
                    returns_df = pd.DataFrame({'標的代號': returns.index, '近一年累積報酬率 (%)': returns.values})
                    returns_df = returns_df.sort_values(by='近一年累積報酬率 (%)', ascending=False).reset_index(drop=True)
                    st.dataframe(returns_df.style.format({'近一年累積報酬率 (%)': '{:.2f}%'}))

        except Exception as e:
            st.error(f"運算時發生錯誤，請確認代號是否正確。錯誤細節：{e}")

st.divider()
st.caption("⚠️ **免責聲明**：本系統所有數據由 Yahoo Finance 提供，存在延遲可能。歷史績效與系統評估不代表未來報酬，投資請務必自行審慎評估。")
