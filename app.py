
import streamlit as st
import os
import pandas as pd

st.set_page_config(page_title="편의점 행사 대시보드", page_icon="🏪", layout="wide")

# CSS 로드 (모든 페이지 공통)
if os.path.exists("style.css"):
    with open("style.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 데이터 로드 (사이드바 통계용)
@st.cache_data(ttl=3600)
def get_summary_stats():
    file_path = os.path.join('data', 'categorized_data.csv')
    if not os.path.exists(file_path):
        return None
    df = pd.read_csv(file_path)
    return {
        "total_count": len(df),
        "brands_count": len(df['brand'].unique())
    }

# 사이드바 공통 영역
def show_sidebar():
    stats = get_summary_stats()
    if stats:
        st.sidebar.markdown("### 📊 실시간 현황")
        st.sidebar.write(f"✅ 총 행사 상품: **{stats['total_count']:,}개**")
        st.sidebar.write(f"🏢 참여 브랜드: **{stats['brands_count']}개**")
    
    st.sidebar.markdown("---")
    st.sidebar.caption("© 2026 Convenience Store Dashboard")

# 페이지 정의
home_page = st.Page("pages/00_home.py", title="🏠 메인보드", default=True)
summary_page = st.Page("pages/01_overall_summary.py", title="🔍 전체 요약")
comparison_page = st.Page("pages/02_brand_comparison.py", title="📊 브랜드 비교")
best_value_page = st.Page("pages/03_best_value.py", title="💎 가성비 TOP 50")

# 내비게이션 구성
pg = st.navigation({
    "대시보드": [home_page],
    "상세 서비스": [summary_page, comparison_page, best_value_page]
})

# 사이드바 실행
show_sidebar()

# 페이지 실행
pg.run()

from scraper import cu_scraper, gs25_scraper, seven_eleven_scraper, emart24_scraper
import time
import os
from datetime import datetime

def run_all_scrapers():
    """
    편의점 데이터 통합 수집 엔진 (Test Runner)
    모든 브랜드의 스크래퍼를 순차적으로 실행하고 결과를 집계합니다.
    """
    # 저장 폴더 사전 생성
    os.makedirs("data", exist_ok=True)
    
    start_time = time.time()
    
    print("\n" + "═" * 60)
    print(f" 🏪 CONV-DASHBOARD DATA COLLECTOR v1.0")
    print(f" 📅 실행 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 60)
    
    # 실행 대상 스크래퍼 리스트
    scrapers = [
        ("CU", cu_scraper),
        ("GS25", gs25_scraper),
        ("7-Eleven", seven_eleven_scraper),
        ("emart24", emart24_scraper)
    ]
    
    success_count = 0
    
    for brand, module in scrapers:
        try:
            # 각 스크래퍼 내부에서 상세 로그를 출력합니다.
            module.scrape()
            success_count += 1
            print(f" 🏁 {brand} 프로세스 정상 종료")
            print("-" * 40)
        except Exception as e:
            print(f"\n ❌ [{brand}] 치명적 에러 발생: {e}")
            print("-" * 40)
            
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "═" * 60)
    print(f" 전체 수집 작업 완료 ({success_count}/{len(scrapers)})")
    print(f" 총 소요 시간: {int(duration // 60)}분 {int(duration % 60)}초")
    print(f" 데이터 위치: {os.path.abspath('data')}")
    print("═" * 60 + "\n")

if __name__ == "__main__":
    run_all_scrapers()

