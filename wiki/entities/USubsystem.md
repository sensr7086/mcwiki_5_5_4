---
type: entity
title: "USubsystem"
aliases: [USubsystem, UDynamicSubsystem]
kind: model
sources:
  - "[[sources/ue-subsystem-skill]]"
tags: [ue, runtime, subsystem]
last_updated: 2026-05-09
---

# USubsystem

## 요약

[[entities/UObject]] 자손 (Abstract). UE Engine 이 자동 인스턴스 생성 + 라이프사이클 관리하는 5 종 베이스. ShouldCreateSubsystem (조건) + Initialize (초기화) + Deinitialize (해제) 3 virtual.

## 관계

- 부모: [[entities/UObject]]
- 자손: UEngineSubsystem / UEditorSubsystem / UGameInstanceSubsystem / UWorldSubsystem / ULocalPlayerSubsystem
- 변형: UDynamicSubsystem (Engine/Editor — 모듈 로드 시 자동), UTickableWorldSubsystem (Tick 가능)

## 핵심 주장

- 3 virtual 의 표준 구현:
  - `bool ShouldCreateSubsystem(UObject* Outer)` — false 반환 시 인스턴스 X. 서버 only / WITH_EDITOR only / 특정 플랫폼 만 분기.
  - `void Initialize(FSubsystemCollectionBase& Collection)` — 의존 Subsystem 등록 (`Collection.InitializeDependency<USomeOtherSubsystem>()`) + 자체 초기화.
  - `void Deinitialize()` — 정리. UObject lifecycle 의 BeginDestroy 와 별개.
- 5 종 비교 (자세한 [[concepts/Subsystem-5-Types]]):
  - Engine / Editor / GameInstance / World / LocalPlayer.
- 전역 이터레이터 회피의 표준 대안 — 등록 1회 + 검색 0. [[raw/ue-wiki-llm/references/09_GlobalIteratorPolicy.md]]
- Network: `int32 GetFunctionCallspace(UFunction*, FFrame*)` override 로 RPC 처리 가능.

## 열린 질문

- [ ] Initialize 안에서 다른 Subsystem 의존 등록 패턴
- [ ] UDynamicSubsystem 의 모듈 로드 순서 의존
