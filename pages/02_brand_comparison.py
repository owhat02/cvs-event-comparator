import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import numpy as np

# 페이지 설정
st.set_page_config(page_title="브랜드별 비교 분석", page_icon="📊", layout="wide")

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
    df['brand'] = df['brand'].astype(str).str.strip()
    df['category'] = df['category'].fillna('기타')
    
    # 1. '세일' 또는 'SALE' 관련 데이터 제거
    if 'event' in df.columns:
        df['event'] = df['event'].astype(str).str.replace(r'\s+', '', regex=True)
        df = df[~df['event'].str.contains(r'(?i)sale|세일', regex=True, na=False)]
        
        # 2. 덤 증정 이벤트 정규화
        df.loc[df['event'].str.contains(r'1\+1', regex=True, na=False), 'event'] = '1+1'
        df.loc[df['event'].str.contains(r'2\+1', regex=True, na=False), 'event'] = '2+1'
        df.loc[df['event'].str.contains(r'3\+1', regex=True, na=False), 'event'] = '3+1'
        
        # 3. 덤 증정 상품만 유지
        df = df[df['event'].isin(['1+1', '2+1', '3+1'])]

    # 가격 정규화
    df['price'] = pd.to_numeric(df['price'].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0).astype(int)
    
    # 실질 구매가 및 할인율 계산
    def calc_unit_price(row):
        e, p = row['event'], row['price']
        if e == '1+1': return p // 2
        if e == '2+1': return (p * 2) // 3
        if e == '3+1': return (p * 3) // 4
        return p
    
    df['unit_price'] = df.apply(calc_unit_price, axis=1)
    df['discount_rate'] = 0.0
    valid_mask = df['price'] > 0
    df.loc[valid_mask, 'discount_rate'] = ((df.loc[valid_mask, 'price'] - df.loc[valid_mask, 'unit_price']) / df.loc[valid_mask, 'price'] * 100)
    
    return df

df = get_data()

brand_colors = {
    "CU": "#9BC621",
    "7Eleven": "#008135",
    "emart24": "#FFB71B",
    "GS25": "#0095D3"
}

st.title("📊 브랜드별 행사 전략 심층 비교")
st.markdown("단순 할인을 제외한 **순수 덤 증정(1+1, 2+1 등)** 상품들의 전략을 분석합니다.")

