---
title: UE LiveCoding Cpp-Only Trigger Hazard
slug: UE-LiveCoding-CppOnly-Trigger-Hazard
kind: concept
status: live
confidence: 🟡 PARTIAL
last_updated: 2026-05-27
audit_5_5_4: partial-impl-expanded  # 2026-05-27 Phase 2 engine grep 완료
engine_version: 5.5.4
related_concepts:
  - UE-LiveCoding-Module-Path-Hazard
  - Unity-Build-Include-Cascade
related_synthesis:
  - mc-datatable-auto-blueprint
  - mc-datatable-auto-build-cycle-postmortem
tags: [livecoding, unity-build, header-only, ustruct, ide-rebuild, autocompile]
sources:
  - "C:/Unreal/UnrealEngine/Engine/Source/Developer/Windows/LiveCoding/Public/ILiveCodingModule.h"
---

# UE LiveCoding Cpp-Only Trigger Hazard

## 한 줄 요약

**Live Coding 은 일반적으로 *.cpp 변경 감지* 기반 → *.h-only 신규 추가* (예: USTRUCT 만 있는 헤더) 는 무시 가능.** 새 reflection 타입을 활성화하려면 *.cpp 페어 추가* / *기존 cpp 더미 변경* / *IDE 전체 Rebuild* 중 하나가 필요.

## 권위 (🟡 PARTIAL)

`ILiveCodingModule` API ([[concepts/UE-LiveCoding-Module-Path-Hazard]]) 는 `Compile()` / `OnPatchComplete` 만 제공 — *어떤 파일이 trigger 되는지* 는 internal Live++ (Molecular Matters) 기술. UE Live Coding 의 내부 file watcher 는 컴파일 단위 (translation unit) 기반 — **.cpp 만 추적**, .h 단독 추가는 unity build cascade 의무이지만 .cpp 변경 trigger 없으면 무시.

🟡 PARTIAL — Engine 본가 grep 결과 internal Live++ source 는 외부 공개 X. *경험적 관찰 + MCMaterialAuto 사례 + UE 5.x 일반 거동* 추론.

## 함정 family

### 1. MCDataTableAuto generate_row_struct case (✅ 직접 관찰)

```cpp
// Phase 3c-3 4차 — Source/KMCProject/MCPlayModule/MCGame/MCData_<Name>.h
USTRUCT(BlueprintType)
struct FMCData_<Name> : public FMCDataBase {
    GENERATED_BODY()
    UPROPERTY(EditAnywhere) int32 TableID;
    // ...
};
```

cpp 페어 *없음* — 순수 .h-only USTRUCT.

Live Coding `Compile()` 호출 → **NoChanges** 반환 가능 (변경 trigger cpp 없음) → `OnPatchComplete` 미발생 → 자동 재시도 흐름 차단 → 사용자 IDE Rebuild 강제.

### 2. 관찰된 동작 (UE 5.7.4 + KMCProject)

| 변경 종류 | Live Coding 결과 |
|---|---|
| 기존 .cpp 함수 body 수정 | ✅ patch 정상 |
| 기존 .cpp 에 새 함수 추가 + .h 선언 | ✅ 둘 다 patch |
| .h-only 신규 USTRUCT 파일 | 🟡 보통 NoChanges (cpp trigger 없음) |
| 기존 .h 에 UPROPERTY 추가 (cpp 변경 없음) | 🟡 무시 가능 |
| 기존 .cpp 와 페어인 새 .h struct | ✅ unity build cascade |

### 3. 회피 패턴

#### A. 더미 .cpp 페어 생성 (UE 의무는 아니지만 trigger 보장)

```cpp
// MCData_<Name>.cpp
#include "MCData_<Name>.h"
// (empty body — Live Coding trigger 용)
```

generate_row_struct 가 .h 와 함께 빈 .cpp 도 생성하면 Live Coding 이 trigger 됨.

#### B. 기존 .cpp 더미 변경 (의도 위험)

`MCDataBase.cpp` 등 기존 파일에 *공백 라인 추가* → 모든 reflection 갱신. 단, 의도하지 않은 변경 추적 어려움.

#### C. IDE 전체 Rebuild (확실한 해결책)

Visual Studio Ctrl+Shift+B 또는 Development Editor 빌드 → 전체 unity build 재실행 → 모든 .h reflection 통합. UE 재기동 후 새 USTRUCT 활성.

#### D. UUserDefinedStruct 동적 생성 (Live Coding 우회)

C++ 컴파일 cycle 자체를 우회 — Editor runtime 안에서 `UUserDefinedStruct` 동적 생성 → 즉시 사용 가능. 단점: BP 친화 / C++ 코드 부재 → versioning 약함.

MCDataTableAuto v0.2 후보 — 자동 row struct 생성에서 .h 대신 UDS 시도.

## MCDataTableAuto 적용 흐름

Phase 3c-3 후속 (2026-05-26) — `TryImmediateAutoRetryAfterSkip` 의 sub-B (RowStruct 미활성) 분기 정식화:

1. generate_row_struct → .h-only 파일 작성 → Live Coding 트리거 (auto)
2. **Live Coding NoChanges 가능** → OnPatchComplete 미발생 → 자동 재시도 차단
3. 사용자 widget log broadcast: *"IDE Rebuild 후 일괄 생성 재클릭"*
4. 사용자 manual IDE Rebuild → UE 재기동 → RowStruct path 활성 → 일괄 생성 재클릭 → sub-A → 자동 재시도 진행 ✅

## Citation Rule 회피 절차

`Compile()` 호출 후 *변경 trigger 가 실제로 일어났는지* 확신 어려움 — Live Coding internal 은 closed source. **권장 절차**:

1. Live Coding 트리거 + `OnPatchComplete` arm (정상 trigger case)
2. 동시에 사용자에게 *IDE Rebuild* fallback 안내 (NoChanges case 대비)
3. 자동 재시도 후 `FindObject<UScriptStruct>` 으로 활성 여부 *실측 확인* (sub-A / sub-B 분기)

## 변경 이력

- **2026-05-26** — 신규 작성. MCDataTableAuto Phase 3c-3 후속 sub-B 발견 case 정식화. confidence: 🟡 PARTIAL — Live Coding internal closed source.
## §X. 5.5.4 Audit Status (2026-05-27) — engine grep 완료

> Phase 2 audit · [[synthesis/phase-2-audit-14-concepts]] §3·§5 · **결정**: partial-impl-expanded

**검증 결과 (engine source dual-grep, 2026-05-27)**:

- LiveCoding module 위치: `Source/Developer/Windows/LiveCoding/` — 양 버전 동일 경로
- Private sources: 5.5.4 **7 files** vs 5.7.4 **9 files** (5.7.4 가 2개 더)
- 핵심 동작 (`.cpp` trigger / `.h-only` 무시) 자체는 LiveCoding 의 본질 — 5.5.4 에서도 동일 패턴 추정
- **결정**: 🟡 PARTIAL — 핵심 동작은 양쪽 stable 추정이지만 5.7.4 의 2 신규 file 이 어떤 추가 기능/edge case 를 도입했는지 미확인. 5.5.4 환경에서 본 페이지 hazard 적용 시 추가 verify 권장.

> 본 audit 는 5.5.4 + 5.7.4 engine source 직접 grep 으로 수행 (2026-05-27). `[[raw/ue-wiki-llm/...]]` 인용은 5.7.4 vintage 자료 보존, 새 검증은 engine source 본가 기반.
