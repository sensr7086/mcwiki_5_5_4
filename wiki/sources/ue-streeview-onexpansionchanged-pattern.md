---
type: source
title: "UE Slate — STreeView OnExpansionChanged 양방향 sync + spurious 콜백 guard 패턴"
slug: ue-streeview-onexpansionchanged-pattern
source_path: raw/ue-wiki-llm/skills/Slate/references/STreeView-OnExpansionChanged.md
source_kind: enriched
source_date: 2026-05-19
ingested: 2026-05-19
last_updated: 2026-05-19
cycle: 5p+5
tier: enriched
related_concepts:
  - "[[concepts/Slate-Paint-Cycle]]"
  - "[[concepts/Slate-Invalidation]]"
related_sources:
  - "[[sources/ue-slate-liststrees]]"
  - "[[sources/ue-coreuobject-uobject]]"
  - "[[sources/ue-slatecore-swidget]]"
trigger: "KMCProject MCComboEditor Phase 5p+8 — TransformTrack 9 channel tree (Outliner) 의 사용자 ▶ 클릭 expansion 상태 영속 (UPROPERTY uint8:1) + TrackArea 양방향 sync. ApplyExpansionRecursive 재진입 spurious 콜백 회피 가드 발견."
tags: [ue, slate, streeview, onexpansionchanged, fonexpansionchanged, expansion-state, bidirectional-sync, reentrancy-guard, slate-event, outliner-pattern]
---

# UE Slate — STreeView OnExpansionChanged 양방향 sync + spurious 콜백 guard

> Source: `Engine/Source/Runtime/Slate/Public/Widgets/Views/STreeView.h` L109 (FOnExpansionChanged typedef) + L192 (SLATE_EVENT) + L1100 (SetItemExpansion impl) + KMCProject MCComboEditor Phase 5p+8 실측 사례.
> Parent: [[sources/ue-slate-liststrees]] §STreeView

## 1. Summary

STreeView 의 `OnExpansionChanged` 델리게이트로 사용자 ▶ 클릭 시점 외부 상태 (UObject 측 영속 expansion bitfield) 와 양방향 sync 구현. 

**핵심 함정**: 외부 트리거 (RebuildTree → ApplyExpansionRecursive → SetItemExpansion) 가 OnExpansionChanged 콜백을 재발행 → UObject Modify() 폭주 / 무한 루프 risk. spurious 콜백 가드 의무.

## 2. Engine 권위 (STreeView.h)

```cpp
template <typename ItemType>
class STreeView : public SListView<ItemType> {
public:
    /** L109 — FOnExpansionChanged delegate typedef */
    DECLARE_DELEGATE_TwoParams(FOnExpansionChanged, ItemType, bool /*bExpanded*/);

    /** L192 — SLATE_EVENT */
    SLATE_BEGIN_ARGS(STreeView<ItemType>) {}
        SLATE_EVENT(typename FOnGenerateRow, OnGenerateRow)
        SLATE_EVENT(typename FOnGetChildren, OnGetChildren)
        SLATE_EVENT(typename FOnTableViewScrolled, OnTreeViewScrolled)
        SLATE_EVENT(typename FOnExpansionChanged, OnExpansionChanged)  // ⭐
        ...
    SLATE_END_ARGS()

    /** L1100 — SetItemExpansion (외부 호출). 내부적으로 expansion state 갱신 후 OnExpansionChanged 발행. */
    void SetItemExpansion(ItemType TheItem, bool ShouldBeExpanded);

    /** 현재 expansion 상태 read. */
    bool IsItemExpanded(ItemType TheItem) const;
};
```

⚠ `SetItemExpansion` 가 OnExpansionChanged 를 **항상** 발행 — 외부 (RebuildTree 의 ApplyExpansionRecursive) 가 의도적으로 expansion 상태 적용 시에도 콜백 트리거.

## 3. 양방향 sync 패턴 (KMCProject Phase 5p+8 사례)

UObject 측 영속 expansion 상태 (UPROPERTY uint8:1 bitfield) 와 Slate Item 측 bool 의 양방향 sync.

### 3.1 BuildXxxItem — UObject → Item (RebuildTree 시)

