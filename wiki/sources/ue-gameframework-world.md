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
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 pass-minor-numeric** (자동 분석)

raw 5.5.4 vs 5.7.4 diff: 시그니처 0 / 추가 0 / 제거 0 / 수치 3 — 표면 변경만, 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/GameFramework/references/World.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/GameFramework/references/World.md`
