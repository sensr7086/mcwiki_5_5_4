---
name: policy-priority
description: 13개 횡단 인덱스 + 6대 / 12종 / 5대 / 8단 / 4단 / 7단계 50+ 규칙 충돌 시 우선순위 + 결정 트리. 정책 간 모순 / Edge case 처리 표준. 글 2 의 "단순성 유지" 원칙 적용.
---

# 16. Policy Priority — 정책 충돌 해결 표준

> 본 문서는 **LLM_Wiki 의 13개 횡단 정책 + 50+ 규칙 충돌 시** 결정 기준. 외부 평가자가 지적한 핵심 결함 — "정책 충돌 가이드 부재 / 인지 부하" — 의 해결.
>
> **요지**: 모든 정책 동시 적용 = 불가능. **우선순위 + 충돌 해결 트리** 필수.

---

## 0. 정책 인지 부하 현황 (외부 평가자 지적)

```
13개 횡단 인덱스 + 카테고리 별 규칙:
- 6대 정책 (Components — 10_ComponentPolicies)
- 12종 규약 (Input — Input)
- 5대 영역 (Optimization — 12_AssetOptimizationPolicy)
- 8단 정책 (AssetLoading — 11_AssetLoadingPolicy)
- 4단 표준 (SpawnActor 히칭 방지)
- 7단계 (IMC Priority)
- 11단계 (Actor 라이프사이클)
- 9개 항목 (다수 NPC 매트릭스)
- 5종 ResolutionRule (Audio Concurrency)
- 4종 SignificanceHandling (Niagara)
- ...

= 매 코드 작성 시 50+ 규칙 동시 적용 의무 → 인지 부하 폭발
```

---

## 1. 정책 우선순위 매트릭스 (5단계)

> **충돌 시 상위 정책 우선**. 동일 단계 내 정책끼리는 §3 결정 트리 적용.

### Tier 1 — 컴파일 / 빌드 (가장 높은 우선순위)

```
🔴 절대 위반 불가:
1. Cooked Build 컴파일 통과
2. Editor 컴파일 통과
3. UFunction / UPROPERTY 매크로 정확
4. Replicated 정합성 (DOREPLIFETIME 등록)
```

→ **이걸 위반 = 코드 동작 안 함**. 다른 모든 정책보다 우선.

### Tier 2 — 메모리 / GC (Crash 방지)

```
🚨 GC 안전 + 메모리 누수 방지:
5. UObject 멤버 = UPROPERTY() + TObjectPtr (10_ComponentPolicies §3)
6. 비-UCLASS = TStrongObjectPtr 또는 FGCObject (10_ComponentPolicies §3)
7. FStreamableHandle Pin (11_AssetLoadingPolicy §5)
8. Async 콜백 IsValid(this) 가드 (11_AssetLoadingPolicy §5.5)
9. Subsystem nullptr 가드 (Dedicated Server)
```

→ **Crash 또는 메모리 누수 직결**. Tier 1 다음 우선.

### Tier 3 — 런타임 동작 (정책 위반 시 동작 깨짐)

```
🚨 런타임 정확성:
10. Mobility 명시 (10_ComponentPolicies §1)
11. Constructor 안 어셋 로드 금지 (11_AssetLoadingPolicy §1)
12. CreateDefaultSubobject 는 Constructor 안만 (10_ComponentPolicies §6)
13. Super 호출 위치 정확 (PostInit 처음 / EndPlay 마지막) (04_OverrideIndex)
14. Enhanced Input 의무 + DefaultInput.ini 설정 (Input §1-§2)
15. ETriggerEvent 정확 (Move=Triggered / Jump=Started+Completed) (Input §5)
16. bTriggerWhenPaused (Input §10)
17. LocalPlayer Subsystem (Input §9)
```

→ **위반 시 동작 안 하거나 잘못 동작**.

### Tier 4 — 성능 (60fps / 메모리 한계)

```
🎯 성능 정책:
18. PrimaryComponentTick = false 기본 (10_ComponentPolicies §5)
19. TActorIterator / TObjectIterator 사용 안 함 (09_GlobalIteratorPolicy)
20. 콜백 첫 줄 프로파일링 스코프 (07_ProfilingScopeRule)
21. SkeletalMesh Bone LOD (12_AssetOptimizationPolicy §1)
22. StaticMesh LOD ScreenSize 표준 (12_AssetOptimizationPolicy §2)
23. Actor Merging (HISM / HLOD) (12_AssetOptimizationPolicy §3)
24. Audio Culling (Attenuation + Concurrency) (12_AssetOptimizationPolicy §4)
25. Niagara Quality Scaling (12_AssetOptimizationPolicy §5)
26. PreloadPrimaryAssets Match Start (11_AssetLoadingPolicy §6.3)
27. SpawnActorDeferred + FinishSpawning (Actor §12)
28. DeadZone 의무 (Input §6)
```

