---
type: source
title: "UE Editor — TUniquePtr<FScopedTransaction> drag begin/end 1-entry-per-drag 패턴 (undo stack 폭주 회피)"
slug: ue-fscopedtransaction-drag-1-entry
source_path: raw/ue-wiki-llm/skills/Editor/references/FScopedTransaction-Drag-1-Entry.md
source_kind: enriched
source_date: 2026-05-19
ingested: 2026-05-19
last_updated: 2026-05-19
cycle: 5p+5
tier: enriched
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
related_sources:
  - "[[sources/ue-coreuobject-uobject]]"
  - "[[sources/ue-editor-asseteditorapi]]"
  - "[[sources/ue-slatecore-input]]"
trigger: "KMCProject MCComboEditor Phase 3+ §B + Phase 5p+6/+7/+8 — drag 중 매 pixel Section->Modify() 호출 시 undo stack 수십 entry 폭주. Engine ICurveEditorDragOperation.h L156 TUniquePtr<FScopedTransaction> 멤버 패턴 미러. drag begin 1회 Modify + end 시 transaction commit."
tags: [ue, editor, fscopedtransaction, transaction, undo, drag, mouse-button-down, mouse-button-up, tuniqueptr, raii, kmcproject-case-study]
---

# UE Editor — TUniquePtr<FScopedTransaction> drag 1-entry-per-drag 패턴

> Source: `Engine/Source/Editor/CurveEditor/Public/ICurveEditorDragOperation.h` L156 (Engine TUniquePtr 멤버 패턴) + `Engine/Source/Editor/CurveEditor/Private/Views/SInteractiveCurveEditorView.cpp` L1622 (사용처) + `Engine/Source/Editor/Kismet/Public/SSCSEditor.h` L474 (자매 패턴) + KMCProject MCComboEditor 실측 사례.

## 1. Summary

`FScopedTransaction` 는 RAII pattern 으로 생성자 안 `GEditor->BeginTransaction` + 소멸자 안 commit. 일반적으로 단일 scope 내 stack 변수로 사용. **그러나 drag 처럼 begin (MouseButtonDown) / end (MouseButtonUp) 가 콜백 분리된 시나리오** 에서는 `TUniquePtr<FScopedTransaction>` 으로 heap allocate + RAII commit — undo stack 1 entry per drag 보장.

**문제**: drag 중 매 OnMouseMove 호출 마다 `Section->Modify()` → undo stack 매 pixel entry 추가 → 수십~수백 entry 폭주 + Ctrl+Z 한 번에 1 pixel 복원 (사용자 경험 망가짐).

**해결**: drag begin 시 `TUniquePtr<FScopedTransaction>` 멤버 생성 + 1회 Modify. drag 중 `SetXxx(..., bMarkDirty=false)` → Modify skip. drag end 시 `Reset()` (destructor → commit) → undo stack 1 entry per drag.

## 2. Engine 권위 미러 패턴

### 2.1 ICurveEditorDragOperation.h L156

```cpp
class ICurveEditorDragOperation
{
public:
    // ...
protected:
    TUniquePtr<FScopedTransaction> Transaction;  // L156 — drag scope 멤버
};
```

### 2.2 SInteractiveCurveEditorView.cpp L1622

```cpp
class SInteractiveCurveEditorView
{
private:
    // L1622
    TUniquePtr<FScopedTransaction> RootTransaction;
};
```

### 2.3 SSCSEditor.h L474

```cpp
class SSCSEditor
{
private:
    // L474
    TUniquePtr<FScopedTransaction> OngoingCreateTransaction;
};
```

→ 모두 begin/end 가 분리된 인터랙션 (drag / create modal / 등) 에서 1-entry-per-interaction 패턴.

## 3. 표준 적용 패턴 (KMCProject 미러)

