# [01. 설정 및 라이브러리]
import streamlit as st
import yfinance as yf
import pandas as pd
import time
import urllib.parse
import datetime
import zoneinfo
st.cache_data.clear()
now = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Seoul"))
from streamlit_autorefresh import st_autorefresh

# [02. 데이터 연결 ID]
INFO_SHEET_ID = "10BZzLb5lKxujiVo1ktxPih-4n6_mWW_A4YaofmCVcTo"
DATA_SHEET_ID = "10XzkMRByoPPjJ9ycm7i6IaaOpKEpBHaK8g6RQpE65sk"

# [03. 시트 데이터 함수]
def get_cell_value(cell_range):
    url = f"https://docs.google.com/spreadsheets/d/{INFO_SHEET_ID}/gviz/tq?tqx=out:csv&range={cell_range}"
    try:
        df = pd.read_csv(url, header=None)
        return str(df.iloc[0, 0]) if not df.empty else "데이터 없음"
    except: return "데이터 없음"

def load_data():
    sheet_url = f"https://docs.google.com/spreadsheets/d/{DATA_SHEET_ID}/export?format=csv&t={time.time()}"
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip()
    return df.fillna("")

# [04. 시장 데이터 로드 함수]
def get_market_data():
    tickers = {
        "코스피": "^KS11", 
        "코스닥": "^KQ11", 
        "나스닥": "^IXIC",
        "코스피선물": "069500.KS",
        "환율": "USDKRW=X",
        "S&P500": "^GSPC"
    }
    data = {}
    for name, ticker in tickers.items():
        try:
            df = yf.Ticker(ticker).history(period="5d")
            if not df.empty:
                curr = float(df['Close'].iloc[-1])
                prev = float(df['Close'].iloc[-2]) if len(df) > 1 else curr
                data[name] = {"curr": round(curr, 2), "diff": round(curr - prev, 2)}
            else:
                data[name] = {"curr": 0.0, "diff": 0.0}
        except:
            data[name] = {"curr": 0.0, "diff": 0.0}
    return data
# [05. 로그인 로직]
if "password_correct" not in st.session_state: st.session_state["password_correct"] = False

