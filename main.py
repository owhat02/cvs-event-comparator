import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime


def crawl_7eleven():
    print("🚀 세븐일레븐 데이터 수집을 시작합니다")

    all_products = []
    # pTab 1: 1+1, pTab 2: 2+1
    event_configs = [(1, "1+1"), (2, "2+1")]

    url = "https://www.7-eleven.co.kr/product/listMoreAjax.asp"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "https://www.7-eleven.co.kr/product/presentList.asp"
    }

    for p_tab, event_label in event_configs:
        print(f"📦 {event_label} 상품 가져오는 중...")

        payload = {
            "intPageSize": 1000000,
            "pTab": p_tab,
            "currPage": 1
        }

        try:
            response = requests.post(url, headers=headers, data=payload)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.select("li")

                category_count = 0
                for item in items:
                    try:
                        img_tag = item.select_one(".pic_product img")
                        name = img_tag.get('alt', '').strip() if img_tag else item.select_one(".txt_product").get_text(
                            strip=True)

                        price_text = item.select_one(".price_list span").get_text(strip=True).replace(',', '')
                        price = int(price_text)

                        event = item.select_one(".tag_list_01 li").get_text(strip=True)

                        img_src = img_tag.get('src')
                        img_url = f"https://www.7-eleven.co.kr{img_src}"

                        all_products.append({
                            "brand": "7Eleven",
                            "name": name,
                            "price": price,
                            "event": event,
                            "img_url": img_url
                        })
                        category_count += 1
                    except Exception:
                        continue
        except Exception as e:
            print(f"❌ {event_label} 수집 중 오류: {e}")

    # --- 데이터 저장 (중복 제거 로직 삭제됨) ---
    if all_products:
        df = pd.DataFrame(all_products)

        # 열 순서 고정
        df = df[["brand", "name", "price", "event", "img_url"]]

        today = datetime.now().strftime("%y%m%d")
        file_name = f"7Eleven_{today}.csv"

        # 중복 제거 없이 바로 저장
        df.to_csv(file_name, index=False, encoding='utf-8-sig')
    else:
        print("❌ 수집된 데이터가 없습니다.")


if __name__ == "__main__":
    crawl_7eleven()