---
title: "UE Delegate Lambda ParamCount Mismatch Hazard — Tuple/Invoke 지옥 template error"
kind: concept
status: stable
severity: "★★"
tags: [ue, delegate, lambda, template-error, hazard, ue-574]
related_concepts:
  - "[[concepts/UE-Phantom-Header-Hallucination-Hazard]]"
related_synthesis:
  - "[[synthesis/ue-llm-assumption-hazard-family]]"
created: 2026-05-26
last_updated: 2026-05-26
---

# UE Delegate Lambda ParamCount Mismatch Hazard

> **유래**: MCDataTableAuto Phase 3c-2 빌드 발견 (2026-05-26). `FInteractiveProcess::OnCompleted` 의 람다에 bool 인자 누락 → C2672 cascade.

## 정의

UE delegate 의 `BindLambda` / `AddLambda` 시 람다 인자 개수가 *declared delegate* 의 ParamCount 와 mismatch 면 컴파일 실패. 증상은 *Tuple.h 안 Invoke ApplyAfter / TMemberFunctionPtrOuter 특수화 실패* 라는 *지옥 같은 template error* — 일반 사용자가 보면 *원인 추적 불가*.

## 자세히

### 사례 — `FOnInteractiveProcessCompleted` (2026-05-26)

🟢 **VAULT** — KMCProject 실측.

**증상**:
```
Tuple.h(326,145): error C2672: 'Invoke': 일치하는 오버로드된 함수가 없습니다.
note: 'TMemberFunctionPtrOuter_T': 별칭 템플릿을 특수화하지 못했습니다.
note: 'Type': 직접 또는 간접 기본 클래스 'TMemberFunctionPtrOuter<PtrMemFunType>'의 멤버가 아닙니다.
with [ PtrMemFunType=FMCDataTableAutoClaudeProcess::Run::<lambda_2> ]
```

핵심 단서:
- `Run::<lambda_2>` = N번째 람다 (mismatch 정확 위치)
- `Invoke` mismatch + `TMemberFunctionPtrOuter` 특수화 실패 = *람다 시그니처 ≠ delegate 시그니처*

**원인** (🟢 Engine grep `Misc/InteractiveProcess.h:25`):
```cpp
DECLARE_DELEGATE_TwoParams(FOnInteractiveProcessCompleted, int32, bool);
```

→ **2 params** `(int32 ExitCode, bool bShutdown)`.

위반 코드 (Phase 3c-2 작성 실수):
```cpp
Process->OnCompleted().BindLambda(
    [Self](int32 ExitCode)    // ❌ 1 param — bool 누락
    { ... });
```

**Fix**:
```cpp
Process->OnCompleted().BindLambda(
    [Self](int32 ExitCode, bool /*bShutdown*/)   // ✅ 2 params
    { ... });
```

## 회피 — 4-Layer Defense

### Layer 1: BindLambda 작성 전 DECLARE_DELEGATE_* grep 의무

```
Grep "DECLARE_DELEGATE.*<DelegateTypeName>" Engine/Source
```

매크로 이름의 *Param 개수* 분석:
- `DECLARE_DELEGATE` — 0 params
- `DECLARE_DELEGATE_OneParam` — 1 param
- `DECLARE_DELEGATE_TwoParams` — 2 params
- `DECLARE_DELEGATE_ThreeParams` — 3 params
- `..._FourParams / _FiveParams` 등
- `DECLARE_DELEGATE_RetVal_*Params` — return type + params
- `DECLARE_MULTICAST_DELEGATE_*` — multicast 변종

매크로 끝의 *Params* 부분이 람다 인자 개수를 명시.

### Layer 2: 람다 인자 vs declared 매크로 정합성 검증

