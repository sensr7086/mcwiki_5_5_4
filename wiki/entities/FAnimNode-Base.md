---
type: entity
title: "FAnimNode_Base"
aliases: [FAnimNode_Base, AnimNode]
kind: model
sources:
  - "[[sources/ue-animation-skill]]"
tags: [ue, runtime, animation]
last_updated: 2026-05-09
---

# FAnimNode_Base

## 요약

AnimGraph 의 노드 베이스. Custom AnimNode 작성 시 본 struct 를 상속 + 4 단계 `_AnyThread` 메서드 override: Initialize_AnyThread / CacheBones_AnyThread / Update_AnyThread / Evaluate_AnyThread. 모든 호출이 워커 스레드 → game-thread API 사용 금지.

## 관계

- 자손 (5.x 일부): FAnimNode_StateMachine / FAnimNode_BlendSpacePlayer / FAnimNode_Inertialization / FAnimNode_IKRig / FAnimNode_RetargetPoseFromMesh / FAnimNode_LayeredBoneBlend / 등 다수
- 호스트: [[entities/UAnimInstance]] 의 AnimGraph
- 워커 스레드 데이터 source: [[entities/FAnimInstanceProxy]]

## 핵심 주장

- 4 단계 호출 순서: Initialize_AnyThread (1회) → CacheBones_AnyThread (Skeleton 변경 시) → Update_AnyThread (매 frame, 시간 진행) → Evaluate_AnyThread (Pose 계산). [[raw/ue-wiki-llm/skills/Animation/SKILL.md]]
- 모두 `_AnyThread` 접미 — 워커 스레드 호출 의무. UObject API / TActorIterator / GetWorld() 등 game-thread 한정 API 호출 금지.
- Profiling 의무: Update_AnyThread / Evaluate_AnyThread 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`. → [[concepts/Profiling-Scope-Rule]]
- BP 노출: USTRUCT(BlueprintType) + UPROPERTY(EditAnywhere, meta=(...)). AnimGraph Editor 에서 노드로 표시.
- 5.x StateMachine: FAnimNode_StateMachine 의 sub state 들도 본 4 단계 동일 호출.
- 5.x Animation Layer Interface: AnimGraph 를 Layer 로 분할 → 다른 BP 가 layer override.

## 열린 질문

- [ ] CacheBones_AnyThread 가 정확히 언제 호출되는가 (LOD 변경 / Skeleton 변경 / Mesh 변경)
- [ ] Custom AnimNode 의 예제 코드 (Pose 변형 — 시선 추적 등)
