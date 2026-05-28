---
name: coreuobject-main
description: Tier 1 CoreUObject 모듈 메인 — UObject + Reflection + Property + Package + Interface + GC + Serialization + Network + Editor 🛠 + Cooking 🛠 + StructUtils + ObjectHandles + DeprecatedUProperty 13개 sub-skill 인덱스. 모든 UObject 자손 코드 작성의 베이스.
---

# CoreUObject — 모듈 진입점

> Tier 1 · L2 (UObject·직렬화·리플렉션) · UE 5.5.4 기준
> 위치: `Engine/Source/Runtime/CoreUObject/`
> 의존: **Public** Core, TraceLog, CorePreciseFP / **Private** AutoRTFM, Projects, Json (편집기/서버 빌드 시 DerivedDataCache 추가)
> 출처: `CoreUObject.Build.cs` 직접 확인
>
> **상위 인덱스**: [`../references/03_WikiHarness.md`](../../references/03_WikiHarness.md) 의 시나리오 표가 어떤 sub-skill을 묶어 읽을지 알려준다. `CLAUDE.md §11` 의 빠른 표도 동일.

---

## 1. 개요

`CoreUObject`는 `Core`(컨테이너/메모리/스레드) 위에 **객체 시스템·리플렉션·GC·직렬화·패키지 로딩**을 얹는 모듈로, 거의 모든 게임플레이/엔진/에디터 모듈이 이 위에 쌓인다. 이 모듈에는 **63개의 UCLASS**가 정의되어 있고, 기능 응집도가 명확히 구분되므로 본 위키에서는 모듈 전체를 13개 **sub-skill**로 분할해 다룬다.

이 문서(메인 SKILL.md)는 모듈 진입점만 제공한다 — 의존·자주 쓰는 API의 큰 그림 → sub-skill 인덱스 → 관련 모듈. 각 클래스/함수의 상세, virtual override 포인트, 라이프사이클, 예제는 sub-skill 안에서 다룬다.

---

## 2. 의존·빌드 (`CoreUObject.Build.cs` 요약)

```text
PublicDependencyModuleNames  : Core, TraceLog, CorePreciseFP
PrivateDependencyModuleNames : AutoRTFM, Projects, Json
                              + DerivedDataCache (Target.bBuildWithEditorOnlyData)
PublicDefinitions            : WITH_VERSE_COMPILER = (Editor or Server) ? 1 : 0
SharedPCHHeaderFile          : Public/CoreUObjectSharedPCH.h
PrivatePCHHeaderFile         : Private/CoreUObjectPrivatePCH.h
```

- `bMinimizeGeneratedIncludes = true` — `*.generated.h` 의 include 최소화로 CoreUObject 내부 순환 의존을 줄임.
- `UnsafeTypeCastWarningLevel = WarningLevel.Error` — 위험한 캐스트는 에러로 처리.

---

## 3. 자주 쓰는 API (1줄 요약 — 상세는 각 sub-skill)

```cpp
// 객체 생성/검색/로드 (UObjectGlobals.h)
UMyComp* C = NewObject<UMyComp>(Owner, UMyComp::StaticClass(), TEXT("Health"));
UTexture2D* T = LoadObject<UTexture2D>(nullptr, TEXT("/Game/UI/Logo.Logo"));
UMyActor* A = FindObject<UMyActor>(World, TEXT("PlayerStart_0"));

// 캐스팅 (Templates/Casts.h)
if (UMyComp* M = Cast<UMyComp>(Comp)) { ... }
UPawn* P = CastChecked<UPawn>(SomeActor);

// 핸들 (UObject/ObjectPtr.h, WeakObjectPtr.h, SoftObjectPtr.h, StrongObjectPtr.h)
UPROPERTY() TObjectPtr<USkeletalMesh> Mesh;
TWeakObjectPtr<APlayerController> WeakPC = PC;
TStrongObjectPtr<UMyData> Pinned(NewObject<UMyData>());

// 가비지 컬렉션 (UObjectGlobals.h)
CollectGarbage(RF_NoFlags, /*bPerformFullPurge=*/true);
```

상세 시그니처·오버로드·사용 패턴은 다음 sub-skill에서 다룬다.

---

## 4. 사용 예제 (UCLASS 골격)

```cpp
// MyHealthComponent.h
#pragma once
#include "Components/ActorComponent.h"
#include "MyHealthComponent.generated.h"

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class MYGAME_API UMyHealthComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UMyHealthComponent();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Health")
    float MaxHealth = 100.f;

    UFUNCTION(BlueprintCallable, Category="Health")
    void ApplyDamage(float Amount);
};
```

