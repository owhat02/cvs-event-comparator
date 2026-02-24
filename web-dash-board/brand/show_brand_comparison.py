import streamlit as st
import plotly.express as px
import pandas as pd


def show_brand_comparison(filtered_df, sort_option):
    st.subheader("📊 브랜드별 행사 통계")

    if filtered_df.empty:
        st.warning("데이터가 없습니다.")
        return

    # 1️⃣ [수치 정렬 기준] 평균가격을 먼저 구해서 필터(가격 순)대로 정렬
    avg_price_df = (
        filtered_df
        .groupby('brand')['unit_price']
        .mean()
        .reset_index()
    )

    if sort_option == "가격 낮은 순":
        avg_price_df = avg_price_df.sort_values(by='unit_price', ascending=True)
    else:  # 가격 높은 순
        avg_price_df = avg_price_df.sort_values(by='unit_price', ascending=False)

    # 정렬된 순서대로 브랜드 리스트 추출 (이 순서가 표의 행 순서가 됨)
    brand_order = avg_price_df['brand'].tolist()

    # 2️⃣ 상세 통계 표 데이터 (1+1, 2+1 수치 계산)
    event_counts = (
        filtered_df
        .groupby(['brand', 'event'])
        .size()
        .unstack(fill_value=0)
    )

    # 🔥 [핵심] 표의 행 순서를 '가격 수치로 정렬된 브랜드 순서'로 강제 재배치
    # 이렇게 해야 1+1, 2+1 수치들이 가격 순서에 맞춰서 정렬됨
    final_table = (
        event_counts
        .reindex(brand_order)
        .fillna(0)
        .astype(int)
        .reset_index()
    )
    final_table.rename(columns={'brand': '브랜드'}, inplace=True)

    brand_colors = {"CU": "#9BC621", "7Eleven": "#008135", "emart24": "#FFB71B", "GS25": "#0095D3"}
    col1, col2 = st.columns(2)

    with col1:
        st.write("✨ 브랜드별 총 행사 상품 수")
        brand_total = filtered_df['brand'].value_counts().reset_index()
        fig1 = px.bar(
            avg_price_df.merge(brand_total, on='brand'),
            x='brand', y='count', text='count',
            color='brand', color_discrete_map=brand_colors,
            category_orders={"brand": brand_order}
        )
        fig1.update_layout(showlegend=False, height=400, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig1, use_container_width=True)

    # 🔥 3️⃣ 상세 통계 표: 동그라미 치신 수치들이 이제 필터에 맞게 정렬되어 나옴
    with col2:
        st.write(f"📝 상세 통계 표 ({sort_option} 수치 반영)")
        st.dataframe(
            final_table,
            use_container_width=True,
            hide_index=True,
            # key를 다르게 주어 필터 변경 시 표를 강제로 새로 고침
            key=f"final_sorted_table_{sort_option}",
            column_config={
                "브랜드": st.column_config.TextColumn("브랜드"),
                **{
                    str(col): st.column_config.NumberColumn(str(col), format="%d")
                    for col in final_table.columns if col != "브랜드"
                }
            }
        )

    # 4️⃣ 평균 가격 라인 그래프
    st.write("💰 브랜드별 평균 개당 가격 (unit_price)")
    fig2 = px.line(
        avg_price_df,
        x='brand', y='unit_price', markers=True,
        category_orders={"brand": brand_order}
    )
    fig2.update_traces(line=dict(color="#FF6B6B", width=3), marker=dict(size=10))
    fig2.update_layout(showlegend=False, height=400, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig2, use_container_width=True)