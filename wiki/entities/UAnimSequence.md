---
type: entity
title: "UAnimSequence"
aliases: [UAnimSequence, AnimSequence]
kind: model
sources:
  - "[[sources/ue-assetclasses-skill]]"
  - "[[sources/ue-animation-skill]]"
tags: [ue, asset, animation]
last_updated: 2026-05-09
---

# UAnimSequence

## 요약

[[entities/UObject]] 자손 (자산 클래스). 단일 모션 클립 — 1,001 lines. Pose 키 (per-bone) + Curve (float / vector / transform) + Notify (event 트리거) + Compression (ACL 5.x). USkeleton 단위로 호환.

## 관계

- 부모: [[entities/UObject]]
- 협력 자산: USkeleton (참조 Skeleton), [[entities/USkeletalMesh]] (간접)
- 페어 컨테이너: [[entities/UAnimMontage]] (구간), [[entities/UBlendSpace]] (블렌드), AnimSequencer (Sequencer)
- 런타임 평가: [[entities/UAnimInstance]] 의 AnimGraph

## 핵심 주장

- Pose 데이터: per-bone Transform per frame. Compression 으로 메모리 ↓ (ACL — Animation Compression Library, 5.x 표준).
- Curve: float / vector / transform 타입. Animation Layer 의 알파 / 오프셋 / IK weight 등에 사용.
- Notify: 시퀀스 시간상의 한 점 (UAnimNotify) 또는 구간 (UAnimNotifyState) 트리거. → [[entities/UAnimNotify]]
- Compression Settings: ACL Default / High Fidelity / etc. Editor 에서 build 시 결정. WITH_EDITORONLY_DATA 의 raw 키와 Cooked 의 compressed data 분리.
- bEnableRootMotion: root motion 활성 시 root bone 의 변환이 Character 이동 구동. [[concepts/RootMotion]]
- AdditiveAnimType: None / Mesh Space / Local Space — additive blend 시 사용.

## 열린 질문

- [ ] ACL 5.x compression 의 메모리 절감 비율 — 기존 비교
- [ ] AnimSequence 의 Cooked 빌드 메모리 — 자주 사용 시 PreloadPrimaryAssets
