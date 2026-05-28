---
name: umg-panelwidgets
description: UCanvasPanel + UHorizontalBox + UVerticalBox + UOverlay + UScrollBox + UWrapBox + UGridPanel - 패널.
---

# UMG · PanelWidgets sub-skill

> **모듈**: UMG (Tier 3 · Slate 카테고리)
> **위치**: `Engine/Source/Runtime/UMG/Public/Components/`
> **다루는 범위**: 자식 위젯을 배치/정렬하는 컨테이너 위젯 — VerticalBox / HorizontalBox / CanvasPanel / Overlay / GridPanel / UniformGridPanel / StackBox / WrapBox / ScrollBox / ScaleBox / SizeBox / SafeZone / Border / Border.

---

## 1. 개요

`UPanelWidget` (자식 N개) 또는 `UContentWidget` (자식 1개) 자손. 내부에 대응하는 SXxxPanel/SBoxPanel/SOverlay 등 Slate 컨테이너 1개를 보유. **자식의 배치 정책**(축·정렬·간격·자동 줄바꿈 등)을 결정하며, 자식별 추가 프로퍼티는 **`UPanelSlot`** 자손이 보유 (자세한 [`UMG/references/Slot.md`](../Slot/SKILL.md)).

---

## 2. 핵심 헤더와 클래스

### 2.1 베이스 사슬

```
UWidget (Widget.h L?)
└── UPanelWidget (PanelWidget.h L?)            자식 N개
    ├── UVerticalBox / UHorizontalBox          1축 stack
    ├── UStackBox                              StackBox.h — 5.x 통합 stack (Vertical/Horizontal 양용)
    ├── UWrapBox                               1축 + 줄바꿈
    ├── UCanvasPanel                           절대좌표 / Anchor
    ├── UOverlay                               Z-order 중첩
    ├── UGridPanel                             가변 셀 크기 그리드
    ├── UUniformGridPanel                      균일 셀 크기 그리드
    └── UScrollBox                             1축 + 스크롤
└── UContentWidget (단일 자식)
    ├── UScaleBox                              자식 크기 조정
    ├── USizeBox                               자식 사이즈 강제
    ├── USafeZone                              모바일 안전 영역
    ├── UBorder                                테두리 + 단일 자식
    └── UInvalidationBox / URetainerBox        (캐시·렌더 → §5)
```

### 2.2 핵심 헤더 (5.5.4)

| 클래스 | 헤더 | 베이스 |
|--------|------|--------|
| `UPanelWidget` | `PanelWidget.h` | `UWidget` |
| `UVerticalBox` | `VerticalBox.h` | `UPanelWidget` |
| `UHorizontalBox` | `HorizontalBox.h` | `UPanelWidget` |
| `UStackBox` | `StackBox.h` | `UPanelWidget` |
| `UWrapBox` | `WrapBox.h` | `UPanelWidget` |
| `UCanvasPanel` | `CanvasPanel.h` | `UPanelWidget` |
| `UOverlay` | `Overlay.h` | `UPanelWidget` |
| `UGridPanel` | `GridPanel.h` | `UPanelWidget` |
| `UUniformGridPanel` | `UniformGridPanel.h` | `UPanelWidget` |
| `UScrollBox` | `ScrollBox.h` | `UPanelWidget` |
| `UScaleBox` | `ScaleBox.h` | `UContentWidget` |
| `USizeBox` | `SizeBox.h` | `UContentWidget` |
| `USafeZone` | `SafeZone.h` | `UContentWidget` |
| `UBorder` | `Border.h` | `UContentWidget` |

`UContentWidget` 은 별도 헤더 (`ContentWidget.h`) — `UPanelWidget` 자손이지만 `MaxNumChildren=1` 고정.

---

## 3. 자주 쓰는 API (위젯별)

### 3.1 UPanelWidget 베이스 API (모든 패널 공통)

| API | 메모 |
|-----|------|
| `int32 GetChildrenCount() const` | |
| `UWidget* GetChildAt(int32) const` | |
| `int32 GetChildIndex(const UWidget*) const` | |
| `bool HasChild(UWidget*) const` | |
| `UPanelSlot* AddChild(UWidget*)` | **공통 추가** — 반환 슬롯에서 자식별 프로퍼티 설정 |
| `bool RemoveChild(UWidget*)` / `RemoveChildAt(int32)` / `ClearChildren()` | |
| `int32 GetChildIndex(const UWidget*) const` | |
| `bool ReplaceChildAt(int32, UWidget*)` 🛠 | `WITH_EDITOR` |

