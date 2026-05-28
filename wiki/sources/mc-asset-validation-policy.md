---
type: source
title: "MC Asset Validation Policy — LOG vs ensure (KMCProject)"
slug: mc-asset-validation-policy
source_path: raw/articles/2026-05-10_mc-asset-validation-policy.md
source_kind: design-note
source_date: 2026-05-10
ingested: 2026-05-10
last_updated: 2026-05-14
related_entities:
  - "[[entities/UActorComponent]]"
  - "[[entities/USkeletalMeshComponent]]"
related_concepts:
  - "[[concepts/MC-Asset-Validation-Policy]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, runtime, policy, logging, ensure, validation, project, kmcproject, const-correctness, variable-naming-convention]
---

# MC Asset Validation Policy — LOG vs ensure

> Source: [[raw/articles/2026-05-10_mc-asset-validation-policy.md]]
> Kind: design-note · Date: 2026-05-10 · Ingested: 2026-05-10 · Last updated: 2026-05-14
> Project: KMCProject · Header: `Source/KMCProject/MCPlayModule/Core/MCAssetValidation.h`

## 1. Summary

KMCProject 의 모든 런타임 컴포넌트 silent return 가드를 두 모드로 명시 분리. **(A) Soft fail** = 자산 / 의존이 합법적으로 없는 케이스 → `UE_LOG(LogMCAsset, Warning/Verbose) + return`. **(B) Hard fail** = 프로그래머 / 정책 위반 → `ensureMsgf(...) + return`. 매크로 8종 + `LogMCAsset` 카테고리. ⭐ **§6 static-friendly 변형 부재** (2026-05-13) · ⭐ **§11 const-correctness 체크리스트** (2026-05-14) · ⭐ **§12 변수 이름 회피 규약** (2026-05-14 사용자 진단).

## 2. Key claims

(상세 기존 유지 — 두 모드 분리, UE_LOG Warning Shipping, ensure 사이트 결정, MCSoftSkeletalMesh 20 사이트 등)

## 3. Quotations

> "`ApplyPhysicalAnimationProfileBelow` 생성자 안 호출 — `UnsafeDuringActorConstruction` — BeginPlay 이후" → 본 정책의 **유일한 ensure 사이트**

> "**Hard vs Soft 결정**: 항상 사용 = `TObjectPtr<T>` / 가끔 큰 자산 = `TSoftObjectPtr<T>`" → `MC_LOGRET_IF_SOFT_NULL`

> "UPROPERTY 누락 = dangling. UPROPERTY + `TObjectPtr<>` / `TWeakObjectPtr<>`" → `MC_LOGRET_IF_INVALID_WEAK`

> "변수 이름에 UE 글로벌 매크로 식별자 (`PI` / `SMALL_NUMBER` / `check`) 사용 시 전처리기 즉시 치환 → C2059 / silent pollution. underscore prefix (`_PreviewInstance`) 또는 도메인 prefix 의무." (2026-05-14 KMCProject 사용자 직접 진단)

## 4. Open questions / next sources

- [ ] 다른 MC 컴포넌트 일괄 refactor
- [ ] BP-callable 매크로 적용
- [ ] `MC_VALIDATE_SKELETON_COMPATIBILITY` 헬퍼
- [x] **§6 static-friendly 변형 부재** (2026-05-13)
- [x] **§11 const-correctness 체크리스트** (2026-05-14)
- [x] **§12 변수 이름 회피 규약** (2026-05-14)

## 5. 매크로 시그니처 정밀 표 (2026-05-13)

| 매크로 | 시그니처 | this 참조 |
| -- | -- | -- |
| `MC_LOGRET_IF_NULL(Ptr, Reason)` | `Ptr == nullptr` → LOG + return | ✅ |
| `MC_LOGRET_IF_INVALID_WEAK(WeakPtr, Reason)` | LOG + return | ✅ |
| `MC_LOGRET_IF_SOFT_NULL(SoftPtr, Reason)` | LOG + return | ✅ |
| `MC_LOGRET_IF_FALSE(Cond, Reason)` | LOG + return | ✅ |
| `MC_LOGRET_VAL_IF_NULL(Ptr, ReturnExpr, Reason)` | LOG + return ReturnExpr | ✅ |
| `MC_ENSURE_POLICY(Cond, Reason)` | `ensureMsgf` | ✅ |
| `MC_ENSURE_AND_RETURN(Cond, Reason)` | ensure → return | ✅ |
| `MC_ENSURE_AND_RETURN_VAL(Cond, ReturnExpr, Reason)` | ensure → return ReturnExpr | ✅ |

모든 매크로 `*GetNameSafe(this)` 사용 → 멤버 함수 전용.

## 6. ⭐ static-friendly 변형 부재 함정 (2026-05-13)

`UMCSpatialQueryLibrary` BPFunction static 함수 안 `MC_LOGRET_*` 사용 → C2355 'this'. file-local `MCSP_LOGRET_*` 우회.

