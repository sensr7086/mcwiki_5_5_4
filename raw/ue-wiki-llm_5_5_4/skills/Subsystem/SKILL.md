---
name: subsystem
description: UE Subsystem 통합 가이드 — USubsystem 베이스 5종 (UEngineSubsystem / UGameInstanceSubsystem / UWorldSubsystem / ULocalPlayerSubsystem / UEditorSubsystem) + Online Subsystem 통합 (Steam/EOS/PSN/Xbox/Switch SDK). 비교 매트릭스 + 작성 표준 + 결정 트리 + 함정. 전역 이터레이터 회피 표준.
---

# Subsystem — UE Subsystem (베이스 5종 + Online)

> **확장 (2026-05-08)**: [`OnlineSubsystem/SKILL.md`](./OnlineSubsystem/SKILL.md) — Online Subsystem (멀티플레이 / 매치메이킹 / 친구 / 업적) + Steam / EOS / PSN / Xbox / Switch SDK 통합.

---

> **위치**: `Engine/Source/Runtime/Engine/Public/Subsystems/{Subsystem,EngineSubsystem,GameInstanceSubsystem,WorldSubsystem,LocalPlayerSubsystem}.h` + `Editor/EditorSubsystem/Public/EditorSubsystem.h` (Editor 모듈)
> **베이스**: `UObject` → `USubsystem` (또는 `UDynamicSubsystem` for Engine/Editor)
> **요지**: **UE Engine 이 자동 인스턴스 생성 + 라이프사이클 관리**. 5종 = Engine / Editor / GameInstance / World / LocalPlayer. **`TActorIterator` / `TObjectIterator` / 전역 매니저 패턴 회피의 표준 대안** (등록 비용 1회 + 검색 비용 0).

---

## 1. USubsystem 베이스 (모든 Subsystem 공통)

[`Subsystem.h:46-76`](../../../UnrealEngine/Engine/Source/Runtime/Engine/Public/Subsystems/Subsystem.h):

```cpp
UCLASS(Abstract, MinimalAPI)
class USubsystem : public UObject
{
public:
    /** Override to control if the Subsystem should be created at all.
     *  예: 서버 전용 / WITH_EDITOR 만 / 특정 플랫폼 만 */
    virtual bool ShouldCreateSubsystem(UObject* Outer) const { return true; }

    /** 인스턴스 초기화 — Engine 자동 호출 */
    virtual void Initialize(FSubsystemCollectionBase& Collection) {}

    /** 인스턴스 해제 — Engine 자동 호출 */
    virtual void Deinitialize() {}

    /** Network Callspace (RPC 처리) */
    virtual int32 GetFunctionCallspace(UFunction* Function, FFrame* Stack) override;
};
```

### 1.1 UDynamicSubsystem (Engine + Editor 만)

[`Subsystem.h:86-93`]:
```cpp
UCLASS(Abstract, MinimalAPI)
class UDynamicSubsystem : public USubsystem
{
    // 모듈 로드/언로드 시 자동 인스턴스 생성/해제
    // → UEngineSubsystem / UEditorSubsystem 만 상속
};
```

> **DynamicSubsystem** = `LoadModule("ModuleName")` 시 자동 등록 + 모듈 unload 시 자동 해제. **GameInstance/World/LocalPlayer 는 정적** (각 Outer 라이프사이클 따름).

---

## 2. 5종 Subsystem 비교 매트릭스 (베이스 선택)

