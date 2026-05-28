"""
mcwiki MCP server tool #2 — suggest_missing_cross_link
======================================================

전역 backlink 분석으로 누락 cross-link 추천.
다른 페이지가 `slug` 를 cross-link 하지만, `slug` 가 그 페이지로 reverse-link 하지 않은 경우 추천.

Cycle 5j #2 PR 코드 (Cycle 5h #3 §6.6 후속 PR #3).

vault 명세: [[sources/ue-meta-baseline-grep-system]] §5.4 + §6.6

도구 #1 `find_cross_link_broken` 의 wikilink 추출 / kind 추론 로직 재사용.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Wikilink 정규식 — 도구 #1 과 동일
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")

# 페이지 kind enum
VALID_KINDS = {"sources", "entities", "concepts", "synthesis", "meta", "00_meta"}


def _kind_root(kind: str, vault_root: Path) -> Path:
    """kind 별 디렉토리 경로 — `00_meta` 는 vault parent (lint.py / find_cross_link_broken.py 정합, Cycle 5p+1 fix)."""
    if kind == "00_meta":
        return vault_root.parent / "00_meta"
    if kind == "meta":
        return vault_root.parent / "00_meta"   # alias (mcp_server.py _normalize_kind 와 페어)
    return vault_root / kind


# 코드 블록 안 wikilink 무시 패턴 — Cycle 5j Phase 1 false positive 회피
CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
INLINE_CODE_RE = re.compile(r"`[^`]+`")


def strip_code_blocks(content: str) -> str:
    """code block + inline code 제거 — wikilink 추출 시 false positive 회피."""
    content = CODE_BLOCK_RE.sub("", content)
    content = INLINE_CODE_RE.sub("", content)
    return content


def parse_target(target: str) -> Tuple[Optional[str], str]:
    """[[wikilink]] target → (kind, slug). 도구 #1 과 동일."""
    target = target.strip()
    if "|" in target:
        target = target.split("|", 1)[0].strip()
    if "/" in target:
        kind, slug = target.split("/", 1)
        if kind in VALID_KINDS:
            return kind, slug
    return None, target


def auto_detect_kind(slug: str, vault_root: Path) -> Optional[str]:
    """slug 의 kind 자동 추론."""
    for kind in VALID_KINDS:
        target = _kind_root(kind, vault_root) / f"{slug}.md"
        if target.is_file():
            return kind
    return None


def extract_wikilinks(content: str) -> List[Tuple[str, str]]:
    """본문에서 wikilink 추출 — (target_kind, target_slug) 튜플 리스트.
    code block / inline code 안 wikilink 는 무시 (false positive 회피)."""
    content_stripped = strip_code_blocks(content)
    results = []
    for match in WIKILINK_RE.finditer(content_stripped):
        target = match.group(1)
        kind, slug = parse_target(target)
        results.append((kind or "", slug))
    return results


# v0.5.3 (Cycle 5n #3) — 모듈 레벨 백링크 인덱스 캐시.
# Process lifetime 동안 vault content 변경 시점 (file count + max mtime) 감지하여 invalidate.
_BACKLINK_CACHE: Dict[str, Tuple[Tuple[int, float], Dict[Tuple[str, str], List[Tuple[str, str]]]]] = {}


def _vault_signature(vault_root: Path) -> Tuple[int, float]:
    """vault content 변경 감지 signature — (file count, max mtime).

    stat 만 호출하므로 read_text 보다 ~100x 빠름.
    """
    count = 0
    max_mtime = 0.0
    for kind in VALID_KINDS:
        kind_dir = _kind_root(kind, vault_root)
        if not kind_dir.is_dir():
            continue
        for p in kind_dir.glob("*.md"):
            count += 1
            try:
                m = p.stat().st_mtime
                if m > max_mtime:
                    max_mtime = m
            except OSError:
                pass
    return (count, max_mtime)


def _build_backlink_index_uncached(vault_root: Path) -> Dict[Tuple[str, str], List[Tuple[str, str]]]:
    """vault 전체를 스캔 → 역색인. 캐시 미스 시만 호출."""
    index: Dict[Tuple[str, str], List[Tuple[str, str]]] = {}
    for kind in VALID_KINDS:
        kind_dir = _kind_root(kind, vault_root)
        if not kind_dir.is_dir():
            continue
        for page_path in kind_dir.glob("*.md"):
            source_slug = page_path.stem
            source_key = (kind, source_slug)
            try:
                content = page_path.read_text(encoding="utf-8", errors="replace")
            except (UnicodeDecodeError, OSError):
                continue
            wikilinks = extract_wikilinks(content)
            for target_kind, target_slug in wikilinks:
                if not target_kind:
                    target_kind = auto_detect_kind(target_slug, vault_root) or ""
                if not target_kind:
                    continue   # broken — suggest 대상 아님
                target_key = (target_kind, target_slug)
                index.setdefault(target_key, []).append(source_key)
    return index


def build_global_backlink_index(vault_root: Path) -> Dict[Tuple[str, str], List[Tuple[str, str]]]:
    """vault 전체 역색인. v0.5.3 — 캐시 hit 시 stat-only check 후 즉시 반환.

    Returns:
        {("sources", "ue-editor-asseteditorapi"): [("sources", "mc-combo-editor-levelsequence-lite"), ...]}
    """
    key = str(vault_root)
    sig = _vault_signature(vault_root)
    cached = _BACKLINK_CACHE.get(key)
    if cached is not None and cached[0] == sig:
        return cached[1]
    # cache miss — 재빌드
    index = _build_backlink_index_uncached(vault_root)
    _BACKLINK_CACHE[key] = (sig, index)
    return index


