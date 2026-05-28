---
name: coreuobject-uobject
description: UObject 베이스 클래스 - 라이프사이클 (PostInitProperties/PostLoad/BeginDestroy/FinalizeDestroy) + Super 호출 규약 + ConstructObject vs NewObject + ProcessEvent + 생성자 패턴.
---

# CoreUObject / UObject

> 부모 모듈: [`CoreUObject`](../SKILL.md) · UE 5.5.4
> 다루는 영역: `UObjectBase` → `UObjectBaseUtility` → `UObject` 본체와 라이프사이클 가상 함수
> 관련 sub-skill: [`Reflection/`](../Reflection/SKILL.md), [`GC/`](../GC/SKILL.md), [`Serialization/`](../Serialization/SKILL.md), [`ObjectHandles/`](../ObjectHandles/SKILL.md)

---

## 1. 개요

UE의 모든 게임플레이/에디터 객체는 `UObject`를 루트로 하는 사슬에서 출발한다. 베이스 사슬은 다음 3단계:

```
UObjectBase           (Public/UObject/UObjectBase.h:41)         ← UCLASS 아님, 순수 C++
  └─ UObjectBaseUtility (Public/UObject/UObjectBaseUtility.h:45) ← UCLASS 아님, 헬퍼 묶음
       └─ UObject       (Public/UObject/Object.h:91)             ← 모든 UCLASS의 루트
```

`UObjectBase`는 GENERATED_BODY 없이 직접 멤버를 들고 있고(클래스 포인터·Outer·Name·Index·플래그), `UObjectBaseUtility`는 `GetName/GetPathName/IsA/GetOuter` 같은 헬퍼만 묶어 둔 중간층이다. `UObject`는 게임플레이가 사용하는 표준 인터페이스(`Serialize`, `PostLoad`, `BeginDestroy` 등 가상 함수와 매크로 기반 리플렉션 진입점)를 제공한다.

---

## 2. 핵심 헤더와 클래스

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/UObject/UObjectBase.h` | `UObjectBase` (L58) | UClass 포인터·Outer·FName·내부 인덱스·`EObjectFlags` 보유. 컴파일 등록(`UObjectForceRegistration` L477, `RegisterCompiledInInfo` L525)도 여기. |
| `Public/UObject/UObjectBaseUtility.h` | `UObjectBaseUtility` (L44) | `GetName/GetPathName/GetOuter/IsA<T>/GetTypedOuter<T>` 등 사용 헬퍼. `MarkAsGarbage()` (L182), `CanBeClusterRoot()` (L396) 도 여기. |
| `Public/UObject/Object.h` | `UObject` (L94, `: public UObjectBaseUtility`) | 표준 라이프사이클·직렬화·에디터 콜백 가상 함수 + `ProcessEvent`. |
| `Public/UObject/UObjectGlobals.h` | `NewObject<T>` (L1891·L1919·L1934), `StaticConstructObject_Internal`, `LoadObject<T>` (L2135), `FindObject<T>` (L2037) | 생성/검색/로드 진입점. (검색·로드 자체는 `Package/SKILL.md`에서 더 자세히.) |
| `Public/UObject/ObjectMacros.h` | `EObjectFlags` (`RF_*`), `ENewObjectFlags` | 객체 플래그 정의. (UCLASS/UPROPERTY 매크로 자체는 `Reflection/`에서 다룸.) |

### 2.1 EObjectFlags 핵심 비트

`ObjectMacros.h` 정의의 자주 쓰는 비트:

- `RF_NoFlags = 0` — 기본
- `RF_Public` / `RF_Standalone` — 외부 참조 가능 / 단독 보관(에셋 직접)
- `RF_Transient` — 직렬화 제외 (런타임 임시)
- `RF_Transactional` — Undo 트랜잭션 추적 대상
- `RF_ClassDefaultObject` — CDO 자체에 붙음
- `RF_ArchetypeObject` — 인스턴싱 템플릿
- `RF_NeedLoad`/`RF_NeedPostLoad` — 로딩 진행 상태
- `RF_MirroredGarbage` — `MarkAsGarbage()`의 GC 마크 미러

> ⚠ `RF_MirroredGarbage`는 `SetFlags()` 로 직접 세팅 금지 — `MarkAsGarbage()` 만 사용. (`UObjectBaseUtility.h:75` 의 `checkf` 메시지로 강제됨.)

---

## 3. 자주 쓰는 API

```cpp
// 생성 (가장 표준)
UMyComp* C = NewObject<UMyComp>(/*Outer=*/Owner,
                                /*Class=*/UMyComp::StaticClass(),
                                /*Name=*/TEXT("Health"),
                                /*Flags=*/RF_Transactional);

