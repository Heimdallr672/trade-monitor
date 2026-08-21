import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="全球跨市場供應鏈與機構籌碼決策系統", layout="wide")

# 1. 預設供應鏈資料庫 (支援台美全產業擴充)
SUPPLY_CHAIN_DB = {
    "NVDA": [("2330.TW", "台積電 (晶圓代工)"), ("2317.TW", "鴻海 (伺服器組裝)"), 
             ("3017.TW", "奇鋐 (水冷散熱)"), ("VRT", "Vertiv (電力散熱)"), ("AVGO", "博通 (客製化晶片)")],
    "2330.TW": [("ASML", "艾司摩爾 (光刻設備)"), ("AMAT", "應用材料 (半導體設備)"), 
                ("3680.TW", "家登 (光罩載具)"), ("3583.TW", "辛耘 (CoWoS設備)")],
    "AAPL": [("2317.TW", "鴻海 (組裝代工)"), ("2330.TW", "台積電 (核心晶片)"), 
             ("3008.TW", "大立光 (光學鏡頭)"), ("QCOM", "高通 (基頻晶片)")],
    "TSLA": [("2308.TW", "台達電 (電源模組)"), ("NVDA", "輝達 (智駕運算)"), 
             ("PANW", "派拓網絡 (車聯網安全)")]
}

# 2. 獲取大盤與宏觀風險指標 (S&P500, 費半, 台股, VIX)
@st.cache_data(ttl=600)
def get_macro_market_context():
    indexes = {"美股 S&P500": "^GSPC", "費城半導體": "^SOX", "台股加權": "^TWII", "VIX 恐慌指數": "^VIX"}
    summary = {}
    for name, sym in indexes.items():
        try:
            df = yf.Ticker(sym).history(period="5d")
            if not df.empty:
                cur = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                pct = (cur - prev) / prev
                summary[name] = {"price": cur, "change": pct}
        except:
            summary[name] = {"price": 0, "change": 0}
    return summary

# 3. 機構籌碼與多因子決策核心計算
def analyze_stock_full(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="6mo")
        if df.empty or len(df) < 40:
            return None
        
        price = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        
        # 動能與 RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        mom5d = (price - df['Close'].iloc[-5]) / df['Close'].iloc[-5]

        # 籌碼指標：Chaikin Money Flow (CMF 20日機構資金流)
        mf_multiplier = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'] + 1e-9)
        mf_volume = mf_multiplier * df['Volume']
        cmf_20 = (mf_volume.rolling(20).sum() / (df['Volume'].rolling(20).sum() + 1e-9)).iloc[-1]
        
        # 5日成交量與大戶推力比
        vol_5d_avg = df['Volume'].iloc[-5:].mean()
        vol_20d_avg = df['Volume'].iloc[-20:].mean()
        vol_ratio = vol_5d_avg / (vol_20d_avg + 1e-9)

        # 籌碼面評級
        if cmf_20 > 0.10 and vol_ratio > 1.2:
            chip_status = "🟢 法人大舉吸籌 (放量增持)"
        elif cmf_20 > 0.0:
            chip_status = "🟡 資金溫和流入"
        elif cmf_20 < -0.10:
            chip_status = "🔴 主力資金流出 (出貨警戒)"
        else:
            chip_status = "⚪ 籌碼中性觀望"

        # 資深顧問戰術決策 (共振模型)
        is_bull = (price > ma20 > ma60) and (rsi > 50)
        is_val = (price >= ma60 * 0.98) and (rsi < 65)

        if is_bull and cmf_20 > 0.05:
            action = "🔥 主升段進攻佈局 (趨勢+籌碼雙多)"
            position_size = "70% ~ 80% 倉位 (積極)"
            entry_tranche = f"第一筆：現價 ${round(price,2)} (40%)，第二筆拉回月線 ${round(ma20,2)} (40%)"
            target = price * 1.15
            stop_loss = ma20 * 0.97
            advisor_logic = "均線呈現多頭排列，且 20 日機構資金流 (CMF) 呈現顯著淨流入，屬法人認養標的。"
        elif is_val and cmf_20 >= 0:
            action = "💎 價值左側分批佈局"
            position_size = "40% ~ 50% 倉位 (穩健)"
            entry_tranche = f"季線 ${round(ma60,2)} 附近分 3 筆逢低承接"
            target = price * 1.20
            stop_loss = ma60 * 0.93
            advisor_logic = "股價處於季線關鍵防守位，法人並未顯著撤退，具備極佳風報比。"
        elif rsi > 78 or cmf_20 < -0.10:
            action = "⚠️ 風險警戒 / 減碼防禦"
            position_size = "10% ~ 20% 防禦倉位或空手"
            entry_tranche = "暫停新開倉，等待籌碼沉澱"
            target = price
            stop_loss = price * 0.98
            advisor_logic = "短線指標過熱或主力資金出現顯著撤退背離跡象，應適時獲利了結。"
        else:
            action = "⏳ 區間震盪觀望"
            position_size = "20% ~ 30% 試單倉位"
            entry_tranche = "突破 20MA 或拉回 60MA 確認支撐後再行進場"
            target = price * 1.05
            stop_loss = price * 0.95
            advisor_logic = "多空方向未明，主力維持洗盤震盪格局，建議多看少做。"

        return {
            "symbol": symbol, "price": price, "mom5d": mom5d, "rsi": rsi,
            "ma20": ma20, "ma60": ma60, "cmf": cmf_20, "chip_status": chip_status,
            "action": action, "position_size": position_size, "entry_tranche": entry_tranche,
            "target": target, "stop_loss": stop_loss, "logic": advisor_logic, "df": df
        }
    except:
        return None

