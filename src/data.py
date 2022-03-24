import ast
import os
from datetime import timedelta

import pandas as pd
import requests
from dateutil.parser import parse
from tqdm import tqdm

from src import BASEDATE, DATADIR


def load_stations_metadata() -> pd.DataFrame:
    """Load the stations metadata."""
    stations_api = "https://rata.digitraffic.fi/api/v1/metadata/stations"
    df = pd.read_json(requests.get(stations_api).text)
    return df


def load_trains_last_30_days() -> pd.DataFrame:
    """Load the trains dataset for the last 30 days."""
    last_30_days = [
        (BASEDATE - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)
    ]
    # Call the endpoint for each of the departure dates we want
    data = []
    for dep_date in tqdm(last_30_days):
        day_api = f"https://rata.digitraffic.fi/api/v1/trains/{dep_date}"
        data.append(pd.read_json(requests.get(day_api).text))
    # Concatenate data from last 30 days
    df = pd.concat(data).reset_index(drop=True)
    return df


def prep_trains_last_30_days(df) -> pd.DataFrame:
    """Prepare the trains dataset for the last 30 days."""

    def _compute_duration(rows):
        if (
            rows[0].get("actualTime") is not None
            and rows[-1].get("actualTime") is not None
        ):
            return parse(rows[-1]["actualTime"]) - parse(rows[0]["actualTime"])
        else:
            return parse(rows[-1]["scheduledTime"]) - parse(rows[0]["scheduledTime"])

    def _extract_route_embedding(rows):
        non_consecutive_rows = [
            j["stationShortCode"]
            for i, j in enumerate(rows)
            if j["stationShortCode"] != rows[i - 1]["stationShortCode"] or i == 0
        ]
        return "-".join(non_consecutive_rows)

    # Feature engineering
    df["numberStopedStations"] = (
        df["timeTableRows"]
        .apply(
            lambda x: (len(list(filter(lambda y: y["trainStopping"], x))) - 2) / 2 + 2
        )
        .astype(int)
    )
    df["trainDuration"] = df["timeTableRows"].apply(_compute_duration)
    df["routeEmbedding"] = df["timeTableRows"].apply(_extract_route_embedding)
    return df


def load_cleaned_trains() -> pd.DataFrame:
    """Load the cleaned trains dataset."""
    datafile = os.path.join(DATADIR, "trains_cleaned.csv")
    # Load datafile form disk if it exists else create it
    if os.path.isfile(datafile):
        # Specify how to load each column
        converter = {"timeTableRows": lambda x: ast.literal_eval(x)}
        df = pd.read_csv(
            datafile,
            converters=converter,
            parse_dates=["timetableAcceptanceDate"],
        )
        df["trainDuration"] = pd.to_timedelta(df["trainDuration"])
        return df
    else:
        df = load_trains_last_30_days()
        df = prep_trains_last_30_days(df)
        # Save df as csv
        df.to_csv(datafile, index=False)
        return df
