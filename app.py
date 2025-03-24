import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
import plotly.express as px
import mysql.connector
import pandas as pd
import re
from dash.dependencies import Input, Output, State
from db import get_alcohol_data

# 從 MySQL 資料庫取得資料
def get_data():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",  # <<< 改成你的 MySQL 密碼
        database="0322"
    )
    query = "SELECT * FROM 績效日報表"  # 資料表名稱是 sheet
    df = pd.read_sql(query, conn)
    conn.close()

    df = df[~df["車牌"].astype(str).str.contains("總計", na=False)]

    # 欄位轉換
    df["行駛里程"] = pd.to_numeric(df["行駛里程"], errors="coerce")
    df["車輛成本"] = pd.to_numeric(df["車輛成本"], errors="coerce")
    df["人力成本"] = pd.to_numeric(df["人力成本"], errors="coerce")
    df["總成本"] = df["車輛成本"].fillna(0) + df["人力成本"].fillna(0)
    df["ETC費用"] = pd.to_numeric(df["ETC費用"], errors="coerce")
    df["行駛里程"] = pd.to_numeric(df["行駛里程"], errors="coerce")
    df["碳排放"] = pd.to_numeric(df["碳排放"], errors="coerce")
    
    # 避免除以零的問題：只在 ETC 費用大於 0 時計算成本效益比
    df["成本效益比"] = 0  # 預設值設為 0
    mask = df["ETC費用"] > 0  # 找出 ETC 費用大於 0 的記錄
    df.loc[mask, "成本效益比"] = df.loc[mask, "行駛里程"] / df.loc[mask, "ETC費用"]
    
    return df

# 建立 Dash 應用程式
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css"
    ]
)


df = get_data()
df_alcohol = get_alcohol_data()

operation_date = df["作業日期"].iloc[0]  # 假設欄位叫"作業日期"

# 只保留像 "BTA-0375"、"KLK-8221" 這種格式的車牌（字母3碼 + - + 數字4碼）
valid_plate_pattern = r"^[A-Z]{3}-\d{4}$"
valid_df = df[df["車牌"].astype(str).str.match(valid_plate_pattern)]

total_departures = valid_df.shape[0] # 總出車數量 = 有效車牌的筆數
# KPI 統計資料
average_cost = df["總成本"].mean()
total_etc = df["ETC費用"].sum()
total_carbon = df["碳排放"].sum()
total_mileage = df["行駛里程"].sum()

# 過濾掉成本效益比為0的資料（這些可能是 ETC 費用為 0 的車輛）
df_for_chart = df[df["成本效益比"] > 0]
# 總成本長條圖 排序資料
df_for_chart = df_for_chart.sort_values(by="成本效益比", ascending=False)
fig = px.bar(df_for_chart, x="車牌", y="成本效益比", title="各車輛成本效益比(行駛里程/ETC費用)", color="成本效益比", height=350)


# Dash Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div([
                    html.Div("宥辰", className="fs-4 fw-bold text-white text-center my-3"),
                    html.Hr(className="border-white mx-3"),
                    html.Ul([
                        html.Li([html.I(className="bi bi-bar-chart-line me-2"), "即時分析"],
                                className="nav-item text-white px-3 py-2"),
                        html.Li([html.I(className="bi bi-clock me-2"), "還"],
                                className="nav-item text-white px-3 py-2"),
                        html.Li([html.I(className="bi bi-person me-2"), "沒"],
                                className="nav-item text-white px-3 py-2"),
                        html.Li([html.I(className="bi bi-file-earmark-text me-2"), "想"],
                                className="nav-item text-white px-3 py-2"),
                        html.Li([html.I(className="bi bi-display me-2"), "到"],
                                className="nav-item text-white px-3 py-2"),
                    ], className="list-unstyled")
                ], className="d-flex flex-column h-100")
            ], style={
                "width": "220px",
                "backgroundColor": "#81a69b",
                "position": "fixed",
                "top": "0",
                "bottom": "0",
                "left": "0",
                "padding": "0",
                "zIndex": "1000"
            })
        ], width=2),

        dbc.Col([
            # 查詢區（Dropdown + Button + 日期顯示）
            dbc.Row([
                # 左側 Dropdown + Button 同行
                dbc.Col([
                    dbc.InputGroup([
                        dcc.Dropdown(
                            id="date-dropdown",
                            options=[{"label": d, "value": d} for d in sorted(df["作業日期"].unique())],
                            value=operation_date,
                            placeholder="請選擇作業日期",
                            style={"flex": "1"}
                        ),
                        dbc.Button("查詢", id="submit-button", color="primary", className="ms-2")
                    ], className="d-flex")
                ], width=8),

                # 右側顯示選取日期
                dbc.Col([
                    html.H6(id="selected-date-display", className="text-end mb-0")
                ], width=4, className="d-flex align-items-center justify-content-end")
            ], className="my-3"),

            # 資料顯示區（由 callback 替換）
            html.Div(id="main-content")
        ], width=10, style={"marginLeft": "220px"})
    ])
], fluid=True)

@app.callback(
    Output("main-content", "children"),
    Output("selected-date-display", "children"),
    Input("submit-button", "n_clicks"),
    State("date-dropdown", "value")
)

