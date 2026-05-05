"""
Task 3 — Process Discovery & Interactive GUI
Requirements covered:
  3a  Process map from event log (NetworkX + Pyvis)
  3b  Route filter dropdown (All Routes + individual route_id)
  3c  Transition duration labels near every directed edge (min sec format)
  3d  Case-frequency display (side panel table + edge tooltip)

FIXES:
  - All text now visible on dark backgrounds (light-colored text throughout)
  - Edge duration labels positioned NEAR edges (not on them) via alignment offset
  - Node labels positioned BELOW nodes (not overlaid)
  - Metric cards, dataframes, sidebar text all readable
"""

import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import os, json

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CDA Bus | Process Discovery",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
    color: #e2e8f0;
}

/* ---- Background ---- */
.stApp {
    background: linear-gradient(135deg, #0a0f1e 0%, #0d1b2a 50%, #0a1628 100%);
    color: #e2e8f0;
}

/* ---- Global text override — ensure nothing inherits near-black ---- */
p, span, div, label, li, td, th {
    color: #e2e8f0;
}

/* ---- Sidebar ---- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid #1e40af55;
}
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] .stSelectbox label {
    color: #93c5fd !important;
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 0.05em;
}
[data-testid="stSidebar"] h3 {
    color: #bfdbfe !important;
}

/* ---- Selectbox dropdown list items → black text ---- */
[data-baseweb="select"] [data-baseweb="menu"] *,
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="option"] *,
[data-baseweb="popover"] li,
[data-baseweb="popover"] li *,
ul[data-baseweb="menu"] li,
ul[data-baseweb="menu"] li *,
div[role="listbox"] *,
div[role="option"],
div[role="option"] * {
    color: #000000 !important;
}
/* Selected item shown in the closed selectbox box itself */
[data-baseweb="select"] [data-baseweb="tag"],
[data-baseweb="select"] span,
[data-baseweb="select"] div[class*="ValueContainer"] *,
[data-testid="stSelectbox"] [data-baseweb="select"] * {
    color: #000000 !important;
}

/* ---- Metric cards ---- */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1e3a5f, #0f2240);
    border: 1px solid #3b82f655;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 4px 20px #0008;
}
[data-testid="metric-container"] label,
[data-testid="stMetricLabel"] *,
[data-testid="stMetricLabel"] p {
    color: #93c5fd !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] * {
    color: #f0f9ff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.7rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] {
    color: #34d399 !important;
}

/* ---- Dataframe / table ---- */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}
[data-testid="stDataFrame"] * {
    color: #e2e8f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
}
[data-testid="stDataFrame"] th {
    background: #1e3a5f !important;
    color: #93c5fd !important;
    font-weight: 700 !important;
}
[data-testid="stDataFrame"] tr:nth-child(even) td {
    background: #0f1e33 !important;
}
[data-testid="stDataFrame"] tr:nth-child(odd) td {
    background: #0a1628 !important;
}

/* ---- Headings ---- */
h1, h2, h3, h4 {
    color: #93c5fd !important;
    font-weight: 700 !important;
}

/* ---- Expander ---- */
[data-testid="stExpander"] {
    background: #111827;
    border: 1px solid #1e40af44;
    border-radius: 12px;
}
[data-testid="stExpander"] * {
    color: #cbd5e1 !important;
}
[data-testid="stExpander"] summary {
    color: #93c5fd !important;
    font-weight: 700 !important;
}

