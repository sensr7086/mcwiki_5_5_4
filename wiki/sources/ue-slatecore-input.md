---
type: source
title: "UE SlateCore — Input sub-skill"
slug: ue-slatecore-input
source_path: raw/ue-wiki-llm/skills/SlateCore/references/Input.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, slate, ui, input]
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
