---
name: gameframework-gamemode
description: AGameModeBase + AGameMode (Match State 5종) + AGameStateBase + AGameState + APlayerState - SeamlessTravel + Multiplayer 게임 흐름.
---

# GameFramework/GameMode — GameModeBase + GameMode + GameStateBase + GameState + PlayerState

> **위치**: `Engine/Source/Runtime/Engine/Classes/GameFramework/`
> **파일**: `GameModeBase.h` (672 lines) + `GameMode.h` (11K — Match State 흐름) + `GameStateBase.h` (7K) + `GameState.h` (3K) + `PlayerState.h` (16K)
> **베이스**: `AGameModeBase : public AInfo` (AInfo : public AActor) / `AGameMode : public AGameModeBase`
> **요지**: GameModeBase = **🔒 서버 only Authority** (모든 게임 룰·플레이어 관리). GameStateBase = **모든 클라이언트 복제** (게임 상태 — PlayerArray·ServerTime). PlayerState = **개별 플레이어 데이터** (점수·이름·UniqueId).

---

## 🚨 공통 정책 (Components 6대 의무 + GameMode 특화)

| # | 정책 | GameMode/State 적용 |
|---|------|--------------------|
| 1 | **Mobility** | GameMode/GameState 는 RootComponent 시각 무관 (AInfo 자손 — 보이지 않는 Actor). 위치 추적 X. |
| 2 | **NewObject + DuplicateObject** | GameMode = **UWorld 가 자동 Spawn** (1개 인스턴스 — Server only). GameState = GameMode 가 Spawn 후 **모든 클라 복제**. PlayerState = PlayerController 페어 자동 Spawn. |
| 3 | **GC 방어** | `UPROPERTY()` + `TObjectPtr<>` 자동. PlayerArray 의 PlayerState 는 GameStateBase 가 자동 관리. |
| 4 | **GetGameInstance / GetWorld 캐싱** | GameMode 는 1개 인스턴스 — `GetGameInstance()` 캐싱 불필요 (inline). PlayerState ↔ Controller 페어는 양방향 캐싱 필요. |
| 5 | **PrimaryActorTick** | GameMode Tick 권장 안 함 — Match State 흐름은 Timer 기반 표준. GameState Tick 도 OFF — 매 프레임 갱신 필요 시 PlayerState 갱신 + Replication. |
| 6 | **CDO + OnConstruction** | GameMode 의 클래스 슬롯 (DefaultPawnClass / PlayerControllerClass / GameStateClass / HUDClass) 은 Constructor 안만 — DefaultEngine.ini `[/Script/Engine.GameMode]` 에서 BP 클래스 지정. |
| 🎯 **어셋 로드** | 🚨 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) — **🔥 GameMode 가 PreLoad 의 진입점**. **`HandleMatchHasStarted`** 안에서 매치 사용 모든 Primary Asset (Weapon / Enemy / Powerup) `PreloadPrimaryAssets(bLoadRecursive=true)` 호출 — Subobject 까지 메모리 + GPU 상주. **DefaultPawnClass / PlayerControllerClass / GameStateClass = Hard** (자주 Spawn 되어 Soft 비효율). **SeamlessTravel 시 다음 Map 의 Primary Asset 사전 로드** + Transition Map 사용. 자세한 패턴 = [`Actor §12.5`](../Actor/SKILL.md). |

---

## 1. 의존 트리 + Login 흐름

```
AActor                                  (GameFramework/Actor)
└── AInfo                               (보이지 않는 Actor — RootComponent X)
    ├── AGameModeBase                   (서버 only, 1개 인스턴스)
    │   └── AGameMode                   (Match State 흐름 추가)
    ├── AGameStateBase                  (모든 클라 복제)
    │   └── AGameState                  (MatchState 복제 추가)
    └── APlayerState                    (PlayerController 페어 — 클라마다 1개)
```

### Login 흐름 (Server only)

