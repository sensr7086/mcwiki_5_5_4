---
name: umg-uuserwidget
description: UUserWidget - PreConstruct (디자이너) + Construct + Destruct + NativeConstruct + NativeDestruct + Tick + InvalidateLayoutAndVolatility.
---

# UMG / UUserWidget

> 부모 모듈: [`UMG`](../SKILL.md) · UE 5.7.4
> 다루는 영역: BP 위젯의 베이스 — `UUserWidget : UWidget, INamedSlotInterface` + **Native\* 라이프사이클 30+ virtual** (NativeOnInitialized/NativePreConstruct/NativeConstruct/NativeDestruct/NativeTick + 입력/포커스/드래그/터치/Paint) + `EWidgetTickFrequency` (Never/Auto) + `UWidgetTree` + `UWidgetBlueprintGeneratedClass` + `BindWidget`/`BindWidgetOptional` 메타 + `INamedSlotInterface` + `AddToViewport`/`AddToPlayerScreen` + `GetOwningPlayer`
> **🚨 인밸리데이션 갱신 흐름은 본 sub-skill 의 의무 섹션 (§5)** + **`NativeOnPaint`/`NativePaint` override 시 LayerId 중복·DrawCall 폭증·자동 휘발성 함정** ([`SlateCore/SKILL.md §5.1`](../../SlateCore/SKILL.md) 표 + [`SlateCore/Drawing/§5`](../../SlateCore/references/Drawing.md) 의무 섹션 cross-reference).
> 관련 sub-skill: [`UWidget/`](../UWidget/SKILL.md), [`PanelWidgets/`](../PanelWidgets/SKILL.md), [`ListWidgets/`](../ListWidgets/SKILL.md), [`ViewModel/`](../ViewModel/SKILL.md), [`../../SlateCore/Drawing/`](../../SlateCore/references/Drawing.md), [`../../SlateCore/Input/`](../../SlateCore/references/Input.md)

---

## 1. 개요

`UUserWidget` 은 **블루프린트 위젯의 C++ 베이스**다. 디자이너가 `.uasset` 위젯 블루프린트를 만들면 자동으로 `UUserWidget` 자손 클래스가 생성되고, C++에서는 `UUserWidget` 또는 그 자손을 상속해서 Native 로직을 작성한다.

```
UWidget (UMG/references/UWidget.md)
  └─ UUserWidget : UWidget, INamedSlotInterface  (★ BP 위젯의 베이스)
       ├─ UWidgetTree         (자식 위젯 트리 — 디자이너 트리)
       ├─ Native* virtual 30+ (라이프사이클·입력·페인트)
       ├─ BindWidget 메타     (디자이너 위젯 ↔ C++ 멤버 자동 연결)
       └─ EWidgetTickFrequency (Never/Auto — Tick 비용 제어)

생성 흐름:
  CreateWidget<T>(World, Class)
   → NewObject + Initialize() (한 번)
     → InitializeNamedSlots
     → NativeOnInitialized()
   → AddToViewport / AddToPlayerScreen
     → RebuildWidget → SObjectWidget 생성
     → NativePreConstruct → BP PreConstruct
     → NativeConstruct → BP Construct
   → 매 프레임 NativeTick (TickFrequency 결정에 따라)
   → RemoveFromParent
     → NativeDestruct → BP Destruct
   → BeginDestroy → ReleaseSlateResources
```

**왜 Native\* 가 30+개인가** — 모든 입력 이벤트(키/마우스/터치/드래그/포커스/모션)와 라이프사이클·페인트를 BP 와 C++ 둘 다에서 override 가능하게 하기 위해. Native 가 먼저 호출되고, 기본 구현이 BP 의 같은 이름 이벤트를 호출.

---

## 2. 핵심 헤더와 클래스

