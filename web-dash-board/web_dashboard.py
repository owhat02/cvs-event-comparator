import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="이달의 편의점 행사", layout="wide")

# --- Author: Kim Han Jin
# --- Date: 2026-02-24

# CSS 로드
def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("style.css")


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


df = get_combined_data()

# 1. 사이드바 (비교)
st.sidebar.title("📌 메뉴")
menu = st.sidebar.radio(
    "비교 데이터 방법 선택",
    ["전체 요약", "브랜드별 비교", "가성비 비교"]
)

# 2. 메인 화면 상단: 필터 및 검색 (메인 상단으로 이동)
st.title(f"🏪 {datetime.now().strftime('%Y년 %m월')} 편의점 행사 정보")

# 필터 영역을 접고 펼칠 수 있게 하거나 컬럼으로 배치
with st.expander("🔍 상세 필터 및 검색", expanded=True):
    f1, f2, f3, f4 = st.columns([2, 2, 2, 1.5])

    with f1:
        brand_list = sorted(df['brand'].unique().tolist())
        selected_brands = st.multiselect("🏪 브랜드", brand_list, default=brand_list)

    with f2:
        event_types = sorted([e for e in df['event'].unique().tolist() if e != '세일'])
        selected_events = st.multiselect("🏷️ 행사", event_types, default=event_types)

    with f3:
        search_query = st.text_input("📝 상품명 검색", "")

    with f4:
        sort_option = st.selectbox("💰 정렬", ["기본 (랜덤)", "가격 낮은 순", "가격 높은 순"])

# 데이터 필터링 로직
filtered_df = df[(df['brand'].isin(selected_brands)) & (df['event'].isin(selected_events)) & (
    df['name'].str.contains(search_query, case=False))]

if sort_option == "가격 낮은 순":
    filtered_df = filtered_df.sort_values(by='unit_price', ascending=True)
elif sort_option == "가격 높은 순":
    filtered_df = filtered_df.sort_values(by='unit_price', ascending=False)

