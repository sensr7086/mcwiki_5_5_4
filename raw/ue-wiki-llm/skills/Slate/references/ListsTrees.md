---
name: slate-liststrees
description: SListView + STreeView + STableRow + ITableRow - 리스트/트리 표시.
---

# Slate · ListsTrees sub-skill

> **모듈**: Slate (Tier 3 — 게임/에디터 공통)
> **위치**: `Engine/Source/Runtime/Slate/Public/Widgets/Views/` (9 헤더)
> **다루는 범위**: 가상 풀링 리스트 — `SListView<T>` · `STreeView<T>` · `STileView<T>` · `STableViewBase` · `STableRow<T>` · `SHeaderRow` + `IItemsSource` / `ITableRow`.

---

## 1. 개요

대량 데이터 표시 시 **가시 영역만 풀링**해서 그리는 SCompoundWidget. UMG 의 `UListView`/`UTreeView`/`UTileView` ([`UMG/ListWidgets`](../../UMG/references/ListWidgets.md)) 가 본 위젯들의 BP 노출 래퍼. C++ 인하우스 툴에서는 직접 SListView<T> 사용.

핵심 패턴:
1. **데이터 소스** (`TArray<TSharedPtr<FMyItem>>` 또는 `IItemsSource`)
2. **항목 위젯 생성기** (`OnGenerateRow` 콜백 — `STableRow<T>` 자손 반환)
3. **선택 처리** (`OnSelectionChanged`)

---

## 2. 핵심 헤더

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `STableViewBase.h` | `STableViewBase` | 모든 리스트 뷰 베이스 |
| `SListView.h` | `SListView<ItemType>` (template) | 1차원 리스트 |
| `STreeView.h` | `STreeView<ItemType>` | 펼침/접기 |
| `STileView.h` | `STileView<ItemType>` | 그리드 |
| `STableRow.h` | `STableRow<ItemType>` | 항목 행 베이스 |
| `ITableRow.h` | `ITableRow` 인터페이스 | 행 인터페이스 |
| `SHeaderRow.h` | `SHeaderRow` | 컬럼 헤더 |
| `SExpanderArrow.h` | `SExpanderArrow` | 트리 펼침 화살표 |
| `IItemsSource.h` | `IItemsSource` 인터페이스 | 동적 데이터 소스 |

---

## 3. SListView<T> (가장 자주)

### 3.1 SLATE_BEGIN_ARGS 핵심

| 인자 | 의미 |
|------|------|
| `SLATE_ARGUMENT(const TArray<ItemType>*, ListItemsSource)` | 데이터 배열 포인터 |
| `SLATE_EVENT(FOnGenerateRow, OnGenerateRow)` | 행 생성 콜백 — `TSharedRef<ITableRow>` 반환 |
| `SLATE_EVENT(FOnSelectionChanged, OnSelectionChanged)` | 선택 변경 |
| `SLATE_EVENT(FOnMouseButtonDoubleClick, OnMouseButtonDoubleClick)` | 더블클릭 |
| `SLATE_ATTRIBUTE(ESelectionMode::Type, SelectionMode)` | None / Single / SingleToggle / Multi |
| `SLATE_ARGUMENT(EOrientation, Orientation)` | Vertical / Horizontal |
| `SLATE_ARGUMENT(float, ItemHeight)` | 항목 높이 (가상 풀링 계산용) |

### 3.2 사용