```
[Server — 클라이언트 접속 시]
1. UWorld::Listen()                                    ── 서버 시작
2. AGameModeBase::InitGame(MapName, Options, Error)    ── 맵 로드 직전
3. AGameModeBase::InitGameState()                       ── GameStateBase Spawn
4. AGameStateBase::HandleBeginPlay()                    ── GameState BeginPlay (모든 클라에 복제)
5. AGameModeBase::StartPlay()                           ── 모든 Actor BeginPlay 트리거

[새 플레이어 접속 시]
6. AGameModeBase::PreLogin(...) (override 가능)         ── 검증 (밴 / 비밀번호 등)
7. AGameModeBase::Login(NewPlayer, Portal, Options, ID, Error) ── PlayerController Spawn
8. AGameModeBase::PostLogin(NewPlayer)                  ── 자식 override 진입점
   ↓ HandleStartingNewPlayer(NewPlayer)
   ↓ RestartPlayer(NewPlayer)
     ↓ FindPlayerStart                                  ── PlayerStart 위치 탐색
     ↓ SpawnDefaultPawnFor(NewPlayer)                   ── Pawn Spawn (DefaultPawnClass)
     ↓ NewPlayer->Possess(Pawn)                         ── Controller → Pawn 연결

[플레이어 떠날 때]
9. AGameModeBase::Logout(Exiting)                       ── PlayerState 정리
```

---

## 2. AGameModeBase 핵심 (672 lines)

### 2.1 클래스 슬롯 (BP 에서 지정)

```cpp
// GameModeBase.h:92~112
TSubclassOf<AGameStateBase> GameStateClass;             // 기본 = AGameStateBase
TSubclassOf<APlayerController> PlayerControllerClass;    // 기본 = APlayerController
TSubclassOf<APlayerState> PlayerStateClass;              // 기본 = APlayerState
TSubclassOf<AHUD> HUDClass;                              // 기본 = AHUD
TSubclassOf<APawn> DefaultPawnClass;                     // 기본 = ADefaultPawn
TSubclassOf<ASpectatorPawn> SpectatorClass;              // 기본 = ASpectatorPawn
TSubclassOf<APlayerController> ReplaySpectatorPlayerControllerClass;
```

```cpp
// MyGameMode Constructor — BP 에서 또는 코드에서
AMyGameMode::AMyGameMode()
{
    DefaultPawnClass        = AMyCharacter::StaticClass();
    PlayerControllerClass   = AMyPlayerController::StaticClass();
    GameStateClass          = AMyGameState::StaticClass();
    PlayerStateClass        = AMyPlayerState::StaticClass();
    HUDClass                = AMyHUD::StaticClass();
    SpectatorClass          = ASpectatorPawn::StaticClass();
}
```

### 2.2 라이프사이클 진입점

| virtual | 위치 | 호출 시점 |
|---------|------|----------|
| `InitGame(MapName, Options, Error)` | `GameModeBase.h:62` | 맵 로드 직전 — BeginPlay 보다 먼저 |
| `InitGameState()` | `GameModeBase.h:69` | GameState Spawn 후 |
| `StartPlay()` | `GameModeBase.h:159` | 모든 Actor BeginPlay 트리거 |
| `PostLogin(NewPlayer)` | `GameModeBase.h:326` | 새 플레이어 PlayerController Spawn 후 |
| `Logout(Exiting)` | `GameModeBase.h:342` | 플레이어 떠날 때 |
| `HandleSeamlessTravelPlayer(C)` | `GameModeBase.h:262` | SeamlessTravel 시 PC 데이터 이전 |

```cpp
// MyGameMode.cpp
void AMyGameMode::InitGame(const FString& MapName, const FString& Options, FString& ErrorMessage)
{
    Super::InitGame(MapName, Options, ErrorMessage);   // ⚠️ 처음
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyGameMode::InitGame);

    // URL 옵션 파싱 — `?MaxPlayers=4` 등
    MaxPlayers = UGameplayStatics::GetIntOption(Options, TEXT("MaxPlayers"), 4);

    // ⚠️ BeginPlay 전 — Actor 검색 X / GameState 아직 nullptr
}

void AMyGameMode::PostLogin(APlayerController* NewPlayer)
{
    Super::PostLogin(NewPlayer);                       // ⚠️ 처음 — 베이스가 RestartPlayer 호출
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyGameMode::PostLogin);

    // 모든 플레이어 입장 후 게임 시작
    if (GetNumPlayers() >= MaxPlayers)
    {
        StartGame();
    }
}

void AMyGameMode::Logout(AController* Exiting)
{
    // 정리 작업 먼저
    SaveExitingPlayerState(Exiting);

    Super::Logout(Exiting);                            // ⚠️ 마지막
}
```

### 2.3 RestartPlayer / FindPlayerStart / SpawnDefaultPawnFor

