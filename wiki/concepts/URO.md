---
type: concept
title: "URO (UpdateRateOptimization)"
aliases: [URO, UpdateRateOptimization, FAnimUpdateRateParameters]
sources:
  - "[[sources/ue-animation-skill]]"
related_concepts:
  - "[[concepts/EVisibilityBasedAnimTickOption]]"
  - "[[concepts/Asset-Optimization-Policy]]"
  - "[[concepts/Bone-LOD]]"
tags: [ue, runtime, animation, optimization]
last_updated: 2026-05-09
---

# URO — Update Rate Optimization

## 1. 정의 (한 줄)

[[entities/USkeletalMeshComponent]] 의 Animation Tick 주기를 거리/Significance 기반으로 분할 — 매 프레임 → 2/4/8 프레임마다 → "보간 (interpolate) 만". `FAnimUpdateRateParameters` 가 보유.

## 2. 자세히

```
거리 가까움 / 화면 큼 / Significance 높음 ─▶ EvaluationRate = 1 (매 프레임 완전 평가)
거리 멀음 / 화면 작음 / Significance 낮음 ─▶ EvaluationRate = 2~8 (n 프레임마다)
                                          + Interpolation (사이 프레임은 보간만)
화면 밖 / 매우 멀리                       ─▶ Tick 자체 skip (EVisibilityBasedAnimTickOption)
```

- **EvaluationRate**: 1 ~ N. Pose 를 N 프레임마다 평가, 사이는 이전 결과 사용.
- **Interpolation**: 이전 → 다음 사이를 lerp — 시각적 jittering 회피.
- **bInterpolate**: Pose 보간 활성. 비활성 시 hold (덜 부드러움 / 더 가벼움).

## 3. 변형 / 사례 / 응용

- **5 중 최적화 누적**: URO + [[concepts/EVisibilityBasedAnimTickOption]] + Significance + AnimSharing + AnimationBudgetAllocator. → [[concepts/Asset-Optimization-Policy]]
- **표준 셋업**: Distance Cull + Significance 기반 자동 EvaluationRate 결정 (FAnimUpdateRateParameters 의 GetEvaluationRate override).
- **Bucketing**: 거리별 EvaluationRate bucket (1/2/4/8 등) 으로 NPC 그룹화 — 매 프레임 일정 비율의 NPC 만 update.

## 4. 관련 entity

- [[entities/USkeletalMeshComponent]]
- [[entities/UAnimInstance]]

## 5. 열린 질문

- [ ] FAnimUpdateRateParameters override 로 custom bucketing
- [ ] URO 와 [[concepts/EVisibilityBasedAnimTickOption]] 의 우선순위 충돌 해결
