---
name: umg-uuserwidget-invalidationdeep
description: UUserWidget 깊이 자료 — Native* 가상 함수 30+ + 라이프사이클 5종 (NativeOnInitialized/PreConstruct/Construct/Destruct/Tick) + Super 호출 규약 + 인밸리데이션 갱신 흐름 + NativePaint 함정 + InvalidationBox + 5가지 핵심 원칙.
---

# UMG / UUserWidget — InvalidationDeep Reference

> 본 문서는 [`SKILL.md §4~§5`](../SKILL.md) 의 깊이 자료. 메인 SKILL.md 는 §1~§3 (개요/핵심클래스/API) + §6 예제. 본 reference 는 가상 함수 30+ + 인밸리데이션 의무 섹션.
>
> **트리거**: NativeConstruct / NativeTick / NativePaint override / 인밸리데이션 디버깅 / Super 호출 규약 / TickFrequency 결정 / InvalidationBox 사용 시 로드.

---

## 1. 가상 함수 (오버라이드 포인트) — Native* 30+

### 1.1 라이프사이클 (5 — 가장 자주 override)

| 시그니처 | 위치 | 호출 시점 / 용도 |
|----------|------|------------------|
| `virtual void NativeOnInitialized()` | UserWidget.h L1574 | **`Initialize()` 안에서 한 번만** — 외부 시스템 구독·초기 데이터 로드. PIE/standalone 모두 동작. |
| `virtual void NativePreConstruct()` | UserWidget.h L1575 | 디자이너 미리보기·실행 전 한 번. **디자이너 변경 즉시 반영**되는 hook. |
| `virtual void NativeConstruct()` | UserWidget.h L1576 | **뷰포트 추가될 때마다** — 데이터 새로고침·델리게이트 바인딩. |
| `virtual void NativeDestruct()` | UserWidget.h L1577 | 뷰포트에서 제거될 때 — 델리게이트 언바인딩·외부 참조 해제. |
| `virtual void NativeTick(const FGeometry&, float DeltaTime)` | UserWidget.h L1578 | **매 프레임** (TickFrequency 결정 시) — **최대한 회피**. ActiveTimer / 이벤트 기반으로 대체 권장. |

#### 1.1.1 🚨 Super 호출 순서 + 구획별 초기화 책임

라이프사이클 5종은 **각 베이스가 책임지는 초기화 구획**이 다르다.

##### Super 호출 규칙 (모든 UUserWidget 파생 클래스의 의무)

| 가상 함수 | Super 호출 위치 | 위반 시 증상 |
|-----------|----------------|--------------|
| `NativeOnInitialized()` | **첫 줄** (Super FIRST) | InputComponent 미생성 → `BindAction` 무시 / Extension 미초기화 / OnInitialized BP 이벤트 미발화 |
| `NativePreConstruct()` | **첫 줄** (Super FIRST) | DesiredFocusWidget 미해석 → 자동 포커스 안 잡힘 / Extension PreConstruct 누락 / PreConstruct BP 이벤트 미발화 |
| `NativeConstruct()` | **첫 줄** (Super FIRST) | InputScriptDelegates 미시작 → BP `OnKeyDown` 등 안 동작 / PlayerController 변경 리스너 미등록 / Construct BP 이벤트 미발화 / `UpdateCanTick` 안 돌아 Tick이 비활성으로 남음 |
| `NativeDestruct()` | **마지막 줄** (Super LAST) | Extension Destruct가 사용자 cleanup보다 먼저 실행돼 핸들 무효화 / 입력 델리게이트가 사용자 cleanup 중 콜백 발사 / OnNativeDestruct broadcast가 너무 늦게 발생 |
| `NativeTick()` | **첫 줄** (Super FIRST) | `TickActionsAndAnimation` 미실행 → UMG Animation/Latent Action 정지 → 시퀀스 진행 안 함 |

> **일반 규칙**: 초기화 계열(`Initialized`/`PreConstruct`/`Construct`/`Tick`) 은 **Super 먼저**, 정리 계열(`Destruct`) 은 **Super 마지막**. UE 전체 라이프사이클 관례(AActor::EndPlay·UObject::BeginDestroy 의 Super LAST)와 동일.

##### 구획별 초기화 (베이스에서 자동 수행되는 것)

