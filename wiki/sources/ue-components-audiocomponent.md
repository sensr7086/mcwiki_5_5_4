---
type: source
title: "UE Components — AudioComponent sub-skill"
slug: ue-components-audiocomponent
source_path: raw/ue-wiki-llm/skills/Components/references/AudioComponent.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/USoundBase]]"
related_concepts:
  - "[[concepts/Asset-Optimization-Policy]]"
tags: [ue, runtime, components, audio]
---

# UE Components — AudioComponent sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/AudioComponent.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

UAudioComponent 의 풀 디테일 — [[entities/USoundBase]] 호스트 + UForceFeedbackComponent (Gamepad rumble) + 5.x ISoundParameterController (MetaSounds 파라미터). USoundAttenuation (거리 감쇠) + USoundConcurrency (동시 재생 제한 — [[concepts/Asset-Optimization-Policy]] §4).

## 2. Key claims

- Play / Stop / SetActive — 기본 제어. bAutoActivate (Spawn 시 자동 재생).
- SetSound(USoundBase) — 동적 sound 변경. SetVolumeMultiplier / SetPitchMultiplier.
- SetParameterValue (5.x MetaSounds): float / int / bool / object 타입별 — `SetFloatParameter` / `SetBoolParameter`.
- USoundAttenuation: 거리 감쇠 + 공간 음향 (Linear / Custom / Natural Sound).
- USoundConcurrency: ResolutionRule 5종 (PreventNew / StopOldest / StopFarthest / StopLowestPriority / StopQuietest) — 다수 NPC 환경 표준.
- UForceFeedbackComponent: Gamepad rumble — UForceFeedbackEffect 자산 + IForceFeedbackInterface.
- 5.x MetaSounds: SoundCue 후속 — 그래프 + dynamic params.

## 3. Open questions

- [ ] MetaSounds 의 audio-rate parameter 패턴
- [ ] Concurrency 의 다수 NPC 5중 최적화 통합
