import streamlit as st
import pandas as pd
from pathlib import Path
import os
import itertools
import random  # ⭐️ 다양성을 위해 추가

# ----------------------------------
# 페이지 설정 및 CSS 로드
# ----------------------------------
st.set_page_config(page_title="예산 맞춤 꿀조합", page_icon="🍱", layout="wide")

def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
local_css("style.css")

# ----------------------------------
# 데이터 로딩 함수 (파일 내 직접 포함)
# ----------------------------------
@st.cache_data
def load_data():
    file_path = Path("data/categorized_data.csv")
    if not file_path.exists():
        st.error("데이터 파일을 찾을 수 없습니다.")
        return pd.DataFrame()
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        st.error(f"데이터 파일 읽기 실패: {e}")
        return pd.DataFrame()

    required_cols = ["brand", "name", "price", "event", "category", "img_url"]
    if not all(col in df.columns for col in required_cols):
        st.error("데이터 파일에 필수 컬럼이 부족합니다.")
        return pd.DataFrame()

    if df['price'].dtype == object:
        df['price'] = pd.to_numeric(df['price'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce').fillna(0)
    
    df['price'] = df['price'].astype(int)
    df['unit_price'] = df['price'].astype(float)
    df['discount_rate'] = 0.0

    masks = {
        '1+1': (df['price'] / 2, 50.0),
        '2+1': ((df['price'] * 2) / 3, 33.3),
        '3+1': ((df['price'] * 3) / 4, 25.0)
    }
    for event_type, (unit_price_calc, discount) in masks.items():
        mask = df['event'].astype(str).str.contains(event_type.replace('+', r'\+'), na=False)
        df.loc[mask, 'unit_price'] = unit_price_calc
        df.loc[mask, 'discount_rate'] = discount

    df['unit_price'] = df['unit_price'].astype(int)
    return df

# --- 데이터 로드 ---
df = load_data()

st.title("🍱 내 예산 맞춤 꿀조합 생성기")
st.markdown("##### 주어진 예산과 카테고리 내에서 **가장 많이 절약할 수 있는 최적의 상품 조합**을 찾아드려요!")
st.write("")

if df.empty:
    st.stop()

# ----------------------------------
# 1. 사용자 입력 UI
# ----------------------------------
col1, col2 = st.columns(2)
with col1:
    budget = st.slider("💰 예산을 알려주세요", min_value=3000, max_value=30000, value=10000, step=1000)
with col2:
    selected_brand = st.selectbox("🏪 특정 편의점을 선호하시나요?", options=['모든 편의점'] + list(df['brand'].unique()))

st.markdown("🛒 어떤 종류의 상품을 담고 싶나요? (2개 이상 선택)")
selected_categories = st.multiselect(
    "카테고리 선택", 
    options=df['category'].unique(),
    label_visibility="collapsed"
)

st.markdown("---")

# ----------------------------------
# 2. 조합 생성 및 결과 표시
# ----------------------------------
if st.button("✨ 최적의 꿀조합 찾기", use_container_width=True):
    if len(selected_categories) < 2:
        st.warning("최소 2개 이상의 카테고리를 선택해야 조합을 만들 수 있습니다!")
    else:
        with st.spinner("최적의 조합을 계산하는 중입니다... 잠시만 기다려주세요."):
            # 1. 브랜드 필터링
            filtered_df = df if selected_brand == '모든 편의점' else df[df['brand'] == selected_brand]
            
            # 2. 선택한 카테고리별 후보 추출
            candidate_items = []
            meal_keywords = ['도시락', '김밥', '샌드위치', '햄버거', '핫도그', '주먹밥', '샐러드', '면', '밥', '삼각김밥', '국', '찌개', '즉석밥']
            
            for cat in selected_categories:
                cat_df = filtered_df[filtered_df['category'] == cat]
                
                # '간편식' 카테고리의 경우, 식사류 키워드를 포함하는 상품 우선 선별
                if cat == '간편식' and not cat_df.empty:
                    meal_items_mask = cat_df['name'].str.contains('|'.join(meal_keywords), case=False, na=False)
                    meal_items = cat_df[meal_items_mask]
                    other_items = cat_df[~meal_items_mask]
                    
                    # ⭐️ 수정: 풀(Pool)을 10개에서 30개로 늘려 다양성 확보
                    top_items_for_cat = pd.concat([
                        meal_items.sort_values(by=['discount_rate', 'unit_price'], ascending=[False, True]),
                        other_items.sort_values(by=['discount_rate', 'unit_price'], ascending=[False, True])
                    ]).drop_duplicates(subset=['name']).head(30)
                else:
                    top_items_for_cat = cat_df.sort_values(by=['discount_rate', 'unit_price'], ascending=[False, True]).head(30)
                
                if not top_items_for_cat.empty:
                    # ⭐️ 핵심: 상위 30개 중 최대 10개를 '무작위'로 뽑아 똑같은 결과 방지
                    pool_list = top_items_for_cat.to_dict('records')
                    sample_size = min(len(pool_list), 10)
                    candidate_items.append(random.sample(pool_list, sample_size))
            
            # 3. 모든 가능한 조합 생성
            if len(candidate_items) == len(selected_categories):
                all_combinations = list(itertools.product(*candidate_items))
                
                # ⭐️ 핵심: 조합을 섞어버려서 1위가 매번 바뀌게 만듦
                random.shuffle(all_combinations)
                
                valid_combinations = []
                seen_names = set() # ⭐️ 핵심: 중복된 상품 구성 방지
                
                for combo in all_combinations:
                    total_price = sum(item['price'] for item in combo)
                    
                    if total_price <= budget:
                        # 조합 내 상품 이름들만 뽑아서 고유 키(Key) 생성
                        combo_names = tuple(sorted([item['name'] for item in combo]))
                        
                        # 완전히 처음 보는 조합일 때만 결과 리스트에 추가
                        if combo_names not in seen_names:
                            saved_money = sum(item['price'] - item['unit_price'] for item in combo)
                            valid_combinations.append({
                                'items': combo,
                                'total_price': total_price,
                                'saved_money': saved_money
                            })
                            seen_names.add(combo_names)
                            
                            # 넉넉하게 30개의 유효 조합을 찾으면 탐색 중단 (속도 향상)
                            if len(valid_combinations) >= 30:
                                break
                
                # 4. '절약 금액'이 가장 큰 순서대로 정렬하여 상위 5개 추출
                valid_combinations.sort(key=lambda x: x['saved_money'], reverse=True)
                top_5 = valid_combinations[:5]
                
                # 5. 결과 출력
                if top_5:
                    st.subheader(f"🎉 예산 {budget:,}원으로 찾은 최고의 꿀조합 Top {len(top_5)}")
                    
                    cols = st.columns(len(top_5))
                    for idx, combo_data in enumerate(top_5):
                        with cols[idx]:
                            with st.container(border=True):
                                st.markdown(f"#### 🥇 추천 {idx + 1}위")
                                
                                for item in combo_data['items']:
                                    st.image(item['img_url'] if pd.notna(item['img_url']) else "https://via.placeholder.com/100", width=100)
                                    st.markdown(f"**{item['name']}** ({item['brand']})")
                                    st.markdown(f"_{item['event']}_ | {item['price']:,}원")
                                    st.divider()

                                st.markdown(f"**합계: {int(combo_data['total_price']):,}원**")
                                st.markdown(f"<span style='color:red; font-weight:bold;'>🔥 {int(combo_data['saved_money']):,}원 절약!</span>", unsafe_allow_html=True)
                else:
                    st.error("아쉽게도 조건에 맞는 조합을 찾지 못했어요. 예산을 올리거나 카테고리를 변경해보세요!")
            else:
                st.warning("선택하신 카테고리 중 일부에 해당하는 상품이 없습니다. 다른 카테고리를 선택해주세요.")