from __future__ import annotations

import argparse
import copy
import json
import statistics
import time
from pathlib import Path
from typing import Any

from banner_generator.lambda_handler import handler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark repeated Lambda handler renders.")
    parser.add_argument("event", type=Path, help="Path to a Lambda event JSON file.")
    parser.add_argument("--count", type=int, default=10, help="Number of renders to run.")
    parser.add_argument("--warmup", type=int, default=1, help="Warmup renders excluded from stats.")
    parser.add_argument(
        "--unique-certificates",
        action="store_true",
        help="Vary certificate_id/name/url fields for each render.",
    )
    return parser


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    index = min(len(values) - 1, max(0, round((len(values) - 1) * pct)))
    return sorted(values)[index]


def event_for_iteration(base_event: dict[str, Any], index: int, unique: bool) -> dict[str, Any]:
    event = copy.deepcopy(base_event)
    if not unique:
        return event

    data = event.setdefault("data", {})
    certificate_id = f"benchmark-{index + 1:05d}"
    data["name"] = f"Benchmark Learner {index + 1:05d}"
    data["certificate_id"] = certificate_id
    data["certificate_url"] = f"https://certificates.aishippinglabs.com/ai-hero/{certificate_id}.pdf"

    if "s3" in event:
        target = event["s3"]
        suffix = "pdf" if event.get("format") == "pdf" else event.get("format", "png")
        target["key"] = f"benchmark/{certificate_id}.{suffix}"

    return event


def summarize(durations: list[float], count: int, warmup: int) -> dict[str, Any]:
    total = sum(durations)
    measured = durations[warmup:]
    measured_total = sum(measured)
    return {
        "count": count,
        "warmup": warmup,
        "measured_count": len(measured),
        "total_seconds": round(total, 3),
        "measured_seconds": round(measured_total, 3),
        "mean_seconds": round(statistics.mean(measured), 3) if measured else 0,
        "median_seconds": round(statistics.median(measured), 3) if measured else 0,
        "min_seconds": round(min(measured), 3) if measured else 0,
        "max_seconds": round(max(measured), 3) if measured else 0,
        "p90_seconds": round(percentile(measured, 0.90), 3),
        "p95_seconds": round(percentile(measured, 0.95), 3),
        "renders_per_minute": round((len(measured) / measured_total) * 60, 2)
        if measured_total
        else 0,
        "estimated_500_sequential_seconds": round((500 / len(measured)) * measured_total, 1)
        if measured
        else 0,
    }


def main() -> int:
    args = build_parser().parse_args()
    if args.count <= 0:
        raise SystemExit("--count must be positive")
    if args.warmup < 0 or args.warmup >= args.count:
        raise SystemExit("--warmup must be >= 0 and smaller than --count")

    base_event = json.loads(args.event.read_text())
    durations: list[float] = []
    last_summary: dict[str, Any] = {}

    for index in range(args.count):
        event = event_for_iteration(base_event, index, args.unique_certificates)
        started = time.perf_counter()
        response = handler(event)
        durations.append(time.perf_counter() - started)
        last_summary = {
            "statusCode": response.get("statusCode"),
            "ok": response.get("ok"),
            "content_type": response.get("content_type") or response.get("headers", {}).get("Content-Type"),
            "body_length": len(response.get("body", "")),
            "s3": response.get("s3"),
        }

    result = summarize(durations, args.count, args.warmup)
    result["first_render_seconds"] = round(durations[0], 3)
    result["last_response"] = last_summary
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
