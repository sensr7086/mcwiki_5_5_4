---
name: umg-main
description: Tier 3 UMG 모듈 메인 — UWidget + UUserWidget + StandardWidgets + PanelWidgets + ListWidgets + Slot + ViewModel 7개 sub-skill 인덱스. UWidget/UUserWidget 인밸리데이션 의무 + Super 호출 규약 (Construct/PreConstruct → Super FIRST, Destruct → Super LAST). WidgetClass = SoftClassPtr + CreateWidget PreLoad 표준.
---

# UMG — 모듈 진입점

> Tier 3 · L7 (게임/시네마틱/AI/UI 게임 레이어) · UE 5.7.4 기준
> 위치: `Engine/Source/Runtime/UMG/`
> 의존: **Public** FieldNotification, HTTP, MovieScene, MovieSceneTracks, PropertyPath, TimeManagement / **Private** Core, TraceLog, CoreUObject, DeveloperSettings, Engine, InputCore, Slate, SlateCore, RenderCore, Renderer, RHI, ApplicationCore (+ SlateRHIRenderer — 비-서버)
> 출처: `UMG.Build.cs` 직접 확인
>
> **상위 인덱스**: [`../../references/03_WikiHarness.md`](../../references/03_WikiHarness.md) · 시나리오 §3.12 (새 SWidget·UMG 위젯 작성).
>
> **🎯 어셋 로드 의무**: UMG 의 **WidgetClass (`TSubclassOf<UUserWidget>`)** 가 큰 BP — `TSoftClassPtr<UUserWidget>` + `FStreamableManager::RequestAsyncLoad` 표준. 첫 `CreateWidget` 시 BP 컴파일·SWidget 트리 생성 비용 — **메뉴 / HUD 등 자주 표시되는 위젯은 로딩 화면 / Map 시작 시 사전 PreLoad 의무**. 자세한 패턴 = 🚨 [`11_AssetLoadingPolicy.md`](../../references/11_AssetLoadingPolicy.md) (특히 §10 sub-skill 적용 매트릭스 — UMG 행).

---

## 1. 개요

`UMG` (Unreal Motion Graphics) 는 [`Slate`](../Slate/SKILL.md) 위에 **UObject + 블루프린트 노출 레이어** 를 얹는 모듈이다. 게임 UI 의 표준 — 디자이너가 에디터의 위젯 블루프린트 (`.uasset`) 로 트리를 짜고, 디테일 패널로 속성을 편집하며, BP 노드로 동작을 작성한다. 모든 UMG 위젯 (`UWidget` 자손) 은 내부적으로 `TSharedRef<SWidget>` 을 만들어 Slate 그리기 사이클에 들어간다.

```
UMG (이 모듈)
  ├─ UVisual (UObject 베이스)
  │   └─ UWidget (모든 UMG 위젯의 베이스, 50+ 자손)
  │        ├─ UPanelWidget (자식 N개 + Slot)
  │        │     ├─ UContentWidget (자식 1개)
  │        │     │     ├─ UButton / UBorder / UInvalidationBox / URetainerBox 등
  │        │     │     └─ UUserWidget (★ BP 위젯의 베이스)
  │        │     └─ UCanvasPanel / UGridPanel / UHorizontalBox / UVerticalBox 등
  │        ├─ ULeafWidget 류 (자식 없음): UTextBlock / UImage / USpinBox / USlider / UProgressBar
  │        └─ UListViewBase 류: UListView / UTreeView / UTileView
  └─ UPanelSlot (UVisual 자손) — 자식 배치 메타 (각 Panel마다 전용 Slot)
```

**왜 Slate 위에 또 한 층?** — Slate 만으로는 BP 노출·디자이너 편집·시퀀서 통합·`TObjectPtr` 멤버 직렬화가 안 된다. UMG 가 다음을 추가:

- UCLASS 통합 → 디테일 패널·BP 핀 노출
- `UWidgetBlueprintGeneratedClass` → BP 컴파일 결과
- `UWidgetTree` → 디자이너 트리 직렬화
- `UWidgetAnimation` (MovieScene 기반) → 시퀀서 키프레임 (※ 본 위키 제외, LevelSequence 위키에서)
- `BindWidget`/`BindWidgetOptional` 메타 → 디자이너 위젯 ↔ C++ 멤버 자동 연결
- `INotifyFieldValueChanged` (FieldNotification) → MVVM 데이터 바인딩

---

## 2. 의존·빌드 (`UMG.Build.cs` 요약)

