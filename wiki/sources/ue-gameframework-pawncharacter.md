---
type: source
title: "UE GameFramework — PawnCharacter sub-skill"
slug: ue-gameframework-pawncharacter
source_path: raw/ue-wiki-llm/skills/GameFramework/references/PawnCharacter.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
related_entities:
  - "[[entities/APawn]]"
  - "[[entities/ACharacter]]"
  - "[[entities/UCharacterMovementComponent]]"
related_concepts:
  - "[[concepts/RootMotion]]"
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/URO]]"
tags: [ue, runtime, gameframework, character]
---

# UE GameFramework — PawnCharacter sub-skill

> Source: [[raw/ue-wiki-llm/skills/GameFramework/references/PawnCharacter.md]]
> Parent: [[sources/ue-gameframework-skill]]

## 1. Summary

[[entities/APawn]] (598) + [[entities/ACharacter]] (1,095) 합본. Jump / Crouch / Landing / [[concepts/RootMotion]] + 5 종 Movement 모드. **§6 다수 NPC 환경 최적화 10 종**.

## 2. Deep references

- [[sources/ue-gameframework-characteroptimization]] — 최적화 10 종 + AI vs Player 9 매트릭스 + 결정 트리

## 3. Key claims

- APawn: Controller 가 Possess 가능. SetupPlayerInputComponent (Possess 시 자동).
- ACharacter: Capsule + SkeletalMesh + [[entities/UCharacterMovementComponent]] 강제 페어. Jump / Crouch / Launch / OnLanded.
- bIsCrouched 복제 — Capsule HalfHeight + MaxWalkSpeedCrouched.
- 최적화 10 종: PrimaryActorTick 비활성 / Component Tick 분산 / [[concepts/URO]] / EVisibilityBasedAnimTickOption / Bone LOD / Significance / AnimationBudgetAllocator / AnimSharing / Network / AI vs Player.
- AI vs Player 분기: AAIController = ServerAuthoritative + 비-cosmetic, APlayerController = Local + cosmetic 풀.
- Multiplayer: Server Authoritative + Client Prediction (FSavedMove_Character).

## 4. Open questions

- [ ] PhysCustom override 패턴 (grappling / wall run)
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 pass-minor-numeric** (자동 분석)

raw 5.5.4 vs 5.7.4 diff: 시그니처 0 / 추가 0 / 제거 0 / 수치 4 — 표면 변경만, 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/GameFramework/references/PawnCharacter.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/GameFramework/references/PawnCharacter.md`
