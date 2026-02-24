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
