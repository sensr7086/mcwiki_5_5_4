---
type: concept
title: "MC Asset Validation Policy (LOG vs ensure)"
aliases: [MC Validation Policy, LogMCAsset, MC_LOGRET, MC_ENSURE]
sources:
  - "[[sources/mc-asset-validation-policy]]"
  - "[[sources/mc-soft-skeletalmesh-ragdoll]]"
related_concepts:
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, runtime, policy, logging, ensure, project, kmcproject]
last_updated: 2026-05-10
---

# MC Asset Validation Policy (LOG vs ensure)

## 1. 정의 (한 줄)

KMCProject 의 모든 런타임 컴포넌트가 따르는 *자산 / 의존 객체 검증* 정책. **Soft fail** (자산이 합법적으로 없는 런타임 케이스) 은 `UE_LOG(LogMCAsset, Warning) + return`. **Hard fail** (프로그래머 / 정책 위반) 은 `ensure / ensureMsgf`. silent return 금지. 매크로 정의: `Source/KMCProject/MCPlayModule/Core/MCAssetValidation.h`.

## 2. 자세히

| 모드 | 트리거 | 처리 | Shipping |
| -- | -- | -- | -- |
| **(A) Soft fail** | `nullptr` / `TWeakObjectPtr.IsValid() == false` / `TSoftObjectPtr.IsNull()` / `FName.IsNone()` / 0 임펄스 등 | `UE_LOG(LogMCAsset, Warning/Verbose) + return` | LOG 출력 (Warning 이상). 게임 계속. |
| **(B) Hard fail** | Constructor/PostInit 단계 PhysAnim Apply / `HasBegunPlay()==false` / Skeleton 미호환 swap 등 | `ensureMsgf(...) + return` | break 없이 false 반환. 게임 계속. |

**왜 silent return 을 막는가** — 두 종류 케이스가 섞여 있으면 디버그 시 *어느 가드에서 빠졌는지 모름*. 매크로가 자동으로 `[<ComponentName>::<Function>] <Reason> — <Symbol> <State>` 포맷으로 출력해 식별 가능. ensure 는 Development 빌드에서 디버거 break + 다이얼로그 → 잘못된 사용 패턴이 코드 리뷰 / QA 단계에서 즉시 발견.

## 3. 매크로 (`Core/MCAssetValidation.h`)

```cpp
// (A) Soft fail
MC_LOGRET_IF_NULL(Ptr, "Reason");
MC_LOGRET_IF_INVALID_WEAK(WeakPtr, "Reason");
MC_LOGRET_IF_SOFT_NULL(SoftPtr, "Reason");
MC_LOGRET_IF_FALSE(Cond, "Reason");
MC_LOGRET_VAL_IF_NULL(Ptr, ReturnExpr, "Reason");

// (B) Hard fail
MC_ENSURE_POLICY(Cond, "Reason");                 // ensure 만 (return 없음)
MC_ENSURE_AND_RETURN(Cond, "Reason");             // ensure + return
MC_ENSURE_AND_RETURN_VAL(Cond, ReturnExpr, "Reason");
```

`do { ... } while (0)` 패턴 — `if/else` 분기 안 안전. `LogMCAsset` 카테고리는 `MCSoftSkeletalMeshComponent.cpp` 에서 단일 `DEFINE_LOG_CATEGORY`.

## 4. Verbosity 결정 트리

- **Verbose** — 자주 발생, 디버그 가치 낮음 (idempotent 가드, 0 임펄스). Shipping strip.
- **Warning** — 가끔 발생, 디버깅 가치 큼 (자연 GC, 메시 미지정). Shipping 출력.
- **ensure** — 절대 발생하면 안 됨 (Constructor 안 호출 등). Development break + Shipping 안전 false 반환.

## 5. 변형 / 사례

- [[sources/mc-soft-skeletalmesh-ragdoll]] 의 1차 적용 — LOG 사이트 19개 + ensure 사이트 1개 (`EnsurePhysicalAnimationComponent` 의 `HasBegunPlay()`).
- [[sources/ue-components-physicscomponents]] §11 함정 #7 (`UnsafeDuringActorConstruction`) 이 KMCProject 에서 ensure 로 *런타임 가드* 됨.
- [[concepts/Asset-Loading-Policy]] §2 단계 5 의 *콜백 도착 전 GC* 케이스가 `MC_LOGRET_IF_INVALID_WEAK` 로 명시적 가시화.
- [[concepts/Component-Policies-6]] §3 GC 방어 — `TObjectPtr` / `TWeakObjectPtr` 사용 + 본 정책 매크로가 IsValid 검사 자동.

## 6. 적용 절차 (새 컴포넌트)

1. `#include "KMCProject/MCPlayModule/Core/MCAssetValidation.h"`
2. silent return 사이트를 `MC_LOGRET_*` 매크로로 — 메시지에 *왜* 명시
3. *진짜 정책 위반* 사이트만 `MC_ENSURE_*` — 보수적으로 (LOG 가 디폴트)
4. `LogMCAsset` 은 extern 만 — `DEFINE_LOG_CATEGORY` 는 한 곳에서만 ([[sources/mc-soft-skeletalmesh-ragdoll]] 의 cpp)

## 7. 관련 entity

- [[entities/USkeletalMeshComponent]] (KMCProject 변형 `UMCSoftSkeletalMeshComponent` 가 1차 적용)
- [[entities/UActorComponent]] / [[entities/USceneComponent]] / [[entities/UPrimitiveComponent]] — 다른 MC 컴포넌트도 같은 베이스

## 8. 열린 질문

- [ ] 다른 MC 컴포넌트 (`UMCBouyancyComponent` / `UMCMoveComponent` / `UMCPartsLoaderComponent` 등) 에도 적용 — 일괄 refactor 작업
- [ ] `MC_VALIDATE_SKELETON_COMPATIBILITY` 헬퍼 — [[sources/ue-assetclasses-mesh]] §7 #3 (Skeleton 호환 swap) 을 ensure 로
- [ ] BP-callable 함수의 매크로 출력 형식 — BP 측 디버그 메시지 (Print String 등) 와 통합
- [ ] `check` (Shipping break) 사용 영역 결정 — 데이터 손상 / 보안 위반 케이스. 본 정책은 ensure 만 사용 중.
