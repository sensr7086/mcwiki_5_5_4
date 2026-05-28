---
name: coreuobject-gc
description: Garbage Collection 시스템 - CollectGarbage + IncrementalGC + MarkAsGarbage + IsValid + AddReferencedObject + FGCObject + FReferenceCollector + FReferenceChainSearch.
---

# CoreUObject / GC (Garbage Collection)

> 부모 모듈: [`CoreUObject`](../SKILL.md) · UE 5.7.4
> 다루는 영역: 가비지 컬렉션 — `UGCObjectReferencer`, `FGCObject`, `FReferenceCollector`, `CollectGarbage`, 클러스터, GC virtual hook
> 관련 sub-skill: [`UObject/`](../UObject/SKILL.md), [`ObjectHandles/`](../ObjectHandles/SKILL.md), [`Reflection/`](../Reflection/SKILL.md), [`Property/`](../Property/SKILL.md)

---

## 1. 개요

UE의 GC는 **마크앤스윕 + 토큰 스트림(빠른 참조 수집)** 의 결합이다. UPROPERTY 메타로부터 컴파일 타임에 토큰 스트림이 생성돼, 멀티스레드로 객체 그래프를 빠르게 마크한다. 그래프에서 도달 못 하는 객체는 다음 사이클에 회수.

핵심 원칙:

1. **UPROPERTY 멤버는 자동 추적**. UCLASS의 `static AddReferencedObjects` 가 UHT 생성 코드로 채워진다.
2. **UPROPERTY가 아닌 raw `UObject*`** 는 GC가 못 본다 → `TStrongObjectPtr` 또는 `FGCObject` 상속이 필요.
3. **`MarkAsGarbage()`** 로 즉시 폐기 표시 → 다음 GC 사이클에 회수.
4. **GC는 메인 스레드 stop-the-world 단계가 있다**. 워커 스레드에서 `UObject*` 보유 금지.

---

## 2. 핵심 헤더와 클래스

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/UObject/UObjectGlobals.h` | `CollectGarbage(EObjectFlags, bool=true)` (L930), `TryCollectGarbage(...)` (L940), `class FReferenceCollector` (L2491) | GC 진입점 + 참조 수집 인터페이스. |
| `Public/UObject/GCObject.h` | `class FGCObject` (L127), `UGCObjectReferencer` (L28) | 비-UObject가 UObject 참조를 GC에 알리는 다리. |
| `Public/UObject/GCObjectScopeGuard.h` | `TGCObjectScopeGuard<T>`, `FGCObjectScopeGuard` | 스코프 동안 단일 객체를 GC로부터 보호. `TStrongObjectPtr`의 lean 버전. |
| `Public/UObject/GarbageCollection.h` | `RegisterSlowImplementation(...)` (L59), `EAROFlags`, `IsGarbageCollectingAndLockingUObjectHashTables()` (L207) | GC 내부 구성. |
| `Public/UObject/GarbageCollectionGlobals.h` | GC 옵션 전역 | 임계값·디버그 토글. |
| `Public/UObject/GarbageCollectionSchema.h` | 토큰 스트림 스키마 | UHT 생성과 짝. |
| `Public/UObject/GarbageCollectionHistory.h` | GC 히스토리(디버그) | `ENABLE_GC_HISTORY` 가드. |
| `Public/UObject/FastReferenceCollector.h` | `FFastReferenceCollector`, `UE::GC::FWorkCoordinator`/`FWorkerContext` | 멀티스레드 수집기 본체. 일반 코드에서 직접 호출 안 함. |
| `Public/UObject/UObjectClusters.h` | `FUObjectCluster`, `DumpClusterToLog(...)` (L22) | 클러스터 GC. |
| `Public/UObject/UObjectAnnotation.h` | `FUObjectAnnotationSparse`, `FUObjectAnnotationDense` | 객체별 외부 데이터(annotation). |
| `Public/UObject/ReachabilityAnalysis.h` | 도달성 분석 도우미 | GC 흐름 일부. |
| `Public/UObject/ReferenceChainSearch.h` | `FReferenceChainSearch` | "왜 이 객체가 살아있나?" 디버깅. |
| `Public/UObject/UObjectBaseUtility.h` | `MarkAsGarbage()` (L182), `CanBeClusterRoot()` (L396), `OnClusterMarkedAsPendingKill()` (L416) | 객체별 GC 훅. |

---

## 3. 자주 쓰는 API

```cpp
// === GC 실행 ===
CollectGarbage(/*KeepFlags=*/RF_NoFlags, /*bPerformFullPurge=*/true);
bool bDone = TryCollectGarbage(RF_NoFlags, true);
bool bIsGCing = IsGarbageCollectingAndLockingUObjectHashTables();   // GarbageCollection.h:207

