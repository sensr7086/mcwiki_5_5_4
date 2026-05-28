---
type: source
title: "UE AssetClasses — Camera sub-skill"
slug: ue-assetclasses-camera
source_path: raw/ue-wiki-llm/skills/AssetClasses/references/Camera.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
tags: [ue, asset, camera]
---

# UE AssetClasses — Camera sub-skill

> Source: [[raw/ue-wiki-llm/skills/AssetClasses/references/Camera.md]]
> Parent: [[sources/ue-assetclasses-skill]]

## 1. Summary

UCameraShakeBase + UCameraShakePattern 4 종 (Wave / Perlin / Sequence / Custom) + UCameraModifier + 5.x UCameraAnimationSequence.

## 2. Key claims

- UCameraShakeBase: 흔들림 자산 베이스. PlayCameraShake (PlayerCameraManager) 또는 Component 측 발화.
- UCameraShakePattern 4 종:
  - Wave: 단순 sin 진동 (TimingFunction).
  - Perlin: 비주기 noise (자연스러운 흔들림).
  - Sequence: 명시적 키프레임 (디자이너 곡선).
  - Custom: 사용자 정의 (override).
- UCameraModifier: PostProcess + 위치 / 회전 modifier. PlayerCameraManager 의 ModifierList.
- 5.x UCameraAnimationSequence: Sequencer 의 카메라 애니메이션 자산 — SequenceCameraShakePattern 의 입력.
- UCameraShakeSourceComponent: shake 발화 위치 + Attenuation (거리 약화).

## 3. Open questions

- [ ] Wave vs Perlin 결정 트리 (어떤 효과에 어느)
