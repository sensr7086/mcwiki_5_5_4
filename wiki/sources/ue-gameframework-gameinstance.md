---
type: source
title: "UE GameFramework — GameInstance sub-skill"
slug: ue-gameframework-gameinstance
source_path: raw/ue-wiki-llm/skills/GameFramework/references/GameInstance.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/UGameInstance]]"
related_concepts:
  - "[[concepts/Subsystem-5-Types]]"
  - "[[concepts/SeamlessTravel]]"
tags: [ue, runtime, gameframework]
---

# UE GameFramework — GameInstance sub-skill

> Source: [[raw/ue-wiki-llm/skills/GameFramework/references/GameInstance.md]]
> Parent: [[sources/ue-gameframework-skill]]

## 1. Summary

[[entities/UGameInstance]] (664 lines) — Levels/맵 전환 살아남는 *유일한 World-bound 외 객체*. Init / Start / Shutdown 라이프사이클. UGameInstanceSubsystem (UDynamicSubsystem) 호스트. UAssetManager 진입점.

## 2. Key claims

- 라이프사이클 3 단계: Init() → Start() → Shutdown(). 게임 실행 시 1 번씩만.
- [[concepts/SeamlessTravel]] 동안 살아남음 — PlayerController / GameMode / World 는 새로 생성되지만 GameInstance 는 그대로.
- LocalPlayer 관리: GetLocalPlayers() / CreateLocalPlayer / RemoveLocalPlayer (Couch Co-op).
- UAssetManager 진입점: GetAssetManager() — Project Settings 의 AssetManagerClassName.
- UGameInstanceSubsystem ([[concepts/Subsystem-5-Types]]) = UDynamicSubsystem 자손, 모듈 로드 시 자동 인스턴싱.
- 영속 데이터 / 세션 정보 / 글로벌 통계 표준 위치.
- LoadingScreen 진입점.
- Online Subsystem 통합 (Steam / EOS / PSN 등).

## 3. Open questions

- [ ] SeamlessTravel 데이터 인계 — PlayerState 와 비교
- [ ] UAssetManager 커스터마이징 5.x bundle 표준
