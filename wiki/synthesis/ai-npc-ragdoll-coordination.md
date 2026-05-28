---
type: synthesis
title: "AI/NPC Ragdoll 통합 — BehaviorTree Service GetUp 트리거 + Server-authoritative + 다중 피격 race"
slug: ai-npc-ragdoll-coordination
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/mc-soft-skeletalmesh-ragdoll]]"
  - "[[sources/ue-ai-skill]]"
  - "[[sources/ue-gameframework-controller]]"
  - "[[sources/ue-gameframework-pawncharacter]]"
  - "[[sources/ue-networking-skill]]"
entities:
  - "[[entities/AAIController]]"
  - "[[entities/UBehaviorTree]]"
  - "[[entities/UBlackboardComponent]]"
  - "[[entities/USkeletalMeshComponent]]"
  - "[[entities/ACharacter]]"
concepts:
  - "[[concepts/Possession]]"
  - "[[concepts/Authority-NetMode]]"
  - "[[concepts/MC-Asset-Validation-Policy]]"
status: living
tags: [synthesis, ai, npc, ragdoll, behaviortree, multiplayer]
---

# AI/NPC Ragdoll 통합

## 1. Thesis

[[synthesis/ragdoll-getup-anim-recovery]] 의 미해결 — *AI / NPC 의 GetUp 트리거 누가?* — 답은 **AAIController + BehaviorTree Service** 가 Blackboard 의 `bIsRagdoll` 를 모니터링하고 GetUp 가능 시점에 `EQS` (목적지 검증) → `MoveTo + GetUpMontage Task` 발화. Multiplayer 는 [[synthesis/ragdoll-multiplayer-replication]] 의 (B) Multicast trigger + Server-authoritative GetUp 결정 (Server 만 Blackboard mutate). 다중 피격 race — Server 가 hit 받을 때마다 *ragdoll 진입 / GetUp 취소* 를 idempotent 처리. 본 synthesis 는 BehaviorTree + Blackboard + Server 권한 + idempotent 의 4 축 통합.

## 2. 4 축 매트릭스

| 축 | 누가 | 무엇 |
| -- | -- | -- |
| BT Service | NPC AAIController | `bIsRagdoll` Blackboard key 매 N 초 갱신 (mesh 의 `IsRagdollActive()` 기반) |
| BT Decorator | Selector / Sequence | `bIsRagdoll == true` 면 GetUp 분기, false 면 일반 행동 |
| BT Task | Server only | `Task_GetUpFromRagdoll` — DisableRagdoll + SnapMesh + PlayMontage |
| Multicast | Server → Client | Ragdoll 진입/탈출 RPC ([[synthesis/ragdoll-multiplayer-replication]] B) |

## 3. BehaviorTree 노드 구조

```
[Selector]
├── [Decorator: bIsRagdoll == true]
│   └── [Sequence: GetUp]
│       ├── [Service: BS_MonitorRagdoll]  (매 0.5초 — Blackboard 갱신)
│       ├── [Task: Task_WaitRagdollSettle] (속도 < 임계, 안정화 대기)
│       ├── [Task: Task_GetUpFromRagdoll]  (DisableRagdoll + Capsule snap + Montage)
│       └── [Task: Wait 1.0s]              (Inertialization 블렌드 완료 대기)
└── [Sequence: 일반 행동]
    ├── [Task: FindTarget]
    ├── [Task: MoveToTarget]
    └── [Task: AttackTarget]
```

## 4. Service 골격

```cpp
UCLASS()
class UBS_MonitorRagdoll : public UBTService_BlackboardBase
{
    UPROPERTY(EditAnywhere) FBlackboardKeySelector RagdollKey;
    UPROPERTY(EditAnywhere) FBlackboardKeySelector SettledKey;

    virtual void TickNode(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory, float Dt) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UBS_MonitorRagdoll::Tick);
        Super::TickNode(OwnerComp, NodeMemory, Dt);
        AAIController* AIC = OwnerComp.GetAIOwner();
        MC_LOGRET_IF_NULL(AIC, "AIOwner null");
        ACharacter* Char = Cast<ACharacter>(AIC->GetPawn());
        MC_LOGRET_IF_NULL(Char, "Pawn null");
        UMCSoftSkeletalMeshComponent* Mesh = Cast<UMCSoftSkeletalMeshComponent>(Char->GetMesh());
        MC_LOGRET_IF_NULL(Mesh, "Mesh not MC type");

        UBlackboardComponent* BB = OwnerComp.GetBlackboardComponent();
        const bool bRag = Mesh->IsRagdollActive();
        BB->SetValueAsBool(RagdollKey.SelectedKeyName, bRag);

        // Ragdoll 안정화 — 본 위치 거의 안 변하면 GetUp 가능
        if (bRag) {
            const FVector PelvisVel = Mesh->GetPhysicsLinearVelocity(TEXT("pelvis"));
            BB->SetValueAsBool(SettledKey.SelectedKeyName, PelvisVel.SizeSquared() < 50.f * 50.f);
        } else {
            BB->SetValueAsBool(SettledKey.SelectedKeyName, false);
        }
    }
};
```

