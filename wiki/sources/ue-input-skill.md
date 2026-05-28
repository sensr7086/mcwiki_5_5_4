---
type: source
title: "UE 5.7.4 Input Module — Main SKILL"
slug: ue-input-skill
source_path: raw/ue-wiki-llm/skills/Input/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UInputAction]]"
  - "[[entities/UInputMappingContext]]"
  - "[[entities/UEnhancedInputLocalPlayerSubsystem]]"
  - "[[entities/UEnhancedInputComponent]]"
  - "[[entities/FKey]]"
related_concepts:
  - "[[concepts/Enhanced-Input-Standard]]"
  - "[[concepts/IMC-Stack]]"
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, input]
---

# UE 5.7.4 Input Module — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/Input/SKILL.md]]

## 1. Summary

5.x Enhanced Input Plugin 표준 + Legacy + InputCore + InputDevice. 5 sub-skill 분할.

## 2. Sub-skills (5 — Phase 4D 완료)

- [[sources/ue-input-enhancedinput]] — 5.x Plugin 메인 + 4 단 셋업 + Pawn/PC 통합
- [[sources/ue-input-action]] — UInputAction + ValueType 4 + ETriggerEvent 7 + UInputTrigger 8 + UInputModifier 9
- [[sources/ue-input-subsystem]] — UEnhancedInputLocalPlayerSubsystem + IMC Stack 7 단계 + Modular 5.x
- [[sources/ue-input-inputcore]] — FKey + EKeys 200+ + Face Button 플랫폼 추상화
- [[sources/ue-input-legacy]] — UInputComponent + DefaultInput.ini + Force Feedback 4 채널 + Haptic 5.x + Migration 5 단계

## 3. Open questions

- [ ] Enhanced Input 의 Multiplayer 동작 (Server-side Input)
