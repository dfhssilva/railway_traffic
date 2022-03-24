import networkx as nx
import pandas as pd
from dateutil.parser import parse

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
    """Create the weighted network edges for the cleaned trains DataFrame."""

    def _extract_edge_rows(rows):
        def _sort_alphabetically(station1, station2):
            return sorted([station1, station2], key=str.lower)

        edges = []
        for i, j in enumerate(rows):
            # We want edges to represent DEPARTURE->DEPARTURE (connect different stations and include time spent on station)
            if j["type"] == "ARRIVAL":
                continue
            # In the last DEPARTURE, compute duration to next ARRIVAL and not to next DEPARTURE
            if i == len(rows) - 2:
                step = 1
            else:
                step = 2
            # Use actualTime if available to be more precise
            if (
                j.get("actualTime") is not None
                and rows[i + step].get("actualTime") is not None
            ):
                duration = parse(rows[i + step]["actualTime"]) - parse(j["actualTime"])
            else:
                duration = parse(rows[i + step]["scheduledTime"]) - parse(
                    j["scheduledTime"]
                )
            # Sort stations alphabetically so the direction doesn't interfere with the edgeCode
            left_station, right_station = _sort_alphabetically(
                j["stationShortCode"], rows[i + step]["stationShortCode"]
            )
            edge = {
                "edgeCode": f"{left_station}-{right_station}",
                "avgDuration": int(duration.total_seconds() / 60),
            }
            edges.append(edge)
        return edges

    # Create edge_rows
    edges = df["timeTableRows"].apply(_extract_edge_rows)
    # Convert edge_rows to DataFrame
    edges = pd.DataFrame(edges.explode().reset_index(drop=True).tolist())
    # Group by edgeCode and get average duration
    edges = edges.groupby("edgeCode").mean()
    # Assemble edges in expected format by networkx
    edges = list(
        map(lambda x: (*x[0].split("-"), x[1]), edges.to_dict(orient="index").items())
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
