---
type: synthesis
title: "UE 5.7.4 — Custom Slate Widget OnPaint Layer 전략 (Content + Overlay + Cursor 3계 분리)"
slug: ue-slate-custom-onpaint-layer-strategy
created: 2026-05-19
last_updated: 2026-05-19
project_role: general-pattern
project: vault-general
measured_date: 2026-05-19
status: living
cycle: 5p+6
tier: enriched
sources:
  - "[[sources/ue-slatecore-drawing]]"
  - "[[sources/ue-slatecore-swidget]]"
  - "[[sources/ue-slatecore-clipping]]"
  - "[[synthesis/timeline-custom-slate-widget-pattern]]"
  - "[[synthesis/mc-combo-editor-levelsequence-lite]]"
entities:
  - "[[entities/SWidget]]"
  - "[[entities/FSlateDrawElement]]"
concepts:
  - "[[concepts/Slate-Paint-Cycle]]"
tags: [synthesis, ue-general, slate, custom-widget, onpaint, layer-strategy, z-order, ruler-overlay, scroll-overlay-cursor-3tier, kmcproject-case-study]
citation_disclosure: "🟢 8+ (KMCProject Cycle 5p+6 실측 + Engine FSlateDrawElement LayerId z-sort + SSequencer 권위 미러)"
---

# UE 5.7.4 — Custom Slate Widget OnPaint Layer 전략 (3계 분리)

> **목적**: Custom Slate widget 의 OnPaint 안 다층 element (배경 / 콘텐츠 / 오버레이 / 커서) 의 LayerId 할당 전략을 일반화. vertical/horizontal scroll 시 오버레이 가림 (occlusion) 회피 + 커서 가림 회피.
>
> **사용처**: Timeline / curve editor / canvas / graph editor 등 OnPaint 직접 호출하는 모든 custom widget 안 *fixed overlay* (헤더 / ruler / status bar) + *cursor* (scrub head / playhead / cursor crosshair) 분리 필요한 사례.

## 1. 문제 — Single-Layer Paint 시 Scroll Occlusion

Slate `FSlateDrawElement::Make*` 호출은 `LayerId` 기반 z-sort. 동일 LayerId 안에서는 호출 순서가 paint 순서. **문제**: Custom OnPaint 가 배경 / 콘텐츠 / 헤더 모두 `LayerId+0` 에 paint 시:

- Vertical scroll 적용 → 콘텐츠 Y 가 위로 shift → 헤더/ruler 영역 (Y < HeaderHeight) 위로 흘러나감
- Paint 호출 순서: 배경 → ruler → 콘텐츠 → ...
- 같은 LayerId 안 콘텐츠가 ruler **위에** paint (호출 순서 = z-order)
- **결과**: ruler 가림 (occlusion) — 사용자 시각 혼란

→ KMCProject Cycle 5p+6 사용자 image 보고 (vertical scroll 시 sub-row Section box 가 ruler 위로 paint).

## 2. 해결 — 3계 Layer 분리

**전략**: OnPaint 안 LayerId 범위를 3계 (또는 4계) 으로 명시 분리. 각 계층은 z-order 정확히 정의:

```
┌──────────────────────────────────────────────────────────┐
│  Cursor   (L_max)        — Scrub head / Playhead / Mouse │  ← 모든 위
├──────────────────────────────────────────────────────────┤
│  Overlay  (L_overlay)    — Ruler / Header / Status bar   │  ← 콘텐츠 위, 커서 아래
├──────────────────────────────────────────────────────────┤
│  Content  (L_0..L_C-1)   — Rows / Section boxes / Labels │  ← 자유롭게 다층 사용
└──────────────────────────────────────────────────────────┘
```

**LayerId 매트릭스** (예시 — KMCProject Cycle 5p+6 사례, 12-Layer 전략):

| Layer | 용도 | 가림 회피 의무 |
| -- | -- | -- |
| L0 | 배경 + zebra striping + 행 배경 | (가림 회피 대상 아님) |
| L1 | Section 본체 + Hatched + 보더 | 콘텐츠 base |
| L2 | Easing 그라디언트 | 본체 위 |
| L3 | Reverse 화살표 | 본체 위 |
| L4 | Weight bar | 본체 위 |
| L5 | DisplayName / SlotName 라벨 | 본체 위 |
| L6 | PlayRate × 배수 + Keyframe circle body | 라벨 위 |
| L7 | Keyframe circle outline | body 위 |
| L8 | Lock + dim 알파 | 모든 콘텐츠 위 (cursor 효과 미러) |
| L9 | 선택 테두리 | 콘텐츠 최상위 |
| **L10** | **Ruler + tick + tick label (overlay)** | **scroll 시 콘텐츠가 위로 흘러나가도 항상 visible** |
| **L11** | **Scrub head (cursor)** | **Ruler 안에서도 visible** |

