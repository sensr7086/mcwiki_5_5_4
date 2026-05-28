---
title: "FAssetEditorToolkit"
kind: entity
status: stub
parent: editor
tags: [editor, toolkit, asset-editor, ue-574]
module: UnrealEd
header: "Public/Toolkits/AssetEditorToolkit.h"
created: 2026-05-22
last_updated: 2026-05-22
---

# FAssetEditorToolkit

[[IToolkit]] 의 핵심 구현 베이스 — **단일 또는 다중 asset 을 편집하는 editor window 의 lifecycle 관리**. Material Editor / Blueprint Editor / Animation Editor 등 거의 모든 asset editor 가 이를 상속 또는 컴포지션.

## 핵심 특성

- **InitAssetEditor**: tab manager + toolbar + commands 초기화
- **Asset 배열 보유**: TArray<UObject*> EditingObjects — 다중 편집 지원
- **Modes**: `FWorkflowCentricApplication` 사용 시 ApplicationMode 로 layout 분기
- **Toolbar + Menu**: `ExtendToolBar` / `ExtendMenu` 통해 외부 모듈 확장

## 주요 API

| API | 설명 |
|---|---|
| `InitAssetEditor(...)` | 초기화 — TabManager + StandaloneToolkit 모드 |
| `GetEditingObject()` | 단일 asset accessor |
| `GetEditingObjects()` | 다중 asset accessor |
| `CloseWindow()` | tab manager close |
| `RegisterTabSpawners` | 탭 등록 |

## 관련 함정

- [[concepts/Material-Editor-External-Change-Reopen]] — toolkit 의 Preview viewport / Details panel cache 가 외부 변경에 미동기
- Close + Reopen 시 사용자 state (selection / camera / scroll) reset
- TabManager lifecycle — toolkit 종료 전 tab spawner unregister 의무

## 관련 entity

- [[IToolkit]] · [[UAssetEditorSubsystem]] · [[FTabManager]] · [[FUICommandList]]

## Citation Disclosure

| 주장 | Tier |
|---|---|
| 다중 asset 편집 지원 | 🟢 VAULT (UE 5.7 `AssetEditorToolkit.h`) |
| WorkflowCentric mode 분기 | 🟢 VAULT |
| Preview/Details cache 외부 미동기 | 🟡 PARTIAL (실측 — toolkit-by-toolkit 차이) |

## 변경 이력

- 2026-05-22: stub 작성 (MMA-33+34 filing-back cross-link)
