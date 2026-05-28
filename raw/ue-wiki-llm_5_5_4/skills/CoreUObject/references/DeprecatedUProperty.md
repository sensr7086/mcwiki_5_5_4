---
name: coreuobject-deprecateduproperty
description: UProperty (deprecated 4.25) → FProperty 마이그레이션 가이드 - 옛 API 식별 + 변경 매핑 + 호환 코드.
---

# CoreUObject / DeprecatedUProperty

> 부모 모듈: [`CoreUObject`](../SKILL.md) · UE 5.5.4
> 다루는 영역: `UnrealTypePrivate.h` 의 33개 deprecated `UProperty` 사슬 카탈로그 + `FProperty`로의 마이그레이션 가이드
> 관련 sub-skill: [`Property/`](../Property/SKILL.md), [`Reflection/`](../Reflection/SKILL.md)

> ⚠ **이 sub-skill은 호환·마이그레이션 참고용이다.** 신규 코드에서는 **항상 `FProperty` 계열**(`Property/SKILL.md`)을 사용한다. 본 카탈로그는 옛 코드를 읽거나 5.5.4 트리에서 만나는 `UProperty*` 심볼이 무엇인지 확인하기 위한 것.

---

## 1. 개요

UE 4.25 이전엔 모든 프로퍼티의 메타 객체가 UObject(`UProperty` 계열)였다. **4.25부터 `FField`/`FProperty` (비-UObject 일반 C++ 객체)로 마이그레이션**되었다. 이유:

1. **메모리** — 모든 프로퍼티가 UObject면 GC 부하·메타 오버헤드가 큼.
2. **빌드 시간** — UProperty 등록 코드가 UCLASS 메타에 합쳐져 컴파일 시간 증가.
3. **API 일관성** — 프로퍼티는 객체가 아니라 메타 정보 — UObject 라이프사이클이 의미 없음.

호환성을 위해 **`UnrealTypePrivate.h` 안에 옛 UProperty 사슬이 남아 있다**. 옛 직렬화 데이터 / BP CDO / UPROPERTY 핫 리로드 / 옛 모듈 호환에 사용된다.

```cpp
// UnrealTypePrivate.h:14
#define USE_UPROPERTY_LOAD_DEFERRING (USE_CIRCULAR_DEPENDENCY_LOAD_DEFERRING && WITH_EDITORONLY_DATA)
```

이 가드를 보면 알 수 있듯, **주된 사용처가 에디터 빌드의 호환·로드 지연 처리**다.

---

## 2. 핵심 헤더와 클래스

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/UObject/UnrealTypePrivate.h` | `UCLASS(Abstract, Config=Engine) class UProperty : public UField` (L17) + 32개 자손 | 옛 UProperty 사슬 전체. UCLASS이므로 UObject·GC 대상. |

전체 33개 클래스 목록 (모두 `UnrealTypePrivate.h`):

```
UField (Class.h)
  └─ UProperty (L17)                                    [Abstract, Config=Engine]
       ├─ UNumericProperty (L185)
       │    ├─ UByteProperty   (L205)
       │    ├─ UInt8Property   (L238)
       │    ├─ UInt16Property  (L260)
       │    ├─ UIntProperty    (L282)        // int32
       │    ├─ UInt64Property  (L304)
       │    ├─ UUInt16Property (L326)
       │    ├─ UUInt32Property (L348)
       │    ├─ UUInt64Property (L365)
       │    ├─ UFloatProperty  (L387)
       │    └─ UDoubleProperty (L409)
       ├─ UBoolProperty   (L431)
       ├─ UObjectPropertyBase (L499)
       │    ├─ UObjectProperty (L537)
       │    │    └─ UClassProperty (L623)
       │    ├─ UWeakObjectProperty (L559)
       │    ├─ ULazyObjectProperty (L581)
       │    └─ USoftObjectProperty (L603)
       │         └─ USoftClassProperty (L672)
       ├─ UInterfaceProperty       (L719)
       ├─ UNameProperty            (L768)
       ├─ UStrProperty             (L790)
       ├─ UArrayProperty           (L812)
       ├─ UMapProperty             (L843)
       ├─ USetProperty             (L868)
       ├─ UStructProperty          (L891)
       ├─ UDelegateProperty        (L914)
       ├─ UMulticastDelegateProperty (L948)
       │    ├─ UMulticastInlineDelegateProperty (L976)
       │    └─ UMulticastSparseDelegateProperty (L998)
       ├─ UEnumProperty            (L1022)
       └─ UTextProperty            (L1045)
