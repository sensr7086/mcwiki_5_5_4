#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Wiki Linter — mechanical checks.

Checks (CLAUDE.md §5.3 + §5.4 §C-2 신설 2026-05-13):
  1) Frontmatter required fields
  2) Wikilink target exists (in wiki/, raw/, or 00_meta/, or docs/)
  3) Orphan pages (no inbound)
  4) Stale pages (last_updated > 90 days)
  5) ODD_FENCE — log.md 등의 미닫힌 fenced code block ```. 미닫힘 시 strip_code_blocks 가
     EOF 까지 전체 mask → 그 안 wikilink silently strip → BROKEN_LINK silent miss.
  6) COUNT_MISMATCH — index.md 의 5-tier 카운트 정합 (00_meta/07 §2.4):
     · 헤더 line "Last updated: ..." 안 sources/entities/concepts/synthesis 4종
     · 섹션 헤더 ## Sources (N) / Entities (N) / Concepts (N) / Synthesis (N)
     · 하단 통계 블록 sources: / entities: / concepts: / synthesis:
     vs ground truth = wiki/<kind>/ 디렉토리 *.md 카운트.

Usage:
  python tools/lint.py
  python tools/lint.py --json
  python tools/lint.py --quiet
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
RAW = ROOT / "raw"
META = ROOT / "00_meta"

WIKILINK_RE = re.compile(r"\[\[([^\[\]\|\#]+?)(?:\#[^\[\]\|]+)?(?:\|[^\[\]]+)?\]\]")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

REQUIRED = {
    "source": ["type", "title", "slug", "source_path", "source_kind", "ingested"],
    "entity": ["type", "title", "kind"],
    "concept": ["type", "title"],
    "synthesis": ["type", "title", "created"],
}
STALE_DAYS = 90


def is_log_or_archive(slug: str) -> bool:
    """log.md (active) + archive/log-* (historical) 는 lint 의 broken-link / odd-fence skip.

    Cycle 5p+1 (2026-05-19) — log.md Option D compaction 으로 wiki/archive/ 하위
    log-YYYY-MM-weekN.md 같은 historical archive 가 생성됨. 이들도 본 함수로 일괄 skip.
    """
    return slug == "log" or slug.startswith("archive/")


def parse_frontmatter(text):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    out = {}
    for line in m.group(1).splitlines():
        line = line.rstrip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, _, v = line.partition(":")
        k = k.strip()
        v = v.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            if not inner:
                v = []
            else:
                v = [x.strip().strip('"').strip("'") for x in inner.split(",")]
        out[k] = v
    return out


def collect_pages(root):
    pages = {}
    for f in root.rglob("*.md"):
        rel = f.relative_to(root).with_suffix("").as_posix()
        pages[rel] = f
    return pages


def parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def lint(fix_trivial=False):
    if not WIKI.exists():
        return ([{"code": "NO_WIKI_DIR", "page": "", "detail": str(WIKI)}], {})

    pages = collect_pages(WIKI)
    rel_paths = set(pages.keys())
    basenames = {p.rsplit("/", 1)[-1] for p in rel_paths}

    # additional valid targets — raw/, 00_meta/, docs/ (vault root layers)
    DOCS = ROOT / "docs"
    for extra in (RAW, META, DOCS):
        if extra.exists():
            for f in extra.rglob("*.md"):
                rel_v = f.relative_to(ROOT).with_suffix("").as_posix()
                rel_paths.add(rel_v)
                basenames.add(rel_v.rsplit("/", 1)[-1])

    issues = []
    inbound = defaultdict(set)
    today = date.today()

    def strip_code_blocks(s: str, page_slug: str = "") -> str:
        """Replace fenced code blocks (```...```) and inline code (`...`) with
        same-length spaces, so wikilinks inside docs examples are not validated.

        Bugfix 2026-05-13: 미닫힌 fenced block 발견 시 *그대로 보존* (이전엔 EOF 까지
        mask → 그 안 wikilink silently strip → BROKEN_LINK silent miss). ODD_FENCE
        issue 별도 보고."""
        out = []
        i = 0
        n = len(s)
        def is_line_start_fence(pos):
            """``` at pos 가 line-start (직전 char 가 \\n 또는 pos=0) 인지."""
            if pos == 0:
                return True
            return s[pos - 1] in ("\n", "\r")

        while i < n:
            # Fenced code block ``` — *line-start* 만 fence 인정 (markdown spec)
            if s.startswith("```", i) and is_line_start_fence(i):
                # 다음 line-start ``` 찾기
                search_from = i + 3
                end = -1
                while search_from < n:
                    cand = s.find("```", search_from)
                    if cand < 0:
                        break
                    if is_line_start_fence(cand):
                        end = cand
                        break
                    search_from = cand + 3
                if end < 0:
                    # 미닫힘 — fence 만 mask, 이후 본문 보존
                    out.append("   ")        # ``` 만 mask
                    i += 3
                    # log.md (+ archive/log-*) = append-only history archive — fence balance 자연 깨짐, skip
                    if page_slug and not is_log_or_archive(page_slug):
                        odd_fence_pages.add(page_slug)
                    continue
                out.append(" " * (end + 3 - i))
                i = end + 3
                continue
            # Inline code `...`
            if s[i] == "`":
                end = s.find("`", i + 1)
                if 0 < end < n:
                    out.append(" " * (end + 1 - i))
                    i = end + 1
                    continue
            out.append(s[i])
            i += 1
        return "".join(out)

    odd_fence_pages = set()

    for slug, path in pages.items():
        text = path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        text_for_links = strip_code_blocks(text, slug)

        if fm is None:
            # index + log (active/archive) 는 frontmatter 의무 면제
            if slug != "index" and not is_log_or_archive(slug):
                issues.append({"code": "NO_FRONTMATTER", "page": slug, "detail": ""})
        else:
            ptype = fm.get("type")
            for required in REQUIRED.get(ptype, []):
                if required not in fm or fm[required] in ("", [], None):
                    issues.append({"code": "MISSING_FIELD", "page": slug, "detail": ptype + "/" + required})
            lu = fm.get("last_updated") or fm.get("ingested") or fm.get("created")
            d = parse_date(lu) if isinstance(lu, str) else None
            if d and (today - d) > timedelta(days=STALE_DAYS):
                issues.append({"code": "STALE", "page": slug, "detail": str((today - d).days) + " days"})

        for m in WIKILINK_RE.finditer(text_for_links):
            target = m.group(1).strip()
            inbound[target].add(slug)
            # log.md (+ archive/log-*) = append-only history archive — broken-link 검사 skip
            # (이전 entry 의 stale wikilink + 예시 placeholder 자연 발생)
            if is_log_or_archive(slug):
                continue
            if target in rel_paths or target in basenames:
                continue
            if target.endswith(".md"):
                bare = target[:-3]
                if bare in rel_paths or bare in basenames:
                    continue
            issues.append({"code": "BROKEN_LINK", "page": slug, "detail": target})

    for slug in pages:
        if slug in ("index", "log"):
            continue
        bn = slug.rsplit("/", 1)[-1]
        if not inbound.get(slug) and not inbound.get(bn):
            issues.append({"code": "ORPHAN", "page": slug, "detail": ""})

    # ODD_FENCE — 미닫힌 fenced block 보유 페이지
    for slug in sorted(odd_fence_pages):
        issues.append({"code": "ODD_FENCE", "page": slug, "detail": "unclosed ``` — wikilink silent-strip 위험"})

    # COUNT_MISMATCH — index.md 5-tier 카운트 vs ground truth (wiki/<kind>/ 디렉토리)
    index_path = WIKI / "index.md"
    if index_path.exists():
        index_text = index_path.read_text(encoding="utf-8")
        # ground truth — wiki/{sources,entities,concepts,synthesis}/*.md
        gt = {}
        for kind in ("sources", "entities", "concepts", "synthesis"):
            kd = WIKI / kind
            gt[kind] = len(list(kd.rglob("*.md"))) if kd.exists() else 0

        # tier 1 — 헤더 "N sources / N entities / N concepts / N synthesis"
        m = re.search(r"(\d+)\s*sources\s*/\s*(\d+)\s*entities\s*/\s*(\d+)\s*concepts\s*/\s*(\d+)\s*synthesis", index_text)
        if m:
            for idx, kind in enumerate(("sources", "entities", "concepts", "synthesis")):
                claimed = int(m.group(idx + 1))
                if claimed != gt[kind]:
                    issues.append({"code": "COUNT_MISMATCH", "page": "index",
                                   "detail": "tier1 header — " + kind + ": " + str(claimed) + " vs ground " + str(gt[kind])})

        # tier 2 — 섹션 헤더 "## Sources (N)" / Entities / Concepts / Synthesis
        for kind_cap, kind in (("Sources", "sources"), ("Entities", "entities"),
                                 ("Concepts", "concepts"), ("Synthesis", "synthesis")):
            sec = re.search(r"^##\s+" + kind_cap + r"\s*\((\d+)\)", index_text, re.MULTILINE)
            if sec:
                claimed = int(sec.group(1))
                if claimed != gt[kind]:
                    issues.append({"code": "COUNT_MISMATCH", "page": "index",
                                   "detail": "tier2 section — ## " + kind_cap + " (" + str(claimed) + ") vs ground " + str(gt[kind])})

        # tier 3 — 섹션 본문 wikilink 카탈로그 unique 카운트 vs ground truth
        # (한 sources/X wikilink 가 섹션 안/밖 여러 번 나와도 set 으로 dedup)
        for kind_cap, kind in (("Sources", "sources"), ("Entities", "entities"),
                                 ("Concepts", "concepts"), ("Synthesis", "synthesis")):
            sec_pat = re.compile(
                r"^##\s+" + kind_cap + r"\s*\(\d+\).*?(?=^##\s+\w|^---\s*$|\Z)",
                re.MULTILINE | re.DOTALL)
            sec_m = sec_pat.search(index_text)
            if not sec_m:
                continue
            sec_body = sec_m.group(0)
            # kind/X 형식 wikilink 만 매칭 (path 안 / 1개)
            link_pat = re.compile(r"\[\[" + kind + r"/([^\[\]\|\#\/]+?)(?:\#[^\[\]\|]+)?(?:\|[^\[\]]+)?\]\]")
            unique = set(link_pat.findall(sec_body))
            if len(unique) != gt[kind]:
                issues.append({"code": "COUNT_MISMATCH", "page": "index",
                               "detail": "tier3 catalog — " + kind + " section unique wikilinks: " +
                                         str(len(unique)) + " vs ground " + str(gt[kind])})

        # tier 4 — Ingest 진척도 표 row 별 카테고리 카운트 vs slug-prefix ground truth
        # 카테고리 → slug prefix 매핑
        category_prefix = {
            "CoreUObject": "ue-coreuobject-",
            "Components": "ue-components-",
            "GameFramework": "ue-gameframework-",
            "AssetClasses": "ue-assetclasses-",
            "Animation": "ue-animation-",
            "Input": "ue-input-",
            "Editor": "ue-editor-",
            "Slate": "ue-slate-",
            "SlateCore": "ue-slatecore-",
            "UMG": "ue-umg-",
            "Render": "ue-render-",
            "SpatialPartition": "ue-spatialpartition-",
            "Subsystem": "ue-subsystem-",
        }
        # ground truth — sources/ 안 prefix 별 카운트
        prefix_counts = {}
        if (WIKI / "sources").exists():
            for f in (WIKI / "sources").glob("*.md"):
                stem = f.stem
                for cat, prefix in category_prefix.items():
                    if stem.startswith(prefix):
                        prefix_counts[cat] = prefix_counts.get(cat, 0) + 1
                        break

        # 진척도 표 추출 — "## Ingest 진척도" 섹션 안 표
        table_pat = re.compile(r"##\s*Ingest\s*진척도.*?(?=^##\s|\Z)", re.MULTILINE | re.DOTALL)
        table_m = table_pat.search(index_text)
        seen_cats = set()
        if table_m:
            table_text = table_m.group(0)
            for line in table_text.split("\n"):
                line_stripped = line.strip()
                if not line_stripped.startswith("|") or "---" in line_stripped:
                    continue
                # 각 카테고리명 word boundary 매치
                for cat, prefix in category_prefix.items():
                    if not re.search(r"(?<![A-Za-z])" + re.escape(cat) + r"(?![A-Za-z])", line):
                        continue
                    if cat in seen_cats:
                        continue   # 이미 처리된 row (header 등)
                    # 두 번째 컬럼 (main + sub 또는 sum) 추출
                    cols = [c for c in line.split("|") if c.strip()]
                    if len(cols) < 2:
                        continue
                    second_col = cols[1]
                    # "= N" 합계 우선 — "1 + 9 + ... = 26"
                    total_match = re.search(r"=\s*(\d+)", second_col)
                    if total_match:
                        row_total = int(total_match.group(1))
                    else:
                        # 모든 숫자 합산 (단순 N + M + deep K 형식)
                        nums = re.findall(r"\d+", second_col)
                        row_total = sum(int(n) for n in nums)
                    seen_cats.add(cat)
                    gt_cnt = prefix_counts.get(cat, 0)
                    if row_total != gt_cnt:
                        issues.append({"code": "COUNT_MISMATCH", "page": "index",
                                       "detail": "tier4 progress — " + cat + " row=" + str(row_total) +
                                                 " vs ground (sources/" + prefix + "*) " + str(gt_cnt)})
                    break
        # 매핑된 카테고리 중 진척도 표에 없는 것
        for cat in category_prefix:
            if cat not in seen_cats and prefix_counts.get(cat, 0) > 0:
                issues.append({"code": "COUNT_MISMATCH", "page": "index",
                               "detail": "tier4 progress — " + cat + " row 누락 (ground " + str(prefix_counts[cat]) + ")"})

        # tier 5 — 하단 통계 블록 "sources:    N"
        for kind in ("sources", "entities", "concepts", "synthesis"):
            stat = re.search(r"^" + kind + r":\s+(\d+)", index_text, re.MULTILINE)
            if stat:
                claimed = int(stat.group(1))
                if claimed != gt[kind]:
                    issues.append({"code": "COUNT_MISMATCH", "page": "index",
                                   "detail": "tier5 footer — " + kind + ": " + str(claimed) + " vs ground " + str(gt[kind])})

    summary = {"pages": len(pages), "issues": len(issues), "by_code": {}}
    for it in issues:
        summary["by_code"][it["code"]] = summary["by_code"].get(it["code"], 0) + 1

    return issues, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    issues, summary = lint()

    if args.json:
        print(json.dumps({"issues": issues, "summary": summary}, ensure_ascii=False, indent=2))
    else:
        print("Lint: " + str(summary.get("pages", 0)) + " pages, " + str(summary.get("issues", 0)) + " issues.")
        if not args.quiet:
            for it in issues:
                print("  [" + it["code"] + "] " + it["page"] + "  " + it["detail"])
        for code, n in sorted(summary.get("by_code", {}).items()):
            print("  - " + code + ": " + str(n))

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
