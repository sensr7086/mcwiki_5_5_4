---
name: coreuobject-property
description: FProperty 5.x 시스템 - FObjectProperty / FArrayProperty / FMapProperty / FStructProperty + CastField + TFieldIterator + ImportText / ExportText + ContainerPtrToValuePtr.
---

# CoreUObject / Property

> 부모 모듈: [`CoreUObject`](../SKILL.md) · UE 5.7.4
> 다루는 영역: `FField`/`FProperty` 계층 (4.25 이후 비-UObject 프로퍼티) + Cast / Iterator / PropertyWrapper
> 관련 sub-skill: [`Reflection/`](../Reflection/SKILL.md), [`UObject/`](../UObject/SKILL.md), [`Serialization/`](../Serialization/SKILL.md), [`DeprecatedUProperty/`](../DeprecatedUProperty/SKILL.md)

---

## 1. 개요

UE 4.25부터 모든 프로퍼티(UPROPERTY 멤버의 메타 객체)는 UObject가 아닌 **`FField` 계층의 일반 C++ 객체**다. 베이스는 `FField` (`Field.h:555`), 그 자손이 `FProperty` (`UnrealType.h:173`), 그 아래에 타입별 `FObjectProperty`/`FStructProperty`/`FArrayProperty` 등이 분포한다. 옛 `UProperty` 사슬(`UnrealTypePrivate.h`)은 호환을 위해 남아있을 뿐, 신규 코드는 항상 `FProperty` 쪽을 사용한다.

`FProperty`는 다음 일을 한다:

1. **메모리 오프셋·크기 보유** — 컨테이너 포인터에 더해서 값 주소 계산
2. **직렬화** — `SerializeItem(FStructuredArchive::FSlot, void*, const void*)` (PURE_VIRTUAL)
3. **비교/복사/초기화/파괴** — `Identical`, `CopySingleValue`, `InitializeValue`, `DestroyValue`
4. **텍스트 변환** — `ExportText_Internal`/`ImportText_Internal` (에디터 복붙·INI)
5. **GC 토큰 방출** — `ContainsObjectReference`로 GC 추적 대상 표시

---

## 2. 핵심 헤더와 클래스

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/UObject/Field.h` | `FField` (L555), `FFieldVariant`, `FFieldClass` | 모든 FProperty의 베이스. `FName Name` / `FFieldVariant Owner`. |
| `Public/UObject/UnrealType.h` | `FProperty` (L173), `FNumericProperty` (L1765), `FBoolProperty` (L2542), `FObjectPropertyBase` (TFObjectPropertyBase 템플릿), `FObjectProperty` (L3086, `: TFObjectPropertyBase<TObjectPtr<UObject>>`), `FInterfaceProperty` (L3560), `FArrayProperty` (L3701), `FStructProperty` (L6305), `TFieldIterator<T>` (L7082) | 프로퍼티 본체와 타입별 특화. |
| `Public/UObject/EnumProperty.h` | `FEnumProperty` | UENUM 멤버. |
| `Public/UObject/StrProperty.h`, `TextProperty.h`, `Utf8StrProperty.h`, `AnsiStrProperty.h` | `FStrProperty`, `FTextProperty`, `FUtf8StrProperty`, `FAnsiStrProperty` | 문자열 특화. |
| `Public/UObject/FieldPathProperty.h` | `FFieldPathProperty` | `FFieldPath` 보유 프로퍼티. |
| `Public/UObject/PropertyOptional.h` | `FOptionalProperty` | `TOptional<T>` 표현. |
| `Public/UObject/PropertyVisitor.h` | `FPropertyVisitor` | 중첩 프로퍼티 방문자 패턴. |
| `Public/UObject/PropertyAccessUtil.h` | `FPropertyAccessUtil` | 안전한 외부 접근(에디터·BP). |
| `Public/Templates/Casts.h` | `Cast<T>`/`CastChecked<T>`/`ExactCast<T>` (UObject용), `CastField<T>`/`CastFieldChecked<T>` (FField용) | 다형 캐스트. |
| `Public/UObject/PropertyWrapper.h` | `UPropertyWrapper` (L22), `UMulticastDelegatePropertyWrapper` (L53), `UMulticastInlineDelegatePropertyWrapper` (L65) | FProperty를 UObject로 감싸 디테일 패널/스크립트에서 사용 가능하게. **에디터 그리드 위주**. |

### 2.1 FProperty 자손 한눈에

`UnrealType.h` 안 (이하 라인 번호는 클래스 선언):

```
FField (Field.h:555)
  └─ FProperty (L173)
       ├─ FNumericProperty (L1765)              ← 숫자 베이스
       │    └─ TProperty<...> 특화 다수 (FByte/FInt8/.../FFloat/FDouble)
       ├─ FBoolProperty (L2542)
       ├─ TFObjectPropertyBase<...>             ← 객체 프로퍼티 베이스
       │    ├─ FObjectProperty (L3086)          ← UPROPERTY() TObjectPtr<U...>
       │    ├─ FWeakObjectProperty             ← TWeakObjectPtr
       │    ├─ FLazyObjectProperty             ← TLazyObjectPtr
       │    └─ FSoftObjectProperty             ← TSoftObjectPtr / FSoftObjectPath
       ├─ FInterfaceProperty (L3560)
       ├─ FArrayProperty (L3701)                ← TArray<...>
       ├─ FMapProperty / FSetProperty           ← TMap / TSet
       ├─ FStructProperty (L6305)               ← USTRUCT 멤버
       ├─ FNameProperty / FStrProperty / FTextProperty / FUtf8StrProperty / FAnsiStrProperty
       ├─ FEnumProperty                         ← UENUM (typed)
       ├─ FFieldPathProperty                    ← FFieldPath
       ├─ FOptionalProperty                     ← TOptional<T>
       ├─ FDelegateProperty / FMulticastDelegateProperty (Inline/Sparse 변형)
       └─ FVerseValueProperty / FVerseStringProperty / FVerseClassProperty