if not df.empty:
    # --- 상단 상세 필터 ---
    with st.expander("🔍 상세 필터 및 검색", expanded=True):
        r1_c1, r1_c2 = st.columns([3, 1])
        with r1_c1:
            search_query = st.text_input("📝 상품명 검색", "", placeholder="예: 초코, 제로, 도시락")
        with r1_c2:
            sort_option = st.selectbox("💰 정렬 기준", ["기본", "상품 많은 순", "가격 낮은 순", "할인율 높은 순"])

        r2_c1, r2_c2, r2_c3 = st.columns([1, 1, 1])
        with r2_c1:
            brand_list = sorted(df['brand'].unique().tolist())
            selected_brands = st.multiselect("🏪 브랜드", brand_list, default=brand_list)
        with r2_c2:
            event_list = sorted(df['event'].unique().tolist())
            selected_events = st.multiselect("🎁 행사 유형", event_list, default=event_list)
        with r2_c3:
            cat_list = sorted(df['category'].unique().tolist())
            selected_cats = st.multiselect("📂 카테고리 분류", cat_list, default=cat_list)

    # --- 데이터 필터링 ---
    f_df = df[
        (df['brand'].isin(selected_brands)) & 
        (df['event'].isin(selected_events)) &
        (df['category'].isin(selected_cats)) &
        (df['name'].str.contains(search_query, case=False, na=False))
    ]

    # --- 정렬 로직 ---
    if sort_option == "상품 많은 순":
        brand_order = f_df['brand'].value_counts().index.tolist()
    elif sort_option == "가격 낮은 순":
        brand_order = f_df.groupby('brand')['unit_price'].mean().sort_values().index.tolist()
    elif sort_option == "할인율 높은 순":
        brand_order = f_df.groupby('brand')['discount_rate'].mean().sort_values(ascending=False).index.tolist()
    else:
        brand_order = sorted(selected_brands)

    if f_df.empty:
        st.warning("선택한 조건에 맞는 상품이 없습니다. 필터를 조정해 주세요.")
    else:
        # --- 핵심 지표 요약 ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("행사 상품 수", f"{len(f_df):,}개")
        m2.metric("평균 할인 효과", f"{f_df['discount_rate'].mean():.1f}%")
        m3.metric("평균 실질구매가", f"{int(f_df['unit_price'].mean()):,}원")
        m4.metric("최다 행사 품목", f"{f_df['category'].mode()[0]}")

        # --- 인터랙티브 탭 ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🧬 브랜드 DNA", "🍱 카테고리/비중 분석", "💸 가격 전략", "🔥 트렌드 키워드", "📈 요약 통계"])

        # Tab 1: 브랜드 DNA
        with tab1:
            st.subheader("🧬 브랜드별 증정 전략 프로필 (Brand DNA)")
            stats = []
            for brand in selected_brands:
                b_df = f_df[f_df['brand'] == brand]
                if b_df.empty: continue
                variety = len(b_df)
                depth = b_df['discount_rate'].mean()
                meal_focus = len(b_df[b_df['category'] == '식사류']) / len(b_df) * 100
                snack_focus = len(b_df[b_df['category'] == '간식류']) / len(b_df) * 100
                value_focus = len(b_df[b_df['unit_price'] < 3000]) / len(b_df) * 100
                stats.append({'brand': brand, '다양성': variety, '할인강도': depth, '식사특화': meal_focus, '간식특화': snack_focus, '가성비': value_focus})
            radar_df = pd.DataFrame(stats)
            if not radar_df.empty:
                for col in ['다양성', '할인강도', '식사특화', '간식특화', '가성비']:
                    if radar_df[col].max() > 0:
                        radar_df[col] = (radar_df[col] / radar_df[col].max()) * 100
                fig_radar = go.Figure()
                categories = ['다양성', '할인강도', '식사특화', '간식특화', '가성비']
                for i, row in radar_df.iterrows():
                    fig_radar.add_trace(go.Scatterpolar(r=[row[c] for c in categories], theta=categories, fill='toself', name=row['brand'], line_color=brand_colors.get(row['brand'], None)))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=500)
                st.plotly_chart(fig_radar, use_container_width=True)

        # Tab 2: 카테고리 및 행사 비중 분석
        with tab2:
            st.subheader("브랜드별 행사 유형 비중 (1+1 vs 2+1)")
            # 비중 데이터 계산 (Normalization)
            event_pct = f_df.groupby(['brand', 'event']).size().reset_index(name='count')
            brand_totals = event_pct.groupby('brand')['count'].transform('sum')
            event_pct['percentage'] = (event_pct['count'] / brand_totals) * 100
            
            fig_pct = px.bar(event_pct, x='brand', y='percentage', color='event',
                            text=event_pct['percentage'].apply(lambda x: f'{x:.1f}%'),
                            category_orders={"brand": brand_order},
                            color_discrete_sequence=px.colors.qualitative.Pastel,
                            labels={'percentage': '비중 (%)', 'brand': '브랜드', 'event': '행사유형'})
            fig_pct.update_layout(yaxis_title="비중 (%)", barmode='stack', height=450)
            st.plotly_chart(fig_pct, use_container_width=True)
            st.info("💡 각 브랜드가 어떤 증정 방식에 더 집중하고 있는지 한눈에 비교할 수 있습니다.")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("카테고리별 비중 (Treemap)")
                fig_tree = px.treemap(f_df, path=['brand', 'category'], color='brand', color_discrete_map=brand_colors)
                st.plotly_chart(fig_tree, use_container_width=True)
            with col2:
                st.subheader("브랜드 x 카테고리 집중도 (Heatmap)")
                heat_data = f_df.groupby(['brand', 'category']).size().unstack(fill_value=0)
                fig_heat = px.imshow(heat_data, text_auto=True, color_continuous_scale='GnBu')
                st.plotly_chart(fig_heat, use_container_width=True)

        # Tab 3: 가격 전략
        with tab3:
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.subheader("브랜드별 실질 구매가 분포 (Box Plot)")
                fig_box = px.box(f_df, x='brand', y='unit_price', color='brand', color_discrete_map=brand_colors, category_orders={"brand": brand_order})
                st.plotly_chart(fig_box, use_container_width=True)
            with col_p2:
                st.subheader("가격 구간별 상품 비중")
                f_df['price_group'] = pd.cut(f_df['unit_price'], bins=[0, 1500, 3000, 5000, 10000, 100000],
                                            labels=['1.5천원 이하', '3천원 이하', '5천원 이하', '1만원 이하', '1만원 초과'])
                price_group_df = f_df.groupby(['brand', 'price_group'], observed=False).size().reset_index(name='상품 수')
                fig_price_group = px.bar(price_group_df, x='brand', y='상품 수', color='price_group', barmode='stack', color_discrete_sequence=px.colors.sequential.Teal, category_orders={"brand": brand_order})
                st.plotly_chart(fig_price_group, use_container_width=True)

        # Tab 4: 트렌드 키워드
        with tab4:
            st.subheader("🔍 트렌드 키워드 대응력")
            keywords = {'제로/슈가프리': ['제로', 'zero', '무설탕', '저당'], '단백질/헬스': ['단백질', '프로틴', 'protein', '닭가슴살'], '매운맛/마라': ['매운', '핫', 'hot', '마라', '불닭'], '과일/상큼': ['딸기', '사과', '포도', '망고', '레몬']}
            key_stats = []
            for brand in selected_brands:
                b_df = f_df[f_df['brand'] == brand]
                for key, words in keywords.items():
                    count = b_df['name'].str.contains('|'.join(words), case=False, na=False).sum()
                    key_stats.append({'브랜드': brand, '트렌드': key, '상품 수': count})
            fig_key = px.bar(pd.DataFrame(key_stats), x='트렌드', y='상품 수', color='브랜드', barmode='group', color_discrete_map=brand_colors, text_auto=True)
            st.plotly_chart(fig_key, use_container_width=True)

        # Tab 5: 요약 통계
        with tab5:
            st.subheader("📈 실시간 필터링 요약")
            col_s1, col_s2 = st.columns([1, 1.2])
            with col_s1:
                st.write(f"✨ 브랜드별 상품 수 (정렬: {sort_option})")
                brand_counts = f_df['brand'].value_counts().reindex(brand_order).reset_index()
                brand_counts.columns = ['브랜드', '상품 개수']
                fig_v1 = px.bar(brand_counts, x='브랜드', y='상품 개수', text='상품 개수', color='브랜드', color_discrete_map=brand_colors, category_orders={"브랜드": brand_order})
                fig_v1.update_layout(xaxis_tickangle=0, showlegend=False, height=400)
                st.plotly_chart(fig_v1, use_container_width=True)
            with col_s2:
                st.write("📝 행사 유형별 상세 통계")
                event_pivot = f_df.groupby(['brand', 'event']).size().unstack(fill_value=0).reindex(brand_order)
                st.dataframe(event_pivot, use_container_width=True)
            st.divider()
            col_s3, col_s4 = st.columns(2)
            with col_s3:
                st.subheader("💰 평균 가격 추이")
                avg_price = f_df.groupby('brand')['unit_price'].mean().reindex(brand_order).reset_index()
                fig_v2 = px.line(avg_price, x='brand', y='unit_price', markers=True, category_orders={"brand": brand_order})
                fig_v2.update_traces(line=dict(color="#FF6B6B", width=3), marker=dict(size=10))
                st.plotly_chart(fig_v2, use_container_width=True)
            with col_s4:
                st.subheader("📉 평균 할인율 (Toss Style)")
                avg_disc = f_df.groupby('brand')['discount_rate'].mean().reindex(brand_order).reset_index()
                fig_v3 = px.bar(avg_disc, x='brand', y='discount_rate', 
                                text=avg_disc['discount_rate'].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "0%"),
                                color='brand', color_discrete_map=brand_colors, category_orders={"brand": brand_order})
                fig_v3.update_traces(textposition='outside', marker_line_width=0, width=0.5)
                fig_v3.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis=dict(showticklabels=False, showgrid=True, gridcolor='rgba(255,255,255,0.05)'), xaxis=dict(showgrid=False), showlegend=False, height=400)
                st.plotly_chart(fig_v3, use_container_width=True)

        with st.expander("📄 검색 결과 상품 목록"):
            st.dataframe(f_df[['brand', 'category', 'name', 'price', 'event', 'unit_price', 'discount_rate']], 
                         use_container_width=True, hide_index=True)

else:
    st.error("데이터를 로드할 수 없습니다.")
