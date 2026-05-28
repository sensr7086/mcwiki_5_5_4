---
type: synthesis
title: "KMCProject MCComboEditor — Phase 8 Channel Iterator + 100% Cast 마일스톤 (SSoT + Visitor + Auto-Numbering)"
slug: mc-combo-editor-phase-8-channel-iterator
created: 2026-05-21
last_updated: 2026-05-21
project_role: case-study
project: KMCProject
measured_date: 2026-05-21
sources:
  - "[[sources/ue-levelsequence-tracks]]"
  - "[[sources/ue-animation-animinstance]]"
  - "[[synthesis/mc-combo-editor-phase-6-7-inhouse-master]]"
  - "[[synthesis/mc-combo-editor-phase-5g-5l-drag-ux-suite]]"
  - "[[synthesis/mc-combo-section-levelsequence-style-upgrade]]"
  - "[[synthesis/ue-track-area-section-paint-anatomy]]"
concepts:
  - "[[concepts/Slate-Paint-Cycle]]"
status: living
tags: [synthesis, kmcproject, mc-combo, phase-8, phase-8-1, phase-8-2, phase-8-2-2, channel-iterator, ssot, visitor-pattern, auto-numbering, cast-removal-100, evaluator-7th, recommendation-1, recommendation-2, recommendation-3, recommendation-4]
citation_disclosure: "🟢 18 — Engine source 직접 인용 (IMovieScenePlayer Visitor 패턴 / FRichCurve channel API / FName SSoT 패턴) + KMCProject Phase 8 → 권고 5건 일괄 반영 실측 + 7차 ue-evaluator 91/100 LIVE + Cast 24/24 = 100% 매트릭스 + 권고 #1-#5 반영 결과 검증 (2026-05-21)"
---

# KMCProject MCComboEditor — Phase 8 Channel Iterator + 100% Cast 마일스톤

> **2026-05-21 — Phase 8 시리즈 (Visitor + Channel Iterator) 완료 + 7차 ue-evaluator 91/100 권고 5건 일괄 반영** — Cast 24/24 = **100% 제거 달성** + SSoT 채널 테이블 통합 + Asset auto-numbering 정책 옵션화 + BP API 회귀 정책 명시. **Phase 6-7 base page 상위 보완** (전체 Phase 6-8 정리는 [[synthesis/mc-combo-editor-phase-6-7-inhouse-master]] 참조).

## 1. 본 페이지 범위 (Scope)

본 synthesis 는 **Phase 8 series 단독 case study** — Phase 6-7 base 패턴은 cross-link 만.

| 범위 | 본 페이지 | base 페이지 ([[mc-combo-editor-phase-6-7-inhouse-master]]) |
| -- | -- | -- |
| Phase 6a-7a-2 (extensibility / runtime API) | reference §2 | **canonical** §2-§7 |
| **Phase 8 (Visitor 패턴)** | **canonical §2 + §3** | reference §8 |
| **Phase 8.1 (Asset auto-numbering)** | **canonical §4** | reference §11C |
| **Phase 8.2 / 8.2.2 (Channel iterator)** | **canonical §5 + §6** | reference §14 후속 |
| **7차 evaluator 권고 #1-#5 일괄 반영** | **canonical §7** | (반영 결과만 base 변경 이력에 기록) |
| Cast 위치 매트릭스 (24/24) | **canonical §8** | reference §9 (잔존 2 표시) |
| 함정 매트릭스 | **§9 (Phase 8 신규 4건만)** | reference §12 (10건 누적) |

## 2. Phase 8 — Visitor 패턴 (Cast -4 / 누적 22/24 = 92%)

### 2.1 인터페이스 (`MCComboPreviewVisitor.h`, runtime 모듈)

```cpp
class MCPLAYMODULE_API IMCComboPreviewVisitor
{
public:
    virtual ~IMCComboPreviewVisitor() = default;
    virtual void VisitMontageSection(UMCComboMontageSection* Section)     {}
    virtual void VisitTransformSection(UMCComboTransformSection* Section) {}
    virtual void VisitGenericSection(UMCComboSection* Section)            {}
};
```

- Slate 의존 X — forward declare 만.
- Engine 권위: `IMovieScenePlayer` (MovieScene 모듈) 패턴 — runtime interface + Editor 측 구현체.

