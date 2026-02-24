
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import re
import os
import time

def crawl_7eleven():
    start_ts = datetime.now()
    brand_name = "7-Eleven"
    print(f"🚀 [{brand_name}] 데이터 수집을 시작합니다...")

    all_products = []
    event_configs = [(1, "1+1"), (2, "2+1")]
    url = "https://www.7-eleven.co.kr/product/listMoreAjax.asp"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "https://www.7-eleven.co.kr/product/presentList.asp"
    }

    for p_tab, event_label in event_configs:
        print(f" 📦 {event_label} 상품 데이터를 가져오는 중...")
        payload = {"intPageSize": 10000, "pTab": p_tab, "currPage": 1}

        try:
            response = requests.post(url, headers=headers, data=payload)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.select("li")
                for item in items:
                    try:
                        name_tag = item.select_one(".name")
                        if not name_tag: continue
                        name = name_tag.get_text(strip=True)
                        price_tag = item.select_one(".price span")
                        price = int(re.sub(r'[^0-9]', '', price_tag.get_text(strip=True).replace(',', ''))) if price_tag else 0
                        event_tag = item.select_one(".tag_list_01 li")
                        event = event_tag.get_text(strip=True) if event_tag else event_label
                        img_tag = item.select_one(".pic_product img")
                        img_url = f"https://www.7-eleven.co.kr{img_tag.get('src')}" if img_tag else ""
                        all_products.append({"brand": "7Eleven", "name": name, "price": price, "event": event, "img_url": img_url})
                    except Exception: continue
        except Exception as e:
            print(f" ❌ {event_label} 수집 중 오류: {e}")

    if all_products:
        df = pd.DataFrame(all_products)
        raw_count = len(df)
        df = df.drop_duplicates(subset=['name', 'event'], keep='first')
        
        today = datetime.now().strftime("%y%m%d")
        file_name = f"7Eleven_{today}.csv"
        os.makedirs("data", exist_ok=True)
        file_path = os.path.join("data", file_name)
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
    crawl_7eleven()

if __name__ == "__main__":
    scrape()

import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import re
import os
import time

def crawl_7eleven():
    start_ts = datetime.now()
    brand_name = "7-Eleven"
    print(f"🚀 [{brand_name}] 데이터 수집을 시작합니다...")

    all_products = []
    event_configs = [(1, "1+1"), (2, "2+1")]
    url = "https://www.7-eleven.co.kr/product/listMoreAjax.asp"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "https://www.7-eleven.co.kr/product/presentList.asp"
    }

    for p_tab, event_label in event_configs:
        print(f" 📦 {event_label} 상품 데이터를 가져오는 중...")
        payload = {"intPageSize": 10000, "pTab": p_tab, "currPage": 1}

        try:
            response = requests.post(url, headers=headers, data=payload)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.select("li")
                for item in items:
                    try:
                        name_tag = item.select_one(".name")
                        if not name_tag: continue
                        name = name_tag.get_text(strip=True)
                        price_tag = item.select_one(".price span")
                        price = int(re.sub(r'[^0-9]', '', price_tag.get_text(strip=True).replace(',', ''))) if price_tag else 0
                        event_tag = item.select_one(".tag_list_01 li")
                        event = event_tag.get_text(strip=True) if event_tag else event_label
                        img_tag = item.select_one(".pic_product img")
                        img_url = f"https://www.7-eleven.co.kr{img_tag.get('src')}" if img_tag else ""
                        all_products.append({"brand": "7Eleven", "name": name, "price": price, "event": event, "img_url": img_url})
                    except Exception: continue
        except Exception as e:
            print(f" ❌ {event_label} 수집 중 오류: {e}")

    if all_products:
        df = pd.DataFrame(all_products)
        raw_count = len(df)
        df = df.drop_duplicates(subset=['name', 'event'], keep='first')
        
        today = datetime.now().strftime("%y%m%d")
        file_name = f"7Eleven_{today}.csv"
        os.makedirs("data", exist_ok=True)
        file_path = os.path.join("data", file_name)
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
    crawl_7eleven()

if __name__ == "__main__":
    scrape()

