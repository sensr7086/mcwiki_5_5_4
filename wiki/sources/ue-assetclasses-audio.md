---
type: source
title: "UE AssetClasses — Audio sub-skill"
slug: ue-assetclasses-audio
source_path: raw/ue-wiki-llm/skills/AssetClasses/references/Audio.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
related_entities:
  - "[[entities/USoundBase]]"
related_concepts:
  - "[[concepts/Asset-Optimization-Policy]]"
tags: [ue, asset, audio]
---

# UE AssetClasses — Audio sub-skill

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/references/Audio.md]]
> Parent: [[sources/ue-assetclasses-skill]]

## 1. Summary

[[entities/USoundBase]] (418) + USoundCue (379) + USoundWave (1,822) + USoundClass + USoundConcurrency + USoundMix + USoundAttenuation + 5.x MetaSounds.

## 2. Sub-sub-skills

- [[sources/ue-assetclasses-audio-metasound]] — 5.x MetaSound deep (UMetaSoundSource + UMetaSoundPatch + DSP graph)

## 3. Key claims

- USoundBase: 베이스. USoundCue / USoundWave / UMetaSoundSource 의 부모.
- USoundCue: 노드 그래프 (Random / Concatenator / Doppler / Modulator).
- USoundWave: 압축 PCM. BulkData. 5.x Streaming SoundWave.
- USoundClass: 그룹 (Volume / Pitch).
- USoundConcurrency: ResolutionRule 5 종 — 다수 NPC 표준 ([[concepts/Asset-Optimization-Policy]] §4).
- USoundMix: 효과 셋 — 일시적 활성.
- USoundAttenuation: 거리 / 방향 / Spatial.
- 5.x MetaSounds: SoundCue 후속 — graph + audio-rate + 동적 인스턴싱.
