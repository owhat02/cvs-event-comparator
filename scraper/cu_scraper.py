import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import os
from datetime import datetime

class CUCrawler:
    def __init__(self):
        self.brand = "CU"
        self.base_url = "https://cu.bgfretail.com/event/plusAjax.do"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://cu.bgfretail.com/event/plus.do"
        }
        self.product_list = []

    def fetch_page(self, page_index):
        payload = {"pageIndex": page_index, "listType": "0", "searchCondition": "", "searchWord": ""}
        try:
            response = requests.post(self.base_url, data=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception: return None

    def parse_data(self, html):
        if not html: return False
        soup = BeautifulSoup(html, "html.parser")
        items = soup.select("li.prod_list")
        if not items: return False
        for item in items:
            try:
                name = item.select_one(".name p").get_text(strip=True)
                price_raw = item.select_one(".price strong").get_text(strip=True)
                price = int(re.sub(r"[^\d]", "", price_raw))
                event_element = item.select_one(".badge span")
                event = event_element.get_text(strip=True) if event_element else "행사정보없음"
                img_url = item.select_one(".prod_img img")['src']
                if img_url.startswith("//"): img_url = "https:" + img_url
                self.product_list.append({"brand": self.brand, "name": name, "price": price, "event": event, "img_url": img_url})
            except Exception: continue 
        return True

    def run(self, max_pages=150):
        start_ts = datetime.now()
        print(f"🚀 [{self.brand}] 데이터 수집을 시작합니다...")
        
        for page in range(1, max_pages + 1):
            html = self.fetch_page(page)
            if not self.parse_data(html): break
            if page % 10 == 0: print(f" 📦 {page}페이지 수집 중... (누적: {len(self.product_list)}건)")
            time.sleep(0.5)

        self._save_to_csv(start_ts)

    def _save_to_csv(self, start_ts):
        if not self.product_list:
            print("❌ 수집된 데이터가 없습니다.")
            return

        df = pd.DataFrame(self.product_list)
        raw_count = len(df)
        df = df.drop_duplicates(subset=['name', 'price', 'event'])
        
        date_str = datetime.now().strftime("%y%m%d")
        filename = f"CU_{date_str}.csv"
        os.makedirs("data", exist_ok=True)
        file_path = os.path.join("data", filename)
        df.to_csv(file_path, index=False, encoding="utf-8-sig")

        duration = datetime.now() - start_ts
        print(f"\n최종 결과 요약:")
        print(f" - 전체 수집 개수: {raw_count}")
        print(f" - 중복 제거 후  : {len(df)}")
        print(f" - 저장 파일명   : {file_path}")
        print(f" - 소요 시간     : {duration.seconds // 60}분 {duration.seconds % 60}초")

def scrape():
    crawler = CUCrawler()
    crawler.run()

if __name__ == "__main__":
    scrape()
