---
title: "UE MetaSpecifier LongPath Requirement — UE 5.5+ UPROPERTY meta 강제"
kind: concept
status: stable
severity: "★"
tags: [ue, uproperty, meta-specifier, uht, ue-5.5, migration, hazard]
related_concepts: []
related_synthesis: []
created: 2026-05-26
last_updated: 2026-05-26
---

# UE MetaSpecifier LongPath Requirement

> **유래**: KMCProject Phase 1a 빌드 cycle (2026-05-25). `MetaStruct="MCDataBase"` short name → UHT 거부.

## 정의

UE 5.5+ 의 UHT (UnrealHeaderTool) 가 UPROPERTY meta specifier 의 *클래스/구조체 참조* 에 **long path format 강제**. Short name (`MCDataBase`) / F-prefix (`FMCDataBase`) 거부 → `not a valid long path name` 에러.

대상 meta specifier:
- `MetaStruct=` (USTRUCT picker 의 베이스 필터)
- `MetaClass=` (UCLASS picker 의 베이스 필터)
- `RowType=` (DataTable RowStruct 필터)
- `AllowedClasses=` (asset picker 의 허용 클래스 list)
- 기타 *클래스/구조체 참조* meta 일반

## 자세히

### 사례 — MCTableRegistry.h (KMCProject Phase 1a)

🟢 **VAULT** — KMCProject 실측.

**위반 코드**:
```cpp
UPROPERTY(EditAnywhere, Category="MC|Table", meta=(MetaStruct="MCDataBase"))
TObjectPtr<UScriptStruct> ExpectedRowStruct = nullptr;
```

**UHT 에러**:
```
MCTableRegistry.h(69): error : MetaData MetaStruct on ExpectedRowStruct has value 'MCDataBase'
which is not a valid long path name. Did you mean '/Script/MCPlayModule.MCDataBase' ?
```

**Fix**:
```cpp
UPROPERTY(EditAnywhere, Category="MC|Table",
    meta=(MetaStruct="/Script/MCPlayModule.MCDataBase"))
TObjectPtr<UScriptStruct> ExpectedRowStruct = nullptr;
```

## Long path format

```
/Script/<ModuleName>.<TypeName>
```

규칙:
- `/Script/` prefix — C++ 정의 type (BP 정의는 `/Game/...`)
- `<ModuleName>` — Build.cs 의 module 이름 (e.g. `MCPlayModule`, `Engine`, `CoreUObject`)
- `<TypeName>` — *F/U/A prefix 제외* (reflection 시스템 안 이름)

### 예시

```cpp
// C++ USTRUCT FMCDataBase (MCPlayModule)
meta=(MetaStruct="/Script/MCPlayModule.MCDataBase")          // ✅ F 제외

// C++ UCLASS UMCStoryAsset (MCPlayModule)
meta=(MetaClass="/Script/MCPlayModule.MCStoryAsset")         // ✅ U 제외

// Engine 클래스 AActor (Engine module)
meta=(MetaClass="/Script/Engine.Actor")                       // ✅ A 제외

// BP 정의 USTRUCT
meta=(MetaStruct="/Game/MyContent/MyBPStruct.MyBPStruct")    // /Game/ prefix
```

## 위반 패턴 (UE 5.5+ 거부)

```cpp
meta=(MetaStruct="MCDataBase")          // ❌ short name
meta=(MetaStruct="FMCDataBase")         // ❌ F prefix 포함
meta=(MetaStruct="MCPlayModule.MCDataBase")   // ❌ /Script/ prefix 누락
meta=(MetaStruct="/Script/MCDataBase")  // ❌ module name 누락
meta=(MetaClass="UMCStoryAsset")        // ❌ U prefix 포함
```

UHT 가 모두 거부 — `not a valid long path name` 에러.

## UE 5.4 이전 호환성

UE 5.4 까지 short name 도 허용됐던 것으로 추정 (🟡 PARTIAL — 정확 버전 미확정). 5.5 migration 시 모든 UPROPERTY meta specifier 검수 의무.

## 회피

### Layer 1: 코드 작성 시 처음부터 long path

```cpp
meta=(MetaStruct="/Script/<ModuleName>.<TypeName>")
```

주석으로 module name + type name 명시:
```cpp
// meta=(MetaStruct="/Script/MCPlayModule.MCDataBase") — F prefix 제외 의무.
UPROPERTY(EditAnywhere, meta=(MetaStruct="/Script/MCPlayModule.MCDataBase"))
TObjectPtr<UScriptStruct> ExpectedRowStruct;
```

### Layer 2: grep 으로 audit

```
Grep "MetaStruct=|MetaClass=|RowType=" Source/
```

각 result 의 값이 `/Script/<Module>.<Type>` format 인지 확인. Short name → 즉시 fix.

### Layer 3: UHT 에러 메시지 활용

UHT 가 *suggested fix* 를 제공 — `Did you mean '/Script/<Module>.<Type>' ?` — 그대로 적용.

### Layer 4: PR review 체크리스트

UPROPERTY 의 모든 meta specifier 의 클래스/구조체 참조 값을 review 시 long-path 형식 확인.

## 다른 meta specifier — 영향 없음

```cpp
// 일반 value 또는 enum — long path 무관
meta=(ClampMin="0", ClampMax="100")           // ✅ 숫자 literal
meta=(EditCondition="bEnableFoo")             // ✅ property name
meta=(DisplayName="My Property")              // ✅ string literal
meta=(Tooltip="설명...")                       // ✅ string
meta=(ClampMin="0")                           // ✅ 숫자
```

→ *클래스/구조체 참조* 만 long-path 강제.

## 관련

- [[concepts/UE-Phantom-Header-Hallucination-Hazard]] (UHT 관련 함정 family)
- [[concepts/Reflection-System]] (UPROPERTY meta 시스템 일반)

## 열린 질문

1. ❓ UE 5.4 정확히 어느 시점부터 long-path 강제 — 5.4? 5.5? 5.6? 미확정.
2. ❓ Plugin module 의 type 도 같은 format (`/Script/PluginModuleName.Type`) — 검증 미수행 (KMCProject 는 plugin 0).
3. ❓ Anonymous USTRUCT / generic UClass의 meta — vault 미확정.

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| MCTableRegistry.h 실측 에러 | 🟢 VAULT | KMCProject Phase 1a 빌드 |
| Long path format /Script/Module.Type | 🟢 VAULT | UHT suggested fix + KMCProject fix 검증 |
| F/U/A prefix 제외 의무 | 🟢 VAULT | UE reflection 시스템 표준 |
| UE 5.5+ 강제 정확 버전 | 🟡 PARTIAL | UE 5.4 까지 허용 추정 — 미검증 |
| Plugin module 동일 format | 🔴 INFERRED | 미검증 |

## 변경 이력

- 2026-05-26: 초안 작성. KMCProject Phase 1a 빌드 cycle 발견 — MetaStruct short name 거부. Phase 3 작업 회고 cycle filing-back.
