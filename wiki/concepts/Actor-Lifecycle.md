---
type: concept
title: "AActor Lifecycle (11 stages)"
aliases: [Actor Lifecycle, Actor Lifetime, OnConstruction, BeginPlay]
sources:
  - "[[sources/ue-gameframework-skill]]"
related_concepts:
  - "[[concepts/Object-Lifecycle]]"
  - "[[concepts/Component-Lifecycle]]"
tags: [ue, runtime, gameframework]
last_updated: 2026-05-09
---

# AActor Lifecycle — 11 stages

## 1. 정의 (한 줄)

[[entities/AActor]] 의 Spawn ~ Destroy 11 단계 — Constructor / PostInitProperties / OnConstruction (RerunConstructionScripts) / PostInitializeComponents / BeginPlay / Tick / EndPlay / BeginDestroy / FinishDestroy + Editor 추가 단계.

## 2. 자세히

```
World->SpawnActor<T>() ─┐
                        ├─▶ Constructor (C++)
                        ├─▶ PostInitProperties
                        ├─▶ OnConstruction (Spawn 시 1회 + Editor 패널 변경마다 재호출 — 멱등 의무)
                        ├─▶ Component 생성 (CreateDefaultSubobject in ctor)
                        ├─▶ Component OnRegister / InitializeComponent
                        ├─▶ Actor PostInitializeComponents
                        ├─▶ Actor BeginPlay
                        ├─▶ Component BeginPlay
                        ├─▶ Tick (PrimaryActorTick.bCanEverTick = true 인 경우)
                        └─▶ Destroy / End of Level
                            ├─▶ Component EndPlay
                            ├─▶ Actor EndPlay
                            ├─▶ BeginDestroy
                            └─▶ FinishDestroy
```

## 3. 변형 / 사례 / 응용

- **OnConstruction 멱등 의무**: Editor 의 Construction Script 와 런타임 Spawn 양쪽에서 호출. 다중 호출에 강해야 함 (Component clear → recreate 패턴). [[concepts/Component-Policies-6]]
- **Super 호출 규약**: BeginPlay → Super FIRST, EndPlay → Super LAST.
- **SpawnActorDeferred + FinishSpawning**: Property 셋업 후 BeginPlay — Spawn 직후 Property 변경하고 싶을 때.
- **Destroy 흐름**: `Destroy()` → 다음 GC 사이클까지 BeginDestroy / FinishDestroy 지연 → Component 들도 같이.
- **Editor PIE vs Cooked**: PIE 는 Editor World 가 World 라 추가 callback 일부, Cooked Game 은 Cleaner.

## 4. 관련 entity

- [[entities/AActor]]
- [[entities/UActorComponent]]

## 5. 열린 질문

- [ ] Editor PIE vs Standalone Game vs Dedicated Server 의 라이프사이클 차이 매트릭스
- [ ] Component 의 InitializeComponent 와 Actor 의 PostInitializeComponents 호출 순서
