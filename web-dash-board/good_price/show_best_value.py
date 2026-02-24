import streamlit as st
import pandas as pd


def show_best_value(filtered_df, df, search_query, selected_brands, selected_events, sort_option):

    st.subheader("💎 최고의 가성비 아이템")

    v_df = filtered_df.copy()

    if v_df.empty:
        st.warning("분석할 데이터가 없습니다.")
        return

    # -------------------------
    # 1️⃣ 가격 숫자 변환
    # -------------------------
    v_df["price"] = pd.to_numeric(v_df["price"], errors="coerce").fillna(0)

    # -------------------------
    # 2️⃣ 할인율 숫자 변환
    # -------------------------
    v_df["discount_num"] = (
        v_df["discount_rate"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .fillna("0")
        .astype(float)
    )

    # -------------------------
    # 3️⃣ 체감 단가 계산
    # -------------------------
    def calc_real_price(row):
        price = row["price"]
        event = row["event"]

        if event == "1+1":
            return price / 2
        elif event == "2+1":
            return price * 2 / 3
        elif event == "3+1":
            return price * 3 / 4
        else:
            return price

    v_df["real_unit_price"] = v_df.apply(calc_real_price, axis=1)

    # -------------------------
    # 🔥 4️⃣ 정렬 (메인에서 전달받은 값 사용)
    # -------------------------
    if sort_option == "가격 낮은 순":
        v_df = v_df.sort_values(by="real_unit_price", ascending=True)

    elif sort_option == "가격 높은 순":
        v_df = v_df.sort_values(by="real_unit_price", ascending=False)

    elif sort_option == "할인율 높은 순":
        v_df = v_df.sort_values(by="discount_num", ascending=False)

    else:
        v_df = v_df.sort_values(
            by=["real_unit_price", "discount_num"],
            ascending=[True, False]
        )

    v_df = v_df.reset_index(drop=True)

    # -------------------------
    # 5️⃣ 페이지네이션
    # -------------------------
    items_per_page = 9
    total_pages = max((len(v_df) - 1) // items_per_page + 1, 1)

    if "good_price_page" not in st.session_state:
        st.session_state.good_price_page = 1

    if st.session_state.good_price_page > total_pages:
        st.session_state.good_price_page = 1

    start_idx = (st.session_state.good_price_page - 1) * items_per_page
    display_df = v_df.iloc[start_idx:start_idx + items_per_page]

    # -------------------------
    # 6️⃣ UI 출력
    # -------------------------
    for _, row in display_df.iterrows():
        with st.container():
            c1, c2, c3 = st.columns([1, 4, 2])

            with c1:
                st.image(row["img_url"], width=80)

            with c2:
                st.markdown(f"**{row['name']}**")
                st.caption(f"📍 {row['brand']} | {row['event']}")

            with c3:
                st.markdown(f"#### {row['discount_rate']} 할인")
                st.write(f"개당 {int(row['real_unit_price']):,}원 (체감가)")

            st.divider()

    # -------------------------
    # 7️⃣ 페이지 버튼
    # -------------------------
    st.markdown("---")
    _, b1, p_box, b2, _ = st.columns([4, 0.3, 1, 0.3, 4])

    with b1:
        if st.button("❮", key="good_prev_btn") and st.session_state.good_price_page > 1:
            st.session_state.good_price_page -= 1
            st.rerun()

    with p_box:
        st.markdown(
            f"<div class='page-info-box'>{st.session_state.good_price_page} / {total_pages}</div>",
            unsafe_allow_html=True
        )

    with b2:
        if st.button("❯", key="good_next_btn") and st.session_state.good_price_page < total_pages:
            st.session_state.good_price_page += 1
            st.rerun()