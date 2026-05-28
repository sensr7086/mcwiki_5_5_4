---
type: source
title: "UE meta — improvement-roadmap (vault 한계 해결 trajectory)"
slug: ue-meta-improvement-roadmap
source_path: raw/ue-wiki-llm/meta/improvement-roadmap.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-28
audit_5_5_4: pass-cosmetic  # 2026-05-28 Phase 2-B auto-classified
tags: [ue, meta, roadmap, p0-p3-priority, vault-evolution, cycle-5e-candidates]
citation_disclosure: "본 카드 = 🟢 vault 직시 (Cycle 5a~5d 진화 + 21건 보강 + 6건 정정 모두 vault 안 페이지 / log.md 로 검증 가능). raw 원본 slim → vault-side 정밀 mirror. P0-P3 매트릭스 = vault 한계 6대 (honest-limits §1) 에 대한 점진적 해결안. Cycle 5e 후보 풀 = Cycle 5d 1차 + 2차 후 남은 미진행 항목."
---

# UE meta — improvement-roadmap (vault 한계 해결 trajectory)

> Source: [[raw/ue-wiki-llm/meta/improvement-roadmap.md]]
>
> 보강 2026-05-15 (Cycle 5d 2차) — slim card → 정밀 enrich. raw 의 "P0-P3 우선순위" 를 vault Phase 1~10 + Cycle 1~5d 진화 안에서 발견한 해결안 매트릭스 + Cycle 5e 후보 풀 + Phase II 게이트 PASS 후속 절차로 정밀화.

## 1. Summary

UE LLM Wiki 의 한계 해결 방안 매트릭스 — **P0~P3 우선순위**. [[sources/ue-meta-honest-limits]] §1 의 6 대 본질 문제에 대한 점진적 개선안. 2026-05-09 raw 카드의 추상 매트릭스를 Cycle 1~5d 진화 안 실측 사례로 정밀화 + 향후 Cycle 5e~5f 후보 풀 명시.

## 2. P0~P3 우선순위 매트릭스 (정밀판)

### 2.1 P0 (즉시 해결 의무 — 완료) ✅

| # | 한계 (honest-limits §1) | 해결 방안 | 진행 |
| -- | -- | -- | -- |
| P0.1 | vault 자체 진단 실패 (PI 매크로 사례) | [[sources/ue-coreuobject-uobject]] §2.12 + §2.12.7 자체 평가 정정 | ✅ Cycle 5c 2026-05-14 |
| P0.2 | vault 평가자가 vault 함정을 권고 | [[sources/ue-agent-evaluator]] §3 self-correction 의무 | ✅ Cycle 5b 2026-05-12 |
| P0.3 | 6대 본질 문제 명시 누락 | [[sources/ue-meta-honest-limits]] §2 Self-eval bias 신규 | ✅ Cycle 5c 2026-05-12 |
| P0.4 | 함정 카탈로그 미통합 (KMCProject 9건 산발) | [[sources/ue-coreuobject-uobject]] §4 11대 통합 매트릭스 | ✅ Cycle 5a~5d (9→11) |

### 2.2 P1 (분기 audit 의무 — 진행 중) ⏳

| # | 한계 | 해결 방안 | 진행 |
| -- | -- | -- | -- |
| P1.1 | KMCProject 외 검증 사이트 비율 < 50% | UE Engine grep 재현 검증 의무 (§2.11.1 패턴) | ⏳ Cycle 5d 2차 완료 (§2.11.1 = 1 건 격상) — 65% 도달 |
| P1.2 | `[inferred]` / 🔴 INFERRED 항목 누적 | corrections.md 정정 절차 표준화 | ✅ Cycle 5d 2차 corrections §3 신규 |
| P1.3 | sub-skill 라이프사이클 미명시 | governance §3 5상태 표준 | ✅ Cycle 5d 2차 governance §3 신규 |
| P1.4 | UE 마이너 업그레이드 절차 미명시 | governance §5.2 + ref-00-readme §8.2 | ✅ Cycle 5d 2차 |

### 2.3 P2 (장기 enrich — 대기) 🕐

| # | 한계 | 해결 방안 | 진행 |
| -- | -- | -- | -- |
| P2.1 | cross-platform 커버리지 ≠ 100% (Mobile / VR / Console 일부 외삽) | Mobile / VR / Console 측정 사이트 확보 — 외부 검증 의존 | 🕐 대기 (외부 의존) |
| P2.2 | 비-UE 콘텐츠 (Anthropic SDK / 외부 패키지) 0% | 별도 vault 분리 권장 (UE 도메인 단일) | 🕐 (의도된 한계) |
| P2.3 | 5.7.4 만 검증 — 다른 마이너 외삽 | 분기 audit 시 UE 새 마이너 검증 (Q3 ~ Q4 예정) | 🕐 분기 일정 |
| P2.4 | raw/ ingest = 2026-05-09 스냅샷 — 그 이후 미반영 | 분기 audit 시 재ingest | 🕐 Q2 2026 audit 일정 |

