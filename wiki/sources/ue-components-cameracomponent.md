---
type: source
title: "UE Components — CameraComponent sub-skill"
slug: ue-components-cameracomponent
source_path: raw/ue-wiki-llm/skills/Components/references/CameraComponent.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_concepts:
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, components, camera]
---

# UE Components — CameraComponent sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/CameraComponent.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

카메라 컴포넌트 — UCameraComponent + UCineCameraComponent (5.x cinematic) + UCameraShakeSourceComponent. PostProcessSettings + ProjectionMode + FieldOfView + AspectRatio.

## 2. Key claims

- UCameraComponent: 일반 카메라. FieldOfView (FOV) + AspectRatio + PostProcessSettings + ProjectionMode (Perspective / Orthographic).
- UCineCameraComponent (5.x): cinematic 카메라 — Filmback (35mm/65mm) + LensSettings (focal length) + FocusSettings (depth of field). Sequencer 통합.
- UCameraShakeSourceComponent: shake 발화 위치. Attenuation 으로 거리 기반 약화.
- PostProcessSettings: PostProcess Material 추가 (Domain=PostProcess) + 이펙트 (Vignette / Chromatic / Bloom 등).
- bConstrainAspectRatio: 화면 비율 강제 (시네마틱).
- TickGroup: PostUpdateWork (가장 늦게, 모든 위치 결정 후).

## 3. Open questions

- [ ] CineCamera 의 Sequencer 통합 표준
- [ ] PlayerCameraManager 와 CameraComponent 의 책임 분담
