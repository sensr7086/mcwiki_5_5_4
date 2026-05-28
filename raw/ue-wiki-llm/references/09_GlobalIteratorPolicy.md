---
name: global-iterator-policy
description: 🚨 TActorIterator/TObjectIterator/TObjectRange/TActorRange 사용 금지 정책. 매 프레임/콜백 안 사용 시 즉시 폭사. 대안 7종 (Subsystem 등록·AssetRegistry·UWorld::Actors·Tag·캐시·SpatialHash·OverlapMulti) + 결정 트리 + 최후의 수단 5조건. 모든 코드 작성 시 우선 검토.
---

# Global Iterator Policy — TActorIterator / TObjectIterator / TObjectRange 사용 금지 정책

> **🚨 모든 sub-skill 공통 의무** — 본 인덱스는 UE의 **전역 객체 이터레이터** 사용에 대한 정책. 코드 작성 시 **최대한 사용 금지**, 다른 모든 대안이 부적절할 때만 **최후의 수단**으로 사용.
> CLAUDE.md §8.1 / 03_WikiHarness.md §0.1 교차 참조 인덱스에서 본 문서를 참조.
> 5.7.4 트리 검증 (`Engine/Public/EngineUtils.h` L318·L569·L621 / `CoreUObject/Public/UObject/UObjectIterator.h` L75·L256·L414).

---

## 0. 한 줄 정책

> **"전역 이터레이터(TActorIterator·TObjectIterator·TObjectRange)는 매 사용마다 N개 객체 전체를 순회한다. 매 프레임·매 콜백에서 호출하면 즉시 성능 폭사. 등록 패턴(Subsystem·Manager·Tag)으로 대체 후, 정말 다른 방법이 없을 때만 1회·드물게 호출."**

---

## 1. 대상 이터레이터

### 1.1 TActorIterator<ActorType> (`Engine/Public/EngineUtils.h` L569)

```cpp
template<typename ActorType>
class TActorIterator : public TActorIteratorBase<TActorIterator<ActorType>>
```

**용도**: 현재 World의 모든 액터 중 특정 클래스 자손 순회.

```cpp
for (TActorIterator<AMyEnemy> It(GetWorld()); It; ++It)
{
    AMyEnemy* Enemy = *It;
    // ...
}
```

**비용**:
- O(N) — World의 PersistentLevel + 모든 Streaming Level 의 액터 전체 순회
- 클래스 필터는 자식 검사 (`IsA`) — N 비례
- 50,000 액터 환경에서 매 프레임 호출 시 수십 ms 스파이크

### 1.2 TObjectIterator<T> (`CoreUObject/Public/UObject/UObjectIterator.h` L256)

```cpp
template<class T> class TObjectIterator
```

**용도**: 메모리 안 모든 UObject 인스턴스 (전 World + 에디터 객체 + CDO + 기타) 중 특정 클래스 순회.

```cpp
for (TObjectIterator<UMyAsset> It; It; ++It)
{
    UMyAsset* Asset = *It;
    // ...
}
```

**비용**:
- O(N_global) — **전체 GUObjectArray** 순회 (런타임 5만~30만+, 에디터 50만+)
- TActorIterator보다 **훨씬 비쌈** — 액터 외 모든 UObject 포함
- 매 프레임 호출 = 즉사

### 1.3 TObjectRange<T> (`CoreUObject/Public/UObject/UObjectIterator.h` L414)

```cpp
template<class T>
struct TObjectRange
{
    TObjectRange(EObjectFlags AdditionalExclusionFlags = RF_ClassDefaultObject,
                 bool bIncludeDerivedClasses = true,
                 EInternalObjectFlags InInternalExclusionFlags = EInternalObjectFlags::None);
    // ... begin/end (range-for 지원)
};
```

**용도**: TObjectIterator 의 range-for 변형. **비용 동일** — 문법만 다름.

```cpp
for (UMyAsset* Asset : TObjectRange<UMyAsset>())
{
    // ...
}
```

