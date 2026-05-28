---
type: entity
title: "UGameInstance"
aliases: [UGameInstance, GameInstance]
kind: model
sources:
  - "[[sources/ue-gameframework-skill]]"
tags: [ue, runtime, gameframework, foundation]
last_updated: 2026-05-09
---

# UGameInstance

## 요약

[[entities/UObject]] 자손. **Levels/맵 전환을 살아남는 유일한 World-bound 외 객체** (664 lines). 게임 실행 ~ 종료까지 1개. UGameInstanceSubsystem (UDynamicSubsystem 자손) 의 호스트. UAssetManager 진입점 + LocalPlayer 관리.

## 관계

- 부모: [[entities/UObject]]
- 자손: 사용자 정의 GameInstance (DefaultGameInstance 또는 Game.ini 에 등록)
- Subsystem: UGameInstanceSubsystem (UDynamicSubsystem) — 자동 인스턴싱
- 협력: [[entities/UWorld]] (OwningGameInstance), ULocalPlayer

## 핵심 주장

- 라이프사이클 3 단계: Init() → Start() → Shutdown(). 게임 실행 시점에 1번씩만.
- 맵 전환에서 살아남음 — [[concepts/SeamlessTravel]] 동안 World/GameMode/PlayerController 는 새로 생성되지만 GameInstance 는 그대로.
- LocalPlayer 관리: GetLocalPlayers() / CreateLocalPlayer / RemoveLocalPlayer (Couch Co-op).
- UAssetManager 진입점: GetAssetManager() — Project Settings 의 AssetManagerClassName 으로 결정. Primary Asset 등록 + PreloadPrimaryAssets. [[concepts/Asset-Loading-Policy]]
- LoadingScreen / 영속 데이터 (세이브 파일 핸들 / 글로벌 통계) 의 자연스러운 위치.
- UDynamicSubsystem (UGameInstanceSubsystem) 패턴 — 모듈 로드 시 자동 인스턴싱. TActorIterator 회피의 표준 대안. [[raw/ue-wiki-llm/references/09_GlobalIteratorPolicy.md]]

## 열린 질문

- [ ] GameInstance 의 SeamlessTravel 데이터 인계 패턴 — PlayerState 와 비교
- [ ] UAssetManager 커스터마이징 — 5.x bundle 표준
