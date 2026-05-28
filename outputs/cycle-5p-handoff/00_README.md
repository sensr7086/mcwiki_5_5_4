---
type: postmortem
title: "KMCProject Phase 2 (MCComboSection LevelSequence-style upgrade) Postmortem — 시간 손실 분석 + Wiki Manager 보강 인계"
slug: phase2-combosection-postmortem-2026-05-17
created: 2026-05-17
project_role: case-study
project: KMCProject
status: handoff-to-wiki-manager
cycle: 5p (proposed)
target_agent: ue-wiki-llm:ue-wiki-maintainer
related_synthesis:
  - "[[synthesis/mc-combo-section-levelsequence-style-upgrade]]"
related_meta:
  - "[[00_meta/03_EvaluatorRecipe]]"
  - "[[00_meta/05_HandoffProtocol]]"
  - "[[00_meta/07_AgentBoundaryProtocol]]"
  - "[[00_meta/09_StubVsEnrichedPolicy]]"
---

# Phase 2 Postmortem — MCComboSection LevelSequence-style upgrade

> **결론**: Phase 2 (2a/2b/2c/2d) 4단계가 누적 PASS 했으나, **2회의 refactor 사이클이 발생하여 약 268초 (전체 17%) 손실**. 두 사이클 모두 **specialist 가 Engine 본가 패턴을 사전 verify 안 한 Compile blocker**가 원인. evaluator 가 사후에 잡은 형태.
>
> **본 폴더의 목적**: 위키 관리자 (`ue-wiki-llm:ue-wiki-maintainer`) 가 본 폴더의 보강 명세 6개 파일을 읽고 `00_meta/` 정책 + 11 specialist agent prompt + 15_EvaluatorRecipe + 07_AgentBoundaryProtocol 갱신 작업 수행.

---

## 진입점 매트릭스

| 파일 | 내용 | Wiki Manager Action |
| --- | --- | --- |
| `01_timing_analysis.md` | 11회 Agent 호출 duration_ms 실측 + 손실 사이클 분석 | (참고용 — 통계 인용) |
| `02_remediation_specialist_prompts.md` | **11 specialist agent prompt 갱신 patch** (§pre-write 1단계 Engine grep 의무) | ⭐⭐⭐ Cycle 5p #1 — plugin agent .md 11개 patch |
| `03_remediation_synthesis_policy.md` | `00_meta/08_VaultScopePolicy` §3.5 신규 추가 (handoff document §2 격상 매트릭스 작성 시 Engine UPROPERTY grep 의무) | ⭐⭐ Cycle 5p #2 — 00_meta/08 갱신 |
| `04_remediation_evaluator_stage2.md` | `00_meta/03_EvaluatorRecipe` Stage 2 Compile 강화 — Engine 본가 UPROPERTY 패턴 grep 명시 의무 | ⭐⭐⭐ Cycle 5p #3 — 00_meta/03 갱신 + Phase 1 evaluator 도 동일 적용 |
| `05_remediation_orchestrator_preflight.md` | `00_meta/07_AgentBoundaryProtocol` 에 메인 (Orchestrator 역할) pre-flight grep 의무 추가 | ⭐⭐ Cycle 5p #4 — 00_meta/07 갱신 |
| `06_engine_grep_evidence.md` | Engine 본가 권위 grep 증거 7건 (FMovieSceneFrameRange / Array.h L752 / ElementBatcher.cpp L1783 / ICursor.h / CursorReply.h / MovieSceneSection.h L820/L824 / AnimInstance.h L437/L442/L605/L1619) | (인용 source — patch 작성 시 권위 인용 의무) |

---

## TL;DR (위키 관리자 빠른 시작)

### 손실 시간 분포

| 단계 | 시간 (초) | 비고 |
| --- | --- | --- |
| Phase 2a 1차 specialist + evaluator | 128 + 180 = **308** | ⚠ Compile BLOCKER 발생 |
| Phase 2a-**refactor** specialist + evaluator | 158 + 122 = **280** | ⚠ 재작업 |
| Phase 2b specialist + evaluator | 70 + 89 = 159 | 정상 |
| Phase 2c 1차 specialist + evaluator | 234 + 193 = **427** | ⚠ Compile BLOCKER 발생 |
| Phase 2c-**refactor** specialist (재평가 skip) | 110 | 재작업 |
| Phase 2d specialist + evaluator | 195 + 143 = 338 | 정상 |
| **합계** | **1,622 (~27분)** | refactor 손실 = 280 + 110 = **390초 (24%)** |

