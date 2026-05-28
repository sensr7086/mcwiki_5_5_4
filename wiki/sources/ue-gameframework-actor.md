---
type: source
title: "UE GameFramework — Actor sub-skill"
slug: ue-gameframework-actor
source_path: raw/ue-wiki-llm/skills/GameFramework/references/Actor.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/AActor]]"
related_concepts:
  - "[[concepts/Actor-Lifecycle]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, runtime, gameframework]
---

# UE GameFramework — Actor sub-skill

> Source: [[raw/ue-wiki-llm/skills/GameFramework/references/Actor.md]]
> Parent: [[sources/ue-gameframework-skill]]

## 1. Summary

[[entities/AActor]] 베이스 (가장 큰 — 5,074 lines) 의 풀 디테일 — 라이프사이클 11 단계 + Super 호출 규약 + 6 대 정책 + SpawnActorDeferred + 어셋 로드 4 단 + Cooked 검증.

## 2. Key claims

- 라이프사이클 11 단계 ([[concepts/Actor-Lifecycle]]): PostActorCreated → PostInitProperties → OnConstruction → PostInitializeComponents → BeginPlay → Tick → EndPlay → BeginDestroy → FinishDestroy + Editor preview / RerunConstructionScripts.
- Super 호출 규약: BeginPlay → Super FIRST, EndPlay → Super LAST.
- SpawnActor: `World->SpawnActor<T>(Class, Transform, Params)`. Deferred 변형: `SpawnActorDeferred + Property 설정 + FinishSpawning`.
- 6 대 정책 ([[concepts/Component-Policies-6]]) 자동 적용 + Actor 특화 (NewObject<AActor> 직접 호출 금지).
- 어셋 로드 4 단 ([[concepts/Asset-Loading-Policy]]): Class load (TSubclassOf vs TSoftClassPtr) → CDO 로드 → Asset 멤버 로드 → Constructor 추가 로드. Match Start `PreloadPrimaryAssets`.
- Cooked Build (Development) `stat unit` 검증 의무.
- OnConstruction 멱등 의무 — Editor + 런타임 다중 호출.

## 3. Open questions

- [ ] Editor PIE vs Standalone vs Dedicated Server 라이프사이클 차이 매트릭스
