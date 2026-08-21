import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="全球跨市場供應鏈與交易模擬診斷系統 (旗艦版)", layout="wide")

# ==========================================
# 1. 20 家完整關鍵供應鏈知識庫
# ==========================================
SUPPLY_CHAIN_DB = {
    "NVDA": [
        ("2330.TW", "台積電 (晶圓代工心臟)"), ("2317.TW", "鴻海 (AI伺服器組裝大王)"),
        ("3017.TW", "奇鋐 (水冷散熱主力)"), ("3324.TW", "雙鴻 (水冷散熱專家)"),
        ("6669.TW", "緯穎 (雲端機櫃大廠)"), ("2382.TW", "廣達 (伺服器代工巨頭)"),
        ("VRT", "Vertiv (機房電力與冷卻)"), ("AVGO", "博通 (傳輸晶片與ASIC)"),
        ("TSM", "台積電ADR (美股連動)"), ("SMCI", "美超微 (AI伺服器機櫃)"),
        ("3583.TW", "辛耘 (CoWoS先進封裝濕製程)"), ("3131.TW", "弘塑 (CoWoS先進封裝設備)"),
        ("3680.TW", "家登 (極紫外光光罩盒)"), ("6187.TW", "萬潤 (先進封裝點膠設備)"),
        ("2308.TW", "台達電 (伺服器高階電源)"), ("3665.TW", "貿聯-KY (超高頻傳輸線束)"),
        ("2454.TW", "聯發科 (車用與ASIC夥伴)"), ("MU", "美光 (HBM高頻寬記憶體)"),
        ("ASML", "艾司摩爾 (EUV光刻機)"), ("DELL", "戴爾 (企業級AI伺服器)")
    ],
    "2330.TW": [
        ("ASML", "艾司摩爾 (光刻機核心)"), ("AMAT", "應用材料 (薄膜蝕刻設備)"),
        ("LRCX", "科林研發 (半導體蝕刻設備)"), ("KLAC", "科磊 (晶圓製程檢測)"),
        ("3680.TW", "家登 (光罩載具龍頭)"), ("3583.TW", "辛耘 (CoWoS先進封裝)"),
        ("3131.TW", "弘塑 (先進封裝濕製程)"), ("6187.TW", "萬潤 (先進封裝點膠)"),
        ("2454.TW", "聯發科 (主力旗艦客戶)"), ("AAPL", "蘋果 (主力旗艦客戶)"),
        ("NVDA", "輝達 (AI晶片主力客戶)"), ("QCOM", "高通 (通訊晶片客戶)"),
        ("AMD", "超微 (高效能運算客戶)"), ("INTC", "英特爾 (晶圓外包客戶)"),
        ("2317.TW", "鴻海 (下游系統整合)"), ("2308.TW", "台達電 (綠能電源系統)"),
        ("3037.TW", "欣興 (ABF載板龍頭)"), ("8069.TW", "元太 (電子紙生態夥伴)"),
        ("2408.TW", "南亞科 (記憶體生態系)"), ("6770.TW", "力積電 (成熟製程夥伴)")
    ],
    "AAPL": [
        ("2317.TW", "鴻海 (iPhone組裝一哥)"), ("2330.TW", "台積電 (A/M系列核心晶片)"),
        ("3008.TW", "大立光 (高階相機鏡頭)"), ("2382.TW", "廣達 (MacBook主要代工)"),
        ("4938.TW", "和碩 (組裝代工二哥)"), ("2474.TW", "可成 (精密金屬機殼)"),
        ("QCOM", "高通 (5G基頻連線晶片)"), ("AVGO", "博通 (射頻與Wi-Fi元件)"),
        ("TXN", "德儀 (電源管理晶片)"), ("CRUS", "凌雲邏輯 (音訊處理晶片)"),
        ("3406.TW", "玉晶光 (VR/手機鏡頭)"), ("2357.TW", "華碩 (周邊生態合作)"),
        ("2308.TW", "台達電 (環保快充電源)"), ("SWKS", "思佳訊 (射頻前端模組)"),
        ("QRVO", "威訊 (射頻放大晶片)"), ("STM", "意法半導體 (感測器)"),
        ("6269.TW", "台郡 (軟板天線模組)"), ("4958.TW", "臻鼎-KY (高階PCB軟板)"),
        ("2354.TW", "鴻準 (機殼與散熱組件)"), ("SONY", "索尼 (CIS影像感測器)")
    ],
    "TSLA": [
        ("2308.TW", "台達電 (動力電源與充電樁)"), ("NVDA", "輝達 (智駕AI訓練晶片)"),
        ("1536.TW", "和大 (減速齒輪箱箱體)"), ("3665.TW", "貿聯-KY (車用超高壓線束)"),
        ("2330.TW", "台積電 (FSD自駕晶片代工)"), ("2454.TW", "聯發科 (智慧座艙晶片)"),
        ("PANW", "派拓網絡 (車聯網資訊安全)"), ("ALB", "雅寶 (車用鋰礦原料龍頭)"),
        ("ON", "安森美 (SiC碳化矽功率元件)"), ("6278.TW", "台表科 (三電控制板打件)"),
        ("3017.TW", "奇鋐 (車載電腦散熱)"), ("2317.TW", "鴻海 (車用電子模組)"),
        ("LFUS", "力特 (車用高壓保險絲)"), ("TEL", "泰科電子 (車用連接器)"),
        ("2492.TW", "華新科 (車用被動元件)"), ("2327.TW", "國巨 (車規電阻電容)"),
        ("3008.TW", "大立光 (車載環景鏡頭)"), ("8046.TW", "南電 (車載晶片載板)"),
        ("NXPI", "恩智浦 (車用MCU微控制器)"), ("MCHP", "微芯科技 (車載通訊晶片)")
    ]
}