```cpp
// GameModeBase.h:441 — 표준 Restart (BeginPlay + Death 후 재시작)
ENGINE_API virtual void RestartPlayer(AController* NewPlayer);

// GameModeBase.h:445 — 특정 PlayerStart 위치
ENGINE_API virtual void RestartPlayerAtPlayerStart(AController* NewPlayer, AActor* StartSpot);

// GameModeBase.h:449 — 임의 Transform
ENGINE_API virtual void RestartPlayerAtTransform(AController* NewPlayer, const FTransform& SpawnTransform);

// FindPlayerStart override — 팀 기반 / 첫 PlayerStart 등
ENGINE_API virtual AActor* ChoosePlayerStart_Implementation(AController* Player);
```

```cpp
// 팀 기반 PlayerStart
AActor* AMyGameMode::ChoosePlayerStart_Implementation(AController* Player)
{
    auto* MyPS = Player->GetPlayerState<AMyPlayerState>();
    int32 TeamIndex = MyPS ? MyPS->TeamIndex : 0;

    TArray<AActor*> Starts;
    UGameplayStatics::GetAllActorsOfClass(this, ATeamPlayerStart::StaticClass(), Starts);
    for (AActor* S : Starts)
    {
        if (auto* TS = Cast<ATeamPlayerStart>(S); TS && TS->TeamIndex == TeamIndex)
        {
            return TS;
        }
    }
    return Super::ChoosePlayerStart_Implementation(Player);
}
```

---

## 3. AGameMode — Match State 흐름 (확장 — 멀티플레이 게임)

### 3.1 5종 Match State (GameMode.h:16-26)

```cpp
namespace MatchState
{
    extern const FName EnteringMap;          // 맵 입장 중
    extern const FName WaitingToStart;       // 모든 플레이어 입장 대기
    extern const FName InProgress;           // 게임 진행
    extern const FName WaitingPostMatch;     // 게임 종료 — 리절트 표시 / Tick 유지
    extern const FName LeavingMap;           // 다음 맵 전환
    extern const FName Aborted;              // 비정상 종료
}
```

### 3.2 전이 메소드

```cpp
// GameMode.h:51 — WaitingToStart → InProgress
ENGINE_API virtual void StartMatch();

// GameMode.h:55 — InProgress → WaitingPostMatch
ENGINE_API virtual void EndMatch();

// GameMode.h:63 — 비정상 종료
ENGINE_API virtual void AbortMatch();

// GameMode.h:88 — 자동 시작 조건 (override 가능)
ENGINE_API bool ReadyToStartMatch();

// GameMode.h:95 — 자동 종료 조건
ENGINE_API bool ReadyToEndMatch();
```

### 3.3 Match State Handler (자동 호출)

```cpp
// GameMode.h:84/91/98/101 — 각 상태 진입 시 자동 호출
ENGINE_API virtual void HandleMatchIsWaitingToStart();
ENGINE_API virtual void HandleMatchHasStarted();
ENGINE_API virtual void HandleMatchHasEnded();
ENGINE_API virtual void HandleLeavingMap();
```

```cpp
// MyGameMode (AGameMode 자손) — 표준 Match 흐름
void AMyGameMode::HandleMatchHasStarted()
{
    Super::HandleMatchHasStarted();   // 베이스가 모든 PC->ClientStartMatch 호출
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyGameMode::HandleMatchHasStarted);

    // 모든 플레이어 점수 리셋
    for (auto* PS : GameState->PlayerArray)
    {
        if (auto* MyPS = Cast<AMyPlayerState>(PS))
        {
            MyPS->Score = 0;
            MyPS->Kills = 0;
        }
    }

    // 매치 타이머 시작
    GetWorld()->GetTimerManager().SetTimer(MatchTimer, this, &AMyGameMode::EndMatch, MatchDuration, false);
}

bool AMyGameMode::ReadyToStartMatch_Implementation()
{
    return GetNumPlayers() >= MinPlayers;   // 최소 플레이어 수 충족 시 자동 StartMatch
}
```

> **AGameModeBase vs AGameMode 결정**:
> - 단일 플레이어 / 협동 / 캐주얼 → **AGameModeBase** (Match State 불필요)
> - 멀티플레이어 매치 / 라운드 게임 → **AGameMode** (Match State 5종 흐름)

---

## 4. AGameStateBase — 모든 클라 복제 (7K)

### 4.1 핵심 멤버

