---
type: synthesis
title: "Lint Audit — MCSoft*MeshComponent 결함 16 종 (2026-05-10)"
slug: lint-2026-05-10-mcsoft-components
created: 2026-05-10
last_updated: 2026-05-11
sources:
  - "[[sources/mc-soft-skeletalmesh-ragdoll]]"
  - "[[sources/mc-asset-validation-policy]]"
  - "[[sources/ue-components-physicscomponents]]"
  - "[[sources/ue-assetclasses-mesh]]"
entities:
  - "[[entities/USkeletalMeshComponent]]"
  - "[[entities/UStaticMeshComponent]]"
  - "[[entities/USkeletalMesh]]"
concepts:
  - "[[concepts/MC-Asset-Validation-Policy]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Asset-Loading-Policy]]"
status: settled
tags: [synthesis, audit, lint, mcsoft, defects]
---

# Lint Audit — MCSoft*MeshComponent 결함 16 종 (2026-05-10)

## 1. Thesis

[[synthesis/mc-soft-asset-component-pattern]] / [[synthesis/mc-character-hit-reaction-pipeline]] 의 1·2·3 차 작업이 누적된 후 *vault 정책 기준* 으로 코드 회의적 audit. 결과 — Critical 3 + High 5 + Medium 3 + Low 3 + 사전 build error 1 + 신설 매크로 1 + 신설 파일 1 = **총 16 항목 식별 → 14 fix + 1 의도된 보류 (L1) + 1 재검증 (C1 — 파일 이미 존재)**. Karpathy 패턴의 lint report 로 vault 에 정착 — 다음 audit 의 기준선.

## 2. 결함 매트릭스 (16 종)