// === 객체 폐기 표시 ===
MyObj->MarkAsGarbage();               // UObjectBaseUtility.h:182 — 다음 GC 사이클에 회수
// (5.x에서 MarkPendingKill 은 deprecated, MarkAsGarbage 권장)

// === GC 보호 (UPROPERTY 외부) ===
TStrongObjectPtr<UMyData> Pinned(NewObject<UMyData>());   // ObjectHandles/SKILL.md
// 또는 스코프 한정:
{
    FGCObjectScopeGuard Guard(MyObj);                      // GCObjectScopeGuard.h
    // 이 스코프 동안 MyObj는 GC 보호
}

// === FGCObject 상속 (영구 보호) ===
class FMyTool : public FGCObject
{
    UMyAsset* Cached = nullptr;
    virtual void AddReferencedObjects(FReferenceCollector& C) override
    {
        C.AddReferencedObject(Cached);
    }
    virtual FString GetReferencerName() const override { return TEXT("FMyTool"); }
};

// === 디버그: 어떤 사슬로 살아있는지 추적 ===
FReferenceChainSearch Search(MyObj, EReferenceChainSearchMode::Shortest);
Search.PrintResults();                                     // ReferenceChainSearch.h
```

### 3.1 FReferenceCollector 권장 메서드 (`UObjectGlobals.h:2491~`)

배치 수집을 활용해 더 빠르다 — **stable** (오랜 라이프타임)인 참조에 사용:

```cpp
// 권장: 배치 가능 (객체가 GC tracing보다 오래 살아야 함)
virtual void AddStableReference(TObjectPtr<UObject>* Object);                          // L2497
virtual void AddStableReferenceArray(TArray<TObjectPtr<UObject>>* Objects);            // L2500
virtual void AddStableReferenceSet(TSet<TObjectPtr<UObject>>* Objects);                // L2503
template <...> void AddStableReferenceMap(TMap<...>& Map);                             // L2506

// 임시/스택 참조용: AddReferencedObject(...) (호환 인터페이스)
Collector.AddReferencedObject(MyObj);
Collector.AddReferencedObjects(MyArrayOfObjects);
```

> 가능하면 멤버를 `TObjectPtr<T>` 로 두고 `AddStableReference` 를 쓰면 GC 코스트가 줄어든다.

---

## 4. 가상 함수 (오버라이드 포인트)

### 4.1 FGCObject (`GCObject.h`)

| 시그니처 | 위치 | 의미 |
|----------|------|------|
| `virtual void AddReferencedObjects(FReferenceCollector&) = 0` | GCObject.h L195 | 모든 보유 UObject를 등록. 누락 시 GC가 회수 → 댕글링. |
| `virtual FString GetReferencerName() const = 0` | GCObject.h L198 | 디버그·리포트 이름. |
| `virtual bool GetReferencerPropertyName(UObject*, FString&) const` | GCObject.h L201 | 어느 멤버가 객체를 잡고 있는지 (선택적). |
| `virtual ~FGCObject()` | GCObject.h L175 | 자동 GC 등록 해제. |
| `virtual void FinishDestroy() override` | GCObject.h L83 | (UGCObjectReferencer 측) |

### 4.2 UCLASS의 GC 통합 — static (virtual 아님)

```cpp
// UObject::AddReferencedObjects 는 virtual이 아니라 static — UHT가 UCLASS마다 채운다.
static COREUOBJECT_API void AddReferencedObjects(UObject* InThis, FReferenceCollector& Collector);
//   Object.h:786, UStruct에서도 Class.h:629
```

UPROPERTY 가 아닌 raw `UObject*` 멤버를 GC가 추적하게 하려면 클래스 안에 다음 패턴을 넣는다 (UHT가 base 호출도 자동 합성):

```cpp
UCLASS()
class UMyHolder : public UObject
{
    GENERATED_BODY()
public:
    // UPROPERTY 아닌 raw 포인터
    UObject* HiddenRef = nullptr;