```cpp
// GameStateBase.h:43 — 현재 GameMode 클래스 (Replicated)
UPROPERTY(Transient, BlueprintReadOnly, Category=GameState, ReplicatedUsing=OnRep_GameModeClass)
TSubclassOf<AGameModeBase> GameModeClass;

// GameStateBase.h:47 — 서버 측 GameMode 인스턴스 (서버 only)
TObjectPtr<AGameModeBase> AuthorityGameMode;

// GameStateBase.h:55 — 모든 PlayerState 배열 (자동 관리)
UPROPERTY(BlueprintReadOnly, Category=GameState)
TArray<TObjectPtr<APlayerState>> PlayerArray;
```

### 4.2 ServerWorldTimeSeconds (네트워크 동기 시간)

```cpp
// GameStateBase.h:72 — 서버 시간 (모든 클라 동기)
ENGINE_API virtual double GetServerWorldTimeSeconds() const;

// 클라 측 — 서버와의 차이 자동 계산
float ServerWorldTimeSecondsDelta;   // 클라 World Time - 서버 World Time
```

> **사용 케이스**: 서버 측 매치 타이머 표시 / 동기된 애니메이션 시간 / 네트워크 lag 감지.

```cpp
// 매치 타이머 표시 (모든 클라 동일)
double ServerTime = GameState->GetServerWorldTimeSeconds();
double ElapsedTime = ServerTime - MatchStartTime;
double Remaining = MatchDuration - ElapsedTime;
```

### 4.3 PlayerArray 관리 (자동)

```cpp
// GameStateBase.h:111
ENGINE_API virtual void AddPlayerState(APlayerState* PlayerState);

// GameStateBase.h:114
ENGINE_API virtual void RemovePlayerState(APlayerState* PlayerState);

// HasBegunPlay — 모든 클라 동기
ENGINE_API virtual bool HasBegunPlay() const;
{
    // 서버 = bReplicatedHasBegunPlay
    // 클라 = OnRep_ReplicatedHasBegunPlay 콜백 후 true
}
```

### 4.4 표준 사용 패턴

```cpp
// 모든 PlayerState 순회 (서버 + 클라 모두 — 복제됨)
for (auto* PS : GameState->PlayerArray)
{
    if (auto* MyPS = Cast<AMyPlayerState>(PS))
    {
        // 점수 합산 / 팀별 순위 등
    }
}

// HasBegunPlay 검사 — Actor BeginPlay 보장 시점
if (auto* GS = GetWorld()->GetGameState())
{
    if (GS->HasBegunPlay())
    {
        // 모든 Actor 들의 BeginPlay 완료
    }
}
```

---

## 5. AGameState — Match State 복제 (3K)

```cpp
// GameState.h — Match State 추가
UPROPERTY(ReplicatedUsing=OnRep_MatchState)
FName MatchState;

UPROPERTY(Replicated)
float MatchStartTime;     // 매치 시작 시간 (Server World Time)

// 클라 측 콜백
virtual void OnRep_MatchState();
{
    // HandleMatchIsWaitingToStart / HandleMatchHasStarted / HandleMatchHasEnded 호출
}
```

> **AGameStateBase vs AGameState** = AGameModeBase vs AGameMode 페어. **Match State 사용 시 둘 다 GameMode/GameState 변형 사용 의무**.

---

## 6. APlayerState — 개별 플레이어 (16K)

### 6.1 핵심 멤버

```cpp
// PlayerState.h:48 — 점수 (자동 복제 + OnRep)
UPROPERTY(ReplicatedUsing=OnRep_Score)
float Score;

// PlayerState.h:73 — Spectator 여부
UPROPERTY(ReplicatedUsing=OnRep_bIsSpectator)
uint8 bIsSpectator:1;

// PlayerState.h:115 — UniqueNetId (Online Subsystem)
UPROPERTY(ReplicatedUsing=OnRep_UniqueId)
FUniqueNetIdRepl UniqueId;

// PlayerState.h:161 — 플레이어 이름 (private — Setter 사용)
UPROPERTY(ReplicatedUsing=OnRep_PlayerName)
FString PlayerNamePrivate;

// PlayerState.h:225 — 이름 설정 (서버 only)
ENGINE_API virtual void SetPlayerName(const FString& S);

// PlayerState.h:232 — 이름 조회
ENGINE_API FString GetPlayerName() const;
```

### 6.2 자식 PlayerState 작성 패턴