| 라이프사이클 단계 | 베이스 자동 처리 (UserWidget.cpp 라인) | 사용자가 추가로 할 일 |
|------------------|---------------------------------------|---------------------|
| `NativeOnInitialized` (L1824) | (1) `CreateInputComponent()` → UInputComponent 생성 ·BindAction 활성화<br>(2) `BPClass->ForEachExtension(Initialize)`<br>(3) `Extensions[i]->Initialize()`<br>(4) `OnInitialized()` BP 이벤트 | 외부 시스템 구독·초기 데이터 로드·서브시스템 핸들 캐싱 |
| `NativePreConstruct` (L1847) | (1) `BPClass extensions PreConstruct(bIsDesignTime)`<br>(2) `Extensions[i]->PreConstruct(bIsDesignTime)`<br>(3) `DesiredFocusWidget.Resolve(WidgetTree)`<br>(4) `PreConstruct(bIsDesignTime)` BP 이벤트 | 디자이너 미리보기에 즉시 반영해야 하는 초기 시각 상태 |
| `NativeConstruct` (L1874) | (1) `StartProcessingInputScriptDelegates()`<br>(2) `StartListeningForPlayerControllerChanges()`<br>(3) `BPClass extensions Construct`<br>(4) `Extensions[i]->Construct()`<br>(5) `Construct()` BP 이벤트<br>(6) `UpdateCanTick()` | 델리게이트 바인딩·뷰모델 구독·데이터 새로고침·`PlayAnimation` 호출·ActiveTimer 등록 |
| `NativeDestruct` (L1908) | (1) `StopProcessingInputScriptDelegates()`<br>(2) `StopListeningForPlayerControllerChanges()`<br>(3) `OnNativeDestruct.Broadcast(this)`<br>(4) `Destruct()` BP 이벤트<br>(5) `Extensions Destruct` (역순)<br>(6) `BPClass extensions Destruct` | 델리게이트 언바인딩·`StopAllAnimations()`·ActiveTimer 해제·외부 시스템 구독 해제 → **이 모든 것을 끝낸 뒤 마지막에 `Super::NativeDestruct()` 호출** |
| `NativeTick` (L2086) | `TickActionsAndAnimation(InDeltaTime)` → 애니메이션·Latent Action 진행 | (가능하면 사용 X). 부득이하면 Super FIRST 후 사용자 로직 |

##### 표준 override 템플릿

```cpp
void UMyUserWidget::NativeOnInitialized()
{
    Super::NativeOnInitialized();       // ← FIRST: InputComponent / Extensions / OnInitialized BP

    if (UGameInstance* GI = GetGameInstance())
    {
        if (UMySubsystem* Sub = GI->GetSubsystem<UMySubsystem>())
        {
            Sub->OnDataChanged.AddDynamic(this, &UMyUserWidget::HandleDataChanged);
        }
    }
}

void UMyUserWidget::NativePreConstruct()
{
    Super::NativePreConstruct();        // ← FIRST: Extensions / DesiredFocus / PreConstruct BP

    if (TitleText)
    {
        TitleText->SetText(IsDesignTime() ? FText::FromString(TEXT("[Preview]")) : DefaultTitle);
    }
}

void UMyUserWidget::NativeConstruct()
{
    Super::NativeConstruct();           // ← FIRST: 입력 델리게이트·PC 리스너·Extensions·Construct BP·UpdateCanTick

    RefreshFromViewModel();
    if (FadeInAnim)
    {
        PlayAnimation(FadeInAnim);
    }
}

void UMyUserWidget::NativeDestruct()
{
    // 사용자 cleanup 먼저
    StopAllAnimations();
    if (UGameInstance* GI = GetGameInstance())
    {
        if (UMySubsystem* Sub = GI->GetSubsystem<UMySubsystem>())
        {
            Sub->OnDataChanged.RemoveDynamic(this, &UMyUserWidget::HandleDataChanged);
        }
    }

    Super::NativeDestruct();            // ← LAST: 입력 델리게이트 중지·OnNativeDestruct broadcast·Destruct BP·Extensions Destruct
}

void UMyUserWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);  // ← FIRST: TickActionsAndAnimation
    UpdateThrobberPhase(InDeltaTime);
}
```

##### `Initialize()` vs `NativeOnInitialized()` — 한 단계 위 진입점

