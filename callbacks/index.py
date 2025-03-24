from dash import Input, Output, State, callback_context, dash_table, html, dcc
import dash_bootstrap_components as dbc
from db.db_conn import get_data, get_alcohol_data
import pandas as pd
import plotly.express as px

def register_callbacks(app):
    @app.callback(
        Output("main-content", "children"),
        Output("selected-date-display", "children"),
        Output("clickData-store", "data"),
        Input("submit-button", "n_clicks"),
        State("date-dropdown", "value")
    )
    def update_dashboard(n_clicks, selected_date):
        if not selected_date:
            return html.Div("請選擇日期"), "", {}

        df = get_data()
        df_filtered = df[df["作業日期"] == selected_date]
        df_filtered = df_filtered[~df_filtered["車牌"].astype(str).str.contains("總計", na=False)]

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
        時段統計 = pd.merge(出車統計, 回車統計, left_on="出車時段", right_on="回車時段", how="outer")
        時段統計["時段"] = 時段統計["出車時段"].combine_first(時段統計["回車時段"])
        時段統計 = 時段統計[["時段", "出車數量", "回車數量"]].fillna(0).sort_values(by="時段")

        df_store = {
            "selected_date": selected_date,
            "出車數據": df_filtered[["車牌", "司機", "出車時間", "出車時段"]].to_dict("records"),
            "回車數據": df_filtered[["車牌", "司機", "回車時間", "回車時段"]].to_dict("records"),
        }

        total_departures = df_filtered.shape[0]
        total_mileage = df_filtered["行駛里程"].sum()
        total_carbon = df_filtered["碳排放"].sum()
        total_etc = df_filtered["ETC費用"].sum()

        df_filtered = df_filtered.copy()
        df_filtered["成本效益比"] = (df_filtered["行駛里程"] / df_filtered["ETC費用"]).astype(float)
        df_filtered["成本效益比"] = df_filtered["成本效益比"].replace([float("inf"), -float("inf")], 0).fillna(0)
        df_sorted = df_filtered.sort_values(by="成本效益比", ascending=False)

        fig_line = px.line(時段統計, x="時段", y=["出車數量", "回車數量"], markers=True, labels={"value": "車輛數", "variable": "類型"}, height=200)
        fig_line.update_layout(margin=dict(l=30, r=30, t=30, b=30))

        df_alcohol = get_alcohol_data()
        df_alcohol["時間"] = pd.to_datetime(df_alcohol["時間"]).dt.date
        selected_date_obj = pd.to_datetime(selected_date).date()
        df_alcohol_filtered = df_alcohol[df_alcohol["時間"] == selected_date_obj]
        df_alcohol_filtered["是否通過"] = df_alcohol_filtered["酒測值"] < df_alcohol_filtered["臨界值"]
        pass_count = df_alcohol_filtered["是否通過"].sum()
        fail_count = len(df_alcohol_filtered) - pass_count
        pass_rate = round(pass_count / (pass_count + fail_count) * 100, 1) if (pass_count + fail_count) > 0 else 0

        fig_alcohol = px.pie(names=["通過", "未通過"], values=[pass_count, fail_count], hole=0.6, color_discrete_sequence=["#50e3e6", "#dddddd"])
        fig_alcohol.update_traces(textinfo='none', hoverinfo='label+percent', showlegend=False)
        fig_alcohol.update_layout(annotations=[{'text': f"{pass_rate:.0f}%", 'font': {'size': 32}, 'showarrow': False}], margin=dict(l=0, r=0, t=5, b=0), height=200)
        
        fig = px.bar(df_sorted, x="車牌", y="成本效益比", title=f"{selected_date} 成本效益比(行駛里程/總成本)", color="成本效益比", height=350)

        return html.Div([
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardBody([html.H6("總出車數量", className="text-muted"), html.H3(f"{total_departures} 輛", className="text-success")])]), width=3),
                dbc.Col(dbc.Card([dbc.CardBody([html.H6("總行駛里程", className="text-muted"), html.H3(f"{total_mileage:.1f} km", className="text-success")])]), width=3),
                dbc.Col(dbc.Card([dbc.CardBody([html.H6("總碳排量", className="text-muted"), html.H3(f"{total_carbon:.1f} CO²e", className="text-success")])]), width=3),
                dbc.Col(dbc.Card([dbc.CardBody([html.H6("總成本", className="text-muted"), html.H3(f"${total_etc:.0f}", className="text-success")])]), width=3)
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("酒測通過率"), dbc.CardBody(dcc.Graph(figure=fig_alcohol))]), width=3),
                dbc.Col(dbc.Card([dbc.CardHeader("出車與回車時段"), dbc.CardBody(dcc.Graph(id="time-series-chart", figure=fig_line))]), width=9)
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("各車輛總成本比較"), dbc.CardBody(dcc.Graph(figure=fig))]), width=12)
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardHeader("詳細資料表"), dbc.CardBody(dash_table.DataTable(
                    columns=[{"name": i, "id": i} for i in ["車牌", "司機", "行駛里程", "ETC費用", "碳排放"]],
                    data=df_filtered.to_dict("records"),
                    page_size=10,
                    style_table={"overflowX": "auto"},
                    style_cell={"textAlign": "center", "fontFamily": "Arial", "padding": "8px"},
                    style_header={"backgroundColor": "lightgray", "fontWeight": "bold"}
                ))]), width=12)
            ])
        ]), f"查詢日期：{selected_date}", df_store

    @app.callback(
        Output("detail-modal", "is_open"),
        Output("modal-title", "children"),
        Output("modal-body", "children"),
        [Input("time-series-chart", "clickData"),
         Input("close-modal", "n_clicks")],
        [State("clickData-store", "data"),
         State("detail-modal", "is_open")]
    )
    def toggle_modal(clickData, close_clicks, stored_data, is_open):
        ctx = callback_context
        if not ctx.triggered:
            return False, "", ""

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "close-modal":
            return False, "", ""

        if button_id == "time-series-chart" and clickData:
            curve_number = clickData["points"][0]["curveNumber"]
            clicked_hour = clickData["points"][0]["x"]

            if curve_number == 0:
                filtered_data = [record for record in stored_data["出車數據"] if record["出車時段"] == clicked_hour]
                title = f"時段 {clicked_hour}點 - 出車詳細資料"
                columns = [{"name": i, "id": i} for i in ["車牌", "司機", "出車時間"]]
                display_data = [{k: v for k, v in record.items() if k in ["車牌", "司機", "出車時間"]} for record in filtered_data]
            else:
                filtered_data = [record for record in stored_data["回車數據"] if record["回車時段"] == clicked_hour]
                title = f"時段 {clicked_hour}點 - 回車詳細資料"
                columns = [{"name": i, "id": i} for i in ["車牌", "司機", "回車時間"]]
                display_data = [{k: v for k, v in record.items() if k in ["車牌", "司機", "回車時間"]} for record in filtered_data]

            table = dash_table.DataTable(
                columns=columns,
                data=display_data,
                page_size=10,
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "center", "fontFamily": "Arial", "padding": "8px"},
                style_header={"backgroundColor": "lightgray", "fontWeight": "bold"}
            )
            return True, title, table

        return is_open, "", ""