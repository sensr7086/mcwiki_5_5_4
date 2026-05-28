---
type: entity
title: "IToolkit / IToolkitHost / UEdMode"
aliases: [IToolkit, FAssetEditorToolkit, IToolkitHost, UEdMode]
kind: model
sources:
  - "[[sources/ue-editor-skill]]"
tags: [ue, editor, framework]
last_updated: 2026-05-09
---

# IToolkit / IToolkitHost / UEdMode

## 요약

🛠 EditorFramework 의 베이스. **인하우스 에셋 에디터의 골격**. IToolkit (에디터 인터페이스 베이스) + FAssetEditorToolkit (자산별 에디터, 자손) + IToolkitHost (탭/도킹 host) + UEdMode (Editor 모드 시스템 베이스 + 5.x Element System).

## 관계

- 부모: IToolkit / UEdMode
- 자손: FBlueprintEditor / FMaterialEditor / FStaticMeshEditor (에셋 종류별)
- 페어: FTabManager (도킹), [[entities/UToolMenus]] (메뉴), FUICommandList (단축키)

## 핵심 주장

- 인하우스 에셋 에디터 만들 때 FAssetEditorToolkit 자손 작성 → IAssetEditorInstance 등록.
- UEdMode = 5.x 모던 모드 시스템 — UPlacementSubsystem 통합 + Element System (per-element 선택 / 변환).
- IToolkitHost 는 Toolkit 의 호스팅 — 보통 Standalone Window 또는 LevelEditor 의 패널 이 implement.
- Editor 빌드만 — `#if WITH_EDITOR` 가드 의무.

## 열린 질문

- [ ] 5.x Element System 의 사용처 카탈로그
- [ ] FAssetEditorToolkit 의 표준 layout (탭 셋업)
