---
type: entity
title: "UNetDriver / UNetConnection"
aliases: [UNetDriver, UNetConnection, FRepLayout]
kind: model
sources:
  - "[[sources/ue-networking-skill]]"
tags: [ue, networking, multiplayer]
last_updated: 2026-05-09
---

# UNetDriver / UNetConnection

## 요약

UE 의 네트워크 transport 베이스. UNetDriver (서버측: 모든 client connection 관리) + UNetConnection (개별 client connection) + FRepLayout (클래스별 복제 레이아웃 캐시). 게임플레이 코드는 직접 사용 안 함 — Replication API 가 wrapping.

## 관계

- 자손: UIpNetDriver (UDP), UReplicationDriver (5.x 분산)
- 협력: [[entities/AActor]] (Replicated), [[entities/UActorComponent]]

## 핵심 주장

- ServerTickActorChannels: 매 프레임 모든 connection 별 RelevantActors 결정 → 변경된 Property 만 전송 (DOREPLIFETIME).
- FRepLayout: 클래스의 Replicated Property layout 을 캐싱 — 매 frame 분석 비용 회피.
- UReplicationGraph (5.x 옵션 / Plugin): 큰 World 의 Replication 분산 — Cell 기반 actor grouping.
- NetCullDistance / NetUpdateFrequency: Actor 별 네트워크 비용 조절.
- 게임플레이 코드는 보통 직접 안 만남 — Server/Client RPC + Replicated 매크로가 추상화.

## 열린 질문

- [ ] UReplicationGraph vs 기본 Replication 의 결정 기준
- [ ] FRepLayout 의 캐시 invalidation 시점
