import streamlit as st
import pandas as pd
import urllib.parse

# v23.0: 태블릿 레이아웃 최적화 및 강제 새로고침 방지
st.set_page_config(layout="wide", page_title="지비서 추노 작전판 v23", page_icon="📈")

# 1. 암호 확인
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

# 2. 데이터 로드
sheet_url = "https://docs.google.com/spreadsheets/d/10XzkMRByoPPjJ9ycm7i6IaaOpKEpBHaK8g6RQpE65sk/edit?usp=sharing"
csv_url = sheet_url.split('/edit')[0] + '/export?format=csv'
df = pd.read_csv(csv_url)
df.columns = df.columns.str.strip()

# 숫자 처리
for col in ['현재가', '매집평단', '전일종가']:
    df[col] = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce')
df['변동율'] = (df['현재가'] - df['전일종가']) / df['전일종가']

# 3. 전광판 (스크롤바)
watch_col = next((col for col in df.columns if '지정가' in col and '감시' in col), None)
ticker_items = []
if watch_col:
    near_df = df[df[watch_col].astype(str).str.contains('지정가 근접|지정가근접', na=False)]
    for _, row in near_df.iterrows():
        ns = str(row['뉴스 와 펄']) if '뉴스 와 펄' in row and pd.notnull(row['뉴스 와 펄']) else ""
        ticker_items.append(f"🔥 [{row['테마']}] {row['종목명']} - {ns}")
ticker_text = " 🚀 ".join(ticker_items) if ticker_items else "✨ 감시 중인 종목이 없습니다."

st.markdown(f"""<div style="background-color: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #ff4b4b;">
    <marquee behavior="scroll" direction="left" scrollamount="5" style="color: #ffffff; font-size: 18px; font-weight: bold;">{ticker_text}</marquee></div>""", unsafe_allow_html=True)

# 4. 검색 및 테마
col1, col2 = st.columns([1, 1])
with col1:
    selected_theme = st.selectbox("📂 테마 선택", df['테마'].unique(), key="theme_select")
with col2:
    search_query = st.text_input("🔍 종목명 검색", key="search_bar")

filtered_df = df[df['종목명'].str.contains(search_query, na=False)] if search_query else df[df['테마'] == selected_theme]

# 5. 종목 일람표 (태블릿 대응)
st.subheader("📋 종목 일람표")
# 선택된 행의 인덱스를 세션에 저장하여 리포트와 연결
event = st.dataframe(filtered_df[['종목명', '현재가', '변동율', '매집평단', '현재단계']], 
                     use_container_width=True, height=350, on_select="rerun", selection_mode="single-row")

st.divider()

# 6. 상세 분석 리포트 (표 아래에 항상 위치)
if event.selection['rows']:
    idx = event.selection['rows'][0]
    row = filtered_df.iloc[idx]
    st.markdown(f"### 🔍 **{row['종목명']}** 상세 리포트")
    st.info(f"📌 **뉴스 와 펄**: {row.get('뉴스 와 펄', '내용 없음')}")
    
    c1, c2 = st.columns(2)
    with c1: st.link_button("📈 네이버 증권", f"https://search.naver.com/search.naver?query={urllib.parse.quote(row['종목명'] + ' 주가')}")
    with c2: st.link_button("📢 DART 공시", f"https://dart.fss.or.kr/dsab001/main.do?textCrpNm={urllib.parse.quote(row['종목명'])}")
else:
    st.write("👆 **표에서 종목을 선택하시면 상세 정보가 아래에 표시됩니다.**")
