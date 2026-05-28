"""Run full vault audit using all 4 Baseline Grep tools.

Cycle 5l #3 — 222 sources + 43 synthesis (or all kinds, selectable) audit batch.

Outputs:
  audit_results/<date>_summary.json    — 종합 통계
  audit_results/<date>_broken.json     — find_cross_link_broken 결과
  audit_results/<date>_missing.json    — suggest_missing_cross_link 결과
  audit_results/<date>_stale.json      — find_stale_baseline 결과
  audit_results/<date>_conflict.json   — find_claim_conflict (페어 매트릭스 — 시간 비용 큼, default skip)

Usage:
  python tools/run_full_audit.py                      # all sources/synthesis (skip conflict)
  python tools/run_full_audit.py --kinds sources      # sources only
  python tools/run_full_audit.py --include-conflict   # +conflict (느림)
  python tools/run_full_audit.py --sample 20          # sample 첫 20 페이지만 (테스트용)
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
VAULT_ROOT = TOOLS_DIR.parent
WIKI = VAULT_ROOT / "wiki"
OUT_DIR = VAULT_ROOT / "audit_results"

sys.path.insert(0, str(TOOLS_DIR))

from find_cross_link_broken import find_cross_link_broken_handler  # noqa: E402
from suggest_missing_cross_link import suggest_missing_cross_link_handler  # noqa: E402
from find_stale_baseline import find_stale_baseline_handler  # noqa: E402
from find_claim_conflict import find_claim_conflict_handler  # noqa: E402


def _iter_pages(kinds: list[str], sample: int | None = None):
    """Yield (kind, slug) tuples."""
    count = 0
    for kind in kinds:
        folder = WIKI / kind
        if not folder.is_dir():
            continue
        for f in sorted(folder.glob("*.md")):
            yield kind, f.stem
            count += 1
            if sample is not None and count >= sample:
                return


def run_broken(kinds, sample):
    print("[1/4] find_cross_link_broken — scanning ...", flush=True)
    results = []
    total_links = total_broken = pages_with_broken = 0
    for kind, slug in _iter_pages(kinds, sample):
        r = find_cross_link_broken_handler(slug, kind, vault_root=WIKI)
        total_links += r["total_wikilinks"]
        if r["broken_count"] > 0:
            results.append(r)
            pages_with_broken += 1
            total_broken += r["broken_count"]
    print(f"      pages_with_broken={pages_with_broken} broken_total={total_broken} links_total={total_links}")
    return {
        "tool": "find_cross_link_broken",
        "pages_with_broken": pages_with_broken,
        "broken_total": total_broken,
        "links_total": total_links,
        "results": results,
    }


def run_missing(kinds, sample, min_inbound=2):
    print(f"[2/4] suggest_missing_cross_link — scanning (min_inbound={min_inbound}) ...", flush=True)
    results = []
    total_missing = pages_with_missing = 0
    for kind, slug in _iter_pages(kinds, sample):
        r = suggest_missing_cross_link_handler(slug, kind, vault_root=WIKI, min_inbound=min_inbound)
        missing = [s for s in r.get("suggestions", []) if s.get("missing")]
        if missing:
            results.append({
                "slug": slug,
                "kind": kind,
                "outbound_count": r.get("outbound_count"),
                "inbound_count": r.get("inbound_count"),
                "missing": missing,
            })
            pages_with_missing += 1
            total_missing += len(missing)
    print(f"      pages_with_missing={pages_with_missing} missing_total={total_missing}")
    return {
        "tool": "suggest_missing_cross_link",
        "min_inbound": min_inbound,
        "pages_with_missing": pages_with_missing,
        "missing_total": total_missing,
        "results": results,
    }


def run_stale(kinds, sample, threshold_days=90):
    print(f"[3/4] find_stale_baseline — scanning (threshold={threshold_days}d) ...", flush=True)
    results = []
    stale_count = aged_count = total = 0
    for kind, slug in _iter_pages(kinds, sample):
        r = find_stale_baseline_handler(slug, kind, threshold_days, vault_root=WIKI)
        total += 1
        if r.get("is_stale"):
            stale_count += 1
            results.append(r)
        elif r.get("age_days", 0) >= threshold_days // 2:
            aged_count += 1
    print(f"      stale={stale_count} aged_50%={aged_count} total={total}")
    return {
        "tool": "find_stale_baseline",
        "threshold_days": threshold_days,
        "stale_count": stale_count,
        "aged_50%": aged_count,
        "total": total,
        "results": results,
    }


def run_conflict(kinds, sample):
    """Pair conflict — N*N/2 = 매우 비싼. Curated pair list 만 사용 (heuristic mode)."""
    print("[4/4] find_claim_conflict — curated 10 pairs (heuristic mode) ...", flush=True)
    pairs = [
        ("ue-editor-asseteditorapi", "ue-editor-personatoolkit"),
        ("ue-editor-asseteditorapi", "ue-editor-toolmenus"),
        ("ue-coreuobject-uobject", "ue-coreuobject-reflection"),
        ("ue-components-skill", "ue-coreuobject-uobject"),
        ("ue-render-skill", "ue-render-rdg"),
        ("ue-render-lumennanite", "ue-render-meshdrawing"),
        ("ue-levelsequence-skill", "ue-levelsequence-moviescene"),
        ("ue-levelsequence-levelsequenceplayer", "ue-levelsequence-moviescene"),
        ("ue-spatialpartition-skill", "ue-spatialpartition-toctree2"),
        ("ue-animation-skill", "ue-animation-animinstance"),
    ]
    results = []
    total_conflicts = 0
    for slug_a, slug_b in pairs:
        try:
            r = find_claim_conflict_handler(slug_a, slug_b, "sources", "sources", vault_root=WIKI)
            conflicts = r.get("conflicts", [])
            if conflicts:
                results.append({
                    "pair": [slug_a, slug_b],
                    "mode": r.get("mode"),
                    "conflicts": conflicts,
                })
                total_conflicts += len(conflicts)
        except Exception as e:
            results.append({"pair": [slug_a, slug_b], "error": str(e)})
    print(f"      pairs={len(pairs)} conflicts_total={total_conflicts}")
    return {
        "tool": "find_claim_conflict",
        "mode": "heuristic",
        "pairs": len(pairs),
        "conflicts_total": total_conflicts,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kinds", nargs="+",
                        default=["sources", "synthesis"],
                        choices=["sources", "entities", "concepts", "synthesis"])
    parser.add_argument("--sample", type=int, default=None,
                        help="Limit total pages scanned (for testing)")
    parser.add_argument("--include-conflict", action="store_true")
    parser.add_argument("--min-inbound", type=int, default=2)
    parser.add_argument("--threshold-days", type=int, default=90)
    args = parser.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    today = date.today().isoformat()

    print(f"===== Cycle 5l #3 — Full Vault Audit ({today}) =====")
    print(f"  kinds={args.kinds}  sample={args.sample}  conflict={args.include_conflict}")
    print()

    broken   = run_broken(args.kinds, args.sample)
    missing  = run_missing(args.kinds, args.sample, args.min_inbound)
    stale    = run_stale(args.kinds, args.sample, args.threshold_days)
    conflict = run_conflict(args.kinds, args.sample) if args.include_conflict else None

    # Save individual + summary
    (OUT_DIR / f"{today}_broken.json").write_text(
        json.dumps(broken, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / f"{today}_missing.json").write_text(
        json.dumps(missing, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / f"{today}_stale.json").write_text(
        json.dumps(stale, ensure_ascii=False, indent=2), encoding="utf-8")
    if conflict:
        (OUT_DIR / f"{today}_conflict.json").write_text(
            json.dumps(conflict, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "date": today,
        "kinds": args.kinds,
        "sample": args.sample,
        "broken": {
            "pages_with_broken": broken["pages_with_broken"],
            "broken_total": broken["broken_total"],
            "links_total": broken["links_total"],
        },
        "missing": {
            "pages_with_missing": missing["pages_with_missing"],
            "missing_total": missing["missing_total"],
            "min_inbound": missing["min_inbound"],
        },
        "stale": {
            "stale_count": stale["stale_count"],
            "aged_50%": stale["aged_50%"],
            "total": stale["total"],
            "threshold_days": stale["threshold_days"],
        },
    }
    if conflict:
        summary["conflict"] = {
            "pairs": conflict["pairs"],
            "conflicts_total": conflict["conflicts_total"],
            "mode": conflict["mode"],
        }
    (OUT_DIR / f"{today}_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print("===== Summary =====")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nResults saved to: {OUT_DIR}")


if __name__ == "__main__":
    main()
