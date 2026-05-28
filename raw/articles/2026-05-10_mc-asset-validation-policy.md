---
title: "MC Asset Validation Policy — LOG vs ensure"
project: KMCProject
scope: MCPlayModule (runtime modules using MCAssetValidation.h)
ue_version: 5.7.4
date: 2026-05-10
author: KMCProject (Min-Cheol)
related_vault:
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Profiling-Scope-Rule]]"
  - "[[sources/mc-soft-skeletalmesh-ragdoll]]"
tags: [ue, runtime, policy, logging, ensure, validation, project, kmcproject]
---

# MC Asset Validation Policy — LOG vs ensure

> **두 가지 실패 모드를 명확히 분리** — Soft fail (자산/의존이 합법적으로 없는 런타임 케이스) 은 `UE_LOG(LogMCAsset, Warning) + return`. Hard fail (프로그래머/정책 위반) 은 `ensure` 또는 `ensureMsgf`. KMCProject 의 모든 런타임 컴포넌트가 동일 매크로를 쓰도록 정착.

## 1. 동기 (왜 만드는가)

[[sources/mc-soft-skeletalmesh-ragdoll]] 1차 작성 시 silent return / Broadcast-only 가드가 곳곳에 있었다 — `if (!Mesh) return;` / `if (!CachedOwner.IsValid()) return;`. 두 종류 케이스가 섞여 있는 게 문제:

| 케이스 | 의미 | 적절한 처리 |
| ---- | ---- | ---- |
| `SoftSkeletalMesh.IsNull()` (메시 미지정) | **합법적 런타임 상태** — 디테일 패널 미설정, 프리뷰용 컴포넌트 등 | LOG + return (디버그 가시성) |
| `CachedOwner.IsValid() == false` | **자연스러운 GC** ([[concepts/Asset-Loading-Policy]] §2 단계 5 — 콜백 도착 전 World tear-down) | LOG + return |
| `ApplyPhysicalAnimationProfile` Constructor 안 호출 | **`UnsafeDuringActorConstruction` 위반** ([[sources/ue-components-physicscomponents]] §11 #7) — 프로그래머가 잘못 쓴 것 | ensure |
| `EnsurePhysicalAnimationComponent` BeginPlay 전 호출 | **정책 위반** — 위 #7 의 변형 | ensure |

silent return 으로 두면 둘 다 *조용히 무시* — 디버깅이 어렵고, 정책 위반이 드러나지 않는다. 본 정책으로 명시적 분리.

## 2. 두 실패 모드의 정의

### 2.1 (A) Soft fail — `UE_LOG(LogMCAsset, Warning) + return`

자산 / 의존 객체가 *런타임 컨텍스트상 합법적으로 없을 수 있는* 모든 케이스. Shipping 빌드도 LOG 출력 (Warning 이상은 strip 되지 않음 — 다만 Verbose 는 Development 만).

**조건**:
- `nullptr` 검사 (포인터 / Cast 결과 / Get 함수 반환값)
- `TWeakObjectPtr / TWeakInterfacePtr` 의 `IsValid() == false`
- `TSoftObjectPtr / TSoftClassPtr` 의 `IsNull() == true`
- `FName.IsNone()` (BoneName / ProfileName)
- 임의 bool 검사 — 0 임펄스 / 0 Strength / 0 Radius

**메시지 포맷**: `[<ComponentName>::<Function>] <Reason> — <Symbol> <State>`. `__FUNCTION__` + `GetNameSafe(this)` 자동 삽입 (매크로 안).

### 2.2 (B) Hard fail — `ensure` / `ensureMsgf`

프로그래머가 *잘못 쓴 케이스* — 본질적으로 코드 흐름 오류. ensure 는:
- Development / Editor 빌드 — 한 번 break (디버거) + 다이얼로그 + false 반환
- Shipping 빌드 — break 없이 false 만 반환 (게임 계속 동작)

**조건**:
- `HasBegunPlay()` 검사 — Constructor / `PostInitProperties` 단계에서 PhysAnim / Subsystem API 호출 위반
- `HasAnyFlags(RF_ClassDefaultObject) == false` — CDO 변경 시도 ([[concepts/Component-Policies-6]] §6)
- Skeleton 호환되지 않는 SkeletalMesh swap ([[sources/ue-assetclasses-mesh]] §7 #3) — 같은 Skeleton 또는 Compatible 만 허용
- 사용자 호출 순서 강제 — 예: `EndPlay` 안 호출되었는데 컴포넌트 destroy

`ensure` 후 false 라도 가드 흐름 (`return`) 으로 fallback 하므로 게임은 계속 동작 — 단지 *그 호출의 효과가 사라진다*. Shipping 안전.

## 3. 매크로 인터페이스 (`Core/MCAssetValidation.h`)

```cpp
// Soft fail — UE_LOG(Warning) + return
MC_LOGRET_IF_NULL(Ptr, "Reason");
MC_LOGRET_IF_INVALID_WEAK(WeakPtr, "Reason");
MC_LOGRET_IF_SOFT_NULL(SoftPtr, "Reason");
MC_LOGRET_IF_FALSE(Cond, "Reason");
MC_LOGRET_VAL_IF_NULL(Ptr, ReturnExpr, "Reason");   // 반환값 있는 함수용

// Hard fail — ensureMsgf + return
MC_ENSURE_POLICY(Cond, "Reason");                    // ensure 만 (return 없음 — bool 반환)
MC_ENSURE_AND_RETURN(Cond, "Reason");                // ensure + return
MC_ENSURE_AND_RETURN_VAL(Cond, ReturnExpr, "Reason");
```

매크로 안에 `do { ... } while (0)` 패턴 — `if/else` 분기 안에서도 안전하게 `;` 하나로 끝남.

로그 카테고리: `LogMCAsset` (Log, All — Shipping 도 Warning+ 출력). MCSoftSkeletalMeshComponent.cpp 에 `DEFINE_LOG_CATEGORY(LogMCAsset)` 단일 정의.

## 4. UMCSoftSkeletalMeshComponent 적용 매트릭스

`UMCSoftSkeletalMeshComponent` 에 본 정책 1차 적용. 다른 MC 컴포넌트도 이 패턴 차용.

| 사이트 | 케이스 | 처리 |
| ---- | ---- | ---- |
| `RequestLoadAsync` 진입 — `SoftSkeletalMesh.IsNull()` | 메시 미지정 | LOG(Warning) + Broadcast Failed + return |
| `RequestLoadAsync` 끝 — `LoadHandle.IsValid() == false` | StreamableManager 거절 | LOG(Warning) + Broadcast + return |
| `HandleAssetsLoaded` — `!IsValid(this)` | this GC | LOG(Verbose) + return |
| `HandleAssetsLoaded` — `!CachedOwner.IsValid()` | Owner GC | LOG(Warning) + Broadcast + return |
| `ApplyLoadedAssets` — `LoadedMesh == nullptr` | Cooked 누락 / 취소 | LOG(Warning) + Broadcast + return |
| `EnablePartialRagdoll` — `Pivot.IsNone()` | 본 미설정 | LOG(Warning) + return |
| `HandleRagdollPhysicsAssetLoaded` — `!IsValid(this)` | this GC | LOG(Verbose) + return |
| `HandleRagdollPhysicsAssetLoaded` — `!CachedOwner.IsValid()` | Owner GC | LOG(Warning) + return |
| `HandleRagdollPhysicsAssetLoaded` — `GetSkeletalMeshAsset() == nullptr` | 메시 비동기 로드 미완 | LOG(Warning) + return |
| `EnableFullRagdoll` — `bRagdollActive == true` | idempotent 재진입 | LOG(Verbose) + return |
| **`EnsurePhysicalAnimationComponent` — `!HasBegunPlay()`** | **Constructor / 초기화 단계 호출** | **ensure + return nullptr** |
| `EnsurePhysicalAnimationComponent` — `!Owner` | Component detached | LOG(Warning) + return nullptr |
| `EnsurePhysicalAnimationComponent` — `NewObject` returned null | 엔진 메모리 실패 | LOG(Warning) + return nullptr |
| `ApplyMotorProfileBelow` — BoneName/ProfileName None | 미지정 | LOG(Warning) + return |
| `ApplyMotorSettingsBelow` — BoneName None | 미지정 | LOG(Warning) + return |
| `FadeMotorStrength` — `!PhysicalAnim` | PhysAnim 미생성 | LOG(Warning) + return |
| `ApplyHitImpulse` — `Impulse.IsNearlyZero()` | 0 임펄스 | LOG(Verbose) + return |
| `ApplyRadialHitImpulse` — Strength/Radius <= 0 | 잘못된 인자 | LOG(Warning) + return |
| `OnHitReceived` — Mesh 미로드 | 비동기 로드 미완 | LOG(Warning) + return |
| `OnHitReceived` — EffectiveBone None | 본 미지정 | LOG(Warning) + return |
| `SnapMeshToOwnerCapsule` — `!Owner` | Component detached | LOG(Warning) + return |

**ensure 1 곳만** — `EnsurePhysicalAnimationComponent` 의 `HasBegunPlay()` 체크. 이게 [[sources/ue-components-physicscomponents]] §11 함정 #7 의 *유일한 진짜 정책 위반* 사이트. 다른 모든 사이트는 런타임에 합법적으로 발생할 수 있어 Soft fail.

## 5. 로그 Verbosity 결정 트리

```
이 케이스가 *프로덕션* 에서 발생할 수 있는가?
├── 자주 (예: 매 프레임 / 매 hit / 매 spawn) — Verbose
│   └── ApplyHitImpulse(0 vec) 같은 idempotent 가드, EnableFullRagdoll 재진입
├── 가끔 (예: 비동기 로드 콜백 도착 전 GC, 메시 안 지정한 프리뷰 컴포넌트) — Warning
│   └── 대부분의 LOGRET 사이트
└── 절대 안 됨 (예: Constructor 안 PhysAnim Apply) — ensure (= Error 등급 + break)
```

**`Verbose`** 는 Shipping 에서 strip — 프로덕션 로그 노이즈 0.
**`Warning`** 은 Shipping 도 출력 — QA 가 LOG 파일에서 식별 가능.
**`ensure`** 는 Development 디버거 break — 개발 단계에서 즉시 발견.

## 6. 다른 컴포넌트로 확장 절차

같은 정책을 새 컴포넌트에 적용할 때:

1. `#include "KMCProject/MCPlayModule/Core/MCAssetValidation.h"` (헤더 또는 .cpp)
2. silent return 사이트를 매크로로 갈아끼움 — 메시지에 *왜* 가 들어가도록
3. *진짜 정책 위반* 사이트만 `MC_ENSURE_*` 로 — 위 §4 의 단일 ensure 사이트가 모범 사례
4. `LogMCAsset` 카테고리는 한 곳에서만 `DEFINE_LOG_CATEGORY` (현재 `MCSoftSkeletalMeshComponent.cpp`) — 새 컴포넌트는 extern 참조만

## 7. vault 정책 매핑

| 본 정책 | vault 매핑 | 강화 부분 |
| ---- | ---- | ---- |
| LOG + return (자산 미존재) | [[concepts/Asset-Loading-Policy]] §2 단계 5 (Soft + Handle Pin) | 콜백 도착 전 GC 케이스를 *명시적* LOG 로 가시화 |
| ensure (Constructor 위반) | [[sources/ue-components-physicscomponents]] §11 함정 #7 | `HasBegunPlay()` ensure 로 *컴파일 타임이 아닌 런타임 가드* |
| GC 방어 — TObjectPtr / TWeakObjectPtr | [[concepts/Component-Policies-6]] §3 | 매크로가 IsValid 검사 + 메시지 자동 |
| 콜백 첫 줄 Trace scope | [[concepts/Profiling-Scope-Rule]] | LOG 매크로는 *Trace scope 안에서* 호출 (LOG 자체는 별도 — Trace 와 호환) |

## 8. 함정 / 비-적용 케이스

- **Critical 영역 (RHI / Render thread / Physics tick)** — `UE_LOG` 가 lock 을 걸어 성능 저하 가능. 이 영역에선 `UE_TRACE_LOG_SCOPED_T` / verbose flag 검사 후 출력. 본 컴포넌트는 모두 GameThread 라 영향 없음.
- **`check` vs `ensure`** — `check` 는 Shipping 에서도 break + 크래시. 데이터 손상 / 보안 위반 같은 *복구 불가* 케이스만. 본 정책은 ensure 만 사용 (Shipping 안전).
- **Verbosity 남용** — 모든 게 Warning 이면 노이즈. *런타임 빈도 × 디버깅 가치* 로 결정 (위 §5 트리).

## 9. 미해결 / 다음 작업

- [ ] 다른 MC 컴포넌트 (`UMCBouyancyComponent`, `UMCWaterPlaneComponent`, `UMCMoveComponent`, `UMCCharacterMoveComponent`, `UMCActorComponent`, `UMCPartsLoaderComponent`) 에 동일 정책 적용
- [ ] `MCActorBlueprintLibrary` / `MCWaterBlueprintLibrary` 의 BP-callable 함수에도 매크로 적용 — BP 측 디버깅 가시성
- [ ] `MCStorySubSystem` / `MCCameraSubSystem` 의 Subsystem API 도 본 정책 차용
- [ ] `MC_VALIDATE_SKELETON_COMPATIBILITY(Mesh, ExpectedSkeleton)` — Skeleton 호환 검증 헬퍼 추가 ([[sources/ue-assetclasses-mesh]] §7 #3 의 ensure 화)
- [ ] vault concept `[[concepts/MC-Asset-Validation-Policy]]` 페이지 작성 (본 raw 의 골자)

## 10. 변경 이력

| 날짜 | 변경 |
| ---- | ---- |
| 2026-05-10 | 최초 작성. Soft fail vs Hard fail 분리. `Core/MCAssetValidation.h` 매크로 8종 + `LogMCAsset` 카테고리. `UMCSoftSkeletalMeshComponent` 1차 적용 매트릭스 (LOG 사이트 19개 + ensure 사이트 1개). |
