from dash import dcc, html
from dash.dependencies import Input, Output
from jupyter_dash import JupyterDash

from src.app.figures import plot_scatter_mapbox

options = [
    {"value": "counts", "label": "Activity"},
    {"value": "stopFreq", "label": "Stopping"},
    {"value": "commercialFreq", "label": "Commercial frequency"},
    {"value": "cancelledFreq", "label": "Cancellation frequency"},
    {"value": "absAvgDiff", "label": "Average time difference"},
    {"value": "community", "label": "Community"},
    {"value": "typeArrivalFreq", "label": "Arrival frequency"},
    {"value": "typeDepartureFreq", "label": "Departure frequency"},
    {"value": "passagerTraffic", "label": "Passenger Traffic"},
    {"value": "type", "label": "Station type"},
]


def create_dash_app(df):
    """Create the network visualizer app given the DataFrame."""

    # ------------------------------------- Instantiate app -------------------------------------
    app = JupyterDash(__name__, assets_folder="assets")
    server = app.server

    # ------------------------------------- Define app layout -------------------------------------
    app.layout = html.Div(
        [
            html.Div(
                className="ten columns",
                children=[
                    dcc.Graph(
                        id="scatter_mapbox",
                        figure=plot_scatter_mapbox(df),
                    )
                ],
            ),
            html.Div(
                className="two columns",
                children=[
                    dcc.Dropdown(
                        id="color-filter",
                        options=options,
                        placeholder="Scatter Color",
                    ),
                    dcc.Dropdown(
                        id="size-filter",
                        options=options,
                        placeholder="Scatter Size",
                    ),
                ],
            ),
        ]
    )

    # ------------------------------------- Define callbacks -------------------------------------

    @app.callback(
        Output("scatter_mapbox", "figure"),
        Input("color-filter", "value"),
        Input("size-filter", "value"),
    )
    def update_graph(selected_color, selected_size):
        """Update the scatter_mapbox element by changing color-filter and size-filter."""
        return plot_scatter_mapbox(df, color=selected_color, size=selected_size)

    return app
