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
