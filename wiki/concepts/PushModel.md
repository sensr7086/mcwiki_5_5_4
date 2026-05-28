---
type: concept
title: "Push Model Replication (5.x)"
aliases: [PushModel, MARK_PROPERTY_DIRTY_FROM_NAME, Push-based replication]
sources:
  - "[[sources/ue-networking-skill]]"
related_concepts:
  - "[[concepts/Replication]]"
tags: [ue, networking, multiplayer, optimization]
last_updated: 2026-05-09
---

# Push Model Replication

## 1. 정의 (한 줄)

5.x 권장 — Replicated Property 를 명시적으로 mark dirty (`MARK_PROPERTY_DIRTY_FROM_NAME`). Pull 모델 (매 frame 모든 property 비교) 대비 CPU ↓ 큼.

## 2. 자세히

기존 Pull 모델: 매 프레임 모든 Replicated Property 의 이전값과 비교 → 변경된 것만 전송. Property 많을수록 CPU 비용.

Push 모델: SetValue 시점에 명시적 dirty mark → 다음 frame 에 dirty 만 처리. Property 만 + 변경 시점에만 비용.

```cpp
// 등록 (DOREPLIFETIME_WITH_PARAMS_FAST)
DOREPLIFETIME_WITH_PARAMS_FAST(AMyActor, Health, FDoRepLifetimeParams{}.bIsPushBased = true);

// SetValue 시 mark
void AMyActor::SetHealth(float NewHealth)
{
    Health = NewHealth;
    MARK_PROPERTY_DIRTY_FROM_NAME(AMyActor, Health, this);
}
```

## 3. 변형 / 사례 / 응용

- 5.x 마이그레이션: 자주 변경되는 Property 부터 Push 로. 거의 안 변하는 Property 는 Pull 도 OK.
- FFastArraySerializer 와 통합: TArray<FFastArrayItem> 의 변경분 + Push.
- 함정: SetValue 후 MARK_PROPERTY_DIRTY 누락 = Client 가 변경 못 받음 (조용한 버그).
- ProjectSettings: bUsePushBasedReplication 으로 default 활성 가능.

## 4. 관련 entity

- [[entities/AActor]] · [[entities/UActorComponent]]

## 5. 열린 질문

- [ ] Push Model 의 자동 검증 (matrix 누락 발견)
- [ ] FastArraySerializer + Push 통합 패턴
