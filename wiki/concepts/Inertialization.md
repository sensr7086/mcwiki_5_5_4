---
type: concept
title: "Inertialization (5.x, 0ms blend)"
aliases: [Inertialization, FAnimNode_Inertialization]
sources:
  - "[[sources/ue-animation-skill]]"
related_concepts:
  - "[[concepts/RootMotion]]"
tags: [ue, runtime, animation]
last_updated: 2026-05-09
---

# Inertialization (5.x — 0 ms blend)

## 1. 정의 (한 줄)

5.x 의 새 블렌드 표준 — 이전 모션의 *inertia* (속도 + 가속도) 를 보존한 채 새 모션으로 0 ms 전환. `FAnimNode_Inertialization` 노드가 AnimGraph 에서 처리.

## 2. 자세히

전통적 CrossFade (alpha 0→1 N 프레임): 두 모션을 동시에 evaluate → blend → 비용 2x + 어색한 transition.

Inertialization: 새 모션만 evaluate → 이전 inertia 를 별도 spring-damper 로 decay → 0 ms 즉시 전환 + 자연스러움.

```
이전 모션 (Walk)              Walk 끝 시점의 본 transform velocity 캡쳐
       │
       ▼ "Inertialize" 트리거
새 모션 (Jump)                Jump 시작 — 이전 velocity 를 spring-damper 로 decay 적용
       │
       ▼ N 프레임 후
새 모션만 (Jump)              decay 완료 — pure 새 모션
```

## 3. 변형 / 사례 / 응용

- **표준 사용**: 점프 → 착지, Idle → Run, 콤보 transition. Crossfade 대비 깔끔.
- **AnimGraph 통합**: Final Pose 직전에 `Inertialization` 노드 1 개 — Request 발화점에서 트리거.
- **DurationInertialization**: decay 시간 (0.2 ~ 0.5 s 표준).
- **vs Sync Group**: Sync 는 두 모션의 *박자* 를 맞춤. Inertialization 은 *transition* 을 부드럽게.

## 4. 관련 entity

- [[entities/UAnimInstance]] · [[entities/FAnimNode-Base]]

## 5. 열린 질문

- [ ] Inertialization 의 본별 weight (전신 vs 상체만)
- [ ] Crossfade 와의 수치적 비교 (CPU / 시각적)
