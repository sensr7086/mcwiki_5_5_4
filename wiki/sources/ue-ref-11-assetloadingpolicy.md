---
type: source
title: "UE refs — 11 AssetLoadingPolicy (SpawnActor 5대)"
slug: ue-ref-11-assetloadingpolicy
source_path: raw/ue-wiki-llm/references/11_AssetLoadingPolicy.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
related_entities:
  - "[[entities/AActor]]"
  - "[[entities/UGameInstance]]"
  - "[[entities/UStaticMesh]]"
  - "[[entities/USkeletalMesh]]"
  - "[[entities/UMaterial]]"
related_concepts:
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Soft-Reference-vs-Hard]]"
  - "[[concepts/Cooked-vs-Uncooked]]"
  - "[[concepts/Profiling-Scope-Rule]]"
  - "[[concepts/Component-Policies-6]]"
tags: [ue, reference, policy, asset, loading, soft-reference, primary-asset, streamable, spawnactor]
---

# UE refs — 11 AssetLoadingPolicy 🚨

> Source: [[raw/ue-wiki-llm/references/11_AssetLoadingPolicy.md]] · 487 lines / 23 KB · CLAUDE.md §0.1.3 의무 정책

## 1. Summary

🚨 어셋 로드 정책 — **Hard Reference 무분별 사용** 이 **SpawnActor 히칭 + Cooked Build 메모리 폭발 + 첫 프레임 stall 의 90% 원인**. 핵심 5: (a) SpawnActor 4단 히칭 메커니즘 (Class CDO / Subobject / 재귀 / PSO compile), (b) Soft vs Hard Reference 6종 비교 + 결정 트리, (c) 환경 모드별 분기 (Editor Pure = TryLoad / PIE / Cooked Game = Async), (d) UAssetManager Primary Asset + Bundle + FStreamableManager 패턴, (e) SpawnActorDeferred + FinishSpawning 4단 표준. 권위 concept = [[concepts/Asset-Loading-Policy]]. 깊이 자료 = [[sources/ue-ref-deep-assetloading]].

## 2. Key claims

### 2.1. SpawnActor 4단 히칭 메커니즘 🟢

- **[1] Class CDO 로드** — Cooked 첫 호출 시 동기 LoadObject. 자식 BP Class 면 부모 체인 모두. HDD 100ms+ / SSD 10~30ms.
- **[2] Subobject CDO 들** — `CreateDefaultSubobject` 의 Mesh/Material/Texture/SoundCue 등 Hard Reference 5~20개 동기 로드. **200ms+ 히칭**.
- **[3] Subobject 의 Subobject 재귀** — Mesh→Material→Texture / AnimBP→SkeletalMesh 5단계 깊이 가능. 대형 캐릭터 **1초+ 히칭**.
- **[4] 첫 Render PSO 컴파일** — Material/Shader PSO + Texture GPU 업로드 + GPU 메모리 할당. Spawn 직후 1~2 프레임. 50~500ms. → [[concepts/PSO-Precache]].
- **총합 Cooked 첫 SpawnActor**: 수백 ms ~ 수 초 (캐릭터/차량 복잡 Actor).

### 2.2. Editor PIE 함정 (대표 안티패턴)

- **Editor PIE** = Editor 시작 시 모든 어셋 메모리 상주 → 거의 0ms (캐시됨).
- **Cooked Build (Shipping)** = pak IO + Shader 캐시 → **200ms ~ 수 초**.
- 🚨 **함정**: Editor PIE 잘 동작 → Shipping 히칭 = 본 정책 위반의 가장 흔한 증상. QA 회피 위험.

### 2.3. Soft vs Hard Reference 6종 🟢

| 종류 | 선언 | Cooked 시 즉시 로드 | 표준 사용 |
| -- | -- | -- | -- |
| Hard Object | `TObjectPtr<T>` | ✅ Class 로드 시 동기 | 영구 보유 객체 |
| Hard Class | `TSubclassOf<T>` | ✅ | 즉시 SpawnActor |
| Soft Object | `TSoftObjectPtr<T>` | ❌ Path 만 | 가끔 사용 |
| Soft Class | `TSoftClassPtr<T>` | ❌ Path 만 | DLC / 가변 |
| `FSoftObjectPath` | FString | ❌ | Manager 패턴 |
| `FPrimaryAssetId` | Type::Name | ❌ | DataAsset 표준 |

### 2.4. Hard / Soft 결정 트리

- ALWAYS USED (Constructor → EndPlay) → **Hard** (TObjectPtr). 예: Pawn 의 CapsuleComponent / Mesh / CharacterMovement.
- 가끔 사용 + 미리 로드 가능 → **Soft + Primary Asset Pre-Load**. 예: 무기 Mesh, 특수 효과.
- 동적 / DLC / Custom → **Soft + 사용 직전 Async Load**. 예: NPC 종류, MOD.
- 일회용 (Spawn → Destroy) → **Hard** (단순). 예: 발사체 Bullet.

### 2.5. Editor 도구 예외

디테일 패널 / Custom Asset Editor / Factory / Importer — **Editor 순수 모드** 에서는 Soft Reference 라도 **동기 TryLoad 표준**. `IsPureEditorMode` 검증 + `WorldType` (GIsEditor 아닌) 분기. → [[sources/ue-editor-unrealed-factories]] §2.7.

### 2.6. SpawnActor 히칭 방지 4단 표준 🟢

