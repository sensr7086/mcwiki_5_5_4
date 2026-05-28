---
type: synthesis
title: "UE 5.7.4 — Slate Paint + Hit-test 동일 Row Descriptor 공유 패턴 (custom widget 정합 의무)"
slug: ue-paint-hittest-shared-rowmap
created: 2026-05-19
last_updated: 2026-05-19
project_role: general-pattern
project: vault-general
measured_date: 2026-05-19
status: living
cycle: 5p+5
tier: enriched
sources:
  - "[[sources/ue-slatecore-drawing]]"
  - "[[sources/ue-slatecore-swidget]]"
  - "[[sources/ue-slatecore-input]]"
  - "[[synthesis/timeline-custom-slate-widget-pattern]]"
  - "[[synthesis/mc-combo-editor-levelsequence-lite]]"
entities:
  - "[[entities/SWidget]]"
  - "[[entities/FSlateDrawElement]]"
concepts:
  - "[[concepts/Slate-Paint-Cycle]]"
tags: [synthesis, ue-general, slate, custom-widget, paint, hit-test, row-descriptor, single-source-of-truth, drift-prevention, kmcproject-case-study]
citation_disclosure: "🟢 10+ (KMCProject Phase 5p+8 Minor M1 실측 + Engine 권위 FSlateDrawElement / OnMouseButtonDown / OnPaint)"
---

# UE 5.7.4 — Slate Paint + Hit-test 동일 Row Descriptor 공유

> **목적**: Custom Slate widget 의 OnPaint 와 OnMouseButtonDown(Hit-test) 가 동일 순서/구조 row descriptor 배열을 공유 → 시각과 hit 정합성 보장. drift (paint 그렸지만 클릭 hit 안 됨, 또는 hit 됐지만 painting 위치 어긋남) 회피.
>
> **사용처**: STreeView / SListView 외 custom OnPaint widget (timeline / curve editor / canvas / graph editor 등) 안 다중 row / 다중 element 가 동적 expansion 상태에 따라 visible/invisible 토글되는 모든 사례.

## 1. 문제 — Paint vs Hit-test drift

custom Slate widget 안 OnPaint 가 N 개 element (rows / diamonds / handles) 를 동적 순서로 그리고, OnMouseButtonDown 이 동일 element 에 hit-test 시도. 두 곳이 별도 빌더로 작성된 경우:

- Paint loop: `for (i = 0..N) { computeY(i); paint(i); }`
- Hit-test loop: `for (i = 0..M) { computeY(i); hitTest(i); }`

**Drift 발생 시나리오**:
- Paint 안 새 row 추가 후 Hit-test 갱신 누락 → 시각상 보이지만 클릭 hit 안 됨
- Hit-test 안 expansion 분기 누락 → 사용자가 group 접었지만 클릭 시 옛 위치 row 가 hit
- Paint 는 SubRow 12개 그렸는데 Hit-test 는 8개만 (group 펼침 상태 분기 비대칭)
- Y 좌표 계산식 둘이 미세하게 다름 (예: `+3px` offset 한 곳만 적용)

**Engine 사례**: `SGraphEditor` / `SListView` 등 Slate 표준 widget 은 paint + hit-test 가 동일 내부 데이터 (Items array, panel slots) 를 공유 → drift 본질적으로 차단. custom widget 작성 시 동일 보장 의무.

## 2. 해결 — Single Source of Truth Row Descriptor

**핵심 원칙**: Paint loop 와 Hit-test loop 가 *동일* row descriptor 배열을 빌드하거나, 공통 helper 가 빌드 후 양쪽 공유.

### 2.1 Pattern A — 공통 helper 호출

```cpp
struct FRowDescriptor
{
    int32 SubIdx;
    FString Label;
    const TArray<FKey>* Channel;  // nullptr = group/header
    bool bIsGroup;
};

class SMyCustomWidget : public SCompoundWidget
{
private:
    void BuildVisibleRowDescriptors(const FState& State, TArray<FRowDescriptor, TInlineAllocator<16>>& Out) const;

    virtual int32 OnPaint(...) const override
    {
        TArray<FRowDescriptor, TInlineAllocator<16>> Rows;
        BuildVisibleRowDescriptors(State, Rows);
        for (int32 i = 0; i < Rows.Num(); ++i)
        {
            const float RowY = StartY + i * RowHeight;
            // paint Rows[i] at RowY
        }
    }

    virtual FReply OnMouseButtonDown(...) override
    {
        TArray<FRowDescriptor, TInlineAllocator<16>> Rows;
        BuildVisibleRowDescriptors(State, Rows);
        const int32 HitIdx = static_cast<int32>((LocalPos.Y - StartY) / RowHeight);
        if (Rows.IsValidIndex(HitIdx)) { /* hit Rows[HitIdx] */ }
    }
};
```

### 2.2 Pattern B — 캐시 + invalidate (perf 우선)

매 paint 마다 빌더 호출이 hot path 시 캐시:

```cpp
mutable TArray<FRowDescriptor, TInlineAllocator<16>> CachedRows;
mutable bool bRowDescriptorsDirty = true;

void InvalidateRowDescriptors() { bRowDescriptorsDirty = true; }

const TArray<FRowDescriptor>& GetRowDescriptors() const
{
    if (bRowDescriptorsDirty)
    {
        BuildVisibleRowDescriptors(State, CachedRows);
        bRowDescriptorsDirty = false;
    }
    return CachedRows;
}
```

