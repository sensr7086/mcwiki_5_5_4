---
type: entity
title: "UToolMenus / UToolMenu / FToolMenuEntry"
aliases: [UToolMenus, ToolMenus, FToolMenuContext]
kind: model
sources:
  - "[[sources/ue-editor-skill]]"
tags: [ue, editor, ui]
last_updated: 2026-05-09
---

# UToolMenus

## 요약

🛠 5.x 모던 메뉴 시스템 — FMenuBuilder 의 후속. UToolMenus (UEngineSubsystem) + UToolMenu (개별 메뉴) + FToolMenuEntry (메뉴 항목) + FToolMenuContext (호출 컨텍스트). LevelEditor 의 메인 메뉴 / 콘텍스트 메뉴 / 툴바 의 표준 진입점.

## 관계

- 부모: UEngineSubsystem (UToolMenus 자체)
- 5.x 표준 위치: Editor 모듈
- Legacy: FMenuBuilder / FToolBarBuilder (FUICommandList 와 같이 사용)

## 핵심 주장

- 등록 패턴: `UToolMenus::Get()->RegisterMenu("LevelEditor.MainMenu.MyMenu")` → `Menu->AddSection` → Section 에 FToolMenuEntry 추가.
- FToolMenuEntry::InitMenuEntry(Name, Label, Tooltip, Icon, FUIAction(Callback)).
- FToolMenuContext: 메뉴 호출 시 컨텍스트 (선택된 액터 / 현재 모드 등).
- 5.x 표준 — 신규 에디터 메뉴는 무조건 UToolMenus. FMenuBuilder 는 호환만.
- LevelEditor 의 표준 메뉴 path: `MainFrame.MainMenu.*` / `LevelEditor.MainMenu.*`.

## 열린 질문

- [ ] UToolMenus 의 BP 노출 (Editor Utility Widget 통합)
- [ ] Custom Toolbar 의 표준 패턴
