import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse

# 1. 암호 확인 및 설정
def check_password():
    def password_entered():
        if st.session_state["password"] == "rkwhr42":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.text_input("🔑 대장님, 암호를 입력하십시오.", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state.get("password_correct", False)

if not check_password():
    st.stop()

st.set_page_config(layout="wide", page_title="지비서 추노 작전판 v22", page_icon="📈")

# 2. 데이터 로드
sheet_url = "https://docs.google.com/spreadsheets/d/10XzkMRByoPPjJ9ycm7i6IaaOpKEpBHaK8g6RQpE65sk/edit?usp=sharing"
csv_url = sheet_url.split('/edit')[0] + '/export?format=csv'
df = pd.read_csv(csv_url)
df.columns = df.columns.str.strip()

# 숫자 컬럼 정제
for col in ['현재가', '매집평단', '전일종가']:
    df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce')
df['변동율'] = (df['현재가'] - df['전일종가']) / df['전일종가']

# 3. 전광판 로직 (뉴스 와 펄 전체 출력 버전)
watch_col = next((col for col in df.columns if '지정가' in col and '감시' in col), None)
ticker_items = []
if watch_col:
    # 지정가 근접 종목들을 찾아 리스트에 담습니다
    near_df = df[df[watch_col].astype(str).str.contains('지정가 근접|지정가근접', na=False)]
    for _, row in near_df.iterrows():
        # 뉴스 와 펄이 있을 경우 가져오고, 없으면 빈칸으로 처리
        ns = str(row['뉴스 와 펄']) if '뉴스 와 펄' in row and pd.notnull(row['뉴스 와 펄']) else ""
        ticker_items.append(f"🔥 [{row['테마']}] {row['종목명']} - {ns}")

# 전광판에 들어갈 최종 텍스트
ticker_text = " 🚀 ".join(ticker_items) if ticker_items else "✨ 현재 감시 중인 '지정가 근접' 종목이 없습니다. 편안하게 관망하십시오. ☕"

# 전광판 화면 출력
st.markdown(f"""
    <div style="background-color: #1a1a1a; padding: 14px; border-radius: 5px; margin-bottom: 25px; border-left: 5px solid #ff4b4b;">
        <marquee behavior="scroll" direction="left" scrollamount="5" style="color: #ffffff; font-size: 17px; font-weight: bold;">
            {ticker_text}
        </marquee>
    </div>
""", unsafe_allow_html=True)

# 4. 검색/테마 동기화 로직
def clear_search(): st.session_state.search_bar = ""
def clear_theme(): st.session_state.theme_select = None

col1, col2 = st.columns([1, 1])
with col1:
    selected_theme = st.selectbox("📂 테마 선택", df['테마'].unique(), key="theme_select", on_change=clear_search)
with col2:
    search_query = st.text_input("🔍 종목명 직접 검색", key="search_bar", on_change=clear_theme)

filtered_df = df[df['종목명'].str.contains(search_query, na=False)] if search_query else df[df['테마'] == selected_theme]

# 5. 일람표 및 상세분석
left, right = st.columns([9, 7])

with left:
    high_col = next((c for c in df.columns if '예상 고점' in c), None)
    show_cols = ['종목명', '현재가', '변동율', '매집평단', '현재단계'] + ([high_col] if high_col else [])
    
    styled_df = filtered_df[show_cols].style.format({'변동율': '{:.2%}', '현재가': '{:,.0f}원', '매집평단': '{:,.0f}원'}).map(
        lambda x: 'color: red; font-weight: bold;' if x > 0 else 'color: blue; font-weight: bold;', subset=['변동율']
    )
    selected_rows = st.dataframe(styled_df, use_container_width=True, height=520, on_select="rerun", selection_mode="single-row")

with right:
    if selected_rows and 'selection' in selected_rows and selected_rows['selection']['rows']:
        idx = selected_rows['selection']['rows'][0]
        row = filtered_df.iloc[idx]
        st.markdown(f"### 🔍 **{row['종목명']}** 분석 리포트")
        
        if '뉴스 와 펄' in row:
            st.markdown(f"<div style='background-color: #f8f9fa; padding: 15px; border-left: 5px solid #228be6; margin-bottom: 20px;'><h5>📌 대장님의 뉴스 와 펄</h5>{row['뉴스 와 펄']}</div>", unsafe_allow_html=True)
        
        # 뉴스 확인 버튼 (뉴스가 안 뜰 때를 대비해 버튼으로 보완)
        st.markdown(f"📰 **{row['종목명']} 실시간 확인**")
        c1, c2 = st.columns(2)
        with c1: st.link_button("📈 네이버 증권", f"https://search.naver.com/search.naver?query={urllib.parse.quote(row['종목명'] + ' 주가')}")
        with c2: st.link_button("📢 DART 공시", f"https://dart.fss.or.kr/dsab001/main.do?textCrpNm={urllib.parse.quote(row['종목명'])}")
    else:
        st.write("표에서 종목을 선택하시면 상세 정보가 표시됩니다.")
