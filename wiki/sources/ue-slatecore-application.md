---
type: source
title: "UE SlateCore — Application sub-skill"
slug: ue-slatecore-application
source_path: raw/ue-wiki-llm/skills/SlateCore/references/Application.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/FSlateApplication]]"
tags: [ue, slate, ui]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
---

# UE SlateCore — Application sub-skill

> Source: [[raw/ue-wiki-llm/skills/SlateCore/references/Application.md]]
> Parent: [[sources/ue-slatecore-skill]]

## 1. Summary

[[entities/FSlateApplication]] 글로벌 — GetCursorPos + GetUserIndexForKeyboard + Tooltip + Window Activation.

## 2. Key claims

- FSlateApplication::Get() 싱글톤.
- GetCursorPos() / SetCursorPos() — 마우스 위치.
- GetUserIndexForKeyboard / GetUserIndexForController — 멀티유저 (Couch Co-op) 입력 식별.
- Tooltip: 자동 hover tooltip 시스템. SetToolTip(SWidget) 으로 등록.
- Window Activation: OnActiveWindowChanged delegate. Game / Editor 윈도우 전환.
- Tick: 매 프레임 호출. SWidget Tick + Layout 갱신.
- AddModalWindow(Window, Parent): 모달 윈도우 (UI 차단).
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 lineshift-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **lineshift-only**. 5.5↔5.7 raw diff 가 라인 번호 shift 만 — 본문 의미 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
