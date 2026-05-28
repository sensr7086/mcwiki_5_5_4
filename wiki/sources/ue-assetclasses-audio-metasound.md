---
type: source
title: "UE AssetClasses Audio — MetaSound (5.x) deep"
slug: ue-assetclasses-audio-metasound
source_path: raw/ue-wiki-llm/skills/AssetClasses/references/Audio/Metasound.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
related_entities:
  - "[[entities/USoundBase]]"
tags: [ue, asset, audio]
---

# UE AssetClasses Audio — MetaSound (5.x deep)

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/references/Audio/Metasound.md]]
> Parent: [[sources/ue-assetclasses-audio]]

## 1. Summary

UE 5.x **MetaSound** — UMetaSoundSource + UMetaSoundPatch + Graph 노드 + Trigger/Audio/Wave 데이터 타입 + Parameter Pack 런타임 제어. Cascade-style USoundCue 대비 5.x DSP 그래프 표준. UAudioComponent 페어.

## 2. Key claims

- UMetaSoundSource: 실제 sound 자산 (USoundBase 자손) — UAudioComponent 가 재생.
- UMetaSoundPatch: 재사용 가능한 sub-graph (function 처럼).
- 데이터 타입 3 종: Trigger (이벤트) / Audio (audio-rate float) / Wave (USoundWave 참조).
- Graph 노드: Generators (Sine / Triangle / Noise) / Filters / Mixers / Math / Samplers.
- Parameter Pack: 런타임에 외부에서 그래프 파라미터 변경 (UAudioComponent::SetFloatParameter 등).
- vs USoundCue: 더 강력한 DSP + audio-rate parameters + 동적 인스턴싱. SoundCue 는 호환만.
- IAudioParameterControllerInterface — 5.x 표준 인터페이스.