- `GENERATED_BODY()` 가 UnrealHeaderTool 생성 코드와의 접점.
- `UCLASS`/`UPROPERTY`/`UFUNCTION` 메타가 그대로 `UClass`·`FProperty`·`UFunction` 메타데이터로 등록된다 (자세한 매크로·UHT 흐름은 `Reflection/SKILL.md`).

---

## 5. Sub-skill 인덱스

CoreUObject 내부의 클래스·virtual·예제는 다음 13개 sub-skill로 분산되어 있다. 각 sub-skill은 *개요 → 핵심 헤더/클래스 → 자주 쓰는 API → virtual 오버라이드 포인트 → 예제 → 관련 sub-skill* 의 일관 구조를 따른다.

| # | Sub-skill | 다루는 영역 | 주요 클래스/심볼 |
|---|-----------|-------------|------------------|
| 1 | [`UObject/`](./UObject/SKILL.md) | UObject 본체와 라이프사이클 | `UObjectBase`, `UObjectBaseUtility`, `UObject`, PostInit/PostLoad/BeginDestroy/FinishDestroy virtual |
| 2 | [`Reflection/`](./Reflection/SKILL.md) | 리플렉션 메타 객체 | `UField`/`UStruct`/`UScriptStruct`/`UFunction`/`UDelegateFunction`/`USparseDelegateFunction`/`UEnum`/`UClass` + Verse 변형 4 + `UPROPERTY`/`UCLASS`/`UFUNCTION`/`USTRUCT`/`UENUM` 매크로 + `UObjectIterator` |
| 3 | [`Property/`](./Property/SKILL.md) | 프로퍼티 시스템 | `FField`/`FProperty`/`FObjectProperty`/`FStructProperty`/`FArrayProperty` 등 + `CastField` + `TFieldIterator` + `UPropertyWrapper` 3 + PURE_VIRTUAL |
| 4 | [`Package/`](./Package/SKILL.md) | 패키지·링커·저장 | `UPackage`, `FLinkerLoad`, `FLinkerSave`, `FPackageFileSummary`, `SavePackage`, `FPackagePath` |
| 5 | [`Interface/`](./Interface/SKILL.md) | UInterface 패턴 | `UInterface`, `IInterface` 패턴, `TScriptInterface<T>`, `UEditorPathObjectInterface` |
| 6 | [`GC/`](./GC/SKILL.md) | 가비지 컬렉션 | `UGCObjectReferencer`, `FGCObject`, `FReferenceCollector`, `FFastReferenceCollector`, `CollectGarbage`, 클러스터, MarkAsGarbage, GC virtual |
| 7 | [`Serialization/`](./Serialization/SKILL.md) | 직렬화·BulkData·Async 로딩 | `FArchiveUObject`, `FObjectReader`/`FObjectWriter`, `FBulkData*`, `AsyncLoading2.h`, `UObject::Serialize` 및 PreSave/PostSave virtual |
| 8 | [`Network/`](./Network/SKILL.md) | 네트워크 복제 통합 | `UPackageMap`, `GetLifetimeReplicatedProps`, `PreNetReceive`/`PostNetReceive`, `IsSupportedForNetworking`, `RegisterReplicationFragments` |
| 9 | [`Editor/`](./Editor/SKILL.md) | 에디터 콜백·트랜잭션 | `PreEditChange`/`PostEditChangeProperty`, `Modify`, `PreEditUndo`/`PostEditUndo`, `IsSelectedInEditor`, 에셋 메타 virtual |
| 10 | [`Cooking/`](./Cooking/SKILL.md) | 쿠킹·플랫폼 게이팅·메타 보존 | `NeedsLoadFor*`/`IsEditorOnly` virtual, `BeginCacheForCookedPlatformData`, `UEnumCookedMetaData`/`UStructCookedMetaData`/`UClassCookedMetaData`, `UObjectRedirector`, `UDEPRECATED_MetaData` |
| 11 | [`StructUtils/`](./StructUtils/SKILL.md) | 동적 USTRUCT / 인스턴스드 구조 | `UPropertyBag`, `UUserDefinedStruct`, `UPropertyBagMissingObject`, `UUserDefinedStructEditorDataBase`, `FInstancedStruct`, `FSharedStruct`, `FStructView` |
| 12 | [`ObjectHandles/`](./ObjectHandles/SKILL.md) | 객체 핸들·경로 식별자 | `TObjectPtr<T>`, `TWeakObjectPtr<T>`, `TSoftObjectPtr<T>`, `TStrongObjectPtr<T>`, `TLazyObjectPtr<T>`, `FSoftObjectPath`, `FTopLevelAssetPath`, `FPrimaryAssetId` |
| 13 | [`DeprecatedUProperty/`](./DeprecatedUProperty/SKILL.md) | 4.25 이전 UProperty 미러 | `UnrealTypePrivate.h`의 33개 `UProperty` 자손 + `FProperty`로의 마이그레이션 가이드 |

