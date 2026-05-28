import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib.parse
import streamlit as st
import streamlit as st
import pandas as pd
# ... (기존 import들)

# 비밀번호 설정 (대장님만 아는 번호로 바꾸세요)
def check_password():
    def password_entered():
        if st.session_state["password"] == "7669": # 👈 이 1234를 원하는 비밀번호로 변경!
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("🔑 대장님, 암호를 입력하십시오.", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("🔑 암호가 틀렸습니다. 다시 입력하세요.", type="password", on_change=password_entered, key="password")
        return False
    else:
        return True

if not check_password():
    st.stop() # 비밀번호가 틀리면 여기서 멈춤

# --- 여기서부터 아래에 원래 코드 본문 붙여넣기 ---
# ... (다른 import 문들)

# 💡 화면 깨짐 방지: 모바일 전용 CSS 설정
st.markdown("""
    <style>
    /* 모바일에서 사이드바와 컬럼이 무조건 한 줄로 정렬되게 함 */
    @media (max-width: 800px) {
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }
        /* 뉴스 글자 크기 최적화 */
        .stMarkdown, .stText {
            font-size: 13px !important;
        }
        /* 데이터프레임이 화면 밖으로 나가는 것 방지 */
        .stDataFrame {
            width: 100% !important;
        }
    }
    </style>
""", unsafe_allow_html=True)
# 1. 앱 기본 설정
st.set_page_config(
    layout="wide", 
    page_title="지비서 추노 작전판 v16",
    page_icon="📈"
)

# 기존 코드의 st.set_page_config 아래에 이 내용을 붙여넣으세요.
st.markdown("""
    <style>
    /* 모바일 환경 최적화 */
    @media (max-width: 768px) {
        /* 전광판 글자 크기 조정 */
        marquee { font-size: 14px !important; }
        
        /* 뉴스 제목 및 폰트 크기 강제 축소 */
        div, p, span, a { font-size: 13px !important; }
        
        /* 헤더 크기 조정 */
        h1 { font-size: 20px !important; }
        h2, h3 { font-size: 16px !important; }
        
        /* 뉴스 속보 리스트 간격 조절 */
        .stMarkdown { margin-bottom: 5px !important; }
        
        /* 새로고침 버튼 크기 조정 */
        div.stButton > button { height: 35px !important; font-size: 13px !important; }
    }
    </style>
""", unsafe_allow_html=True)
st.title("⚔️ 추노 작전판  ⚔️")
st.markdown("---")

# 구글 시트 주소
sheet_url = "https://docs.google.com/spreadsheets/d/10XzkMRByoPPjJ9ycm7i6IaaOpKEpBHaK8g6RQpE65sk/edit?usp=sharing"

# 💡 [절대 막히지 않는 무적 엔진] 구글 실시간 뉴스 RSS 크롤링 함수
def get_google_realtime_news(stock_name):
    try:
        encoded_name = urllib.parse.quote(f"{stock_name} 주식 뉴스")
        url = f"https://news.google.com/rss/search?q={encoded_name}&hl=ko&gl=KR&ceid=KR:ko"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'xml')
        items = soup.find_all('item')
        news_list = []
        for i in range(min(5, len(items))):
            title_text = items[i].title.text if items[i].title else "제목 없음"
            if " - " in title_text:
                title_text = title_text.rsplit(" - ", 1)[0]
            link = items[i].link.text if items[i].link else "#"
            info_text = items[i].source.text if items[i].source else "구글뉴스"
            date_text = items[i].pubDate.text if items[i].pubDate else "방금 전"
            if len(date_text) > 16:
                date_text = date_text[:16]
            news_list.append({"title": title_text, "link": link, "info": info_text, "date": date_text})
        return news_list
    except:
        return []