```cpp
// MyPlayerState.h
UCLASS()
class AMyPlayerState : public APlayerState
{
    GENERATED_BODY()
public:
    UPROPERTY(ReplicatedUsing=OnRep_TeamIndex)
    int32 TeamIndex = 0;

    UPROPERTY(Replicated)
    int32 Kills = 0;

    UPROPERTY(Replicated)
    int32 Deaths = 0;

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    UFUNCTION()
    void OnRep_TeamIndex();

    // SeamlessTravel 시 데이터 이전
    virtual void CopyProperties(APlayerState* PlayerState) override;
};

// MyPlayerState.cpp
void AMyPlayerState::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
    DOREPLIFETIME(AMyPlayerState, TeamIndex);
    DOREPLIFETIME(AMyPlayerState, Kills);
    DOREPLIFETIME(AMyPlayerState, Deaths);
}

void AMyPlayerState::CopyProperties(APlayerState* PlayerState)
{
    Super::CopyProperties(PlayerState);   // 베이스 데이터 복사 (Score / PlayerName / UniqueId)
    if (auto* NewMyPS = Cast<AMyPlayerState>(PlayerState))
    {
        NewMyPS->TeamIndex = TeamIndex;
        NewMyPS->Kills = Kills;
        NewMyPS->Deaths = Deaths;
    }
}
```

> **CopyProperties** = **SeamlessTravel 안 PlayerState 데이터 이전 표준** — 베이스 호출 후 자식 데이터 복사.

---

## 7. SeamlessTravel 흐름 (멀티플레이 맵 전환)

```
[Server]
1. ServerTravel(NewMapURL, /*bSeamless=*/true)
2. UWorld::SeamlessTravel(NewMapURL)
3. UGameInstance::PreSeamlessTravel + LoadingScreen
4. Transition Map (`Transition.umap`) 로드 — 짧은 빈 맵
5. NewMap 비동기 로드 — Streaming
6. AGameModeBase::HandleSeamlessTravelPlayer(C) ── 각 PlayerController 처리
   ↓ NewPC = SpawnPlayerController(InRemoteRole, Loc, Rot, NewClass)
   ↓ OldPC->SeamlessTravelTo(NewPC)             ── (이전 PC) 데이터 이전 트리거
   ↓ NewPC->SeamlessTravelFrom(OldPC)            ── (새 PC) 데이터 받기
   ↓ NewPS->CopyProperties(OldPS)                 ── PlayerState 복사
7. AGameModeBase::PostSeamlessTravel
8. 모든 PC->PostSeamlessTravel
9. 정상 게임플레이 재개
```

```cpp
// MyGameMode 측 — 살아남는 Actor 명시
void AMyGameMode::HandleSeamlessTravelPlayer(AController*& C)
{
    Super::HandleSeamlessTravelPlayer(C);   // 베이스가 PC + PS 처리
    // 추가 셋업 — 새 PC 측에서 점수 복원 등
}
```

> **SeamlessTravel 의 장점**: 클라이언트 연결 끊김 없음 + 데이터 이전 가능. **단점**: 메모리 2배 (이전 + 새 World 모두 일시 보유). **Transition Map 사용** 으로 메모리 피크 회피.

---

## 8. 🎯 최적화 방안

### 8.1 GameMode Tick 비활성

```cpp
AMyGameMode::AMyGameMode()
{
    PrimaryActorTick.bCanEverTick = false;   // Match 흐름은 Timer 기반
}

// 매치 타이머 — Tick 대신 GetWorld()->GetTimerManager()
GetWorld()->GetTimerManager().SetTimer(MatchTimer, this, &AMyGameMode::OnMatchTick, 1.f, true);
```

### 8.2 PlayerArray 순회 최적화 (자주 사용)

```cpp
// 매 프레임 PlayerArray 순회 = 안티패턴
// 대신 Cached score sum + RepNotify 갱신
void AMyPlayerState::OnRep_Score()
{
    // 점수 변경될 때만 GameState 의 TotalScore 갱신
    GetWorld()->GetGameState<AMyGameState>()->RebuildScoreboard();
}
```

### 8.3 SeamlessTravel 메모리 피크 회피

```ini
; DefaultEngine.ini
[/Script/Engine.GameMapsSettings]
TransitionMap=/Game/Maps/Transition

; Transition Map = 빈 맵 — 메모리 최소
```

### 8.4 PlayerState Replication 빈도 조정

