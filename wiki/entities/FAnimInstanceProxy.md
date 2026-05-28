---
type: entity
title: "FAnimInstanceProxy"
aliases: [FAnimInstanceProxy, AnimInstanceProxy]
kind: model
sources:
  - "[[sources/ue-animation-skill]]"
tags: [ue, runtime, animation, threading]
last_updated: 2026-05-09
---

# FAnimInstanceProxy

## 요약

[[entities/UAnimInstance]] 의 **워커 스레드 데이터 owner**. 게임 스레드의 AnimInstance 가 매 프레임 데이터 푸시 → Proxy 가 워커 스레드 (AnimGraph Update_AnyThread / Evaluate_AnyThread) 에서 사용. 이 분리가 다수 캐릭터 60fps 의 핵심.

## 관계

- 페어: [[entities/UAnimInstance]] (게임 스레드)
- 사용: [[entities/FAnimNode-Base]] 자손들 (Update_AnyThread 안에서 Proxy 데이터 read)

## 핵심 주장

- 게임 스레드에서 데이터 캐싱 → 워커 스레드에서 read-only — 동시 race condition 회피.
- AnimInstance 의 NativeUpdate (게임 스레드) 에서 Proxy 의 멤버 set, 워커 스레드 코드는 read 만.
- TWeakObjectPtr / 값 복사로 외부 객체 참조 — UPROPERTY + TObjectPtr 는 게임 스레드에서만 안전.
- GetProxyOnGameThread / GetProxyOnAnyThread 헬퍼 — context 별 안전한 접근.
- Custom AnimInstance + Custom Proxy 패턴: AnimInstance 자손 + Proxy 자손 (USTRUCT) 양쪽 작성.

## 열린 질문

- [ ] Proxy 의 멀티스레딩 안전 보장 — UE 가 어떻게 sync
- [ ] 일반적인 race condition 함정 (TWeakObjectPtr 가 NULL 이 되는 경우)
