---
type: source
title: "UE Components — MovementComponents sub-skill"
slug: ue-components-movementcomponents
source_path: raw/ue-wiki-llm/skills/Components/references/MovementComponents.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
related_entities:
  - "[[entities/UCharacterMovementComponent]]"
related_concepts:
  - "[[concepts/Replication]]"
  - "[[concepts/RootMotion]]"
tags: [ue, runtime, components, movement]
---

# UE Components — MovementComponents sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/MovementComponents.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

이동 처리 컴포넌트 — [[entities/UCharacterMovementComponent]] (CMC, 5 종 모드) + UFloatingPawnMovement + UProjectileMovementComponent + URotatingMovementComponent + UInterpToMovementComponent. [[concepts/Replication]] (Server Authoritative + Client Prediction) + [[concepts/RootMotion]].

## 2. Deep references

- [[sources/ue-components-charactermovementdeep]] — CMC 깊이 자료 (Floor / Step Up / Movement Base / Jump 6 / RVO / Force 9)

## 3. Key claims

- UCharacterMovementComponent (CMC): 5 모드 (Walking / NavWalking / Falling / Swimming / Flying / Custom). [[entities/ACharacter]] 페어. FSavedMove Client Prediction.
- UFloatingPawnMovement: 단순 Pawn — AddMovementInput / 마찰 없음 / 중력 없음.
- UProjectileMovementComponent: 발사체 — InitialSpeed / MaxSpeed / Velocity / bShouldBounce / ProjectileGravityScale.
- URotatingMovementComponent: 자동 회전 — RotationRate.
- UInterpToMovementComponent: 정해진 경로 보간 — PathPoints + Duration.
- 6 대 정책 자동. Replication 표준.
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 pass-minor-numeric** (자동 분석)

raw 5.5.4 vs 5.7.4 diff: 시그니처 0 / 추가 0 / 제거 0 / 수치 2 — 표면 변경만, 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/Components/references/MovementComponents.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/Components/references/MovementComponents.md`
