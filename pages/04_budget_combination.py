import streamlit as st
import pandas as pd
from pathlib import Path
import os
import itertools
import random

# 브랜드별 고유 컬러 반환 함수
def get_brand_color(brand):
    brand_colors = {
        "CU": "#652D90",
        "GS25": "#0054A6",
        "7-Eleven": "#008061",
        "7Eleven": "#008061",
        "세븐일레븐": "#008061",
        "emart24": "#FFB81C",
        "이마트24": "#FFB81C"
    }
    return brand_colors.get(brand, "#8b949e")

# ==========================================
# 1. 상수 정의 (Constants)
# ==========================================
MEAL_KEYWORDS = ['도시락', '김밥', '샌드위치', '햄버거', '핫도그', '주먹밥', '샐러드', '면', '밥', '삼각김밥', '국', '찌개', '탕', '즉석밥', '덮밥', '볶음밥', '죽', '컵밥', '밥버거']
SOUP_KEYWORDS = ['국', '찌개', '탕', '전골', '부대찌개', '순두부', '육개장', '곰탕', '설렁탕']
MEAL_EXCLUDE_KEYWORDS = ['도시락김', '김밥김', '삼각김밥용', '볶음밥용', '찌개양념', '국물용', '세트', '재료', '용기', '즉석', '조리']
RICE_STAPLE_KEYWORDS = ['즉석밥', '백미밥', '현미밥', '잡곡밥', '햇반', '오뚜기밥', '밥', '볶음밥', '덮밥', '컵밥', '주먹밥', '김밥', '삼각김밥', '김치볶음밥', '새우볶음밥', '소불고기덮밥']
NOT_RICE_KEYWORDS = ['장조림', '양갱', '스낵', '과자', '초콜릿', '젤리', '사탕', '비스킷', '빵', '케이크', '안주', '반찬', '요리', '소스', '양념', '볶음', '김치', '단무지', '밥도둑', '밥이랑']
SIDE_DISH_KEYWORDS = ['장조림', '볶음', '김치', '고기', '햄', '소시지', '소세지', '참치', '김', '만두', '돈까스', '치킨', '너겟', '젓갈', '절임', '무침', '조림', '튀김', '닭가슴살', '육포', '스테이크']
INTEGRATED_KEYWORDS = ['컵밥', '찌개밥', '국밥', '덮밥']

REDUNDANT_GROUPS = [
    ['물', '생수', '에비앙', '삼다수', '아이시스', '평창수', '워터'],
    ['라면', '컵라면', '불닭', '너구리', '신라면', '짜파게티', '비빔면'],
    ['음료', '콜라', '사이다', '쥬스', '주스', '에이드', '탄산', '커피', '우유', '차', '아메리카노', '라떼']
]