# ======================= 前端 UI 介面 =======================
st.title("🌐 全球跨市場供應鏈與機構籌碼決策系統")
st.caption("【機構級交易視角】跨市場大盤宏觀 · 供應鏈聯動相關性 · 主力籌碼資金流 · 戰術資產配置")

# 1. 頂部宏觀大盤看板
st.subheader("📊 跨市場宏觀大盤與風險監控")
macro_data = get_macro_market_context()
cols = st.columns(4)
for idx, (m_name, m_info) in enumerate(macro_data.items()):
    val_str = f"{m_info['price']:,.2f}"
    pct_str = f"{m_info['change']:+.2%}"
    cols[idx].metric(m_name, val_str, pct_str)

vix_val = macro_data.get("VIX 恐慌指數", {}).get("price", 15)
if vix_val > 25:
    st.warning("⚠️ **宏觀風險警報**：VIX 恐慌指數突破 25，全球股市波動加劇，建議總體持倉降至 50% 以下！")

st.markdown("---")

# 2. 標的輸入與執行
c1, c2 = st.columns([3, 1])
with c1:
    target_sym = st.text_input("輸入核心標的代碼 (台美股皆可，例: NVDA, 2330.TW, AAPL, 2317.TW):", value="NVDA").upper().strip()
with c2:
    st.write(" ")
    st.write(" ")
    btn = st.button("🚀 執行機構級深度分析", use_container_width=True)

if target_sym:
    with st.spinner(f"正在穿透分析 {target_sym} 籌碼、供應鏈與機構決策..."):
        res = analyze_stock_full(target_sym)
        
        if res:
            # 核心標的儀表板
            st.subheader(f"🎯 核心標的：{target_sym} 深度診斷")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("當前現價", f"${res['price']:.2f}", f"{res['mom5d']:+.2%} (5日)")
            k2.metric("RSI (14D)", f"{res['rsi']:.1f}")
            k3.metric("機構資金流 (CMF)", f"{res['cmf']:+.3f}")
            k4.metric("籌碼狀態", res['chip_status'].split()[1])

            # 顧問決策戰術框
            with st.container():
                st.success(f"### 📋 資深投資顧問戰術建議：{res['action']}")
                sc1, sc2, sc3 = st.columns(3)
                sc1.markdown(f"**💼 建議佈局倉位**：`{res['position_size']}`")
                sc2.markdown(f"**🎯 階段目標價**：`${res['target']:.2f}` (+{((res['target']/res['price'])-1):.1%})")
                sc3.markdown(f"**🛡️ 嚴格停損防守**：`${res['stop_loss']:.2f}` (-{(1-(res['stop_loss']/res['price'])):.1%})")
                st.markdown(f"**🪜 分批建倉節奏**：{res['entry_tranche']}")
                st.info(f"💡 **判斷邏輯與佐證**：{res['logic']}")

            # 3. 供應鏈上下游聯動與籌碼清單
            st.markdown("---")
            st.subheader(f"🔗 {target_sym} 關鍵供應鏈上下游聯動與籌碼監控")
            
            suppliers = SUPPLY_CHAIN_DB.get(target_sym, [("SPY", "美股大盤連動"), ("0050.TW", "台股權值連動")])
            chain_list = []
            price_series_dict = {target_sym: res['df']['Close']}
            
            for s_sym, role in suppliers:
                s_data = analyze_stock_full(s_sym)
                if s_data:
                    chain_list.append({
                        "代號": s_sym, "供應鏈角色/產業地位": role,
                        "現價": round(s_data['price'], 2), "5日動能": f"{s_data['mom5d']:+.2%}",
                        "RSI": round(s_data['rsi'], 1), "主力籌碼狀態": s_data['chip_status'],
                        "顧問評級": s_data['action'].split()[1], "目標價": round(s_data['target'], 2),
                        "停損價": round(s_data['stop_loss'], 2)
                    })
                    price_series_dict[s_sym] = s_data['df']['Close']

            if chain_list:
                st.dataframe(pd.DataFrame(chain_list), use_container_width=True)

            # 4. 供應鏈價格 30 日聯動相關係數矩陣 (Correlation Heatmap)
            st.markdown("---")
            st.subheader("🔥 供應鏈 30 日報酬相關係數熱圖 (識別領先 vs 落後補漲)")
            
            # 計算報酬率相關係數
            combined_df = pd.DataFrame(price_series_dict).dropna().tail(30)
            returns_df = combined_df.pct_change().dropna()
            corr_matrix = returns_df.corr().round(2)

            fig_corr = px.imshow(
                corr_matrix, text_auto=True, aspect="auto",
                color_continuous_scale="RdYlGn", title="30日股價報酬相關性 (數值越接近 1 代表聯動性極高)"
            )
            fig_corr.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_corr, use_container_width=True)
            
            st.caption("💡 **相關性應用法則**：若核心客戶（如 NVDA）已先行大漲，而相關係數高於 0.7 且籌碼偏多的供應鏈（如散熱/組裝）尚未發動，即為極佳之「落後補漲」勝率進場點。")

        else:
            st.error("無法取得該標的數據，請確認代碼（台股請加 .TW，例: 2330.TW）。")