def update_dashboard(n_clicks, selected_date):
    if not selected_date:
        return html.Div("請選擇日期"), ""

    # 根據選取日期過濾資料
    df_filtered = df[df["作業日期"] == selected_date]
    df_filtered = df_filtered[~df_filtered["車牌"].astype(str).str.contains("總計", na=False)]
        
    # 轉換時間字串為小時數字
    def extract_hour_from_str(t):
        try:
            if pd.isna(t):
                return None
            return int(str(t).split(":")[0])
        except:
            return None

    df_filtered["出車時段"] = df_filtered["出車時間"].apply(extract_hour_from_str)
    df_filtered["回車時段"] = df_filtered["回車時間"].apply(extract_hour_from_str)

    出車統計 = df_filtered.groupby("出車時段").size().reset_index(name="出車數量")
    回車統計 = df_filtered.groupby("回車時段").size().reset_index(name="回車數量")

    # 合併出車與回車統計
    時段統計 = pd.merge(出車統計, 回車統計, left_on="出車時段", right_on="回車時段", how="outer")
    時段統計["時段"] = 時段統計["出車時段"].combine_first(時段統計["回車時段"])
    時段統計 = 時段統計[["時段", "出車數量", "回車數量"]].fillna(0).sort_values(by="時段")

    # 計算 KPI 數值
    total_departures = df_filtered.shape[0]
    total_mileage = df_filtered["行駛里程"].sum()
    total_carbon = df_filtered["碳排放"].sum()
    total_etc = df_filtered["ETC費用"].sum()

    # 成本效益比（行駛里程 / ETC費用）
    df_filtered = df_filtered.copy()
    df_filtered["成本效益比"] = df_filtered["行駛里程"] / df_filtered["ETC費用"]
    df_filtered["成本效益比"] = df_filtered["成本效益比"].replace([float("inf"), -float("inf")], 0).fillna(0)

    df_sorted = df_filtered.sort_values(by="成本效益比", ascending=False)

    fig_line = px.line( 時段統計, x="時段", y=["出車數量", "回車數量"], markers=True, labels={"value": "車輛數", "variable": "類型"}, height=200)
    fig_line.update_layout(margin=dict(l=30, r=30, t=30, b=30))

    df_alcohol = get_alcohol_data()
    df_alcohol["時間"] = pd.to_datetime(df_alcohol["時間"]).dt.date  # 確保是 date 格式
    selected_date_obj = pd.to_datetime(selected_date).date()

    df_alcohol_filtered = df_alcohol[df_alcohol["時間"] == selected_date_obj]
    df_alcohol_filtered["是否通過"] = df_alcohol_filtered["酒測值"] < df_alcohol_filtered["臨界值"]
    pass_count = df_alcohol_filtered["是否通過"].sum()
    fail_count = len(df_alcohol_filtered) - pass_count

    pass_rate = round(pass_count / (pass_count + fail_count) * 100, 1) if (pass_count + fail_count) > 0 else 0
    fig_alcohol = px.pie(names=["通過", "未通過"],values=[pass_count, fail_count],hole=0.6,color_discrete_sequence=["#50e3e6", "#dddddd"])
    fig_alcohol.update_traces(textinfo='none',hoverinfo='label+percent',showlegend=False)
    fig_alcohol.update_layout(annotations=[{'text': f"{pass_rate:.0f}%",'font': {'size': 32},'showarrow': False}],margin=dict(l=0, r=0, t=5, b=0),height=200)
    
    # 繪製長條圖
    fig = px.bar(df_sorted, x="車牌",y="成本效益比",title=f"{selected_date} 成本效益比(行駛里程/總成本)",color="成本效益比",height=350)

    # 回傳更新後的畫面內容
    return html.Div([
        # KPI 卡片
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("總出車數量", className="text-muted"),
                    html.Div(
                        html.H3(f"{total_departures} 輛", className="text-success"),
                        className="d-flex justify-content-center align-items-center"
                    )
                ])
            ]), width=3),

            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("總行駛里程", className="text-muted"),
                    html.Div(
                        html.H3(f"{total_mileage:.1f} km", className="text-success"),
                        className="d-flex justify-content-center align-items-center"
                    )
                ])
            ]), width=3),

            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("總碳排量", className="text-muted"),
                    html.Div(
                        html.H3(f"{total_carbon:.1f} CO²e", className="text-success"),
                        className="d-flex justify-content-center align-items-center"
                    )
                ])
            ]), width=3),

            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H6("總成本", className="text-muted"),
                    html.Div(
                        html.H3(f"${total_etc:.0f}", className="text-success"),
                        className="d-flex justify-content-center align-items-center"
                    )
                ])
            ]), width=3),
        ], className="mb-3"),
        
        # 出車/回車時段圖表
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("酒測通過率"),
                dbc.CardBody(dcc.Graph(figure=fig_alcohol))
            ]), width=3),
            dbc.Col(dbc.Card([
                dbc.CardHeader("出車與回車時段"),
                dbc.CardBody(dcc.Graph(figure=fig_line))
            ]), width=9)
        ], className="mb-3"),

        # 成本效益圖表
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("各車輛總成本比較"),
                dbc.CardBody(dcc.Graph(figure=fig))
            ]), width=12)
        ], className="mb-3"),

        # 資料表格
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("詳細資料表"),
                dbc.CardBody(dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in ["車牌", "司機", "行駛里程", "ETC費用", "碳排放"]],
                    data=df_filtered.to_dict("records"),
                    page_size=10,
                    style_table={"overflowX": "auto"},
                    style_cell={"textAlign": "center", "fontFamily": "Arial", "padding": "8px"},
                    style_header={"backgroundColor": "lightgray", "fontWeight": "bold"}
                ))
            ]), width=12)
        ])
    ]), f"查詢日期：{selected_date}"


if __name__ == '__main__':
    app.run(debug=True)