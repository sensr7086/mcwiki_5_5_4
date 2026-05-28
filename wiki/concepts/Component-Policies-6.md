---
type: concept
title: "Component 6대 의무 정책"
aliases: [Component Policies, 6대 정책]
sources:
  - "[[sources/ue-components-skill]]"
  - "[[sources/ue-gameframework-skill]]"
related_concepts:
  - "[[concepts/Mobility]]"
  - "[[concepts/Garbage-Collection]]"
  - "[[concepts/Component-Lifecycle]]"
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, runtime, components, policy]
last_updated: 2026-05-09
---

# Component 6대 의무 정책

## 1. 정의 (한 줄)

UE 의 Components / GameFramework 작성 시 *항상* 적용되는 6 가지 정책 — Mobility / NewObject·DuplicateObject / GC 방어 / GetOwner 캐싱 / PrimaryComponentTick / CDO. UE 횡단 의무. 자세한 코드는 [[raw/ue-wiki-llm/references/10_ComponentPolicies.md]].

## 2. 자세히

| # | 정책 | 핵심 |
| -- | -- | -- |
| 1 | [[concepts/Mobility]] | SceneComponent 자손은 Static / Stationary / Movable 명시. 런타임 SetMobility 금지. Movable 외 Tick 비활성. |
| 2 | NewObject·DuplicateObject | Component = `CreateDefaultSubobject` (Constructor) 또는 `NewObject<>(Outer=Actor)`. Actor = `World->SpawnActor<>()`. 직접 NewObject<AActor> 금지. |
| 3 | GC 방어 | UPROPERTY + `TObjectPtr<>` (멤버) / `TWeakObjectPtr<>` (캐싱) / `TStrongObjectPtr<>` (비-UCLASS). UPROPERTY 누락 = dangling. |
| 4 | GetOwner / GetController / GetPawn 캐싱 | BeginPlay 에서 1회 캐싱 → TWeakObjectPtr 보관 + Tick / 콜백 재조회 금지. |
| 5 | PrimaryComponentTick | 기본 `bCanEverTick = false` + `TickGroup` (TG_PrePhysics 표준) + `TickInterval` 우선 + 매 프레임 Tick = 마지막 수단. |
| 6 | CDO | `GetMutableDefault<T>()->Set*()` 으로 CDO 변경 금지 + `HasAnyFlags(RF_ClassDefaultObject)` 검사 + `CreateDefaultSubobject` 는 Constructor 안만. |

## 3. 변형 / 사례 / 응용

- 모든 [[entities/UActorComponent]] / [[entities/USceneComponent]] / [[entities/UPrimitiveComponent]] 자손 + [[entities/AActor]] / [[entities/APawn]] / [[entities/ACharacter]] / [[entities/AGameModeBase]] 자손 모두 적용.
- 각 sub-skill 본문 시작부에 6 대 정책 블록 의무 삽입 (raw skills/Components/, skills/GameFramework/ 의 표준).

## 4. 관련 entity

- [[entities/UActorComponent]]
- [[entities/AActor]]

## 5. 열린 질문

- [ ] 6대 정책의 자동 검증 도구 (정적 분석 / lint)
