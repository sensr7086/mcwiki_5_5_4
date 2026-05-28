---
type: synthesis
title: "Cycle 5p Postmortem Remediation — Engine Compile Blocker 3중 verify 도입"
slug: cycle-5p-postmortem-remediation
created: 2026-05-17
last_updated: 2026-05-17
status: settled
sources:
  - "[[sources/ue-meta-baseline-grep-system]]"
  - "[[sources/ue-agent-evaluator]]"
  - "[[sources/ue-agent-orchestrator]]"
entities: []
concepts: []
tags: [governance, cycle-5p, postmortem, remediation, engine-verify, compile-blocker, kmcproject-derived, three-tier-verify]
---

# Cycle 5p Postmortem Remediation — Engine Compile Blocker 3중 verify 도입

> KMCProject Phase 2 (MCComboSection LevelSequence-style upgrade) 사후 분석에서 도출된 4 patch 의 vault 측 페어. 핵심 메커니즘 = **Generator §pre-write + Evaluator §Stage 2.X + Orchestrator §Pre-Flight 3중 verify**. 손실 시간 ~390-735s (24-45%) → ~605s (37%) 회복 가능 (예측).

## 1. Thesis

**vault 일반 패턴**: UE 5.7.4 C++ 코드 작성 시 Engine 본가 패턴 (UPROPERTY templated container / TArray cross-type / bitfield / DEPRECATED / Custom Serialize / Slate API) 을 사전 verify 하지 않으면 Compile blocker 발생 → refactor 사이클 필연.

**원인**: Phase 2 작업 (2026-05-16~17) 의 11 Agent 호출 중 2회 BLOCKER 발생:
- Phase 2a `TRange<FFrameNumber>` UPROPERTY 직접 부착 → UHT reflection 불가 → USTRUCT 래퍼 의무
- Phase 2c `TArray<UMCComboSection*> = Track->Sections` cross-type copy-init → `Array.h L752` `explicit` ctor → direct-init 의무

**해결**: 3중 verify 구조 — Generator (specialist) / Evaluator (사용자 수동 호출) / Orchestrator (메인) 가 각자 다른 시점에 Engine 본가 grep 수행. 7 항목 (A~G) 동일 매트릭스.

## 2. 4 patch 적용 매트릭스

