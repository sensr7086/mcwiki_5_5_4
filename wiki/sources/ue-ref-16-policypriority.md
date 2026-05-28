---
type: source
title: "UE refs — 16 PolicyPriority (5단 우선순위 ⚖)"
slug: ue-ref-16-policypriority
source_path: raw/ue-wiki-llm/references/16_PolicyPriority.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
tags: [ue, reference, governance, policy, conflict-resolution]
---

# UE refs — 16 PolicyPriority ⚖

> Source: [[raw/ue-wiki-llm/references/16_PolicyPriority.md]] · 13 횡단 인덱스 + 50+ 규칙의 **충돌 시 우선순위** + 결정 트리

## 1. Summary

LLM_Wiki 의 13 횡단 정책 + 6대/12종/5대/8단/4단/7단계 50+ 규칙 **동시 적용 불가** — 우선순위 + 충돌 해결 트리 의무. 5 Tier (Compile > GC > Runtime > Performance > Maintainability) + 자주 발생 충돌 5종 결정 매트릭스 + 인지 부하 감소 전략. vault [[00_meta/01_PolicyPriority]] 의 UE 특화 정밀판. CLAUDE.md §0.1.2 매핑.

## 2. ⭐ 5단계 Tier 우선순위 🟢

> **충돌 시 상위 Tier 우선**. 동일 Tier 내 정책 = §4 결정 트리.

### Tier 1 — 컴파일 / 빌드 (절대 위반 불가) 🔴

```
1. Cooked Build 컴파일 통과
2. Editor 컴파일 통과
3. UFunction / UPROPERTY 매크로 정확
4. Replicated 정합성 (DOREPLIFETIME 등록)
```

→ **위반 = 코드 동작 X**. 다른 모든 정책보다 우선.

### Tier 2 — 메모리 / GC (Crash 방지) 🚨

```
5. UObject 멤버 = UPROPERTY() + TObjectPtr ([[sources/ue-ref-10-componentpolicies]] §3)
6. 비-UCLASS = TStrongObjectPtr 또는 FGCObject (§3)
7. FStreamableHandle Pin ([[sources/ue-ref-11-assetloadingpolicy]] §5)
8. Async 콜백 IsValid(this) 가드 (§5.5)
9. Subsystem nullptr 가드 (Dedicated Server)
```

→ **Crash 또는 메모리 누수 직결**.

### Tier 3 — 런타임 동작 🚨

```
10. Mobility 명시 (10_ComponentPolicies §1)
11. Constructor 안 어셋 로드 금지 (11_AssetLoadingPolicy §1)
12. CreateDefaultSubobject 는 Constructor 안만 (10_ComponentPolicies §6)
13. Super 호출 위치 정확 (PostInit FIRST / EndPlay LAST) ([[sources/ue-ref-04-overrideindex]])
14. Enhanced Input 의무 + DefaultInput.ini ([[sources/ue-input-skill]] §1-§2)
15. ETriggerEvent 정확 (Move=Triggered / Jump=Started+Completed) (§5)
16. bTriggerWhenPaused (§10)
17. LocalPlayer Subsystem (§9)
```

→ **위반 시 동작 안 하거나 잘못 동작**.

### Tier 4 — 성능 🎯

```
18. PrimaryComponentTick = false 기본 ([[sources/ue-ref-10-componentpolicies]] §5)
19. TActorIterator / TObjectIterator 사용 X ([[sources/ue-ref-09-globaliteratorpolicy]])
20. 콜백 첫 줄 프로파일링 스코프 ([[sources/ue-ref-07-profilingscopeRule]])
21-25. SkM Bone LOD / SM ScreenSize / Actor Merging / Audio Cull / Niagara Quality ([[sources/ue-ref-12-assetoptimizationpolicy]] §1-§5)
26. PreloadPrimaryAssets Match Start (11_AssetLoadingPolicy §6.3)
27. SpawnActorDeferred + FinishSpawning (Actor §12)
28. DeadZone 의무 (Input §6)
```

→ **위반 시 60fps 미달 / 메모리 초과 / 첫 Spawn 히칭**. 측정 가능.

### Tier 5 — 유지보수성 🟢

```
29. Epic 명명 규칙 (U/A/F/I/E 접두사)
30. 헤더 최소 포함 + 전방선언
31. const 정확성
32. WITH_EDITOR 가드 ([[sources/ue-ref-05-editoronlyindex]])
33. Cross-link 정확성
34. SKILL.md < 30KB (progressive disclosure)
35. UPROPERTY EditDefaultsOnly + BP 지정 (Input §8)
36. Face Button 추상 (Input §11)
```

→ **위반해도 동작은 함**. 가장 낮은 우선순위.

