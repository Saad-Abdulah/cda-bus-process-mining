"""
Task 5 — Agentic AI Trip Planner
SE4009 Process Mining & Simulation — FAST National University

Integrates a local grounded trip-planning agent with the discovered CDA route data to answer natural-language
trip-planning queries grounded in the routes.csv data.
"""

import os
import json
import re
import time
import textwrap
from difflib import get_close_matches
from datetime import datetime
from pathlib import Path
from collections import defaultdict, deque

import streamlit as st
import pandas as pd

# ── CONSTANTS ──────────────────────────────────────────────────────────────────
BASE_DATE      = "2000-01-01 "

# ── PAGE CONFIG ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CDA Bus | AI Trip Planner",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── STYLES ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Sora', sans-serif; color: #e2e8f0; }

.stApp {
    background: linear-gradient(135deg, #0a0f1e 0%, #0d1b2a 50%, #0a1628 100%);
    color: #e2e8f0;
}
p, span, div, label, li, td, th { color: #e2e8f0; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid #1e40af55;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

/* Dropdown item text */
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] [role="option"] *,
div[role="listbox"] * { color: #000 !important; }
[data-baseweb="select"] span,
[data-baseweb="select"] div[class*="ValueContainer"] * { color: #000 !important; }

h1, h2, h3, h4 { color: #93c5fd !important; font-weight: 700 !important; }

/* ── Chat bubbles ── */
.chat-wrap { display: flex; flex-direction: column; gap: 14px; padding: 8px 0; }

.bubble-user {
    align-self: flex-end;
    background: linear-gradient(135deg, #1d4ed8, #1e40af);
    border: 1px solid #3b82f655;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px;
    max-width: 72%;
    font-size: 0.92rem;
    color: #f0f9ff !important;
    box-shadow: 0 4px 16px #0006;
}
.bubble-bot {
    align-self: flex-start;
    background: linear-gradient(135deg, #111827, #1e293b);
    border: 1px solid #1e40af55;
    border-radius: 18px 18px 18px 4px;
    padding: 14px 18px;
    max-width: 82%;
    font-size: 0.92rem;
    color: #e2e8f0 !important;
    box-shadow: 0 4px 16px #0006;
    line-height: 1.65;
}
.bubble-bot b  { color: #93c5fd; }
.bubble-bot em { color: #86efac; font-style: normal; }

.avatar-user { font-size: 1.1rem; margin-left: 6px; }
.avatar-bot  { font-size: 1.1rem; margin-right: 6px; }

.row-user { display:flex; justify-content:flex-end; align-items:flex-end; gap:4px; }
.row-bot  { display:flex; justify-content:flex-start; align-items:flex-end; gap:4px; }

/* ── Hero ── */
.hero-banner {
    background: linear-gradient(90deg, #1e3a8a33, #0369a133, #1e3a8a33);
    border: 1px solid #3b82f655;
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 24px;
    position: relative; overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute; inset: 0;
    background: repeating-linear-gradient(45deg, transparent, transparent 40px, #ffffff06 40px, #ffffff06 41px);
    pointer-events: none;
}
.hero-title  { font-size: 2.1rem; font-weight: 700; color: #f0f9ff; margin: 0 0 6px; }
.hero-sub    { font-size: 0.95rem; color: #93c5fd; margin: 0; }
.hero-badge  {
    display: inline-block; background: #1d4ed8; color: #bfdbfe;
    font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
    padding: 3px 12px; border-radius: 999px; margin-bottom: 12px;
    border: 1px solid #3b82f666;
}

/* ── Info box ── */
.info-box {
    background: #0f1e33; border: 1px solid #1e40af55;
    border-left: 3px solid #3b82f6; border-radius: 8px;
    padding: 12px 16px; font-size: 0.85rem; color: #94a3b8;
    margin: 12px 0; line-height: 1.6;
}
.info-box b { color: #bfdbfe; }

/* ── Suggestions ── */
.suggestion-btn {
    background: #0f2240; border: 1px solid #3b82f655;
    border-radius: 10px; padding: 8px 14px;
    color: #93c5fd; font-size: 0.82rem; cursor: pointer;
    transition: all 0.2s;
}
.suggestion-btn:hover { background: #1e3a5f; border-color: #60a5fa; }

/* ── Typing indicator ── */
.typing-dots span {
    display: inline-block; width: 7px; height: 7px;
    border-radius: 50%; background: #60a5fa; margin: 0 2px;
    animation: bounce 1.2s infinite ease-in-out;
}
.typing-dots span:nth-child(2) { animation-delay: 0.2s; }
.typing-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
    0%,80%,100% { transform: translateY(0); }
    40%          { transform: translateY(-8px); }
}

hr { border-color: #1e40af55 !important; }
[data-testid="stCaptionContainer"] * { color: #94a3b8 !important; }

/* Chat input area */
.stTextInput input {
    background: #111827 !important;
    border: 1px solid #1e40af !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
    font-family: 'Sora', sans-serif !important;
}
.stTextInput input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 2px #3b82f622 !important;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1e3a5f, #0f2240);
    border: 1px solid #3b82f655; border-radius: 12px;
    padding: 16px; box-shadow: 0 4px 20px #0008;
}
[data-testid="stMetricLabel"] * { color: #93c5fd !important; font-size: 0.78rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; }
[data-testid="stMetricValue"] * { color: #f0f9ff !important; font-family: 'JetBrains Mono', monospace !important; font-size: 1.6rem !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)


# ── DATA LOADING ────────────────────────────────────────────────────────────────
@st.cache_data
def load_routes() -> pd.DataFrame:
    for path in [
        os.path.join("data", "output", "routes.csv"),
        os.path.join("..", "..", "data", "output", "routes.csv"),
        "routes.csv",
    ]:
        if os.path.exists(path):
            df = pd.read_csv(path)
            df["departure_dt"] = pd.to_datetime(
                BASE_DATE + df["departure_time"].astype(str),
                format="%Y-%m-%d %H:%M:%S", errors="coerce",
            )
            df["arrival_dt"] = pd.to_datetime(
                BASE_DATE + df["arrival_time"].astype(str),
                format="%Y-%m-%d %H:%M:%S", errors="coerce",
            )
            return df.sort_values(["route_id", "direction", "trip_id", "stop_sequence"]).reset_index(drop=True)
    st.error("❌ routes.csv not found. Please run from the project root.")
    st.stop()


# ── ROUTE KNOWLEDGE BUILDER ─────────────────────────────────────────────────────
@st.cache_data
def build_route_knowledge(df: pd.DataFrame) -> dict:
    """Build a comprehensive knowledge base from routes.csv for the AI agent."""

    knowledge = {
        "routes": {},
        "stop_to_routes": defaultdict(list),
        "edges": {},          # (src, tgt) -> {mean_sec, route_ids, trip_count}
        "all_stops": sorted(df["stop_name"].unique().tolist()),
    }

    # Per-route info
    for route_id, rdf in df.groupby("route_id"):
        route_name = rdf["route_name"].iloc[0]
        directions = {}
        for direction, ddf in rdf.groupby("direction"):
            trips = []
            for trip_id, tdf in ddf.groupby("trip_id"):
                tdf = tdf.sort_values("stop_sequence")
                stops = tdf["stop_name"].tolist()
                times = tdf["departure_time"].tolist()
                trips.append({"trip_id": trip_id, "stops": stops, "times": times})
            directions[direction] = trips
        knowledge["routes"][route_id] = {
            "name": route_name,
            "directions": directions,
        }

    # Stop → routes mapping
    for _, row in df.iterrows():
        entry = (row["route_id"], row["direction"])
        if entry not in knowledge["stop_to_routes"][row["stop_name"]]:
            knowledge["stop_to_routes"][row["stop_name"]].append(entry)

    # Edge transition times
    raw_edges = defaultdict(list)
    for (_, _, _), grp in df.groupby(["route_id", "direction", "trip_id"]):
        grp = grp.sort_values("stop_sequence").reset_index(drop=True)
        for i in range(len(grp) - 1):
            src = grp.loc[i, "stop_name"]
            tgt = grp.loc[i + 1, "stop_name"]
            dt = (grp.loc[i + 1, "departure_dt"] - grp.loc[i, "departure_dt"]).total_seconds()
            if dt >= 0:
                raw_edges[(src, tgt)].append(dt)

    for (src, tgt), secs_list in raw_edges.items():
        mean_sec = sum(secs_list) / len(secs_list)
        knowledge["edges"][(src, tgt)] = {
            "mean_sec": mean_sec,
            "trip_count": len(secs_list),
        }

    return knowledge


# ── BFS PATH FINDER ────────────────────────────────────────────────────────────
def find_paths(knowledge: dict, origin: str, destination: str, max_transfers: int = 2) -> list[dict]:
    """BFS over the stop graph to find paths from origin to destination."""

    # Build adjacency: stop -> list of (next_stop, route_id, direction, mean_sec)
    adj = defaultdict(list)
    for route_id, rinfo in knowledge["routes"].items():
        for direction, trips in rinfo["directions"].items():
            if not trips:
                continue
            # Use first trip's stop sequence for adjacency
            stops = trips[0]["stops"]
            for i in range(len(stops) - 1):
                adj[stops[i]].append({
                    "next": stops[i + 1],
                    "route_id": route_id,
                    "direction": direction,
                    "route_name": rinfo["name"],
                })

    if origin not in adj and origin not in knowledge["all_stops"]:
        return []
    if destination not in knowledge["all_stops"]:
        return []

    # BFS: state = (current_stop, current_route, path_so_far, transfers_used)
    results = []
    visited = set()
    queue = deque()
    queue.append({
        "stop": origin,
        "route": None,
        "path": [{"stop": origin, "route": None, "direction": None}],
        "transfers": -1,
        "total_sec": 0.0,
    })

    while queue and len(results) < 5:
        state = queue.popleft()
        cur_stop = state["stop"]
        cur_route = state["route"]
        transfers = state["transfers"]

        if cur_stop == destination:
            results.append(state)
            continue

        if transfers >= max_transfers:
            continue

        state_key = (cur_stop, cur_route, transfers)
        if state_key in visited:
            continue
        visited.add(state_key)

        for edge in adj.get(cur_stop, []):
            next_stop = edge["next"]
            next_route = edge["route_id"]
            new_transfer = transfers + (1 if next_route != cur_route and cur_route is not None else 0)
            if new_transfer > max_transfers:
                continue

            edge_key = (cur_stop, next_stop)
            mean_sec = knowledge["edges"].get(edge_key, {}).get("mean_sec", 120.0)

            new_path = state["path"] + [{
                "stop": next_stop,
                "route": next_route,
                "direction": edge["direction"],
                "route_name": edge["route_name"],
            }]
            queue.append({
                "stop": next_stop,
                "route": next_route,
                "path": new_path,
                "transfers": new_transfer,
                "total_sec": state["total_sec"] + mean_sec,
            })

    return results


def fmt_sec(sec: float) -> str:
    sec = max(0, int(round(sec)))
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m}m"
    if m > 0:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def find_next_departure(knowledge: dict, stop: str, route_id: str, direction: str, after_time: str = None) -> str:
    """Find the next departure time from a stop on a given route."""
    now = datetime.strptime(f"2000-01-01 {datetime.now().strftime('%H:%M:%S')}", "%Y-%m-%d %H:%M:%S")
    if after_time:
        try:
            now = datetime.strptime(f"2000-01-01 {after_time}", "%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

    rinfo = knowledge["routes"].get(route_id, {})
    trips = rinfo.get("directions", {}).get(direction, [])

    candidates = []
    for trip in trips:
        if stop in trip["stops"]:
            idx = trip["stops"].index(stop)
            dep_str = trip["times"][idx]
            try:
                dep_dt = datetime.strptime(f"2000-01-01 {dep_str}", "%Y-%m-%d %H:%M:%S")
                if dep_dt >= now:
                    candidates.append(dep_str)
            except Exception:
                pass

    if candidates:
        return sorted(candidates)[0]
    return "—"

def find_last_departure(knowledge: dict, stop: str) -> tuple[str, list[str]]:
    """Find the latest departure from a stop across all routes."""
    departures = []
    for route_id, direction in knowledge["stop_to_routes"].get(stop, []):
        rinfo = knowledge["routes"].get(route_id, {})
        for trip in rinfo.get("directions", {}).get(direction, []):
            if stop not in trip["stops"]:
                continue
            idx = trip["stops"].index(stop)
            dep_str = trip["times"][idx]
            try:
                dep_dt = datetime.strptime(f"2000-01-01 {dep_str}", "%Y-%m-%d %H:%M:%S")
            except Exception:
                continue
            departures.append((dep_dt, dep_str, route_id, direction, rinfo.get("name", route_id)))

    if not departures:
        return "", []

    latest_dt = max(item[0] for item in departures)
    latest = [item for item in departures if item[0] == latest_dt]
    labels = [f"{route_id} ({direction}, {name})" for _, _, route_id, direction, name in latest]
    return latest[0][1], labels


def normalize_text(value: str) -> str:
    value = value.lower().replace("khanna", "khana")
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def match_stops_in_query(query: str, all_stops: list[str]) -> list[str]:
    """Return route-data stops mentioned by the user, preserving query order."""
    normalized_query = f" {normalize_text(query)} "
    matches = []
    for stop in all_stops:
        normalized_stop = normalize_text(stop)
        pos = normalized_query.find(f" {normalized_stop} ")
        if pos >= 0:
            matches.append((pos, -len(normalized_stop), stop))

    if matches:
        return [stop for _, _, stop in sorted(matches)]

    candidates = re.split(r"\bfrom\b|\bto\b|\bthrough\b|\bvia\b|\bat\b|\bserve\b|\bserves\b", query, flags=re.I)
    normalized_stops = {normalize_text(stop): stop for stop in all_stops}
    found = []
    for part in candidates:
        cleaned = normalize_text(part)
        if not cleaned:
            continue
        close = get_close_matches(cleaned, normalized_stops.keys(), n=1, cutoff=0.78)
        if close and normalized_stops[close[0]] not in found:
            found.append(normalized_stops[close[0]])
    return found


def describe_route_segments(path: dict) -> list[dict]:
    """Compress a stop-by-stop path into route segments."""
    steps = path["path"]
    if len(steps) < 2:
        return []

    segments = []
    current = None
    segment_start = steps[0]["stop"]
    previous_stop = steps[0]["stop"]

    for step in steps[1:]:
        route = step["route"]
        if current and route != current["route"]:
            current["end"] = previous_stop
            segments.append(current)
            segment_start = previous_stop

        if not current or route != current["route"]:
            current = {
                "route": route,
                "direction": step["direction"],
                "route_name": step.get("route_name", route),
                "start": segment_start,
                "end": step["stop"],
            }
        else:
            current["end"] = step["stop"]

        previous_stop = step["stop"]

    if current:
        segments.append(current)
    return segments


def answer_routes_at_stop(stop: str, knowledge: dict) -> str:
    routes = sorted(set(knowledge["stop_to_routes"].get(stop, [])))
    if not routes:
        return f"I could not find any route serving {stop} in routes.csv."

    lines = [f"{stop} is served by these route directions:"]
    for route_id, direction in routes[:12]:
        name = knowledge["routes"][route_id]["name"]
        lines.append(f"- {route_id} ({direction}) - {name}")
    if len(routes) > 12:
        lines.append(f"- Plus {len(routes) - 12} more route direction(s).")
    return "\n".join(lines)


def local_agent_response(query: str, knowledge: dict) -> str:
    """Grounded offline trip-planning agent for Task 5."""
    q_lower = query.lower()
    stops = match_stops_in_query(query, knowledge["all_stops"])

    if not stops:
        examples = "; ".join(SAMPLE_QUERIES[:4])
        return (
            "I could not match any stop from your question to routes.csv. "
            f"Try using an exact stop name, for example: {examples}."
        )

    if len(stops) == 1 and any(word in q_lower for word in ["last", "latest", "final"]):
        stop = stops[0]
        departure, routes = find_last_departure(knowledge, stop)
        if not departure:
            return f"I found {stop}, but no departure time is available for it in routes.csv."
        return (
            f"The last bus departure from {stop} is {departure}.\n"
            f"Route(s): {', '.join(routes)}."
        )

    if len(stops) == 1 and any(phrase in q_lower for phrase in ["which route", "which routes", "through", "serve", "serves", "go through", "goes through"]):
        return answer_routes_at_stop(stops[0], knowledge)

    if len(stops) < 2:
        return answer_routes_at_stop(stops[0], knowledge)

    origin, destination = stops[0], stops[1]
    paths = find_paths(knowledge, origin, destination)
    if not paths:
        return (
            f"I found both stops in routes.csv, but no connection from {origin} "
            f"to {destination} was found within 2 transfers in the discovered route graph."
        )

    lines = [f"Options from {origin} to {destination} based only on routes.csv:"]
    for idx, path in enumerate(paths[:3], 1):
        transfers = max(0, path["transfers"])
        lines.append(f"\nOption {idx}: {fmt_sec(path['total_sec'])}, {transfers} transfer(s)")

        for segment in describe_route_segments(path):
            next_departure = find_next_departure(
                knowledge,
                segment["start"],
                segment["route"],
                segment["direction"],
            )
            lines.append(
                f"- Take {segment['route']} ({segment['direction']}, {segment['route_name']}) "
                f"from {segment['start']} to {segment['end']}. "
                f"Next departure from {segment['start']}: {next_departure}."
            )

    return "\n".join(lines)


def build_context_summary(knowledge: dict) -> str:
    """Summarize the route knowledge for the AI system prompt."""
    lines = []
    lines.append(f"Total unique stops: {len(knowledge['all_stops'])}")
    lines.append(f"Total routes: {len(knowledge['routes'])}")
    lines.append("")

    lines.append("ROUTES:")
    for rid, rinfo in sorted(knowledge["routes"].items()):
        directions = list(rinfo["directions"].keys())
        n_trips = sum(len(v) for v in rinfo["directions"].values())
        # Get all unique stops across all trips in Forward direction
        fwd_trips = rinfo["directions"].get("Forward", [])
        all_stops_fwd = fwd_trips[0]["stops"] if fwd_trips else []
        stops_preview = " → ".join(all_stops_fwd[:5])
        if len(all_stops_fwd) > 5:
            stops_preview += f" ... ({len(all_stops_fwd)} stops total)"
        lines.append(f"  {rid}: {rinfo['name']} | Directions: {directions} | Trips: {n_trips}")
        lines.append(f"    Forward stops: {stops_preview}")

    lines.append("")
    lines.append(f"ALL STOPS (297 total):")
    lines.append(", ".join(knowledge["all_stops"]))

    return "\n".join(lines)


# ── SAMPLE QUERIES ──────────────────────────────────────────────────────────────
SAMPLE_QUERIES = [
    "How do I get from Khanna Pul to NUST Metro Station?",
    "Which routes go through Faizabad?",
    "What time does the last bus leave from FAST University?",
    "How long does it take from Khanna Pul to Faizabad?",
    "Do any routes connect G-9 Markaz to F-10 Markaz?",
    "What routes serve PIMS Hospital?",
    "How do I get from Zero Point to Bahria University?",
    "Which route goes to Quaid Azam University?",
]


# ── LOAD DATA ───────────────────────────────────────────────────────────────────
df = load_routes()
knowledge = build_route_knowledge(df)

# ── SESSION STATE ───────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = ""

# ── HERO ─────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
  <div class="hero-badge">SE4009 · Process Mining & Simulation · Task 5</div>
  <div class="hero-title">🤖 CDA Bus AI Trip Planner</div>
  <div class="hero-sub">Natural-language trip planning grounded in real CDA route data · 21 routes · 297 stops</div>
</div>
""", unsafe_allow_html=True)

# ── LAYOUT ─────────────────────────────────────────────────────────────────────
col_chat, col_panel = st.columns([2, 1], gap="large")

# ════════════════════════════════════════════════════════════════════════════════
# LEFT — CHAT PANEL
# ════════════════════════════════════════════════════════════════════════════════
with col_chat:
    st.markdown("### 💬 Chat with CDA Bus Agent")
    st.caption("Ask about routes, stops, travel times, transfers, and more.")

    # ── Render conversation ──────────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            st.markdown(
                '<div class="bubble-bot">'
                '🚌 <b>Hello!</b> I\'m your CDA Bus Trip Planner. I have real-time knowledge '
                'of all 21 CDA routes and 297 stops in Islamabad.<br><br>'
                'Ask me anything like:<br>'
                '• <em>"How do I get from Khanna Pul to NUST?"</em><br>'
                '• <em>"Which routes serve Faizabad?"</em><br>'
                '• <em>"How long from G-9 to F-10 Markaz?"</em>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            html_parts = ['<div class="chat-wrap">']
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    html_parts.append(
                        f'<div class="row-user">'
                        f'<div class="bubble-user">{msg["content"]}</div>'
                        f'<span class="avatar-user">🧑</span></div>'
                    )
                else:
                    content = msg["content"].replace("\n", "<br>")
                    html_parts.append(
                        f'<div class="row-bot">'
                        f'<span class="avatar-bot">🤖</span>'
                        f'<div class="bubble-bot">{content}</div></div>'
                    )
            html_parts.append('</div>')
            st.markdown("\n".join(html_parts), unsafe_allow_html=True)

    st.markdown("---")

    # ── Input form ──────────────────────────────────────────────────────────
    with st.form("chat_form", clear_on_submit=True):
        cols = st.columns([5, 1])
        with cols[0]:
            user_input = st.text_input(
                "Your question",
                value=st.session_state.pending_query,
                placeholder="e.g. How do I get from Khanna Pul to NUST Metro Station?",
                label_visibility="collapsed",
            )
        with cols[1]:
            submitted = st.form_submit_button("Send 🚀", use_container_width=True)

    if submitted and user_input.strip():
        query = user_input.strip()
        st.session_state.pending_query = ""

        # Add user message
        st.session_state.messages.append({"role": "user", "content": query})

        # Answer locally from routes.csv. No external API key is required.
        response = local_agent_response(query, knowledge)

        # Keep the same Streamlit loading feedback as the original chat flow.
        with st.spinner("🤖 Agent thinking..."):
            pass

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.pending_query = ""
        st.rerun()

    # ── Clear button ────────────────────────────────────────────────────────
    if st.session_state.messages:
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# RIGHT — INFO PANEL
# ════════════════════════════════════════════════════════════════════════════════
with col_panel:
    # ── Stats ────────────────────────────────────────────────────────────────
    st.markdown("### 📊 Network Overview")
    c1, c2 = st.columns(2)
    c1.metric("Routes", len(knowledge["routes"]))
    c2.metric("Stops",  len(knowledge["all_stops"]))

    c3, c4 = st.columns(2)
    c3.metric("Edges", len(knowledge["edges"]))
    total_trips = sum(
        len(trips)
        for rinfo in knowledge["routes"].values()
        for trips in rinfo["directions"].values()
    )
    c4.metric("Trips", total_trips)

    st.markdown("---")

    # ── Route Directory ─────────────────────────────────────────────────────
    st.markdown("### 🗺️ Route Directory")
    with st.expander("View all routes", expanded=False):
        for rid, rinfo in sorted(knowledge["routes"].items()):
            st.markdown(
                f'<div class="info-box" style="margin:4px 0;padding:8px 12px;">'
                f'<b style="color:#60a5fa">{rid}</b> — {rinfo["name"]}'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── Sample Queries ──────────────────────────────────────────────────────
    st.markdown("### 💡 Try These Queries")
    for q in SAMPLE_QUERIES:
        if st.button(f"→ {q}", key=f"sq_{q[:20]}", use_container_width=True):
            st.session_state.pending_query = q
            st.rerun()

    st.markdown("---")

    # ── Stop Lookup ─────────────────────────────────────────────────────────
    st.markdown("### 🔍 Stop Lookup")
    search_stop = st.text_input("Search stop name", placeholder="e.g. Faizabad")
    if search_stop:
        matches = [s for s in knowledge["all_stops"] if search_stop.lower() in s.lower()]
        if matches:
            for m in matches[:8]:
                routes_here = knowledge["stop_to_routes"].get(m, [])
                route_str = ", ".join(f"{r[0]}" for r in routes_here[:6])
                st.markdown(
                    f'<div class="info-box" style="margin:4px 0;padding:8px 12px;">'
                    f'<b>{m}</b><br>'
                    f'<span style="color:#64748b;font-size:0.8rem">Routes: {route_str}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No stops matched.")

# ── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center;color:#475569;font-size:0.78rem;padding-bottom:24px;">'
    "CDA Bus Route Analysis · Task 5 — Agentic AI Trip Planner · "
    "SE4009 Process Mining & Simulation · FAST National University"
    "</div>",
    unsafe_allow_html=True,
)
