---
type: source
title: "UE Animation — AnimGraph sub-skill"
slug: ue-animation-animgraph
source_path: raw/ue-wiki-llm/skills/Animation/references/AnimGraph.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/FAnimNode-Base]]"
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, runtime, animation]
---

# UE Animation — AnimGraph sub-skill

> Source: [[raw/ue-wiki-llm/skills/Animation/references/AnimGraph.md]]
> Parent: [[sources/ue-animation-skill]]

## 1. Summary

AnimGraph 노드 — [[entities/FAnimNode-Base]] 자손 의 4 단계 `_AnyThread` callback (Initialize / CacheBones / Update / Evaluate) + GatherDebugData. StateMachine + Transition + Layer Interface (5.x). Custom AnimNode 작성 표준.

## 2. Key claims

- 4 단계 호출 순서: Initialize_AnyThread (1회) → CacheBones_AnyThread (Skeleton 변경 시) → Update_AnyThread (매 frame 시간 진행) → Evaluate_AnyThread (Pose 계산).
- 모두 워커 스레드 호출 — UObject API / TActorIterator / GetWorld() 등 game-thread API 금지.
- GatherDebugData: Editor 디버그 패널의 노드 정보 수집.
- StateMachine: FAnimNode_StateMachine 의 sub state 들도 동일 4 단계 호출.
- 5.x Animation Layer Interface: AnimGraph 를 Layer 로 분할 → 다른 BP 가 Layer override (예: 무기별 다른 상체 layer).
- Profiling 의무 ([[concepts/Profiling-Scope-Rule]]): Update_AnyThread / Evaluate_AnyThread 첫 줄 SCOPE.
- Custom AnimNode 작성: USTRUCT(BlueprintType) + UPROPERTY 노출 + 4 callback 구현.

## 3. Open questions

- [ ] CacheBones_AnyThread 호출 시점 (LOD / Skeleton / Mesh 변경)
- [ ] Custom AnimNode 예제 (시선 추적 등)
