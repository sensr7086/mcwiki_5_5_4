---
type: synthesis
title: "UE 5.7.4 — Tree Widget ↔ UObject Expansion State 양방향 sync (UPROPERTY uint8:1 bitfield + Track-level enforce 패턴)"
slug: ue-tree-uobject-expansion-bidirectional-sync
created: 2026-05-19
last_updated: 2026-05-19
project_role: general-pattern
project: vault-general
measured_date: 2026-05-19
status: living
cycle: 5p+5
tier: enriched
sources:
  - "[[sources/ue-streeview-onexpansionchanged-pattern]]"
  - "[[sources/ue-slate-liststrees]]"
  - "[[sources/ue-coreuobject-uobject]]"
  - "[[sources/ue-coreuobject-serialization]]"
  - "[[synthesis/mc-combo-editor-levelsequence-lite]]"
  - "[[synthesis/timeline-custom-slate-widget-pattern]]"
entities:
  - "[[entities/SWidget]]"
concepts:
  - "[[concepts/Slate-Invalidation]]"
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [synthesis, ue-general, slate, streeview, uobject, expansion-state, bidirectional-sync, uproperty-bitfield, virtual-addsection, track-level-enforce]
citation_disclosure: "🟢 12+ (KMCProject Phase 5p+7/5p+8 사례 + Engine 권위 STreeView.h + CoreUObject UObject Modify pattern)"
---

# UE 5.7.4 — Tree Widget ↔ UObject Expansion State 양방향 sync

> **목적**: STreeView 의 Item-level expansion state 를 UObject UPROPERTY 안 영속 (Asset 저장 시 사용자 시각 선호 유지). 사용자 ▶ 클릭 ↔ UObject bitfield 양방향 sync + spurious 콜백 가드 일반화.
>
> **사용처**: Outliner / Inspector / Tree-based asset editor 등에서 Asset 안 사용자 expansion 상태 보존이 필요한 모든 사례.

## 1. 결정 트리

| 시나리오 | 권장 | 이유 |
| -- | -- | -- |
| Session 내 자유 토글, Asset 저장 무관 | Slate Item bool only | RebuildTree 시 default 값으로 reset |
| Asset 저장 영속 (사용자 expansion 선호도 보존) | **UPROPERTY uint8:1 bitfield + 양방향 sync** | 본 패턴 |
| 사용자 글로벌 선호도 (Asset 무관) | UEditorPerProjectUserSettings | 별도 SaveGame / Config |
| 동적 트리 (Item 자체가 자주 변경) | Slate Item bool + 별도 cache | Asset 저장 불가 (Item 식별자 일관성 X) |

## 2. UPROPERTY uint8:1 bitfield 패턴

```cpp
UCLASS()
class UMyTrack : public UObject
{
    GENERATED_BODY()
public:
    UMyTrack();

    /** UI expansion 상태 (UObject 영속). */
    UPROPERTY()  // ⚠ EditAnywhere 미부착 — Detail Panel 노출 X (UI state)
    uint8 bIsExpanded : 1;
};

UMyTrack::UMyTrack()
    : bIsExpanded(0)  // default 접힘 (또는 자손 ctor 에서 1 으로 override)
{
}
```

**의무 사항**:
- `UPROPERTY()` 부착 — serialization 안전
- `EditAnywhere` 미부착 — Detail Panel 사용자 토글과 STreeView ▶ 클릭 sync 부재 회피
- 생성자 안 명시 초기화 — bitfield 는 default 0 보장 안 됨 (uninitialized risk)

## 3. 양방향 sync 패턴 (Eye/Lock/Solo 패턴 미러)

### 3.1 UObject → Item (RebuildTree 시, 권위 = UObject)

```cpp
// SMyOutliner::BuildTrackItem
TSharedPtr<FMyItem> Item = MakeShared<FMyItem>();
Item->bIsExpanded = !!Track->bIsExpanded;
// ...
return Item;

// ApplyExpansionRecursive 가 Item->bIsExpanded → STreeView state 반영
```

### 3.2 Slate → UObject (사용자 ▶ 클릭, 권위 = Slate)