각 패널은 추가로 **타입별 헬퍼** 가 있다:
- `UVerticalBox::AddChildToVerticalBox(UWidget*) → UVerticalBoxSlot*`
- `UHorizontalBox::AddChildToHorizontalBox(UWidget*) → UHorizontalBoxSlot*`
- `UCanvasPanel::AddChildToCanvas(UWidget*) → UCanvasPanelSlot*`
- 등등

### 3.2 UVerticalBox / UHorizontalBox (`VerticalBox.h` / `HorizontalBox.h`)

가장 자주 쓰는 1축 stack. 자식의 `UVerticalBoxSlot::SetSize` 로 Auto/Fill 결정, `SetPadding`/`SetHorizontalAlignment`/`SetVerticalAlignment` 로 정렬.

### 3.3 UStackBox (`StackBox.h`) — 5.x 통합

`UVerticalBox` + `UHorizontalBox` 기능을 한 클래스로. `Orientation` 프로퍼티로 축 결정. 신규 코드 권장.

### 3.4 UWrapBox (`WrapBox.h`)

자식이 한 줄에 안 맞으면 자동 줄바꿈. `SetWrapWidth(float)` / `SetWrapSize(FVector2D)` / `SetInnerSlotPadding(FVector2D)`.

### 3.5 UCanvasPanel (`CanvasPanel.h`)

절대좌표 + Anchor. 자식 `UCanvasPanelSlot::SetAnchors`/`SetOffsets`/`SetAlignment`/`SetZOrder`/`SetAutoSize` 로 배치. **HUD 절대 위치 잡을 때** 표준.

### 3.6 UOverlay (`Overlay.h`)

자식이 같은 영역에 Z-order로 쌓임. 자식 `UOverlaySlot::SetHorizontalAlignment`/`SetVerticalAlignment`/`SetPadding`. **단순 Z-stacking** (Anchor 없음).

### 3.7 UGridPanel (`GridPanel.h`) / UUniformGridPanel (`UniformGridPanel.h`)

| API | 메모 |
|-----|------|
| `UGridPanel::AddChildToGrid(UWidget*, int32 Row, int32 Column) → UGridSlot*` | 가변 셀 |
| `SetColumnFill(int32 ColumnIndex, float Coefficient)` / `SetRowFill(...)` | Fill 계수 |
| `UUniformGridPanel::AddChildToUniformGrid(UWidget*, int32 Row, int32 Column) → UUniformGridSlot*` | 균일 셀 |
| `SetSlotPadding(FMargin)` / `SetMinDesiredSlotWidth(float)` / `SetMinDesiredSlotHeight(float)` | 균일 셀 사이즈 |

### 3.8 UScrollBox (`ScrollBox.h`)

| API | 메모 |
|-----|------|
| `void SetOrientation(EOrientation::Type)` | Vertical/Horizontal |
| `float GetScrollOffset() const` / `SetScrollOffset(float)` | 픽셀 |
| `void ScrollToStart()` / `ScrollToEnd()` | |
| `void ScrollWidgetIntoView(UWidget*, bool bAnimateScroll=true, EDescendantScrollDestination=...)` | **자식 강조 시 표준** |
| `void EndInertialScrolling()` | |
| `SetScrollBarVisibility(ESlateVisibility)` / `SetScrollBarThickness(FVector2D)` | |
| `bAlwaysShowScrollbar` / `bAllowOverscroll` / `bAnimateWheelScrolling` | 동작 정책 |
| 이벤트 | `OnUserScrolled(float CurrentOffset)` |

**🚨 함정**: `UScrollBox` 안에 자식 수가 많으면 (수백 개 이상) **`UListView` 로 대체** — ScrollBox는 모든 자식을 항상 렌더, ListView는 가시 항목만 풀링. 자세한 [`UMG/references/ListWidgets.md`](../ListWidgets/SKILL.md).

### 3.9 UScaleBox (`ScaleBox.h`)

| API | 메모 |
|-----|------|
| `void SetStretch(EStretch::Type)` | None/Fill/ScaleToFit/ScaleToFill/ScaleBySafeZone/UserSpecified/UserSpecifiedWithClipping/ScaleToFitX/Y |
| `void SetUserSpecifiedScale(float)` | UserSpecified 일 때 |
| `void SetIgnoreInheritedScale(bool)` | 부모 스케일 무시 |

자식 콘텐츠를 부모 영역에 맞춰 자동 스케일.

### 3.10 USizeBox (`SizeBox.h`)

자식 사이즈 강제. `SetWidthOverride/HeightOverride/MinDesiredWidth/MinDesiredHeight/MaxDesiredWidth/MaxDesiredHeight/MinAspectRatio/MaxAspectRatio`.

