---
type: synthesis
title: "AI NPC Squad 협력 + BT Service Tick budget 최적화 — Squad GetUp + AnimNotify Cue race"
slug: ai-npc-squad-coordination-tick-budget
created: 2026-05-11
last_updated: 2026-05-11
sources:
  - "[[sources/ue-ai-skill]]"
  - "[[sources/ue-animation-animnotify]]"
  - "[[sources/ue-animation-optimization]]"
  - "[[sources/ue-significance-skill]]"
  - "[[sources/ue-gameframework-pawncharacter]]"
  - "[[sources/mc-soft-skeletalmesh-ragdoll]]"
entities:
  - "[[entities/AAIController]]"
  - "[[entities/UBehaviorTree]]"
  - "[[entities/UBlackboardComponent]]"
  - "[[entities/USignificanceManager]]"
  - "[[entities/UAnimNotify]]"
concepts:
  - "[[concepts/Tick-Group]]"
  - "[[concepts/EVisibilityBasedAnimTickOption]]"
  - "[[concepts/MC-Asset-Validation-Policy]]"
status: living
tags: [synthesis, ai, npc, squad, bt-service, tick-budget]
---

# AI NPC Squad 협력 + BT Service Tick budget 최적화

## 1. Thesis

[[synthesis/ai-npc-ragdoll-coordination]] 의 미해결 — *BT Service Tick 비용* / *Squad 협력 GetUp* / *AnimNotify Cue race* — 3 축 통합. 핵심 — **(1) BT Service 호출을 USignificanceManager bucket 별로 분산 (50 NPC × 매 0.5s = 100 Hz → bucket 4 분할 = 25 Hz × 4 phase) / (2) Squad GetUp 은 Blackboard "AllyDown" 키 + Service 가 인근 동료 모니터 → 가장 가까운 ally Move-To + GetUp 보조 Task / (3) AnimNotify Footstep/Cue 의 Server-only 발화 보장 (Multicast 또는 Local-only 결정 트리)**. 본 synthesis 는 3 축의 결정 트리 + 골격 + 함정.

## 2. 3 축 매트릭스

| 축 | 문제 | 해결 |
| -- | -- | -- |
| BT Service Tick 비용 | 50 NPC × Tick = 매 frame 50 Service 호출 | Significance bucket 4 분할 + Service Interval 분산 |
| Squad GetUp 협력 | NPC 1명이 KO 시 동료 NPC 가 자동으로 일으켜 줌 | "AllyDown" Blackboard + Service 가 인근 ally 후보 추적 + Move-To + GetUp 보조 Task |
| AnimNotify Cue race | Footstep 사운드 / VFX 가 클라마다 다르게 발화 | Server-only 발화 + Multicast vs Local 분기 결정 트리 |

## 3. BT Service Tick budget 분산

[[entities/USignificanceManager]] 의 bucket 별 Service Tick 주기 분할:

```cpp
class UBS_RagdollMonitor : public UBTService_BlackboardBase
{
    virtual void TickNode(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory, float Dt) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UBS_RagdollMonitor::Tick);
        Super::TickNode(OwnerComp, NodeMemory, Dt);

        // Significance bucket 별 분기 — vault: [[sources/ue-significance-skill]]
        AAIController* AIC = OwnerComp.GetAIOwner();
        if (USignificanceManager* SM = USignificanceManager::Get(AIC->GetWorld())) {
            const float Score = SM->GetSignificance(AIC->GetPawn());
            // High (Score >= 0.7) → Service Interval 0.1s (매 frame 가까이)
            // Med  (0.3 <= S < 0.7) → 0.5s
            // Low  (S < 0.3) → 2.0s (멀리 있는 적)
            const float TargetInterval = (Score >= 0.7f) ? 0.1f : (Score >= 0.3f) ? 0.5f : 2.0f;
            if (Interval != TargetInterval) {
                Interval = TargetInterval;   // BTService 의 RandomDeviation 도 적용
            }
        }
        // 실제 모니터링 (가벼움 — Blackboard 갱신만)
        UpdateRagdollAndAllyKeys(OwnerComp);
    }
};
```

**비용**: 50 NPC 평균 — High 10 (0.1s) + Med 20 (0.5s) + Low 20 (2.0s) = 100 + 40 + 10 = 150 calls/sec → naïve 5000 (100 NPC × 50Hz) 대비 30× 감소.

## 4. Squad 협력 GetUp

Service 가 *동료 KO 감지* + Task 가 *Move-To + GetUp 보조*:

