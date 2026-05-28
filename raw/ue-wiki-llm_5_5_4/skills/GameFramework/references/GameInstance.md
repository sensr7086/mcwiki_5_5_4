---
name: gameframework-gameinstance
description: UGameInstance (676 lines) - 영속 세션 + Subsystem 4종 (Engine/GameInstance/World/LocalPlayer) + Init/Shutdown + LoadingScreen.
---

# GameFramework/GameInstance — UGameInstance + GameInstanceSubsystem

> **위치**: `Engine/Source/Runtime/Engine/Classes/Engine/GameInstance.h` (676 lines)
> **베이스**: `UGameInstance : public UObject`
> **요지**: **게임 전체 라이프사이클을 가로지르는 유일한 객체** — World/Map 전환 시 살아남음. 세션 영속 데이터 (LocalPlayer / Online Session / 설정값) + GameInstanceSubsystem 자동 관리.

---

## 🚨 공통 정책 (Components 6대 의무 + GameInstance 특화)

| # | 정책 | GameInstance 적용 |
|---|------|------------------|
| 1 | **Mobility** | UObject — Mobility 무관 (Actor 아님). |
| 2 | **NewObject + DuplicateObject** | Engine 이 자동 생성 — `GEngine->CreateGameInstance(...)` 1회만. **사용자가 직접 NewObject 절대 금지**. DefaultEngine.ini `[/Script/EngineSettings.GameMapsSettings] GameInstanceClass=...` 에서 클래스 지정. |
| 3 | **GC 방어** | `UPROPERTY()` + `TObjectPtr<>` — Engine 이 GameInstance 자체를 강참조. 멤버는 표준 GC 규칙. |
| 4 | **Cached References** | `GetGameInstance<T>()` — World / Subsystem / Component 어디서든 호출 비용 0 (Engine 캐싱). 캐싱 불필요. |
| 5 | **PrimaryActorTick** | UObject — Tick 없음. 매 프레임 갱신 필요 시 `FTSTicker` 또는 `WorldSubsystem` 사용. |
| 6 | **CDO + 자동 생성** | Engine 이 자동 — Constructor 안 World 의존 데이터 접근 금지 (GameInstance Init 전 World nullptr). `Init()` 에서 처리. |
| 🎯 **어셋 로드** | 🚨 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) — **🔥 GameInstance 가 글로벌 PreLoad 진입점**. **`Init()`** 안에서 `UAssetManager::Get().ScanPathForPrimaryAssets()` Primary Asset Type 등록 + 게임 전체 영속 어셋 (UI / 글로벌 매니저 / Save 데이터) PreLoad. **GameInstanceSubsystem = 영속 데이터** (Map 전환 살아남음) — Map 전환 시 GC 안 됨. **큰 자산은 보유 X** (FSoftObjectPath 만 보유 + 사용 직전 Async). DefaultEngine.ini `[/Script/Engine.AssetManagerSettings]` PrimaryAssetTypesToScan 자동 스캔 등록. |

---

## 1. 라이프사이클 (가장 중요 — Map 전환 시 살아남음)

```
[프로세스 시작]
1. UEngine::Init()
2. UGameInstance Constructor                      ── CDO + 인스턴스 생성
3. UGameInstance::Init()                          ── 1회만 호출 — 영속 데이터 셋업
4. UGameInstance::StartGameInstance()             ── 첫 맵 로드 + StartGame
5. (UWorld::BeginPlay → GameMode 등 로드)

[Map 전환 — ServerTravel / ClientTravel / SeamlessTravel]
   ↓ UWorld 새 인스턴스 생성 / 이전 World GC
   ↓ ⚠️ GameInstance 는 그대로 — 데이터 영속

[프로세스 종료]
N-1. UGameInstance::Shutdown()                    ── 정리
N. (Engine 종료)
```

> **🔑 핵심**: **`Init()` / `Shutdown()` 은 1회만 호출**. World/맵 전환 시 모든 Actor / Component 는 destroy 되지만 GameInstance 는 살아남음 — **세션 영속 데이터의 유일한 안전한 저장소**.

### 1.1 라이프사이클 진입점

```cpp
// GameInstance.h:217 — 1회만 호출 (Engine 시작 시)
ENGINE_API virtual void Init();

// GameInstance.h:224 — 1회만 호출 (Engine 종료 시)
ENGINE_API virtual void Shutdown();

// GameInstance.h:301 — 첫 맵 로드 + 시작
ENGINE_API virtual void StartGameInstance();
```

