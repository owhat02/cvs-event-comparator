# 🏪 편의점 행사 통합 대시보드 (CVS Event Comparator)

본 프로젝트는 국내 주요 편의점(CU, GS25, 7-Eleven, emart24)의 행사 상품 데이터를 실시간으로 수집, 정제, 시각화하여 사용자에게 최적의 쇼핑 정보를 제공하는 통합 대시보드 시스템입니다.

---

## 📂 전체 프로젝트 구조 (Detailed Project Structure)

```text
conv-dashboard/
┣━━ 📂 .devcontainer/                       # 개발 환경 컨테이너화 설정 폴더
┃   ┗━━ 📄 devcontainer.json                # 클라우드 개발 환경 자동화 명세서
┣━━ 📂 .streamlit/                          # Streamlit 설정
┃   ┗━━ 📄 config.toml                      # 테마, 레이아웃 및 서버 구성
┣━━ 📂 assets/                              # 이미지 및 정적 리소스
┃   ┣━━ 🖼️ logo_cu.png                      # CU 로고
┃   ┣━━ 🖼️ logo_gs25.png                    # GS25 로고
┃   ┣━━ 🖼️ logo_7eleven.png                 # 세븐일레븐 로고
┃   ┣━━ 🖼️ logo_emart24.png                 # 이마트24 로고
┃   ┣━━ 🖼️ brandname_visual.png             # 브랜드 통계 시각화 이미지
┃   ┗━━ 🖼️ graph.png                        # 가격 분석 그래프 이미지
┣━━ 📂 batch/                               # 정기 데이터 수집 배치 처리
┃   ┣━━ 📂 script/              
┃   ┃   ┗━━ 📄 crawl_batch_script.py        # 실제 크롤링 배치 실행 스크립트
┃   ┣━━ 📄 batch_scheduler_manager.py       # 배치 스케줄 관리 모듈
┃   ┣━━ 📄 Batach_README.md                 # 배치 시스템 가이드
┃   ┗━━ 📄 __init__.py
┣━━ 📂 data/                                # 수집 및 정제된 데이터 (CSV)
┃   ┣━━ 📄 CU_260224.csv                    # 브랜드별 원본 수집 데이터
┃   ┣━━ 📄 GS25_260224.csv
┃   ┣━━ 📄 7Eleven_260224.csv
┃   ┣━━ 📄 emart24_260224.csv
┃   ┣━━ 📄 cleaned_data.csv                 # 중복 제거 및 형식 통일 데이터
┃   ┣━━ 📄 categorized_data.csv             # 카테고리(식사/간식 등) 분류 데이터
┃   ┗━━ 📄 filtered_convenience_stores.csv  # 지도 표시용 매장 정보
┣━━ 📂 pages/                               # 대시보드 상세 페이지 (Streamlit)
┃   ┣━━ 📄 00_home.py                       # 메인 대시보드 & 실시간 추천
┃   ┣━━ 📄 01_overall_summary.py            # 전체 상품 검색 및 통합 필터
┃   ┣━━ 📄 02_brand_comparison.py           # 브랜드별 행사 규모 및 통계 비교
┃   ┣━━ 📄 03_best_value.py                 # 할인율 TOP 50 가성비 랭킹
┃   ┣━━ 📄 04_budget_combination.py         # 예산 기반 최적 상품 조합 추천
┃   ┣━━ 📄 05_diet_guide.py                 # 고단백/제로 테마 상품 가이드
┃   ┣━━ 📄 06_night_snack_guide.py          # 야식 & 안주 테마 상품 가이드
┃   ┣━━ 📄 07_convenience_store_map.py      # 전국 편의점 위치 지도 서비스
┃   ┣━━ 📄 08_random_picker.py              # 랜덤 추천 럭키박스
┃   ┗━━ 📄 09_jackpot_game.py               # 재미를 위한 잭팟(슬롯머신) 게임
┣━━ 📂 scraper/                             # 브랜드별 데이터 수집 엔진
┃   ┣━━ 📄 cu_scraper.py                    # CU 크롤러
┃   ┣━━ 📄 gs25_scraper.py                  # GS25 크롤러
┃   ┣━━ 📄 seven_eleven_scraper.py          # 세븐일레븐 크롤러
┃   ┣━━ 📄 emart24_scraper.py               # 이마트24 크롤러
┃   ┣━━ 📄 event_news_scraper.py            # 행사 관련 소식 수집기
┃   ┗━━ 📄 __init__.py
┣━━ 📂 test/                                # 단위 및 통합 테스트
┃   ┣━━ 📄 batch_scheduler_test.py
┃   ┗━━ 📄 batch_script_test.py
┣━━ 📂 utils/                               # 공용 유틸리티 및 데이터 처리 도구
┃   ┣━━ 📄 data_cleaner.py                  # 메인 데이터 정제 로직
┃   ┣━━ 📄 data_categorize.py               # 상품명 기반 카테고리 분류 엔진
┃   ┣━━ 📄 chatbot.py                       # AI 상품 도우미 챗봇 모듈
┃   ┣━━ 📄 brandname_visual.py              # 시각화 차트 생성 스크립트
┃   ┣━━ 📄 graph.py                         # 분석 그래프 생성 모듈
┃   ┣━━ 📄 cart.py                          # 장바구니/찜 기능 관련 유틸리티
┃   ┣━━ 📄 news_scraper.py                  # 뉴스 데이터 수집 지원
┃   ┣━━ 📄 data_cleaner_batch.py            # 배치용 데이터 정제 모듈
┃   ┣━━ 📄 data_visualization.ipynb         # 데이터 분석용 Jupyter Notebook
┃   ┗━━ 📄 __init__.py
┣━━ 📄 app.py                               # 프로젝트 메인 실행 파일 (Navigation)
┣━━ 📄 style.css                            # 대시보드 커스텀 UI 스타일
┣━━ 📄 requirements.txt                     # 설치 필요 라이브러리 목록
┣━━ 📄 .gitignore                           # Git 관리 제외 설정
┗━━ 📄 README.md                            # 프로젝트 안내 문서
```

