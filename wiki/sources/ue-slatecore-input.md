---
type: source
title: "UE SlateCore — Input sub-skill"
slug: ue-slatecore-input
source_path: raw/ue-wiki-llm/skills/SlateCore/references/Input.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, slate, ui, input]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
---

# UE SlateCore — Input sub-skill

> Source: [[raw/ue-wiki-llm/skills/SlateCore/references/Input.md]]
> Parent: [[sources/ue-slatecore-skill]]

## 1. Summary

OnMouseButtonDown / Up + OnMouseMove + OnKeyDown + OnFocusReceived + FReply + FCaptureLostEvent + FocusManager.

## 2. Key claims

- SWidget 의 입력 callback override: OnMouseButtonDown / OnMouseButtonUp / OnMouseMove / OnMouseWheel / OnMouseEnter / OnMouseLeave / OnKeyDown / OnKeyUp / OnFocusReceived / OnFocusLost.
- FReply: handler 결과 — Handled / Unhandled / SetUserFocus / CaptureMouse / ReleaseMouseCapture.
- FCaptureLostEvent: 마우스 / 키보드 capture 강제 해제 시.
- FocusManager: focus 이동 (Tab / Shift+Tab + Programmatic SetFocus).
- 입력 라우팅: SWidget tree 따라 전파 (자식 → 부모). Handled 면 stop.
- 우선순위: Modal > Popup > Application focus widget.
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 lineshift-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **lineshift-only**. 5.5↔5.7 raw diff 가 라인 번호 shift 만 — 본문 의미 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