| Patch | Priority | 대상 | 핵심 추가 § | 영향 |
| -- | -- | -- | -- | -- |
| **a (#1)** | P0 | 11 specialist `.md` (raw/ue-wiki-llm/agents/) | `## §pre-write 1단계 — Engine Compile Blocker Verification` | Generator 가 작성 *전* Engine grep 의무 |
| **b (#2)** | P1 | [[00_meta/08_VaultScopePolicy]] | `### 3.5 Handoff Compile-Level Verify 의무` | handoff document (mc-/synthesis/*) Phase 1 evaluator Critical 30 감점 |
| **c (#3)** | P0 | [[00_meta/03_EvaluatorRecipe]] | `## 1.5 UE 코드 평가 시 Stage 2.X — Engine Authority Verification` | Evaluator (사용자 수동 호출) 가 작성 *후* Engine grep *재검증* |
| **d (#4)** | P2 | [[00_meta/07_AgentBoundaryProtocol]] | `## §2.5 Pre-Flight Engine Grep Batch 의무` | Orchestrator (메인) 가 multi-step 호출 *전* batch grep |

## 3. 손실 시간 정량화 (실측 + 예측)

🟢 **실측** (`outputs/cycle-5p-handoff/01_timing_analysis.md`):

| Phase | 1차 (s) | refactor (s) | 결과 |
|-------|--------|-------------|------|
| 2a | 308 (BLOCKER — TRange) | 280 (PASS 91.0 — USTRUCT 래퍼) | TRange UPROPERTY |
| 2b | 159 (PASS 94.0) | — | 정상 |
| 2c | 427 (BLOCKER — TArray cross-type) | 110 (재평가 skip) | TArray copy-init |
| 2d | 338 (PASS 91.0) | — | 정상 |
| **합계** | **1,622s (~27분)** | | |

**손실**:
- 직접: refactor 사이클 = **390s (24%)**
- 간접 (보수적): 1차 BLOCKER 까지 도달한 specialist + evaluator = **735s (45%)**

🟡 **예측** — Cycle 5p 4 patch 적용 후 (refactor 사이클 0회 가정):

| 항목 | Before | After | 단축 |
| -- | --: | --: | --: |
| Phase 2a | 588s | ~250s | -338s |
| Phase 2b | 159s | 159s | 0 |
| Phase 2c | 537s | ~270s | -267s |
| Phase 2d | 338s | 338s | 0 |
| **합계** | **1,622s** | **~1,017s** | **-605s (37%)** |

→ 다음 Cycle 5p+1 의 multi-step 작업에서 실측 검증 의무.

## 4. 3중 verify 분담

| 단계 | 주체 | 시점 | 위치 | 7 항목 (A~G) |
| -- | -- | -- | -- | -- |
| **Pre-Flight** | 메인 (Orchestrator) | specialist 호출 *전* | [[00_meta/07_AgentBoundaryProtocol]] §2.5 | batch grep 1회 + prompt 사전 첨부 |
| **Pre-write** | Specialist (Generator) | 코드 작성 *전* | specialist `.md` §pre-write 1단계 (raw/agents/) | 메인 batch 결과 *재검증* (sanity) |
| **Stage 2.X** | Evaluator (사용자 수동 호출) | 코드 작성 *후* | [[00_meta/03_EvaluatorRecipe]] §1.5 | generator verify 결과 *재검증* (Article 1 self-eval bias 회피) |
| **§3.5** | Phase 1 evaluator (handoff document) | handoff 작성 시 | [[00_meta/08_VaultScopePolicy]] §3.5 | UPROPERTY 타입 Critical 30 감점 |

→ 4 단계 verify 로 Compile blocker 영구 차단.

## 5. 7 항목 verify (A~G) — 권위 source

🟢 모든 인용 = `outputs/cycle-5p-handoff/06_engine_grep_evidence.md` (Phase 2 evaluator 가 verify 한 11 Engine 라인):

| 항목 | 권위 Engine 파일:라인 |
| -- | -- |
| A. UPROPERTY templated container | `MovieSceneFrameMigration.h L26-104` (FMovieSceneFrameRange 5 트레잇) + `MovieSceneSection.h L787-788` (UPROPERTY USTRUCT 래퍼) |
| B. TArray cross-type explicit ctor | `Containers/Array.h L745-755` |
| C. TObjectPtr `.Get()` 변환 | (관습) |
| D. bitfield UPROPERTY | `MovieSceneSection.h L820, L824` (`uint32 :1`) + `BodyInstanceCore.h L38-59` (`uint8 :1` 4건, BlueprintReadOnly 호환) |
| E. DEPRECATED `_DEPRECATED` 접미사 | `CoreUObject/Private/UObject/Class.cpp L1690-1760` (brute force search) + `MovieSceneSection.h L834-848` (StartTime_DEPRECATED 사례) |
| F. Custom Serialize trait | `MovieSceneFrameMigration.h L107-110` (TStructOpsTypeTraits 5 트레잇) |
| G. Slate API 시그니처 | `SlateCore/Public/Input/CursorReply.h L33` (FCursorReply) + `ApplicationCore/Public/GenericPlatform/ICursor.h L17-60` (EMouseCursor) |
| 보너스 | `Renderer/Private/SlateRendering/ElementBatcher.cpp L1783-1788` (Orient_Vertical) + `Animation/AnimInstance.h L437/442/605/1619` (SlotName 1급 식별자) |

## 6. 정책 변경 — auto-evaluator 호출 제거 (Cycle 5p 정책)

🚨 **중요 정책 변경** — Cycle 5p 진행 중 사용자가 결정:

| 항목 | Before | After |
| -- | -- | -- |
| 자동 evaluator 호출 (specialist → evaluator post-write hook) | 의무 | **제거** |
| evaluator agent 자체 (`raw/ue-wiki-llm/agents/ue-evaluator.md`) | (활성) | **유지** — 사용자 수동 호출 시만 |
| 사유 | — | 평가 체크 시 timeout 심각 (실측: evaluator 89~193s per call) |

→ Cycle 5p 의 4 patch 는 모두 "사용자 수동 호출 시 적용" framing 으로 작성. Cycle 5p+1 후보 = auto-evaluator 호출 제거 patch (11 specialist .md + 4 meta + 2 catalog 추가 갱신).

## 7. 검증 결과 (mcwiki MCP)

🟢 **lint**: 394 pages, **0 issues**

🟢 **find_cross_link_broken** (Cycle 5p 편집 페이지):
- `00_meta/08_VaultScopePolicy`: 13 wikilinks / **0 broken**
- `00_meta/03_EvaluatorRecipe`: 3 wikilinks / **0 broken**
- `00_meta/07_AgentBoundaryProtocol`: 11 wikilinks / **1 broken** (pre-existing — `entities/IMainFrameModule` L39 §1.2 예시)

⚠ **tool 한계 (Cycle 5p+1 후보)**:
- `find_claim_conflict` + `find_stale_baseline` + `suggest_missing_cross_link` — `00_meta` kind 정규화 오류 (`wiki/meta/` 로 검색 시도 → 미존재)
- v0.5.1 에서 alias 부분 해결, 일부 도구 잔여 — Cycle 5p+1 도구 patch 필요

## 8. Cycle 5p+1 후보 풀 — 진척 상태

✅ **완료 (Cycle 5p+1, 2026-05-17)**:

1. ✅ **A — auto-evaluator 호출 제거 patch** — 11 specialist .md `작업 패턴` ue-evaluator 호출 라인 + 14 .md governance §8.4 row #4 + orchestrator 6 references + wiki-maintainer 2 references + evaluator self frontmatter/8단계 모두 user-triggered framing 갱신
2. ✅ **B — vault catalog sync (2 메타)** — sources/ue-agent-evaluator + sources/ue-agent-orchestrator (Cycle 5p §1.5 Stage 2.X / §2.5 Pre-Flight + Cycle 5p+1 auto-evaluator 제거 통합)
3. ✅ **C — mcwiki 도구 `00_meta` alias fix** — find_claim_conflict / find_stale_baseline / suggest_missing_cross_link 의 `_kind_root()` helper 추가 (find_cross_link_broken.py 패턴 미러). Python 직접 검증: 2/3 도구 (find_stale + suggest_missing) PASS, find_claim_conflict bash mount sync 지연으로 직접 검증 불가 (file 측 적용 완료). MCP server 재시작 후 효과 발휘.
4. ✅ **D — entities/IMainFrameModule 신규 (stub)** — `wiki/entities/IMainFrameModule.md` 신규 (2337 bytes). 07_AgentBoundaryProtocol §1.2 broken link 해소 → 1 broken → **0 broken**. index Entities 79 → 80 / Editor 8 → 9.

❌ **폐기 (사용자 결정)**:

5. ❌ ~~**KMCProject Phase 1 evaluator 재평가** — `[[synthesis/mc-combo-section-levelsequence-style-upgrade]]` (89.10 → ?)~~ — 사용자 결정: 본 항목 폐기.

🟡 **이월 (Cycle 5p+2)**:

6. 🟡 **3중 verify 실측** — 다음 multi-step KMCProject 작업에서 Cycle 5p 4 patch + Cycle 5p+1 A/B/C/D 효과 측정 (refactor 0회 + 시간 ~37% 단축 검증). 측정 가능 작업 미수행 — 자연 발생 시 측정.

추가 후속 (Cycle 5p+2 신규 후보):

7. 🟡 **11 specialist catalog sync** (Cycle 5p+1 B variant) — 각 sources/ue-agent-{asset,components,slate-umg,...} 11종 catalog 에 Cycle 5p §pre-write 1단계 cross-link
8. 🟡 **entities/IMainFrameModule 정밀 enrich** (stub → 정밀) — Engine 본가 `IMainFrameModule.h` grep 검증 의무 + §pre-write 1단계 적용
9. 🟡 **find_claim_conflict bash mount sync 검증** — MCP server 재시작 후 직접 호출 verify

## 9. cross-link

### Governance (00_meta)
- [[00_meta/00_QualityCriteria]] · [[00_meta/03_EvaluatorRecipe]] §1.5 (Cycle 5p) · [[00_meta/05_HandoffProtocol]]
- [[00_meta/06_VaultCitationRule]] · [[00_meta/07_AgentBoundaryProtocol]] §2.5 (Cycle 5p) · [[00_meta/08_VaultScopePolicy]] §3.5 (Cycle 5p)

### Baseline Grep 시스템 (페어)
- [[sources/ue-meta-baseline-grep-system]] — specialist 측 § patch 명세 (Cycle 5h #4)

### Agent vault catalog
- [[sources/ue-agent-evaluator]] — §Stage 2.X 도입 (catalog sync 후속 후보)
- [[sources/ue-agent-orchestrator]] — §Pre-Flight 도입 (catalog sync 후속 후보)
- 11 specialist catalog — `sources/ue-agent-{asset,components,slate-umg,animation,gameframework,input,render,plugin,editor,spatial-partition,levelsequence}` (catalog sync 후속 후보)

### postmortem source
- `outputs/cycle-5p-handoff/00_README.md` — 마스터 진입점
- `outputs/cycle-5p-handoff/01_timing_analysis.md` — 11 Agent 호출 duration_ms 실측
- `outputs/cycle-5p-handoff/02_remediation_specialist_prompts.md` — specialist patch 명세
- `outputs/cycle-5p-handoff/03_remediation_synthesis_policy.md` — 00_meta/08 patch 명세
- `outputs/cycle-5p-handoff/04_remediation_evaluator_stage2.md` — 00_meta/03 patch 명세
- `outputs/cycle-5p-handoff/05_remediation_orchestrator_preflight.md` — 00_meta/07 patch 명세
- `outputs/cycle-5p-handoff/06_engine_grep_evidence.md` — 11 권위 인용

## 10. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-17 (Cycle 5p) | 최초 작성. KMCProject Phase 2 postmortem (`outputs/cycle-5p-handoff/`) 기반 4 patch (a/b/c/d) 적용 완료의 vault 측 페어 synthesis. 3중 verify 구조 (Generator §pre-write + Evaluator §Stage 2.X + Orchestrator §Pre-Flight) + auto-evaluator 호출 제거 정책 + Cycle 5p+1 후보 6건. |
| **2026-05-17 (Cycle 5p+1)** | **§8 후보 풀 4건 완료 (A/B/C/D)** — auto-evaluator 호출 제거 patch + vault catalog sync (2 메타) + mcwiki 도구 `00_meta` alias fix (3 도구) + entities/IMainFrameModule 신규 (07 §1.2 broken link 해소). 후보 #5 (mc-combo-section 재평가) **폐기** (사용자 결정). 후보 #6 (3중 verify 실측) 이월. Cycle 5p+2 신규 후보 3건 추가. lint **396 pages, 0 issues** ✅. |