→ **위반 시 60fps 미달 / 메모리 초과 / 첫 Spawn 히칭**. 측정 가능.

### Tier 5 — 유지보수성 (Code Quality)

```
🟢 코드 품질:
29. Epic 명명 규칙 (U/A/F/I/E 접두사)
30. 헤더 최소 포함 + 전방선언
31. const 정확성
32. 에디터 전용 코드 = WITH_EDITOR 가드 (05_EditorOnlyIndex)
33. Cross-link 정확성 (sub-skill)
34. SKILL.md < 30KB (글 3 progressive disclosure)
35. UPROPERTY EditDefaultsOnly + BP 지정 (Input §8)
36. Face Button 추상 (Input §11)
```

→ **위반해도 동작은 함**. 가장 낮은 우선순위.

---

## 2. 충돌 해결 결정 트리

### 2.1 일반 결정 트리

```
정책 A 와 정책 B 충돌?
├── A 와 B 가 다른 Tier?
│   └── 상위 Tier 우선 (예: Tier 1 vs Tier 4 → Tier 1 우선)
│
├── A 와 B 가 같은 Tier?
│   ├── 더 구체적 정책 우선 (구체성 우선)
│   │   예: "Constructor 안 어셋 로드 금지" (구체적) vs "어셋 멤버 = UPROPERTY" (일반)
│   │   → 구체적 정책 우선
│   │
│   ├── 측정 가능한 정책 우선 (측정 가능성)
│   │   예: "60fps 유지" (측정 가능) vs "코드 가독성" (주관적)
│   │   → 측정 가능 우선
│   │
│   └── 명시적 예외 케이스?
│       예: "TActorIterator 금지" 정책 (09_GlobalIteratorPolicy)
│       └── §7 허용 예외 5조건 만족 시 → 정책 위반 X
│
└── 사용자 명시 예외?
    └── 명시적 사용자 결정 우선 (단 §3 검토 필수)
```

### 2.2 자주 발생하는 충돌 5종 (해결책)

#### 충돌 1: Constructor 안 CreateDefaultSubobject vs 어셋 로드 금지

```
10_ComponentPolicies §6 CDO: "CreateDefaultSubobject 는 Constructor 안만"
11_AssetLoadingPolicy §1: "Constructor 안 어셋 로드 절대 금지"

❓ Component 멤버 (Mesh / Audio Component) = Constructor 의 CreateDefaultSubobject 인데?
   → CreateDefaultSubobject 는 컴포넌트 인스턴스 생성 (어셋 로드 X)
   → 컴포넌트의 자산 멤버 (Mesh / Material / Texture) 는 별도 — Soft + BeginPlay Async

✅ 정답:
- Component 인스턴스 = Constructor 안 CreateDefaultSubobject (10_ComponentPolicies §6)
- 자산 (Mesh / Material) = UPROPERTY EditAnywhere + BP 지정 (11_AssetLoadingPolicy)
- 동적 로드 = BeginPlay 안 FStreamableManager Async
```

#### 충돌 2: bCanEverTick = false vs 매 프레임 갱신 필요

```
10_ComponentPolicies §5: "bCanEverTick = false 기본"
실제: 매 프레임 갱신 필요 (예: 카메라 흔들림)

❓ 둘 다 만족 가능?
   → §5 의 "마지막 수단" — 정말 매 프레임 필요한가?

✅ 정답:
1순위: TickInterval (0.05~1s) — 매 프레임 X
2순위: TimerManager + Timer Interval
3순위: Significance Manager + 거리 기반 활성/비활성
4순위 (마지막): bCanEverTick = true — 명시적 사유 + 프로파일링 스코프 의무
```

#### 충돌 3: Hard Reference (단순성) vs Soft Reference (메모리)

