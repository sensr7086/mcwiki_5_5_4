---
name: gameframework-world
description: UWorld (4,358 lines) + ULevel - Tick Group 8종 (PrePhysics/DuringPhysics/PostPhysics/PostUpdateWork) + Streaming 3종 + WorldSubsystem 등록.
---

# GameFramework/World — UWorld + ULevel + Streaming + WorldSubsystem

> **위치**: `Engine/Source/Runtime/Engine/Classes/Engine/World.h` (4,358 lines) + `Level.h` (66KB)
> **베이스**: `UWorld : public UObject` / `ULevel : public UObject`
> **요지**: UWorld = **게임 세계 컨테이너** (1개 PersistentLevel + N개 StreamingLevels + GameMode + GameState + Tick Group + Subsystem). ULevel = **Actor 모음 단위** (BP Level Script + Streaming 단위).

---

## 🚨 공통 정책 (Components 6대 의무 + World 특화)

| # | 정책 | World/Level 적용 |
|---|------|-----------------|
| 1 | **Mobility** | UObject — Mobility 무관 (Actor 컨테이너). |
| 2 | **NewObject + DuplicateObject** | World = Engine 자동 생성 (UWorld::CreateWorld). 사용자가 직접 NewObject 금지. Level = Streaming 시 LoadPackage 자동. |
| 3 | **GC 방어** | World 자체는 GameInstance 가 강참조. `UPROPERTY(Transient)` 멤버 — 자동 GC. **`GetWorld()` 결과 캐싱 금지** — UObject 마다 inline 호출 비용 0. |
| 4 | **Cached References** | `UWorld*` 캐싱 안 함 (호출 비용 0). `WorldSubsystem` 1회 검색 → 캐싱 권장 (Subsystem 자체는 영속). |
| 5 | **PrimaryActorTick** | UWorld 가 Tick 의 호스트 — `RunTickGroup(ETickingGroup)` 자동 호출. 매 프레임 갱신 = `UWorldSubsystem::Tick` 또는 `FTickFunction`. |
| 6 | **CDO + 자동 생성** | World 클래스 자체 CDO 무관 — 자식 클래스 만들 일 없음. WorldSubsystem 자식만 작성. |
| 🎯 **어셋 로드** | 🚨 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) — **Level Streaming = 비동기 + LoadingScreen 페어**. `FlushLevelStreaming(Full)` 게임 중 사용 금지 (프레임 멈춤). 5.x **WorldPartition** = Grid 기반 자동 streaming + ServerStreamingLevelsVisibility 멀티플레이 동기. **WorldSubsystem 등록 패턴** 으로 World-bound 어셋 매니저 작성 — Map 마다 새로 Init/Deinit. 글로벌 영속 데이터는 `GameInstanceSubsystem` 사용 (Map 전환 살아남음). |
| 🎯 **어셋 최적화** | 🚨 [`12_AssetOptimizationPolicy.md §3`](../../../references/12_AssetOptimizationPolicy.md) — **Actor Merging 4종** — (1) **HISM** (동일 메시 100+ — Foliage / Procedural Foliage 자동), (2) **Mesh Merge** (작은 영역 — Editor `Window > Developer Tools > Merge Actors` + `FMeshMergingSettings` + `MergeComponentsToStaticMesh` API), (3) **HLOD** (큰 영역 — 4.x `[/Script/Engine.HierarchicalLODSetup]` + `Build > Build HLOD` + 거리 기반 단일 메시 통합 Level 0/1/2), (4) **5.x WorldPartition HLOD** (오픈 월드 표준 — Grid Cell 200m / Layer 1km / Region 10km 자동). 결정 트리 = 동일 메시 100+ → HISM / 작은 영역 → Mesh Merge / 큰 영역 → HLOD / 오픈 월드 5.x → WorldPartition HLOD. |

---

## 1. UWorld 핵심 멤버 (4,358 lines)

### 1.1 Level 시스템

```cpp
// World.h:939 — 메인 Level (가장 중요)
UPROPERTY(Transient)
TObjectPtr<class ULevel> PersistentLevel;

// World.h:987 — 스트리밍 Level 배열
UPROPERTY(Transient)
TArray<TObjectPtr<ULevelStreaming>> StreamingLevels;

// World.h:991 — 활성 검토 중인 StreamingLevel (subset)
FStreamingLevelsToConsider StreamingLevelsToConsider;
```

### 1.2 GameMode / GameState 페어

