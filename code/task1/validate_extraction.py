from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from pypdf import PdfReader


TIME_RE = re.compile(r"\b(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?\b")


def count_pdf_time_tokens(pdf_path: Path) -> int:
    text = "\n".join((page.extract_text() or "") for page in PdfReader(str(pdf_path)).pages)
    return len(TIME_RE.findall(text))


def summarize_csv(csv_path: Path) -> tuple[int, int, int]:
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    arr_non_empty = sum(1 for row in rows if (row.get("arrival_time") or "").strip())
    dep_non_empty = sum(1 for row in rows if (row.get("departure_time") or "").strip())
    return len(rows), arr_non_empty, dep_non_empty


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate extraction completeness for route CSV.")
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--csv-path", type=Path, required=True)
    parser.add_argument("--report-path", type=Path, required=True)
    args = parser.parse_args()

    pdf_files = sorted(args.pdf_dir.glob("*.pdf"))
    if not pdf_files:
        raise SystemExit(f"No PDFs found in {args.pdf_dir}")

    total_pdf_times = sum(count_pdf_time_tokens(pdf) for pdf in pdf_files)
    total_rows, csv_arr_times, csv_dep_times = summarize_csv(args.csv_path)

    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    with args.report_path.open("w", encoding="utf-8") as fp:
        fp.write("Task 1 Extraction Validation\n")
        fp.write("============================\n")
        fp.write(f"PDF files scanned: {len(pdf_files)}\n")
        fp.write(f"Clock-time tokens found in PDFs: {total_pdf_times}\n")
        fp.write(f"Rows in routes.csv: {total_rows}\n")
        fp.write(f"Non-empty arrival_time values in routes.csv: {csv_arr_times}\n")
        fp.write(f"Non-empty departure_time values in routes.csv: {csv_dep_times}\n")
        fp.write("\n")
        if total_pdf_times == 0:
            fp.write(
                "Interpretation: Source PDFs do not contain machine-extractable HH:MM[:SS] values; "
                "empty arrival/departure time values are expected for this source set.\n"
            )
        else:
            fp.write(
                "Interpretation: PDFs contain time values. If arrival/departure columns are low/empty, "
                "improve parser rules for your route PDF layout.\n"
            )

    print(f"Validation report written to {args.report_path}")


if __name__ == "__main__":
    main()
