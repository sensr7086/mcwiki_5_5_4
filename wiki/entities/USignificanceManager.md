---
type: entity
title: "USignificanceManager / FManagedObjectInfo"
aliases: [USignificanceManager, FManagedObjectInfo, FOrderedBudget, EPostSignificanceType]
kind: model
sources:
  - "[[sources/ue-significance-skill]]"
tags: [ue, plugin, optimization, subsystem]
last_updated: 2026-05-09
---

# USignificanceManager

## 요약

Plugin (`SignificanceManager`) 의 글로벌 매니저. UObject (USubsystem 패턴 of UWorldSubsystem). 매 프레임 등록된 객체 N 개와 ViewPoints 비교 → 중요도 (0~1) 계산 → PostFunction 콜백 → Tick / LOD / Audio / Niagara 자동 토글.

## 관계

- 부모: [[entities/UObject]] (USubsystem 패턴)
- 협력: FManagedObjectInfo (관리되는 객체 1개), FOrderedBudget (LOD/Budget 분배 헬퍼)

## 핵심 주장

- 등록 패턴: `Manager->RegisterObject(Obj, Tag, SignificanceFunction, EPostSignificanceType, PostFunction)`. BeginPlay 에서 1 회.
- SignificanceFunction(Obj, ViewPoints) → float 0~1 — 거리/시야 기반 점수 반환.
- EPostSignificanceType 3종: None / Concurrent (parallel-safe) / Sequential.
- PostFunction(Obj, OldSignificance, NewSignificance, bFinal) — 점수 변경 후 후처리. Tick 토글 / LOD 강제 / Audio cull / Niagara cull.
- FOrderedBudget: 거리 순 정렬된 N 개 객체에 LOD 단계 분배 (예: 가까운 5개 = LOD 0, 다음 10개 = LOD 1, ...).
- 5 대 영역 통합 진입점 ([[concepts/Asset-Optimization-Policy]]): Bone LOD + Audio + Niagara 동시 토글.

## 열린 질문

- [ ] SignificanceFunction 의 매 프레임 비용 — 등록 객체 × ViewPoints 곱
- [ ] FOrderedBudget 의 5 단계 9 항목 매트릭스
