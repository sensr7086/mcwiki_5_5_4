---
title: "FName"
kind: entity
status: stub
parent: foundation
tags: [foundation, string, name, identifier, hash, ue-574]
module: Core
header: "Public/UObject/NameTypes.h"
created: 2026-05-22
last_updated: 2026-05-22
---

# FName

UE 의 **case-insensitive, 해시 기반 고유 식별자 문자열**. UClass / UObject / UProperty / Asset / Tag 등 거의 모든 reflection 식별자가 FName 으로 저장된다. 같은 문자열은 *전역 string table* 에 1번만 저장되고 모든 FName 인스턴스는 그 entry 의 index 만 보유 → equality 비교 O(1), 메모리 매우 효율.

## 핵심 특성

- **Case-insensitive**: `FName("Foo") == FName("FOO")` 가 true
- **Display vs Comparison**: 화면 출력은 원본 case 유지 (`ToString`), 비교는 lowercase normalize
- **Hash O(1)**: equality / hash 모두 index 비교
- **Immutable**: 한번 생성된 FName 은 변경 불가

## 주요 API

| API | 설명 |
|---|---|
| `FName(TEXT("Name"))` | 생성 (string table 자동 등록) |
| `FName(NAME_None)` | 빈 FName (`NAME_None` 매크로) |
| `IsNone()` | 빈 FName 검사 |
| `ToString()` | display string 반환 (FString) |
| `Compare(Other)` | 비교 (less/equal/greater) |
| `operator==` / `operator!=` | equality 비교 — O(1) |

## 사용 패턴

- **Reflection lookup**: `UClass::FindFunctionByName(FName)`, `UEnum::GetValueByName(FName)`
- **Asset tag**: `FGameplayTag` 내부 표현, AssetRegistry tag/value 키
- **Dynamic property access**: `UStruct::FindPropertyByName(FName)`
- **Sub-object 식별**: `AActor::GetDefaultSubobjectByName(FName)`

## 관련 함정

- 동적 생성 FName 이 많으면 string table 비대 → 메모리 leak 유사 증상 (특히 generated names per-frame)
- Cooked build 에서는 string table 압축 적용 — debugging 시 raw index 만 보이는 경우 있음
- [[concepts/UEnum-GetValueByName-FullyQualified]] — FName lookup 시 fully-qualified prefix 요구 hazard

## 관련 entity

- [[FProperty]] · [[UClass]] · [[UObject]] · [[UEnum]] · [[FGameplayTag]]

## Citation Disclosure

| 주장 | Tier |
|---|---|
| Case-insensitive 비교 | 🟢 VAULT (UE 5.7 `NameTypes.h` 직접 확인) |
| String table 1번 등록 | 🟢 VAULT |
| Equality O(1) | 🟢 VAULT |
| Cooked 압축 동작 | 🔴 INFERRED (정확한 mechanism 미확인) |

## 변경 이력

- 2026-05-22: stub 작성 (MCMaterialAuto v0.14-0.17 filing-back cross-link 정합 — 19 broken link cycle)