```cpp
// MyGameInstance.cpp
void UMyGameInstance::Init()
{
    Super::Init();                            // ⚠️ 처음
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyGameInstance::Init);

    // 영속 데이터 로드 (Save Game / 설정 / Online Session)
    LoadSavedGame();

    // Online Subsystem 진입점
    if (auto* OS = IOnlineSubsystem::Get())
    {
        OS->GetSessionInterface()->AddOnSessionUserInviteAcceptedDelegate_Handle(
            FOnSessionUserInviteAcceptedDelegate::CreateUObject(this, &UMyGameInstance::OnSessionInviteAccepted));
    }

    // Network Failure 핸들러
    GEngine->OnNetworkFailure().AddUObject(this, &UMyGameInstance::HandleNetworkError);
}

void UMyGameInstance::Shutdown()
{
    // 정리 작업 먼저 — Save / Logout 등
    SaveGame();
    Super::Shutdown();                         // ⚠️ 마지막
}
```

---

## 2. LocalPlayer 관리 (Split Screen / Couch Co-op)

```cpp
// GameInstance.h:173 — 모든 LocalPlayer 배열
UPROPERTY()
TArray<TObjectPtr<ULocalPlayer>> LocalPlayers;

// GameInstance.h:335 — 새 LocalPlayer 추가 (Couch Co-op)
ENGINE_API ULocalPlayer* CreateLocalPlayer(int32 ControllerId, FString& OutError, bool bSpawnPlayerController);

// GameInstance.h:362
ENGINE_API int32 GetNumLocalPlayers() const;

// GameInstance.h:368 — 첫 LocalPlayer (가장 흔함)
ENGINE_API ULocalPlayer* GetFirstGamePlayer() const;

// GameInstance.h:371 — 첫 LocalPlayer 의 PlayerController
ENGINE_API APlayerController* GetFirstLocalPlayerController(const UWorld* World = nullptr) const;
```

```cpp
// 2번째 플레이어 추가 (Couch Co-op)
void UMyGameInstance::AddSecondPlayer()
{
    FString Error;
    ULocalPlayer* NewLP = CreateLocalPlayer(/*ControllerId=*/1, Error, /*bSpawnPC=*/true);
    if (!NewLP)
    {
        UE_LOG(LogTemp, Warning, TEXT("Failed: %s"), *Error);
    }
}

// LocalPlayer 추가/제거 이벤트
FOnLocalPlayerEvent OnLocalPlayerAddedEvent;
FOnLocalPlayerEvent OnLocalPlayerRemovedEvent;
```

---

## 3. UGameInstanceSubsystem (가장 중요한 패턴)

> **`UGameInstance` 의 라이프사이클 동안 살아있는 자동 관리 객체** — Manager / Service / Cache 패턴 표준.

### 3.1 베이스 클래스 + 자동 생성

```cpp
// MySaveSubsystem.h
#include "Subsystems/GameInstanceSubsystem.h"

UCLASS()
class UMySaveSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    UFUNCTION(BlueprintCallable)
    void SaveGame();

    UFUNCTION(BlueprintCallable)
    void LoadGame();
};

// MySaveSubsystem.cpp
void UMySaveSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    TRACE_CPUPROFILER_EVENT_SCOPE(UMySaveSubsystem::Initialize);
    // GameInstance::Init 직후 자동 호출 — 1회만
}

void UMySaveSubsystem::Deinitialize()
{
    // Shutdown 직전 자동 호출
    Super::Deinitialize();
}
```

### 3.2 사용 (어디서든 GetSubsystem)

```cpp
// 어디서든
UMySaveSubsystem* SaveSys = GetGameInstance()->GetSubsystem<UMySaveSubsystem>();
UMySaveSubsystem* SaveSys2 = UGameInstance::GetSubsystem<UMySaveSubsystem>(GetWorld()->GetGameInstance());

// World/Actor 안에서
UMySaveSubsystem* SaveSys3 = GetWorld()->GetGameInstance()->GetSubsystem<UMySaveSubsystem>();
```

### 3.3 Subsystem 5종 비교 — [`Subsystem/SKILL.md`](../../Subsystem/SKILL.md) ✂️

