---
type: source
title: "UE Slate/UMG Specialist — Slate + SlateCore + UMG 30 sub-skill 통합"
slug: ue-agent-slate-umg
source_path: raw/ue-wiki-llm/agents/ue-slate-umg-specialist.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-15
related_entities:
  - "[[entities/SWidget]]"
  - "[[entities/UWidget]]"
  - "[[entities/UUserWidget]]"
related_concepts:
  - "[[concepts/Slate-Invalidation]]"
  - "[[concepts/Slate-Paint-Cycle]]"
  - "[[concepts/UMG-Super-Call-Convention]]"
tags: [ue, agent, specialist, slate, umg, invalidation, super-call, enriched-card]
citation_disclosure: "🟢 raw verified · Cycle 5n Round 2 enrich"
---

# UE Slate/UMG Specialist

> Source: [[raw/ue-wiki-llm/agents/ue-slate-umg-specialist.md]]
> Parent: [[sources/ue-agent-orchestrator]] — `[Slate]` / `[UMG]` / `[SlateCore]` prefix 호출
> Cycle 5n Round 2 — stub → 정밀 enrich

## 1. Summary

🟢 Slate / SlateCore / UMG 통합 전문가 — SWidget + Slate 인하우스 툴 (Docking/Menu/Commands/GraphEditor) + UMG 위젯 (UWidget / UUserWidget / UButton 등) **30 sub-skill**. 인밸리데이션 / Super 호출 규약 / NativeOnPaint 함정 / TickFrequency 자동 적용.

## 2. 자동 로드 (6 파일)

1. `skills/SlateCore/SKILL.md` (10 sub-skill)
2. `skills/Slate/SKILL.md` (12 sub-skill — 인하우스 툴 묶음)
3. `skills/UMG/SKILL.md` (7 sub-skill)
4. [[sources/ue-ref-04-overrideindex]] (Super 호출 통합 표)
5. [[sources/ue-ref-06-invalidationhotspots]] (인밸리데이션 회피)
6. [[sources/ue-ref-07-profilingscopeRule]]

## 3. 결정 트리

```
UI 작성?
├── 게임 런타임 UI / 디자이너 협업       → UMG (UUserWidget)
├── 에디터 툴 / 정적 / 고성능            → Slate (SWidget)
├── 도킹/메뉴/단축키/노드 그래프 (인하우스) → Slate 인하우스 툴 묶음
└── 둘 섞임                              → UMG 안에 SWidget 호스팅
```

## 4. Super 호출 규약 (UMG — 04_OverrideIndex §6)

| 함수 | Super 위치 | 위반 증상 |
|------|-----------|----------|
| `NativeOnInitialized` | **FIRST** | InputComponent 미생성 |
| `NativePreConstruct` | **FIRST** | DesiredFocusWidget 미해석 |
| `NativeConstruct` | **FIRST** | InputScriptDelegates 미시작 |
| `NativeDestruct` | **LAST** | Extension Destruct 순서 깨짐 |
| `NativeTick` | **FIRST** | TickActionsAndAnimation 정지 |

## 5. 인밸리데이션 5대 원칙 (06_InvalidationHotspots §8)

1. **TickFrequency = Never** 우선 (정적 위젯)
2. **NativeOnPaint 마지막 수단** — override 시 LayerId 단조 증가 + Super 반환값 사용
3. **UInvalidationBox** 안에 정적 영역만 (휘발성 X)
4. **표준 setter 사용** — `SetText` / `SetVisibility` (자동 인밸리데이션)
5. **ZOrder ≠ LayerId** 혼동 금지

## 6. NativeOnPaint 표준

```cpp
virtual int32 NativePaint(const FPaintArgs& Args, ...) const override {
    int32 NewLayer = Super::NativePaint(Args, ...);   // ✅ Super 반환값 사용
    FSlateDrawElement::MakeBox(Out, NewLayer + 1, ...); // ✅ LayerId +1
    return NewLayer + 2;   // ✅ 단조 증가
}
```

## 7. 인하우스 툴 4단 방어 (Slate 카테고리)

→ Slate §8 런타임/에디터 분리:
1. 모듈 분리 (Runtime / Editor 두 모듈)
2. uplugin Type 명시 (`Type=Editor`)
3. Build.cs 분기 (`bBuildDeveloperTools=true`)
4. `#if WITH_EDITOR` 가드

## 8. Baseline Grep 의무

함정 키워드: `SWidget` / `Invalidate` / `RebuildWidget` / `NativePaint` / `TAttribute` / `TSlateAttribute` / `FSlateDrawElement` / `UInvalidationBox` / `IUserListEntry::OnListItemObjectSet` / `FCurveSequence`.

## 9. 거부 조건

- Component / Actor — 다른 specialist
- Editor 도구 (도킹 / 메뉴 / 단축키 / 노드 그래프) — `ue-editor-specialist`

## 10. Cross-link

- 메타 agent: [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-evaluator]] · [[sources/ue-agent-audit]] · [[sources/ue-agent-wiki-maintainer]]
- 페어 specialist: [[sources/ue-agent-editor]] (Editor 도구 — Docking/Menu/Commands/GraphEditor) · [[sources/ue-agent-components]] (호스트 페어)
- sub-skill 주요: [[sources/ue-slate-skill]] · [[sources/ue-slatecore-skill]] · [[sources/ue-umg-skill]] · [[sources/ue-umg-uuserwidget]] · [[sources/ue-slatecore-swidget]] · [[sources/ue-slate-docking]] · [[sources/ue-slate-menu]] · [[sources/ue-slate-commands]] · [[sources/ue-slate-grapheditor]]
- 정책: [[sources/ue-ref-04-overrideindex]] · [[sources/ue-ref-06-invalidationhotspots]] · [[sources/ue-ref-deep-invalidationhotspots]] · [[sources/ue-ref-deep-overridetables]]
- 시스템: [[sources/ue-meta-baseline-grep-system]] §7

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | stub 카드 |
| 2026-05-15 (Cycle 5n Round 2) | ⭐⭐⭐ stub → 정밀 11 절. 30 sub-skill 통합 + 결정 트리 + Super 5종 + 인밸리데이션 5 원칙 + 4단 방어 |
