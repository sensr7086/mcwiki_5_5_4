---
name: subsystem-online
description: Online Subsystem (멀티플레이 / 매치메이킹 / 친구 / 업적) — Steam / EOS (Epic Online Services) / PSN / Xbox Live / Switch / Google Play. IOnlineSubsystem + IOnlineSession + IOnlineIdentity + IOnlineFriends 인터페이스 + 5.x EOSCore Plugin 표준.
---

# Subsystem/OnlineSubsystem — 멀티플레이 / 매치메이킹 / 플랫폼 SDK

> **위치**: `Engine/Plugins/Online/OnlineSubsystem*` (Steam / EOS / Null / etc) + Plugin SDK 별도
> **베이스**: `IOnlineSubsystem` (인터페이스) + 플랫폼별 구현
> **요지**: 멀티플레이 / 친구 / 매치메이킹 / 업적 / 클라우드 저장의 표준. Steam / Epic Online Services / 콘솔 SDK 통합.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 비동기 의무 | 모든 Online API = Async (Delegate 콜백) — 동기 호출 X |
| 🚨 Lifetime | Login / Logout 페어 + Subsystem 라이프사이클과 페어 |
| 🚨 Cooked Build | Plugin SDK = Cook 시점 통합 — 빌드 검증 의무 |
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | 콜백 Delegate 첫 줄 프로파일링 스코프 |

---

## 1. Online Subsystem 5종 (Plugin)

| Plugin | 플랫폼 | Plugin 이름 | 5.x 상태 |
|--------|-------|-----------|---------|
| **OnlineSubsystemSteam** | PC / Steam | `OnlineSubsystemSteam` | ✅ 표준 |
| **OnlineSubsystemEOS** ⭐ | Cross-Platform (PC/Console/Mobile) | `OnlineSubsystemEOS` + `EOSCore` | ✅ 5.x 권장 |
| **OnlineSubsystemNull** | 로컬 / 개발 | `OnlineSubsystemNull` | ✅ 항상 사용 가능 |
| **OnlineSubsystemPSN** | PS4/PS5 | (Sony NDA) | ✅ |
| **OnlineSubsystemLive** | Xbox One/Series | (Microsoft NDA) | ✅ |
| **OnlineSubsystemSwitch** | Nintendo Switch | (Nintendo NDA) | ✅ |
| **OnlineSubsystemGooglePlay** | Android | `OnlineSubsystemGooglePlay` | ✅ |
| **OnlineSubsystemIOS** | iOS / GameCenter | `OnlineSubsystemIOS` | ✅ |

---

## 2. IOnlineSubsystem 핵심 인터페이스 7종

```cpp
// IOnlineSubsystem.h
class IOnlineSubsystem
{
    virtual IOnlineSessionPtr GetSessionInterface() const;        // 매치메이킹 / 세션
    virtual IOnlineIdentityPtr GetIdentityInterface() const;       // 로그인 / 사용자 ID
    virtual IOnlineFriendsPtr GetFriendsInterface() const;          // 친구 목록
    virtual IOnlinePresencePtr GetPresenceInterface() const;        // 온라인 상태
    virtual IOnlineAchievementsPtr GetAchievementsInterface() const;// 업적
    virtual IOnlineLeaderboardsPtr GetLeaderboardsInterface() const;// 리더보드
    virtual IOnlineUserCloudPtr GetUserCloudInterface() const;      // 클라우드 저장
};
```

---

## 3. EOS (Epic Online Services) 표준 — 5.x 권장

### 3.1 활성

```ini
; DefaultEngine.ini
[OnlineSubsystem]
DefaultPlatformService=EOS

[OnlineSubsystemEOS]
bEnabled=true
ProductId=...           ; Epic Dev Portal 발급
SandboxId=...
DeploymentId=...
ClientId=...
ClientSecret=...
```

### 3.2 EOSCore Plugin (5.x)

EOS 의 더 깊은 기능 (Lobbies / Sanctions / Stats):
```
- OnlineSubsystemEOS = 표준 인터페이스 (UE 표준)
- EOSCore Plugin = 추가 기능 (Lobbies 등 — UE 표준 인터페이스 외)
```

### 3.3 Cross-Platform 매트릭스

