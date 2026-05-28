---
name: gameframework-main
description: Tier 1 GameFramework 메인 — Actor (라이프사이클 11단계) + PawnCharacter (Pawn + Character 합본 + 최적화 10종) + Controller (PlayerController + AIController) + GameMode (GameModeBase + Match State + GameStateBase + PlayerState) + GameInstance + World 6개 sub-skill. 모든 Actor 게임 흐름 베이스. SpawnActor 히칭 방지 4단 표준 패턴.
---

# GameFramework — Actor / Pawn / Character / Controller / GameMode / GameInstance / World

> **위치**: `Engine/Source/Runtime/Engine/Classes/GameFramework/` + `Engine/Classes/Engine/` (UWorld·UGameInstance·ULevel)
> **요지**: 게임 흐름의 베이스 — `AActor` → `APawn` → `ACharacter` 의 **컴포넌트 호스트**, `AController` → `APlayerController/AAIController` 의 **입력·소유 흐름**, `AGameMode` 의 **권한 흐름**, `UGameInstance` 의 **세션 영속**, `UWorld`/`ULevel` 의 **세계 컨테이너**.
> **카테고리**: `[GameFramework]` (`[Components]` 의 호스트 카테고리 — Components 는 Actor 의 부속, GameFramework 는 Actor 자체).

---

## 🚨 공통 정책 (모든 GameFramework sub-skill 본문 시작부 의무 블록)

> 모든 GameFramework 클래스 작성 시 [`10_ComponentPolicies.md`](../../references/10_ComponentPolicies.md) 의 **6대 정책** 중 Actor 에 적용되는 항목 + Actor 특화 항목.

| # | 정책 | Actor 특화 |
|---|------|-----------|
| 1 | **Mobility (SceneComponent 자손)** | RootComponent 는 SceneComponent — 생성자에서 `Static`/`Stationary`/`Movable` 명시. 런타임 `SetMobility` 금지. Movable 외 Actor 는 Tick 비활성 권장. |
| 2 | **NewObject + DuplicateObject** | Actor = `World->SpawnActor<AMyActor>(Class, Transform)` (Constructor=`CreateDefaultSubobject` Component / 런타임=`SpawnActor`). Outer = `UWorld`. **`NewObject<AActor>` 직접 호출 금지** (Spawn 라이프사이클 우회). |
| 3 | **GC 방어** | UPROPERTY() + TObjectPtr<AActor> (Actor 멤버) / TWeakObjectPtr<AActor> (캐싱·Lifetime 분리) / TStrongObjectPtr (비-UCLASS — 드물다). Spawn 한 Actor 는 World 가 강참조하므로 OwnedActors 자동 GC 보호. |
| 4 | **GetOwner / GetController / GetPawn 캐싱** | `BeginPlay` 에서 1회 캐싱 → TWeakObjectPtr 보관 + 매 Tick/콜백 재조회 금지. PossessedBy / OnPossess 콜백에서만 Controller 갱신. |
| 5 | **PrimaryActorTick** | 기본 `bCanEverTick = false` + 필요 시 `TickGroup` (TG_PrePhysics 표준) + `TickInterval` (0.05~1s) 우선 + 매 프레임 Tick = 마지막 수단. **Actor Tick 은 Component 들의 Tick 의 컨테이너** — 베이스 Actor Tick 안에 매 프레임 로직 작성 금지. |
| 6 | **CDO + OnConstruction** | `GetMutableDefault<AActor>()->Set*()` 으로 CDO 변경 금지 + `PostInitProperties` 안 `HasAnyFlags(RF_ClassDefaultObject)` 검사 + `CreateDefaultSubobject` 는 **Constructor 안만** + **Spawn 시 `OnConstruction(Transform)` 호출 — RerunConstructionScripts 는 매번 호출되어 멱등(idempotent) 해야 함**. BP Construction Script 도 OnConstruction 안에서 실행. |
| 🎯 **어셋 로드 정책** | 🚨 [`11_AssetLoadingPolicy.md`](../../references/11_AssetLoadingPolicy.md) — **모든 GameFramework 클래스는 Class 슬롯 (TSubclassOf vs TSoftClassPtr) + 어셋 멤버 (Hard vs Soft) 결정 의무**. 자주 Spawn 되는 Actor / 무기 / 발사체 = `UAssetManager::PreloadPrimaryAssets(bLoadRecursive=true)` Match Start 사전 로드. **`SpawnActorDeferred + FinishSpawning` 분리** — Property 셋업 후 BeginPlay. **Cooked Build (Development) `stat unit` 검증 의무** — Editor PIE 와 다름. |

