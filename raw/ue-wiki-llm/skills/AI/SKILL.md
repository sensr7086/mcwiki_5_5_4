---
name: ue-ai
description: UE 5.7.4 AI 시스템 위키. AAIController + Behavior Tree(Task/Service/Decorator) + Blackboard + EQS(EnvironmentQuery) + Navigation(UNavigationSystemV1, RecastNavMesh, Crowd) + Perception(Sight/Hearing/Damage). 다수 NPC 5중 최적화 + Significance 통합.
---

# AI — UE 5.7.4 AI 시스템 / Behavior Tree / Navigation

> **카테고리** — Tier 1 (NPC / 적 AI / 군중)
> **대표 클래스** — `AAIController`, `UBehaviorTree`, `UBlackboardComponent`, `UBTTaskNode`, `UBTService`, `UBTDecorator`, `UEnvQuery`, `UNavigationSystemV1`, `UCrowdManager`, `UAIPerceptionComponent`
> **트리거 키워드** — Behavior Tree, Blackboard, EQS, Navigation, NavMesh, Crowd, Perception, AI Sense, RVO

본 sub-skill은 게임 AI의 4대 축(Controller / BT / Nav / Perception)을 정리. 다수 NPC 환경 최적화는 [`skills/Animation/Optimization`](../Animation/references/Optimization.md) + [`skills/Significance`](../Significance/SKILL.md) 페어.

---

## 1. AIController 표준

```cpp
UCLASS()
class AMyAIController : public AAIController
{
    GENERATED_BODY()
public:
    AMyAIController();
    virtual void OnPossess(APawn* P) override;
    virtual void OnUnPossess() override;

protected:
    UPROPERTY(EditDefaultsOnly, Category="AI")
    TObjectPtr<UBehaviorTree> DefaultBT;
};

void AMyAIController::OnPossess(APawn* P)
{
    Super::OnPossess(P);  // 04_OverrideIndex — Super FIRST
    if (DefaultBT && DefaultBT->BlackboardAsset)
    {
        UseBlackboard(DefaultBT->BlackboardAsset, BlackboardComponent);
        RunBehaviorTree(DefaultBT);
    }
}
```

> 🚨 `OnPossess` Super FIRST 의무 — Blackboard 초기화 누락 시 `RunBehaviorTree` NOP [grep-listed].

---

## 2. Behavior Tree — 4 노드 종류

| 종류 | 베이스 | 역할 | 평가 시점 |
|------|--------|------|----------|
| Composite | `UBTCompositeNode` | Sequence / Selector / Parallel / SimpleParallel | 자식 라우팅 |
| Task | `UBTTaskNode` | 실제 액션 — `ExecuteTask` 반환값 | 시작 시 |
| Decorator | `UBTDecorator` | 조건 — `CalculateRawConditionValue` | Observer 등록 시 매 Tick (조건부) |
| Service | `UBTService` | 주기 갱신 — `TickNode` | 자식 활성 동안 주기 |

### 2.1 Task 작성 표준

```cpp
UCLASS()
class UBTTask_FindRandomLocation : public UBTTask_BlackboardBase
{
    GENERATED_BODY()
public:
    virtual EBTNodeResult::Type ExecuteTask(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory) override;
};
```

반환값 — `Succeeded / Failed / InProgress / Aborted`. InProgress 시 `FinishLatentTask(OwnerComp, ...)`로 비동기 완료 통지.

### 2.2 Decorator Observer 함정

```cpp
UCLASS()
class UBTDecorator_HasTarget : public UBTDecorator_BlackboardBase
{
    GENERATED_BODY()
protected:
    virtual bool CalculateRawConditionValue(UBehaviorTreeComponent& OwnerComp, uint8* NodeMemory) const override;
};
```

> ⚠ Observer Aborts 설정 시 **매 Tick 평가** — 정밀하지만 비싸. `Self` (자기 자식만) vs `Both` (자식 + 형제) 구분.

---

## 3. Blackboard

```cpp
const UBlackboardComponent* BB = GetBlackboardComponent();
const FVector Loc = BB->GetValueAsVector("TargetLocation");
BB->SetValueAsObject("TargetActor", FoundEnemy);
```

| 키 타입 | API |
|---------|-----|
| Bool / Int / Float | `GetValueAs{Bool,Int,Float}` / `SetValueAs...` |
| Vector / Rotator | `GetValueAsVector` / `Rotator` |
| Object / Class | `GetValueAsObject` / `Class` |
| Name / String | 디버깅 용 |
| Enum | `GetValueAsEnum` |

> 🚨 키 이름 타이포 — 컴파일 안 잡힘. `FName` 상수 const로 보관 권장 [grep-listed].

---

## 4. EQS (EnvironmentQuery)

위치 탐색 — "가장 가까운 적 옆 + 시야 확보된 곳" 등.

```cpp
UEnvQueryInstanceBlueprintWrapper* EQS = UEnvQueryManager::RunEQSQuery(
    this, MyEQSAsset, this, EEnvQueryRunMode::SingleResult,
    UEnvQueryInstanceBlueprintWrapper::StaticClass());
EQS->GetOnQueryFinishedEvent().AddDynamic(this, &ThisClass::OnEQSDone);
```

