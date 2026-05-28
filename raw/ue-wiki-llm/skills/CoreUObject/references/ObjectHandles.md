---
name: coreuobject-objecthandles
description: TObjectPtr + TWeakObjectPtr + TSoftObjectPtr + FSoftObjectPath + FPrimaryAssetId + FObjectKey + Lazy Load 패턴.
---

# CoreUObject / ObjectHandles

> 부모 모듈: [`CoreUObject`](../SKILL.md) · UE 5.7.4
> 다루는 영역: UObject 핸들 — `TObjectPtr`/`TWeakObjectPtr`/`TSoftObjectPtr`/`TStrongObjectPtr`/`TLazyObjectPtr` + 경로 식별자 `FSoftObjectPath`/`FTopLevelAssetPath`/`FPrimaryAssetId`/`FObjectKey`
> 관련 sub-skill: [`UObject/`](../UObject/SKILL.md), [`GC/`](../GC/SKILL.md), [`Property/`](../Property/SKILL.md), [`Package/`](../Package/SKILL.md)

---

## 1. 개요

UE에는 UObject를 가리키는 핸들이 다섯 종류 있다. **수명·로딩·GC 동작이 모두 다르다** — 무엇을 쓸지가 코드 품질의 핵심:

| 핸들 | 보유 | GC 동작 | 로딩 | UPROPERTY 권장 |
|------|------|--------|------|----------------|
| `TObjectPtr<T>` | 강(소유) | UPROPERTY 멤버로 추적 | 즉시 (이미 로드된 객체만) | ✅ 멤버 권장형 |
| `TWeakObjectPtr<T>` | 약 | 추적 안 함 (회수해도 OK) | 즉시 (이미 로드) | ❌ 보통 일반 변수 |
| `TStrongObjectPtr<T>` | 강 (UPROPERTY 외부) | `FGCObject` 통해 추적 | 즉시 | ❌ UPROPERTY 외부에서만 |
| `TSoftObjectPtr<T>` | 비-소유 (경로) | 추적 안 함 | **비동기 로드 가능** | ✅ 에셋 참조 권장 |
| `TLazyObjectPtr<T>` | 비-소유 (GUID) | 추적 안 함 | 지연 (액터 GUID) | ⚠ 에디터·Sequencer 위주 |

핵심 규칙:

- **UPROPERTY 멤버** = `TObjectPtr<T>` 또는 `TSoftObjectPtr<T>`.
- **일반 C++ 변수** = `TWeakObjectPtr<T>` 또는 `TStrongObjectPtr<T>`.
- **에셋 참조 (지연 로드 가능해야)** = `TSoftObjectPtr<T>` + `FSoftObjectPath`.
- **고유 식별자 (해시 키)** = `FObjectKey` 또는 `FPrimaryAssetId`.

---

## 2. 핵심 헤더와 클래스

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/UObject/ObjectPtr.h` | `struct FObjectPtr` (L54), `struct TObjectPtr<T>` (L487) | UPROPERTY 권장형. 에디터에선 lazy-resolve, 쿠킹 후 raw로 축퇴. |
| `Public/UObject/WeakObjectPtr.h`, `WeakObjectPtrFwd.h` | `FWeakObjectPtr`, `TWeakObjectPtr<T>` | 약 참조. `IsValid()` 로 유효성 검사. (`WeakObjectPtrTemplates.h` 는 Core 모듈 측 헤더로, CoreUObject가 include만 함.) |
| `Public/UObject/PersistentObjectPtr.h` | `template <typename Path> TPersistentObjectPtr<Path>` | 경로 기반 지연 핸들 베이스. |
| `Public/UObject/SoftObjectPtr.h` | `struct FSoftObjectPtr : TPersistentObjectPtr<FSoftObjectPath>` (L44), `struct TSoftObjectPtr<T>` (L173), `class TSoftClassPtr<T>` (L762), `FSoftObjectPtrFastLess`/`LexicalLess` | 에셋 비동기 로드 가능. |
| `Public/UObject/SoftObjectPath.h` | `struct FSoftObjectPath` (L55), `struct FSoftClassPath : FSoftObjectPath` (L538), `FSoftObjectPathFastLess`(L506)/`LexicalLess`(L515), `FSoftObjectPathThreadContext` (L682) | 패키지 + 객체 경로 (`/Game/UI/Logo.Logo:Sub`). |
| `Public/UObject/StrongObjectPtr.h` | `template <typename T> class TStrongObjectPtr` | UPROPERTY 외부에서 GC 보호 강 참조. |
| `Public/UObject/LazyObjectPtr.h` | `class FLazyObjectPtr`, `template <typename T> class TLazyObjectPtr` | 액터 GUID 기반 지연 핸들. |
| `Public/UObject/TopLevelAssetPath.h` | `struct FTopLevelAssetPath` (L37), `FTopLevelAssetPathFastLess`(L217)/`LexicalLess`(L226) | `/Game/UI/Logo.Logo` 형태(서브 객체 없음). 5.x 신표준. |
| `Public/UObject/PrimaryAssetId.h` | `struct FPrimaryAssetType` (L27), `struct FPrimaryAssetId` (L125) | Asset Manager 식별자. |
| `Public/UObject/ObjectKey.h` | `struct FObjectKey` (L18), `template <typename T> class TObjectKey<T>` (L227) | 객체의 고유 해시 키. 객체 파괴 후에도 비교 가능. |
| `Public/UObject/ObjectHandle.h` | `FObjectHandle`, 관련 헬퍼 | TObjectPtr 내부 구현. 직접 다루지 않음. |
| `Public/UObject/ObjectHandleTracking.h`, `ObjectHandleDefines.h` 🛠 | 디버그/추적 | 에디터 빌드. |
| (외부 모듈) `UniversalObjectLocator` | `FUniversalObjectLocator` | Sequencer 등에서 사용하는 통합 객체 식별자. **CoreUObject 모듈 외**(별도 `UniversalObjectLocator` 모듈 또는 `Public/UObject/`에 forward만) — 본 카탈로그 범위 밖이지만 ObjectHandles 영역과 의미상 짝지어짐. |

---

## 3. 자주 쓰는 API

```cpp
// === TObjectPtr (UPROPERTY 멤버 권장) ===
UCLASS()
class AMyChar : public ACharacter
{
    GENERATED_BODY()
    UPROPERTY()
    TObjectPtr<USkeletalMesh> Mesh = nullptr;
    UPROPERTY(EditAnywhere)
    TObjectPtr<UMyComp> Health = nullptr;
};
// 사용 시 raw 포인터처럼:
USkeletalMesh* M = Mesh;
if (Mesh) Mesh->GetSomething();

