---
type: concept
title: "UE Build Configurations (5종)"
aliases: [Debug, DebugGame, Development, Test, Shipping]
sources:
  - "[[sources/ue-build-skill]]"
related_concepts:
  - "[[concepts/Cooked-vs-Uncooked]]"
tags: [ue, build]
last_updated: 2026-05-09
---

# Build Configurations

## 1. 정의 (한 줄)

UE 의 5 가지 빌드 구성 — Debug / DebugGame / Development / Test / Shipping. 각각 최적화 / 디버그 정보 / 자동 테스트 / 셰이더 캐시 / 로깅 정책 다름.

## 2. 자세히

| 구성 | 최적화 | 디버그 정보 | 로깅 | 사용처 |
| -- | -- | -- | -- | -- |
| **Debug** | 없음 | 풀 | 풀 | 엔진 코드 디버깅 |
| **DebugGame** | 게임만 없음 (엔진은 Development) | 게임만 풀 | 풀 | 게임 코드 디버깅 |
| **Development** | 보통 (default) | 부분 | 풀 | 일반 개발 |
| **Test** | 풀 (Shipping 에 가까움) | 거의 없음 | 부분 (자동 테스트) | 자동 테스트 빌드 |
| **Shipping** | 풀 | 없음 | 없음 (default) | 출시 |

## 3. 변형 / 사례 / 응용

- 일상 개발 = Development Editor (Editor 빌드) + Development Game (게임 빌드).
- 디버깅 = DebugGame Editor (게임 코드만 디버그).
- CI 자동 테스트 = Test.
- 출시 = Shipping.
- `stat unit` 등 stat command 는 Test / Shipping 에서 비활성 — `bUseLoggingInShipping=true` 등 옵션으로 조절.

## 4. 관련 entity

- [[entities/UnrealBuildTool]] · [[entities/UnrealAutomationTool]]

## 5. 열린 질문

- [ ] Test 빌드의 자동 테스트 통합 표준
- [ ] Shipping 의 Cheat Manager 비활성 패턴
