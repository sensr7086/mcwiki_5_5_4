---
type: entity
title: "FTabManager / SDockTab"
aliases: [FTabManager, SDockTab, FTabSpawner]
kind: model
sources:
  - "[[sources/ue-slate-skill]]"
tags: [ue, slate, editor, ui]
last_updated: 2026-05-09
---

# FTabManager / SDockTab

## 요약

🛠 도킹 시스템 — 사용자 dock 가능한 탭 정의 + layout 저장. FTabManager (탭 관리자) + SDockTab (실제 탭 위젯) + FTabSpawnerEntry (탭 등록). 인하우스 에디터의 표준 패턴.

## 관계

- 협력: [[entities/IToolkit]] (FAssetEditorToolkit 가 FTabManager 보유), MajorTab / MinorTab 분류

## 핵심 주장

- 표준 패턴: TabManager->RegisterTabSpawner("MyTab", FOnSpawnTab::CreateRaw(this, &FMyToolkit::SpawnMyTab)).
- FTabSpawnerEntry::SetMenuType / SetIcon / SetGroup — 메뉴 표시 메타.
- SDockTab::SetContent(SWidget) 으로 본문 채움.
- Layout 저장: FTabManager::FLayout / FStack / FArea — XML 으로 저장 가능 → 사용자 layout 보존.
- LiveTab vs DefaultTab — 사용자가 닫은 탭은 다음에 자동 복원.

## 열린 질문

- [ ] LayoutExtender 의 표준 패턴 (다른 모듈이 탭 추가)
- [ ] Sidebar Tab 5.x 의 통합
