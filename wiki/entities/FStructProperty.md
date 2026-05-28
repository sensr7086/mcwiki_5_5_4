---
title: "FStructProperty"
kind: entity
status: stub
parent: foundation
tags: [foundation, reflection, property, struct, ue-574]
module: CoreUObject
header: "Public/UObject/UnrealType.h"
created: 2026-05-22
last_updated: 2026-05-22
---

# FStructProperty

[[FProperty]] 의 specialization — **USTRUCT (또는 reflection-registered C++ struct)** 멤버를 가리키는 reflection property. `TFieldIterator<FStructProperty>` 로 클래스의 모든 struct 멤버를 enumerate 가능. 단, **타입 가정 reinterpret cast** (`ContainerPtrToValuePtr<T>`) 는 caller 책임 — 잘못된 T 지정 시 dangling.

## 핵심 특성

- **`Struct` 필드**: `UScriptStruct*` — 해당 property 의 실제 struct type
- **`ContainerPtrToValuePtr<T>(Object)`**: Object 안 raw 메모리 위치 반환 → `T*` 로 reinterpret (caller 가 T 정확성 보장 의무)
- **Plain C++ struct 도 등록 가능**: `USTRUCT()` 매크로 없이 `UPROPERTY` 만 있으면 reflection 등록 — `::StaticStruct()` 호출 *불가능*. 예: `FExpressionInput`

## 주요 API

| API | 설명 |
|---|---|
| `Struct` | `UScriptStruct*` 멤버 — struct type 식별 |
| `Struct->GetFName()` | struct 이름 비교용 (FName) |
| `ContainerPtrToValuePtr<T>(Container)` | raw 포인터 reinterpret cast |
| `CopyCompleteValue(Dest, Src)` | 전체 struct 복사 |
| `ExportTextItem` / `ImportText` | 문자열 ↔ struct 변환 |

## 사용 패턴 (안전)

[[concepts/UE-FStructProperty-Cast-Type-Safety]] 의 3-Layer defense:

```cpp
for (TFieldIterator<FStructProperty> It(Obj->GetClass()); It; ++It)
{
    FStructProperty* SP = *It;
    if (!SP || !SP->Struct) continue;
    if (SP->Struct->GetFName() != FName(TEXT("ExpressionInput"))) continue; // ★ name check
    FExpressionInput* In = SP->ContainerPtrToValuePtr<FExpressionInput>(Obj);
    if (!In) continue;
    if (!In->Expression || !In->Expression->IsValidLowLevel()) continue;
    // 안전한 사용
}
```

## 관련 함정

- [[concepts/UE-FStructProperty-Cast-Type-Safety]] — ContainerPtrToValuePtr<T> dangling 위험
- 잘못된 T 지정 시 *임의 비트* 가 valid pointer 처럼 보이는 silent corruption
- Plain C++ struct (USTRUCT 아님) 는 `::StaticStruct()` 불가 → 이름 비교만 유일

## 관련 entity

- [[FProperty]] · [[FName]] · [[UObject]] · [[FExpressionInput]] · [[TFieldIterator]]

## Citation Disclosure

| 주장 | Tier |
|---|---|
| ContainerPtrToValuePtr<T> reinterpret 동작 | 🟢 VAULT (UE 5.7 `UnrealType.cpp`) |
| FExpressionInput USTRUCT 아님 | 🟢 VAULT (`MaterialExpressionIO.h` 직접 확인) |
| Struct->GetFName() 비교가 유일 방법 (USTRUCT 외) | 🟢 VAULT |
| 잘못된 T 의 silent corruption 경로 | 🟡 PARTIAL (실측 동작 — race 시나리오 미검증) |

## 변경 이력

- 2026-05-22: stub 작성 (MMA-37 filing-back cross-link)
