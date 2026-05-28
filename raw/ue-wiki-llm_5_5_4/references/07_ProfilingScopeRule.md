---
name: profiling-scope-rule
description: 🚨 모든 sub-skill 공통 의무 — Tick/TimerManager/FTSTicker/람다/UFunction/OnRep_*/FieldNotify/ActiveTimer 첫 줄에 TRACE_CPUPROFILER_EVENT_SCOPE / SCOPED_NAMED_EVENT / QUICK_SCOPE_CYCLE_COUNTER 부착. 모든 코드 작성 시.
---

# Profiling Scope Rule — Tick · TimerManager · 람다 · UFunction 의무 규약

> **모든 sub-skill에 동일 적용되는 전역 규약**. 본 위키의 어느 카테고리(Render/Slate/Components)·어느 sub-skill을 따라 코드를 작성하든, **매 프레임 호출되거나 외부에서 시간 기반 디스패치되는 모든 진입점**에는 프로파일링 이벤트 스코프를 부착해야 한다.
> CLAUDE.md §8.1 작업 원칙·03_WikiHarness.md §0.1 교차 참조 인덱스에서 본 문서를 참조.
> **소스 검증**: 본 규약의 매크로 사용 패턴은 모두 UE 5.5.4 트리(SlateCore·UMG)에서 grep으로 확인된 실제 사용례 기반.

---

## 0. 한 줄 요약

> **"매 프레임·매 타이머 콜백·바인딩된 UFunction·시간으로 끌리는 람다 — 첫 줄에 프로파일링 스코프"**.

Unreal Insights·Stat Profiler·외부 프로파일러에서 식별 가능한 이름이 없으면 성능 문제가 생겼을 때 **해당 람다/콜백이 어디 있는지 찾을 수 없다**.

---

## 1. 사용할 매크로 (5.5.4 검증)

| 매크로 | 시그니처 | 용도 / 장점 / 단점 |
|--------|----------|--------------------|
| `TRACE_CPUPROFILER_EVENT_SCOPE(Name)` | 컴파일 타임 이름 | **Unreal Insights 표준** — CSV/터미널/UI 모두에서 식별. 가장 권장. |
| `TRACE_CPUPROFILER_EVENT_SCOPE_STR(NameStr)` | 런타임 문자열 | 동적 이름 (예: 위젯 클래스명 포함) |
| `SCOPED_NAMED_EVENT(Name, Color)` | 컴파일 타임 이름 + 색 | **외부 프로파일러** (Pix/Razor/Tracy) 색상 강조 — Slate 본체가 가장 자주 사용 |
| `SCOPED_NAMED_EVENT_TEXT("Lit", FColor::X)` | 리터럴 + 색 | 위와 동일, 가독성 |
| `SCOPED_NAMED_EVENT_FSTRING(FStringVar, FColor::X)` | FString + 색 | UMG `SObjectWidget::Tick` 패턴 (위젯 클래스명 포함) |
| `QUICK_SCOPE_CYCLE_COUNTER(STAT_X)` | STAT 식별자 | **`stat <Group>` 콘솔 표시** — 즉석 STAT, group 정의 불필요 |
| `DECLARE_CYCLE_STAT(...)` + `SCOPE_CYCLE_COUNTER(STAT_X)` | 사전 선언된 STAT | 그룹화된 STAT — 정식 STAT |
| `DECLARE_SCOPE_CYCLE_COUNTER(...)` | 인라인 STAT | 헤더에서 group + name 한번에 |
| `LLM_SCOPE(Tag)` | 메모리 태그 | 메모리 할당 추적 |

**선택 가이드**:
- **새 코드**: `TRACE_CPUPROFILER_EVENT_SCOPE` 권장 (Insights 표준)
- **Slate/UMG 본체 패턴 따라가기**: `SCOPED_NAMED_EVENT(Name, FColor)` (색으로 카테고리 구분)
- **즉석 측정 / 일회성**: `QUICK_SCOPE_CYCLE_COUNTER(STAT_FunctionName_Lambda)`
- **동적 이름 필요**: `SCOPED_NAMED_EVENT_FSTRING` 또는 `TRACE_CPUPROFILER_EVENT_SCOPE_STR`

