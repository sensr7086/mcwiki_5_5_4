---
type: source
title: "UE Animation — Sync sub-skill"
slug: ue-animation-sync
source_path: raw/ue-wiki-llm/skills/Animation/references/Sync.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_concepts:
  - "[[concepts/Inertialization]]"
tags: [ue, runtime, animation]
---

# UE Animation — Sync sub-skill

> Source: [[raw/ue-wiki-llm/skills/Animation/references/Sync.md]]
> Parent: [[sources/ue-animation-skill]]

## 1. Summary

SyncGroup (FAnimSyncScope) + Mirror (MirrorSyncScope) + [[concepts/Inertialization]] (FAnimNode_Inertialization 5.x). 다중 BlendSpace / Sequence 박자 동기 + 좌우 미러 + 0 ms 블렌드 (전이) 표준.

## 2. Key claims

- FAnimSyncScope: SyncGroup 이름 (예: "Locomotion") 으로 묶인 Sequence / BlendSpace 가 같은 박자 (Phase) 로 진행. 발자국 동기.
- Sync Marker: Sequence / BlendSpace 의 named marker (예: "LeftFoot" / "RightFoot") — Phase 진행 기준.
- MirrorSyncScope: 좌우 mirror — 같은 Sequence 가 좌우 반전. Mirror Data Table 자산.
- [[concepts/Inertialization]] 5.x: 0 ms 블렌드 — 이전 모션의 inertia (속도 + 가속도) 를 spring-damper 로 decay. Crossfade 대비 깔끔.
- FAnimNode_Inertialization: AnimGraph 의 Final Pose 직전에 1 개. Request 발화점에서 트리거.
- State Machine 전이 자동 통합 — Inertialization 노드가 있으면 transition 시 자동 사용.

## 3. Open questions

- [ ] Inertialization 의 본별 weight (전신 vs 상체만)
- [ ] Sync Marker 의 BlendSpace 통합 패턴