**Invalidate 시점** — state 변경 callback (OnExpansionChanged / SetSection / 등):
```cpp
void HandleExpansionChanged(...) { /* state update */; InvalidateRowDescriptors(); }
```

## 3. KMCProject 실측 사례 — Phase 5p+8 Minor M1

**증상** (Cycle 5p+5 evaluator Minor M1):
- `SMCComboTrackArea::OnPaint` (L864-895) — `FSubRowDef` struct + SubRows 빌더 (TransformTrack sub-row 13개)
- `SMCComboTrackArea::OnMouseButtonDown` (L1057-1082) — `FSubRowCh` struct + SubRowChannels 빌더 (per-channel hit-test)
- 두 빌더가 *거의 동일* 순서 (Section row → 위치 group → X/Y/Z → 회전 group → ...) 이지만 별도 struct 분기

**Drift risk**:
- 향후 group 순서 변경 (예: 위치/회전/스케일 → 회전/위치/스케일) 시 한 곳만 변경 + 다른 곳 누락 → paint 와 hit 어긋남
- group 펼침 분기 조건 한 곳만 변경 (예: 새 group 추가) → 12 sub-row 시각 vs 9 sub-row hit

**Minor M1 권고 (Cycle 5p+5 evaluator)**:
- 단일 helper `BuildTransformSubRowDescriptors(TransformSection, OutDescriptors)` 도입
- struct 통합 (`FSubRowDef` 또는 `FSubRowCh` 단일화 — Label + Channel ptr + bIsGroup)
- Paint loop 와 Hit-test loop 양쪽이 동일 helper 호출

## 4. 일반화 함정 카탈로그

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | Paint loop 와 Hit-test loop 가 별도 빌더 (drift risk) | 공통 helper `BuildVisibleRowDescriptors` 호출 |
| 2 | Y 좌표 계산식 paint/hit-test 차이 (`+3` offset 한 곳만) | 좌표 산출도 helper 분리 (`GetRowY(SubIdx)`) |
| 3 | Hit-test 안 expansion 분기 누락 (Paint 만 갱신) | helper 안 expansion 분기 통합 — 양쪽 자동 sync |
| 4 | 매 paint 호출 마다 빌더 (perf hit) | 캐시 + invalidate 시점 명시 |
| 5 | cache invalidate 시점 누락 (state 변경했지만 cache stale) | OnExpansionChanged / state setter 안 InvalidateRowDescriptors 호출 |
| 6 | Row descriptor struct 둘이 분리 (이름만 다른 동일 필드) | 단일 struct 정의 — 두 곳 공유 |
| 7 | InlineAllocator size 부적절 (16 vs 32 시 spillover heap alloc) | 일반적 최대 row 수 + 약간 margin (TransformTrack = 13, allocator 16 충분) |
| 8 | Tooltip / cursor / drag mode 분기도 같은 row descriptor 사용 안 함 | hit-test 통합 후 Tooltip/cursor 등 모든 derived state 도 helper 통해 |

## 5. 결정 트리 — 적용 여부

| 시나리오 | 권장 |
| -- | -- |
| 단순 정적 row (1-3개 고정) | 분리 빌더 OK (drift risk 낮음) |
| 동적 expansion state 다중 row | **단일 helper 의무** (drift 본질적 회피) |
| 다중 level expansion (group + sub-channel) | **단일 helper + 캐시 권장** (perf + drift 양쪽) |
| Tooltip / Cursor / Hover 도 row 별 분기 필요 | **단일 helper + derived state 분리** (3+ consumer 공유) |

## 6. Engine 권위 참조

| 패턴 | 위치 | 인용 |
| -- | -- | -- |
| `FSlateDrawElement::Make*` paint | `SlateCore/Public/Rendering/DrawElements.h` | OnPaint 안 호출 |
| `OnPaint(...)` 시그니처 | `SlateCore/Public/Widgets/SWidget.h` | virtual override |
| `OnMouseButtonDown(...)` 시그니처 | 동일 | virtual override |
| `STableViewBase` Items array 공유 | `Slate/Public/Widgets/Views/STableViewBase.h` | Engine widget 의 paint+hit 통합 사례 |
| `SGraphEditor` Nodes 배열 | `Editor/GraphEditor/Public/SGraphEditor.h` | 동일 |

## 7. Cross-link

- [[sources/ue-slatecore-drawing]] — FSlateDrawElement OnPaint cycle
- [[sources/ue-slatecore-input]] — OnMouseButtonDown / OnCursorQuery
- [[synthesis/timeline-custom-slate-widget-pattern]] §3 OnPaint 9-Layer + §4 Drag mode 결정 트리
- [[synthesis/mc-combo-editor-levelsequence-lite]] §5.10.4 (Phase 5p+8 sub-row paint + hit-test)
- [[sources/ue-streeview-onexpansionchanged-pattern]] — expansion 상태 cache invalidation 시점

## 8. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-19 (Cycle 5p+5) | 최초 작성 — Slate Paint + Hit-test 동일 row descriptor 공유 패턴 일반화. KMCProject Phase 5p+8 Minor M1 (FSubRowDef vs FSubRowCh 분리 빌더 drift risk) 실측 사례. Pattern A (공통 helper 호출) + Pattern B (캐시 + invalidate) 분리 + 결정 트리 + 8 함정 카탈로그. Engine 권위 참조 (FSlateDrawElement / OnPaint / OnMouseButtonDown / STableViewBase / SGraphEditor 패턴 미러). |
