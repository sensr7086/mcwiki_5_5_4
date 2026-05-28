---
title: "UMaterialExpression"
kind: entity
status: stub
parent: render
tags: [render, material, expression, node, ue-574]
module: Engine
header: "Public/Materials/MaterialExpression.h"
created: 2026-05-22
last_updated: 2026-05-22
---

# UMaterialExpression

Material 그래프 안의 **단일 노드 베이스 클래스**. Constant3Vector, TextureSample, MaterialFunctionCall, Multiply 등 모든 머티리얼 노드는 `UMaterialExpression` 상속. 그래프 안에서 input/output pin 으로 다른 expression 과 연결되어 셰이더 코드를 구성.

## 핵심 특성

- **Material 의 `Expressions` 배열** 에 포함됨 (직렬화 대상)
- **MaterialNode** (UMaterialGraphNode) 가 Slate 측 visualization 담당 — 별도 객체
- **Input pin**: `FExpressionInput` 또는 derived (`FColorMaterialInput` 등) 멤버로 표현
- **Output**: `EvaluatePin` / `Compile` virtual override 로 셰이더 코드 생성

## 주요 멤버

| 멤버 | 설명 |
|---|---|
| `MaterialExpressionEditorX/Y` | Editor 그래프 위치 (정수 픽셀) |
| `Material` | 소유 UMaterial (weak parent) |
| `Function` | (있을 시) 소유 UMaterialFunction |
| `bIsParameterExpression` | Parameter 노드 여부 (`UMaterialExpressionScalarParameter` 등) |

## 관련 함정

- [[concepts/Material-Editor-External-Change-Reopen]] — 외부에서 add/delete 후 UI refresh 3-Layer 의무
- [[concepts/UE-FStructProperty-Cast-Type-Safety]] — input pin 을 reflection 으로 enumerate 시 FExpressionInput 만 정확히 캐스트
- `GetInputs()` / `GetInputCount()` 같은 generic API 가 *없음* — derived 클래스마다 멤버 다름, reflection 통한 순회 필요

## 관련 entity

- [[UMaterial]] · [[UMaterialGraph]] · [[FExpressionInput]] · [[UMaterialEditingLibrary]]

## Citation Disclosure

| 주장 | Tier |
|---|---|
| `Expressions` 배열 직렬화 | 🟢 VAULT (UE 5.7 `Material.h`) |
| MaterialNode 별도 객체 | 🟢 VAULT |
| GetInputs/GetInputCount 부재 | 🟢 VAULT (MMA-37 빌드 실측) |
| Compile virtual 동작 | 🟡 PARTIAL (shader codegen 세부 미확인) |

## 변경 이력

- 2026-05-22: stub 작성 (MMA-37 / v0.14 filing-back cross-link)