### 1.4 TActorRange (`Engine/Public/EngineUtils.h` L621)

`TActorIterator` 의 range-for 변형 — 동일 비용.

```cpp
for (AMyEnemy* Enemy : TActorRange<AMyEnemy>(GetWorld()))
{
    // ...
}
```

### 1.5 변형들 (모두 동일 정책)

| 이터레이터 | 위치 | 의미 |
|----------|------|------|
| `FActorIterator` | EngineUtils.h L498 | 모든 액터 (제너릭 X) |
| `FSelectedActorIterator` 🛠 | EngineUtils.h L652 | 에디터 선택 액터 |
| `FObjectIterator` (`TObjectIterator<UObject>`) | UObjectIterator.h L361 | 모든 UObject |
| `FThreadSafeObjectIterator` | (베이스) | TObjectIterator의 베이스 |
| `FUObjectArray::TIterator` | UObjectArray.h | 가장 저수준 |

---

## 2. 🚨 사용 금지 — 전형적 안티패턴

### 2.1 매 프레임 / Tick 안에서 호출

```cpp
// ❌ 절대 금지 — 매 프레임 World의 모든 액터 순회
void AMyManager::Tick(float DeltaTime)
{
    Super::Tick(DeltaTime);
    for (TActorIterator<AEnemy> It(GetWorld()); It; ++It) { /* ... */ }
}

// ❌ 절대 금지 — 매 프레임 모든 UObject 순회
void AMyManager::Tick(float DeltaTime)
{
    for (TObjectIterator<UMyAsset> It; It; ++It) { /* ... */ }
}
```

### 2.2 콜백 / 델리게이트 핸들러 안

```cpp
// ❌ Overlap 콜백 — 매 진입마다 전체 액터 순회
UFUNCTION() void HandleBeginOverlap(...)
{
    for (TActorIterator<AItem> It(GetWorld()); It; ++It) { /* ... */ }
}
```

### 2.3 Begin 시점 외 게임 빌드 코드

```cpp
// ❌ 게임 빌드에서 TObjectIterator
void UMyComponent::BeginPlay()
{
    Super::BeginPlay();
    // 메모리 안 모든 UMyAsset 검색 — 게임 빌드에선 절대 X
    for (TObjectIterator<UMyAsset> It; It; ++It) { /* ... */ }
}
```

### 2.4 사용자 입력 / UI 응답

```cpp
// ❌ 버튼 클릭 시 — 응답성 폭사
UFUNCTION() void OnRefreshClicked()
{
    for (TActorIterator<APickup> It(GetWorld()); It; ++It) { /* ... */ }
}
```

---

## 3. ✅ 대안 패턴 (우선순위 순)

### 3.1 Subsystem / Manager 등록 패턴 (1순위 — 가장 권장)

```cpp
// World Subsystem이 액터를 등록·관리
UCLASS()
class UEnemyManagerSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()
public:
    void RegisterEnemy(AEnemy* Enemy)   { Enemies.AddUnique(Enemy); }
    void UnregisterEnemy(AEnemy* Enemy) { Enemies.RemoveSwap(Enemy); }
    const TArray<TWeakObjectPtr<AEnemy>>& GetEnemies() const { return Enemies; }

private:
    UPROPERTY()
    TArray<TWeakObjectPtr<AEnemy>> Enemies;
};

// 액터 본인이 등록·해제
void AEnemy::BeginPlay()
{
    Super::BeginPlay();
    if (UEnemyManagerSubsystem* Mgr = GetWorld()->GetSubsystem<UEnemyManagerSubsystem>())
    {
        Mgr->RegisterEnemy(this);
    }
}

void AEnemy::EndPlay(const EEndPlayReason::Type Reason)
{
    if (UEnemyManagerSubsystem* Mgr = GetWorld()->GetSubsystem<UEnemyManagerSubsystem>())
    {
        Mgr->UnregisterEnemy(this);
    }
    Super::EndPlay(Reason);
}

// 사용 — O(1) 시간에 캐시된 배열 접근
const TArray<TWeakObjectPtr<AEnemy>>& Enemies = Mgr->GetEnemies();
```

