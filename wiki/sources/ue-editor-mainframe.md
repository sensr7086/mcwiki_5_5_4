---
type: source
title: "UE Editor — MainFrame sub-skill"
slug: ue-editor-mainframe
source_path: raw/ue-wiki-llm/skills/Editor/references/MainFrame.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, editor, ui]
---

# UE Editor — MainFrame sub-skill

> Source: [[raw/ue-wiki-llm/skills/Editor/references/MainFrame.md]]
> Parent: [[sources/ue-editor-skill]]

## 1. Summary

🛠 MainFrame 모듈 — IMainFrameModule + OnMainFrameCreationFinished + SetApplicationTitleOverride + MainFrame.MainMenu.* 표준 메뉴.

## 2. Key claims

- IMainFrameModule::Get() 싱글톤 — Editor 의 메인 윈도우 진입점.
- OnMainFrameCreationFinished delegate — Editor Main Window 생성 후 callback (메뉴 / 툴바 추가의 표준 시점).
- SetApplicationTitleOverride: Editor 타이틀 바 변경 (회사 / 프로젝트 명).
- 표준 메뉴 path:
  - `MainFrame.MainMenu.File` (File 메뉴).
  - `MainFrame.MainMenu.Edit` (Edit 메뉴).
  - `MainFrame.MainMenu.Window` (Window 메뉴).
  - `MainFrame.MainMenu.Help` (Help 메뉴).
- LayoutExtender 통합 — 사용자 plugin 이 MainMenu 에 항목 추가.

## 3. Open questions

- [ ] OnMainFrameCreationFinished 의 timing (다른 callback 과의 순서)
