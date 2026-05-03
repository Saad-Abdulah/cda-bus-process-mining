from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader


TRIP_LINE_RE = re.compile(r"^([A-Za-z0-9-]+)\s+(\d{2}:\d{2}:\d{2})$")
STOP_ROW_RE = re.compile(r"^(.*?)\s+(\d{2}:\d{2}:\d{2})\s+(\d{2}:\d{2}:\d{2})$")


def normalize_stop_name(raw: str) -> str:
    cleaned = re.sub(r"\s+", " ", raw).strip(" -\t:")
    return cleaned


def iter_pdf_lines(pdf_path: Path) -> Iterable[str]:
    reader = PdfReader(str(pdf_path))
    for page in reader.pages:
        text = page.extract_text() or ""
        for line in text.splitlines():
            line = line.strip()
            if line:
                yield line


def parse_routes_from_pdf(pdf_path: Path) -> tuple[list[dict], dict]:
    lines = list(iter_pdf_lines(pdf_path))
    rows: list[dict] = []

    route_id = ""
    route_name = ""
    direction = ""
    current_trip_id = ""
    current_trip_start = ""
    stop_seq_in_trip = 0

    for line in lines:
        lower = line.lower()
        if lower.startswith("short name"):
            route_id = normalize_stop_name(line.replace("Short Name", "", 1))
            continue
        if lower.startswith("long name"):
            route_name = normalize_stop_name(line.replace("Long Name", "", 1))
            continue
        if lower.startswith("direction"):
            direction = normalize_stop_name(line.replace("Direction", "", 1))
            continue
        if lower.startswith("trip id start time") or lower.startswith("stop_name arrival_time departure_time"):
            continue

        trip_match = TRIP_LINE_RE.match(line)
        if trip_match:
            current_trip_id, current_trip_start = trip_match.groups()
            stop_seq_in_trip = 0
            continue

        stop_match = STOP_ROW_RE.match(line)
        if not stop_match or not current_trip_id:
            continue

        stop_name, arrival_time, departure_time = stop_match.groups()
        stop_name = normalize_stop_name(stop_name)
        if not stop_name:
            continue

        # Exclude header-like artifacts that occasionally appear in OCR text.
        if stop_name.lower() in {"field value", "trip id", "start time", "stop_name"}:
            continue

        stop_seq_in_trip += 1
        rows.append(
            {
                "source_pdf": pdf_path.name,
                "route_id": route_id or "UNKNOWN",
                "route_name": route_name or f"Route {route_id or 'UNKNOWN'}",
                "direction": direction or "UNKNOWN",
                "trip_id": current_trip_id,
                "trip_start_time": current_trip_start,
                "stop_sequence": stop_seq_in_trip,
                "stop_name": stop_name,
                "arrival_time": arrival_time,
                "departure_time": departure_time,
            }
        )

    # Keep stable unique entries.
    dedup = {}
    for row in rows:
        key = (
            row["source_pdf"],
            row["route_id"],
            row["direction"],
            row["trip_id"],
            row["stop_sequence"],
            row["stop_name"],
            row["arrival_time"],
            row["departure_time"],
        )
        if key not in dedup:
            dedup[key] = row

    clean_rows = list(dedup.values())
    stats = {
        "source_pdf": pdf_path.name,
        "rows_extracted": len(clean_rows),
        "trip_count": len({r["trip_id"] for r in clean_rows}),
        "non_empty_departure_time": sum(1 for r in clean_rows if r["departure_time"]),
    }
    return clean_rows, stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract CDA routes into routes.csv")
    parser.add_argument("--input-dir", type=Path, required=True, help="Folder with route PDFs")
    parser.add_argument("--output-csv", type=Path, required=True, help="Output routes.csv path")
    parser.add_argument(
        "--summary-csv",
        type=Path,
        default=None,
        help="Optional per-file extraction summary CSV path",
    )
    args = parser.parse_args()

    pdf_files = sorted(args.input_dir.glob("*.pdf"))
    if not pdf_files:
        raise SystemExit(f"No PDF files found in {args.input_dir}")

    all_rows: list[dict] = []
    summaries: list[dict] = []
    for pdf in pdf_files:
        rows, stats = parse_routes_from_pdf(pdf)
        all_rows.extend(rows)
        summaries.append(stats)

    if not all_rows:
        raise SystemExit("No route rows extracted. Check PDF quality/text extraction.")

    direction_rank = {"Forward": 0, "Backward": 1}
    all_rows.sort(
        key=lambda r: (
            r.get("route_id", ""),
            direction_rank.get(r.get("direction", ""), 99),
            r.get("trip_start_time", ""),
            r.get("trip_id", ""),
            int(r.get("stop_sequence", 0)),
        )
    )

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source_pdf",
        "route_id",
        "route_name",
        "direction",
        "trip_id",
        "trip_start_time",
        "stop_sequence",
        "stop_name",
        "arrival_time",
        "departure_time",
    ]
    with args.output_csv.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    if args.summary_csv:
        args.summary_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.summary_csv.open("w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(
                fp,
                fieldnames=["source_pdf", "rows_extracted", "trip_count", "non_empty_departure_time"],
            )
            writer.writeheader()
            writer.writerows(summaries)

    print(f"Extracted {len(all_rows)} rows into {args.output_csv}")


if __name__ == "__main__":
    main()