## 3. 패턴 코드

```cpp
int32 SMyCustomWidget::OnPaint(const FPaintArgs& Args,
                              const FGeometry& AllottedGeometry,
                              const FSlateRect& MyCullingRect,
                              FSlateWindowElementList& OutDrawElements,
                              int32 LayerId,
                              const FWidgetStyle& InWidgetStyle,
                              bool bParentEnabled) const
{
    // L0..L_C-1: 콘텐츠 paint (배경 / 행 / Section box / 라벨 / 키프레임 등)
    PaintContent(OutDrawElements, LayerId, AllottedGeometry, ...);

    // L_overlay (L10): 오버레이 — vertical scroll 무관 항상 최상위
    PaintRulerOverlay(OutDrawElements, LayerId + 10, AllottedGeometry, ...);

    // L_cursor (L_max = L11): 커서 — 오버레이 위 (ruler 안에서도 visible)
    PaintScrubCursor(OutDrawElements, LayerId + 11, AllottedGeometry, ...);

    return LayerId + 12;  // 호출자에게 사용 layer 범위 알림
}
```

⭐ **return 값** — 호출자 widget 이 자식 paint 후 다음 layer 부터 paint 가능하도록 정확 값 반환. 자식 widget chaining 시 layer 충돌 회피.

## 4. Engine 권위 참조

| API / 패턴 | 위치 | 인용 |
| -- | -- | -- |
| `FSlateDrawElement::Make*(OutDrawElements, LayerId, ...)` | `SlateCore/Public/Rendering/DrawElements.h` | LayerId 첫 매개변수 — z-sort 키 |
| `FSlateWindowElementList` z-sort | `SlateCore/Private/Rendering/SlateRenderer.cpp` | LayerId asc 정렬 후 batch paint |
| `SWidget::OnPaint` virtual | `SlateCore/Public/Widgets/SWidget.h` | `int32` return — 사용 layer 최대값 + 1 |
| `SSequencer` overlay strategy | `Sequencer/Private/SSequencer.cpp` | 비슷한 ruler + scrub 3계 분리 (실제 코드 확인) |
| `SCurveEditorPanel` | `CurveEditor/Private/SCurveEditorPanel.cpp` | curve + handle + grid 다층 paint 표준 |

## 5. 결정 트리 — 언제 3계 분리 vs 단일 layer?

| 시나리오 | 권장 | 이유 |
| -- | -- | -- |
| 단순 list widget (모든 element 같은 z) | 단일 layer | overhead 없음, sort 비용 절감 |
| Static panel (scroll 없음) | 단일 layer | occlusion risk 없음 |
| **Scroll + 헤더 / ruler / status bar** | **2계 분리 (content L0..L_C-1 + overlay L_C)** | 헤더 가림 회피 |
| **Scroll + cursor (playhead / scrub head)** | **3계 분리 (+ cursor L_C+1)** | 헤더 안에서도 cursor visible |
| **Drag handles + tooltip overlay** | **4계 (+ tooltip L_C+2)** | tooltip 가림 회피 |
| Multiple overlapping content tracks | content layer 안에서 z-stagger (L0, L1, L2...) | 내부 z-order 유지 |

## 6. SSequencer / SCurveEditor 표준 비교

**SSequencer** (Engine `Sequencer/Private/SSequencer.cpp`):
- Tree (Outliner) widget — 별도 SWidget (SSplitter slot)
- Track area — SSequencerTrackArea SWidget
- Ruler — overlay 안 별도 SWidget (SSequencerTimeSlider)
- → SWidget 분리 아키텍처 (각 SWidget 자체 LayerId 관리)

**lite 미러** (KMCProject Cycle 5p+6):
- 단일 SMCComboTrackArea SWidget 안 OnPaint 으로 ruler + content + scrub 모두 그리기
- 3계 분리 LayerId 매트릭스 으로 동등 z-order 보장
- → SWidget 1개로 구현 simplicity + Sequencer 풀스택 의존 회피

