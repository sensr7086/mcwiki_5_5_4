---
type: source
title: "UE Animation — Optimization sub-skill"
slug: ue-animation-optimization
source_path: raw/ue-wiki-llm/skills/Animation/references/Optimization.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/USkeletalMeshComponent]]"
related_concepts:
  - "[[concepts/URO]]"
  - "[[concepts/EVisibilityBasedAnimTickOption]]"
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/Bone-LOD]]"
tags: [ue, runtime, animation, optimization]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
---

# UE Animation — Optimization sub-skill ⭐⭐

> Source: [[raw/ue-wiki-llm/skills/Animation/references/Optimization.md]]
> Parent: [[sources/ue-animation-skill]]

## 1. Summary

다수 NPC Animation 최적화 **5 중 통합** — [[concepts/URO]] (FAnimUpdateRateParameters) + [[concepts/EVisibilityBasedAnimTickOption]] 5 종 + AnimSharing (UAnimSharingInstance) + AnimationBudgetAllocator (USkeletalMeshComponentBudgeted + IAnimBudgetAllocator Plugin) + USignificanceManager 통합. [[concepts/Asset-Optimization-Policy]] §1 의 핵심.

## 2. Key claims

- 5 중 누적 (50+ NPC 환경 표준):
  1. **URO**: 거리/Significance 기반 Tick 주기 분할 (1 → 2 → 4 → 8 frame). FAnimUpdateRateParameters override.
  2. **EVisibilityBasedAnimTickOption** 5 종: 화면 밖 Tick 정책. 표준 = OnlyTickPoseWhenRendered.
  3. **AnimSharing**: UAnimSharingInstance — 같은 BP 의 다수 NPC 가 한 번의 evaluation 결과 공유.
  4. **AnimationBudgetAllocator** (Plugin): USkeletalMeshComponentBudgeted 자동 등록 → 프레임 budget 안에서 우선순위 큰 캐릭터부터.
  5. **USignificanceManager**: 거리 + 시야 기반 중요도 → 위 4 개 동시 토글.
- [[concepts/Bone-LOD]] (USkeletalMeshLODSettings BonesToRemove) — Mesh 자산 측면.
- 의사결정 트리: 거리 가까움 → 풀 Tick. 거리 중간 → URO. 거리 멀음 → URO + Visibility Off. 매우 멀음 → Significance Cull.
- AI vs Player 매트릭스: AI 는 ServerAuthoritative + cosmetic 풀, Player 는 Local + 높은 우선순위.

## 3. Open questions

- [ ] 5 중 누적의 ms 절감 비교 (각 단계별)
- [ ] AnimSharing 의 BP 작성 표준
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 lineshift-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **lineshift-only**. 5.5↔5.7 raw diff 가 라인 번호 shift 만 — 본문 의미 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
