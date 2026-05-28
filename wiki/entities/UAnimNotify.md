---
type: entity
title: "UAnimNotify"
aliases: [UAnimNotify, UAnimNotifyState, AnimNotify]
kind: model
sources:
  - "[[sources/ue-animation-skill]]"
tags: [ue, runtime, animation]
last_updated: 2026-05-09
---

# UAnimNotify / UAnimNotifyState

## 요약

[[entities/UObject]] 자손. **AnimSequence / AnimMontage 시간상의 이벤트 트리거** — UAnimNotify (점, 한 순간) + UAnimNotifyState (구간, 시작~끝). 발자국 / 콤보 윈도우 / 히트박스 / 무기 trail 등이 표준 사용처. Pool / AutoRelease 의무 — Notify 객체는 GC 회피용 풀링.

## 관계

- 부모: [[entities/UObject]]
- 자손 (예시): UAnimNotify_PlaySound / UAnimNotify_PlayParticleEffect / UAnimNotifyState_Trail / UAnimNotifyState_TimedNiagaraEffect / 사용자 정의
- 호스트: [[entities/UAnimSequence]] / [[entities/UAnimMontage]] 의 Notify 트랙

## 핵심 주장

- 점 vs 구간: UAnimNotify 는 한 순간 (한 번 호출), UAnimNotifyState 는 구간 (NotifyBegin / NotifyTick / NotifyEnd 3 단).
- Pool / AutoRelease 의무: Notify 객체는 매 호출마다 NewObject 하면 GC 부담 — UE 가 풀링 관리. Custom Notify 작성 시 멤버 캐싱은 짧게 (Pool 에서 재사용 시 stale 위험).
- Branch Point notify: AnimMontage 에 등록된 특수 Notify — Section 분기 결정 지점. Combo / Hit reaction.
- Notify Queue: AnimGraph Update_AnyThread → Notify Queue 모음 → Game thread 에서 발화 (Notify::Notify / NotifyBegin/End 콜백).
- Profiling 의무: Notify::Notify / NotifyBegin / NotifyEnd 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`. [[concepts/Profiling-Scope-Rule]]

## 열린 질문

- [ ] AnimNotify Pool 의 정확한 동작 — 멤버 변수 사용 시 함정
- [ ] Branch Point Notify 와 일반 Notify 의 호출 순서
