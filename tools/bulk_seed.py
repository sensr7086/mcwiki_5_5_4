#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bulk seed wiki/sources/ stubs from a raw/ subtree.

Walks raw/<path>/ recursively, finds every .md file, creates a wiki/sources/<slug>.md
stub for each one. Slugs are derived from raw path (kebab-case, with parent folders).

The LLM later fills the stub bodies via "ingest" (CLAUDE.md §5.1 step 1-10).

Usage:
  python tools/bulk_seed.py raw/ue-wiki-llm/skills/Animation/
  python tools/bulk_seed.py raw/ue-wiki-llm/skills/Animation/ --kind text
  python tools/bulk_seed.py raw/ue-wiki-llm/ --dry-run
  python tools/bulk_seed.py raw/ue-wiki-llm/skills/Animation/ --prefix ue-animation

Dependencies: stdlib only.
"""
from __future__ import annotations
import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
RAW = ROOT / "raw"
TMPL = ROOT / "templates" / "source.md"


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^\w\s\-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s).strip("-")
    s = re.sub(r"-+", "-", s)
    return s or "untitled"


def derive_slug(rel_path: Path, prefix: str = "") -> str:
    """raw/ue-wiki-llm/skills/Animation/SKILL.md -> ue-skills-animation-skill"""
    parts = list(rel_path.with_suffix("").parts)
    # Skip "raw" prefix and "ue-wiki-llm" if present
    if parts and parts[0] == "raw":
        parts = parts[1:]
    # Compress: take last 3-4 meaningful parts
    if len(parts) > 4:
        parts = parts[-4:]
    slug = "-".join(slugify(p) for p in parts if p and p.lower() not in ("readme",))
    if prefix:
        slug = prefix + "-" + slug
    return slug


def derive_title(rel_path: Path) -> str:
    """raw/ue-wiki-llm/skills/Animation/SKILL.md -> 'Animation / SKILL'"""
    parts = list(rel_path.with_suffix("").parts)
    if parts and parts[0] == "raw":
        parts = parts[1:]
    if len(parts) > 4:
        parts = parts[-4:]
    return " / ".join(parts)


def fill(template: str, **kw) -> str:
    out = template
    pairs = [
        ("<TITLE>", kw["title"]),
        ("<kebab-case-slug>", kw["slug"]),
        ("<source_path>", kw["source_path"]),
        ("<relative path>", kw["source_path"]),
        ("<source_kind>", kw["source_kind"]),
        ("<source_date>", kw["source_date"]),
        ("{{date:YYYY-MM-DD}}", kw["today"]),
    ]
    for k, v in pairs:
        out = out.replace(k, v)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("subtree", help="raw/ subtree, e.g. raw/ue-wiki-llm/skills/Animation/")
    ap.add_argument("--kind", default="text", help="source_kind (default text)")
    ap.add_argument("--prefix", default="", help="slug prefix")
    ap.add_argument("--dry-run", action="store_true", help="show actions, don't write")
    ap.add_argument("--no-log", action="store_true")
    ap.add_argument("--ext", default=".md", help="file extension (default .md)")
    args = ap.parse_args()

    subtree = (ROOT / args.subtree).resolve()
    if not subtree.exists():
        print("ERROR: subtree not found: " + str(subtree), file=sys.stderr)
        sys.exit(2)
    if not str(subtree).startswith(str(RAW)):
        print("ERROR: subtree must be inside raw/: " + str(subtree), file=sys.stderr)
        sys.exit(3)
    if not TMPL.exists():
        print("ERROR: template not found: " + str(TMPL), file=sys.stderr)
        sys.exit(4)

    today = date.today().isoformat()
    template = TMPL.read_text(encoding="utf-8")

    files = sorted([f for f in subtree.rglob("*" + args.ext) if f.is_file()])
    if not files:
        print("no files matched.")
        return 0

    print("found " + str(len(files)) + " files in " + str(subtree.relative_to(ROOT)))
    print()

    seeded = 0
    skipped = 0
    collisions = []

    for f in files:
        rel = f.relative_to(ROOT)
        slug = derive_slug(rel, prefix=args.prefix)
        title = derive_title(rel)
        out_path = WIKI / "sources" / (slug + ".md")
        if out_path.exists():
            skipped += 1
            collisions.append(slug)
            continue

        body = fill(
            template,
            title=title,
            slug=slug,
            source_path=str(rel).replace("\\", "/"),
            source_kind=args.kind,
            source_date=today,
            today=today,
        )

        if args.dry_run:
            print("  WOULD seed: " + slug + "  <- " + str(rel))
        else:
            out_path.write_text(body, encoding="utf-8")
            seeded += 1
            print("  seeded: " + slug)

    print()
    print("summary:  seeded=" + str(seeded) + "  skipped=" + str(skipped))
    if collisions:
        print("  collisions (already exist): " + ", ".join(collisions[:5])
              + (" ... " + str(len(collisions) - 5) + " more" if len(collisions) > 5 else ""))

    # log.md
    if not args.dry_run and not args.no_log and seeded > 0:
        log = WIKI / "log.md"
        if log.exists():
            text = log.read_text(encoding="utf-8")
            entry = (
                "## [" + today + "] bulk-seed | " + str(subtree.relative_to(ROOT))
                + " | source stubs: " + str(seeded) + "\n"
                + "- " + str(seeded) + " stubs created in wiki/sources/\n"
                + "- LLM next: ingest each stub (fill body, extract entities/concepts)\n\n---\n\n"
            )
            m = re.search(r"\n(## \[\d{4}-\d{2}-\d{2}\])", text)
            if m:
                i = m.start() + 1
                text = text[:i] + entry + text[i:]
            else:
                text += "\n" + entry
            log.write_text(text, encoding="utf-8")
            print("appended: wiki/log.md")

    print()
    print("Next steps:")
    print("  1) Verify:  python tools/lint.py")
    print("  2) Stats:   python tools/stats.py")
    print("  3) In LLM:  'ingest the next batch of wiki/sources/ stubs.'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