`UUserWidget::Initialize()` (UserWidget.h L300) 는 `CreateWidget<T>` 가 자동 호출하는 **인스턴스 1회 초기화**. 내부에서 `WidgetTree` 복제 + `BindWidget` 메타 자동 연결 + **`NativeOnInitialized()` 호출**.

| 함수 | Super 호출 | 호출 횟수 | 책임 |
|------|-----------|-----------|------|
| `Initialize()` | FIRST + return Super 결과 | 인스턴스당 1회 | WidgetTree 복제·BindWidget 연결·NativeOnInitialized 호출 |
| `NativeOnInitialized()` | FIRST | 인스턴스당 1회 (Initialize 내부) | InputComponent 생성·Extensions Initialize·OnInitialized BP |

> 외부 시스템 구독·캐싱은 **`NativeOnInitialized`** 가 표준.

### 1.2 Paint (1 — 인밸리데이션 함정 의무)

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual int32 NativePaint(...) const` | UserWidget.h L1584 | **최대한 회피** — override 시 자동 휘발성처럼 동작해 캐시 비활성. 자세한 LayerId/DrawCall 함정은 §2.4 + [`SlateCore/Drawing/§5`](../../../SlateCore/references/Drawing.md). |

### 1.3 입력 (FReply 반환)

#### 키보드 / 문자 / 아날로그

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual FReply NativeOnPreviewKeyDown(...)` | L1600 | 자식 위젯 처리 전. 가로채기. |
| `virtual FReply NativeOnKeyDown(...)` | L1601 | 키 누름. 자식 처리 후. |
| `virtual FReply NativeOnKeyUp(...)` | L1602 | 키 뗌. |
| `virtual FReply NativeOnKeyChar(...)` | L1599 | 문자 입력 (IME). |
| `virtual FReply NativeOnAnalogValueChanged(...)` | L1603 | 게임패드 스틱 등. |

#### 마우스 / 포인터

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual FReply NativeOnPreviewMouseButtonDown(...)` | L1605 | 자식 처리 전. |
| `virtual FReply NativeOnMouseButtonDown(...)` | L1604 | 클릭. |
| `virtual FReply NativeOnMouseButtonUp(...)` | L1606 | 뗌. |
| `virtual FReply NativeOnMouseButtonDoubleClick(...)` | L1611 | 더블 클릭. |
| `virtual FReply NativeOnMouseMove(...)` | L1607 | 이동. |
| `virtual void NativeOnMouseEnter(...)` | L1608 | 진입. |
| `virtual void NativeOnMouseLeave(...)` | L1609 | 이탈. |
| `virtual FReply NativeOnMouseWheel(...)` | L1610 | 휠. |

#### 포커스 / 내비게이션

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual FReply NativeOnFocusReceived(...)` | L1593 | 포커스 획득. |
| `virtual void NativeOnFocusLost(...)` | L1594 | 포커스 상실. |
| `virtual void NativeOnFocusChanging(...)` | L1595 | 포커스 이동 중. |
| `virtual void NativeOnAddedToFocusPath(...)` | L1596 | 포커스 경로에 들어감. |
| `virtual void NativeOnRemovedFromFocusPath(...)` | L1597 | 포커스 경로에서 빠짐. |
| `virtual bool NativeSupportsKeyboardFocus()` | L1590 | 포커스 받을 수 있는지. |
| `virtual bool NativeSupportsCustomNavigation() const` | L1591 | 커스텀 내비. |
| `virtual bool NativeIsInteractable()` | L1589 | 입력 인터랙션 대상. |

#### 드래그 앤 드롭

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual void NativeOnDragDetected(...)` | L1612 | 드래그 시작 — `OutOperation` 에 `NewObject<UMyDragOp>` 할당. |
| `virtual void NativeOnDragEnter(...)` | L1613 | 드래그 진입. |
| `virtual void NativeOnDragLeave(...)` | L1614 | 드래그 이탈. |
| `virtual bool NativeOnDragOver(...)` | L1615 | 드래그 호버 — true 반환 시 드롭 가능. |
| `virtual bool NativeOnDrop(...)` | L1616 | 드롭. |
| `virtual void NativeOnDragCancelled(...)` | L1617 | 취소. |

#### 터치 / 모션 (모바일·태블릿)

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual FReply NativeOnTouchStarted(...)` | L1619 | 터치 시작. |
| `virtual FReply NativeOnTouchMoved(...)` | L1620 | 터치 이동. |
| `virtual FReply NativeOnTouchEnded(...)` | L1621 | 터치 끝. |
| `virtual FReply NativeOnTouchGesture(...)` | L1618 | 제스처 (Pinch/Pan/Rotate). |
| `virtual FReply NativeOnTouchForceChanged(...)` | L1623 | 압력 변경. |
| `virtual FReply NativeOnTouchFirstMove(...)` | L1624 | 첫 이동. |
| `virtual FReply NativeOnMotionDetected(...)` | L1622 | 디바이스 모션. |

