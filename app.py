import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="全球跨市場供應鏈決策系統", layout="wide")

SUPPLY_CHAIN_DB = {
    "NVDA": [("2330.TW", "台積電 (晶圓代工)"), ("2317.TW", "鴻海 (伺服器組裝)"), 
             ("3017.TW", "奇鋐 (水冷散熱)"), ("VRT", "Vertiv (電力與散熱)"), ("AVGO", "博通 (客製化ASIC)")],
    "2330.TW": [("ASML", "艾司摩爾 (EUV設備)"), ("AMAT", "應用材料 (設備)"), 
                ("3680.TW", "家登 (光罩載具)"), ("3583.TW", "辛耘 (CoWoS設備)")],
    "AAPL": [("2317.TW", "鴻海 (組裝代工)"), ("2330.TW", "台積電 (A/M晶片)"), 
             ("3008.TW", "大立光 (光學鏡頭)"), ("QCOM", "高通 (通訊基頻)")],
    "TSLA": [("2308.TW", "台達電 (電源系統)"), ("NVDA", "輝達 (自動駕駛晶片)"), 
             ("PANW", "派拓網絡 (車聯網資安)")]
}

def calculate_advisor_signals(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="6mo")
        if df.empty or len(df) < 60:
            return None
        
        price = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        mom5d = (price - df['Close'].iloc[-5]) / df['Close'].iloc[-5]
        pe = ticker.info.get('trailingPE', 20.0) or 20.0

        val_buy = (pe < 22) and (price >= ma60 * 0.98)
        mom_buy = (price > ma20 > ma60) and (mom5d > 0.01) and (50 <= rsi <= 72)
        swing_exit = (rsi > 78) or (price < ma20 and mom5d < -0.02)

        if mom_buy and val_buy:
            sig, target, sl, logic = "🔥 強烈買進 (價值+動能共振)", price * 1.15, ma20 * 0.97, "估值安全且均線多頭排列，風報比極佳。"
        elif mom_buy:
            sig, target, sl, logic = "🚀 趨勢買進 (動能型)", price * 1.10, ma20 * 0.98, "主升段動能強勁，嚴守月線停損。"
        elif val_buy:
            sig, target, sl, logic = "💎 價值分批建倉", price * 1.20, ma60 * 0.93, "歷史本益比低檔，季線支撐強勁。"
        elif swing_exit:
            sig, target, sl, logic = "⚠️ 減碼/停利出場", price, price * 0.98, "短線嚴重超買或跌破短均線，注意回檔風險。"
        else:
            sig, target, sl, logic = "⏳ 中性觀望", price * 1.05, price * 0.95, "量價整理中，等待突破或拉回關鍵支撐。"

        return {
            "代號": symbol, "現價": round(price, 2), "5日動能": f"{mom5d:+.2%}",
            "RSI": round(rsi, 1), "20MA": round(ma20, 2), "60MA": round(ma60, 2),
            "顧問評級": sig, "建議目標價": round(target, 2), "停損點位": round(sl, 2),
            "佐證邏輯": logic, "歷史數據": df
        }
    except:
        return None

st.title("🌐 全球跨市場供應鏈交易決策系統")
st.caption("即時串接台美股 · 供應鏈穿透分析 · 價值/動能/波段三流派評估")

col1, col2 = st.columns([2, 1])
with col1:
    target = st.text_input("輸入核心標的代碼 (例: NVDA, 2330.TW, AAPL, TSLA):", value="NVDA").upper().strip()
with col2:
    refresh = st.button("🔄 一鍵即時分析", use_container_width=True)

if target:
    with st.spinner(f"正在穿透分析 {target} 及其關鍵供應鏈..."):
        main_res = calculate_advisor_signals(target)
        
        if main_res:
            st.subheader(f"📌 核心目標：{target} 分析結果")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("現價", f"${main_res['現價']}")
            m2.metric("5日動能", main_res['5日動能'])
            m3.metric("RSI(14)", main_res['RSI'])
            m4.metric("顧問評級", main_res['顧問評級'])

            st.info(f"💡 **進出場策略與佐證邏輯**：{main_res['佐證邏輯']} ｜ **目標價**：${main_res['建議目標價']} ｜ **防守停損**：${main_res['停損點位']}")

            suppliers = SUPPLY_CHAIN_DB.get(target, [("SPY", "美股大盤連動"), ("0050.TW", "台股大盤連動")])
            st.markdown("---")
            st.subheader(f"🔗 {target} 關鍵供應鏈上下游聯動監控")
            
            chain_data = []
            for s_sym, role in suppliers:
                s_res = calculate_advisor_signals(s_sym)
                if s_res:
                    s_res["供應鏈角色"] = role
                    chain_data.append(s_res)
            
            if chain_data:
                chain_df = pd.DataFrame(chain_data)
                cols_to_show = ["代號", "供應鏈角色", "現價", "5日動能", "RSI", "顧問評級", "建議目標價", "停損點位", "佐證邏輯"]
                st.dataframe(chain_df[cols_to_show], use_container_width=True)

            st.markdown("---")
            st.subheader("📈 核心標的量價走勢與均線結構")
            df_hist = main_res['歷史數據']
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df_hist.index, open=df_hist['Open'], high=df_hist['High'],
                                         low=df_hist['Low'], close=df_hist['Close'], name='K線'))
            fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist['Close'].rolling(20).mean(), name='20MA (月線)', line=dict(color='orange', width=1.5)))
            fig.add_trace(go.Scatter(x=df_hist.index, y=df_hist['Close'].rolling(60).mean(), name='60MA (季線)', line=dict(color='blue', width=1.5)))
            fig.update_layout(xaxis_rangeslider_visible=False, height=450, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("無法取得該標的數據，請確認代碼是否正確（台股請加 .TW，例: 2330.TW）。")
