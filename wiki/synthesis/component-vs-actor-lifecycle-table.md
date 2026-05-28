---
type: synthesis
title: "Component vs Actor 라이프사이클 호출 순서 통합표 — Actor 11단 + Component 5단 매핑"
slug: component-vs-actor-lifecycle-table
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/ue-gameframework-actor]]"
  - "[[sources/ue-components-actorcomponent]]"
  - "[[sources/ue-components-skill]]"
  - "[[sources/ue-ref-04-overrideindex]]"
  - "[[sources/ue-ref-10-componentpolicies]]"
  - "[[sources/ue-coreuobject-uobject]]"
entities:
  - "[[entities/AActor]]"
  - "[[entities/UActorComponent]]"
  - "[[entities/USceneComponent]]"
  - "[[entities/UPrimitiveComponent]]"
  - "[[entities/UObject]]"
concepts:
  - "[[concepts/Actor-Lifecycle]]"
  - "[[concepts/Component-Lifecycle]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Object-Lifecycle]]"
  - "[[concepts/Tick-Group]]"
status: living
tags: [synthesis, lifecycle, beginplay, components, actor]
---

# Component vs Actor 라이프사이클 호출 순서 통합표

## 1. Thesis

`AActor` 의 11단 라이프사이클 ([[concepts/Actor-Lifecycle]]) 과 `UActorComponent` 의 5단 라이프사이클 ([[concepts/Component-Lifecycle]]) 은 *서로 끼워져* 호출된다 — Actor 의 어떤 단계가 컴포넌트의 어떤 단계를 *유발* 하는지 명시 매트릭스. Override 시 각 단계의 **Super 호출 위치** + **이 단계에서 합법적 행동** + **금기** 가 한 표에 정리됨. [[sources/ue-ref-04-overrideindex]] §6.1 (Override 표) + [[sources/ue-ref-10-componentpolicies]] §1·5 (Mobility / Tick) 통합.

## 2. 라이프사이클 통합 매트릭스

| # | Actor 단계 | 호출 시점 | Component 단계 | Super | 합법 / 금기 |
| -- | -- | -- | -- | -- | -- |
| 1 | `PostInitProperties` | Constructor 직후 | (없음) | FIRST | UPROPERTY 디폴트 점검. 자산 로드 금지. CDO 수정 금지 |
| 2 | `PostLoad` | .uasset 로드 시 | (없음) | FIRST | 마이그레이션. PIE / Cooked 모두 발생 |
| 3 | (Constructor) | C++ 객체 생성 | Constructor | — | `CreateDefaultSubobject` 만. `LoadObject` 금지. `Mobility` 명시 |
| 4 | `PostInitializeComponents` | 모든 컴포넌트 등록 후 | `OnRegister` (각 컴포넌트) | FIRST | 컴포넌트 간 참조 캐싱 가능 |
| 5 | (각 컴포넌트) | (4 의 부속) | `InitializeComponent` | FIRST | UWorld 접근 가능. Tick 예약 가능 |
| 6 | `BeginPlay` | World 시작 / Spawn | `BeginPlay` (각 컴포넌트) | **FIRST** | `CachedOwner` 1회 캐싱. 비동기 자산 로드 시작. Subsystem API 안전 |
| 7 | `Tick` (각 그룹) | TG_PrePhysics 등 | `TickComponent` (그룹) | FIRST | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 ([[concepts/Profiling-Scope-Rule]]). `bCanEverTick=true` 일 때만 |
| 8 | `EndPlay` | Destroy / Level 전환 | `EndPlay` (각 컴포넌트) | **LAST** | 비동기 핸들 Cancel. 외부 Subsystem deregister |
| 9 | `OnDestroyed` Delegate | EndPlay 직후 | (없음) | — | DDC / 로그 cleanup |
| 10 | (각 컴포넌트) | EndPlay 안 | `OnUnregister` | FIRST | RenderState 해제 |
| 11 | `BeginDestroy` / `FinishDestroy` | GC | `OnComponentDestroyed` | FIRST | UObject GC — 다른 UObject 참조 금지 |

## 3. Super 호출 규약

| Override | Super 위치 | 이유 |
| -- | -- | -- |
| `BeginPlay` | **FIRST** (자기 코드 위) | 부모가 컴포넌트 등록 / Tick 예약 / Replication 셋업 — 자기 로직은 그 *위* 에서 동작 |
| `Tick` | **FIRST** | 같은 이유 — 부모의 base movement / pose update 필요 |
| `EndPlay` | **LAST** (자기 코드 아래) | 자기 cleanup 끝낸 후 부모가 base teardown — 역순 |
| `OnRegister` / `InitializeComponent` | FIRST | 부모가 RenderState 셋업 |
| `OnUnregister` / `OnComponentDestroyed` | FIRST | 부모 RenderState 해제 |
| `BeginDestroy` | LAST | GC — 자기 참조 먼저 끊고 부모로 |

