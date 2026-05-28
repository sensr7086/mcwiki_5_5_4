---
name: gameframework-controller
description: AController + APlayerController (2,377 lines) + AAIController - Possess/UnPossess + Camera + InputMode + SeamlessTravel + Voice/Audio.
---

# GameFramework/Controller — AController + APlayerController + AIController (cross-link)

> **위치**: `Engine/Source/Runtime/Engine/Classes/GameFramework/Controller.h` (420 lines) + `PlayerController.h` (2,377 lines)
> **베이스**: `AController : public AActor` / `APlayerController : public AController` / `AAIController : public AController` (AIModule — 본 위키 분석 범위 외 → cross-link)
> **요지**: AController = **Pawn 의 비물질 소유자** (Server only Authority). APlayerController = **Local + Remote 클라이언트의 입력·카메라·UI 게이트웨이** (자동 복제 + RPC 진입점). AAIController = **AI 두뇌 호스트** (BehaviorTree + Blackboard + Perception).

---

## 🚨 공통 정책 (Components 6대 의무 + Controller 특화)

| # | 정책 | Controller 적용 |
|---|------|----------------|
| 1 | **Mobility** | Controller 는 RootComponent 보유하지만 시각 X — `Static`/`Movable` 무관 (위치 추적 안 함). |
| 2 | **NewObject + DuplicateObject** | Controller = `World->SpawnActor<APlayerController>(Class, Transform)` — 일반적으로 **GameMode 가 SpawnPlayerController 자동 호출**. AIController = `Pawn->SpawnDefaultController()` 또는 Pawn 의 `AIControllerClass` 자동. |
| 3 | **GC 방어** | `UPROPERTY()` + `TObjectPtr<AController>` 또는 `TWeakObjectPtr<AController>` (캐싱 — Possess/UnPossess 시 변경됨) + Pawn 의 Controller 멤버는 베이스에서 자동 복제. |
| 4 | **Cached References** | `OnPossess(InPawn)` 안에서 `CachedPawn` / `CachedCharacter` 캐싱 + `OnUnPossess()` 에서 `Reset()`. PlayerController 의 PlayerState 는 베이스가 자동. |
| 5 | **PrimaryActorTick** | AController 자체 Tick 비활성 + APlayerController 는 `PlayerTick(DeltaTime)` 자동 (Local 클라이언트만). AAIController 는 BehaviorTree Tick 분리. |
| 6 | **CDO + OnConstruction** | Controller 의 PlayerCameraManagerClass / PlayerInputClass 등 BP 셋업은 Constructor 안 — OnConstruction 멱등 의무. |
| 🎯 **어셋 로드** | 🚨 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) — **PlayerCameraManagerClass / HUDClass / PlayerInputClass = Hard** (BP 작음). HUD 자식의 Texture / Brush / Font = Soft + 첫 표시 직전 PreLoad. **InputMappingContext (Enhanced Input)** = `TObjectPtr<UInputMappingContext>` Hard (작은 자산). **AIController = BehaviorTree / Blackboard 자산** = Hard (BT 자체 작음, Task 자식만 Soft 검토). |

---

## 1. 의존 트리 + Possess 흐름

```
AActor                              (GameFramework/Actor)
└── AController                     (GameFramework/Controller §3)
    │
    │  📌 핵심: Pawn 의 비물질 소유자 (Server only) + PlayerState 페어 + StateName
    │
    ├── APlayerController           (GameFramework/Controller §4)
    │     │
    │     │  📌 핵심: Local + Remote 클라 + 입력 Stack + Camera Manager + UI Mode
    │     │
    │     ├─ PlayerCameraManager: APlayerCameraManager   ── 시점 관리 (자동 Spawn)
    │     ├─ PlayerInput: UPlayerInput                   ── 입력 매핑 (자동 생성)
    │     ├─ MyHUD: AHUD                                 ── HUD (BP 클래스 설정)
    │     ├─ PlayerState: APlayerState                   ── 베이스에서 자동 (서버 Spawn + 복제)
    │     └─ CurrentInputStack: TArray<TWeakObjectPtr<UInputComponent>>   ── 입력 Stack
    │
    └── AAIController                (AIModule — cross-link only)
          ├─ PathFollowingComponent: UPathFollowingComponent
          ├─ BrainComponent: UBrainComponent
          ├─ Blackboard: UBlackboardComponent
          └─ Perception: UAIPerceptionComponent
```

### Possess 흐름 (Server only — Authority)

