import streamlit as st
import pandas as pd
from pathlib import Path
import os
import itertools
import random

# ----------------------------------
# 페이지 설정 및 CSS 로드
# ----------------------------------
st.set_page_config(page_title="예산 맞춤 꿀조합", page_icon="🍱", layout="wide")

def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
local_css("static/css/style.css")

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
    selected_brands = st.multiselect(
        "🏪 특정 편의점을 선호하시나요? (미선택 시 전체)", 
        options=list(df['brand'].unique()),
        default=[]
    )

allowed_categories = ['식사류', '간식류', '음료', '생수']
filtered_unique_categories = [cat for cat in df['category'].unique() if cat in allowed_categories]

st.markdown("🛒 어떤 종류의 상품을 담고 싶나요? (2개 이상 선택)")
selected_categories = st.multiselect(
    "카테고리 선택", 
    options=filtered_unique_categories, # 필터링된 카테고리만 제공
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
            if selected_brands:
                filtered_df = df[df['brand'].isin(selected_brands)]
            else:
                filtered_df = df
            
            # 2. 선택한 카테고리별 후보 추출 및 키워드 정의
            candidate_items = []
            meal_keywords = ['도시락', '김밥', '샌드위치', '햄버거', '핫도그', '주먹밥', '샐러드', '면', '밥', '삼각김밥', '국', '찌개', '탕', '즉석밥', '덮밥', '볶음밥', '죽', '컵밥', '밥버거']
            soup_keywords = ['국', '찌개', '탕', '전골', '부대찌개', '순두부', '육개장', '곰탕', '설렁탕']
            
            # [수정 1] 제외 키워드 리스트 추가
            meal_exclude_keywords = ['도시락김', '김밥김', '삼각김밥용', '볶음밥용', '찌개양념', '국물용', '소스', '양념', '세트', '재료', '용기', '즉석', '조리']

            rice_staple_keywords = [
                '즉석밥', '백미밥', '현미밥', '잡곡밥', '햇반', '오뚜기밥', '밥', # 기본적인 밥
                '볶음밥', '덮밥', '컵밥', '주먹밥', '김밥', '삼각김밥', # 밥 베이스 식사
                '김치볶음밥', '새우볶음밥', '소불고기덮밥' # 특정 메뉴 이름
            ]
            not_rice_keywords = [
                '장조림', '양갱', '스낵', '과자', '초콜릿', '젤리', '사탕', '비스킷', '빵', '케이크', # 간식류
                '안주', '반찬', '요리', '소스', '양념', '볶음', '김치', '단무지', # 반찬/곁들임
                '밥도둑', '밥이랑' # 이름에 밥이 들어가지만 실제 밥이 아닌 경우
            ]
            side_dish_keywords = [
                '장조림', '볶음', '김치', '고기', '햄', '소시지', '소세지', '참치', '김', '만두', '돈까스', '치킨', '너겟', # 메인 반찬/요리
                '젓갈', '절임', '무침', '조림', '구이', '튀김', # 요리 방식/종류
                '닭가슴살', '육포', '스테이크' # 단백질 보충용
            ]
            integrated_keywords = ['컵밥', '찌개밥', '국밥', '덮밥'] # 이미 밥이 포함된 경우
            
            redundant_groups = [
                ['물', '생수', '에비앙', '삼다수', '아이시스', '평창수', '워터'],
                ['라면', '컵라면', '불닭', '너구리', '신라면', '짜파게티', '비빔면'],
                ['콜라', '사이다', '환타', '웰치스', '소다'], # 탄산 중복 방지
                ['커피', '아메리카노', '라떼', '바리스타', '콜드브루'], # 커피 중복 방지
                ['헛개', '컨디션', '여명', '숙취'], # 헛개차/숙취해소제 중복 방지!
                ['우유', '두유', '요구르트', '요플레'], # 유제품 중복 방지
                ['에너지바', '프로틴바', '초코바'] # 바 종류 중복 방지
            ]

            rice_mask = filtered_df['name'].str.contains('|'.join(rice_staple_keywords), case=False, na=False)
            not_rice_mask = filtered_df['name'].str.contains('|'.join(not_rice_keywords), case=False, na=False)
            rice_candidates = filtered_df[rice_mask & ~not_rice_mask].sort_values(by=['unit_price']).head(15).to_dict('records')
            
            side_mask = filtered_df['name'].str.contains('|'.join(side_dish_keywords), case=False, na=False)
            side_candidates = filtered_df[side_mask].sort_values(by=['unit_price']).head(20).to_dict('records')
            
            num_selected_categories = len(selected_categories)
            for cat in selected_categories:
                cat_df = filtered_df[filtered_df['category'] == cat]
                
                target_price = budget / num_selected_categories
                cat_df['price_diff'] = (cat_df['price'] - target_price).abs()

                cat_df = cat_df[cat_df['price'] <= budget * 0.6] 

                if cat == '식사류' and not cat_df.empty:
                    # [수정 2] meal_items_mask 로직 강화
                    mask_include = cat_df['name'].str.contains('|'.join(meal_keywords), case=False, na=False)
                    mask_exclude = cat_df['name'].str.contains('|'.join(meal_exclude_keywords), case=False, na=False)
                    meal_items_mask = mask_include & ~mask_exclude
                    
                    meal_items = cat_df[meal_items_mask]
                    other_items = cat_df[~meal_items_mask]
                    
                    top_items_for_cat = pd.concat([
                        meal_items.sort_values(by=['discount_rate', 'price_diff'], ascending=[False, True]),
                        other_items.sort_values(by=['discount_rate', 'price_diff'], ascending=[False, True])
                    ]).drop_duplicates(subset=['name']).head(30)
                else:
                    top_items_for_cat = cat_df.sort_values(by=['discount_rate', 'price_diff'], ascending=[False, True]).head(30)
                
                if not top_items_for_cat.empty:
                    pool_list = top_items_for_cat.to_dict('records')
                    sample_size = min(len(pool_list), 10)
                    candidate_items.append(random.sample(pool_list, sample_size))
            
            # 3. 모든 가능한 조합 생성
            if len(candidate_items) == num_selected_categories: 
                all_combinations = list(itertools.product(*candidate_items))
                random.shuffle(all_combinations)
                
                valid_combinations = []
                seen_names = set()

                def has_redundancy(items):
                    for group in redundant_groups:
                        count = 0
                        for item in items:
                            if any(word in item['name'] for word in group):
                                count += 1
                        if count > 1: return True
                    return False

                for combo in all_combinations:
                    current_items = list(combo)
                    
                    if has_redundancy(current_items):
                        continue

                    # --- [식사류 짝꿍 맞추기 로직] ---
                    # '식사류' 카테고리 선택 시에만 동작
                    if '식사류' in selected_categories:
                        has_soup = any(any(skw in item['name'] for skw in soup_keywords) and 
                                       not any(ikw in item['name'] for ikw in integrated_keywords) 
                                       for item in current_items)
                        
                        has_staple_rice = any(any(rkw in item['name'] for rkw in rice_staple_keywords) and 
                                              not any(nrkw in item['name'] for nrkw in not_rice_keywords)
                                              for item in current_items)
                        
                        # [수정 3] is_complete_meal 로직 강화
                        is_complete_meal = any(
                            any(ikw in item['name'] for ikw in ['도시락', '삼각김밥', '김밥', '컵밥', '덮밥', '샌드위치', '햄버거']) and 
                            not any(ekw in item['name'] for ekw in meal_exclude_keywords) 
                            for item in current_items
                        )
                        
                        # [개선 1] 국물류 단독일 경우 밥 추가 및 실패 시 조합 탈락
                        if has_soup and not has_staple_rice and not is_complete_meal and rice_candidates:
                            rice_added_success = False
                            for rice_item in rice_candidates:
                                if sum(item['price'] for item in current_items) + rice_item['price'] <= budget:
                                    current_items.append(rice_item)
                                    has_staple_rice = True # 밥이 추가되었음을 표시
                                    rice_added_success = True
                                    break
                            if not rice_added_success: # 밥 추가에 실패했다면 이 조합은 탈락
                                continue

                        # [개선 2] 맨밥 단독일 경우 반찬 추가 및 실패 시 조합 탈락
                        has_side = any(any(skw in item['name'] for skw in side_dish_keywords) for item in current_items)
                        if not has_soup and not is_complete_meal and not has_side and has_staple_rice and side_candidates:
                            side_added_success = False
                            for side_item in side_candidates:
                                if side_item['name'] not in [it['name'] for it in current_items]:
                                    if sum(item['price'] for item in current_items) + side_item['price'] <= budget:
                                        current_items.append(side_item)
                                        side_added_success = True
                                        break
                            if not side_added_success: # 반찬 추가에 실패했다면 이 조합은 탈락
                                continue
                    
                    # --- 예산 기반 추가 담기 (카테고리 우선순위 및 다양성 확보) ---
                    current_total = sum(item['price'] for item in current_items)
                    
                    if budget - current_total >= 1000 and len(current_items) < 5: # 최대 5개까지 담을 수 있도록 여유 확보
                        
                        # 1. 질문자님의 우선순위 규칙 적용 (타겟 카테고리 설정)
                        target_fill_cats = []
                        if '식사류' in selected_categories and '간식류' in selected_categories:
                            target_fill_cats = ['식사류', '간식류'] # 식사+간식이면 둘 다 골고루
                        elif '식사류' in selected_categories:
                            target_fill_cats = ['식사류'] # 식사가 있으면 무조건 식사 추가
                        elif '간식류' in selected_categories:
                            target_fill_cats = ['간식류'] # 간식이 있으면 무조건 간식 추가
                        else:
                            target_fill_cats = selected_categories # 음료+생수 조합이면 아무거나
                            
                        # 2. 타겟 카테고리에 맞는 후보만 쏙쏙 뽑기
                        all_selectable_candidates = []
                        for pool in candidate_items:
                            for item in pool:
                                if item['category'] in target_fill_cats:
                                    all_selectable_candidates.append(item)
                                    
                        # 3. 비싼 순서(price reverse) 정렬 제거 -> 무작위 섞기 (헛개차 도배 방지 핵심!)
                        random.shuffle(all_selectable_candidates)

                        # 4. 상품 추가
                        for extra_item in all_selectable_candidates:
                            # 이름이 완전히 똑같지 않은지 확인
                            if extra_item['name'] not in [it['name'] for it in current_items]:
                                temp_items = current_items + [extra_item]
                                
                                # 동종 상품(redundant_groups)이 아니고, 예산을 초과하지 않으면 추가!
                                if not has_redundancy(temp_items) and sum(it['price'] for it in temp_items) <= budget:
                                    current_items = temp_items
                                    current_total += extra_item['price']
                                    
                                    # 예산이 1000원 미만으로 남았거나, 5개를 다 채웠으면 멈춤
                                    if budget - current_total < 1000 or len(current_items) >= 5:
                                        break

                    total_price = sum(item['price'] for item in current_items)
                    
                    if total_price <= budget:
                        combo_names = tuple(sorted([item['name'] for item in current_items]))
                        
                        if combo_names not in seen_names:
                            saved_money = sum(item['price'] - item['unit_price'] for item in current_items)
                            valid_combinations.append({
                                'items': current_items,
                                'total_price': total_price,
                                'saved_money': saved_money
                            })
                            seen_names.add(combo_names)
                            
                            if len(valid_combinations) >= 30:
                                break

                # 4. '절약 금액'이 가장 큰 순서대로 정렬하여 상위 5개 추출
                valid_combinations.sort(key=lambda x: (x['total_price'], x['saved_money']), reverse=True)
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
