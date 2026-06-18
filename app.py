import streamlit as st
import yfinance as yf
import pandas as pd
import os
import time
import urllib.parse
from streamlit_autorefresh import st_autorefresh

# 파일 경로 설정
NOTICE_FILE = "notice.txt"
NEWS_FILE = "news.txt"
QUOTE_FILE = "quote.txt"

# [데이터 가져오기 함수]
def get_market_data():
    tickers = {"코스피": "^KS11", "코스닥": "^KQ11", "코스피선물": "069500.KS", "환율": "USDKRW=X", "나스닥": "^IXIC", "S&P500": "^GSPC"}
    data = {}
    for name, ticker in tickers.items():
        try:
            df = yf.Ticker(ticker).history(period="2d")
            if not df.empty:
                curr, prev = df['Close'].iloc[-1], df['Close'].iloc[-2]
                data[name] = {"curr": round(curr, 2), "diff": round(curr - prev, 2)}
            else: data[name] = {"curr": 0, "diff": 0}
        except: data[name] = {"curr": 0, "diff": 0}
    return data

def load_data():
    url = f"https://docs.google.com/spreadsheets/d/10XzkMRByoPPjJ9ycm7i6IaaOpKEpBHaK8g6RQpE65sk/export?format=csv&t={time.time()}"
    return pd.read_csv(url).fillna("")

# [세션 상태 초기화]
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False