| Subsystem | 베이스 | Outer (Within) | 라이프사이클 | 동적 로드 | 추가 virtual | 주요 사용 케이스 |
|-----------|--------|----------------|-------------|----------|-------------|-----------------|
| **`UEngineSubsystem`** | `UDynamicSubsystem` | `UEngine` | Engine 시작 → 종료 (가장 김) | ✅ | (베이스 3개만) | Engine-wide 캐시 / 글로벌 Manager / Plugin 진입점 |
| **`UEditorSubsystem`** 🛠 | `UDynamicSubsystem` | `UEditorEngine` | Editor 시작 → 종료 | ✅ | (베이스 3개만) | Editor 도구 / Asset 처리 / WITH_EDITOR 전용 |
| **`UGameInstanceSubsystem`** ⭐ | `USubsystem` | `UGameInstance` | GameInstance Init → Shutdown (Map 전환 살아남음) | ❌ | `GetGameInstance()` | Save / Online Session / 설정값 / 영속 데이터 |
| **`UWorldSubsystem`** | `USubsystem` | `UWorld` | World Init → Cleanup (Map 마다 새로 생성) | ❌ | `GetWorld()` final + `PostInitialize` + `OnWorldBeginPlay` + `OnWorldEndPlay` + `OnWorldComponentsUpdated` + `DoesSupportWorldType` | Spawned Actor 추적 / NavMesh / Physics / World-bound 매니저 |
| **`ULocalPlayerSubsystem`** | `USubsystem` (Within=LocalPlayer) | `ULocalPlayer` | LocalPlayer 추가 → 제거 (Couch Co-op 지원) | ❌ | `GetLocalPlayer<T>()` template + `PlayerControllerChanged` | UI Stack / Camera / Input (Enhanced Input) / Local-only 데이터 |

### 2.1 UTickableWorldSubsystem (Tick 가능)

[`WorldSubsystem.h:55-82`]:
```cpp
UCLASS(Abstract, MinimalAPI)
class UTickableWorldSubsystem : public UWorldSubsystem, public FTickableGameObject
{
public:
    virtual ETickableTickType GetTickableTickType() const override;
    virtual void Tick(float DeltaTime) override;
    virtual TStatId GetStatId() const override PURE_VIRTUAL(...);
    bool IsInitialized() const { return bInitialized; }
};
```

> **Tick 필요한 Subsystem 만** UTickableWorldSubsystem 상속. 다른 4종은 Tick 불가 — Tick 필요 시 `FTSTicker` 또는 `World->GetTimerManager()` 사용.

---

## 3. 작성 표준 패턴 (모든 Subsystem 공통)

### 3.1 헤더 + 구현 표준

```cpp
// MyGameSubsystem.h
#pragma once
#include "Subsystems/GameInstanceSubsystem.h"
#include "MyGameSubsystem.generated.h"

UCLASS()
class MYGAME_API UMyGameSubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    // (1) 생성 조건 (선택)
    virtual bool ShouldCreateSubsystem(UObject* Outer) const override;

    // (2) 초기화 / 해제 (가장 자주 override)
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    // 사용자 API
    UFUNCTION(BlueprintCallable, Category = "MyGame")
    void DoSomething();

private:
    UPROPERTY()  // ⚠️ GC 방어
    TObjectPtr<UMyData> CachedData;
};

// MyGameSubsystem.cpp
bool UMyGameSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
    // 예: 서버 전용
    UWorld* World = GetWorld();
    if (World && World->GetNetMode() == NM_Client) return false;

    // Editor 전용 / Dedicated Server / Cooked Build 등 분기
    return Super::ShouldCreateSubsystem(Outer);
}

void UMyGameSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyGameSubsystem::Initialize);  // 🚨 프로파일링 스코프 의무
    Super::Initialize(Collection);   // ⚠️ FIRST

    // 의존 Subsystem 명시 (선택) — 본 Subsystem 보다 먼저 초기화
    Collection.InitializeDependency<UOtherSubsystem>();

    // 외부 시스템 구독 / 초기 데이터 로드
}

void UMyGameSubsystem::Deinitialize()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyGameSubsystem::Deinitialize);
    // 사용자 cleanup 먼저 (델리게이트 unbind 등)
    Super::Deinitialize();           // ⚠️ LAST
}
```

### 3.2 사용 (어디서든 GetSubsystem)