→ 후속: `MC_STATIC_LOGRET_*` 6 매크로 정식 추가 (P0).

## 7. ⭐ 매크로 우회 검증 사례 (2026-05-13)

`UMCSpatialQueryLibrary` — file-local `MCSP_LOGRET_*` 2종 + `#undef`. 빌드 통과 검증.

## 8. Cross-link

### Related concepts

[[concepts/MC-Asset-Validation-Policy]] · [[concepts/Component-Policies-6]] §3 · [[concepts/Asset-Loading-Policy]] §2 · [[concepts/Profiling-Scope-Rule]]

### Related sources

[[sources/mc-soft-skeletalmesh-ragdoll]] · [[sources/ue-components-physicscomponents]] §11 #7 · [[sources/ue-coreuobject-interface]] · [[sources/ue-coreuobject-uobject]] §2.10 + §2.11 + ⭐ §2.12 (UE 매크로 식별자 — §12 페어)

### Related synthesis

[[synthesis/mc-validation-policy-rollout]] · [[synthesis/mc-validation-automation-tooling]] · [[synthesis/mc-actor-spawn-subsystem-implementation]] §7.1 / §7.2 · [[synthesis/mc-character-hit-reaction-pipeline]] §6.5 함정 12 (UE PI 매크로) — §12 KMCProject 검증 사례 페어

### Related fix / feature log

- `[2026-05-10] feature | MCSoftSkeletalMeshComponent 본 정책 1차 적용` (20 사이트)
- `[2026-05-13] feature | UMCSpatialQueryLibrary — file-local 우회` (§6)
- `[2026-05-14] fix | C2440 fix — USkeletalMesh::GetSkeleton() const` (§11)
- ⭐ `[2026-05-14] fix | ⚠ 자체 평가 정정 — Phase 5 C2059 진짜 원인 = UE PI 매크로` (§12 1차 검증, 사용자 직접 진단)

## 9. 후속 우선순위 (2026-05-13 갱신)

1. **P0** — `MC_STATIC_LOGRET_*` 6 매크로 정식 추가
2. **P1** — 다른 MC 컴포넌트 일괄 refactor
3. **P1** — `MC_VALIDATE_SKELETON_COMPATIBILITY` 헬퍼
4. **P2** — BP 측 Print String 통합
5. **P2** — clang-tidy 룰 통합 (자동 검출 — §12 변수 이름도 함께)

## 10. 신뢰도 매트릭스 (3-tier)

| 영역 | tier | 근거 |
| -- | -- | -- |
| 매크로 8종 시그니처 | 🟢 | `MCAssetValidation.h` 직접 인용 |
| `LogMCAsset` 카테고리 단일 정의 | 🟢 | `MCSoftSkeletalMeshComponent.cpp` |
| MCSoftSkeletalMesh 적용 (20 사이트) | 🟢 | log `[2026-05-10] feature` |
| **§6 static-friendly 변형 부재** | 🟢⭐ | `UMCSpatialQueryLibrary` 빌드 + file-local 우회 (2026-05-13) |
| **§11 const-correctness 체크리스트** | 🟢⭐ | `UMCHitBoneCurveUserData::IsDataValid` C2440 + fix (2026-05-14) |
| **§12 변수 이름 회피 규약** | 🟢⭐⭐⭐ | `SMCHitBoneCurveEditor` C2059 (PI 매크로) + 사용자 진단 (2026-05-14) |

## 11. ⭐ const-correctness 체크리스트 — Validation 메서드 작성 시 (2026-05-14)

### 11.1 배경

`IsDataValid(FDataValidationContext&) const` override 작성 시 `GetOuter()` Cast 결과 const propagation 의무.

### 11.2 검증 사례 (2026-05-14)

```cpp
// ❌ C2440
if (const USkeletalMesh* OwnerMesh = Cast<USkeletalMesh>(GetOuter()))
{
    if (USkeleton* Skeleton = OwnerMesh->GetSkeleton())   // ❌ const → 비-const
    // ...
}

// ✅ fix
if (const USkeleton* Skeleton = OwnerMesh->GetSkeleton())   // const 받기
```

### 11.3 6점 체크리스트

| # | 점검 | 위반 시 |
| -- | -- | -- |
| 1 | 함수 자체가 `const` 한정 | C4264 |
| 2 | `GetOuter()` Cast 결과 `const T*` 받기 | C2440 |
| 3 | Cast 결과 호출 const 오버로드만 | C2662 |
| 4 | Context modify 허용 (비-const 참조 인자) | (정상) |
| 5 | `mutable` 멤버만 modify | C2662 |
| 6 | `Super::IsDataValid(Context)` 호출 FIRST | Engine chain 끊김 |

### 11.4 const 오버로드 함수 매트릭스 + 11.5 함정 5종 + 11.6 cross-link

→ 상세 [[sources/ue-coreuobject-uobject]] §2.10 + [[sources/ue-assetclasses-mesh]] §3.

## 12. ⭐⭐⭐ KMCProject 변수 이름 회피 규약 (2026-05-14 신규, 사용자 진단)