---

## 🛠️ 주요 모듈 설명

### 1. **Core (app.py)**
- 애플리케이션의 컨트롤 타워입니다.
- Streamlit의 `st.navigation`을 통해 멀티 페이지를 구성하며, 사이드바 통계 및 공통 챗봇 기능을 로드합니다.

### 2. **Data Collection (scraper/)**
- 각 편의점의 서로 다른 웹 구조를 분석하여 `Selenium` 및 `BeautifulSoup`으로 데이터를 추출합니다.
- 수집 항목: 브랜드명, 상품명, 가격, 행사 종류(1+1, 2+1 등), 이미지 URL.

### 3. **Batch System (batch/)**
- 수동 실행 없이도 정기적으로 최신 데이터를 수집할 수 있도록 스케줄러를 포함하고 있습니다.
- `batch_scheduler_manager.py`를 통해 `app.py` 실행 시 백그라운드에서 동작합니다.

### 4. **Data Intelligence (utils/)**
- **Clean & Categorize**: 수집된 로우 데이터를 정제하고, 1,000개 이상의 상품을 '식사류', '간식류' 등으로 자동 분류합니다.
- **AI Chatbot**: 사용자의 질문을 분석하여 조건에 맞는 상품을 대화형으로 추천합니다.

---

## 🚀 설치 및 실행 방법

### 1. 환경 구축
```bash
# 라이브러리 설치
pip install -r requirements.txt
```

### 2. 대시보드 실행
```bash
streamlit run app.py
```

### 3. 데이터 업데이트 (선택 사항)
배치 시스템이 자동으로 동작하지만, 수동으로 데이터를 즉시 수집하려면:
```bash
# 개별 크롤러 실행
python scraper/cu_scraper.py
# 이후 데이터 정제 실행
python utils/data_cleaner.py
python utils/data_categorize.py
```

---
© 2026 Convenience Store Event Dashboard Project.
