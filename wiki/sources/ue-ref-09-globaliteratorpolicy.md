---
type: source
title: "UE refs — 09 GlobalIteratorPolicy (전역 이터레이터 금지)"
slug: ue-ref-09-globaliteratorpolicy
source_path: raw/ue-wiki-llm/references/09_GlobalIteratorPolicy.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
related_concepts:
  - "[[concepts/Global-Iterator-Avoidance]]"
  - "[[concepts/Subsystem-5-Types]]"
tags: [ue, reference, policy, iterator, governance, performance]
---

# UE refs — 09 GlobalIteratorPolicy 🚨

> Source: [[raw/ue-wiki-llm/references/09_GlobalIteratorPolicy.md]] · CLAUDE.md §0.1.3 의무 정책 · UE 5.7.4 EngineUtils.h / UObjectIterator.h grep 검증

## 1. Summary

🚨 **모든 sub-skill 공통 의무** — `TActorIterator` / `TObjectIterator` / `TObjectRange` / `TActorRange` **사용 금지 정책**. 매 사용마다 N개 객체 전체 순회 → 매 프레임 / 콜백 안 사용 시 즉시 성능 폭사. **등록 패턴 (Subsystem / Manager / Tag)** 으로 대체 후, 정말 다른 방법이 없을 때만 **최후의 수단** 으로 1회 / 드물게 호출. 권위 concept = [[concepts/Global-Iterator-Avoidance]].

## 2. 대상 이터레이터 (4종) 🟢

| 이터레이터 | 위치 | 비용 | 가장 비쌈 |
| -- | -- | -- | -- |
| `TActorIterator<T>` | `Engine/Public/EngineUtils.h:L569` | O(N) — World 액터 전체 | 50,000 액터 환경 매 프레임 = 수십 ms |
| **`TObjectIterator<T>`** | `CoreUObject/Public/UObject/UObjectIterator.h:L256` | O(N_global) — 전체 GUObjectArray | 런타임 5만~30만+ / 에디터 50만+ — **즉사** |
| `TObjectRange<T>` | `UObjectIterator.h:L414` | TObjectIterator range-for 변형 | 비용 동일 |
| `TActorRange<T>` | `EngineUtils.h:L621` | TActorIterator range-for 변형 | 비용 동일 |

추가 변형 (동일 정책): `FActorIterator` (L498) · `FSelectedActorIterator` 🛠 (L652) · `FObjectIterator` (L361) · `FThreadSafeObjectIterator` · `FUObjectArray::TIterator`.

## 3. 사용 금지 안티패턴 (4종) 🔴

| # | 케이스 | 이유 |
| -- | -- | -- |
| 1 | **`Tick` 안** | 매 프레임 — 즉사 |
| 2 | **`OnComponentBeginOverlap` / `OnRep_*` / `AddDynamic` 핸들러** | 빈도 폭증 + 외부 시점 |
| 3 | **사용자 입력 / UI 응답** (OnClicked) | 응답성 폭사 |
| 4 | **`BeginPlay` 안 (게임 빌드)** | N 개 액터 모두 BeginPlay 시 N×N |

```cpp
// 🔴 절대 금지 — 매 프레임 World 의 모든 액터 순회
void AMyManager::Tick(float Dt)
{
    Super::Tick(Dt);
    for (TActorIterator<AEnemy> It(GetWorld()); It; ++It) { /* ... */ }
}
```

## 4. 대안 패턴 (7종, 우선순위 순) 🟢

### 4.1. Subsystem / Manager 등록 패턴 (1순위 — 가장 권장)

