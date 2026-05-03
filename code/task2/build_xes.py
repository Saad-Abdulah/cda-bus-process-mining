from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from xml.etree.ElementTree import Element, ElementTree, SubElement

import pandas as pd


def make_iso(dt: datetime) -> str:
    # UTC timestamp, XES-compatible ISO-8601 with timezone.
    return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")


def parse_clock_to_datetime(clock: str, base_date: datetime) -> datetime:
    h, m, s = [int(x) for x in str(clock).split(":")]
    return base_date.replace(hour=h, minute=m, second=s)


def build_xes(routes_df: pd.DataFrame) -> Element:
    log = Element("log")
    log.set("xes.version", "1.0")
    log.set("xes.features", "nested-attributes")
    log.set("openxes.version", "1.0RC7")
    log.set("xmlns", "http://www.xes-standard.org/")

    SubElement(
        log,
        "extension",
        name="Concept",
        prefix="concept",
        uri="http://www.xes-standard.org/concept.xesext",
    )
    SubElement(
        log,
        "extension",
        name="Time",
        prefix="time",
        uri="http://www.xes-standard.org/time.xesext",
    )
    SubElement(
        log,
        "extension",
        name="Lifecycle",
        prefix="lifecycle",
        uri="http://www.xes-standard.org/lifecycle.xesext",
    )
    SubElement(log, "classifier", name="Activity", keys="concept:name")
    SubElement(log, "classifier", name="Activity+Lifecycle", keys="concept:name lifecycle:transition")
    global_trace = SubElement(log, "global", scope="trace")
    SubElement(global_trace, "string", key="concept:name", value="UNDEFINED_TRACE")
    global_event = SubElement(log, "global", scope="event")
    SubElement(global_event, "string", key="concept:name", value="UNDEFINED_EVENT")
    SubElement(global_event, "string", key="lifecycle:transition", value="complete")
    SubElement(global_event, "date", key="time:timestamp", value="1970-01-01T00:00:00+00:00")

    SubElement(log, "string", key="concept:name", value="CDA Bus Routes Event Log")
    SubElement(log, "string", key="source", value="routes.csv")
    SubElement(log, "string", key="lifecycle:model", value="standard")

    # Build per-trip traces when trip-level columns are present; fallback to route-level.
    if "trip_id" in routes_df.columns and "direction" in routes_df.columns:
        routes_df["case_id"] = (
            routes_df["route_id"].astype(str)
            + "_"
            + routes_df["direction"].astype(str)
            + "_"
            + routes_df["trip_id"].astype(str)
        )
    else:
        routes_df["case_id"] = routes_df["route_id"].astype(str)

    routes_df = routes_df.sort_values(["case_id", "stop_sequence"])
    base_date = datetime(2026, 1, 1, 0, 0, 0)

    for case_id, group in routes_df.groupby("case_id", sort=True):
        trace = SubElement(log, "trace")
        SubElement(trace, "string", key="concept:name", value=f"case_{case_id}")
        route_id = str(group["route_id"].iloc[0])
        SubElement(trace, "string", key="route_id", value=str(route_id))
        route_name = str(group["route_name"].iloc[0]) if "route_name" in group.columns else f"Route {route_id}"
        SubElement(trace, "string", key="route_name", value=route_name)
        if "direction" in group.columns:
            SubElement(trace, "string", key="direction", value=str(group["direction"].iloc[0]))
        if "trip_id" in group.columns:
            SubElement(trace, "string", key="trip_id", value=str(group["trip_id"].iloc[0]))

        for row in group.itertuples(index=False):
            event = SubElement(trace, "event")
            SubElement(event, "string", key="concept:name", value=str(row.stop_name))
            SubElement(event, "string", key="lifecycle:transition", value="complete")
            SubElement(event, "string", key="route_id", value=str(row.route_id))
            SubElement(event, "int", key="stop_sequence", value=str(int(row.stop_sequence)))
            if hasattr(row, "arrival_time"):
                SubElement(event, "string", key="arrival_time", value=str(row.arrival_time))
            if hasattr(row, "departure_time"):
                SubElement(event, "string", key="departure_time", value=str(row.departure_time))
            dep = getattr(row, "departure_time", None) or getattr(row, "scheduled_time", None)
            arr = getattr(row, "arrival_time", None)
            clock = dep if isinstance(dep, str) and dep else arr
            if not isinstance(clock, str) or not clock:
                # Strict fallback only when no time columns are available.
                clock = "00:00:00"
            event_time = parse_clock_to_datetime(clock, base_date)
            SubElement(event, "date", key="time:timestamp", value=make_iso(event_time))

    return log


def main() -> None:
    parser = argparse.ArgumentParser(description="Build merged XES from routes.csv")
    parser.add_argument("--input-csv", type=Path, required=True, help="Input routes.csv")
    parser.add_argument("--output-xes", type=Path, required=True, help="Output merged_routes.xes")
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    required = {"route_id", "stop_sequence", "stop_name"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Missing required columns: {sorted(missing)}")

    xes_root = build_xes(df)
    args.output_xes.parent.mkdir(parents=True, exist_ok=True)
    ElementTree(xes_root).write(args.output_xes, encoding="utf-8", xml_declaration=True)
    print(f"Wrote XES to {args.output_xes}")


if __name__ == "__main__":
    main()
