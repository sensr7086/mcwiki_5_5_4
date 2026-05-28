---
type: source
title: "UE Components — SpecialComponents sub-skill"
slug: ue-components-specialcomponents
source_path: raw/ue-wiki-llm/skills/Components/references/SpecialComponents.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_concepts:
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, components]
---

# UE Components — SpecialComponents sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/SpecialComponents.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

특수 용도 컴포넌트 — USplineComponent (path) + USplineMeshComponent (Spline 따라 mesh 변형) + UTimelineComponent (시간 곡선 애니메이션) + UStereoLayerComponent (VR overlay).

## 2. Key claims

- USplineComponent: 3D path. AddSplinePoint / GetLocationAtSplinePoint / GetTangentAtSplinePoint. AI patrol / 로프 / 트랙.
- USplineMeshComponent: Static Mesh 를 Spline 의 시작 ~ 끝 사이로 deform. SetStartAndEnd. 도로 / 케이블 / 강.
- UTimelineComponent: float / vector / linear color 의 시간 기반 곡선. PlayFromStart / Reverse / SetPlayRate. 페이드 / 펄스 / 카메라 dolly.
- UStereoLayerComponent (VR): VR HMD 의 별도 layer (해상도 보존). HUD / 메뉴 / 자막.
- 6 대 정책 자동 적용. Mobility 보통 Movable.

## 3. Open questions

- [ ] Spline 의 path follow 표준 패턴 (AI / 카메라)
- [ ] StereoLayer 의 OpenXR 통합