⚠ **trade-off**: SWidget 분리 시 Slate framework 가 자동 hit-test / cursor / focus 분배. 단일 SWidget 안 OnPaint 으로 합치면 hit-test / cursor 도 자체 분기 의무 (예: `Y < RulerHeight` 분기로 Scrub 트리거).

## 7. Clipping (EWidgetClipping) 와의 조합

3계 분리 만으로 z-order 보장 충분 — `EWidgetClipping::ClipToBounds` 와 직교.

**조합 시너지**:
- 3계 Layer → 자식 paint 우선순위 (overlay always on top)
- ClipToBounds → widget 영역 외 paint 자동 mask (sibling widget 영역 침범 방지)
- 함께 사용 시 visual 정합성 완성

→ [[sources/ue-slatecore-clipping]] §6 KMCProject 실측 사례 페어.

## 8. 함정 카탈로그

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | Single-layer paint — scroll 시 콘텐츠가 헤더/ruler 가림 | 3계 분리 (content L0..L_C-1 + overlay L_C + cursor L_C+1) |
| 2 | LayerId 매트릭스 미문서화 — 추후 변경자가 layer 충돌 발생 | OnPaint 상단 주석에 layer-by-layer 매트릭스 명시 |
| 3 | `return LayerId + N` 잘못 — 자식 widget chain 시 layer 충돌 | 사용한 최대 layer + 1 정확 반환 (예: scrub at L11 → return L12) |
| 4 | Overlay paint 호출 순서 무시 — 같은 layer 안 호출 순서가 paint 순서 | overlay 안에서도 z-stagger 필요 시 sub-layer 분리 (L_overlay + L_overlay+0.5 등 불가, 정수 layer 분리 의무) |
| 5 | 그림자 / Hover / focus border 분리 누락 | hover/focus border 는 L_overlay 직전 (L_C+0.9 ≈ L9) 권장 — overlay 아래 (overlay 가 가림) 또는 위 (overlay 가 가려짐) 결정 |
| 6 | Cursor (scrub head) 가 Overlay 아래 paint — ruler 안 cursor 사라짐 | Cursor 를 가장 높은 layer 에 paint (L_C+1) |
| 7 | OnPaint 안 sub-widget OnPaint 호출 시 LayerId 전달 잘못 | `int32 NewLayerId = ChildWidget->OnPaint(..., LayerId + 5, ...);` 으로 자식 layer 범위 명시 |

## 9. KMCProject 적용 사례 (Cycle 5p+6)

- **이전**: ruler L0 + scrub L9 + content L0..L9 → vertical scroll 시 sub-row Section box (L1) + Diamond (L6/L7) 이 ruler 영역 (Y<22) 위로 paint 흘러나감 → ruler 가림
- **현재**: ruler **L10** (콘텐츠 위) + scrub **L11** (ruler 위) + content L0..L9 → 3계 분리 완성
- `SMCComboTrackArea::OnPaint` 4 paint call LayerId 격상 (ruler background + tick line + tick label + scrub head)
- `return LayerId + 12` (이전 +10)
- Layer 주석 매트릭스 12-Layer 갱신

→ 상세: [[synthesis/mc-combo-editor-levelsequence-lite]] §5.12.1

## 10. Cross-link

- [[sources/ue-slatecore-drawing]] — FSlateDrawElement / OnPaint cycle
- [[sources/ue-slatecore-clipping]] — EWidgetClipping 페어 (Cycle 5p+5)
- [[sources/ue-slatecore-swidget]] — SWidget OnPaint virtual
- [[synthesis/timeline-custom-slate-widget-pattern]] §3 (OnPaint 9-Layer — 본 패턴의 content 부분 case study)
- [[synthesis/mc-combo-editor-levelsequence-lite]] §5.12.1 (Cycle 5p+6 KMCProject 적용)
- [[synthesis/ue-paint-hittest-shared-rowmap]] (paint + hit-test 정합성 페어)

## 11. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-19 (Cycle 5p+6) | 최초 작성 — Custom Slate Widget OnPaint Layer 3계 분리 전략 일반화. KMCProject Cycle 5p+6 실측 사례 (ruler L0→L10 격상 + scrub L9→L11 + content L0..L9). 12-Layer 매트릭스 예시 (Sequencer Section paint) + 결정 트리 (단일 vs 2계 vs 3계 vs 4계) + Engine 권위 (FSlateDrawElement LayerId z-sort / SSequencer ruler+scrub 분리) + Clipping 페어 + 7 함정 카탈로그. |