## 3. ⭐ 자주 발생 충돌 5종 (해결 매트릭스) 🟢

### 충돌 1 — Constructor CreateDefaultSubobject vs 어셋 로드 금지

| 정책 A | 정책 B | 결정 |
| -- | -- | -- |
| 10_ComponentPolicies §6: CreateDefaultSubobject 는 Constructor 안만 | 11_AssetLoadingPolicy §1: Constructor 안 어셋 로드 절대 금지 | **둘 다 만족 — Component 인스턴스 ≠ 어셋 로드** |

```cpp
// ✅ 정답
- Component 인스턴스 = Constructor 안 CreateDefaultSubobject (10_§6)
- 자산 (Mesh / Material) = UPROPERTY EditAnywhere + BP 지정 (11_)
- 동적 로드 = BeginPlay 안 FStreamableManager Async
```

### 충돌 2 — bCanEverTick=false vs 매 프레임 갱신 필요

| 우선순위 | 패턴 |
| -- | -- |
| 1순위 | `TickInterval` (0.05~1s) — 매 프레임 X |
| 2순위 | TimerManager + Timer Interval |
| 3순위 | Significance Manager + 거리 기반 활성/비활성 |
| 4순위 (마지막) | `bCanEverTick=true` — 명시 사유 + 프로파일링 스코프 의무 |

### 충돌 3 — Hard Reference (단순성) vs Soft Reference (메모리)

11_AssetLoadingPolicy §2.2 결정 매트릭스:

| 사용 빈도 / 종류 | 결정 |
| -- | -- |
| 항상 사용 + 작은 자산 | **Hard** (TObjectPtr) |
| 자주 사용 + 종류 적음 | **Hard + Match Start PreLoad** |
| 가끔 사용 + 종류 많음 | **Soft + Primary Asset** |
| DLC / MOD | **Soft + 동적 로드** (LoadPrimaryAsset) |

### 충돌 4 — TActorIterator 금지 vs Editor 1회성

09_GlobalIteratorPolicy §7 허용 5조건 만족 시 예외:

1. **`WITH_EDITOR` 가드**
2. **1회 호출** (BeginPlay 1회 / 사용자 액션 1회)
3. 게임 시작 시 캐싱
4. 사용자 명시적 액션 (버튼 클릭)
5. PIE 안만

→ 게임 런타임 = 금지 / Editor 도구 = 5조건 + 스코프 + 주석 시 허용.

### 충돌 5 — Cooked Build 검증 vs 작은 변경

| 변경 규모 | 검증 단계 |
| -- | -- |
| 작은 변경 (단일 파일 typo) | Editor 빌드 + PIE 검증 |
| 중간 변경 (여러 파일) | + Standalone |
| 큰 변경 (신규 Class / Module) | + Cooked Development |
| Production 임박 | + Cooked Shipping |

## 4. 충돌 해결 결정 트리 🟢

### 4.1. 일반 결정 트리

```
정책 A 와 정책 B 충돌?
├── 다른 Tier?
│   └── 상위 Tier 우선 (Tier 1 > Tier 2 > ... > Tier 5)
│
├── 같은 Tier?
│   ├── 더 구체적 정책 우선
│   ├── 측정 가능한 정책 우선
│   └── 명시적 예외 케이스 검토 (§7 등)
│
└── 사용자 명시 예외?
    └── 우선 (단 §6 검토 + 주석 의무)
```

### 4.2. 간결 결정 트리

```
정책 위반 발견?
├── Tier 1 (컴파일)? → 즉시 수정 (다른 모든 것 우선)
├── Tier 2 (GC)?    → 즉시 수정 (Crash 위험)
├── Tier 3 (런타임)? → 수정 + 사유 검토
├── Tier 4 (성능)?
│   ├── 측정 가능 = 영향 측정 후 결정
│   └── 측정 불가 = 정책 따름 (보수적)
└── Tier 5 (유지보수)? → 사용자 결정 (사유 명시)
```

## 5. 인지 부하 감소 — 작업 단위별 적용 🟢

### 5.1. 항상 의무 정책 (5개)

```
모든 코드 작성 시:
1. Tier 1 컴파일 정확성
2. Tier 2 GC 안전
3. 07_ProfilingScopeRule (콜백 스코프)
4. 09_GlobalIteratorPolicy (전역 이터레이터 금지)
5. 14_TaskHandoffTemplate (세션 종료 시)
```

### 5.2. 카테고리별 추가