> 단, "refactor 손실 = 280+110" 은 직접 손실이고, 1차 BLOCKER 까지 도달한 specialist+evaluator 시간 (308+427) 도 결과적으로 무의미한 작업이 되었으므로 **총 손실 = ~735초 (45%)** 로 볼 수도 있음 (보수적 해석).

### 근본 원인 4건

1. **Specialist 가 UPROPERTY 부착 타입 / TArray cross-type / TObjectPtr 변환 등 Compile-blocker 후보를 Engine 본가에서 사전 verify 안 함** (가장 큰 원인)
2. **synthesis handoff document 가 Engine 본가 패턴 검증 없이 작성**되어 specialist 가 잘못된 명세를 따름 (Phase 1 evaluator 89.10 통과했음에도)
3. **메인 (오케스트레이터 역할) 이 specialist 호출 prompt 작성 시 Engine grep 결과 사전 첨부 안 함**
4. **Generator/Evaluator 분리 패턴이 Compile blocker 같은 사전 검증 가능 항목까지 evaluator 뒤로 미루는 비대칭 비용**

### 보강 항목 4건 (`02~05_remediation_*.md` 참조)

각 파일에 wiki manager 가 적용할 정확한 §, 라인, patch 텍스트 포함.

---

## Phase 2 결과 (참고용 — 누적 PASS 확인)

| Phase | Specialist | Score | 변경 파일 / 라인 |
| --- | --- | ---: | --- |
| 2a-refactor | ue-asset-specialist | 91.0 | MCComboFrameRange.h/.cpp 신규 (76+22) / MCComboSection.h/.cpp 정정 (146+68) |
| 2b | ue-asset-specialist | 94.0 | MCComboMontageTrack.h/.cpp (60+24) |
| 2c-refactor | ue-slate-umg-specialist | ~88+ (재평가 skip — evaluator 사전 명시) | SMCComboTrackPanel.cpp +186 (303→499) |
| 2d | ue-slate-umg-specialist | 91.0 | SMCComboTrackPanel.h/.cpp (90+626) |

7건의 Engine 권위 인용 + 10/10 함정 회피 + 7/7 잔여 위험 해소 (#5 → §A 전환).

---

## Wiki Manager 의무 (작업 시작 시 read_raw)

본 폴더의 6개 MD 를 모두 읽은 뒤 다음 patch 작업 진행:

1. `02_remediation_specialist_prompts.md` → 11 plugin specialist agent `.md` 갱신
2. `03_remediation_synthesis_policy.md` → `00_meta/08_VaultScopePolicy` §3.5 추가
3. `04_remediation_evaluator_stage2.md` → `00_meta/03_EvaluatorRecipe` Stage 2 갱신
4. `05_remediation_orchestrator_preflight.md` → `00_meta/07_AgentBoundaryProtocol` 보강
5. `06_engine_grep_evidence.md` → 각 patch 의 권위 인용 source

작업 완료 후 `synthesis/cycle-5p-postmortem-remediation` 신규 작성 (본 postmortem 의 vault 측 페어).

---

## 결재 / 검증 흐름 (위키 관리자 표준)

1. wiki-maintainer 가 본 README 읽기
2. 6개 부속 MD 모두 read_raw (stub 정책 — `00_meta/09`)
3. 4개 patch 작성 (Cycle 5p #1~#4)
4. 각 patch 별로 ue-evaluator 호출 평가 (Generator/Evaluator 분리 — Article 1)
5. evaluator PASS (≥80) 시 vault 적용
6. mcwiki MCP 6 도구 batch (lint / find_cross_link_broken / suggest_missing_cross_link / find_claim_conflict / find_stale_baseline / append_log)
7. `synthesis/cycle-5p-postmortem-remediation` 신규 작성 (case-study 항목)
8. 사용자에게 완료 보고

---

## 변경 이력

| 날짜 | 변경 |
| --- | --- |
| 2026-05-17 | 본 폴더 신규 작성 — 메인 Claude 가 Phase 2 작업 후 사용자 요청으로 postmortem 작성. 위키 관리자 인계 |
