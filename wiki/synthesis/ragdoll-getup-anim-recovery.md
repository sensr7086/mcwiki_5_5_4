---
type: synthesis
title: "Ragdoll → 일어서기 (GetUp) 표준 시퀀스 — AnimMontage + Inertialization + URO bucket 1 + RootMotion 결합"
slug: ragdoll-getup-anim-recovery
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/mc-soft-skeletalmesh-ragdoll]]"
  - "[[sources/ue-animation-rootmotion]]"
  - "[[sources/ue-animation-optimization]]"
  - "[[sources/ue-animation-skill]]"
  - "[[sources/ue-components-physicscomponents]]"
  - "[[sources/ue-components-charactermovementdeep]]"
entities:
  - "[[entities/USkeletalMeshComponent]]"
  - "[[entities/UAnimMontage]]"
  - "[[entities/UAnimInstance]]"
  - "[[entities/ACharacter]]"
  - "[[entities/UCharacterMovementComponent]]"
concepts:
  - "[[concepts/Inertialization]]"
  - "[[concepts/RootMotion]]"
  - "[[concepts/URO]]"
  - "[[concepts/EVisibilityBasedAnimTickOption]]"
  - "[[concepts/MC-Asset-Validation-Policy]]"
status: living
tags: [synthesis, ragdoll, animation, inertialization, getup, rootmotion]
---

# Ragdoll → 일어서기 (GetUp) 표준 시퀀스

## 1. Thesis

캐릭터가 ragdoll 로 쓰러진 뒤 *AnimMontage 로 자연스럽게 일어서는 시퀀스* 는 4 단계의 정확한 순서 + Inertialization + URO bucket 강제로 구현된다 — **(1) ragdoll 정지 → (2) 마지막 본 자세 캡처 (캐릭터 누운 방향 결정) → (3) Owner Capsule 을 누운 위치로 이동 + Mesh snap-back → (4) GetUp Montage 재생 (Pelvis 에서 ref-pose 로 [[concepts/Inertialization]] 블렌드)**. RootMotion 활성 시 URO bucket 1 (매프레임 Tick) 강제 + 부분 ragdoll 의 AnimClass *유지* 분기 ([[sources/mc-soft-skeletalmesh-ragdoll]] §3.2) 와 다르게 풀-바디는 AnimClass *복원* 후 Montage. 본 synthesis 는 [[synthesis/mc-character-hit-reaction-pipeline]] 의 Cleanup §2.3 을 *대체* — `DisableRagdoll() + SnapMeshToOwnerCapsule()` 만으론 본이 캡슐 *안* 으로 워프되는 어색함이 남기 때문.

## 2. 4 단 매트릭스

| 단계 | 호출 / 상태 | 정책 |
| -- | -- | -- |
| 1. Ragdoll 정지 | `SetAllBodiesSimulatePhysics(false)` 한 *직후 본 위치 캐시* | [[sources/mc-soft-skeletalmesh-ragdoll]] §3.3 |
| 2. 누운 방향 판정 | `Pelvis` 본의 World Forward · Up 벡터 → 누운 자세 (앞 / 뒤 / 옆) 결정 | 분기 Montage 선택 — `GetUp_FromBack` / `GetUp_FromFront` |
| 3. Capsule + Mesh snap | Owner Capsule 을 Pelvis 의 *지면 투영 위치* 로 워프 + `SnapMeshToOwnerCapsule()` | [[sources/mc-soft-skeletalmesh-ragdoll]] §SnapMeshToOwnerCapsule |
| 4. AnimClass 복원 + Montage | `SetAnimInstanceClass(CachedAnimClass)` → 1 frame 대기 → `PlayMontage(GetUpMontage)` | [[concepts/Inertialization]] 블렌드 — Montage 의 Inertial Blend Time 0.2~0.5s |

## 3. 시나리오

**시나리오 A — 일반 KO 후 일어서기**

```cpp
void AMyChar::OnDeathRecover()  // 사망이 아닌 KO 시
{
    USkeletalMeshComponent* Mesh = GetMesh();

    // 1. Ragdoll 정지 직전 — 본 위치 캐시
    const FTransform PelvisW = Mesh->GetSocketTransform(TEXT("pelvis"), RTS_World);

    // 2. 누운 방향 — Pelvis Up 의 Z 부호로 앞/뒤 분기
    const FVector PelvisUp = PelvisW.GetUnitAxis(EAxis::Z);
    UAnimMontage* GetUpMontage = (PelvisUp.Z > 0.f) ? GetUp_FromBack : GetUp_FromFront;

    // 3. Disable Ragdoll + Capsule snap (지면 투영)
    Cast<UMCSoftSkeletalMeshComponent>(Mesh)->DisableRagdoll();
    FVector GroundLoc = PelvisW.GetLocation();
    GroundLoc.Z = GetActorLocation().Z;  // 캡슐 Z 유지 (지면)
    SetActorLocation(GroundLoc, /*bSweep=*/false);
    Cast<UMCSoftSkeletalMeshComponent>(Mesh)->SnapMeshToOwnerCapsule();

    // 4. AnimClass 복원은 DisableRagdoll 안에서 자동 (bRestoreAnimClassOnDisable=true)
    //    1 frame 대기 후 Montage — AnimInstance 가 새로 생성되는 시간 필요
    GetWorld()->GetTimerManager().SetTimerForNextTick([this, GetUpMontage]() {
        if (UAnimInstance* AI = GetMesh()->GetAnimInstance()) {
            AI->Montage_Play(GetUpMontage, 1.f, EMontagePlayReturnType::MontageLength,
                             /*InTimeToStartMontageAt=*/0.f, /*bStopAllMontages=*/true);
        }
    });
}
```

