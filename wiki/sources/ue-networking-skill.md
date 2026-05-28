---
type: source
title: "UE 5.7.4 Networking Module — Main SKILL"
slug: ue-networking-skill
source_path: raw/ue-wiki-llm/skills/Networking/SKILL.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/AActor]]"
  - "[[entities/UActorComponent]]"
  - "[[entities/UNetDriver]]"
  - "[[entities/UNetConnection]]"
related_concepts:
  - "[[concepts/Replication]]"
  - "[[concepts/RPC]]"
  - "[[concepts/Authority-NetMode]]"
  - "[[concepts/PushModel]]"
tags: [ue, networking, multiplayer]
last_updated: 2026-05-28
audit_5_5_4: pass-body-no-direct-cite  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE 5.7.4 Networking Module — Main SKILL

> Source: [[raw/ue-wiki-llm/skills/Networking/SKILL.md]]
> Kind: text · Date: 2026-05-09 · Ingested: 2026-05-09

## 1. Summary

게임플레이 코드의 네트워킹 패턴. [[concepts/Replication]] (DOREPLIFETIME / OnRep_ / [[concepts/PushModel]]) + [[concepts/RPC]] (Server / Client / NetMulticast, Reliable / Unreliable) + [[concepts/Authority-NetMode]] (HasAuthority / GetNetMode 분기) + RelevantTo / NetCullDistance + FastArraySerializer + 데디 서버 분기. CoreUObject/Network sub-skill 의 게임 레벨 컴패니언.

## 2. Key claims

- NetMode 5종: Standalone / Client / DedicatedServer / ListenServer / Standalone (테스트). `GetNetMode()` 로 분기.
- Authority vs NetMode 의미 구분: HasAuthority() = 객체 단위 (서버 또는 Standalone), NetMode = World 단위.
- DOREPLIFETIME 매크로 + `GetLifetimeReplicatedProps` override + UPROPERTY(Replicated) — 표준 복제 셋업.
- OnRep_<Var> callback — 클라이언트에서 변수 변경 감지 (UPROPERTY(ReplicatedUsing=OnRep_Var)).
- [[concepts/PushModel]] (5.x 권장) — 변경된 프로퍼티만 명시적 mark dirty (`MARK_PROPERTY_DIRTY_FROM_NAME`). 기존 Pull 모델 대비 CPU ↓.
- RPC 3 종: Server (Client → Server) / Client (Server → 특정 Client) / NetMulticast (Server → 모든 Client). Reliable (보장) / Unreliable (드롭 가능, 빠름).
- RelevantTo / NetCullDistance — 거리 기반 자동 비-relevant. NetUpdateFrequency 로 update rate 조정.
- FastArraySerializer — `TArray<FFastArrayItem>` 의 효율적 복제 (변경 분만).
- 데디 서버 분기: `WITH_SERVER_CODE` + `IsRunningDedicatedServer()`. Cosmetic 코드 (VFX/SFX) skip.

## 3. Quotations

> "HasAuthority() vs GetNetMode() == NM_Client 의미 다름 — Authority 는 객체 단위, NetMode 는 World 단위 [grep-listed]."

## 4. Open questions / next sources

- [ ] PushModel 의 5.x 마이그레이션 표준 — 어떤 프로퍼티부터
- [ ] FastArraySerializer 의 IsFastArray 함정
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-content-shift** (자동 분석)

raw 5.5.4 vs 5.7.4 diff: 작은 의미 변경 + 큰 cosmetic. 시그니처 0 / 추가 4 / 제거 0 / 수치 0 / 기타 1.

**주요 변경 sample**:
- `---`
- ``
- `# Networking — UE 5.5.4 멀티플레이 / Replication`
- `- 5.5.4 위치: `Engine/Source/Runtime/Experimental/Iris/Core/` (Public/Iris/{ReplicationSystem, ReplicationState, Serializa`

**결정**: 🟡 본질 안정, 일부 표현 갱신 필요 가능. 후속 본문 정합 확인 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/Networking/SKILL.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/Networking/SKILL.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **0 변경**
- 정합 후 tier: **🟢 pass-body-no-direct-cite**
