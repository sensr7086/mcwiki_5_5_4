---
type: synthesis
title: "5종 Subsystem 결정 트리 9 시나리오 — Engine/Editor/GameInstance/World/LocalPlayer"
slug: subsystem-5-types-decision-tree
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/ue-subsystem-skill]]"
  - "[[sources/ue-subsystem-onlinesubsystem]]"
  - "[[sources/ue-gameframework-gameinstance]]"
  - "[[sources/ue-gameframework-world]]"
  - "[[sources/ue-input-subsystem]]"
  - "[[sources/ue-editor-editorsubsystem]]"
entities:
  - "[[entities/USubsystem]]"
  - "[[entities/UEngineSubsystem]]"
  - "[[entities/UGameInstance]]"
  - "[[entities/UWorld]]"
  - "[[entities/UEnhancedInputLocalPlayerSubsystem]]"
concepts:
  - "[[concepts/Subsystem-5-Types]]"
  - "[[concepts/SeamlessTravel]]"
  - "[[concepts/Global-Iterator-Avoidance]]"
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
status: living
tags: [synthesis, subsystem, gameinstance, worldsubsystem, localplayer]
---

# 5종 Subsystem 결정 트리 9 시나리오

## 1. Thesis

UE 의 5종 Subsystem (`UEngineSubsystem` / `UEditorSubsystem` / `UGameInstanceSubsystem` / `UWorldSubsystem` / `ULocalPlayerSubsystem`) 은 *수명 + 접근성 + Cooked vs Editor* 의 3 축으로 자동 결정 — 9 가지 흔한 시나리오에서 결정 트리만 따라가면 정답이 나옴. [[concepts/Subsystem-5-Types]] 의 분류표 + [[sources/ue-subsystem-skill]] §결정 트리 + [[sources/ue-subsystem-onlinesubsystem]] (5번째 — Online Plugin 통합) 통합.

## 2. 5 종 매트릭스

| Subsystem | 수명 | 접근 | Cooked OK | 흔한 용도 |
| -- | -- | -- | -- | -- |
| `UEngineSubsystem` | 엔진 시작 ~ 종료 (게임 전체) | `GEngine->GetEngineSubsystem<T>()` | ✓ | 글로벌 등록부 / 디바이스 스캔 |
| `UEditorSubsystem` 🛠 | 에디터 열림 ~ 닫힘 | `GEditor->GetEditorSubsystem<T>()` | ✗ (Editor only) | 인하우스 툴 / Asset 작업 |
| `UGameInstanceSubsystem` | 게임 시작 ~ 종료 (Map 전환 *생존*) | `GameInstance->GetSubsystem<T>()` | ✓ | 세이브 / 글로벌 게임 상태 / Online |
| `UWorldSubsystem` | World 로드 ~ 언로드 (Map 전환 *재생성*) | `World->GetSubsystem<T>()` | ✓ | Map-specific 매니저 / 적 spawner |
| `ULocalPlayerSubsystem` | LocalPlayer 1명당 1개 (split-screen N 명) | `PlayerController->GetLocalPlayer()->GetSubsystem<T>()` | ✓ | Input (UEnhancedInputLocalPlayerSubsystem) / UI / 개별 세이브 |

## 3. 결정 트리 (3 축)

```
[축 1] 이 시스템이 Map 전환을 살아남아야 하나?
├── 예 → GameInstance / Engine / LocalPlayer 후보
│   ├── 1명 플레이어 / 멀티 모두 동일 → GameInstance
│   ├── 1명 플레이어마다 따로 (split-screen) → LocalPlayer
│   └── 게임 다중 인스턴스 (PIE 동시 2 World) 도 1개 → Engine
└── 아니오 (Map 별로 새로) → World 후보
    └── World

[축 2] Editor only 인가?
├── 예 → Editor (다른 4 종은 Cooked 빌드도 동작 — Editor 만 strip)
└── 아니오 → 위 4 종 중

[축 3] 외부 SDK (Steam / EOS / PSN) 통합인가?
└── 예 → OnlineSubsystem (5번째 — Plugin) 또는 GameInstance 안 호스팅
```

## 4. 9 시나리오