```cpp
// 1. UGameInstanceSubsystem
UMyGameSubsystem* Sys = GetGameInstance()->GetSubsystem<UMyGameSubsystem>();
// 또는 nullptr 안전 (GameInstance 가 nullptr 일 수 있을 때)
UMyGameSubsystem* Sys2 = UGameInstance::GetSubsystem<UMyGameSubsystem>(GameInstance);

// 2. UWorldSubsystem
UMyWorldSys* Wsys = GetWorld()->GetSubsystem<UMyWorldSys>();

// 3. ULocalPlayerSubsystem
ULocalPlayer* LP = GetWorld()->GetFirstLocalPlayerFromController();
UMyLPSys* Lsys = LP->GetSubsystem<UMyLPSys>();
// 또는 Controller 에서
UMyLPSys* Lsys2 = ULocalPlayer::GetSubsystem<UMyLPSys>(PC->GetLocalPlayer());

// 4. UEngineSubsystem
UMyEngineSys* Esys = GEngine->GetEngineSubsystem<UMyEngineSys>();

// 5. UEditorSubsystem 🛠 (#if WITH_EDITOR)
UMyEditorSys* EdSys = GEditor->GetEditorSubsystem<UMyEditorSys>();
```

### 3.3 Subsystem 간 의존성 명시

```cpp
void UMySubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    // 본 Subsystem 보다 먼저 초기화 의무 — 순환 의존 시 Engine 이 감지
    Collection.InitializeDependency<USaveSubsystem>();
    Collection.InitializeDependency<UAssetManagerSubsystem>();

    // 이제 안전하게 사용
    USaveSubsystem* Save = GetGameInstance()->GetSubsystem<USaveSubsystem>();
}
```

### 3.4 UWorldSubsystem 추가 콜백

```cpp
class UMyWorldSys : public UWorldSubsystem
{
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void PostInitialize() override;          // 모든 World Subsystem Initialize 후
    virtual void OnWorldBeginPlay(UWorld& InWorld) override;   // BeginPlay 직전
    virtual void OnWorldEndPlay(UWorld& InWorld) {}             // EndPlay
    virtual void Deinitialize() override;

protected:
    // 본 Subsystem 이 활성화될 World 종류 제한 (PIE / Editor / Game)
    virtual bool DoesSupportWorldType(EWorldType::Type WorldType) const override
    {
        return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
    }
};
```

### 3.5 ULocalPlayerSubsystem 콜백

```cpp
class UMyLPSys : public ULocalPlayerSubsystem
{
public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    // PlayerController 변경 시 콜백 (Possess / UnPossess 등)
    virtual void PlayerControllerChanged(APlayerController* NewPC) override
    {
        // 예: Input Mapping Context 재구성
        if (auto* EISys = GetLocalPlayer()->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
        {
            EISys->ClearAllMappings();
            EISys->AddMappingContext(DefaultMappingContext, 0);
        }
    }
};
```

---

## 4. 결정 트리 — 어느 Subsystem 베이스 선택?

```
새 Subsystem 작성?
├── Editor 전용 (WITH_EDITOR)?
│   └── ✅ UEditorSubsystem 🛠 (Editor 시작/종료 라이프사이클)
│
├── 데이터가 Engine 시작 시 ~ 종료까지 살아남아야?
│   └── ✅ UEngineSubsystem (Plugin 진입점 / 글로벌 캐시)
│
├── 데이터가 Map 전환 시 살아남아야?
│   └── ✅ UGameInstanceSubsystem ⭐ (Save / Online Session / 설정값)
│
├── 데이터가 LocalPlayer 별 (Couch Co-op 지원)?
│   └── ✅ ULocalPlayerSubsystem (UI Stack / Camera / Input)
│
├── Map 마다 재초기화 필요 + Tick 필요?
│   └── ✅ UTickableWorldSubsystem (NavMesh / 매 프레임 매니저)
│
└── Map 마다 재초기화 필요 + Tick 안 함?
    └── ✅ UWorldSubsystem (Spawned Actor 추적 / World 매니저)
```