---

## 2. 의무 부착 위치 (모든 sub-skill 공통)

### 2.1 매 프레임 진입점 — 무조건 스코프

| 진입점 | sub-skill | 스코프 권장 |
|--------|-----------|------------|
| `AActor::Tick(float)` / `UActorComponent::TickComponent(float, ELevelTick, FActorComponentTickFunction*)` | (Engine 모듈, 향후) | `TRACE_CPUPROFILER_EVENT_SCOPE` |
| `UUserWidget::NativeTick(FGeometry, float)` | [`UMG/UUserWidget §4.1.1`](../skills/UMG/references/UUserWidget.md) | `SCOPED_NAMED_EVENT_TEXT("MyWidget::Tick", FColor::Cyan)` 또는 `TRACE_CPUPROFILER_EVENT_SCOPE` |
| `SWidget::Tick(FGeometry, double, float)` | [`SlateCore/SWidget`](../skills/SlateCore/references/SWidget.md) | `SCOPED_NAMED_EVENT(MyWidget_Tick, FColor::Green)` |
| `IInputProcessor::Tick(...)` | [`Slate/EditorApplication §6.1`](../skills/Slate/references/EditorApplication.md) | `TRACE_CPUPROFILER_EVENT_SCOPE` |
| `FSceneViewExtensionBase::*Pass` (RDG 콜백) | (Render 카테고리) | `TRACE_CPUPROFILER_EVENT_SCOPE` + RDG 자체의 `RDG_EVENT_SCOPE` |
| `FTickFunction::ExecuteTick` 자손 | (Engine) | `TRACE_CPUPROFILER_EVENT_SCOPE` |
| `FTSTicker::FDelegateHandle` 콜백 | (Core) | `TRACE_CPUPROFILER_EVENT_SCOPE` |

### 2.2 Time Manager 콜백 — 무조건 스코프

`FTimerManager` / `FTSTicker` / `FTicker` (deprecated) / `UWorld::GetTimerManager()` / `UTickableGameObject` 같은 **시간으로 디스패치**되는 모든 콜백:

```cpp
// ❌ 스코프 없음 — 프로파일러에서 "anonymous lambda" 표시
GetWorld()->GetTimerManager().SetTimer(MyHandle, FTimerDelegate::CreateLambda([this]()
{
    // ... 무거운 작업 ...
}), 0.1f, true);

// ✅ 스코프 부착 — Insights에서 "MyClass::HealthDecayTick" 명확
GetWorld()->GetTimerManager().SetTimer(MyHandle, FTimerDelegate::CreateLambda([this]()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyClass_HealthDecayTick);
    // ... 무거운 작업 ...
}), 0.1f, true);
```

| TimeManager 종류 | 스코프 위치 |
|------------------|------------|
| `FTimerManager::SetTimer(FTimerDelegate, ...)` 람다/UFunction | 콜백 첫 줄 |
| `FTSTicker::AddTicker(FTickerDelegate, Delay)` 람다 | 콜백 첫 줄 |
| `FTickerObjectBase::Tick(float)` override | 첫 줄 |
| `UTickableGameObject::Tick(float)` override | 첫 줄 |
| `UTickableWorldSubsystem::Tick(float)` override | 첫 줄 |
| `SWidget::RegisterActiveTimer(Period, FWidgetActiveTimerDelegate)` 람다 | 콜백 첫 줄 |
| `FCurveSequence::TickSequence` 자손 (이미 베이스에 있음 — `STAT_FCurveSequence_TickPlay`) | (참고용) |

### 2.3 바인딩된 UFunction — 의무 스코프

`AddDynamic` / `AddUObject` / `BindUFunction` / `BindDynamic` 등으로 **델리게이트에 바인딩된** UFUNCTION 또는 일반 함수도 외부에서 임의 시점에 호출되므로 스코프 부착:

```cpp
// ❌ 바인딩된 함수 본체에 스코프 없음
UFUNCTION() void HandleScoreChanged()
{
    UpdateUI();
    PlayAnimation(FlashAnim);
    // ... 어디서 호출되는지 프로파일러로 역추적 어려움
}

// ✅ 첫 줄에 스코프
UFUNCTION() void HandleScoreChanged()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyHUD_HandleScoreChanged);
    UpdateUI();
    PlayAnimation(FlashAnim);
}
```

특히 **자주 발사되는 델리게이트** 핸들러는 의무:
- `INotifyFieldValueChanged::FFieldValueChangedDelegate` 콜백 (FieldNotify)
- `UButton::OnClicked` / `OnPressed` / `OnReleased` 등 입력 콜백 (사용자 인터랙션 — 빈도 낮지만 식별 필요)
- `UMulticastDelegate` 의 옵서버 콜백 (특히 GameState 변경 등 빈번)
- `FOnGameStateChanged::AddDynamic` 같은 게임 이벤트 콜백
- `UGameplayMessageSubsystem` 메시지 콜백
- 네트워크 RepNotify (`OnRep_*`) 함수 — 클라이언트에서 임의 시점에 호출

### 2.4 람다 캡처 — 의무 스코프

람다는 **이름이 없으므로** 프로파일러에서 어디서 정의된 람다인지 추적이 매우 어렵다. 다음 모든 람다에 스코프 의무:

| 람다 종류 | 예시 |
|-----------|------|
| `FTimerDelegate::CreateLambda([](){...})` | TimerManager 콜백 |
| `FTSTicker::AddTicker(FTickerDelegate::CreateLambda([](){...}))` | Ticker 콜백 |
| `Async`/`AsyncTask`/`FFunctionGraphTask::CreateAndDispatchWhenReady` 람다 | 비동기 작업 |
| `ParallelFor([](int32 Index){...})` 람다 | 병렬 루프 — 각 iteration에 스코프 (혹은 외부 1회) |
| `ENQUEUE_RENDER_COMMAND([](FRHICommandList&){...})` | 렌더 스레드 |
| `GameThread`/`AsyncThread` 디스패치 람다 | |
| `FWidgetActiveTimerDelegate::CreateLambda([](double, float){...})` | Slate ActiveTimer |
| `Delegate.AddLambda([](){...})` 일반 멀티캐스트 | |

```cpp
// ❌ 익명
ParallelFor(Items.Num(), [&](int32 Index)
{
    Items[Index].HeavyComputation();
});

// ✅ 스코프
ParallelFor(Items.Num(), [&](int32 Index)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyItem_ComputeParallel);
    Items[Index].HeavyComputation();
});

// 더 좋음 (외부 1회 + 내부 식별 필요 시 STAT)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyItem_ComputeAll);
    ParallelFor(Items.Num(), [&](int32 Index) { Items[Index].HeavyComputation(); });
}
```

### 2.5 RepNotify (`OnRep_*`)

서버 → 클라이언트 복제 후 **임의 시점에 호출** — 사용자가 인지할 수 없으므로 무조건 스코프:

```cpp
UFUNCTION() void UMyComponent::OnRep_CurrentHealth(float OldHealth)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyComponent_OnRep_CurrentHealth);
    // ... UI 갱신, 효과 재생 등
}
```

---

## 3. 스코프를 부착하지 않아도 되는 곳

본 규약은 "매 프레임 / 시간 기반 / 델리게이트" 진입점에만 적용. 다음은 **선택**:

- **생성자·소멸자** (인스턴스 1회) — 단, `PostInitProperties`/`PostLoad`/`BeginDestroy` 도 사실상 1회이지만 대량 객체 로드 시 누적되면 측정 가치 있음 → 의심되면 부착
- **순수 함수 / Getter / Setter** — Slate setter는 자동 인밸리데이션 동반 — 매 프레임 호출 시에만
- **단일 사용자 인터랙션** (예: `UButton::OnClicked` — 사용자 클릭은 빈도 낮음) — 단, 핸들러 내부가 무거우면 부착 권장
- **테스트 코드 / 일회성 디버그**