```cpp
// SMCComboOutlinerView::BuildTrackItem
TSharedPtr<FMCComboOutlinerItem> Item = MakeShared<FMCComboOutlinerItem>();
Item->bIsExpanded = !!Track->bIsExpanded;  // UObject UPROPERTY uint8:1 → bool
// ...
return Item;
```

이후 `ApplyExpansionRecursive` 가 Item->bIsExpanded → `TreeView->SetItemExpansion(Item, true/false)` 호출.

### 3.2 OnExpansionChanged — Slate → UObject (사용자 ▶ 클릭 시)

```cpp
// Construct 안 binding
TreeView = SNew(STreeView<FItemPtr>)
    .OnExpansionChanged(this, &SMyOutliner::HandleExpansionChanged)
    ...;

void SMyOutliner::HandleExpansionChanged(FItemPtr Item, bool bInExpanded)
{
    Item->bIsExpanded = bInExpanded;  // 즉시 Item 동기 (메모리 캐시)

    // UObject 측 영속 — 단 spurious 콜백 가드 의무.
    if (UMyTrack* Track = Cast<UMyTrack>(Item->SourceObject.Get()))
    {
        if ((!!Track->bIsExpanded) != bInExpanded)  // ⭐ 실제 변경 시만
        {
            Track->Modify();                         // transactional
            Track->bIsExpanded = bInExpanded ? 1 : 0;
            MarkAssetDirty();
        }
    }
}
```

## 4. ⚠ Spurious 콜백 가드 — 의무 패턴

**문제 시나리오**:
1. 사용자 액션 (Add Section 등) → `NotifyTrackChanged` → `RebuildTree`
2. `RebuildTree` 안 새 Item 생성 + `ApplyExpansionRecursive(Item)` 호출
3. `ApplyExpansionRecursive` 가 `TreeView->SetItemExpansion(Item, Item->bIsExpanded)` 호출
4. `SetItemExpansion` 가 **OnExpansionChanged 콜백 재발행**
5. 콜백 안 `UObject->Modify()` + `MarkAssetDirty()` 호출 → 사용자 액션 1회 마다 dirty 폭주

**가드 패턴** (Phase 5p+8 적용):

```cpp
void SMyOutliner::HandleExpansionChanged(FItemPtr Item, bool bInExpanded)
{
    Item->bIsExpanded = bInExpanded;

    // ⚠ UObject 상태 vs Slate 인자 비교 후 실제 변경 시만 Modify.
    //   ApplyExpansionRecursive 안 SetItemExpansion 재진입 시 UObject 측이 이미 동기 상태 → skip.
    if (UMyTrack* Track = Cast<UMyTrack>(Item->SourceObject.Get()))
    {
        const bool bUObjState = !!Track->bIsExpanded;
        if (bUObjState != bInExpanded)  // ⭐ Engine 권위 위반 차단
        {
            Track->Modify();
            Track->bIsExpanded = bInExpanded ? 1 : 0;
            MarkAssetDirty();
        }
        // else: spurious 콜백 — UObject 측 이미 동일 → no-op
    }
}
```

## 5. ⚠ RebuildTree 회피 — Re-entrancy risk

**문제**: OnExpansionChanged 안 `NotifyTrackChanged` → `RebuildTree` 호출 시:
- STreeView callback 내부 → RebuildTree → 새 Item 생성 (이전 Item 메모리 해제 가능) → STreeView 의 state stale
- ApplyExpansionRecursive 재진입 → 또 OnExpansionChanged → 무한 재귀 risk

**회피**: HandleExpansionChanged 안 `RebuildTree` **미호출**. 단 `MarkPackageDirty` 만 — TrackArea 등 외부 viewer 는 다음 paint cycle 안 UObject 상태 자동 반영 (OnPaint 안 UObject 직접 read).

```cpp
void SMyOutliner::HandleExpansionChanged(FItemPtr Item, bool bInExpanded)
{
    // ...
    if (Track && bUObjState != bInExpanded)
    {
        Track->Modify();
        Track->bIsExpanded = bInExpanded ? 1 : 0;

        // ⚠ NotifyTrackChanged (RebuildTree) 미호출 — STreeView callback reentrancy risk.
        // MarkPackageDirty 만 — TrackArea 는 다음 paint 시 UObject->bIsExpanded 자동 반영.
        if (UMyAsset* Asset = GetAsset())
        {
            Asset->MarkPackageDirty();
        }
    }
}
```

