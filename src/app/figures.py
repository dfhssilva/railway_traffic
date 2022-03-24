import plotly.express as px


def plot_scatter_mapbox(
    data,
    color="community",
    size="absAvgDiff",
):
    """Plot scatter_mapbox of Finland railroad."""
    default_hover_data = {
        "stationShortCode": True,
        "latitude": False,
        "longitude": False,
    }
    # Update hover data in special cases
    if color == "absAvgDiff" or size == "absAvgDiff":
        default_hover_data.update({"absAvgDiff": False, "avgDiff": True})
    # Define figure
    fig = px.scatter_mapbox(
        data,
        lat="latitude",
        lon="longitude",
        hover_name="stationName",
        color=color,
        color_discrete_sequence=px.colors.qualitative.Dark24,
        hover_data=default_hover_data,
        size=size,
        zoom=4.8,
        center={"lat": 63.5, "lon": 25.5},
        width=1250,
        height=900,
        mapbox_style="open-street-map",
    )
    return fig