```cpp
// 데이터 — TSharedPtr<FMyItem> 권장 (TWeakPtr 검사 가능)
struct FMyItem { FString Name; int32 Count; };

class SMyListWidget : public SCompoundWidget
{
public:
    SLATE_BEGIN_ARGS(SMyListWidget) {}
    SLATE_END_ARGS()

    void Construct(const FArguments& InArgs)
    {
        // 데이터 채우기
        for (int32 i = 0; i < 100; i++)
        {
            Items.Add(MakeShared<FMyItem>(FMyItem{ FString::Printf(TEXT("Item %d"), i), i * 10 }));
        }

        ChildSlot[
            SAssignNew(ListView, SListView<TSharedPtr<FMyItem>>)
            .ListItemsSource(&Items)
            .OnGenerateRow(this, &SMyListWidget::HandleGenerateRow)
            .OnSelectionChanged(this, &SMyListWidget::HandleSelectionChanged)
            .SelectionMode(ESelectionMode::Single)
        ];
    }

    TSharedRef<ITableRow> HandleGenerateRow(TSharedPtr<FMyItem> Item, const TSharedRef<STableViewBase>& OwnerTable)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(SMyListWidget_HandleGenerateRow);
        return SNew(STableRow<TSharedPtr<FMyItem>>, OwnerTable)
        [
            SNew(SHorizontalBox)
            +SHorizontalBox::Slot()[ SNew(STextBlock).Text(FText::FromString(Item->Name)) ]
            +SHorizontalBox::Slot().AutoWidth()[ SNew(STextBlock).Text(FText::AsNumber(Item->Count)) ]
        ];
    }

    void HandleSelectionChanged(TSharedPtr<FMyItem> SelectedItem, ESelectInfo::Type SelectInfo)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(SMyListWidget_HandleSelectionChanged);
        // ...
    }

private:
    TArray<TSharedPtr<FMyItem>> Items;
    TSharedPtr<SListView<TSharedPtr<FMyItem>>> ListView;
};
```

### 3.3 자주 쓰는 API

| API | 의미 |
|-----|------|
| `void RequestListRefresh()` | 데이터 변경 후 표시 갱신 (가벼움) |
| `void RebuildList()` | 모든 행 재생성 (무거움) |
| `void ScrollIntoView(ItemType)` | 항목 스크롤 |
| `void SetSelection(ItemType, ESelectInfo::Type)` | 선택 |
| `void ClearSelection()` | 선택 해제 |
| `TArray<ItemType> GetSelectedItems() const` | 선택 항목들 |
| `int32 GetNumItemsSelected() const` | 선택 수 |
| `bool IsItemSelected(ItemType) const` | 검사 |

---

## 4. STreeView<T>

`SListView<T>` 확장 — 펼침/접기 + 자식 항목 콜백:

```cpp
SAssignNew(TreeView, STreeView<TSharedPtr<FMyNode>>)
.TreeItemsSource(&RootItems)
.OnGenerateRow(...)
.OnGetChildren(this, &SMyTree::HandleGetChildren)     // ← 추가
.OnExpansionChanged(this, &SMyTree::HandleExpansionChanged)
.SelectionMode(ESelectionMode::Single);

void HandleGetChildren(TSharedPtr<FMyNode> Item, TArray<TSharedPtr<FMyNode>>& OutChildren)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SMyTree_HandleGetChildren);
    OutChildren = Item->Children;
}
```

추가 API:
- `void SetItemExpansion(ItemType, bool bExpand)`
- `bool IsItemExpanded(ItemType) const`
- `void RequestTreeRefresh()`

---

## 5. STileView<T>

`SListView<T>` 확장 — 그리드 배치 + 셀 사이즈:

```cpp
SAssignNew(TileView, STileView<TSharedPtr<FMyItem>>)
.ListItemsSource(&Items)
.OnGenerateTile(...)
.ItemWidth(128.0f)
.ItemHeight(128.0f)
.ItemAlignment(EListItemAlignment::EvenlySpaced);
```

---

## 6. STableRow<T> — 항목 행 커스터마이징

```cpp
class SMyCustomRow : public STableRow<TSharedPtr<FMyItem>>
{
public:
    void Construct(const FArguments& InArgs, const TSharedRef<STableViewBase>& InOwnerTable, TSharedPtr<FMyItem> InItem)
    {
        Item = InItem;
        STableRow<TSharedPtr<FMyItem>>::Construct(
            STableRow::FArguments()
            .Style(&FAppStyle::Get().GetWidgetStyle<FTableRowStyle>("TableView.Row")),
            InOwnerTable);

        ChildSlot[ /* 사용자 정의 콘텐츠 */ ];
    }

    // override 가능
    virtual int32 OnPaint(...) const override
    {
        // 사용자 정의 페인트 (선택 강조 등)
        return STableRow::OnPaint(...);
    }

private:
    TSharedPtr<FMyItem> Item;
};
```

---

## 7. SHeaderRow — 컬럼 헤더 (다중 컬럼)

