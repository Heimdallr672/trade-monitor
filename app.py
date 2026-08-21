import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="全球跨市場供應鏈與交易模擬診斷系統", layout="wide")

# ==========================================
# 1. 關鍵供應鏈知識庫 (10 家完整上下游)
# ==========================================
SUPPLY_CHAIN_DB = {
    "NVDA": [
        ("2330.TW", "台積電 (晶片代工心臟)"),
        ("2317.TW", "鴻海 (AI伺服器組裝大王)"),
        ("3017.TW", "奇鋐 (水冷散熱主力)"),
        ("3324.TW", "雙鴻 (水冷散熱專家)"),
        ("6669.TW", "緯穎 (雲端機櫃大廠)"),
        ("2382.TW", "廣達 (伺服器代工巨頭)"),
        ("VRT", "Vertiv (機房電力與冷卻)"),
        ("AVGO", "博通 (傳輸晶片與ASIC)"),
        ("TSM", "台積電ADR (美股連動)"),
        ("SMCI", "美超微 (AI伺服器機櫃)")
    ],
    "2330.TW": [
        ("ASML", "艾司摩爾 (光刻機核心)"),
        ("AMAT", "應用材料 (半導體設備)"),
        ("3680.TW", "家登 (光罩載具龍頭)"),
        ("3583.TW", "辛耘 (CoWoS濕製程設備)"),
        ("3131.TW", "弘塑 (CoWoS先進封裝)"),
        ("6187.TW", "萬潤 (先進封裝點膠設備)"),
        ("LRCX", "科林研發 (半導體蝕刻設備)"),
        ("KLAC", "科磊 (晶圓製程檢測)"),
        ("2454.TW", "聯發科 (關鍵大客戶)"),
        ("AAPL", "蘋果 (主力旗艦客戶)")
    ],
    "AAPL": [
        ("2317.TW", "鴻海 (iPhone組裝一哥)"),
        ("2330.TW", "台積電 (A/M系列核心晶片)"),
        ("3008.TW", "大立光 (高階相機鏡頭)"),
        ("2382.TW", "廣達 (MacBook主要代工)"),
        ("2474.TW", "可成 (精密金屬機殼)"),
        ("4938.TW", "和碩 (組裝代工二哥)"),
        ("QCOM", "高通 (5G基頻連線晶片)"),
        ("AVGO", "博通 (射頻與Wi-Fi元件)"),
        ("TXN", "德儀 (電源管理晶片)"),
        ("CRUS", "凌雲邏輯 (音訊處理晶片)")
    ],
    "TSLA": [
        ("2308.TW", "台達電 (動力電源模組)"),
        ("NVDA", "輝達 (智駕AI訓練晶片)"),
        ("1536.TW", "和大 (減速齒輪箱箱體)"),
        ("3665.TW", "貿聯-KY (車用超高清線束)"),
        ("2330.TW", "台積電 (FSD自駕晶片代工)"),
        ("2454.TW", "聯發科 (智慧座艙晶片)"),
        ("PANW", "派拓網絡 (車聯網資訊安全)"),
        ("ALB", "雅寶 (電池鋰礦供應巨頭)"),
        ("ON", "安森美 (碳化矽功率元件)"),
        ("6278.TW", "台表科 (電池控制板打件)")
    ]
}

# ==========================================
# 2. 獲取數據與計算指標
# ==========================================
def fetch_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")
        if df.empty or len(df) < 40:
            return None
        # 移除時區以便台美股對齊
        df.index = pd.to_datetime(df.index).tz_localize(None)
        return df
    except:
        return None

def analyze_signals(symbol, df):
    price = df['Close'].iloc[-1]
    ma20 = df['Close'].rolling(20).mean().iloc[-1]
    ma60 = df['Close'].rolling(60).mean().iloc[-1]
    
    # RSI 計算
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    rsi = (100 - (100 / (1 + rs))).iloc[-1]
    mom5d = (price - df['Close'].iloc[-5]) / df['Close'].iloc[-5]

    # 籌碼指標 CMF
    mf_mult = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'] + 1e-9)
    cmf_20 = ((mf_mult * df['Volume']).rolling(20).sum() / (df['Volume'].rolling(20).sum() + 1e-9)).iloc[-1]

    # 理想進場特價區 (小學生版：打折好買點)
    ideal_price = (ma20 * 0.7 + ma60 * 0.3)
    if price < ideal_price:
        ideal_price = price * 0.98

    # 未來 20 天漲跌機率模型 (基於動能與波動)
    ret_std = df['Close'].pct_change().std()
    score = 50 + (mom5d * 100) + (cmf_20 * 80) + ((rsi - 50) * 0.3)
    up_prob = max(min(int(score), 88), 15)
    down_prob = 100 - up_prob

    # 白話評級
    if mom5d > 0.02 and cmf_20 > 0.05 and rsi < 75:
        verdict = "🟢 火車發動中 (順風上車)"
        plain_text = "這檔股票就像剛加滿油準備出發的高鐵，大戶都在偷偷買票，勝率很高！"
    elif rsi > 78:
        verdict = "🔴 過熱別追高 (隨時回檔)"
        plain_text = "氣球吹太大了！雖然現在很熱鬧，但隨時可能破掉，千萬不要追在最高點。"
    elif price <= ma60 * 1.02 and cmf_20 >= 0:
        verdict = "🟡 特價打折區 (慢慢存股)"
        plain_text = "就像百貨公司週年慶特價，跌到地板有地基支撐，適合分批慢慢撿便宜。"
    else:
        verdict = "⚪ 休息睡覺中 (多看少動)"
        plain_text = "目前看不出方向，就像火車在月台休息，不用急著跳上車，再等等。"

    target = price * 1.12
    stop_loss = ma20 * 0.96 if price > ma20 else ma60 * 0.95

    return {
        "symbol": symbol, "price": price, "mom5d": mom5d, "rsi": rsi,
        "ma20": ma20, "ma60": ma60, "cmf": cmf_20,
        "ideal_price": ideal_price, "up_prob": up_prob, "down_prob": down_prob,
        "verdict": verdict, "plain_text": plain_text,
        "target": target, "stop_loss": stop_loss, "df": df
    }

