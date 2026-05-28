---
name: coreuobject-structutils
description: FInstancedStruct + FSharedStruct + FStructView + UPropertyBag + UUserDefinedStruct - 동적 USTRUCT 5.x.
---

# CoreUObject / StructUtils

> 부모 모듈: [`CoreUObject`](../SKILL.md) · UE 5.7.4
> 다루는 영역: 동적 USTRUCT (`UPropertyBag`, `FInstancedPropertyBag`) + 인스턴스드 구조 (`FInstancedStruct`/`FSharedStruct`/`FStructView`/`FInstancedStructContainer`) + 사용자 정의 구조체 (`UUserDefinedStruct`)
> 관련 sub-skill: [`Reflection/`](../Reflection/SKILL.md), [`Property/`](../Property/SKILL.md), [`Serialization/`](../Serialization/SKILL.md)

---

## 1. 개요

StructUtils는 5.x에서 표준화된 **유연한 USTRUCT 컨테이너 모음**이다. 게임플레이가 다음과 같은 패턴에서 필요로 한다:

1. **타입 다형 USTRUCT** — `FInstancedStruct` 한 멤버에 어떤 USTRUCT라도 담음. BP에서도 노출.
2. **공유 USTRUCT** — `FSharedStruct` 로 여러 객체가 공유 (참조 카운팅).
3. **읽기 전용 뷰** — `FStructView` 로 USTRUCT를 빌려서만 봄 (소유 없음).
4. **동적 프로퍼티 가방** — `FInstancedPropertyBag` 로 런타임에 프로퍼티를 추가/제거 (메타데이터 기반 동적 USTRUCT). 부모 메타로 `UPropertyBag`이 사용됨.
5. **사용자 정의 USTRUCT** — `UUserDefinedStruct` 가 BP/에디터에서 만든 USTRUCT.

> 본 sub-skill은 5.x에서 5.0.x의 `StructUtils` 플러그인 내용이 CoreUObject로 흡수된 결과를 다룬다. 옛 플러그인 의존을 가진 코드는 마이그레이션 필요.

---

## 2. 핵심 헤더와 클래스

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/InstancedStruct.h` | `USTRUCT FInstancedStruct` | 한 멤버에 임의의 USTRUCT 인스턴스를 보관. UPROPERTY로 노출 가능, BP에도 노출. |
| `Public/InstancedStructContainer.h` | `USTRUCT FInstancedStructContainer` | `FInstancedStruct` 를 효율적으로 묶어 보관 (배열 위 array-of-struct). |
| `Public/SharedStruct.h` | `USTRUCT FSharedStruct`, `FConstSharedStruct` | 참조 카운팅으로 USTRUCT 공유. |
| `Public/StructView.h` | `USTRUCT FStructView`, `FConstStructView` | USTRUCT 인스턴스를 가리키는 비-소유 핸들. |
| `Public/StructUtils/PropertyBag.h` | `enum class EPropertyBagPropertyType : uint8` (L18), `EPropertyBagContainerType : uint8` (L44), `FPropertyBagContainerTypes` (L60), `EPropertyBagResult : uint8` (L171), `EPropertyBagAlterationResult : uint8` (L182), `FPropertyBagPropertyDescMetaData` (L195), `FPropertyBagPropertyDesc` (L248), `FInstancedPropertyBag` (L417), `FPropertyBagArrayRef : FScriptArrayHelper` (L970), `FPropertyBagSetRef : private FScriptSetHelper` (L1162), `EPropertyBagMissingEnum : uint8` (L1282), `FPropertyBagMissingStruct` (L1288), `UPropertyBagMissingObject : UObject` (L1294), `UPropertyBag : UScriptStruct` (L1308) ⚠ | 동적 프로퍼티 가방 — 런타임에 USTRUCT 정의 자체를 만들고 값을 다룸. |
| `Public/StructUtils/StructArrayView.h` | `TStructArrayView<T>`, `FStructArrayView` | USTRUCT 배열의 비-소유 뷰. |
| `Public/StructUtils/StructTypeBitSet.h` | `TStructTypeBitSet<T>` | 타입을 비트셋으로 표현 (Mass·AI). |
| `Public/StructUtils/StructUtils.h` | 공용 헬퍼 | 패키지 진입 헤더. |
| `Public/StructUtils/StructUtilsMacros.h` | 매크로 | `DECLARE_*` 패턴. |
| `Public/StructUtils/StructUtilsTypes.h` | 공용 타입 | enum 등. |
| `Public/StructUtils/UserDefinedStruct.h` | `UUserDefinedStruct : UScriptStruct`, `EUserDefinedStructureStatus`, `FUserStructOnScopeIgnoreDefaults` | BP에서 만드는 USTRUCT. |
| `Public/StructUtils/UserDefinedStructEditorUtils.h` 🛠 | `UUserDefinedStructEditorDataBase : UObject` | UUserDefinedStruct 의 에디터 부속 데이터. |

> ⚠ `UPropertyBag` 은 `UCLASS(Transient, MinimalAPI)`로 선언되었으나 부모가 `UScriptStruct`인 비정상적 구성이다 (UCLASS인데 USTRUCT 메타 베이스). 동적 USTRUCT를 표현하기 위한 트릭이며 일반 코드에서 흉내내지 말 것.

---

## 3. 자주 쓰는 API

```cpp
// === FInstancedStruct ===
UPROPERTY(EditAnywhere)
FInstancedStruct Item;            // 디테일 패널에서 USTRUCT 타입 선택 가능

