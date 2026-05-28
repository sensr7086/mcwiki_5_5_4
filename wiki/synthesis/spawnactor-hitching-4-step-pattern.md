---
type: synthesis
title: "SpawnActor 히칭 회피 4단 표준 패턴 — Class load + CDO + Asset members + Constructor"
slug: spawnactor-hitching-4-step-pattern
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/ue-ref-11-assetloadingpolicy]]"
  - "[[sources/ue-gameframework-actor]]"
  - "[[sources/ue-coreuobject-uobject]]"
  - "[[sources/ue-coreuobject-package]]"
  - "[[sources/ue-assetclasses-mesh]]"
  - "[[sources/ue-components-skill]]"
  - "[[sources/mc-soft-skeletalmesh-ragdoll]]"
entities:
  - "[[entities/UClass]]"
  - "[[entities/UBlueprintGeneratedClass]]"
  - "[[entities/UPackage]]"
  - "[[entities/AActor]]"
  - "[[entities/UObject]]"
  - "[[entities/UGameInstance]]"
concepts:
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Soft-Reference-vs-Hard]]"
  - "[[concepts/Cooked-vs-Uncooked]]"
  - "[[concepts/Object-Lifecycle]]"
  - "[[concepts/Asset-Lifecycle]]"
status: living
tags: [synthesis, spawnactor, hitching, async-load, cooked]
---

# SpawnActor 히칭 회피 4단 표준 패턴

## 1. Thesis

`World->SpawnActor<T>(Class, ...)` 의 첫 호출이 Cooked Build 에서 **수십~수백 ms 히칭** 을 일으키는 4 단계 원인 — **[1] Class load (UClass / UBlueprintGeneratedClass) → [2] CDO load (Class Default Object) → [3] BP 안 자산 멤버 (Mesh/Material/Niagara/Audio) hard reference 동기 로드 → [4] Constructor 안 추가 자산 로드 (`ConstructorHelpers::FObjectFinder`)** ([[concepts/Asset-Loading-Policy]] §3). 본 synthesis 는 각 단계를 **언제 / 무엇이 / 왜 비싼가** 로 풀고, 단계별 회피 패턴을 제시.

## 2. 4 단 매트릭스

| 단계 | 무엇이 로드되는가 | 비용 | 회피 |
| -- | -- | -- | -- |
| **[1] Class load** | `UClass` (C++) 는 모듈 로드 시 끝. `UBlueprintGeneratedClass` (BP 자손) 는 Asset 처럼 .uasset 디스크 read | BP Class = 5~50 KB IO + serialize | `TSoftClassPtr<>` + `FStreamableManager` 로 미리 로드 |
| **[2] CDO load** | `Class->GetDefaultObject()` 에 접근하면 Class 의 모든 UPROPERTY 디폴트 + Subobject (`CreateDefaultSubobject`) 들이 instantiated | Class 당 1 회 (캐시) — 첫 SpawnActor 가 부담 | 게임 시작 시 `LoadObject<UClass>(...)` 또는 PreLoad 로 미리 |
| **[3] Asset members** | CDO 안 `TObjectPtr<UStaticMesh> Mesh;` 같은 hard 멤버 = CDO 로드와 함께 메시 / 머티리얼 / 텍스처 / Niagara 가 chain 로드 | Mesh 5~100 MB + Texture 다수 = 수백 ms IO | 멤버를 `TSoftObjectPtr<>` 로 + 컴포넌트 BeginPlay 비동기 로드 |
| **[4] Constructor** | `ConstructorHelpers::FObjectFinder<UStaticMesh>(...)` = CDO 생성 시점마다 동기 로드 | [3] 와 같은 비용 — 모든 Spawn 마다 (CDO 만이 아니라 인스턴스마다) | Constructor 안 자산 로드 *절대 금지*. UPROPERTY EditAnywhere + BP 디테일 패널 또는 Soft + BeginPlay |

원본 표 — [[sources/ue-ref-11-assetloadingpolicy]] §3 + [[sources/ue-assetclasses-mesh]] §7 함정 #1 (`ConstructorHelpers::FObjectFinder` 안티패턴).

## 3. 회피 결정 트리

```
이 자산 / 클래스가 SpawnActor 첫 프레임에 필요한가?
├── 항상 (Player Character / 핵심 적 / 메인 무기)
│   └── 게임 시작 시 PreLoad ([[concepts/Asset-Loading-Policy]] §2 단계 4)
│       UAssetManager::PreloadPrimaryAssets(bLoadRecursive=true)
│       → SpawnActor 시점엔 이미 메모리 상주 (Hard 만큼 빠름, 첫 로드만 분리)
├── 가끔 (특정 적 / 컷씬 무기 / 일회성 NPC)
│   └── Soft + BeginPlay 비동기 로드 ([[sources/mc-soft-skeletalmesh-ragdoll]] 의 컴포넌트 패턴)
│       → SpawnActor 자체는 빠름 (Class+CDO 만), 메시는 fade-in
├── 매우 자주 (총알 / 파편)
│   └── Object Pool — 첫 N개 미리 Spawn + Reuse
└── 한 번도 안 쓰일 수도 있음 (조건부 보스 / DLC)
    └── Soft + 트리거 시점 비동기 로드 + Bundle 단위 묶음
```