| 기능 | Steam | EOS | PSN | Xbox |
|------|:-----:|:---:|:---:|:----:|
| 매치메이킹 | ✅ | ✅ | ✅ | ✅ |
| 친구 / 초대 | ✅ | ✅ | ✅ | ✅ |
| Cross-Platform Play | ❌ | ✅ ⭐ | ⚠ | ⚠ |
| 업적 | ✅ | ✅ | ✅ | ✅ |
| 리더보드 | ✅ | ✅ | ✅ | ✅ |
| 클라우드 저장 | ✅ | ✅ | ✅ | ✅ |
| Voice Chat | ⚠ | ✅ ⭐ | ✅ | ✅ |

→ **Cross-Platform 게임 = EOS 권장** (모든 플랫폼 통합).

---

## 4. 표준 사용 패턴 — 로그인 + 세션 생성

### 4.1 GameInstanceSubsystem 베이스

```cpp
// MyOnlineSubsystem.h
UCLASS()
class UMyOnlineSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    UFUNCTION(BlueprintCallable, Category="Online")
    void Login();

    UFUNCTION(BlueprintCallable, Category="Online")
    void CreateSession();

    DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnLoginComplete, bool, bSuccess);
    UPROPERTY(BlueprintAssignable)
    FOnLoginComplete OnLoginComplete;

private:
    FDelegateHandle LoginCompleteDelegateHandle;

    void HandleLoginComplete(int32 LocalUserNum, bool bWasSuccessful, const FUniqueNetId& UserId, const FString& Error);
};

// MyOnlineSubsystem.cpp
void UMyOnlineSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyOnlineSubsystem::Initialize);
}

void UMyOnlineSubsystem::Login()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyOnlineSubsystem::Login);

    IOnlineSubsystem* OSS = IOnlineSubsystem::Get();
    if (!OSS) { return; }

    IOnlineIdentityPtr Identity = OSS->GetIdentityInterface();
    if (!Identity.IsValid()) { return; }

    // 콜백 등록
    LoginCompleteDelegateHandle = Identity->AddOnLoginCompleteDelegate_Handle(0,
        FOnLoginCompleteDelegate::CreateUObject(this, &UMyOnlineSubsystem::HandleLoginComplete));

    // 비동기 Login
    FOnlineAccountCredentials Credentials;
    Credentials.Type = TEXT("AccountPortal");   // EOS
    Identity->Login(0, Credentials);
}

void UMyOnlineSubsystem::HandleLoginComplete(
    int32 LocalUserNum, bool bWasSuccessful,
    const FUniqueNetId& UserId, const FString& Error)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyOnlineSubsystem::HandleLoginComplete);

    IOnlineSubsystem* OSS = IOnlineSubsystem::Get();
    if (OSS && OSS->GetIdentityInterface().IsValid())
    {
        // 콜백 해제 (의무)
        OSS->GetIdentityInterface()->ClearOnLoginCompleteDelegate_Handle(0, LoginCompleteDelegateHandle);
    }

    OnLoginComplete.Broadcast(bWasSuccessful);
}

void UMyOnlineSubsystem::Deinitialize()
{
    // 로그아웃 / 세션 정리
    IOnlineSubsystem* OSS = IOnlineSubsystem::Get();
    if (OSS && OSS->GetIdentityInterface().IsValid())
    {
        OSS->GetIdentityInterface()->Logout(0);
    }

    Super::Deinitialize();
}
```

### 4.2 세션 생성 패턴

```cpp
void UMyOnlineSubsystem::CreateSession()
{
    IOnlineSubsystem* OSS = IOnlineSubsystem::Get();
    if (!OSS) { return; }

    IOnlineSessionPtr Sessions = OSS->GetSessionInterface();
    if (!Sessions.IsValid()) { return; }

    FOnlineSessionSettings Settings;
    Settings.NumPublicConnections = 4;
    Settings.bShouldAdvertise = true;
    Settings.bAllowJoinInProgress = true;
    Settings.bUsesPresence = true;
    Settings.bUseLobbiesIfAvailable = true;          // EOS Lobbies (5.x)
    Settings.Set(TEXT("MAP"), FString("DM-Default"), EOnlineDataAdvertisementType::ViaOnlineService);

    // 콜백 등록
    Sessions->AddOnCreateSessionCompleteDelegate_Handle(
        FOnCreateSessionCompleteDelegate::CreateUObject(this, &UMyOnlineSubsystem::HandleCreateSessionComplete));

    Sessions->CreateSession(0, NAME_GameSession, Settings);
}
```

