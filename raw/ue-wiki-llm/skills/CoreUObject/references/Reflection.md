---
name: coreuobject-reflection
description: UCLASS / UPROPERTY / UFUNCTION / UENUM / USTRUCT 매크로 + UnrealHeaderTool generated.h + UClass / UEnum / UScriptStruct + 메타데이터 키 + UObjectIterator / TObjectIterator.
---

# CoreUObject / Reflection

> 부모 모듈: [`CoreUObject`](../SKILL.md) · UE 5.7.4
> 다루는 영역: 리플렉션 메타 객체(`UField`/`UStruct`/`UClass`/`UEnum`/`UFunction` 등) + UCLASS/UPROPERTY/UFUNCTION 매크로 + UObject 순회/검색 함수
> 관련 sub-skill: [`Property/`](../Property/SKILL.md), [`UObject/`](../UObject/SKILL.md), [`Package/`](../Package/SKILL.md)

---

## 1. 개요

UE의 리플렉션은 **컴파일 타임의 매크로 + UnrealHeaderTool(UHT) 코드 생성 + 런타임의 메타 객체** 3박자로 동작한다. 매크로(`UCLASS`/`USTRUCT`/`UPROPERTY`/`UFUNCTION`/`UENUM`/`UINTERFACE`)는 빈 매크로지만 UHT가 헤더를 사전 스캔해 `*.generated.h`/`*.gen.cpp` 를 만들어 `UClass` 등록 코드를 채워 넣는다. 런타임에서는 이 메타가 모두 UObject 자손인 `UClass`/`UStruct`/`UFunction`/`UEnum` 인스턴스로 살아있어, GC가 추적하고 `UObjectIterator<UClass>`로 순회 가능하다.

```
UObject
  └─ UField (Class.h:180)
       ├─ UStruct (L476)
       │    ├─ UScriptStruct (L1719)        ← USTRUCT 메타     ├─ UFunction (L2475)              ← UFUNCTION 메타
       │    │    └─ UDelegateFunction (L2680) → USparseDelegateFunction (L2709)
       │    └─ UClass (L3792)               ← UCLASS 메타 (자기 자신을 표현)
       └─ UEnum (L2790)                     ← UENUM 메타
```

Verse VM 변형 4종은 같은 사슬에 끼어든다: `UVerseClass : UClass`, `UVerseFunction : UFunction`, `UVerseStruct : UScriptStruct`, `UVerseEnum : UEnum`.

---

## 2. 핵심 헤더와 클래스

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/UObject/Class.h` | `UField` (L180), `UStruct` (L476), `UScriptStruct` (L1719), `UFunction` (L2475), `UDelegateFunction` (L2680), `USparseDelegateFunction` (L2709), `UEnum` (L2790), `UClass` (L3792) | 리플렉션 메타 객체 사슬. |
| `Public/UObject/ObjectMacros.h` | `UCLASS`/`UPROPERTY`/`UFUNCTION`/`USTRUCT`/`UENUM`/`UINTERFACE`/`UMETA`/`UPARAM`/`GENERATED_BODY` | UHT 진입 매크로. 컴파일 시 빈 매크로, UHT가 헤더 스캔으로 등록 코드 생성. `EClassFlags`(`CLASS_*`), `EObjectFlags`(`RF_*`), `EPropertyFlags`(`CPF_*`)도 여기. |
| `Public/UObject/UObjectIterator.h` | `TObjectIterator<T>`, `FRawObjectIterator`, `FThreadSafeObjectIterator` | 모든 UObject 순회. 메타 객체(`UClass`/`UFunction` 등)도 UObject이므로 그대로 순회 가능. |
| `Public/UObject/UObjectHash.h` | `GetObjectsOfClass(L198)`, `GetObjectsWithOuter(L128)`, `GetObjectsWithPackage(L175)`, `FindObjectWithOuter(L164)` | 빠른 검색. |
| `Public/VerseVM/VVMVerseClass.h`, `VVMVerseFunction.h`, `VVMVerseStruct.h`, `VVMVerseEnum.h` | `UVerseClass`(L136), `UVerseFunction`(L24), `UVerseStruct`(L32), `UVerseEnum`(L35) | Verse 객체 시스템과의 다리. `WITH_VERSE_COMPILER` 빌드에서만 활성화. |

### 2.1 매크로 (`ObjectMacros.h`)

```cpp
#define UPROPERTY(...)        // L744
#define UFUNCTION(...)        // L745
#define USTRUCT(...)          // L746
#define UENUM(...)            // L749
#define UMETA(...)            // L747  ← enum 멤버에 표시명·툴팁 부여
#define UPARAM(...)           // L748  ← BP 함수 파라미터에 표시명·기본값
#define GENERATED_BODY(...)   // L765  → BODY_MACRO_COMBINE(... _GENERATED_BODY)
#define UCLASS(...)           // L773 (UHT-passthrough) / L776 (BODY_MACRO 합성)
#define UINTERFACE(...)       // L780  → UCLASS()
#define GENERATED_USTRUCT_BODY(...)  // L767 → GENERATED_BODY()
```

플래그 마스크 (자주 인용):

- `RF_Load` (L615) — 디스크 직렬화 시 보존되는 플래그 합집합
- `RF_PropagateToSubObjects` (L618) — 서브오브젝트에 자동 전파되는 플래그
- `CLASS_Inherit` (L281) — 자식 클래스가 자동 상속받는 클래스 플래그
- `CLASS_RecompilerClear` (L285) — 재컴파일 시 클리어할 플래그
- `RF_AllFlags` (L612) — 전체 비트(에러 체크용)

---

## 3. 자주 쓰는 API

```cpp
// 클래스/타입 정보
UClass* C   = UMyActor::StaticClass();           // 컴파일 타임 결정
UClass* RC  = MyObj->GetClass();                 // 런타임 결정
bool bIs    = MyObj->IsA<AMyActor>();            // 또는 IsA(UMyActor::StaticClass())
UClass* Sup = C->GetSuperClass();
bool bChild = C->IsChildOf(AActor::StaticClass());  // Class.h L807