```
[Server]
GameMode->SpawnDefaultPawnFor(NewPlayer)
  ↓ APawn* Pawn = World->SpawnActor<APawn>(...)
  ↓
NewPlayer->Possess(Pawn)   ── 4.22+ final — OnPossess override
  ↓ Pawn->PossessedBy(this)               ── Pawn.cpp §3.1 — Controller 캐싱
  ↓ AController::OnPossess(Pawn)           ── 자식 override 진입점
  ↓ Pawn->Restart()                        ── 입력 셋업
  ↓ ChangeState(NAME_Playing)              ── 상태 전이
  ↓ if PlayerController: SpawnPlayerCameraManager / SetViewTarget(Pawn) / ClientRestart
[Client] (PlayerController 만)
  ↓ AcknowledgePawn(Pawn)                  ── 클라 → 서버 ACK (서버가 Pawn 복제 완료 알림)
  ↓ Pawn->NotifyControllerChanged()         ── BP 콜백
```

> **UnPossess 흐름**:
> ```
> Server: AController::UnPossess()  (final)
>   ↓ AController::OnUnPossess()             ── 자식 override 진입점
>   ↓ Pawn->UnPossessed()                    ── Pawn.cpp §3.1
>   ↓ ChangeState(NAME_Inactive)
>   ↓ Pawn = nullptr / Character = nullptr
> ```

---

## 2. AController 베이스 (420 lines)

### 2.1 핵심 멤버

```cpp
// Controller.h:50 — PlayerState (PlayerController 만 — AI 는 nullptr)
UPROPERTY(replicatedUsing = OnRep_PlayerState, BlueprintReadOnly, Category=Controller)
TObjectPtr<APlayerState> PlayerState;

// Controller.h:230 — Pawn 캐싱
inline TObjectPtr<APawn> GetPawn() const { return Pawn; }

// Controller.h:240 — Character 캐싱 (Cast 자동 — Pawn 이 ACharacter 자손이면)
inline ACharacter* GetCharacter() const { return Character; }

// Controller.h:66 — 상태 이름 (NAME_Playing / NAME_Inactive / NAME_Spectating 등)
FName StateName;
```

### 2.2 Possess / UnPossess (4.22+ final — OnPossess override)

```cpp
// Controller.h:281 — final 처리됨 (override 금지)
ENGINE_API virtual void Possess(APawn* InPawn) final;

// Controller.h:296 — 자식 override 진입점
ENGINE_API virtual void OnPossess(APawn* InPawn);

// Controller.h:285 — final
ENGINE_API virtual void UnPossess() final;

// 자식 override 진입점
ENGINE_API virtual void OnUnPossess();
```

```cpp
// MyAIController.cpp — 표준 override
void AMyAIController::OnPossess(APawn* InPawn)
{
    Super::OnPossess(InPawn);    // ⚠️ 처음 — 베이스가 Pawn 캐싱 + ChangeState
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyAIController::OnPossess);

    // 캐싱
    CachedPawn = InPawn;
    CachedCharacter = Cast<AMyCharacter>(InPawn);

    // BehaviorTree 시작
    if (auto* AICharacter = Cast<AMyAICharacter>(InPawn))
    {
        if (UBehaviorTree* BT = AICharacter->BehaviorTreeAsset)
        {
            RunBehaviorTree(BT);
        }
    }
}

void AMyAIController::OnUnPossess()
{
    // BT 정리 먼저
    if (BrainComponent) BrainComponent->StopLogic(TEXT("OnUnPossess"));
    CachedPawn.Reset();

    Super::OnUnPossess();         // ⚠️ 마지막
}
```

### 2.3 ChangeState / StateName

```cpp
// Controller.h:142
ENGINE_API virtual void ChangeState(FName NewState);

// Controller.h:149
ENGINE_API bool IsInState(FName InStateName) const;

// 베이스 상태 (Engine 전역)
NAME_Spectating              // 관전 중
NAME_Playing                 // 게임 중
NAME_Inactive                // 비활성
NAME_Roaming                 // 자유 이동
```

### 2.4 PlayerState 라이프사이클 (PlayerController 만)

```cpp
// Controller.h:185 — 클라 측 PlayerState 복제 콜백
ENGINE_API virtual void OnRep_PlayerState();
{
    // 베이스가 OnPlayerStateChanged 호출
}

// Controller.h:269 — Destroyed 시 호출
ENGINE_API virtual void CleanupPlayerState();
{
    // PlayerState->Destroy() — 베이스가 자동
}
```

