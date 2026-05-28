---
name: umg-listwidgets
description: UListView + UTileView + UTreeView + UDynamicEntryBox - 데이터 기반 리스트.
---

# UMG · ListWidgets sub-skill

> **모듈**: UMG (Tier 3 · Slate 카테고리)
> **위치**: `Engine/Source/Runtime/UMG/Public/Components/` + `Engine/Source/Runtime/UMG/Public/Blueprint/IUserList*.h`
> **다루는 범위**: 가상 풀링 리스트 위젯 — `UListView` / `UTreeView` / `UTileView` (베이스 `UListViewBase`) + EntryWidget 인터페이스 (`IUserListEntry` / `IUserObjectListEntry`).

---

## 1. 개요

대량 데이터를 표시할 때 **가시 영역 자식만 풀링**하여 그리는 컨테이너. 일반 `UScrollBox + UVerticalBox` 패턴은 모든 자식이 항상 페인트/레이아웃 → 100개 이상이면 즉시 성능 문제. ListView 계열은 `SListView<T>` (Slate) 위에 UMG 래퍼를 씌운 형태로, **보이는 만큼만 EntryWidget 인스턴스 재사용**.

핵심 패턴:
1. **데이터 객체** (UObject 자손) 의 배열을 ListView에 setItems
2. **EntryWidget 클래스** (UUserWidget + IUserObjectListEntry/IUserListEntry 구현) 를 EntryWidgetClass 에 지정
3. ListView 가 자동으로 EntryWidget 인스턴스를 풀링·재사용하며 `OnListItemObjectSet(UObject*)` 등 콜백 호출

---

## 2. 핵심 헤더와 클래스

### 2.1 베이스 사슬

```
UWidget
└── UListViewBase (ListViewBase.h L499)
    └── UListView (ListView.h L27)              UObject* 항목 — ITypedUMGListView<UObject*> 구현
        ├── UTreeView (TreeView.h L20)          ListView + 펼침/접기
        └── UTileView (TileView.h L15)          ListView + 그리드 배치
```

### 2.2 EntryWidget 인터페이스

| 인터페이스 | 헤더 | 의미 |
|-----------|------|------|
| `IUserListEntry` | `Blueprint/IUserListEntry.h` L26 | 모든 EntryWidget 의 베이스 — 선택/펼침/호버/오너 리스트 정보 |
| `IUserObjectListEntry` | `Blueprint/IUserObjectListEntry.h` L18 | `IUserListEntry` 확장 — `UObject*` 항목을 직접 다루는 표준 (ListView/TreeView/TileView 사용 시 **반드시 이쪽 구현**) |

> "To be usable as an entry for UListView, UTileView, or UTreeView, implement `IUserObjectListEntry` instead" — IUserListEntry.h L18

### 2.3 핵심 헤더 (5.5.4)

| 클래스 | 헤더 | 라인 |
|--------|------|------|
| `UListViewBase` | `ListViewBase.h` | L499 |
| `UListView` | `ListView.h` | L27 |
| `UTreeView` | `TreeView.h` | L20 |
| `UTileView` | `TileView.h` | L15 |
| `IUserListEntry` | `Blueprint/IUserListEntry.h` | L26 |
| `IUserObjectListEntry` | `Blueprint/IUserObjectListEntry.h` | L18 |

---

## 3. 자주 쓰는 API

### 3.1 UListView (`ListView.h`)