// Outer 생략 시 transient package
UMyData* D = NewObject<UMyData>();      // → Outer = GetTransientPackageAsObject()

// 정보 조회 (UObjectBaseUtility)
FString Name      = D->GetName();        // "MyData_0"
FString Path      = D->GetPathName();    // "/Engine/Transient.MyData_0"
UClass* Cls       = D->GetClass();       // UMyData::StaticClass()
UObject* Outer    = D->GetOuter();
UWorld*  World    = D->GetWorld();       // virtual — 객체별 override

// 플래그 조작
D->SetFlags(RF_Transactional);
bool bAsset = D->HasAnyFlags(RF_Standalone | RF_Public);

// 파괴 (GC에 위임)
D->MarkAsGarbage();                      // 다음 GC 사이클에 회수
// CollectGarbage()는 GC sub-skill 참조
```

`StaticConstructObject_Internal`은 일반 코드에서 직접 호출하지 않는다 — 항상 `NewObject<T>` 템플릿을 통한다.

---

## 4. 가상 함수 (라이프사이클 — 가장 자주 override)

| 시그니처 | 위치 | 호출 시점 / 용도 |
|----------|------|------------------|
| `virtual void PostInitProperties()` | Object.h L222 | 생성자 종료 후 UPROPERTY 기본값까지 적용된 직후. **파생 멤버 초기화 권장 위치**. |
| `virtual void PostReinitProperties()` | Object.h L228 | CDO 재초기화/HotReload 등 프로퍼티 재적용 시. |
| `virtual void PostCDOContruct()` | Object.h L234 | CDO 생성 후. (엔진 표기 그대로 — `Construct` ≠ `Contruct`.) |
| `virtual void PostCDOCompiled(const FPostCDOCompiledContext&)` | Object.h L246 | 블루프린트 CDO 컴파일 종료 후. |
| `virtual bool IsReadyForAsyncPostLoad() const` | Object.h L345 | true 반환 시 비동기 PostLoad 진행. |
| `virtual void PostLoad()` | Object.h L351 | 디스크 로드 완료 + 모든 참조 해소 후. **에셋 마이그레이션·버전 업그레이드의 표준 위치**. |
| `virtual void PostLoadSubobjects(FObjectInstancingGraph*)` | Object.h L360 | 서브오브젝트까지 로드 후. 인스턴싱 그래프 보정. |
| `virtual void BeginDestroy()` | Object.h L366 | **파괴 1단계** — 비동기 작업 취소·외부 핸들 해제. **반드시 `Super::BeginDestroy()` 호출 (마지막에)**. |
| `virtual bool IsReadyForFinishDestroy()` | Object.h L373 | 비동기 정리 미완 시 false → GC가 다음 사이클로 미룸. |
| `virtual void FinishDestroy()` | Object.h L387 | 파괴 2단계 — 메모리 해제 직전 마지막 정리. |
| `virtual void ShutdownAfterError()` | Object.h L420 | 엔진 비정상 종료 경로용. |

### 4.1 일반 / 월드 통합

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual UWorld* GetWorld() const` | Object.h L719 | 객체가 속한 월드 반환. **컴포넌트/위젯/서브시스템에서 자주 override**. |
| `virtual bool ImplementsGetWorld() const` | Object.h L726 | GetWorld가 의미 있는 값을 반환하는지(에디터 트레이스용). |
| `virtual void GetResourceSizeEx(FResourceSizeEx&)` | Object.h L754 | 메모리 통계용 크기 보고. |
| `virtual FString GetDesc()` | Object.h L704 | 에디터 트리뷰의 짧은 설명 문자열. |
| `virtual bool CheckDefaultSubobjectsInternal() const` | Object.h L1785 | 기본 서브오브젝트 정합성 체크. |

