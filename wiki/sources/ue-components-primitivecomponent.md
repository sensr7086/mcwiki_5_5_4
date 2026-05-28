---
type: source
title: "UE Components — UPrimitiveComponent sub-skill"
slug: ue-components-primitivecomponent
source_path: raw/ue-wiki-llm/skills/Components/references/PrimitiveComponent.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UPrimitiveComponent]]"
related_concepts:
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, components, rendering]
---

# UE Components — UPrimitiveComponent sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/PrimitiveComponent.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

[[entities/UPrimitiveComponent]] 렌더 + 콜리전 통합 베이스 — SetVisibility / SetCollisionEnabled / Overlap 이벤트 / Custom Depth / Render Proxy.

## 2. Key claims

- SetVisibility(bVisible, bPropagateToChildren) — Render 시각 토글.
- SetCollisionEnabled(ECollisionEnabled): NoCollision / QueryOnly / PhysicsOnly / QueryAndPhysics.
- CollisionProfile (Pawn / WorldStatic 등) + Channel (ECC_*) 매트릭스.
- Overlap 이벤트: bGenerateOverlapEvents + UpdateOverlaps. OnComponentBeginOverlap / OnComponentEndOverlap delegate. Hot spot — 다수 Actor 환경에서 큰 비용 ([[raw/ue-wiki-llm/references/08_OverlapHotspots.md]]).
- Custom Depth: SetRenderCustomDepth(true) — 외곽선 / 후처리 효과 표준.
- Render Proxy (FPrimitiveSceneProxy): 렌더 스레드 표현 분리. ENQUEUE_RENDER_COMMAND 로 데이터 전달 (포인터 공유 X).
- Material: SetMaterial(Index, Material) — UMaterialInstanceDynamic (MID) 으로 동적 파라미터.

## 3. Open questions

- [ ] FPrimitiveSceneProxy 의 BatchedElement / DrawDynamic 분기
