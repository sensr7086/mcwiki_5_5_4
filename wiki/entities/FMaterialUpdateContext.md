---
title: "FMaterialUpdateContext"
kind: entity
status: stub
parent: render
tags: [render, material, update, scope, ue-574]
module: Engine
header: "Public/Materials/MaterialInstanceSupport.h"
created: 2026-05-22
last_updated: 2026-05-22
---

# FMaterialUpdateContext

**Scoped RAII helper** — 머티리얼 변경을 묶어 **render thread + 사용처 모든 invalidation** 을 한번에 처리. constructor 에서 변경 시작, destructor 에서 dependent system (PSO cache / MaterialInstance / Component RenderState) 일괄 invalidate.

## 핵심 특성

- **Scope-based**: 함수 안 stack 변수로 선언 → 함수 종료 시 자동 invalidate
- **Bulk propagation**: 한번에 여러 머티리얼 묶어 효율적 처리
- **`UMaterial::PostEditChange` 내부 사용** — 일반 caller 는 직접 사용 드묾

## 주요 사용

```cpp
{
    FMaterialUpdateContext Ctx;
    Ctx.AddMaterial(M1);
    Ctx.AddMaterial(M2);
    M1->BaseColor = ...;
    M2->Roughness = ...;
}  // ← 여기서 일괄 invalidate
```

## 관련 함정

- 직접 사용 시 **scope 종료 시점 의도** — 변경 직후 즉시 invalidate 원하면 명시 destructor 호출
- 다수 머티리얼 묶을 때 PSO precache miss 증가 가능 — production 측정 필요

## 관련 entity

- [[UMaterial]] · [[UMaterialEditingLibrary]] · [[UPrimitiveComponent]] (RenderState invalidation 대상)

## Citation Disclosure

| 주장 | Tier |
|---|---|
| Scope-based RAII pattern | 🟢 VAULT (UE 5.7 `MaterialInstanceSupport.h`) |
| PostEditChange 내부 사용 | 🟡 PARTIAL (header 확인, 호출 site 정확 추적 미완) |
| Bulk propagation 효율 | 🔴 INFERRED |

## 변경 이력

- 2026-05-22: stub 작성 (MMA-33+34 filing-back cross-link)