```

각각은 `FProperty` 사슬에 대응되는 변형이 있다 (보통 `U` → `F` 로 이름 한 글자만 바뀜).

---

## 3. UProperty ↔ FProperty 매핑 표

| 옛 (UProperty 계열) | 신 (FProperty 계열) | 헤더 (신) |
|---------------------|---------------------|-----------|
| `UProperty` | `FProperty` | `UnrealType.h:173` |
| `UNumericProperty` | `FNumericProperty` | `UnrealType.h:1765` |
| `UByteProperty` | `FByteProperty` | `UnrealType.h` |
| `UInt8Property` | `FInt8Property` | `UnrealType.h` |
| `UInt16Property` | `FInt16Property` | `UnrealType.h` |
| `UIntProperty` | `FIntProperty` (int32) | `UnrealType.h` |
| `UInt64Property` | `FInt64Property` | `UnrealType.h` |
| `UUInt16Property` | `FUInt16Property` | `UnrealType.h` |
| `UUInt32Property` | `FUInt32Property` | `UnrealType.h` |
| `UUInt64Property` | `FUInt64Property` | `UnrealType.h` |
| `UFloatProperty` | `FFloatProperty` | `UnrealType.h` |
| `UDoubleProperty` | `FDoubleProperty` | `UnrealType.h` |
| `UBoolProperty` | `FBoolProperty` | `UnrealType.h:2542` |
| `UObjectPropertyBase` | `TFObjectPropertyBase<TObjectPtr<UObject>>` | `UnrealType.h` |
| `UObjectProperty` | `FObjectProperty` | `UnrealType.h:3086` |
| `UClassProperty` | `FClassProperty` | `UnrealType.h` |
| `UWeakObjectProperty` | `FWeakObjectProperty` | `UnrealType.h` |
| `ULazyObjectProperty` | `FLazyObjectProperty` | `UnrealType.h` |
| `USoftObjectProperty` | `FSoftObjectProperty` | `UnrealType.h` |
| `USoftClassProperty` | `FSoftClassProperty` | `UnrealType.h` |
| `UInterfaceProperty` | `FInterfaceProperty` | `UnrealType.h:3560` |
| `UNameProperty` | `FNameProperty` | `UnrealType.h` |
| `UStrProperty` | `FStrProperty` | `StrProperty.h` |
| `UArrayProperty` | `FArrayProperty` | `UnrealType.h:3701` |
| `UMapProperty` | `FMapProperty` | `UnrealType.h` |
| `USetProperty` | `FSetProperty` | `UnrealType.h` |
| `UStructProperty` | `FStructProperty` | `UnrealType.h:6305` |
| `UDelegateProperty` | `FDelegateProperty` | `UnrealType.h` |
| `UMulticastDelegateProperty` | `FMulticastDelegateProperty` | `UnrealType.h` |
| `UMulticastInlineDelegateProperty` | `FMulticastInlineDelegateProperty` | `UnrealType.h` |
| `UMulticastSparseDelegateProperty` | `FMulticastSparseDelegateProperty` | `UnrealType.h` |
| `UEnumProperty` | `FEnumProperty` | `EnumProperty.h` |
| `UTextProperty` | `FTextProperty` | `TextProperty.h` |

---

## 4. 마이그레이션 가이드

### 4.1 캐스트

```cpp
// 옛 코드:
if (UObjectProperty* OP = Cast<UObjectProperty>(SomeUProp))
{
    UObject* Obj = OP->GetObjectPropertyValue(Container);
}

