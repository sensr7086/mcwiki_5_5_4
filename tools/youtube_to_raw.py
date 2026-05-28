#!/usr/bin/env python3
"""
YouTube URL → raw/youtube/<slug>.md (자막 + 메타).

자막은 youtube-transcript-api (pip install) 로 추출 — 외부 transcription API 안 씀.
영상 자체 다운로드 안 함. 자막 없는 영상은 실패.

사용법:
  pip install youtube-transcript-api
  python tools/youtube_to_raw.py https://www.youtube.com/watch?v=kCc8FmEb1nY
  python tools/youtube_to_raw.py https://youtu.be/zduSFxRajkE --lang ko en
  python tools/youtube_to_raw.py <url> --slug lets-build-gpt

출력:
  raw/youtube/<slug>.md  — frontmatter + 1줄당 [HH:MM:SS] timestamp 자막
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw" / "youtube"


def extract_video_id(url: str) -> str | None:
    p = urlparse(url)
    if p.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        if p.path == "/watch":
            return parse_qs(p.query).get("v", [None])[0]
        if p.path.startswith("/embed/") or p.path.startswith("/v/"):
            return p.path.split("/")[2]
    if p.hostname in ("youtu.be",):
        return p.path.lstrip("/")
    return None


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^\w\s\-가-힣]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s).strip("-")
    s = re.sub(r"-+", "-", s)
    return s or "untitled"


def hms(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="YouTube URL (전체 또는 youtu.be 단축)")
    ap.add_argument("--lang", nargs="+", default=["en", "ko"], help="자막 언어 우선순위")
    ap.add_argument("--slug", help="명시 slug")
    ap.add_argument("--title", help="명시 title (없으면 video id)")
    args = ap.parse_args()

    vid = extract_video_id(args.url)
    if not vid:
        print(f"ERROR: video id 추출 실패: {args.url}", file=sys.stderr)
        sys.exit(2)

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        print("youtube-transcript-api 가 설치돼 있지 않음.\n"
              "  pip install youtube-transcript-api", file=sys.stderr)
        sys.exit(3)

    try:
        transcript = YouTubeTranscriptApi.get_transcript(vid, languages=args.lang)
    except Exception as e:
        print(f"ERROR: 자막 가져오기 실패: {e}", file=sys.stderr)
        sys.exit(4)

    title = args.title or f"YouTube {vid}"
    slug = args.slug or slugify(title)
    today = date.today().isoformat()

    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / f"{slug}.md"
    if out.exists():
        print(f"ERROR: 이미 존재: {out}", file=sys.stderr)
        sys.exit(5)

    lines = []
    lines.append("---")
    lines.append(f'title: "{title}"')
    lines.append(f'video_id: "{vid}"')
    lines.append(f'url: "https://www.youtube.com/watch?v={vid}"')
    lines.append(f"fetched: {today}")
    lines.append(f'transcript_lang: "{args.lang[0]}"')
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"원본 영상: <https://www.youtube.com/watch?v={vid}>")
    lines.append("")
    lines.append("## Transcript")
    lines.append("")
    for entry in transcript:
        ts = hms(entry["start"])
        text = entry["text"].replace("\n", " ").strip()
        lines.append(f"[{ts}] {text}")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"created: {out.relative_to(ROOT)}  ({len(transcript)} segments)")
    print()
    print("다음 단계:")
    print(f"  python tools/ingest_seed.py \"{title}\" raw/youtube/{slug}.md youtube")
    print(f"  그 후 LLM 에 발화: \"ingest wiki/sources/{slug}.md\"")


if __name__ == "__main__":
    main()