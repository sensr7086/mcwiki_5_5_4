---
type: source
title: "11_AssetLoadingPolicy — Deep Reference (FStreamableManager + UAssetManager + 함정 12)"
slug: ue-ref-deep-assetloading
source_path: raw/ue-wiki-llm/references/deep/AssetLoadingDeep.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-15
related_entities: []
related_concepts:
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Soft-Reference-vs-Hard]]"
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, reference, policy, enriched-card]
citation_disclosure: "🟢 9 / 🟡 3 / 🔴 0 · raw verified (594L) · Cycle 5f #1 enrich"
---

# 11_AssetLoadingPolicy — Deep Reference

> Source: [[raw/ue-wiki-llm/references/deep/AssetLoadingDeep.md]] (594L)
> 부모 정책: 🚨 [[sources/ue-ref-11-assetloadingpolicy]] · [[concepts/Asset-Loading-Policy]]
> Cycle 5f #1 — stub 카드 → enrich 카드 (raw 본문 §1~§5 카탈로그 + 3-tier marker)

## 1. Summary

🟢 FStreamableManager 비동기 로드 표준 + UAssetManager Primary Asset/Bundle + PreLoad 5대 정책 + 함정 12종 + sub-skill 적용 매트릭스 14종.

## 2. 핵심 §/매트릭스 카탈로그 (raw §1~§5)

### 2.1 FStreamableManager — 비동기 로드 (raw §1) 🟢

- 🟢 진입점 `UAssetManager::GetStreamableManager()` (`AssetManager.h:105`)
- 🟢 `RequestAsyncLoad(Path, Delegate, Priority, bManageActiveHandle)` (`StreamableManager.h:730`)
- 🟢 `FStreamableHandle` 8 메소드 (HasLoadCompleted / IsLoadingInProgress / WasCanceled / BindCompleteDelegate / BindCancelDelegate / CancelHandle / ReleaseHandle / GetRequestedAssets)
- 🟢 표준 패턴 2종: 멤버 Handle Pin / `bManageActiveHandle=true`
- 🚨 `RequestSyncLoad` = Editor / 로딩 화면만, 게임 중 금지

### 2.2 UAssetManager — Primary Asset + Bundle (raw §2) 🟢

- 🟢 `FPrimaryAssetId(Type, Name)` + `UPrimaryDataAsset::GetPrimaryAssetId()` override
- 🟢 `LoadPrimaryAsset(Id, Bundles, Delegate, Priority)` (`AssetManager.h:308`)
- 🟢 `meta=(AssetBundles="Visual")` UPROPERTY 메타 — Bundle 그룹
- 🟢 `ChangeBundleStateForPrimaryAssets` 동적 Bundle 변경 (`AssetManager.h:365`)
- 🟢 `PreloadPrimaryAssets` 메모리 상주 (`AssetManager.h:492`)
- 🟢 DefaultEngine.ini `PrimaryAssetTypesToScan` — 자동 스캔 등록
- 🟢 GameInstance::Init 안 `ScanPathForPrimaryAssets` + 글로벌 PreLoad

### 2.3 PreLoad 5대 정책 (raw §3) 🟢

| # | 정책 | tier |
|---|------|------|
| 1 | Constructor 안 `ConstructorHelpers::FObjectFinder` 금지 — 5.x deprecated 추세 | 🟢 |
| 2 | BeginPlay 안 `LoadObject<T>` / `StaticLoadObject` 금지 (동기 = 히칭) | 🟢 |
| 3 | Map 전환 시 LoadingScreen 표시 + `PreloadPrimaryAssets` 사전 | 🟢 |
| 4 | Bundle 단위 로드 (Equipped / Holstered 등) | 🟢 |
| 5 | Handle Pin/Release 명시 — `EndPlay` 안 `LoadHandle.Reset()` | 🟢 |

### 2.4 함정 12종 (raw §4) 🟢/🟡

| # | 함정 | tier |
|---|------|------|
| 1 | `ConstructorHelpers::FObjectFinder` Constructor 로드 | 🟢 |
| 2 | `LoadObject<T>()` 게임 중 호출 | 🟢 |
| 3 | Soft Reference 후 Handle 보관 안 함 | 🟢 |
| 4 | Hard Reference Database — 메모리 폭발 | 🟢 |
| 5 | Editor PIE OK → Cooked 히칭 (Editor 캐시) | 🟢 |
| 6 | Primary Asset Type 스캔 안 등록 | 🟢 |
| 7 | `LoadBundles {}` = Default Bundle, 명시 누락 | 🟡 |
| 8 | `bLoadRecursive=false` — 자식 어셋 누락 | 🟢 |
| 9 | RequestAsyncLoad 람다 안 `this` raw 캡처 | 🟢 |
| 10 | Soft Reference 변경 후 SaveGame 안 함 | 🟡 |
| 11 | 🚨 `RequestSyncLoad` 게임 중 사용 | 🟢 |
| 12 | 🚨 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` 누락 | 🟢 (페어: [[sources/ue-ref-07-profilingscopeRule]]) |

### 2.5 sub-skill 적용 매트릭스 14종 (raw §5) 🟡

GameFramework (Actor 4단 SpawnActor + PawnCharacter Modular + Controller Hard + GameMode 사전 PreLoad + GameInstance 글로벌 + World LoadStreamLevel) + Components (Mesh/Movement/Audio/Particle 4종) + Niagara + GAS + UMG + Slate.

> 🟡 sub-skill 페어 14종 카탈로그 — 본 카드는 raw 참조용, 자세한 적용은 각 sub-skill 본문 참조.

## 3. Cross-link

- 부모 정책 (필수): 🚨 [[sources/ue-ref-11-assetloadingpolicy]] · [[concepts/Asset-Loading-Policy]] · [[concepts/Soft-Reference-vs-Hard]]
- 페어 정책: [[sources/ue-ref-12-assetoptimizationpolicy]] · [[sources/ue-ref-deep-assetoptimization]]
- 프로파일링: 🚨 [[sources/ue-ref-07-profilingscopeRule]] (함정 12)
- sub-skill: [[sources/ue-gameframework-actor]] (SpawnActor 4단) · [[synthesis/spawnactor-hitching-4-step-pattern]]

## 4. 신뢰도 + 변경 이력

| 항목 | tier | 출처 |
|------|------|------|
| FStreamableManager API 8 | 🟢 verified | `StreamableManager.h:197-349` |
| UAssetManager Primary Asset API | 🟢 verified | `AssetManager.h:105,283,308,365,492` |
| PreLoad 5대 정책 | 🟢 verified | raw §3 + KMCProject 실측 |
| 함정 12 (10 🟢 + 2 🟡) | 🟢/🟡 | raw §4 |
| sub-skill 14 매트릭스 | 🟡 carry-over | raw §5 (개별 검증 후속) |

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | 11_AssetLoadingPolicy 분리 (raw 9 KB) |
| 2026-05-15 | Cycle 5f #1 — stub 카드 → enrich 카드 (3-tier marker + raw §1~§5 카탈로그 + Cross-link 5건) |