# 3. 메뉴별 콘텐츠 출력
if menu == "전체 요약":
    # --- 기존 상품 리스트 출력 로직 ---
    items_per_page = 30
    total_pages = max((len(filtered_df) // items_per_page) + (1 if len(filtered_df) % items_per_page > 0 else 0), 1)

    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1

    query_hash = search_query + str(selected_events) + str(selected_brands) + sort_option
    if 'last_query' not in st.session_state or st.session_state.last_query != query_hash:
        st.session_state.current_page = 1
        st.session_state.last_query = query_hash

    start_idx = (st.session_state.current_page - 1) * items_per_page
    display_df = filtered_df.iloc[start_idx: start_idx + items_per_page]

    if not display_df.empty:
        cols = st.columns(5)
        for idx, (_, row) in enumerate(display_df.iterrows()):
            with cols[idx % 5]:
                st.markdown(f"""
                    <div class="product-card">
                        <div class="img-container"><img src="{row['img_url']}"></div>
                        <div class="product-name">{row['name']}</div>
                        <div style="margin-top: 8px;">
                            <span style="font-size: 1.2rem; font-weight: 800; color: #ffffff;">{row['price']:,}원</span>
                            <span style="font-size: 0.85rem; color: #ff6b6b; font-weight: bold; margin-left: 5px;">({row['discount_rate']}↓)</span>
                        </div>
                        <div class="unit-price-text">개당 <b>{row['unit_price']:,}원</b></div>
                        <div class="brand-text">📍 {row['brand']} | <span class="event-tag">{row['event']}</span></div>
                    </div>
                """, unsafe_allow_html=True)

        # 페이지네이션
        st.markdown("---")
        _, b1, p_box, b2, _ = st.columns([4, 0.3, 1, 0.3, 4])
        with b1:
            if st.button("❮", key="prev_btn") and st.session_state.current_page > 1:
                st.session_state.current_page -= 1
                st.rerun()
        with p_box:
            st.markdown(f"<div class='page-info-box'>{st.session_state.current_page} / {total_pages}</div>",
                        unsafe_allow_html=True)
        with b2:
            if st.button("❯", key="next_btn") and st.session_state.current_page < total_pages:
                st.session_state.current_page += 1
                st.rerun()
    else:
        st.warning("결과가 없습니다.")

elif menu == "브랜드별 비교":
    st.subheader("📊 브랜드별 행사 통계")

    # 1. 브랜드별 상품 개수 집계
    brand_counts = filtered_df['brand'].value_counts().reset_index()
    brand_counts.columns = ['브랜드', '상품 개수']

    brand_colors = {
        "CU": "#9BC621",
        "7Eleven": "#008135",
        "emart24": "#FFB71B",
        "GS25": "#0095D3"
    }

    col1, col2 = st.columns(2)
    with col1:
        st.write("✨ 브랜드별 총 행사 상품 수")
        # Plotly bar 차트 사용 + 색상 맵 적용
        fig1 = px.bar(
            brand_counts,
            x='브랜드',
            y='상품 개수',
            text='상품 개수',
            color='브랜드',
            color_discrete_map=brand_colors  # 색상 설정 추가
        )
        fig1.update_layout(
            xaxis_tickangle=0,  # 텍스트 가로 고정
            showlegend=False,
            height=400,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig1, width='stretch')

    with col2:
        st.write("📝 상세 통계 표")
        event_brand_counts = filtered_df.groupby(['brand', 'event']).size().unstack(fill_value=0)
        st.dataframe(event_brand_counts, width='stretch')

    # 3. 평균 가격 비교
    st.write("💰 브랜드별 평균 개당 가격 (unit_price)")
    avg_price = filtered_df.groupby('brand')['unit_price'].mean().reset_index()
    avg_price.columns = ['브랜드', '평균가격']

    # 라인 차트를 생성
    fig2 = px.line(
        avg_price,
        x='브랜드',
        y='평균가격',
        markers=True
    )

    # 선의 스타일 설정
    fig2.update_traces(
        line=dict(color="#FF6B6B", width=3),
        marker=dict(size=10)
    )

    # 각 점(markers)에만 브랜드별 색상 적용
    for brand, color in brand_colors.items():
        fig2.update_traces(
            marker=dict(color=color),
            selector=dict(name=brand)
        )

    fig2.update_layout(
        xaxis_tickangle=0,
        showlegend=False,
        height=400,
        margin=dict(l=20, r=20, t=20, b=20),
        hovermode="x unified"
    )

    st.plotly_chart(fig2, width='stretch')

elif menu == "가성비 비교":
    st.subheader("💎 최고의 가성비 아이템 (할인율 TOP 50)")

    # 1. 검색어 유무에 따른 데이터 선택 로직 (기능 해결)
    base_df = filtered_df if search_query else df

    v_df = base_df.copy()
    if not v_df.empty:
        # 할인율을 숫자로 변환하여 정확한 정렬 제공
        v_df['discount_num'] = v_df['discount_rate'].str.replace('%', '', regex=False).astype(float)

        # 할인율 TOP 50 추출
        best_value_df = v_df.sort_values(
            by=['discount_num', 'unit_price'],
            ascending=[False, True]
        ).head(50)

        # 2. 페이지네이션 변수 설정 (기존 로직 유지)
        items_per_page = 9
        total_pages = max((len(best_value_df) - 1) // items_per_page + 1, 1)

        page = st.number_input("페이지", min_value=1, max_value=total_pages, step=1)
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page

        # 현재 페이지 아이템 슬라이싱
        page_items = best_value_df.iloc[start_idx:end_idx]

        # 3. 사용자님의 기존 디자인 구조 그대로 출력
        for _, row in page_items.iterrows(): # page_items로 변경하여 기능 해결
            with st.container():
                c1, c2, c3 = st.columns([1, 4, 2])
                with c1:
                    st.image(row['img_url'], width=80)
                with c2:
                    st.markdown(f"**{row['name']}**")
                    st.caption(f"📍 {row['brand']} | {row['event']}")
                with c3:
                    st.markdown(f"#### {row['discount_rate']} 할인")
                    st.write(f"개당 {row['unit_price']:,}원")
                st.divider()

        st.markdown(f"<div class='page-info-box'>{page} / {total_pages} 페이지</div>", unsafe_allow_html=True)
    else:
        st.warning("분석할 데이터가 없습니다.")