> **Actor 6대 정책의 GameFramework 적용 — 자세한 코드 패턴·결정 트리·함정·체크리스트는 [`10_ComponentPolicies.md`](../../references/10_ComponentPolicies.md) + 각 sub-skill 본문 §1-§2.**
> **🎯 어셋 로드 정책 4단 표준 = [`11_AssetLoadingPolicy.md`](../../references/11_AssetLoadingPolicy.md) §5 + Actor §12** — SpawnActor 히칭 회피 의무.

---

## 1. sub-skill 인덱스 (6개)

| # | sub-skill | 위치 | 한 줄 요약 |
|---|-----------|------|----------|
| 1 | [`Actor`](./Actor/SKILL.md) | `skills/GameFramework/references/Actor.md` | **베이스 — 가장 큼**. AActor 5,074 lines. **라이프사이클 11단계** + **Super 호출 규약** + Spawn/Destroy + Tick + Component 등록 + Replication 진입점 + 6대 정책 적용. |
| 2 | [`PawnCharacter`](./PawnCharacter/SKILL.md) | `skills/GameFramework/references/PawnCharacter.md` | APawn 598 + ACharacter 1,095 lines **합본**. APawn (Controller 소유 + InputComponent + ReceiveControllerChanged) + ACharacter (CapsuleComponent + Mesh + CharacterMovementComponent 페어 + Jump/Crouch/Launch + RootMotion + bIsCrouched 복제). |
| 3 | [`Controller`](./Controller/SKILL.md) | `skills/GameFramework/references/Controller.md` | AController 420 + APlayerController 2,377 lines **합본** + AAIController (AIModule — cross-link). Possess/UnPossess 흐름 + Local/Remote + Camera Manager + Input Mode + RPC. |
| 4 | [`GameMode`](./GameMode/SKILL.md) | `skills/GameFramework/references/GameMode.md` | AGameModeBase 672 + AGameMode 11K + AGameStateBase / AGameState / APlayerState **합본**. **서버 only** Authority — DefaultPawnClass / RestartPlayer / InitGame / PostLogin / Logout + Match State (WaitingToStart/InProgress/WaitingPostMatch/LeavingMap) + SeamlessTravel. |
| 5 | [`GameInstance`](./GameInstance/SKILL.md) | `skills/GameFramework/references/GameInstance.md` | UGameInstance 664 lines + GameInstanceSubsystem (UDynamicSubsystem). **Levels/맵 전환 안 살아남는 유일한 World-bound 외 객체** + Init/Start/Shutdown + LocalPlayer 관리 + AssetManager 진입점 + LoadingScreen. |
| 6 | [`World`](./World/SKILL.md) | `skills/GameFramework/references/World.md` | UWorld 4,667 + ULevel 66KB **합본**. PersistentLevel + StreamingLevels + AuthorityGameMode + GameState + WorldType (Game/Editor/PIE/EditorPreview) + WorldSubsystem + Tick Group (TG_PrePhysics/DuringPhysics/PostPhysics 등) + Level Streaming (Always Loaded / Streaming / WorldPartition). |

---

## 2. 의존성 트리 (베이스 체인)

