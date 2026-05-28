---
type: source
title: "UE GameFramework Specialist — Actor 11단 + Subsystem 5종 + SpawnActor 4단"
slug: ue-agent-gameframework
source_path: raw/ue-wiki-llm/agents/ue-gameframework-specialist.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-28
audit_5_5_4: pass-label-only  # 2026-05-28 Phase 2-B auto-classified
related_entities:
  - "[[entities/AActor]]"
  - "[[entities/APawn]]"
  - "[[entities/ACharacter]]"
  - "[[entities/UGameInstance]]"
related_concepts:
  - "[[concepts/Actor-Lifecycle]]"
  - "[[concepts/Possession]]"
  - "[[concepts/Subsystem-5-Types]]"
tags: [ue, agent, specialist, gameframework, subsystem, actor-lifecycle-11, enriched-card]
citation_disclosure: "🟢 raw verified · Cycle 5n Round 2 enrich"
---

# UE GameFramework Specialist

> Source: [[raw/ue-wiki-llm/agents/ue-gameframework-specialist.md]]
> Parent: [[sources/ue-agent-orchestrator]] — `[GameFramework]` / `[Subsystem]` prefix 호출
> Cycle 5n Round 2 — stub → 정밀 enrich

## 1. Summary

🟢 UE 5.7.4 GameFramework + Subsystem 카테고리 전문가 — **AActor / APawn / ACharacter / AController / APlayerController / AAIController / AGameMode / AGameState / APlayerState / UGameInstance / UWorld 6 sub-skill** + Subsystem 통합. **라이프사이클 11단계** + Super 호출 + 어셋 로드 4단 + Match State 자동.

## 2. 자동 로드 (5 파일)

1. `skills/GameFramework/SKILL.md` (메인)
2. `skills/Subsystem/SKILL.md` (5종 통합)
3. [[sources/ue-ref-11-assetloadingpolicy]] (SpawnActor 히칭)
4. [[sources/ue-ref-10-componentpolicies]] (6대 정책 — Actor 도 적용)
5. 사용자 요청 매칭 sub-skill

## 3. Actor 라이프사이클 11단계

```
Constructor → PostInitProperties → PostInitializeComponents
   → BeginPlay → [Tick / Possess / Replication]
   → EndPlay → Destroyed → BeginDestroy → FinishDestroy
```

**Super 호출 의무**:
- 초기화 (PostInit / BeginPlay) → **Super FIRST**
- 정리 (EndPlay / BeginDestroy) → **Super LAST**

## 4. SpawnActor 히칭 4단 표준 (Actor §12)

```cpp
1. PreLoad — UAssetManager::PreloadPrimaryAssets({...}, ..., bLoadRecursive=true)
2. Wait — Handle->WaitUntilComplete()
3. SpawnActorDeferred — World->SpawnActorDeferred<>(...)
4. FinishSpawning — Actor->FinishSpawning(Transform)
```

❌ 안티패턴: `World->SpawnActor<>()` — Cooked Build 첫 호출 100ms~1s 히칭.

## 5. Subsystem 5종 결정 트리

```
Editor 전용?              → UEditorSubsystem 🛠
Engine 시작~종료?         → UEngineSubsystem
Map 전환 살아남음?        → UGameInstanceSubsystem ⭐
LocalPlayer 별 (Co-op)?  → ULocalPlayerSubsystem
Map 마다 + Tick 필요?    → UTickableWorldSubsystem
Map 마다 + Tick X?        → UWorldSubsystem
```

## 6. Pawn vs Character 결정

| 시나리오 | 추천 |
|---------|------|
| 캐릭터 (걷기/뛰기/점프/크라우치) | **ACharacter** (Capsule + Mesh + CMC 페어) |
| 차량 / 비행기 / 로봇 | **APawn** (커스텀 Movement) |
| AI Pawn (단순) | APawn + AAIController |
| Player Pawn | ACharacter + APlayerController |

## 7. 다수 NPC 환경 (Character)

→ `GameFramework/PawnCharacter/CharacterOptimization.md` (10종):
- `bCanEverTick = false`
- URO + EVisibilityBasedAnimTickOption
- Significance 통합
- AnimationBudgetAllocator (5.x Plugin)
- Network 분리 (Player vs AI)

## 8. Baseline Grep 의무

함정 키워드: `AActor` / `BeginPlay` / `EndPlay` / `Possession` / `SpawnActor` / `Match-State` / `SeamlessTravel` / `OnConstruction` / `Replication` / `PostInitializeComponents`.

## 9. 거부 조건

- 단일 Component — `ue-components-specialist`
- UI / HUD — `ue-slate-umg-specialist`
- Editor 도구 — `ue-editor-specialist`
- Plugin (GAS / Niagara) — `ue-plugin-specialist`

## 10. Cross-link

- 메타 agent: [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-evaluator]] · [[sources/ue-agent-audit]] · [[sources/ue-agent-wiki-maintainer]]
- 페어 specialist: [[sources/ue-agent-components]] (Component 호스트) · [[sources/ue-agent-input]] (Possession + InputComponent)
- 정책 권위: [[sources/ue-ref-11-assetloadingpolicy]] · [[sources/ue-ref-10-componentpolicies]]
- sub-skill: [[sources/ue-gameframework-actor]] · [[sources/ue-gameframework-pawncharacter]] · [[sources/ue-gameframework-controller]] · [[sources/ue-gameframework-gamemode]] · [[sources/ue-gameframework-gameinstance]] · [[sources/ue-gameframework-world]] · [[sources/ue-gameframework-characteroptimization]]
- 시스템: [[sources/ue-meta-baseline-grep-system]] §7

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | stub 카드 |
| 2026-05-15 (Cycle 5n Round 2) | ⭐⭐⭐ stub → 정밀 11 절. 라이프사이클 11단 + SpawnActor 4단 + Subsystem 5종 + Pawn vs Character |
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
