"""
mcwiki MCP server tool #3 v0.4.1 — find_claim_conflict (LLM mode)
==================================================================

**v0.4.0 → v0.4.1 변경 (Cycle 5k Phase 3)**:
- LLM mode 추가 — Claude Haiku 3.5 호출로 휴리스틱 false positive 회피
- v0.4.0 (Cycle 5j) 의 휴리스틱 mode 한계 보완:
  - keyword "종" / "개" 등 일반 단어 → false positive (Cycle 5k Phase 1 검증에서 발견)
  - 휴리스틱이 잡지 못하는 의미적 충돌 (e.g., "Persona 5 모드" vs "Persona 4 모드")

**Cycle 5k Phase 1 실측 false positive**:
- `find_claim_conflict("ue-editor-asseteditorapi", "ue-editor-personatoolkit")` →
  numeric_mismatch keyword="종", line a:45 (8종) vs b:315 (11종), severity=high
- 실제로는 다른 문맥 — asseteditorapi 의 "8종 EAssetEditorCloseReason" vs personatoolkit 의 "11종 카탈로그 사례". 충돌 아님.

vault 명세: [[sources/ue-meta-baseline-grep-system]] §5.2 + §5.6 (LLM mode 후속 PR)

LLM provider: Claude Haiku 3.5 (`claude-haiku-4-5-20251001` 또는 v0.4.1 시점 최신).
환경변수: `ANTHROPIC_API_KEY` (또는 `MCWIKI_LLM_PROVIDER` 통합).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# === 휴리스틱 mode (v0.4.0 그대로 — 재사용) ===

SECTION_HEADER_RE = re.compile(r"^#+\s+(.+?)$", re.MULTILINE)
NUMERIC_CLAIM_RE = re.compile(r"(\d+)\s*(PURE_VIRTUAL|virtual|메소드|메서드|함정|개|종|호스트|파라미터|param)", re.IGNORECASE)
TIER_DIST_RE = re.compile(r"🟢\s*(\d+)\s*/\s*🟡\s*(\d+)\s*/\s*🔴\s*(\d+)")
API_SIG_RE = re.compile(r"\b([A-Z][a-zA-Z0-9]+(?:::[a-zA-Z0-9_]+)+)\s*\(")

VALID_KINDS = {"sources", "entities", "concepts", "synthesis", "meta", "00_meta"}


# === LLM mode 신규 (Cycle 5k Phase 3) ===

LLM_VERIFICATION_PROMPT = """\
두 UE 5.7.4 vault 페이지의 claim 충돌 검증:

페이지 A (`{slug_a}`) 라인 {line_a}:
"{context_a}"

페이지 B (`{slug_b}`) 라인 {line_b}:
"{context_b}"

키워드: "{keyword}" (수치 A={count_a}, B={count_b})

**판단 기준**:
1. 두 라인이 *같은 주제 / 같은 객체* 에 대한 수치 claim 인가?
2. 만약 같은 주제면 — 수치 불일치는 실제 충돌 (vault 정정 필요).
3. 만약 다른 주제면 — 휴리스틱 false positive. 충돌 아님.

