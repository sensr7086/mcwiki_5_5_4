---
title: "UMaterialEditingLibrary"
kind: entity
status: stub
parent: render
tags: [render, material, blueprint-library, editor, automation, ue-574]
module: UnrealEd
header: "Public/MaterialEditingLibrary.h"
created: 2026-05-22
last_updated: 2026-05-22
---

# UMaterialEditingLibrary

UE 5.7 의 **공식 머티리얼 자동화 라이브러리** — UFUNCTION(BlueprintCallable) 58종 + 정적 helper. Python / Blueprint / C++ MCP server 등 *editor 외부에서 머티리얼을 프로그래밍 방식으로 조작* 할 때 사용. Material / MaterialInstance / MaterialFunction 모두 지원.

## 핵심 카테고리

| 카테고리 | 주요 함수 |
|---|---|
| Expression 관리 | `CreateMaterialExpression` / `DeleteMaterialExpression` / `GetMaterialExpressions` |
| 연결 | `ConnectMaterialProperty` / `ConnectMaterialExpressions` / `DisconnectMaterialProperty` |
| Layout | `LayoutMaterialExpressions` |
| Compile | `RecompileMaterial` / `UpdateMaterialFunction` |
| MIC | `CreateMaterialInstance` / `SetMaterialInstanceScalarParameterValue` / `SetMaterialInstanceVectorParameterValue` / `SetMaterialInstanceTextureParameterValue` |
| MaterialFunction | `CreateMaterialFunction` / `AddFunctionInput` / `AddFunctionOutput` |

## ⭐ ConnectMaterialExpressions 의 Pin Name Shortening (v0.23 보강)

`ConnectMaterialExpressions(From, FromOut, To, ToInputName)` 의 `ToInputName` 비교가 *raw property name 그대로 안 됨*.

🟢 **VAULT** — `MaterialEditingLibrary.cpp:700` 호출 흐름:

```
ConnectMaterialExpressions
  → GetExpressionInputByName(To, FName(ToInputName))     // L700
    → for (FExpressionInputIterator) {                    // L57
        rawName = To->GetInputName(i)                     // property 이름
        testName = UMaterialGraphNode::GetShortenPinName(rawName)
        if (testName == ToInputName) return Input         // ★ 축약 이름으로 매치
      }
    → return nullptr;                                     // 매치 실패 → caller 가 false
```

**9개 매핑** — [[concepts/UE-Material-Pin-Name-Shortening]] 페이지:
- `Coordinates → UVs` / `TextureObject → Tex` / `Input → ""` (NAME_None)
- `Exponent → Exp` / `MipLevel → Level` / `MipBias → Bias`
- `AGreaterThanB → CompactAGreaterThanB` / `AEqualsB → CompactAEqualsB` / `ALessThanB → CompactALessThanB`

→ 외부 caller (LLM / Python / MCP) 는 reflection 으로 얻은 property name 을 직접 전달하면 9개 경우 거부 — *축약 이름으로 변환 후* 전달 의무.

## 사용 패턴

```cpp
// 새 머티리얼 + Constant3Vector + BaseColor 연결
UMaterial* M = MaterialFactory->FactoryCreateNew(...);
UMaterialExpressionConstant3Vector* C =
    Cast<UMaterialExpressionConstant3Vector>(
        UMaterialEditingLibrary::CreateMaterialExpression(M, UMaterialExpressionConstant3Vector::StaticClass()));
C->Constant = FLinearColor::Red;
UMaterialEditingLibrary::ConnectMaterialProperty(C, TEXT(""), MP_BaseColor);
UMaterialEditingLibrary::RecompileMaterial(M);
```

## 관련 함정

- ⭐⭐⭐ [[concepts/UE-Material-Pin-Name-Shortening]] — 9개 input pin name shortening hazard (`Exponent → Exp` 등) → caller 측 자동 정규화 의무
- 일부 API 는 **PostEditChange 자동 호출 없음** — caller 가 명시 호출 의무
- [[concepts/Material-Editor-External-Change-Reopen]] — Editor UI refresh 별도 책임
- `ConnectMaterialProperty` 는 BaseColor / Metallic 등 **MaterialProperty enum** 사용 — fully-qualified 또는 `MP_*` 매크로

## 관련 entity

- [[UMaterial]] · [[UMaterialExpression]] · [[UMaterialGraph]] · [[FExpressionInput]] · [[EMaterialProperty]]

## Citation Disclosure

| 주장 | Tier |
|---|---|
| 58 UFUNCTION 카탈로그 | 🟢 VAULT ([[sources/ue-render-material-editing-library]]) |
| PostEditChange 자동 호출 부재 | 🟡 PARTIAL (실측 — 일부 함수만 검증) |
| MP_* 매크로 권장 | 🟢 VAULT |
| ConnectMaterialExpressions 의 pin name shortening 호출 흐름 | 🟢 VAULT (MaterialEditingLibrary.cpp:45-78 + :700 직접 확인) |

## 변경 이력

- 2026-05-22: stub 작성 (Cycle 5p+1 ingest 와 cross-link)
- 2026-05-22: ConnectMaterialExpressions Pin Name Shortening 메커니즘 추가 (MMA-48 / v0.23 filing-back)
