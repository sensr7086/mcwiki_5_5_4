---
title: "TFieldIterator"
kind: entity
status: stub
parent: foundation
tags: [foundation, reflection, iterator, template, ue-574]
module: CoreUObject
header: "Public/UObject/UnrealType.h"
created: 2026-05-22
last_updated: 2026-05-22
---

# TFieldIterator

UE reflection 시스템의 **template iterator** — UStruct (UClass / UScriptStruct / UFunction) 안의 모든 FProperty 멤버를 type-filtered 로 순회. `TFieldIterator<FStructProperty>` / `TFieldIterator<FObjectProperty>` / `TFieldIterator<FProperty>` 등으로 type narrowing 가능.

## 핵심 특성

- **Template specialization**: `TFieldIterator<T>` 에서 T 는 FProperty 의 subclass — 해당 subclass 만 반환
- **Super class traversal**: default 로 부모 클래스 properties 도 enumerate (옵션으로 disable 가능)
- **Read-only iteration**: const-correctness 안전, 멤버 mutation 은 cast 결과 통해 수행

## 주요 API

| API | 설명 |
|---|---|
| `TFieldIterator<T>(UStruct*)` | 생성자 — 순회 시작 |
| `operator*()` | 현재 property 반환 (`T*`) |
| `operator++()` | 다음 property |
| `operator bool()` | 더 있으면 true |
| `Iterator.GetStruct()` | 현재 reading 중인 UStruct |

## 사용 패턴

```cpp
// 모든 property 순회
for (TFieldIterator<FProperty> It(Obj->GetClass()); It; ++It)
{
    FProperty* P = *It;
    UE_LOG(LogTemp, Log, TEXT("%s: %s"), *P->GetName(), *P->GetCPPType());
}

// FStructProperty 만 — 추가 type check 의무
for (TFieldIterator<FStructProperty> It(Obj->GetClass()); It; ++It)
{
    FStructProperty* SP = *It;
    if (SP->Struct->GetFName() != FName(TEXT("ExpressionInput"))) continue;
    // ...
}
```

## 관련 함정

- [[concepts/UE-FStructProperty-Cast-Type-Safety]] — type-filtered iter 도 *struct type* 별도 검사 필요
- Super class traversal default 동작 — `EFieldIteratorFlags::ExcludeSuper` 명시 옵션 권고 (의도 명확화)
- Iter 중 GC 발생 시 UObject pointer dangling 위험 — `IsValidLowLevel` 검사 필요

## 관련 entity

- [[FProperty]] · [[FStructProperty]] · [[UClass]] · [[UObject]]

## Citation Disclosure

| 주장 | Tier |
|---|---|
| Template type-filtering | 🟢 VAULT (UE 5.7 `Field.h`) |
| Super class traversal default | 🟢 VAULT |
| ExcludeSuper flag 옵션 | 🟢 VAULT |
| GC 중 dangling 가능성 | 🟡 PARTIAL (이론상 가능, 실측 시나리오 미특정) |

## 변경 이력

- 2026-05-22: stub 작성 (MMA-37 filing-back cross-link)
