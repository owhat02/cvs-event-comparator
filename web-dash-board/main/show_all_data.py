import streamlit as st


def show_all_data(filtered_df):
    items_per_page = 30
    total_pages = max((len(filtered_df) // items_per_page) + (1 if len(filtered_df) % items_per_page > 0 else 0), 1)

    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1

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
                            <span class="main-price"">{row['price']:}원</span>
                            <span style="font-size: 0.85rem; color: #ff6b6b; font-weight: bold; margin-left: 5px;">({row['discount_rate']}↓)</span>
                        </div>
                        <div class="unit-price-text">개당 <b>{row['unit_price']:,}원</b></div>
                        <div class="brand-text">📍 {row['brand']} | <span class="event-tag">{row['event']}</span></div>
                    </div>
                """, unsafe_allow_html=True)

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