---

## 3. APlayerController 깊이 (2,377 lines)

### 3.1 핵심 멤버

```cpp
// PlayerController.h:285 — 카메라 매니저 (자동 Spawn)
TObjectPtr<APlayerCameraManager> PlayerCameraManager;

// PlayerController.h:289 — 카메라 클래스 (BP 에서 설정)
TSubclassOf<APlayerCameraManager> PlayerCameraManagerClass;

// PlayerController.h:368 — 입력 매핑
TObjectPtr<UPlayerInput> PlayerInput;

// PlayerController.h:1695 — 입력 Stack
TArray<TWeakObjectPtr<UInputComponent>> CurrentInputStack;
```

### 3.2 Input Mode 3종 (UI / Game / Hybrid)

```cpp
// PlayerController.h:124 — UI 만 (메뉴)
struct FInputModeUIOnly : public FInputModeDataBase
{
    FInputModeUIOnly& SetWidgetToFocus(TSharedPtr<SWidget> InWidget);
    FInputModeUIOnly& SetLockMouseToViewportBehavior(EMouseLockMode InMode);
};

// PlayerController.h:179 — UI + Game 동시 (인벤토리 + 캐릭터 회전)
struct FInputModeGameAndUI : public FInputModeDataBase
{
    FInputModeGameAndUI& SetWidgetToFocus(TSharedPtr<SWidget> InWidget);
    FInputModeGameAndUI& SetLockMouseToViewportBehavior(EMouseLockMode InMode);
    FInputModeGameAndUI& SetHideCursorDuringCapture(bool bHide);
};

// PlayerController.h:210 — Game 만 (FPS 표준)
struct FInputModeGameOnly : public FInputModeDataBase
{
    FInputModeGameOnly& SetConsumeCaptureMouseDown(bool bConsume);
};
```

```cpp
// 표준 사용
void AMyPlayerController::OpenMenu()
{
    FInputModeUIOnly Mode;
    Mode.SetWidgetToFocus(MenuWidget->TakeWidget());
    Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    SetInputMode(Mode);
    bShowMouseCursor = true;
}

void AMyPlayerController::CloseMenu()
{
    FInputModeGameOnly Mode;
    SetInputMode(Mode);
    bShowMouseCursor = false;
}

void AMyPlayerController::OpenInventory()
{
    FInputModeGameAndUI Mode;
    Mode.SetWidgetToFocus(InventoryWidget->TakeWidget());
    Mode.SetHideCursorDuringCapture(false);
    SetInputMode(Mode);
    bShowMouseCursor = true;
}
```

### 3.3 Input Component Stack (Push / Pop)

> **모든 입력은 Stack — Top 부터 Bottom 으로 처리 (Consumed 되면 stop)**.

```cpp
// PlayerController.h:1747
ENGINE_API virtual void PushInputComponent(UInputComponent* Input);

// PlayerController.h:1750
ENGINE_API virtual bool PopInputComponent(UInputComponent* Input);

// PlayerController.h:1753
ENGINE_API virtual bool IsInputComponentInStack(const UInputComponent* Input) const;
```

```cpp
// 사용 — 메뉴 열 때 Pawn 입력 무시
class UMenuWidget : public UUserWidget
{
    UPROPERTY()
    TObjectPtr<UInputComponent> MenuInputComponent;

    void ShowMenu()
    {
        MenuInputComponent->BindAction(CloseAction, ETriggerEvent::Started, this, &UMenuWidget::Close);
        GetOwningPlayer()->PushInputComponent(MenuInputComponent);
    }

    void HideMenu()
    {
        GetOwningPlayer()->PopInputComponent(MenuInputComponent);
    }
};
```

### 3.4 Camera / View Target

```cpp
// PlayerController.h:1215 — Client RPC (서버 → 클라)
ENGINE_API void ClientSetViewTarget(AActor* A, FViewTargetTransitionParams TransitionParams = FViewTargetTransitionParams());

// 일반 — Local 호출 (서버 + Local 클라 모두)
ENGINE_API virtual void SetViewTarget(AActor* NewViewTarget, FViewTargetTransitionParams TransitionParams = FViewTargetTransitionParams());

// 부드러운 전환
ENGINE_API void SetViewTargetWithBlend(
    AActor* NewViewTarget,
    float BlendTime = 0.f,
    EViewTargetBlendFunction BlendFunc = VTBlend_Linear,
    float BlendExp = 0.f,
    bool bLockOutgoing = false
);
```