| API | 메모 |
|-----|------|
| `void SetListItems(const TArray<UObject*>&)` | **항목 배열 통째 교체** — 가장 자주 사용 |
| `void AddItem(UObject*)` / `RemoveItem(UObject*)` | 단일 항목 |
| `void ClearListItems()` | 전체 비움 |
| `int32 GetNumItems() const` | |
| `UObject* GetSelectedItem() const` / `TArray<UObject*> GetSelectedItems() const` | |
| `void SetSelectedItem(UObject*)` / `void ClearSelection()` | |
| `bool IsItemSelected(UObject*) const` | |
| `void ScrollIndexIntoView(int32)` / `void ScrollItemIntoView(UObject*)` | 자식 풀링 시 강제 스크롤 |
| `void RequestRefresh()` | 데이터는 그대로, 표시만 갱신 |
| `void RegenerateAllEntries()` | 모든 EntryWidget 강제 재생성 |
| `void RebuildList()` | Slate 측 SListView 재구성 |
| 이벤트 | `OnItemClicked` · `OnItemDoubleClicked` · `OnItemSelectionChanged` · `OnItemIsHoveredChanged` · `OnItemScrolledIntoView` · `OnListViewScrolled` · `OnFinishedScrolling` |

`EntryWidgetClass` (TSubclassOf<UUserWidget>) 와 `SelectionMode` (None/Single/SingleToggle/Multi) 가 디자이너 핵심 프로퍼티.

### 3.2 UTreeView (`TreeView.h`)

ListView + 펼침/접기. 자식 항목 노출 콜백 추가:

| API | 메모 |
|-----|------|
| `void SetItemExpansion(UObject* Item, bool bExpand)` | |
| `bool IsItemExpanded(UObject*) const` | |
| `void ExpandAll()` / `CollapseAll()` | |
| 이벤트 추가 | `OnItemExpansionChanged` · `OnGetItemChildren` (자식 항목 제공) |

자식 제공 콜백: `void HandleGetItemChildren(UObject* Item, TArray<UObject*>& OutChildren)` — 디자이너에서 바인드.

### 3.3 UTileView (`TileView.h`)

ListView + 그리드 배치 (가로/세로 자동 줄바꿈).

| API | 메모 |
|-----|------|
| `void SetEntryHeight(float)` / `SetEntryWidth(float)` | 셀 사이즈 |
| `void SetTileAlignment(EListItemAlignment)` | EvenlySpaced/LeftAligned/RightAligned/CenterAligned |

### 3.4 EntryWidget 측 (IUserObjectListEntry / IUserListEntry)

**EntryWidget 으로 쓸 UUserWidget 자손에 인터페이스 구현**:

```cpp
UCLASS()
class UMyItemEntry : public UUserWidget, public IUserObjectListEntry
{
    GENERATED_BODY()
protected:
    // IUserObjectListEntry 의 BlueprintNativeEvent
    virtual void NativeOnListItemObjectSet(UObject* ListItemObject) override;
    
    // IUserListEntry 의 BlueprintNativeEvent
    virtual void NativeOnEntryReleased() override;
    virtual void NativeOnItemSelectionChanged(bool bIsSelected) override;
    virtual void NativeOnItemExpansionChanged(bool bIsExpanded) override;
};
```

`IUserObjectListEntry` 의 핵심 콜백 (BlueprintNativeEvent — Native\* prefix override):

| 시그니처 | 호출 시점 |
|----------|-----------|
| `void NativeOnListItemObjectSet(UObject* ListItemObject)` | EntryWidget 이 새 항목에 바인드될 때 — **데이터 → 위젯 동기화 표준 위치** |

`IUserListEntry` 의 핵심 콜백:

| 시그니처 | 호출 시점 |
|----------|-----------|
| `void NativeOnEntryReleased()` | EntryWidget 이 풀로 반환될 때 — 캐시·구독 해제 |
| `void NativeOnItemSelectionChanged(bool bIsSelected)` | 선택 상태 변경 |
| `void NativeOnItemExpansionChanged(bool bIsExpanded)` | (TreeView) 펼침 상태 변경 |

**static 헬퍼** (`UUserObjectListEntryLibrary` / `UUserListEntryLibrary`):

