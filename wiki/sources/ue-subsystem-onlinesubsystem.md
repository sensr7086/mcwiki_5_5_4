---
type: source
title: "UE Subsystem — OnlineSubsystem (멀티플레이/매치메이킹)"
slug: ue-subsystem-onlinesubsystem
source_path: raw/ue-wiki-llm/skills/Subsystem/references/OnlineSubsystem.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
tags: [ue, subsystem, online, multiplayer]
---

# UE Subsystem — OnlineSubsystem

> Source: [[raw/ue-wiki-llm/skills/Subsystem/references/OnlineSubsystem.md]]
> Parent: [[sources/ue-subsystem-skill]]

## 1. Summary

Online Subsystem — 멀티플레이 / 매치메이킹 / 친구 / 업적. **Steam / EOS (Epic Online Services) / PSN / Xbox Live / Switch / Google Play**. IOnlineSubsystem + IOnlineSession + IOnlineIdentity + IOnlineFriends 인터페이스 + 5.x EOSCore.

## 2. Key claims

- IOnlineSubsystem: 플랫폼별 구현 (Steam / EOS / PSN / etc) 의 추상 인터페이스.
- 인터페이스 카탈로그: IOnlineSession (방 만들기/찾기) / IOnlineIdentity (로그인/프로필) / IOnlineFriends / IOnlineLeaderboards / IOnlineAchievements / IOnlineVoice.
- 5.x EOSCore (Epic Online Services): cross-platform 매치메이킹 / 친구 / 업적 표준.
- Activation: DefaultEngine.ini 의 [OnlineSubsystem] DefaultPlatformService.
- API 사용: `IOnlineSubsystem::Get()->GetSessionInterface()` 등 → delegate 기반 비동기 callback.
- Listen Server / Dedicated Server 별 셋업 차이.
- UGameInstance 가 Online Subsystem 의 표준 호스트 — Login / Logout 라이프사이클.
