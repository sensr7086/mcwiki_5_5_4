---
type: source
title: "UE GameFramework — Actor sub-skill"
slug: ue-gameframework-actor
source_path: raw/ue-wiki-llm/skills/GameFramework/references/Actor.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
related_entities:
  - "[[entities/AActor]]"
related_concepts:
  - "[[concepts/Actor-Lifecycle]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, runtime, gameframework]
last_updated: 2026-05-28
audit_5_5_4: pass-body-reconciled  # 2026-05-28 Phase 2-C body-reconciliation
---

# UE GameFramework — Actor sub-skill

> Source: [[raw/ue-wiki-llm/skills/GameFramework/references/Actor.md]]
> Parent: [[sources/ue-gameframework-skill]]

## 1. Summary

[[entities/AActor]] 베이스 (가장 큰 — 4,912 lines) 의 풀 디테일 — 라이프사이클 11 단계 + Super 호출 규약 + 6 대 정책 + SpawnActorDeferred + 어셋 로드 4 단 + Cooked 검증.

## 2. Key claims

- 라이프사이클 11 단계 ([[concepts/Actor-Lifecycle]]): PostActorCreated → PostInitProperties → OnConstruction → PostInitializeComponents → BeginPlay → Tick → EndPlay → BeginDestroy → FinishDestroy + Editor preview / RerunConstructionScripts.
- Super 호출 규약: BeginPlay → Super FIRST, EndPlay → Super LAST.
- SpawnActor: `World->SpawnActor<T>(Class, Transform, Params)`. Deferred 변형: `SpawnActorDeferred + Property 설정 + FinishSpawning`.
- 6 대 정책 ([[concepts/Component-Policies-6]]) 자동 적용 + Actor 특화 (NewObject<AActor> 직접 호출 금지).
- 어셋 로드 4 단 ([[concepts/Asset-Loading-Policy]]): Class load (TSubclassOf vs TSoftClassPtr) → CDO 로드 → Asset 멤버 로드 → Constructor 추가 로드. Match Start `PreloadPrimaryAssets`.
- Cooked Build (Development) `stat unit` 검증 의무.
- OnConstruction 멱등 의무 — Editor + 런타임 다중 호출.

## 3. Open questions

- [ ] Editor PIE vs Standalone vs Dedicated Server 라이프사이클 차이 매트릭스
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 partial-needs-review** (자동 분석)

raw 5.5.4 vs 5.7.4 diff 자동 분석:
- 시그니처 변경: 2
- 추가 (5.5.4 에만): 0
- 제거 (5.7.4 에만, 5.5.4 에 없음): 0
- 수치 변경: 0

**주요 시그니처**:
- `> **위치**: `Engine/Source/Runtime/Engine/Classes/GameFramework/Actor.h` (5,074 li → > **위치**: `Engine/Source/Runtime/Engine/Classes/GameFramework/Actor.h` (4,912 li`
- `| 2026-05-05 | 최초 작성. AActor 5,074 lines 분석. 라이프사이클 11단계 (Constructor/PostInitPr → | 2026-05-05 | 최초 작성. AActor 4,912 lines 분석. 라이프사이클 11단계 (Constructor/PostInitPr`

**5.5.4 에만 (5.7.4 에 없음)**:
_(없음)_

**5.7.4 에만 (5.5.4 에 없음 — 5.5 → 5.7 추가)**:
_(없음)_

**결정**: 🟡 PARTIAL — 본 페이지의 핵심 결론은 대부분 stable 추정. 위 변경이 본문 정합에 영향 — 후속 본문 갱신 권장.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/skills/GameFramework/references/Actor.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/skills/GameFramework/references/Actor.md`

### Body Reconciliation (2026-05-28)

- 자동 substitution: **1 변경**
- 정합 후 tier: **🟢 pass-body-reconciled**