| 함수 | 의미 |
|------|------|
| `UObject* GetListItemObject(TScriptInterface<IUserObjectListEntry>)` | 현재 바인드된 항목 객체 |
| `int32 GetListItemIndex(TScriptInterface<IUserObjectListEntry>)` | 인덱스 |
| `bool IsFirstWidget/IsLastWidget(TScriptInterface<IUserObjectListEntry>)` | 위치 |
| `bool IsListItemSelected(TScriptInterface<IUserListEntry>)` | 선택 |
| `bool IsListItemExpanded(TScriptInterface<IUserListEntry>)` | 펼침 |
| `UListViewBase* GetOwningListView(TScriptInterface<IUserListEntry>)` | 오너 리스트 |

---

## 4. 가상 함수 (오버라이드 포인트)

### 4.1 EntryWidget 측 (UUserWidget + 인터페이스)

**Native\* 프리픽스로 override** 가 표준. BP 이벤트는 자동 발화.

| 시그니처 | Super | 시점 |
|----------|-------|------|
| `virtual void NativeOnListItemObjectSet(UObject*) override` | (인터페이스 — Super 없음) | 항목 바인드 |
| `virtual void NativeOnEntryReleased() override` | (인터페이스) | 풀 반환 |
| `virtual void NativeOnItemSelectionChanged(bool) override` | (인터페이스) | 선택 변경 |
| `virtual void NativeOnItemExpansionChanged(bool) override` | (인터페이스) | 펼침 변경 (TreeView) |

> **UUserWidget 베이스의 라이프사이클** (`NativeOnInitialized` / `NativePreConstruct` / `NativeConstruct` / `NativeDestruct`) 은 **여전히 사용** — 풀링이지만 인스턴스마다 한 번 호출. Super 호출 규약은 [`UMG/references/UUserWidget.md §4.1.1`](../UUserWidget/SKILL.md).

### 4.2 ListView 측 (사용자 정의 풀링/Spawn 변경)

| 시그니처 | Super | 시점 |
|----------|-------|------|
| `virtual TSharedRef<STableViewBase> RebuildListWidget() override` (UListViewBase) | (호출 안 함) | 자체 SListView/STreeView/STileView 생성 |
| `virtual void HandleListEntryHovered(UUserWidget& EntryWidget) override` | **FIRST** | 호버 |
| `virtual void HandleListEntryUnhovered(UUserWidget& EntryWidget) override` | **FIRST** | 언호버 |
| `virtual UUserWidget& OnGenerateEntryWidgetInternal(UObject* Item, TSubclassOf<UUserWidget> DesiredEntryClass, const TSharedRef<STableViewBase>& OwnerTable)` | (override 권장) | EntryWidget 생성 정책 |

---

## 5. 🚨 인밸리데이션 / 갱신 흐름 (의무 섹션)

### 5.1 SetListItems vs RequestRefresh vs RegenerateAllEntries

| 호출 | 효과 | 비용 |
|------|------|------|
| `SetListItems(NewArray)` | 항목 배열 교체 → 가시 영역 EntryWidget 다시 바인드 (`OnListItemObjectSet` 재호출) | 보통 |
| `RequestRefresh()` | 표시 갱신만 (사이즈 재계산) | 낮음 |
| `RegenerateAllEntries()` | 모든 EntryWidget 인스턴스 폐기 + 재생성 | **매우 높음** — 거의 안 씀 |
| `RebuildList()` | Slate SListView 통째 재구성 | **매우 높음** |

**규칙**: 데이터 변경 시 `SetListItems` (또는 `AddItem`/`RemoveItem`). EntryWidget 시각만 갱신은 항목 객체에 `FieldNotify` 변경 → EntryWidget 이 ViewModel 패턴으로 자동 반영.

### 5.2 UScrollBox 와의 차이 — 풀링 효과

| 케이스 | UScrollBox + UVerticalBox | UListView |
|--------|---------------------------|-----------|
| 100개 항목 | 100개 EntryWidget 모두 생성·페인트 | 화면에 보이는 ~10개만 |
| 항목 추가 | `AddChildToVerticalBox` → ChildOrder Invalidate | `AddItem` → 가시 영역만 갱신 |
| 메모리 | O(N) | O(가시 영역) |
| 초기 로딩 | 모든 EntryWidget 인스턴스 생성 시간 | 가시 영역만 즉시 |

