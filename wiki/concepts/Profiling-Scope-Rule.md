---
type: concept
title: "Profiling Scope 의무 정책"
aliases: [TRACE_CPUPROFILER_EVENT_SCOPE, Profiling Scope]
sources:
  - "[[sources/ue-components-skill]]"
  - "[[sources/ue-animation-skill]]"
related_concepts:
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, profiling, policy]
last_updated: 2026-05-09
---

# Profiling Scope 의무 정책

## 1. 정의 (한 줄)

매 프레임 호출되는 모든 함수 (Tick / Update / Notify / OnRep_* / 람다 / TimerManager / UFunction 콜백) 의 첫 줄에 `TRACE_CPUPROFILER_EVENT_SCOPE` 매크로 의무 — Insights / stat unit 에서 정확한 캡처 보장.

## 2. 자세히

```cpp
void UMyComp::TickComponent(float Dt, ...)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyComp::TickComponent);
    // ... 본문
}

void UMyAnimInstance::NativeUpdateAnimation(float DeltaSeconds)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyAnimInstance::NativeUpdateAnimation);
    // ...
}

UMyComp::UMyComp()
{
    GetWorld()->GetTimerManager().SetTimer(Handle, FTimerDelegate::CreateLambda([this]()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyComp::TimerLambda_Foo);
        // ...
    }), 1.0f, true);
}
```

## 3. 변형 / 사례 / 응용

대상 함수 카탈로그 (raw/ue-wiki-llm/references/07_ProfilingScopeRule.md):
- Tick* / TickComponent / TickActor
- NativeUpdateAnimation / NativeThreadSafeUpdateAnimation / FAnimNode_*::Update_AnyThread / Evaluate_AnyThread
- UAnimNotify::Notify / NotifyBegin / NotifyEnd
- OnRep_* (Replication callback)
- TimerManager 람다
- UFUNCTION 콜백 (Server/Client/NetMulticast RPC 받는 쪽 포함)
- Montage_* 콜백 (OnMontageBlendingOut 등)

## 4. 관련 entity

- [[entities/UActorComponent]]
- [[entities/UAnimInstance]]
- [[entities/FAnimNode-Base]]

## 5. 열린 질문

- [ ] TRACE_CPUPROFILER_EVENT_SCOPE_TEXT (동적 이름) vs SCOPE (정적 이름) 의 비용 차이
- [ ] Insights vs stat unit 의 적합 시나리오