Item.InitializeAs<FMyStruct>();   // 새 인스턴스 생성
FMyStruct& Ref = Item.GetMutable<FMyStruct>();
Ref.Field = 42;

if (FMyStruct const* P = Item.GetPtr<FMyStruct>()) { /* 안전 접근 */ }

// 타입 검사
if (Item.GetScriptStruct() == FMyStruct::StaticStruct()) { /* ... */ }
Item.Reset();                     // 비우기

// === FStructView (비-소유 뷰) ===
FStructView View = FStructView::Make(Ref);   // 내부 포인터+메타만
if (FMyStruct* P = View.GetMutablePtr<FMyStruct>()) { /* ... */ }

// === FSharedStruct (공유) ===
FSharedStruct A = FSharedStruct::Make<FMyStruct>(/*ctor args*/);
FSharedStruct B = A;              // 참조 카운팅으로 공유
B.GetMutable<FMyStruct>().Field = 7;

// === FInstancedStructContainer ===
FInstancedStructContainer Container;
Container.Append({ FInstancedStruct::Make<FMyStruct>(),
                   FInstancedStruct::Make<FOtherStruct>() });
for (const FStructView V : Container) { /* 순회 */ }

// === FInstancedPropertyBag (동적 프로퍼티) ===
FInstancedPropertyBag Bag;
Bag.AddProperty(FName("Health"), EPropertyBagPropertyType::Float);
Bag.AddProperty(FName("Tags"),   EPropertyBagPropertyType::Name, EPropertyBagContainerType::Array);

Bag.SetValueFloat(FName("Health"), 100.f);
TValueOrError<float, EPropertyBagResult> H = Bag.GetValueFloat(FName("Health"));
```

`FInstancedPropertyBag` 의 모든 변경은 `EPropertyBagAlterationResult` 또는 `EPropertyBagResult` 로 결과 보고. 누락된 프로퍼티는 `UPropertyBagMissingObject`/`FPropertyBagMissingStruct` 같은 placeholder 로 대체된다.

### 3.1 EPropertyBagPropertyType (`PropertyBag.h:18`)

```
None, Bool, Byte, Int32, Int64, Float, Double,
Name, String, Text, Enum, Struct, Object, SoftObject, Class, SoftClass
```

### 3.2 EPropertyBagContainerType (`PropertyBag.h:44`)

```
None, Array, Set
```

---

## 4. 가상 함수 (오버라이드 포인트)

이 sub-skill의 클래스들은 대부분 USTRUCT(또는 UUserDefinedStruct/UPropertyBag 메타)이고, 일반 게임 코드가 override 할 일이 거의 없다. 한 곳에서 자주 만나는 것이 `UUserDefinedStruct`:

| 시그니처 | 위치 | 가드 | 용도 |
|----------|------|------|------|
| `virtual void PostDuplicate(bool bDuplicateForPIE)` 🛠 | UserDefinedStruct.h | `WITH_EDITOR` | 복제 시 파생 데이터 갱신. |
| `virtual void GetAssetRegistryTags(FAssetRegistryTagsContext)` 🛠 | UserDefinedStruct.h | `WITH_EDITOR` | 사용자 정의 USTRUCT 검색용 태그. |
| `virtual void PostLoad()` 🛠 | UserDefinedStruct.h | `WITH_EDITOR` | 검증·마이그레이션. |
| `virtual void PreSaveRoot(FObjectPreSaveRootContext)` 🛠 | UserDefinedStruct.h | `WITH_EDITOR` | 저장 전 정리. |

`UScriptStruct` 의 `InitializeStruct`/`DestroyStruct`/`SerializeItem` 등은 [`Reflection/`](../Reflection/SKILL.md) §3.2 참조.

---

## 5. 예제

### 5.1 행동 변형이 다양한 아이템 (FInstancedStruct)

```cpp
USTRUCT(BlueprintType) struct FUseEffect       { GENERATED_BODY() virtual ~FUseEffect()=default; };
USTRUCT(BlueprintType) struct FHealEffect : public FUseEffect { GENERATED_BODY() UPROPERTY() float Amount = 10.f; };
USTRUCT(BlueprintType) struct FDamageEffect : public FUseEffect { GENERATED_BODY() UPROPERTY() float Dmg = 5.f; };