→ 매 프레임 호출 가능. 전체 World 순회 X.

### 3.2 AssetRegistry (디스크 에셋 검색)

```cpp
// 디스크의 모든 UMyAsset 검색 — TObjectIterator 대체
IAssetRegistry& Reg = IAssetRegistry::GetChecked();
FARFilter Filter;
Filter.ClassPaths.Add(UMyAsset::StaticClass()->GetClassPathName());
Filter.bRecursiveClasses = true;
TArray<FAssetData> AssetDataList;
Reg.GetAssets(Filter, AssetDataList);
// → 비동기 가능 (FStreamableManager + RequestAsyncLoad)
```

자세한 — [`skills/AssetRegistry`](../skills/Editor/references/AssetRegistry.md).

### 3.3 UWorld의 ActorList (단일 World 액터 검색)

```cpp
// PersistentLevel + Streaming Level 액터 직접 접근
ULevel* Level = GetWorld()->PersistentLevel;
for (AActor* Actor : Level->Actors)   // O(N)
{
    if (AMyEnemy* Enemy = Cast<AMyEnemy>(Actor)) { /* ... */ }
}

// 또는 GameMode/GameState 의 캐시
AGameStateBase* GS = GetWorld()->GetGameState();
TArray<APlayerState*> Players = GS->PlayerArray;  // 표준 PlayerState 배열
```

→ 단일 World 액터만 — TObjectIterator(전 메모리) 보다는 가벼우나 여전히 O(N) — 이벤트 기반 1회 호출 권장.

### 3.4 Tag / GameplayTag 기반 필터

```cpp
// 액터에 GameplayTag 부여
UGameplayTagComponent* TagComp = GetComponentByClass<UGameplayTagComponent>();
TagComp->AddGameplayTag(FGameplayTag::RequestGameplayTag("Enemy.Boss"));

// GameplayTagSubsystem 또는 자체 Manager 가 Tag → Actors 매핑 보관
```

### 3.5 GameInstanceSubsystem 캐시 (게임 라이프타임)

```cpp
UCLASS()
class UGameDataSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override
    {
        Super::Initialize(Collection);
        // 게임 시작 시 1회만 — AssetRegistry 사용
        BuildAssetCache();
    }

    const TArray<TSoftObjectPtr<UMyAsset>>& GetAllMyAssets() const { return AllMyAssets; }

private:
    UPROPERTY()
    TArray<TSoftObjectPtr<UMyAsset>> AllMyAssets;

    void BuildAssetCache()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UGameDataSubsystem_BuildAssetCache);
        IAssetRegistry& Reg = IAssetRegistry::GetChecked();
        // ...
    }
};
```

→ 게임 시작 시 1회. 이후 O(1) 캐시 접근.

### 3.6 Component 배열 캐시 (액터 안 컴포넌트)

```cpp
// 한 액터의 모든 UMyComponent 자손
TArray<UMyComponent*> Comps;
GetOwner()->GetComponents<UMyComponent>(Comps);    // 액터 자체 컴포넌트 배열
```

전 World 순회 아님 — 액터 1개의 컴포넌트만 — 가벼움.

### 3.7 Spatial Hash / Octree (위치 기반 검색)

```cpp
// 일정 반경 내 액터만 — Overlap 또는 SphereTrace 사용
TArray<FOverlapResult> Overlaps;
FCollisionQueryParams Params;
GetWorld()->OverlapMultiByChannel(
    Overlaps,
    GetActorLocation(),
    FQuat::Identity,
    ECC_Pawn,
    FCollisionShape::MakeSphere(Radius),
    Params);
```

→ Spatial 자료구조 사용 — 전체 순회보다 빠름.

---

## 4. 결정 트리