### 2.1 본체 사슬 (`Public/Blueprint/`)

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Blueprint/UserWidget.h` | `class UUserWidget : public UWidget, public INamedSlotInterface` (L283) | **BP 위젯의 베이스**. 친구 `SObjectWidget`. UObject 라이프사이클 + Native\* virtual + Initialize + AddToViewport/PlayerScreen + ColorAndOpacity/ForegroundColor/Padding/InputActionPriority/IsFocusable/InputActionBlocking 등 BP 노출 멤버. |
| `Blueprint/UserWidget.h` | `enum class EWidgetTickFrequency : uint8` (L120) | **Never** (절대 tick 안 함) / **Auto** (BP tick 함수 / latent action / 애니메이션 / 비-UserWidget 부모 native tick 시 자동). `meta=(DisableNativeTick)` 클래스 메타로 native tick 비활성. |
| `Blueprint/UserWidget.h` | `enum class EWidgetAnimationEvent : uint8` (Started/Finished) | UWidgetAnimation 시작/종료 이벤트. |
| `Blueprint/WidgetTree.h` | `class UWidgetTree : public UObject, public INamedSlotInterface` (L19) | 위젯 트리 — 디자이너가 만든 자식 계층. `FindWidget(FName)`/`FindWidget(SWidget)`/`RemoveWidget`/`FindWidgetParent`/`FindWidgetChild`/`FindChildIndex`. |
| `Blueprint/WidgetBlueprintGeneratedClass.h` | `class UWidgetBlueprintGeneratedClass : public UBlueprintGeneratedClass` (L80) | BP 컴파일 결과 클래스. `WidgetTree` (DuplicateTransient), `Extensions`, `bClassRequiresNativeTick`, `bCanCallInitializedWithoutPlayerContext`, `Bindings`, `Animations`, `NamedSlots`. |
| `Blueprint/UserWidgetPool.h` | `FUserWidgetPool` | UUserWidget 인스턴스 풀 — `UListView` 등이 아이템 위젯 재사용에 활용. |
| `Blueprint/IUserListEntry.h` / `IUserObjectListEntry.h` | `IUserListEntry` / `IUserObjectListEntry` | `UListView`/`UTreeView`/`UTileView` 의 엔트리 위젯 인터페이스. [`ListWidgets/`](../ListWidgets/SKILL.md) 참조. |
| `Blueprint/WidgetNavigation.h` | `UWidgetNavigation` | 디자이너에서 설정하는 내비게이션 정책 (UWidget setter 의 디자이너 측). |
| `Blueprint/WidgetChild.h` | `FWidgetChild` | 위젯 자식 참조 헬퍼. |
| `Blueprint/SlateBlueprintLibrary.h`/`WidgetBlueprintLibrary.h`/`WidgetLayoutLibrary.h` | 정적 BP 함수 묶음 | `ProjectWorldLocationToWidgetPosition` / `GetMousePositionOnViewport` 등. |
| `Blueprint/DragDropOperation.h` | `UDragDropOperation` | UMG 드래그 앤 드롭 작업 베이스. `NativeOnDragDetected` 의 `OutOperation`. |
| `Blueprint/AsyncTaskDownloadImage.h` | `UAsyncTaskDownloadImage` | URL → UTexture2D 비동기 다운로드. |
| `Blueprint/GameViewportSubsystem.h` | `UGameViewportSubsystem` | 뷰포트 위젯 추가/제거 관리 (5.x). `AddToViewport` 가 내부적으로 사용. |
| `Blueprint/UMGSequencePlayMode.h` | `EUMGSequencePlayMode` | UWidgetAnimation 재생 모드 (Forward/Reverse/PingPong) — ※ 본 위키 제외 영역. |
| `Components/NamedSlot.h`/`NamedSlotInterface.h` | `UNamedSlot` / `INamedSlotInterface` | 부모 BP 가 자식 BP 에 컨텐츠 주입 (named slot — 슬롯 이름으로). |

### 2.2 핵심 멤버 (UUserWidget)

| 멤버 | 위치 | 의미 |
|------|------|------|
| `EWidgetTickFrequency TickFrequency` | UserWidget.h L1717 | 기본 `Auto` — `Never` 권장 (성능). |
| `FLinearColor ColorAndOpacity` (L998) | UserWidget.h | 위젯 트리 전체 색·투명도. |
| `FSlateColor ForegroundColor` (L1009) | UserWidget.h | 텍스트·아이콘 등 forecolor. |
| `FMargin Padding` (L1026) | UserWidget.h | 위젯 외곽 padding. |
| `int32 InputActionPriority` (L1030) | UserWidget.h | 입력 액션 우선순위. |
| `bool bIsFocusable` (L1035) | UserWidget.h | 키보드 포커스 받을 수 있는지. |
| `bool bIsInputActionBlocking` (L1039) | UserWidget.h | 입력 액션 차단. |
| `class UWidgetTree* WidgetTree` | (BP 컴파일 시 주입) | BP 가 만든 자식 위젯 트리. |

### 2.3 INamedSlotInterface (3 virtual)

```cpp
virtual void GetSlotNames(TArray<FName>& SlotNames) const override;       // 사용 가능한 슬롯 이름들
virtual UWidget* GetContentForSlot(FName SlotName) const override;        // 슬롯의 컨텐츠
virtual void SetContentForSlot(FName SlotName, UWidget* Content) override; // 슬롯에 컨텐츠 설정
```

부모 BP 가 자식 BP 의 `UNamedSlot` 에 위젯을 주입할 때 사용. 자식 BP 의 디테일 패널에 named slot 이 노출됨.

---

## 3. 자주 쓰는 API

### 3.1 위젯 인스턴스 생성·뷰포트 추가 (가장 흔함)

```cpp
// === 인스턴스 생성 (Initialize 자동 호출됨) ===
UMyHUDWidget* HUD = CreateWidget<UMyHUDWidget>(GetWorld(), HUDClass);    // World context
// 또는 PlayerController 컨텍스트 (입력 라우팅)
UMyHUDWidget* HUD = CreateWidget<UMyHUDWidget>(PlayerController, HUDClass);

