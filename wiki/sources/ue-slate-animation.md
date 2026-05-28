---
type: source
title: "UE Slate — Animation sub-skill"
slug: ue-slate-animation
source_path: raw/ue-wiki-llm/skills/Slate/references/Animation.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, slate, ui]
---

# UE Slate — Animation sub-skill

> Source: [[raw/ue-wiki-llm/skills/Slate/references/Animation.md]]
> Parent: [[sources/ue-slate-skill]]

## 1. Summary

SBorder + SCurveHandle + 슬레이트 애니메이션 — FCurveSequence 통합.

## 2. Key claims

- FCurveSequence: 시간 기반 곡선 컨테이너. AddCurve(StartTime, Duration, EaseFunc) → FCurveHandle 반환.
- FCurveHandle::GetLerp(): 0~1 interpolated value. ColorAndOpacity / RenderTransform attribute 의 source.
- SBorder + RenderTransform: ScaleBy / Translate / Rotate — 이펙트 (등장 / 강조).
- ActiveTimer: SWidget 의 RegisterActiveTimer — 매 frame callback 으로 애니메이션 update.
- 게임 UMG 보다 가볍지만 declarative 가 아닌 imperative — 복잡한 애니메이션은 UMG Animation (Sequencer) 권장.
