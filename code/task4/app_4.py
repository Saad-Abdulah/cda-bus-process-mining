"""
Task 4 — Performance & Bottleneck Analytics
SE4009 Process Mining & Simulation — FAST National University
Member 3

Sub-tasks:
  4a: Throughput Time per Trip (avg/min/max) — 5 marks
  4b: Bottleneck Detection & Visual Highlighting — 5 marks
"""

# ── imports ────────────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import os

BASE_DATE = "2000-01-01 "  # prefix for time parsing

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CDA Bus | Performance Analytics",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS (copied verbatim from app_3.py) ─────────────────────────────────
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


# ── DATA LOADING ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    csv_path = os.path.join("data", "output", "routes.csv")
    if not os.path.exists(csv_path):
        csv_path = os.path.join("..", "..", "data", "output", "routes.csv")
    if not os.path.exists(csv_path):
        st.error("routes.csv not found. Run from project root or code/task4/.")
        st.stop()

    df = pd.read_csv(csv_path)

    df["departure_dt"] = pd.to_datetime(
        BASE_DATE + df["departure_time"].astype(str),
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce",
    )
    df["arrival_dt"] = pd.to_datetime(
        BASE_DATE + df["arrival_time"].astype(str),
        format="%Y-%m-%d %H:%M:%S",
        errors="coerce",
    )

    df = df.sort_values(
        ["route_id", "direction", "trip_id", "stop_sequence"]
    ).reset_index(drop=True)

    return df


