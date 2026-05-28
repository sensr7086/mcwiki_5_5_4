---
type: source
title: "UE Animation — AnimInstance sub-skill"
slug: ue-animation-animinstance
source_path: raw/ue-wiki-llm/skills/Animation/references/AnimInstance.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-28
audit_5_5_4: pass-body-reconciled  # 2026-05-28 Phase 2-C body-reconciliation
related_entities:
  - "[[entities/UAnimInstance]]"
  - "[[entities/FAnimInstanceProxy]]"
  - "[[entities/UAnimMontage]]"
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, runtime, animation, slot-system, case-study-pair, kmcproject-pair]
---

# UE Animation — AnimInstance sub-skill

> Source: [[raw/ue-wiki-llm/skills/Animation/references/AnimInstance.md]]
> Parent: [[sources/ue-animation-skill]]

## 1. Summary

[[entities/UAnimInstance]] (1,705 lines) 라이프사이클 + [[entities/FAnimInstanceProxy]] (워커 스레드) + Curve API + Montage_* 시리즈 + Slot 시스템 (FName 1급 식별자).

## 2. Key claims

- 라이프사이클 5 단계: NativeInitializeAnimation → NativeBeginPlay → NativeUpdateAnimation (게임 스레드) → NativeThreadSafeUpdateAnimation (워커) → NativeUninitializeAnimation.
- 게임 스레드 vs 워커 분리 의무: NativeUpdate 안에서 Pawn / World 의존 OK. ThreadSafeUpdate 안에서는 GameThread API 호출 금지 (캐싱한 데이터만).
- FAnimInstanceProxy: AnimGraph Update_AnyThread / Evaluate_AnyThread 의 데이터 owner. Custom Proxy 는 USTRUCT 자손.
- Curve API: GetCurveValue / GetCurveValueFiltered / SetCurveValue / GetActiveCurveNames.
- Montage_* API: Montage_Play / Montage_Stop / Montage_JumpToSection / Montage_IsPlaying. OnMontageBlendingOut / OnMontageEnded delegate.
- Profiling 의무 ([[concepts/Profiling-Scope-Rule]]): 모든 Native* 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`.
- AnimClass 결정: SkeletalMeshComponent->SetAnimClass(Class) — TSubclassOf<UAnimInstance>.
- **§4 신규 (Cycle 5p §B4)** — Slot System: `FName SlotNodeName` 이 AnimInstance/Montage API 의 1급 식별자. AnimGraph 안 Slot 노드 (`UAnimGraphNode_Slot`) 이름과 매칭.

## 3. Open questions

- [ ] FAnimInstanceProxy 의 정확한 데이터 흐름 (게임 → 워커 → 게임)
- [ ] Slot 다중 활성 시 Weight 합산 규칙 (`GetSlotMontageGlobalWeight` vs `GetSlotMontageLocalWeight` 차이)

## 4. ⭐ Slot System — Cycle 5p §B4 신규

### 4.1 Engine 권위 4건 (UE 5.7.4 verify)

→ Engine 본가: `Engine/Source/Runtime/Engine/Classes/Animation/AnimInstance.h` (Phase 2b evaluator 가 4건 모두 라인 일치 verify, Self-correction 0건).

| Engine 라인 | 시그니처 | 의미 |
| -- | -- | -- |
| **L437** | `ENGINE_API float GetSlotMontageGlobalWeight(const FName& SlotNodeName) const;` | Slot 의 **글로벌 가중치** (모든 Montage 인스턴스 합산) |
| **L442** | `ENGINE_API float GetSlotMontageLocalWeight(const FName& SlotNodeName) const;` | Slot 의 **로컬 가중치** (현재 활성 Montage 만) |
| **L605** | `ENGINE_API float Blueprint_GetSlotMontageLocalWeight(FName SlotNodeName) const;` | BP 노출 (Blueprint 호출용) |
| **L1619** | `FQueuedRootMotionBlend::SlotName` | Root Motion Blend 의 Slot 식별자 (queued root motion 시스템) |

⭐ 4건 모두 `FName` 또는 `const FName&` 으로 SlotName 사용 — Slot 은 AnimInstance 의 **1급 식별자**.

### 4.2 Slot 시스템 동작

```
AnimGraph 안 UAnimGraphNode_Slot (디자이너가 명명):
    ┌─────────────────────────────┐
    │ Slot: "DefaultGroup.AttackSlot" │
    └─────────────────────────────┘
                ↓
런타임 — AnimInstance::Montage_Play(MontageAsset, ..., SlotNodeName="AttackSlot"):
    1. SlotNodeName 으로 AnimGraph 안 Slot 노드 검색
    2. 매칭된 Slot 노드의 Source pose 를 Montage 의 pose 로 대체
    3. Weight blend (GetSlotMontageGlobalWeight / GetSlotMontageLocalWeight) 적용
                ↓