// 메타데이터 (UHT가 채움)
FString Tip = C->GetMetaData(TEXT("ToolTip"));
bool bHas   = C->HasMetaData(TEXT("Blueprintable"));
// 🛠 SetMetaData / RemoveMetaData (Class.h L307·L377) — 에디터/툴 빌드만 의미
//   `WITH_EDITOR` 가드 안에서만 호출

// 멤버 순회 (FProperty는 Property/SKILL.md 참조)
for (TFieldIterator<UFunction> It(C); It; ++It) { UFunction* F = *It; /* ... */ }
for (TFieldIterator<FProperty> It(C); It; ++It) { /* ... */ }

// 모든 인스턴스 순회 (UObjectIterator.h)
for (TObjectIterator<UMyActor> It; It; ++It) { AMyActor* A = *It; /* ... */ }

// 해시 검색 (UObjectHash.h)
TArray<UObject*> Out;
GetObjectsOfClass(UMyData::StaticClass(), Out, /*bIncludeDerived=*/true);
GetObjectsWithOuter(MyOuter, Out);
GetObjectsWithPackage(MyPkg, Out);
UObject* Found = (UObject*)FindObjectWithOuter(MyOuter, UMyData::StaticClass(), TEXT("Foo"));

// 캐스팅
if (UMyClass* M = Cast<UMyClass>(Obj)) { ... }      // Templates/Casts.h
UPawn* P = CastChecked<UPawn>(Actor);               // 실패 시 check()
```

### 3.1 UStruct 핵심 메서드 (`Class.h`)

| 메서드 | 위치 | 용도 |
|--------|------|------|
| `IsChildOf(const UStruct*)` | L807 | 상속 관계 검사. `UClass::IsChildOf` 도 동일. |
| `StaticLink(bool bRelinkExisting=false)` | L662 | 프로퍼티 체인을 다시 연결 (HotReload·BP 컴파일 후). |
| `SerializeProperties(FArchive&)` | L982 | 모든 UPROPERTY 자동 직렬화. 보통 직접 호출 안 함. |
| `ConvertUFieldsToFFields()` | L985 | 옛 UProperty 미러를 FProperty로 변환. |
| `InstanceSubobjectTemplates(...)` | L656 | UPROPERTY 인스턴싱(서브오브젝트 복제) 처리. |
| `CollectBytecodeReferencedObjects(...)` | L926 | BP 바이트코드가 참조하는 UObject 수집. |
| `CollectPropertyReferencedObjects(...)` | L931 | UPROPERTY가 참조하는 UObject 수집. |

### 3.2 UScriptStruct 핵심 메서드

| 메서드 | 위치 | 용도 |
|--------|------|------|
| `SerializeItem(FArchive&, void* Value, void const* Defaults)` | L2354 | USTRUCT 단일 인스턴스 직렬화. |
| `ExportText(...)` / `ImportText(...)` | L2368~ | 텍스트 ↔ struct (에디터 복붙·INI). |
| `CompareScriptStruct(const void* A, const void* B, uint32 PortFlags)` | L2406 | 두 인스턴스 동일성 비교. |
| `CopyScriptStruct(void* Dest, void const* Src, int32 ArrayDim=1)` | L2416 | 인스턴스 복사. |
| `InitializeStruct/DestroyStruct` | L2247·L2248 (override) | 라이프사이클. |
| `PrepareCppStructOps()` | L2289 | C++ struct 연산자 테이블 준비. |
| `static DeferCppStructOps(FTopLevelAssetPath, ICppStructOps*)` | L2260 | C++ struct 등록 지연. |

---

## 4. 가상 함수 (오버라이드 포인트)

리플렉션 메타 클래스의 virtual 은 거의 엔진 내부에서만 override 한다. 일반 게임 코드가 손댈 일이 거의 없으나, 새 Field 타입·새 Property 타입을 만들 때 알아야 한다. (FProperty PURE_VIRTUAL 은 [`Property/`](../Property/SKILL.md).)

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual void Serialize(FArchive&) override` | Class.h L2242 | UStruct/UClass 자체의 직렬화. |
| `virtual void Link(FArchive&, bool bRelinkExisting) override` | Class.h L2246 | 프로퍼티 체인 재연결. |
| `virtual void InitializeStruct(void*, int32) const override` | Class.h L2247 | 인스턴스 초기화. |
| `virtual void DestroyStruct(void*, int32) const override` | Class.h L2248 | 인스턴스 파괴. |
| `virtual bool IsStructTrashed() const override` | Class.h L2249 | 손상된 USTRUCT 감지. |

