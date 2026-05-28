---
type: entity
title: "USoundBase"
aliases: [USoundBase, USoundCue, USoundWave]
kind: model
sources:
  - "[[sources/ue-assetclasses-skill]]"
tags: [ue, asset, audio]
last_updated: 2026-05-09
---

# USoundBase / USoundCue / USoundWave

## 요약

USoundBase (418 lines) 베이스 + USoundCue (379, 노드 그래프 — 분기/랜덤/감쇠) + USoundWave (1,822, 실제 PCM 데이터). USoundClass / USoundConcurrency / USoundMix / USoundAttenuation 으로 그룹/제한/효과/공간 음향. 5.x MetaSounds 가 SoundCue 의 후속.

## 관계

- 부모: [[entities/UObject]]
- 자손: USoundCue / USoundWave + 5.x UMetaSoundSource
- 협력 자산: USoundClass (그룹), USoundConcurrency (동시 재생 제한), USoundMix (효과 셋), USoundAttenuation (감쇠 / 공간)
- 페어 호스트: UAudioComponent

## 핵심 주장

- SoundCue: 노드 그래프 — Random / Concatenator / Doppler / Modulator / Looping. Editor 에서 합성. Component 가 SoundCue 또는 SoundWave 직접 재생.
- SoundWave: 압축된 PCM 데이터 — Vorbis / Opus / ADPCM (platform 별). BulkData. 5.x 에서 Streaming SoundWave 지원.
- Concurrency: ResolutionRule 5 종 — PreventNew / StopOldest / StopFarthest / StopLowestPriority / StopQuietest. 동시 재생 수 제한 — 다수 NPC 환경 표준.
- Attenuation: 거리 / 방향 / Spatial / Air absorption. Spatial Method (Linear/Custom/Natural Sound).
- 5.x MetaSounds: SoundCue 의 후속 — 더 강력한 그래프 + audio-rate parameters + 동적 인스턴싱. 기존 SoundCue 호환.

## 열린 질문

- [ ] MetaSounds 와 SoundCue 의 마이그레이션 경로
- [ ] Concurrency 의 다수 NPC 환경에서 [[concepts/Asset-Optimization-Policy]] 통합