### 3.11 USafeZone (`SafeZone.h`)

모바일·콘솔 안전 영역 (TV overscan 등) 회피. `SetPadLeft/PadRight/PadTop/PadBottom(bool)` + `SafeAreaScale` 자동.

### 3.12 UBorder (`Border.h`)

테두리 + 단일 자식. `SetBrushColor(FLinearColor)`/`SetBrush(FSlateBrush)`/`SetContentColorAndOpacity(FLinearColor)`/`SetPadding(FMargin)`/`SetHorizontalAlignment`/`SetVerticalAlignment`. 마우스 캡처 정책도 (`SetMouseButtonDownEvent`).

---

## 4. 가상 함수 (오버라이드 포인트)

패널은 거의 override 안 함 — **사용**이 목적. 사용자 정의 패널 작성 시:

| 시그니처 | Super | 메모 |
|----------|-------|------|
| `virtual UClass* GetSlotClass() const override` | (호출 안 함) | 이 패널이 사용할 `UPanelSlot` 자손 클래스 반환 |
| `virtual void OnSlotAdded(UPanelSlot*)` | **FIRST** | AddChild 시 호출 — Slate 측 슬롯 추가 |
| `virtual void OnSlotRemoved(UPanelSlot*)` | **FIRST** | RemoveChild 시 |
| `virtual TSharedRef<SWidget> RebuildWidget() override` | (호출 안 함) | 자체 SXxxPanel 생성 |

> **Super 호출 규약**: [`04_OverrideIndex.md §6.4`](../../../references/04_OverrideIndex.md).

---

## 5. 🚨 인밸리데이션 / 갱신 흐름 (의무 섹션)

### 5.1 자식 추가/제거 → ChildOrder Invalidate

`AddChild`/`RemoveChild`/`ClearChildren` → 패널 `Invalidate(EInvalidateWidgetReason::ChildOrder)` → 부모 InvalidationBox 캐시 무효 + 레이아웃 + 페인트.

런타임 매 프레임 자식 리스트를 재구성하는 패턴 (예: `ClearChildren` + 다시 `AddChild` 루프) 은 **금지**. 변경된 자식만 추가/제거.

### 5.2 캐싱 패널 (UInvalidationBox / URetainerBox)

#### UInvalidationBox

자식 위젯 트리를 캐시. **자식이 거의 변하지 않을 때** DrawCall 절감. 자식 중 하나가 휘발성이면 캐시 효과 0.

```cpp
// 디자이너 또는 C++
UInvalidationBox* CacheBox = WidgetTree->ConstructWidget<UInvalidationBox>();
CacheBox->AddChild(MainContent);
CacheBox->SetCanCache(true);                  // 명시적
```

**결정 트리** (자세한 [`06_InvalidationHotspots.md §3`](../../../references/06_InvalidationHotspots.md)):

```
이 영역의 자식 묶음이 1초에 1회 이하 갱신?
├─ Yes → InvalidationBox 사용
│   └─ 휘발성 자식 (Throbber/Marquee/Animation) 포함?
│       └─ Yes → 효과 0 → 사용 X
└─ No (자주 갱신) → 사용 X
```

#### URetainerBox

자식 위젯 트리를 **별도 RenderTarget 에 페인트** → 그 텍스처를 본 위치에 그림. 매우 복잡한 트리를 렌더 비용으로 캐시. `SetEffectMaterial(...)` 로 포스트 효과 (블러/색조 등) 적용. 비용은 RT 생성 / 메모리.

### 5.3 패널별 인밸리데이션 hotspot

| 패널 | 자주 발생 케이스 | 회피 |
|------|------------------|------|
| `UScrollBox` | 자식 사이즈 변동 → ScrollBox 전체 재배치 | 자식 사이즈 고정 / `UListView` 대체 |
| `UCanvasPanel` | 자식 Anchor/Offset 매 프레임 변경 | TSlateAttribute 활용 (자동 인밸리데이션) |
| `UWrapBox` | 폭 변경 → 줄바꿈 재계산 → 모든 자식 재배치 | 폭 고정 / DesignTime 결정 |
| `USizeBox` | `SetWidthOverride` 매 프레임 호출 | TAttribute 활용 |
| `UScaleBox` | 부모 사이즈 변경 → 모든 자식 스케일 재계산 | 변동 시점 한정 |

자세한 hotspot 표는 [`06_InvalidationHotspots.md §2.5`](../../../references/06_InvalidationHotspots.md).

---

## 6. 예제

### 6.1 UVerticalBox 동적 자식 추가/제거