```cpp
// World.h — 서버 측 GameMode (Authority 만)
TObjectPtr<AGameModeBase> AuthorityGameMode;

// World.h:655 — GameState (모든 클라 복제)
AGameStateBase* GetGameState() const { return GameState; }
TObjectPtr<class AGameStateBase> GameState;
```

### 1.3 WorldType (Game / Editor / PIE)

```cpp
// World.h:1231
TEnumAsByte<EWorldType::Type> WorldType;

namespace EWorldType
{
    enum Type
    {
        None,             // 초기화 전
        Game,             // 일반 게임 (Standalone / Server / Client)
        Editor,           // 에디터 메인 World (PIE 안 한 상태)
        PIE,              // Play In Editor
        EditorPreview,    // Material Editor 등 미리보기
        GamePreview,      // BP Editor Sequence preview
        GameRPC,          // RPC 전용 (Headless)
        Inactive          // GC 대기
    };
}
```

```cpp
// 가드 패턴 — 에디터 코드 분리
if (GetWorld()->WorldType == EWorldType::Editor)
{
    // 에디터 전용 로직
}
else if (GetWorld()->IsGameWorld())   // Game / PIE / GamePreview 모두
{
    // 게임 로직
}
```

---

## 2. Tick Group 시스템 (가장 중요)

### 2.1 ETickingGroup 8종 + 호출 순서

```cpp
enum ETickingGroup
{
    TG_PrePhysics = 0,           // 물리 시뮬 전 (가장 먼저)  ── Actor / Component 기본값
    TG_StartPhysics,              // 물리 시뮬 시작
    TG_DuringPhysics,             // 물리 시뮬 중               ── 물리 객체 보조
    TG_EndPhysics,                // 물리 시뮬 끝               ── 물리 결과 후처리
    TG_PostPhysics,               // 물리 후                    ── SkeletalMesh Anim 적용 후
    TG_PostUpdateWork,            // 가장 마지막                ── 카메라 (모든 위치 결정 후)
    TG_LastDemotable,             // 강등 가능 그룹             ── (드물게)
    TG_NewlySpawned               // 이번 프레임 Spawn 된 것    ── (자동 처리)
};
```

### 2.2 RunTickGroup (UWorld 내부 호출)

```cpp
// World.h:3314
UE_API void RunTickGroup(ETickingGroup Group, bool bBlockTillComplete);

// 내부 흐름
[UEngine::Tick]
  ↓ UWorld::Tick(LevelTick, DeltaSeconds)
    ↓ for each TickGroup (TG_PrePhysics → TG_PostUpdateWork):
      ↓ RunTickGroup(Group)
        ↓ 모든 Actor / Component 의 TickFunction 호출 (그룹 일치하면)
```

### 2.3 Tick Group 결정 매트릭스

| Tick 대상 | 권장 Group |
|----------|-----------|
| 일반 Actor / 로직 Component | `TG_PrePhysics` (기본) |
| Pawn 입력 / Movement | `TG_PrePhysics` |
| 물리 객체 보조 (PhysicsHandle 등) | `TG_DuringPhysics` |
| 물리 결과 적용 (Constraint 후처리) | `TG_EndPhysics` |
| SkeletalMesh Anim (CharacterMovement 후) | `TG_PostPhysics` |
| **Camera Component** (모든 위치 결정 후) | `TG_PostUpdateWork` |
| HUD 갱신 | `TG_PostUpdateWork` |

```cpp
// 카메라 Tick — Pawn / Anim 후 마지막
PrimaryActorTick.TickGroup = TG_PostUpdateWork;
```

### 2.4 Tick Prerequisite (그룹 내 순서)

```cpp
// 같은 그룹 내에서 다른 Actor / Component 후 Tick
AddTickPrerequisiteActor(OtherActor);
MyComp->AddTickPrerequisiteComponent(OtherComp);
```

> **Group 으로 큰 분류 + Prerequisite 으로 세밀 분류** — 매 프레임 자동 정렬.

---

## 3. ULevel — Actor 모음 단위

### 3.1 핵심 멤버

```cpp
// Level.h:432 — Actor 배열 (가장 중요)
UPROPERTY()
TArray<TObjectPtr<AActor>> Actors;

// Level.h:457 — 부모 World
TObjectPtr<UWorld> OwningWorld;

// Level.h:473 — Level Script BP
TObjectPtr<class ULevelScriptBlueprint> LevelScriptBlueprint;

// Level.h:490 — Level Script Actor (BP 인스턴스)
TObjectPtr<class ALevelScriptActor> LevelScriptActor;

// Level.h:445 — World Partition External Actors 사용 여부
bool bUseExternalActors;
```