**JSON 응답** (다른 텍스트 없이):
{{
  "is_real_conflict": true|false,
  "reason": "1-2문장 한국어 설명",
  "suggested_action": "vault 정정 필요 (slug_a 또는 slug_b)" | "false positive — 충돌 아님"
}}
"""


def call_haiku_llm(prompt: str) -> Dict:
    """
    Claude Haiku 3.5 호출 (실제 구현 — Anthropic SDK).

    mcwiki extension 의 LLM provider 통합 필요. 환경변수 `ANTHROPIC_API_KEY` 또는
    `MCWIKI_LLM_API_KEY` 사용.

    Returns: parsed JSON dict {"is_real_conflict": bool, "reason": str, "suggested_action": str}

    실제 mcwiki extension 통합 시:
    ```python
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",   # 또는 mcwiki extension 시점 최신
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(msg.content[0].text)
    ```
    """
    # 본 PR 은 mcwiki extension 의 LLM provider 통합 미완 — stub 반환.
    # 실제 통합 시점에 위 anthropic SDK 호출로 대체.
    return {
        "is_real_conflict": None,
        "reason": "LLM stub — mcwiki extension LLM provider 통합 미완 (Cycle 5l 후보)",
        "suggested_action": "manual review required",
    }


def auto_detect_kind(slug: str, vault_root: Path) -> Optional[str]:
    for kind in VALID_KINDS:
        if (vault_root / kind / f"{slug}.md").is_file():
            return kind
    return None


def extract_context_line(content: str, line_no: int, context_lines: int = 2) -> str:
    """주어진 라인 +- N 줄 추출 — LLM 에 context 제공."""
    lines = content.splitlines()
    start = max(0, line_no - 1 - context_lines)
    end = min(len(lines), line_no + context_lines)
    return "\n".join(lines[start:end]).strip()


def extract_claims(content: str) -> Dict[str, List[Tuple[int, str]]]:
    """v0.4.0 그대로 — claim 4 패턴 추출."""
    claims = {"section_headers": [], "numeric_claims": [], "tier_dists": [], "api_signatures": []}
    for line_no, line in enumerate(content.splitlines(), start=1):
        for m in SECTION_HEADER_RE.finditer(line):
            claims["section_headers"].append((line_no, m.group(1).strip()))
        for m in NUMERIC_CLAIM_RE.finditer(line):
            claims["numeric_claims"].append((line_no, m.group(0)))
        for m in TIER_DIST_RE.finditer(line):
            claims["tier_dists"].append((line_no, f"🟢 {m.group(1)} / 🟡 {m.group(2)} / 🔴 {m.group(3)}"))
        for m in API_SIG_RE.finditer(line):
            claims["api_signatures"].append((line_no, m.group(1)))
    return claims


def find_numeric_conflicts_with_llm(
    a_content: str, b_content: str,
    a_claims: List[Tuple[int, str]], b_claims: List[Tuple[int, str]],
    slug_a: str, slug_b: str,
    use_llm: bool = True,
) -> List[Dict]:
    """v0.4.0 휴리스틱 + LLM mode 검증."""
    conflicts = []
    a_by_keyword: Dict[str, List[Tuple[int, int]]] = {}
    b_by_keyword: Dict[str, List[Tuple[int, int]]] = {}

    for line, claim in a_claims:
        m = NUMERIC_CLAIM_RE.match(claim)
        if not m:
            continue
        a_by_keyword.setdefault(m.group(2).strip().upper(), []).append((line, int(m.group(1))))

    for line, claim in b_claims:
        m = NUMERIC_CLAIM_RE.match(claim)
        if not m:
            continue
        b_by_keyword.setdefault(m.group(2).strip().upper(), []).append((line, int(m.group(1))))

    common = set(a_by_keyword.keys()) & set(b_by_keyword.keys())
    for keyword in common:
        a_counts = {c for _, c in a_by_keyword[keyword]}
        b_counts = {c for _, c in b_by_keyword[keyword]}
        if a_counts != b_counts and not (a_counts & b_counts):
            # 휴리스틱 충돌 검출
            a_line, a_count = a_by_keyword[keyword][0]
            b_line, b_count = b_by_keyword[keyword][0]

            conflict = {
                "type": "numeric_mismatch",
                "keyword": keyword,
                "a_lines": [(l, c) for l, c in a_by_keyword[keyword]],
                "b_lines": [(l, c) for l, c in b_by_keyword[keyword]],
                "severity": "high" if abs(max(a_counts) - max(b_counts)) > 1 else "med",
            }

            # ⭐ v0.4.1 LLM 검증 — false positive 회피
            if use_llm:
                prompt = LLM_VERIFICATION_PROMPT.format(
                    slug_a=slug_a, slug_b=slug_b,
                    line_a=a_line, line_b=b_line,
                    count_a=a_count, count_b=b_count,
                    keyword=keyword,
                    context_a=extract_context_line(a_content, a_line),
                    context_b=extract_context_line(b_content, b_line),
                )
                llm_result = call_haiku_llm(prompt)
                conflict["llm_verification"] = llm_result

                # LLM 이 false positive 라고 판단하면 severity 강등 또는 충돌 리스트에서 제거
                if llm_result.get("is_real_conflict") is False:
                    conflict["severity"] = "false_positive"
                    conflict["llm_filtered"] = True
                    # continue   # 또는 conflict 추가 안 함 (정책 결정)
                # is_real_conflict=None (LLM stub) 인 경우 휴리스틱 결과 그대로 유지

            conflicts.append(conflict)
    return conflicts


def find_claim_conflict_handler(
    slug_a: str,
    slug_b: str,
    kind_a: Optional[str] = None,
    kind_b: Optional[str] = None,
    vault_root: Optional[Path] = None,
    use_llm: bool = False,
) -> Dict:
    """
    v0.4.1 — 휴리스틱 mode (기본) + LLM mode (use_llm=True).

    Args:
        slug_a, slug_b: 비교 대상 페이지 slug 2개
        kind_a, kind_b: 각 페이지 kind (옵션)
        vault_root: vault 의 wiki 디렉토리 절대 경로
        use_llm: True 면 LLM 검증 활성 (false positive 회피). 기본 False (휴리스틱만).

    Returns:
        {
            "slug_a": "...", "kind_a": "...",
            "slug_b": "...", "kind_b": "...",
            "conflict_count": int,
            "conflicts": [...],
            "mode": "heuristic" | "heuristic+llm"
        }
    """
    if vault_root is None:
        vault_root_str = os.environ.get("MCWIKI_VAULT_ROOT")
        if not vault_root_str:
            raise ValueError("MCWIKI_VAULT_ROOT 환경변수 또는 vault_root 인자 필요")
        vault_root = Path(vault_root_str)
    vault_root = Path(vault_root)

    def _load(slug, kind):
        if kind is None:
            kind = auto_detect_kind(slug, vault_root)
            if kind is None:
                return None, None, f"page not found: {slug}"
        path = vault_root / kind / f"{slug}.md"
        if not path.is_file():
            return kind, None, f"page not found: {path}"
        return kind, path.read_text(encoding="utf-8"), None

    kind_a, content_a, err_a = _load(slug_a, kind_a)
    kind_b, content_b, err_b = _load(slug_b, kind_b)
    if err_a or err_b:
        return {
            "slug_a": slug_a, "slug_b": slug_b,
            "kind_a": kind_a, "kind_b": kind_b,
            "conflict_count": 0, "conflicts": [],
            "error": err_a or err_b,
            "mode": "heuristic+llm" if use_llm else "heuristic",
        }

    claims_a = extract_claims(content_a)
    claims_b = extract_claims(content_b)

    all_conflicts = []
    all_conflicts.extend(find_numeric_conflicts_with_llm(
        content_a, content_b,
        claims_a["numeric_claims"], claims_b["numeric_claims"],
        slug_a, slug_b,
        use_llm=use_llm,
    ))

    # tier_distribution 과 api_signature 는 휴리스틱만 (LLM 검증 후속 PR)
    # ... (v0.4.0 그대로 — 생략)

    # llm_filtered 제외 시 진짜 충돌만 카운트
    real_conflicts = [c for c in all_conflicts if not c.get("llm_filtered", False)]
    return {
        "slug_a": slug_a, "kind_a": kind_a,
        "slug_b": slug_b, "kind_b": kind_b,
        "conflict_count": len(real_conflicts),
        "conflicts": all_conflicts,   # 전체 (llm_filtered 포함) — 사용자 검토용
        "mode": "heuristic+llm" if use_llm else "heuristic",
    }


# === 테스트 — Cycle 5k Phase 1 false positive 검증 ===========================

def test_cycle_5k_phase1_false_positive_with_llm_mock():
    """
    Cycle 5k Phase 1 false positive 시나리오 시뮬레이션:
    `find_claim_conflict("ue-editor-asseteditorapi", "ue-editor-personatoolkit")`
    → keyword "종" line 45 (8종) vs line 315 (11종) — 다른 문맥의 "종".

    LLM mock 으로 is_real_conflict=False 반환 → severity=false_positive 강등 검증.
    """
    import os
    vault_root = Path(os.environ.get("MCWIKI_VAULT_ROOT", ""))
    if not vault_root.is_dir():
        print("SKIP: vault_root not found")
        return

    # LLM stub 임시 override — false positive 시뮬레이션
    global call_haiku_llm
    original = call_haiku_llm
    def _mock_llm(prompt: str) -> Dict:
        return {
            "is_real_conflict": False,
            "reason": "두 라인은 다른 문맥 — '8종 EAssetEditorCloseReason' vs '11종 카탈로그 사례'. 같은 객체 X.",
            "suggested_action": "false positive — 충돌 아님",
        }
    call_haiku_llm = _mock_llm

    try:
        result = find_claim_conflict_handler(
            "ue-editor-asseteditorapi", "ue-editor-personatoolkit",
            vault_root=vault_root, use_llm=True,
        )
        print(f"LLM mode: {result['mode']}, real conflicts: {result['conflict_count']}")
        for c in result["conflicts"]:
            print(f"  - {c.get('type')} keyword='{c.get('keyword')}' severity={c.get('severity')}")
            if "llm_verification" in c:
                print(f"    LLM: {c['llm_verification']}")
        # 실제 vault 에서 keyword "종" conflict 가 있다면 LLM mock 으로 강등됨
        assert result["conflict_count"] == 0 or all(
            c.get("severity") == "false_positive" for c in result["conflicts"]
            if c.get("keyword") == "종"
        )
    finally:
        call_haiku_llm = original

    print("✅ Cycle 5k Phase 1 false positive LLM mode 검증 완료 (mock)")


if __name__ == "__main__":
    test_cycle_5k_phase1_false_positive_with_llm_mock()