> **5종 통합 매트릭스 + 결정 트리 + 작성 표준 패턴 + 함정 10종 = [`skills/Subsystem/SKILL.md`](../../Subsystem/SKILL.md)** 참조.
>
> 본 sub-skill 은 **UGameInstanceSubsystem** 깊이 (Save / Online Session / 설정값 — Map 전환 살아남음) 만 다룸. 다른 베이스 (Engine / World / LocalPlayer / Editor) 는 통합 가이드 참조.

### 3.4 Subsystem 패턴의 장점 (전역 이터레이터 회피)

```cpp
// ❌ 안티패턴 — 매 호출마다 N개 Actor 순회
TActorIterator<AMyManager> It(GetWorld());
AMyManager* Mgr = It ? *It : nullptr;

// ✅ 정답 — Subsystem 패턴 (등록 1회 / 검색 비용 0)
UMyManagerSubsystem* Mgr = GetGameInstance()->GetSubsystem<UMyManagerSubsystem>();
```

> **자세한 등록 패턴 = [`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md)** — Subsystem 우선 사용 정책.

---

## 4. Online Session 진입점

```cpp
// GameInstance.h:302/303 — Join Session (Online Subsystem)
virtual bool JoinSession(ULocalPlayer* LocalPlayer, int32 SessionIndexInSearchResults) { return false; }
virtual bool JoinSession(ULocalPlayer* LocalPlayer, const FOnlineSessionSearchResult& SearchResult) { return false; }
```

> **OnlineSubsystem 진입점 — 자식 GameInstance 가 override 하여 Steam / EOS / Discord / 자체 백엔드 통합**.

---

## 5. Network Failure 핸들러

```cpp
// GameInstance.h:264 — 네트워크 오류 처리
ENGINE_API void HandleNetworkError(ENetworkFailure::Type FailureType, bool bIsServer);
```

```cpp
// 오류 시 메인 메뉴로 복귀
void UMyGameInstance::HandleNetworkError(ENetworkFailure::Type FailureType, bool bIsServer)
{
    UE_LOG(LogTemp, Error, TEXT("Network failure: %s"), ToCString(FailureType));

    // PendingNetGame 정리 + Main Menu 로 ClientTravel
    if (auto* PC = GetFirstLocalPlayerController())
    {
        PC->ClientTravel(TEXT("/Game/Maps/MainMenu"), ETravelType::TRAVEL_Absolute);
    }
}
```

### ENetworkFailure 종류

| 종류 | 의미 |
|------|------|
| `ConnectionLost` | 연결 끊김 |
| `ConnectionTimeout` | 시간 초과 |
| `FailureReceived` | 일반 오류 |
| `OutdatedClient` / `OutdatedServer` | 버전 불일치 |
| `PendingConnectionFailure` | Pending 단계 실패 |
| `NetGuidMismatch` | NetGUID 불일치 |
| `NetChecksumMismatch` | 체크섬 불일치 |

---

## 6. WorldContext (싱글 vs PIE 다중 World)

```cpp
// GameInstance.h:294
struct FWorldContext* GetWorldContext() const { return WorldContext; }
```

> **PIE (Play In Editor)** 시 — 여러 GameInstance + WorldContext 동시 — 각자 별개 World. **Standalone Game** = 1개 GameInstance + 1개 WorldContext.

```cpp
// 현재 GameInstance 의 World
UWorld* World = GetWorld();   // GameInstance->GetWorldContext()->World()
```

---

## 7. SeamlessTravel 통합

```cpp
// GameInstance.h:281
ENGINE_API virtual void HandleSeamlessTravelPlayer(AController*& C);
{
    // GameMode 가 처리 — GameInstance 측 추가 셋업 가능
}

// 자식 override — 데이터 이전
void UMyGameInstance::HandleSeamlessTravelPlayer(AController*& C)
{
    Super::HandleSeamlessTravelPlayer(C);
    // 추가 셋업 — 클라 측 데이터
}
```

> **자세한 SeamlessTravel = [`GameMode §7`](../GameMode/SKILL.md)**.

---

## 8. 🎯 최적화 방안

### 8.1 Subsystem 패턴 (가장 큰 최적화)

> **모든 글로벌 Manager 는 Subsystem 으로** — 전역 이터레이터 회피 + 자동 라이프사이클 + GC 안전.

```cpp
// AI 매니저 / 음악 매니저 / Save 매니저 / 설정 매니저 등
GetGameInstance()->GetSubsystem<UMySubsystem>();   // O(1) 검색
```

### 8.2 Map 전환 시 메모리 관리

```cpp
// 영속 데이터만 GameInstance 에 저장 — 큰 자산은 GameInstance 에 보유 X
UCLASS()
class UMyGameInstance : public UGameInstance
{
    UPROPERTY()
    FPlayerSavedData SavedData;        // 작은 데이터만 (점수 / 인벤토리 등)

    // ❌ 큰 자산 보유 금지 — Map 전환 시 GC 안 됨 → 메모리 누적
    // UPROPERTY() TObjectPtr<UTexture2D> BigCachedTexture;   // 안티패턴

    // ✅ 정답 — 자산은 Map 안에 두고 SoftPath 만 보유
    UPROPERTY()
    FSoftObjectPath CachedTexturePath;
};
```

### 8.3 PreSeamlessTravel + LoadingScreen

```cpp
// SeamlessTravel 직전 LoadingScreen 표시
void UMyGameInstance::PreSeamlessTravel()
{
    Super::PreSeamlessTravel();
    if (auto* LoadingScreen = GetSubsystem<ULoadingScreenSubsystem>())
    {
        LoadingScreen->Show();
    }
}
```

### 8.4 Online Session 비동기 처리

```cpp
// JoinSession 은 비동기 — 콜백으로 처리
SessionInterface->OnJoinSessionCompleteDelegate.AddUObject(this, &UMyGameInstance::OnJoinSessionComplete);
SessionInterface->JoinSession(LocalPlayer->GetUniqueNetIdForPlatformUser(), SessionName, SearchResult);

void UMyGameInstance::OnJoinSessionComplete(FName SessionName, EOnJoinSessionCompleteResult::Type Result)
{
    // 완료 후 ClientTravel
}
```

---

## 9. 함정 & 안티패턴 (8종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | `Constructor` 안 World / Map 데이터 접근 | nullptr — `Init()` 에서 처리 |
| 2 | Init / Shutdown 매 Map 전환마다 호출될 거라 가정 | 1회만 — 영속 셋업은 Init / 매 Map = `WorldSubsystem` |
| 3 | 큰 자산 (Texture / Mesh) GameInstance 에 보유 | Map 전환 시 GC 안 됨 → 누적. SoftPath 만 보유 |
| 4 | Subsystem 안 만들고 Manager Actor 사용 + TActorIterator 검색 | Subsystem 패턴 — O(1) 검색 + 자동 라이프사이클 |
| 5 | `WorldSubsystem` 으로 영속 데이터 보유 | World 마다 재생성 → 데이터 손실. `GameInstanceSubsystem` 사용 |
| 6 | `GetGameInstance()` 결과 캐싱 | inline + 비용 0 — 캐싱 불필요. 매번 호출 OK |
| 7 | DefaultEngine.ini `GameInstanceClass` 지정 안 함 | UGameInstance 베이스 — 자식 클래스 지정 필요 |
| 8 | 🚨 Init / Shutdown / 콜백 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 ([`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)) |