### 4.2 스크립트 / 콘솔 디스패치

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual void ProcessEvent(UFunction*, void* Parms)` | Object.h L1499 | UFUNCTION 호출 디스패치. RPC/리플리케이션 게이트로 자주 override. |
| `virtual int32 GetFunctionCallspace(UFunction*, FFrame*)` | Object.h L1509 | 함수 호출이 로컬/서버/클라이언트 어디서 실행될지 결정. |
| `virtual bool CallRemoteFunction(UFunction*, void*, FOutParmRec*, FFrame*)` | Object.h L1523 | 원격 호출 송신 훅. (자세한 패턴은 `Network/SKILL.md`.) |
| `virtual bool ProcessConsoleExec(const TCHAR*, FOutputDevice&, UObject*)` | Object.h L1544 | 콘솔 명령 라우팅. |

> `Serialize`, `PreSave`, `PostSave*` 등 직렬화 virtual은 [`Serialization/`](../Serialization/SKILL.md)
> `PreEditChange`/`PostEditChangeProperty`/`Modify`/`PostEditUndo` 는 [`Editor/`](../Editor/SKILL.md)
> `GetLifetimeReplicatedProps`/`PreNetReceive` 는 [`Network/`](../Network/SKILL.md)
> `NeedsLoadFor*`/`IsEditorOnly`/`BeginCacheForCookedPlatformData` 는 [`Cooking/`](../Cooking/SKILL.md)
> `AddReferencedObjects`(static) 와 클러스터 virtual 은 [`GC/`](../GC/SKILL.md)

### 4.3 override 패턴 체크리스트

대부분 베이스 호출이 **필수**다 — 누락 시 라이프사이클이 깨진다:

```cpp
void UMyObject::PostInitProperties()  { Super::PostInitProperties();   /* 내 초기화 */ }   // 처음에
void UMyObject::PostLoad()            { Super::PostLoad();             /* 마이그레이션 */ }
void UMyObject::BeginDestroy()        { /* 비동기 취소·핸들 해제 */ Super::BeginDestroy(); } // 마지막에
bool UMyObject::IsReadyForFinishDestroy()
                                      { return Super::IsReadyForFinishDestroy() && bMyAsyncDone; }
void UMyObject::FinishDestroy()       { /* 마지막 정리 */ Super::FinishDestroy(); }
```

생성자에서는 `UPROPERTY` 멤버 기본값만 세팅하고, 외부 의존 초기화는 `PostInitProperties()` 또는 `PostLoad()` 로 미룬다 (디스크에서 읽힐 수도 있고 `NewObject` 로 만들어질 수도 있으므로).

---

## 5. 예제

### 5.1 데이터 객체 정의 + 라이프사이클 hook

```cpp
// MyDataAsset.h
#pragma once
#include "Engine/DataAsset.h"
#include "MyDataAsset.generated.h"

UCLASS(BlueprintType)
class MYGAME_API UMyDataAsset : public UDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, Category="Data")
    int32 Version = 1;

    UPROPERTY(EditAnywhere, Category="Data")
    TArray<FName> Tags;

    // 캐시 — UPROPERTY 아님, 직렬화 안 됨
    TMap<FName, int32> RuntimeIndex;

    virtual void PostInitProperties() override;
    virtual void PostLoad() override;
    virtual void BeginDestroy() override;
};
```

```cpp
// MyDataAsset.cpp
void UMyDataAsset::PostInitProperties()
{
    Super::PostInitProperties();
    // 새로 만든 인스턴스(NewObject) 와 디스크에서 로드된 인스턴스 모두 여기로 옴
    RuntimeIndex.Empty();
    for (int32 i = 0; i < Tags.Num(); ++i) RuntimeIndex.Add(Tags[i], i);
}

void UMyDataAsset::PostLoad()
{
    Super::PostLoad();
    // 옛 버전 마이그레이션 — 디스크에서 올라온 객체에만 호출
    if (Version < 2) { /* 5.5.4 호환 변환 */ Version = 2; }
}