// 신 코드 (FProperty 사슬 + CastField):
if (FObjectProperty* OP = CastField<FObjectProperty>(SomeFProp))
{
    UObject* Obj = OP->GetObjectPropertyValue(Container);
}
```

`Cast<T>` 는 UObject 캐스트, `CastField<T>` 는 FField 캐스트. **헷갈리면 컴파일 에러로 알려준다.**

### 4.2 순회

```cpp
// 옛 코드:
for (TFieldIterator<UProperty> It(C); It; ++It) { /* ... */ }

// 신 코드:
for (TFieldIterator<FProperty> It(C); It; ++It) { /* ... */ }
```

`TFieldIterator<T>` 는 둘 다 받지만 `T = FProperty` 가 권장.

### 4.3 멤버 변경

UProperty 시절의 일부 멤버는 FField 베이스로 옮겨졌다:

| 옛 (UProperty.h 멤버) | 신 (FField/FProperty 멤버) |
|------------------------|--------------------------|
| `Property->GetName()` | 동일 (FField에서 상속) |
| `Property->GetFName()` | 동일 (`FField.h:526`) |
| `Property->GetOuter()` | `Property->GetOwner<UField>()` 또는 `GetOwnerStruct()` |
| `Property->ContainerPtrToValuePtr<T>(Container)` | 동일 |
| `Property->GetMetaData(Key)` | 동일 (`FField.h:930·931`) |
| `Property->ArrayDim` | 동일 (UnrealTypePrivate.h:23) |
| `Property->ElementSize` | 동일 |
| `Property->PropertyFlags` | 동일 (`EPropertyFlags`) |

### 4.4 BP/리플렉션 코드

옛 BP 노드 코드(`UK2Node_*`, `FBlueprintCompiler*`)는 `UProperty*` 를 다뤘지만 5.x에선 `FProperty*` 로 변환 — 보통 자동. 사용자 정의 K2Node 가 있다면 검토 필요.

### 4.5 직렬화 호환

옛 패키지(.uasset)에 UProperty 미러로 저장된 데이터는 자동으로 FProperty로 컨버트된다 — `UStruct::ConvertUFieldsToFFields()` (Class.h:985) 가 그 작업. 일반 게임 코드에서 직접 호출 안 함.

---

## 5. 가상 함수 (오버라이드 포인트)

`UProperty` 계열도 자체 virtual 을 가지지만, **신규 override는 의미 없다** — 엔진 내부에서만 사용. 구현 패턴은 `FProperty` 의 PURE_VIRTUAL 과 거의 1:1 대응이다 ([`Property/`](../Property/SKILL.md) §4.1).

`UProperty` 자체는 `UCLASS(Abstract, Config=Engine)` 로 선언되어 ini 백킹이 된다 (옛 호환 — 신규엔 무관).

---

## 6. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `UnrealTypePrivate.h` 전체 🛠 (실용) | (헤더) | (런타임 컴파일은 되지만 주 사용처가 에디터·옛 호환) | `USE_UPROPERTY_LOAD_DEFERRING` 가 `WITH_EDITORONLY_DATA` 의존. |
| `UProperty 33개 사슬` 🛠 (실용) | UnrealTypePrivate.h | 동상 | 신규 코드는 만지지 말 것. |

> 신규 코드에서 `UProperty*` 가 보이면 99% **옛 코드를 그대로 옮겨온 흔적**이다. `FProperty*` 로 교체해야 한다.

---

## 7. 관련 sub-skill

- [`Property/`](../Property/SKILL.md) — `FProperty` 사슬과 사용 API (마이그레이션 후 권장 사용)
- [`Reflection/`](../Reflection/SKILL.md) — `UStruct::ConvertUFieldsToFFields()` 자동 변환