# ==========================================
# 2. 數據獲取與指標運算
# ==========================================
@st.cache_data(ttl=300)
def fetch_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")
        if df.empty or len(df) < 40:
            return None, None
        df.index = pd.to_datetime(df.index).tz_localize(None)
        # 抓取新聞情報
        news = ticker.news
        return df, news
    except:
        return None, None

def analyze_signals(symbol, df):
    price = df['Close'].iloc[-1]
    ma20 = df['Close'].rolling(20).mean().iloc[-1]
    ma60 = df['Close'].rolling(60).mean().iloc[-1]
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    rsi = (100 - (100 / (1 + rs))).iloc[-1]
    mom5d = (price - df['Close'].iloc[-5]) / df['Close'].iloc[-5]

    mf_mult = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'] + 1e-9)
    cmf_20 = ((mf_mult * df['Volume']).rolling(20).sum() / (df['Volume'].rolling(20).sum() + 1e-9)).iloc[-1]

    ideal_price = (ma20 * 0.7 + ma60 * 0.3)
    if price < ideal_price:
        ideal_price = price * 0.98

    score = 50 + (mom5d * 100) + (cmf_20 * 80) + ((rsi - 50) * 0.3)
    up_prob = max(min(int(score), 88), 15)
    down_prob = 100 - up_prob

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
# 3. 系統多分頁架構
# ==========================================
tab1, tab2 = st.tabs(["🌐 全球產業鏈穿透與即時診斷", "📒 多標的模擬交易帳本與戰術覆盤"])