[[sources/ue-ref-04-overrideindex]] §6.1 의 단일 진실 — UMG 의 Construct/Destruct (FIRST/LAST) 도 같은 패턴 ([[concepts/UMG-Super-Call-Convention]]).

## 4. 시나리오 — 컴포넌트 작성 시 단계별 합법 행동

```cpp
class UMyComp : public UActorComponent
{
    UMyComp() {
        // [3] Constructor — 합법:
        PrimaryComponentTick.bCanEverTick = false;        // Tick 정책
        SetMobility(EComponentMobility::Movable);          // 컴포넌트라면 호스트 SceneComp
        // 금기:
        // LoadObject<>...                                  // ❌ [4] 단계 — 모든 Spawn 동기 IO
        // ConstructorHelpers::FObjectFinder<>             // ❌ Editor only 의도
    }

    virtual void OnRegister() override {
        Super::OnRegister();                                // FIRST
        // RenderState 등록 후 — Material 동적 변경 등
    }

    virtual void BeginPlay() override {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyComp::BeginPlay);  // 의무
        Super::BeginPlay();                                 // FIRST
        CachedOwner = GetOwner();                           // 1회 캐싱
        StartAsyncLoad();                                    // 비동기 자산 로드
    }

    virtual void TickComponent(float Dt, ELevelTick Type, FActorComponentTickFunction* Func) override {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyComp::Tick);
        Super::TickComponent(Dt, Type, Func);                // FIRST
        // Per-frame 로직
    }

    virtual void EndPlay(EEndPlayReason::Type R) override {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyComp::EndPlay);
        // 자기 cleanup 먼저 — 비동기 핸들 등
        if (LoadHandle) LoadHandle->CancelHandle();
        Super::EndPlay(R);                                   // LAST
    }
};
```

## 5. 함정 / 열린 질문

- [ ] **`BeginPlay` 안 자산 로드 동기 호출** — `LoadObject<UStaticMesh>(...)` = 메인 스레드 IO 차단 ([[concepts/Asset-Loading-Policy]] §2 단계 3). 비동기로 ([[sources/mc-soft-skeletalmesh-ragdoll]])
- [ ] **`EndPlay` 안 Super 누락** — 부모 base teardown 안 됨 → RenderProxy / PhysicsState leak
- [ ] **`PostInitializeComponents` vs `BeginPlay`** — 둘 다 모든 컴포넌트 사용 가능. 차이: `PostInitializeComponents` = Spawn 직후 (PIE 미시작 / 시뮬 아직), `BeginPlay` = World 가 *Tick 시작* 후. Subsystem 접근 / RPC 는 BeginPlay 이후만 안전
- [ ] **`UnsafeDuringActorConstruction`** — `UPhysicalAnimationComponent::ApplyPhysicalAnimationProfile*` 같은 함수 ([[sources/ue-components-physicscomponents]] §11 #7). Constructor / `PostInit` 단계 호출 = ensure 위반 ([[concepts/MC-Asset-Validation-Policy]] (B))
- [ ] **컴포넌트 동적 추가 (`NewObject<UMyComp>(this)`)** — `RegisterComponent()` + `AddInstanceComponent()` 페어 호출 의무. 안 그러면 컴포넌트 트리에서 사라짐 ([[concepts/Component-Policies-6]] §2)
- [ ] **`OnRep_*` 의 시점** — Replication 콜백은 Property 도착 직후 (BeginPlay 와 race 가능). Server 쪽은 `BeginPlay` 후에 setter 호출이 정상이지만 Client 는 OnRep_ 가 BeginPlay 보다 먼저 도착할 수 있음 ([[concepts/Replication]] — 열린)
- [ ] **AActor::PreInitializeComponents** — 컴포넌트 등록 *직전*. SubsystemCollection 만 사용 가능. 일반적으로 override 불필요 (열린)

## 6. 관련

### Sources

[[sources/ue-gameframework-actor]] · [[sources/ue-components-actorcomponent]] · [[sources/ue-components-skill]] · [[sources/ue-ref-04-overrideindex]] · [[sources/ue-ref-10-componentpolicies]] · [[sources/ue-coreuobject-uobject]]

### Entities

[[entities/AActor]] · [[entities/UActorComponent]] · [[entities/USceneComponent]] · [[entities/UPrimitiveComponent]] · [[entities/UObject]]

### Concepts

[[concepts/Actor-Lifecycle]] · [[concepts/Component-Lifecycle]] · [[concepts/Component-Policies-6]] · [[concepts/Object-Lifecycle]] · [[concepts/Tick-Group]]

### Related synthesis

[[synthesis/spawnactor-hitching-4-step-pattern]] (Constructor / BeginPlay 비용) · [[synthesis/mc-soft-asset-component-pattern]] (BeginPlay 안 비동기 로드) · [[synthesis/subsystem-5-types-decision-tree]] (Subsystem 의 Initialize 시점)