| # | ID | 등급 | 위치 | 설명 | Status | Fix 위치 |
| -- | -- | -- | -- | -- | -- | -- |
| 1 | 사전 | Build error | Skeletal.cpp:71 | `bHidden` (AActor deprecated) — 빌드 실패 | ✅ fixed | `bInitiallyHidden = bHiddenInGame;` (괄호 X 삼항 X) |
| 2 | C1 | Critical | Static | `MCSoftStaticMeshComponent.cpp` 누락 — 링크 에러 우려 | ⚠️ false alarm | 파일 존재 (이전 Glob stale) — 재검증 후 H1 만 적용 |
| 3 | C2 | Critical | Skeletal `OnHitReceived` | 풀-바디 ragdoll + motor profile = AnimInstance=nullptr 라 motor 효과 0 | ✅ fixed | `if (!bUseFullRagdoll && !EffectiveProfile.IsNone())` 가드 |
| 4 | C3 | Critical | Skeletal `OnHitReceived` | Soft PhysicsAsset 비동기 race — motor/impulse 가 시뮬 안 된 본에 적용 → noop | ✅ fixed | `RequestRagdollActivation(..., TFunction OnRagdollReady)` 콜백 chain + `ApplyHitMotorAndImpulse` 헬퍼 분리 |
| 5 | H1 | High | Static.h | `MCAssetValidation.h` include 누락 + silent return 4 사이트 | ✅ fixed | include 추가 + LOG (Path null / handle invalid / Cooked 누락 / Owner GC) |
| 6 | H2 | High | Skeletal | `bInitialTickEnabled` 죽은 코드 (Ctor 가 false 강제 → 항상 false 캐싱) | ✅ fixed | 헤더+cpp 에서 멤버 + 사용 라인 제거 |
| 7 | H3 | High | Skeletal `ReleaseLoadedAsset` | `RagdollLoadHandle` Cancel 누락 + PhysicsAsset 클리어 누락 | ✅ fixed | `RagdollLoadHandle->CancelHandle` + `SetPhysicsAsset(nullptr)` + ragdoll 상태 리셋 |
| 8 | H4 | High | Skeletal `ApplyLoadedAssets` | Skeleton 호환 검증 누락 ([[sources/ue-assetclasses-mesh]] §7 #3) | ✅ fixed | `MC_ENSURE_SKELETON_COMPAT(this, NewMesh)` 매크로 신설 + 적용 |
| 9 | H5 | High | Skeletal `DisableRagdoll` | 부분 ragdoll 만 활성된 경우에도 모든 본 시뮬 정지 | ✅ fixed | `bWasFullActive` vs `bWasPartialActive` 분기 — 부분 시 `SetAllBodiesBelowSimulatePhysics(ActivePartialRagdollBone, false, ...)` 만 |
| 10 | M1 | Medium | Skeletal.cpp | `DEFINE_LOG_CATEGORY(LogMCAsset)` 가 SkeletalMesh.cpp 에 위치 — 단일 책임 위반 | ✅ fixed | `MCAssetValidation.cpp` 별도 파일 신설 → 카테고리 정의 이전 |
| 11 | M2 | Medium | Static | `PostEditChangeProperty` 누락 의심 | ⚠️ false alarm | 이미 구현됨 (Static.cpp 91~125) — 검증만 |
| 12 | M3 | Medium | Skeletal Ctor | 헤더 주석은 "메시 비워둠" 인데 명시 호출 없음 | ✅ fixed | `SetSkeletalMeshAsset(nullptr); SetAnimInstanceClass(nullptr);` — Static Ctor 도 동일 |
| 13 | M4 | Medium | Skeletal `OnHitReceived` | `HitUpwardBias` `Z += bias` 후 Normalize — 비율 의미 불명확 | ✅ fixed | `FMath::Lerp(Dir, FVector::UpVector, bias).GetSafeNormal()` — 0~1 비율 |
| 14 | L1 | Low | MCAssetValidation.h | 매크로가 `*GetNameSafe(this)` 강제 — static 함수 / free function 사용 불가 | 🟡 deferred | 사용 사례 적어 보류, [[synthesis/mc-validation-automation-tooling]] 와 함께 추후 검토 |
| 15 | L2 | Low | Skeletal `RequestLoadAsync` | §2 즉시 적용 분기 진입 전 `LoadHandle` 미취소 — race 약점 | ✅ fixed | §2 안에 cancel 추가 (Static.cpp 도 같은 패턴) |
| 16 | L3 | Low | Static + Skeletal | `LoadPriority = 0` 매직 넘버 | ✅ fixed | `(LoadPriority > 0) ? ... : FStreamableManager::DefaultAsyncLoadPriority` 양쪽 |
| 17 | L4 | Low | Skeletal `OnHitFromResult` | Mesh nullptr 시 silent — `FindClosestBone` 안 호출 후 잡히지만 race 가시화 부족 | ✅ fixed | Verbose LOG 추가 |
| 보너스 | refactor | Refactor | Static + Skeletal | `bHiddenInGame` 컨벤션 통일 (괄호 X / 삼항 X) | ✅ fixed | 4 사이트 통일 |

## 3. Fix 통계

- **빌드 통과 임계 (Critical + Build error)**: 3 fixed (사전 / C2 / C3) + 1 false alarm (C1)
- **정책 위반 (High + Medium)**: 7 fixed + 1 false alarm (M2)
- **개선 (Low)**: 3 fixed + 1 deferred (L1)
- **통일 refactor**: 1 (`bHiddenInGame`)
- **신설**: `MC_ENSURE_SKELETON_COMPAT` 매크로 + `MCAssetValidation.cpp` 파일

총 적용 변경 — 14 fixes + 2 신설 + 1 refactor = **17 변경** (16 결함 식별 + 1 사전 빌드 에러 + 1 false alarm 2 종 = 식별 18, fix 14).

## 4. vault 정책 매핑 (어느 정책이 어떤 결함을 잡았는가)

| vault 정책 | 잡은 결함 |
| -- | -- |
| [[concepts/MC-Asset-Validation-Policy]] (A/B 분리) | H1, H3, L4 (silent return → LOG/ensure) |
| [[concepts/Component-Policies-6]] §3 GC 방어 | H3 (PhysicsAsset 미클리어), L2 (race) |
| [[concepts/Asset-Loading-Policy]] §2 단계 5 | C3 (비동기 race), H3 (RagdollLoadHandle Cancel), L2 |
| [[concepts/Profiling-Scope-Rule]] | (모든 신규 사이트에 자동 적용) |
| [[sources/ue-assetclasses-mesh]] §7 함정 #3 | H4 (Skeleton compat) |
| [[sources/ue-assetclasses-mesh]] §7 함정 #6 | C3 (PhysicsAsset 변경 후 SetSimulate 페어) |
| [[sources/ue-components-physicscomponents]] §11 함정 #7 | M3 (UnsafeDuringActorConstruction — 이미 적용된 ensure) |
| [[sources/ue-components-physicscomponents]] §11 함정 #8 | C2 (Profile 적용 후 SetSimulate 페어 — 풀-바디 시 motor 의미 없음) |

각 정책이 *각자 하나 이상의 결함을 잡음* — 정책 cross-cover 효과 검증.

## 5. fix 후 기준선 (다음 audit 시 비교용)

- `MCSoftSkeletalMeshComponent.cpp` 라인 ~870 (변경 후) / 카테고리: 이상 없음
- `MCSoftStaticMeshComponent.cpp` 라인 ~325 (변경 후) / 카테고리: 이상 없음
- `MCAssetValidation.h` 매크로 9 종 (Soft 5 + Hard 3 + Skeleton compat 1)
- `MCAssetValidation.cpp` (LogMCAsset 단일 정의)
- silent return 사이트: **0** (양쪽 컴포넌트)
- ensure 사이트: 1 (`EnsurePhysicalAnimationComponent` 의 `HasBegunPlay()`)
- TRACE_CPUPROFILER_EVENT_SCOPE 사이트: 모든 콜백 / Tick / 람다 진입점 (vault [[concepts/Profiling-Scope-Rule]] 100%)

## 6. 함정 / 열린 질문

- [ ] **L1 deferred 추적** — `MC_LOGRET_*` static-context 매크로 변형 — 사용 사례 발생 시 [[synthesis/mc-validation-automation-tooling]] 의 자동화 도구에서 처리 여부 결정 (열린)
- [ ] **다른 MC 컴포넌트 일괄 적용** — [[synthesis/mc-validation-policy-rollout]] §4 의 10 모듈 매트릭스 진행 — 본 audit 의 패턴 따름. 차세대 audit 노트 (`lint-YYYY-MM-DD-mc-componentbouyancy.md` 등) 표준 (열린)
- [ ] **Static.cpp 의 `EmptyOverrideMaterials()`** — Skeletal 은 명시적 `for (i) SetMaterial(i, nullptr)` — 양쪽 패턴 차이. UMeshComponent API 의 차이인지 검토 필요 (열린)
- [ ] **Skeletal Ctor 의 `SetSkeletalMeshAsset(nullptr)` 호출 시점** — Super 가 이미 nullptr 디폴트면 중복. Cooked 빌드 검증 시 차이 없는지 확인 (열린)
- [ ] **C2 fix 의 *full ragdoll + impulse* 동작 검증** — motor 는 skip 했지만 임펄스는 적용. 풀-바디 ragdoll 의 본이 시뮬 활성된 시점에 임펄스가 정상 적용되는지 PIE 테스트 (열린)
- [ ] **TFunction 캡처 leak 위험** — `RequestRagdollActivation` 의 `TFunction<void()> OnRagdollReady` 가 비동기 콜백 안에서 `MoveTemp` 캡처. 콜백이 *호출되지 않은 채* 컴포넌트 destroy 시 람다는 `WeakSelf.Get() == nullptr` 분기로 안전. 검증 완료 (cleared)
- [ ] **vault audit 자동화** — 본 노트 작성을 [[synthesis/mc-validation-automation-tooling]] 의 Python script 가 자동 생성하도록 통합 — `silent return 발견 → LOG 변환 제안 → audit 노트 자동 append` (열린)

## 7. 관련

### Sources

[[sources/mc-soft-skeletalmesh-ragdoll]] · [[sources/mc-asset-validation-policy]] · [[sources/ue-components-physicscomponents]] · [[sources/ue-assetclasses-mesh]]

### Entities

[[entities/USkeletalMeshComponent]] · [[entities/UStaticMeshComponent]] · [[entities/USkeletalMesh]]

### Concepts

[[concepts/MC-Asset-Validation-Policy]] · [[concepts/Component-Policies-6]] · [[concepts/Asset-Loading-Policy]]

### Related synthesis

[[synthesis/mc-soft-asset-component-pattern]] (audit 대상 컴포넌트 골격) · [[synthesis/mc-character-hit-reaction-pipeline]] (대상 파이프라인) · [[synthesis/mc-validation-policy-rollout]] (audit 의 정책 출처) · [[synthesis/mc-validation-automation-tooling]] (audit 자동화 미래)

### Log entries (chronological — 4 chain)

1. `## [2026-05-10] fix | MCSoft*MeshComponent 결함 audit 후 일괄 fix (16종)` — 일괄 fix
2. `## [2026-05-10] note | KMCProject 컨벤션 — IsHiddenInGame 직접 접근...` (틀림 — 사용자 오타 기반)
3. `## [2026-05-10] note | 정정 — IsHiddenInGame 컨벤션 → bHiddenInGame...` — 정정
4. `## [2026-05-10] refactor | MCSoft*MeshComponent — bHiddenInGame 컨벤션 통일` — Static + Skeletal 4 사이트 통일
