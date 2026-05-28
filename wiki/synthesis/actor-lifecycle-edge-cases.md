---
type: synthesis
title: "Actor 라이프사이클 엣지 케이스 — OnRep_* race vs BeginPlay + PreInitializeComponents 사용처 + idempotent 가드"
slug: actor-lifecycle-edge-cases
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/ue-gameframework-actor]]"
  - "[[sources/ue-components-actorcomponent]]"
  - "[[sources/ue-networking-skill]]"
  - "[[sources/mc-asset-validation-policy]]"
  - "[[sources/ue-coreuobject-uobject]]"
entities:
  - "[[entities/AActor]]"
  - "[[entities/UActorComponent]]"
  - "[[entities/UNetDriver]]"
  - "[[entities/APawn]]"
concepts:
  - "[[concepts/Actor-Lifecycle]]"
  - "[[concepts/Component-Lifecycle]]"
  - "[[concepts/Replication]]"
  - "[[concepts/MC-Asset-Validation-Policy]]"
status: living
tags: [synthesis, lifecycle, replication, race-condition, edge-case]
---

# Actor 라이프사이클 엣지 케이스

## 1. Thesis

[[synthesis/component-vs-actor-lifecycle-table]] 의 11 단 매트릭스로는 닿지 않는 *3 가지 race / 미세 시점 케이스* — **(1) Client 의 `OnRep_*` 가 `BeginPlay` 보다 *먼저* 도착할 수 있음 (Replication 도착 vs World Tick 시작 race) / (2) `PreInitializeComponents` 의 거의 안 알려진 사용처 (Subsystem 의존 캐싱 / Component 등록 직전 셋업) / (3) idempotent 가드 패턴 — 같은 이벤트가 여러 번 호출 가능한 경우 (Late Join + Replication 재전송 + AnimNotify race)**. 본 synthesis 는 각 case 의 *디버깅 어려운 race* 를 표면화 + [[concepts/MC-Asset-Validation-Policy]] 의 매크로로 가시화.

## 2. (1) `OnRep_*` race vs `BeginPlay`

기본 가정 — `BeginPlay` 후에 `OnRep_*` 호출. **틀림**. Client 의 패킷 도착 순서는 비결정적.

```
Server: SpawnActor → BeginPlay → SetReplicatedHP(50) → ...
                                        ↓ Replicate
Client: 패킷 도착 → 1. Actor channel open
                  → 2. Property delta (HP=50)
                  → 3. OnRep_HP    ← 이 시점에 BeginPlay 호출됐을지 미정
                  → 4. (다음 frame) BeginPlay
```

가시화:
```cpp
void AMyChar::BeginPlay()
{
    Super::BeginPlay();
    UE_LOG(LogTemp, Warning, TEXT("BeginPlay HP=%d"), HP);
}
void AMyChar::OnRep_HP()
{
    UE_LOG(LogTemp, Warning, TEXT("OnRep_HP HP=%d, HasBegunPlay=%d"), HP, HasActorBegunPlay());
    // → 종종 HasBegunPlay=false 출력
}
```

**해결 패턴**:

```cpp
void AMyChar::OnRep_HP()
{
    if (!HasActorBegunPlay()) {
        // 도착했지만 아직 BeginPlay 안 됨 — 큐에 보류
        return;  // BeginPlay 가 도착 후 다시 호출하지 않으므로...
    }
    UpdateHPUI();
}

void AMyChar::BeginPlay()
{
    Super::BeginPlay();
    // BeginPlay 시점에 *이미 도착한* HP 값으로 한번 처리
    UpdateHPUI();
}
```

**더 안전한 표준** — `PostNetReceive` override + `BeginPlay` 둘 다에서 idempotent UpdateHPUI 호출.

## 3. (2) `PreInitializeComponents` 사용처

11 단 매트릭스의 4 단계 *직전* — Components 가 등록되기 *전*. Subsystem / Engine API 는 사용 가능, 하지만 World 안 다른 Actor 는 아직 BeginPlay 전.

**합법 사용**:

```cpp
void AMyChar::PreInitializeComponents()
{
    Super::PreInitializeComponents();

    // 1. Subsystem 캐싱 (BeginPlay 보다 먼저 — Component 의 InitializeComponent 가 의존)
    if (UGameInstance* GI = GetGameInstance()) {
        ConfigCache = GI->GetSubsystem<UMCConfigManager>();
    }

    // 2. Component property override 마지막 기회 (이후 InitializeComponent 가 사용)
    if (UCharacterMovementComponent* CMC = GetCharacterMovement()) {
        CMC->MaxWalkSpeed = ConfigCache ? ConfigCache->GetWalkSpeed() : 600.f;
    }
}
```

**금기**:
- 다른 Actor 참조 (아직 BeginPlay 전 — 컴포넌트 미등록 → 본 위치 / 콜리전 정확 X)
- 비동기 자산 로드 (콜백이 BeginPlay 전 도착하면 Component 가 받을 준비 X)
- Replication 가정 (Authority 만 호출됨 — Client 는 `PreInitializeComponents` 안 호출됨, 11단 매트릭스 보강 필요)

## 4. (3) Idempotent 가드 패턴