> 모듈 안에서 어떤 영역이 필요한지 모를 때는 위 표의 "다루는 영역"에서 키워드를 검색하면 된다. `Reflection/`과 `Property/`는 자주 함께 참조되며, `GC/`는 `Serialization/` 의 `Serialize` 동작과 짝지어 본다.

---

## 6. 관련 모듈

- **상위 (의존됨)**: `Engine`, `BlueprintRuntime`, `AssetRegistry`, 거의 모든 게임플레이 모듈.
- **하위 (의존)**: `Core`, `TraceLog`, `CorePreciseFP` (Public) / `AutoRTFM`, `Projects`, `Json` (Private).
- **연계**: `AssetRegistry`(에셋 메타 인덱스), `GameplayTags`(태그 시스템 — `FName`·UStruct 기반), `Json`/`JsonUtilities`(UStruct ↔ JSON), `Serialization`(FArchive 확장 유틸).
- **에디터/개발 보조**: 에디터 빌드에서 `DerivedDataCache`가 추가 의존으로 들어가며, Editor 모듈에서 UPROPERTY 메타 기반 디테일 패널을 구성한다.

---

## 7. 작성·인용 규칙 (모든 sub-skill 공통)

1. 사실 인용은 5.5.4 트리(`C:\Unreal\UnrealEngine\Engine\Source\Runtime\CoreUObject`)의 실제 헤더에서 grep으로 검증한 라인 번호를 (`헤더:라인`) 형식으로 표기.
2. 추측은 명시("추정") 또는 생략. UPropertyBag 같은 비정상적 구조는 ⚠로 표기.
3. UE 4.25 이전의 UProperty 계열은 deprecated이므로 신규 코드 가이드에서는 항상 `FProperty`를 쓰도록 안내.
4. 라인 번호는 마이너 패치/Verse 갱신에 따라 ±수십 라인 이동 가능 — 정확 위치는 헤더에서 재확인.

### 7.1 에디터 전용 기능 표기 규칙 🛠

UE에는 **에디터 빌드에만 존재**하는 클래스·멤버·가상 함수가 다수 있다. 쿠킹된 게임 빌드(`UE_BUILD_SHIPPING` 등)에서는 컴파일에서 빠지므로, 게임플레이 코드에서 의존하면 안 된다. 본 위키에서는 이를 다음 규칙으로 표기한다:

- 항목 앞에 **🛠** 마커 — 에디터 빌드에만 존재
- 가드 매크로 명시 — `WITH_EDITOR`(에디터 코드 전체), `WITH_EDITORONLY_DATA`(에디터 전용 멤버), `WITH_EDITOR_DATA_VALIDATION` 등
- 각 sub-skill 마지막에 표준 섹션 **"N. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA)"** 으로 모아서 다시 한 번 인덱스
- 에디터 전용이 전혀 없는 sub-skill은 해당 섹션에 "없음" 한 줄

대표 예:

| 카테고리 | 예시 |
|---------|------|
| 에디터 콜백 virtual | `PreEditChange`, `PostEditChangeProperty`, `PostEditUndo`, `IsSelectedInEditor` |
| 에디터 전용 직렬화 | `EditorBulkData`, `DerivedData`, `EditorBulkDataReader/Writer` |
| 에디터 전용 메타 | `GetAssetRegistryTags`, `IsDataValid` |
| 에디터 전용 프로퍼티 | `UPROPERTY(EditAnywhere ...)` 의 메타데이터 일부 |
| 에디터 전용 헤더 | `#if WITH_EDITOR ... #endif` 가드된 함수 선언 |

전반적인 에디터 콜백·트랜잭션 흐름은 [`Editor/SKILL.md`](./Editor/SKILL.md) 에 모여 있으며, 다른 sub-skill의 에디터 전용 항목도 거기서 cross-reference 인덱스로 다시 모아 본다.