# ==========================================
# 2. 데이터 로드 및 전처리 (절약 금액 로직 보완)
# ==========================================
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

    # 가격 정규화: 숫자가 아닌 문자 제거 및 결측치 처리
    if df['price'].dtype == object:
        df['price'] = pd.to_numeric(df['price'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce').fillna(0)
    
    # ★ [중요] 행사명 정규화: 공백 제거 (1 + 1 -> 1+1 방지)
    df['event'] = df['event'].astype(str).str.replace(' ', '', regex=False)
    
    df['price'] = df['price'].astype(int)
    df['unit_price'] = df['price'].astype(float) # 초기값은 정가
    df['discount_rate'] = 0.0

    # 행사별 단가 계산 (masks 최적화)
    masks_config = {
        '1+1': (0.5, 50.0),
        '2+1': (2/3, 33.3),
        '3+1': (0.75, 25.0)
    }
    
    for event_key, (multiplier, discount) in masks_config.items():
        # 정규표현식으로 정확히 매칭 (예: 1+1, 2+1)
        mask = df['event'].str.contains(event_key.replace('+', r'\+'), na=False)
        df.loc[mask, 'unit_price'] = df.loc[mask, 'price'] * multiplier
        df.loc[mask, 'discount_rate'] = discount

    df['unit_price'] = df['unit_price'].astype(int)
    return df

# ==========================================
# 3. 비즈니스 로직 (기존 로직 유지)
# ==========================================
def has_redundancy(items):
    for group in REDUNDANT_GROUPS:
        count = sum(1 for item in items if any(word in item['name'] for word in group))
        if count > 1: return True
    return False

def get_candidate_pools(df, categories, budget):
    candidate_items = []
    target_price = budget / len(categories)
    for cat in categories:
        cat_df = df[(df['category'] == cat) & (df['price'] <= budget * 0.6)].copy()
        if cat_df.empty: continue
        cat_df['price_diff'] = (cat_df['price'] - target_price).abs()
        if cat == '식사류':
            mask_include = cat_df['name'].str.contains('|'.join(MEAL_KEYWORDS), case=False, na=False)
            mask_exclude = cat_df['name'].str.contains('|'.join(MEAL_EXCLUDE_KEYWORDS), case=False, na=False)
            meal_items_mask = mask_include & ~mask_exclude
            top_items = pd.concat([
                cat_df[meal_items_mask].sort_values(by=['discount_rate', 'price_diff'], ascending=[False, True]),
                cat_df[~meal_items_mask].sort_values(by=['discount_rate', 'price_diff'], ascending=[False, True])
            ]).drop_duplicates(subset=['name']).head(30)
        else:
            top_items = cat_df.sort_values(by=['discount_rate', 'price_diff'], ascending=[False, True]).head(30)
        if not top_items.empty:
            pool_list = top_items.to_dict('records')
            candidate_items.append(random.sample(pool_list, min(len(pool_list), 10)))
    return candidate_items

def find_best_combinations(df, selected_categories, budget):
    rice_mask = df['name'].str.contains('|'.join(RICE_STAPLE_KEYWORDS), case=False, na=False)
    not_rice_mask = df['name'].str.contains('|'.join(NOT_RICE_KEYWORDS), case=False, na=False)
    rice_candidates = df[rice_mask & ~not_rice_mask].sort_values(by=['unit_price']).head(15).to_dict('records')
    side_mask = df['name'].str.contains('|'.join(SIDE_DISH_KEYWORDS), case=False, na=False)
    side_candidates = df[side_mask].sort_values(by=['unit_price']).head(20).to_dict('records')

    candidate_items = get_candidate_pools(df, selected_categories, budget)
    if len(candidate_items) < len(selected_categories): return []

    all_combinations = list(itertools.product(*candidate_items))
    random.shuffle(all_combinations)
    valid_combinations, seen_names = [], set()

    for combo in all_combinations:
        current_items = list(combo)
        if has_redundancy(current_items): continue

        if '식사류' in selected_categories:
            has_soup = any(any(k in i['name'] for k in SOUP_KEYWORDS) and not any(k in i['name'] for k in INTEGRATED_KEYWORDS) for i in current_items)
            has_staple_rice = any(any(k in i['name'] for k in RICE_STAPLE_KEYWORDS) and not any(k in i['name'] for k in NOT_RICE_KEYWORDS) for i in current_items)
            is_complete_meal = any(any(k in i['name'] for k in ['도시락', '삼각김밥', '김밥', '컵밥', '덮밥', '샌드위치', '햄버거']) and not any(k in i['name'] for k in MEAL_EXCLUDE_KEYWORDS) for i in current_items)
            if has_soup and not has_staple_rice and not is_complete_meal and rice_candidates:
                rice_added = next((r for r in rice_candidates if sum(i['price'] for i in current_items) + r['price'] <= budget), None)
                if rice_added:
                    current_items.append(rice_added)
                    has_staple_rice = True
            has_side = any(any(k in i['name'] for k in SIDE_DISH_KEYWORDS) for i in current_items)
            if not has_soup and not is_complete_meal and not has_side and has_staple_rice and side_candidates:
                side_added = next((s for s in side_candidates if s['name'] not in [i['name'] for i in current_items] and sum(i['price'] for i in current_items) + s['price'] <= budget), None)
                if side_added: current_items.append(side_added)

        current_total = sum(i['price'] for i in current_items)
        if budget - current_total >= 1000 and len(current_items) < 5:
            target_fill_cats = []
            if '식사류' in selected_categories and '간식류' in selected_categories: target_fill_cats = ['식사류', '간식류']
            elif '식사류' in selected_categories: target_fill_cats = ['식사류']
            elif '간식류' in selected_categories: target_fill_cats = ['간식류']
            else: target_fill_cats = selected_categories
            all_selectable = [item for pool in candidate_items for item in pool if item['category'] in target_fill_cats]
            random.shuffle(all_selectable)
            for extra in all_selectable:
                if extra['name'] not in [i['name'] for i in current_items]:
                    temp_items = current_items + [extra]
                    if not has_redundancy(temp_items) and sum(i['price'] for i in temp_items) <= budget:
                        current_items = temp_items
                        current_total += extra['price']
                        if budget - current_total < 1000 or len(current_items) >= 5: break

        total_price = sum(i['price'] for i in current_items)
        if total_price <= budget:
            combo_names = tuple(sorted([i['name'] for i in current_items]))
            if combo_names not in seen_names:
                # ★ 절약 금액 계산: 정가(price) - 할인단가(unit_price)
                saved_money = sum(i['price'] - i['unit_price'] for i in current_items)
                valid_combinations.append({'items': current_items, 'total_price': total_price, 'saved_money': saved_money})
                seen_names.add(combo_names)
                if len(valid_combinations) >= 30: break

    valid_combinations.sort(key=lambda x: (x['total_price'], x['saved_money']), reverse=True)
    return valid_combinations[:5]

# ==========================================
# 4. 화면 UI 출력부
# ==========================================
df = load_data()

st.title("🍱 내 예산 맞춤 꿀조합 생성기")
st.markdown("##### 💰 당신의 예산과 취향을 완벽하게 저격할 편의점 꿀조합을 찾아드려요!")

with st.container(border=True):
    st.subheader("🛒 나만의 꿀조합 레시피")
    col1, col2 = st.columns(2)
    with col1:
        budget = st.slider("💰 예산을 알려주세요", 3000, 30000, 10000, 1000)
    with col2:
        selected_brands = st.multiselect("🏪 편의점 선택", options=list(df['brand'].unique()))

    allowed_categories = ['식사류', '간식류', '음료', '생수']
    filtered_unique_categories = [cat for cat in df['category'].unique() if cat in allowed_categories]
    selected_categories = st.multiselect("📂 카테고리 선택 (2개 이상)", options=filtered_unique_categories, default=['식사류', '음료'])

if st.button("✨ 최적의 꿀조합 찾기", use_container_width=True):
    if len(selected_categories) < 2:
        st.warning("⚠️ 카테고리를 2개 이상 선택해주세요!")
    else:
        with st.spinner("⏳ 최고의 꿀조합 선별 중..."):
            filtered_df = df[df['brand'].isin(selected_brands)] if selected_brands else df
            top_combinations = find_best_combinations(filtered_df, selected_categories, budget)

            if top_combinations:
                st.subheader("🎉 당신을 위한 최고의 꿀조합!")
                for idx, combo in enumerate(top_combinations):
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1: st.markdown(f"### 🍯 추천 {idx + 1}순위")
                        with c2: st.markdown(f"<div style='text-align:right;'><b style='font-size:1.1rem;'>총 {int(combo['total_price']):,}원</b><br><span style='color:#ff4b4b; font-weight:bold;'>🔥 {int(combo['saved_money']):,}원 절약</span></div>", unsafe_allow_html=True)
                        
                        items = combo['items']
                        item_cols = st.columns(len(items))
                        for i, item in enumerate(items):
                            with item_cols[i]:
                                img_url = item['img_url'] if pd.notna(item['img_url']) else "https://via.placeholder.com/150"
                                st.markdown(f"""
                                    <div style="background-color: #1c1c1e; border-radius: 12px; padding: 12px; border: 1px solid #333; text-align: center; height: 100%;">
                                        <img src="{img_url}" style="width: 100%; height: 80px; object-fit: contain; margin-bottom: 10px;">
                                        <div style="font-size: 0.8rem; font-weight: bold; color: white; height: 35px; overflow: hidden; line-height: 1.2;">{item['name']}</div>
                                        <div style="font-size: 0.9rem; color: #58a6ff; font-weight: bold; margin-top: 5px;">{item['price']:,}원</div>
                                        <div style="font-size: 0.7rem; background: #3182f6; color: white; border-radius: 4px; display: inline-block; padding: 2px 5px; margin-top: 5px;">{item['event']}</div>
                                    </div>
                                """, unsafe_allow_html=True)
            else:
                st.error("😥 조건에 맞는 조합을 찾지 못했어요. 예산을 조정해 보세요!")