**기준**: 항목 수 50개 이상이면 ListView, 그 미만이면 ScrollBox+VerticalBox 도 무방.

### 5.3 EntryWidget 풀링 함정

- **`NativeOnListItemObjectSet` 안에서 강한 외부 참조 보관 금지** — 풀로 반환되어도 참조가 살아있으면 GC 사이클
- **`NativeOnEntryReleased` 에서 모든 구독·델리게이트 해제** — 다음 항목 바인드 전에 깨끗한 상태로
- **EntryWidget 멤버 캐시는 항목별로 무효화** — 풀 재사용 시 옛 항목 데이터 잔존 가능

---

## 6. 예제

### 6.1 인벤토리 ListView — 데이터 객체 + EntryWidget

```cpp
// 데이터 객체 (UObject 자손 - ListView 항목으로 사용)
UCLASS(BlueprintType)
class UInventoryItemData : public UObject
{
    GENERATED_BODY()
public:
    UPROPERTY(BlueprintReadWrite) FText DisplayName;
    UPROPERTY(BlueprintReadWrite) TObjectPtr<UTexture2D> Icon = nullptr;
    UPROPERTY(BlueprintReadWrite) int32 Count = 0;
};

// EntryWidget
UCLASS()
class UInventoryEntryWidget : public UUserWidget, public IUserObjectListEntry
{
    GENERATED_BODY()
protected:
    UPROPERTY(meta=(BindWidget)) UImage* IconImage = nullptr;
    UPROPERTY(meta=(BindWidget)) UTextBlock* NameText = nullptr;
    UPROPERTY(meta=(BindWidget)) UTextBlock* CountText = nullptr;

    virtual void NativeOnListItemObjectSet(UObject* ListItemObject) override
    {
        // 인터페이스 콜백 — Super 호출 의무 없음 (인터페이스)
        if (UInventoryItemData* Item = Cast<UInventoryItemData>(ListItemObject))
        {
            IconImage->SetBrushFromTexture(Item->Icon);
            NameText->SetText(Item->DisplayName);
            CountText->SetText(FText::AsNumber(Item->Count));
        }
    }
    
    virtual void NativeOnEntryReleased() override
    {
        // 풀로 반환 시 — 캐시·구독 해제
        IconImage->SetBrush(FSlateBrush());
        NameText->SetText(FText::GetEmpty());
        CountText->SetText(FText::GetEmpty());
    }

    virtual void NativeOnItemSelectionChanged(bool bIsSelected) override
    {
        // 선택 강조 표시
        SetRenderOpacity(bIsSelected ? 1.0f : 0.7f);
    }
};

// 호스트 위젯
UCLASS()
class UMyInventoryWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    void Refresh(const TArray<FInventoryItem>& Items)
    {
        // FInventoryItem (USTRUCT) → UInventoryItemData (UObject) 변환
        TArray<UObject*> DataObjects;
        DataObjects.Reserve(Items.Num());
        for (const FInventoryItem& Item : Items)
        {
            UInventoryItemData* Data = NewObject<UInventoryItemData>(this);
            Data->DisplayName = Item.DisplayName;
            Data->Icon = Item.Icon;
            Data->Count = Item.Count;
            DataObjects.Add(Data);
        }
        ItemList->SetListItems(DataObjects);
    }

protected:
    UPROPERTY(meta=(BindWidget)) UListView* ItemList = nullptr;

    virtual void NativeConstruct() override
    {
        Super::NativeConstruct();           // ← FIRST: 입력 델리게이트·UpdateCanTick
        ItemList->OnItemClicked().AddUObject(this, &UMyInventoryWidget::HandleItemClicked);
    }

    virtual void NativeDestruct() override
    {
        ItemList->OnItemClicked().RemoveAll(this);
        Super::NativeDestruct();            // ← LAST
    }

    void HandleItemClicked(UObject* Item);
};
```

