---
type: source
title: "UE SlateCore — Trace sub-skill"
slug: ue-slatecore-trace
source_path: raw/ue-wiki-llm/skills/SlateCore/references/Trace.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, slate, editor, debug]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
---

# UE SlateCore — Trace sub-skill

> Source: [[raw/ue-wiki-llm/skills/SlateCore/references/Trace.md]]
> Parent: [[sources/ue-slatecore-skill]]

## 1. Summary

🛠 Slate Trace — Insights 통합 + WidgetReflector + DebugWidgets cvar.

## 2. Key claims

- Slate.Trace channel: Insights 의 Slate 측 (paint / invalidate / focus 추적).
- WidgetReflector: 마우스로 위젯 hover → 정보 표시 (Class / Tooltip / Path). Editor 의 강력한 디버그 도구.
- Slate Insights: paint frequency / invalidation hot spot / layout 비용.
- DebugWidgets cvar: Slate.GlobalInvalidation, Slate.AlwaysInvalidate 등.
- WidgetReflector 단축키: Ctrl+Alt+W (Editor).
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