### 2.4 P3 (탐색 후보 — 미확정) 🔍

| # | 후보 | 비고 |
| -- | -- | -- |
| P3.1 | IWYU (`include-what-you-use`) 자동 검출 통합 | uobject §2.13 cpp include 누락 자동 검출 |
| P3.2 | clang-tidy 정적 분석 룰 통합 | uobject §2.12 글로벌 매크로 식별자 / §2.10 const propagation 자동 검출 |
| P3.3 | LLM 자체 평가의 calibration 측정 | [[sources/ue-measure-summary]] 의 H1~H3 측정 (현재 ⭐⭐ 1건만 정밀) |
| P3.4 | KMCProject 외 vault testbed 확보 | 다른 UE 프로젝트의 vault 활용 + 정정 catalog 합류 |

## 3. Cycle 5e 후보 풀 (2026-05-15 Cycle 5d 2차 종료 시점)

Cycle 5d 1차 / 2차 미진행 항목 + 신규 발견 후보. 사용자 결정 단계.

### 3.1 기존 Cycle 5d 풀 잔여 (3건) 🕐

| # | 항목 | 사유 | 권장 Cycle |
| -- | -- | -- | -- |
| 2 | `ue-ref-deep-*` 5종 검토 | 단순 검토 (작성 없음) — ue-audit-agent 별도 호출 영역 | 5e (검토) |
| 4 | `ue-animation-animnotify` Phase 3 OnHitReceived | KMCProject Phase 3 코드 보류 — 코드 진행 후 enrich | 5f (대기 — KMCProject 의존) |
| 6 | `FBlueprintEditorModule::OnRegisterTabs` 검증 | UE Engine grep 필요 — Cycle 5e 별도 진행 권장 | 5e |

### 3.2 Cycle 5d 후속 신규 후보 (3건) 🕐

| # | 항목 | trigger | 권장 Cycle |
| -- | -- | -- | -- |
| 7 | `MCComboEditor` Phase 2 — `SMCComboPreviewViewport` AdvancedPreviewScene 통합 시 | KMCProject MCComboEditor Phase 2 진행 | 5f (대기 — KMCProject Phase 2 진행 후) |
| 8 | `UMCTimelineAsset` 추상 베이스 추출 | 4 자산 공통 인터페이스 분리 (Combo / Dialogue / Cutscene-lite 등 차용 trigger 시) | 5f (대기 — 차용 trigger) |
| 9 | cpp include 누락 IWYU 자동 검출 | [[synthesis/validation-static-analysis-ide-integration]] 통합 검토 | 5e (검토) — P3.1 페어 |

### 3.3 Cycle 5d 2차 종료 후 신규 발견 후보 (3건) 🕐

| # | 항목 | trigger | 권장 Cycle |
| -- | -- | -- | -- |
| 10 | §2.11.1.4 NotifyHook / Delegate 등 다른 array-element-pointer 시스템 동일 함정 catalog | §2.11.1.4 🟡 외삽 검증 의무 | 5e (grep 검증) |
| 11 | `ue-editor-assettools` §2.6.1 FText 두 번째 호출 무시 가설 | corrections §2.5 — vault grep 실측 미완료 | 5e (검증) |
| 12 | 9 specialist 의 vault 페어 페이지 baseline grep 시스템화 | evaluator self-correction 의무 (governance §4.1) 의 자동화 | 5f (도구 작성 — mcwiki MCP 신규) |

## 4. Cycle 5d 2차 진척 (2026-05-15)

본 Cycle 5d 2차 작업으로 P0/P1 카테고리 일부 진행:

### 4.1 진행 항목

| 항목 | 갱신 페이지 | tier |
| -- | -- | -- |
| ref-00-readme 정밀 enrich | [[sources/ue-ref-00-readme]] | slim card → 정밀 |
| meta 5종 정밀 enrich | [[sources/ue-meta-confidence-tags]] / [[sources/ue-meta-corrections]] / [[sources/ue-meta-governance]] / [[sources/ue-meta-improvement-roadmap]] (본 페이지) / [[sources/ue-meta-honest-limits]] (기존 정밀 유지) | 4 신규 정밀 + 1 갱신 |
| uobject §2.11 후속 검증 | [[sources/ue-coreuobject-uobject]] §2.11.1 | 🟡 single-case → 🟢 일반 패턴 |