### 3.2 PersistentLevel vs StreamingLevel

| 종류 | 의미 |
|------|------|
| **PersistentLevel** | World 의 메인 Level — 항상 로드. 1개만 |
| **StreamingLevel** | 동적 로드/언로드 가능 — 0~N개 (Always Loaded / Streaming / WorldPartition) |

```cpp
// 모든 Level (Persistent + Streaming) 순회
for (ULevel* Level : GetWorld()->GetLevels())
{
    for (AActor* Actor : Level->Actors)
    {
        // ...
    }
}
```

### 3.3 ⚠️ Level->Actors 직접 순회 — 신중

> [`09_GlobalIteratorPolicy.md §6`](../../../references/09_GlobalIteratorPolicy.md) 참조 — `Level->Actors` 는 nullptr 포함 가능 (Destroyed Actor) + Streaming 안 안전. **TActorIterator 보다 빠르지만** 매 프레임 사용 금지. **WorldSubsystem 등록 패턴 우선**.

---

## 4. Level Streaming 시스템

### 4.1 3종 Streaming 방식

| 방식 | 의미 | 사용 케이스 |
|------|------|----------|
| **Always Loaded** | 시작 시 로드 + 영구 유지 | UI 레이어 / 글로벌 객체 |
| **Streaming (Volume / Distance)** | 동적 로드 / 언로드 | 큰 맵의 영역 분할 |
| **WorldPartition (5.x)** | Grid 기반 자동 streaming | 오픈 월드 / 5.x 표준 |

### 4.2 Streaming API

```cpp
// World.h:3165 — 동기 강제 로드
UE_API void FlushLevelStreaming(EFlushLevelStreamingType FlushType = EFlushLevelStreamingType::Full);

// 비동기 로드 (BP / Code 표준)
UGameplayStatics::LoadStreamLevel(this, TEXT("MySublevel"), /*bMakeVisible=*/true, /*bShouldBlock=*/false, FLatentActionInfo());
UGameplayStatics::UnloadStreamLevel(this, TEXT("MySublevel"), FLatentActionInfo(), /*bShouldBlockOnUnload=*/false);

// EFlushLevelStreamingType
enum class EFlushLevelStreamingType
{
    None,
    Full,             // 모든 Streaming 처리 완료 대기
    Visibility        // Visibility 변경만 처리
};
```

### 4.3 WorldPartition (5.x — 오픈 월드 표준)

> **5.x WorldPartition** — Grid 기반 자동 streaming. Level Stream 수동 관리 불필요.

```cpp
// PlayerController 가 자동으로 ViewLocation 기반 Streaming Source
// 추가 Source = UWorldPartitionStreamingSourceComponent
```

> **자세한 패턴 = [`Components/SystemComponents §10`](../../Components/references/SystemComponents.md)** — UWorldPartitionStreamingSourceComponent.

### 4.4 ServerStreamingLevelsVisibility (서버 측 동기)

```cpp
// World.h:994
TObjectPtr<AServerStreamingLevelsVisibility> ServerStreamingLevelsVisibility;
```

> **서버가 어떤 StreamingLevel 을 Visibility 가지고 있는지 모든 클라에 복제** — 5.x 멀티플레이 표준.

---

## 5. UWorldSubsystem (가장 중요한 패턴)

> **UWorld 의 라이프사이클 동안 살아있는 자동 관리 객체** — Map 마다 새로 생성. World-bound 매니저 표준.

### 5.1 베이스 + 자동 생성

```cpp
// MyWorldSubsystem.h
#include "Subsystems/WorldSubsystem.h"

UCLASS()
class UMyWorldSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;
    virtual void OnWorldBeginPlay(UWorld& InWorld) override;

    UFUNCTION(BlueprintCallable)
    void RegisterEnemy(AEnemy* Enemy);

    UFUNCTION(BlueprintCallable)
    AEnemy* FindClosestEnemy(const FVector& Location) const;

private:
    UPROPERTY()
    TArray<TWeakObjectPtr<AEnemy>> RegisteredEnemies;
};

// MyWorldSubsystem.cpp
void UMyWorldSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyWorldSubsystem::Initialize);
    // World 생성 직후 자동 호출
}

void UMyWorldSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
    Super::OnWorldBeginPlay(InWorld);
    // 모든 Actor BeginPlay 후 자동 호출
}

void UMyWorldSubsystem::Deinitialize()
{
    // World 종료 시 자동
    RegisteredEnemies.Empty();
    Super::Deinitialize();
}
```

