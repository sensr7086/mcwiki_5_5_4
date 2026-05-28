---
type: concept
title: "Replication (DOREPLIFETIME / OnRep_)"
aliases: [Replication, DOREPLIFETIME, OnRep, Replicated]
sources:
  - "[[sources/ue-networking-skill]]"
related_concepts:
  - "[[concepts/PushModel]]"
  - "[[concepts/Authority-NetMode]]"
  - "[[concepts/RPC]]"
tags: [ue, networking, multiplayer]
last_updated: 2026-05-09
---

# Replication

## 1. 정의 (한 줄)

[[entities/AActor]] / [[entities/UActorComponent]] 의 Property 를 Server → Client 자동 동기화. UPROPERTY(Replicated) + DOREPLIFETIME + GetLifetimeReplicatedProps + 선택적 OnRep_ callback.

## 2. 자세히

표준 셋업:
```cpp
// Header
UPROPERTY(ReplicatedUsing=OnRep_Health)
float Health;

UFUNCTION()
void OnRep_Health();

// .cpp
void AMyActor::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AMyActor, Health);
    DOREPLIFETIME_CONDITION(AMyActor, Mana, COND_OwnerOnly);
}
```

조건 매크로 (DOREPLIFETIME_CONDITION): COND_OwnerOnly / COND_SkipOwner / COND_AutonomousOnly / COND_SimulatedOnly / COND_Custom.

## 3. 변형 / 사례 / 응용

- bReplicates = true 가 Actor 측 활성. Component 는 SetIsReplicatedByDefault(true) 또는 Owner 의 bReplicates 가 자동.
- OnRep_ callback: Client 만 호출 (Server 는 SetValue 시 직접 처리). Server 측 callback 시뮬은 별도 함수로.
- [[concepts/PushModel]] (5.x 권장): 변경 마크 명시 → Pull 모델 대비 CPU ↓.
- FastArraySerializer: TArray<FFastArrayItem> 변경분만 복제.
- NetUpdateFrequency / NetCullDistance / bAlwaysRelevant — 조절.

## 4. 관련 entity

- [[entities/AActor]] · [[entities/UActorComponent]] · [[entities/UNetDriver]] · [[entities/UNetConnection]]

## 5. 열린 질문

- [ ] FastArraySerializer 의 IsFastArray 함정
- [ ] Replication Graph 5.x 의 도입 결정
