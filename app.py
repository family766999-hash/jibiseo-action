import streamlit as st
import pandas as pd
import urllib.parse

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="지비서 작전판", page_icon="📈")

# 2. 암호 관리
if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
def check_password():
    if st.session_state["password_correct"]: return True
    pwd = st.text_input("🔑 대장님, 암호를 입력하십시오.", type="password")
    if pwd == "rkwhr42": st.session_state["password_correct"] = True; st.rerun()
    elif pwd: st.error("암호가 틀렸습니다.")
    return False
if not check_password(): st.stop()

# 3. 데이터 로드
@st.cache_data(ttl=60)
def load_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/10XzkMRByoPPjJ9ycm7i6IaaOpKEpBHaK8g6RQpE65sk/export?format=csv"
    df = pd.read_csv(sheet_url)
    df.columns = df.columns.str.strip()
    return df.fillna("")

df = load_data()

# 4. 전광판 로직
ticker_items = []
for _, row in df.iterrows():
    # 모든 값을 문자열로 안전하게 변환하여 합치기
    row_str = " ".join([str(val) for val in row.values])
    if '지정가근접' in row_str:
        news = str(row.get('뉴스 와 펄', ''))
        news_display = f" | {news}" if news else ""
        item = f"🔥 [{row.get('테마', '')}] {row.get('종목명', '')}{news_display}"
        if item not in ticker_items: ticker_items.append(item)

ticker_text = " 🚀 ".join(ticker_items) if ticker_items else "✨ 현재 감시 중인 '지정가 근접' 종목이 없습니다. ☕"
st.markdown(f"""
    <div style="background-color: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #ff4b4b;">
        <marquee behavior="scroll" direction="left" scrollamount="5" style="color: #ffffff; font-size: 18px; font-weight: bold;">{ticker_text}</marquee>
    </div>
""", unsafe_allow_html=True)

# 5. 검색 및 일람표 (조건부 서식 적용 버전)

def clear_search(): st.session_state["search_bar"] = ""

col1, col2 = st.columns([1, 1])
themes = df['테마'].unique() if not df.empty and '테마' in df.columns else []
with col1: selected_theme = st.selectbox("📂 테마 선택", themes, on_change=clear_search)
with col2: search_query = st.text_input("🔍 종목명 직접 검색", key="search_bar")

if search_query:
    filtered_df = df[df['종목명'].astype(str).str.contains(search_query, na=False)]
else:
    filtered_df = df[df['테마'] == selected_theme]

# 이모티콘 처리
display_df = filtered_df.copy()
if not display_df.empty:
    display_df['종목명'] = display_df.apply(lambda x: "🔥 " + str(x['종목명']) if '지정가근접' in str(x.values) else str(x['종목명']), axis=1)

st.subheader("📋 종목 일람표")
cols = ['종목명', '현재가', '변동율', '매집평단', '평단비율', '현재단계', '예상고점']
valid_cols = [c for c in cols if c in display_df.columns]

# --- [조건부 서식 함수] ---
def color_text(val):
    try:
        # 문자로 된 숫자에서 기호를 제거하고 float 변환
        num = float(str(val).replace('%', '').replace(',', '').strip())
        color = 'red' if num > 0 else 'blue' if num < 0 else 'black'
    except:
        color = 'black'
    return f'color: {color}'

# 데이터프레임 스타일링 (변동율, 평단비율 컬럼에만 적용)
styled_df = display_df[valid_cols].style.map(color_text, subset=['변동율', '평단비율'])

event = st.dataframe(
    styled_df, 
    use_container_width=True, 
    selection_mode="single-row", 
    on_select="rerun"
)
# 6. 상세 분석 리포트 & 지비서 호출 (디자인 유지 + 태블릿 링크 안정화)
if len(event.selection.rows) > 0:
    idx = event.selection.rows[0]
    row = filtered_df.iloc[idx]
    
    st.markdown(f"---")
    st.markdown(f"### 🔍 **{row['종목명']}** 상세 분석")
    if '뉴스 와 펄' in row and pd.notnull(row['뉴스 와 펄']): 
        st.info(f"📌 **기존 참고 자료(뉴스 와 펄)**: {row['뉴스 와 펄']}")
    
    stock_name = urllib.parse.quote(str(row['종목명']))
    
    # 디자인 통일: 배경색 없고 테두리만 있는 깔끔한 스타일 유지
    st.markdown("""
        <style>
        .nav-container { display: flex; gap: 10px; margin-bottom: 20px; }
        .nav-btn { 
            flex: 1; 
            padding: 15px; 
            text-align: center; 
            border-radius: 8px; 
            font-weight: bold; 
            text-decoration: none; 
            border: 2px solid #555; 
            color: #333; 
            background-color: transparent; 
        }
        </style>
    """, unsafe_allow_html=True)

    # [수정] target="_blank"와 rel="noopener noreferrer" 추가
    # 태블릿에서 이 속성이 있어야 브라우저가 '새 탭 열기' 명령을 올바르게 수행합니다.
    st.markdown(f"""
        <div class="nav-container">
            <a href="https://search.naver.com/search.naver?query={stock_name}+주가" target="_blank" rel="noopener noreferrer" class="nav-btn">📈 네이버증권</a>
            <a href="https://dart.fss.or.kr/dsab001/main.do?textCrpNm={stock_name}" target="_blank" rel="noopener noreferrer" class="nav-btn">📢 DART공시</a>
            <a href="https://gemini.google.com/app" target="_blank" rel="noopener noreferrer" class="nav-btn">🚀 지비서호출</a>
        </div>
    """, unsafe_allow_html=True)

    # 2. 지비서 분석 요청서
    st.markdown(f"---")
    st.subheader("🤖 지비서(AI) 분석 요청서")
    
    persona_prompt = (
        f"너는 나만의 주식 투자 전문 비서야 나는 대장이야.\n\n"
        f"분석 대상: {row['종목명']}\n"
        f"참고용 기존 자료: {row.get('뉴스 와 펄', '없음')}\n\n"
        f"지시사항:\n"
        f"1. 웹 검색을 통해 해당 종목의 '최신 뉴스'와 '최신 공시'를 우선적으로 찾아줘.\n"
        f"2. 기존 자료는 참고만 하고, 최신 실시간 정보를 기반으로 기업의 핵심 이슈를 정리해줘.\n"
        f"3. 가격, 매매 전략, 평단가 등은 배제하고 오직 기업의 강점과 약점 사업 가치와 최신 뉴스 흐름 위주로만 보고해줘."
    )
    
    st.code(persona_prompt, language="text")
    st.caption("💡 태블릿에서는 버튼을 누르면 새 탭으로 열립니다. 만약 닫히면 버튼을 **길게 꾸욱 눌러 [새 탭에서 열기]** 하세요!")

else:
    st.write("👆 위 표에서 종목을 선택하시면 상세 리포트가 나타납니다.")
