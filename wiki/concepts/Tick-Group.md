---
type: concept
title: "Tick Group (TG_PrePhysics ~ LastDemotable)"
aliases: [Tick Group, TickGroup, ETickingGroup]
sources:
  - "[[sources/ue-gameframework-skill]]"
  - "[[sources/ue-components-skill]]"
related_concepts:
  - "[[concepts/Component-Policies-6]]"
tags: [ue, runtime, gameframework, components]
last_updated: 2026-05-09
---

# Tick Group

## 1. 정의 (한 줄)

UE 의 매 프레임 Tick 순서 결정 enum — Actor / Component 의 PrimaryActorTick.TickGroup / PrimaryComponentTick.TickGroup 으로 결정. 8 종 (PrePhysics / DuringPhysics / PostPhysics / PostUpdateWork / LastDemotable + 내부 사용 3 종).

## 2. 자세히

| Group | 시점 | 사용처 |
| -- | -- | -- |
| **TG_PrePhysics** | 물리 시뮬 전 (default) | 일반 게임 로직, 입력 처리 |
| **TG_StartPhysics** | (내부) | UE 자체 사용 |
| **TG_DuringPhysics** | 물리 시뮬 중 | 물리 결과 영향 받지 않는 cosmetic |
| **TG_EndPhysics** | (내부) | UE 자체 사용 |
| **TG_PostPhysics** | 물리 시뮬 후 | 물리 결과 사용 (Hit 처리 등) |
| **TG_PostUpdateWork** | Render 직전 | 카메라 / VFX 위치 갱신 |
| **TG_LastDemotable** | 가장 마지막 | 디버그 / 최종 정리 |

## 3. 변형 / 사례 / 응용

- 같은 그룹 안의 Tick 순서는 보장 안 됨 → 의존 관계가 있으면 `AddTickPrerequisiteActor` / `AddTickPrerequisiteComponent` 로 강제.
- **TickInterval** (0.05 ~ 1s 등) 으로 매 프레임이 아닌 주기적 Tick — 다수 NPC 환경에서 필수. [[concepts/Component-Policies-6]] §5.
- **CharacterMovement 의 표준**: PostPhysics — 물리 결과 후 위치 finalize.
- **Camera Component**: PostUpdateWork — 마지막에 위치 결정 (가장 늦게 렌더 직전).

## 4. 관련 entity

- [[entities/UWorld]] (Tick 호출 진입점)
- [[entities/AActor]] · [[entities/UActorComponent]]

## 5. 열린 질문

- [ ] DuringPhysics 그룹의 안전한 사용처
- [ ] TickPrerequisite 의 cycle 검출 / 함정