```cpp
class SMyTrackArea : public SCompoundWidget
{
public:
    void Construct(const FArguments& InArgs);

    virtual FReply OnMouseButtonDown(...) override;
    virtual FReply OnMouseMove(...) override;
    virtual FReply OnMouseButtonUp(...) override;

private:
    /**
     * Phase 3+ §B — drag mode 시작 시 1회 begin, 종료 시 reset (RAII commit).
     *
     * Engine 권위:
     *   - CurveEditor/Public/ICurveEditorDragOperation.h L156
     *   - CurveEditor/Private/Views/SInteractiveCurveEditorView.cpp L1622
     *   - Kismet/Public/SSCSEditor.h L474
     */
    TUniquePtr<FScopedTransaction> ActiveDragTransaction;
};

// .cpp
FReply SMyTrackArea::OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& Event)
{
    if (Event.GetEffectingButton() != EKeys::LeftMouseButton) return FReply::Unhandled();

    UMySection* Section = HitTestSection(...);
    if (!Section || Section->bIsLocked) return FReply::Handled();

    // drag mode 결정 (Edge / Move / Slip / 등)
    DragMode = /* ... */;
    DragOffset = /* ... */;

    // ⭐ Drag 시작 — 1회 Begin + Modify.
    FText TransactionLabel;
    switch (DragMode)
    {
        case Move:      TransactionLabel = LOCTEXT("MoveSection", "Move Section"); break;
        case TrimLeft:  TransactionLabel = LOCTEXT("TrimSection", "Trim Section"); break;
        // ...
    }
    ActiveDragTransaction = MakeUnique<FScopedTransaction>(TransactionLabel);
    Section->Modify();  // 1회만 — drag scope 전체 변경 캡처

    return FReply::Handled().CaptureMouse(SharedThis(this));
}

FReply SMyTrackArea::OnMouseMove(const FGeometry& MyGeometry, const FPointerEvent& Event)
{
    if (DragMode == None || !SelectedSection.IsValid()) return FReply::Unhandled();

    // ⭐ drag 중 매 pixel 호출 — bMarkDirty=false 로 Modify skip.
    //   Section->SetRange 안 bMarkDirty 매개변수 분기 의무 (Phase 3+ §B):
    //     true (default) — 외부 단발 setter 호환 (Modify 1 호출 = undo stack 1 entry)
    //     false           — drag mode 안 매 pixel 호출, Modify skip (호출처가 FScopedTransaction 으로 묶음)
    Section->SetRange(NewStart, NewEnd, /*bMarkDirty=*/false);

    return FReply::Handled();
}

FReply SMyTrackArea::OnMouseButtonUp(const FGeometry& MyGeometry, const FPointerEvent& Event)
{
    if (DragMode != None)
    {
        DragMode = None;
        // ⭐ Drag 종료 — TUniquePtr::Reset → FScopedTransaction destructor → GEditor->EndTransaction (commit).
        //   undo stack 에 drag 1 회당 1 entry 만 남음.
        ActiveDragTransaction.Reset();
        return FReply::Handled().ReleaseMouseCapture();
    }
    return FReply::Unhandled();
}
```

## 4. SetXxx 안 bMarkDirty 매개변수 분기 의무

drag 중 매 pixel 호출되는 setter (`SetRange` / `SetLocation` / `SetRotation` 등) 는 `bMarkDirty` 매개변수 추가 의무 — drag 모드 안 Modify skip 가드:

```cpp
class UMySection : public UObject
{
public:
    /**
     * Range 직접 셋.
     *
     * Phase 3+ §B — bMarkDirty 매개변수:
     *   true (default)  : 외부 호출처 호환 — Modify() 호출 (undo stack 1 entry / 호출)
     *   false           : drag 중 매 pixel 호출 시 — Modify() skip. 호출처가 FScopedTransaction 으로
     *                     묶어 1 entry 만 남기는 패턴 (Engine ICurveEditorDragOperation.h L156 미러)
     */
    void SetRange(FFrameNumber InStart, FFrameNumber InEnd, bool bMarkDirty = true);
};

void UMySection::SetRange(FFrameNumber InStart, FFrameNumber InEnd, bool bMarkDirty)
{
#if WITH_EDITOR
    if (bMarkDirty)
    {
        Modify();  // single setter 사용 시 — undo stack 1 entry
    }
#endif
    SectionRange = FMyFrameRange(InStart, InEnd);
}
```

⚠ **default 유지**: `true` (기존 호출처 호환 — 외부 단발 setter / Detail Panel 직접 입력 / BP 호출 등 모두 default Modify 동작).

## 5. 다중 drag mode 통합 패턴

여러 drag mode (Move / Trim / Slip / Scrub / Diamond drag / 등) 모두 동일 `ActiveDragTransaction` 멤버 공유:

```cpp
enum class EDragMode : uint8 { None, Move, TrimLeft, TrimRight, SlipLeft, SlipRight, Scrub, TransformKey };

FReply SMyTrackArea::OnMouseButtonDown(...)
{
    // ... drag mode 결정 ...
    if (DragMode == Scrub) return FReply::Handled().CaptureMouse(SharedThis(this));  // Scrub 은 transaction 없음 (asset 변경 X)

    FText TransactionLabel;
    switch (DragMode)
    {
        case Move:          TransactionLabel = LOCTEXT("MoveSection",       "Move Section"); break;
        case TrimLeft:
        case TrimRight:     TransactionLabel = LOCTEXT("TrimSection",       "Trim Section"); break;
        case SlipLeft:
        case SlipRight:     TransactionLabel = LOCTEXT("SlipSection",       "Slip Section"); break;
        case TransformKey:  TransactionLabel = LOCTEXT("MoveTransformKey",  "Move Transform Key"); break;
        default:            TransactionLabel = LOCTEXT("EditSection",       "Edit Section"); break;
    }
    ActiveDragTransaction = MakeUnique<FScopedTransaction>(TransactionLabel);
    Section->Modify();
    // ...
}
```

⚠ **Scrub 제외** — Scrub 은 asset 변경 없음 (transient `CurrentScrubFrame` 만), transaction 불필요. CaptureMouse 만.

## 6. 캡처 해제 + cleanup

