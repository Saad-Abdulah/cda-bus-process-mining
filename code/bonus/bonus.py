"""
Task 6 Bonus - Personal Route Map

Maps each team member's nearest CDA stop to FAST University using the
extracted CDA route data and a light OpenStreetMap visualisation.
"""

import os
import pandas as pd
import pydeck as pdk
import streamlit as st


st.set_page_config(
    page_title="CDA Bus | Personal Route Maps",
    page_icon="Map",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
html, body, [class*="css"] { font-family: Arial, sans-serif; }
.stApp { background: #f8fafc; color: #0f172a; }
h1, h2, h3 { color: #0f172a !important; }
[data-testid="stSidebar"] {
    background: #1f2937;
}
[data-testid="stSidebar"] * {
    color: #f8fafc !important;
}
[data-testid="stSidebar"] .info-box,
[data-testid="stSidebar"] .info-box * {
    color: #0f172a !important;
}
.hero {
    background: #ffffff;
    border: 1px solid #dbe4ee;
    border-radius: 10px;
    padding: 22px 26px;
    margin-bottom: 18px;
    box-shadow: 0 8px 24px rgba(15,23,42,0.08);
}
.hero-title { font-size: 2rem; font-weight: 800; margin-bottom: 4px; color: #0f172a; }
.hero-sub { color: #475569; font-size: 0.95rem; }
.member-card, .info-box {
    background: #ffffff;
    border: 1px solid #dbe4ee;
    border-left: 4px solid #2563eb;
    border-radius: 8px;
    padding: 14px 16px;
    margin: 10px 0;
    color: #0f172a;
    box-shadow: 0 4px 14px rgba(15,23,42,0.06);
}
.muted { color: #64748b; font-size: 0.86rem; }
.pill {
    display: inline-block;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    color: #1d4ed8;
    border-radius: 999px;
    padding: 4px 10px;
    margin: 4px 4px 4px 0;
    font-size: 0.8rem;
    font-weight: 700;
}
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #dbe4ee;
    border-radius: 8px;
    padding: 12px;
}
[data-testid="stMetric"] * {
    color: #0f172a !important;
}
[data-testid="stMetric"] [data-testid="stMetricLabel"] * {
    color: #475569 !important;
}
.svg-map-wrap {
    background: #ffffff;
    border: 1px solid #dbe4ee;
    border-radius: 10px;
    box-shadow: 0 8px 24px rgba(15,23,42,0.08);
    overflow: hidden;
}
</style>
""",
    unsafe_allow_html=True,
)


STOP_COORDS = {
    "Pindora Chungi": (33.6519, 73.0644),
    "Pindora": (33.6519, 73.0644),
    "Katarian Chungi": (33.6550, 73.0633),
    "Katarian Pull": (33.6581, 73.0624),
    "CDA Stop": (33.6623, 73.0615),
    "Pully Stop": (33.6662, 73.0607),
    "Mandi Morh": (33.6701, 73.0598),
    "Sabzi Mandi": (33.6712, 73.0600),
    "Metro CNC": (33.6689, 73.0535),
    "IMC Hospital": (33.6665, 73.0466),
    "PAEC General Hospital": (33.6641, 73.0388),
    "Islamic University": (33.6573, 73.0250),
    "FAST University": (33.6566, 73.0157),
    "G-11 Markaz": (33.6693, 72.9999),
    "Mehrabad": (33.6614, 73.0018),
    "Nust Metro Station": (33.6438, 72.9906),
    "Bar Council": (33.6487, 72.9946),
    "A.K Bari Road": (33.6499, 72.9963),
    "Police Foundation Metro Station": (33.6568, 72.9992),
    "NPA Stop": (33.6554, 73.0068),
}

FAST_COORDS = STOP_COORDS["FAST University"]

MEMBERS = [
    {
        "name": "Immad Baber",
        "student_id": "23i-3062",
        "home_area": "Pindora, Satellite Town",
        "home_coords": (33.6514, 73.0656),
        "nearest_stop": "Pindora Chungi",
        "color": "#16a34a",
        "route": [
            {
                "segment": 1,
                "route_id": "FR-14",
                "route_name": "Bara Kahu to Mandi Morh",
                "direction": "Forward",
                "stops": ["Pindora Chungi", "Katarian Chungi", "Katarian Pull", "CDA Stop", "Pully Stop", "Mandi Morh"],
                "dep_time": "07:42:56",
                "arr_time": "07:53:00",
                "color": "#16a34a",
            },
            {
                "segment": 2,
                "route_id": "FR-01",
                "route_name": "Khana Pul to NUST",
                "direction": "Backward",
                "stops": ["Mandi Morh", "Sabzi Mandi", "Metro CNC", "IMC Hospital", "PAEC General Hospital", "Islamic University", "FAST University"],
                "dep_time": "07:54:33",
                "arr_time": "08:06:43",
                "color": "#f59e0b",
            },
        ],
        "total_time_min": 24,
        "transfers": 1,
        "note": "Nearest stop is Pindora Chungi on I.J.P. Road. FR-14 connects to Mandi Morh, then FR-01 reaches FAST University.",
    },
    {
        "name": "Qadeer Raza",
        "student_id": "23i-3059",
        "home_area": "G-12",
        "home_coords": (33.6762, 72.9848),
        "nearest_stop": "G-11 Markaz",
        "color": "#2563eb",
        "route": [
            {
                "segment": 1,
                "route_id": "FR-07",
                "route_name": "PIMS Hospital to Police Foundation",
                "direction": "Forward",
                "stops": ["G-11 Markaz", "Mehrabad", "Nust Metro Station", "Bar Council", "A.K Bari Road", "Police Foundation Metro Station"],
                "dep_time": "06:30:44",
                "arr_time": "06:47:20",
                "color": "#2563eb",
            },
            {
                "segment": 2,
                "route_id": "FR-01",
                "route_name": "Khana Pul to NUST",
                "direction": "Forward",
                "stops": ["Police Foundation Metro Station", "NPA Stop", "Islamic University", "FAST University"],
                "dep_time": "06:47:20",
                "arr_time": "06:55:00",
                "color": "#f59e0b",
            },
        ],
        "total_time_min": 24,
        "transfers": 1,
        "note": "G-12 is not a named stop in routes.csv, so G-11 Markaz is used as the nearest available CDA stop before continuing via Police Foundation to FAST.",
    },
    {
        "name": "Muhammad Anas",
        "student_id": "23i-3026",
        "home_area": "G-11",
        "home_coords": (33.6693, 72.9999),
        "nearest_stop": "G-11 Markaz",
        "color": "#d97706",
        "route": [
            {
                "segment": 1,
                "route_id": "FR-07",
                "route_name": "PIMS Hospital to Police Foundation",
                "direction": "Forward",
                "stops": ["G-11 Markaz", "Mehrabad", "Nust Metro Station", "Bar Council", "A.K Bari Road", "Police Foundation Metro Station"],
                "dep_time": "06:30:44",
                "arr_time": "06:47:20",
                "color": "#d97706",
            },
            {
                "segment": 2,
                "route_id": "FR-01",
                "route_name": "Khana Pul to NUST",
                "direction": "Forward",
                "stops": ["Police Foundation Metro Station", "NPA Stop", "Islamic University", "FAST University"],
                "dep_time": "06:47:20",
                "arr_time": "06:55:00",
                "color": "#2563eb",
            },
        ],
        "total_time_min": 24,
        "transfers": 1,
        "note": "Nearest stop is G-11 Markaz. FR-07 reaches Police Foundation, where FR-01 continues to FAST University.",
    },
    {
        "name": "Saad Abdullah",
        "student_id": "23i-3044",
        "home_area": "H-13",
        "home_coords": (33.6475, 72.9815),
        "nearest_stop": "Nust Metro Station",
        "color": "#dc2626",
        "route": [
            {
                "segment": 1,
                "route_id": "FR-01",
                "route_name": "Khana Pul to NUST",
                "direction": "Forward",
                "stops": ["Nust Metro Station", "Police Foundation Metro Station", "NPA Stop", "Islamic University", "FAST University"],
                "dep_time": "06:00:00",
                "arr_time": "06:10:40",
                "color": "#dc2626",
            },
        ],
        "total_time_min": 11,
        "transfers": 0,
        "note": "H-13 is closest to the NUST/H-12 corridor in this network. FR-01 goes directly from Nust Metro Station to FAST University.",
    },
]


@st.cache_data
def load_routes() -> pd.DataFrame:
    for path in [
        os.path.join("data", "output", "routes.csv"),
        os.path.join("..", "..", "data", "output", "routes.csv"),
        "routes.csv",
    ]:
        if os.path.exists(path):
            return pd.read_csv(path)
    return pd.DataFrame()


def build_svg_map(member: dict, show_all: bool = False) -> str:
    members = MEMBERS if show_all else [member]
    points = [FAST_COORDS]
    for m in members:
        points.append(m["home_coords"])
        for seg in m["route"]:
            points.extend(STOP_COORDS[s] for s in seg["stops"] if s in STOP_COORDS)

    min_lat = min(p[0] for p in points)
    max_lat = max(p[0] for p in points)
    min_lon = min(p[1] for p in points)
    max_lon = max(p[1] for p in points)
    width, height, pad = 900, 540, 58

    def project(coord: tuple[float, float]) -> tuple[float, float]:
        lat, lon = coord
        x = pad + (lon - min_lon) / max(0.0001, max_lon - min_lon) * (width - 2 * pad)
        y = pad + (max_lat - lat) / max(0.0001, max_lat - min_lat) * (height - 2 * pad)
        return x, y

    route_shapes = []
    labels = []
    seen_stops = set()

    for m in members:
        hx, hy = project(m["home_coords"])
        route_shapes.append(f"<circle cx='{hx:.1f}' cy='{hy:.1f}' r='13' fill='{m['color']}' stroke='#0f172a' stroke-width='2'/>")
        labels.append(f"<text x='{hx + 16:.1f}' y='{hy - 10:.1f}' class='label'>{m['name']}</text>")
        labels.append(f"<text x='{hx + 16:.1f}' y='{hy + 6:.1f}' class='small'>Home: {m['home_area']}</text>")

        for seg in m["route"]:
            coords = [STOP_COORDS[s] for s in seg["stops"] if s in STOP_COORDS]
            if len(coords) >= 2:
                pts = " ".join(f"{project(c)[0]:.1f},{project(c)[1]:.1f}" for c in coords)
                dash = " stroke-dasharray='9 7'" if seg["segment"] > 1 else ""
                route_shapes.append(
                    f"<polyline points='{pts}' fill='none' stroke='{seg['color']}' stroke-width='6' "
                    f"stroke-linecap='round' stroke-linejoin='round' opacity='0.9'{dash}/>"
                )
            for stop in seg["stops"]:
                if stop not in STOP_COORDS or stop in seen_stops:
                    continue
                seen_stops.add(stop)
                x, y = project(STOP_COORDS[stop])
                radius = 8 if stop in [seg["stops"][0], seg["stops"][-1], "FAST University"] else 5
                route_shapes.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{radius}' fill='#ffffff' stroke='{seg['color']}' stroke-width='3'/>")
                if radius == 8:
                    labels.append(f"<text x='{x + 11:.1f}' y='{y + 4:.1f}' class='small'>{stop}</text>")

    fx, fy = project(FAST_COORDS)
    route_shapes.append(f"<rect x='{fx - 11:.1f}' y='{fy - 11:.1f}' width='22' height='22' rx='5' fill='#0f172a'/>")
    labels.append(f"<text x='{fx + 16:.1f}' y='{fy + 5:.1f}' class='label'>FAST University</text>")

    legend = "".join(
        f"<div><span style='background:{m['color']}'></span>{m['name']} - {m['nearest_stop']}</div>"
        for m in MEMBERS
    )

    return f"""
<div class="svg-map-wrap">
<svg viewBox="0 0 {width} {height}" width="100%" height="540" role="img">
  <defs>
    <pattern id="grid" width="44" height="44" patternUnits="userSpaceOnUse">
      <path d="M 44 0 L 0 0 0 44" fill="none" stroke="#e2e8f0" stroke-width="1"/>
    </pattern>
    <style>
      .label {{ font: 700 15px Arial, sans-serif; fill: #0f172a; }}
      .small {{ font: 12px Arial, sans-serif; fill: #334155; }}
      .caption {{ font: 12px Arial, sans-serif; fill: #64748b; }}
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#ffffff"/>
  <rect x="0" y="0" width="100%" height="100%" fill="url(#grid)" opacity="0.65"/>
  <text x="24" y="32" class="label">Personal CDA Route Map</text>
  <text x="24" y="52" class="caption">Self-contained schematic map based on route stop coordinates</text>
  {''.join(route_shapes)}
  {''.join(labels)}
</svg>
<div style="display:flex;flex-wrap:wrap;gap:14px;padding:10px 14px;border-top:1px solid #dbe4ee;background:#f8fafc;color:#0f172a;font-size:13px">
  <style>.svg-map-wrap span {{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:6px}}</style>
  {legend}
</div>
</div>
"""


def build_leaflet_map(member: dict, show_all: bool = False) -> str:
    members = MEMBERS if show_all else [member]
    markers = []
    polylines = []

    for m in members:
        color = m["color"]
        home_lat, home_lon = m["home_coords"]
        markers.append(
            f"""
L.circleMarker([{home_lat}, {home_lon}], {{
  radius: 11, color: '{color}', fillColor: '{color}', fillOpacity: 0.95, weight: 3
}}).addTo(map).bindPopup('<b>{m["name"]}</b><br>{m["student_id"]}<br>{m["home_area"]}<br>Nearest stop: <b>{m["nearest_stop"]}</b>');
"""
        )

        for seg in m["route"]:
            coords = []
            for stop in seg["stops"]:
                if stop not in STOP_COORDS:
                    continue
                lat, lon = STOP_COORDS[stop]
                coords.append([lat, lon])
                radius = 8 if stop in [seg["stops"][0], seg["stops"][-1], "FAST University"] else 5
                markers.append(
                    f"""
L.circleMarker([{lat}, {lon}], {{
  radius: {radius}, color: '{seg["color"]}', fillColor: '#ffffff', fillOpacity: 1, weight: 3
}}).addTo(map).bindPopup('<b>{stop}</b><br>{seg["route_id"]} ({seg["direction"]})');
"""
                )
            if len(coords) >= 2:
                dash = "null" if seg["segment"] == 1 else "'8,6'"
                polylines.append(
                    f"""
L.polyline({coords}, {{
  color: '{seg["color"]}', weight: 6, opacity: 0.9, dashArray: {dash}
}}).addTo(map).bindPopup('<b>{seg["route_id"]}</b><br>{seg["route_name"]}');
"""
                )

    markers.append(
        f"""
L.marker([{FAST_COORDS[0]}, {FAST_COORDS[1]}]).addTo(map).bindPopup('<b>FAST University</b><br>Destination');
"""
    )

    if show_all:
        center_lat = sum(m["home_coords"][0] for m in MEMBERS) / len(MEMBERS)
        center_lon = sum(m["home_coords"][1] for m in MEMBERS) / len(MEMBERS)
        zoom = 12
    else:
        center_lat = (member["home_coords"][0] + FAST_COORDS[0]) / 2
        center_lon = (member["home_coords"][1] + FAST_COORDS[1]) / 2
        zoom = 13

    legend_rows = "".join(
        f"<div><span class='dot' style='background:{m['color']}'></span>{m['name']} - {m['home_area']}</div>"
        for m in MEMBERS
    )

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
body {{ margin:0; background:#ffffff; }}
#map {{ width:100%; height:540px; border-radius:10px; background:#ffffff; }}
.legend {{
  background:rgba(255,255,255,0.96); border:1px solid #cbd5e1; border-radius:8px;
  padding:10px 12px; color:#0f172a; font-family:Arial,sans-serif; font-size:12px;
  box-shadow:0 8px 22px rgba(15,23,42,0.16); line-height:1.7;
}}
.dot {{ display:inline-block; width:11px; height:11px; border-radius:50%; margin-right:6px; }}
</style>
</head>
<body>
<div id="map"></div>
<script>
var map = L.map('map', {{ center: [{center_lat}, {center_lon}], zoom: {zoom}, zoomControl: true }});
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  attribution: '&copy; OpenStreetMap &copy; CARTO',
  subdomains: 'abcd',
  maxZoom: 19
}}).addTo(map);
{''.join(polylines)}
{''.join(markers)}
var legend = L.control({{position:'bottomright'}});
legend.onAdd = function(map) {{
  var div = L.DomUtil.create('div', 'legend');
  div.innerHTML = '<b>Legend</b><br>{legend_rows}<div>FAST University</div>';
  return div;
}};
legend.addTo(map);
</script>
</body>
</html>
"""


df = load_routes()


def hex_to_rgb(hex_color: str) -> list[int]:
    hex_color = hex_color.lstrip("#")
    return [int(hex_color[i:i + 2], 16) for i in (0, 2, 4)]


def build_pydeck_map(member: dict, show_all: bool = False) -> pdk.Deck:
    members = MEMBERS if show_all else [member]
    points = []
    paths = []
    labels = []

    for m in members:
        rgb = hex_to_rgb(m["color"])
        home_lat, home_lon = m["home_coords"]
        points.append({
            "lat": home_lat,
            "lon": home_lon,
            "name": f"{m['name']} home",
            "type": "Home",
            "color": rgb,
            "radius": 7,
        })
        labels.append({"lat": home_lat, "lon": home_lon, "text": m["name"], "color": rgb})

        for seg in m["route"]:
            seg_rgb = hex_to_rgb(seg["color"])
            route_path = []
            for stop in seg["stops"]:
                if stop not in STOP_COORDS:
                    continue
                lat, lon = STOP_COORDS[stop]
                route_path.append([lon, lat])
                points.append({
                    "lat": lat,
                    "lon": lon,
                    "name": stop,
                    "type": f"{seg['route_id']} {seg['direction']}",
                    "color": seg_rgb,
                    "radius": 4 if stop != "FAST University" else 7,
                })
            if len(route_path) >= 2:
                paths.append({
                    "path": route_path,
                    "name": f"{m['name']} - {seg['route_id']}",
                    "color": seg_rgb,
                })

    points.append({
        "lat": FAST_COORDS[0],
        "lon": FAST_COORDS[1],
        "name": "FAST University",
        "type": "Destination",
        "color": [15, 23, 42],
        "radius": 8,
    })
    labels.append({"lat": FAST_COORDS[0], "lon": FAST_COORDS[1], "text": "FAST University", "color": [15, 23, 42]})

    all_lats = [p["lat"] for p in points]
    all_lons = [p["lon"] for p in points]
    view_state = pdk.ViewState(
        latitude=sum(all_lats) / len(all_lats),
        longitude=sum(all_lons) / len(all_lons),
        zoom=11.2 if show_all else 12.5,
        pitch=0,
    )

    return pdk.Deck(
        map_style=pdk.map_styles.CARTO_LIGHT,
        initial_view_state=view_state,
        tooltip={"text": "{name}\n{type}"},
        layers=[
            pdk.Layer(
                "PathLayer",
                data=paths,
                get_path="path",
                get_color="color",
                width_scale=1,
                width_min_pixels=3,
                rounded=True,
                pickable=True,
            ),
            pdk.Layer(
                "ScatterplotLayer",
                data=points,
                get_position="[lon, lat]",
                get_fill_color="color",
                get_line_color=[255, 255, 255],
                get_radius="radius",
                radius_units="pixels",
                line_width_min_pixels=2,
                stroked=True,
                filled=True,
                pickable=True,
            ),
            pdk.Layer(
                "TextLayer",
                data=labels,
                get_position="[lon, lat]",
                get_text="text",
                get_color="color",
                get_size=12,
                get_alignment_baseline="'bottom'",
                get_pixel_offset=[0, -10],
            ),
        ],
    )

st.markdown(
    """
<div class="hero">
  <div class="hero-title">Personal Route Maps - Task 6 Bonus</div>
  <div class="hero-sub">Each member's nearest CDA stop to FAST University, traced on a white interactive map.</div>
</div>
""",
    unsafe_allow_html=True,
)

routes_used = sorted({seg["route_id"] for m in MEMBERS for seg in m["route"]})
c1, c2, c3, c4 = st.columns(4)
c1.metric("Team Members", len(MEMBERS))
c2.metric("Routes Used", ", ".join(routes_used))
c3.metric("Max Transfers", max(m["transfers"] for m in MEMBERS))
c4.metric("Avg Journey", f"{sum(m['total_time_min'] for m in MEMBERS) // len(MEMBERS)} min")

with st.sidebar:
    st.markdown("### Team Members")
    mode = st.radio("View Mode", ["All Members Overview", "Individual Member"], index=0)
    selected_name = st.selectbox("Select Member", [m["name"] for m in MEMBERS])
    selected_member = next(m for m in MEMBERS if m["name"] == selected_name)
    st.markdown("---")
    st.markdown("### Route Notes")
    st.markdown(
        """
<div class="info-box">
<b>FR-01</b>: NUST / Police Foundation / FAST corridor<br>
<b>FR-07</b>: G-11 to Police Foundation connector<br>
<b>FR-14</b>: Pindora Chungi to Mandi Morh connector
</div>
""",
        unsafe_allow_html=True,
    )

if mode == "All Members Overview":
    st.markdown("## Combined Map")
    st.pydeck_chart(build_pydeck_map(MEMBERS[0], show_all=True), height=560)

    st.markdown("## Member Summaries")
    cols = st.columns(2)
    for i, m in enumerate(MEMBERS):
        route_labels = " -> ".join(seg["route_id"] for seg in m["route"])
        with cols[i % 2]:
            st.markdown(
                f"""
<div class="member-card" style="border-left-color:{m['color']}">
  <h3>{m['name']} <span class="muted">({m['student_id']})</span></h3>
  <div class="muted">Home Area: {m['home_area']}</div>
  <span class="pill">Nearest Stop: {m['nearest_stop']}</span>
  <span class="pill">Routes: {route_labels}</span>
  <span class="pill">Time: {m['total_time_min']} min</span>
  <span class="pill">Transfers: {m['transfers']}</span>
  <div class="muted">{m['note']}</div>
</div>
""",
                unsafe_allow_html=True,
            )

    st.markdown("## Report Summary Table")
    summary = []
    for m in MEMBERS:
        summary.append(
            {
                "Member": m["name"],
                "Student ID": m["student_id"],
                "Home Area": m["home_area"],
                "Nearest Stop": m["nearest_stop"],
                "Route(s) Used": " -> ".join(seg["route_id"] for seg in m["route"]),
                "Departure": m["route"][0]["dep_time"],
                "Arrives FAST": m["route"][-1]["arr_time"],
                "Estimated Travel Time": f"{m['total_time_min']} min",
                "Transfers": m["transfers"],
            }
        )
    st.dataframe(pd.DataFrame(summary), width="stretch", hide_index=True)

else:
    m = selected_member
    st.markdown(f"## {m['name']} - Personal Route")
    col_map, col_info = st.columns([3, 2], gap="large")
    with col_map:
        st.pydeck_chart(build_pydeck_map(m, show_all=False), height=560)
    with col_info:
        st.markdown(
            f"""
<div class="info-box" style="border-left-color:{m['color']}">
<b>Member:</b> {m['name']} ({m['student_id']})<br>
<b>Home Area:</b> {m['home_area']}<br>
<b>Nearest Stop:</b> {m['nearest_stop']}<br>
<b>Destination:</b> FAST University<br>
<b>Estimated Time:</b> {m['total_time_min']} min<br>
<b>Transfers:</b> {m['transfers']}<br>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown("### Route Segments")
        for seg in m["route"]:
            st.markdown(
                f"""
<div class="member-card" style="border-left-color:{seg['color']}">
<b>{seg['route_id']} - {seg['direction']}</b><br>
<span class="muted">{seg['route_name']}</span><br>
<span class="muted">Dep: {seg['dep_time']} | Arr: {seg['arr_time']} | Stops: {len(seg['stops'])}</span>
</div>
""",
                unsafe_allow_html=True,
            )
        with st.expander("Stop Sequence", expanded=True):
            for seg in m["route"]:
                for stop in seg["stops"]:
                    st.write(f"{seg['route_id']} - {stop}")

st.markdown("---")
st.caption("CDA Bus Route Analysis - Task 6 Bonus - Personal Route Maps")
