---
title: "FStructProperty Cast 타입 안전성 — ContainerPtrToValuePtr<T> dangling 위험"
kind: concept
status: stable
severity: "★★★"
tags: [reflection, fproperty, dangling, MMA-37, hazard, ue-574, foundation]
created: 2026-05-22
last_updated: 2026-05-27
audit_5_5_4: pass-pattern-stable  # 2026-05-27 Phase 2 audit · raw dual-confirmed
---

# FStructProperty Cast 타입 안전성 — `ContainerPtrToValuePtr<T>` dangling 위험

## 정의

`FStructProperty::ContainerPtrToValuePtr<T>(Object)` 는 **caller 가 명시한 타입 T 가 실제 struct 와 일치한다는 가정** 하에 raw 포인터를 반환한다. T 가 실제 struct 와 다르면 **타입 오해석**으로 dangling 포인터 / 잘못된 멤버 read / crash 가 발생한다. `FStructProperty::Struct` 를 *반드시* 검사한 뒤에야 cast 해야 안전하다.

특히 UE Material Expression 의 input 필드를 reflection 으로 순회할 때:
- `FExpressionInput` 만 안전한 cast 대상
- `FColorMaterialInput` / `FVectorMaterialInput` / `FScalarMaterialInput` 등 derived input 도 layout 호환이지만 *별도 struct name* 으로 등록되어 있을 수 있음
- 무관한 struct (`FLinearColor`, `FVector`, `FRotator`, …) 가 같이 잡히면 → 메모리 잘못 읽음

## 자세히

### 사례: MCMaterialAuto v0.14.12 dangling crash

🟢 **VAULT** — MMA-37 hazard 로그:

초기 코드 (위험):
```cpp
for (TFieldIterator<FStructProperty> It(Expr->GetClass()); It; ++It)
{
    FStructProperty* StructProp = *It;
    FExpressionInput* In = StructProp->ContainerPtrToValuePtr<FExpressionInput>(Expr);
    if (In && In->Expression)   // ← In->Expression 이 dangling
    {
        // ...
    }
}
```

**문제**:
1. `TFieldIterator<FStructProperty>` 는 모든 USTRUCT 속성을 잡음 — `FLinearColor`, `FVector2D`, custom struct 등 포함
2. `ContainerPtrToValuePtr<FExpressionInput>` 는 raw memory 를 `FExpressionInput*` 로 *재해석* — 타입 미일치 시 `In->Expression` 위치에 임의 비트가 들어옴
3. 그 비트가 우연히 valid pointer 처럼 보이면 → `UObject::IsValidLowLevel()` (UObject 의 method) 도 통과할 수 있음 (드물게)
4. dereference → crash 또는 silent wrong value

### Fix (MCMaterialAuto v0.14.13 채택)

```cpp
static const FName ExpressionInputName(TEXT("ExpressionInput"));

for (TFieldIterator<FStructProperty> It(Expr->GetClass()); It; ++It)
{
    FStructProperty* StructProp = *It;
    if (!StructProp || !StructProp->Struct) continue;
    if (StructProp->Struct->GetFName() != ExpressionInputName) continue;   // ★ 핵심

    FExpressionInput* In = StructProp->ContainerPtrToValuePtr<FExpressionInput>(Expr);
    if (!In) continue;
    if (!In->Expression) continue;
    if (!In->Expression->IsValidLowLevel()) continue;                       // 이중 안전망

    // ... 안전한 사용
}
```

**핵심**: `StructProp->Struct->GetFName()` 으로 struct **이름 비교**.

🟡 **PARTIAL** — `UScriptStruct::StaticStruct()` 비교 (예: `StructProp->Struct == FExpressionInput::StaticStruct()`) 가 더 직관적이지만, **`FExpressionInput` 은 UStruct 가 아니라 plain C++ struct** (`USTRUCT()` 매크로 없음 — UPROPERTY metadata 만 reflection 등록됨). 따라서 `::StaticStruct()` 호출 불가능. **이름 기반 비교만이 유일한 방법**.

### Derived input types

🔴 **INFERRED** — `FColorMaterialInput`, `FVectorMaterialInput`, `FScalarMaterialInput` 도 reflection 에 등록되어 있으면 `GetFName()` 이 각각 `"ColorMaterialInput"` 등으로 반환될 것. **포함 여부는 use case 별 결정**:
- MCMaterialAuto 의 `connect_expression_to_expression` 은 *generic* input 연결만 처리 — `FExpressionInput` 으로 한정해도 base class 멤버만 접근하므로 안전
- 만약 BaseColor 의 alpha 또는 vector 의 4th channel 까지 다루려면 derived type 별도 케이스 추가 필요

## 회피 패턴 (3-Layer Defense)

