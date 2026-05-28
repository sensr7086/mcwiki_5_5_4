---
type: entity
title: "UEdMode"
aliases: [UEdMode, EdMode, UPlacementSubsystem]
kind: model
sources:
  - "[[sources/ue-editor-skill]]"
tags: [ue, editor, framework]
last_updated: 2026-05-09
---

# UEdMode (5.x 모던 모드 시스템)

## 요약

🛠 5.x 의 Editor 모드 시스템 베이스. Legacy FEdMode 의 후속. UPlacementSubsystem 통합 + Element System (per-element 선택 / 변환). LevelEditor 의 모드 (Foliage / Landscape / Mesh Painting / Brush 등) 의 베이스.

## 관계

- 부모: UEditorInteractiveToolsContext 자손
- 자손: 사용자 정의 EdMode (FoliageEditMode / LandscapeEditMode 등)
- 5.x 통합: UPlacementSubsystem (UEditorSubsystem 자손)

## 핵심 주장

- Legacy FEdMode (UE 4.x) 는 deprecated — 신규 모드는 UEdMode 의무.
- Editor 빌드만 — `#if WITH_EDITOR` 가드.
- Element System: 5.x 의 통합 선택 시스템 — Actor / Component / Object 단위로 일관 처리.
- Tools Context: UInteractiveToolsContext + UInteractiveTool 의 InteractiveTools framework 통합.

## 열린 질문

- [ ] FEdMode → UEdMode 마이그레이션 표준 절차
- [ ] InteractiveTool 의 5.x 표준 패턴