### 2.2 Section 베이스 + 자손 dispatch

```cpp
// Base (cpp 측 분리 — header inline 시 forward declare 만으로 호출 불가, Visitor-Cycle-01 함정).
void UMCComboSection::AcceptPreviewVisitor(IMCComboPreviewVisitor& V) { V.VisitGenericSection(this); }
void UMCComboMontageSection::AcceptPreviewVisitor(IMCComboPreviewVisitor& V) { V.VisitMontageSection(this); }
void UMCComboTransformSection::AcceptPreviewVisitor(IMCComboPreviewVisitor& V) { V.VisitTransformSection(this); }
```

### 2.3 Editor 측 collector

```cpp
class FLoadAssetPreviewCollector : public IMCComboPreviewVisitor
{
    virtual void VisitMontageSection(UMCComboMontageSection*) override   { /* Montage 수집 */ }
    virtual void VisitTransformSection(UMCComboTransformSection*) override { /* Transform 수집 */ }
};

for (Binding : Bindings) for (Track : Binding->Tracks) for (Section : Track->Sections)
{
    Section->AcceptPreviewVisitor(Collector);  // ⭐ Cast 0
}
```

→ PreviewSceneViewport 안 Track type 별 4 Cast 일괄 제거.

### 2.4 새 Section type 추가 비용 (정직성)

3 곳 수정:
1. Visitor 인터페이스에 `VisitX` 메서드 추가 (default no-op) — **runtime 모듈 헤더 변경 + 빌드 재현** ⚠
2. Section 자손이 `AcceptPreviewVisitor` override 안 `Visitor.VisitX(this)` 호출 (1 줄)
3. Collector 구현체 (Editor 측) 에서 `VisitX` override (필요 시만)

→ collector **본체 무수정**. Cast 분기 산재 vs interface 통합 → trade-off 정직 명시.

## 3. Phase 8.1 — Asset auto-numbering (UX 보완 + 권고 #3 적용)

### 3.1 정책

Asset scope Track 은 **중복 허용** ([[mc-combo-editor-phase-6-7-inhouse-master]] §3, §5). 같은 TrackClass 여러 instance 시 식별 의무:

| TrackName | 시나리오 |
| -- | -- |
| `Audio` | 첫 instance (default `bAlwaysSuffixFirst=false`) |
| `Audio #2` | 2nd instance |
| `Audio #3` | 3rd instance |
| ... | ... |

- **첫 instance suffix skip** — 단일 instance UX 일관성 (사용자가 1개만 사용할 때 시각 노이즈 X).

### 3.2 권고 #3 — `bAlwaysSuffixFirst` UPROPERTY 옵션

`UMCComboAsset` 신규 UPROPERTY:

```cpp
UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Combo|AssetTracks",
    meta = (DisplayName = "Always Suffix First Instance"))
uint8 bAlwaysSuffixFirst : 1;
```

| flag | 첫 instance | 2nd | 3rd |
| -- | -- | -- | -- |
| **false** (default) | `Audio` | `Audio #2` | `Audio #3` |
| **true** | `Audio #1` | `Audio #2` | `Audio #3` |

→ 디자이너가 모든 instance 명시 번호 원할 때 Detail Panel 에서 toggle.

### 3.3 SkeletalMesh scope 와 정책 분리 정합성