SlotName == NAME_None → AnimInstance default Slot 사용 (AnimGraph 의 첫 Slot)
```

### 4.3 SlotName 사용 패턴 — 3가지

1. **`Montage_Play(Montage, PlayRate, ..., SlotNodeName)`** — 명시적 Slot 지정
2. **`UAnimMontage::SlotAnimTracks`** — Montage 자산 안 Track 별로 Slot 명시 (다중 Slot Montage)
3. **`UAnimGraphNode_Slot` UPROPERTY `SlotName`** — AnimGraph 노드의 정적 식별자

### 4.4 함정 — SlotName 매칭 실패

- `Montage_Play` 호출 시 `SlotNodeName` 이 AnimGraph 의 Slot 노드 이름과 불일치 → **silent fail** (Montage 재생 안 됨, 에러 메시지 없음)
- 회피: `AnimInstance::GetActiveSlotNodeWeights()` 로 활성 Slot 목록 verify

### 4.5 ⭐ Case Study: KMCProject UMCComboMontageSection (Cycle 5p §B4)

> **case study 페어**: [[synthesis/mc-combo-section-levelsequence-style-upgrade]] §2.2 (자손 specific 결정) + [[synthesis/mc-combo-editor-levelsequence-lite]] §3.5.2 (Phase 2b 자손 격상).
>
> **vault scope 정책** ([[00_meta/08_VaultScopePolicy]]): 본 sub-§은 KMCProject (mc-) 실측 사례를 본 일반 페이지 (ue-) 에 reverse-link 보강한 항목.

KMCProject `UMCComboMontageSection` 은 Phase 2b 에서 `FName SlotName` 을 UPROPERTY 로 신규 추가 — Engine 권위 4건 모두 verify 후 적용:

```cpp
// MCComboMontageTrack.h (Phase 2b 신규)
UCLASS(BlueprintType)
class MCPLAYMODULE_API UMCComboMontageSection : public UMCComboSection
{
    GENERATED_BODY()
public:
    /** 재생할 AnimMontage (Soft Reference). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combo|Montage")
    TSoftObjectPtr<UAnimMontage> Montage;

    /** 시작 섹션명 (몽타주 안 named section — 빈 = 처음부터). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combo|Montage")
    FName StartSectionName = NAME_None;

    /**
     * AnimInstance Slot Name — 몽타주가 재생될 Slot 노드.
     * NAME_None = AnimInstance default Slot 사용.
     * 권위: Engine/Source/Runtime/Engine/Classes/Animation/AnimInstance.h
     *   L437 GetSlotMontageGlobalWeight(const FName& SlotNodeName)
     *   L442 GetSlotMontageLocalWeight(const FName& SlotNodeName)
     *   L605 Blueprint_GetSlotMontageLocalWeight(FName SlotNodeName)
     *   L1619 FQueuedRootMotionBlend::SlotName
     */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combo|Montage")
    FName SlotName = NAME_None;

    /** AnimNotify 발화 skip 여부 (default false = 발화). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Combo|Montage")
    bool bSkipAnimNotifiers = false;
};
```

### 4.6 SlotName 베이스 vs 자손 결정 (KMCProject 사례)

UMCComboInputSection / UMCComboNotifySection 은 SlotName 의미 없음 (InputAction / GameplayTag 도메인) — 자손 specific 유지가 깨끗한 OOP. KMCProject 는 **베이스에 SlotName 비-격상, UMCComboMontageSection only 추가** 결정.

### 4.7 evaluator 검증 (Cycle 5p)

본 sub-§의 권위 인용 (L437/L442/L605/L1619) 은 KMCProject Phase 2b evaluator (94.0 / 100 PASS) 가 직접 verify. UE 5.7.4 (Build.version verify ✓) 에서 4건 모두 라인 일치, Self-correction 0건.

## 5. Cross-link

### Engine 권위

- `Engine/Source/Runtime/Engine/Classes/Animation/AnimInstance.h` L437 / L442 / L605 / L1619 (Slot Name 4 시그니처 — UE 5.7.4 verify)

### Parent / 페어 sub-skills

- Parent: [[sources/ue-animation-skill]]
- 페어 sub-skill: [[sources/ue-animation-animgraph]] (UAnimGraphNode_Slot) · [[sources/ue-animation-animnotify]] (AnimNotify 발화) · [[sources/ue-animation-rootmotion]] (FQueuedRootMotionBlend.SlotName) · [[sources/ue-animation-sync]] (Sync Marker)
- 자산 측 페어: [[sources/ue-assetclasses-animation]] (UAnimMontage 자산)

### Concept

- [[concepts/RootMotion]] · [[concepts/Inertialization]]

### ⭐ Case study (mc-, Cycle 5p §B4)

- [[synthesis/mc-combo-section-levelsequence-style-upgrade]] §2.2 (Phase 1 handoff — 자손 specific 결정)
- [[synthesis/mc-combo-editor-levelsequence-lite]] §3.5.2 (Phase 2 누적 합성 — UMCComboMontageSection 자손 격상)

### Governance (Cycle 5p)

- [[00_meta/08_VaultScopePolicy]] §3 — `mc-` 페이지 사례를 `ue-` 일반 페이지에 reverse-link 의무 (본 §4.5)
- [[00_meta/03_EvaluatorRecipe]] §1.5 — Stage 2.X Engine Authority Verification (본 §4.7)
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 1
- 추가 (5.5.4 에만): 0
- 제거 (5.7.4 에만, 5.5.4 에 없음): 0
- 수치 변경: 3

**주요 시그니처**:
- `> **위치**: `Engine/Source/Runtime/Engine/Public/Animation/AnimInstance.h` (1,776) → > **위치**: `Engine/Source/Runtime/Engine/Classes/Animation/AnimInstance.h` (1,705`

**5.5.4 에만 (5.7.4 에 없음)**:
_(없음)_

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/Animation/references/AnimInstance.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/Animation/references/AnimInstance.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **1 변경**
- 정합 후 tier: **🟢 pass-body-reconciled**