// === TWeakObjectPtr (약 참조) ===
TWeakObjectPtr<APlayerController> WeakPC;
WeakPC = MyPC;
if (APlayerController* PC = WeakPC.Get())   // GC된 객체는 nullptr
{
    PC->ClientMessage(TEXT("hi"));
}
bool bAlive = WeakPC.IsValid();

// === TStrongObjectPtr (UPROPERTY 외부 강 참조) ===
TStrongObjectPtr<UMyData> Pinned(NewObject<UMyData>());   // 이 변수 살아있는 동안 GC 안 됨

// === TSoftObjectPtr (지연 로드 가능 에셋 참조) ===
UPROPERTY(EditAnywhere)
TSoftObjectPtr<UTexture2D> SoftTex;

// 동기 로드:
UTexture2D* Tex = SoftTex.LoadSynchronous();
// 비동기 로드:
TSharedPtr<FStreamableHandle> H = UAssetManager::GetStreamableManager().RequestAsyncLoad(
    SoftTex.ToSoftObjectPath(),
    FStreamableDelegate::CreateLambda([SoftTex](){ UTexture2D* T = SoftTex.Get(); /* ... */ }));

// === FSoftObjectPath (경로 자체) ===
FSoftObjectPath Path(TEXT("/Game/UI/Logo.Logo"));
UObject* O = Path.TryLoad();           // 동기 로드
bool bExist = Path.IsValid();
FString S = Path.ToString();
Path.SetPath(TEXT("/Game/UI/Logo2.Logo2"));

// === FTopLevelAssetPath (서브 객체 없는 경로) ===
FTopLevelAssetPath TLP(TEXT("/Game/UI/Logo"), TEXT("Logo"));
FName PkgName = TLP.GetPackageName();   // "/Game/UI/Logo"
FName AssetName = TLP.GetAssetName();   // "Logo"

// === FPrimaryAssetId (Asset Manager) ===
FPrimaryAssetType Type(TEXT("Item"));
FPrimaryAssetId Id(Type, TEXT("Sword01"));
UObject* Asset = UAssetManager::Get().GetPrimaryAssetObject(Id);

// === FObjectKey (해시 키) ===
TMap<FObjectKey, int32> Counters;
Counters.FindOrAdd(FObjectKey(MyObj))++;
// 객체가 파괴되어도 키 비교는 안전
```

---

## 4. 가상 함수 (오버라이드 포인트)

이 sub-skill의 핸들/경로 타입들은 **모두 USTRUCT 또는 일반 C++ struct**로 가상 함수가 없다. UObject 측 통합은 다음 가상 함수들에서 일어난다:

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual UWorld* GetWorld() const` | Object.h L719 | 핸들이 가리키는 객체의 월드 — [`UObject/`](../UObject/SKILL.md) §4.1 |
| `virtual FPrimaryAssetId GetPrimaryAssetId() const` | Object.h L1030 | Asset Manager 식별자 노출 — [`Editor/`](../Editor/SKILL.md) |
| `virtual bool IsAsset() const` | Object.h L1023 | 에셋 레지스트리 노출 여부 |

