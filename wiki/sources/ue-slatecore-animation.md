---
type: source
title: "UE SlateCore — Animation sub-skill"
slug: ue-slatecore-animation
source_path: raw/ue-wiki-llm/skills/SlateCore/references/Animation.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, slate, ui]
last_updated: 2026-05-28
audit_5_5_4: raw  # 2026-05-28 Phase 2-B (regression-fix)
---

# UE SlateCore — Animation sub-skill

> Source: [[raw/ue-wiki-llm/skills/SlateCore/references/Animation.md]]
> Parent: [[sources/ue-slatecore-skill]]

## 1. Summary

FCurveSequence + FCurveHandle + Interpolation + Sequencer + ActiveTimer.

## 2. Key claims

- FCurveSequence::AddCurve(StartTime, Duration, EaseFunc) → FCurveHandle.
- FCurveHandle::GetLerp() — interpolated 0~1 value. ColorAndOpacity / RenderTransform attribute source.
- Interpolation 함수: ECurveEaseFunction (Linear / QuadIn / QuadOut / QuadInOut / CubicIn / etc).
- Sequencer 통합: USlateAnimationSequence (Editor 의 sequencer 자산 — 5.x 일부).
- ActiveTimer: SWidget::RegisterActiveTimer — 매 frame callback. EActiveTimerReturnType (Continue / Stop).
- 사용처: 메뉴 슬라이드 인 / fade out / 강조 펄스.
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
