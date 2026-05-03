from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path


ISO_TZ_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$")


def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1]


def validate_xes(xes_path: Path) -> dict:
    tree = ET.parse(xes_path)
    root = tree.getroot()
    if strip_ns(root.tag) != "log":
        raise ValueError("Root element is not <log>.")

    xes_version = root.attrib.get("xes.version")
    if xes_version != "1.0":
        raise ValueError(f'Invalid xes.version: expected "1.0", got "{xes_version}"')

    extensions = [e for e in root if strip_ns(e.tag) == "extension"]
    classifiers = [e for e in root if strip_ns(e.tag) == "classifier"]
    traces = [e for e in root if strip_ns(e.tag) == "trace"]
    if not traces:
        raise ValueError("No traces found in XES log.")

    trace_count = 0
    event_count = 0
    missing_event_name = 0
    missing_event_time = 0
    bad_timestamp_format = 0
    bad_int_stop_sequence = 0

    for trace in traces:
        trace_count += 1
        events = [c for c in trace if strip_ns(c.tag) == "event"]
        if not events:
            raise ValueError("Found a trace without events.")

        for event in events:
            event_count += 1
            attrs = [c for c in event]
            has_name = False
            has_time = False
            for attr in attrs:
                t = strip_ns(attr.tag)
                key = attr.attrib.get("key", "")
                val = attr.attrib.get("value", "")
                if t == "string" and key == "concept:name" and val:
                    has_name = True
                if t == "date" and key == "time:timestamp":
                    has_time = True
                    if not ISO_TZ_RE.match(val):
                        bad_timestamp_format += 1
                if key == "stop_sequence":
                    if t != "int" or not val.isdigit():
                        bad_int_stop_sequence += 1
            if not has_name:
                missing_event_name += 1
            if not has_time:
                missing_event_time += 1

    if missing_event_name or missing_event_time or bad_timestamp_format or bad_int_stop_sequence:
        raise ValueError(
            "XES validation failed: "
            f"missing_event_name={missing_event_name}, "
            f"missing_event_time={missing_event_time}, "
            f"bad_timestamp_format={bad_timestamp_format}, "
            f"bad_int_stop_sequence={bad_int_stop_sequence}"
        )

    return {
        "xes_version": xes_version,
        "trace_count": trace_count,
        "event_count": event_count,
        "extension_count": len(extensions),
        "classifier_count": len(classifiers),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate strict XES requirements.")
    parser.add_argument("--xes-path", type=Path, required=True)
    parser.add_argument("--report-path", type=Path, required=True)
    args = parser.parse_args()

    metrics = validate_xes(args.xes_path)
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    with args.report_path.open("w", encoding="utf-8") as fp:
        fp.write("Task 2 XES Validation Report\n")
        fp.write("============================\n")
        fp.write(f"XES file: {args.xes_path}\n")
        fp.write("Validation result: PASS\n")
        fp.write(f"xes.version: {metrics['xes_version']}\n")
        fp.write(f"Extensions: {metrics['extension_count']}\n")
        fp.write(f"Classifiers: {metrics['classifier_count']}\n")
        fp.write(f"Trace count: {metrics['trace_count']}\n")
        fp.write(f"Event count: {metrics['event_count']}\n")
        fp.write("Timestamp format check: PASS (ISO 8601 with timezone)\n")
        fp.write("Attribute type checks: PASS (string/int/date)\n")

    print(f"XES validation passed. Report written to {args.report_path}")


if __name__ == "__main__":
    main()