```cpp
// MyPlayerState Constructor
SetNetUpdateFrequency(2.f);    // 점수는 자주 갱신 안 함 (2Hz)
```

---

## 9. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | GameMode 클라에서 접근 | ⚠️ Server only — `GetWorld()->GetAuthGameMode()` 는 클라에서 nullptr |
| 2 | GameMode Tick 사용 + 매 프레임 PlayerArray 순회 | Timer + RepNotify 갱신 패턴 |
| 3 | `bUseSeamlessTravel = true` 안 했는데 SeamlessTravel 호출 | 무시됨 — DefaultEngine.ini 또는 코드에서 설정 의무 |
| 4 | PlayerState 데이터 SeamlessTravel 후 손실 | `CopyProperties` override + Super 처음 호출 의무 |
| 5 | InitGame 안에서 GameState 접근 | ⚠️ GameState 아직 nullptr — `InitGameState` 또는 `StartPlay` 사용 |
| 6 | Match State 변경을 SetMatchState 직접 호출 | `StartMatch` / `EndMatch` / `AbortMatch` 사용 — Handler 자동 호출 |
| 7 | PlayerName 직접 PlayerNamePrivate = "..." | private — `SetPlayerName(S)` 사용 (서버 only) |
| 8 | DefaultPawnClass = nullptr 일 때 RestartPlayer | Pawn Spawn 실패 — Default 검사 / `ADefaultPawn` 폴백 |
| 9 | 🚨 InitGame / PostLogin / Logout 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 ([`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)) |
| 10 | 🚨 `TActorIterator<APlayerStart>` 매 RestartPlayer 호출 | GameMode 가 등록 패턴 사용 — `CacheLevelSavedPlayerStarts()` BeginPlay 1회 캐싱 |

---

## 10. 체크리스트 (GameMode 자식 작성 시)

- [ ] Constructor: 클래스 슬롯 6종 명시 (DefaultPawnClass / PlayerControllerClass / GameStateClass / PlayerStateClass / HUDClass / SpectatorClass)
- [ ] Constructor: `PrimaryActorTick.bCanEverTick = false`
- [ ] InitGame: Super 처음 + URL 옵션 파싱 + `TRACE_CPUPROFILER_EVENT_SCOPE`
- [ ] PostLogin: Super 처음 + 캐싱 + 매치 시작 조건 검사
- [ ] Logout: Super 마지막 + PlayerState 정리
- [ ] HandleSeamlessTravelPlayer: Super 처음 + 추가 셋업
- [ ] AGameMode 자식: HandleMatchHasStarted / HandleMatchHasEnded override + Super 처음
- [ ] AGameStateBase 자식: PlayerArray 순회 = Tick 아닌 RepNotify 갱신
- [ ] APlayerState 자식: `CopyProperties` override + Super 처음 + 자식 데이터 복사
- [ ] DefaultEngine.ini: `[/Script/Engine.GameMode]` 또는 BP DefaultGameMode 설정
- [ ] DefaultEngine.ini: `bUseSeamlessTravel = true` (필요 시)
- [ ] DefaultEngine.ini: `TransitionMap` 설정 (SeamlessTravel 메모리 피크 회피)
- [ ] 🚨 6대 정책 만족 ([`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md))

---

## 11. 관련 sub-skill

- [`GameFramework/Actor`](../Actor/SKILL.md) — 베이스 (GameMode → AInfo → Actor)
- [`GameFramework/Controller`](../Controller/SKILL.md) — Spawn 진입점 (SpawnPlayerController) + SeamlessTravel 페어
- [`GameFramework/PawnCharacter`](../PawnCharacter/SKILL.md) — DefaultPawnClass + RestartPlayer 흐름
- [`GameFramework/GameInstance`](../GameInstance/SKILL.md) — PreSeamlessTravel / LoadingScreen
- [`GameFramework/World`](../World/SKILL.md) — UWorld::Listen / ServerTravel / SeamlessTravel
- [`CoreUObject/Network`](../../CoreUObject/references/Network.md) — DOREPLIFETIME / RepNotify / RPC
- 교차: 🚨 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) · 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) · 🚨 [`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md)

---

## 12. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. AGameModeBase 672 lines (클래스 슬롯 6종 / InitGame / InitGameState / StartPlay / PostLogin / Logout / RestartPlayer / FindPlayerStart / SpawnDefaultPawnFor / HandleSeamlessTravelPlayer). AGameMode 11K (Match State 5종 EnteringMap/Wa