---
title: "FExpressionInput"
kind: entity
status: stub
parent: render
tags: [render, material, input-pin, plain-struct, ue-574]
module: Engine
header: "Public/Materials/MaterialExpressionIO.h"
created: 2026-05-22
last_updated: 2026-05-22
---

# FExpressionInput

UMaterialExpression 의 **input pin 표현 — plain C++ struct** (USTRUCT 매크로 *없음*). Material 그래프의 노드 간 연결을 표현. derived 타입 (`FColorMaterialInput`, `FVectorMaterialInput`, `FScalarMaterialInput`) 도 동일 layout 으로 확장.

## 핵심 특성

- **USTRUCT 아님** → `::StaticStruct()` 호출 *불가능*
- Reflection 등록은 UPROPERTY 메타데이터 통해서만 — `FStructProperty::Struct->GetFName() == "ExpressionInput"` 으로 식별
- **Derived input**: ColorMaterialInput / VectorMaterialInput / ScalarMaterialInput — layout 호환이지만 별도 struct name 으로 등록

## 주요 멤버

| 멤버 | 설명 |
|---|---|
| `Expression` | 연결된 UMaterialExpression* (input source) |
| `OutputIndex` | 출처 expression 의 output pin index |
| `Mask` | 채널 mask (R/G/B/A) |
| `MaskR/G/B/A` | 개별 채널 활성 여부 |
| `InputName` | UI 표시명 |

## 사용 패턴 (Reflection 안전)

[[concepts/UE-FStructProperty-Cast-Type-Safety]] 3-Layer defense:

```cpp
static const FName ExpressionInputName(TEXT("ExpressionInput"));
for (TFieldIterator<FStructProperty> It(Expr->GetClass()); It; ++It)
{
    if (It->Struct->GetFName() != ExpressionInputName) continue;
    FExpressionInput* In = It->ContainerPtrToValuePtr<FExpressionInput>(Expr);
    if (!In || !In->Expression || !In->Expression->IsValidLowLevel()) continue;
    // 안전한 사용
}
```

## 관련 함정

- [[concepts/UE-FStructProperty-Cast-Type-Safety]] — 잘못된 cast 시 dangling
- Derived input 들이 자동 reflection 등록되는지 미검증 — `GetFName()` 정확값 확인 필요

## 관련 entity

- [[UMaterialExpression]] · [[FStructProperty]] · [[UMaterial]] · [[UMaterialEditingLibrary]]

## Citation Disclosure

| 주장 | Tier |
|---|---|
| USTRUCT 아님 — plain C++ struct | 🟢 VAULT (UE 5.7 `MaterialExpressionIO.h` 직접 확인) |
| StaticStruct() 호출 불가 | 🟢 VAULT |
| Struct name 비교가 유일 식별법 | 🟢 VAULT |
| Derived input 자동 등록 | 🔴 INFERRED |

## 변경 이력

- 2026-05-22: stub 작성 (MMA-37 filing-back cross-link)
