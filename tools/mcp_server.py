#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCWiki MCP server (STDIO).

Exposes the local Karpathy-style wiki vault to any MCP client (Claude Code,
Claude Desktop, etc) as resources + tools.

Resources
---------
  wiki://index                  -> wiki/index.md
  wiki://log                    -> wiki/log.md
  wiki://sources/<slug>         -> wiki/sources/<slug>.md
  wiki://entities/<slug>        -> wiki/entities/<slug>.md
  wiki://concepts/<slug>        -> wiki/concepts/<slug>.md
  wiki://synthesis/<slug>       -> wiki/synthesis/<slug>.md
  wiki://meta/<slug>            -> 00_meta/<slug>.md
  wiki://raw/<rel-path>         -> raw/<rel-path>           (read-only mirror)

Tools
-----
  list_pages(kind)              -> list slugs in a wiki kind dir
  search(query, scope?)         -> ripgrep-lite across wiki/ (and raw/ optional)
  lint()                        -> run tools/lint.py and capture stdout
  stats()                       -> run tools/stats.py and capture stdout
  ingest_seed(slug, source_path, kind?, title?)
                                -> scaffold a new source page from templates/

The vault root is auto-detected (parent of this file's tools/ dir),
or overridden via env MCWIKI_ROOT.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Resource, TextContent, Tool
except ImportError:
    print(
        "[mcp_server] missing dependency: pip install 'mcp>=1.0.0'",
        file=sys.stderr,
    )
    raise


# ---------------------------------------------------------------------------
# Vault location

ROOT = Path(os.environ.get("MCWIKI_ROOT", Path(__file__).resolve().parent.parent))
WIKI = ROOT / "wiki"
RAW = ROOT / "raw"
META = ROOT / "00_meta"
TEMPLATES = ROOT / "templates"

WIKI_KINDS = ("sources", "entities", "concepts", "synthesis")
WIKI_KINDS_WRITE = WIKI_KINDS + ("index",)   # write_page 만 — index.md 직접 편집 지원 (v0.2.1)
# v0.5.4 (Cycle 5o #3) — read-only tools 의 kind enum 에 "00_meta" alias 추가.
# vault content 안 wikilink 표기 `[[00_meta/X]]` (historical, 정렬용 prefix) 를 mcwiki kind 로도 지원.
# 두 enum 모두 동일 META 디렉토리 (E:\MCWiki\00_meta) 매핑.
WIKI_KINDS_READ = list(WIKI_KINDS) + ["meta", "00_meta"]


def _normalize_kind(kind: str) -> str:
    """v0.5.4 — kind alias 정규화: '00_meta' → 'meta' (handler 내부 처리 단일화)."""
    return "meta" if kind == "00_meta" else kind

server = Server("mcwiki")


# ---------------------------------------------------------------------------
# Git integration (Pattern X — GitHub-backed local server)
#
# When the vault is a git repo, the server pulls the latest main on startup
# so multiple machines stay in sync via `git push`. Disable with
# MCWIKI_AUTOPULL=0.

import shutil as _shutil

# Detect git binary ONCE at module load — avoids per-call PATH lookup overhead
# in sandboxed runtimes (e.g. Cowork's .mcpb runtime) where each subprocess
# spawn is slow.
_GIT_BIN = _shutil.which("git")


def _git(*args: str, timeout: float = 5.0) -> tuple[int, str, str]:
    """Run `git -C ROOT <args>` and return (returncode, stdout, stderr).

    Returns immediately with rc=-1 if git binary isn't on PATH (cached check).
    Per-call timeout reduced to 5 s so worst-case 3 sequential calls stay
    under the MCP request timeout.
    """
    if _GIT_BIN is None:
        return -1, "", "git executable not on PATH (cached at startup)"
    try:
        proc = subprocess.run(
            [_GIT_BIN, "-C", str(ROOT), *args],
            capture_output=True, text=True, timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return -1, "", "git executable not on PATH"
    except subprocess.TimeoutExpired:
        return -2, "", f"git {' '.join(args)} timed out after {timeout}s"


def _git_pull_if_repo() -> None:
    """Fast-forward pull on startup if the vault is a git repo and AUTOPULL is on."""
    if (ROOT / ".git").exists() and os.environ.get("MCWIKI_AUTOPULL", "1") != "0":
        _git("pull", "--ff-only", "--quiet", timeout=10.0)


# ---------------------------------------------------------------------------
# Synthesis pipeline helpers

_KOREAN_STOP = {
    "의", "에", "을", "를", "이", "가", "은", "는", "와", "과", "도",
    "에서", "으로", "에게", "에서의", "처럼", "처리", "관련", "기반",
    "위한", "통한", "대한", "사용", "사용한", "사용하는", "이용",
    "관해", "대해", "위해", "통해",
}


def _extract_keywords(topic: str) -> list[str]:
    """Extract keyword candidates from a synthesis topic title.
    Picks ASCII words >=2 chars and Korean nouns >=2 chars, dedupes,
    filters short particles."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9_]+|[가-힣]{2,}", topic)
    seen: list[str] = []
    for w in words:
        if w in _KOREAN_STOP or len(w) < 2:
            continue
        if w.lower() in {x.lower() for x in seen}:
            continue
        seen.append(w)
    return seen


def _slugify(topic: str) -> str:
    """Best-effort English-friendly slug. Falls back to date+hash for Korean-only."""
    keep = re.sub(r"[^A-Za-z0-9가-힣\-_ ]", "", topic).strip()
    keep = re.sub(r"\s+", "-", keep)
    keep = keep[:80].strip("-_")
    return keep or "synthesis-untitled"


def _discover_related(keywords: list[str], per_kind_cap: int = 30) -> dict:
    """Return {kind: [slug, ...]} for sources/entities/concepts whose body contains
    any of the keywords (case-insensitive). Capped per kind."""
    out: dict[str, list[str]] = {"sources": [], "entities": [], "concepts": []}
    if not keywords:
        return out
    pattern = re.compile("|".join(re.escape(k) for k in keywords), re.IGNORECASE)
    for kind in ("sources", "entities", "concepts"):
        folder = WIKI / kind
        if not folder.is_dir():
            continue
        scored: list[tuple[int, str]] = []
        for p in folder.glob("*.md"):
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            hits = len(pattern.findall(text))
            if hits:
                scored.append((hits, p.stem))
        scored.sort(reverse=True)  # most matches first
        out[kind] = [s for _, s in scored[:per_kind_cap]]
    return out


# ---------------------------------------------------------------------------
# Resources

def _iter_md(folder: Path):
    if not folder.is_dir():
        return
    for p in sorted(folder.glob("*.md")):
        yield p


@server.list_resources()
async def list_resources() -> list[Resource]:
    out: list[Resource] = []

    out.append(Resource(uri="wiki://index", name="index", mimeType="text/markdown"))
    out.append(Resource(uri="wiki://log", name="log", mimeType="text/markdown"))

    for kind in WIKI_KINDS:
        for p in _iter_md(WIKI / kind):
            out.append(
                Resource(
                    uri=f"wiki://{kind}/{p.stem}",
                    name=f"{kind}/{p.stem}",
                    mimeType="text/markdown",
                )
            )

    for p in _iter_md(META):
        out.append(
            Resource(
                uri=f"wiki://meta/{p.stem}",
                name=f"meta/{p.stem}",
                mimeType="text/markdown",
            )
        )

    return out


@server.read_resource()
async def read_resource(uri: str) -> str:
    path = _resolve(uri)
    if path is None or not path.is_file():
        raise ValueError(f"resource not found: {uri}")
    return path.read_text(encoding="utf-8")


def _resolve(uri: str) -> Path | None:
    if not uri.startswith("wiki://"):
        return None
    rest = uri[len("wiki://"):]
    if rest == "index":
        return WIKI / "index.md"
    if rest == "log":
        return WIKI / "log.md"
    if "/" not in rest:
        return None
    kind, slug = rest.split("/", 1)
    if kind in WIKI_KINDS:
        return WIKI / kind / f"{slug}.md"
    if kind == "meta":
        return META / f"{slug}.md"
    if kind == "raw":
        # disallow .. traversal
        rel = Path(slug)
        if any(part == ".." for part in rel.parts):
            return None
        return RAW / rel
    return None


# ---------------------------------------------------------------------------
# Tools

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="list_pages",
            description="List slugs in a wiki kind directory (sources/entities/concepts/synthesis/meta).",
            inputSchema={
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": WIKI_KINDS_READ,
                    }
                },
                "required": ["kind"],
            },
        ),
        Tool(
            name="search",
            description="Grep-style substring search across wiki/ (default) or wiki/+raw/. Returns up to 50 hits.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "scope": {
                        "type": "string",
                        "enum": ["wiki", "all"],
                        "default": "wiki",
                    },
                    "limit": {"type": "integer", "default": 50},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="lint",
            description="Run tools/lint.py and return its stdout.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="stats",
            description="Run tools/stats.py and return its stdout.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="read_page",
            description="Return the full markdown of a wiki page. kind ∈ sources/entities/concepts/synthesis/meta. Use list_pages first to discover slugs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": WIKI_KINDS_READ,
                    },
                    "slug": {"type": "string", "description": "Page slug without .md (e.g. ue-components-skill)."},
                },
                "required": ["kind", "slug"],
            },
        ),
        Tool(
            name="read_raw",
            description="Return the full content of a file under raw/. rel_path is relative to raw/ (e.g. ue-wiki-llm/skills/Components/SKILL.md). `..` traversal is rejected.",
            inputSchema={
                "type": "object",
                "properties": {
                    "rel_path": {"type": "string"},
                },
                "required": ["rel_path"],
            },
        ),
        Tool(
            name="read_index",
            description="Return wiki/index.md (vault catalog: sources/entities/concepts/synthesis enumerated by category).",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="read_log",
            description="Return wiki/log.md (append-only operations log).",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="ingest_seed",
            description="Scaffold a new wiki/sources/<slug>.md from templates/source.md. Frontmatter is auto-filled.",
            inputSchema={
                "type": "object",
                "properties": {
                    "slug": {"type": "string"},
                    "source_path": {"type": "string", "description": "raw/... path"},
                    "title": {"type": "string"},
                },
                "required": ["slug", "source_path"],
            },
        ),
        Tool(
            name="write_page",
            description="Create or update a wiki page. kind ∈ sources/entities/concepts/synthesis/index (meta excluded — governance-protected). Default fails if page exists; set overwrite=true to replace. content must include valid YAML frontmatter starting with --- EXCEPT for kind=index (no frontmatter). When kind=index, slug must be 'index' (target = wiki/index.md, overwrite always required since it always exists).",
            inputSchema={
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": list(WIKI_KINDS_WRITE),
                    },
                    "slug": {"type": "string", "description": "Page slug — alphanumeric, dashes, underscores only."},
                    "content": {"type": "string", "description": "Full markdown including frontmatter."},
                    "overwrite": {"type": "boolean", "default": False},
                },
                "required": ["kind", "slug", "content"],
            },
        ),
        Tool(
            name="append_log",
            description="Append a properly formatted entry to wiki/log.md. Header is auto-prefixed as `## [YYYY-MM-DD] <op> | <title>`. body should be the markdown content after the header.",
            inputSchema={
                "type": "object",
                "properties": {
                    "op": {
                        "type": "string",
                        "enum": ["ingest", "query", "synthesis", "lint", "refactor", "schema-change", "note", "fix", "feature", "doc", "verify", "scaffold", "bulk-import", "bulk-seed"],
                    },
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["op", "title", "body"],
            },
        ),
        Tool(
            name="synthesis_seed",
            description="Discover sources/entities/concepts related to a synthesis topic and return a frontmatter scaffold with auto-populated cross-references + suggested 5-section outline. Does NOT write to disk — agent composes body using read_page on related items, then calls write_page(kind=synthesis, slug, content) to save.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Synthesis thesis / topic title."},
                    "slug": {"type": "string", "description": "Optional explicit slug; auto-derived from topic if omitted."},
                    "extra_keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional search terms beyond what's auto-extracted from topic.",
                    },
                },
                "required": ["topic"],
            },
        ),
        Tool(
            name="synthesis_finalize",
            description="Validate a written synthesis page (lint must pass) + bump wiki/index.md's `## Synthesis (N)` count + append a [synthesis] log entry. Call after write_page completes the body.",
            inputSchema={
                "type": "object",
                "properties": {
                    "slug": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["draft", "living", "settled"],
                        "default": "living",
                    },
                    "summary": {"type": "string", "description": "One-line summary for the log entry."},
                },
                "required": ["slug"],
            },
        ),
        Tool(
            name="query_recap",
            description="Capsule a Q&A and route filing-back. Use after answering a user query to decide whether to log only / append to existing page / spawn a synthesis. mode determines disposition. Compresses CLAUDE.md §5.2 query workflow steps 4-5 into one call.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "User's question (or distilled topic)."},
                    "answer_summary": {"type": "string", "description": "Compressed answer body (markdown). Used in modes append_to_log / append_to_page / propose_synthesis."},
                    "mode": {
                        "type": "string",
                        "enum": ["skip", "append_to_log", "append_to_page", "propose_synthesis"],
                        "default": "append_to_log",
                        "description": "skip = no-op. append_to_log = wiki/log.md only. append_to_page = append `## Q&A — ... (date)` to existing wiki page. propose_synthesis = log query + return suggested synthesis_seed call for the next step.",
                    },
                    "target_kind": {
                        "type": "string",
                        "enum": list(WIKI_KINDS),
                        "description": "For append_to_page mode.",
                    },
                    "target_slug": {"type": "string", "description": "For append_to_page mode."},
                    "synthesis_topic": {"type": "string", "description": "For propose_synthesis mode (synthesis title). Defaults to the question."},
                    "synthesis_slug": {"type": "string", "description": "For propose_synthesis mode (optional explicit slug)."},
                },
                "required": ["question", "mode"],
            },
        ),
        Tool(
            name="git_status",
            description="Show the vault's git status (branch, ahead/behind, dirty files).",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="git_pull",
            description="Fetch & fast-forward pull main from origin. No-op if not a git repo.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="find_cross_link_broken",
            description="Validate [[wikilink]] targets in a vault page. Returns broken_count + broken_links (target_slug + line_number + section_path). Recognizes wiki/{sources,entities,concepts,synthesis}/, 00_meta/, raw/, docs/ + vault root .md files (CLAUDE.md / AGENTS.md / README.md) as valid targets (lint.py parity, v0.3.3). v0.3.1: strip_code_blocks_preserve_lines() — code-block wikilinks ignored. v0.3.2: 00_meta + raw/docs prefix. v0.3.3 (Cycle 5n #1): vault root .md + #anchor 분리 (parse_target). kind auto-detected if omitted.",
            inputSchema={
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "Page slug without .md (e.g. 'ue-editor-asseteditorapi').",
                    },
                    "kind": {
                        "type": "string",
                        "enum": WIKI_KINDS_READ,
                        "description": "Page kind (optional — auto-detected by scanning kind directories).",
                    },
                },
                "required": ["slug"],
            },
        ),
        Tool(
            name="suggest_missing_cross_link",
            description="Backlink-based cross-link recommendation. Scans the entire vault for pages that link inbound to this page, then suggests outbound cross-links the author may have missed. Returns outbound_count + inbound_count + ranked suggestions (confidence: high/med/low) with is_reverse_linked flag. Skips wikilinks inside code blocks/inline code (Cycle 5j fix).",
            inputSchema={
                "type": "object",
                "properties": {
                    "slug": {"type": "string"},
                    "kind": {
                        "type": "string",
                        "enum": WIKI_KINDS_READ,
                    },
                    "min_inbound": {
                        "type": "integer",
                        "default": 1,
                        "description": "Minimum inbound link count for a page to qualify as a suggestion (default 1).",
                    },
                },
                "required": ["slug"],
            },
        ),
        Tool(
            name="find_claim_conflict",
            description="Heuristic claim conflict detector across two pages. v0.5.5 (Cycle 5p #1): 한국어 단위 명사 (종/개/함정/대/회/호스트) false positive 자동 강등 — 숫자+단위 직전 객체 명사 추출 후 (keyword, object) 페어 매칭. 객체 명사 다르면 conflict 제외, 미식별 시 severity=low+note 표기. v0.5.1: LLM mode 제거 (heuristic only). Extracts 4 claim patterns (section headers / numeric / tier distribution / API signatures) and reports 3 conflict categories.",
            inputSchema={
                "type": "object",
                "properties": {
                    "slug_a": {"type": "string"},
                    "slug_b": {"type": "string"},
                    "kind_a": {
                        "type": "string",
                        "enum": WIKI_KINDS_READ,
                    },
                    "kind_b": {
                        "type": "string",
                        "enum": WIKI_KINDS_READ,
                    },
                },
                "required": ["slug_a", "slug_b"],
            },
        ),
        Tool(
            name="find_stale_baseline",
            description="Staleness detector. Compares the page's last_updated (frontmatter) against today and against the last_updated of its dependent pages (extracted from wikilinks). Returns age_days + is_stale (>threshold_days) + dependent_changes (deps updated after this page's baseline). Frontmatter priority: last_updated > ingested > source_date. Default threshold 90 days (quarterly audit).",
            inputSchema={
                "type": "object",
                "properties": {
                    "slug": {"type": "string"},
                    "kind": {
                        "type": "string",
                        "enum": WIKI_KINDS_READ,
                    },
                    "threshold_days": {
                        "type": "integer",
                        "default": 90,
                        "description": "Days after which a page is considered stale (default 90 — quarterly audit baseline).",
                    },
                },
                "required": ["slug"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "list_pages":
        kind = _normalize_kind(arguments["kind"])
        folder = META if kind == "meta" else WIKI / kind
        slugs = [p.stem for p in _iter_md(folder)]
        return [TextContent(type="text", text="\n".join(slugs) or "(empty)")]

    if name == "search":
        query = arguments["query"]
        scope = arguments.get("scope", "wiki")
        limit = int(arguments.get("limit", 50))
        roots = [WIKI] + ([RAW] if scope == "all" else [])
        hits: list[str] = []
        rx = re.compile(re.escape(query), re.IGNORECASE)
        for root in roots:
            for p in root.rglob("*.md"):
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                for i, line in enumerate(text.splitlines(), start=1):
                    if rx.search(line):
                        rel = p.relative_to(ROOT).as_posix()
                        hits.append(f"{rel}:{i}: {line.strip()[:200]}")
                        if len(hits) >= limit:
                            return [TextContent(type="text", text="\n".join(hits))]
        return [TextContent(type="text", text="\n".join(hits) or "(no hits)")]

    if name == "lint":
        return [TextContent(type="text", text=_run_inproc("lint"))]

    if name == "stats":
        return [TextContent(type="text", text=_run_inproc("stats"))]

    if name == "read_page":
        kind = _normalize_kind(arguments["kind"])
        slug = arguments["slug"]
        folder = META if kind == "meta" else WIKI / kind
        target = folder / f"{slug}.md"
        if not target.is_file():
            return [TextContent(type="text", text=f"page not found: {kind}/{slug}")]
        try:
            return [TextContent(type="text", text=target.read_text(encoding="utf-8"))]
        except OSError as exc:
            return [TextContent(type="text", text=f"[error] {exc}")]

    if name == "read_raw":
        rel = Path(arguments["rel_path"])
        if any(part == ".." for part in rel.parts) or rel.is_absolute():
            return [TextContent(type="text", text="rejected: rel_path must be inside raw/ and free of `..`")]
        target = RAW / rel
        if not target.is_file():
            return [TextContent(type="text", text=f"raw file not found: {rel.as_posix()}")]
        try:
            return [TextContent(type="text", text=target.read_text(encoding="utf-8"))]
        except UnicodeDecodeError:
            return [TextContent(type="text", text=f"[binary file — read_raw skipped: {rel.as_posix()}]")]
        except OSError as exc:
            return [TextContent(type="text", text=f"[error] {exc}")]

    if name == "read_index":
        return [TextContent(type="text", text=(WIKI / "index.md").read_text(encoding="utf-8"))]

    if name == "read_log":
        return [TextContent(type="text", text=(WIKI / "log.md").read_text(encoding="utf-8"))]

    if name == "write_page":
        kind = _normalize_kind(arguments["kind"])
        slug = arguments["slug"]
        content = arguments["content"]
        overwrite = bool(arguments.get("overwrite", False))

        if kind not in WIKI_KINDS_WRITE:
            return [TextContent(type="text", text=f"rejected: kind must be in {list(WIKI_KINDS_WRITE)}")]
        if not re.fullmatch(r"[A-Za-z0-9_\-\.]+", slug):
            return [TextContent(type="text", text="rejected: slug must be alphanumeric (+ dash/underscore/dot) only")]

        # kind=index — wiki/index.md 직접 편집 (v0.2.1)
        if kind == "index":
            if slug != "index":
                return [TextContent(type="text", text="rejected: kind=index requires slug='index' (target = wiki/index.md)")]
            target = WIKI / "index.md"
            # index.md 는 항상 존재 → overwrite=true 강제
            if not overwrite:
                return [TextContent(type="text", text="rejected: kind=index always exists. Pass overwrite=true to replace.")]
            # frontmatter 검증 skip — index.md 는 frontmatter 없음
            try:
                target.write_text(content, encoding="utf-8")
                return [TextContent(type="text", text=f"updated: wiki/index.md ({len(content)} bytes)")]
            except OSError as exc:
                return [TextContent(type="text", text=f"[error] {exc}")]

        # 일반 kind (sources/entities/concepts/synthesis)
        if not content.lstrip().startswith("---"):
            return [TextContent(type="text", text="rejected: content must start with YAML frontmatter (---)")]

        target = WIKI / kind / f"{slug}.md"
        if target.exists() and not overwrite:
            return [TextContent(type="text", text=f"rejected: {target.relative_to(ROOT).as_posix()} already exists. Pass overwrite=true to replace.")]

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            action = "updated" if overwrite and target.exists() else "created"
            return [TextContent(type="text", text=f"{action}: {target.relative_to(ROOT).as_posix()} ({len(content)} bytes)")]
        except OSError as exc:
            return [TextContent(type="text", text=f"[error] {exc}")]

    if name == "append_log":
        from datetime import date
        op = arguments["op"]
        title = arguments["title"]
        body = arguments["body"]
        today = date.today().isoformat()
        entry = f"\n\n---\n\n## [{today}] {op} | {title}\n\n{body.rstrip()}\n"
        log_path = WIKI / "log.md"
        try:
            with log_path.open("a", encoding="utf-8") as f:
                f.write(entry)
            return [TextContent(type="text", text=f"appended {len(entry)} bytes to wiki/log.md (## [{today}] {op} | {title})")]
        except OSError as exc:
            return [TextContent(type="text", text=f"[error] {exc}")]

    if name == "synthesis_seed":
        from datetime import date
        topic = arguments["topic"]
        slug = arguments.get("slug") or _slugify(topic)
        extra = arguments.get("extra_keywords") or []
        keywords = list(dict.fromkeys(_extract_keywords(topic) + list(extra)))
        related = _discover_related(keywords)

        target = WIKI / "synthesis" / f"{slug}.md"
        if target.exists():
            return [TextContent(type="text", text=f"NOTE: wiki/synthesis/{slug}.md already exists. Either pick a different slug or read it via read_page kind=synthesis slug={slug} before calling write_page with overwrite=true.")]

        today = date.today().isoformat()

        def _yaml_list(prefix: str, items: list[str]) -> str:
            if not items:
                return f"{prefix}: []"
            return f"{prefix}:\n" + "\n".join(f'  - "[[{prefix.split(":")[0]}/{s}]]"' for s in items)

        sources_yaml = _yaml_list("sources", related["sources"])
        entities_yaml = _yaml_list("entities", related["entities"])
        concepts_yaml = _yaml_list("concepts", related["concepts"])

        scaffold = f"""---
type: synthesis
title: "{topic}"
slug: {slug}
created: {today}
last_updated: {today}
{sources_yaml}
{entities_yaml}
{concepts_yaml}
status: draft
tags: [synthesis]
---

# {topic}

> 작성: {today} · status: draft
> Auto-discovered: {len(related['sources'])} sources / {len(related['entities'])} entities / {len(related['concepts'])} concepts

## 1. 정의 / Thesis

(LLM: 한 줄 요약 — 이 synthesis 의 핵심 주장)

## 2. 핵심 매트릭스 / 결정 트리

(LLM: 비교 표 또는 결정 트리. 관련 sources 의 핵심을 종합)

## 3. 단계별 / 사례

(LLM: 구체적 시나리오와 단계)

## 4. 함정 / 열린 질문

- [ ] (LLM: 이 주제에서 자주 만나는 함정)
- [ ] (LLM: 추가 조사가 필요한 열린 질문)

## 5. 관련

### Sources ({len(related['sources'])})

{', '.join(f'[[sources/{s}]]' for s in related['sources']) or '(none auto-discovered — adjust extra_keywords)'}

### Entities ({len(related['entities'])})

{', '.join(f'[[entities/{e}]]' for e in related['entities']) or '(none)'}

### Concepts ({len(related['concepts'])})

{', '.join(f'[[concepts/{c}]]' for c in related['concepts']) or '(none)'}
"""

        guidance = f"""SCAFFOLD ready for {slug}. Workflow:
1. Use read_page kind=sources slug=<each-related> to gather context for §1-§3.
2. Compose body filling the (LLM: ...) placeholders.
3. Call write_page kind=synthesis slug={slug} content=<full markdown> overwrite=false.
4. Call synthesis_finalize slug={slug} status=living summary=<one-line>.

KEYWORDS USED: {', '.join(keywords) or '(none — provide extra_keywords)'}

---

{scaffold}
"""
        return [TextContent(type="text", text=guidance)]

    if name == "synthesis_finalize":
        from datetime import date
        slug = arguments["slug"]
        status = arguments.get("status", "living")
        summary = arguments.get("summary", "")
        target = WIKI / "synthesis" / f"{slug}.md"

        if not target.exists():
            return [TextContent(type="text", text=f"rejected: wiki/synthesis/{slug}.md not found. Call write_page first.")]

        # Run lint via in-process helper — must be 0 issues (or surface them)
        try:
            lint_result = _run_inproc("lint")
        except Exception as exc:  # noqa: BLE001
            lint_result = f"[error] {exc}"

        if "0 issues" not in lint_result.split("\n", 1)[0]:
            return [TextContent(type="text", text=f"rejected: lint reports issues — fix before finalize.\n\n{lint_result}")]

        # Update wiki/index.md — bump `## Synthesis (N)` count
        idx_path = WIKI / "index.md"
        try:
            idx_text = idx_path.read_text(encoding="utf-8")
        except OSError as exc:
            return [TextContent(type="text", text=f"[error] reading index.md: {exc}")]

        new_count = sum(1 for _ in (WIKI / "synthesis").glob("*.md"))
        idx_text_new = re.sub(
            r"^## Synthesis \(\d+\)",
            f"## Synthesis ({new_count})",
            idx_text,
            count=1,
            flags=re.MULTILINE,
        )
        if idx_text_new != idx_text:
            idx_path.write_text(idx_text_new, encoding="utf-8")
            idx_msg = f"index.md: ## Synthesis ({new_count}) updated"
        else:
            idx_msg = "index.md: no `## Synthesis (N)` header found — skipped"

        # Append log entry
        today = date.today().isoformat()
        log_body = f"""[[synthesis/{slug}]] — status: {status}
{summary}

검증: lint 0 issues / wiki/index.md `## Synthesis (N)` 갱신.
""".strip()
        log_path = WIKI / "log.md"
        log_entry = f"\n\n---\n\n## [{today}] synthesis | {slug}\n\n{log_body}\n"
        try:
            with log_path.open("a", encoding="utf-8") as f:
                f.write(log_entry)
            log_msg = f"log.md: appended `## [{today}] synthesis | {slug}`"
        except OSError as exc:
            log_msg = f"log.md error: {exc}"

        return [TextContent(type="text", text=f"finalized: synthesis/{slug}\n- {idx_msg}\n- {log_msg}\n\n{lint_result.splitlines()[0]}")]

    if name == "query_recap":
        from datetime import date
        question = arguments["question"]
        mode = arguments.get("mode", "append_to_log")
        answer = arguments.get("answer_summary", "")
        today = date.today().isoformat()
        q_short = question.strip().splitlines()[0][:120]

        if mode == "skip":
            return [TextContent(type="text", text="skipped: no filing performed.")]

        if mode == "append_to_log":
            body = f"**Q**: {question.strip()}"
            if answer.strip():
                body += f"\n\n**A**: {answer.strip()}"
            entry = f"\n\n---\n\n## [{today}] query | {q_short}\n\n{body}\n"
            try:
                with (WIKI / "log.md").open("a", encoding="utf-8") as f:
                    f.write(entry)
                return [TextContent(type="text", text=f"appended to wiki/log.md as `## [{today}] query | {q_short}` ({len(entry)} bytes)")]
            except OSError as exc:
                return [TextContent(type="text", text=f"[error] {exc}")]

        if mode == "append_to_page":
            kind = arguments.get("target_kind")
            slug = arguments.get("target_slug")
            if kind not in WIKI_KINDS:
                return [TextContent(type="text", text=f"rejected: target_kind must be in {list(WIKI_KINDS)}")]
            if not slug or not re.fullmatch(r"[A-Za-z0-9_\-\.]+", slug):
                return [TextContent(type="text", text="rejected: invalid target_slug (alphanumeric + dash/underscore/dot only)")]
            target = WIKI / kind / f"{slug}.md"
            if not target.is_file():
                return [TextContent(type="text", text=f"rejected: page not found — {kind}/{slug}")]
            section = f"\n\n## Q&A — {q_short} ({today})\n\n**Q**: {question.strip()}\n\n**A**: {answer.strip() or '(no answer body provided)'}\n"
            try:
                with target.open("a", encoding="utf-8") as f:
                    f.write(section)
                # Also log this filing-back action
                log_entry = f"\n\n---\n\n## [{today}] query | {q_short}\n\nFiled back as Q&A section of [[{kind}/{slug}]].\n"
                with (WIKI / "log.md").open("a", encoding="utf-8") as f:
                    f.write(log_entry)
                return [TextContent(type="text", text=f"appended `## Q&A — {q_short}` to {kind}/{slug} ({len(section)} bytes) + log entry written.")]
            except OSError as exc:
                return [TextContent(type="text", text=f"[error] {exc}")]

        if mode == "propose_synthesis":
            topic = arguments.get("synthesis_topic") or question.strip()
            synth_slug = arguments.get("synthesis_slug") or _slugify(topic)
            log_entry = (
                f"\n\n---\n\n## [{today}] query | {q_short}\n\n"
                f"**Q**: {question.strip()}\n\n"
                f"**A** (summary): {answer.strip() or '(see synthesis page)'}\n\n"
                f"Disposition: propose_synthesis → [[synthesis/{synth_slug}]]\n"
            )
            try:
                with (WIKI / "log.md").open("a", encoding="utf-8") as f:
                    f.write(log_entry)
                next_step = (
                    f"PROPOSED. Next 4 steps for the agent:\n"
                    f'  [1] mcwiki:synthesis_seed topic="{topic}" slug={synth_slug}\n'
                    f"  [2] mcwiki:read_page on each related item from the seed output\n"
                    f"  [3] mcwiki:write_page kind=synthesis slug={synth_slug} content=<composed body>\n"
                    f"  [4] mcwiki:synthesis_finalize slug={synth_slug} status=living summary=<one-line>\n"
                )
                return [TextContent(type="text", text=f"logged query proposing synthesis [[synthesis/{synth_slug}]].\n\n{next_step}")]
            except OSError as exc:
                return [TextContent(type="text", text=f"[error] {exc}")]

        return [TextContent(type="text", text=f"unknown mode: {mode}")]

    if name == "git_status":
        git_dir = ROOT / ".git"
        if not git_dir.exists():
            return [TextContent(type="text", text="not a git repo")]

        # Always-available fallback: read .git/HEAD directly (no git binary needed).
        branch_fallback = "(detached or unknown)"
        try:
            head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
            if head.startswith("ref: refs/heads/"):
                branch_fallback = head[len("ref: refs/heads/"):]
            else:
                branch_fallback = f"detached@{head[:8]}"
        except OSError:
            pass

        # Try the git CLI for richer info; fall back gracefully.
        rc1, branch, err1 = _git("rev-parse", "--abbrev-ref", "HEAD")
        rc2, dirty, err2 = _git("status", "--porcelain")
        rc3, ahead_behind, _ = _git("rev-list", "--left-right", "--count", "HEAD...@{upstream}")

        if rc1 != 0 or not branch.strip():
            # git binary missing or in error state — use HEAD-file fallback
            out_lines = [
                f"branch: {branch_fallback}  (read from .git/HEAD; git CLI unavailable)",
                f"git CLI: rc={rc1} {err1.strip()}",
            ]
        else:
            out_lines = [
                f"branch: {branch.strip()}",
                f"ahead/behind (vs upstream): {ahead_behind.strip() or '(no upstream)'}",
                f"dirty: {len(dirty.splitlines())} file(s)",
            ]
            if dirty.strip():
                out_lines.append(dirty.rstrip())
        return [TextContent(type="text", text="\n".join(out_lines))]

    if name == "git_pull":
        if not (ROOT / ".git").exists():
            return [TextContent(type="text", text="not a git repo")]
        rc, out, err = _git("pull", "--ff-only")
        return [TextContent(type="text", text=f"[rc={rc}] {out}{err}")]

    if name == "find_cross_link_broken":
        slug = arguments["slug"]
        kind = arguments.get("kind")
        if kind:
            kind = _normalize_kind(kind)
        # v0.3.1 (Cycle 5i) - handler signature + vault_root explicit
        from find_cross_link_broken import find_cross_link_broken_handler as _fclb
        result = _fclb(slug, kind, vault_root=WIKI)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    if name == "suggest_missing_cross_link":
        slug = arguments["slug"]
        kind = arguments.get("kind")
        if kind:
            kind = _normalize_kind(kind)
        min_inbound = int(arguments.get("min_inbound", 1))
        from suggest_missing_cross_link import suggest_missing_cross_link_handler
        result = suggest_missing_cross_link_handler(
            slug, kind, vault_root=WIKI, min_inbound=min_inbound
        )
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    if name == "find_claim_conflict":
        slug_a = arguments["slug_a"]
        slug_b = arguments["slug_b"]
        kind_a = arguments.get("kind_a")
        if kind_a:
            kind_a = _normalize_kind(kind_a)
        kind_b = arguments.get("kind_b")
        if kind_b:
            kind_b = _normalize_kind(kind_b)
        from find_claim_conflict import find_claim_conflict_handler
        result = find_claim_conflict_handler(
            slug_a, slug_b, kind_a, kind_b, vault_root=WIKI
        )
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    if name == "find_stale_baseline":
        slug = arguments["slug"]
        kind = arguments.get("kind")
        if kind:
            kind = _normalize_kind(kind)
        threshold_days = int(arguments.get("threshold_days", 90))
        from find_stale_baseline import find_stale_baseline_handler
        result = find_stale_baseline_handler(
            slug, kind, threshold_days, vault_root=WIKI
        )
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    if name == "ingest_seed":
        slug = arguments["slug"]
        src = arguments["source_path"]
        title = arguments.get("title", slug)
        target = WIKI / "sources" / f"{slug}.md"
        if target.exists():
            return [TextContent(type="text", text=f"already exists: {target}")]
        tmpl = (TEMPLATES / "source.md").read_text(encoding="utf-8")
        from datetime import date
        today = date.today().isoformat()

        # Substitute both Templater-style descriptive placeholders (<TITLE>, etc.)
        # and {{var}} curly-style. Covers all template formats in use.
        replacements = {
            # Descriptive (<X>) — Obsidian Templater compat
            "<TITLE>": title,
            "<kebab-case-slug>": slug,
            "<source_path>": src,
            "<source_kind>": "text",
            "<source_date>": today,
            "<5–15 lines. After reading this paragraph alone, the reader knows what the source delivers.>": f"(LLM: 5–15 lines summary of {src})",
            "<location §, p., HH:MM:SS>": "(LLM: fill in)",
            "<short quote>": "(LLM: short quote)",
            # Curly ({{x}}) — same set, both styles supported
            "{{title}}": title,
            "{{slug}}": slug,
            "{{source_path}}": src,
            "{{source_kind}}": "text",
            "{{source_date}}": today,
            "{{date}}": today,
            "{{date:YYYY-MM-DD}}": today,
        }
        body = tmpl
        for old, new in replacements.items():
            body = body.replace(old, new)

        # Ensure frontmatter `type: source` is present even if template misses it
        if "type: source" not in body[:200]:
            body = f"""---
type: source
title: "{title}"
slug: {slug}
source_path: {src}
source_kind: text
source_date: {today}
ingested: {today}
related_entities: []
related_concepts: []
tags: []
---

# {title}

> Source: [[{src}]]

""" + body

        target.write_text(body, encoding="utf-8")
        return [TextContent(type="text", text=f"created: {target.relative_to(ROOT).as_posix()} ({len(body)} bytes)")]

    raise ValueError(f"unknown tool: {name}")


def _run_py(script: str) -> str:
    """Legacy subprocess runner — kept for fallback. Prefer _run_inproc."""
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / script)],
        capture_output=True, text=True, cwd=ROOT, timeout=20,
    )
    return (proc.stdout or "") + (("\n[stderr]\n" + proc.stderr) if proc.stderr else "")


def _run_inproc(module_name: str) -> str:
    """Call lint/stats in-process *without* redirect_stdout.

    The previous implementation used contextlib.redirect_stdout which broke
    the MCP server because stdio_server uses stdin/stdout for JSON-RPC —
    swapping sys.stdout corrupted the protocol channel.  Here we instead call
    the report-building helpers directly and return the formatted string.
    """
    import importlib

    tools_dir = str(ROOT / "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)

    try:
        mod = importlib.import_module(module_name)
        importlib.reload(mod)  # pick up edits between calls

        if module_name == "lint":
            issues, summary = mod.lint()
            lines = [f"Lint: {summary.get('pages', 0)} pages, {summary.get('issues', 0)} issues."]
            for it in issues[:50]:
                lines.append(f"  [{it['code']}] {it['page']}  {it['detail']}")
            for code, n in sorted(summary.get("by_code", {}).items()):
                lines.append(f"  - {code}: {n}")
            if len(issues) > 50:
                lines.append(f"  ... +{len(issues) - 50} more")
            return "\n".join(lines)

        if module_name == "stats":
            s = mod.collect()
            if s is None:
                return "wiki/ not found."
            lines = ["# Wiki Stats"]
            lines.append(f"sources:    {s.sources}")
            lines.append(f"entities:   {s.entities}")
            lines.append(f"concepts:   {s.concepts}")
            lines.append(f"synthesis:  {s.synthesis}")
            lines.append(f"orphans:    {s.orphans}")
            return "\n".join(lines)
        return f"unknown module: {module_name}"
    except Exception as exc:
        return f"[error] {type(exc).__name__}: {exc}"


# ---------------------------------------------------------------------------
# Entry point

async def _main() -> None:
    _git_pull_if_repo()
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(_main())