```cpp
// 컷씬 카메라 전환
PC->SetViewTargetWithBlend(CinematicCamera, 2.f, VTBlend_EaseInOut, 2.f, true);
// 컷씬 끝
PC->SetViewTargetWithBlend(GetPawn(), 1.f, VTBlend_EaseInOut, 2.f, true);
```

### 3.5 Mouse Cursor / Hit Test

```cpp
// PlayerController.h:525
uint32 bShowMouseCursor:1;            // 커서 표시
uint32 bEnableClickEvents:1;          // 클릭 이벤트 활성
uint32 bEnableMouseOverEvents:1;      // MouseOver 활성

// PlayerController.h:710 — 커서 아래 트레이스 (RTS / Click-to-move)
ENGINE_API bool GetHitResultUnderCursorByChannel(ETraceTypeQuery TraceChannel, bool bTraceComplex, FHitResult& HitResult) const;

// PlayerController.h:1618
ENGINE_API bool GetMousePosition(double& LocationX, double& LocationY) const;

// PlayerController.h:1632
ENGINE_API void GetInputAnalogStickState(EControllerAnalogStick::Type WhichStick, double& StickX, double& StickY) const;
```

```cpp
// RTS Click-to-move
void AMyPC::OnClick()
{
    FHitResult Hit;
    if (GetHitResultUnderCursorByChannel(UEngineTypes::ConvertToTraceType(ECC_Visibility), false, Hit))
    {
        UAIBlueprintHelperLibrary::SimpleMoveToLocation(this, Hit.Location);
    }
}
```

### 3.6 ClientTravel / SeamlessTravel (맵 전환)

```cpp
// PlayerController.h:1411 — 맵 전환 (클라 측 호출)
ENGINE_API void ClientTravel(const FString& URL, ETravelType TravelType, bool bSeamless = false, FGuid MapPackageGuid = FGuid());

// SeamlessTravel — UGameInstance 가 처리
ENGINE_API virtual void SeamlessTravelTo(APlayerController* NewPC);   // 이전 PC → 새 PC 데이터 이전
ENGINE_API virtual void SeamlessTravelFrom(APlayerController* OldPC);
ENGINE_API virtual void PostSeamlessTravel();
```

```cpp
// SeamlessTravel 데이터 이전 — PlayerState 복사 패턴
void AMyPC::SeamlessTravelFrom(APlayerController* OldPC)
{
    Super::SeamlessTravelFrom(OldPC);
    if (auto* OldMyPC = Cast<AMyPC>(OldPC))
    {
        // 점수·인벤토리 등 이전
        SavedScore = OldMyPC->SavedScore;
    }
}

// 살아남는 Actor 명시 (Server)
void AMyPC::GetSeamlessTravelActorList(bool bToEntry, TArray<AActor*>& ActorList)
{
    Super::GetSeamlessTravelActorList(bToEntry, ActorList);
    if (auto* PreservedActor = GetPreservedActor())
    {
        ActorList.Add(PreservedActor);
    }
}
```

> **자세한 SeamlessTravel = [`GameFramework/GameMode`](../GameMode/SKILL.md)** + [`GameInstance`](../GameInstance/SKILL.md).

### 3.7 PlayerTick (Local Only)

```cpp
// PlayerController.h:678 — PlayerInput Tick 후 호출 (Local 만)
ENGINE_API virtual void PlayerTick(float DeltaTime);
```

> **함정**: PlayerTick 은 **로컬 클라**만 호출 — Dedicated Server 에서 호출 안 됨. 서버 측 매 프레임 로직 = Pawn::Tick 또는 Tick.

### 3.8 AcknowledgePawn (서버 → 클라 동기)

```cpp
// 서버가 Pawn Spawn + Possess 후 클라 측 Pawn 복제 완료 시 자동 호출
ENGINE_API virtual void AcknowledgePawn(APawn* P);
{
    // 베이스: SetViewTarget + Pawn->Restart 등
}
```

> **Possess 후 Pawn 의 입력이 안 작동** = AcknowledgePawn 누락 의심. 베이스가 자동 처리하지만 override 시 Super 호출 의무.

---

## 4. AAIController (AIModule — cross-link)

> **AIModule 은 본 위키 분석 범위 외** (Engine/Source/Runtime/AIModule). 표준 셋업 + cross-reference 만.

### 4.1 핵심 컴포넌트

