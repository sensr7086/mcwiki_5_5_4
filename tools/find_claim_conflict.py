"""
mcwiki MCP server tool #3 v0.5.5 — find_claim_conflict (heuristic + Korean filter)
==================================================================================

**v0.5.5 변경 (Cycle 5p #1 — 한국어 단위 명사 false positive 회피)**:
- `OBJECT_BEFORE_NUMBER_RE` 추가 — 숫자+단위 직전 객체 명사 추출.
- `find_numeric_conflicts` 에서 (keyword, object) 페어로 묶음 — 객체 명사 다르면 비교 제외.
- Cycle 5m audit 의 4 false positive (8종 EAssetEditorCloseReason vs 11종 UE 글로벌 매크로 등) 자동 강등.

**v0.5.1 (Cycle 5l rollback)**:
- LLM mode (use_llm 옵션 + Claude Sonnet 호출 + anthropic SDK 통합) **제거**.
- Cycle 5j 의 휴리스틱 mode 만 유지 — 복잡도 + 외부 의존성 회피.

**v0.4.0 (Cycle 5j) 휴리스틱 mode**:
- 4 claim 패턴 추출 (section headers / numeric / tier 분포 / API 시그니처)
- 3 충돌 카테고리 보고 (numeric_mismatch / tier_distribution_mismatch / api_signature_conflict)

vault 명세: [[sources/ue-meta-baseline-grep-system]] §5.2

**한국어 단위 명사 패턴**:
- 단위 명사 (종/개/함정/대/회/메소드/메서드 등) 의 false positive 회피.
- 같은 단위 명사라도 객체 명사 (앞쪽 1~3 단어) 다르면 다른 entity 가리킴.
- 예: "EAssetEditorCloseReason 8종" vs "UE 글로벌 매크로 11종" — object 다름 → conflict X.
- 예: "TWeakObjectPtr 회피 패턴 3종" vs "UCharacterMovementComponent 5종 모드" — object 다름 → conflict X.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# === 휴리스틱 mode ===

SECTION_HEADER_RE = re.compile(r"^#+\s+(.+?)$", re.MULTILINE)
NUMERIC_CLAIM_RE = re.compile(r"(\d+)\s*(PURE_VIRTUAL|virtual|메소드|메서드|함정|개|종|호스트|파라미터|param|대|회)", re.IGNORECASE)
TIER_DIST_RE = re.compile(r"🟢\s*(\d+)\s*/\s*🟡\s*(\d+)\s*/\s*🔴\s*(\d+)")
API_SIG_RE = re.compile(r"\b([A-Z][a-zA-Z0-9]+(?:::[a-zA-Z0-9_]+)+)\s*\(")

# v0.5.5 (Cycle 5p #1) — 숫자+단위 직전 객체 명사 추출.
# - 영문 PascalCase / camelCase / snake_case / scoped (e.g., FString::Trim)
# - 한글 1~3 단어 (각 단어는 1+ 한글 문자)
# - "한글 + 영문" 혼합 (예: "UE 글로벌 매크로", "Niagara 에디터 모듈")
OBJECT_BEFORE_NUMBER_RE = re.compile(
    r"((?:[A-Za-z][A-Za-z0-9_]*(?:::[A-Za-z0-9_]+)*"     # 영문 식별자 (스코프 가능)
    r"|[가-힣]+)"                                          # 또는 한글 단어
    r"(?:\s+(?:[A-Za-z][A-Za-z0-9_]*|[가-힣]+)){0,2})"     # + 추가 1~2 단어 (영문/한글)
    r"\s+(\d+)\s*(PURE_VIRTUAL|virtual|메소드|메서드|함정|개|종|호스트|파라미터|param|대|회)",
    re.IGNORECASE,
)

# 한국어 단위 명사 — 객체 명사 다르면 자동 강등 대상.
KOREAN_UNIT_NOUNS = {"종", "개", "함정", "대", "회", "호스트"}

VALID_KINDS = {"sources", "entities", "concepts", "synthesis", "meta", "00_meta"}


def _kind_root(kind: str, vault_root: Path) -> Path:
    """kind 별 디렉토리 경로 — `00_meta` 는 vault parent (lint.py / find_cross_link_broken.py 정합, Cycle 5p+1 fix)."""
    if kind == "00_meta":
        return vault_root.parent / "00_meta"
    if kind == "meta":
        return vault_root.parent / "00_meta"   # alias (mcp_server.py _normalize_kind 와 페어)
    return vault_root / kind


def extract_object_before_number(line: str, number: int, unit: str) -> str:
    """line 안에서 (숫자 + 단위) 직전 객체 명사 추출.

    Returns:
        object name (upper) — 매칭 실패 시 "".
    """
    unit_norm = unit.strip().upper()
    for m in OBJECT_BEFORE_NUMBER_RE.finditer(line):
        if int(m.group(2)) != number:
            continue
        if m.group(3).strip().upper() != unit_norm:
            continue
        return m.group(1).strip().upper()
    return ""


def auto_detect_kind(slug: str, vault_root: Path) -> Optional[str]:
    for kind in VALID_KINDS:
        if (_kind_root(kind, vault_root) / f"{slug}.md").is_file():
            return kind
    return None


def extract_claims(content: str) -> Dict[str, List[Tuple]]:
    """claim 4 패턴 추출.

    v0.5.5: numeric_claims 튜플이 (line_no, raw_match, object_name) 3-tuple — 객체 명사 포함.
    """
    claims: Dict[str, List[Tuple]] = {
        "section_headers": [],
        "numeric_claims": [],
        "tier_dists": [],
        "api_signatures": [],
    }
    for line_no, line in enumerate(content.splitlines(), start=1):
        for m in SECTION_HEADER_RE.finditer(line):
            claims["section_headers"].append((line_no, m.group(1).strip()))
        for m in NUMERIC_CLAIM_RE.finditer(line):
            number = int(m.group(1))
            unit = m.group(2)
            obj = extract_object_before_number(line, number, unit)
            claims["numeric_claims"].append((line_no, m.group(0), obj))
        for m in TIER_DIST_RE.finditer(line):
            claims["tier_dists"].append((line_no, f"🟢 {m.group(1)} / 🟡 {m.group(2)} / 🔴 {m.group(3)}"))
        for m in API_SIG_RE.finditer(line):
            claims["api_signatures"].append((line_no, m.group(1)))
    return claims


def _unpack_numeric_claim(tup: Tuple) -> Tuple[int, str, str]:
    """numeric_claim 튜플 unpack — backward compat (2-tuple) + v0.5.5 3-tuple."""
    if len(tup) == 3:
        return tup
    line, claim = tup
    return line, claim, ""


def find_numeric_conflicts(
    a_claims: List[Tuple], b_claims: List[Tuple],
) -> List[Dict]:
    """수치 claim 불일치 검출.

    v0.5.5 (Cycle 5p #1): (keyword, object) 페어로 묶음 — 한국어 단위 명사 false positive 회피.
    - 한국어 단위 (종/개/함정/대/회/호스트) 면서 객체 명사 다름 → conflict 제외 (false positive 강등).
    - 객체 명사 같거나 영문 단위 명사 (PURE_VIRTUAL/virtual/메소드 등) → 종전대로 비교.
    """
    conflicts = []
    # key = (keyword_upper, object_upper). object 없으면 "".
    a_by_key: Dict[Tuple[str, str], List[Tuple[int, int]]] = {}
    b_by_key: Dict[Tuple[str, str], List[Tuple[int, int]]] = {}

    for tup in a_claims:
        line, claim, obj = _unpack_numeric_claim(tup)
        m = NUMERIC_CLAIM_RE.match(claim)
        if not m:
            continue
        keyword = m.group(2).strip().upper()
        a_by_key.setdefault((keyword, obj), []).append((line, int(m.group(1))))

    for tup in b_claims:
        line, claim, obj = _unpack_numeric_claim(tup)
        m = NUMERIC_CLAIM_RE.match(claim)
        if not m:
            continue
        keyword = m.group(2).strip().upper()
        b_by_key.setdefault((keyword, obj), []).append((line, int(m.group(1))))

    # 정확 매칭 — 같은 (keyword, object) 페어.
    # 한국어 단위 + 객체 미식별 (obj="") 페어는 false positive 추정 → 자동 low 강등.
    korean_units_upper = {n.upper() for n in KOREAN_UNIT_NOUNS}
    common = set(a_by_key.keys()) & set(b_by_key.keys())
    for key in common:
        keyword, obj = key
        a_counts = {c for _, c in a_by_key[key]}
        b_counts = {c for _, c in b_by_key[key]}
        if a_counts == b_counts or (a_counts & b_counts):
            continue
        # Korean filter: 객체 미식별 + 한국어 단위 → low + note.
        is_korean_unidentified = (not obj) and (keyword in korean_units_upper)
        if is_korean_unidentified:
            entry = {
                "type": "numeric_mismatch",
                "keyword": keyword,
                "object": "(unidentified — likely false positive)",
                "a_lines": [list(t) for t in a_by_key[key]],
                "b_lines": [list(t) for t in b_by_key[key]],
                "severity": "low",
                "note": "Korean unit noun without identifiable object — heuristic strongly suggests false positive (다른 entity).",
            }
        else:
            entry = {
                "type": "numeric_mismatch",
                "keyword": keyword,
                "object": obj or "(unspecified)",
                "a_lines": [list(t) for t in a_by_key[key]],
                "b_lines": [list(t) for t in b_by_key[key]],
                "severity": "high" if abs(max(a_counts) - max(b_counts)) > 1 else "med",
            }
        conflicts.append(entry)
    return conflicts


def find_tier_conflicts(
    a_claims: List[Tuple[int, str]], b_claims: List[Tuple[int, str]],
) -> List[Dict]:
    """tier 분포 불일치."""
    if not a_claims or not b_claims:
        return []
    a_first = a_claims[0]
    b_first = b_claims[0]
    if a_first[1] != b_first[1]:
        return [{
            "type": "tier_distribution_mismatch",
            "a_line": a_first[0],
            "a_dist": a_first[1],
            "b_line": b_first[0],
            "b_dist": b_first[1],
            "severity": "med",
        }]
    return []


def find_api_signature_conflicts(
    a_claims: List[Tuple[int, str]], b_claims: List[Tuple[int, str]],
) -> List[Dict]:
    """공통 API 패턴 부재 (확장 후속)."""
    a_apis = {api for _, api in a_claims}
    b_apis = {api for _, api in b_claims}
    if a_apis and b_apis and not (a_apis & b_apis):
        return [{
            "type": "api_signature_conflict",
            "a_apis_sample": sorted(a_apis)[:3],
            "b_apis_sample": sorted(b_apis)[:3],
            "severity": "low",
            "note": "common API pattern not found (heuristic — may be unrelated pages)",
        }]
    return []


def find_claim_conflict_handler(
    slug_a: str,
    slug_b: str,
    kind_a: Optional[str] = None,
    kind_b: Optional[str] = None,
    vault_root: Optional[Path] = None,
) -> Dict:
    """
    두 페이지의 claim 충돌 검출 (휴리스틱 mode only — v0.5.1).

    Args:
        slug_a, slug_b: 비교 대상 페이지 slug 2개
        kind_a, kind_b: 각 페이지 kind (옵션 — None 이면 자동 추론)
        vault_root: vault 의 wiki 디렉토리 절대 경로

    Returns:
        {
            "slug_a": str, "kind_a": str,
            "slug_b": str, "kind_b": str,
            "mode": "heuristic",
            "conflict_count": int,
            "conflicts": [
                {"type": "numeric_mismatch", "keyword": "...", "a_lines": [...], "b_lines": [...], "severity": "..."},
                {"type": "tier_distribution_mismatch", ...},
                {"type": "api_signature_conflict", ...}
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

    def _load(slug: str, kind: Optional[str]) -> Tuple[str, str, Optional[str]]:
        if kind is None:
            kind = auto_detect_kind(slug, vault_root)
            if kind is None:
                return "", "", f"page not found: {slug}"
        path = _kind_root(kind, vault_root) / f"{slug}.md"
        if not path.is_file():
            return kind, "", f"page not found: {path}"
        return kind, path.read_text(encoding="utf-8", errors="replace"), None

    kind_a, content_a, err_a = _load(slug_a, kind_a)
    if err_a:
        return {"slug_a": slug_a, "slug_b": slug_b, "error": err_a}
    kind_b, content_b, err_b = _load(slug_b, kind_b)
    if err_b:
        return {"slug_a": slug_a, "slug_b": slug_b, "error": err_b}

    a_claims = extract_claims(content_a)
    b_claims = extract_claims(content_b)

    conflicts = []
    conflicts.extend(find_numeric_conflicts(a_claims["numeric_claims"], b_claims["numeric_claims"]))
    conflicts.extend(find_tier_conflicts(a_claims["tier_dists"], b_claims["tier_dists"]))
    conflicts.extend(find_api_signature_conflicts(a_claims["api_signatures"], b_claims["api_signatures"]))

    return {
        "slug_a": slug_a, "kind_a": kind_a,
        "slug_b": slug_b, "kind_b": kind_b,
        "mode": "heuristic",
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
    }
