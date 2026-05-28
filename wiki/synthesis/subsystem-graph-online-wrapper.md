---
type: synthesis
title: "Subsystem 그래프 + Online (Steam/EOS) Wrapper — Cycle Detection + IOnlineSubsystem 통합"
slug: subsystem-graph-online-wrapper
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/ue-subsystem-skill]]"
  - "[[sources/ue-subsystem-onlinesubsystem]]"
  - "[[sources/ue-gameframework-gameinstance]]"
entities:
  - "[[entities/USubsystem]]"
  - "[[entities/UGameInstance]]"
  - "[[entities/UEngineSubsystem]]"
concepts:
  - "[[concepts/Subsystem-5-Types]]"
  - "[[concepts/MC-Asset-Validation-Policy]]"
status: living
tags: [synthesis, subsystem, online, steam, eos, dependency]
---

# Subsystem 그래프 + Online (Steam/EOS) Wrapper

## 1. Thesis

[[synthesis/subsystem-advanced-patterns]] §4 의 `InitializeDependency<T>()` 는 Subsystem 간 의존 그래프를 형성한다. 그래프는 *위상 정렬 가능한 DAG* 여야 — cycle 발생 시 ensure 발화 + 게임 시작 안 됨. 본 synthesis 는 **(1) 의존 그래프 visualization + cycle detection 도구화 / (2) IOnlineSubsystem (Steam/EOS/PSN) 의 GameInstance Subsystem wrapper 표준 패턴 — 외부 SDK 의 5번째 Subsystem 위치**. [[sources/ue-subsystem-onlinesubsystem]] 의 wrapper 권장 + 멀티 SDK 분기 (Steam vs EOS) + 함정.

## 2. 의존 그래프 — Cycle Detection

UE 자체는 cycle 발생 시 ensure → false 반환 → 의존 무한 재귀 차단. 사용자 진단 도구:

```cpp
// 디버그 콘솔 명령 — Subsystem 그래프 dump
static FAutoConsoleCommand DumpSubsystemGraph(
    TEXT("MC.DumpSubsystemGraph"), TEXT("Subsystem dependency graph"),
    FConsoleCommandDelegate::CreateLambda([](){
        if (UGameInstance* GI = GEngine->GetWorldFromContextObjectChecked(GWorld)->GetGameInstance()) {
            const TArray<UGameInstanceSubsystem*>& Subs = GI->GetSubsystemArrayCopy<UGameInstanceSubsystem>();
            for (UGameInstanceSubsystem* S : Subs) {
                UE_LOG(LogMCAsset, Log, TEXT("  Subsystem: %s"), *S->GetName());
                // 의존 정보는 private — 시각화는 InitializeDependency 호출을 hook
            }
        }
    }));
```

UE 가 의존 그래프를 *공식 dump API* 안 줌 — 사용자는 *자신의 Subsystem 의 Initialize 안에서 InitializeDependency 호출 의도를 주석 / 디자인 문서로 보존*. 그래프 도구화는 Editor plugin 으로 `IModuleInterface::StartupModule` 시점에 수집 — 별도 노트 (열린).

## 3. Online Subsystem Wrapper 표준

`IOnlineSubsystem` 은 USubsystem 아님 — 자체 Plugin. GameInstance Subsystem wrapper 권장:

```cpp
UCLASS()
class UMCOnlineSubsystem : public UGameInstanceSubsystem
{
    IOnlineSubsystem* OnlineSub = nullptr;   // C++ 포인터 (UObject 아님)
    IOnlineSessionPtr SessionInterface;
    IOnlineFriendsPtr FriendsInterface;

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override
    {
        Super::Initialize(Collection);
        // SDK 자동 감지 — Project Settings 의 [OnlineSubsystem] 가 결정
        OnlineSub = IOnlineSubsystem::Get();   // Steam / EOS / Null
        MC_LOGRET_IF_NULL(OnlineSub, "No OnlineSubsystem available — running NULL");
        SessionInterface = OnlineSub->GetSessionInterface();
        FriendsInterface = OnlineSub->GetFriendsInterface();
    }

    virtual void Deinitialize() override
    {
        SessionInterface.Reset();
        FriendsInterface.Reset();
        OnlineSub = nullptr;
        Super::Deinitialize();
    }

    UFUNCTION(BlueprintCallable) bool CreateSession(...);
    UFUNCTION(BlueprintCallable) bool JoinSession(...);
    UFUNCTION(BlueprintCallable) void GetFriends(TArray<FOnlineFriendInfo>& OutFriends);
};
```

**왜 wrapper?** — `IOnlineSubsystem` 의 *C++ 포인터 / 인터페이스 호출* 을 BP 노출. BP 가 직접 `IOnlineSubsystem::Get()` 호출 못 함.

## 4. Multi-SDK 분기 (Steam vs EOS vs PSN)

`DefaultEngine.ini`:
```ini
[OnlineSubsystem]
DefaultPlatformService=Steam   ; 또는 EOS / PSN / Null

[OnlineSubsystemSteam]
bEnabled=true
SteamDevAppId=480              ; Spacewar test ID

[OnlineSubsystemEOS]
bEnabled=false
ProductId=...
```

런타임에 어느 SDK 인지 식별:

```cpp
const FName SubsystemName = OnlineSub->GetSubsystemName();
// FName("STEAM") / FName("EOS") / FName("NULL")
if (SubsystemName == FName("STEAM")) {
    // Steam 전용 코드 (Steam Achievement 등)
} else if (SubsystemName == FName("EOS")) {
    // EOS 전용 (Crossplay)
}
```

플랫폼별 Online Wrapper 분기:

```cpp
class UMCOnlineSubsystem : public UGameInstanceSubsystem
{
    virtual bool ShouldCreateSubsystem(UObject* Outer) const override
    {
#if PLATFORM_PS5 || PLATFORM_XBOXONE
        return false;  // 콘솔은 별도 Plugin (PSN / Xbox Live SDK)
#else
        return Super::ShouldCreateSubsystem(Outer);
#endif
    }
};

class UMCConsoleOnlineSubsystem : public UGameInstanceSubsystem
{
    virtual bool ShouldCreateSubsystem(UObject* Outer) const override
    {
#if PLATFORM_PS5 || PLATFORM_XBOXONE
        return Super::ShouldCreateSubsystem(Outer);
#else
        return false;
#endif
    }
};
```

[[synthesis/subsystem-advanced-patterns]] §3 의 `ShouldCreateSubsystem` 빌드별 분기와 결합.

## 5. 의존 패턴 — `UMCSaveLoad` → `UMCOnlineSubsystem` → `UMCAchievement`

```cpp
// SaveLoad 가 Online 에 의존 (Cloud Save 활용)
class UMCSaveLoad : public UGameInstanceSubsystem
{
    virtual void Initialize(FSubsystemCollectionBase& Collection) override
    {
        Collection.InitializeDependency<UMCOnlineSubsystem>();
        Super::Initialize(Collection);
    }
};

// Achievement 도 Online 에 의존
class UMCAchievement : public UGameInstanceSubsystem
{
    virtual void Initialize(FSubsystemCollectionBase& Collection) override
    {
        Collection.InitializeDependency<UMCOnlineSubsystem>();
        Super::Initialize(Collection);
    }
};

// 그래프:
// UMCOnlineSubsystem (root, 의존 없음)
//      ↑                    ↑
// UMCSaveLoad        UMCAchievement
```

cycle 검증: `UMCOnlineSubsystem` 이 `UMCSaveLoad` 에 의존하면 cycle → ensure.

## 6. 함정 / 열린 질문

- [ ] **OnlineSubsystem null fallback** — `bEnabled=false` 인 SDK 가 디폴트면 `IOnlineSubsystem::Get()` 가 NULL 인스턴스 반환 — Lobby/Friends 함수 모두 *fail*. wrapper 의 모든 함수가 `MC_LOGRET_IF_NULL(SessionInterface, ...)` 체크
- [ ] **Initialize 시점에 SDK 미초기화** — Steam/EOS 의 internal init 이 비동기. `OnlineSub->IsEnabled()` 검사 + 초기화 완료 콜백 (`OnInitComplete`)
- [ ] **Deinitialize 순서 — 역순** — Online 이 SaveLoad 보다 먼저 destroy 되면 SaveLoad 의 cleanup 에서 nullptr. UE 가 보장 — 하지만 사용자가 weak ptr 캐싱하면 무효 검사 의무
- [ ] **PIE 의 OnlineSubsystem** — Editor 가 `Null` Online 사용 (Steam/EOS test 안 함). Cooked Build 만 실제 SDK
- [ ] **Crossplay (Steam ↔ EOS)** — EOS 의 *Linked Account* 로 Steam User 가 EOS Lobby 참여. Multi-SDK wrapper 가 양쪽 핸들 보관 (열린)
- [ ] **GAS 와 Online 결합** — Multiplayer 매치 lobby 가 GAS Replicate Mode 결정 (Mixed vs Full). Lobby 종료 후 GameInstance Subsystem 의 데이터 cleanup ([[synthesis/gas-pawn-vs-playerstate-decision]])
- [ ] **Subsystem 그래프 시각화 도구** — Editor Plugin 으로 그래프 ASCII / Mermaid 자동 생성 — UE 자체 안 줌, 사용자 도구 (열린, [[synthesis/mc-validation-automation-tooling]] 와 결합)
- [ ] **Online Subsystem 의 Editor only 기능** — `IOnlineUserCloud` 의 *Cloud Save 검증 도구* 는 Editor 만. Build 분기 ([[concepts/Editor-Only-4-Tier-Separation]])

## 7. 관련

### Sources

[[sources/ue-subsystem-skill]] · [[sources/ue-subsystem-onlinesubsystem]] · [[sources/ue-gameframework-gameinstance]]

### Entities

[[entities/USubsystem]] · [[entities/UGameInstance]] · [[entities/UEngineSubsystem]]

### Concepts

[[concepts/Subsystem-5-Types]] · [[concepts/MC-Asset-Validation-Policy]]

### Related synthesis

[[synthesis/subsystem-advanced-patterns]] (Initialize / ShouldCreate 베이스) · [[synthesis/subsystem-5-types-decision-tree]] (5 종 결정) · [[synthesis/gas-pawn-vs-playerstate-decision]] (Lobby + GAS Replicate) · [[synthesis/online-crossplay-gas-lobby]] (Crossplay + GAS Lobby + 그래프 도구)
