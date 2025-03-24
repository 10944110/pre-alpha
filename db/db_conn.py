from sqlalchemy import create_engine
import pandas as pd
import re

def time_str_to_minutes(s):
    if pd.isna(s):
        return 0
    match = re.match(r"(\d+)時(\d+)分", str(s))
    if match:
        hours, minutes = match.groups()
        return int(hours) * 60 + int(minutes)
    elif "分" in str(s):
        return int(re.search(r"(\d+)分", str(s)).group(1))
    return 0

# 建立 SQLAlchemy 引擎（可重複使用）
engine = create_engine("mysql+pymysql://root:1234@localhost:3306/0322") #root:改成你的MySQL密碼@localhost:3306/改成你的database名稱

def get_data():
    query = "SELECT * FROM 績效日報表"
    df = pd.read_sql(query, engine)

    # 去除總計行
    df = df[~df["車牌"].astype(str).str.contains("總計", na=False)]

    # 轉換欄位為分鐘
    for col in ["出車時數", "發動時數", "怠停時數", "開車時數", "停留時數"]:
        df[col + "_分鐘"] = df[col].apply(time_str_to_minutes)

    return df

def get_alcohol_data():
    query = "SELECT * FROM 酒測紀錄"
    df = pd.read_sql(query, engine)
    return df