```
11_AssetLoadingPolicy §2.2: "결정 트리"

❓ 무기 BP Class — Hard 인가 Soft 인가?
   → 자주 Spawn 되는 (Bullet / Weapon Class) = Hard + Match Start PreLoad
   → 종류 많음 (50+ Weapon) = Soft + UAssetManager Primary Asset
   → DLC / MOD = Soft + LoadPrimaryAsset 동적

✅ 결정 매트릭스 (11_AssetLoadingPolicy §2.2):
- 항상 사용 + 작은 자산 = Hard
- 자주 사용 + 종류 적음 = Hard + Match Start PreLoad
- 가끔 사용 + 종류 많음 = Soft + Primary Asset
- DLC / MOD = Soft + 동적 로드
```

#### 충돌 4: TActorIterator 금지 vs Editor 도구 / 1회성

```
09_GlobalIteratorPolicy: "TActorIterator 사용 금지"
실제: 에디터 도구에서 모든 Actor 조회 필요

❓ 모든 곳 금지?
   → §7 허용 예외 5조건:
     1. WITH_EDITOR 가드
     2. 1회 호출 (BeginPlay 1회)
     3. 게임 시작 시 캐싱
     4. 사용자 명시적 액션 (버튼 클릭)
     5. PIE 안만

✅ 정답: 게임 런타임 = 금지 / Editor 도구 = §7 5조건 만족 시 허용 + 스코프 + 주석
```

#### 충돌 5: Cooked Build 검증 의무 vs 작은 변경

```
15_EvaluatorRecipe Stage 2: "Cooked Build 검증 의무"
실제: 한 줄 변경 (typo 수정)

❓ 매 변경마다 Cooked Build?
   → §4 평가 시점 (큰 작업 / Production 직전)
   → 작은 변경 = Editor 빌드만 OK

✅ 정답:
- 작은 변경 (단일 파일) = Editor 빌드 + PIE 검증
- 큰 변경 (여러 파일 / 신규 Class) = + Standalone
- Production 임박 = + Cooked Development + Shipping
```

---

## 3. 인지 부하 감소 — 정책 사용 우선순위

### 3.1 작업 시작 시 - 필수 정책 (always)

```
모든 코드 작성 시 의무 적용 (5개):
1. Tier 1 컴파일 정확성 (의무)
2. Tier 2 GC 안전 (의무)
3. 07_ProfilingScopeRule (콜백 스코프)
4. 09_GlobalIteratorPolicy (전역 이터레이터 금지)
5. 14_TaskHandoffTemplate (세션 종료 시)
```

### 3.2 카테고리별 추가 정책 (sub-skill 페어)

| 카테고리 | 의무 추가 |
|---------|----------|
| `[Components]` | 10_ComponentPolicies (6대) + 11_AssetLoadingPolicy (어셋 멤버 시) |
| `[GameFramework]` | 10_ComponentPolicies + 11_AssetLoadingPolicy (자주 Spawn) |
| `[AssetClasses]` | 11_AssetLoadingPolicy + 12_AssetOptimizationPolicy + 05_EditorOnlyIndex (Editor 데이터) |
| `[Input]` | Input (12종) + 10_ComponentPolicies (UInputComponent 호스트) |
| `[Slate]/[UMG]` | 06_InvalidationHotspots + 04_OverrideIndex |
| `[Render]` | (전용 정책 없음 — 향후 추가) |

### 3.3 시나리오별 추가 정책

| 시나리오 | 의무 추가 |
|---------|---------|
| 멀티플레이 코드 | 11_AssetLoadingPolicy (Replication) + 15_EvaluatorRecipe (Replicated 정합성) |
| 다수 NPC 환경 | 12_AssetOptimizationPolicy §6 통합 매트릭스 |
| Pause / 메뉴 | Input §10 (bTriggerWhenPaused) |
| 큰 작업 (3+ 단계) | 14_TaskHandoffTemplate + 15_EvaluatorRecipe |
| Production 직전 | 15_EvaluatorRecipe Stage 2-8 모두 |

---

## 4. "정책 안 적용" 케이스 (정상)

> 모든 정책이 항상 적용되는 것은 아님. **명시적 예외 케이스**:

| 케이스 | 적용 안 하는 정책 |
|--------|--------------|
| **에디터 도구 (`WITH_EDITOR`)** | 09_GlobalIteratorPolicy (TActorIterator 허용) |
| **단순 프로토타입** | Input (Legacy 허용) |
| **5.x 마이그레이션** | Input (Legacy 호환 단계) |
| **단일 플레이어 작은 게임** | 12_AssetOptimizationPolicy (큰 매트릭스 불필요) |
| **DLC / MOD 안 함** | UPrimaryDataAsset 표준 (단순 UDataAsset OK) |
| **Editor PIE 만 사용** | Cooked Build 검증 (Production 시만) |