> ⚠ 비동기 — 결과 콜백에서 처리 의무. 매 Tick 호출 금지 (`07_ProfilingScopeRule` + Service 주기 사용).

---

## 5. Navigation

### 5.1 핵심 API

```cpp
UNavigationSystemV1* Nav = UNavigationSystemV1::GetCurrent(GetWorld());
FVector Random;
Nav->GetRandomReachablePointInRadius(Origin, 1000.f, Random);
```

| API | 용도 |
|-----|------|
| `GetRandomReachablePointInRadius` | 패트롤 위치 |
| `ProjectPointToNavigation` | 위치를 NavMesh에 스냅 |
| `FindPathSync` / `FindPathAsync` | 경로 계산 |
| `GetPathLength` | 거리 검증 |

### 5.2 RecastNavMesh — 빌드 시점

- Editor — Build → Build Paths 또는 Auto Update
- Runtime — `bRuntimeGeneration = true` (오픈월드)
- 동적 장애물 — `UNavModifierComponent` / `UNavRelevantComponent`

### 5.3 Crowd / RVO

```cpp
GetCharacterMovement()->SetAvoidanceEnabled(true);  // RVO
// Or
UCrowdFollowingComponent를 PathFollowing 대체로 등록
```

> 🚨 다수 NPC 100+ 시 — Crowd ON + Significance OFF / LOD 누적 (`12_AssetOptimizationPolicy` + `skills/Significance`).

---

## 6. Perception

```cpp
UAIPerceptionComponent* Perception;
UAISenseConfig_Sight* SightCfg = NewObject<UAISenseConfig_Sight>(this);
SightCfg->SightRadius = 1500.f;
SightCfg->LoseSightRadius = 2000.f;
SightCfg->PeripheralVisionAngleDegrees = 60.f;
SightCfg->DetectionByAffiliation.bDetectEnemies = true;
Perception->ConfigureSense(*SightCfg);
Perception->OnTargetPerceptionUpdated.AddDynamic(this, &ThisClass::OnSeen);
```

| Sense | 클래스 | 트리거 |
|-------|--------|--------|
| Sight | `UAISenseConfig_Sight` | 시야 |
| Hearing | `UAISenseConfig_Hearing` | `MakeNoise` 호출 |
| Damage | `UAISenseConfig_Damage` | TakeDamage |
| Team | `UAISenseConfig_Team` | 아군 위치 공유 |
| Touch | `UAISenseConfig_Touch` | 충돌 |
| Prediction | `UAISenseConfig_Prediction` | 예측 |

> 🚨 Affiliation 미설정 시 NPC가 자기끼리 인식 못 함. `IGenericTeamAgentInterface` 구현 의무.

---

## 7. 다수 NPC 최적화 (5중 누적)

`skills/Animation/references/Optimization.md`의 5중을 그대로 적용:

1. **Significance Manager** — 거리 기반 LOD/Tick 토글
2. **EVisibilityBasedAnimTickOption::OnlyTickPoseWhenRendered** — 비가시 NPC Tick 스킵
3. **URO** — Animation 갱신율 동적 조정
4. **AnimSharingInstance** — 동일 AnimBP 공유
5. **BehaviorTreeComponent::SetSendTreeUpdateNotificationsToObserver(false)** — Observer 비활성화 [inferred]

다수 NPC + AI 환경에서 60fps 안정 (`[grep-listed]` — sub-skill 인용).

---

## 8. 정책 의무

- 🚨 `04_OverrideIndex` — `OnPossess` / `OnUnPossess` Super FIRST/LAST
- 🚨 `07_ProfilingScopeRule` — Service Tick / EQS 호출 측정 의무
- 🚨 `09_GlobalIteratorPolicy` — `TActorIterator<APawn>` 회피, AIPerception 등록 사용
- 🚨 `10_ComponentPolicies §3` — Blackboard `UPROPERTY` 보호

---

## 9. 검증 절차

1. Editor PIE — `ShowDebug AI` / `ShowDebug Perception`
2. Behavior Tree 디버거 — Outliner에서 NPC 선택 → BT 시각화
3. Visual Logger — 시간축 기반 AI 결정 로그
4. NavMesh — `Show Navigation` (P 키) — 누락 영역 확인

---

## 10. 외부 검증

- 위키에 없는 EQS Generator/Test → docs.unrealengine.com `EQS` 섹션 (`references/19_ExternalSourcesGuide.md`)
- StateTree (5.x 신규) → 위키에 없음, `[inferred]`
- Mass AI (Plugin) → 위키에 없음, 외부 검증 의무

---

## 관련

- [`skills/GameFramework/references/Controller.md`](../GameFramework/references/Controller.md) — AIController/PlayerController
- [`skills/Animation/references/Optimization.md`](../Animation/references/Optimization.md) — 다수 NPC 5중
- [`skills/Significance/SKILL.md`](../Significance/SKILL.md) — 거리 LOD
- [`references/12_AssetOptimizationPolicy.md`](../../references/12_AssetOptimizationPolicy.md)
- [`references/19_ExternalSourcesGuide.md`](../../references/19_ExternalSourcesGuide.md)