```

각 클래스가 어디 헤더에 있는지는 `git grep -nE "^class .*F.*Property[^[:alnum:]_]"` 또는 본 위키의 [`DeprecatedUProperty/`](../DeprecatedUProperty/SKILL.md) 카탈로그 참조.

---

## 3. 자주 쓰는 API

```cpp
// 멤버 순회 (UStruct/UClass 기준)
for (TFieldIterator<FProperty> It(Obj->GetClass()); It; ++It)
{
    FProperty* P = *It;

    // 컨테이너 포인터로부터 실제 값 주소 계산
    void* Value = P->ContainerPtrToValuePtr<void>(Obj);

    // CPP 표기 ("int32", "TArray<FVector>" 등) — PURE_VIRTUAL
    FString Type = P->GetCPPType();

    // 동일성 / 복사 / 초기화 / 파괴
    bool bSame  = P->Identical(A, B);
    P->CopySingleValue(Dest, Src);    // UnrealType.h L879
    P->CopyCompleteValue(Dest, Src);  // UnrealType.h L913 (배열 차원 고려)
    P->InitializeValue(Mem);          // L1108
    P->DestroyValue(Mem);             // L1025
}

// 타입 캐스트 (FField 계열)
if (FObjectProperty* OP = CastField<FObjectProperty>(P))
{
    UObject* Ptr = OP->GetObjectPropertyValue(Value);
}
FStructProperty* SP = CastFieldChecked<FStructProperty>(P);  // 실패 시 check()

// 메타데이터 (Field.h)
bool bHas = P->HasMetaData(TEXT("ClampMin"));      // L540
FString S = P->GetMetaData(TEXT("Category"));      // L930·L931
FName N   = P->GetFName();                          // L526

// FBoolProperty 전용 (UnrealType.h L2633·L2655)
if (FBoolProperty* BP = CastField<FBoolProperty>(P))
{
    bool b = BP->GetPropertyValue(Value);
    BP->SetPropertyValue(Value, !b);
}
```

`ContainerPtrToValuePtr<T>` 은 가장 자주 쓰는 헬퍼. UPROPERTY 멤버의 실제 메모리 주소를 안전하게 계산한다 (오프셋 + ArrayIndex).

---

## 4. 가상 함수 (오버라이드 포인트)

### 4.1 FProperty PURE_VIRTUAL — 새 프로퍼티 타입을 만들 때만

| 시그니처 | 위치 | 의미 |
|----------|------|------|
| `virtual FString GetCPPType(FString*, uint32) const` | UnrealType.h L339 | `int32`, `TArray<FVector>` 같은 C++ 표기. |
| `virtual bool Identical(const void* A, const void* B, uint32 PortFlags) const` | UnrealType.h L515 | 두 값 동일성. 직렬화 최적화·델타 비교 기반. |
| `virtual void SerializeItem(FStructuredArchive::FSlot, void* Value, void const* Defaults) const` | UnrealType.h L581 | 단일 값 직렬화. |
| `virtual void ExportText_Internal(...)` | UnrealType.h L718 | 텍스트로 내보내기 (에디터 복붙·INI). |
| `virtual const TCHAR* ImportText_Internal(...)` | UnrealType.h L719 | 텍스트에서 읽기. |
| `virtual bool HasIntrusiveUnsetOptionalState() const` | UnrealType.h L1335 | `TOptional<T>` 인트루시브 표현 지원 여부. |

### 4.2 자주 override되는 일반 virtual

| 시그니처 | 위치(베이스) | 용도 |
|----------|------|------|
| `virtual bool ContainsObjectReference(...) const` | UnrealType.h (ex L3067 in `FObjectProperty`) | 강/약/소프트 UObject 참조 보유 여부 — GC 토큰 방출. |
| `virtual void CopyValuesInternal(...)` | UnrealType.h L1608 (`TProperty`) | 다중 값 복사. 타입별 특화. |
| `virtual void ClearValueInternal/InitializeValueInternal/DestroyValueInternal` | UnrealType.h L1615/L1619/L1626 | 메모리 라이프사이클. |
| `virtual EConvertFromTypeResult ConvertFromType(...)` | UnrealType.h L1992 | 옛 직렬화 데이터의 타입 변환 (마이그레이션). |
| `virtual bool HasSetter()/HasGetter()`, `CallSetter()/CallGetter()` | UnrealType.h L348~L376 | UPROPERTY(BlueprintSetter/Getter) 지원. |

### 4.3 FField virtual (`Field.h`)

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual FFieldClass* GetFieldClassPrivate()` | Field.h L571 | **PURE_VIRTUAL** — 동적 타입 식별. `DECLARE_FIELD` 매크로가 자동 구현. |
| `virtual SIZE_T GetFieldSize() const` | Field.h L585 | 메모리 통계. |
| `virtual FField* GetInnerFieldByName(const FName&)` | Field.h L890 | 중첩 필드 검색 (`FStructProperty` override). |
| `virtual void GetInnerFields(TArray<FField*>&)` | Field.h L896 | 중첩 필드 열거. |