---

## 5. Plugin SDK 통합 (Steam / EOS / 콘솔)

### 5.1 Steam SDK

```ini
; DefaultEngine.ini
[OnlineSubsystem]
DefaultPlatformService=Steam

[OnlineSubsystemSteam]
bEnabled=true
SteamDevAppId=480       ; SpaceWar 개발용 ID

[/Script/OnlineSubsystemSteam.SteamNetDriver]
NetConnectionClassName="OnlineSubsystemSteam.SteamNetConnection"
```

### 5.2 EOS SDK

```ini
[OnlineSubsystemEOS]
bEnabled=true

[/Script/OnlineSubsystemEOS.NetDriverEOS]
bIsUsingP2PSockets=true
```

### 5.3 콘솔 SDK (NDA — 자세한 정보 비공개)
```
- PSN = Sony Developer Portal SDK
- Xbox = Microsoft GDK / GDKX (Xbox Series)
- Switch = Nintendo NDK + NetEx
- iOS = GameCenter (iOS 표준)
```

---

## 6. Replication 통합 (Networking 카테고리 페어)

→ 자세한 = [`Networking/SKILL.md`](../../Networking/SKILL.md).

```cpp
// GameMode 측 — Online Subsystem 통한 PreLogin
virtual void PreLogin(...) override
{
    // Online Subsystem 으로 Player 인증
    if (auto* Identity = IOnlineSubsystem::Get()->GetIdentityInterface())
    {
        if (!Identity->IsLoggedIn(...))
        {
            // 거부
            return;
        }
    }
    Super::PreLogin(...);
}
```

---

## 7. 함정 & 안티패턴 (10대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | 동기 Login / CreateSession 호출 (없음 — 모두 Async) | Delegate 콜백 의무 |
| 2 | Delegate 등록 후 해제 누락 | `Clear*Delegate_Handle` 페어 |
| 3 | Cross-Platform 게임 + Steam 만 사용 | EOS 권장 (Cross-Platform 표준) |
| 4 | EOS Sandbox / Production 혼동 | DefaultEngine.ini 분기 의무 |
| 5 | 5.x EOSCore Plugin 미사용 (Lobbies 누락) | EOSCore Plugin 추가 |
| 6 | Steam DevAppId = 480 (개발) Production 사용 | 출시용 AppId 발급 의무 |
| 7 | SessionSettings.bUseLobbiesIfAvailable=false | EOS = true (Lobbies 사용) |
| 8 | UniqueNetId 직접 Cast (Steam vs EOS 다름) | TSharedRef<FUniqueNetId> 추상 |
| 9 | Cooked Build SDK 통합 누락 | Plugin Cook + 콘솔 SDK 빌드 의무 |
| 10 | 콘솔 SDK = NDA 위반 (오픈 소스 / GitHub) | 콘솔 SDK = 비공개 저장소 의무 |

---

## 8. 체크리스트

- [ ] OnlineSubsystem 활성 (Steam / EOS / 콘솔)
- [ ] 5.x = EOS 권장 (Cross-Platform)
- [ ] EOSCore Plugin (Lobbies 등 추가 기능)
- [ ] Login → Delegate 콜백 + Clear 페어
- [ ] Session → bUseLobbiesIfAvailable=true (EOS)
- [ ] Plugin SDK Cooked Build 검증
- [ ] 콘솔 SDK = 비공개 저장소
- [ ] Cross-Platform 인증 (UniqueNetId 추상)
- [ ] Production AppId / DeploymentId 분리 (Sandbox vs Production)

---

## 9. 관련

- [`Subsystem/SKILL.md`](../SKILL.md) — 메인 (5종 Subsystem)
- [`Networking/SKILL.md`](../../Networking/SKILL.md) — Replication 페어
- [`Build/SKILL.md`](../../Build/SKILL.md) — Plugin SDK Cooked Build
- [`GameFramework/references/GameInstance.md`](../../GameFramework/references/GameInstance.md) — UGameInstanceSubsystem
- [`GameFramework/references/GameMode.md`](../../GameFramework/references/GameMode.md) — PreLogin 통합

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-08 | 최초 작성. **Online Subsystem 8 Plugin** + EOS 표준 + 7 인터페이스 + Login/Session 표준 + Plugin SDK 통합 + Cross-Platform 매트릭스 + 콘솔 NDA + 함정 10대. |