```cpp
class AAIController : public AController
{
    TObjectPtr<UPathFollowingComponent> PathFollowingComponent;   // NavMesh 경로 추종
    TObjectPtr<UBrainComponent> BrainComponent;                    // BehaviorTree 호스트
    TObjectPtr<UAIPerceptionComponent> PerceptionComponent;        // 시각·청각·데미지 감지
    TObjectPtr<UBlackboardComponent> Blackboard;                   // 동적 데이터 저장
};
```

### 4.2 표준 사용 (BehaviorTree + Blackboard)

```cpp
class AMyAIController : public AAIController
{
    AMyAIController()
    {
        // 자동 BT + Blackboard
        BrainComponent = CreateDefaultSubobject<UBehaviorTreeComponent>(TEXT("BTComp"));
        Blackboard = CreateDefaultSubobject<UBlackboardComponent>(TEXT("BBComp"));
    }

    virtual void OnPossess(APawn* InPawn) override
    {
        Super::OnPossess(InPawn);
        if (auto* AIChar = Cast<AMyAICharacter>(InPawn))
        {
            if (UBlackboardData* BBData = AIChar->BlackboardAsset)
            {
                UseBlackboard(BBData, Blackboard);
            }
            if (UBehaviorTree* BT = AIChar->BehaviorTreeAsset)
            {
                RunBehaviorTree(BT);
            }
        }
    }
};
```

### 4.3 AI 표준 패턴 (Pawn 의 AIControllerClass + AutoPossessAI)

```cpp
// AMyAICharacter Constructor
AMyAICharacter::AMyAICharacter()
{
    AIControllerClass = AMyAIController::StaticClass();
    AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;   // 표준
}
```

> **AIController = AIModule 의존 — Build.cs 에 `"AIModule", "GameplayTasks", "NavigationSystem"` 추가 의무**.

---

## 5. Player vs AI Controller 분기 결정

| 시나리오 | Controller |
|---------|-----------|
| 사람 플레이어 (Local + Remote) | `APlayerController` |
| AI NPC (BehaviorTree) | `AAIController` (AIModule) |
| Spectator (관전자) | `APlayerController` + `bSpectator = true` |
| 무선 조종 (Remote AI 명령) | `AAIController` + Network RPC |
| 컷씬 카메라 (조종 X) | `APlayerController` (입력 비활성) + `SetViewTarget(CinematicCam)` |

---

## 6. 🎯 최적화 방안 (Controller 측면)

### 6.1 PlayerController Tick 회피

```cpp
// AMyPC Constructor
PrimaryActorTick.bCanEverTick = false;     // PlayerTick 으로 자동 (Local 만)
// PlayerTick 안에 매 프레임 로직 — 단 Local 만
```

### 6.2 AIController Tick — Significance + BehaviorTree Tick 조정

```cpp
// AI Significance — BT Tick Interval 조정
auto* BTComp = Cast<UBehaviorTreeComponent>(BrainComponent);
BTComp->SetComponentTickEnabled(true);
BTComp->SetComponentTickInterval(0.2f);    // 200ms — 가까운 AI 만 빠르게

// 매우 멀리 (Significance < 0.1) — BT 정지
if (NewSig < 0.1f)
{
    BTComp->StopLogic(TEXT("LowSignificance"));
}
```

### 6.3 Network 최적화

| 항목 | Player | AI |
|------|--------|-----|
| AController.bReplicates | true (자동) | false (서버 only) |
| PlayerState 복제 | true | nullptr (없음) |
| RPC 빈도 | 33Hz | N/A (서버 only) |
| ViewTarget 복제 | true (Smooth) | N/A |

### 6.4 Input Stack 최적화

```cpp
// 메뉴 열 때 Pawn 입력 비활성 — Pawn->DisableInput 보다 Stack 사용 권장
GetOwningPlayer()->PushInputComponent(MenuInputComp);   // 메뉴 입력만 활성
// 메뉴 닫을 때
GetOwningPlayer()->PopInputComponent(MenuInputComp);     // 자동 복원
```

> **Pawn->DisableInput** 는 InputComponent 자체 비활성 — Stack 으로 처리하면 더 깔끔 + 복원 자동.

---

