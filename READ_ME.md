# 🏪 7Eleven Crawling Project

세븐일레븐 편의점의 **1+1** 및 **2+1** 행사 상품 정보를 자동으로 수집하여 CSV 파일로 저장

---
### 📋 주요 기능
* 세븐 일레븐 공홈 기준 데이터 크롤링 (https://www.7-eleven.co.kr/product/presentList.asp)
* pTab 1: 1+1 행사 상품, pTab 2: 2+1 행사 상품
* 상품 이미지가 없는것도 있습니다(생각 보다 많습니다)
* 상품 이미지 또한 세븐 일레븐 공홈 기준 크롤링(데이터 주는대로 크롤링)
* 수집된 데이터는 CSV 파일로 저장 (상품명, 가격, 행사 종류, 상품 이미지 주소)
  - ex) 7Eleven,LG)샤프란아우라1L(스윗만다린),12900,1+1,https://www.7-eleven.co.kr/upload/product/8801051/189308.1.jpg
---

###  설치 및 환경 설정

*- 필수 라이브러리 설치*
```bash
pip install pandas requests beautifulsoup4
```

*- 실행 방법*
```bash
python seven_eleven_crawler.py
```
*- 참고 사항*
-  기존 Csv 파일이 존재할 경우,삭제후 시행.
-  