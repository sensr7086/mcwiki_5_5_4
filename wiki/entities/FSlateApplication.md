---
type: entity
title: "FSlateApplication"
aliases: [FSlateApplication]
kind: model
sources:
  - "[[sources/ue-slate-skill]]"
tags: [ue, slate, ui]
last_updated: 2026-05-09
---

# FSlateApplication

## 요약

Slate 의 본체. 게임 + 에디터 공통 Application. 입력 라우팅 (마우스/키보드/터치) + 렌더 사이클 + 윈도우 관리 + Modal/PopUp + Tick 진입점. `FSlateApplication::Get()` 싱글톤 패턴.

## 관계

- 베이스: FGenericApplicationMessageHandler
- 협력: [[entities/SWidget]] (모든 위젯), FTabManager, IInputDevice

## 핵심 주장

- Tick: 매 프레임 호출. SWidget 들의 OnTick + Layout 갱신.
- 입력 라우팅: Mouse / Keyboard / Touch / Controller. SWidget 의 OnMouseButtonDown 등 callback 발화.
- Modal 윈도우: `AddModalWindow(SWindow, Parent)` — UI 차단.
- 렌더 호출: 매 프레임 OnPaint 사이클 → FSlateDrawElement 누적 → Slate Renderer.
- 게임 빌드 vs 에디터: 둘 다 동일 Application — 단 Editor 는 추가 SWindow 와 Tab 관리.

## 열린 질문

- [ ] 게임 World 의 Slate Tick 과 Engine Tick 의 순서
- [ ] Input Preprocessor 의 등록 패턴
