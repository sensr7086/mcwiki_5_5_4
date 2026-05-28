---
type: synthesis
title: "Online Crossplay (Steam ↔ EOS) + GAS Online Lobby + Subsystem 그래프 시각화 도구"
slug: online-crossplay-gas-lobby
created: 2026-05-11
last_updated: 2026-05-11
sources:
  - "[[sources/ue-subsystem-onlinesubsystem]]"
  - "[[sources/ue-subsystem-skill]]"
  - "[[sources/ue-gas-skill]]"
  - "[[sources/ue-gameframework-gameinstance]]"
entities:
  - "[[entities/USubsystem]]"
  - "[[entities/UGameInstance]]"
  - "[[entities/UAbilitySystemComponent]]"
concepts:
  - "[[concepts/Subsystem-5-Types]]"
  - "[[concepts/SeamlessTravel]]"
status: living
tags: [synthesis, online, crossplay, steam, eos, gas, lobby]
---

# Online Crossplay + GAS Lobby + Subsystem 그래프 시각화

## 1. Thesis

[[synthesis/subsystem-graph-online-wrapper]] 의 3 미해결 — **Crossplay (Steam ↔ EOS Linked Account) / GAS Lobby (매치 전 ASC 셋업) / Subsystem 의존 그래프 시각화 도구** — 3 축. 핵심 — **(1) EOS 가 *cross-platform identity provider*, Steam 은 *플랫폼 한정* — wrapper 가 EOS 통일 + Steam Linked Account hint / (2) Lobby 단계는 매치 전 — PlayerState 모델 GAS 에서 ASC 가 *Lobby 동안* 능력 미부여, 매치 시작 시점에 한꺼번에 GiveAbility / (3) Subsystem 의존 그래프는 Editor 시각화 도구 — Editor only Plugin 으로 InitializeDependency 그래프 ASCII / Mermaid dump**.

## 2. (1) Crossplay Wrapper

```cpp
UCLASS()
class UMCCrossplaySubsystem : public UGameInstanceSubsystem
{
    IOnlineSubsystem* Primary = nullptr;     // EOS (cross-platform)
    IOnlineSubsystem* Platform = nullptr;    // Steam / PSN / Xbox (네이티브)

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override
    {
        Super::Initialize(Collection);
        Primary  = IOnlineSubsystem::Get(FName("EOS"));
        Platform = IOnlineSubsystem::Get();   // 디폴트 (DefaultPlatformService)
        MC_LOGRET_IF_NULL(Primary, "EOS Online Subsystem not configured");

        // EOS 에 Steam Linked Account 등록 — Steam 사용자가 EOS Lobby 참여 가능
        if (Platform && Platform->GetSubsystemName() == FName("STEAM")) {
            LinkSteamToEOS();
        }
    }

    void CreateCrossplayLobby(...) {
        IOnlineSessionPtr Session = Primary->GetSessionInterface();
        FOnlineSessionSettings Settings;
        Settings.bUsesPresence = true;
        Settings.bAllowJoinViaPresence = true;
        Settings.bIsLANMatch = false;
        // Crossplay 활성 — EOS 는 platform-agnostic
        Settings.Set(SETTING_CROSSPLAY, true, EOnlineDataAdvertisementType::ViaOnlineService);
        Session->CreateSession(/*HostingPlayerNum=*/0, NAME_GameSession, Settings);
    }

    void LinkSteamToEOS() {
        // EOS Connect API — Steam Session Ticket 으로 EOS Account Token 발급
        // (Steamworks SDK 호출 + EOS_Connect_LoginCallback)
    }
};
```

[[synthesis/subsystem-graph-online-wrapper]] §3 의 wrapper 패턴 확장 — 두 SDK 동시 보유.

## 3. (2) GAS Lobby — 매치 전 ASC 셋업

PlayerState 모델 GAS — Lobby 단계에서 ASC 는 *존재* 하지만 *능력은 미부여*:

```cpp
// AMyPlayerState — Lobby 진입 시점
void AMyPlayerState::BeginPlay()
{
    Super::BeginPlay();
    if (HasAuthority()) {
        // ASC 생성 (Ctor 에서 이미)
        // 그러나 능력 부여는 매치 시작까지 보류
        AbilitySystemComponent->ClearAllAbilities();
        AbilitySystemComponent->RemoveActiveGameplayEffectsByTag(FGameplayTagContainer::EmptyContainer);
    }
}

// AMyGameMode::HandleMatchHasStarted (Lobby → InProgress)
void AMyGameMode::HandleMatchHasStarted()
{
    Super::HandleMatchHasStarted();

    // 모든 PlayerState 에 능력 부여 — 매치 시작
    for (APlayerState* PS : GameState->PlayerArray) {
        if (auto* MyPS = Cast<AMyPlayerState>(PS)) {
            UAbilitySystemComponent* ASC = MyPS->GetAbilitySystemComponent();
            for (TSubclassOf<UGameplayAbility> Cls : DefaultAbilities) {
                ASC->GiveAbility(FGameplayAbilitySpec(Cls));
            }
        }
    }
}
```