| # | 시나리오 | 답 | 이유 |
| -- | -- | -- | -- |
| 1 | 글로벌 자산 카탈로그 (모든 Spawn 가능 캐릭터 메타) | `Engine` | 게임 다중 인스턴스 무관, 엔진 전체 1개 |
| 2 | 세이브 / 로드 시스템 | `GameInstance` | Map 전환 살아남고, 1 게임 = 1 매니저 |
| 3 | 적 NPC Spawner (현재 Map 만) | `World` | Map 별 새 인스턴스, 언로드 시 자동 cleanup |
| 4 | Enhanced Input MappingContext stack | `LocalPlayer` (UEnhancedInputLocalPlayerSubsystem 내장) | Input 은 플레이어별 |
| 5 | 인하우스 에셋 검증 툴 | `Editor` 🛠 | Cooked 빌드 미포함 |
| 6 | Steam Lobby / Matchmaking | `Online` (Plugin) + GameInstance 가 핸들 보관 | 외부 SDK + Map 생존 |
| 7 | 캐릭터 인벤토리 (드롭 / 수집) | `LocalPlayer` 또는 `GameInstance` (싱글) | 멀티면 LocalPlayer (각자), 싱글이면 GameInstance |
| 8 | Cinematic Sequence 매니저 (현재 레벨 컷씬) | `World` | Map 별 |
| 9 | 디버그 콘솔 / 치트 매니저 | `Engine` 또는 `GameInstance` | 글로벌 — 보통 GameInstance |

## 5. 작성 골격

```cpp
UCLASS()
class UMyManager : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    // 의무 override
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;
    virtual bool ShouldCreateSubsystem(UObject* Outer) const override
    {
        // 디폴트 true. 특정 빌드 / 플랫폼 제한할 때 override
        return Super::ShouldCreateSubsystem(Outer);
    }
};
```

[[sources/ue-subsystem-skill]] §작성 표준 — `Initialize` 가 Constructor 의 안전 변형 (UWorld 접근 가능). 다른 Subsystem 의존 시 `Collection.InitializeDependency<TOther>()`.

## 6. 함정 / 열린 질문

- [ ] **`UWorldSubsystem` 의 SeamlessTravel** ([[concepts/SeamlessTravel]]) — 일부 데이터를 살리려면 GameInstance 로 옮겨야. World 는 무조건 새로 만들어짐
- [ ] **PIE 2 인스턴스 동시 실행** — World/LocalPlayer Subsystem 은 *각 인스턴스별* 독립. Engine/GameInstance 는 PIE 별 1개 (Server PIE / Client PIE 별도). 글로벌 mutate 시 race 가능
- [ ] **`Online` 은 5번째 자리지만 USubsystem 아님** ([[sources/ue-subsystem-onlinesubsystem]]) — IOnlineSubsystem 은 Plugin 의 IModuleInterface. GameInstanceSubsystem 안 wrapper 작성이 권장 패턴
- [ ] **`TActorIterator` 회피** ([[concepts/Global-Iterator-Avoidance]]) — Subsystem 의 RegisterObject 패턴이 정답. Iterator 매 프레임 = O(n) 검색
- [ ] **Editor Subsystem 의 4단 분리** ([[concepts/Editor-Only-4-Tier-Separation]]) — 런타임 모듈에서 import 금지. `WITH_EDITOR` 가드 + 별도 Editor 모듈
- [ ] **LocalPlayer 의 split-screen 동기화** — 4 명 split-screen 시 4 LocalPlayerSubsystem. UI / 인벤토리 동기 필요시 GameInstance 가 broadcast (열린)
- [ ] **`ShouldCreateSubsystem` 으로 빌드별 분기** — Mobile vs Console vs PC 별 다른 Subsystem 활성. 잘 안 알려진 패턴 (열린)

## 7. 관련

### Sources

[[sources/ue-subsystem-skill]] · [[sources/ue-subsystem-onlinesubsystem]] · [[sources/ue-gameframework-gameinstance]] · [[sources/ue-gameframework-world]] · [[sources/ue-input-subsystem]] · [[sources/ue-editor-editorsubsystem]]

### Entities

[[entities/USubsystem]] · [[entities/UEngineSubsystem]] · [[entities/UGameInstance]] · [[entities/UWorld]] · [[entities/UEnhancedInputLocalPlayerSubsystem]]

### Concepts

[[concepts/Subsystem-5-Types]] · [[concepts/SeamlessTravel]] · [[concepts/Global-Iterator-Avoidance]] · [[concepts/Editor-Only-4-Tier-Separation]]

### Related synthesis

[[synthesis/component-vs-actor-lifecycle-table]] (Subsystem Initialize / Deinitialize 시점) · [[synthesis/server-vs-client-rpc-decision-tree]] (멀티플레이 Subsystem 분산) · [[synthesis/gas-pawn-vs-playerstate-decision]] (GAS 호스트 = Pawn vs PlayerState 의 Subsystem 변형 사례)