```
"이 컴포넌트/액터/오브젝트들을 검색하고 싶다" →
│
├─ 매 프레임 / Tick / 콜백 안에서?
│   ├─ Yes → 등록 패턴 (Subsystem) 의무
│   │       (TActorIterator/TObjectIterator 절대 금지)
│   │
│   └─ No → 다음 단계
│
├─ 메모리 안 객체? 디스크 에셋?
│   ├─ 디스크 에셋 → AssetRegistry 의무
│   │
│   └─ 메모리 안 → 다음 단계
│
├─ 액터인가 일반 UObject 인가?
│   ├─ 액터 → UWorld::PersistentLevel->Actors / GetGameState()->PlayerArray
│   │       또는 등록 패턴
│   │
│   └─ UObject → 등록 패턴 (Subsystem)
│       또는 GameInstanceSubsystem 캐시
│
├─ 위치 기반 (반경·시야) 검색?
│   └─ OverlapMulti / SphereTrace / Spatial Hash
│
└─ 모든 대안이 부적절 + 1회 호출 + 디버그/에디터 ?
    └─ TObjectIterator/TActorIterator 사용 가능 (§5 조건 만족 시)
```

---

## 5. 최후의 수단으로 허용되는 케이스

다음 **모든** 조건을 만족할 때만 사용:

1. **호출 빈도가 매우 낮음** — 게임 시작 1회 / 사용자가 명시적 트리거 (UI 버튼) / 에디터 빌드만
2. **다른 대안이 부적절** — Subsystem 등록 어려움 (예: 외부 플러그인 액터, 마이그레이션 도구)
3. **🚨 프로파일링 스코프 의무** — `TRACE_CPUPROFILER_EVENT_SCOPE` 부착
4. **명시적 주석** — 왜 사용하는지 + 왜 다른 대안이 안 되는지
5. **`#if WITH_EDITOR` 가드 (가능하면)** — 게임 빌드에서 빠지도록

```cpp
#if WITH_EDITOR
void UMyEditorTool::FindAllInvalidAssets()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyEditorTool_FindAllInvalidAssets);

    // 사유: 5.x AssetRegistry로는 메모리에 로드된 객체 상태(bIsDirty 등)를
    // 알 수 없어 TObjectIterator 사용 (1회·에디터 전용·사용자 명시 트리거)
    for (TObjectIterator<UMyAsset> It; It; ++It)
    {
        if (It->IsValidationFailing())
        {
            // ...
        }
    }
}
#endif
```

### 5.1 합리적 사용 케이스 (예외)

| 케이스 | 빈도 | 가드 | 대안 검토 |
|--------|------|------|----------|
| 에디터 도구 — Validate Project (사용자 메뉴 클릭) | 1회·드물게 | `WITH_EDITOR` | AssetRegistry 부족 시 OK |
| 디버그 콘솔 명령 — `DumpAllPawns` | 사용자 명시 | (필요 시 `WITH_EDITOR`) | OK |
| Save/Load — 마이그레이션 (예: 5.0→5.1 데이터 변환) | 1회 | (Cook 시점) | OK |
| Cook 시점 처리 (`CommandletMain`) | 빌드 1회 | `IsRunningCommandlet()` | OK |
| 게임 시작 1회 — 외부 플러그인 액터 검색 | BeginPlay 1회 | (없음) | Subsystem 등록 시도 후 |
| Automation Test — 객체 무결성 검증 | 테스트 1회 | (테스트 빌드) | OK |
| 메모리 디버그 — Leak 추적 | 명시 호출 | `WITH_EDITOR` | OK |

### 5.2 절대 금지 케이스

| 케이스 | 이유 |
|--------|------|
| `Tick` 안 | 매 프레임 — 즉사 |
| `OnComponentBeginOverlap` 등 콜백 | 빈도 폭증 |
| `UFUNCTION` 바인딩된 핸들러 | 외부 호출 시점 모름 |
| `OnRep_*` 안 | 임의 시점 |
| `BeginPlay` 안 (게임 빌드) | N개 액터 모두 BeginPlay 시 N×N |
| 사용자 입력 직접 처리 | 응답성 폭사 |

