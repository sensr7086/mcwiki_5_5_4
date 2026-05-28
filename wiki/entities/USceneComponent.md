---
type: entity
title: "USceneComponent"
aliases: [USceneComponent, SceneComponent]
kind: model
sources:
  - "[[sources/ue-components-skill]]"
tags: [ue, runtime, components]
last_updated: 2026-05-09
---

# USceneComponent

## 요약

[[entities/UActorComponent]] 자손. **트랜스폼 보유** (RelativeLocation/Rotation/Scale + WorldTransform 캐싱). Attach 가능 → Component Hierarchy 형성. [[concepts/Mobility]] 속성 보유 (Static / Stationary / Movable). Sockets 지원.

## 관계

- 부모: [[entities/UActorComponent]]
- 자손: [[entities/UPrimitiveComponent]] (콜리전+렌더+물리), UCameraComponent, USpringArmComponent, UAudioComponent, USpotLightComponent, ...
- Attach 대상: 다른 USceneComponent (RootComponent 또는 부모 Component 의 Socket)

## 핵심 주장

- RootComponent = Actor 의 첫 USceneComponent. Actor 의 World Location 이 곧 RootComponent 의 World Transform. [[entities/AActor]]
- AttachToComponent 시 KeepRelative / KeepWorld / SnapToTarget 3 종 옵션. [[raw/ue-wiki-llm/skills/Components/SKILL.md]]
- [[concepts/Mobility]]: Static (런타임 변경 X / Light Baking O), Stationary (위치 고정 / Light 동적), Movable (모두 가능 / Light Baking X). 생성자에서 결정 — 런타임 SetMobility 금지. [[raw/ue-wiki-llm/references/10_ComponentPolicies.md]]
- WorldTransform 은 캐싱됨 — Attach Hierarchy 갱신 시 자동 dirty. SetRelativeLocation / SetWorldLocation 으로 변경.
- Tick 자체보다 SkeletalMesh / StaticMesh 등 자손이 Tick 비용 큼. SceneComponent 자체 Tick 은 가벼움.

## 열린 질문

- [ ] AttachToComponent 의 Sockets 동작 (Skeleton 의 본 이름)
- [ ] UpdateOverlaps / UpdateChildTransforms 의 호출 순서