### 5.2 사용 (어디서든 GetSubsystem)

```cpp
// World.h:4196 — 표준 검색
auto* MyWS = GetWorld()->GetSubsystem<UMyWorldSubsystem>();

// World.h:4215 — static 헬퍼
auto* MyWS2 = UWorld::GetSubsystem<UMyWorldSubsystem>(GetWorld());

// World.h:4205 — Checked (보장 — assert)
auto* MyWS3 = GetWorld()->GetSubsystemChecked<UMyWorldSubsystem>();
```

### 5.3 ShouldCreateSubsystem (조건부 생성)

```cpp
// 특정 WorldType 에서만 생성 (PIE 만 / Game 만 등)
virtual bool ShouldCreateSubsystem(UObject* Outer) const override
{
    UWorld* World = Cast<UWorld>(Outer);
    return World && World->IsGameWorld();   // Game / PIE / GamePreview 만
}

// Editor World 에서는 생성 X
return World->WorldType == EWorldType::Game || World->WorldType == EWorldType::PIE;
```

### 5.4 등록 패턴 (전역 이터레이터 회피 — 가장 강력)

```cpp
// Enemy 자식 — BeginPlay 시 자동 등록
void AEnemy::BeginPlay()
{
    Super::BeginPlay();
    if (auto* WS = GetWorld()->GetSubsystem<UMyWorldSubsystem>())
    {
        WS->RegisterEnemy(this);
    }
}

void AEnemy::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (auto* WS = GetWorld()->GetSubsystem<UMyWorldSubsystem>())
    {
        WS->UnregisterEnemy(this);
    }
    Super::EndPlay(EndPlayReason);
}

// Manager — 등록된 객체에서만 검색 (TActorIterator 회피)
AEnemy* UMyWorldSubsystem::FindClosestEnemy(const FVector& Location) const
{
    AEnemy* Closest = nullptr;
    float MinDistSq = FLT_MAX;
    for (auto& WeakEnemy : RegisteredEnemies)
    {
        if (auto* E = WeakEnemy.Get())
        {
            float D = FVector::DistSquared(E->GetActorLocation(), Location);
            if (D < MinDistSq) { MinDistSq = D; Closest = E; }
        }
    }
    return Closest;
}
```

---

## 6. TimerManager + LatentActionManager

```cpp
// World.h:4173
UE_API FTimerManager& GetTimerManager() const;

// World.h:4182
UE_API FLatentActionManager& GetLatentActionManager();
```

```cpp
// 표준 Timer
GetWorld()->GetTimerManager().SetTimer(MyHandle, this, &AMyActor::OnTimer, 1.0f, /*bLoop=*/true);
GetWorld()->GetTimerManager().ClearTimer(MyHandle);

// 람다 Timer — 프로파일링 스코프 의무
GetWorld()->GetTimerManager().SetTimer(MyHandle, FTimerDelegate::CreateLambda([this]()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyLambdaTimer);
    // ...
}), 1.0f, true);
```

> **자세한 Timer 프로파일링 = [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)**.

---

## 7. 🎯 최적화 방안

### 7.1 WorldSubsystem 등록 패턴 (가장 큰 최적화)

> **모든 World-bound 글로벌 검색 → WorldSubsystem 등록** — 전역 이터레이터 회피.

```cpp
// ❌ 매 프레임 검색 — N번 순회
for (TActorIterator<AEnemy> It(GetWorld()); It; ++It) { ... }

// ✅ Subsystem 등록 — O(N) 한 번 + 매번 O(1)
GetWorld()->GetSubsystem<UEnemySubsystem>()->GetAllEnemies();
```

### 7.2 Level Streaming 비동기 + Block 회피

```cpp
// ❌ FlushLevelStreaming — 동기 (프레임 멈춤)
GetWorld()->FlushLevelStreaming(EFlushLevelStreamingType::Full);

// ✅ 비동기 — Latent
FLatentActionInfo Info;
Info.CallbackTarget = this;
Info.ExecutionFunction = "OnLevelLoaded";
Info.UUID = 1;
Info.Linkage = 0;
UGameplayStatics::LoadStreamLevel(this, "MyLevel", true, false, Info);
```