---

## 6. 측정 / 디버깅

### 6.1 비용 측정

```cpp
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyClass_ScanAllAssets);
    const double Start = FPlatformTime::Seconds();

    int32 Count = 0;
    for (TObjectIterator<UMyAsset> It; It; ++It) { Count++; }

    const double Elapsed = (FPlatformTime::Seconds() - Start) * 1000.0;
    UE_LOG(LogTemp, Warning, TEXT("Scanned %d UMyAsset in %.2fms"), Count, Elapsed);
}
```

게임 빌드 50ms+ 라면 즉시 대안 검토.

### 6.2 콘솔 명령

| 명령 | 의미 |
|------|------|
| `obj list class=AMyEnemy` | 클래스별 객체 카운트 |
| `obj list inside=...` | 특정 Outer 의 객체 |
| `stat unit` | 프레임 시간 |
| `stat memory` | 메모리 사용 |

### 6.3 Insights 트레이스

`TRACE_CPUPROFILER_EVENT_SCOPE` 를 부착했다면 Insights에서 시간 측정 가능. 프레임 spike 분석 시 우선 검사.

---

## 7. 스코프 / 정책 통합

본 정책 + [`07_ProfilingScopeRule.md`](./07_ProfilingScopeRule.md) 통합:

- **사용 시 의무**:
  - 🚨 `TRACE_CPUPROFILER_EVENT_SCOPE` 첫 줄에 부착
  - 명시적 주석 (왜 / 빈도)
  - 가능하면 `#if WITH_EDITOR` 가드
- **사용 금지 시**:
  - Subsystem 등록 패턴
  - AssetRegistry
  - 캐시 + 옵서버

---

## 8. 5단 작업 체크리스트

코드 작성 시:

- [ ] `TActorIterator` / `TObjectIterator` / `TObjectRange` / `TActorRange` 사용을 **먼저 의심**한다
- [ ] 매 프레임·Tick·콜백 안에서 사용한다면 **즉시 등록 패턴으로 대체**
- [ ] 메모리 안 객체 검색이면 **Subsystem 등록 / AssetRegistry / Spatial 검색** 우선
- [ ] 정말 불가피하면 §5.1 케이스에 부합하는지 확인 + 5조건 만족
- [ ] 사용 시 `TRACE_CPUPROFILER_EVENT_SCOPE` + 주석 + 가능하면 `#if WITH_EDITOR`

---

## 9. sub-skill 별 적용 매트릭스

| sub-skill | 대표 대안 |
|-----------|----------|
| [`Components/ActorComponent`](../skills/Components/references/ActorComponent.md) | UWorldSubsystem 등록 패턴 |
| [`Components/PrimitiveComponent`](../skills/Components/references/PrimitiveComponent.md) | Overlap / SphereTrace 사용 |
| [`Components/MeshComponents`](../skills/Components/references/MeshComponents.md) | Significance + Subsystem |
| [`Significance`](../skills/Significance/SKILL.md) | 자기 자신이 등록 패턴 |
| [`AssetRegistry`](../skills/Editor/references/AssetRegistry.md) | TObjectIterator 의 디스크 대안 |
| [`UnrealEd/Subsystems`](../skills/Editor/references/UnrealEd/Subsystems.md) | UEditorActorSubsystem (액터 일괄) |
| [`UnrealEd/Elements`](../skills/Editor/references/UnrealEd/Elements.md) | 5.x Element 시스템 |
| [`CoreUObject/Reflection`](../skills/CoreUObject/references/Reflection.md) | UObjectIterator 자체 정의 (참고용) |

---

## 10. 갱신 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. EngineUtils.h L318·L498·L569·L621·L652 + UObjectIterator.h L75·L256·L361·L414 검증. **사용 금지 안티패턴 4종** + **대안 7종** + **결정 트리** + **§5 최후의 수단 허용 5조건 + 7예외 케이스 + 6금지 케이스** + **5단 체크리스트** + sub-skill 적용 매트릭스. |