---

## 4. 표준 부착 패턴 (코드 템플릿)

### 4.1 NativeTick / Tick override

```cpp
void UMyHUDWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);   // ← FIRST (Super 호출 규약)
    SCOPED_NAMED_EVENT_TEXT("MyHUDWidget::Tick", FColor::Cyan);
    // 또는: TRACE_CPUPROFILER_EVENT_SCOPE(MyHUDWidget_Tick);

    UpdateThrobberPhase(InDeltaTime);
    // ...
}
```

> Super 호출과 스코프 순서 — **Super 먼저, 스코프 그 다음**. Super 안의 비용은 SObjectWidget::Tick에서 자체 측정됨 (`SCOPED_NAMED_EVENT_FSTRING(DebugTickEventName, FColor::Turquoise)` — UMG/Private/Slate/SObjectWidget.cpp L118).

### 4.2 FTimerManager 콜백 (UFunction 바인딩)

```cpp
void UMyComponent::BeginPlay()
{
    Super::BeginPlay();
    GetWorld()->GetTimerManager().SetTimer(DecayHandle, this, &UMyComponent::HandleHealthDecay, 1.0f, true);
}

UFUNCTION() void UMyComponent::HandleHealthDecay()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyComponent_HandleHealthDecay);
    CurrentHealth = FMath::Max(0.f, CurrentHealth - DecayPerSec);
    OnHealthChanged.Broadcast(CurrentHealth);
}
```

### 4.3 FTimerManager 콜백 (람다)

```cpp
GetWorld()->GetTimerManager().SetTimer(MyHandle,
    FTimerDelegate::CreateWeakLambda(this, [this]()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(MyComponent_RegenTickLambda);
        if (CurrentHealth < MaxHealth)
        {
            CurrentHealth = FMath::Min(MaxHealth, CurrentHealth + RegenPerSec);
        }
    }),
    /*Period=*/0.5f, /*bLoop=*/true);
```

> **TWeakObjectPtr 캡처 또는 `CreateWeakLambda(this, ...)`** 권장 — 람다 캡처 시 강 참조 함정 회피.

### 4.4 FTSTicker

```cpp
FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateWeakLambda(this, [this](float DeltaTime)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyClass_TickerCallback);
    // 작업
    return true;        // 계속 호출 / false 면 등록 해제
}), /*Delay=*/1.0f);
```

### 4.5 SWidget ActiveTimer

```cpp
RegisterActiveTimer(/*Period=*/0.1f,
    FWidgetActiveTimerDelegate::CreateSP(this, &SMyWidget::HandleActiveTimer));

EActiveTimerReturnType SMyWidget::HandleActiveTimer(double InCurrentTime, float InDeltaTime)
{
    SCOPED_NAMED_EVENT(SMyWidget_ActiveTimer, FColor::Yellow);
    // 작업
    return EActiveTimerReturnType::Continue;
}
```

### 4.6 FieldNotify 옵서버 콜백

```cpp
void UMyHUDWidget::HandleScoreChanged(UObject* Object, FFieldNotificationId FieldId)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyHUDWidget_HandleScoreChanged);
    if (UPlayerStatsViewModel* VM = Cast<UPlayerStatsViewModel>(Object))
    {
        ScoreText->SetText(FText::AsNumber(VM->GetScore()));
    }
}
```

### 4.7 RepNotify

```cpp
UFUNCTION() void UMyComponent::OnRep_CurrentHealth(float OldHealth)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyComponent_OnRep_CurrentHealth);
    OnHealthChanged.Broadcast(CurrentHealth);
}
```

### 4.8 비동기 작업 (Async/ParallelFor/RenderCommand)

```cpp
// 게임 스레드 디스패치
AsyncTask(ENamedThreads::GameThread, [WeakThis = TWeakObjectPtr<UMyClass>(this)]()
{
    if (UMyClass* Self = WeakThis.Get())
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(MyClass_AsyncGameThread_Callback);
        Self->RefreshUI();
    }
});

// 렌더 스레드
ENQUEUE_RENDER_COMMAND(MyRenderCommand)([](FRHICommandListImmediate& RHICmdList)
{
    SCOPED_NAMED_EVENT(MyClass_RenderEnqueue, FColor::Magenta);
    // RHICmdList.* 호출
});
```

