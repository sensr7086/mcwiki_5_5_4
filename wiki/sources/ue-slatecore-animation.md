---
type: source
title: "UE SlateCore — Animation sub-skill"
slug: ue-slatecore-animation
source_path: raw/ue-wiki-llm/skills/SlateCore/references/Animation.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, slate, ui]
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