### 4.1 자주 헷갈리는 결정

| 시나리오 | 추천 베이스 | 사유 |
|----------|-------------|------|
| 인벤토리 데이터 (Map 전환 보존) | UGameInstanceSubsystem | Map 전환 살아남음 |
| 현재 Map 의 적 매니저 | UWorldSubsystem | Map 마다 새로 |
| HUD / UI Stack (분할 화면 지원) | ULocalPlayerSubsystem | LocalPlayer 별 |
| Achievement / Steam | UGameInstanceSubsystem | 영속 |
| AI Spawner Tick | UTickableWorldSubsystem | World + Tick |
| Damage Number 풀 | UWorldSubsystem | Map 단위 |
| 글로벌 사운드 매니저 | UGameInstanceSubsystem | Map 전환 살아남음 |
| 자산 임포트 도구 🛠 | UEditorSubsystem | Editor 전용 |
| Pluging 진입점 (Module 로드) | UEngineSubsystem | 동적 로드 |

---

## 5. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | `Initialize` 안 `Super` 호출 누락 | **`Super::Initialize` FIRST 의무** |
| 2 | `Deinitialize` 안 `Super` 호출 누락 | **`Super::Deinitialize` LAST 의무** (사용자 cleanup 후) |
| 3 | UObject 멤버 `UPROPERTY()` 누락 | GC Crash — 항상 `UPROPERTY() + TObjectPtr` 의무 (10_ComponentPolicies §3) |
| 4 | `GetWorld()` 호출 시 nullptr (Dedicated Server) | UWorldSubsystem = Initialize 안 안전 / 다른 종 = nullptr 검사 의무 |
| 5 | `GetSubsystem<T>` 매 프레임 호출 (캐싱 안 함) | `Initialize` 또는 `BeginPlay` 안 1회 캐싱 — `TWeakObjectPtr` 또는 멤버 |
| 6 | `ShouldCreateSubsystem` 안 의도 안 맞음 (예: Editor Subsystem 인데 Game 빌드 활성) | `WorldType` / `NetMode` / `WITH_EDITOR` 검사 |
| 7 | Subsystem 끼리 순환 의존 | `Collection.InitializeDependency<T>()` 명시 — Engine 이 순환 감지 |
| 8 | `Tick` 필요한데 일반 `UWorldSubsystem` 사용 | `UTickableWorldSubsystem` + `Tick` override |
| 9 | `LocalPlayerSubsystem` 안 `GetWorld()` 호출 | `GetLocalPlayer()->GetWorld()` 또는 PC 통해 |
| 10 | 🚨 `Initialize` / `Deinitialize` 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 ([`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md)) |

---

## 6. 9_GlobalIteratorPolicy 와의 관계

> **Subsystem 패턴 = 전역 이터레이터 (TActorIterator/TObjectIterator) 회피의 표준 대안**.

```cpp
// ❌ 안티패턴 — 매 호출마다 N개 Actor 순회
TActorIterator<AMyManager> It(GetWorld());
AMyManager* Mgr = It ? *It : nullptr;

// ✅ 정답 — Subsystem 패턴 (등록 1회 / 검색 비용 0)
UMyManagerSubsystem* Mgr = GetGameInstance()->GetSubsystem<UMyManagerSubsystem>();
```

자세한 정책 = [`09_GlobalIteratorPolicy.md`](../../references/09_GlobalIteratorPolicy.md) §대안 7종 §1 (Subsystem 우선).

---

## 7. 체크리스트 (Subsystem 작성 시)

- [ ] 5종 베이스 (`UEngine` / `UEditor` / `UGameInstance` / `UWorld` / `ULocalPlayer`) 중 결정 트리 §4 따라 선택
- [ ] `Initialize` 안 `Super::Initialize(Collection)` 첫 줄
- [ ] `Deinitialize` 안 `Super::Deinitialize()` 마지막 줄 (사용자 cleanup 후)
- [ ] UObject 멤버 = `UPROPERTY()` + `TObjectPtr<T>` 또는 `TStrongObjectPtr` 의무
- [ ] `Initialize`/`Deinitialize` 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` 부착
- [ ] 의존 Subsystem 있으면 `Collection.InitializeDependency<T>()` 명시
- [ ] Server / Client 분기 필요 시 `ShouldCreateSubsystem` override
- [ ] `WorldSubsystem` = `DoesSupportWorldType` override (PIE / Game 만 등)
- [ ] Tick 필요 시 `UTickableWorldSubsystem` (다른 4종 = Tick 불가 → FTSTicker / TimerManager)
- [ ] `GetSubsystem<T>` 결과는 1회 캐싱 (`TWeakObjectPtr` 또는 멤버)
- [ ] Editor 전용 시 `WITH_EDITOR` 가드 + `UEditorSubsystem` 베이스

---

## 8. 관련 sub-skill (cross-link)

### 깊이 자료 (각 Subsystem 종 별)

- [`GameFramework/references/GameInstance.md`](../GameFramework/references/GameInstance.md) — **UGameInstanceSubsystem 깊이** (§3 Save 패턴 + Online Session + Init 흐름)
- [`GameFramework/references/World.md`](../GameFramework/references/World.md) — **UWorldSubsystem 깊이** (Tick Group + Streaming + WorldType 분기)
- [`Input/references/Subsystem.md`](../Input/references/Subsystem.md) — **UEnhancedInputLocalPlayerSubsystem** (IMC Stack + Couch Co-op)
- [`EditorSubsystem/SKILL.md`](../EditorSubsystem/SKILL.md) 🛠 — **UEditorSubsystem 베이스 모듈** (Editor 라이프사이클)
- [`UnrealEd/Subsystems/SKILL.md`](../UnrealEd/Subsystems/SKILL.md) 🛠 — **UEditorActorSubsystem / UEditorAssetSubsystem 등** Editor Subsystem 종합

### 횡단 정책

- [`09_GlobalIteratorPolicy.md`](../../references/09_GlobalIteratorPolicy.md) 🚨 — Subsystem 우선 사용 정책
- [`10_ComponentPolicies.md`](../../references/10_ComponentPolicies.md) §3 — UObject 멤버 GC 방어 (Subsystem 도 동일)
- [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) — Initialize / Deinitialize 콜백 스코프 의무

---

## 9. 검증 로그 (자체 평가)

[`17_QualityCriteria.md`](../../references/17_QualityCriteria.md) 4종 가중:
- Performance 35: ⭐⭐⭐⭐⭐ 33/35 (등록 비용 1회 + 검색 0)
- Memory 25: ⭐⭐⭐⭐⭐ 25/25 (Engine 자동 GC 관리)
- Network 15: ⭐⭐⭐⭐ 13/15 (UFunction RPC 지원 — `GetFunctionCallspace`)
- Maintainability 25: ⭐⭐⭐⭐⭐ 24/25 (5종 비교 + 결정 트리 + 함정 10종 명시)
- **합계: 95/100 ✅**

> 🚨 **Self-evaluation bias 경고** — [`15_EvaluatorRecipe.md`](../../references/15_EvaluatorRecipe.md) 8단계 평가는 다른 Claude 인스턴스 / 사용자 의무.

---

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-06 | 최초 작성. UE 5.5.4 5종 Subsystem (UEngine / UEditor / UGameInstance / UWorld / ULocalPlayer) + UDynamicSubsystem + UTickableWorldSubsystem 통합 매트릭스 + 작성 표준 패턴 + 결정 트리 (9개 시나리오 매핑) + 함정 10종 + 09_GlobalIt