---
type: source
title: "UE Components — ShapeComponents sub-skill"
slug: ue-components-shapecomponents
source_path: raw/ue-wiki-llm/skills/Components/references/ShapeComponents.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UPrimitiveComponent]]"
related_concepts:
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, components, collision]
---

# UE Components — ShapeComponents sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/ShapeComponents.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

콜리전 전용 단순 모양 — UBoxComponent / USphereComponent / UCapsuleComponent / UTriggerVolume. [[entities/UPrimitiveComponent]] 자손이지만 *시각 없음 (Editor 시각화만)*. Trigger / Detection / Pawn Capsule 표준 사용.

## 2. Key claims

- UBoxComponent: Box-shaped collision. SetBoxExtent(FVector). Trigger zone.
- USphereComponent: Sphere collision. SetSphereRadius. Detection radius (적 인지 등).
- UCapsuleComponent: Capsule (원기둥 + 양 끝 반구). [[entities/ACharacter]] 의 RootComponent 표준 — Pawn 의 충돌 + 발 위치 결정.
- UTriggerVolume = UBoxComponent 의 Volume 사용 — Map 에 배치된 trigger.
- Editor 시각화: Wireframe (게임 빌드 안 보임). bDrawOnlyIfSelected.
- 6 대 정책 ([[concepts/Component-Policies-6]]) 자동 적용 — Mobility (대부분 Movable, 트리거 zone 은 Static).

## 3. Open questions

- [ ] Capsule vs Box 결정 트리 (Pawn / Trigger / Detection 별)
