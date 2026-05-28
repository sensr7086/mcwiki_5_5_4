---
type: entity
title: "UWorld"
aliases: [UWorld, World]
kind: model
sources:
  - "[[sources/ue-gameframework-skill]]"
tags: [ue, runtime, gameframework, foundation]
last_updated: 2026-05-09
---

# UWorld

## 요약

[[entities/UObject]] 자손. **세계 컨테이너** — PersistentLevel + StreamingLevels + AuthorityGameMode + GameState + Tick Group 8종 + WorldSubsystem. 4,667 lines. Spawn 의 진입점 (`World->SpawnActor<>()`). 5.x WorldPartition 으로 streaming 패러다임 변화.

## 관계

- 부모: [[entities/UObject]]
- 컨테이너: ULevel (PersistentLevel + StreamingLevels)
- 협력: [[entities/AGameModeBase]] (AuthorityGameMode), AGameStateBase, [[entities/UGameInstance]] (OwningGameInstance)
- Subsystem: UWorldSubsystem (Map 마다 새로 생성)

## 핵심 주장

- WorldType 분기: Game / Editor / PIE / EditorPreview / Inactive. Editor PIE 와 Cooked Game 의 동작 차이가 자주 함정. [[raw/ue-wiki-llm/meta/CLAUDE-wiki-honest-limits.md]]
- [[concepts/Tick-Group]] 8종: TG_PrePhysics (default) / DuringPhysics / PostPhysics / PostUpdateWork / LastDemotable + 내부 4종. Actor 의 PrimaryActorTick.TickGroup 으로 결정.
- Level Streaming 3종: Always Loaded / Streaming Volume / Blueprint Streaming + 5.x WorldPartition (cell 기반 자동 streaming).
- Spawn 진입점: `World->SpawnActor<T>(Class, Transform, Params)`. NewObject<AActor> 직접 호출 금지. [[concepts/Component-Policies-6]]
- WorldSubsystem (UWorldSubsystem 자손) — Map 마다 새로 생성. SeamlessTravel 시 새 World 의 새 Subsystem 인스턴스. [[entities/UGameInstance]] 의 GameInstanceSubsystem 과 비교.
- Time: GetTimeSeconds / GetUnpausedTimeSeconds / GetRealTimeSeconds 차이 — pause / dilation / realtime.

## 열린 질문

- [ ] WorldPartition 5.x 의 Streaming Source / Cell 동작
- [ ] WorldSubsystem 의 라이프사이클 — Initialize 시점 (PostInitWorld)