### 1.4 UWidget / UVisual / UObject override

| 시그니처 | 위치 | 의미 |
|----------|------|------|
| `virtual UWorld* GetWorld() const override` | UserWidget.h | **이 위젯의 World**. |
| `virtual void PostDuplicate(bool bDuplicateForPIE) override` | UserWidget.h | 복제 시. |
| `virtual void BeginDestroy() override` | UserWidget.h | UObject 파괴. |
| `virtual void PostLoad() override` | UserWidget.h | 디스크 로드. |
| `virtual bool Initialize()` | UserWidget.h L300 | **위젯 인스턴스 초기화**. |
| `virtual void ReleaseSlateResources(bool bReleaseChildren) override` | UserWidget.h | UVisual override. |
| `virtual void SynchronizeProperties() override` | UserWidget.h | UWidget override. |
| `virtual ULocalPlayer* GetOwningLocalPlayer() const override` | UserWidget.h L411 | UWidget override. |
| `virtual APlayerController* GetOwningPlayer() const override` | UserWidget.h L433 | UWidget override. |

### 1.5 INamedSlotInterface (3, 메인 §2.3 참조)

---

## 2. 🚨 인밸리데이션 / 갱신 흐름 (의무 섹션)

UUserWidget 의 갱신은 **5가지 시점**에서 발생하며, 각각의 의미와 함정이 다르다.

### 2.1 라이프사이클 시점별 인밸리데이션

```
CreateWidget<T>
  └─ Initialize() ──→ NativeOnInitialized()        ① 한 번만 — 인밸리데이션 X (위젯 트리 미생성)
                  └─ InitializeNamedSlots()

AddToViewport
  └─ RebuildWidget ──→ SObjectWidget 생성           ② SWidget 트리 생성 — 첫 페인트 트리거
  └─ NativePreConstruct                             ③ 디자이너/실행 전 — UPROPERTY → 위젯 동기화
  └─ NativeConstruct                                ④ 매 추가 시 — 데이터 새로고침
                                                      이 시점에 SetVisibility/SetText 등 setter 호출 → 자동 인밸리데이션

[매 프레임]
  └─ NativeTick (TickFrequency=Auto/Never)          ⑤ Tick 안에서 SetXxx 호출 → 인밸리데이션 발생
                                                      → 가능하면 회피 (이벤트 기반 권장)

RemoveFromParent
  └─ NativeDestruct                                 ⑥ 정리 — 인밸리데이션 무관
  └─ ReleaseSlateResources                          ⑦ SWidget 해제

BeginDestroy                                         ⑧ UObject 파괴
```

### 2.2 SynchronizeProperties (UWidget override) 호출 시점

부모 [`UWidget/SKILL.md §5.1`](../../UWidget/SKILL.md) 의 3가지 시점이 모두 적용:

1. **디자이너에서 UPROPERTY 변경** (PostEditChangeProperty)
2. **`CreateWidget<T>` 시 Construct 직후** (Initialize 안에서)
3. **RerunConstructionScript** 같은 컨텍스트

UUserWidget 의 자식 BP 위젯도 SynchronizeProperties 가 호출되어 자식 트리 전체 갱신.

### 2.3 EWidgetTickFrequency — Tick 비용 제어

| 값 | 동작 | 권장 사용 |
|----|------|-----------|
| `Never` | 절대 NativeTick 호출 안 함 | **정적 HUD / 메뉴 — 권장** |
| `Auto` | BP tick 함수 / latent action / 애니메이션 / 비-UserWidget 부모 native tick 시 자동 활성 | 동적 HUD (체력바 부드러운 보간 등) |

**`Auto` 일 때 Tick 비용** — 매 프레임 함수 호출 + 위젯 트리 traverse. 100개 위젯이 모두 Auto 면 100번 호출. 정말 필요한 위젯만 Auto.