**디자이너 설정**: `ItemList` (UListView) 의 `EntryWidgetClass = UInventoryEntryWidget`, `SelectionMode = Single`.

### 6.2 TreeView — 카테고리 트리

```cpp
UCLASS(BlueprintType)
class UCategoryNode : public UObject
{
    GENERATED_BODY()
public:
    UPROPERTY(BlueprintReadWrite) FText Name;
    UPROPERTY(BlueprintReadWrite) TArray<TObjectPtr<UCategoryNode>> Children;
};

// 호스트 위젯에서
void UMyCategoryWidget::NativeConstruct()
{
    Super::NativeConstruct();              // ← FIRST
    CategoryTree->SetOnGetItemChildren(FOnGetItemChildren::CreateUObject(this, &UMyCategoryWidget::HandleGetChildren));
    CategoryTree->SetListItems(RootNodes);
}

void UMyCategoryWidget::HandleGetChildren(UObject* Item, TArray<UObject*>& OutChildren)
{
    if (UCategoryNode* Node = Cast<UCategoryNode>(Item))
    {
        for (UCategoryNode* Child : Node->Children)
        {
            OutChildren.Add(Child);
        }
    }
}
```

---

## 7. 운영 가이드 / 함정

| 함정 | 회피 |
|------|------|
| `IUserListEntry` 만 구현 (`IUserObjectListEntry` 누락) | UListView/UTreeView/UTileView 사용 시 `IUserObjectListEntry` 의무 |
| 데이터로 USTRUCT 사용 시도 | UObject 자손이어야 — 임시 wrapper UCLASS 작성 |
| `RegenerateAllEntries()` 자주 호출 | 매우 비용 — `SetListItems` 또는 `RequestRefresh` |
| `ScrollBox + VerticalBox` 에 100+ 항목 | ListView 로 대체 |
| EntryWidget 에 무거운 초기화 | EntryWidget은 풀링 — `NativeOnInitialized` 한 번만 무거운 작업 |
| 풀 반환 시 구독 안 끊음 | `NativeOnEntryReleased` 에서 모두 해제 |
| 항목 객체 GC | 호스트가 `UPROPERTY` 또는 ListView 가 강 참조 유지 (자동) |
| 선택 단일/다중 모드 혼동 | `SelectionMode` (None/Single/SingleToggle/Multi) 디자이너 명시 |

---

## 8. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 가드 |
|------|------|
| `UListViewBase::IsDesignerPreview()` 🛠 | `WITH_EDITOR` (디자이너 미리보기 항목 표시) |
| `UListViewBase::OnPreviewRowsChanged` 🛠 | `WITH_EDITORONLY_DATA` |
| `EntryWidget` 디자이너 미리보기 시 더미 항목 | `IUserObjectListEntry::IsDesignerPreview` 체크 + 분기 |

자세한 에디터 전용 통합은 [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md).

---

## 9. 관련 sub-skill

- [`UMG/UWidget`](../UWidget/SKILL.md) — UWidget 베이스
- [`UMG/UUserWidget`](../UUserWidget/SKILL.md) — UUserWidget Native\* 라이프사이클 + Super 호출 규약
- [`UMG/PanelWidgets`](../PanelWidgets/SKILL.md) — UScrollBox (50개 미만 시) / UInvalidationBox 비교
- [`UMG/StandardWidgets`](../StandardWidgets/SKILL.md) — Image/TextBlock (EntryWidget 자식)
- [`UMG/ViewModel`](../ViewModel/SKILL.md) — FieldNotify 항목 객체 → EntryWidget 자동 갱신
- [`SlateCore/SWidget`](../../SlateCore/references/SWidget.md) — SListView<T> 기반
- [`06_InvalidationHotspots.md §2.6`](../../../references/06_InvalidationHotspots.md) — ListView 풀링 효과
- [`04_OverrideIndex.md §6.5`](../../../references/04_OverrideIndex.md) — Native\* Super 호출 규약 (EntryWidget도 동일)
