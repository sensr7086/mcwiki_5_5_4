---
type: entity
title: "UNavigationSystemV1 / RecastNavMesh / UCrowdManager"
aliases: [UNavigationSystemV1, NavMesh, Recast, UCrowdManager, RVO]
kind: model
sources:
  - "[[sources/ue-ai-skill]]"
tags: [ue, ai, navigation]
last_updated: 2026-05-09
---

# UNavigationSystemV1 / RecastNavMesh / UCrowdManager

## 요약

[[entities/UObject]] 자손 (싱글톤). UE 의 navigation 진입점. Recast 알고리즘 기반 NavMesh + Crowd Manager (군중 회피, RVO) + ANavigationData (추상 NavMesh 베이스).

## 관계

- 자체 모듈: NavigationSystem (Engine 모듈)
- 페어: ARecastNavMesh (Actor — Map 에 배치, Build 시 NavMesh 생성)
- 협력: UCrowdManager (Plugin — DetourCrowd)

## 핵심 주장

- 싱글톤 접근: `UNavigationSystemV1::GetCurrent(World)`. Subsystem 패턴은 아님 (전통 싱글톤).
- API: FindPath / SimpleMoveToLocation / GetRandomReachablePointInRadius.
- RecastNavMesh: World 에 1+ ARecastNavMesh Actor 배치 → Build 시 NavMesh polygons 생성. Editor 의 'P' 키로 표시.
- DynamicObstacle: UNavModifierComponent 으로 런타임 NavMesh 수정 가능.
- UCrowdManager: 다수 AI 의 동시 이동 시 충돌 회피 (Reciprocal Velocity Obstacle, RVO). UCharacterMovementComponent 의 bUseRVOAvoidance 와 통합.
- 5.x WorldPartition 통합: Cell 단위 NavMesh streaming.

## 열린 질문

- [ ] Dynamic NavMesh build 비용 — 큰 World 의 점진적 build
- [ ] Multiplayer 의 NavMesh 동기 (Server-side path + Client-side prediction)