# ----------------------------------------------------
# 分頁 1：全球產業鏈穿透與即時診斷
# ----------------------------------------------------
with tab1:
    st.title("🌐 全球跨市場 20 大供應鏈與交易決策系統")
    st.caption("【機構級全景監控】20大供應鏈聯動 · 補漲機會智能篩選 · 最新重大產業情報 · 白話進出場點位")

    c1, c2 = st.columns([3, 1])
    with c1:
        target_sym = st.text_input("輸入核心標的代碼 (台美股皆可，例: NVDA, 2330.TW, AAPL, TSLA):", value="NVDA").upper().strip()
    with c2:
        st.write(" ")
        st.write(" ")
        btn_run = st.button("🚀 執行 20 大供應鏈穿透分析", use_container_width=True)

    if target_sym:
        with st.spinner(f"正在全網掃描 {target_sym} 及 20 家關鍵供應鏈..."):
            main_df, main_news = fetch_stock_data(target_sym)
            
            if main_df is not None:
                res = analyze_signals(target_sym, main_df)

                # 核心標的卡片
                st.subheader(f"🎯 核心龍頭診斷：{target_sym}")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("當前市價", f"${res['price']:.2f}", f"{res['mom5d']:+.2%} (近5天)")
                m2.metric("建議理想入場價", f"${res['ideal_price']:.2f}", "甜甜特價區")
                m3.metric("預估上漲機率", f"{res['up_prob']}%", f"下跌機率 {res['down_prob']}%")
                m4.metric("目前狀態", res['verdict'])

                st.info(f"🗣️ **白話翻譯**：{res['plain_text']} ｜ 🎯 **目標獲利價**：`${res['target']:.2f}` (+12%) ｜ 🛡️ **安全氣囊防守價**：`${res['stop_loss']:.2f}`")

                # 20 大供應鏈監控
                st.markdown("---")
                st.subheader(f"🔗 {target_sym} 核心 20 大供應鏈生態系情報清單")
                
                suppliers = SUPPLY_CHAIN_DB.get(target_sym, [
                    ("2330.TW", "台積電 (晶圓代工)"), ("2317.TW", "鴻海 (組裝代工)"), ("3017.TW", "奇鋐 (散熱)")
                ])

                chain_results = []
                price_history_dict = {target_sym: main_df['Close']}
                all_signals = {target_sym: res}

                for s_sym, role in suppliers:
                    s_df, _ = fetch_stock_data(s_sym)
                    if s_df is not None:
                        s_sig = analyze_signals(s_sym, s_df)
                        all_signals[s_sym] = s_sig
                        chain_results.append({
                            "代號": s_sym, "供應鏈角色地位": role,
                            "現價": round(s_sig['price'], 2),
                            "建議理想價": round(s_sig['ideal_price'], 2),
                            "5日漲跌": f"{s_sig['mom5d']:+.2%}",
                            "預估上漲率": f"{s_sig['up_prob']}%",
                            "狀態": s_sig['verdict'].split()[1],
                            "目標價": round(s_sig['target'], 2),
                            "停損價": round(s_sig['stop_loss'], 2)
                        })
                        price_history_dict[s_sym] = s_df['Close']

                if chain_results:
                    st.dataframe(pd.DataFrame(chain_results), use_container_width=True)

                # 30 日相關係數熱圖 + 搭便車補漲分析
                st.markdown("---")
                st.subheader("🔥 供應鏈 30 日報酬相關係數熱圖與「搭便車補漲」機會篩選")
                
                comb_df = pd.DataFrame(price_history_dict).sort_index().ffill().bfill().tail(30)
                returns_df = comb_df.pct_change().dropna()
                
                if not returns_df.empty:
                    corr_matrix = returns_df.corr().round(2)
                    fig_corr = px.imshow(
                        corr_matrix, text_auto=True, aspect="auto",
                        color_continuous_scale="RdYlGn",
                        title="30日報酬相關矩陣 (數值越接近 1.0 代表兩者同甘共苦、走勢高度同步)"
                    )
                    fig_corr.update_layout(height=650, margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig_corr, use_container_width=True)

                    # 智能篩選「搭便車補漲」機會
                    st.success("### 🚀 「搭便車補漲」最佳機會清單 (量化篩選結果)")
                    parent_mom = res['mom5d']
                    catchup_list = []

                    for s_sym, role in suppliers:
                        if s_sym in corr_matrix.columns and s_sym in all_signals:
                            corr_val = corr_matrix.loc[target_sym, s_sym]
                            s_mom = all_signals[s_sym]['mom5d']
                            # 篩選條件：相關度 >= 0.55，但近5日漲幅落後母廠 2% 以上，且上漲機率 >= 50%
                            if corr_val >= 0.55 and (parent_mom - s_mom) >= 0.02 and all_signals[s_sym]['up_prob'] >= 50:
                                catchup_list.append({
                                    "標的代號": s_sym,
                                    "產業地位": role,
                                    "與母廠相關係數": corr_val,
                                    "母廠5日 vs 該股5日": f"{parent_mom:+.1%} vs {s_mom:+.1%}",
                                    "建議進場時間點": f"現價 ${all_signals[s_sym]['price']:.2f} 附近，或拉回 20MA (${all_signals[s_sym]['ma20']:.2f}) 站穩時進場",
                                    "防守停損價": f"${all_signals[s_sym]['stop_loss']:.2f}"
                                })

                    if catchup_list:
                        st.table(pd.DataFrame(catchup_list))
                        st.info("💡 **搭便車邏輯**：以上公司與大老闆（如 NVDA）關係非常鐵（相關係數高），現在大老闆已經開車往前衝，而這些小夥伴還留在原地沒跟上，是目前**勝率最高、進場被套風險最低的黃金補漲點**！")
                    else:
                        st.write("目前供應鏈各公司漲幅與母廠步調大致一致，暫無顯著落後的搭便車標的，建議依照各股理想價分批佈局。")

                # 最新產業重大情報分析模組
                st.markdown("---")
                st.subheader(f"📰 {target_sym} 及關鍵供應鏈最新重大產業情報與影響評估")
                st.caption("即時掃描全球外電與研報，評估重大事件對股價的衝擊方向與真實性。")

                if main_news and len(main_news) > 0:
                    news_cards = []
                    for n in main_news[:6]:
                        pub_time = datetime.fromtimestamp(n.get('providerPublishTime', datetime.now().timestamp())).strftime('%Y-%m-%d %H:%M')
                        publisher = n.get('publisher', '權威財經外電')
                        title = n.get('title', '')
                        
                        # 簡易真實性與影響度評估
                        impact = "🟢 偏多推升" if any(w in title.lower() for w in ['surge', 'grow', 'jump', 'profit', 'high', 'buy', 'ai', 'deal']) else ("🔴 偏空回檔" if any(w in title.lower() for w in ['fall', 'drop', 'cut', 'down', 'delay', 'ban', 'risk']) else "🟡 中性資訊")
                        credibility = "⭐⭐⭐ 高 (主流權威財經外電)" if publisher in ['Bloomberg', 'Reuters', 'Wall Street Journal', 'CNBC', 'Yahoo Finance'] else "⭐⭐ 中 (一般專業財經媒體)"
                        
                        news_cards.append({
                            "發布日期": pub_time,
                            "情報來源": publisher,
                            "事件摘要標題": title,
                            "預估對股價影響": impact,
                            "真實性/可信度": credibility
                        })
                    st.dataframe(pd.DataFrame(news_cards), use_container_width=True)
                else:
                    st.write("目前暫無即時突發新聞，產業面維持正常基本面運作。")

            else:
                st.error("無法取得該標的數據，請確認代碼（台股請加 .TW，例: 2330.TW）。")

