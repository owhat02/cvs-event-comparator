import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. 파일 분리 로직 임포트 (폴더 구조 반영)
from filter.render_filters import render_filters
from list.show_all_summary import show_all_summary
from brand.show_brand_comparison import show_brand_comparison
from good_price.show_best_value import show_best_value

st.set_page_config(page_title="이달의 편의점 행사", layout="wide")

# CSS 로드 함수
def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")

# 데이터 로드 함수 (이게 render_filters보다 먼저 정의되어야 함)
@st.cache_data(ttl=3600)
def get_combined_data():
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not csv_files: return pd.DataFrame()
    list_df = [pd.read_csv(f) for f in csv_files]
    df = pd.concat(list_df, ignore_index=True)
    df['event'] = df['event'].str.replace(' ', '', regex=False)
    df['price'] = df['price'].astype(str).str.replace(r'[^\d.]', '', regex=True)
    df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0).astype(int)

    def calc_info(row):
        e, p = row['event'], row['price']
        if e == '1+1': return p // 2, "50%"
        if e == '2+1': return p // 3, "33%"
        if e == '3+1': return p // 4, "25%"
        return p, "0%"

    df[['unit_price', 'discount_rate']] = df.apply(lambda x: pd.Series(calc_info(x)), axis=1)
    return df.drop_duplicates(subset=['name', 'event', 'brand'])

# --- 중요: 데이터 정의가 호출보다 먼저 와야 함 ---
df = get_combined_data()

# 사이드바 메뉴 정의
st.sidebar.title("📌 메뉴")
menu = st.sidebar.radio(
    "비교 데이터 방법 선택",
    ["전체 요약", "브랜드별 비교", "가성비 비교"]
)

st.title(f"🏪 {datetime.now().strftime('%Y년 %m월')} 편의점 행사 정보")

# 이제 df가 정의되었으므로 필터 함수 호출 가능
selected_brands, selected_events, search_query, sort_option = render_filters(df)

# 필터링 로직
filtered_df = df[(df['brand'].isin(selected_brands)) &
                 (df['event'].isin(selected_events)) &
                 (df['name'].str.contains(search_query, case=False))]

if sort_option == "가격 낮은 순":
    filtered_df = filtered_df.sort_values(by='unit_price', ascending=True)
elif sort_option == "가격 높은 순":
    filtered_df = filtered_df.sort_values(by='unit_price', ascending=False)

# 메뉴별 콘텐츠 출력
if menu == "전체 요약":
    show_all_summary(filtered_df)
elif menu == "브랜드별 비교":
    show_brand_comparison(filtered_df)
elif menu == "가성비 비교":
    show_best_value(filtered_df, df, search_query, selected_brands, selected_events,  sort_option)