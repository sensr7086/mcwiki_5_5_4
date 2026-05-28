---
type: source
title: "UE Input — Subsystem sub-skill"
slug: ue-input-subsystem
source_path: raw/ue-wiki-llm/skills/Input/references/Subsystem.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UEnhancedInputLocalPlayerSubsystem]]"
related_concepts:
  - "[[concepts/IMC-Stack]]"
tags: [ue, input, plugin, subsystem]
---

# UE Input — Subsystem sub-skill

> Source: [[raw/ue-wiki-llm/skills/Input/references/Subsystem.md]]
> Parent: [[sources/ue-input-skill]]

## 1. Summary

[[entities/UEnhancedInputLocalPlayerSubsystem]] + IMC Stack (Priority 7 단계) + UEnhancedPlayerInput + UEnhancedInputComponent + Modular 5.x.

## 2. Key claims

- LocalPlayerSubsystem 자손 — LocalPlayer 마다 별개 (Couch Co-op).
- API: AddMappingContext(IMC, Priority, Options) / RemoveMappingContext / ClearAllMappings.
- IMC Stack ([[concepts/IMC-Stack]]) 7 단계 권장: 0 DefaultGame / 1 Vehicle / 2 Aim / 3 Menu / 4 Cinematic / 5 Debug / 6 Modal.
- UEnhancedPlayerInput: Player 의 입력 처리기 (per-tick value evaluator).
- Modular 5.x: 다른 Plugin (Common Input) 과의 통합 표준.
- 라이프사이클: LocalPlayer 생성 시 자동 Initialize (PlayerController possess 이전 또는 동시).
- ShouldCreateSubsystem(Outer) — EnhancedInput Plugin 활성 시만.

## 3. Open questions

- [ ] LocalPlayer 동적 추가/제거 시 Subsystem 동작 (Couch Co-op 새 player)