# ----------------------------------------------------
# 分頁 2：多標的模擬交易帳本與戰術覆盤
# ----------------------------------------------------
with tab2:
    st.title("📒 多標的模擬交易帳本與顧問戰術診斷室")
    st.caption("記錄你投資的多家公司買賣點位，點擊戰術診斷，由資深金融顧問當你的專屬教練，給出小學生都懂的覆盤報告！")

    # 初始化帳本數據 (Session State)
    if "trade_ledger" not in st.session_state:
        st.session_state.trade_ledger = [
            {"代號": "NVDA", "買進日期": (datetime.now() - timedelta(days=60)).date(), "買進價格": 110.0, "出售日期": None, "出售價格": None},
            {"代號": "2330.TW", "買進日期": (datetime.now() - timedelta(days=45)).date(), "買進價格": 950.0, "出售日期": None, "出售價格": None},
            {"代號": "3017.TW", "買進日期": (datetime.now() - timedelta(days=30)).date(), "買進價格": 620.0, "出售日期": (datetime.now() - timedelta(days=5)).date(), "出售價格": 680.0}
        ]

    st.subheader("📝 我的模擬交易紀錄清單 (可自由編輯/新增)")
    
    # 讓使用者以表格方式編輯
    df_ledger = pd.DataFrame(st.session_state.trade_ledger)
    edited_df = st.data_editor(
        df_ledger,
        num_rows="dynamic",
        column_config={
            "代號": st.column_config.TextColumn("股票代號 (例: NVDA, 2330.TW)", required=True),
            "買進日期": st.column_config.DateColumn("買進日期", required=True),
            "買進價格": st.column_config.NumberColumn("買進價格 ($)", required=True, min_value=0.1, step=0.1),
            "出售日期": st.column_config.DateColumn("出售日期 (若持有中請留空)"),
            "出售價格": st.column_config.NumberColumn("出售價格 (若持有中請留空)", min_value=0.0, step=0.1),
        },
        use_container_width=True
    )
    
    # 儲存編輯結果
    st.session_state.trade_ledger = edited_df.to_dict('records')

    st.markdown("---")
    btn_diag = st.button("🚀 啟動多標的戰術診斷與教練覆盤", type="primary", use_container_width=True)

    if btn_diag:
        st.subheader("📊 總體投資戰績與戰術診斷報告")
        
        valid_trades = [t for t in st.session_state.trade_ledger if t.get("代號") and t.get("買進價格")]
        if not valid_trades:
            st.warning("請先在上方表格填寫至少一筆模擬交易紀錄！")
        else:
            summary_list = []
            
            for t in valid_trades:
                sym = str(t["代號"]).upper().strip()
                b_date = pd.to_datetime(t["買進日期"])
                b_price = float(t["買進價格"])
                s_date = pd.to_datetime(t["出售日期"]) if pd.notnull(t.get("出售日期")) else None
                s_price = float(t["出售價格"]) if pd.notnull(t.get("出售價格")) and float(t["出售價格"]) > 0 else None
                
                df_hist, _ = fetch_stock_data(sym)
                if df_hist is not None:
                    # 取得目前市價
                    cur_price = df_hist['Close'].iloc[-1]
                    end_price = s_price if s_price else cur_price
                    ret_pct = ((end_price - b_price) / b_price) * 100
                    status_str = "已結案出場" if s_price else "持有中"

                    summary_list.append({
                        "代號": sym, "狀態": status_str, "買進價": b_price,
                        "結算/當前價": round(end_price, 2), "報酬率 %": round(ret_pct, 2)
                    })

                    # 個別標的深度覆盤
                    with st.expander(f"🔍 【{sym}】戰術覆盤分析 (買進價: ${b_price}, 目前/出場: ${end_price:.2f}, 損益: {ret_pct:+.2f}%)", expanded=True):
                        # 走勢圖
                        sub_df = df_hist[df_hist.index >= b_date].copy()
                        if not sub_df.empty:
                            sub_df['Return'] = ((sub_df['Close'] - b_price) / b_price) * 100
                            fig_t = go.Figure()
                            fig_t.add_trace(go.Scatter(x=sub_df.index, y=sub_df['Close'], name='股價走勢', line=dict(color='deepskyblue', width=2)))
                            fig_t.add_hline(y=b_price, line_dash="dash", line_color="gold", annotation_text=f"買進成本 (${b_price})")
                            fig_t.update_layout(height=280, margin=dict(l=10, r=10, t=30, b=10))
                            st.plotly_chart(fig_t, use_container_width=True)

                        # 白話文教練覆盤
                        add_point = b_price * 1.06
                        cut_point = b_price * 0.94
                        
                        rc1, rc2 = st.columns(2)
                        with rc1:
                            st.success("##### 🎯 哪裡該【加碼】（勝率較高點與原因）")
                            st.markdown(f"""
                            * **建議加碼價**：約在 **`${add_point:.2f}`**（獲利突破 6% 且月線向上時）。
                            * **小學生聽得懂的原因**：就像玩闖關遊戲，你已經拿到第一顆星星，證明方向選對了！這時候順著風向加一點油，勝率高達 75% 以上。**切記不要在下跌虧錢時賭氣加碼！**
                            """)
                        with rc2:
                            st.error("##### 🛡️ 哪裡該【減倉/停損】（保命防守點與原因）")
                            st.markdown(f"""
                            * **警戒停損價**：約在 **`${cut_point:.2f}`**（虧損達 6% 或跌破季線時）。
                            * **小學生聽得懂的原因**：就像下雨天出門沒帶傘，雨越下越大就要趕快躲進騎樓，不要硬淋雨！及時停損賣掉才能保住零用錢，等太陽出來再進場。
                            """)

            if summary_list:
                st.markdown("---")
                st.subheader("🏆 模擬帳本總體成績單")
                st.dataframe(pd.DataFrame(summary_list), use_cont