`static AddReferencedObjects(UObject*, FReferenceCollector&)` (Class.h L629) 는 메타 객체 자체가 GC 대상이라 자기 자신의 자식 필드를 등록한다 — 자세한 GC 흐름은 [`GC/`](../GC/SKILL.md).

---

## 5. 예제

### 5.1 UCLASS·UPROPERTY·UFUNCTION 골격

```cpp
UCLASS(Blueprintable, BlueprintType, meta=(DisplayName="My Item"))
class MYGAME_API UMyItem : public UObject
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Item",
              meta=(ClampMin="0", ClampMax="999"))
    int32 Count = 1;

    UFUNCTION(BlueprintCallable, Category="Item",
              meta=(DisplayName="Use Item"))
    bool TryUse(UPARAM(ref) int32& OutRemaining);
};
```

### 5.2 enum 메타

```cpp
UENUM(BlueprintType)
enum class EWeaponSlot : uint8
{
    Primary    UMETA(DisplayName="Primary"),
    Secondary  UMETA(DisplayName="Secondary"),
    Melee      UMETA(DisplayName="Melee", ToolTip="Knife or fists"),
    None       UMETA(Hidden),
};
```

### 5.3 리플렉션 순회 (FProperty 정보를 로깅)

```cpp
void DumpProperties(UObject* Obj)
{
    if (!Obj) return;
    UClass* C = Obj->GetClass();
    for (TFieldIterator<FProperty> It(C); It; ++It)
    {
        FProperty* P = *It;
        FString CppType = P->GetCPPType();              // PURE_VIRTUAL — Property/SKILL.md
        UE_LOG(LogTemp, Log, TEXT("%s : %s"), *P->GetName(), *CppType);
    }
}
```

### 5.4 모든 자손 인스턴스 일괄 처리

```cpp
TArray<UObject*> Items;
GetObjectsOfClass(UMyItem::StaticClass(), Items, /*bIncludeDerived=*/true);
for (UObject* O : Items)
{
    if (UMyItem* It = Cast<UMyItem>(O)) { /* ... */ }
}
```

---

## 6. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `SetMetaData(TCHAR*/FName, TCHAR*)` 🛠 | Class.h L307·L308 | `WITH_EDITOR` | 메타데이터는 쿠킹 후에 부분만 보존. |
| `RemoveMetaData(...)` 🛠 | Class.h L377·L378 | `WITH_EDITOR` | |
| `GetAuthoredName()` 🛠 | Class.h L234 | `WITH_EDITOR` | UPROPERTY 원래 이름(공백 변환 전). |
| `FormatNativeToolTip(...)` 🛠 | Class.h L259 | `WITH_EDITOR` | 디테일 패널 툴팁 후처리. |
| `GetBoolMetaDataHierarchical(FName)` 🛠 | Class.h L855 | `WITH_EDITOR` | 부모 클래스까지 메타 검색. |
| `GetStringMetaDataHierarchical(...)` 🛠 | Class.h L858 | `WITH_EDITOR` | 동일. |
| UPROPERTY 메타 키들 (`EditAnywhere`/`EditCondition`/`Category`/`DisplayName`/`ToolTip` 등) | (UPROPERTY 메타) | `WITH_EDITORONLY_DATA` | 쿠킹 빌드에 일부만 잔존. |
| `UVerseClass`/`UVerseFunction`/`UVerseStruct`/`UVerseEnum` (조건부) | VerseVM/* | `WITH_VERSE_COMPILER` | 에디터 또는 서버 빌드에서만 활성 (`CoreUObject.Build.cs:46~53`). |

> 게임 런타임에서 메타데이터 키가 필요하면 `Cooked` 메타 객체(`UClassCookedMetaData` 등 — [`Cooking/`](../Cooking/SKILL.md))로 보존된 부분만 사용.

---

## 7. 관련 sub-skill

- [`UObject/`](../UObject/SKILL.md) — 리플렉션 메타 자체가 UObject. 라이프사이클 공유.
- [`Property/`](../Property/SKILL.md) — `FField`/`FProperty` (4.25 이후 비-UObject 프로퍼티)
- [`Package/`](../Package/SKILL.md) — `UClass` 가 어느 `UPackage` 에 있는지 / `Linker` 가 직렬화/저장
- [`Cooking/`](../Cooking/SKILL.md) — 쿠킹 시 메타 보존 (`U{Class,Struct,Enum}CookedMetaData`)
- [`StructUtils/`](../StructUtils/SKILL.md) — `UPropertyBag`(동적 USTRUCT) 의 `UScriptStruct` 활용
- [`DeprecatedUProperty/`](../DeprecatedUProperty/SKILL.md) — `UnrealTypePrivate.h` 의 옛 UProperty 미러