// === 뷰포트 추가 (이때 Construct 흐름 시작) ===
HUD->AddToViewport(/*ZOrder=*/0);                                         // L345 — 전체 화면
HUD->AddToPlayerScreen(/*ZOrder=*/10);                                    // L354 — 스플릿스크린의 한 플레이어 영역만

// === 제거 ===
HUD->RemoveFromParent();                                                  // 5.1+ 권장
// HUD->RemoveFromViewport();                                             // L361 — DEPRECATED 5.1

// === 플레이어 컨텍스트 ===
HUD->SetOwningPlayer(MyPlayerController);                                 // L450
HUD->SetPlayerContext(FLocalPlayerContext(MyLocalPlayer));                // L402
APlayerController* PC = HUD->GetOwningPlayer();                           // L433
ULocalPlayer* LP      = HUD->GetOwningLocalPlayer();                      // L411
const FLocalPlayerContext& Ctx = HUD->GetPlayerContext();                 // L405
```

### 3.2 BindWidget / BindWidgetOptional 패턴

```cpp
UCLASS()
class UMyHUDWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    // ★ 디자이너가 같은 이름의 위젯을 두면 자동 연결
    //    이름 안 맞으면 컴파일 에러
    UPROPERTY(meta=(BindWidget))
    UTextBlock* HealthText;

    UPROPERTY(meta=(BindWidget))
    UProgressBar* HealthBar;

    // ★ 옵션 — 디자이너가 안 두어도 컴파일 OK (런타임에 nullptr 체크)
    UPROPERTY(meta=(BindWidgetOptional))
    UImage* StatusIcon;

    // ★ 애니메이션 바인딩 — UWidgetAnimation 동일 이름과 자동 연결 (Animation/ 별도 — 본 위키 제외)
    UPROPERTY(meta=(BindWidgetAnim), Transient)
    UWidgetAnimation* OpenAnim;
};
```

**디자이너에서 `HealthText` 라는 이름의 `Text Block` 위젯을 두면**, 위젯 컴파일 시 자동으로 `HealthText` 멤버에 그 인스턴스가 할당됨. 디자이너가 위젯 이름을 바꾸거나 삭제하면 — `BindWidget` 은 컴파일 에러, `BindWidgetOptional` 은 런타임 nullptr.

### 3.3 위젯 트리 검색 / 조작

```cpp
UWidget* W = WidgetTree->FindWidget(FName("MyButton"));                   // WidgetTree.h
UButton* B = WidgetTree->FindWidget<UButton>(FName("MyButton"));          // 템플릿 캐스트

int32 ChildIdx;
UPanelWidget* Parent = UWidgetTree::FindWidgetParent(MyWidget, ChildIdx); // 정적

UWidget* Child = UWidgetTree::FindWidgetChild(SomePanel, FName("Slot1"), ChildIdx);  // 정적 재귀
int32 Idx = UWidgetTree::FindChildIndex(SomePanel, MyChildWidget);

WidgetTree->RemoveWidget(MyWidget);
```

`WidgetTree` 직접 조작은 드물다 — 보통 `UPanelWidget::AddChild`/`RemoveChild` 가 자동.

### 3.4 INamedSlotInterface 사용

```cpp
// 부모 BP 가 자식 BP 에 컨텐츠 주입
TArray<FName> Slots;
ChildWidget->GetSlotNames(Slots);                                         // {"HeaderSlot", "ContentSlot"}
ChildWidget->SetContentForSlot(FName("HeaderSlot"), MyTitleWidget);
UWidget* Content = ChildWidget->GetContentForSlot(FName("ContentSlot"));
```

자식 BP 가 `UNamedSlot` 위젯을 트리에 둔 경우만 슬롯 이름이 노출됨.

### 3.5 Tick 빈도 제어

```cpp
// C++ 에서:
MyWidget->TickFrequency = EWidgetTickFrequency::Never;                    // 매 프레임 NativeTick 호출 안 함
EWidgetTickFrequency Cur = MyWidget->GetDesiredTickFrequency();           // L302