```cpp
DECLARE_DELEGATE_TwoParams(MyDelegate, int32, FString);

// 일치 패턴 — 모두 OK
.BindLambda([](int32 A, FString B) { ... });
.BindLambda([](int32, FString) { ... });               // unused 인자
.BindLambda([](int32 A, FString /*Unused*/) { ... });  // 명시적 unused
.BindLambda([](int32 A, const FString& B) { ... });    // value → const ref OK

// 불일치 — 모두 컴파일 실패 (Tuple/Invoke template error)
.BindLambda([](int32 A) { ... });                      // ❌ 인자 누락
.BindLambda([](int32 A, FString B, bool C) { ... });   // ❌ 추가 인자
.BindLambda([]() { ... });                             // ❌ 인자 모두 누락
```

### Layer 3: AI 작성 코드 review 시 BindLambda 전수 검증

LLM (Claude / Copilot 등) 이 작성한 *모든* BindLambda / AddLambda / CreateLambda 의 람다 인자 개수가:
1. Declared delegate 의 매크로 *Params* 와 일치하는지
2. Engine 본가에서 같은 delegate 의 사용 예시와 일치하는지

검증 의무. AI 작성 prior 가 *흔한 1-param 패턴* 으로 hallucinate 가능 (e.g. OnCompleted 의 일반 prior 는 `(ExitCode)` 만).

### Layer 4: clean build 정기 트리거

UE 의 incremental build / PCH cache 는 template instantiation 실패를 *숨김*. 정기적으로:
- `clean rebuild`
- 새 source 추가 (makefile invalidation)
- non-unity 빌드 (`bUseUnityBuild = false`)

→ latent mismatch 드러남.

## 비슷한 hazard family

같은 메커니즘 — *signature mismatch* 의 다른 변종:

| Hazard | 증상 |
|---|---|
| **Delegate ParamCount** (본 concept) | Tuple/Invoke template error |
| 람다 return type mismatch | `decltype(auto)` deduction 실패 |
| `const` qualifier mismatch | `cannot convert this pointer` |
| MemberFunction pointer mismatch | `PtrMemFunType` 특수화 실패 |
| 함수 포인터 calling convention | `__cdecl` vs `__stdcall` 충돌 (Windows) |

모두 *Engine 본가 grep* + *Layer 1-4* 회피.

## 관련

- [[concepts/UE-Phantom-Header-Hallucination-Hazard]] (signature hallucination 의 *header* 변종)
- [[concepts/LLM-Visual-Reference-Hallucination]] (image 변종)
- [[synthesis/ue-llm-assumption-hazard-family]] (LLM 추측 hazard 통합)

## 열린 질문

1. ❓ Tuple/Invoke template error 의 IDE 자동 진단 가능성 — clangd / Visual Assist 가 *람다 위치* 와 *declared delegate ParamCount* 를 cross-check 하는지 미확정.
2. ❓ UHT 단계에서 사전 검출 가능한가 — generated.h 의 DECLARE_DELEGATE 사용처를 *람다 binding 위치* 와 함께 분석 가능성. 현재 UHT 가 안 함.

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| FOnInteractiveProcessCompleted = TwoParams(int32, bool) | 🟢 VAULT | Engine grep Misc/InteractiveProcess.h:25 |
| C2672 cascade 의 정확 증상 | 🟢 VAULT | KMCProject Phase 3c-2 실측 빌드 에러 |
| MCMaterialAutoClaudeProcess.cpp:209 정확 패턴 | 🟢 VAULT | KMCProject 실측 코드 read |
| 다른 mismatch family (return type / const / calling conv) | 🟡 PARTIAL | UE template 일반 패턴 + 외삽 |
| IDE 자동 진단 / UHT 사전 검출 | 🔴 INFERRED | 미검증 |

## 변경 이력

- 2026-05-26: 초안 작성. MCDataTableAuto Phase 3c-2 빌드 cycle 발견 — `FOnInteractiveProcessCompleted` 람다 bool 인자 누락. [[concepts/UE-Phantom-Header-Hallucination-Hazard]] family 의 *signature* 변종.
