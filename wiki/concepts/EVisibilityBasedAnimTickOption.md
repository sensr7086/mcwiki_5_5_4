---
type: concept
title: "EVisibilityBasedAnimTickOption (5종)"
aliases: [VisibilityBasedAnimTickOption, OnlyTickPoseWhenRendered]
sources:
  - "[[sources/ue-animation-skill]]"
related_concepts:
  - "[[concepts/URO]]"
  - "[[concepts/Asset-Optimization-Policy]]"
tags: [ue, runtime, animation, optimization]
last_updated: 2026-05-09
---

# EVisibilityBasedAnimTickOption

## 1. 정의 (한 줄)

[[entities/USkeletalMeshComponent]] 가 화면 밖일 때 Animation Tick 을 어떻게 조정할지의 5 enum — AlwaysTickPoseAndRefreshBones / AlwaysTickPose / OnlyTickMontagesWhenNotRendered / OnlyTickPoseWhenRendered / OnlyTickMontagesAndRefreshBonesWhenPlayingMontages.

## 2. 자세히

| 옵션 | 화면 안 | 화면 밖 | 사용처 |
| -- | -- | -- | -- |
| AlwaysTickPoseAndRefreshBones | 모두 | 모두 | 화면 밖에서도 본 데이터 필요 (Trail / 그림자) |
| AlwaysTickPose | Pose Tick | Pose Tick (본 갱신 X) | 시각만 보존, 본 위치 부정확 OK |
| OnlyTickMontagesWhenNotRendered | 모두 | Montage 만 | 화면 밖에서 Montage 진행 보존 |
| OnlyTickPoseWhenRendered | 모두 | Tick X | 표준 — 화면 밖 = 비활성 |
| OnlyTickMontagesAndRefreshBonesWhenPlayingMontages | 모두 | Montage 진행 시만 본 갱신 | 5.x 신규 — 가장 정교한 균형 |

## 3. 변형 / 사례 / 응용

- **다수 NPC (50+) 표준**: OnlyTickPoseWhenRendered. 화면 밖 = 0 비용.
- **콤보/공격이 화면 밖에서 진행되는 게임**: OnlyTickMontagesWhenNotRendered.
- **그림자가 보이는 캐릭터**: AlwaysTickPoseAndRefreshBones (그림자가 본 위치 의존).
- **5중 최적화 누적**: 본 옵션 + [[concepts/URO]] + Significance + AnimSharing + Budget. [[concepts/Asset-Optimization-Policy]]

## 4. 관련 entity

- [[entities/USkeletalMeshComponent]]
- [[entities/UAnimInstance]]

## 5. 열린 질문

- [ ] 5.x OnlyTickMontagesAndRefreshBonesWhenPlayingMontages 의 정확한 동작
- [ ] 옵션별 ms 절감 비교 (다수 NPC 환경에서)