---

## 10. 체크리스트

- [ ] DefaultEngine.ini: `[/Script/EngineSettings.GameMapsSettings] GameInstanceClass=...` 설정
- [ ] Init: Super 처음 + 영속 데이터 로드 + Online Subsystem 진입점 + `TRACE_CPUPROFILER_EVENT_SCOPE`
- [ ] Shutdown: Save + Online Logout 후 Super 마지막
- [ ] Manager / Service / Cache → `UGameInstanceSubsystem` 자식
- [ ] 영속 데이터만 보유 — 큰 자산은 SoftPath
- [ ] Network Failure 핸들러 등록 — Map 복귀
- [ ] 🚨 6대 정책 만족 ([`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md))

---

## 11. 관련 sub-skill

- [`GameFramework/World`](../World/SKILL.md) — UWorld + WorldSubsystem (Map 단위)
- [`GameFramework/GameMode`](../GameMode/SKILL.md) — GameMode 가 GameInstance 안에서 SeamlessTravel
- [`GameFramework/Controller`](../Controller/SKILL.md) — LocalPlayer / GetFirstLocalPlayerController
- [`UnrealEd/Subsystems`](../../UnrealEd/Subsystems/SKILL.md) — Subsystem 패턴 통합
- [`CoreUObject/UObject`](../../CoreUObject/references/UObject.md) — UObject 베이스
- 교차: 🚨 [`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md) (Subsystem 등록 패턴) · 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)

---

## 12. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05