### 4.2 Cycle 5d 2차 평가 점수 (목표)

각 페이지 evaluator 8단계 회의적 평가 — 4종 가중 100점 (목표 ≥ 80):

| 페이지 | 목표 점수 |
| -- | -- |
| ue-ref-00-readme | ≥ 85 (정밀 enrich) |
| ue-meta-confidence-tags | ≥ 85 |
| ue-meta-corrections | ≥ 85 |
| ue-meta-governance | ≥ 85 |
| ue-meta-improvement-roadmap (본) | ≥ 85 |
| ue-meta-honest-limits | (기존 점수 유지) |
| ue-coreuobject-uobject §2.11.1 | ≥ 88 (격상 — UE Engine 검증 사이트 확보) |

## 5. Phase II 게이트 PASS 후속 절차

상세 = [[00_meta/07_AgentBoundaryProtocol]] (main ↔ specialist boundary 5 단계 + Phase II orchestrator MCP 권한 점진).

### 5.1 현재 상태 (2026-05-15)

- §5.4 G2 게이트: **PASS** (10/10) — Cycle 5b 시점
- §5.4 G3 게이트: 진행 중 — agents raw 15 / plugin 활성 13 동기화 작업 미완료

### 5.2 Cycle 5e+ 게이트 후보

| 게이트 | 조건 | 진행 |
| -- | -- | -- |
| G3 | agents 15 = plugin 활성 13 → 15 동기화 | ⏳ LevelSequence Cycle #12 agent + SpatialPartition Cycle #11 agent plugin 등록 |
| G4 | KMCProject 외 vault testbed 1건 이상 합류 | 🕐 P3.4 후보 |
| G5 | 분기 audit Q2 2026 PASS | 🕐 분기 일정 |

→ 게이트 PASS 시 main orchestrator 의 MCP 권한 점진 (mcwiki 전체 도구 → 외부 도구 확장 + 외부 agent 자동 호출).

## 6. ⚠ 본 roadmap 의 한계

- **자기참조성** — 본 roadmap 의 진행 평가는 vault 자체가 판단 (self-eval bias 위험)
- 완화 방안 — 분기 audit 시 ue-agent-audit 가 독립 검증 + corrections.md 정정 catalog 가 입력

## 7. Cross-link

### 페어 (의무 Read)

- [[sources/ue-meta-honest-limits]] §1 — 6대 한계 (본 §2 P0~P3 의 입력)
- [[sources/ue-meta-corrections]] — 정정 누적 (P1 검증 trail)
- [[sources/ue-meta-confidence-tags]] — 3 tier (P1.2 격상 / 강등 권위)
- [[sources/ue-meta-governance]] — 거버넌스 마스터 (P0~P3 의 운영 권위)

### 운영 메타 + references

- [[00_meta/04_AuditPolicy]] (P2/P3 분기 일정 권위)
- [[00_meta/07_AgentBoundaryProtocol]] (§5 권위)
- [[sources/ue-ref-18-modelevolutionaudit]] (분기 audit 표준)

### Cycle 5e 권위

- [[sources/ue-coreuobject-uobject]] §2.11.1 (P1.1 격상 사례)
- [[sources/ue-editor-asseteditorapi]] §11.4 (§3.1 #6 BlueprintEditor OnRegisterTabs 후보 출처)

## 8. Changelog

| 날짜 | 변경 |
| -- | -- |
| 2026-05-09 | 카드 작성 (raw ingest, slim) |
| **2026-05-15 (Cycle 5d 2차)** | **정밀 enrich** — §2 P0~P3 우선순위 매트릭스 (P0 4건 완료 / P1 4건 진행 중 / P2 4건 대기 / P3 4건 탐색) + §3 Cycle 5e 후보 풀 9건 (기존 3 + Cycle 5d 후속 3 + Cycle 5d 2차 종료 후 신규 3) + §4 Cycle 5d 2차 진척 (7 페이지 정밀 enrich + uobject §2.11.1 격상) + §5 Phase II 게이트 PASS 후속 절차 (G3~G5) + §6 본 roadmap 자기참조성 한계 + §7 Cross-link 4 권위. raw slim → vault-side 정밀 mirror. 🟢 vault 직시 (모든 P0~P1 진행이 vault 내 페이지 진화 + log.md entry 로 검증 가능). |
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 mostly-cosmetic**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **mostly-cosmetic**. 5.5↔5.7 raw diff 가 대부분 cosmetic (whitespace / formatting) + 소수 (≤2) 의미 변경 — 본문 본질 안정.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
