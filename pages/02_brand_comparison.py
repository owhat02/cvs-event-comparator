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
    ].copy()

    # --- 정렬 로직 (모든 선택 브랜드 포함) ---
    if sort_option == "상품 많은 순":
        brand_order = f_df['brand'].value_counts().reindex(selected_brands, fill_value=0).sort_values(ascending=False).index.tolist()
    elif sort_option == "가격 낮은 순":
        brand_order = f_df.groupby('brand', observed=False)['unit_price'].mean().reindex(selected_brands).sort_values().index.tolist()
    elif sort_option == "할인율 높은 순":
        brand_order = f_df.groupby('brand', observed=False)['discount_rate'].mean().reindex(selected_brands).sort_values(ascending=False).index.tolist()
    else:
        brand_order = selected_brands

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
            for brand in brand_order:
                b_df = f_df[f_df['brand'] == brand]
                if b_df.empty:
                    stats.append({'brand': brand, '다양성': 0, '할인강도': 0, '식사특화': 0, '간식특화': 0, '가성비': 0})
                    continue
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
                st.plotly_chart(fig_radar, width="stretch")

        # Tab 2: 카테고리 및 행사 비중 분석
        with tab2:
            st.subheader("브랜드별 행사 유형 비중 (1+1 vs 2+1 vs 3+1)")
            
            # 모든 브랜드/행사 조합을 포함하기 위해 범주형 변환
            plot_df = f_df.copy()
            plot_df['brand'] = pd.Categorical(plot_df['brand'], categories=brand_order, ordered=True)
            plot_df['event'] = pd.Categorical(plot_df['event'], categories=selected_events, ordered=True)
            plot_df['category'] = pd.Categorical(plot_df['category'], categories=selected_cats, ordered=True)

            # 비중 데이터 계산 (모든 조합 유지)
            event_stats = plot_df.groupby(['brand', 'event'], observed=False).size().reset_index(name='count')
            brand_totals = event_stats.groupby('brand', observed=False)['count'].transform('sum')
            event_stats['percentage'] = np.where(brand_totals > 0, (event_stats['count'] / brand_totals) * 100, 0)
            
            fig_pct = px.bar(event_stats, x='brand', y='percentage', color='event',
                            text=event_stats['percentage'].apply(lambda x: f'{x:.1f}%' if x > 0 else ''),
                            category_orders={"brand": brand_order, "event": selected_events},
                            color_discrete_sequence=px.colors.qualitative.Pastel,
                            labels={'percentage': '비중 (%)', 'brand': '브랜드', 'event': '행사유형'})
            fig_pct.update_layout(yaxis_title="비중 (%)", barmode='stack', height=450)
            st.plotly_chart(fig_pct, width="stretch")
            st.info("💡 각 브랜드가 어떤 증정 방식에 더 집중하고 있는지 한눈에 비교할 수 있습니다.")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("브랜드별 카테고리 구성 (Stacked Bar)")
                # Treemap은 순서 고정이 어려우므로 정렬 가능한 Stacked Bar로 변경
                cat_stats = plot_df.groupby(['brand', 'category'], observed=False).size().reset_index(name='count')
                cat_brand_totals = cat_stats.groupby('brand', observed=False)['count'].transform('sum')
                cat_stats['percentage'] = np.where(cat_brand_totals > 0, (cat_stats['count'] / cat_brand_totals) * 100, 0)
                
                fig_cat_pct = px.bar(cat_stats, x='brand', y='percentage', color='category',
                                    text=cat_stats['percentage'].apply(lambda x: f'{x:.1f}%' if x > 5 else ''), # 5% 이상만 표시
                                    category_orders={"brand": brand_order, "category": selected_cats},
                                    color_discrete_sequence=px.colors.qualitative.Safe,
                                    labels={'percentage': '비중 (%)', 'brand': '브랜드', 'category': '카테고리'})
                fig_cat_pct.update_layout(yaxis_title="비중 (%)", barmode='stack', height=450)
                st.plotly_chart(fig_cat_pct, width="stretch")
            with col2:
                st.subheader("브랜드 x 카테고리 집중도 (Heatmap)")
                # Heatmap 데이터 생성 (Categorical 반영으로 자동 정렬됨)
                heat_data = plot_df.groupby(['brand', 'category'], observed=False).size().unstack(fill_value=0)
                fig_heat = px.imshow(heat_data, text_auto=True, color_continuous_scale='GnBu',
                                   labels=dict(x="카테고리", y="브랜드", color="상품 수"))
                st.plotly_chart(fig_heat, width="stretch")

        # Tab 3: 가격 전략
        with tab3:
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.subheader("브랜드별 실질 구매가 분포 (Box Plot)")
                fig_box = px.box(f_df, x='brand', y='unit_price', color='brand', color_discrete_map=brand_colors, category_orders={"brand": brand_order})
                st.plotly_chart(fig_box, width="stretch")
            with col_p2:
                st.subheader("가격 구간별 상품 비중")
                f_df['price_group'] = pd.cut(f_df['unit_price'], bins=[0, 1500, 3000, 5000, 10000, 100000],
                                            labels=['1.5천원 이하', '3천원 이하', '5천원 이하', '1만원 이하', '1만원 초과'])
                price_group_df = f_df.groupby(['brand', 'price_group'], observed=False).size().reset_index(name='상품 수')
                fig_price_group = px.bar(price_group_df, x='brand', y='상품 수', color='price_group', barmode='stack', color_discrete_sequence=px.colors.sequential.Teal, category_orders={"brand": brand_order})
                st.plotly_chart(fig_price_group, width="stretch")

        # Tab 4: 트렌드 키워드
        with tab4:
            st.subheader("🔍 트렌드 키워드 대응력")
            keywords = {'제로/슈가프리': ['제로', 'zero', '무설탕', '저당'], '단백질/헬스': ['단백질', '프로틴', 'protein', '닭가슴살'], '매운맛/마라': ['매운', '핫', 'hot', '마라', '불닭'], '과일/상큼': ['딸기', '사과', '포도', '망고', '레몬']}
            key_stats = []
            for brand in brand_order:
                b_df = f_df[f_df['brand'] == brand]
                for key, words in keywords.items():
                    count = b_df['name'].str.contains('|'.join(words), case=False, na=False).sum()
                    key_stats.append({'브랜드': brand, '트렌드': key, '상품 수': count})
            fig_key = px.bar(pd.DataFrame(key_stats), x='트렌드', y='상품 수', color='브랜드', barmode='group', color_discrete_map=brand_colors, text_auto=True, category_orders={"브랜드": brand_order})
            st.plotly_chart(fig_key, width="stretch")

        # Tab 5: 요약 통계
        with tab5:
            st.subheader("📈 실시간 필터링 요약")
            col_s1, col_s2 = st.columns([1, 1.2])
            with col_s1:
                st.write(f"✨ 브랜드별 상품 수 (정렬: {sort_option})")
                brand_counts = f_df['brand'].value_counts().reindex(brand_order, fill_value=0).reset_index()
                brand_counts.columns = ['브랜드', '상품 개수']
                fig_v1 = px.bar(brand_counts, x='브랜드', y='상품 개수', text='상품 개수', color='브랜드', color_discrete_map=brand_colors, category_orders={"브랜드": brand_order})
                fig_v1.update_traces(textposition='outside', marker_line_width=0, width=0.5)
                fig_v1.update_layout(xaxis_tickangle=0, showlegend=False, height=400, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_v1, width="stretch")
            with col_s2:
                st.write(f"📝 행사 유형별 상세 통계 ({sort_option})")
                # 피벗 생성 및 브랜드 정렬
                event_pivot = f_df.groupby(['brand', 'event'], observed=False).size().unstack(fill_value=0).reindex(brand_order, fill_value=0)
                
                # 사용자가 필터에서 선택한 순서대로 컬럼 정렬
                # pivot 테이블에 존재하는 컬럼만 필터링하여 순서 적용
                cols_order = [e for e in selected_events if e in event_pivot.columns]
                # 혹시 pivot에만 존재하는 컬럼이 있다면 뒤에 추가 (예외 상황 대비)
                remaining_cols = [c for c in event_pivot.columns if c not in selected_events]
                event_pivot = event_pivot[cols_order + remaining_cols]
                
                st.dataframe(event_pivot, width="stretch")

            st.divider()
            col_s3, col_s4 = st.columns(2)
            with col_s3:
                st.subheader("💰 평균 가격 추이")
                avg_price = f_df.groupby('brand', observed=False)['unit_price'].mean().reindex(brand_order).reset_index()
                avg_price.columns = ['brand', 'unit_price']
                fig_v2 = px.line(avg_price, x='brand', y='unit_price', markers=True, category_orders={"brand": brand_order})
                fig_v2.update_traces(line=dict(color="#FF6B6B", width=3), marker=dict(size=10))
                fig_v2.update_layout(height=400, xaxis_title=None, yaxis_title="평균 가격 (원)", margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_v2, width="stretch")
            with col_s4:
                st.subheader("📉 평균 할인율 (Toss Style)")
                avg_disc = f_df.groupby('brand', observed=False)['discount_rate'].mean().reindex(brand_order).reset_index()
                avg_disc.columns = ['brand', 'discount_rate']
                
                # 돋보기 효과를 위한 Y축 범위 계산
                min_val = avg_disc['discount_rate'].min()
                max_val = avg_disc['discount_rate'].max()
                y_min = max(0, min_val - 2) if pd.notnull(min_val) else 0
                y_max = (max_val + 2) if pd.notnull(max_val) and max_val > 0 else 50

                fig_v3 = px.bar(avg_disc, x='brand', y='discount_rate', 
                                text=avg_disc['discount_rate'].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "0%"),
                                color='brand', color_discrete_map=brand_colors, category_orders={"brand": brand_order})
                fig_v3.update_traces(
                    textposition='outside', 
                    textfont=dict(size=14, weight='bold'),
                    marker_line_width=0, 
                    width=0.45
                )
                fig_v3.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    yaxis=dict(showticklabels=False, showgrid=True, gridcolor='rgba(255,255,255,0.05)', range=[y_min, y_max]), 
                    xaxis=dict(showgrid=False), 
                    showlegend=False, 
                    height=400,
                    margin=dict(l=10, r=10, t=40, b=10)
                )
                st.plotly_chart(fig_v3, width="stretch")

        with st.expander("📄 검색 결과 상품 목록"):
            st.dataframe(f_df[['brand', 'category', 'name', 'price', 'event', 'unit_price', 'discount_rate']], 
                         width="stretch", hide_index=True)

else:
    st.error("데이터를 로드할 수 없습니다.")