def invalidate_backlink_cache(vault_root: Optional[Path] = None) -> None:
    """캐시 수동 invalidate — write_page 등 vault 변경 후 호출 가능 (옵션).

    vault_root 미지정 시 전체 캐시 비움.
    """
    if vault_root is None:
        _BACKLINK_CACHE.clear()
    else:
        _BACKLINK_CACHE.pop(str(vault_root), None)


def suggest_missing_cross_link_handler(
    slug: str,
    kind: Optional[str] = None,
    vault_root: Optional[Path] = None,
    min_inbound: int = 1,
) -> Dict:
    """
    본 페이지에 누락된 cross-link 후보 추천.

    Args:
        slug: 검증할 페이지 slug
        kind: 페이지 kind (옵션 — None 이면 자동 추론)
        vault_root: vault 의 wiki 디렉토리 절대 경로
        min_inbound: 최소 inbound 횟수 (default 1)

    Returns:
        {
            "slug": str,
            "kind": str,
            "outbound_count": int,             # 본 페이지가 가진 wikilink 수
            "inbound_count": int,              # 다른 페이지가 본 페이지 가리키는 횟수
            "suggestions": [
                {
                    "source_slug": str,        # 본 페이지를 가리키는 페이지
                    "source_kind": str,
                    "inbound_count": int,      # 해당 source 가 본 페이지 가리키는 횟수
                    "confidence": "high|med|low",   # 카테고리 일치 + 횟수
                    "is_reverse_linked": bool, # 본 페이지가 그 source 로 reverse-link 하는지
                    "missing": bool            # reverse-link 누락 여부 (true = 추천)
                },
                ...
            ]
        }
    """
    if vault_root is None:
        import os
        vault_root_str = os.environ.get("MCWIKI_VAULT_ROOT")
        if not vault_root_str:
            raise ValueError("MCWIKI_VAULT_ROOT 환경변수 또는 vault_root 인자 필요")
        vault_root = Path(vault_root_str)
    vault_root = Path(vault_root)

    # 1. 본 페이지 kind 추론
    if kind is None:
        kind = auto_detect_kind(slug, vault_root)
        if kind is None:
            return {"slug": slug, "kind": None, "error": f"page not found: {slug}"}

    page_path = _kind_root(kind, vault_root) / f"{slug}.md"
    if not page_path.is_file():
        return {"slug": slug, "kind": kind, "error": f"page not found: {page_path}"}

    content = page_path.read_text(encoding="utf-8", errors="replace")

    # 2. 본 페이지의 outbound wikilinks
    outbound = extract_wikilinks(content)
    outbound_targets = set()
    for target_kind, target_slug in outbound:
        if not target_kind:
            target_kind = auto_detect_kind(target_slug, vault_root) or ""
        if target_kind:
            outbound_targets.add((target_kind, target_slug))

    # 3. 전역 backlink 인덱스
    backlink_index = build_global_backlink_index(vault_root)
    inbound_sources = backlink_index.get((kind, slug), [])
    inbound_counter = Counter(inbound_sources)

    # 4. 추천 후보 생성
    suggestions = []
    for source_key, count in inbound_counter.most_common():
        if count < min_inbound:
            continue
        source_kind, source_slug = source_key
        is_reverse_linked = source_key in outbound_targets
        missing = not is_reverse_linked

        # confidence — 카테고리 일치 + inbound 횟수
        if source_kind == kind and count >= 3:
            confidence = "high"
        elif source_kind == kind or count >= 3:
            confidence = "med"
        else:
            confidence = "low"

        suggestions.append({
            "source_slug": source_slug,
            "source_kind": source_kind,
            "inbound_count": count,
            "confidence": confidence,
            "is_reverse_linked": is_reverse_linked,
            "missing": missing,
        })

    return {
        "slug": slug,
        "kind": kind,
        "outbound_count": len(outbound_targets),
        "inbound_count": sum(inbound_counter.values()),
        "suggestions": suggestions,
    }


# === 테스트 ====================================================================

def test_suggest_missing_cross_link_on_uobject():
    """uobject 페이지 — KMCProject MC 시리즈 + assetclasses 등 다수 inbound 기대."""
    import os
    vault_root = Path(os.environ.get("MCWIKI_VAULT_ROOT", ""))
    if not vault_root.is_dir():
        print(f"SKIP: vault_root not found: {vault_root}")
        return

    result = suggest_missing_cross_link_handler("ue-coreuobject-uobject", vault_root=vault_root)
    print(f"uobject: outbound {result['outbound_count']} / inbound {result['inbound_count']}")
    missing = [s for s in result["suggestions"] if s["missing"]]
    print(f"missing reverse-links: {len(missing)}")
    for s in missing[:5]:
        print(f"  - {s['source_kind']}/{s['source_slug']} ({s['inbound_count']}x, {s['confidence']})")


def test_strip_code_blocks():
    """code block 안 wikilink 무시 단위 테스트 — Cycle 5j Phase 1 false positive 회피."""
    sample = """
    실제 [[sources/ue-x]] 인용.

    ```python
    # 코드 안 [[wikilink]] 는 무시
    pattern = r"\\[\\[([^\\]]+)\\]\\]"
    ```

    inline `[[code-example]]` 도 무시.

    [[concepts/Real-Link]] 인용 2.
    """
    stripped = strip_code_blocks(sample)
    wikilinks = WIKILINK_RE.findall(stripped)
    assert "sources/ue-x" in wikilinks
    assert "concepts/Real-Link" in wikilinks
    assert "wikilink" not in wikilinks   # code block 안
    assert "code-example" not in wikilinks   # inline code 안
    print(f"strip_code_blocks: PASS ({len(wikilinks)} valid wikilinks)")


if __name__ == "__main__":
    test_strip_code_blocks()
    test_suggest_missing_cross_link_on_uobject()