→ [[sources/ue-streeview-onexpansionchanged-pattern]] 본문 참조. 핵심 가드:

```cpp
void SMyOutliner::HandleExpansionChanged(FItemPtr Item, bool bInExpanded)
{
    Item->bIsExpanded = bInExpanded;
    if (UMyTrack* Track = Cast<UMyTrack>(Item->SourceObject.Get()))
    {
        if ((!!Track->bIsExpanded) != bInExpanded)  // ⭐ spurious 콜백 가드
        {
            Track->Modify();
            Track->bIsExpanded = bInExpanded ? 1 : 0;
            MarkAssetDirty();
        }
    }
}
```

⚠ **NotifyTrackChanged (RebuildTree) 미호출** — STreeView callback reentrancy risk. `MarkPackageDirty` 만.

## 4. Multi-level expansion (Group + Sub-channel 패턴)

복합 트리 (예: TransformSection — 3 Group × 3 Channel) 시 각 level 별 UPROPERTY 분리:

```cpp
UCLASS()
class UMyTransformSection : public UMySection {
    GENERATED_BODY()
public:
    UMyTransformSection();

    // Group-level expansion (사용자 어느 그룹을 열어 둘지 영속)
    UPROPERTY() uint8 bExpandLocation : 1;
    UPROPERTY() uint8 bExpandRotation : 1;
    UPROPERTY() uint8 bExpandScale    : 1;
};

UMyTransformSection::UMyTransformSection()
    : bExpandLocation(1)
    , bExpandRotation(1)
    , bExpandScale(1)
{
    bIsExpanded = 1;  // 부모 클래스 bIsExpanded override (default 0 → 1)
}
```

OnExpansionChanged 안 PropertyName 분기 (SubProperty Item type 용):

```cpp
case FItem::EItemType::SubProperty:
{
    if (UMyTransformSection* Sec = Cast<UMyTransformSection>(Item->SourceObject.Get()))
    {
        const FName& PropName = Item->PropertyName;
        if (PropName == TEXT("LocationGroup") && (!!Sec->bExpandLocation) != bInExpanded)
        {
            Sec->Modify();
            Sec->bExpandLocation = bInExpanded ? 1 : 0;
        }
        // ... RotationGroup / ScaleGroup 동일 패턴 ...
    }
    break;
}
```

## 5. Track-level Section enforce 패턴 (페어)

UObject expansion state 와 함께 자주 동반되는 Track-level Section 1개 enforce — virtual `AddSection` override:

```cpp
// 베이스 UMyTrack — virtual 격상 의무 (C3668 함정 51 회피)
UFUNCTION(BlueprintCallable)
virtual UMySection* AddSection(FFrameNumber InStart, FFrameNumber InEnd);

// 자손 override — Section 1개만 허용
UMySection* UMyTransformTrack::AddSection(FFrameNumber InStart, FFrameNumber InEnd)
{
    if (Sections.Num() > 0)
    {
        UE_LOG(LogTemp, Warning,
            TEXT("UMyTransformTrack::AddSection — Track '%s' already has Section. Returning existing."),
            *GetName());
        return Sections[0].Get();
    }
    return Super::AddSection(InStart, InEnd);
}
```

⚠ **C3668 함정** — 베이스 `UFUNCTION(BlueprintCallable)` virtual 격상 누락 시 자손 override 빌드 실패. virtual override 추가 전 base class header grep 의무.

## 6. TrackArea / 외부 viewer 와의 sync

UObject 측 expansion 상태가 변경되면 TrackArea (또는 다른 viewer) 의 row height 계산도 즉시 반영되어야 함.

**패턴**: TrackArea `ComputeRowHeight` 가 UObject->bIsExpanded 를 직접 read — 다음 paint cycle 안 자동 반영.

```cpp
float SMyTrackArea::ComputeRowHeight(const FPaintRow& Row) const
{
    float Height = LaneHeight * Row.Track->GetLaneCount();
    if (Row.Track->bIsExpanded && /* ... */)
    {
        // sub-row 영역 추가
        Height += ComputeSubRowCount(Row.Track) * LaneHeight;
    }
    return Height;
}
```

