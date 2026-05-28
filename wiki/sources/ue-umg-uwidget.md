---
type: source
title: "UE UMG — UWidget sub-skill"
slug: ue-umg-uwidget
source_path: raw/ue-wiki-llm/skills/UMG/references/UWidget.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UWidget]]"
related_concepts:
  - "[[concepts/Slate-Invalidation]]"
tags: [ue, umg, ui]
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE UMG — UWidget sub-skill

> Source: [[raw/ue-wiki-llm/skills/UMG/references/UWidget.md]]
> Parent: [[sources/ue-umg-skill]]

## 1. Summary

[[entities/UWidget]] 베이스 — RebuildWidget + SynchronizeProperties + ReleaseSlateResources + Visibility + IsVisible + GetCachedWidget.

## 2. Key claims

- RebuildWidget(): SWidget 트리 재생성. Editor 측 Construction 또는 런타임 첫 표시 시.
- SynchronizeProperties(): UWidget 속성 → SWidget 동기화. UPROPERTY 변경 후 호출.
- ReleaseSlateResources(bool): SWidget 참조 해제 — Destruct 시 호출.
- Visibility (ESlateVisibility 5 종): Visible / Collapsed / Hidden / HitTestInvisible / SelfHitTestInvisible.
- IsVisible(): Visible 또는 HitTestInvisible 만 true.
- GetCachedWidget(): 내부 TSharedPtr<SWidget> 접근. RebuildWidget 후만 valid.
- TakeWidget(): SWidget 반환 (필요 시 RebuildWidget 호출).
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 5
- 추가 (5.5.4 에만): 4
- 제거 (5.7.4 에만, 5.5.4 에 없음): 0
- 수치 변경: 0

**주요 시그니처**:
- `| `Public/Components/Widget.h` | `class UWidget : public UVisual, public INotify → | `Public/Components/Widget.h` | `class UWidget : public UVisual, public INotify`
- `| `UPROPERTY FText ToolTipText` (L297) | Widget.h | 툴팁 — Setter `SetToolTipText` → | `UPROPERTY TObjectPtr<UPanelSlot> Slot` | Widget.h L263 (5.5) | 부모 패널의 자식 배치 메`
- `| `UPROPERTY FWidgetTransform RenderTransform` (L297) | Widget.h | 렌더 변환 — Sette → | `UPROPERTY FWidgetTransform RenderTransform` (L297, 5.5) | Widget.h | 렌더 변환 — `
- `| `UPROPERTY ESlateVisibility Visibility` (L439) | Widget.h | 가시성 — Setter `SetV → | `UPROPERTY ESlateVisibility Visibility` (L434, 5.5) | Widget.h | 가시성 — Setter `

**5.5.4 에만 (5.7.4 에 없음)**:
- `| `UPROPERTY FText ToolTipText` (L276, 5.5) | Widget.h | 툴팁 — Setter `SetToolTipText` (L550, 5.5) + `FieldNotify` (Field`
- `| `uint8 bIsVolatile:1` | Widget.h L387 (5.5) | 휘발성 (캐시 비활성). `ForceVolatile` 으로 토글. |`
- ``
- `> ⚠ **UE 5.5 line 번호 주의**: 아래 코드 주석의 `// L###` setter line 번호는 UE 5.7.4 기준으로 기록된 값 — UE 5.5.4 에서는 함수 정의 위치가 평균 ~5~30 라인 `

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/UMG/references/UWidget.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/UMG/references/UWidget.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **0 변경**
- 정합 후 tier: **🟢 pass-body-no-direct-cite**