production code 의 권장 패턴:

```cpp
// Layer 1: Struct name match
if (StructProp->Struct->GetFName() != FName(TEXT("ExpressionInput"))) continue;

// Layer 2: Null check on cast result
FExpressionInput* In = StructProp->ContainerPtrToValuePtr<FExpressionInput>(Expr);
if (!In) continue;

// Layer 3: Pointer validity (UObject)
if (!In->Expression || !In->Expression->IsValidLowLevel()) continue;
```

3개 모두 통과해야 dereference. 어느 하나라도 빠지면 dangling 가능.

## 변형 사례

1. **`TFieldIterator<FProperty>` (base class iter)**:
   - 모든 property type 잡음 — `FStructProperty` 외에 `FObjectProperty`, `FArrayProperty` 등도 포함
   - 더 broad → 더 위험. 항상 `Cast<FStructProperty>` + null check 우선.

2. **`FMapProperty` / `FArrayProperty` 내부 element type**:
   - container element 도 동일 원리 — element struct name 검사 필수
   - `FScriptArrayHelper` 사용 시 inner property 의 struct name 까지 확인

3. **UEnum reflection 도 유사 위험**:
   - `GetValueByName` 의 prefix qualification — `concepts/UEnum-GetValueByName-FullyQualified` 참조

## 관련 entity

- [[FStructProperty]]
- [[FProperty]]
- [[TFieldIterator]]
- [[FExpressionInput]] (plain C++ struct, not USTRUCT)
- [[UMaterialExpression]]
- [[UObject]] (`IsValidLowLevel()` method — 본문 inline)

## 열린 질문

1. ❓ UE 5.7 이 `FExpressionInput` 의 derived input 들을 reflection 시스템에 자동 등록하는지 — `FColorMaterialInput` etc. 의 정확한 `GetFName()` 값 미확인. 실제 검증 필요.
2. ❓ `ContainerPtrToValuePtr` 의 base-cast 안전성 — base 타입 (`FExpressionInput`) 으로 derived 객체 cast 는 layout-compatible 한지 UE 코드 컨벤션 미특정.
3. ❓ Editor-only types (예: `FMaterialInput<T>` template) 의 reflection 등록 패턴 — template instantiation 마다 별도 USTRUCT 등록인지 미확인.

## Cross-link

- `concepts/Material-Editor-External-Change-Reopen` (같은 v0.14 작업)
- `concepts/UEnum-GetValueByName-FullyQualified` (유사 reflection hazard)
- `synthesis/UE-Reflection-Type-Safety-Patterns` (TODO — reflection 관련 hazard 합성)
- `00_meta/03_EvaluatorRecipe` § Stage 4 (Type-Safety 검증)

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| `ContainerPtrToValuePtr` 는 타입 가정 reinterpret | 🟢 VAULT | `entities/FStructProperty` |
| `FExpressionInput` 은 plain C++ struct (USTRUCT 아님) | 🟢 VAULT | UE 5.7 소스 `MaterialExpressionIO.h` 직접 확인 |
| `::StaticStruct()` 사용 불가 — 이름 기반만 유일 방법 | 🟢 VAULT | 위와 동일 |
| Derived input types 의 자동 등록 | 🔴 INFERRED | 실측 미완 |
| `IsValidLowLevel()` 추가가 dangling 완전 차단 | 🟡 PARTIAL | 일반 UE 패턴이지만 race 상황 미검증 |

## 변경 이력

- 2026-05-22: 초안 작성 (MMA-37 fix 직후, dangling crash → struct name match + IsValidLowLevel 채택본 기반)
- 2026-05-22: cross-link 정리 — `UObject::IsValidLowLevel` link → `[[UObject]]` + method 명시 inline
## §X. 5.5.4 Audit Status (2026-05-27)

> Phase 2 audit · [[synthesis/phase-2-audit-14-concepts]] §3 · **결정: 🟢 Group A — pass-pattern-stable**

FStructProperty reflection 패턴 (raw 4→4 동일 + MaterialExpressionIO 관련 `StructUtils.md` raw 확인). reinterpret-cast 안전성 / `::StaticStruct()` 제약은 CoreUObject 기초 — minor patch 통과.

원본 🟢 VAULT marker 는 5.7.4 시점 engine grep 사실로 *그대로 보존*. 5.5.4 에서 동일 결론 유효 — pattern 자체가 minor patch 사이 변동 없음.

**Audit pending (선택)**: line number / 특정 hit count 가 5.5.4 에서 정확히 같은지 검증하려면 `C:\Unreal\UnrealEngine\Engine\Source\` 직접 grep. 본 audit 에서는 pattern 결론만 검증, 정량 라인은 후속 작업으로 분리.