drag 종료 시 mouse capture release + transaction commit + 추가 cleanup (sort / lane 재할당 등):

```cpp
FReply SMyTrackArea::OnMouseButtonUp(...)
{
    if (DragMode == TransformKey)
    {
        // 추가 cleanup — drag 중 변경된 key Time 들 정렬 (sort 위치 어긋남 회피).
        if (UMyTransformSection* TSec = DraggedKeySection.Get())
        {
            TSec->SortAllChannels();
        }
        DraggedKeySection.Reset();
        DraggedKeyIndex = INDEX_NONE;
    }
    else if (DragMode == Move || DragMode == TrimLeft || DragMode == TrimRight)
    {
        // Lane 재할당 (mid-drag 깜박임 회피 — drag end 시점 1회만)
        if (UMySection* Section = SelectedSection.Get())
        {
            if (UMyTrack* OwnerTrack = Cast<UMyTrack>(Section->GetOuter()))
            {
                Section->AssignAutoRowIndex(OwnerTrack->Sections);
            }
        }
    }

    DragMode = None;
    ActiveDragTransaction.Reset();  // ⭐ FScopedTransaction destructor → commit
    return FReply::Handled().ReleaseMouseCapture();
}
```

## 7. 함정 카탈로그

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | drag 중 매 pixel Section->Modify() → undo stack 폭주 | TUniquePtr<FScopedTransaction> drag begin 시 1회 Modify + setter bMarkDirty=false |
| 2 | SetXxx 의 bMarkDirty 매개변수 default `false` 로 변경 (외부 호출처 호환 깨짐) | default `true` 의무 — drag 호출처가 명시 `false` |
| 3 | OnMouseButtonUp 안 Reset 누락 → transaction 영구 유지 (다음 drag 시 nested) | 모든 return path 에 Reset 보장 (focus lost / mouse out 등 edge case 포함) |
| 4 | drag 중 다른 input (키보드 단축키) 으로 새 transaction 시작 — nested transaction | 외부 transaction trigger 안 ActiveDragTransaction.IsValid() 검사 |
| 5 | Scrub mode 가 transaction 시작 (asset 변경 없는데 undo stack entry) | Scrub 분기 시 transaction 미생성 — CaptureMouse 만 |
| 6 | TUniquePtr 가 SP (SharedPtr) 가 아닌 UniquePtr 인데 헷갈려 SP 사용 | Engine 권위 미러 — TUniquePtr (단일 ownership, drag widget 만 보유) |
| 7 | FScopedTransaction stack 변수로 begin/end 분리 시 호환 안 됨 | TUniquePtr heap 사용 의무 (콜백 분리 시) |
| 8 | drag 중 Section 이 GC 되면 Modify 호출 후 deleted object 안전성 | TWeakObjectPtr<USection> 으로 보유 + drag move 마다 IsValid 검사 |

## 8. KMCProject 적용 사례 (Phase 3+ §B ~ Phase 5p+8 누적)

- **Phase 3+ §B**: `SMCComboTrackArea::ActiveDragTransaction` 멤버 + `OnMouseButtonDown` 안 mode 별 label + Modify / `OnMouseMove` 안 `SetRange(..., bMarkDirty=false)` / `OnMouseButtonUp` 안 Reset
- **Phase 5p+6**: Diamond drag mode (TransformKey) 추가 — 동일 패턴
- **Phase 5p+7**: 9 channel mutate (Time 동시 변경) — Reset 시 `SortAllChannels` cleanup
- **Phase 5p+8**: Per-channel diamond drag (DraggedChannelName 분기) — 동일 transaction wrap

→ 상세: [[synthesis/mc-combo-editor-levelsequence-lite]] §5.10.2 + §5.10.3 + §5.10.4

## 9. Cross-link

- [[sources/ue-coreuobject-uobject]] — UObject::Modify pattern
- [[sources/ue-editor-asseteditorapi]] — Asset 안 transaction scope
- [[sources/ue-slatecore-input]] — OnMouseButtonDown / Move / Up 콜백 분리
- [[synthesis/timeline-custom-slate-widget-pattern]] §11 — KMCProject 실측 inline
- [[synthesis/mc-combo-editor-levelsequence-lite]] §5.10 — Phase 5p+6/7/8 누적

## 10. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-19 (Cycle 5p+5) | 최초 작성 — TUniquePtr<FScopedTransaction> drag begin/end 1-entry-per-drag 패턴 일반화. Engine 권위 3 사례 (ICurveEditorDragOperation.h L156 / SInteractiveCurveEditorView.cpp L1622 / SSCSEditor.h L474) + KMCProject Phase 3+ §B ~ Phase 5p+8 누적 적용 사례. SetXxx 의 bMarkDirty 매개변수 분기 의무 + 다중 drag mode 통합 패턴 + Scrub 제외 + cleanup (sort / lane 재할당). 8 함정 카탈로그 (undo 폭주 / bMarkDirty default / Reset 누락 / nested transaction / Scrub 분기 / TUniquePtr vs SP / heap 의무 / GC 안전). |
