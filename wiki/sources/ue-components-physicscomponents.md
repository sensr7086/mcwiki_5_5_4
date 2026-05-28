---
type: source
title: "UE Components — PhysicsComponents sub-skill"
slug: ue-components-physicscomponents
source_path: raw/ue-wiki-llm/skills/Components/references/PhysicsComponents.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UPrimitiveComponent]]"
related_concepts:
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, components, physics]
---

# UE Components — PhysicsComponents sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/PhysicsComponents.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

물리 동적 컴포넌트 — UPhysicsConstraintComponent (관절) + UPhysicsHandleComponent (집어들기) + UPhysicsThrusterComponent (로켓 추진) + URadialForceComponent (폭발) + USpringArmComponent (카메라 spring) + UPhysicsSpringComponent + UPhysicalAnimationComponent + UClusterUnionComponent (5.x).

## 2. Key claims

- UPhysicsConstraintComponent: 두 PhysicsBody 간 관절 (6DoF — 6 자유도). UPhysicsConstraintTemplate 자산 페어.
- UPhysicsHandleComponent: 마우스로 물리 객체 끌기. GrabComponent / ReleaseComponent.
- UPhysicsThrusterComponent: 로컬 force 적용 — 로켓 / 추진기.
- URadialForceComponent: 반경 force — 폭발 / 충격파.
- USpringArmComponent: 카메라 spring (3rd person). SocketOffset / TargetArmLength + 충돌 회피.
- UPhysicalAnimationComponent: AnimSequence + Ragdoll 혼합 (피격 시 부분 ragdoll).
- UClusterUnionComponent (5.x): Geometry Collection (Chaos) 의 클러스터 결합 — 파괴 시스템.

## 3. Open questions

- [ ] PhysicsConstraint 의 6DoF Profile 결정
- [ ] PhysicalAnimation 의 Profile 셋업 패턴

## Cross-link

### Cycle 5o reverse-link 보강 (high confidence missing)

- [[sources/mc-soft-skeletalmesh-ragdoll]] (inbound=7, suggest_missing_cross_link high confidence)