| scope | 중복 정책 | suffix |
| -- | -- | -- |
| SkeletalMesh (Binding->Tracks) | 🚫 차단 | 1개만 — suffix 불필요 |
| **Asset (AssetLevelTracks)** | ✅ **허용** | **auto-suffix 정책 (#3.2)** |

## 4. Phase 8.2 / 8.2.2 — Channel Iterator (Cast -2 / 100% 달성)

### 4.1 베이스 API (MCComboSection.h)

```cpp
/** 권고 #4 (2026-05-21) — UFUNCTION 의도적 미부착. */
virtual TArrayView<FMCComboFloatKey> GetMutableChannelKeys(FName ChannelName)
{ return TArrayView<FMCComboFloatKey>(); }

virtual TArray<FName> GetAllChannelNames() const { return {}; }

virtual void SortAllChannels() {}
```

- `TArrayView` — BP 노출 불가 (UStruct ABI 불일치). 의도적으로 BP override 차단 — 새 channel-bearing Section 은 C++ 안 override 만.
- `FMCComboFloatKey` 베이스 헤더 이동 — Phase 8.2 의 핵심 enabler. generic float keyframe 으로 Vector/Color 등 향후 channel Section 재사용 가능.

### 4.2 자손 override (TransformSection — 9 channel)

```cpp
TArrayView<FMCComboFloatKey> UMCComboTransformSection::GetMutableChannelKeys(FName ChannelName)
{
    using namespace MCComboTransformChannelTable;
    if (const FChannelDesc* Desc = FindChannel(ChannelName))
    {
        return this->*(Desc->MemberPtr);  // pointer-to-member 표준
    }
    return TArrayView<FMCComboFloatKey>();
}
```

### 4.3 Phase 8.2.2 — drag/hit-test 마이그레이션 (잔존 2 Cast 해소)

SMCComboTrackArea.cpp 의 4 위치 일괄 generic 화:

| 위치 | 기존 | 8.2.2 후 |
| -- | -- | -- |
| L1568 drag start | `Cast<UMCComboTransformSection>(Sec)` + 9 channel switch | `Sec->AppendSubRowPaintEntries` + `GetMutableChannelKeys(Entry.ChannelName)` |
| L1668 hit-test | Cast + GetUniqueKeyTimes | `Sec->GetDecorationKeyframes()` |
| L1877 drag mid | Cast + 9 channel switch | `Sec->GetAllChannelNames` + `GetMutableChannelKeys(Name)` |
| L2030 drag end | Cast + 직접 9 channel Sort | `Sec->SortAllChannels()` virtual |

→ **24/24 Cast 제거 = 100% 달성**.

## 5. SSoT 채널 테이블 (권고 #1, 2026-05-21)

### 5.1 배경

Phase 8.2.2 완료 후 evaluator 권고 #1: TransformSection 안 9 channel name 문자열이 **5+ 곳** (`GetMutableChannelKeys` / `GetAllChannelNames` / `LookupConst` / `LookupMutable` / `AppendOutlinerSubProperties` / `AppendSubRowPaintEntries` / `SortAllChannels`) 산재 — channel 추가/변경 시 모든 사이트 일관 갱신 의무.

### 5.2 SSoT 테이블 설계 (MCComboTransformTrack.cpp 파일 top 통합)

```cpp
namespace MCComboTransformChannelTable
{
    struct FChannelDesc
    {
        FName    ChannelName;     // "Location.X" 등 — drag/Outliner/Visitor 매핑 키
        FName    GroupName;       // "LocationGroup" 등 — UI 부모 그룹
        float    DefaultValue;    // 빈 channel 보간 fallback (Loc/Rot=0, Scale=1)
        TArray<FMCComboFloatKey> UMCComboTransformSection::* MemberPtr;
        const TCHAR* DisplayLabel;  // "X" / "Roll" / "Z" — TrackArea indented 라벨
    };

    static const FChannelDesc Channels[] =
    {
        { FName("Location.X"),     FName("LocationGroup"), 0.0f, &UMCComboTransformSection::LocationX,     TEXT("X")     },
        { FName("Location.Y"),     FName("LocationGroup"), 0.0f, &UMCComboTransformSection::LocationY,     TEXT("Y")     },
        // ... 7개 더
        { FName("Scale.Z"),        FName("ScaleGroup"),    1.0f, &UMCComboTransformSection::ScaleZ,        TEXT("Z")     },
    };

    struct FGroupDesc
    {
        FName    GroupName;
        const TCHAR* DisplayLabel;
        bool (*GetExpand)(const UMCComboTransformSection*);
        void (*SetExpand)(UMCComboTransformSection*, bool);
    };

    static const FGroupDesc Groups[] = { /* 3 group */ };
}
```

- **Pointer-to-member** (`TArray<FMCComboFloatKey> UMCComboTransformSection::*`) — C++ 표준. UPROPERTY 와 무관 (reflection 미경유).
- **bitfield 제한 우회**: `bExpandLocation:1` 등은 pointer-to-bitfield 표현 불가 → free function pointer `GetExpand/SetExpand` 사용.

### 5.3 사용처 통합

| 사이트 | 변경 |
| -- | -- |
| `GetMutableChannelKeys` | `FindChannel(Name)` + `this->*(Desc->MemberPtr)` |
| `GetAllChannelNames` | `for (Desc : Channels) Names.Add(Desc.ChannelName)` |
| `GetChannelValueAtLocalFrame` | `FindChannel` + `EvaluateChannel(Channel, Frame, Desc->DefaultValue)` |
| `SetChannelKeyAtGlobalFrame` | `FindChannel` + `AddKeyToChannel(this->*MemberPtr, ...)` |
| `SortAllChannels` | `for (Desc : Channels) (this->*MemberPtr).Sort(...)` |
| `SetSubGroupExpanded` | `FindGroup(Name)` + `Desc->SetExpand(this, b)` |
| `AppendOutlinerSubProperties` | `Channels[i].ChannelName` + NSLOCTEXT 라벨 (loc 정적 분석 보존) |
| `AppendSubRowPaintEntries` | `for (Group) for (Channel) ...` — 완전 테이블 순회 |

### 5.4 효과

- **새 channel 추가 시 변경 사이트 = 1** (테이블 한 줄). 기존: 5-7 곳 일관 변경 의무.
- NSLOCTEXT 만 별도 보존 (localization 정적 분석 의무) — label 자체는 SSoT 외부.

## 6. AppendSubRowPaintEntriesWithSectionRow virtual (권고 #2, 2026-05-21)

### 6.1 배경

Phase 8.2.2 의 drag start L1580 안 dummy entry 수동 prepend 패턴:

```cpp
// 권고 #2 반영 전 — dummy entry 명시 불충분
TArray<FMCComboSubRowPaintEntry> SubEntries;
SubEntries.Add(FMCComboSubRowPaintEntry(FString(), /*bIsGroup=*/false));  // 의도 불투명
if (Sec->bIsExpanded)
{
    Sec->AppendSubRowPaintEntries(SubEntries);
}
```

→ caller 가 sub-row index 의미 (`0 = Section row anchor`, `1..N = sub-row entries`) 를 직접 유지. 의도 코드 안 흩어짐.

### 6.2 새 virtual 설계 (MCComboSection.h)

```cpp
/**
 * ⭐ 권고 #2 — Section row + sub-row entries 일괄 반환 (drag start hit-test 명시화).
 *   index 0 = Section main lane row anchor (ChannelName=None, bIsGroup=false) — diamond hit-test 대상 아님.
 *   index 1..N = Section 자손이 bIsExpanded 일 때만 추가하는 sub-row entries.
 *   default 구현이 모든 자손 대상으로 동작 — override 불필요.
 */
virtual void AppendSubRowPaintEntriesWithSectionRow(TArray<struct FMCComboSubRowPaintEntry>& OutEntries) const
{
    OutEntries.Add(FMCComboSubRowPaintEntry(FString(), /*bIsGroup=*/false));
    if (bIsExpanded)
    {
        AppendSubRowPaintEntries(OutEntries);
    }
}
```

### 6.3 사용처 단순화

```cpp
// 권고 #2 반영 후 — 의도 명시
TArray<FMCComboSubRowPaintEntry> SubEntries;
Sec->AppendSubRowPaintEntriesWithSectionRow(SubEntries);
```

→ caller 의 dummy entry 책임 제거. 함정 회피 (Section row 정의 변경 시 본 virtual만 수정).

## 7. 7차 evaluator 권고 5건 일괄 반영 매트릭스

| 권고 | 범위 | 산출 | 위치 |
| -- | -- | -- | -- |
| **#1** | 9 channel name SSoT 통합 | `MCComboTransformChannelTable::Channels[]` (9 desc) + `Groups[]` (3 desc) | `MCComboTransformTrack.cpp` 파일 top |
| **#2** | `AppendSubRowPaintEntriesWithSectionRow` virtual 분리 | dummy entry 책임 베이스 virtual 안 격리 | `MCComboSection.h` + `SMCComboTrackArea.cpp` L1577-1580 |
| **#3** | `bAlwaysSuffixFirst` UPROPERTY + docstring | suffix 정책 디자이너 선택 가능 + `AddAssetLevelTrack` docstring 명문화 | `MCComboAsset.h` + `MCComboAsset.cpp` |
| **#4** | `SortAllChannels` / `GetAllChannelNames` / `GetMutableChannelKeys` BP API 회귀 명시 | 3 메서드 docstring 안 UFUNCTION 미부착 의도 설명 | `MCComboSection.h` |
| **#5** | Phase 8 channel iterator 전용 synthesis 페이지 | 본 페이지 신규 — base 페이지와 cross-link | `wiki/synthesis/mc-combo-editor-phase-8-channel-iterator.md` |

## 8. Cast 위치 매트릭스 — 100% 완성

> Phase 6-7 분 18 위치 ([[mc-combo-editor-phase-6-7-inhouse-master]] §9 참조). 본 매트릭스는 Phase 8 시리즈 6 위치만 명시.

| 위치 | Phase | 상태 |
| -- | -- | -- |
| `SMCComboPreviewSceneViewport.cpp` Montage Track Cast | 8 | ✅ Visitor |
| `SMCComboPreviewSceneViewport.cpp` Transform Track Cast | 8 | ✅ Visitor |
| `SMCComboPreviewSceneViewport.cpp` Montage Section Cast | 8 | ✅ Visitor |
| `SMCComboPreviewSceneViewport.cpp` Transform Section Cast | 8 | ✅ Visitor |
| `SMCComboTrackArea.cpp` L1568 drag start (9 channel switch) | 8.2.2 | ✅ `GetMutableChannelKeys` + `AppendSubRowPaintEntries` |
| `SMCComboTrackArea.cpp` L1668 hit-test | 8.2.2 | ✅ `GetDecorationKeyframes` |
| `SMCComboTrackArea.cpp` L1877 drag mid (9 channel switch) | 8.2.2 | ✅ `GetAllChannelNames` + `GetMutableChannelKeys` |
| `SMCComboTrackArea.cpp` L2030 drag end (9 channel Sort) | 8.2.2 | ✅ `SortAllChannels` virtual |

→ **24/24 = 100% 달성** (2026-05-20 Phase 8.2.2). 권고 #2 (2026-05-21) 가 본 코드 패턴을 추가 명시화 — Cast 추가 제거는 없지만 의도 transparency 강화.

## 9. 함정 매트릭스 (Phase 8 신규 4건)

| # | 함정 | Phase | 정답 |
| -- | -- | -- | -- |
| Visitor-Cycle-01 | header inline 호출 시 `IMCComboPreviewVisitor` 완전 정의 의무 | 8 | cpp 분리 + `MCComboPreviewVisitor.h` include cpp 측 |
| **Visitor-Module-01** | 새 Section type 추가 시 Visitor 인터페이스 헤더 (runtime 모듈) 수정 → runtime 모듈 빌드 재현 의무. Cast 분기 산재 vs interface 통합 trade-off 정직 명시. | 8 | 시나리오 D 의 비용 (3 곳 — interface header + section override + collector) 명시 |
| **Bitfield-PtrMember-01** | UPROPERTY bitfield (`uint8 bExpand* : 1`) 는 C++ 표준 pointer-to-bitfield 표현 불가 — SSoT 테이블 안 직접 매핑 불가. | 8 (권고 #1) | free function pointer `GetExpand/SetExpand` 우회. table 의 `bool(*)(const T*)` 사용. |
| **BP-Override-Mismatch-01** | `GetMutableChannelKeys / GetAllChannelNames / SortAllChannels` 를 BP 노출 시 자손이 sort 대상 (UPROPERTY TArray) 동적 추가 불가 — override 가 의미적으로 표현 불가. | 8.2.2 (권고 #4) | UFUNCTION 의도적 미부착 + docstring 안 근거 명문화. 새 channel type 은 C++ 만. |

## 10. Engine 권위 인용 매트릭스 (Phase 8 시리즈 신규)

| Engine API | KMCProject 미러 | 사용처 |
| -- | -- | -- |
| `IMovieScenePlayer` (MovieScene 모듈) — runtime interface + Editor 구현체 패턴 | `IMCComboPreviewVisitor` + `FLoadAssetPreviewCollector` | Phase 8 |
| Pointer-to-member (C++ 표준) | `TArray<FMCComboFloatKey> UMCComboTransformSection::* MemberPtr` | Phase 8 SSoT (권고 #1) |
| `FName` SSoT 패턴 — name table 인덱스 (UE 5.7 NameTable.h) | `MCComboTransformChannelTable::Channels[].ChannelName` | Phase 8 SSoT (권고 #1) |
| `FRichCurve::GetCopyOfKeys` / `FRichCurveKey` (의미) | `GetMutableChannelKeys` (generic mutate view 반환) + `FMCComboFloatKey` 베이스 이동 | Phase 8.2 |
| `UPROPERTY meta = (DisplayName = ...)` — Detail Panel 라벨 | `bAlwaysSuffixFirst` | Phase 8.1 (권고 #3) |
| `NSLOCTEXT` literal string 정적 분석 — loc extraction 의무 | `AppendOutlinerSubProperties` 안 NSLOCTEXT 유지 (SSoT 외부) | Phase 8 (권고 #1 hybrid) |

## 11. 사용 시나리오 — Phase 8 시리즈 특화

### A: 새 channel-bearing Section 추가 (예: VectorSection — Translation X/Y/Z only, 3 channel)

C++ 1 파일:

```cpp
UCLASS(BlueprintType)
class UMCComboVectorSection : public UMCComboSection
{
    UPROPERTY(EditAnywhere) TArray<FMCComboFloatKey> X;
    UPROPERTY(EditAnywhere) TArray<FMCComboFloatKey> Y;
    UPROPERTY(EditAnywhere) TArray<FMCComboFloatKey> Z;

    // 채널 테이블 (cpp 안 — TransformSection 패턴 미러)
    // 3 channel desc + 3 channel name FName
    virtual TArrayView<FMCComboFloatKey> GetMutableChannelKeys(FName Name) override { /* table lookup */ }
    virtual TArray<FName> GetAllChannelNames() const override { /* table iterate */ }
    virtual void SortAllChannels() override { /* table iterate Sort */ }
    virtual void AppendSubRowPaintEntries(TArray<FMCComboSubRowPaintEntry>&) const override { /* ... */ }
};
```

→ Editor drag/hit-test/sort 무수정. PreviewSceneViewport Visitor 인터페이스에 `VisitVectorSection` 추가만 의무 (시나리오 D 비용 명시).

### B: AudioTrack 다중 instance 추가 (Asset scope + auto-numbering)

```
Asset ⊕ → MCComboAudioTrack 클릭 (1st instance) → TrackName = "Audio"
Asset ⊕ → MCComboAudioTrack 클릭 (2nd instance) → TrackName = "Audio #2"
Asset ⊕ → MCComboAudioTrack 클릭 (3rd instance) → TrackName = "Audio #3"

(Asset Detail Panel 안 bAlwaysSuffixFirst=true 토글 후)
Asset ⊕ → MCComboAudioTrack 클릭 (4th instance) → TrackName = "Audio #4" (기존 명명 유지)
```

→ 디자이너가 instance 별 다른 SoundCue 설정 + Outliner 안 식별 자동.

## 12. 후속 권고 (Phase 9+)

| Phase | 내용 | 우선순위 | ROI |
| -- | -- | -- | -- |
| **9.0** | `UMCComboPlayerComponent` (Actor Tick → Asset::EvaluateAtFrame chain) — Phase 7b 잔여 | **높음** | **실 런타임 검증 진입** |
| 9.1 | `UMCComboVectorSection` / `UMCComboColorSection` 신규 — Phase 8 SSoT 테이블 패턴 재사용 검증 | 중 | 새 channel type 추가 비용 실측 |
| 9.2 | DRY 정리 — `GetOutlinerSubRowCount` 자동 계산 (spec 배열에서 추론) | 낮음 | Article 2 (SSoT) 강화 |
| 9.3 | base page split — Phase 6-7-8 통합 분량 절제 — Phase 9 시 새 base 분리 권고 | 낮음 | Article 8 (분량 절제) |

## 13. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-21 (신규) | Phase 8 시리즈 (Visitor + Channel Iterator) + 100% Cast 마일스톤 전용 case study 신규. base page ([[mc-combo-editor-phase-6-7-inhouse-master]]) 와 cross-link. 7차 evaluator 권고 5건 일괄 반영 결과 §7. SSoT 테이블 설계 §5. 함정 4건 신규 §9 (Visitor-Cycle-01 / Visitor-Module-01 / Bitfield-PtrMember-01 / BP-Override-Mismatch-01). citation_disclosure 18. |