try:
    csv_url = sheet_url.split('/edit')[0] + '/export?format=csv'
    df = pd.read_csv(csv_url)
    
    # 데이터 정리
    df.columns = df.columns.str.strip()
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.strip()
            
    # 숫자 데이터 정제
    for col in ['현재가', '매집평단', '예상 고점', '6단계 3파 고점']:
        found = [c for c in df.columns if col in c]
        if found:
            df[found[0]] = df[found[0]].astype(str).str.replace('[^\d]', '', regex=True)
            df[found[0]] = pd.to_numeric(df[found[0]], errors='coerce')

    # 🚨 지정가 감시 실시간 전광판
    ticker_text = ""
    watch_col = [col for col in df.columns if '지정가' in col and '감시' in col]
    if watch_col and '종목명' in df.columns:
        col_name = watch_col[0]
        near_df = df[df[col_name].str.contains('지정가 근접|지정가근접', na=False)]
        near_stocks = []
        for idx, row in near_df.iterrows():
            stock_name = row['종목명']
            cur_price = row['현재가'] if '현재가' in df.columns and pd.notna(row['현재가']) else 0
            target_price = row['매집평단'] if '매집평단' in df.columns and pd.notna(row['매집평단']) else 0
            news_info = row['뉴스 와 펄'] if '뉴스 와 펄' in df.columns and pd.notna(row['뉴스 와 펄']) and str(row['뉴스 와 펄']) != 'nan' else ""
            news_tail = f" 🌟재료: {news_info}" if news_info else ""
            if cur_price > 0 and target_price > 0:
                near_stocks.append(f"🔥 [{stock_name}] 지정가 근접! (현재: {int(cur_price):,}원 / 평단: {int(target_price):,}원){news_tail}")
            else:
                near_stocks.append(f"🔥 [{stock_name}] 지정가 근접!{news_tail}")
        
        if near_stocks:
            ticker_text = " 🚀 " + " 🚀 ".join(near_stocks)
        else:
            ticker_text = "✨ 현재 감시 중인 '지정가 근접' 종목이 없습니다. 편안하게 관망하십시오. ☕"
            
    st.markdown(f"""
    <div style="background-color: #1a1a1a; padding: 14px; border-radius: 5px; margin-bottom: 25px; border-left: 5px solid #ff4b4b;">
        <marquee behavior="scroll" direction="left" scrollamount="5" style="color: #ffffff; font-size: 18px; font-weight: bold;">
            {ticker_text}
        </marquee>
    </div>
    """, unsafe_allow_html=True)

    all_themes = [t for t in df['테마'].unique() if t and t != 'nan']
    top_col1, top_col2 = st.columns([4, 1])
    with top_col1:
        selected_theme = st.selectbox("📂 보실 작전 테마를 선택하세요:", all_themes)
    with top_col2:
        st.write("") 
        st.write("") 
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()
            
    st.markdown("---")
    
    filtered_df = df[df['테마'] == selected_theme].reset_index(drop=True)
    high_col = [col for col in df.columns if '예상' in col and '고점' in col]
    if not high_col:
        high_col = [col for col in df.columns if '6단계' in col or '3파' in col]
    target_high_col = high_col[0] if high_col else None

    left_side, right_side = st.columns([9, 7])
    
    with left_side:
        st.subheader("🎯 테마 종목 일람표")
        st.caption("💡 왼쪽 사각박스에 v 표시를 하시면 우측에 실시간 뉴스가 완벽 연동됩니다.")
        show_cols = ['종목명', '현재가', '매집평단', '현재단계']
        if target_high_col:
            show_cols.append(target_high_col)
        final_cols = [c for c in show_cols if c in filtered_df.columns]
        
        def color_rows(row):
            if '현재단계' in row:
                if '매수' in str(row['현재단계']) or '진입' in str(row['현재단계']):
                    return ['background-color: #d4edda; color: #155724'] * len(row)
                elif '돌파' in str(row['현재단계']) or '급등' in str(row['현재단계']):
                    return ['background-color: #f8d7da; color: #721c24'] * len(row)
            return [''] * len(row)
            
        if final_cols:
            format_dict = {col: "{:,.0f}원" for col in ['현재가', '매집평단'] if col in final_cols}
            if target_high_col:
                format_dict[target_high_col] = "{:,.0f}원"
            styled_df = filtered_df[final_cols].style.apply(color_rows, axis=1).format(format_dict, na_rep="")
            
            selected_rows = st.dataframe(
                styled_df, use_container_width=True, height=520, 
                on_select="rerun", selection_mode="single-row"
            )
            
            clicked_idx = 0
            if selected_rows and 'rows' in selected_rows.get('selection', {}) and selected_rows['selection']['rows']:
                clicked_idx = selected_rows['selection']['rows'][0]
                stock_row = filtered_df.iloc[clicked_idx]
                selected_stock = stock_row['종목명']
            else:
                selected_stock = "선택 없음"
        else:
            st.dataframe(filtered_df, use_container_width=True, height=520)
            selected_stock = "선택 없음"

    with right_side:
        st.subheader("📋 종목 종합 모멘텀")
        if selected_stock != "선택 없음":
            st.markdown(f"### 🔍 **{selected_stock}** 분석 리포트")
            if '뉴스 와 펄' in filtered_df.columns:
                news_text = stock_row['뉴스 와 펄']
                st.markdown(f"""
                <div style="background-color: #f8f9fa; padding: 18px; border-radius: 8px; border-left: 5px solid #228be6; margin-bottom: 25px;">
                    <h5 style='margin-top:0; color:#228be6; font-weight:bold;'>📌 대장님의 뉴스 와 펄</h5>
                    <p style='font-size: 15px; line-height: 1.6; color: #343a40; margin-bottom:0;'>{news_text}</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"📰 **{selected_stock} 관련 실시간 뉴스 속보** ()")
            with st.spinner("구글 실시간 속보망 동기화 중..."):
                live_news = get_google_realtime_news(selected_stock)
            if live_news:
                for news in live_news:
                    st.markdown(f"""
                    <div style="padding: 12px 5px; border-bottom: 1px solid #eee; font-size: 14px;">
                        <a href="{news['link']}" target="_blank" style="color: #1a0dab; text-decoration: none; font-weight: bold; line-height:1.4;">
                            • {news['title']}
                        </a><br>
                        <span style="color: #666; font-size: 12px;">{news['info']} | {news['date']}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("✨ 현재 해당 종목의 검색된 신규 구글 속보가 없습니다.")
        else:
            st.write("왼쪽 표의 사각박스에 v 표시를 하시면 상세 리포트와 뉴스가 출력됩니다.")

except Exception as e:
    st.error(f"❌ 시스템 오류 발생: {e}")