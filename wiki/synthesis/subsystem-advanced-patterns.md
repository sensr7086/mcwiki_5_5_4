---
type: synthesis
title: "Subsystem 고급 패턴 — LocalPlayer split-screen 동기화 + ShouldCreateSubsystem 빌드별 분기 + Subsystem 의존 Initialize"
slug: subsystem-advanced-patterns
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/ue-subsystem-skill]]"
  - "[[sources/ue-input-subsystem]]"
  - "[[sources/ue-gameframework-gameinstance]]"
  - "[[sources/ue-build-skill]]"
  - "[[sources/ue-subsystem-onlinesubsystem]]"
entities:
  - "[[entities/USubsystem]]"
  - "[[entities/UEnhancedInputLocalPlayerSubsystem]]"
  - "[[entities/UGameInstance]]"
  - "[[entities/APlayerController]]"
concepts:
  - "[[concepts/Subsystem-5-Types]]"
  - "[[concepts/Build-Configurations]]"
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
status: living
tags: [synthesis, subsystem, splitscreen, localplayer, build]
---

# Subsystem 고급 패턴

## 1. Thesis

[[synthesis/subsystem-5-types-decision-tree]] 의 5 종 결정 외에, *실제 프로덕션* 에서 부딪히는 3 가지 고급 케이스 — **(1) Split-screen 4 인 LocalPlayer Subsystem 의 동기화** (4 개 인스턴스 vs 1 GameInstance) / **(2) `ShouldCreateSubsystem` 으로 빌드/플랫폼 별 활성** (Mobile vs PC vs Console) / **(3) `Initialize(FSubsystemCollectionBase&)` 안 다른 Subsystem 의존 명시**. 본 synthesis 는 잘 알려지지 않은 패턴 + 함정.

## 2. (1) Split-Screen 동기화

LocalPlayer Subsystem 은 *플레이어 1명당 1개* — 4 인 split-screen 시 4 인스턴스. 플레이어 간 데이터 공유가 필요하면:

| 케이스 | 패턴 |
| -- | -- |
| 각자 독립 (자기 인벤토리 / Input) | LocalPlayer Subsystem (4 인스턴스) |
| 공유 (보스 HP / 팀 점수) | GameInstance Subsystem 1개 + 4 LocalPlayer 가 broadcast |
| 일부 공유 (팀 채팅) | Mixed — LocalPlayer 가 자기 메시지 입력 → GameInstance 가 모든 LocalPlayer 에 broadcast |

```cpp
// LocalPlayer Subsystem — 자기 입력만
class UMCPlayerInventory : public ULocalPlayerSubsystem
{
    void AddItem(int32 ItemId);  // 자기 인벤토리
};

// GameInstance Subsystem — 팀 공유
class UMCTeamScore : public UGameInstanceSubsystem
{
    DECLARE_MULTICAST_DELEGATE_OneParam(FOnScoreChanged, int32);
    FOnScoreChanged OnScoreChanged;
    void AddScore(int32 Delta);  // broadcast 모든 LocalPlayer
};

// LocalPlayer 가 broadcast 구독
void UMCPlayerInventory::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    if (UGameInstance* GI = GetLocalPlayer()->GetGameInstance()) {
        if (UMCTeamScore* TS = GI->GetSubsystem<UMCTeamScore>()) {
            TS->OnScoreChanged.AddUObject(this, &ThisClass::HandleTeamScore);
        }
    }
}
```

## 3. (2) ShouldCreateSubsystem 빌드별 분기

```cpp
class UMCMobileTouchManager : public ULocalPlayerSubsystem
{
    virtual bool ShouldCreateSubsystem(UObject* Outer) const override
    {
#if PLATFORM_DESKTOP
        return false;  // PC / 콘솔 = 키보드/패드 — 터치 매니저 불필요
#else
        return Super::ShouldCreateSubsystem(Outer);
#endif
    }
};

class UMCDevConsole : public UGameInstanceSubsystem
{
    virtual bool ShouldCreateSubsystem(UObject* Outer) const override
    {
#if UE_BUILD_SHIPPING
        return false;  // Shipping 빌드는 콘솔 차단
#else
        return Super::ShouldCreateSubsystem(Outer);
#endif
    }
};
```

매트릭스:
- `PLATFORM_DESKTOP` / `PLATFORM_IOS` / `PLATFORM_ANDROID` / `PLATFORM_WINDOWS` / `PLATFORM_MAC` 등 — 플랫폼 별
- `UE_BUILD_SHIPPING` / `UE_BUILD_DEBUG` / `UE_BUILD_DEVELOPMENT` — 빌드 컨피그 별 ([[concepts/Build-Configurations]])
- `WITH_EDITOR` — 에디터 only (이미 `UEditorSubsystem` 으로 분리되지만, GameInstanceSubsystem 안 일부 기능만 Editor 분기 시)
- `bDedicatedServer` — 서버 only (UI Subsystem 등 클라 only 기능 차단)

