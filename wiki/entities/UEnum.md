---
title: "UEnum"
kind: entity
status: stub
parent: foundation
tags: [foundation, reflection, enum, uobject, ue-574]
module: CoreUObject
header: "Public/UObject/UnrealType.h"
created: 2026-05-22
last_updated: 2026-05-22
---

# UEnum

C++ `enum class` 의 **reflection 표현 UObject**. UENUM() 매크로로 마킹된 enum 은 UnrealHeaderTool 이 UEnum 인스턴스를 자동 생성하고 `StaticEnum<TEnum>()` template 으로 접근 가능. Blueprint dropdown, asset serialization, property editor combo box 등 모두 UEnum 메타데이터 사용.

## 핵심 특성

- **Fully-qualified naming**: enum 값의 internal name 은 `EnumTypeName::EnumValueName` 형식 — 짧은 이름 lookup 은 INDEX_NONE (silent failure)
- **Display name 분리**: `DisplayName` metadata 로 화면 표시 이름 별도 지정 가능
- **MAX sentinel**: 마지막 enum 값에 자동 `_MAX` 추가 (counting 용)

## 주요 API

| API | 설명 |
|---|---|
| `StaticEnum<TEnum>()` | template specialization — UEnum* 반환 |
| `GetValueByName(FName)` | **fully-qualified name** 필수, 짧은 이름 → `INDEX_NONE` |
| `GetIndexByName(FName)` | index 반환 (value 와 다름) |
| `GetNameByValue(int64)` | fully-qualified name 반환 |
| `GetDisplayNameTextByValue(int64)` | DisplayName metadata 적용된 FText |
| `NumEnums()` | enum 값 개수 (_MAX 포함) |
| `CppType` | C++ type 이름 (namespace 포함) |

## 사용 패턴

- **MCP/JSON 입력 처리**: 사용자 문자열 → enum value 변환 시 [[concepts/UEnum-GetValueByName-FullyQualified]] 패턴 의무 (TMap 사전 정의 권고)
- **Blueprint dropdown**: BlueprintType UENUM 으로 마킹 시 BP 에서 자동 dropdown
- **Asset serialization**: SaveGame, JSON export, ImportText/ExportText

## 관련 함정

- [[concepts/UEnum-GetValueByName-FullyQualified]] — 짧은 이름 silent failure
- BlueprintType 미명시 시 BP 노드에서 사용 불가
- `_MAX` sentinel 값을 game logic 에서 실수로 사용하지 않도록 주의

## 관련 entity

- [[FName]] · [[FProperty]] · [[UClass]] · [[UObject]]

## Citation Disclosure

| 주장 | Tier |
|---|---|
| `GetValueByName` fully-qualified 요구 | 🟢 VAULT (`UnrealType.cpp` 직접 확인) |
| `StaticEnum<T>()` template specialization | 🟢 VAULT |
| `_MAX` sentinel 자동 추가 | 🟢 VAULT |
| `CppType` 정확한 형식 (namespace) | 🔴 INFERRED |

## 변경 이력

- 2026-05-22: stub 작성 (MMA-32 filing-back cross-link)
