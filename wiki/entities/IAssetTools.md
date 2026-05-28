---
type: entity
title: "IAssetTools / IAssetTypeActions / IAssetRegistry"
aliases: [IAssetTools, IAssetTypeActions, FAssetTypeActions_Base, IAssetRegistry]
kind: model
sources:
  - "[[sources/ue-editor-skill]]"
tags: [ue, editor, asset]
last_updated: 2026-05-09
---

# IAssetTools / IAssetRegistry

## 요약

🛠 AssetTools (Developer 모듈) + AssetRegistry (Runtime 모듈, Editor 만 풀 동작). IAssetTools 가 에셋 종류별 동작 (생성 / 복제 / 변환 / 삭제) 정의. IAssetRegistry 가 모든 에셋의 메타 캐시 (`FAssetData` / `FARFilter`).

## 관계

- 등록 진입점 (AssetTools): IAssetTools::RegisterAssetTypeActions
- 베이스: FAssetTypeActions_Base 자손 (사용자 정의)
- AssetRegistry 는 Runtime 모듈이지만 Cooked 빌드는 메타만 (간소화)

## 핵심 주장

- IAssetTypeActions 자손: GetName / GetTypeColor / GetClass / GetCategories (EAssetTypeCategories) / OpenAssetEditor.
- IAssetRegistry::GetChecked() → FAssetData / FARFilter 로 검색. OnAssetAdded / OnAssetRemoved / OnFilesLoaded delegate.
- AssetRegistry 의 IAssetDependencyGatherer — 자산 간 의존 그래프 수집.
- Cooked 빌드: IAssetRegistry 의 일부 동작만 (간소화된 데이터). Editor 가 풀 동작.
- 자산 자동 검색 패턴: `TActorIterator` 회피의 표준 (asset 측면) — `IAssetRegistry::GetAssetsByClass`.

## 열린 질문

- [ ] AssetRegistry 의 Cooked 빌드 동작 차이
- [ ] FARFilter 의 PackagePaths / ClassNames 매트릭스
