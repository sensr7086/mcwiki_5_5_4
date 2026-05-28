---
type: entity
title: "UNetConnection"
aliases: [UNetConnection, NetOwner, OwningConnection]
kind: model
sources:
  - "[[sources/ue-networking-skill]]"
tags: [ue, networking, multiplayer]
last_updated: 2026-05-09
---

# UNetConnection

## 요약

[[entities/UNetDriver]] 가 보유한 개별 client connection. 서버에서 client 1개당 1 인스턴스 (Listen Server 자체도 1 connection). Owner [[entities/APlayerController]] / RPC 발화점 / channel 관리.

## 관계

- 부모: [[entities/UObject]]
- 컨테이너: [[entities/UNetDriver]] (서버 측 ClientConnections 배열)
- 페어: [[entities/APlayerController]] (NetOwner)

## 핵심 주장

- Server-side 만 다중 — Client 측에서는 Server connection 1개 만.
- NetOwner = APlayerController. RPC 의 `Server` / `Client` 발화 시 NetOwner 의 Connection 사용.
- Channel 관리: ActorChannel / VoiceChannel / ControlChannel. 각 Channel 이 sub-object 단위 RPC / Replication.
- Saturation: 네트워크 대역 한계 모니터링. 고비용 Replicated Actor 가 saturate 시 일부 update skip.
- Disconnect: ConnectionId / NMT_GameSpecific 메시지 / FUniqueNetIdRepl.

## 열린 질문

- [ ] ChannelClose 의 표준 시점 (Player Quit 등)
- [ ] Voice Channel 의 5.x 활성화
