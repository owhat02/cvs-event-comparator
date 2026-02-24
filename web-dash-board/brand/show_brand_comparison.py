import streamlit as st
import plotly.express as px

def show_brand_comparison(filtered_df):
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
            color_discrete_map=brand_colors
        )
        fig1.update_layout(
            xaxis_tickangle=0,
            showlegend=False,
            height=400,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.write("📝 상세 통계 표")
        if not filtered_df.empty:
            event_brand_counts = filtered_df.groupby(['brand', 'event']).size().unstack(fill_value=0)
            st.dataframe(event_brand_counts, use_container_width=True)
        else:
            st.warning("데이터가 없습니다.")

    # 3. 평균 가격 비교
    st.write("💰 브랜드별 평균 개당 가격 (unit_price)")
    if not filtered_df.empty:
        avg_price = filtered_df.groupby('brand')['unit_price'].mean().reset_index()
        avg_price.columns = ['브랜드', '평균가격']

        # 라인 차트 생성
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

        # 각 점(markers)에 브랜드별 색상 적용 (기존 로직 유지)
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

        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("비교할 데이터가 없습니다.")