```cpp
TSharedPtr<SHeaderRow> Header = SNew(SHeaderRow)
    + SHeaderRow::Column("Name").DefaultLabel(LOCTEXT("Name", "Name")).FillWidth(2.0f)
    + SHeaderRow::Column("Count").DefaultLabel(LOCTEXT("Count", "Count")).FillWidth(1.0f);

SAssignNew(ListView, SListView<TSharedPtr<FMyItem>>)
.HeaderRow(Header)
.OnGenerateRow(this, &SMyWidget::HandleGenerateRow);

// HandleGenerateRow 안에서 GenerateWidgetForColumn 콜백 사용
TSharedRef<ITableRow> HandleGenerateRow(TSharedPtr<FMyItem> Item, const TSharedRef<STableViewBase>& OwnerTable)
{
    return SNew(SMyMultiColumnRow, OwnerTable, Item);    // SMultiColumnTableRow 자손
}
```

`SMultiColumnTableRow<T>` 자손 — `GenerateWidgetForColumn(FName ColumnName)` override.

---

## 8. IItemsSource — 동적 데이터 (드물게 사용)

`TArray<ItemType>*` 직접 전달 대신 인터페이스로 동적 제공:

```cpp
SAssignNew(ListView, SListView<TSharedPtr<FMyItem>>)
.ItemsSource(MyItemsSource)    // TSharedPtr<IItemsSource>
.OnGenerateRow(...);
```

거의 안 쓰임 — `TArray*` 가 일반적.

---

## 9. SExpanderArrow — 트리 펼침 화살표

`STreeView` 의 행 안에서 사용. STableRow 가 자동 생성하므로 직접 인스턴스화는 드묾.

---

## 10. 가상 함수 / Super 호출

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `STableRow::Construct` | (자체 처리) | |
| `STableRow::OnPaint` | **FIRST** (or LAST) | 베이스가 선택 강조 그림 |
| `STableViewBase::Tick` | **FIRST** | 매 프레임 — 베이스가 풀링 진행 |
| `SListView::OnSelectionChanged` (override 시) | (자체) | 콜백 |
| `STreeView::OnExpansionChanged` (override 시) | (자체) | 콜백 |

`Tick` override 시 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) 스코프 의무.

---

## 11. 함정

| 함정 | 회피 |
|------|------|
| `RequestListRefresh` 안 호출 — 데이터 변경 안 보임 | `Items.Add(...)` 후 호출 |
| `RebuildList` 자주 호출 — 무거움 | 데이터 변경은 `RequestListRefresh`, 구조 변경만 `RebuildList` |
| `OnGenerateRow` 안에서 매번 SNew | 비용 — TileView가 풀링이지만 새 항목은 매번 생성 — 가벼운 위젯 사용 |
| `TSharedPtr<FMyItem>` 대신 `FMyItem` 직접 — 슬라이싱 | 항상 TSharedPtr / TWeakPtr |
| 데이터 소스 nullptr | `ListItemsSource(&Items)` 의 Items 가 항상 유효해야 |
| TreeView `OnGetChildren` 결과 캐싱 안 됨 | 매 펼침마다 호출 — 캐싱 |
| 100,000+ 항목 | SListView 도 메모리 부담 — 페이징 또는 가상 데이터 소스 |
| 콜백 람다 캡처 강 참조 | TWeakPtr |
| `OnGenerateRow` / 콜백 스코프 누락 | [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) |
| HeaderRow 사용 시 STableRow — 다중 컬럼 안 됨 | `SMultiColumnTableRow<T>` 자손 작성 |

---

## 12. 에디터 전용? 🛠

런타임 — **게임/에디터 공통**. UMG 의 `UListView` 가 본 위젯의 BP 래퍼.

---

## 13. 관련 sub-skill

- [`UMG/ListWidgets`](../../UMG/references/ListWidgets.md) — UListView/UTreeView/UTileView (BP 노출 + EntryWidget 풀링)
- [`SlateCore/SWidget`](../../SlateCore/references/SWidget.md) — SCompoundWidget 베이스
- [`SlateCore/Layout`](../../SlateCore/references/Layout.md) — FArrangedChildren / FChildren
- [`Slate/CommonWidgets`](../CommonWidgets/SKILL.md) — STableRow 안에 들어가는 표준 위젯
- 교차: [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) (OnGenerateRow / OnGetChildren / OnSelectionChanged 스코프)