# [06. 화면 UI]
if not st.session_state["password_correct"]:
    st.set_page_config(layout="wide")
    col_a, col_b = st.columns([1, 1])
    col_a.subheader("📊 오늘의 종합 시황")
    now_time = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Seoul")).strftime('%Y-%m-%d %H:%M')
    col_b.markdown(f"<div style='text-align: right;'>📅 {now_time}</div>", unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style="background: #1a1a1a; padding: 20px; border-radius: 15px; border: 3px solid #FFD700; box-shadow: 0 0 15px #FFD700; margin-bottom: 30px;">
            <div style="color: #FFD700; font-size: 14px; margin-bottom: 10px; font-weight: bold;">★ 오늘의 투자 격언 ★</div>
            <marquee behavior="scroll" direction="left" scrollamount="7" style="color: #FFFFFF; font-size: 24px; font-weight: bold;">{get_cell_value('B6')}</marquee>
        </div>
    """, unsafe_allow_html=True)    
    

# [07. 시황 데이터 출력]
    m = get_market_data()
    c1, c2, c3 = st.columns(3)
    c1.metric("코스피", m["코스피"]["curr"], m["코스피"]["diff"])
    c2.metric("코스닥", m["코스닥"]["curr"], m["코스닥"]["diff"])
    c3.metric("코스피선물", m["코스피선물"]["curr"], m["코스피선물"]["diff"])
    c4, c5, c6 = st.columns(3)
    c4.metric("환율", m["환율"]["curr"], m["환율"]["diff"])
    c5.metric("나스닥", m["나스닥"]["curr"], m["나스닥"]["diff"])
    c6.metric("S&P500", m["S&P500"]["curr"], m["S&P500"]["diff"])
    
    st.subheader("📢 오늘의 공지사항")
    st.info(f"📌 {get_cell_value('B2')}")
    
    st.markdown("---")
    pwd = st.text_input("🔑 암호를 입력하십시오.", type="password")
    if st.button("로그인"):
        if pwd == "rkwhr42": st.session_state["password_correct"] = True; st.rerun()
        else: st.error("암호가 틀렸습니다.")
    st.stop()

# [08. 종목 일람표 데이터 처리]
df = load_data()
st.markdown(f"""
    <div style="background: #e8f5e9; padding: 15px; border-radius: 10px; border-left: 5px solid #2e7d32; margin-bottom: 20px;">
        <div style="color: #2e7d32; font-weight: bold;">📢 오늘의 이슈</div>
        <marquee style="color: #1b5e20; font-size: 18px; font-weight: bold;">{get_cell_value('B4')}</marquee>
    </div>
""", unsafe_allow_html=True)

def clear_search(): st.session_state["search_bar"] = ""
col1, col2 = st.columns([1, 1])

# [09. 종목 필터링 및 표]
display_df = pd.DataFrame()
if '테마' in df.columns:
    themes = df['테마'].unique()
    with col1: selected_theme = st.selectbox("📂 테마 선택", themes, on_change=clear_search)
    with col2: search_query = st.text_input("🔍 종목명 직접 검색", key="search_bar")
    if search_query: display_df = df[df['종목명'].astype(str).str.contains(search_query, na=False)]
    elif selected_theme: display_df = df[df['테마'] == selected_theme]
    else: display_df = df.copy()
else:
    st.error("시트에서 '테마' 컬럼을 찾을 수 없습니다.")
    display_df = df.copy()

if not display_df.empty:
    display_df['종목명'] = display_df.apply(lambda x: "🔥 " + str(x['종목명']) if '지정가' in str(x.values).replace(" ", "") and '근접' in str(x.values).replace(" ", "") else str(x['종목명']), axis=1)

st.subheader("📋 종목 일람표")
cols = ['종목명', '현재가', '변동율', '매집평단', '평단비율', '현재단계', '예상고점']
valid_cols = [c for c in cols if c in display_df.columns]
def color_text(val):
    try:
        num = float(str(val).replace('%', '').replace(',', '').strip())
        return 'color: red;' if num > 0 else 'color: blue;' if num < 0 else 'color: black;'
    except: return 'color: black;'
styled_df = display_df[valid_cols].style.map(color_text, subset=['변동율', '평단비율'])
event = st.dataframe(styled_df, use_container_width=True, selection_mode="single-row", on_select="rerun")

# [10. 상세 분석 및 링크]
if 'event' in locals() and len(event.selection.rows) > 0:
    idx = event.selection.rows[0]
    row = display_df.iloc[idx]
    st.markdown(f"---")
    st.markdown(f"### 🔍 **{row['종목명']}** 상세 분석")
    if '뉴스 와 펄' in row and row['뉴스 와 펄']: st.info(f"📌 **참고 자료**: {row['뉴스 와 펄']}")
    stock_name = urllib.parse.quote(str(row['종목명']))
    st.markdown(f"""
        <div style="display: flex; gap: 150px; margin-bottom: 20px;">
            <a href="https://search.naver.com/search.naver?query={stock_name}+주가" target="_blank" style="padding:15px; border:2px solid #555; border-radius:8px; text-decoration:none; color:black;font-size: 13px;">📈 네이버증권</a>
            <a href="https://dart.fss.or.kr/dsab001/main.do?textCrpNm={stock_name}" target="_blank" style="padding:15px; border:2px solid #555; border-radius:8px; text-decoration:none; color:black;font-size: 13px;">📢 DART공시</a>
            <a href="https://gemini.google.com/app" target="_blank" style="padding:15px; border:2px solid #555; border-radius:8px; text-decoration:none; color:black;font-size: 13px;">🚀 제미나이 가기</a>
        </div>
    """, unsafe_allow_html=True)
    st.subheader("📋 분석 대상 데이터 복사")
    persona_prompt = (f"분석 대상: {row['종목명']}\n참고용 기존 자료: {row.get('뉴스 와 펄', '없음')}\n\n"
                      "지시사항:\n1. 웹 검색을 통해 해당 종목의 '최신 뉴스'와 '최신 공시'를 우선적으로 찾아줘.\n"
                      "2. 기존 자료는 참고만 하고, 최신 실시간 정보를 기반으로 기업의 핵심 이슈를 정리해줘.\n"
                      "3. 가격, 매매 전략, 평단가 등은 배제하고 오직 기업의 강점과 약점, 사업 가치와 최신 뉴스 흐름 위주로 보고해줘.")
    st.code(persona_prompt, language="text")
