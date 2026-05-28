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

# raw/, docs/ prefix — vault root layer (lint.py 정합). v0.3.2.
EXTRA_PREFIXES = ("raw", "docs")

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
    """[[wikilink]] 안 target 을 (kind, slug) 으로 분리.

    v0.3.3 (Cycle 5n #1): alias `|` + anchor `#` 모두 분리.
    """
    target = target.strip()
    # alias 제거 — `[[slug|display]]`
    if "|" in target:
        target = target.split("|", 1)[0].strip()
    # anchor 제거 — `[[slug#§5.4]]` / `[[kind/slug#anchor]]`
    if "#" in target:
        target = target.split("#", 1)[0].strip()
    if "/" in target:
        kind, slug = target.split("/", 1)
        if kind in VALID_KINDS:
            return kind, slug
    return None, target


def _vault_root_file_exists(target: str, vault_root: Path) -> bool:
    """vault root layer 의 .md 파일 (CLAUDE.md / AGENTS.md / README.md 등) 인지.

    v0.3.3 (Cycle 5n #1): `[[CLAUDE.md]]` 또는 `[[CLAUDE.md#§5.4]]` 같은
    vault root 의 단일 파일 wikilink 처리.
    """
    # alias / anchor 제거
    clean = target.strip()
    if "|" in clean:
        clean = clean.split("|", 1)[0].strip()
    if "#" in clean:
        clean = clean.split("#", 1)[0].strip()
    # "/" 가 있으면 vault root 단일 파일이 아님
    if "/" in clean:
        return False
    # vault_root = wiki/. parent = vault root (E:\MCWiki).
    root = vault_root.parent
    # .md 확장자 유무 모두 시도
    candidates = [root / clean]
    if not clean.endswith(".md"):
        candidates.append(root / f"{clean}.md")
    return any(c.is_file() for c in candidates)


def _kind_root(kind: str, vault_root: Path) -> Path:
    """kind 별 디렉토리 경로 — `00_meta` 는 vault parent (lint.py 정합)."""
    if kind == "00_meta":
        return vault_root.parent / "00_meta"
    if kind == "meta":
        return vault_root.parent / "00_meta"   # alias
    return vault_root / kind


def _extra_prefix_exists(target: str, vault_root: Path) -> bool:
    """raw/ docs/ prefix wikilink 가 vault parent 안 실제 파일 인지 (lint.py 정합)."""
    # alias / anchor 제거
    target_clean = target.strip()
    if "|" in target_clean:
        target_clean = target_clean.split("|", 1)[0].strip()
    if "#" in target_clean:
        target_clean = target_clean.split("#", 1)[0].strip()

    for prefix in EXTRA_PREFIXES:
        if not target_clean.startswith(prefix + "/"):
            continue
        rel = target_clean[len(prefix) + 1:]
        root = vault_root.parent / prefix
        # .md 확장자 유무 모두 시도
        for cand in (root / rel, root / f"{rel}.md"):
            if cand.is_file():
                return True
        return False
    return False


def auto_detect_kind(slug: str, vault_root: Path) -> Optional[str]:
    """slug 의 kind 자동 추론. 00_meta 는 vault parent 안 (lint.py 정합)."""
    for kind in VALID_KINDS:
        if (_kind_root(kind, vault_root) / f"{slug}.md").is_file():
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

    page_path = _kind_root(kind, vault_root) / f"{slug}.md"
    if not page_path.is_file():
        return {"slug": slug, "kind": kind, "total_wikilinks": 0, "broken_count": 0,
                "broken_links": [], "error": f"page not found: {page_path}"}

    content = page_path.read_text(encoding="utf-8", errors="replace")

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
        raw_target = link["target"]

        # v0.3.3 (Cycle 5n #1) — vault root .md 파일 (CLAUDE.md / AGENTS.md / README.md)
        # "/" 없는 wikilink 가 vault root 안 .md 파일이면 valid.
        anchor_stripped = raw_target.split("#", 1)[0].strip()
        if "|" in anchor_stripped:
            anchor_stripped = anchor_stripped.split("|", 1)[0].strip()
        if "/" not in anchor_stripped and _vault_root_file_exists(raw_target, vault_root):
            continue

        # v0.3.2 — raw/ docs/ prefix 처리 (lint.py 정합)
        if any(raw_target.lstrip().startswith(p + "/") for p in EXTRA_PREFIXES):
            if _extra_prefix_exists(raw_target, vault_root):
                continue
            broken.append({**link, "target_kind": "extra", "target_slug": raw_target,
                           "reason": "extra path not found (raw/docs)"})
            continue

        target_kind, target_slug = parse_target(raw_target)
        if target_kind is None:
            target_kind = auto_detect_kind(target_slug, vault_root)
            if target_kind is None:
                broken.append({**link, "target_kind": None, "target_slug": target_slug,
                               "reason": "page not found in any kind"})
                continue
        if not (_kind_root(target_kind, vault_root) / f"{target_slug}.md").is_file():
            broken.append({**link, "target_kind": target_kind, "target_slug": target_slug,
                           "reason": "page not found"})

    return {
        "slug": slug, "kind": kind,
        "total_wikilinks": len(all_links),
        "broken_count": len(broken),
        "broken_links": broken,
    }