```cpp
UCLASS()
class UMyListWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    void Refresh(const TArray<FInventoryItem>& Items);

protected:
    UPROPERTY(meta=(BindWidget)) UVerticalBox* ItemBox = nullptr;

    UPROPERTY(EditDefaultsOnly) TSubclassOf<UInventorySlotWidget> SlotClass;
};

void UMyListWidget::Refresh(const TArray<FInventoryItem>& Items)
{
    ItemBox->ClearChildren();              // ← ChildOrder Invalidate 1회
    for (const FInventoryItem& Item : Items)
    {
        UInventorySlotWidget* Slot = CreateWidget<UInventorySlotWidget>(this, SlotClass);
        Slot->RefreshFromData(Item);
        UVerticalBoxSlot* VBSlot = ItemBox->AddChildToVerticalBox(Slot);
        VBSlot->SetPadding(FMargin(0, 4));
    }
}
```

**개선**: 자주 호출되면 `UListView` (가시 풀링) 권장.

### 6.2 UCanvasPanel + Anchor — HUD 우상단 미니맵

```cpp
UCanvasPanelSlot* MapSlot = CanvasPanel->AddChildToCanvas(MinimapImage);
MapSlot->SetAnchors(FAnchors(1.f, 0.f));           // 우상단
MapSlot->SetAlignment(FVector2D(1.f, 0.f));         // 위젯 우상단 기준
MapSlot->SetOffsets(FMargin(-20, 20, 200, 200));    // 좌측 상단/하단으로 -20/20, 가로/세로 200x200
```

### 6.3 UScrollBox + 강조 스크롤

```cpp
ChatScrollBox->ScrollWidgetIntoView(NewMessageWidget, /*bAnimateScroll=*/true, EDescendantScrollDestination::IntoView);
```

### 6.4 UInvalidationBox 캐싱 — 정적 HUD 패널

```cpp
// 디자이너에서 InvalidationBox > VerticalBox > [정적 라벨/아이콘 묶음]
// 매 프레임 변경 없는 패널이면 캐시 효과 명확
// 단, HP 바 같은 휘발성 자식 포함 시 SeparateBox 분리
```

---

## 7. 운영 가이드 / 함정

| 함정 | 회피 |
|------|------|
| 매 프레임 `ClearChildren` + 다시 추가 | 변경된 자식만 추가/제거 |
| `UScrollBox` 에 수백 자식 | `UListView` 로 대체 |
| `UWrapBox` 폭이 부모 따라 변경 | 폭 고정 또는 디자인타임 결정 |
| `UCanvasPanel` 안에 모든 위젯 | 의도 불명확 — `UVerticalBox`/`UStackBox` 표준 사용 |
| `UInvalidationBox` 안에 휘발성 자식 | 정적 자식만 분리해서 캐시 |
| `URetainerBox` 남발 | RT 메모리 폭증 — 정말 복잡한 트리에만 |
| `UVerticalBox`/`UHorizontalBox` 새 코드 | `UStackBox` 권장 (5.x 통합) |
| `UCanvasPanel` Anchor 매 프레임 변경 | TSlateAttribute (`TAttribute<FAnchorData>`) |
| `USafeZone` 빠뜨림 (모바일) | 메인 HUD 루트는 `USafeZone` 으로 감쌈 |

---

## 8. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 가드 |
|------|------|
| `UPanelWidget::ReplaceChildAt(int32, UWidget*)` 🛠 | `WITH_EDITOR` — 디자이너 트리 편집 |
| `UCanvasPanel::CanAddNewSlot` 🛠 | `WITH_EDITOR` |
| `UPanelWidget::CanHaveMultipleChildren()` 🛠 | `WITH_EDITOR` (디자이너 자식 추가 제한) |

자세한 에디터 전용 통합은 [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md).

---

## 9. 관련 sub-skill

- [`UMG/UWidget`](../UWidget/SKILL.md) — UPanelWidget 베이스
- [`UMG/Slot`](../Slot/SKILL.md) — UPanelSlot 사슬 (각 패널의 자식별 프로퍼티)
- [`UMG/StandardWidgets`](../StandardWidgets/SKILL.md) — Button/CheckBox/Image/TextBlock 등 (자식으로 자주 들어감)
- [`UMG/ListWidgets`](../ListWidgets/SKILL.md) — ListView/TreeView (대량 자식 풀링)
- [`SlateCore/Layout`](../../SlateCore/references/Layout.md) — FGeometry/FArrangedChildren/FMargin
- [`06_InvalidationHotspots.md §2.5 / §3`](../../../references/06_InvalidationHotspots.md) — 패널별 hotspot + InvalidationBox 결정 트리
