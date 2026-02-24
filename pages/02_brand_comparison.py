import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="브랜드별 비교", page_icon="📊", layout="wide")

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
    
    def calc_unit_price(row):
        e, p = row['event'], row['price']
        if e == '1+1': return p // 2
        if e == '2+1': return p // 3
        if e == '3+1': return p // 4
        return p
    
    df['unit_price'] = df.apply(calc_unit_price, axis=1)
    return df

df = get_data()

st.title("📊 브랜드별 행사 비교")

if not df.empty:
    brand_colors = {
        "CU": "#9BC621",
        "7Eleven": "#008135",
        "emart24": "#FFB71B",
        "GS25": "#0095D3"
    }

    # 필터 영역 (01_overall_summary와 동일한 스타일)
    with st.expander("🔍 상세 필터 및 검색", expanded=True):
        # 첫 번째 줄: 검색 및 정렬
        r1_c1, r1_c2 = st.columns([3, 1])
        with r1_c1:
            search_query = st.text_input("📝 검색", "", placeholder="상품명 입력")
        with r1_c2:
            sort_option = st.selectbox("💰 정렬", ["기본", "가격 낮은 순", "가격 높은 순"])

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

    if sort_option == "가격 낮은 순":
        filtered_df = filtered_df.sort_values(by='unit_price', ascending=True)
    elif sort_option == "가격 높은 순":
        filtered_df = filtered_df.sort_values(by='unit_price', ascending=False)

    st.subheader("📊 브랜드별 행사 통계")
    
    if not filtered_df.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.write("✨ 브랜드별 총 행사 상품 수")
            brand_counts = filtered_df['brand'].value_counts().reset_index()
            brand_counts.columns = ['브랜드', '상품 개수']
            fig1 = px.bar(
                brand_counts,
                x='브랜드',
                y='상품 개수',
                text='상품 개수',
                color='브랜드',
                color_discrete_map=brand_colors
            )
            fig1.update_layout(xaxis_tickangle=0, showlegend=False, height=400)
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.write("📝 상세 통계 표 (행사 종류별)")
            event_brand_counts = filtered_df.groupby(['brand', 'event']).size().unstack(fill_value=0)
            st.dataframe(event_brand_counts, use_container_width=True)

        st.subheader("💰 브랜드별 평균 개당 가격 (unit_price)")
        avg_price = filtered_df.groupby('brand')['unit_price'].mean().reset_index()
        avg_price.columns = ['브랜드', '평균가격']
        fig2 = px.line(avg_price, x='브랜드', y='평균가격', markers=True)
        fig2.update_traces(line=dict(color="#FF6B6B", width=3), marker=dict(size=10))
        fig2.update_layout(xaxis_tickangle=0, showlegend=False, height=400, hovermode="x unified")
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("📈 브랜드별 핵심 요약")
        # 실제 필터링된 브랜드들만 출력
        display_brands = [b for b in selected_brands if b in filtered_df['brand'].unique()]
        if display_brands:
            m_cols = st.columns(len(display_brands))
            brand_stats = filtered_df.groupby('brand').agg({
                'name': 'count',
                'unit_price': 'mean'
            }).rename(columns={'name': '상품 수', 'unit_price': '평균 단가'})
            
            for i, brand in enumerate(display_brands):
                if brand in brand_stats.index:
                    row = brand_stats.loc[brand]
                    with m_cols[i]:
                        st.metric(brand, f"{int(row['상품 수'])}개", f"평균 {int(row['평균 단가']):,}원")
    else:
        st.warning("필터링된 결과가 없습니다.")
else:
    st.error("데이터를 불러올 수 없습니다.")