    static void AddReferencedObjects(UObject* InThis, FReferenceCollector& Collector)
    {
        UMyHolder* This = CastChecked<UMyHolder>(InThis);
        Super::AddReferencedObjects(InThis, Collector);
        Collector.AddReferencedObject(This->HiddenRef);
    }
};
```

> 가능하면 그냥 `UPROPERTY()` 로 만드는 게 더 안전하고 빠르다 (UHT가 자동으로 토큰 스트림에 넣어 batched).

### 4.3 클러스터 GC (`UObjectBaseUtility.h`)

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual bool CanBeClusterRoot() const` | UObjectBaseUtility.h L396 | 이 객체가 GC 클러스터의 루트가 될 수 있는지. (ex. 큰 에셋 — 텍스처/사운드/스태틱메시) |
| `virtual void OnClusterMarkedAsPendingKill()` | UObjectBaseUtility.h L416 | 클러스터 회수 통지. |

클러스터는 함께 살고 함께 죽는 객체 묶음으로 GC 비용을 줄인다. 일반 게임 코드에서 직접 만들 일은 거의 없다.

---

## 5. 예제

### 5.1 비-UObject 매니저가 UObject 캐시 보유

```cpp
class FAssetCache : public FGCObject
{
public:
    void Add(FName Key, UObject* Asset) { Map.Add(Key, Asset); }
    UObject* Find(FName Key)            { return Map.FindRef(Key); }

    //~ FGCObject
    virtual void AddReferencedObjects(FReferenceCollector& C) override
    {
        // TObjectPtr 권장: AddStableReferenceMap도 사용 가능
        for (auto& Pair : Map) C.AddReferencedObject(Pair.Value);
    }
    virtual FString GetReferencerName() const override { return TEXT("FAssetCache"); }

private:
    TMap<FName, UObject*> Map;
};
```

### 5.2 스코프 동안만 보호

```cpp
void DoAsyncWork(UMyData* Data)
{
    // 비동기 작업 동안 Data가 GC되지 않도록 가드
    auto Guard = MakeShared<FGCObjectScopeGuard>(Data);
    AsyncTask(ENamedThreads::AnyThread, [Guard]()
    {
        // 여기서는 메인 스레드 아니므로 Data를 직접 만지지 말 것
        // 데이터의 일부 값을 미리 캡처해서 사용
    });
    // Guard가 살아있는 한 Data는 보호됨
}
```

### 5.3 객체 즉시 폐기

```cpp
if (UMyTemp* T = NewObject<UMyTemp>())
{
    T->DoOneShot();
    T->MarkAsGarbage();        // 다음 GC 사이클에 회수
}
// 즉시 회수가 필요하면:
CollectGarbage(RF_NoFlags, /*bPerformFullPurge=*/true);
```

### 5.4 왜 이 객체가 살아있나? (디버그)

```cpp
FReferenceChainSearch Search(SuspiciousObj, EReferenceChainSearchMode::Shortest | EReferenceChainSearchMode::PrintResults);
// 로그에 참조 사슬이 출력됨
```

---

## 6. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `EnableFrankenGCMode(bool)` 🛠 | GarbageCollection.h L93 | 디버그·실험적 | 일반 게임 코드 안 씀. |
| `ShouldFrankenGCRun()` 🛠 | GarbageCollection.h L98 | 동상 | |
| `FReferenceChainSearch` 🛠 (실용적으로) | ReferenceChainSearch.h | 런타임에도 존재하지만 보통 에디터/디버그 빌드 | 런타임 비용이 매우 큼. |
| `GarbageCollectionHistory.h` 🛠 | (헤더 전체) | `ENABLE_GC_HISTORY` (디버그 빌드만 1) | GC 결과 히스토리 로깅. |
| `DumpClusterToLog(...)` 🛠 | UObjectClusters.h L22 | 디버그 | |
| `BeginCacheForCookedPlatformData(...)` 🛠 (간접) | Object.h L1211 | `WITH_EDITOR` | 쿠킹 시 파생 데이터 빌드 — [`Cooking/`](../Cooking/SKILL.md). |

> 게임 런타임에서 정상 동작하는 GC API는 `CollectGarbage`/`MarkAsGarbage`/`FGCObject`/`TStrongObjectPtr`/`TGCObjectScopeGuard` 정도. 나머지는 에디터·디버그 보조다.

---

## 7. 관련 sub-skill

- [`UObject/`](../UObject/SKILL.md) — `BeginDestroy`/`FinishDestroy` 라이프사이클이 GC와 어떻게 짝지어지는가
- [`ObjectHandles/`](../ObjectHandles/SKILL.md) — `TWeakObjectPtr`/`TStrongObjectPtr` 와 GC의 상호작용
- [`Reflection/`](../Reflection/SKILL.md) — UCLASS의 `static AddReferencedObjects` 합성
- [`Property/`](../Property/SKILL.md) — `FProperty::ContainsObjectReference` 가 만드는 GC 토큰
