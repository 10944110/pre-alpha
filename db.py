import mysql.connector
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

def get_data():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",  # 改成你的 MySQL 密碼
        database="0322"
    )
    # 查詢 績效日報表
    query = "SELECT * FROM 績效日報表"
    df = pd.read_sql(query, conn)
    conn.close()

    # 去除總計行
    df = df[~df["車牌"].astype(str).str.contains("總計", na=False)]

    # 轉換欄位為分鐘
    for col in ["出車時數", "發動時數", "怠停時數", "開車時數", "停留時數"]:
        df[col + "_分鐘"] = df[col].apply(time_str_to_minutes)

    return df

def get_alcohol_data():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",  # 改成你的 MySQL 密碼
        database="0322"
    )
    # 查詢 酒測紀錄
    query = "SELECT * FROM 酒測紀錄"
    df = pd.read_sql(query, conn)
    conn.close()

    return df