from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MASK_PATTERNS = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "<EMAIL>"),
    (re.compile(r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "<PRIVATE_IP>"),
    (re.compile(r"\b172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}\b"), "<PRIVATE_IP>"),
    (re.compile(r"\b192\.168\.\d{1,3}\.\d{1,3}\b"), "<PRIVATE_IP>"),
    (re.compile(r"\b[A-Z]{2,}[A-Z0-9-]{3,}\d{2,}\b"), "<HOSTNAME>"),
    (re.compile(r"\bsess[-_][A-Za-z0-9]{8,}\b", re.IGNORECASE), "<SESSION_ID>"),
    (re.compile(r"\buser[-_][A-Za-z0-9]{3,}\b", re.IGNORECASE), "<USER_ID>"),
]


@dataclass
class BaselineResult:
    name: str
    observed: float
    unit: str
    baseline: float
    direction: str
    status: str
    rationale: str


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def sanitize_text(text: str) -> tuple[str, dict[str, int]]:
    masked = text
    counts: dict[str, int] = {}
    for pattern, replacement in MASK_PATTERNS:
        masked, count = pattern.subn(replacement, masked)
        if count:
            label = replacement.strip("<>")
            counts[label] = counts.get(label, 0) + count
    return masked, counts


def aggregate_evidence(incident: dict[str, Any]) -> str:
    parts = [incident.get("title", ""), incident.get("summary", "")]
    for item in incident.get("evidence", []):
        parts.append(item.get("source", ""))
        parts.append(item.get("text", ""))
    return "\n".join(parts)


def score_signals(text: str, runbook: dict[str, Any]) -> list[dict[str, Any]]:
    lower = text.lower()
    claims = []
    for signal in runbook.get("signals", []):
        keywords = [keyword.lower() for keyword in signal.get("keywords", [])]
        matched = [keyword for keyword in keywords if keyword in lower]
        score = min(40, len(matched) * int(signal.get("weight", 0)))
        if score:
            claims.append(
                {
                    "name": signal["name"],
                    "score": score,
                    "matched_keywords": matched,
                    "rationale": signal.get("rationale", ""),
                }
            )
    return sorted(claims, key=lambda item: item["score"], reverse=True)


def evaluate_baselines(incident: dict[str, Any], runbook: dict[str, Any]) -> list[dict[str, Any]]:
    observed_metrics = incident.get("metrics", {})
    results: list[BaselineResult] = []
    for baseline in runbook.get("baselines", []):
        key = baseline["key"]
        if key not in observed_metrics:
            continue
        observed = float(observed_metrics[key])
        threshold = float(baseline["threshold"])
        direction = baseline.get("direction", "max")
        is_outlier = observed > threshold if direction == "max" else observed < threshold
        if not is_outlier:
            status = "within baseline"
        else:
            ratio = observed / threshold if direction == "max" else threshold / max(observed, 0.01)
            status = "outlier" if ratio >= 1.5 else "warning"
        results.append(
            BaselineResult(
                name=baseline["name"],
                observed=observed,
                unit=baseline.get("unit", ""),
                baseline=threshold,
                direction=direction,
                status=status,
                rationale=baseline.get("rationale", ""),
            )
        )
    return [item.__dict__ for item in results]


def evidence_coverage(incident: dict[str, Any], runbook: dict[str, Any]) -> int:
    available = {item.get("type") for item in incident.get("evidence", [])}
    required = set(runbook.get("required_evidence", []))
    if not required:
        return 100
    return round(len(available & required) / len(required) * 100)


def confidence_score(claims: list[dict[str, Any]], baselines: list[dict[str, Any]], coverage: int) -> int:
    signal_strength = min(100, sum(item["score"] for item in claims))
    outlier_count = sum(1 for item in baselines if item["status"] in {"warning", "outlier"})
    baseline_strength = min(100, outlier_count * 30)
    return round(signal_strength * 0.55 + baseline_strength * 0.30 + coverage * 0.15)


def recommend_runbook(incident: dict[str, Any], runbooks: list[dict[str, Any]]) -> dict[str, Any]:
    raw_text = aggregate_evidence(incident)
    sanitized_text, mask_counts = sanitize_text(raw_text)
    candidates = []
    for runbook in runbooks:
        claims = score_signals(sanitized_text, runbook)
        baselines = evaluate_baselines(incident, runbook)
        coverage = evidence_coverage(incident, runbook)
        confidence = confidence_score(claims, baselines, coverage)
        candidates.append(
            {
                "runbook_id": runbook["id"],
                "runbook_title": runbook["title"],
                "owner": runbook["owner"],
                "confidence": confidence,
                "coverage": coverage,
                "claims": claims,
                "baseline_results": baselines,
                "recommended_actions": runbook.get("recommended_actions", []),
                "escalation_template": runbook.get("escalation_template", ""),
            }
        )
    best = max(candidates, key=lambda item: item["confidence"])
    return {
        "incident_id": incident["id"],
        "title": incident["title"],
        "priority": incident["priority"],
        "service": incident["service"],
        "impact": incident["impact"],
        "sanitized_evidence": sanitized_text,
        "mask_counts": mask_counts,
        "recommendation": best,
        "all_candidates": sorted(candidates, key=lambda item: item["confidence"], reverse=True),
    }


def build_summary(results: list[dict[str, Any]]) -> str:
    lines = ["# Support Triage Summary", ""]
    for result in results:
        recommendation = result["recommendation"]
        lines.extend(
            [
                f"## {result['incident_id']} - {result['title']}",
                "",
                f"- Priority: {result['priority']}",
                f"- Service: {result['service']}",
                f"- Recommended runbook: {recommendation['runbook_title']}",
                f"- Confidence: {recommendation['confidence']} percent",
                f"- Evidence coverage: {recommendation['coverage']} percent",
                f"- Next owner: {recommendation['owner']}",
                "",
                "### Strongest Evidence",
            ]
        )
        for claim in recommendation["claims"][:3]:
            lines.append(f"- {claim['name']}: {claim['score']}/40")
        lines.extend(["", "### Baseline Outliers"])
        for item in recommendation["baseline_results"]:
            if item["status"] != "within baseline":
                lines.append(
                    f"- {item['name']}: observed {item['observed']:g}{item['unit']}, baseline {item['baseline']:g}{item['unit']} ({item['status']})"
                )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def load_runbooks(path: Path) -> list[dict[str, Any]]:
    return [load_json(item) for item in sorted(path.glob("*.json"))]


def run(input_path: Path, runbooks_path: Path, output_path: Path, summary_path: Path | None = None) -> list[dict[str, Any]]:
    incidents = load_json(input_path)
    runbooks = load_runbooks(runbooks_path)
    results = [recommend_runbook(incident, runbooks) for incident in incidents]
    write_json(output_path, results)
    if summary_path:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(build_summary(results), encoding="utf-8")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run support triage against sample incidents.")
    parser.add_argument("--input", default="data/sample_incidents.json", type=Path)
    parser.add_argument("--runbooks", default="runbooks", type=Path)
    parser.add_argument("--output", default="output/triage-results.json", type=Path)
    parser.add_argument("--summary", default="output/support-summary.md", type=Path)
    args = parser.parse_args()
    results = run(args.input, args.runbooks, args.output, args.summary)
    print(f"Processed {len(results)} incidents")
    for result in results:
        recommendation = result["recommendation"]
        print(
            f"{result['incident_id']}: {recommendation['runbook_title']} "
            f"({recommendation['confidence']} percent confidence)"
        )


if __name__ == "__main__":
    main()
