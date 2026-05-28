#!/usr/bin/env python3
"""
Naive wiki/raw search.

Karpathy gist §Optional CLI tools 의 가장 단순 형태 — `qmd` 같은 정식 검색이 필요해지면 교체.

사용법:
  python tools/search.py "BPE"
  python tools/search.py "self attention" --raw      # raw/ 도 함께 검색
  python tools/search.py "RLHF" --type entity        # entity 페이지만
  python tools/search.py "softmax" --json
  python tools/search.py "trans" --filenames-only

의존성: stdlib only.
선택: 만약 `rank_bm25` 가 설치돼 있으면 BM25 스코어링도 사용 가능 (--bm25).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
RAW = ROOT / "raw"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def fm_type(text: str) -> str | None:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    for line in m.group(1).splitlines():
        if line.startswith("type:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


def grep_file(path: Path, pattern: re.Pattern, root: Path):
    rel = path.relative_to(root)
    text = path.read_text(encoding="utf-8", errors="ignore")
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if pattern.search(line):
            hits.append({"line": i, "text": line.strip()})
    return rel, text, hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", help="검색어 (case-insensitive 정규식 가능)")
    ap.add_argument("--raw", action="store_true", help="raw/ 도 같이 검색")
    ap.add_argument("--type", choices=("source", "entity", "concept", "synthesis"),
                    help="해당 frontmatter type 만")
    ap.add_argument("--filenames-only", action="store_true", help="파일명만 (snippet 생략)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--bm25", action="store_true",
                    help="BM25 스코어링 (pip install rank_bm25)")
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    pattern = re.compile(args.query, re.IGNORECASE)

    files = list(WIKI.rglob("*.md"))
    if args.raw and RAW.exists():
        files += list(RAW.rglob("*.md"))

    results = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        if args.type:
            t = fm_type(text)
            if t != args.type:
                continue
        # 검색
        rel = f.relative_to(ROOT)
        snippets = []
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                snippets.append({"line": i, "text": line.strip()})
        if snippets:
            results.append({"path": str(rel).replace("\\", "/"),
                            "hits": len(snippets),
                            "snippets": snippets[:5]})

    if args.bm25:
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            print("rank_bm25 가 설치돼 있지 않음. pip install rank-bm25", file=sys.stderr)
            sys.exit(2)
        # naive: 페이지 전체 본문을 token 배열로
        docs = []
        meta = []
        for f in files:
            text = f.read_text(encoding="utf-8", errors="ignore")
            tokens = re.findall(r"\w+", text.lower())
            docs.append(tokens)
            meta.append(f.relative_to(ROOT))
        if not docs:
            print("문서 없음.", file=sys.stderr)
            sys.exit(0)
        bm = BM25Okapi(docs)
        q = re.findall(r"\w+", args.query.lower())
        scores = bm.get_scores(q)
        ranked = sorted(zip(scores, meta), key=lambda x: -x[0])[: args.top]
        results = [{"path": str(p).replace("\\", "/"), "score": float(s)} for s, p in ranked if s > 0]

    results = results[: args.top]

    if args.json:
        print(json.dumps({"query": args.query, "n": len(results), "results": results},
                         ensure_ascii=False, indent=2))
    else:
        print(f"Search: '{args.query}' — {len(results)} hits\n")
        for r in results:
            if "score" in r:
                print(f"  {r['score']:.3f}  {r['path']}")
                continue
            print(f"  {r['hits']:3} hits  {r['path']}")
            if not args.filenames_only:
                for sn in r["snippets"]:
                    text = sn["text"]
                    if len(text) > 120:
                        text = text[:117] + "..."
                    print(f"        L{sn['line']:4}  {text}")
            print()


if __name__ == "__main__":
    main()
