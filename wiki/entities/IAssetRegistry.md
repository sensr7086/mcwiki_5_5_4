---
type: entity
title: "IAssetRegistry"
aliases: [IAssetRegistry, FAssetData, FARFilter, AssetRegistry]
kind: model
sources:
  - "[[sources/ue-editor-skill]]"
tags: [ue, runtime, asset, editor]
last_updated: 2026-05-09
---

# IAssetRegistry

## 요약

AssetRegistry Runtime 모듈의 핵심. **모든 에셋의 메타 캐시** — `IAssetRegistry::GetChecked()` 싱글톤. FAssetData (자산 메타) + FARFilter (검색 조건) + OnAssetAdded / OnFilesLoaded delegate. Editor 가 풀 동작, Cooked 는 메타만 (간소화).

## 관계

- 자체 모듈: AssetRegistry (Runtime, Editor 빌드 시 풀)
- 협력: [[entities/IAssetTools]] (Editor 측 자산 동작)

## 핵심 주장

- 싱글톤 접근: `IAssetRegistry::GetChecked()` — Module 의 Get() 패턴.
- FAssetData = 자산의 메타 (PackageName / AssetName / Class / Tags / SoftObjectPath). 풀 자산 로드 없이 path 만.
- FARFilter = 검색 조건 (PackagePaths / ClassNames / TagsAndValues / bRecursivePaths).
- `GetAssetsByClass(UMyAsset::StaticClass(), AssetData)` — 특정 클래스의 모든 자산.
- OnAssetAdded / OnAssetRemoved / OnFilesLoaded — 비동기 자산 등록 알림. Editor 시작 시 OnFilesLoaded 후에야 풀 검색 가능.
- IAssetDependencyGatherer — 자산 간 의존 그래프 수집.
- Cooked 빌드: 일부 데이터만 (간소화). Editor 가 풀 동작.

## 열린 질문

- [ ] AssetRegistry 의 Cooked 빌드 동작 차이
- [ ] FARFilter 의 PackagePaths / ClassNames 매트릭스