## 7. 함정 & 안티패턴 (12종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | `Possess()` override 시도 | 4.22+ `final` — `OnPossess(APawn*)` override 사용 |
| 2 | `OnPossess` Super 호출 안 함 | Pawn 캐싱·ChangeState 등 베이스 동작 누락 — 의무 호출 |
| 3 | Possess 가 Server 외에서 동작할 거라 가정 | ⚠️ Server only — Client 에서 Possess 직접 호출 시 무시 |
| 4 | `BeginPlay` 에서 `GetPawn()` 사용 — Possess 전 nullptr | `OnPossess` 콜백에서 처리 또는 `if (GetPawn())` 가드 |
| 5 | 클라 측에서 `SetViewTarget` 직접 호출 | Local 만 적용. Server → Client 는 `ClientSetViewTarget` RPC |
| 6 | `bShowMouseCursor` 활성 + InputMode 변경 안 함 | UI 클릭 안 됨 — `SetInputMode(FInputModeGameAndUI)` 의무 |
| 7 | InputComponent 직접 Pawn 에 추가 (PushInputComponent 우회) | Stack 안 들어감 — 우선순위 / Pop 안 됨 |
| 8 | SeamlessTravel 안 PlayerState 데이터 이전 안 함 | `SeamlessTravelFrom(OldPC)` 안에서 명시적 복사 |
| 9 | `PlayerTick` Dedicated Server 에서 호출 가정 | Local 만 — Server 매 프레임 로직 = `Tick` 또는 Pawn::Tick |
| 10 | AIController Build.cs 에 AIModule 추가 안 함 | `PublicDependencyModuleNames.AddRange({"AIModule", "GameplayTasks", "NavigationSystem"})` |
| 11 | 🚨 `OnPossess` / `OnUnPossess` / `PlayerTick` 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 ([`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)) |
| 12 | 🚨 `TActorIterator<APlayerController>` 사용 | `GameInstance->GetLocalPlayerIterator()` 또는 `GetWorld()->GetFirstPlayerController()` 사용 ([`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md)) |

---

## 8. 체크리스트 (Controller 자식 작성 시)

- [ ] `OnPossess(APawn*)` override (Possess 직접 X — final)
- [ ] `OnPossess`: Super 처음 + CachedPawn / CachedCharacter 캐싱 + AI = BT 시작
- [ ] `OnUnPossess`: Super 마지막 + 캐싱 정리 + AI = BT 정지
- [ ] PlayerController: PlayerCameraManagerClass / PlayerInputClass 설정 (필요 시)
- [ ] PlayerController: SetInputMode + bShowMouseCursor 페어 일관
- [ ] PlayerController: Input Stack 사용 (Push/Pop) — 직접 InputComponent 추가 X
- [ ] PlayerController: SetViewTarget — Local 만. Server → Client = ClientSetViewTarget
- [ ] PlayerController: SeamlessTravelFrom 안 데이터 이전
- [ ] AIController: Build.cs `"AIModule", "GameplayTasks", "NavigationSystem"` 추가
- [ ] AIController: BrainComponent + Blackboard CreateDefaultSubobject
- [ ] 🚨 6대 정책 만족 ([`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md))
- [ ] 🚨 콜백 첫 줄 프로파일링 스코프
- [ ] 🚨 전역 이터레이터 사용 안 함

---

## 9. 관련 sub-skill

- [`GameFramework/Actor`](../Actor/SKILL.md) — 베이스 (Controller → Actor)
- [`GameFramework/PawnCharacter`](../PawnCharacter/SKILL.md) — 소유 대상 (Possess/UnPossess 페어)
- [`GameFramework/GameMode`](../GameMode/SKILL.md) — Controller Spawn 진입점 (SpawnPlayerController)
- [`GameFramework/GameInstance`](../GameInstance/SKILL.md) — SeamlessTravel 흐름
- [`Components/SystemComponents`](../../Components/references/SystemComponents.md) — Enhanced Input §1
- [`CoreUObject/Network`](../../CoreUObject/references/Network.md) — RPC / DOREPLIFETIME
- [`Slate`](../../Slate/SKILL.md) — UI Mode + Widget Focus
- 외부: AIModule (분석 범위 외 — BehaviorTree / Blackboard / Perception)
- 교차: 🚨 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) · 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) · 🚨 [`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md)

---

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. AController 420 lines (PlayerState 페어 / GetPawn / GetCharacter / StateName 4종 / Possess+UnPossess final / OnPossess+OnUnPossess override 진입점 / ChangeState / IsInState / OnRep_PlayerState / CleanupPlayerState). APlayerController 2,377 lines (PlayerCameraManager / PlayerInput / Input Mode 3종 UIOnly+GameAndUI+GameOnly / Input Stack Push+Pop / SetViewTarget+SetViewTarget