## 5. Task — GetUpFromRagdoll (Server only)

```cpp
class UBT_GetUpFromRagdoll : public UBTTaskNode
{
    virtual EBTNodeResult::Type ExecuteTask(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UBT_GetUpFromRagdoll::Execute);
        AAIController* AIC = OwnerComp.GetAIOwner();
        ACharacter* Char = Cast<ACharacter>(AIC->GetPawn());

        // [[synthesis/ragdoll-getup-anim-recovery]] 4 단 시퀀스
        // 1. Pelvis 위치 캐시 (누운 방향 결정)
        const FTransform PelvisW = Char->GetMesh()->GetSocketTransform(TEXT("pelvis"), RTS_World);
        const bool bFromBack = PelvisW.GetUnitAxis(EAxis::Z).Z > 0.f;
        UAnimMontage* Montage = bFromBack ? GetUpFromBackMontage : GetUpFromFrontMontage;

        // 2. Server 가 ragdoll 종료 + Capsule snap (Multicast 자동 — UMCSoft Mesh 안)
        if (auto* M = Cast<UMCSoftSkeletalMeshComponent>(Char->GetMesh())) {
            M->DisableRagdoll();
            M->SnapMeshToOwnerCapsule();
        }
        // 3. Montage 재생 (Authority 가 PlayMontage → CharacterMovement Replicate Montage 자동 broadcast)
        if (UAnimInstance* AI = Char->GetMesh()->GetAnimInstance()) {
            AI->Montage_Play(Montage);
        }
        return EBTNodeResult::Succeeded;
    }
};
```

## 6. 다중 피격 race 가드

NPC 가 GetUp 중 다시 hit:

```cpp
void UMCSoftSkeletalMeshComponent::OnHitReceived(...)
{
    // GetUp 중이면 Montage 중단 + Ragdoll 재진입
    if (UAnimInstance* AI = GetAnimInstance()) {
        if (AI->Montage_IsPlaying(GetUpMontage)) {
            AI->Montage_Stop(0.1f, GetUpMontage);   // 짧게 fade out
        }
    }
    // ... 기존 OnHitReceived 흐름 (idempotent)
}
```

BT Service 가 다음 Tick 에서 `bIsRagdoll = true` 다시 감지 → GetUp 재트리거. idempotent 보장.

## 7. 함정 / 열린 질문

- [ ] **BT Service Tick 비용** — 50 NPC × 0.5초 → 100 Tick/초. Service Tick 안 LOG/Cast 비용 작아야. `MC_LOGRET_*` 매크로 한번
- [ ] **Server-only Task 의 클라 동작** — Server 만 ragdoll mutate. Client 는 Multicast 받아 *시각만* 변경. Client BT 는 시뮬레이션 — 보통 NPC AI 는 Server only 라 무관
- [ ] **EQS 목적지 검증** — GetUp 후 이동 목적지가 막혀있으면? Get-up 후 EQS 로 nearby clear cell 검색
- [ ] **AnimMontage 의 Replication** — `Montage_Play` 가 Server 호출 → CharacterMovement Compressed Movement 가 Montage 정보 자동 broadcast. 단, Mesh 가 `ACharacter::Mesh` 가 아니면 manual replicate 필요
- [ ] **GetUp 중 사망** — GetUp Task 진행 중 HP 0. Server `Task_GetUpFromRagdoll` 가 추상화 — `OnHitDealtDeath` 가 즉시 abort + EnableFullRagdoll
- [ ] **AnimNotify_Footstep / Cue 누락** — GetUp Montage 의 Footstep AnimNotify 가 클라마다 다르게 발화 (Montage_Play 시점 race). Server 권한으로 통일 (열린)
- [ ] **Squad 협력 GetUp** — 동료 NPC 가 일으켜 줌 (Tag-team revival). 다중 BT 협력 + GAS 능력 — 별도 synthesis (열린)

## 8. 관련

### Sources

[[sources/mc-soft-skeletalmesh-ragdoll]] · [[sources/ue-ai-skill]] · [[sources/ue-gameframework-controller]] · [[sources/ue-gameframework-pawncharacter]] · [[sources/ue-networking-skill]]

### Entities

[[entities/AAIController]] · [[entities/UBehaviorTree]] · [[entities/UBlackboardComponent]] · [[entities/USkeletalMeshComponent]] · [[entities/ACharacter]]

### Concepts

[[concepts/Possession]] · [[concepts/Authority-NetMode]] · [[concepts/MC-Asset-Validation-Policy]]

### Related synthesis

[[synthesis/ragdoll-getup-anim-recovery]] (4 단 시퀀스 베이스) · [[synthesis/ragdoll-multiplayer-replication]] (Multicast 권한) · [[synthesis/character-many-npc-5-fold-optimization]] (NPC 50+ Service 비용) · [[synthesis/ai-npc-squad-coordination-tick-budget]] (Squad 협력 + Tick budget — 본 노트 미해결 해소)
