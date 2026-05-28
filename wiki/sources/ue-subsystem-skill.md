---
type: source
title: "UE 5.7.4 Subsystem 5종 — Main SKILL"
slug: ue-subsystem-skill
source_path: raw/ue-wiki-llm/skills/Subsystem/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
related_entities:
  - "[[entities/USubsystem]]"
  - "[[entities/UEngineSubsystem]]"
  - "[[entities/UGameInstance]]"
  - "[[entities/UWorld]]"
related_concepts:
  - "[[concepts/Subsystem-5-Types]]"
  - "[[concepts/Global-Iterator-Avoidance]]"
tags: [ue, runtime, subsystem]
---

# UE 5.7.4 Subsystem 5종 — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/Subsystem/SKILL.md]]

## 1. Summary

UE Engine 자동 인스턴스 생성 + 라이프사이클 관리 5 종. TActorIterator/TObjectIterator 회피의 표준 대안 — 등록 1 회 + 검색 0.

## 2. Sub-skills (1)

- [[sources/ue-subsystem-onlinesubsystem]] — Online Subsystem (Steam/EOS/PSN/Xbox/Switch + 5.x EOSCore)

## 3. Key claims

- 5 종: UEngineSubsystem / UEditorSubsystem 🛠 / UGameInstanceSubsystem ⭐ / UWorldSubsystem / ULocalPlayerSubsystem.
- USubsystem 베이스의 3 virtual: ShouldCreateSubsystem / Initialize / Deinitialize.
- 자세한 비교 매트릭스 → [[concepts/Subsystem-5-Types]].
- 전역 이터레이터 회피 → [[concepts/Global-Iterator-Avoidance]].
- 9 시나리오 결정 트리 + 함정 10 종 (raw 본문).

## 4. Open questions

- [ ] UEngineSubsystem vs UGameInstanceSubsystem 결정 트리
- [ ] UTickableWorldSubsystem 의 Tick group 설정