# [로그인 전 화면]
if not st.session_state["password_correct"]:
    st.set_page_config(layout="wide")
    col_a, col_b = st.columns([1, 1])
    col_a.subheader("📊 오늘의 종합 시황")
    col_b.markdown(f"<div style='text-align: right;'>📅 {time.strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)
    
    # 강조된 격언 전광판
    if os.path.exists(QUOTE_FILE):
        with open(QUOTE_FILE, "r", encoding="utf-8") as f:
            q = f.read()
            if q.strip():
                st.markdown(f"""
                <div style="background: #1a1a1a; padding: 20px; border-radius: 15px; border: 3px solid #FFD700; box-shadow: 0 0 15px #FFD700; margin-bottom: 30px;">
                    <div style="color: #FFD700; font-size: 14px; margin-bottom: 10px; font-weight: bold;">★ 오늘의 투자 격언 ★</div>
                    <marquee behavior="scroll" direction="left" scrollamount="7" style="color: #FFFFFF; font-size: 24px; font-weight: bold;">{q}</marquee>
                </div>
                """, unsafe_allow_html=True)
    
    # 시장 지수
    m = get_market_data()
    c1, c2, c3 = st.columns(3)
    c1.metric("코스피", m["코스피"]["curr"], m["코스피"]["diff"])
    c2.metric("코스닥", m["코스닥"]["curr"], m["코스닥"]["diff"])
    c3.metric("코스피선물", m["코스피선물"]["curr"], m["코스피선물"]["diff"])
    c4, c5, c6 = st.columns(3)
    c4.metric("환율", m["환율"]["curr"], m["환율"]["diff"])
    c5.metric("나스닥", m["나스닥"]["curr"], m["나스닥"]["diff"])
    c6.metric("S&P500", m["S&P500"]["curr"], m["S&P500"]["diff"])
    
    # [추가됨] 지수 아래 공지사항 출력
    st.subheader("📢 오늘의 공지사항")
    if os.path.exists(NOTICE_FILE):
        with open(NOTICE_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            st.info(f"📌 {content}" if content.strip() else "등록된 공지가 없습니다.")
    
    st.markdown("---")
    
    pwd = st.text_input("🔑 암호를 입력하십시오.", type="password")
    if st.button("로그인"):
        if pwd == "rkwhr42":
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("암호가 틀렸습니다.")
    st.stop() # 로그인 전 화면 끝










# --- [로그인 성공 후 화면] ---
st_autorefresh(interval=300000, key="datarefresh") # 로그인 후 새로고침 시작

# 지수 출력 없음 (깔끔하게 이슈 전광판만 출력)
daily_issue = open(NEWS_FILE, "r", encoding="utf-8").read() if os.path.exists(NEWS_FILE) else "📢 등록된 오늘의 이슈가 없습니다."
st.markdown(f"""
    <div style="background: #e8f5e9; padding: 15px; border-radius: 10px; border-left: 5px solid #2e7d32; margin-bottom: 20px;">
        <div style="color: #2e7d32; font-weight: bold;">📢 오늘의 이슈</div>
        <marquee style="color: #1b5e20; font-size: 18px; font-weight: bold;">{daily_issue}</marquee>
    </div>
""", unsafe_allow_html=True)





# 3. 사이드바 관리 (동일하게 유지)
with st.sidebar:
    st.header("👩‍💼 제나의 통합 관리")
    
    # 1. 공지사항
    n = st.text_area("공지 수정:", value=open(NOTICE_FILE, "r", encoding="utf-8").read() if os.path.exists(NOTICE_FILE) else "", height=100)
    
    # 2. 오늘의 이슈 (로그인 후용)
    i = st.text_area("오늘의 이슈 수정:", value=open(NEWS_FILE, "r", encoding="utf-8").read() if os.path.exists(NEWS_FILE) else "", height=80)
    
    # 3. 오늘의 격언 (로그인 전용)
    q = st.text_input("오늘의 격언 수정 (로그인 전):", value=open(QUOTE_FILE, "r", encoding="utf-8").read() if os.path.exists(QUOTE_FILE) else "")
    
    if st.button("내용 업데이트 저장"):
        with open(NOTICE_FILE, "w", encoding="utf-8") as f: f.write(n)
        with open(NEWS_FILE, "w", encoding="utf-8") as f: f.write(i)
        with open(QUOTE_FILE, "w", encoding="utf-8") as f: f.write(q)
        st.success("저장 완료!")
        st.rerun()


# 3. 데이터 로드 (강제 새로고침 적용: 시간값 t 추가)
def load_data():
    sheet_url = f"https://docs.google.com/spreadsheets/d/10XzkMRByoPPjJ9ycm7i6IaaOpKEpBHaK8g6RQpE65sk/export?format=csv&t={time.time()}"
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip()
    return df.fillna("")

df = load_data()

# 5. 검색 및 일람표 (데이터 처리)
def clear_search(): st.session_state["search_bar"] = ""
col1, col2 = st.columns([1, 1])
themes = df['테마'].unique() if not df.empty and '테마' in df.columns else []
with col1: selected_theme = st.selectbox("📂 테마 선택", themes, on_change=clear_search)
with col2: search_query = st.text_input("🔍 종목명 직접 검색", key="search_bar")

if search_query:
    filtered_df = df[df['종목명'].astype(str).str.contains(search_query, na=False)]
else:
    filtered_df = df[df['테마'] == selected_theme]

# 전광판과 일람표용 데이터프레임
display_df = filtered_df.copy()




# 일람표 서식 적용
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

# 6. 상세 분석 리포트 (기존 버튼 간격 유지)
if len(event.selection.rows) > 0:
    idx = event.selection.rows[0]
    row = filtered_df.iloc[idx]
    
    st.markdown(f"---")
    st.markdown(f"### 🔍 **{row['종목명']}** 상세 분석")
    
    if '뉴스 와 펄' in row and row['뉴스 와 펄']:
        st.info(f"📌 **참고 자료**: {row['뉴스 와 펄']}")
    
    stock_name = urllib.parse.quote(str(row['종목명']))
    st.markdown(f"""
        <div style="display: flex; gap: 150px; margin-bottom: 20px;">
            <a href="https://search.naver.com/search.naver?query={stock_name}+주가" target="_blank" style="padding:15px; border:2px solid #555; border-radius:8px; text-decoration:none; color:black;font-size: 13px;">📈 네이버증권</a>
            <a href="https://dart.fss.or.kr/dsab001/main.do?textCrpNm={stock_name}" target="_blank" style="padding:15px; border:2px solid #555; border-radius:8px; text-decoration:none; color:black;font-size: 13px;">📢 DART공시</a>
            <a href="https://gemini.google.com/app" target="_blank" style="padding:15px; border:2px solid #555; border-radius:8px; text-decoration:none; color:black;font-size: 13px;">🚀 제미나이 가기</a>
        </div>
    """, unsafe_allow_html=True)
    
    st.subheader("📋 분석 대상 데이터 복사")
    persona_prompt = (f"너는 나만의 주식 투자 전문 비서야. 나는 대장이야.\n\n"
                      f"분석 대상: {row['종목명']}\n참고용 기존 자료: {row.get('뉴스 와 펄', '없음')}\n\n"
                      "지시사항:\n1. 웹 검색을 통해 해당 종목의 '최신 뉴스'와 '최신 공시'를 우선적으로 찾아줘.\n"
                      "2. 기존 자료는 참고만 하고, 최신 실시간 정보를 기반으로 기업의 핵심 이슈를 정리해줘.\n"
                      "3. 가격, 매매 전략, 평단가 등은 배제하고 오직 기업의 강점과 약점, 사업 가치와 최신 뉴스 흐름 위주로 보고해줘.")
    st.code(persona_prompt, language="text")
    st.caption("💡 위 데이터를 [복사]한 뒤, [🚀 제미나이 가기]를 눌러 붙여넣으세요!")