**시나리오 B — RootMotion + URO 호환**

GetUp Montage 가 RootMotion 으로 캐릭터를 일으킬 때, [[synthesis/character-many-npc-5-fold-optimization]] §4 의 함정 #1 — *URO 가 4프레임 skip 시 RootMotion 누락* 발생. 강제로 매프레임 Tick:

```cpp
// Montage 시작 직전에 URO bucket 강제
SkelMesh->bEnableUpdateRateOptimizations = true;
SkelMesh->AnimUpdateRateParams->BaseNonRenderedUpdateRate = 1;
// Montage 종료 시 원복 (NotifyEnd 콜백)
```

또는 `AnimNotify_GetUpStart` / `AnimNotify_GetUpEnd` 본 안에 토글 — Montage 자체 안에서 자동.

**시나리오 C — Inertialization 블렌드**

ragdoll 마지막 본 자세 → ref-pose 로 *cubic Hermite* 블렌드. Montage 의 BlendIn 옵션:

```
BlendIn:
  BlendOption: Inertialization (0.3s) — 5.x 기본
  BlendInTime: 0.3
```

Inertialization 은 *현재 Pose 를 0 으로 evaluate 하지 않고 derivative 만 캡처해 자연스럽게 ref-pose 로 수렴* — ragdoll 의 임의 자세에서 Montage 첫 프레임 ref-pose 로의 popping 없는 전환. [[concepts/Inertialization]] 의 핵심 사용처.

## 4. 함정 / 열린 질문

- [ ] **Capsule 워프 시 충돌** — 누운 자세에서 Capsule 이 벽 *안* 에 있을 수 있음 ([[concepts/Possession]] 의 Spawn 충돌 같은 케이스). `SetActorLocation(..., bSweep=true)` 로 안전 위치 검색 또는 `FindFloor` 헬퍼
- [ ] **AnimClass 복원 1 frame 지연** — `SetAnimInstanceClass` 직후 Montage 호출하면 새 AnimInstance 가 아직 Initialize 안 된 상태. `SetTimerForNextTick` 또는 `OnAnimInstanceInitialized` 콜백
- [ ] **RootMotion + Capsule 동기화** — RootMotion 이 캐릭터를 일으킬 때 캐릭터의 위치가 바뀜. CharacterMovement 의 `bAllowPhysicsRotationDuringAnimRootMotion` 설정 필요
- [ ] **URO bucket 1 의 비용** — 매프레임 Tick → 잠시 비용 폭발. Montage 종료 시 *반드시* 원복 (열린)
- [ ] **부분 ragdoll → 정자세 복귀** — `EnablePartialRagdoll` 후 AnimClass 유지된 상태에선 부분 본만 시뮬 정지하면 됨 — 이 시나리오는 Montage 불필요. 풀-바디 분기와 명확히 구분 필요
- [ ] **GetUp 중 추가 피격** — GetUp Montage 재생 중 다시 hit 받으면? Montage 중단 + Partial Ragdoll 재진입? (열린 — gameplay 결정)
- [ ] **AI / NPC 의 GetUp** — Player Controller 가 없으면 누가 트리거? `BehaviorTree Service` 가 `bIsGettingUp` 플래그 모니터링 + Decorator (열린, [[sources/ue-ai-skill]])
- [ ] **멀티플레이 GetUp 동기** — Server 만 ragdoll 시뮬 → Server 가 본 위치 결정 → 모든 Client 가 같은 GetUp Montage 재생 ([[synthesis/ragdoll-multiplayer-replication]] 와 결합)

## 5. 관련

### Sources

[[sources/mc-soft-skeletalmesh-ragdoll]] · [[sources/ue-animation-rootmotion]] · [[sources/ue-animation-optimization]] · [[sources/ue-animation-skill]] · [[sources/ue-components-physicscomponents]] · [[sources/ue-components-charactermovementdeep]]

### Entities

[[entities/USkeletalMeshComponent]] · [[entities/UAnimMontage]] · [[entities/UAnimInstance]] · [[entities/ACharacter]] · [[entities/UCharacterMovementComponent]]

### Concepts

[[concepts/Inertialization]] · [[concepts/RootMotion]] · [[concepts/URO]] · [[concepts/EVisibilityBasedAnimTickOption]] · [[concepts/MC-Asset-Validation-Policy]]

### Related synthesis

[[synthesis/mc-character-hit-reaction-pipeline]] (Cleanup §2.3 의 후속 단계) · [[synthesis/character-many-npc-5-fold-optimization]] (URO bucket 1 강제) · [[synthesis/ragdoll-multiplayer-replication]] (Server 가 본 자세 결정 → Multicast GetUp) · [[synthesis/ai-npc-ragdoll-coordination]] (AI/NPC 변형 — BehaviorTree Service 트리거)
