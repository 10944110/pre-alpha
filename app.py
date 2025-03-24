import dash
import dash_bootstrap_components as dbc
from layout.dashboard import dashboard_layout
from callbacks.index import register_callbacks

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css"
    ]
)

app.layout = dashboard_layout
register_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True)