### 4.9 동적 이름 (위젯 클래스명 포함)

```cpp
// SObjectWidget.cpp L118 패턴
void UMyUserWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);

    // 위젯 인스턴스마다 다른 이름 (예: WBP_HUD_Player1::Tick)
    const FString DebugName = FString::Printf(TEXT("%s::Tick"), *GetClass()->GetName());
    SCOPED_NAMED_EVENT_FSTRING(DebugName, FColor::Cyan);

    // 작업
}
```

> **주의**: 동적 이름은 매 프레임 FString 생성 비용 — 디자이너/디버그 빌드에서만 활성화하거나 경량 사용. Insights 모드에서는 `TRACE_CPUPROFILER_EVENT_SCOPE_STR(*DebugName)` 도 가능.

---

## 5. 카테고리별 적용 우선순위

| 카테고리 | 핵심 hotspot | 의무 강도 |
|----------|--------------|-----------|
| **[Render]** | RDG pass / SceneViewExtension / 셰이더 디스패치 | 🚨 최우선 — `RDG_EVENT_SCOPE` + `TRACE_CPUPROFILER_EVENT_SCOPE` 동시 |
| **[Slate/UMG]** | NativeTick / NativeOnPaint / SWidget::Tick / ActiveTimer / FieldNotify 콜백 | 🚨 최우선 — Slate 본체 패턴(`SCOPED_NAMED_EVENT`) 따라가기 |
| **[Components]** | Tick / TimerManager 콜백 / RPC 핸들러 / OnRep_* | 🚨 최우선 |
| 사용자 인터랙션 (OnClicked 등) | 본체가 무거우면 부착 | 🟡 권장 |
| 생성자·1회 초기화 | 의심 시 부착 | 🟢 선택 |

---

## 6. 함정 / 안티패턴

| 함정 | 회피 |
|------|------|
| 람다에 스코프 없음 | 람다는 익명 — 무조건 스코프 |
| `AddDynamic`/`AddUObject` 바인딩된 함수에 스코프 없음 | 외부 호출 시점 모름 — 첫 줄 스코프 |
| `OnRep_*` 에 스코프 없음 | 클라이언트 임의 시점 — 첫 줄 스코프 |
| `Super::NativeTick(...)` 보다 스코프 먼저 | Super 의 비용은 베이스가 자체 측정 — Super FIRST + 스코프 |
| 동적 이름 `FString::Printf` 매 프레임 | 디버그 빌드만 또는 경량 |
| `QUICK_SCOPE_CYCLE_COUNTER` 와 STAT 충돌 | 즉석은 `QUICK_*`, 정식 그룹은 `DECLARE_CYCLE_STAT` |
| 같은 이름 여러 위치 | Insights에서 합산되어 출처 모름 — 위치별 고유 이름 (`MyClass_FuncName`) |
| `LLM_SCOPE` 와 CPU 스코프 혼동 | LLM은 메모리 / TRACE_CPU는 시간 |
| 너무 잘게 자른 스코프 | 매크로 자체 비용 (~ns) — 핫루프 내부에선 외부 1회 |

---

## 7. Insights / Stat 콘솔 사용

스코프를 부착했다면 다음 명령으로 확인:

| 명령 | 효과 |
|------|------|
| `stat unit` | Frame/Game/Draw/GPU 시간 |
| `stat gpu` | GPU pass 별 |
| `stat slate` | Slate 전체 그룹 |
| `stat slatedetailed` | Slate 세부 |
| `stat <Group>` | DECLARE_CYCLE_STAT 그룹 |
| `Trace.Start cpu,frame,gpu,slate` | Unreal Insights 트레이스 시작 |
| Unreal Insights 앱 | 트레이스 파일 → 시각화 |