| 카테고리 | 의무 추가 |
| -- | -- |
| `[Components]` | 10_ComponentPolicies (6대) + 11_AssetLoadingPolicy (어셋 멤버 시) |
| `[GameFramework]` | 10_ComponentPolicies + 11_AssetLoadingPolicy (자주 Spawn) |
| `[AssetClasses]` | 11 + 12_AssetOptimizationPolicy + 05_EditorOnlyIndex (Editor 데이터) |
| `[Input]` | Input (12종) + 10 (UInputComponent 호스트) |
| `[Slate]/[UMG]` | 06_InvalidationHotspots + 04_OverrideIndex |

### 5.3. 시나리오별 추가

| 시나리오 | 의무 추가 |
| -- | -- |
| 멀티플레이 | 11 (Replication) + 15_EvaluatorRecipe (Replicated 정합성) |
| 다수 NPC | 12 §6 통합 매트릭스 |
| Pause / 메뉴 | Input §10 (bTriggerWhenPaused) |
| 큰 작업 (3+ 단계) | 14_TaskHandoff + 15_EvaluatorRecipe |
| Production 직전 | 15_EvaluatorRecipe Stage 2-8 모두 |

## 6. 사용자 명시 예외 처리 🟡

사용자가 의도적 정책 위반 명시 시 Claude 행동:

```
1. ⚠ 경고 — "이 코드는 09_GlobalIteratorPolicy §7 5조건 중 N개 만족 안 함"
2. 결과 명시 — "다음 함정 가능 — 매 호출 N개 객체 순회 / 60fps 미달 위험"
3. 사용자 결정 존중 — 실행
4. 코드 주석 — "// USER_OVERRIDE: 09_GlobalIteratorPolicy §7 — 사유 {사용자 명시}"
5. _handoffs 에 Decision Log 기록
```

## 7. "정책 안 적용" 정상 케이스

| 케이스 | 적용 안 하는 정책 |
| -- | -- |
| 에디터 도구 (`WITH_EDITOR`) | 09_GlobalIteratorPolicy (TActorIterator 허용 §7) |
| 단순 프로토타입 | Input (Legacy 허용) |
| 5.x 마이그레이션 | Input (Legacy 호환 단계) |
| 단일 플레이어 작은 게임 | 12 (큰 매트릭스 불필요) |
| DLC / MOD 안 함 | UPrimaryDataAsset (단순 UDataAsset OK) |
| Editor PIE 만 | Cooked Build 검증 (Production 시만) |

## 8. 안티패턴 (10대) 🟡

| # | 함정 | 정답 |
| -- | -- | -- |
| 1 | 모든 정책 100% 동시 적용 시도 | Tier 1-2 의무 + Tier 3-5 = 시나리오별 |
| 2 | 정책 충돌 시 임의 결정 | §4 결정 트리 적용 |
| 3 | "정책 따랐다" 자기 평가 | Evaluator 별도 ([[sources/ue-ref-15-evaluatorrecipe]]) |
| 4 | Tier 5 만 적용 + Tier 1-2 무시 | Tier 우선순위 의무 |
| 5 | "사용자 결정" 으로 모든 정책 무시 | §6 — 경고 + 결과 명시 후 따름 |
| 6 | 작은 변경에 Tier 1-5 모두 검증 | §5 작업 단위별 적용 |
| 7 | 정책 충돌 시 사용자 협의 X | 모호하면 사용자 확인 |
| 8 | 정책끼리 cross-link X | §3 5종 충돌 케이스 cross-link |
| 9 | 정책 stale (5.x 변경 미반영) | [[sources/ue-ref-18-modelevolutionaudit]] 정기 감사 |
| 10 | 외부 Evaluator 없이 자기 평가 | [[sources/ue-ref-15-evaluatorrecipe]] 별도 인스턴스 |

## 9. Cross-link

- **모든 횡단 인덱스** (04-13) — 본 문서가 우선순위 결정
- 자매 governance hub: 📋 [[sources/ue-ref-14-taskhandofftemplate]] (Decision Log 에 충돌 해결 기록) · 🔍 [[sources/ue-ref-15-evaluatorrecipe]] (Tier 별 검사) · 📊 [[sources/ue-ref-17-qualitycriteria]] (Tier 4 측정 기준) · 🕰 [[sources/ue-ref-18-modelevolutionaudit]] (정책 stale 감사)
- Tier 1-5 정책 hub: [[sources/ue-ref-04-overrideindex]] · [[sources/ue-ref-05-editoronlyindex]] · [[sources/ue-ref-07-profilingscopeRule]] · [[sources/ue-ref-09-globaliteratorpolicy]] · [[sources/ue-ref-10-componentpolicies]] · [[sources/ue-ref-11-assetloadingpolicy]] · [[sources/ue-ref-12-assetoptimizationpolicy]] · [[sources/ue-ref-06-invalidationhotspots]] · [[sources/ue-ref-08-overlaphotspots]]
- vault meta: [[00_meta/01_PolicyPriority]] (vault 일반판)