## 4. (3) Subsystem 의존 Initialize

`Initialize(FSubsystemCollectionBase& Collection)` 은 *다른 Subsystem 의 Initialize 가 먼저 끝나야 함을 명시* 가능:

```cpp
class UMCSaveLoad : public UGameInstanceSubsystem
{
    virtual void Initialize(FSubsystemCollectionBase& Collection) override
    {
        // 의존 Subsystem 명시 — UMCConfigManager 의 Initialize 가 먼저 호출되도록 보장
        Collection.InitializeDependency<UMCConfigManager>();

        Super::Initialize(Collection);
        // 이제 GetSubsystem<UMCConfigManager>() 안전하게 사용
        if (UMCConfigManager* Cfg = GetGameInstance()->GetSubsystem<UMCConfigManager>()) {
            SaveDir = Cfg->GetSavePath();
        }
    }
};
```

`InitializeDependency<T>()` — Subsystem 그래프 위상 정렬 → 순서 자동. cycle 있으면 ensure.

## 5. 결정 트리 — 어디 호스팅할까

```
이 시스템 / 데이터 / 매니저:
├── 게임 모든 인스턴스 공통 (예: 자산 카탈로그)
│   └── Engine Subsystem
├── 에디터 only (자산 검증)
│   └── Editor Subsystem 🛠
├── 게임 동안 살아남고 모든 플레이어 공유
│   └── GameInstance Subsystem
├── Map 별 새로 — Map 언로드 시 자동 cleanup
│   └── World Subsystem
├── 플레이어 별 (인벤토리 / Input / UI 상태)
│   └── LocalPlayer Subsystem
│       ├── 1명 → 1 인스턴스 OK
│       └── 4명 split-screen → 4 인스턴스 + GameInstance broadcast (§2)
└── 외부 SDK (Steam/EOS/PSN)
    └── Online Subsystem (Plugin) + GameInstance 가 wrap
```

## 6. 함정 / 열린 질문

- [ ] **`InitializeDependency<T>` 의 한계** — `T` 도 Initialize 안에서 다른 의존 표명 가능 → cycle 발생 시 ensure. 의존 그래프 단순 유지
- [ ] **`Deinitialize` 순서** — `Initialize` 의 *역순*. Subsystem A 가 B 에 의존했으면 Deinit 시 A 먼저 → B. 의존성에 캐시한 weak ptr 도 교차 검증
- [ ] **PIE 다중 인스턴스 → World Subsystem 별도** — Server PIE / Client PIE 별도 World → 각자 Subsystem. PIE 안 디버깅 시 *어느 인스턴스 인지* 명시 가능 (`World->GetNetMode()`)
- [ ] **`bDedicatedServer` ShouldCreateSubsystem** — UI / Audio / VFX Subsystem 차단 의무. 안 그러면 server cook 빌드 X 이기는 한데 메모리/모듈 의존 cascade
- [ ] **LocalPlayer Subsystem 의 split-screen Add/Remove** — 2명 → 3명 → 2명 (한명 leave). 새 LocalPlayer 의 Subsystem 자동 생성. 떠나는 LocalPlayer 의 Subsystem Deinit (열린 — UE 자체 보장하지만 사용자 코드에서 의존 weak ptr 검증)
- [ ] **`ShouldCreateSubsystem` 의 *Outer* 인자** — Outer = GameInstance / World / LocalPlayer 자체. 같은 클래스의 다른 Outer 별 활성 분기 가능 (특정 World 만 등) (열린)
- [ ] **Online Subsystem 과 통합** — IOnlineSubsystem 은 USubsystem 아님 → GameInstance Subsystem 안 wrapper 표준. SDK 별 (Steam/EOS) 분기 패턴 (열린, [[sources/ue-subsystem-onlinesubsystem]])

## 7. 관련

### Sources

[[sources/ue-subsystem-skill]] · [[sources/ue-input-subsystem]] · [[sources/ue-gameframework-gameinstance]] · [[sources/ue-build-skill]] · [[sources/ue-subsystem-onlinesubsystem]]

### Entities

[[entities/USubsystem]] · [[entities/UEnhancedInputLocalPlayerSubsystem]] · [[entities/UGameInstance]] · [[entities/APlayerController]]

### Concepts

[[concepts/Subsystem-5-Types]] · [[concepts/Build-Configurations]] · [[concepts/Editor-Only-4-Tier-Separation]]

### Related synthesis

[[synthesis/subsystem-5-types-decision-tree]] (5 종 베이스) · [[synthesis/component-vs-actor-lifecycle-table]] (Initialize 시점) · [[synthesis/cooked-first-frame-stability]] (PLATFORM_* 매크로 분기)

### Cycle 5o reverse-link 보강 (high confidence missing)

- [[synthesis/subsystem-graph-online-wrapper]] (inbound=3, suggest_missing_cross_link high confidence)
