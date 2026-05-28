---
type: entity
title: "IMainFrameModule"
aliases: ["IMainFrameModule", "MainFrame Module Interface"]
kind: paper
sources:
  - "[[sources/ue-editor-mainframe]]"
tags: [ue, entity, editor, mainframe, 🛠]
last_updated: 2026-05-17
---

# IMainFrameModule

> Editor 모듈 — UnrealEd MainFrame 윈도우 (Editor 의 root 윈도우, 메인 메뉴/툴바/상태 바 호스트) 의 module interface. 🛠 Editor-only.

## 1. Summary

🟢 **IMainFrameModule** = UE Editor 의 MainFrame 윈도우 관리 module interface ([[sources/ue-editor-mainframe]]). `IModuleInterface` 자손 — `FModuleManager::LoadModuleChecked<IMainFrameModule>("MainFrame")` 으로 접근.

🟡 주요 역할 (vault 근거 + 외삽):
- Editor 메인 윈도우 (`SDockableTab` 호스트 root) 의 lifecycle 관리
- Top-level 메뉴 (`File / Edit / Window / Tools / Help`) 호스트
- 상태 바 (`Bottom toolbar`) — FNotificationManager 연결
- MainFrame creation 콜백 — `OnMainFrameCreationFinished()` (5.x — plugin 초기화 hook)
- Project Browser / Map Selection 등 modal 다이얼로그 호스트

## 2. 핵심 API (🔴 INFERRED — 정밀 vault page 미작성)

🔴 추론 (vault 미확정 — Cycle 5p+2 후속 enrich 후보):
- `GetMainFrameCommandBindings()` — `TSharedRef<FUICommandList>` (메인 메뉴 단축키 binding)
- `MakeMainMenu()` — `TSharedRef<SWidget>` (메인 메뉴 widget 빌드)
- `OnMainFrameCreationFinished` — `FMainFrameCreationFinishedEvent` (Editor 시작 완료 콜백)
- `IsWindowInitialized()` — bool (MainFrame 초기화 완료 여부)
- `ShowAboutWindow()` — modal About 다이얼로그

→ 검증 필요: `Engine/Source/Editor/MainFrame/Public/Interfaces/IMainFrameModule.h`

## 3. Usage Pattern (인하우스 에디터 작업 시)

🟡 표준 사용 — Plugin/Editor 모듈 초기화 시:

```cpp
// In FMyEditorModule::StartupModule
IMainFrameModule& MainFrameModule = FModuleManager::LoadModuleChecked<IMainFrameModule>("MainFrame");
MainFrameModule.OnMainFrameCreationFinished().AddRaw(this, &FMyEditorModule::OnMainFrameReady);
```

[[sources/ue-editor-mainframe]] §사용 패턴 참조.

## 4. Cross-link

- [[sources/ue-editor-mainframe]] (메인 catalog)
- [[sources/ue-editor-skill]] (Editor 메인 SKILL)
- [[concepts/Editor-Only-4-Tier-Separation]] (4단 분리 의무 — IMainFrameModule = Editor 모듈 전용)
- [[00_meta/07_AgentBoundaryProtocol]] §1.2 예시 — vault 안 entity 중복 방지 사례로 인용

## 5. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-17 (Cycle 5p+1 D) | 최초 작성 (stub). [[00_meta/07_AgentBoundaryProtocol]] §1.2 의 broken [[entities/IMainFrameModule]] wikilink 해소 + Editor module 카탈로그 entity 보강. 정밀 enrich 는 Cycle 5p+2 후속 (Engine 본가 `IMainFrameModule.h` grep 검증 의무). |
