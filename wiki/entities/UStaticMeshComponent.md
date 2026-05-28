---
type: entity
title: "UStaticMeshComponent"
aliases: [UStaticMeshComponent, StaticMeshComponent]
kind: model
sources:
  - "[[sources/ue-components-skill]]"
  - "[[sources/ue-assetclasses-skill]]"
tags: [ue, runtime, components, mesh]
last_updated: 2026-05-09
---

# UStaticMeshComponent

## 요약

[[entities/UPrimitiveComponent]] 자손. **정적 mesh 의 호스트** — [[entities/UStaticMesh]] 자산 참조 + Material 슬롯 다중 + LOD 자동 (ScreenSize). 가장 흔한 렌더 컴포넌트. 5.x Nanite 지원 (Mesh 자체에 활성화 시).

## 관계

- 부모: [[entities/UPrimitiveComponent]]
- 변형: UInstancedStaticMeshComponent (HISM 자손, 다중 인스턴스 batched), USplineMeshComponent (Spline 따라 변형)
- 페어 자산: [[entities/UStaticMesh]] (필수) + [[entities/UMaterial]] (다중 슬롯) + UPhysicalMaterial

## 핵심 주장

- StaticMesh 슬롯: UPROPERTY(EditAnywhere) `TObjectPtr<UStaticMesh> StaticMesh`. Constructor 에서 `ConstructorHelpers::FObjectFinder<UStaticMesh>` 금지 ([[concepts/Asset-Loading-Policy]] 위반). [[raw/ue-wiki-llm/references/11_AssetLoadingPolicy.md]]
- Material override: 인덱스별로 `SetMaterial(0, Material)`. Mesh 자체의 Material slot 은 그대로, Component 가 override.
- LOD: Mesh 자산의 `LODGroup` + ScreenSize threshold 로 자동. Component 의 `ForcedLodModel` 로 강제 가능 (디버깅).
- HISM (`UHierarchicalInstancedStaticMeshComponent`) 는 다수 인스턴스 (풀밭/돌 등) 를 1 draw call 로 batched. [[concepts/Asset-Optimization-Policy]]
- 5.x Nanite: Mesh 자체에 활성화 → ScreenSize LOD 대신 Nanite virtualized geometry. Component 측 변경 없음.

## 열린 질문

- [ ] Nanite 활성 vs Legacy LOD 의 메모리/GPU 비용 비교
- [ ] HISM vs ISM (Instanced) vs HLOD 의 결정 기준