void UMyDataAsset::BeginDestroy()
{
    // 1단계 정리 — 비동기 작업 취소 등
    Super::BeginDestroy();   // 반드시 마지막에
}
```

### 5.2 Outer / GetWorld 패턴

```cpp
// 컴포넌트는 GetWorld()를 Outer 기반으로 구현 (Engine 모듈에서 override됨)
UWorld* UMyHealthComponent::GetWorld() const
{
    if (UObject* Owner = GetOuter()) return Owner->GetWorld();
    return nullptr;
}
```

---

## 6. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

UObject 베이스 자체에서 에디터 빌드에만 의미가 있는 가상 함수와 멤버. 모두 쿠킹된 게임 빌드에서는 빠지거나 no-op이 된다.

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `IsSelectedInEditor()` 🛠 | Object.h L517 | `WITH_EDITOR` | 런타임에서 호출하면 항상 false. |
| `PreEditChange(FProperty*)` 🛠 | Object.h L431 | `WITH_EDITOR` | 디테일 패널 변경 직전 — 상세는 [`Editor/`](../Editor/SKILL.md). |
| `PostEditChangeProperty(...)` 🛠 | Object.h L473 | `WITH_EDITOR` | 디테일 패널 변경 후. |
| `PostEditUndo()` 🛠 | Object.h L488 | `WITH_EDITOR` | Undo 후 호출. |
| `PostTransacted(...)` 🛠 | Object.h L498 | `WITH_EDITOR` | 트랜잭션 적용 후. |
| `Modify(bool)` 🛠 (의미상) | Object.h L308 | (런타임 호환 시그니처지만 실효는 에디터) | 트랜잭션 등록 — 비-에디터에서는 dirty 표시만 의미. |
| `IsCapturingAsRootObjectForTransaction()` 🛠 | Object.h L311 | `WITH_EDITOR` | 트랜잭션 캡처 여부. |
| `LoadedFromAnotherClass(FName)` 🛠 | Object.h L325 | `WITH_EDITOR` | 클래스 이동 호환용 후크. |
| `GetAssetRegistryTags(...)` 🛠 | Object.h L898 / L900 | `WITH_EDITORONLY_DATA` 영향 | 에셋 검색용 태그 — 쿠킹 결과에 일부 포함되지만 수집은 에디터. |
| `IsDataValid(...)` 🛠 | Object.h L1098 / L1101 / L1111 | `WITH_EDITOR` | "Validate Asset" 메뉴와 자동 검증. |
| `BeginCacheForCookedPlatformData(...)` 🛠 | Object.h L1211 | `WITH_EDITOR` | 쿠킹 시 파생 데이터 사전 빌드 — 자세히는 [`Cooking/`](../Cooking/SKILL.md). |
| `IsCachedCookedPlatformDataLoaded(...)` 🛠 | Object.h L1218 | `WITH_EDITOR` | 위 작업 폴링. |

> 게임플레이 코드에서 위 함수들에 의존하지 말 것. 호출이 필요할 때는 반드시 `#if WITH_EDITOR` 로 감싼다.

```cpp
#if WITH_EDITOR
void UMyObject::PostEditChangeProperty(FPropertyChangedEvent& E)
{
    Super::PostEditChangeProperty(E);
    // 디테일 패널에서 값이 변경된 후 — 에디터 빌드에서만 컴파일됨
    RebuildCachedDerivedData();
}
#endif
```

`UPROPERTY` 멤버 자체에 `EditAnywhere`/`VisibleAnywhere`/`Category` 같은 메타가 붙으면 에디터에서 보이는 동작이 달라지지만, 멤버 변수 자체는 쿠킹 빌드에도 존재한다. 멤버 자체를 에디터 빌드에서만 두려면:

```cpp
#if WITH_EDITORONLY_DATA
UPROPERTY(EditAnywhere, Category="Debug")
bool bShowDebugView = false;
#endif
```

---

## 7. 관련 sub-skill

- [`Reflection/`](../Reflection/SKILL.md) — `UClass`/`UStruct`/`UEnum` 등 메타 객체와 `UCLASS`/`UPROPERTY` 매크로
- [`GC/`](../GC/SKILL.md) — `MarkAsGarbage`, `CollectGarbage`, `FGCObject`, GC 라이프사이클의 그림 전체
- [`Serialization/`](../Serialization/SKILL.md) — `Serialize` 가상 함수와 `Ar << X` 패턴
- [`Editor/`](../Editor/SKILL.md) — `PostEditChangeProperty`/`Modify`/`PostEditUndo`
- [`Network/`](../Network/SKILL.md) — `ProcessEvent` 와 `GetFunctionCallspace` 의 RPC 흐름
- [`ObjectHandles/`](../ObjectHandles/SKILL.md) — `TObjectPtr`/`TWeakObjectPtr` 와 `MarkAsGarbage` 의 상호작용