// 클래스 메타로 native tick 비활성 (자식 클래스 모두 적용)
UCLASS(meta=(DisableNativeTick))
class UMyStaticHUD : public UUserWidget { ... };
```

`Auto` 는 BP tick 함수 / 애니메이션 / latent action 이 있을 때만 자동 활성. 그러나 **대부분의 정적 HUD 는 `Never` 권장**.

---

## 4 ~ 5 깊이 자료 — [`references/InvalidationDeep.md`](./references/InvalidationDeep.md) ✂️

> **Article 3 Level 3 progressive disclosure 적용** — 메인 SKILL.md 슬림화 (32KB → ~13KB) + 깊이 자료 별도 파일 (~17KB).

| § | 내용 | reference 위치 |
|---|------|----------------|
| 4.1 | **라이프사이클 5종** (NativeOnInitialized / PreConstruct / Construct / Destruct / Tick) + **🚨 Super 호출 규약** (FIRST/LAST 매트릭스) + 구획별 초기화 책임 + 표준 override 템플릿 + Initialize() vs NativeOnInitialized | [`§1.1`](./references/InvalidationDeep.md#11-라이프사이클-5--가장-자주-override) |
| 4.2 | **Paint** (NativePaint) — 인밸리데이션 함정 의무 | [`§1.2`](./references/InvalidationDeep.md#12-paint-1--인밸리데이션-함정-의무) |
| 4.3 | **입력 (FReply)** — 키보드 / 마우스 / 포커스 / 드래그 / 터치 / 모션 30+ | [`§1.3`](./references/InvalidationDeep.md#13-입력-freply-반환) |
| 4.4 | **UWidget / UVisual / UObject override** (GetWorld / Initialize / SynchronizeProperties 등) | [`§1.4`](./references/InvalidationDeep.md#14-uwidget--uvisual--uobject-override) |
| 4.5 | **INamedSlotInterface** (3개 — §2.3 참조) | [`§1.5`](./references/InvalidationDeep.md#15-inamedslotinterface-3-메인-§23-참조) |
| 5.1 | **라이프사이클 시점별 인밸리데이션** (8단계 흐름도) | [`§2.1`](./references/InvalidationDeep.md#21-라이프사이클-시점별-인밸리데이션) |
| 5.2 | **SynchronizeProperties** (UWidget override) 호출 시점 3가지 | [`§2.2`](./references/InvalidationDeep.md#22-synchronizeproperties-uwidget-override-호출-시점) |
| 5.3 | **EWidgetTickFrequency** (Never vs Auto) — Tick 비용 제어 | [`§2.3`](./references/InvalidationDeep.md#23-ewidgettickfrequency--tick-비용-제어) |
| 5.4 | **⚠ NativeOnPaint / NativePaint override 함정 (의무)** — 자동 휘발성 / LayerId / FSlateBrush / ZOrder vs LayerId | [`§2.4`](./references/InvalidationDeep.md#24--nativeonpaint--nativepaint-override-함정-의무) |
| 5.5 | **UInvalidationBox** — 정적 영역 캐싱 (안 넣으면 안 되는 케이스) | [`§2.5`](./references/InvalidationDeep.md#25-uinvalidationbox--정적-영역-캐싱) |
| 5.6 | **5가지 핵심 원칙** (TickFrequency Never / NativePaint 마지막 / InvalidationBox 정적만 / 표준 setter / ZOrder ≠ LayerId) | [`§2.6`](./references/InvalidationDeep.md#26-5가지-핵심-원칙) |

> reference 는 [`Article 3 progressive disclosure`](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) 표준 — 메인 routing 후 깊이 필요 시 추가 로드.

<!-- LEVEL3_SPLIT_MARKER — §4 + §5 content moved to references/InvalidationDeep.md (2026-05-06) -->



---

## 6. 예제

### 6.1 기본 HUD 위젯 골격

```cpp
// MyHUDWidget.h
UCLASS()
class MYGAME_API UMyHUDWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    UPROPERTY(meta=(BindWidget))         UTextBlock*   HealthText;
    UPROPERTY(meta=(BindWidget))         UProgressBar* HealthBar;
    UPROPERTY(meta=(BindWidgetOptional)) UImage*       StatusIcon;

    UFUNCTION(BlueprintCallable)
    void SetHealth(float Pct);

protected:
    virtual void NativeOnInitialized() override;
    virtual void NativeConstruct() override;
    virtual void NativeDestruct() override;
};

// MyHUDWidget.cpp
void UMyHUDWidget::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    // 한 번만 — 외부 시스템 구독 (예: 게임 모드 델리게이트)
    if (UGameInstance* GI = GetGameInstance())
    {
        if (UMySubsystem* Sub = GI->GetSubsystem<UMySubsystem>())
        {
            Sub->OnHealthChanged.AddDynamic(this, &UMyHUDWidget::SetHealth);
        }
    }
}

void UMyHUDWidget::NativeConstruct()
{
    Super::