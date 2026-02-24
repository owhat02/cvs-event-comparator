import pandas as pd
from loguru import logger
import os

def classify_product(name):
    name = str(name)
    household = ['샴푸', '린스', '세제', '칫솔', '치약', '물티슈']
    if any(word in name for word in household): return "생활/위생용품"
    snack = ['쿠키', '젤리', '초콜릿', '과자']
    if any(word in name for word in snack): return "간식류"
    meal = ['밥', '찌개', '라면', '도시락']
    if any(word in name for word in meal): return "식사류"
    beverage = ['커피', '콜라', '사이다', '우유']
    if any(word in name for word in beverage): return "음료"
    return "기타"

def run_categorization():
    input_path = 'data/cleaned_data.csv'
    output_path = 'data/categorized_data.csv'
    if not os.path.exists(input_path): return
    df = pd.read_csv(input_path, encoding='utf-8-sig')
    df['category'] = df['name'].apply(classify_product)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.success("분류 완료")

if __name__ == "__main__":
    run_categorization()