```
UObject (CoreUObject)
└── AActor                           (GameFramework/Actor)
    ├── APawn                        (GameFramework/PawnCharacter)
    │   └── ACharacter               (GameFramework/PawnCharacter — Pawn 자식)
    ├── AController                  (GameFramework/Controller)
    │   ├── APlayerController        (GameFramework/Controller)
    │   └── AAIController            (AIModule — cross-link)
    ├── AGameModeBase                (GameFramework/GameMode)
    │   └── AGameMode
    ├── AGameStateBase               (GameFramework/GameMode)
    │   └── AGameState
    ├── APlayerState                 (GameFramework/GameMode)
    └── AHUD                         (별도 — Slate/HUD 카테고리)

UObject
├── UGameInstance                    (GameFramework/GameInstance)
│   └── UGameInstanceSubsystem       (UDynamicSubsystem 자손)
├── UWorld                           (GameFramework/World)
│   └── UWorldSubsystem              (UDynamicSubsystem 자손 — World-bound)
└── ULevel                           (GameFramework/World — UWorld 안 PersistentLevel + StreamingLevels)
```

> **핵심 — Actor 가 모든 게임 객체의 베이스** (Pawn / Character / Controller / GameMode / GameState / PlayerState 모두 Actor 자손). UGameInstance / UWorld / ULevel 은 별도 트리 (UObject 직속).

---

## 3. 베이스 호출 흐름 (스폰 → 라이프사이클 → 디스폰)

```
[스폰 — 게임 스레드]
  UWorld::SpawnActor<T>(Class, Transform)
    ↓ (1) Constructor 호출 — CreateDefaultSubobject 등 — CDO 처리
    ↓ (2) PostInitProperties() — UObject 베이스
    ↓ (3) PostSpawnInitialize() — 트랜스폼 적용 + Owner / Instigator 설정
    ↓ (4) ExecuteConstruction → OnConstruction(Transform) — BP Construction Script + 매번 멱등
    ↓ (5) PostActorConstruction
        ↓ PreInitializeComponents()
        ↓ InitializeComponents() — ActorComponent->RegisterComponent (이때 Component->BeginPlay 안 됨)
        ↓ PostInitializeComponents()
    ↓ (6) FinishSpawning() — 리플리케이션 라우팅 + bHasFinishedSpawning = true
    ↓ (7) BeginPlay() — Component 들의 BeginPlay 도 함께 (UWorld 가 BeginPlayActor 면)
    ↓ (8) Tick(DeltaSeconds) — 매 프레임 (PrimaryActorTick.bCanEverTick == true 일 때만)

[디스폰 — Destroy 호출 또는 World 종료]
  Actor->Destroy() / UWorld::DestroyActor()
    ↓ (9) EndPlay(EEndPlayReason) — Component 들의 EndPlay 도 함께
    ↓ (10) Destroyed() — 즉시 콜백 (현재 프레임)
    ↓ (11) BeginDestroy() — UObject GC 직전 (다음 GC 사이클)
```

> **Super 호출 규약**:
> - `PostInitProperties` / `PostLoad` / `PreInitializeComponents` / `PostInitializeComponents` / `BeginPlay` → **`Super::` 처음** (베이스 초기화 먼저)
> - `EndPlay` / `Destroyed` / `BeginDestroy` → **`Super::` 마지막** (자식 정리 먼저)
> - `Tick` → **`Super::` 처음** (베이스 Tick 먼저)
> - `OnConstruction` → **`Super::` 처음**

자세한 통합 표는 [`04_OverrideIndex.md §6`](../../references/04_OverrideIndex.md) — Actor 라이프사이클 행 추가됨.

---

## 4. CDO + OnConstruction 규칙 (Actor 특화)

> [`10_ComponentPolicies.md §6 CDO`](../../references/10_ComponentPolicies.md) 의 Actor 적용 — **2개 추가 규칙**:

### 4.1 Constructor (CDO 생성 시점) — 의무 사항

```cpp
AMyActor::AMyActor()
{
    PrimaryActorTick.bCanEverTick = false;   // 기본 OFF
    PrimaryActorTick.TickGroup = TG_PrePhysics;
    bReplicates = false;                      // 필요 시만 활성

    // Component 생성 — Constructor 안만
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
    Mesh->SetupAttachment(RootComponent);

    // ⚠️ Constructor 안에서 GetWorld() / GetGameInstance() 호출 금지 — 둘 다 nullptr
    // ⚠️ Constructor 안에서 BeginPlay 안 끝남 — 다른 Actor 참조 금지
}
```

### 4.2 OnConstruction — 매번 멱등 (idempotent) 해야 함

