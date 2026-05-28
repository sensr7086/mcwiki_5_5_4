---
type: source
title: "UE Components — SystemComponents sub-skill"
slug: ue-components-systemcomponents
source_path: raw/ue-wiki-llm/skills/Components/references/SystemComponents.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UEnhancedInputComponent]]"
related_concepts:
  - "[[concepts/Enhanced-Input-Standard]]"
tags: [ue, runtime, components, system]
---

# UE Components — SystemComponents sub-skill

> Source: [[raw/ue-wiki-llm/skills/Components/references/SystemComponents.md]]
> Parent: [[sources/ue-components-skill]]

## 1. Summary

시스템 통합 컴포넌트 — UInputComponent ([[entities/UEnhancedInputComponent]] 5.x) + UChildActorComponent (Actor 합성) + UApplicationLifecycleComponent + UPlatformEventsComponent + UWorldPartitionStreamingSourceComponent.

## 2. Key claims

- UInputComponent / UEnhancedInputComponent: [[concepts/Enhanced-Input-Standard]] 의 페어. [[entities/APlayerController]] / [[entities/APawn]] 의 Possess 시 자동 SetupPlayerInputComponent.
- UChildActorComponent: 다른 Actor 를 Component 처럼 부착. Spawn 시 Class 의 Actor 자동 생성. Actor 합성 (예: 무기 + Owner 캐릭터).
- UApplicationLifecycleComponent: App Foreground / Background / Low Memory 등 OS 이벤트.
- UPlatformEventsComponent: 플랫폼별 이벤트 (예: Mobile 의 thermal warning).
- UWorldPartitionStreamingSourceComponent (5.x): WorldPartition 의 cell streaming 진입점 — 카메라 / 플레이어 위치 기반.

## 3. Open questions

- [ ] UChildActorComponent vs Spawn + Attach 결정 트리
- [ ] WorldPartitionStreamingSource 의 다중 source 패턴 (분할 화면)