`TRACE_CPUPROFILER_EVENT_SCOPE` 는 **Insights 트레이스에만** 잡힘 (Stat 콘솔에는 안 보임). `QUICK_SCOPE_CYCLE_COUNTER(STAT_X)` 는 **`stat <Group>`** 으로 확인. `SCOPED_NAMED_EVENT` 는 **외부 프로파일러** 색상 강조.

> **Slate 디버깅 cvar** (스코프와 별도): `Slate.InvalidationDebugging.LogInvalidationStack` / `SlateDebugger.Start` / `WidgetReflector` — 자세한 [`SlateCore/Trace`](../skills/SlateCore/references/Trace.md).

---

## 8. 모든 sub-skill에 동일 적용 — 작업 체크리스트

코드 작성 시 다음 체크리스트를 의무 통과:

- [ ] `Native\*Tick` / `Tick` / `TickComponent` 첫 줄에 스코프 부착 (Super 다음)
- [ ] `FTimerManager::SetTimer` / `FTSTicker::AddTicker` 콜백 첫 줄에 스코프
- [ ] 모든 람다 (`CreateLambda` / `AddLambda` / `Async` / `ParallelFor` / `ENQUEUE_RENDER_COMMAND`) 에 스코프
- [ ] `AddDynamic` / `AddUObject` / `BindUFunction` 으로 바인딩된 핸들러 함수 첫 줄에 스코프
- [ ] `OnRep_*` 함수 첫 줄에 스코프
- [ ] FieldNotify 옵서버 콜백 첫 줄에 스코프
- [ ] 위젯 ActiveTimer 콜백 첫 줄에 스코프
- [ ] RDG pass 콜백 / SceneViewExtension 콜백에 `TRACE_CPUPROFILER_EVENT_SCOPE` + `RDG_EVENT_SCOPE` (Render)
- [ ] 동일 이름 여러 위치 충돌 회피 (위치별 고유 이름)
- [ ] (선택) 동적 이름이 필요하면 `SCOPED_NAMED_EVENT_FSTRING` 또는 `TRACE_CPUPROFILER_EVENT_SCOPE_STR`

---

## 9. 관련 sub-skill / 인덱스

- [`UMG/UUserWidget §4.1.1`](../skills/UMG/references/UUserWidget.md) — NativeTick Super 호출 + 본 규약 적용 위치
- [`UMG/UWidget §4.4`](../skills/UMG/references/UWidget.md) — Super 호출 규약
- [`SlateCore/SWidget`](../skills/SlateCore/references/SWidget.md) — SWidget::Tick + ActiveTimer
- [`SlateCore/Animation`](../skills/SlateCore/references/Animation.md) — FCurveSequence::TickPlay 베이스 STAT 참고
- [`SlateCore/Application`](../skills/SlateCore/references/Application.md) — `SCOPED_NAMED_EVENT(Slate_GlobalInvalidate, FColor::Red)` 패턴
- [`SlateCore/Trace`](../skills/SlateCore/references/Trace.md) 🛠 — Slate Insights / Widget Reflector / FSlateDebugging
- [`Slate/EditorApplication §6.1`](../skills/Slate/references/EditorApplication.md) — IInputProcessor::Tick
- [`04_OverrideIndex.md §6`](./04_OverrideIndex.md) — Super 호출 통합 표 (스코프와 함께 부착)
- [`06_InvalidationHotspots.md`](./06_InvalidationHotspots.md) — 인밸리데이션 hotspot (스코프 부착 필수 위치 다수)

---

## 10. 갱신 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-04 | 최초 작성. UE 5.5.4 SlateCore/UMG 본체 grep 검증 (SObjectWidget.cpp L118 / SlateApplicationBase.cpp L227 / SlateInvalidationRoot.cpp L379+ / CurveSequence.cpp L282 / ScrollBox.cpp L690 / WidgetComponent.cpp L860 / SWorldWidgetScreenLayer.cpp L102 / UserWidget.cpp L844). 8섹션 + 작업 체크리스트 + cross-reference 9종. |