```cpp
void AMyActor::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);

    // ⚠️ 멱등 — 호출될 때마다 동일 결과여야 함 (이전 상태에 의존 X)
    // BP Construction Script + RerunConstructionScripts (UPROPERTY 변경 등) 시마다 호출
    // → 누적·증분 작업 금지 (예: Mesh 추가 후 다시 추가 → 중복)

    // 정답: 기존 Component 정리 후 다시 생성 (또는 변경되지 않으면 작업 안 함)
    if (DynamicComponents.Num() > 0)
    {
        for (auto* Comp : DynamicComponents) Comp->DestroyComponent();
        DynamicComponents.Empty();
    }

    for (int32 i = 0; i < NumSegments; ++i)
    {
        UStaticMeshComponent* NewComp = NewObject<UStaticMeshComponent>(this, NAME_None, RF_Transactional);
        NewComp->RegisterComponent();
        DynamicComponents.Add(NewComp);
    }
}
```

> **함정**: OnConstruction 안에서 BeginPlay-시점 데이터 (다른 Actor / GameMode / Controller) 접근 금지 — 아직 BeginPlay 전.

### 4.3 PostInitializeComponents — Actor 의 Component 모두 등록 후

```cpp
void AMyActor::PostInitializeComponents()
{
    Super::PostInitializeComponents();

    // 이 시점에서 모든 Component 가 InitializeComponent 호출됨
    // BeginPlay 직전 — Component 간 페어 셋업 가능
    if (HealthComponent && DamageReceiverComponent)
    {
        HealthComponent->BindDamageReceiver(DamageReceiverComponent);
    }
}
```

---

## 5. Components 카테고리와의 차이 (cross-reference)

| 항목 | `[Components]` | `[GameFramework]` |
|------|----------------|-------------------|
| 베이스 | `UActorComponent` | `AActor` |
| 호스트 | Actor 안 부속 | World 안 1급 객체 |
| Spawn | `Actor->AddComponent` 또는 `CreateDefaultSubobject` | `World->SpawnActor` |
| 트랜스폼 | SceneComponent 자손만 보유 | 모든 Actor 가 RootComponent 보유 |
| Tick | `PrimaryComponentTick` | `PrimaryActorTick` (Component 들 전체 Tick 컨테이너) |
| Replication | `SetIsReplicatedByDefault` + `GetLifetimeReplicatedProps` | `bReplicates = true` + `GetLifetimeReplicatedProps` |
| BeginPlay | Component->BeginPlay (Actor BeginPlay 다음) | Actor->BeginPlay (Component 들의 BeginPlay 의 컨테이너) |
| 라이프사이클 | OnRegister / OnUnregister + BeginPlay / EndPlay | Constructor / OnConstruction / PreInit / Init / PostInit / BeginPlay / EndPlay / Destroyed / BeginDestroy |
| 6대 정책 적용 | 본 위키 [`10_ComponentPolicies.md`](../../references/10_ComponentPolicies.md) — **모든 Components sub-skill 본문 시작부** | 본 SKILL.md §0 + 각 GameFramework sub-skill — **Actor 특화 추가 규칙** (OnConstruction 멱등 / SpawnActor / PostSpawnInitialize) |

---

## 6. cross-cutting 인덱스 (모두 Read 권장)

- 🚨 [`10_ComponentPolicies.md`](../../references/10_ComponentPolicies.md) — 6대 정책 (CDO 포함). Actor 도 동일 적용.
- 🚨 [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) — Tick / TimerManager / 람다 / OnRep_\* / FieldNotify 모두 **Actor 콜백**에 동일 적용.
- 🚨 [`09_GlobalIteratorPolicy.md`](../../references/09_GlobalIteratorPolicy.md) — `TActorIterator<T>` 사용 금지. **GameMode / GameState / GameInstance 의 등록 패턴**으로 대체.
- [`04_OverrideIndex.md`](../../references/04_OverrideIndex.md) — virtual + Super 호출 통합 (Actor 라이프사이클 11단계 행 포함).
- [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) — `WITH_EDITOR` / `PostEditChangeProperty` Actor 적용.
- [`08_OverlapHotspots.md`](../../00_Over