**ComputeSubRowCount** — UObject 측 모든 expansion bitfield 누적:

```cpp
int32 SMyTrackArea::ComputeSubRowCount(const UMyTrack* Track) const
{
    if (!Track->bIsExpanded || Track->Sections.Num() == 0) return 0;
    const UMyTransformSection* Sec = Cast<UMyTransformSection>(Track->Sections[0].Get());
    if (!Sec) return 0;

    int32 Count = 1;  // Section row
    if (Sec->bIsExpanded)
    {
        Count += 3;  // 3 group headers
        if (Sec->bExpandLocation) Count += 3;
        if (Sec->bExpandRotation) Count += 3;
        if (Sec->bExpandScale)    Count += 3;
    }
    return Count;
}
```

`ComputeRowHeight` 와 `OnPaint` sub-row loop 양쪽이 동일 helper 사용 — **single source of truth** 의무 (drift 방지).

## 7. 함정 카탈로그

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | ApplyExpansionRecursive 안 SetItemExpansion 재진입 시 OnExpansionChanged spurious 발행 | UObject 상태 vs 인자 비교 가드 |
| 2 | OnExpansionChanged 안 RebuildTree 호출 → STreeView state stale + 재귀 | MarkPackageDirty 만 — RebuildTree 미호출 |
| 3 | UPROPERTY 미부착 bitfield Asset 저장 reset | UPROPERTY() 부착 |
| 4 | EditAnywhere 부착 시 Detail Panel ↔ Outliner ▶ 클릭 sync 부재 | EditAnywhere 미부착 또는 PostEditChangeProperty handler |
| 5 | C3668 base non-virtual AddSection override 부적격 | 베이스 virtual 격상 의무 |
| 6 | ComputeRowHeight / OnPaint sub-row loop 별도 빌더 (drift risk) | single helper 공유 (ComputeSubRowCount) |
| 7 | UObject ctor 안 bitfield 초기화 누락 | 생성자 안 명시 (`bIsExpanded(0)` 또는 `(1)`) |
| 8 | BuildXxxItem 시 UObject → Item 역방향 sync 누락 | Item->bIsExpanded = !!UObj->b* 의무 |

## 8. KMCProject 사례 (Phase 5p+8)

- 4종 UPROPERTY uint8:1 bitfield: `UMCComboTrack::bIsExpanded` / `UMCComboSection::bIsExpanded` / `UMCComboTransformSection::bExpandLocation/Rotation/Scale`
- `SMCComboOutlinerView::HandleExpansionChanged` 안 Item type 별 분기 + spurious 가드
- `MarkPackageDirty` only (RebuildTree 미호출)
- `SMCComboTrackArea::ComputeTransformSubRowCount` helper — single source of truth
- 단일 Section enforce — `UMCComboTransformTrack::AddSection` override + 베이스 `UMCComboTrack::AddSection` virtual 격상 (함정 51 C3668)

→ 상세: [[synthesis/mc-combo-editor-levelsequence-lite]] §5.10.4

## 9. Cross-link

- [[sources/ue-streeview-onexpansionchanged-pattern]] — STreeView OnExpansionChanged API 권위 페어
- [[sources/ue-coreuobject-uobject]] — UPROPERTY + Modify pattern
- [[sources/ue-coreuobject-serialization]] — bitfield serialization
- [[synthesis/timeline-custom-slate-widget-pattern]] — Custom Timeline 일반 패턴
- [[synthesis/ue-paint-hittest-shared-rowmap]] — paint + hit-test 동일 row descriptor 공유 (페어 합성)

## 10. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-19 (Cycle 5p+5) | 최초 작성 — UPROPERTY uint8:1 bitfield + STreeView Item bool 양방향 sync 일반화. KMCProject Phase 5p+7/5p+8 (4종 bitfield + HandleExpansionChanged + Track-level AddSection virtual + ComputeSubRowCount helper) 사례 통합. spurious 콜백 가드 + RebuildTree 회피 + multi-level expansion (Group + Channel) + Track-level Section enforce (C3668 함정 51) 8 함정 카탈로그. |