---

## 5. 예제

### 5.1 모든 UPROPERTY 값 덤프

```cpp
void DumpAllProperties(UObject* Obj)
{
    for (TFieldIterator<FProperty> It(Obj->GetClass()); It; ++It)
    {
        FProperty* P = *It;
        FString CppType = P->GetCPPType();

        FString TextValue;
        P->ExportText_InContainer(/*Index=*/0, TextValue, Obj, Obj, /*Owner=*/nullptr, PPF_None);

        UE_LOG(LogTemp, Log, TEXT("%s %s = %s"), *CppType, *P->GetName(), *TextValue);
    }
}
```

### 5.2 특정 타입 프로퍼티만 안전 처리

```cpp
for (TFieldIterator<FProperty> It(C); It; ++It)
{
    if (FArrayProperty* AP = CastField<FArrayProperty>(*It))
    {
        FScriptArrayHelper Helper(AP, AP->ContainerPtrToValuePtr<void>(Obj));
        UE_LOG(LogTemp, Log, TEXT("Array %s : %d items"), *AP->GetName(), Helper.Num());
    }
    else if (FStructProperty* SP = CastField<FStructProperty>(*It))
    {
        UScriptStruct* S = SP->Struct;          // USTRUCT 메타
        // S 와 SP->ContainerPtrToValuePtr<void>(Obj) 로 인스턴스 다룸
    }
}
```

### 5.3 메타 기반 디테일 패널 게이팅 예

```cpp
// UPROPERTY(EditAnywhere, meta=(EditCondition="bAdvanced"))
// → FProperty->HasMetaData("EditCondition") 로 검사
//   디테일 패널 빌드 코드에서 자주 사용 — 게임 런타임은 보통 안 씀
```

---

## 6. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `FField::SetMetaData / RemoveMetaData` 🛠 | Field.h (Setter는 `WITH_EDITORONLY_DATA`) | `WITH_EDITORONLY_DATA` | 메타데이터 자체가 에디터 전용. |
| `FProperty::ExportText_*` 🛠 (실용적으로) | UnrealType.h L718 | (런타임에도 존재하지만 주 사용처는 에디터·INI·자동화) | 디테일 패널 복붙·INI 라우팅. |
| `FProperty::ImportText_*` 🛠 (동상) | UnrealType.h L719 | 동상 | |
| `UPropertyWrapper`, `UMulticastDelegatePropertyWrapper`, `UMulticastInlineDelegatePropertyWrapper` 🛠 | PropertyWrapper.h L22·L53·L65 | `UCLASS(Transient, MinimalAPI)` — 디테일 패널/그리드용 | "wrapper for native FProperties that can be used by property editors (grids)" — 헤더 주석. |
| UPROPERTY 메타 키 (`EditAnywhere`/`EditCondition`/`Category`/`DisplayName`/`UIMin`/`ClampMin` 등) | (메타) | `WITH_EDITORONLY_DATA` | 쿠킹 후 일부만 잔존 (디테일 패널이 사라지므로 대부분 제거). |
| `BlueprintReadOnly`/`BlueprintReadWrite` | (메타) | 런타임 잔존 | Blueprint VM이 사용하므로 쿠킹에도 남음. |

> 게임 코드에서 `ExportText/ImportText` 를 실시간 호출하는 것은 권장하지 않는다 — 비싸고, 텍스트 포맷이 보장되지 않는다. 데이터 교환은 `Json`/`JsonUtilities` 또는 직접 직렬화를 쓴다.

---

## 7. 관련 sub-skill

- [`Reflection/`](../Reflection/SKILL.md) — `UStruct`/`UClass`의 프로퍼티 체인 관리·`StaticLink`
- [`UObject/`](../UObject/SKILL.md) — `UPROPERTY` 멤버를 가진 객체의 라이프사이클
- [`Serialization/`](../Serialization/SKILL.md) — `FProperty::SerializeItem` 과 `FArchive` 의 만남
- [`GC/`](../GC/SKILL.md) — `ContainsObjectReference`가 만들어내는 GC 토큰
- [`DeprecatedUProperty/`](../DeprecatedUProperty/SKILL.md) — 옛 `UProperty` 미러 사슬과 마이그레이션
