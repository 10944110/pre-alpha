from dash import html, dcc
import dash_bootstrap_components as dbc
from db.db_conn import get_data
import plotly.express as px
import pandas as pd

# 讀取資料
df = get_data()
df["車輛成本"] = pd.to_numeric(df["車輛成本"], errors="coerce")
df["人力成本"] = pd.to_numeric(df["人力成本"], errors="coerce")
df["總成本"] = df["車輛成本"].fillna(0) + df["人力成本"].fillna(0)
operation_date = df["作業日期"].iloc[0]

dashboard_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div([
                    html.Div("宥辰", className="fs-4 fw-bold text-white text-center my-3"),
                    html.Hr(className="border-white mx-3"),
                    html.Ul([
                        html.Li([html.I(className="bi bi-bar-chart-line me-2"), "即時分析"], className="nav-item text-white px-3 py-2"),
                        html.Li([html.I(className="bi bi-clock me-2"), "還"], className="nav-item text-white px-3 py-2"),
                        html.Li([html.I(className="bi bi-person me-2"), "沒"], className="nav-item text-white px-3 py-2"),
                        html.Li([html.I(className="bi bi-file-earmark-text me-2"), "想"], className="nav-item text-white px-3 py-2"),
                        html.Li([html.I(className="bi bi-display me-2"), "到"], className="nav-item text-white px-3 py-2"),
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
            dbc.Row([
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
                dbc.Col([
                    html.H6(id="selected-date-display", className="text-end mb-0")
                ], width=4, className="d-flex align-items-center justify-content-end")
            ], className="my-3"),
            html.Div([
                dcc.Graph(id="time-series-chart", figure={})
            ], id="main-content")
        ], width=10, style={"marginLeft": "220px"})
    ]),

    dcc.Store(id="clickData-store"),

    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
        dbc.ModalBody(id="modal-body"),
        dbc.ModalFooter(dbc.Button("關閉", id="close-modal", className="ms-auto", n_clicks=0))
    ], id="detail-modal", is_open=False, size="lg")

], fluid=True)