```cpp
UCLASS()
class UEnemyManagerSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()
public:
    void RegisterEnemy(AEnemy* E)   { Enemies.AddUnique(E); }
    void UnregisterEnemy(AEnemy* E) { Enemies.RemoveSwap(E); }
    const TArray<TWeakObjectPtr<AEnemy>>& GetEnemies() const { return Enemies; }

private:
    UPROPERTY() TArray<TWeakObjectPtr<AEnemy>> Enemies;
};

// 액터 본인이 등록·해제
void AEnemy::BeginPlay() { Super::BeginPlay(); GetWorld()->GetSubsystem<UEnemyManagerSubsystem>()->RegisterEnemy(this); }
void AEnemy::EndPlay(const EEndPlayReason::Type R) { GetWorld()->GetSubsystem<UEnemyManagerSubsystem>()->UnregisterEnemy(this); Super::EndPlay(R); }
```

→ 매 프레임 호출 가능. 전체 World 순회 X. KMCProject `UMCActorSpawnSubsystem` 사례 — [[synthesis/mc-actor-spawn-subsystem-implementation]].

### 4.2. AssetRegistry (디스크 에셋 검색)

```cpp
IAssetRegistry& Reg = IAssetRegistry::GetChecked();
FARFilter Filter;
Filter.ClassPaths.Add(UMyAsset::StaticClass()->GetClassPathName());
Filter.bRecursiveClasses = true;
TArray<FAssetData> Results;
Reg.GetAssets(Filter, Results);
```

→ [[sources/ue-editor-assetregistry]] (TObjectIterator 의 디스크 대안).

### 4.3. UWorld::PersistentLevel + Streaming Level

```cpp
ULevel* Level = GetWorld()->PersistentLevel;
for (AActor* A : Level->Actors)   // O(N) — 단일 World 만
{
    if (AMyEnemy* E = Cast<AMyEnemy>(A)) { /* ... */ }
}
```

→ TObjectIterator (전 메모리) 보다 가벼움. 이벤트 기반 1회 호출 권장.

### 4.4. GameplayTag / Tag 기반 필터

`UGameplayTagComponent` + Tag → Actors 매핑 보관 (Subsystem 또는 자체 Manager). → [[sources/ue-gas-skill]].

### 4.5. GameInstanceSubsystem 캐시 (게임 라이프타임 1회)

```cpp
virtual void Initialize(FSubsystemCollectionBase& C) override
{
    Super::Initialize(C);
    TRACE_CPUPROFILER_EVENT_SCOPE(UGameDataSubsystem_BuildCache);
    // AssetRegistry 사용 — 1회만
    BuildAssetCache();
}
```

### 4.6. Component 배열 캐시 (액터 안 컴포넌트)

```cpp
TArray<UMyComponent*> Comps;
GetOwner()->GetComponents<UMyComponent>(Comps);   // 액터 1개 컴포넌트만 — 가벼움
```

### 4.7. Spatial Hash / Octree (위치 기반)

```cpp
TArray<FOverlapResult> Overlaps;
GetWorld()->OverlapMultiByChannel(Overlaps, GetActorLocation(), FQuat::Identity,
    ECC_Pawn, FCollisionShape::MakeSphere(Radius));
```

또는 `TOctree2<T, Semantics>` 직접 — [[sources/ue-spatialpartition-toctree2]] ⭐⭐⭐.

## 5. 결정 트리

```
"검색하고 싶다" →
├─ 매 프레임 / Tick / 콜백?     → 등록 패턴 (Subsystem) 의무
├─ 디스크 에셋?                → AssetRegistry
├─ 메모리 안 액터 (단일 World)?  → UWorld::PersistentLevel->Actors / GameStateBase::PlayerArray
├─ 메모리 안 UObject?          → Subsystem 등록 / GameInstanceSubsystem 캐시
├─ 위치 기반 (반경 / 시야)?     → OverlapMulti / TOctree2
└─ 모두 부적절 + 1회 / Editor?  → TObjectIterator/TActorIterator (§6 조건 만족)
```

## 6. 최후의 수단 — 허용 5조건 🟡

모두 만족 시에만 사용:

1. **빈도 매우 낮음** — 게임 시작 1회 / 사용자 명시 트리거 / 에디터만
2. **다른 대안 부적절** — Subsystem 등록 어려움 (외부 플러그인 액터)
3. 🚨 **`TRACE_CPUPROFILER_EVENT_SCOPE` 의무** — [[sources/ue-ref-07-profilingscopeRule]]
4. **명시적 주석** — 왜 / 빈도 / 다른 대안 X
5. **`#if WITH_EDITOR` 가드 (가능 시)**

```cpp
#if WITH_EDITOR
void UMyEditorTool::FindAllInvalidAssets()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyEditorTool_FindAllInvalid);
    // 사유: AssetRegistry 로는 bIsDirty 등 메모리 상태 알 수 없어 사용
    // 빈도: 사용자 메뉴 클릭 1회, 에디터 전용
    for (TObjectIterator<UMyAsset> It; It; ++It)
        if (It->IsValidationFailing()) { /* ... */ }
}
#endif
```

### 6.1. 허용 케이스 7

| 케이스 | 빈도 | 가드 |
| -- | -- | -- |
| 에디터 도구 (Validate Project 사용자 클릭) | 1회 | `WITH_EDITOR` |
| 디버그 콘솔 (`DumpAllPawns`) | 사용자 명시 | (선택) |
| Save/Load 마이그레이션 (5.0→5.1) | 1회 | Cook 시점 |
| Cook 시점 처리 (`CommandletMain`) | 빌드 1회 | `IsRunningCommandlet()` |
| 게임 시작 1회 — 외부 플러그인 액터 | BeginPlay 1회 | (없음) |
| Automation Test 무결성 검증 | 테스트 1회 | (테스트 빌드) |
| 메모리 Leak 추적 | 명시 호출 | `WITH_EDITOR` |

## 7. 측정 / 디버깅

```cpp
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyClass_ScanAllAssets);
    const double Start = FPlatformTime::Seconds();
    int32 Count = 0;
    for (TObjectIterator<UMyAsset> It; It; ++It) { Count++; }
    UE_LOG(LogTemp, Warning, TEXT("Scanned %d in %.2fms"), Count, (FPlatformTime::Seconds()-Start)*1000.0);
}
```

게임 빌드 50ms+ → **즉시 대안 검토**. 콘솔: `obj list class=AMyEnemy` / `stat unit`.

## 8. 체크리스트

- [ ] `TActorIterator` / `TObjectIterator` / `*Range` 사용 **먼저 의심**
- [ ] 매 프레임·Tick·콜백 안 사용 → **즉시 등록 패턴 대체**
- [ ] 메모리 안 객체 검색 → Subsystem / AssetRegistry / Spatial 우선
- [ ] 정말 불가피 → §6 5조건 만족 + `TRACE_CPUPROFILER_EVENT_SCOPE` + 주석 + `#if WITH_EDITOR` (가능 시)

## 9. Cross-link

- 권위 concept: [[concepts/Global-Iterator-Avoidance]] · [[concepts/Subsystem-5-Types]]
- 자매 정책 hub: [[sources/ue-ref-07-profilingscopeRule]] (사용 시 의무) · [[sources/ue-ref-10-componentpolicies]] · [[sources/ue-ref-11-assetloadingpolicy]] · [[sources/ue-ref-12-assetoptimizationpolicy]]
- 대안 source: [[sources/ue-editor-assetregistry]] (디스크 검색) · [[sources/ue-subsystem-skill]] (Subsystem 등록 패턴) · [[sources/ue-spatialpartition-toctree2]] ⭐⭐⭐ (Octree 반경) · [[sources/ue-spatialpartition-skill]] (4 sub-skill)
- 카테고리 main 적용: [[sources/ue-components-skill]] · [[sources/ue-gameframework-skill]] · [[sources/ue-editor-skill]]
- MC-시리즈: [[synthesis/mc-actor-spawn-subsystem-implementation]] (KMCProject UMCActorSpawnSubsystem — 본 정책 적용)
- Significance 통합: [[sources/ue-significance-skill]] (자기 자신이 등록 패턴)
