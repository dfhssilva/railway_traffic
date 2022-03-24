import networkx as nx
import pandas as pd

from src.data import load_cleaned_trains, load_stations_metadata


def create_nodes(df):
    """Create the network nodes for the cleaned trains DataFrame."""

    def _group_nodes(group):
        assert (
            len(group["countryCode"].unique()) == 1
        ), "station exists in multiple countries"
        counts = group.shape[0]
        type_freq = group["type"].value_counts(normalize=True).to_dict()
        stop_freq = (group["trainStopping"] == True).sum() / counts
        commercial_freq = (group["commercialStop"] == True).sum() / counts
        cancelled_freq = (group["cancelled"] == True).sum() / counts
        avg_diff = group["differenceInMinutes"].mean()
        final_dict = {
            "countryCode": group["countryCode"].unique()[0],
            "counts": counts,
            "stopFreq": stop_freq,
            "commercialFreq": commercial_freq,
            "cancelledFreq": cancelled_freq,
            "avgDiff": avg_diff,
            "typeArrivalFreq": type_freq.get("ARRIVAL", 0),
            "typeDepartureFreq": type_freq.get("DEPARTURE", 0),
        }
        return pd.Series(final_dict)

    # Get timeTableRows as a DataFrame
    df = pd.DataFrame(
        df["timeTableRows"].explode().reset_index(drop=True).tolist()
    ).drop(
        columns=[
            "stationUICCode",
            "scheduledTime",
            "actualTime",
            "trainReady",
            "liveEstimateTime",
            "estimateSource",
            "causes",
        ]
    )

    # Extract nodes and respective attributes
    df = df.groupby("stationShortCode").apply(_group_nodes)

    # Integrate stations metadata
    stations_metadata = (
        load_stations_metadata()
        .drop(columns=["stationUICCode", "countryCode"])
        .set_index("stationShortCode", drop=True)
    )
    df = pd.merge(df, stations_metadata, how="left", left_index=True, right_index=True)

    nodes = list(df.to_dict(orient="index").items())
    return nodes


def create_edges(df):
    """Create the network edges for the cleaned trains DataFrame."""

    def _extract_edges(row):
        route = row.split("-")
        return pd.DataFrame(
            [
                [station, route[i + 1]]
                for i, station in enumerate(route)
                if i != len(route) - 1
            ]
        )

    # Extract unique edges from routeEmbedding
    edges = (
        pd.concat(df["routeEmbedding"].apply(_extract_edges).tolist())
        .drop_duplicates()
        .values
    )
    return edges


def create_network(df=None):
    """Create the railway network model for the cleaned trains DataFrame."""
    if df is None:
        # Load cleaned data
        print("------------ Loading data ------------")
        df = load_cleaned_trains()

    # Create nodes
    print("------------ Creating nodes ------------")
    nodes = create_nodes(df)

    # Create edges
    print("------------ Creating edges ------------")
    edges = create_edges(df)

    # Create graph object and populate it
    print("------------ Creating Graph object ------------")
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    return G
