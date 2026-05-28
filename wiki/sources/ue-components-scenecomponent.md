---
type: source
title: "UE Components — USceneComponent sub-skill"
slug: ue-components-scenecomponent
source_path: raw/ue-wiki-llm/skills/Components/references/SceneComponent.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/USceneComponent]]"
related_concepts:
  - "[[concepts/Mobility]]"
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, components]
---

# UE Components — USceneComponent sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/SceneComponent.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

[[entities/USceneComponent]] 트랜스폼 보유 베이스 — SetWorldLocation / SetRelativeLocation / AttachToComponent / GetForwardVector / [[concepts/Mobility]] (Static/Stationary/Movable). Sockets 지원.

## 2. Key claims

- Transform 3 종 axis: Location / Rotation / Scale. Relative (부모 기준) / World (절대).
- AttachToComponent(Parent, SocketName, Rules) — Component Hierarchy. Rules: KeepRelative / KeepWorld / SnapToTarget.
- GetForwardVector / GetRightVector / GetUpVector — World rotation 의 axis.
- [[concepts/Mobility]] 결정 (Constructor 안만, 런타임 SetMobility 금지): Static (변경 X / Light Baked) / Stationary (위치 고정 / Light 일부 동적) / Movable (모두 가능 / Light Baked X).
- Sockets: Skeleton 의 본 또는 Mesh 의 named transform. AttachToComponent 의 SocketName 인자.
- WorldTransform 캐싱 — Attach Hierarchy 갱신 시 자동 dirty.

## 3. Open questions

- [ ] AttachToComponent 의 Sockets 명명 규칙 (Skeleton vs StaticMesh)