# ── TASK 4a — THROUGHPUT TIME ──────────────────────────────────────────────────
@st.cache_data
def compute_trip_throughputs(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    for trip_id, grp in df.groupby("trip_id"):
        grp = grp.sort_values("stop_sequence")
        if len(grp) < 2:
            continue
        first_row = grp.iloc[0]
        last_row = grp.iloc[-1]
        dur = (last_row["departure_dt"] - first_row["departure_dt"]).total_seconds() / 60
        if dur <= 0:
            continue
        records.append({
            "trip_id":         trip_id,
            "route_id":        first_row["route_id"],
            "direction":       first_row["direction"],
            "first_stop":      first_row["stop_name"],
            "last_stop":       last_row["stop_name"],
            "first_departure": first_row["departure_time"],
            "last_departure":  last_row["departure_time"],
            "duration_min":    round(dur, 2),
            "num_stops":       len(grp),
        })

    result = pd.DataFrame(records)
    if result.empty:
        return result
    return result.sort_values("duration_min", ascending=False).reset_index(drop=True)


def compute_throughput_summary(trip_df: pd.DataFrame, route_filter: str = "All Routes") -> dict:
    if trip_df.empty:
        return {"avg": 0, "min": 0, "max": 0,
                "slowest_trip": None, "fastest_trip": None, "count": 0}

    subset = trip_df if route_filter == "All Routes" else trip_df[trip_df["route_id"] == route_filter]
    if subset.empty:
        return {"avg": 0, "min": 0, "max": 0,
                "slowest_trip": None, "fastest_trip": None, "count": 0}

    durations = subset["duration_min"]
    return {
        "avg":          round(durations.mean(), 1),
        "min":          round(durations.min(),  1),
        "max":          round(durations.max(),  1),
        "count":        len(subset),
        "slowest_trip": subset.loc[durations.idxmax()].to_dict(),
        "fastest_trip": subset.loc[durations.idxmin()].to_dict(),
    }


def compute_per_route_summary(trip_df: pd.DataFrame) -> pd.DataFrame:
    if trip_df.empty:
        return pd.DataFrame()

    summary = (
        trip_df.groupby("route_id")["duration_min"]
        .agg(avg_min="mean", min_min="min", max_min="max", trip_count="count")
        .reset_index()
        .round({"avg_min": 1, "min_min": 1, "max_min": 1})
        .sort_values("avg_min", ascending=False)
        .reset_index(drop=True)
    )
    summary.columns = ["Route", "Avg (min)", "Min (min)", "Max (min)", "Trips"]
    return summary


def plot_throughput_histogram(trip_df: pd.DataFrame, route_filter: str = "All Routes") -> plt.Figure:
    subset = trip_df if route_filter == "All Routes" else trip_df[trip_df["route_id"] == route_filter]

    fig, ax = plt.subplots(figsize=(9, 3.5))
    fig.patch.set_facecolor("#060d1a")
    ax.set_facecolor("#0a0f1e")

    if subset.empty or len(subset) < 2:
        ax.text(0.5, 0.5, "No data", transform=ax.transAxes,
                ha="center", va="center", color="#93c5fd", fontsize=14)
    else:
        durations = subset["duration_min"]
        avg = durations.mean()
        n_bins = min(30, max(5, len(subset) // 3))

        ax.hist(durations, bins=n_bins, color="#1d4ed8",
                edgecolor="#60a5fa", linewidth=0.6, alpha=0.85)
        ax.axvline(avg, color="#fbbf24", linewidth=2, linestyle="--",
                   label=f"Avg: {avg:.1f} min")
        ax.axvline(durations.min(), color="#34d399", linewidth=1.5, linestyle=":",
                   label=f"Min: {durations.min():.1f} min")
        ax.axvline(durations.max(), color="#ef4444", linewidth=1.5, linestyle=":",
                   label=f"Max: {durations.max():.1f} min")

        ax.legend(facecolor="#0f1e33", edgecolor="#1e40af",
                  labelcolor="#e2e8f0", fontsize=9)

    ax.set_title(f"Trip Duration Distribution — {route_filter}",
                 color="#93c5fd", fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("Duration (minutes)", color="#94a3b8", fontsize=10)
    ax.set_ylabel("Number of Trips", color="#94a3b8", fontsize=10)
    ax.tick_params(colors="#94a3b8")
    for spine in ax.spines.values():
        spine.set_edgecolor("#1e40af55")

    fig.tight_layout()
    return fig


# ── TASK 4b — BOTTLENECK DETECTION ─────────────────────────────────────────────
@st.cache_data
def compute_edge_stats(df: pd.DataFrame, route_filter: str = "All Routes") -> pd.DataFrame:
    subset = df if route_filter == "All Routes" else df[df["route_id"] == route_filter]

    records = []
    for trip_id, grp in subset.groupby("trip_id"):
        grp = grp.sort_values("stop_sequence").reset_index(drop=True)
        for i in range(len(grp) - 1):
            src = grp.loc[i,   "stop_name"]
            tgt = grp.loc[i+1, "stop_name"]
            dt = (grp.loc[i+1, "departure_dt"] - grp.loc[i, "departure_dt"]).total_seconds()
            if dt >= 0:
                records.append({"source": src, "target": tgt, "seconds": dt})

    if not records:
        return pd.DataFrame()

    raw = pd.DataFrame(records)
    agg = (
        raw.groupby(["source", "target"], as_index=False)
        .agg(
            mean_sec=("seconds", "mean"),
            std_sec=("seconds", "std"),
            min_sec=("seconds", "min"),
            max_sec=("seconds", "max"),
            trip_count=("seconds", "count"),
        )
    )
    agg["std_sec"] = agg["std_sec"].fillna(0)
    agg["mean_min"] = (agg["mean_sec"] / 60).round(2)
    agg["label"] = agg["source"] + " → " + agg["target"]
    agg = agg.sort_values("mean_sec", ascending=False).reset_index(drop=True)
    return agg


def flag_bottlenecks(edge_df: pd.DataFrame,
                     threshold_pct: float = 75.0,
                     manual_threshold_min: float | None = None) -> pd.DataFrame:
    if edge_df.empty:
        return edge_df

    df = edge_df.copy()
    p_val = float(np.percentile(df["mean_sec"], threshold_pct))

    df["is_bottleneck"] = False
    df["bottleneck_reason"] = ""

    mask_pct = df["mean_sec"] > p_val
    df.loc[mask_pct, "is_bottleneck"] = True
    df.loc[mask_pct, "bottleneck_reason"] = f"Top {100 - int(threshold_pct)}% slowest"

    if manual_threshold_min is not None:
        mask_manual = df["mean_min"] > manual_threshold_min
        df.loc[mask_manual, "is_bottleneck"] = True
        df.loc[mask_manual & ~mask_pct, "bottleneck_reason"] = (
            f"Exceeds {manual_threshold_min:.1f} min threshold"
        )
        df.loc[mask_manual & mask_pct, "bottleneck_reason"] = (
            df.loc[mask_manual & mask_pct, "bottleneck_reason"]
            + f" + exceeds {manual_threshold_min:.1f} min"
        )

    return df


def fmt_sec(sec: float) -> str:
    sec = max(0, int(round(sec)))
    m, s = divmod(sec, 60)
    if m > 0:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def plot_bottleneck_bar(edge_df: pd.DataFrame, top_n: int = 10) -> plt.Figure:
    if edge_df.empty:
        fig, ax = plt.subplots(figsize=(9, 3))
        fig.patch.set_facecolor("#060d1a")
        ax.set_facecolor("#0a0f1e")
        ax.text(0.5, 0.5, "No data", transform=ax.transAxes,
                ha="center", va="center", color="#93c5fd")
        return fig

    plot_df = edge_df.head(top_n).copy()
    plot_df = plot_df.iloc[::-1].reset_index(drop=True)
    colors = ["#ef4444" if b else "#1d4ed8" for b in plot_df["is_bottleneck"]]
    labels = plot_df["label"]
    values = plot_df["mean_min"]

    fig, ax = plt.subplots(figsize=(9, max(3.5, top_n * 0.45)))
    fig.patch.set_facecolor("#060d1a")
    ax.set_facecolor("#0a0f1e")

    bars = ax.barh(labels, values, color=colors,
                   edgecolor="#1e40af55", linewidth=0.5)

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}m", va="center", ha="left",
                fontsize=8, color="#e2e8f0")

    patches = [
        mpatches.Patch(color="#ef4444", label="Bottleneck"),
        mpatches.Patch(color="#1d4ed8", label="Normal"),
    ]
    ax.legend(handles=patches, facecolor="#0f1e33",
              edgecolor="#1e40af", labelcolor="#e2e8f0", fontsize=9)

    ax.set_title(f"Top {top_n} Slowest Transitions",
                 color="#93c5fd", fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("Avg Transition Time (minutes)", color="#94a3b8", fontsize=10)
    ax.tick_params(colors="#94a3b8", labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#1e40af55")

    fig.tight_layout()
    return fig


def plot_bottleneck_heatmap(edge_df: pd.DataFrame, top_n: int = 15) -> plt.Figure:
    if edge_df.empty or len(edge_df) < 2:
        fig, ax = plt.subplots(figsize=(8, 3))
        fig.patch.set_facecolor("#060d1a")
        ax.set_facecolor("#0a0f1e")
        ax.text(0.5, 0.5, "No data", transform=ax.transAxes,
                ha="center", va="center", color="#93c5fd")
        return fig

    subset = edge_df.head(top_n)
    sources = sorted(subset["source"].unique())
    targets = sorted(subset["target"].unique())

    matrix = pd.DataFrame(np.nan, index=sources, columns=targets)
    for _, row in subset.iterrows():
        if row["source"] in sources and row["target"] in targets:
            matrix.loc[row["source"], row["target"]] = row["mean_min"]

    fig, ax = plt.subplots(figsize=(max(8, len(targets) * 0.9),
                                    max(4, len(sources) * 0.55)))
    fig.patch.set_facecolor("#060d1a")
    ax.set_facecolor("#0a0f1e")

    im = ax.imshow(
        matrix.values.astype(float),
        cmap="RdYlBu_r", aspect="auto",
        vmin=0, vmax=float(subset["mean_min"].max()),
    )

    ax.set_xticks(range(len(targets)))
    ax.set_yticks(range(len(sources)))
    ax.set_xticklabels(targets, rotation=45, ha="right",
                       color="#94a3b8", fontsize=7)
    ax.set_yticklabels(sources, color="#94a3b8", fontsize=7)

    for i, src in enumerate(sources):
        for j, tgt in enumerate(targets):
            val = matrix.loc[src, tgt]
            if not np.isnan(val):
                ax.text(j, i, f"{val:.1f}m",
                        ha="center", va="center",
                        color="white", fontsize=6, fontweight="bold")

    cbar = plt.colorbar(im, ax=ax, pad=0.01)
    cbar.set_label("Avg Time (min)", color="#94a3b8", fontsize=9)
    cbar.ax.tick_params(colors="#94a3b8")

    ax.set_title("Transition Time Heatmap (top transitions)",
                 color="#93c5fd", fontsize=11, fontweight="bold", pad=10)
    fig.tight_layout()
    return fig


# ── HERO BANNER ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
  <div class="hero-badge">SE4009 · Process Mining & Simulation</div>
  <div class="hero-title">⏱️ CDA Bus Performance Analytics</div>
  <div class="hero-sub">Task 4 · Throughput Time & Bottleneck Detection</div>
</div>
""", unsafe_allow_html=True)

# ── LOAD DATA ──────────────────────────────────────────────────────────────────
df = load_data()

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Controls")

    route_options = ["All Routes"] + sorted(df["route_id"].unique().tolist())
    selected_route = st.selectbox("Filter by Route", route_options)

    st.markdown("---")

    st.markdown("### 🎛️ Bottleneck Threshold")
    st.markdown(
        '<div class="info-box">'
        "The <b>percentile threshold</b> determines which edges are flagged "
        "as bottlenecks. At 75%, the slowest 25% of transitions are flagged.<br><br>"
        "The <b>manual threshold</b> lets you set an absolute time limit."
        "</div>",
        unsafe_allow_html=True,
    )
    pct_threshold = st.slider(
        "Percentile Threshold (%)", 50, 95, 75, 5,
        help="Edges above this percentile of avg duration are flagged as bottlenecks",
    )
    use_manual = st.checkbox("Also use manual time threshold", value=False)
    manual_threshold = None
    if use_manual:
        manual_threshold = st.slider("Manual Threshold (minutes)", 1.0, 30.0, 5.0, 0.5)

    st.markdown("---")
    st.markdown("### 📊 Dataset Info")
    st.metric("Total Routes",  df["route_id"].nunique())
    st.metric("Total Trips",   df["trip_id"].nunique())
    st.metric("Total Stops",   df["stop_name"].nunique())
    st.metric("Total Records", len(df))

# ── COMPUTE ────────────────────────────────────────────────────────────────────
trip_df = compute_trip_throughputs(df)
summary = compute_throughput_summary(trip_df, selected_route)
edge_df = compute_edge_stats(df, selected_route)
edge_df = flag_bottlenecks(edge_df, pct_threshold, manual_threshold)

n_bottlenecks = int(edge_df["is_bottleneck"].sum()) if not edge_df.empty else 0
n_total_edges = len(edge_df)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4a — THROUGHPUT TIME
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 📐 Task 4a — Throughput Time per Trip")
st.markdown(
    '<div class="info-box">'
    "Throughput time = time from <b>first stop departure</b> to "
    "<b>last stop departure</b> for each trip. "
    "Formula: T<sub>total</sub> = t<sub>last departure</sub> − "
    "t<sub>first departure</sub> (in minutes)."
    "</div>",
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Average Duration", f"{summary['avg']} min",
          help="Mean end-to-end trip time across all trips in selection")
c2.metric("Minimum Duration", f"{summary['min']} min", help="Fastest trip in the selection")
c3.metric("Maximum Duration", f"{summary['max']} min", help="Slowest trip in the selection")
c4.metric("Trip Count", f"{summary['count']}", help="Number of trips in current filter")

st.markdown("---")

col_hist, col_detail = st.columns([2, 1], gap="large")

with col_hist:
    st.markdown("### 📊 Trip Duration Distribution")
    fig_hist = plot_throughput_histogram(trip_df, selected_route)
    st.pyplot(fig_hist, use_container_width=True)
    plt.close(fig_hist)

with col_detail:
    st.markdown("### 🏆 Extreme Trips")
    slowest = summary.get("slowest_trip")
    fastest = summary.get("fastest_trip")

    if slowest:
        st.markdown(
            f'<div class="info-box">'
            f'<b style="color:#ef4444">🐢 Slowest Trip</b><br>'
            f'<b>ID:</b> {slowest["trip_id"]}<br>'
            f'<b>Route:</b> {slowest["route_id"]} ({slowest["direction"]})<br>'
            f'<b>From:</b> {slowest["first_stop"]}<br>'
            f'<b>To:</b> {slowest["last_stop"]}<br>'
            f'<b>Departure:</b> {slowest["first_departure"]} → {slowest["last_departure"]}<br>'
            f'<b>Duration:</b> {slowest["duration_min"]} min'
            f'</div>',
            unsafe_allow_html=True,
        )
    if fastest:
        st.markdown(
            f'<div class="info-box">'
            f'<b style="color:#34d399">🐇 Fastest Trip</b><br>'
            f'<b>ID:</b> {fastest["trip_id"]}<br>'
            f'<b>Route:</b> {fastest["route_id"]} ({fastest["direction"]})<br>'
            f'<b>From:</b> {fastest["first_stop"]}<br>'
            f'<b>To:</b> {fastest["last_stop"]}<br>'
            f'<b>Departure:</b> {fastest["first_departure"]} → {fastest["last_departure"]}<br>'
            f'<b>Duration:</b> {fastest["duration_min"]} min'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("---")

st.markdown("### 📋 Per-Route Throughput Summary")
per_route_df = compute_per_route_summary(trip_df)
if not per_route_df.empty:
    st.dataframe(per_route_df, use_container_width=True, hide_index=True, height=300)
else:
    st.info("No trip data available.")

st.markdown("---")

with st.expander("📑 Full Trip Duration Log (all trips)", expanded=False):
    if not trip_df.empty:
        display_trip = trip_df.rename(columns={
            "trip_id":         "Trip ID",
            "route_id":        "Route",
            "direction":       "Direction",
            "first_stop":      "First Stop",
            "last_stop":       "Last Stop",
            "first_departure": "Departs",
            "last_departure":  "Arrives",
            "duration_min":    "Duration (min)",
            "num_stops":       "Stops",
        })
        st.dataframe(display_trip, use_container_width=True, hide_index=True, height=400)
    else:
        st.info("No trips found.")

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4b — BOTTLENECK ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("## 🔴 Task 4b — Bottleneck Detection & Visual Highlighting")
st.markdown(
    f'<div class="info-box">'
    f'<b>Bottleneck definition:</b> A transition is flagged as a bottleneck '
    f'if its average time exceeds the <b>{pct_threshold}th percentile</b> '
    f'of all transitions in the current selection.'
    + (f' Additionally flagged if avg time &gt; <b>{manual_threshold:.1f} min</b>.'
       if manual_threshold else '')
    + f'<br><b>{n_bottlenecks}</b> of <b>{n_total_edges}</b> transitions are '
    f'currently flagged as bottlenecks.'
    f'</div>',
    unsafe_allow_html=True,
)

b1, b2, b3, b4 = st.columns(4)
b1.metric("Bottleneck Transitions", n_bottlenecks)
b2.metric("Normal Transitions", n_total_edges - n_bottlenecks)
b3.metric("Bottleneck Rate", f"{(n_bottlenecks / max(n_total_edges, 1) * 100):.1f}%")
if not edge_df.empty:
    worst = edge_df.iloc[0]
    b4.metric("Worst Transition", f"{worst['mean_min']:.1f} min",
              help=f"{worst['source']} → {worst['target']}")
else:
    b4.metric("Worst Transition", "—")

st.markdown("---")

st.markdown("### ⚠️ Top 3 Bottleneck Transitions")
if not edge_df.empty:
    top3 = edge_df[edge_df["is_bottleneck"]].head(3)
    if top3.empty:
        top3 = edge_df.head(3)

    cols_b = st.columns(3)
    for i, (_, row) in enumerate(top3.iterrows()):
        with cols_b[i]:
            rank_emoji = ["🥇", "🥈", "🥉"][i]
            st.markdown(
                f'<div class="info-box" style="border-left-color:#ef4444;">'
                f'<b style="color:#fca5a5">{rank_emoji} #{i+1} Bottleneck</b><br>'
                f'<b style="color:#e2e8f0">{row["source"]}</b>'
                f' → <b style="color:#e2e8f0">{row["target"]}</b><br>'
                f'<span style="color:#93c5fd">Avg Time:</span> '
                f'<b>{fmt_sec(row["mean_sec"])}</b> '
                f'({row["mean_min"]:.1f} min)<br>'
                f'<span style="color:#93c5fd">Trips observed:</span> '
                f'<b>{int(row["trip_count"])}</b><br>'
                f'<span style="color:#93c5fd">Max observed:</span> '
                f'<b>{fmt_sec(row["max_sec"])}</b><br>'
                f'<span style="color:#fca5a5;font-size:0.8rem">'
                f'{row["bottleneck_reason"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
else:
    st.info("No transition data available for current filter.")

st.markdown("---")

col_bar, col_heat = st.columns([1, 1], gap="large")

with col_bar:
    st.markdown("### 📊 Transition Time Bar Chart")
    st.caption(
        "Red bars = bottleneck transitions (above threshold). "
        "Blue bars = normal. Showing top 10 slowest."
    )
    fig_bar = plot_bottleneck_bar(edge_df, top_n=10)
    st.pyplot(fig_bar, use_container_width=True)
    plt.close(fig_bar)

with col_heat:
    st.markdown("### 🌡️ Transition Heatmap")
    st.caption(
        "Red = slow transitions, Blue = fast. "
        "Only top 15 transitions shown for readability."
    )
    fig_heat = plot_bottleneck_heatmap(edge_df, top_n=15)
    st.pyplot(fig_heat, use_container_width=True)
    plt.close(fig_heat)

st.markdown("---")

st.markdown("### 📋 Full Transition Analytics Table")
st.caption(
    "🔴 = bottleneck &nbsp;|&nbsp; "
    "All transitions sorted by avg time descending &nbsp;|&nbsp; "
    "Use the filter controls in the sidebar to narrow by route."
)

if not edge_df.empty:
    display_edge = edge_df.copy()
    display_edge["Status"] = display_edge["is_bottleneck"].apply(
        lambda x: "🔴 Bottleneck" if x else "🔵 Normal"
    )
    display_edge["Avg Time"] = display_edge["mean_sec"].apply(fmt_sec)
    display_edge["Min Time"] = display_edge["min_sec"].apply(fmt_sec)
    display_edge["Max Time"] = display_edge["max_sec"].apply(fmt_sec)
    display_edge["Std (s)"]  = display_edge["std_sec"].round(1)
    display_edge["Reason"]   = display_edge["bottleneck_reason"]

    cols_show = ["source", "target", "Status", "Avg Time",
                 "Min Time", "Max Time", "Std (s)", "trip_count", "Reason"]
    rename_map = {
        "source":     "From Stop",
        "target":     "To Stop",
        "trip_count": "Trips",
    }
    final_df = display_edge[cols_show].rename(columns=rename_map)
    st.dataframe(final_df, use_container_width=True, hide_index=True, height=400)
else:
    st.info("No transition data.")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center;color:#475569;font-size:0.78rem;'
    'margin-top:32px;padding-bottom:24px;">'
    "CDA Bus Route Analysis · Task 4 — Performance & Bottleneck Analytics · "
    "SE4009 Process Mining & Simulation · FAST National University"
    "</div>",
    unsafe_allow_html=True,
)