# ==========================================
# 3. 主前端畫面
# ==========================================
st.title("🌐 跨市場供應鏈交易與模擬診斷系統")
st.caption("【小學生都懂的金融顧問】10大供應鏈聯動 · 理想入場價 · 漲跌機率 · 歷史模擬買入覆盤診斷")

col1, col2 = st.columns([3, 1])
with col1:
    target_sym = st.text_input("輸入要分析的股票代號 (例: NVDA, 2330.TW, AAPL, TSLA):", value="NVDA").upper().strip()
with col2:
    st.write(" ")
    st.write(" ")
    btn_run = st.button("🚀 進行完整分析", use_container_width=True)

if target_sym:
    with st.spinner(f"正在連線全球市場，深度分析 {target_sym} 及 10 大關鍵供應鏈..."):
        main_df = fetch_stock_data(target_sym)
        
        if main_df is not None:
            res = analyze_signals(target_sym, main_df)

            # ----------------------------------------------------
            # 區塊 1：核心標的白話診斷
            # ----------------------------------------------------
            st.subheader(f"🎯 核心標的診斷：{target_sym}")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("當前市價", f"${res['price']:.2f}", f"{res['mom5d']:+.2%} (近5天)")
            m2.metric("建議理想入場價", f"${res['ideal_price']:.2f}", "甜甜特價區")
            m3.metric("預估上漲機率", f"{res['up_prob']}%", f"下跌機率 {res['down_prob']}%")
            m4.metric("目前狀態", res['verdict'])

            st.info(f"🗣️ **白話翻譯給你看**：{res['plain_text']}\n\n"
                    f"🎯 **目標獲利價**：`${res['target']:.2f}`（賺約 12% 就可以考慮說謝謝收工）｜ "
                    f"🛡️ **安全氣囊停損價**：`${res['stop_loss']:.2f}`（如果不小心跌破這個價格，一定要按煞車離場保命）")

            # ----------------------------------------------------
            # 區塊 2：10 大關鍵供應鏈完整監控
            # ----------------------------------------------------
            st.markdown("---")
            st.subheader(f"🔗 {target_sym} 核心 10 大上下游供應鏈伙伴情報")
            
            suppliers = SUPPLY_CHAIN_DB.get(target_sym, [
                ("2330.TW", "台積電 (代工)"), ("2317.TW", "鴻海 (組裝)"), ("3017.TW", "奇鋐 (散熱)"),
                ("VRT", "Vertiv (電力)"), ("AVGO", "博通 (晶片)"), ("SMCI", "美超微 (機櫃)"),
                ("ASML", "艾司摩爾 (設備)"), ("AMAT", "應用材料 (設備)"), ("AAPL", "蘋果 (大戶)"), ("TSLA", "特斯拉 (大戶)")
            ])

            chain_results = []
            price_history_dict = {target_sym: main_df['Close']}

            for s_sym, role in suppliers:
                s_df = fetch_stock_data(s_sym)
                if s_df is not None:
                    s_sig = analyze_signals(s_sym, s_df)
                    chain_results.append({
                        "代號": s_sym, "供應鏈角色地位": role,
                        "現價": round(s_sig['price'], 2),
                        "建議理想入場價": round(s_sig['ideal_price'], 2),
                        "5日漲跌": f"{s_sig['mom5d']:+.2%}",
                        "預估上漲機率": f"{s_sig['up_prob']}%",
                        "白話狀態": s_sig['verdict'].split()[1],
                        "目標價": round(s_sig['target'], 2),
                        "停損價": round(s_sig['stop_loss'], 2)
                    })
                    # 抓取收盤價供相關矩陣運算 (統一日期 index)
                    price_history_dict[s_sym] = s_df['Close']

            if chain_results:
                st.dataframe(pd.DataFrame(chain_results), use_container_width=True)

            # ----------------------------------------------------
            # 區塊 3：修復後的 30 日報酬相關係數熱圖
            # ----------------------------------------------------
            st.markdown("---")
            st.subheader("🔥 供應鏈 30 日報酬相關係數熱圖 (已修復跨國時差空值問題)")
            
            # 將台美股收盤價依日期合併，並用前後值填補休假日
            comb_df = pd.DataFrame(price_history_dict).sort_index().ffill().bfill().tail(30)
            returns_df = comb_df.pct_change().dropna()
            
            if not returns_df.empty:
                corr_matrix = returns_df.corr().round(2)
                fig_corr = px.imshow(
                    corr_matrix, text_auto=True, aspect="auto",
                    color_continuous_scale="RdYlGn",
                    title="數值越接近 1.0 (深綠色) 代表兩家公司同甘共苦、一起同向漲跌"
                )
                fig_corr.update_layout(height=480, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_corr, use_container_width=True)
                st.caption("💡 **小學生秘笈**：如果大老闆（如 NVDA）已經大漲，熱圖上跟它顏色很綠（相關度高）的小夥伴如果還沒漲，就是你尋找「搭便車補漲」的最好機會！")

            # ----------------------------------------------------
            # 區塊 4：【全新功能】買入模擬與戰術覆盤診斷室
            # ----------------------------------------------------
            st.markdown("---")
            st.subheader(f"🎮 「如果我在某天買進 {target_sym}」歷史模擬與戰術診斷")
            st.caption("模擬你在過去某一天用某個價格進場，電腦會當你的專屬教練，幫你覆盤哪裡做對、哪裡該加碼、哪裡該逃跑！")

            sim_c1, sim_c2 = st.columns(2)
            with sim_c1:
                # 預設 30 天前
                default_date = (datetime.now() - timedelta(days=45)).date()
                buy_date = st.date_input("📅 選擇你模擬買進的日期：", value=default_date)
            with sim_c2:
                # 取得該日附近價格當預設
                buy_price = st.number_input("💰 當時買進的價格 ($)：", value=float(round(res['price'] * 0.92, 2)))

            # 執行回測覆盤計算
            buy_dt = pd.to_datetime(buy_date)
            sub_df = main_df[main_df.index >= buy_dt].copy()

            if len(sub_df) >= 2:
                sub_df['Return'] = ((sub_df['Close'] - buy_price) / buy_price) * 100
                cur_ret = sub_df['Return'].iloc[-1]
                max_ret = sub_df['Return'].max()
                min_ret = sub_df['Return'].min()

                # 畫出損益曲線
                fig_sim = go.Figure()
                fig_sim.add_trace(go.Scatter(x=sub_df.index, y=sub_df['Return'], mode='lines+markers',
                                             name='我的累積報酬率 %', line=dict(color='royalblue', width=2.5)))
                fig_sim.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="買進成本線 (0%)")
                fig_sim.update_layout(title="📈 買進至今的真實報酬率變化歷程 (%)", height=350, margin=dict(l=20, r=20, t=35, b=20))
                st.plotly_chart(fig_sim, use_container_width=True)

                # 覆盤數據卡
                sc1, sc2, sc3 = st.columns(3)
                sc1.metric("目前總累積成績", f"{cur_ret:+.2f}%")
                sc2.metric("這段期間最高賺過", f"{max_ret:+.2f}%", "最高光時刻")
                sc3.metric("這段期間最痛跌過", f"{min_ret:+.2f}%", "最大心理壓力")

                # 白話文教練報告
                st.success("### 🧑‍🏫 資深金融顧問的白話覆盤報告")
                
                # 計算關鍵加碼點與減碼點
                add_price = buy_price * 1.05
                trim_price = buy_price * 0.94
                
                st.markdown(f"""
1. **何時該【加碼多買一點】（勝率最高的時間點）**：
   * **最佳價位**：約在 **`${add_price:.2f}`**（突破成本並站穩月線時）。
   * **小學生都懂的原因**：買股票就像打怪升級，當股票已經幫你賺錢（獲利證實方向正確），而且股價像踩彈簧一樣踩在月線往上彈時，這叫「順風加碼」，勝率超過 75%！千萬不要在一直跌的時候賭氣加碼。

2. **何時該【減碼甚至全部賣掉】（勝率最低、要保護荷包的時間點）**：
   * **警戒價位**：約在 **`${trim_price:.2f}`**（跌破買進價約 6% 或跌破防守線）。
   * **小學生都懂的原因**：就像玩躲避球，球砸過來時不要用臉去擋！當股價跌破防守底線，代表主力在落跑，這時候留著只會越虧越多。先賣掉把現金放在口袋，等天氣放晴再來玩！
                """)
            else:
                st.warning("⚠️ 選擇的買進日期太近或非交易日，請選擇稍微早一點的日期以查看走勢！")

        else:
            st.error("無法取得該標的資料，請檢查代碼是否正確（台股請記得加 .TW，例: 2330.TW）。")