### 12.1 배경

UE 글로벌 헤더 (`UnrealMathUtility.h` / `Build.h` 등) 가 *모든 cpp 가 transitive include*. 매크로 식별자 (`PI` / `SMALL_NUMBER` / `check` 등) 와 변수 이름 충돌 시 전처리기 단계에서 즉시 치환 → C2059 / silent pollution.

→ vault [[sources/ue-coreuobject-uobject]] §2.12 매트릭스 상세 + 매크로 11종 카탈로그.

### 12.2 KMCProject 채용 규약 — Underscore prefix

```cpp
// ❌ C2059 — PI 매크로 치환
auto* PI = Mesh->PreviewInstance.Get();
float Pi = 3.14f;
int32 SMALL_NUMBER = 1;
bool check = bSomeCondition;

// ✅ KMCProject 표준 — underscore prefix
auto* _PreviewInstance = Mesh->PreviewInstance.Get();
float MyPi = 3.14f;
int32 LocalSmallNumber = 1;
bool bCheckOK = bSomeCondition;
```

### 12.3 변수 이름 회피 룰 (3종)

| # | 룰 | 사용 케이스 |
| -- | -- | -- |
| 1 ⭐ | **Underscore prefix (`_`)** — 매크로 충돌 회피 + local 변수 시그널 | 짧은 local 변수 (loop iterator / temp) |
| 2 ⭐ | **도메인 prefix** (예: `Anim`, `Bone`, `MC`) — 의미 명확 + 충돌 회피 | 멤버 변수 / 함수 인자 / public API |
| 3 | **camelCase 시작 lowercase** — UE 표준 외 — 사용 *지양* | (KMCProject 미사용) |

→ KMCProject 표준 = **#1 underscore prefix** (가장 짧음 + 매크로 회피 + lint 신호 명확).

### 12.4 검증 사례 (2026-05-14)

```
SMCHitBoneCurveEditor.cpp 의 `auto* PI` (3회 사용) → C2059
  ↓ 변수 이름 변경
`auto* _PreviewInstance` → 빌드 통과
```

⭐ **사용자 직접 진단** — vault 2회 잘못된 가설 (ToolMenus / MinimalAPI) 후 사용자가 PI 매크로 root cause 발견. log: `[2026-05-14] fix | ⚠ 자체 평가 정정 — Phase 5 C2059 진짜 원인 = UE PI 매크로`.

### 12.5 회피 의무 매크로 식별자 (KMCProject + UE)

UE 글로벌 매크로 (vault [[sources/ue-coreuobject-uobject]] §2.12.3 상세 매트릭스):

| 매크로 | 충돌 위험 |
| -- | -- |
| `PI` / `INV_PI` / `HALF_PI` / `TWO_PI` | ⭐⭐⭐ Math 글로벌 |
| `SMALL_NUMBER` / `KINDA_SMALL_NUMBER` / `BIG_NUMBER` / `EULERS_NUMBER` | ⭐⭐ Math 글로벌 |
| `MAX_FLT` | ⭐ Math 글로벌 |
| `check` / `CHECK` / `verify` | ⭐⭐⭐ Build.h assert macro |
| `INDEX_NONE` / `NAME_None` | ⭐ UE 상수 (값 사용 OK, 변수 이름 X) |

KMCProject 자체 매크로 (`MCAssetValidation.h`):

| 매크로 | 충돌 위험 |
| -- | -- |
| `MC_LOGRET_*` / `MC_ENSURE_*` (8종) | ⭐ KMCProject 자체 |
| `MCSP_LOGRET_*` (file-local) | (local — 영향 적음) |

→ 모든 변수 이름은 위 식별자 회피.

### 12.6 진단 가이드 — C2059 "구문 오류: 상수" 발생 시

```
[순서]
1. 에러 라인의 변수 이름을 §12.5 매크로 식별자 매트릭스 와 대조
2. 매칭 발견 시 → underscore prefix 추가 (KMCProject 표준)
3. 매칭 없음 → 다른 함정 (type 인식 / template 의존 등) 검토
4. *MinimalAPI* / *type 인식 실패* 가설은 *나중* — 매크로 가설 우선
```

⭐ vault 의 함정 진단 우선순위 — *전처리기 단계* > *문법 단계* > *링크 단계*.

### 12.7 후속 — 자동 검출 (clang-tidy 룰)

`[[synthesis/mc-validation-automation-tooling]]` 통합 — KMCProject cpp 안 *위 매크로 식별자 변수 이름* 자동 검출 룰 추가. 매 빌드 시 warning.

### 12.8 cross-link

- [[sources/ue-coreuobject-uobject]] §2.12 — vault 일반화 매트릭스 (UE 글로벌 매크로 11종)
- [[synthesis/mc-character-hit-reaction-pipeline]] §6.5 함정 12 — KMCProject 검증 사례
- [[synthesis/mc-validation-automation-tooling]] — clang-tidy 자동 검출 후속
