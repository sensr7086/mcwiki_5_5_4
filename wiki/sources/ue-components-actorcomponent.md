---
type: source
title: "UE Components — UActorComponent sub-skill"
slug: ue-components-actorcomponent
source_path: raw/ue-wiki-llm/skills/Components/references/ActorComponent.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UActorComponent]]"
related_concepts:
  - "[[concepts/Component-Lifecycle]]"
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, components]
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE Components — UActorComponent sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/ActorComponent.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

[[entities/UActorComponent]] 로직 전용 컴포넌트 베이스 — BeginPlay / EndPlay / TickComponent / GetOwner / Replication / Subobject 등록 + 6대 정책 의무.

## 2. Key claims

- 라이프사이클 6단계 ([[concepts/Component-Lifecycle]]): OnRegister → InitializeComponent → BeginPlay → Tick → EndPlay → UninitializeComponent → OnUnregister.
- Super 호출 규약: BeginPlay → Super FIRST, EndPlay → Super LAST.
- GetOwner: BeginPlay 에서 1회 캐싱 + TWeakObjectPtr 보관. Tick / 콜백 재조회 금지. → [[concepts/Component-Policies-6]] §4.
- TickComponent: PrimaryComponentTick.bCanEverTick = false 가 기본. 활성 시 TickInterval 우선.
- Replication: SetIsReplicatedByDefault(true) 또는 owning Actor 의 bReplicates. UPROPERTY(Replicated) + GetLifetimeReplicatedProps.
- Subobject 등록: CreateDefaultSubobject (Constructor 안만) 또는 NewObject<>(Outer=Actor) (런타임).

## 3. Open questions

- [ ] InitializeComponent vs BeginPlay 호출 순서 — Editor PIE vs Cooked
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 10
- 추가 (5.5.4 에만): 16
- 제거 (5.7.4 에만, 5.5.4 에 없음): 1
- 수치 변경: 0

**주요 시그니처**:
- `| `bool IsBeingDestroyed() const` (L502) | 파괴 중? | → | `bool IsBeingDestroyed() const` (L397) | 파괴 중? |`
- `| `void ToggleActive()` | L583 | | → | `void Activate(bool bReset=false)` | L457 | 활성 — 자식 자동 활성 |`
- `| `void SetAutoActivate(bool)` | L597 | AutoActivate UPROPERTY 변경 | → | `void SetAutoActivate(bool)` | L491 | AutoActivate UPROPERTY 변경 |`
- `| `UWorld* GetWorld() const override final` (L531) | World 캐시 (성능) | → | `AActor* GetOwner() const` (L415) | 부모 액터 |`

**5.5.4 에만 (5.7.4 에 없음)**:
- `| `void Deactivate()` | L463 | 비활성 |`
- `| `void SetActive(bool bNewActive, bool bReset=false)` | L471 | 토글 |`
- `| `void ToggleActive()` | L477 | |`
- `| `UWorld* GetWorld() const override final` (L425) | World 캐시 (성능) |`

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
- `| `CreateClassComponentDesc()` 🛠 | `WITH_EDITOR` | World Partition |`

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/Components/references/ActorComponent.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/Components/references/ActorComponent.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **0 변경**
- 정합 후 tier: **🟢 pass-body-no-direct-cite**
