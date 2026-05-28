#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create a new wiki/sources/<slug>.md from templates/source.md, plus a log entry.

This script does the MECHANICAL part of CLAUDE.md ingest workflow steps 6-9.
The LLM does steps 1-5 and the body fill afterwards.

Usage:
  python tools/ingest_seed.py "Title" raw/articles/x.md url
  python tools/ingest_seed.py "Title" raw/x.md url --slug=x --no-log

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
KINDS = {"pdf", "url", "youtube", "text", "image", "audio", "video"}


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^\w\s\-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s).strip("-")
    s = re.sub(r"-+", "-", s)
    return s or "untitled"


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
    ap.add_argument("title")
    ap.add_argument("source_path")
    ap.add_argument("source_kind", choices=sorted(KINDS))
    ap.add_argument("--slug")
    ap.add_argument("--source-date", default=None)
    ap.add_argument("--no-log", action="store_true")
    args = ap.parse_args()

    sp = args.source_path
    if sp.startswith("raw/"):
        full = RAW / sp[len("raw/"):]
        source_path = sp
    else:
        full = RAW / sp
        source_path = "raw/" + sp

    if not full.exists():
        print("WARN: not in raw/: " + str(full), file=sys.stderr)

    today = date.today().isoformat()
    slug = args.slug or slugify(args.title)
    source_date = args.source_date or today

    if not TMPL.exists():
        print("ERROR: template not found: " + str(TMPL), file=sys.stderr)
        sys.exit(2)

    body = fill(
        TMPL.read_text(encoding="utf-8"),
        title=args.title,
        slug=slug,
        source_path=source_path,
        source_kind=args.source_kind,
        source_date=source_date,
        today=today,
    )

    out_path = WIKI / "sources" / (slug + ".md")
    if out_path.exists():
        print("ERROR: exists: " + str(out_path), file=sys.stderr)
        sys.exit(3)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body, encoding="utf-8")
    print("created: " + str(out_path.relative_to(ROOT)))

    if not args.no_log:
        log = WIKI / "log.md"
        if log.exists():
            text = log.read_text(encoding="utf-8")
            entry = (
                "## [" + today + "] ingest | " + args.title
                + " | source: " + slug + " | touched: 1\n"
                + "- sources/" + slug + " (new -- LLM fills body next)\n\n---\n\n"
            )
            m = re.search(r"\n(## \[\d{4}-\d{2}-\d{2}\])", text)
            if m:
                i = m.start() + 1
                text = text[:i] + entry + text[i:]
            else:
                text += "\n" + entry
            log.write_text(text, encoding="utf-8")
            print("appended: wiki/log.md")

    print("")
    print("Next:")
    print("  In your LLM agent, say:  ingest " + str(out_path.relative_to(ROOT)))
    print("  The LLM reads raw, fills the source body, updates entities/concepts.")


if __name__ == "__main__":
    main()
