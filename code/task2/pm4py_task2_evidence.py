from __future__ import annotations

import argparse
from pathlib import Path

from pm4py.algo.discovery.inductive import algorithm as inductive_miner
from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.objects.conversion.process_tree import converter as pt_converter
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.statistics.traces.generic.log import case_statistics
from pm4py.visualization.petri_net import visualizer as pn_visualizer


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Task 2 PM4Py evidence from XES.")
    parser.add_argument("--xes-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    log = xes_importer.apply(str(args.xes_path))

    trace_count = len(log)
    event_count = sum(len(trace) for trace in log)
    variants_count = len(case_statistics.get_variant_statistics(log))

    print("PM4Py Evidence")
    print("==============")
    print(f"XES File: {args.xes_path}")
    print(f"Trace Count: {trace_count}")
    print(f"Event Count: {event_count}")
    print(f"Variant Count: {variants_count}")

    summary_path = args.output_dir / "pm4py_validation_summary.txt"
    with summary_path.open("w", encoding="utf-8") as fp:
        fp.write("PM4Py Validation Summary\n")
        fp.write("=======================\n")
        fp.write(f"XES File: {args.xes_path}\n")
        fp.write(f"Trace Count: {trace_count}\n")
        fp.write(f"Event Count: {event_count}\n")
        fp.write(f"Variant Count: {variants_count}\n")

    # Full log process model image
    process_tree = inductive_miner.apply(log)
    net, im, fm = pt_converter.apply(process_tree)
    gviz = pn_visualizer.apply(net, im, fm)
    pn_visualizer.save(gviz, str(args.output_dir / "process_model_full.png"))

    # Example route-wise model for FR-01 for screenshot evidence.
    fr01_log = attributes_filter.apply(log, ["FR-01"], parameters={"attribute_key": "route_id", "positive": True})
    if len(fr01_log) > 0:
        process_tree_r = inductive_miner.apply(fr01_log)
        net_r, im_r, fm_r = pt_converter.apply(process_tree_r)
        gviz_r = pn_visualizer.apply(net_r, im_r, fm_r)
        pn_visualizer.save(gviz_r, str(args.output_dir / "process_model_fr01.png"))

    print(f"Summary written to: {summary_path}")
    print(f"Saved image: {args.output_dir / 'process_model_full.png'}")
    if len(fr01_log) > 0:
        print(f"Saved image: {args.output_dir / 'process_model_fr01.png'}")


if __name__ == "__main__":
    main()
