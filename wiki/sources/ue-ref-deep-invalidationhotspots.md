---
type: source
title: "06_InvalidationHotspots — Deep Reference (위젯별 핫스팟 §2 카탈로그)"
slug: ue-ref-deep-invalidationhotspots
source_path: raw/ue-wiki-llm/references/deep/InvalidationHotspotsDeep.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-15
related_entities:
  - "[[entities/SWidget]]"
  - "[[entities/UUserWidget]]"
related_concepts:
  - "[[concepts/Slate-Invalidation]]"
  - "[[concepts/Slate-Paint-Cycle]]"
tags: [ue, reference, ui, invalidation, enriched-card]
citation_disclosure: "🟢 11 / 🟡 3 / 🔴 0 · raw verified · Cycle 5f #1 enrich"
---

# 06_InvalidationHotspots — Deep Reference (§2 위젯별 핫스팟)

> Source: [[raw/ue-wiki-llm/references/deep/InvalidationHotspotsDeep.md]]
> 부모: [[sources/ue-ref-06-invalidationhotspots]] · [[concepts/Slate-Invalidation]]
> Cycle 5f #1 — stub 카드 → enrich 카드 (위젯 카테고리 8종 핫스팟 매트릭스 + 3-tier marker)

## 1. Summary

🟢 UMG/Slate 위젯 8 카테고리별 인밸리데이션 핫스팟 + 회피 패턴. Layout reason 다발 위젯 (RichText / EditableText / ListView / VerticalBox 등) 식별 + 대안.

## 2. 위젯 카테고리 8종 핫스팟 매트릭스 (raw §2)

### 2.1 텍스트 위젯 (raw §2.1) 🟢

- **STextBlock/UTextBlock**: `SetText` (Layout — 폭 재계산) / `SetColorAndOpacity` (Paint) / `SetFont` (Layout, 메트릭 재측정) / `SetJustification` (Layout)
  - 🟢 핫스팟: 매 프레임 텍스트 변경 (HP/MP) — Layout 비용
  - 🟢 대안: `TSlateAttribute<FText, EInvalidateWidgetReason::Layout>` 자동화 + 고정 폭 폰트
- **URichTextBlock** (가장 비싼): `SetText` (Layout + 마크업 파싱 + Run 재구성 + decorator 인스턴스화)
  - 🟢 회피 5 패턴: 단순 텍스트는 STextBlock / 일부만 변경시 분리 / 채팅 누적 / InvalidationBox 안 두지 X / 커스텀 SLeafWidget 대체
- **EditableText/MultiLine** 🟢: 키 입력 (Layout, 매 키) / 선택 영역 (Paint) / 멀티라인 줄바꿈 (Layout × 줄 수)

### 2.2 리스트/트리 위젯 (raw §2.2) 🟢

- **SListView/UListView/UTileView/UTreeView**: `RequestListRefresh` (Layout, 모든 가시 행 재생성) / 스크롤 (Layout, 가시 행 재배치)
- 🟢 회피 5 패턴: 변경된 행만 `RequestRowItemRefresh` / `UDynamicEntryBox` 풀링 / `IUserListEntry::OnListItemObjectSet` (위젯 재사용 + 데이터 갱신만) / 고비용 정렬 회피 / 가상화 활성
- 🟢 표준 패턴: `NativeOnListItemObjectSet` override — `NativeConstruct` 가 아닌

### 2.3 진행도/애니메이션 (raw §2.3) 🟢

- **SProgressBar/UProgressBar**: `SetPercent` (Paint — Layout 없음) / `SetFillColorAndOpacity` (Paint)
  - 🟢 대안: `TSlateAttribute<float, Paint>` 자동화 / 큰 변화만 갱신 (`abs > 0.01f`) / `RegisterActiveTimer` (Tick 대신)
- **Throbber/CircularThrobber** 🟢: 자동 휘발성 (매 프레임 Paint) — `UInvalidationBox` 안 두면 캐시 무효화. 외부 배치 + Visibility 토글
- **FCurveSequence** 🟢: Play (Paint, 재생 중 매 프레임) — 정상 (재생 끝나면 자동 ActiveTimer 종료)

### 2.4 버튼/체크박스 (raw §2.4) 🟢

- **SButton/UButton**: 호버 (Paint) / 클릭 (Paint) / `SetButtonStyle` (Layout)
- 🟢 대안: `UInvalidationBox` 배경에 / `IsFocusable=false` 포커스 인밸리데이션 회피
- **SCheckBox/UCheckBox**: `SetIsChecked` (Paint) / 호버 (Paint) — 가벼움

### 2.5 패널 위젯 자식 변경 (raw §2.5) 🟢