---

## 5. 정책 충돌 — 사용자 명시 예외

> **사용자가 명시적으로 정책 위반을 결정** 시 — Claude 는 **경고만** 하고 따라야 함:

```
사용자: "이 케이스는 09_GlobalIteratorPolicy 위반이지만 의도적 — TActorIterator 사용해"

Claude 행동:
1. 경고: "이 코드는 09_GlobalIteratorPolicy §7 5조건 중 N개 만족 안 함"
2. 결과 명시: "다음 함정 가능 — 매 호출 N개 객체 순회 / 60fps 미달 위험"
3. 사용자 결정 존중하여 실행
4. 코드 안 명시 주석: "// USER_OVERRIDE: 09_GlobalIteratorPolicy §7 — 사유 {사용자 명시}"
5. _handoffs 에 Decision Log 기록
```

---

## 6. 결정 트리 (간결 버전)

```
정책 위반 발견?
├── Tier 1 (컴파일)? → 즉시 수정 (다른 모든 것 우선)
├── Tier 2 (GC)? → 즉시 수정 (Crash 위험)
├── Tier 3 (런타임)? → 수정 + 사유 검토
├── Tier 4 (성능)?
│   ├── 측정 가능 = 영향 측정 후 결정
│   └── 측정 불가 = 정책 따름 (보수적)
└── Tier 5 (유지보수)?
    └── 사용자 결정 (사유 명시)

여러 정책 충돌?
├── 다른 Tier = 상위 Tier 우선
├── 같은 Tier = 구체적 정책 우선
└── 충돌 해결 안 됨 = §2.2 자주 발생하는 충돌 5종 검토
```

---

## 7. 안티패턴 (10종)

| # | 안티패턴 | 정답 |
|---|---------|------|
| 1 | 모든 정책 동시 100% 적용 시도 | Tier 1-2 의무 + Tier 3-5 = 시나리오별 |
| 2 | 정책 충돌 시 임의 결정 | §2 결정 트리 적용 |
| 3 | "정책 따랐다" 자기 평가 | Evaluator 별도 검증 (15_EvaluatorRecipe) |
| 4 | Tier 5 (유지보수) 만 적용 + Tier 1-2 무시 | Tier 우선순위 의무 |
| 5 | "사용자 결정" 으로 모든 정책 무시 | §5 — 경고 + 결과 명시 후 따름 |
| 6 | 작은 변경에 Tier 1-5 모두 검증 | §3.1-§3.3 작업 단위별 적용 |
| 7 | 정책 충돌 시 사용자 / 사용자 협의 안 함 | 모호하면 사용자 확인 |
| 8 | 정책끼리 cross-link 안 됨 | 본 문서 §2.2 5종 충돌 케이스 cross-link |
| 9 | 정책 stale (5.x 변경 미반영) | 18_ModelEvolutionAudit 정기 감사 |
| 10 | 외부 Evaluator 없이 Generator 자기 평가 | 15_EvaluatorRecipe 별도 인스턴스 |

---

## 8. 관련 문서

- 모든 횡단 인덱스 (04~13) — 본 문서가 우선순위 결정
- [`14_TaskHandoffTemplate.md`](./14_TaskHandoffTemplate.md) — Decision Log 에 정책 충돌 해결 기록
- [`15_EvaluatorRecipe.md`](./15_EvaluatorRecipe.md) — Evaluator 가 본 문서 §1 Tier 별 검사
- [`17_QualityCriteria.md`](./17_QualityCriteria.md) — Tier 4 측정 기준
- [`18_ModelEvolutionAudit.md`](./18_ModelEvolutionAudit.md) — 정책 stale 감사

---

## 9. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. 외부 평가자가 지적한 핵심 결함 (정책 충돌 가이드 부재 / 인지 부하) 해결. **5단계 Tier 우선순위** (컴파일 → GC → 런타임 → 성능 → 유지보수) + **자주 발생하는 충돌 5종** 해결 매트릭스 (Constructor CreateDefaultSubobject vs 어셋 로드 / bCanEverTick vs 매 프레임 / Hard vs Soft / TActorIterator 금지 vs Editor / Cooked 검증 vs 작은 변경) + **인지 부하 감소** 작업 단위별 정책 적용 + 카테고리별 추가 정책 매트릭스 + 시나리오별 추가 + **명시적 예외 케이스** + 사용자 명시 예외 처리 + 결정 트리 + 안티패턴 10종. |
