---
type: source
title: "UE UMG — UUserWidget sub-skill"
slug: ue-umg-uuserwidget
source_path: raw/ue-wiki-llm/skills/UMG/references/UUserWidget.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UUserWidget]]"
related_concepts:
  - "[[concepts/UMG-Super-Call-Convention]]"
tags: [ue, umg, ui]
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE UMG — UUserWidget sub-skill

> Source: [[raw/ue-wiki-llm/skills/UMG/references/UUserWidget.md]]
> Parent: [[sources/ue-umg-skill]]

## 1. Summary

[[entities/UUserWidget]] 디테일 — PreConstruct (디자이너) + Construct + Destruct + NativeConstruct + NativeDestruct + Tick + InvalidateLayoutAndVolatility.

## 2. Key claims

- 라이프사이클: NativePreConstruct (Editor preview / 디자이너) → NativeConstruct (런타임) → NativeTick → NativeDestruct.
- BP 페어: PreConstruct / Construct / Tick / Destruct event.
- [[concepts/UMG-Super-Call-Convention]] 의무: NativeConstruct → Super FIRST, NativeDestruct → Super LAST.
- 깊이 자료: [[sources/ue-umg-invalidationdeep]] — Native* 가상 함수 30+ + 5 핵심 원칙.
- InvalidateLayoutAndVolatility: 명시적 invalidate — Slate 가 layout 재계산.
- BindWidget specifier: `UPROPERTY(meta=(BindWidget))` — BP 디자이너 위젯 ↔ C++ 멤버 명시 바인딩.
-
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 6
- 추가 (5.5.4 에만): 13
- 제거 (5.7.4 에만, 5.5.4 에 없음): 0
- 수치 변경: 0

**주요 시그니처**:
- `| `Blueprint/UserWidget.h` | `enum class EWidgetAnimationEvent : uint8` (Started → | `Blueprint/UserWidget.h` | `class UUserWidget : public UWidget, public INamedS`
- `| `bool bIsInputActionBlocking` (L1039) | UserWidget.h | 입력 액션 차단. | → | `EWidgetTickFrequency TickFrequency` | UserWidget.h L1649 (5.5) | 기본 `Auto` — `
- `HUD->AddToPlayerScreen(/*ZOrder=*/10);                                    // L35 → HUD->AddToViewport(/*ZOrder=*/0);                                         // L33`
- `// HUD->RemoveFromViewport();                                             // L36 → // HUD->RemoveFromViewport();                                             // L35`

**5.5.4 에만 (5.7.4 에 없음)**:
- `| `Blueprint/UserWidget.h` | `enum class EWidgetTickFrequency : uint8` (L108, UE 5.5) | **Never** (절대 tick 안 함) / **Auto`
- `| `Blueprint/UserWidget.h` | `enum class EWidgetAnimationEvent : uint8` (Started/Finished, L123) | UWidgetAnimation 시작/종`
- `| `FLinearColor ColorAndOpacity` (L957, 5.5) | UserWidget.h | 위젯 트리 전체 색·투명도. (UPROPERTY Getter/Setter L956) |`
- `| `FSlateColor ForegroundColor` (L968, 5.5) | UserWidget.h | 텍스트·아이콘 등 forecolor. |`

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/UMG/references/UUserWidget.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/UMG/references/UUserWidget.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **0 변경**
- 정합 후 tier: **🟢 pass-body-no-direct-cite**
