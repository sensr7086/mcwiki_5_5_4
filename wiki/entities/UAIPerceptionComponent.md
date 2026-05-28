---
type: entity
title: "UAIPerceptionComponent / UAISense"
aliases: [UAIPerceptionComponent, Perception, UAISense_Sight, UAISense_Hearing]
kind: model
sources:
  - "[[sources/ue-ai-skill]]"
tags: [ue, ai, components]
last_updated: 2026-05-09
---

# UAIPerceptionComponent

## 요약

[[entities/UActorComponent]] 자손. AI 의 감각 진입점 — Sight / Hearing / Damage / Touch / Team / Prediction 6 종 sense. UAISenseConfig_* 자손으로 감각별 설정 등록. OnTargetPerceptionUpdated delegate 로 인지 변화 알림.

## 관계

- 부모: [[entities/UActorComponent]]
- 호스트: [[entities/AAIController]]
- 협력: UAIPerceptionStimuliSourceComponent (감지 대상 측 — 발자국 소리 발생 등), UAISenseConfig_* (Sense 별 설정)

## 핵심 주장

- 6 종 Sense: Sight (시야 거리 + 각도 + 라인 트레이스) / Hearing (소리 반경) / Damage (피격) / Touch (충돌) / Team (팀 인지) / Prediction (이동 예측).
- 등록 패턴: ConfigureSense(SenseConfig) — Editor 디테일 패널에서 또는 C++ Constructor 에서.
- OnTargetPerceptionUpdated(Actor, Stimulus) — 인지 변경 콜백 (등록/사라짐/위치 변화).
- Stimuli Source: 감지 대상 (예: Player) 에 UAIPerceptionStimuliSourceComponent + RegisterForSense(Sense_Sight) — '인지 가능' 표시.
- Sight Configuration: SightRadius / LoseSightRadius / PeripheralVisionAngleDegrees / DetectionByAffiliation (Friendly / Neutral / Enemy).

## 열린 질문

- [ ] Custom UAISense 작성 패턴 (예: Smell / Magic)
- [ ] PeripheralVisionAngleDegrees 의 360 도 (전방위 인지) 함정