UCLASS()
class UMyItem : public UDataAsset
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, meta=(BaseStruct="/Script/MyGame.UseEffect"))
    FInstancedStruct OnUse;        // BP/디테일에서 Heal/Damage 등 골라 인스턴스 생성

    void Use(AActor* Target)
    {
        if (FUseEffect* E = OnUse.GetMutablePtr<FUseEffect>())
        {
            // 폴리모픽 분기
            if (FHealEffect* H = OnUse.GetMutablePtr<FHealEffect>()) { /* Heal */ }
            else if (FDamageEffect* D = OnUse.GetMutablePtr<FDamageEffect>()) { /* Damage */ }
        }
    }
};
```

### 5.2 동적 프로퍼티 가방 (런타임에 스키마 결정)

```cpp
FInstancedPropertyBag Stats;
Stats.AddProperty(FName("HP"),  EPropertyBagPropertyType::Float);
Stats.AddProperty(FName("MP"),  EPropertyBagPropertyType::Float);
Stats.AddProperty(FName("Tag"), EPropertyBagPropertyType::Name);

Stats.SetValueFloat(FName("HP"), 100.f);
Stats.SetValueFloat(FName("MP"), 50.f);
Stats.SetValueName(FName("Tag"), TEXT("Hero"));

if (auto R = Stats.GetValueFloat(FName("HP")); R.HasValue())
{
    float H = R.GetValue();    // 100.f
}
```

### 5.3 비-소유 뷰로 함수에 전달 (FStructView)

```cpp
void Process(FConstStructView V)
{
    if (const FMyStruct* P = V.GetPtr<FMyStruct>()) { /* 읽기 */ }
}

FMyStruct S;
Process(FConstStructView::Make(S));
```

### 5.4 효율적인 묶음 보관 (FInstancedStructContainer)

```cpp
UPROPERTY(EditAnywhere)
FInstancedStructContainer Steps;     // 순서 있는 폴리모픽 USTRUCT 시퀀스

void RunAll()
{
    for (FStructView V : Steps)
    {
        if (FMyStep* P = V.GetMutablePtr<FMyStep>()) P->Execute();
    }
}
```

---

## 6. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `UUserDefinedStruct::PrimaryStruct/ErrorMessage/EditorData` 🛠 | UserDefinedStruct.h | `WITH_EDITORONLY_DATA` | 사용자 정의 struct의 원본 추적·편집 데이터. |
| `UUserDefinedStruct::PostDuplicate/GetAssetRegistryTags/PostLoad/PreSaveRoot` 🛠 | UserDefinedStruct.h | `WITH_EDITOR` | 에디터 라이프사이클. |
| `UUserDefinedStructEditorDataBase` 🛠 | UserDefinedStructEditorUtils.h L13 | `WITH_EDITORONLY_DATA` | UUserDefinedStruct 부속 데이터. |
| `meta=(BaseStruct=...)` (FInstancedStruct UPROPERTY 메타) 🛠 | (메타) | `WITH_EDITORONLY_DATA` | 디테일 패널이 후보 USTRUCT 게이팅. |
| `meta=(StructTypeConst)` 같은 디테일 메타 🛠 | (메타) | `WITH_EDITORONLY_DATA` | 디테일 패널 동작 변경. |

런타임에서 안전하게 쓰는 것은 `FInstancedStruct`/`FSharedStruct`/`FStructView`/`FInstancedStructContainer`/`FInstancedPropertyBag` 자체와 그 메서드들. 메타·에디터 데이터는 보존되지 않는다.

---

## 7. 관련 sub-skill

- [`Reflection/`](../Reflection/SKILL.md) — `UScriptStruct` 가 본 sub-skill의 모든 동적 표현의 메타
- [`Property/`](../Property/SKILL.md) — `FStructProperty` 가 USTRUCT 멤버를 표현
- [`Serialization/`](../Serialization/SKILL.md) — `FInstancedStruct` 의 NetSerialize·Identical 등 USTRUCT 직렬화 통합
- [`Cooking/`](../Cooking/SKILL.md) — 사용자 정의 struct의 쿠킹 메타 보존
