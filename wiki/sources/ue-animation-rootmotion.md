---
type: source
title: "UE Animation — RootMotion sub-skill"
slug: ue-animation-rootmotion
source_path: raw/ue-wiki-llm/skills/Animation/references/RootMotion.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UCharacterMovementComponent]]"
related_concepts:
  - "[[concepts/RootMotion]]"
tags: [ue, runtime, animation, movement]
---

# UE Animation — RootMotion sub-skill

> Source: [[raw/ue-wiki-llm/skills/Animation/references/RootMotion.md]]
> Parent: [[sources/ue-animation-skill]]

## 1. Summary

[[concepts/RootMotion]] + IAnimRootMotionProvider (5.x) + FRootMotionSource 7 종 + [[entities/UCharacterMovementComponent]] 통합. AnimMontage RootMotion 모드 4 종 + bEnableRootMotionMontagesOnly + RootLock 모드 + 멀티플레이.

## 2. Key claims

- AnimMontage RootMotion 모드 4 종: NoRootMotionExtraction / IgnoreRootMotion / RootMotionFromMontagesOnly / RootMotionFromEverything.
- bEnableRootMotionMontagesOnly: ACharacter 의 페어 옵션 — Montage 만 RootMotion 적용.
- IAnimRootMotionProvider (5.x): 더 일반화된 인터페이스 — Mesh-space / Component-space 변환.
- FRootMotionSource 7 종: ConstantForce / RadialForce / MoveToActorForce / MoveToForce / JumpForce / Custom / etc.
- CMC->ApplyRootMotionSource(Source) — 명시적 추가 (어빌리티 시스템 / GAS 통합).
- RootLock 모드: 본 root 가 모션의 일부 잠금 (예: 처형 모션의 시작점 고정).
- Multiplayer: Server Authoritative — RootMotion 도 동일 동기 (Client Prediction 의 ServerMove).
- 함정: bEnableRootMotion 활성 모션이 BlendSpace 에 들어가면 root motion 합성 → 의도와 다른 이동.

## 3. Open questions

- [ ] BlendSpace + RootMotion 함정 카탈로그
- [ ] Custom FRootMotionSource 작성 패턴