[[synthesis/gas-advanced-runtime-patterns]] §4 의 스킬 swap 패턴과 결합 — Lobby 에서 *Character 선택* → 매치 시작 시 그 Character 의 능력 부여.

## 4. (3) Subsystem 의존 그래프 시각화 도구

Editor Plugin 형태로 InitializeDependency 그래프 ASCII / Mermaid dump:

```cpp
#if WITH_EDITOR
class FMCSubsystemGraphTool : public IModuleInterface
{
    // 모든 USubsystem 자손 클래스 검사 (TObjectIterator<UClass>)
    // CDO 의 Initialize 함수에서 InitializeDependency<T> 호출 패턴 정적 분석
    // → DAG 빌드 → Mermaid 출력

    static FString DumpAsMermaid()
    {
        FString Out = TEXT("graph TD\n");
        for (TObjectIterator<UClass> It; It; ++It) {
            UClass* Cls = *It;
            if (Cls->IsChildOf(USubsystem::StaticClass()) && !Cls->HasAnyClassFlags(CLASS_Abstract)) {
                // 의존 추출 — *어렵다* 왜냐하면 InitializeDependency 호출은 runtime
                // 대안: 사용자 정의 메타데이터 UCLASS(meta="DependsOn=UMCOnlineSubsystem")
                FString DependsOn = Cls->GetMetaData(TEXT("DependsOn"));
                if (!DependsOn.IsEmpty()) {
                    Out += FString::Printf(TEXT("    %s --> %s\n"), *DependsOn, *Cls->GetName());
                }
            }
        }
        return Out;
    }
};
#endif
```

또는 Editor Console 명령 — `MC.DumpSubsystemGraph` — Output Log 에 Mermaid 텍스트 출력 → 사용자가 mermaid.live 등에 붙여 시각화.

## 5. 결정 트리 — Crossplay 결정

```
게임 플레이어 베이스?
├── PC only (Steam) → IOnlineSubsystem::Get(FName("STEAM")) — wrapper 단일
├── PC + Console (Crossplay) → EOS Primary + Platform-specific Secondary
├── Mobile + PC (Crossplay) → EOS Primary (iOS Game Center / Google Play 는 platform-specific)
└── 콘솔만 (PSN / Xbox Live) → 플랫폼 SDK 직접 (EOS 옵션 — Sony / Microsoft 인증 필요)
```

## 6. 함정 / 열린 질문

- [ ] **EOS Linked Account 의 *초기 로그인 race*** — Steam Login + EOS Connect 두 비동기 — 둘 다 완료 후 GameMode StartMatch 가능. `OnLoginComplete` 두 콜백 모두 기다림
- [ ] **Crossplay Lobby 의 *Voice Chat*** — EOS Voice 사용 시 cross-platform. Steam Voice 는 Steam-only. wrapper 가 SDK 별 fallback
- [ ] **GAS Lobby 에서 능력 미부여 시 *UI 표시*** — Character 선택 화면 — ASC 가 비어있는 상태에서 Tooltip 의 능력 정보는 *DataAsset* 에서 가져옴. ASC 분리
- [ ] **Subsystem 그래프 시각화의 *런타임 의존 detection 한계*** — `InitializeDependency<T>` 가 코드 안 호출 — 정적 분석 어려움. 대안 메타데이터 (`UCLASS(meta="DependsOn=...")`) 또는 런타임 dump 후 cache
- [ ] **EOS Match Making + GameMode StartMatch race** — EOS 가 매칭 완료 보고 *전에* GameMode 가 StartMatch — 일부 플레이어 미도착. `WaitingToStart` 매치 상태로 차단
- [ ] **Cross-platform Save 의 EOS Player Data Storage vs Steam Cloud** — EOS 통일 권장. Steam Cloud 동기는 fallback
- [ ] **GAS Lobby 동안 ASC `OnRep_PlayerState` race** — 매치 시작 *직전* 능력 부여 시 클라가 *능력 도착 전* GameMode 가 InProgress 진입. RepFrequency 100Hz 강제 + 일관성 검증 (열린)
- [ ] **Subsystem 그래프 cycle detection 자동화** — Editor Plugin 의 정적 분석 + warning. UE 자체는 runtime ensure 만 (열린)

## 7. 관련

### Sources

[[sources/ue-subsystem-onlinesubsystem]] · [[sources/ue-subsystem-skill]] · [[sources/ue-gas-skill]] · [[sources/ue-gameframework-gameinstance]]

### Entities

[[entities/USubsystem]] · [[entities/UGameInstance]] · [[entities/UAbilitySystemComponent]]

### Concepts

[[concepts/Subsystem-5-Types]] · [[concepts/SeamlessTravel]]

### Related synthesis

[[synthesis/subsystem-graph-online-wrapper]] (베이스 — Online wrapper + 그래프) · [[synthesis/gas-advanced-runtime-patterns]] (스킬 swap + Lobby) · [[synthesis/late-join-reconnect-state-sync]] (매치 중 합류 + EOS 연동)