```text
PublicDependencyModuleNames  : FieldNotification, HTTP, MovieScene, MovieSceneTracks, PropertyPath, TimeManagement
PrivateDependencyModuleNames : Core, TraceLog, CoreUObject, DeveloperSettings, Engine, InputCore,
                              Slate, SlateCore, RenderCore, Renderer, RHI, ApplicationCore
                              (+ SlateRHIRenderer — Target.Type != TargetType.Server)
PrivateIncludePathModuleNames: SlateRHIRenderer, ImageWrapper, TargetPlatform
DynamicallyLoadedModuleNames : ImageWrapper (비-서버)
```

`MovieScene`/`MovieSceneTracks` 가 Public 의존 — `UWidgetAnimation` 의 시퀀서 통합 때문. 서버 빌드는 `SlateRHIRenderer` 제외.

---

## 3. 자주 쓰는 API (1줄 요약 — 상세는 각 sub-skill)

```cpp
// === BP 위젯 인스턴스 생성 (가장 흔함) ===
UMyHUDWidget* HUD = CreateWidget<UMyHUDWidget>(GetWorld(), HUDClass);
HUD->AddToViewport();

// === BindWidget 패턴 (디자이너 위젯 ↔ C++ 멤버) ===
UCLASS()
class UMyHUDWidget : public UUserWidget
{
    GENERATED_BODY()
    UPROPERTY(meta=(BindWidget))         UTextBlock* HealthText;
    UPROPERTY(meta=(BindWidgetOptional)) UProgressBar* HealthBar;
};

// === Native 라이프사이클 ===
virtual void NativeOnInitialized() override;     // 한 번 (생성 직후)
virtual void NativeConstruct() override;          // 매번 뷰포트에 추가될 때
virtual void NativeDestruct() override;           // 뷰포트에서 제거될 때
virtual void NativeTick(const FGeometry&, float DeltaTime) override;

// === 프로퍼티 동기화 (디자이너 변경 → 위젯 갱신) ===
virtual void SynchronizeProperties() override;
```

상세 시그니처·오버로드·사용 패턴은 다음 sub-skill에서 다룬다.

---

## 4. ⚡ 인밸리데이션 / 갱신 처리 (가장 자주 빠뜨리는 부분)

[`SlateCore/SKILL.md §5.1`](../SlateCore/SKILL.md) 의무 표에서 본 sub-skill 의 `UWidget` 과 `UUserWidget` 에 인밸리데이션 흐름을 별도 섹션으로 다루도록 명시되어 있다. 핵심:

| sub-skill | 다룰 항목 |
|-----------|-----------|
| [`UWidget/`](./UWidget/SKILL.md) | `SynchronizeProperties()` 호출 시점, `EWidgetVolatility`, `Invalidate(EInvalidateWidgetReason)`, BP 노출 setter 들이 자동 트리거하는 reason |
| [`UUserWidget/`](./UUserWidget/SKILL.md) | `NativePreConstruct`/`NativeOnInitialized`/`NativeConstruct`/`NativeTick`/`NativeDestruct` 시퀀스에서 인밸리데이션 발생 시점, `UInvalidationBox` 사용 패턴, `EWidgetTickFrequency` (NeverTick 권장 조건), **`NativeOnPaint`/`NativePaint` override 시 LayerId 중복·DrawCall 폭증·자동 휘발성 함정 (Canvas ZOrder ≠ LayerId)** |

핵심 원칙 (각 sub-skill 에서 반복):

1. **`SynchronizeProperties`** — 디자이너 변경/생성 시에만 호출. **런타임 setter 는 별도로 `Invalidate(reason)` 호출 필요**.
2. **`EWidgetTickFrequency`** — 기본 `Auto` 가 아닌 **`NeverTick`/`OnlyWhenVisible`** 권장. Tick 비용 회피.
3. **`UInvalidationBox`** 안에 정적 영역 배치 — Slate 의 `SInvalidationPanel` 과 동일.
4. **`NativeOnPaint`/`NativePaint` override** — 자동 휘발성처럼 동작해 `SInvalidationPanel`/`UInvalidationBox` 캐시 비활성. LayerId 단조 증가·DrawCall 배치 가이드는 [`SlateCore/Drawing/§5`](../SlateCore/references/Drawing.md). **마지막 수단** — 가능하면 표준 위젯 조합으로.
5. **`UCanvasPanelSlot::ZOrder`** ≠ Slate `LayerId` — 혼동 금지.

---

## 5. 사용 예제 (UUserWidget 골격)

