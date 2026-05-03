"""
Build a directed transition graph from routes.csv (same cases as the XES log).

Each trip is a trace; consecutive stops yield an edge. Transition duration is
departure(next) - departure(current), matching the project example style.
Aggregates multiple trips on the same edge using the mean duration.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


BASE_DATE = datetime(2000, 1, 1)


def _parse_clock(s: str) -> datetime:
    parts = str(s).strip().split(":")
    h, m, sec = int(parts[0]), int(parts[1]), int(parts[2])
    return BASE_DATE.replace(hour=h, minute=m, second=sec)


def format_duration_hms(total_seconds: float) -> str:
    if total_seconds < 0:
        total_seconds = 0.0
    sec = int(round(total_seconds))
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h} hr {m} min {s} sec"
    if m > 0:
        return f"{m} min {s} sec"
    return f"{s} sec"


def load_transition_edges(csv_path: Path) -> tuple[pd.DataFrame, dict]:
    """
    Returns:
      edges_df: columns source, target, mean_seconds, trip_count, label
      meta: dict with stats
    """
    df = pd.read_csv(csv_path)
    required = {
        "route_id",
        "direction",
        "trip_id",
        "stop_sequence",
        "stop_name",
        "departure_time",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"routes.csv missing columns: {sorted(missing)}")

    df = df.sort_values(["route_id", "direction", "trip_id", "stop_sequence"])
    records: list[tuple[str, str, float]] = []

    for (_, _, _), group in df.groupby(["route_id", "direction", "trip_id"], sort=False):
        g = group.sort_values("stop_sequence")
        prev_dep = None
        prev_name = None
        for row in g.itertuples(index=False):
            name = str(row.stop_name).strip()
            dep = _parse_clock(row.departure_time)
            if prev_dep is not None and prev_name is not None:
                delta = (dep - prev_dep).total_seconds()
                records.append((prev_name, name, float(delta)))
            prev_dep = dep
            prev_name = name

    if not records:
        raise ValueError("No transitions extracted from CSV.")

    edge_df = pd.DataFrame(records, columns=["source", "target", "seconds"])
    agg = (
        edge_df.groupby(["source", "target"], as_index=False)
        .agg(mean_seconds=("seconds", "mean"), trip_count=("seconds", "count"))
    )

    def edge_label(row: pd.Series) -> str:
        dur = format_duration_hms(row["mean_seconds"])
        return f"{row['source']} → {row['target']}\n{dur}"

    agg["label"] = agg.apply(edge_label, axis=1)

    meta = {
        "num_nodes": len(set(agg["source"]) | set(agg["target"])),
        "num_edges": len(agg),
        "num_trips": df.groupby(["route_id", "direction", "trip_id"]).ngroups,
        "num_events": len(df),
    }
    return agg, meta
