import streamlit as st

def render_filters(df):
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
    return selected_brands, selected_events, search_query, sort_option