- **SBoxPanel/UVerticalBox/UHorizontalBox**: `AddChild` (ChildOrder + Prepass + Layout) / `RemoveChild` (ChildOrder)
- 🟢 회피 3 패턴: 채팅창 → ListView/ScrollBox / 풀링 + Visibility 토글 / 정적 자식 InvalidationBox
- **UCanvasPanel/SConstraintCanvas**: `SetPosition` (Layout, 드래그 매 프레임) / `SetSize` (Layout) / `SetZOrder` (ChildOrder)
- 🟢 대안: `SetRenderTransform` (Layout 변경 X) / 드래그 종료 시만 SetPosition

### 2.6 NativeOnPaint/NativePaint override (raw §2.6) 🟢

- 🚨 NativePaint override = 자동 휘발성 → InvalidationBox 캐시 비활성. **마지막 수단**
- 🟢 회피 5 패턴: 표준 UMG 조합 우선 / 작은 영역만 C++ SLeafWidget 분리 / LayerId 단조 증가 (Super 반환값 +1) / FSlateBrush 멤버 캐시 / DrawCall 배치 친화
- 페어: [[sources/ue-umg-uuserwidget]] §5.4 + [[sources/ue-slatecore-drawing]] §5.2

### 2.7 입력/포커스 (raw §2.7) 🟢/🟡

- **포커스 변경** (`OnFocusReceived/Lost`): Paint (게임패드 내비 빈번)
- 🟢 대안: `SBorder` 단일 위젯으로 포커스 표시 (이동만) / `bIsFocusable=false`
- **SetVisibility 매트릭스** 🟢: `Visible↔Collapsed` (Visibility + Layout, 부모 재배치) / `Visible↔Hidden` (Paint만) / `Visible↔HitTestInvisible` (낮음)
- 🟢 대안: 짧은 토글 → Hidden / 영구 숨김 → Collapsed / 페이드 → `SetRenderOpacity(0)` (Paint만)
- 🟡 ZOrder vs LayerId 혼동 — 다른 개념 (자세히 [[sources/ue-slatecore-drawing]] §5.1)

### 2.8 데이터 바인딩 TAttribute lambda (raw §2.8) 🟢

- 🟡 TAttribute lambda 매 프레임 호출 — 결과 변경 시 SWidget setter 자동 invalidate
- 🟢 회피 3 패턴: 결과 캐시 + 단순 조회 / `TSlateAttribute<T, reason>` (값 변경 시만 invalidate) / 직접 SetXxx 호출

## 3. 핵심 회피 패턴 종합 (raw §2 횡단)

| 패턴 | 적용 | tier |
|------|------|------|
| 위젯 풀링 + Visibility 토글 (생성/제거 회피) | ListView / VerticalBox 채팅 | 🟢 |
| `IUserListEntry::OnListItemObjectSet` (위젯 재사용) | ListView 표준 | 🟢 |
| `TSlateAttribute<T, reason>` (TAttribute 대체) | 자주 갱신되는 속성 | 🟢 |
| `SetRenderTransform` (Layout 변경 X) | 드래그/이동 매 프레임 | 🟢 |
| `SetRenderOpacity(0)` (Paint만) | 페이드 (SetVisibility 대신) | 🟢 |
| `UInvalidationBox` 정적 자식 트리 | 메뉴 배경 / 인벤토리 | 🟢 |
| 자동 휘발성 위젯 (Throbber/Animation) InvalidationBox 외부 배치 | 로딩 화면 | 🟢 |
| NativePaint override 회피 (표준 UMG 조합 우선) | 게이지/차트/미니맵 | 🟢 |

## 4. Cross-link

- 부모: [[sources/ue-ref-06-invalidationhotspots]] · [[concepts/Slate-Invalidation]] · [[concepts/Slate-Paint-Cycle]]
- 페어: [[sources/ue-umg-invalidationdeep]] · [[sources/ue-slatecore-drawing]] §5
- UMG: [[sources/ue-umg-uuserwidget]] §5.4 (NativePaint 함정) · [[sources/ue-umg-listwidgets]]
- SlateCore: [[sources/ue-slatecore-swidget]] · [[sources/ue-slatecore-input]]
- 정책: [[concepts/UMG-Super-Call-Convention]] · [[sources/ue-ref-07-profilingscopeRule]]

## 5. 신뢰도 + 변경 이력

| 항목 | tier | 출처 |
|------|------|------|
| 위젯 카테고리 8종 핫스팟 | 🟢 verified | raw §2.1~§2.8 + Engine source |
| Layout vs Paint vs Visibility reason 분류 | 🟢 verified | `EInvalidateWidgetReason` |
| 회피 패턴 8 매트릭스 | 🟢 verified | raw + 실측 |
| TAttribute lambda 동작 | 🟡 inferred | UE 5.x 변경 빈번 |
| ZOrder vs LayerId 분리 | 🟢 verified | SlateCore Drawing |
| `IUserListEntry::OnListItemObjectSet` | 🟢 verified | UMG ListView |

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | 06_InvalidationHotspots §2 분리 |
| 2026-05-15 | Cycle 5f #1 — stub 카드 → enrich 카드 (8 카테고리 매트릭스 + 회피 8 패턴 + 3-tier marker + Cross-link 7건) |
