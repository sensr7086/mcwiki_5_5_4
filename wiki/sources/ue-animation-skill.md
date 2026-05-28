---
type: source
title: "UE 5.7.4 Animation Module — Main SKILL"
slug: ue-animation-skill
source_path: raw/ue-wiki-llm/skills/Animation/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UAnimInstance]]"
  - "[[entities/FAnimInstanceProxy]]"
  - "[[entities/FAnimNode-Base]]"
  - "[[entities/UAnimNotify]]"
  - "[[entities/UIKRigDefinition]]"
  - "[[entities/UIKRetargeter]]"
  - "[[entities/USkeletalMeshComponent]]"
related_concepts:
  - "[[concepts/URO]]"
  - "[[concepts/Inertialization]]"
  - "[[concepts/RootMotion]]"
  - "[[concepts/EVisibilityBasedAnimTickOption]]"
  - "[[concepts/Bone-LOD]]"
  - "[[concepts/Asset-Optimization-Policy]]"
tags: [ue, runtime, animation]
---

# UE 5.7.4 Animation Module — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/Animation/SKILL.md]]

## 1. Summary

SkeletalMesh 런타임 애니메이션 — 자산 → 호스트 (USkeletalMeshComponent) 연결 / 평가 / 동기 / 최적화. 매 프레임 다수 캐릭터 60 fps 유지의 핵심.

## 2. Sub-skills (7 — Phase 4C 완료)

- [[sources/ue-animation-animinstance]] ⭐ — UAnimInstance 라이프사이클 + FAnimInstanceProxy + Curve + Montage_*
- [[sources/ue-animation-animgraph]] — FAnimNode_Base 4 단계 _AnyThread + StateMachine + Layer 5.x
- [[sources/ue-animation-animnotify]] — UAnimNotify + UAnimNotifyState + Branch Point + Pool/AutoRelease
- [[sources/ue-animation-sync]] — FAnimSyncScope + Mirror + Inertialization (5.x 0ms 블렌드)
- [[sources/ue-animation-rootmotion]] — FRootMotionSource 7 종 + IAnimRootMotionProvider 5.x + CMC 페어
- [[sources/ue-animation-optimization]] ⭐⭐ — URO + Visibility + Significance + Sharing + Budget 5 중 통합
- [[sources/ue-animation-ik]] ⭐ — Legacy AnimNode IK 8 + 5.x IK Rig 7 Solvers + 5.x IK Retargeter 16 Ops

## 3. Open questions

- [ ] FAnimInstanceProxy 정확한 데이터 흐름 (게임 → 워커 → 게임)
- [ ] AnimBlueprint vs Native AnimInstance 결정 트리
- [ ] 5.x Inertialization vs Legacy CrossFade 비교
- [ ] IK Rig Solvers 7 종 사용처 카탈로그

## 4. Cross-link

### Cycle 5p reverse-link 보강 (med confidence missing)

- 🚨 [[concepts/Profiling-Scope-Rule]] — Animation 측 콜백 (NativeUpdateAnimation/NativeThreadSafeUpdateAnimation/AnimNotify_*/FAnimNode_Base::Update_AnyThread/Evaluate_AnyThread) 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` 의무. 7 sub-skill 모두에 적용 — 다수 NPC 60fps 유지 핫스팟 검출 베이스.
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 pass-minor-numeric** (자동 분석)

raw 5.5.4 vs 5.7.4 diff: 시그니처 0 / 추가 0 / 제거 0 / 수치 2 — 표면 변경만, 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/Animation/SKILL.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/Animation/SKILL.md`