## 4. 시나리오 — Cooked Build 검증

**검증 절차** ([[sources/ue-ref-11-assetloadingpolicy]] §11):

1. Development 빌드 + `stat unit` / `stat game` 활성
2. 의심 액터 `World->SpawnActor` 호출 직전 / 직후 ms 측정
3. 50ms 넘으면 `stat startfile` → `stat stopfile` 사이에 SpawnActor 실행 → Frontend 로 분석
4. `LoadObject` / `BulkSerialize` / `PostLoad` / `CreateExport` 가 stack 에 보이면 [3] 또는 [4] 단계 문제

**재현 가능한 측정**:

```cpp
// 디버그 매크로
#define MC_MEASURE_SPAWN(WorldPtr, ActorClass) \
    do { \
        const double Start = FPlatformTime::Seconds(); \
        AActor* Spawned = (WorldPtr)->SpawnActor<AActor>((ActorClass)); \
        const double Ms = (FPlatformTime::Seconds() - Start) * 1000.0; \
        UE_LOG(LogMCAsset, Warning, TEXT("SpawnActor %s = %.2f ms"), *GetNameSafe(Spawned), Ms); \
    } while (0)
```

## 5. 함정 / 열린 질문

- [ ] **Constructor 안 `LoadObject<>`** — [4] 단계 그 자체. 모든 Spawn 시 동기 IO. *절대 금지* ([[sources/ue-assetclasses-mesh]] §7 #1)
- [ ] **`ConstructorHelpers::FObjectFinder<>`** — Editor 에서만 의도된 패턴. 게임 모듈에서 쓰면 매 Spawn 마다 동기 로드. UPROPERTY + BP 디테일 패널이 정답.
- [ ] **하위 컴포넌트의 hard 자산** — Actor 자체는 Soft 로 잘 짰는데 그 안 컴포넌트가 hard `TObjectPtr<UStaticMesh>` 면 [3] 단계 그대로 발생. 컴포넌트도 Soft 화 ([[sources/mc-soft-skeletalmesh-ragdoll]])
- [ ] **BP CDO 안 큰 DataTable** — 종종 망각. `TObjectPtr<UDataTable>` hard 멤버는 [3] 의 *조용한 큰 비용* ([[sources/ue-assetclasses-data]])
- [ ] **DefaultPawnClass / GameMode hard 참조** — `AGameMode::DefaultPawnClass` 가 `TSubclassOf<>` (hard Class 참조). [1] 단계의 큰 부분. `TSoftClassPtr<>` 로 전환 후 Match Start 비동기 로드 가능 ([[sources/ue-gameframework-gamemode]] — 열린)
- [ ] **DLC / Patch 의 새 자산** — 같은 Class 가 새 자산 path 로 빌드되어도 PreLoad 가 안 따라옴. Bundle 단위 갱신 (열린)

## 6. 관련

### Sources

[[sources/ue-ref-11-assetloadingpolicy]] · [[sources/ue-gameframework-actor]] · [[sources/ue-coreuobject-uobject]] · [[sources/ue-coreuobject-package]] · [[sources/ue-assetclasses-mesh]] · [[sources/ue-components-skill]] · [[sources/mc-soft-skeletalmesh-ragdoll]]

### Entities

[[entities/UClass]] · [[entities/UBlueprintGeneratedClass]] · [[entities/UPackage]] · [[entities/AActor]] · [[entities/UObject]] · [[entities/UGameInstance]]

### Concepts

[[concepts/Asset-Loading-Policy]] · [[concepts/Soft-Reference-vs-Hard]] · [[concepts/Cooked-vs-Uncooked]] · [[concepts/Object-Lifecycle]] · [[concepts/Asset-Lifecycle]]

### Related synthesis

[[synthesis/mc-soft-asset-component-pattern]] (4단 회피의 *컴포넌트* 표준 골격) · [[synthesis/mc-character-hit-reaction-pipeline]] (적용 사례 — SkeletalMesh 캐릭터) · [[synthesis/component-vs-actor-lifecycle-table]] (Constructor / BeginPlay 시점)

### Cycle 5o reverse-link 보강 (high confidence missing)

- [[synthesis/cooked-first-frame-stability]] (inbound=3, suggest_missing_cross_link high confidence)