## 6. 결정 트리 — 상태 영속 vs Session-only

| 시나리오 | 영속 위치 | 트리거 |
| -- | -- | -- |
| Session 내 자유 토글 (Asset 저장 무관) | Slate Item bool only (FMCComboOutlinerItem::bIsExpanded) | RebuildTree 시 default 값으로 reset |
| Asset 저장 필요 (사용자 expansion 선호도 영속) | **UObject UPROPERTY uint8:1 bitfield** | `Modify()` + `MarkPackageDirty` |
| 사용자 선호도 (전역, Asset 무관) | UEditorPerProjectUserSettings 또는 별도 SaveGame | session 저장 |

KMCProject Phase 5p+8 — Asset 안 expansion 영속 채택 (사용자가 비싼 setup 한 후 닫고 다시 열 때 동일 시각 유지).

## 7. UPROPERTY uint8:1 bitfield 패턴

```cpp
// UObject 헤더
UPROPERTY()  // EditAnywhere 미부착 — Detail Panel 노출 X (UI state only)
uint8 bIsExpanded : 1;

// 생성자 초기화
UMyTrack::UMyTrack() : bIsExpanded(0)  // default 접힘
{
}
```

⚠ **UPROPERTY 부착 의무** — 미부착 시:
- Serialize 안 됨 (Asset 저장 시 default 값 reset)
- GC 가드 무관 (bitfield 는 GC 안 함, 그러나 UPROPERTY 부착하지 않으면 reflection 누락)

⚠ **EditAnywhere 미부착** — Detail Panel 안 노출 시 사용자가 직접 토글 가능하지만, Outliner ▶ 클릭과 sync 안 됨 (PostEditChangeProperty 안 별도 handler 필요).

## 8. 함정 카탈로그

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | ApplyExpansionRecursive 안 SetItemExpansion 재진입 시 OnExpansionChanged 콜백 트리거 → Modify 폭주 | UObject 상태 vs 인자 비교 후 실제 변경 시만 Modify (`(!!UObj->b*) != bInExpanded`) |
| 2 | OnExpansionChanged 안 RebuildTree 호출 시 STreeView state stale + 재귀 risk | MarkPackageDirty 만 — RebuildTree 미호출 (TrackArea 등 외부는 paint cycle 안 자동 반영) |
| 3 | UPROPERTY 미부착 bitfield — Asset 저장 시 default reset | UPROPERTY() 부착 의무 |
| 4 | EditAnywhere 부착 시 Detail Panel ↔ Outliner ▶ 클릭 sync 부재 | EditAnywhere 미부착 또는 PostEditChangeProperty 별도 handler |
| 5 | OnExpansionChanged 콜백 안 Item->bIsExpanded 갱신 누락 | 첫 줄 `Item->bIsExpanded = bInExpanded` 의무 (메모리 캐시 sync) |
| 6 | 새 Item 생성 시 UObject 상태 → Item 역방향 sync 누락 | BuildXxxItem 안 `Item->bIsExpanded = !!UObj->bIsExpanded` 의무 |

## 9. Cross-link

### vault sources
- [[sources/ue-slate-liststrees]] §STreeView (베이스 정의)
- [[sources/ue-coreuobject-uobject]] UPROPERTY meta + Modify pattern
- [[sources/ue-slatecore-swidget]] SLATE_EVENT 매크로

### concepts
- [[concepts/Slate-Invalidation]] — RebuildTree 회피 reasoning

### KMCProject 사례
- [[synthesis/mc-combo-editor-levelsequence-lite]] §5.10.4 (Phase 5p+8 Outliner expansion 양방향 sync)
- [[synthesis/ue-tree-uobject-expansion-bidirectional-sync]] (이 패턴의 합성 페어)

## 10. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-19 (Cycle 5p+5) | 최초 작성 — STreeView FOnExpansionChanged typedef + SLATE_EVENT + SetItemExpansion API + 양방향 sync 패턴 (UObject → Item / Slate → UObject) + spurious 콜백 가드 의무 + RebuildTree 회피 (re-entrancy risk) + 결정 트리 (영속 vs session-only) + UPROPERTY uint8:1 bitfield 패턴 + 6 함정 카탈로그. KMCProject Phase 5p+8 실측 사례 inline. |