여러 번 호출 가능한 이벤트:
- `BeginPlay` — Actor pool 의 `Activate(true, /*bReset=*/true)` 시 두 번째 호출 케이스 (UE 자체는 안 그렇지만 Pool 패턴이 그렇게 만듦)
- `OnRep_*` — 패킷 재전송 / Reconnect 시
- AnimNotify — 같은 frame 안 여러 번 발화
- GameplayCue Execute — Server replicate + Local Predict 둘 다

**표준 가드 패턴**:

```cpp
void AMyChar::HandleDeath()
{
    if (bIsDead) {
        UE_LOG(LogMCAsset, Verbose, TEXT("HandleDeath idempotent skip"));
        return;
    }
    bIsDead = true;
    // 실제 처리 1회만
    PlayDeathMontage();
    EnableRagdoll();
    DropLoot();
}

// OnRep_bIsDead 도 같은 함수 호출 — Server / Client 동시
void AMyChar::OnRep_bIsDead()
{
    if (bIsDead) HandleDeath();
}
```

[[concepts/MC-Asset-Validation-Policy]] 의 `MC_LOGRET_IF_FALSE` 도 idempotent 가드 사례 — 두 번째 호출은 Verbose 로그 + return.

## 5. 매트릭스 — 시점별 안전 작업

| 시점 | Actor 자체 | Components | 다른 Actor | Subsystem | Replication | 비동기 자산 |
| -- | -- | -- | -- | -- | -- | -- |
| Constructor | 일부 (UPROPERTY 디폴트) | `CreateDefaultSubobject` | ✗ | ✗ | ✗ | ✗ |
| `PostInitProperties` | ✓ (UPROPERTY 검증) | ✗ (아직 등록 X) | ✗ | ✗ | ✗ | ✗ |
| `PreInitializeComponents` | ✓ | property override | ✗ | ✓ | ✗ (Authority 만) | ✗ |
| `PostInitializeComponents` | ✓ | ✓ (Component 간 참조) | △ (BeginPlay 전) | ✓ | ✗ | ✗ |
| `BeginPlay` | ✓ | ✓ | ✓ | ✓ | ✓ (Server) | ✓ (시작 가능) |
| `OnRep_*` | ✓ | ✓ (BeginPlay 후라면) | ✓ (도착했다면) | ✓ | ✓ | △ (BeginPlay race 검사) |
| `Tick` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `EndPlay` | ✓ | △ (Super LAST 까지만) | △ | △ (Deinit 진행 중) | ✗ | ✗ (취소만) |

## 6. 함정 / 열린 질문

- [ ] **`OnRep_*` 가 BeginPlay 전 도착** — `HasActorBegunPlay()` 검사 + 큐 보류 또는 idempotent UpdateUI 패턴
- [ ] **`PreInitializeComponents` 는 Server only** — Client 는 호출 안 됨. Client 측 Component override 가 필요하면 `PostNetInit` 또는 `OnRep_*` (열린)
- [ ] **`PostNetReceive`** — 정확히 모든 Property replicate 도착 후 호출. `OnRep_*` 보다 *늦음*. Aggregate 처리 (모든 Property 도착 후 한번에) 에 유용
- [ ] **AActor pool 패턴** — `SetActorEnableCollision(false) + SetActorHiddenInGame(true) + SetTickEnabled(false)` 로 *deactivate*, 재사용 시 *activate*. `BeginPlay/EndPlay` 안 호출되므로 별도 `Reset()` 함수 필요
- [ ] **`OnPossess` 시점** — Pawn 의 `BeginPlay` 후 호출. Possess 가 BeginPlay 전에 일어나면 (편집기 setting), `OnPossess` 안에서 `HasActorBegunPlay()` 검사 ([[concepts/Possession]])
- [ ] **`SetActorTickEnabled(false)` 인 Actor 의 `Tick`** — 호출 안 됨. 그러나 Component 별 Tick 은 별도. `PrimaryComponentTick.bCanEverTick=false` 의무 (열린)
- [ ] **`AAIController::OnPossess` vs `Pawn::PossessedBy`** — 양쪽에서 Init 가능. 모두 idempotent 의무 (열린)
- [ ] **`UWorld::Tick` 순서** — TG_PrePhysics → TG_DuringPhysics → TG_PostPhysics → TG_PostUpdateWork. Tick group 별 의존 — 같은 frame 안 명확한 순서 보장 ([[concepts/Tick-Group]])

## 7. 관련

### Sources

[[sources/ue-gameframework-actor]] · [[sources/ue-components-actorcomponent]] · [[sources/ue-networking-skill]] · [[sources/mc-asset-validation-policy]] · [[sources/ue-coreuobject-uobject]]

### Entities

[[entities/AActor]] · [[entities/UActorComponent]] · [[entities/UNetDriver]] · [[entities/APawn]]

### Concepts

[[concepts/Actor-Lifecycle]] · [[concepts/Component-Lifecycle]] · [[concepts/Replication]] · [[concepts/MC-Asset-Validation-Policy]]

### Related synthesis

[[synthesis/component-vs-actor-lifecycle-table]] (11단 베이스) · [[synthesis/server-vs-client-rpc-decision-tree]] (OnRep_* 시점) · [[synthesis/mc-validation-policy-rollout]] (idempotent 가드 매크로)