### 7.3 WorldPartition (5.x — 오픈 월드 표준)

```ini
; DefaultEngine.ini
[/Script/Engine.WorldPartitionSubsystem]
DefaultStreamingFlushPolicy=BlockTillFullyVisible    ; 또는 None / Always

; DefaultGame.ini
[/Script/Engine.GameMapsSettings]
GameDefaultMap=/Game/Maps/MainOpenWorld
```

### 7.4 Tick Group 분리

```cpp
// 카메라 — TG_PostUpdateWork (모든 위치 결정 후)
PrimaryActorTick.TickGroup = TG_PostUpdateWork;

// 일반 게임 로직 — TG_PrePhysics (기본)
PrimaryActorTick.TickGroup = TG_PrePhysics;

// 물리 보조 — TG_DuringPhysics (Substepping 안전)
PrimaryActorTick.TickGroup = TG_DuringPhysics;
```

### 7.5 ServerStreamingLevelsVisibility (멀티플레이 동기)

> 서버가 어떤 StreamingLevel 을 가지고 있는지 모든 클라에 복제 — 클라 측 Spawn 시점 자동 동기.

---

## 8. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | `UWorld*` 캐싱 | inline + 비용 0 — 매번 `GetWorld()` 호출 OK |
| 2 | `Level->Actors` 매 프레임 순회 | nullptr 포함 가능 + WorldSubsystem 등록 패턴 우선 |
| 3 | `FlushLevelStreaming(Full)` 게임 중 호출 | 프레임 멈춤 — 비동기 Latent 사용 |
| 4 | Camera Tick = `TG_PrePhysics` (기본값) | 위치 결정 전에 카메라 → 1 프레임 지연 → `TG_PostUpdateWork` |
| 5 | `WorldType` 검사 안 하고 에디터에서 BeginPlay 의존 코드 | `WorldType::Editor` 에서는 BeginPlay 안 호출됨 — `IsGameWorld()` 가드 |
| 6 | WorldSubsystem 으로 영속 데이터 보유 | World 마다 재생성 → 데이터 손실. `GameInstanceSubsystem` 사용 |
| 7 | 매 프레임 `TActorIterator<T>` 사용 | WorldSubsystem 등록 패턴 ([`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md)) |
| 8 | `GetTimerManager().SetTimer` 람다 첫 줄 프로파일링 스코프 누락 | 의무 ([`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)) |
| 9 | `LoadStreamLevel` 후 즉시 Actor 검색 | 비동기 — 콜백 안에서 검색 또는 `OnLevelLoaded` Delegate 사용 |
| 10 | 5.x WorldPartition + 수동 LevelStreaming 혼용 | 충돌 가능 — 둘 중 하나만 |

---

## 9. 체크리스트

- [ ] WorldSubsystem 자식: `Initialize` / `Deinitialize` / `OnWorldBeginPlay` override (필요한 것만) + Super 호출
- [ ] WorldSubsystem 자식: `ShouldCreateSubsystem` (Game/PIE 만 등) override
- [ ] Tick Group 명시 — 카메라 = `TG_PostUpdateWork` / 물리 = `TG_DuringPhysics` / 일반 = `TG_PrePhysics`
- [ ] Level Streaming = 비동기 (Latent) — `FlushLevelStreaming` 게임 중 사용 X
- [ ] 글로벌 검색 = WorldSubsystem 등록 패턴 — `TActorIterator` 안 사용
- [ ] WorldType 가드 (`IsGameWorld()` / `WorldType::Editor`)
- [ ] TimerManager 람다 첫 줄 프로파일링 스코프
- [ ] 5.x = WorldPartition 표준 — 수동 LevelStreaming 혼용 X
- [ ] 🚨 6대 정책 만족 ([`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md))
- [ ] 🚨 등록 패턴 ([`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md))
- [ ] 🚨 프로파일링 스코프 ([`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md))

---

## 10. 관련 sub-skill

- [`GameFramework/Actor`](../Actor/SKILL.md) — UWorld::SpawnActor / Tick Group
- [`GameFramework/GameInstance`](../GameInstance/SKILL.md) — Subsystem 4종 비교 + Map 전환 흐름
- [`GameFramework/GameMode`](../GameMode/SKILL.md) — AuthorityGameMode + GameState 페어
- [`Components/SystemComponents`](../../Components/references/SystemComponents.md) — UWorldPartitionStreamingSourceC