import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="가성비 비교", page_icon="💎", layout="wide")

# CSS 로드
if os.path.exists("style.css"):
    with open("style.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_data():
    file_path = os.path.join('data', 'categorized_data.csv')
    if not os.path.exists(file_path):
        return pd.DataFrame()
    
    df = pd.read_csv(file_path)
    df['event'] = df['event'].str.replace(' ', '', regex=False)
    df['price'] = pd.to_numeric(df['price'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0).astype(int)
    
    def calc_info(row):
        e, p = row['event'], row['price']
        if e == '1+1': return p // 2, 50.0, "50%"
        if e == '2+1': return p // 3, 33.3, "33%"
        if e == '3+1': return p // 4, 25.0, "25%"
        return p, 0.0, "0%"
    
    df[['unit_price', 'discount_num', 'discount_rate']] = df.apply(lambda x: pd.Series(calc_info(x)), axis=1)
    return df

df = get_data()

st.title("💎 최고의 가성비 아이템 (할인율 TOP 50)")

if not df.empty:
    # 필터 영역 (01_overall_summary와 동일한 스타일)
    with st.expander("🔍 상세 필터 및 검색", expanded=True):
        # 첫 번째 줄: 검색 및 정렬
        r1_c1, r1_c2 = st.columns([3, 1])
        with r1_c1:
            search_query = st.text_input("📝 검색", "", placeholder="상품명 입력")
        with r1_c2:
            sort_option = st.selectbox("💰 정렬", ["가성비 순 (할인율)", "가격 낮은 순", "가격 높은 순"])

        # 두 번째 줄: 브랜드, 행사, 분류
        r2_c1, r2_c2, r2_c3 = st.columns([1, 1, 1])
        with r2_c1:
            brand_list = sorted(df['brand'].unique().tolist())
            selected_brands = st.multiselect("🏪 브랜드", brand_list, default=brand_list)
        with r2_c2:
            event_list = sorted([e for e in df['event'].unique().tolist() if e not in ['SALE', '세일']])
            selected_events = st.multiselect("🎁 행사", event_list, default=event_list)
        with r2_c3:
            cat_list = sorted(df['category'].unique().tolist())
            selected_cats = st.multiselect("📂 분류", cat_list, default=cat_list)

    # 데이터 필터링
    filtered_df = df[
        (df['brand'].isin(selected_brands)) & 
        (df['event'].isin(selected_events)) &
        (df['category'].isin(selected_cats)) &
        (df['name'].str.contains(search_query, case=False))
    ]

    # 정렬 로직
    if sort_option == "가격 낮은 순":
        best_value_df = filtered_df.sort_values(by='unit_price', ascending=True).head(50)
    elif sort_option == "가격 높은 순":
        best_value_df = filtered_df.sort_values(by='unit_price', ascending=False).head(50)
    else: # 가성비 순
        best_value_df = filtered_df.sort_values(by=['discount_num', 'unit_price'], ascending=[False, True]).head(50)

    if not best_value_df.empty:
        # 페이지네이션
        items_per_page = 9
        total_pages = max((len(best_value_df) - 1) // items_per_page + 1, 1)
        page = st.number_input("페이지", min_value=1, max_value=total_pages, step=1)
        
        start_idx = (page - 1) * items_per_page
        page_items = best_value_df.iloc[start_idx: start_idx + items_per_page]

        st.divider()

        # 리스트 출력
        for _, row in page_items.iterrows():
            with st.container():
                c1, c2, c3 = st.columns([1.5, 4, 2])
                with c1:
                    img_url = row['img_url'] if pd.notna(row['img_url']) else ""
                    st.image(img_url, width=120)
                with c2:
                    st.markdown(f"### {row['name']}")
                    st.markdown(f"📍 **{row['brand']}** | {row['category']} | <span class='event-tag'>{row['event']}</span>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"<h2 style='color:#ff6b6b; margin-bottom:0;'>{row['discount_rate']} 할인</h2>", unsafe_allow_html=True)
                    st.markdown(f"#### 개당 {row['unit_price']:,}원")
                    st.caption(f"정가 {row['price']:,}원")
                st.divider()

        st.markdown(f"<div class='page-info-box'>{page} / {total_pages} 페이지</div>", unsafe_allow_html=True)
    else:
        st.warning("결과가 없습니다.")
else:
    st.error("데이터가 없습니다.")
