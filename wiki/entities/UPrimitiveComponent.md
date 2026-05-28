---
type: entity
title: "UPrimitiveComponent"
aliases: [UPrimitiveComponent, PrimitiveComponent]
kind: model
sources:
  - "[[sources/ue-components-skill]]"
tags: [ue, runtime, components, rendering]
last_updated: 2026-05-09
---

# UPrimitiveComponent

## 요약

[[entities/USceneComponent]] 자손. **콜리전 + 렌더 + 물리** 의 통합 베이스. UMeshComponent / UShapeComponent / UDecalComponent / UParticleSystemComponent / ULightComponent 등이 자손. Render Proxy (FPrimitiveSceneProxy) 보유 — 게임 스레드 ↔ 렌더 스레드 데이터 분리.

## 관계

- 부모: [[entities/USceneComponent]]
- 자손: [[entities/UStaticMeshComponent]] / [[entities/USkeletalMeshComponent]] / UShapeComponent / UDecalComponent / UParticleSystemComponent / [[entities/UNiagaraComponent]] / ULightComponent / UPostProcessComponent / ...
- 페어 자산: [[entities/UMaterial]] (Material 슬롯)

## 핵심 주장

- Overlap / Hit / Block 3 종 콜리전 응답. CollisionProfile (Pawn / WorldStatic 등) 로 일괄 설정. [[raw/ue-wiki-llm/references/08_OverlapHotspots.md]]
- Render Proxy (FPrimitiveSceneProxy) 는 렌더 스레드 표현 — 게임 스레드의 Component 와 분리. ENQUEUE_RENDER_COMMAND 로 데이터 전달 (포인터 공유 X). [[raw/ue-wiki-llm/docs/CLAUDE.md#§4]]
- Material override: SetMaterial(Index, Material) — UMaterialInstanceDynamic (MID) 으로 동적 파라미터 변경. [[entities/UMaterial]]
- Overlap 비용 핫스팟: bGenerateOverlapEvents + UpdateOverlaps 매 프레임 호출 = 다수 Actor 환경에서 큰 비용. → [[raw/ue-wiki-llm/references/08_OverlapHotspots.md]]
- [[concepts/Asset-Optimization-Policy]] 의 LOD 5 종 적용 대상 — StaticMesh ScreenSize / SkeletalMesh Bone LOD / HISM Instance LOD / HLOD / Nanite (5.x).

## 열린 질문

- [ ] FPrimitiveSceneProxy 의 BatchedElement / DrawDynamic 분기 — RDG 통합
- [ ] Hit 이벤트 vs Overlap 이벤트의 트리거 조건 매트릭스