핸들 타입의 `Identical`/`Serialize`/`NetSerialize`/`ExportText`/`ImportText` 같은 동작은 USTRUCT 의 `TStructOpsTypeTraits` 특화로 등록된다 — 일반 코드에서 override 안 함.

---

## 5. 예제

### 5.1 핸들 선택 가이드 (실전 예)

```cpp
UCLASS()
class AMyEnemy : public ACharacter
{
    GENERATED_BODY()

    // 즉시 로드된 컴포넌트 — TObjectPtr (UPROPERTY)
    UPROPERTY()
    TObjectPtr<UAIController> AI;

    // BP/디테일에서 지정하는 에셋, 비동기 로드 가능 — TSoftObjectPtr
    UPROPERTY(EditAnywhere, Category="Loot")
    TSoftObjectPtr<UDataTable> LootTable;

    // 다른 액터 (씬에 있는) — TWeakObjectPtr (사라질 수 있음)
    TWeakObjectPtr<AActor> WeakTarget;

    // 멤버 아니지만 비동기 작업 동안 보호 — TStrongObjectPtr 로컬 변수
    void LoadAndUse()
    {
        if (UDataTable* DT = LootTable.LoadSynchronous())
        {
            TStrongObjectPtr<UDataTable> Pin(DT);  // 콜백 동안 보호
            DoAsync([Pin](){ Pin->...; });
        }
    }
};
```

### 5.2 비동기 로드 + 콜백

```cpp
void UMyLoader::LoadIcon()
{
    FSoftObjectPath Path(TEXT("/Game/UI/Icon.Icon"));
    TSharedPtr<FStreamableHandle> H = UAssetManager::GetStreamableManager()
        .RequestAsyncLoad(Path, FStreamableDelegate::CreateUObject(this, &UMyLoader::OnIconLoaded));
}

void UMyLoader::OnIconLoaded()
{
    if (UTexture2D* Icon = Cast<UTexture2D>(IconPath.ResolveObject()))
    {
        // ...
    }
}
```

### 5.3 객체 파괴 후에도 안전한 매핑

```cpp
// 객체가 사라지면 raw pointer 비교는 위험. FObjectKey는 안전.
TMap<FObjectKey, FStats> StatsByObj;

void OnEvent(UObject* O, int32 Delta)
{
    StatsByObj.FindOrAdd(FObjectKey(O)).Count += Delta;
}
// O가 GC된 후라도 FObjectKey는 비교 가능 (파괴 시점의 식별자 보존)
```

### 5.4 SoftObjectPath 와 TopLevelAssetPath의 차이

```cpp
// FSoftObjectPath: 서브 객체까지 표현 가능
FSoftObjectPath SubObj(TEXT("/Game/Maps/MainMap.MainMap:PersistentLevel.MyActor.MyComp"));

// FTopLevelAssetPath: 패키지 + 톱레벨 객체만 (5.x 권장)
FTopLevelAssetPath Top(TEXT("/Game/Maps/MainMap"), TEXT("MainMap"));
```

5.x 코드에서는 `FTopLevelAssetPath`를 우선 쓴다 (FName 두 개로 빠르고 캐시 친화적). 서브 객체가 필요할 때만 `FSoftObjectPath`.

---

## 6. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `TObjectPtr<T>` 내부 lazy-resolve 🛠 | ObjectPtr.h | `WITH_EDITORONLY_DATA` (디버그/추적 추가) | 에디터 빌드에서 `FObjectHandle` 추적·해시 검사. **쿠킹 후엔 raw pointer 로 축퇴** — 런타임 비용 0. |
| `ObjectHandleTracking.h` 🛠 | (전체) | `WITH_EDITOR` | 객체 핸들 액세스 추적·통계. |
| `meta=(AllowedClasses=...)`, `meta=(MetaClass=...)`, `meta=(BaseStruct=...)` (UPROPERTY 메타) 🛠 | (UPROPERTY 메타) | `WITH_EDITORONLY_DATA` | 디테일 패널의 핸들 게이팅. |
| `FSoftObjectPath` 의 `FixupCoreRedirects` 같은 호환 처리 (실용) 🛠 | SoftObjectPath.h | (런타임에도 시그니처 존재) | 옛 경로 리다이렉트 — 주 사용은 에디터·쿠킹. |

런타임에서 안전한 핸들 자체(저장·비교·로드)는 모두 동작한다. 에디터 전용은 디테일 패널 게이팅과 추적 도구.

---

## 7. 관련 sub-skill

- [`UObject/`](../UObject/SKILL.md) — `MarkAsGarbage` 와 `TWeakObjectPtr::IsValid` 의 상호작용
- [`GC/`](../GC/SKILL.md) — `TStrongObjectPtr` 가 사용하는 `FGCObject` 연동
- [`Property/`](../Property/SKILL.md) — `FObjectProperty`/`FSoftObjectProperty` 가 핸들들의 메타
- [`Package/`](../Package/SKILL.md) — `FSoftObjectPath` 가 패키지 경로를 직접 다룸
