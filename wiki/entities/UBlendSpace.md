---
type: entity
title: "UBlendSpace"
aliases: [UBlendSpace, BlendSpace, BlendSpace1D]
kind: model
sources:
  - "[[sources/ue-assetclasses-skill]]"
  - "[[sources/ue-animation-skill]]"
tags: [ue, asset, animation]
last_updated: 2026-05-09
---

# UBlendSpace

## 요약

[[entities/UObject]] 자손. **다차원 파라미터 → 모션 블렌드** 자산 — 966 lines. 1 axis (BlendSpace1D) 또는 2 axis. Sample 들이 axis 좌표에 배치 → 입력값으로 weighted blend. Locomotion (Speed × Direction) 의 표준.

## 관계

- 부모: [[entities/UObject]]
- 컨텐츠: [[entities/UAnimSequence]] 다수 (sample 위치별)
- 런타임 호스트: [[entities/UAnimInstance]] 의 AnimGraph (BlendSpace 노드)

## 핵심 주장

- Axis 1~2: BlendSpace1D = 1 axis (예: Speed), BlendSpace = 2 axis (예: Speed × Direction). 3 axis 이상은 별도 — 여러 BlendSpace 합성 또는 BlendSpace1DByCurve.
- Sample 좌표: 각 sample 이 axis 좌표 (예: Speed=300, Direction=0). 입력값에 따라 가까운 sample 들의 weighted blend.
- Interpolation: Linear / Cubic / EaseIn 등 — Editor 에서 결정.
- 표준 사용: Character 의 Idle / Walk / Run / Strafe (전후좌우) 가 Speed × Direction 2 axis BlendSpace 한 개로 처리.
- Sync Group 통합: 여러 BlendSpace / Sequence 가 같은 박자로 — [[entities/UAnimInstance]] 의 Sync Group.

## 열린 질문

- [ ] BlendSpace 의 sample 정렬과 wrapping (Direction 의 -180~180)
- [ ] AnimGraph 안 BlendSpace 노드의 Update vs Evaluate 분리
