"""
mcwiki MCP server tool #1 v0.3.1 patch — find_cross_link_broken
================================================================

**v0.3.1 변경 (Cycle 5j #1 Phase 1 false positive 회피)**:
- `strip_code_blocks()` 헬퍼 추가 — 코드 블록 (```...```) + inline code (`...`) 안 wikilink 무시
- Cycle 5j Phase 1 검증에서 `ue-meta-baseline-grep-system` §5.1 의 `[[wikilink]]` literal 표기가 broken 으로 잡힌 false positive 회피

**v0.3.0 → v0.3.1 diff (핵심)**:
- 본문 wikilink 추출 직전 `content = strip_code_blocks(content)` 한 줄 추가
- 라인 번호 추적 시 stripped content 대신 *원본 content* 의 라인 번호 사용 — code block 안 wikilink 위치를 보존하기 위해 (사용자가 정정 필요 시 원본 위치 참조)

vault 명세: [[sources/ue-meta-baseline-grep-system]] §5.1 + §6
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
VALID_KINDS = {"sources", "entities", "concepts", "synthesis", "meta", "00_meta"}

# v0.3.1 신규 — code block / inline code 패턴
CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")


def strip_code_blocks_preserve_lines(content: str) -> str:
    """
    code block / inline code 안 내용을 **빈 줄로 치환** — 라인 번호 보존.

    이전 `strip_code_blocks` (Cycle 5j suggest_missing_cross_link.py) 는 빈 문자열로 치환 →
    라인 번호 어긋남. v0.3.1 은 줄바꿈 보존 정책으로 *원본 라인 번호* 유지.

    예:
        input:  '실제 [[a]]\\n```py\\n[[code]]\\n```\\n[[b]]'
        output: '실제 [[a]]\\n   \\n      \\n   \\n[[b]]'    # code block 줄들 빈 공백 + 줄바꿈 유지
    """
    def _replace_block(match: re.Match) -> str:
        block = match.group(0)
        # 줄바꿈 카운트 유지 — 라인 번호 보존
        newlines = block.count("\n")
        return " " * (len(block) - newlines) + "\n" * newlines

    content = CODE_BLOCK_RE.sub(_replace_block, content)
    content = INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), content)
    return content


def parse_target(target: str) -> Tuple[Optional[str], str]:
    """[[wikilink]] 안 target 을 (kind, slug) 으로 분리."""
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
        if (vault_root / kind / f"{slug}.md").is_file():
            return kind
    return None


def parse_current_section(content_lines: List[str], line_no: int) -> str:
    """주어진 라인 번호 이전의 가장 가까운 `## §` 헤더 추출."""
    section = ""
    for i in range(line_no - 1, -1, -1):
        if i >= len(content_lines):
            continue
        line = content_lines[i]
        if line.startswith("## "):
            section = line[3:].strip()
            break
        elif line.startswith("# "):
            section = line[2:].strip()
            break
    return section or "(no section)"


def find_cross_link_broken_handler(
    slug: str,
    kind: Optional[str] = None,
    vault_root: Optional[Path] = None,
) -> Dict:
    """v0.3.1 — code block false positive 회피."""
    if vault_root is None:
        import os
        vault_root_str = os.environ.get("MCWIKI_VAULT_ROOT")
        if not vault_root_str:
            raise ValueError("MCWIKI_VAULT_ROOT 환경변수 또는 vault_root 인자 필요")
        vault_root = Path(vault_root_str)
    vault_root = Path(vault_root)

    if kind is None:
        kind = auto_detect_kind(slug, vault_root)
        if kind is None:
            return {"slug": slug, "kind": None, "total_wikilinks": 0, "broken_count": 0,
                    "broken_links": [], "error": f"page not found: {slug}"}

    page_path = vault_root / kind / f"{slug}.md"
    if not page_path.is_file():
        return {"slug": slug, "kind": kind, "total_wikilinks": 0, "broken_count": 0,
                "broken_links": [], "error": f"page not found: {page_path}"}

    content = page_path.read_text(encoding="utf-8")

    # v0.3.1 — code block / inline code 안 wikilink 무시 (라인 번호 보존)
    content_stripped = strip_code_blocks_preserve_lines(content)
    content_lines = content.splitlines()   # 원본 라인 (section path 추출용)

    all_links = []
    for line_no, line in enumerate(content_stripped.splitlines(), start=1):
        for match in WIKILINK_RE.finditer(line):
            target = match.group(1).strip()
            section = parse_current_section(content_lines, line_no)
            all_links.append({
                "target": target,
                "line_number": line_no,
                "section_path": section,
            })

    broken = []
    for link in all_links:
        target_kind, target_slug = parse_target(link["target"])
        if target_kind is None:
            target_kind = auto_detect_kind(target_slug, vault_root)
            if target_kind is None:
                broken.append({**link, "target_kind": None, "target_slug": target_slug,
                               "reason": "page not found in any kind"})
                continue
        if not (vault_root / target_kind / f"{target_slug}.md").is_file():
            broken.append({**link, "target_kind": target_kind, "target_slug": target_slug,
                           "reason": "page not found"})

    return {
        "slug": slug, "kind": kind,
        "total_wikilinks": len(all_links),
        "broken_count": len(broken),
        "broken_links": broken,
    }


# === 테스트 — v0.3.1 false positive 회피 확인 ====================================

def test_strip_code_blocks_preserve_lines():
    sample = """실제 [[sources/ue-x]] 인용.

```python
# 코드 안 [[wikilink]] 는 무시
pattern = r"\\[\\["
```

inline `[[code-example]]` 도 무시.

[[concepts/Real-Link]] 인용 2.
"""
    stripped = strip_code_blocks_preserve_lines(sample)
    # 라인 수 동일
    assert sample.count("\n") == stripped.count("\n"), "line count must match"
    # 코드 블록 안 wikilink 추출 안 됨
    wikilinks = WIKILINK_RE.findall(stripped)
    assert "sources/ue-x" in wikilinks
    assert "concepts/Real-Link" in wikilinks
    assert "wikilink" not in wikilinks   # code block 안
    assert "code-example" not in wikilinks   # inline code 안
    print(f"strip_code_blocks_preserve_lines: PASS ({len(wikilinks)} valid wikilinks, {sample.count(chr(10))} lines preserved)")


def test_baseline_grep_system_false_positive_fix():
    """Cycle 5j Phase 1 false positive (baseline-grep-system §5.1) 회피 검증."""
    import os
    vault_root = Path(os.environ.get("MCWIKI_VAULT_ROOT", ""))
    if not vault_root.is_dir():
        print("SKIP: vault_root not found")
        return

    result = find_cross_link_broken_handler("ue-meta-baseline-grep-system", vault_root=vault_root)
    print(f"baseline-grep-system v0.3.1: {result['total_wikilinks']} wikilinks, {result['broken_count']} broken")
    # v0.3.0 에서 broken=1 ([[wikilink]] literal) → v0.3.1 에서 broken=0 기대
    assert result["broken_count"] == 0, f"expected broken_count=0, got {result['broken_count']}"
    print("✅ Cycle 5j Phase 1 false positive 회피 검증 완료")


if __name__ == "__main__":
    test_strip_code_blocks_preserve_lines()
    test_baseline_grep_system_false_positive_fix()