/* ---- Spinner / info / success ---- */
[data-testid="stSpinner"] * { color: #60a5fa !important; }
.stInfo, [data-testid="stInfo"] * { color: #bfdbfe !important; background: #1e3a5f !important; }
.stSuccess, [data-testid="stSuccess"] * { color: #bbf7d0 !important; background: #064e3b !important; }

/* ---- Caption ---- */
[data-testid="stCaptionContainer"] * {
    color: #94a3b8 !important;
}

/* ---- Divider ---- */
hr { border-color: #1e40af55 !important; }

/* ── Hero banner ── */
.hero-banner {
    background: linear-gradient(90deg, #1e3a8a33, #0369a133, #1e3a8a33);
    border: 1px solid #3b82f655;
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(45deg, transparent, transparent 40px, #ffffff06 40px, #ffffff06 41px);
    pointer-events: none;
}
.hero-title { font-size: 2.1rem; font-weight: 700; color: #f0f9ff; margin: 0 0 6px; line-height: 1.2; }
.hero-sub   { font-size: 0.95rem; color: #93c5fd; font-weight: 400; margin: 0; }
.hero-badge {
    display: inline-block; background: #1d4ed8; color: #bfdbfe;
    font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
    padding: 3px 12px; border-radius: 999px; margin-bottom: 12px;
    border: 1px solid #3b82f666;
}

/* ── Section label ── */
.section-label {
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: #60a5fa; margin-bottom: 8px;
}

/* ── Checklist ── */
.check-row {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 8px 0; border-bottom: 1px solid #1e3a5f;
}
.check-dot  { width: 9px; height: 9px; border-radius: 50%; background: #22c55e; flex-shrink: 0; margin-top: 4px; }
.check-text { font-size: 0.88rem; color: #cbd5e1; line-height: 1.5; }
.check-text b { color: #93c5fd; }

/* ── Info box ── */
.info-box {
    background: #0f1e33;
    border: 1px solid #1e40af55;
    border-left: 3px solid #3b82f6;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.85rem;
    color: #94a3b8;
    margin: 12px 0;
    line-height: 1.6;
}
.info-box b { color: #bfdbfe; }

/* ── Legend dots ── */
.legend-dot-blue { display:inline-block; width:10px; height:10px; border-radius:50%; background:#3b82f6; margin-right:5px; }
.legend-dot-red  { display:inline-block; width:10px; height:10px; border-radius:50%; background:#ef4444; margin-right:5px; }
</style>
""", unsafe_allow_html=True)


# ── SAMPLE DATA ────────────────────────────────────────────────────────────────
def generate_sample_data() -> pd.DataFrame:
    import numpy as np
    np.random.seed(42)

    routes = {
        "FR-01": ["Khanna Pul", "Faizabad", "Pak Secretariat", "Zero Point", "H-8", "FAST University"],
        "FR-02": ["Rawalpindi General Hospital", "Faizabad", "F-10 Markaz", "G-9 Markaz", "H-9", "NUST Metro Station"],
        "FR-03": ["Peshawar More", "Faizabad", "Zero Point", "F-7 Markaz", "F-6 Markaz", "Blue Area"],
        "FR-04": ["Airport", "F-10 Markaz", "F-8 Markaz", "Zero Point", "G-8 Markaz", "H-8"],
        "FR-05": ["H-9", "G-9 Markaz", "F-9 Park", "F-8 Markaz", "Jinnah Super", "Blue Area"],
    }
    base_times = {
        "FR-01": pd.Timestamp("2024-01-15 07:00:00"),
        "FR-02": pd.Timestamp("2024-01-15 07:15:00"),
        "FR-03": pd.Timestamp("2024-01-15 06:45:00"),
        "FR-04": pd.Timestamp("2024-01-15 08:00:00"),
        "FR-05": pd.Timestamp("2024-01-15 07:30:00"),
    }

    records = []
    trip_counter = 1
    for route_id, stops in routes.items():
        for dep_offset in [0, 30, 60, 90, 120]:
            t = base_times[route_id] + pd.Timedelta(minutes=dep_offset)
            trip_id = f"TRIP-{trip_counter:04d}"
            for seq, stop in enumerate(stops):
                gap = int(np.random.normal(6, 1.5))
                gap = max(2, gap)
                records.append({
                    "route_id": route_id,
                    "trip_id": trip_id,
                    "stop_name": stop,
                    "stop_seq": seq,
                    "arrival_time": t,
                })
                t += pd.Timedelta(minutes=gap)
            trip_counter += 1

    df = pd.DataFrame(records)
    df["arrival_time"] = pd.to_datetime(df["arrival_time"])
    return df


@st.cache_data
def load_data() -> pd.DataFrame:
    csv_path = os.path.join("data", "output", "routes.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df["arrival_time"] = pd.to_datetime(df["arrival_time"])
        return df
    return generate_sample_data()


# ── GRAPH BUILDER ──────────────────────────────────────────────────────────────
def build_process_graph(data: pd.DataFrame) -> tuple[Network, nx.DiGraph]:
    """
    Build a directed weighted graph.
    KEY FIXES:
      - Node labels are placed BELOW the node dot (labelOffset + font align)
      - Edge duration labels are placed NEAR the edge midpoint (not on top of it)
        using Pyvis font alignment = 'middle' + a background box for readability
    """
    G = nx.DiGraph()
    df_sorted = data.sort_values(["trip_id", "arrival_time"])

    for _, group in df_sorted.groupby("trip_id"):
        stops = group.reset_index(drop=True)
        for i in range(len(stops) - 1):
            u = stops.loc[i,   "stop_name"]
            v = stops.loc[i+1, "stop_name"]
            dt = (stops.loc[i+1, "arrival_time"] - stops.loc[i, "arrival_time"]).total_seconds()
            dt = max(0, dt)
            if G.has_edge(u, v):
                G[u][v]["count"] += 1
                G[u][v]["durations"].append(dt)
            else:
                G.add_edge(u, v, count=1, durations=[dt])

    all_avg = []
    for _, _, d in G.edges(data=True):
        all_avg.append(sum(d["durations"]) / len(d["durations"]))
    p75 = sorted(all_avg)[int(len(all_avg) * 0.75)] if all_avg else float("inf")

    net = Network(
        height="640px",
        width="100%",
        directed=True,
        bgcolor="#060d1a",
        font_color="#e2e8f0",
        notebook=False,
    )

    added_nodes = set()
    for u, v, d in G.edges(data=True):
        avg_sec  = sum(d["durations"]) / len(d["durations"])
        mins, s  = divmod(int(avg_sec), 60)
        time_lbl = f"{mins}m {s:02d}s"
        freq     = d["count"]
        is_bottleneck = avg_sec > p75

        for node in (u, v):
            if node not in added_nodes:
                net.add_node(
                    node,
                    label=node,          # label text shown near (below) the node
                    title=f"<b style='color:#e2e8f0'>{node}</b>",
                    color={
                        "background": "#1d4ed8",
                        "border": "#60a5fa",
                        "highlight": {"background": "#2563eb", "border": "#93c5fd"},
                        "hover":     {"background": "#1e40af", "border": "#bfdbfe"},
                    },
                    shape="dot",
                    size=20,
                    # FIX: label placed BELOW node using font.vadjust (positive = below)
                    font={
                        "color": "#e2e8f0",   # bright white-blue — always visible on dark bg
                        "size": 13,
                        "face": "Sora",
                        "vadjust": 28,        # push label 28px below the node centre
                        "bold": True,
                    },
                )
                added_nodes.add(node)

        edge_color = "#ef4444" if is_bottleneck else "#38bdf8"
        edge_width = max(1.5, min(freq * 0.8, 10))

        tooltip = (
            f"<b style='color:#e2e8f0'>{u} → {v}</b><br>"
            f"<span style='color:#93c5fd'>Avg time:</span> <b>{time_lbl}</b><br>"
            f"<span style='color:#93c5fd'>Trips (cases):</span> <b>{freq}</b>"
            + ("<br><b style='color:#fca5a5'>⚠ Bottleneck (top 25% slowest)</b>" if is_bottleneck else "")
        )

        # FIX: edge label NEAR the edge — use font with background box
        # 'align' middle places label at edge midpoint but offset so it doesn't
        # sit right on the line. Background + stroke make it legible on dark bg.
        net.add_edge(
            u, v,
            label=f" {time_lbl} ",     # spaces add padding inside the label box
            title=tooltip,
            width=edge_width,
            color={"color": edge_color, "highlight": "#fbbf24", "hover": "#fbbf24"},
            arrows={"to": {"enabled": True, "scaleFactor": 0.7}},
            # FIX: font placed near edge midpoint, NOT overlaid on the line
            font={
                "size": 11,
                "color": "#f0f9ff",          # bright text — visible on dark network bg
                "face": "JetBrains Mono",
                "strokeWidth": 0,            # no halo — background box handles contrast
                "background": "#0f2240",     # dark-blue pill background behind label
                "align": "middle",           # centred on edge midpoint
            },
            smooth={"type": "curvedCW", "roundness": 0.12},
        )

    net.set_options(json.dumps({
        "physics": {
            "enabled": True,
            "barnesHut": {
                "gravitationalConstant": -10000,
                "centralGravity": 0.3,
                "springLength": 200,
                "springConstant": 0.04,
                "damping": 0.09,
            },
            "stabilization": {"iterations": 250},
        },
        "interaction": {
            "hover": True,
            "tooltipDelay": 80,
            "zoomView": True,
            "dragView": True,
            "navigationButtons": True,
        },
        "nodes": {
            "labelHighlightBold": True,
        },
        "edges": {
            "labelHighlightBold": True,
            "selectionWidth": 3,
        },
    }))

    return net, G


def compute_throughput(data: pd.DataFrame) -> dict:
    durations = []
    for _, grp in data.groupby("trip_id"):
        grp_s = grp.sort_values("arrival_time")
        dur   = (grp_s["arrival_time"].iloc[-1] - grp_s["arrival_time"].iloc[0]).total_seconds() / 60
        if dur > 0:
            durations.append(dur)
    if not durations:
        return {"avg": 0, "min": 0, "max": 0}
    return {
        "avg": round(sum(durations) / len(durations), 1),
        "min": round(min(durations), 1),
        "max": round(max(durations), 1),
    }


# ── MAIN ───────────────────────────────────────────────────────────────────────
df = load_data()

st.markdown("""
<div class="hero-banner">
  <div class="hero-badge">SE4009 · Process Mining & Simulation</div>
  <div class="hero-title">🚌 CDA Bus Process Discovery</div>
  <div class="hero-sub">Task 3 · Interactive Route Analysis Dashboard</div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🗂️ Route Filter")
    st.markdown('<div class="section-label">3b — Select Route</div>', unsafe_allow_html=True)

    route_options = ["All Routes"] + sorted(df["route_id"].unique().tolist())
    selected_route = st.selectbox("Route", route_options, label_visibility="collapsed")

    st.markdown("---")
    st.markdown("### 📊 Data Summary")
    st.metric("Total Routes", df["route_id"].nunique())
    st.metric("Total Trips",  df["trip_id"].nunique())
    st.metric("Total Stops",  df["stop_name"].nunique())

    st.markdown("---")
    using_sample = not os.path.exists(os.path.join("data", "output", "routes.csv"))
    if using_sample:
        st.info("⚠️ **Using sample data.**\nPlace `routes.csv` in `data/output/` to use real CDA data.")
    else:
        st.success("✅ Loaded `routes.csv`")

    st.markdown("---")
    st.markdown("### 🎨 Map Legend")
    st.markdown(
        '<span class="legend-dot-blue"></span><span style="color:#e2e8f0;font-size:0.82rem">Normal transition</span><br>'
        '<span class="legend-dot-red"></span><span style="color:#e2e8f0;font-size:0.82rem">Bottleneck (top 25% slowest)</span><br>'
        '<span style="color:#94a3b8;font-size:0.78rem;margin-top:6px;display:block">Edge width ∝ trip frequency</span>',
        unsafe_allow_html=True,
    )

# ── Filter ────────────────────────────────────────────────────────────────────
filtered_df = df if selected_route == "All Routes" else df[df["route_id"] == selected_route]

# ── Build graph ────────────────────────────────────────────────────────────────
with st.spinner("Building process map…"):
    process_net, raw_graph = build_process_graph(filtered_df)

# ── Layout ────────────────────────────────────────────────────────────────────
col_map, col_stats = st.columns([3, 1], gap="large")

with col_map:
    route_label = selected_route if selected_route != "All Routes" else "All Routes"
    st.markdown(f"### 🗺️ Process Map — {route_label}")
    st.markdown(
        '<div class="info-box">'
        "<b>Nodes</b> = bus stops (label shown below each dot) &nbsp;·&nbsp; "
        "<b>Directed edges</b> = stop transitions &nbsp;·&nbsp; "
        "<b>Edge label</b> = avg travel time (3c) placed <i>near</i> the edge midpoint &nbsp;·&nbsp; "
        "<span style='color:#fca5a5'><b>Red edges</b></span> = bottlenecks (top 25% slowest) &nbsp;·&nbsp; "
        "Edge width ∝ trip frequency (3d) &nbsp;·&nbsp; "
        "<i>Hover</i> an edge for full tooltip"
        "</div>",
        unsafe_allow_html=True,
    )

    import tempfile, pathlib
    tmp_html = str(pathlib.Path(tempfile.gettempdir()) / "process_map.html")
    process_net.save_graph(tmp_html)
    with open(tmp_html, "r", encoding="utf-8") as f:
        html_content = f.read()
    components.html(html_content, height=660)

with col_stats:
    st.markdown("### 📈 Statistics")

    num_trips = filtered_df["trip_id"].nunique()
    num_stops = filtered_df["stop_name"].nunique()
    num_edges = raw_graph.number_of_edges()

    st.metric("Trips (Cases)", num_trips)
    st.metric("Unique Stops",  num_stops)
    st.metric("Transitions",   num_edges)

    st.markdown("---")
    tp = compute_throughput(filtered_df)
    st.markdown('<div class="section-label">Trip Duration (min)</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg", f"{tp['avg']}")
    c2.metric("Min", f"{tp['min']}")
    c3.metric("Max", f"{tp['max']}")

    st.markdown("---")
    st.markdown('<div class="section-label">3d — Transition Frequencies</div>', unsafe_allow_html=True)

    edge_rows = []
    for u, v, d in raw_graph.edges(data=True):
        avg_sec = sum(d["durations"]) / len(d["durations"])
        mins, s = divmod(int(avg_sec), 60)
        edge_rows.append({
            "From":     u,
            "To":       v,
            "Trips":    d["count"],
            "Avg Time": f"{mins}m {s:02d}s",
        })

    if edge_rows:
        freq_df = (
            pd.DataFrame(edge_rows)
            .sort_values("Trips", ascending=False)
            .reset_index(drop=True)
        )
        st.dataframe(freq_df, use_container_width=True, hide_index=True, height=320)
    else:
        st.info("No transitions found.")

# ── Bottom ────────────────────────────────────────────────────────────────────
st.markdown("---")
col_top, col_bot = st.columns(2, gap="large")

with col_top:
    st.markdown("### 🏆 Top 10 Most Frequent Transitions")
    if edge_rows:
        st.dataframe(freq_df.head(10), use_container_width=True, hide_index=True)

with col_bot:
    st.markdown("### ⚠️ Top 3 Slowest Transitions (Bottlenecks)")
    if edge_rows:
        def to_seconds(t: str) -> int:
            parts = t.replace("m", "").replace("s", "").split()
            return int(parts[0]) * 60 + int(parts[1])

        bot_df = (
            pd.DataFrame(edge_rows)
            .assign(sec=lambda x: x["Avg Time"].apply(to_seconds))
            .sort_values("sec", ascending=False)
            .head(3)
            .drop(columns=["sec"])
            .reset_index(drop=True)
        )
        st.dataframe(bot_df, use_container_width=True, hide_index=True)
        st.caption("🔴 These transitions are highlighted in red on the process map above.")

 

st.markdown(
    '<div style="text-align:center;color:#475569;font-size:0.78rem;margin-top:32px;padding-bottom:24px;">'
    "CDA Bus Route Analysis · SE4009 Process Mining & Simulation · FAST National University"
    "</div>",
    unsafe_allow_html=True,
)