**클래스 단위 비활성** — `UCLASS(meta=(DisableNativeTick))` 으로 native tick 자체를 막음.

### 2.4 ⚠ NativeOnPaint / NativePaint override 함정 (의무)

`UUserWidget::NativePaint` (L1584) override 는 **마지막 수단** — 다음 함정이 따라온다:

| 함정 | 영향 | 회피 |
|------|------|------|
| `NativePaint` override 위젯은 **자동 휘발성** 처럼 동작 | `SInvalidationPanel`/`UInvalidationBox` 캐시 비활성 | 가능하면 표준 UMG 위젯 조합. 직접 그리기 영역만 작은 SLeafWidget(C++) 으로 분리 후 외부에서 `UInvalidationBox` 로 감싸기. |
| `LayerId` 반환 누락 → 자식 위젯이 가려짐 | 텍스트 위에 박스가 덮이는 등 시각 버그 | **반드시 `Super::NativePaint(...)` 의 반환값 사용** + 그 위에 `+1`. |
| 매 프레임 새 `FSlateBrush` 생성 | DrawCall 배치 깨짐 + 메모리 압박 | 멤버에 캐시하거나 `FAppStyle::Get().GetBrush(...)`. |
| `Canvas Panel ZOrder` 와 `LayerId` 혼동 | 의도와 다른 그리기 순서 | **ZOrder 는 부모 패널이 자식을 정렬할 때만, OnPaint 안에서는 LayerId 만 사용**. |
| `UMG` 위젯과 직접 그린 element 혼합 | LayerId 충돌 | 직접 그린 영역을 별도 SLeafWidget 으로 격리하고 그 LayerId 만 관리. |

올바른 NativePaint 패턴:

```cpp
virtual int32 NativePaint(const FPaintArgs& Args, const FGeometry& Geo,
                          const FSlateRect& Cull, FSlateWindowElementList& Out,
                          int32 LayerId, const FWidgetStyle& Style, bool bEnabled) const override
{
    int32 NewLayer = Super::NativePaint(Args, Geo, Cull, Out, LayerId, Style, bEnabled);

    FSlateDrawElement::MakeBox(Out, NewLayer + 1, Geo.ToPaintGeometry(),
                               CachedBrush.Get(), ESlateDrawEffect::None,
                               FLinearColor::White);

    return NewLayer + 2;
}
```

**자세한 LayerId 단조 증가 / DrawCall 배치 (FSlateElementBatcher) / 텍스처 아틀라스 가이드는 [`SlateCore/Drawing/§5`](../../../SlateCore/references/Drawing.md) 의무 섹션 참조**.

### 2.5 UInvalidationBox — 정적 영역 캐싱

```cpp
// 디자이너에서 정적 영역(자주 안 변하는 헤더·인벤토리 그리드)을 UInvalidationBox 안에 배치
//   → SInvalidationPanel 의 캐시 활용
//   → 매 프레임 페인트 비용 0
// 단:
//   - 안에 `NativePaint` override 위젯 있으면 캐시 무효 → 손해
//   - 안에 ForceVolatile(true) 위젯 있으면 캐시 무효 → 손해
//   - 안에 `SetXxx` 자주 호출되는 위젯 있으면 SlowPath 빈번 → 손해
```

자세한 SlowPath/FastPath 흐름은 [`SlateCore/Drawing/§4`](../../../SlateCore/references/Drawing.md) 의무 섹션.

### 2.6 5가지 핵심 원칙

1. **`TickFrequency = Never`** 우선 — 정적 위젯에 NativeTick 비활성. 동적 갱신은 이벤트 기반·`ActiveTimer`.
2. **`NativeOnPaint` 마지막 수단** — 표준 UMG 위젯 조합으로 표현 안 될 때만. override 시 LayerId 단조 증가 + Super 반환값 사용.
3. **`UInvalidationBox`** 안에 정적 영역만. 휘발성·NativePaint 위젯은 외부에.
4. **표준 setter 사용** — `MyTextBlock->SetText(...)` 가 자동 인밸리데이션. 직접 멤버 대입 금지.
5. **`UCanvasPanelSlot::ZOrder` ≠ Slate `LayerId`** — 부모 패널 자식 정렬 vs 한 위젯 안 그리기 순서. 혼동 금지.

---

## 3. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-06 | UMG/references/UUserWidget.md §4~§5 에서 분리. 메인 32KB → ~13KB / reference ~17KB. |
