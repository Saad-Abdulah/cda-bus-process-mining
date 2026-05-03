"""
Task 3a: Interactive process map (all routes) in Streamlit.

Run from project root:
  streamlit run code/task3/app_3a.py

Or:
  cd /path/to/project && /path/to/venv/bin/streamlit run code/task3/app_3a.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from pyvis.network import Network

# Project root: .../project
ROOT = Path(__file__).resolve().parents[2]
TASK3_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = ROOT / "data" / "output" / "routes.csv"

if str(TASK3_DIR) not in sys.path:
    sys.path.insert(0, str(TASK3_DIR))

from graph_builder import format_duration_hms, load_transition_edges  # noqa: E402


def _build_pyvis_html(
    edges_df: pd.DataFrame,
    physics: bool,
    spring_length: int,
    edge_smoothing: bool,
) -> str:
    net = Network(
        height="720px",
        width="100%",
        bgcolor="#0e1117",
        font_color="#e6e6e6",
        directed=True,
    )
    net.set_options(
        json.dumps(
            {
                "physics": {
                    "enabled": physics,
                    "solver": "barnesHut",
                    "barnesHut": {
                        "gravitationalConstant": -18000,
                        "centralGravity": 0.35,
                        "springLength": spring_length,
                        "springConstant": 0.06,
                        "damping": 0.5,
                    },
                    "minVelocity": 0.75,
                },
                "interaction": {
                    "hover": True,
                    "tooltipDelay": 120,
                    "navigationButtons": True,
                    "keyboard": {"enabled": True},
                },
                "edges": {
                    "arrows": {"to": {"enabled": True, "scaleFactor": 0.65}},
                    "smooth": {"enabled": edge_smoothing, "type": "dynamic"},
                    "font": {"size": 11, "align": "middle", "strokeWidth": 0},
                    "scaling": {"min": 1, "max": 10},
                },
                "nodes": {
                    "font": {"size": 13},
                    "borderWidth": 1,
                    "borderWidthSelected": 2,
                },
            }
        )
    )

    nodes = set(edges_df["source"]) | set(edges_df["target"])
    deg: dict[str, int] = {}
    for _, r in edges_df.iterrows():
        deg[r["source"]] = deg.get(r["source"], 0) + 1
        deg[r["target"]] = deg.get(r["target"], 0) + 1

    max_deg = max(deg.values()) if deg else 1
    for name in sorted(nodes):
        d = deg.get(name, 1)
        size = 10 + 22 * (d / max_deg)
        short = name if len(name) <= 28 else name[:25] + "..."
        net.add_node(
            name,
            label=short,
            title=name,
            size=size,
            color={"background": "#2b4c7e", "border": "#8daed8", "highlight": {"background": "#3d6bab"}},
        )

    for _, row in edges_df.iterrows():
        w = max(1.0, min(8.0, float(row["trip_count"]) ** 0.5))
        secs = float(row["mean_seconds"])
        dur = format_duration_hms(secs)
        lbl = f"{dur}\n(n={int(row['trip_count'])})"
        net.add_edge(
            row["source"],
            row["target"],
            title=f"{row['source']} → {row['target']}\n{dur} (mean)\nTrips: {int(row['trip_count'])}",
            label=lbl,
            value=w,
            color={"color": "#6b8cae", "highlight": "#a8c0ff"},
        )

    return net.generate_html()


def main() -> None:
    st.set_page_config(
        page_title="CDA Bus Process Map (3a)",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("CDA Bus Network Process Map")
    st.caption(
        "Task 3a: directed graph of stops (nodes) and transitions (edges). "
        "Edge labels show mean transition time between consecutive stops (from departure timestamps)."
    )

    with st.sidebar:
        st.header("Data")
        csv_path = st.text_input("Path to routes.csv", value=str(DEFAULT_CSV))
        load_btn = st.button("Load graph", type="primary")

        st.header("Clarity (large graphs)")
        min_trips = st.slider(
            "Hide edges with fewer than this many trip crossings",
            min_value=1,
            max_value=50,
            value=1,
            help="Higher values remove rare edges so the map stays readable. "
            "Use 1 to include every observed transition.",
        )
        max_edges = st.slider(
            "Max edges to draw (by trip count)",
            min_value=200,
            max_value=8000,
            value=3500,
            step=100,
            help="Caps the number of edges for browser performance. Highest-frequency edges are kept.",
        )

        st.header("Layout")
        physics = st.toggle("Physics simulation", value=True)
        spring_length = st.slider("Spring length", 80, 400, 200, 10)
        edge_smooth = st.toggle("Smooth edges", value=True)

        st.markdown("---")
        st.caption(
            "Tip: disable physics after dragging nodes to a good layout, "
            "or raise min trips / lower max edges if the view is dense."
        )

    path = Path(csv_path).expanduser()
    if not path.is_file():
        st.error(f"File not found: {path}")
        st.stop()

    path_str = str(path.resolve())
    path_changed = st.session_state.get("loaded_csv_path") != path_str
    need_load = (
        load_btn
        or "edges_df" not in st.session_state
        or path_changed
    )
    if need_load:
        with st.spinner("Building transition graph from event log..."):
            edges_df, meta = load_transition_edges(path)
            st.session_state["edges_df"] = edges_df
            st.session_state["meta"] = meta
            st.session_state["loaded_csv_path"] = path_str

    edges_df = st.session_state["edges_df"].copy()
    meta = st.session_state["meta"]

    filtered = edges_df[edges_df["trip_count"] >= min_trips].copy()
    filtered = filtered.sort_values("trip_count", ascending=False).head(max_edges)

    nodes_in_view = len(set(filtered["source"]) | set(filtered["target"])) if len(filtered) else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Traces (trips)", f"{meta['num_trips']:,}")
    c2.metric("Events (rows)", f"{meta['num_events']:,}")
    c3.metric("Stops in view", f"{nodes_in_view:,}", help="Unique stop names in the current graph view")
    c4.metric("Edges in view", f"{len(filtered):,}", help="Directed transitions after filters")

    if len(filtered) < len(edges_df):
        st.info(
            f"Showing {len(filtered)} of {len(edges_df)} edges after filters "
            f"(min_trips={min_trips}, max_edges={max_edges})."
        )

    if len(filtered) == 0:
        st.warning("No edges match the current filters. Lower min trips or increase max edges.")
        st.stop()

    html_pyvis = _build_pyvis_html(filtered, physics, spring_length, edge_smooth)
    st.components.v1.html(html_pyvis, height=740, scrolling=False)

    with st.expander("Export edge table (current view)"):
        st.dataframe(
            filtered[
                ["source", "target", "mean_seconds", "trip_count", "label"]
            ].rename(columns={"mean_seconds": "mean_seconds"}),
            use_container_width=True,
            height=260,
        )


if __name__ == "__main__":
    main()