1. **Class + Asset Pre-Load** (Match Start / Map 전환 / Equip 시점) — `UAssetManager::LoadPrimaryAssets` + `bLoadRecursive=true`.
2. **`SpawnActorDeferred`** — Init 전에 UPROPERTY 셋업 가능. BeginPlay 호출 지연.
3. **UPROPERTY 셋업** — `WeaponData` / `Damage` 등 BeginPlay 가 보게 됨.
4. **`FinishSpawning(Transform)`** — BeginPlay 호출 + 콜리전 활성.

→ synthesis [[synthesis/spawnactor-hitching-4-step-pattern]].

### 2.7. PreLoadAsset 5대 의무 🟢

1. **Constructor 안 어셋 로드 절대 금지** — `ConstructorHelpers::FObjectFinder` deprecated.
2. **BeginPlay 안 동기 `LoadObject` 금지** — Soft + Async 표준.
3. **Map 전환 시 사전 PreLoad** — LoadingScreen + `PreloadPrimaryAssets`.
4. **Bundle 단위 로드** — Equipped / Holstered 동적 변경.
5. **Handle 생명주기 관리** — Pin / Release 명시.

### 2.8. 함정 5종

- `ConstructorHelpers::FObjectFinder` (deprecated)
- `LoadObject` 게임 중 호출
- Soft Reference 후 `FStreamableHandle` 미보관 → GC
- Editor PIE 와 Cooked 동작 차이 무시
- 콜백 람다 `TWeakObjectPtr<this>` + IsValid 검사 누락

### 2.9. 환경 분기 표준

`#if WITH_EDITOR` 헬퍼 + `WorldType==EWorldType::Editor` 검증 — 같은 컴포넌트가 Editor 도구 (sync TryLoad) / PIE (sync OK) / Cooked Game (Async only) 양쪽 지원하도록.

### 2.10. UE 횡단 정책 정합

- 🚨 [[sources/ue-ref-07-profilingscopeRule]] 의무 — 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`
- 🚨 [[sources/ue-ref-10-componentpolicies]] 6대 (특히 §2 NewObject / §3 GC / §5 Tick)
- 🚨 [[sources/ue-ref-09-globaliteratorpolicy]] (디스크 검색 = AssetRegistry, TObjectIterator 금지)
- 🎯 [[sources/ue-ref-12-assetoptimizationpolicy]] §3 Actor Merging / §5 Niagara Pool (페어 정책)
- [[concepts/Cooked-vs-Uncooked]] 환경 분기
- [[sources/ue-coreuobject-objecthandles]] (TObjectPtr / TWeakObjectPtr / TSoftObjectPtr 깊이)
- [[sources/ue-coreuobject-package]] (LoadPackageAsync 베이스)
- [[sources/ue-coreuobject-cooking]] (Cooked 시 어셋 처리)

## 3. 적용 sub-skill (14종)

GameFramework 6 (Actor / Pawn / Character / Controller / GameMode / GameInstance) + Components 4 (Mesh / Material / SkeletalMesh / Subobject 일반) + Plugin 2 (Niagara / GAS) + UI 2 (UMG / Slate).

## 4. Cross-link

### 핵심 source

- [[sources/ue-ref-deep-assetloading]] — 정밀판 (12 함정 + 14 sub-skill 적용)
- [[sources/ue-coreuobject-objecthandles]] · [[sources/ue-coreuobject-package]] · [[sources/ue-coreuobject-cooking]]
- [[sources/ue-gameframework-actor]] §12 SpawnActor 히칭 방지 (본 정책 4단 적용)
- [[sources/ue-gameframework-gameinstance]] (Subsystem 안 Pre-Load 패턴)
- [[sources/ue-editor-assetregistry]] (IAssetRegistry / FAssetData / FARFilter)
- [[sources/ue-editor-unrealed-factories]] §2.7 (Editor sync TryLoad 예외)

### 자매 정책 hub

- [[sources/ue-ref-07-profilingscopeRule]] · [[sources/ue-ref-09-globaliteratorpolicy]] · [[sources/ue-ref-10-componentpolicies]] · [[sources/ue-ref-12-assetoptimizationpolicy]] · [[sources/ue-ref-04-overrideindex]] (BeginPlay Super FIRST)

### 권위 concept

- [[concepts/Asset-Loading-Policy]] (5 핵심 정책) · [[concepts/Soft-Reference-vs-Hard]] · [[concepts/Cooked-vs-Uncooked]] · [[concepts/PSO-Precache]] (PSO 페어)

### 관련 synthesis

- [[synthesis/spawnactor-hitching-4-step-pattern]] (본 정책 종합 적용)
- [[synthesis/cooked-first-frame-stability]] · [[synthesis/pso-precache-platform-matrix]]
- [[synthesis/mc-soft-asset-component-pattern]] (KMCProject 1차 적용)
- [[synthesis/mc-actor-spawn-subsystem-implementation]] (KMCProject 7 패턴 직교)


### Cycle 5o reverse-link 보강 (high confidence missing)

- [[sources/ue-editor-propertyeditor]] (inbound=3, suggest_missing_cross_link high confidence)
## 5. Open questions

- [ ] [[sources/ue-render-lumennanite]] 와 결합 — Nanite Streaming 자동 + 본 정책 PreLoad 통합?
- [ ] PSO Precache 5.x (§2.1 [4]) 와 본 정책의 *Pre-Load 시점* 일치 — Map 전환 시 PSO + Asset 묶음?
- [ ] DLC 시나리오 ([[synthesis/dlc-asset-migration-edge-cases]]) Primary Asset 동적 등록 — DefaultEngine.ini 외 런타임 등록?
- [ ] WorldPartition Streaming Volume ([[sources/ue-spatialpartition-worldpartitionruntime]]) + 본 정책 Manager 결합
