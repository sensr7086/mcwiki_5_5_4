"""
mcwiki MCP server tool #4 — find_stale_baseline
================================================

페이지 last_updated 기준 + 의존 페이지의 변경 추적 — staleness 검출.

Cycle 5j #4 PR 코드 (Cycle 5h #3 §6.6 후속 PR #5).

vault 명세: [[sources/ue-meta-baseline-grep-system]] §5.3

활용 케이스:
- 분기별 audit (`18_ModelEvolutionAudit` 절차)
- ue-audit-agent 가 자동 호출 → ✅ 페이지 갱신 후보 분류
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Frontmatter 파싱 정규식
FRONTMATTER_RE = re.compile(r"^---\n(.+?)\n---", re.DOTALL)
DATE_RE = re.compile(r"^last_updated:\s*(\d{4}-\d{2}-\d{2})", re.MULTILINE)
INGESTED_RE = re.compile(r"^ingested:\s*(\d{4}-\d{2}-\d{2})", re.MULTILINE)
SOURCE_DATE_RE = re.compile(r"^source_date:\s*(\d{4}-\d{2}-\d{2})", re.MULTILINE)

# Wikilink — 의존 페이지 추출
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
INLINE_CODE_RE = re.compile(r"`[^`]+`")

VALID_KINDS = {"sources", "entities", "concepts", "synthesis", "meta", "00_meta"}


def _kind_root(kind: str, vault_root: Path) -> Path:
    """kind 별 디렉토리 경로 — `00_meta` 는 vault parent (lint.py / find_cross_link_broken.py 정합, Cycle 5p+1 fix)."""
    if kind == "00_meta":
        return vault_root.parent / "00_meta"
    if kind == "meta":
        return vault_root.parent / "00_meta"   # alias (mcp_server.py _normalize_kind 와 페어)
    return vault_root / kind


def strip_code_blocks(content: str) -> str:
    """code block + inline code 제거."""
    content = CODE_BLOCK_RE.sub("", content)
    content = INLINE_CODE_RE.sub("", content)
    return content


def parse_target(target: str) -> Tuple[Optional[str], str]:
    target = target.strip()
    if "|" in target:
        target = target.split("|", 1)[0].strip()
    if "/" in target:
        kind, slug = target.split("/", 1)
        if kind in VALID_KINDS:
            return kind, slug
    return None, target


def auto_detect_kind(slug: str, vault_root: Path) -> Optional[str]:
    for kind in VALID_KINDS:
        if (_kind_root(kind, vault_root) / f"{slug}.md").is_file():
            return kind
    return None


def parse_frontmatter_dates(content: str) -> Dict[str, Optional[date]]:
    """frontmatter 에서 last_updated / ingested / source_date 추출."""
    fm_match = FRONTMATTER_RE.match(content)
    if not fm_match:
        return {"last_updated": None, "ingested": None, "source_date": None}
    fm = fm_match.group(1)

    def _parse(re_pat):
        m = re_pat.search(fm)
        if not m:
            return None
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d").date()
        except ValueError:
            return None

    return {
        "last_updated": _parse(DATE_RE),
        "ingested": _parse(INGESTED_RE),
        "source_date": _parse(SOURCE_DATE_RE),
    }


def extract_dependent_pages(content: str, vault_root: Path) -> List[Tuple[str, str]]:
    """본문의 wikilinks → 의존 페이지 (kind, slug) 리스트."""
    content_stripped = strip_code_blocks(content)
    deps = []
    seen = set()
    for match in WIKILINK_RE.finditer(content_stripped):
        target = match.group(1)
        kind, slug = parse_target(target)
        if not kind:
            kind = auto_detect_kind(slug, vault_root) or ""
        if kind and (kind, slug) not in seen:
            deps.append((kind, slug))
            seen.add((kind, slug))
    return deps


def find_stale_baseline_handler(
    slug: str,
    kind: Optional[str] = None,
    threshold_days: int = 90,
    vault_root: Optional[Path] = None,
) -> Dict:
    """
    페이지 staleness 검출.

    Args:
        slug: 검증할 페이지 slug
        kind: 페이지 kind (옵션)
        threshold_days: stale 임계값 (default 90 — 분기 단위)
        vault_root: vault 의 wiki 디렉토리 절대 경로

    Returns:
        {
            "slug": str, "kind": str,
            "last_updated": "YYYY-MM-DD" or None,
            "age_days": int or None,
            "is_stale": bool,                          # last_updated > threshold_days
            "dependent_changes": [
                {
                    "dep_kind": str, "dep_slug": str,
                    "dep_last_updated": "YYYY-MM-DD",
                    "change_after_baseline": bool      # dep 가 본 페이지 작성 후 갱신됨
                },
                ...
            ],
            "change_after_count": int   # change_after_baseline=true 개수
        }
    """
    if vault_root is None:
        import os
        vault_root_str = os.environ.get("MCWIKI_VAULT_ROOT")
        if not vault_root_str:
            raise ValueError("MCWIKI_VAULT_ROOT 환경변수 또는 vault_root 인자 필요")
        vault_root = Path(vault_root_str)
    vault_root = Path(vault_root)

    # 1. kind 추론 + 페이지 로드
    if kind is None:
        kind = auto_detect_kind(slug, vault_root)
        if kind is None:
            return {"slug": slug, "kind": None, "error": f"page not found: {slug}"}

    page_path = _kind_root(kind, vault_root) / f"{slug}.md"
    if not page_path.is_file():
        return {"slug": slug, "kind": kind, "error": f"page not found: {page_path}"}

    content = page_path.read_text(encoding="utf-8", errors="replace")
    fm_dates = parse_frontmatter_dates(content)
    baseline_date = fm_dates["last_updated"] or fm_dates["ingested"] or fm_dates["source_date"]

    if baseline_date is None:
        return {
            "slug": slug, "kind": kind,
            "last_updated": None,
            "age_days": None,
            "is_stale": False,
            "dependent_changes": [],
            "change_after_count": 0,
            "warning": "no last_updated / ingested / source_date in frontmatter",
        }

    today = date.today()
    age_days = (today - baseline_date).days
    is_stale = age_days > threshold_days

    # 2. 의존 페이지 추적
    deps = extract_dependent_pages(content, vault_root)
    dependent_changes = []

    for dep_kind, dep_slug in deps:
        dep_path = _kind_root(dep_kind, vault_root) / f"{dep_slug}.md"
        if not dep_path.is_file():
            continue
        try:
            dep_content = dep_path.read_text(encoding="utf-8", errors="replace")
        except (UnicodeDecodeError, OSError):
            continue
        dep_dates = parse_frontmatter_dates(dep_content)
        dep_baseline = dep_dates["last_updated"] or dep_dates["ingested"]
        if dep_baseline is None:
            continue
        change_after_baseline = dep_baseline > baseline_date
        if change_after_baseline:
            dependent_changes.append({
                "dep_kind": dep_kind,
                "dep_slug": dep_slug,
                "dep_last_updated": dep_baseline.isoformat(),
                "change_after_baseline": True,
            })

    return {
        "slug": slug, "kind": kind,
        "last_updated": baseline_date.isoformat(),
        "age_days": age_days,
        "is_stale": is_stale,
        "dependent_changes": dependent_changes,
        "change_after_count": len(dependent_changes),
    }


# === 테스트 ====================================================================

def test_parse_frontmatter_dates():
    sample = """---
type: source
slug: ue-x
last_updated: 2026-05-15
ingested: 2026-05-09
source_date: 2026-05-08
---

# X
"""
    dates = parse_frontmatter_dates(sample)
    assert dates["last_updated"] == date(2026, 5, 15)
    assert dates["ingested"] == date(2026, 5, 9)
    assert dates["source_date"] == date(2026, 5, 8)
    print("parse_frontmatter_dates: PASS")


def test_find_stale_baseline_on_uobject():
    import os
    vault_root = Path(os.environ.get("MCWIKI_VAULT_ROOT", ""))
    if not vault_root.is_dir():
        print(f"SKIP: vault_root not found")
        return
    result = find_stale_baseline_handler("ue-coreuobject-uobject", vault_root=vault_root, threshold_days=30)
    print(f"uobject: last_updated {result.get('last_updated')}, age {result.get('age_days')}d, stale={result.get('is_stale')}")
    print(f"  dependent changes (after baseline): {result.get('change_after_count')}")


if __name__ == "__main__":
    test_parse_frontmatter_dates()
    test_find_stale_baseline_on_uobject()
