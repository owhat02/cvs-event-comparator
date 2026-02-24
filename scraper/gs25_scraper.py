import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
import os
from datetime import datetime

def scrape_gs25_event_goods():
    start_ts = datetime.now()
    brand_name = "GS25"
    print(f"🚀 [{brand_name}] 데이터 수집을 시작합니다...")
    
    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        response = session.get("http://gs25.gsretail.com/gscvs/ko/products/event-goods", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'CSRFToken'})['value']
    except Exception as e:
        print(f" ❌ 보안 토큰 확보 실패: {e}")
        return

    api_url = f"http://gs25.gsretail.com/gscvs/ko/products/event-goods-search?CSRFToken={csrf_token}"
    gs25_data_list = []
    page_num = 1
    
    while True:
        payload = {'pageNum': page_num, 'pageSize': 100, 'parameterList': 'TOTAL'}
        res = session.get(api_url, params=payload, headers=headers)
        data = res.json()
        if isinstance(data, str): data = json.loads(data)
        results = data.get('results', [])
        if not results: break
            
        for item in results:
            event_code = item.get('eventTypeSp', {}).get('code', '')
            event_name = '1+1' if event_code == 'ONE_TO_ONE' else '2+1' if event_code == 'TWO_TO_ONE' else '덤증정' if event_code == 'GIFT' else event_code
            try: price = int(float(item.get('price', 0)))
            except: price = 0
            gs25_data_list.append({'brand': 'GS25', 'name': item.get('goodsNm', '').strip(), 'price': price, 'event': event_name, 'img_url': item.get('attFileNm', '')})
        
        if page_num % 5 == 0: print(f" 📦 {page_num}페이지 수집 중... (누적: {len(gs25_data_list)}건)")
        page_num += 1
        time.sleep(0.5)
        
    if gs25_data_list:
        df = pd.DataFrame(gs25_data_list)
        raw_count = len(df)
        df.drop_duplicates(subset=['name', 'event'], keep='first', inplace=True)
        
        file_date_str = datetime.now().strftime("%y%m%d")
        csv_filename = f'GS25_{file_date_str}.csv'
        os.makedirs("data", exist_ok=True)
        file_path = os.path.join("data", csv_filename)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        duration = datetime.now() - start_ts
        print(f"\n최종 결과 요약:")
        print(f" - 전체 수집 개수: {raw_count}")
        print(f" - 중복 제거 후  : {len(df)}")
        print(f" - 저장 파일명   : {file_path}")
        print(f" - 소요 시간     : {duration.seconds // 60}분 {duration.seconds % 60}초")
    else:
        print("❌ 수집된 데이터가 없습니다.")

def scrape():
    scrape_gs25_event_goods()

if __name__ == "__main__":
    scrape()
