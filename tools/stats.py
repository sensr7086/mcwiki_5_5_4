#!/usr/bin/env python3
"""
LLM Wiki Stats — 페이지 분포 / 허브 / 고아 / freshness 요약.

사용법:
  python tools/stats.py
  python tools/stats.py --json
  python tools/stats.py --top 10                 # 상위 N hub 출력
  python tools/stats.py --update-index           # wiki/index.md 의 통계 블록 자동 갱신

의존성: stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
RAW = ROOT / "raw"

WIKILINK_RE = re.compile(r"\[\[([^\[\]\|\#]+?)(?:\#[^\[\]\|]+)?(?:\|[^\[\]]+)?\]\]")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def fm_type(text: str) -> str | None:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    for line in m.group(1).splitlines():
        if line.startswith("type:"):
            v = line.split(":", 1)[1].strip().strip('"').strip("'")
            return v
    return None


def fm_field(text: str, key: str) -> str | None:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    for line in m.group(1).splitlines():
        if line.startswith(f"{key}:"):
            v = line.split(":", 1)[1].strip().strip('"').strip("'")
            return v
    return None


def collect():
    if not WIKI.exists():
        return None
    pages: dict[str, Path] = {}
    by_type = Counter()
    inbound: dict[str, set[str]] = defaultdict(set)
    last_updated: dict[str, date] = {}

    md_files = list(WIKI.rglob("*.md"))
    for f in md_files:
        slug = f.relative_to(WIKI).with_suffix("").as_posix()
        pages[slug] = f
        text = f.read_text(encoding="utf-8")
        t = fm_type(text)
        if t:
            by_type[t] += 1
        # last_updated
        for k in ("last_updated", "ingested", "created"):
            v = fm_field(text, k)
            if v:
                try:
                    last_updated[slug] = datetime.strptime(v, "%Y-%m-%d").date()
                    break
                except ValueError:
                    pass
        # inbound (basename + path 둘 다)
        for m in WIKILINK_RE.finditer(text):
            target = m.group(1).strip()
            inbound[target].add(slug)

    today = date.today()
    fresh = sum(1 for d in last_updated.values() if (today - d).days <= 30)
    aging = sum(1 for d in last_updated.values() if 30 < (today - d).days <= 90)
    stale = sum(1 for d in last_updated.values() if (today - d).days > 90)

    # raw 카운트
    raw_files = []
    if RAW.exists():
        for f in RAW.rglob("*"):
            if f.is_file() and not f.name.startswith(".") and f.name != "README.md":
                raw_files.append(f)

    # Hubs / orphans
    rel_paths = set(pages.keys())
    basenames = {p.rsplit("/", 1)[-1]: p for p in rel_paths}
    inbound_count: Counter = Counter()
    for slug in pages:
        bn = slug.rsplit("/", 1)[-1]
        cnt = len(inbound.get(slug, set()) | inbound.get(bn, set()))
        inbound_count[slug] = cnt
    orphans = [s for s, n in inbound_count.items() if n == 0 and s not in ("index", "log")]
    hubs = inbound_count.most_common()

    return {
        "pages_total": len(pages),
        "by_type": dict(by_type),
        "raw_files": len(raw_files),
        "freshness": {"fresh_<=30d": fresh, "aging_30-90d": aging, "stale_>90d": stale},
        "orphans": orphans,
        "hubs": hubs,
    }


def render_text(s: dict, top: int) -> str:
    lines = []
    lines.append(f"# Wiki Stats — {date.today().isoformat()}")
    lines.append("")
    lines.append(f"raw files:        {s['raw_files']}")
    lines.append(f"wiki pages total: {s['pages_total']}")
    for t in ("source", "entity", "concept", "synthesis"):
        lines.append(f"  - {t:10} {s['by_type'].get(t, 0)}")
    lines.append("")
    lines.append("Freshness:")
    for k, v in s["freshness"].items():
        lines.append(f"  - {k:18} {v}")
    lines.append(f"orphans:          {len(s['orphans'])}")
    lines.append("")
    lines.append(f"Top {top} hubs (inbound link count):")
    for slug, cnt in s["hubs"][:top]:
        if cnt == 0:
            break
        lines.append(f"  {cnt:4}  {slug}")
    if s["orphans"]:
        lines.append("")
        lines.append(f"Orphans (first {top}):")
        for slug in s["orphans"][:top]:
            lines.append(f"  -  {slug}")
    return "\n".join(lines)


STATS_BLOCK_RE = re.compile(r"```\s*\nsources:.*?\n```", re.DOTALL)


def update_index_block(s: dict):
    idx = WIKI / "index.md"
    if not idx.exists():
        return False
    text = idx.read_text(encoding="utf-8")
    block = (
        "```\n"
        f"sources:    {s['by_type'].get('source', 0)}\n"
        f"entities:   {s['by_type'].get('entity', 0)}\n"
        f"concepts:   {s['by_type'].get('concept', 0)}\n"
        f"synthesis:  {s['by_type'].get('synthesis', 0)}\n"
        f"orphans:    {len(s['orphans'])}\n"
        f"broken:     (run lint.py)\n"
        f"stale (>90d): {s['freshness']['stale_>90d']}\n"
        "```"
    )
    new = STATS_BLOCK_RE.sub(block, text, count=1)
    if new != text:
        idx.write_text(new, encoding="utf-8")
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--update-index", action="store_true")
    args = ap.parse_args()

    s = collect()
    if s is None:
        print("wiki/ not found.", file=sys.stderr)
        sys.exit(2)

    if args.update_index:
        ok = update_index_block(s)
        print(f"index.md stats block: {'updated' if ok else 'unchanged'}")

    if args.json:
        s_pub = dict(s)
        s_pub["hubs"] = s["hubs"][: args.top]
        s_pub["orphans"] = s["orphans"][: args.top]
        print(json.dumps(s_pub, ensure_ascii=False, indent=2))
    else:
        print(render_text(s, args.top))


if __name__ == "__main__":
    main()
