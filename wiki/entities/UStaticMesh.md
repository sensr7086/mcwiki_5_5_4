---
type: entity
title: "UStaticMesh"
aliases: [UStaticMesh, StaticMesh]
kind: model
sources:
  - "[[sources/ue-assetclasses-skill]]"
tags: [ue, asset, mesh]
last_updated: 2026-05-09
---

# UStaticMesh

## 요약

[[entities/UObject]] 자손 (자산 클래스). 정적 mesh 자산 (`.uasset`) — 2,543 lines. RenderData (vertex / index buffer) + LOD chain (ScreenSize threshold) + Material slots + Lightmap UV + Collision (BodySetup) + 5.x Nanite. [[entities/UStaticMeshComponent]] 가 호스트.

## 관계

- 부모: [[entities/UObject]]
- 페어 호스트: [[entities/UStaticMeshComponent]] / UInstancedStaticMeshComponent / USplineMeshComponent
- 협력 자산: [[entities/UMaterial]] (다중 슬롯), UPhysicalMaterial (BodySetup), [[entities/UTexture]] (간접)

## 핵심 주장

- LOD: 다단 LOD chain. 각 LOD 의 ScreenSize threshold 로 자동 결정. Component 의 ForcedLodModel 로 강제 가능.
- 5.x Nanite: 활성 시 LOD chain 대신 virtualized geometry 사용. Mesh 자산에 `bEnableNanite` 플래그 + Build 시 Nanite 데이터 생성.
- Material slots: 인덱스별 default material. Component 측 SetMaterial 으로 override.
- BodySetup: 콜리전 표현 (Convex Hull / Trimesh / Simple). UPhysicsAsset 와 별개.
- BulkData: vertex/index buffer 가 [[concepts/BulkData]] — lazy load. WITH_EDITORONLY_DATA 가드. [[concepts/Cooked-vs-Uncooked]]
- DerivedDataCache (DDC): build 결과 캐싱 — Editor build 가속.

## 열린 질문

- [ ] Nanite 활성 vs Legacy LOD 의 결정 트리 (모바일/저사양 platform 고려)
- [ ] HISM 의 PerInstance 데이터 vs 일반 StaticMesh 차이
