---
type: source
title: "UE GameFramework — World sub-skill"
slug: ue-gameframework-world
source_path: raw/ue-wiki-llm/skills/GameFramework/references/World.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UWorld]]"
related_concepts:
  - "[[concepts/Tick-Group]]"
  - "[[concepts/Subsystem-5-Types]]"
tags: [ue, runtime, gameframework]
---

# UE GameFramework — World sub-skill

> Source: [[raw/ue-wiki-llm/skills/GameFramework/references/World.md]]
> Parent: [[sources/ue-gameframework-skill]]

## 1. Summary

[[entities/UWorld]] (4,667) + ULevel — PersistentLevel + StreamingLevels + AuthorityGameMode + GameState + WorldType (Game/Editor/PIE/EditorPreview) + UWorldSubsystem 등록 + [[concepts/Tick-Group]] 8 종 + Streaming 3 종.

## 2. Key claims

- WorldType 분기: Game / Editor / PIE / EditorPreview / Inactive. Editor PIE vs Cooked Game 동작 차이 자주 함정.
- [[concepts/Tick-Group]] 8 종: TG_PrePhysics (default) / DuringPhysics / PostPhysics / PostUpdateWork / LastDemotable + 내부 3.
- Level Streaming 3 종: Always Loaded / Streaming Volume / Blueprint Streaming + 5.x WorldPartition (cell 기반 자동).
- Spawn 진입점: `World->SpawnActor<T>(Class, Transform, Params)`. NewObject<AActor> 직접 호출 금지.
- UWorldSubsystem ([[concepts/Subsystem-5-Types]]) — Map 마다 새로 생성. UTickableWorldSubsystem 변형 = Tick 가능.
- Time: GetTimeSeconds (paused / dilation 영향) / GetUnpausedTimeSeconds / GetRealTimeSeconds (dilation 무시).
- Editor vs Cooked: Editor PIE 는 추가 callback. Cooked Game 은 cleaner.

## 3. Open questions

- [ ] WorldPartition 5.x 의 Streaming Source / Cell 동작
- [ ] WorldSubsystem 의 PostInitWorld 시점
