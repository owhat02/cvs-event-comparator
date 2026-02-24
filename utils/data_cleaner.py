import pandas as pd
import glob
from loguru import logger
import os

def clean_and_merge():
    logger.info("데이터 정제를 시작합니다.")
    all_files = glob.glob("data/*.csv")
    exclude_files = ["data/cleaned_data.csv", "data/categorized_data.csv"]
    all_files = [f for f in all_files if f not in exclude_files]
    if not all_files:
        logger.error("data/ 폴더 안에 처리할 CSV 파일이 없습니다.")
        return
    df_list = []
    for file in all_files:
        try:
            df = pd.read_csv(file, encoding='utf-8-sig')
            df['price'] = df['price'].astype(str).str.replace(r'[^0-9]', '', regex=True)
            df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0).astype(int)
            df_list.append(df)
        except Exception as e:
            logger.error(f"{file} 처리 중 오류 발생: {e}")
    if not df_list: return
    combined_df = pd.concat(df_list, ignore_index=True)
    final_df = combined_df.dropna(subset=['brand', 'name', 'event']).drop_duplicates()
    output_path = "data/cleaned_data.csv"
    final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.success(f"정제 완료: {len(final_df)}개 저장")

if __name__ == "__main__":
    clean_and_merge()