```cpp
// MyHUDWidget.h
UCLASS()
class MYGAME_API UMyHUDWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    // BindWidget — 디자이너가 같은 이름의 위젯을 두면 자동 연결
    UPROPERTY(meta=(BindWidget))
    UTextBlock* HealthText;

    UPROPERTY(meta=(BindWidget))
    UProgressBar* HealthBar;

    UPROPERTY(meta=(BindWidgetOptional))
    UImage* StatusIcon;     // 옵션 — 디자이너가 안 두어도 OK

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
    // 한 번만 — 외부 시스템 구독, 초기 캐시 등
}

void UMyHUDWidget::NativeConstruct()
{
    Super::NativeConstruct();
    // 뷰포트 추가될 때마다 — 데이터 새로고침
    if (HealthText) HealthText->SetText(FText::AsNumber(100));
    if (HealthBar)  HealthBar->SetPercent(1.f);
}

void UMyHUDWidget::SetHealth(float Pct)
{
    if (HealthText) HealthText->SetText(FText::FromString(FString::Printf(TEXT("%.0f"), Pct * 100.f)));
    if (HealthBar)  HealthBar->SetPercent(Pct);
    // ↑ UWidget setter 들은 내부적으로 Invalidate(EInvalidateWidgetReason::Layout/Paint) 자동 호출
}
```

---

## 6. Sub-skill 인덱스

UMG 의 클래스·virtual·예제는 다음 7개 sub-skill 로 분산. 각 sub-skill 은 *개요 → 핵심 헤더/클래스 → 자주 쓰는 API → virtual → 예제 → 에디터 전용 → 관련 sub-skill* 일관 7섹션 구조.

| # | Sub-skill | 다루는 영역 | 주요 헤더/심볼 |
|---|-----------|-------------|----------------|
| 1 | [`UWidget/`](./UWidget/SKILL.md) | **모든 UMG 위젯의 베이스** — `UVisual` (베이스 베이스) → `UWidget` + `INotifyFieldValueChanged` + `SynchronizeProperties`/`RebuildWidget`/`Invalidate(reason)`/`EWidgetVolatility` + **인밸리데이션 갱신 의무** + `INamedSlotInterface` | `Components/Visual.h`, `Components/Widget.h`, `Components/SlateWrapperTypes.h` |
| 2 | [`UUserWidget/`](./UUserWidget/SKILL.md) | **BP 위젯의 베이스** — `UUserWidget` + `Native*` 라이프사이클 (10+ virtual) + `BindWidget`/`BindWidgetOptional` + `EWidgetTickFrequency` + `UWidgetTree` + `UWidgetBlueprintGeneratedClass` + `INamedSlotInterface` + **인밸리데이션 갱신 의무** + **`NativeOnPaint` LayerId/DrawCall 함정** | `Blueprint/UserWidget.h`, `Blueprint/WidgetTree.h`, `Blueprint/WidgetBlueprintGeneratedClass.h`, `Blueprint/UserWidgetPool.h` |
| 3 | [`StandardWidgets/`](./StandardWidgets/SKILL.md) | 표준 위젯 — `UButton`/`UImage`/`UTextBlock`/`URichTextBlock`/`UCheckBox`/`UEditableText`/`UEditableTextBox`/`UMultiLineEditableText`/`USlider`/`USpinBox`/`UProgressBar`/`UComboBox`/`UComboBoxString`/`UComboBoxKey`/`UThrobber`/`UCircularThrobber`/`UInputKeySelector`/`USpacer`/`UMenuAnchor` 등 | `Components/Button.h`, `Image.h`, `TextBlock.h`, `CheckBox.h`, `EditableText.h` 등 |
| 4 | [`PanelWidgets/`](./PanelWidgets/SKILL.md) | 패널 위젯 — `UPanelWidget` (베이스), `UContentWidget`, `UCanvasPanel`, `UGridPanel`/`UUniformGridPanel`, `UHorizontalBox`/`UVerticalBox`, `UWrapBox`, `UStackBox`, `UOverlay`, `UWidgetSwitcher`, `UScaleBox`, `UScrollBox`, `USizeBox`, `USafeZone`, **`UInvalidationBox`**, `URetainerBox`, `UExpandableArea`, `UBackgroundBlur`, `UBorder`, `UWindowTitleBarArea`, `UNamedSlot` | `Components/PanelWidget.h`, `ContentWidget.h`, `CanvasPanel.h`, `InvalidationBox.h` 등 |
| 5 | [`ListWidgets/`](./ListWidgets/SKILL.md) | 리스트/트리/타일 — `UListViewBase`, `UListView`, `UTreeView`, `UTileView`, `UDynamicEntryBox`, `UDynamicEntryBoxBase`, `IUserListEntry`/`IUserObjectListEntry` | `Components/ListView.h`, `ListViewBase.h`, `TreeView.h`, `TileView.h`, `DynamicEntryBox.h`, `Blueprint/IUserListEntry.h` |
| 6 | [`Slot/`](./Slot/SKILL.md) | 자식 배치 메타 — `UPanelSlot` (베이스), `UCanvasPanelSlot`, `UGridSlot`/`UUniformGridSlot`, `UHorizontalBoxSlot`/`UVerticalBoxSlot`, `UWrapBoxSlot`, `UStackBoxSlot`, `UOverlaySlot`, `UWidgetSwitcherSlot`, `UScaleBoxSlot`, `UScrollBoxSlot`, `USizeBoxSlot`, `USafeZoneSlot`, `UBackgroundBlurSlot`, `UBorderSlot`, `UButtonSlot`, `UWindowTitleBarAreaSlot` + ZOrder vs LayerId | `Components/PanelSlot.h`, `CanvasPanelSlot.h`, `GridSlot.h` 등 |
| 7 | [`ViewModel/`](./ViewModel/SKILL.md) | MVVM 데이터 바인딩 + 5.x 신규 — `UWidgetBlueprintGeneratedClass`, `Binding/*` (12종), `INotifyFieldValueChanged`, `Public/Binding/States/WidgetStateBitfield/Registration/Settings`, `Public/FieldNotification/*`, `Public/Extensions/*` (UIComponent/UserWidgetExtension), `WidgetNavigation`, `WidgetChild` | `Binding/*`, `FieldNotification/*`, `Extensions/*`, `Components/Widget.h` (INotifyFieldValueChanged) |

