---
type: concept
title: "UActorComponent Lifecycle"
aliases: [Component Lifecycle, OnRegister, InitializeComponent]
sources:
  - "[[sources/ue-components-skill]]"
related_concepts:
  - "[[concepts/Object-Lifecycle]]"
  - "[[concepts/Actor-Lifecycle]]"
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, components]
last_updated: 2026-05-09
---

# UActorComponent Lifecycle

## 1. 정의 (한 줄)

[[entities/UActorComponent]] 의 등록 ~ 해제 6 단계 — OnRegister / InitializeComponent / BeginPlay / Tick / EndPlay / UninitializeComponent / OnUnregister.

## 2. 자세히

```
Component 생성 ──▶ Outer Actor 가 RegisterComponent
                  ├─▶ OnRegister (게임/에디터 모두)
                  ├─▶ InitializeComponent (게임 만, Actor 의 PostInitializeComponents 후)
                  ├─▶ BeginPlay (Actor BeginPlay 후)
                  ├─▶ Tick (PrimaryComponentTick.bCanEverTick = true 인 경우만)
                  └─▶ Outer Actor Destroy 또는 Component Detach
                      ├─▶ EndPlay
                      ├─▶ UninitializeComponent
                      └─▶ OnUnregister
```

## 3. 변형 / 사례 / 응용

- **Super 호출 규약**: BeginPlay → Super FIRST, EndPlay → Super LAST. OnRegister → Super FIRST. 위반 시 등록 해제 깨짐. [[raw/ue-wiki-llm/references/04_OverrideIndex.md]]
- **PrimaryComponentTick**: 기본 `bCanEverTick = false`. 필요 시 Constructor 에서 활성. TickGroup / TickInterval 우선. → [[concepts/Component-Policies-6]]
- **EditorOnly callbacks**: OnComponentCreated (Editor PIE 첫 spawn), PostEditChangeProperty (Editor 패널 변경) — `WITH_EDITOR` 가드.

## 4. 관련 entity

- [[entities/UActorComponent]]
- [[entities/USceneComponent]]
- [[entities/AActor]]

## 5. 열린 질문

- [ ] InitializeComponent vs BeginPlay 의 Editor PIE vs Standalone vs Cooked Build 차이
- [ ] AddInstanceComponent 로 런타임 추가된 Component 의 lifecycle