```cpp
// Service — 인근 ally 의 ragdoll 상태 모니터
void UBS_AllyMonitor::TickNode(...) {
    AAIController* AIC = OwnerComp.GetAIOwner();
    TArray<AActor*> NearbyAllies;
    UGameplayStatics::GetAllActorsOfClassWithTag(AIC->GetWorld(), AMyChar::StaticClass(),
                                                  FName("Ally"), NearbyAllies);
    AActor* ClosestDownedAlly = nullptr;
    float ClosestDist = FLT_MAX;
    for (AActor* Ally : NearbyAllies) {
        if (auto* M = Cast<UMCSoftSkeletalMeshComponent>(Cast<ACharacter>(Ally)->GetMesh())) {
            if (M->IsRagdollActive()) {
                const float D = FVector::DistSquared(AIC->GetPawn()->GetActorLocation(), Ally->GetActorLocation());
                if (D < ClosestDist) { ClosestDist = D; ClosestDownedAlly = Ally; }
            }
        }
    }
    OwnerComp.GetBlackboardComponent()->SetValueAsObject(AllyKey.SelectedKeyName, ClosestDownedAlly);
}

// Task — Move-To + GetUp 보조 발화
class UBT_AssistDownedAlly : public UBTTaskNode {
    EBTNodeResult::Type ExecuteTask(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory) override {
        AAIController* AIC = OwnerComp.GetAIOwner();
        AActor* Ally = Cast<AActor>(OwnerComp.GetBlackboardComponent()->GetValueAsObject(AllyKey.SelectedKeyName));
        if (!Ally) return EBTNodeResult::Failed;
        // 1. Move-To (가까이)
        AIC->MoveToActor(Ally, 100.f);
        // 2. 도착 후 (BT 다음 Task) — Ally 의 GetUp Task 트리거
        if (auto* AllyMesh = Cast<UMCSoftSkeletalMeshComponent>(Cast<ACharacter>(Ally)->GetMesh())) {
            AllyMesh->DisableRagdoll();
            AllyMesh->SnapMeshToOwnerCapsule();
            // GetUp Montage 재생
        }
        return EBTNodeResult::Succeeded;
    }
};
```

## 5. AnimNotify Cue race 결정 트리

```
이 AnimNotify 의 Cue (Sound / VFX / Camera Shake) 는?
├── 모든 플레이어에게 동일하게 보여야 (보스 스킬 cue)
│   └── Server-only 발화 + Multicast — Server Montage_Play → CharacterMovement Compressed Movement 가 Notify 도 broadcast
├── Owning Client 만 (1st person 카메라 흔들림)
│   └── Local-only — bAuthorOnly=false, IsLocallyControlled() 검사
├── Cosmetic + 빈도 큼 (Footstep)
│   └── Local — *모든 클라가 각자* 발화 (Server 권한 없음, 자기 본 위치 기준)
└── 게임 로직 (Cue 가 Damage 적용 — 안티패턴)
    └── ❌ AnimNotify 가 아니라 GameplayAbility / GameplayEffect 로 처리
```

## 6. 함정 / 열린 질문

- [ ] **Service Interval 변경 시 BTService 의 *NextTickTime* 갱신** — 단순 `Interval = X` 만으로는 다음 Tick 까지 옛 Interval 적용. `OwnerComp.RequestExecution(...)` 또는 NextTickTime 직접 재설정
- [ ] **Squad GetUp 의 *Authority 검증*** — Server 가 인근 ally 검색 + Task. Client 측 BT 는 cosmetic. AllyMesh->DisableRagdoll() 은 Server 권한 필요 — 검증 의무
- [ ] **AnimNotify_Footstep 의 Sound Cue Pool** — 50 NPC 풋스텝 = 매 frame 100+ 사운드. [[synthesis/vfx-audio-soft-pool-significance]] 의 SoundCue Pool + Concurrency 그룹 결합
- [ ] **GetUp 중 추가 hit** — [[synthesis/ragdoll-getup-anim-recovery]] §A 에서 미해결로 남았던 부분. Service 가 *GetUp 진행 중 + 추가 hit* 감지 → Montage 중단 + Ragdoll 재진입 — idempotent
- [ ] **Significance bucket 변경 시 Service Interval *jitter*** — Significance score 가 0.69 ↔ 0.71 oscillate 시 bucket 매 frame 바뀜 → Interval flicker. Hysteresis (>=0.7 으로 olease, <0.6 으로 leave) 의무
- [ ] **AnimNotify_State 의 Begin/End race** — Begin 발화 후 NPC GC → End 안 호출. 명시적 cleanup hook
- [ ] **Squad 의 *순환 의존*** — A 가 B 를 일으키려는 중 B 가 *A 가 KO 된 것* 감지 → 양쪽 RagdollMonitor 가 서로 대기 (deadlock). 가장 가까운 ally 외에 *KO 시점 가장 먼저* 검사 추가 (열린)

## 7. 관련

### Sources

[[sources/ue-ai-skill]] · [[sources/ue-animation-animnotify]] · [[sources/ue-animation-optimization]] · [[sources/ue-significance-skill]] · [[sources/ue-gameframework-pawncharacter]] · [[sources/mc-soft-skeletalmesh-ragdoll]]

### Entities

[[entities/AAIController]] · [[entities/UBehaviorTree]] · [[entities/UBlackboardComponent]] · [[entities/USignificanceManager]] · [[entities/UAnimNotify]]

### Concepts

[[concepts/Tick-Group]] · [[concepts/EVisibilityBasedAnimTickOption]] · [[concepts/MC-Asset-Validation-Policy]]

### Related synthesis

[[synthesis/ai-npc-ragdoll-coordination]] (BT Service / Task 베이스) · [[synthesis/character-many-npc-5-fold-optimization]] (Significance bucket) · [[synthesis/ragdoll-getup-anim-recovery]] (GetUp 시퀀스 결합)