> **`UWidgetAnimation` (MovieScene 기반 시퀀서 통합) 은 본 위키에서 제외** — 향후 `LevelSequence`/`MovieScene` 모듈 위키에서 통합적으로 다룬다. UMG 의 `Public/Animation/` 폴더 (MovieScene 트랙·플레이어·tick 매니저 등) 도 본 sub-skill 묶음에 포함되지 않음.

---

## 7. 관련 모듈

- **상위 (의존됨)**: 거의 모든 게임 모듈, 에디터 위젯, `UMGEditor` (Editor 모듈, 본 위키 분석 범위 외).
- **하위 (의존)**: [`Slate/`](../Slate/SKILL.md), [`SlateCore/`](../SlateCore/SKILL.md), `Engine`, `CoreUObject`, `Renderer`, `RHI`, `MovieScene`, `MovieSceneTracks` (UWidgetAnimation), `FieldNotification` (MVVM), `HTTP` (`AsyncTaskDownloadImage`), `PropertyPath` (Binding), `TimeManagement`.
- **연계**:
  - [`SlateCore/SWidget/`](../SlateCore/references/SWidget.md) — UWidget이 내부적으로 `RebuildWidget()` 으로 만드는 SWidget 베이스
  - [`SlateCore/Drawing/`](../SlateCore/references/Drawing.md) — 인밸리데이션 캐시·LayerId/DrawCall (UWidget setter 가 자동 트리거)
  - [`SlateCore/Styling/`](../SlateCore/references/Styling.md) — `FAppStyle`/`FUMGCoreStyle`/`USlateWidgetStyleAsset`
  - [`SlateCore/Input/`](../SlateCore/references/Input.md) — `FReply` 와 `Native*` 입력 콜백
  - [`CoreUObject/UObject/`](../../CoreUObject/references/UObject.md) — UWidget 라이프사이클이 UObject
  - [`CoreUObject/Editor/`](../../CoreUObject/references/Editor.md) — `PostEditChangeProperty` (디테일 패널 편집 시)
  - `Slate/Application` (게임 측면 — 향후 작성) — `FSlateApplication::Get().AddWindow` 가 위젯 호스팅

---

## 8. 작성·인용 규칙

전체 위키 공통 규칙을 따른다 — `skills/CoreUObject/SKILL.md §7.1` 의 에디터 전용 표기 규칙(🛠 마커 + `WITH_EDITOR`/`WITH_EDITORONLY_DATA` 가드 명시) + 라인 번호 직접 grep 검증.

추가로 UMG 모듈 특수 규약:

- **인밸리데이션 갱신 의무** — `UWidget`/`UUserWidget` sub-skill은 §4 의 5가지 원칙을 별도 섹션으로 의무 기술 ([`SlateCore/SKILL.md §5.1`](../SlateCore/SKILL.md) 참조).
- **MovieScene 기반 `UWidgetAnimation` 제외** — `Animation/` 폴더의 MovieScene*  헤더는 본 위키 sub-sk