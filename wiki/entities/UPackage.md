---
type: entity
title: "UPackage"
aliases: [UPackage]
kind: model
sources:
  - "[[sources/ue-coreuobject-skill]]"
tags: [ue, runtime, asset]
last_updated: 2026-05-09
---

# UPackage

## 요약

`.uasset` / `.umap` 디스크 파일에 대응하는 [[entities/UObject]] 자손. 하나의 패키지 = 하나의 파일. 그 안에 1개+ UObject 가 들어감 (PackageOuter 체인). LoadObject / SavePackage 의 단위.

## 관계

- Outer chain 의 최상위가 UPackage
- 안의 객체들: [[entities/UStaticMesh]] / [[entities/UMaterial]] / [[entities/UTexture]] / Blueprint Class / Level (UWorld) / 등
- AssetRegistry 의 인덱싱 단위

## 핵심 주장

- `LoadObject<T>(nullptr, TEXT("/Game/UI/Logo.Logo"))` 의 경로 = `<MountRoot>/<Path>/<PackageName>.<ObjectName>`. [[sources/ue-coreuobject-skill]]
- 패키지 로드 = 디스크 → UPackage 메모리 → 안의 UObject 들 PostLoad. [[concepts/Object-Lifecycle]]
- Cooked 빌드: `.uasset` 들이 `.pak` / `.iostore` 로 합쳐짐. UPackage 자체는 메모리 표현만 동일.
- BulkData (Mesh RenderData / Texture pixel data 등) 은 UPackage 의 일부지만 lazy load — 필요 시점에 디스크에서 따로 로드. [[concepts/BulkData]]

## 열린 질문

- [ ] 5.x WorldPartition 의 streaming cell 과 UPackage 의 관계
- [ ] LinkerLoad / FArchive / FStructuredArchive 의 직렬화 흐름
