import streamlit as st
import pandas as pd
import urllib.parse
import time

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="지비서 작전판", page_icon="📈")

# 2. 암호 관리
if "password_correct" not in st.session_state: 
    st.session_state["password_correct"] = False

def check_password():
    if st.session_state["password_correct"]: 
        return True
    pwd = st.text_input("🔑 대장님, 암호를 입력하십시오.", type="password")
    if pwd == "rkwhr42": 
        st.session_state["password_correct"] = True
        st.rerun()
    elif pwd: 
        st.error("암호가 틀렸습니다.")
    return False

if not check_password(): 
    st.stop()

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

# 4. 전광판 로직 (수식 관계없이 텍스트로 강제 인식)
ticker_items = []
for _, row in display_df.iterrows():
    # 모든 데이터를 텍스트로 합쳐서 '지정가'와 '근접'이라는 단어가 포함되었는지 확인
    row_str = " ".join([str(val) for val in row.values]).replace(" ", "")
    if '지정가' in row_str and '근접' in row_str:
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
            <a href="https://search.naver.com/search.naver?query={stock_name}+주가" target="_blank" style="padding:15px; border:2px solid #555; border-radius:8px; text-decoration:none; color:black;">📈 네이버증권</a>
            <a href="https://dart.fss.or.kr/dsab001/main.do?textCrpNm={stock_name}" target="_blank" style="padding:15px; border:2px solid #555; border-radius:8px; text-decoration:none; color:black;">📢 DART공시</a>
            <a href="https://gemini.google.com/app" target="_blank" style="padding:15px; border:2px solid #555; border-radius:8px; text-decoration:none; color:black;">🚀 제미나이 가기</a>
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
