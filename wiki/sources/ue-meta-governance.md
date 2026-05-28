---
type: source
title: "UE meta — CLAUDE-wiki-governance (거버넌스 마스터)"
slug: ue-meta-governance
source_path: raw/ue-wiki-llm/meta/CLAUDE-wiki-governance.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-15
tags: [ue, meta, governance, wiki-governance, sub-skill-standard, lifecycle, generator-evaluator, model-evolution, vault-side-mirror]
citation_disclosure: "본 카드 = 🟢 vault 직시 (5단 의무 / 라이프사이클 / Generator-Evaluator 분리 / 모델 진화 대응 모두 vault 안 [[00_meta/03_EvaluatorRecipe]] + [[00_meta/04_AuditPolicy]] + [[00_meta/07_AgentBoundaryProtocol]] + Cycle 5a~5d 실측 사례로 검증 가능). raw 원본 slim → vault-side 정밀 mirror."
---

# UE meta — CLAUDE-wiki-governance (거버넌스 마스터)

> Source: [[raw/ue-wiki-llm/meta/CLAUDE-wiki-governance.md]]
>
> 보강 2026-05-15 (Cycle 5d 2차) — slim card → 정밀 enrich. raw `CLAUDE-wiki-governance.md` 의 5단 의무 + 라이프사이클 + 모델 진화 대응 + Generator-Evaluator 분리를 vault-side mirror 로 정밀화. UE 도메인 측 마스터 거버넌스 (KMCProject CLAUDE.md §13 페어).

## 1. Summary

UE LLM Wiki 거버넌스 마스터 — **sub-skill 작성 5단 의무** + **라이프사이클 5상태** (Draft → Verified → Live → Stale → Deprecated) + **모델 진화 대응** + **측정 가능한 품질 기준** + **Generator-Evaluator 분리** (Article 1). 본 vault 의 CLAUDE.md 와 페어 (UE 도메인 측 — sub-skill / source / synthesis 작성 표준). Cycle 1~5d 안 11대 함정 카탈로그 + 21건 vault 보강 / 6건 정정의 운영 권위.

## 2. 5단 의무 (각 페이지 작성)

[[00_meta/03_EvaluatorRecipe]] / [[00_meta/05_HandoffProtocol]] / [[00_meta/06_VaultCitationRule]] 정밀판의 통합 카드.

| 단계 | 의무 | 검증 도구 | 권위 |
| -- | -- | -- | -- |
| **1. Frontmatter** | 4줄 의무 (`type` / `title` / `slug` + `last_updated` + `tags` + `citation_disclosure` + `related_concepts`) | mcwiki:lint (FRONTMATTER_MISSING / SLUG_MISMATCH) | [[00_meta/02_FrontmatterStandard]] |
| **2. Quality (🟢/🟡/🔴 3 tier)** | 매 사실 주장 tier 명시 + 검증 출처 | mcwiki:lint (CITATION_DISCLOSURE 의무) | [[00_meta/06_VaultCitationRule]] + [[sources/ue-meta-confidence-tags]] |
| **3. Handoff (Cross-link)** | 페어 / 권위 / 함정 카탈로그 / fix log 4 section 의무 | mcwiki:lint (BROKEN_LINK / ORPHAN) | [[00_meta/05_HandoffProtocol]] + [[sources/ue-ref-14-taskhandofftemplate]] |
| **4. Evaluator (8단계)** | 작성 직후 `ue-agent-evaluator` Task tool 호출 — 4종 가중 100점 채점 | Task tool ue-evaluator | [[00_meta/03_EvaluatorRecipe]] + [[sources/ue-ref-15-evaluatorrecipe]] |
| **5. Audit** | `last_updated` 갱신 + `wiki/log.md` append_log + 분기 audit 등록 | mcwiki:append_log | [[00_meta/04_AuditPolicy]] + [[sources/ue-ref-18-modelevolutionaudit]] |

🚨 모든 단계 의무. 5단 중 하나라도 누락 시 페이지는 *vault 자산이 아닌 외삽* (🔴 INFERRED) 으로 격하.

## 3. 라이프사이클 (5 상태)

```text
[Draft]
  │  사용자 / agent 가 신규 작성 시작
  │  frontmatter 4줄 명시 의무
  │  citation_disclosure 없음 = Draft 유지
  ▼
[Verified]
  │  5단 의무 4단 완료 (Frontmatter + Quality + Handoff + Evaluator)
  │  evaluator 점수 ≥ 70 PASS
  │  ⚠ 점수 < 70 → Draft 강등
  ▼
[Live]
  │  사용자 / specialist 가 page 활용 (read_page / search 매치)
  │  cross-link 다른 페이지에서 인용
  │  filing-back 입력
  ▼
[Stale] (>90 days no update)
  │  분기 audit 검증 대상
  │  audit 통과 → Live 유지
  │  audit 실패 → 보강 의무 (또는 Deprecate 검토)
  ▼
[Deprecated]
  │  UE 마이너 업그레이드로 시그니처 변경 + 검증 불가
  │  또는 corrections 누적 후 정정 불가
  │  새 페이지로 마이그레이션 + frontmatter `deprecated: true`
```

→ 현재 vault 통계 (2026-05-15 Cycle 5d 2차): **stale (>90d): 0** / **deprecated: 0** — 모두 Live 상태 유지. 5단 의무 + 분기 audit 의 효과.

## 4. Generator-Evaluator 분리 (Article 1)

🚨 **Self-eval bias 회피의 핵심 메커니즘**. 상세 = [[sources/ue-meta-honest-limits]] §2.

### 4.1 의무

| 역할 | 누가 | 의무 |
| -- | -- | -- |
| **Generator** | sub-skill 작성자 / specialist (ue-agent-*) | 코드 / 페이지 작성 — 자체 평가 금지 |
| **Evaluator** | ue-agent-evaluator (별도 세션) | 회의적 평가만 — 코드 수정 금지 |

**최소 의무** — Generator 와 Evaluator 가 같은 세션이라도 *명시적으로 분리 호출* (`Task tool`). evaluator 가 vault 페어 페이지 baseline grep 의무 (예: `IDetailCustomization` 자손 권고 시 `[[sources/ue-editor-propertyeditor]] §2.6.9` 함정 9 검증).

### 4.2 실패 사례 (Cycle 5d 2차 시점, 2건)

**사례 1** ([[sources/ue-meta-honest-limits]] §2.1) — vault 평가자가 vault 함정을 권고 (2026-05-12):
- 외부 에이전트가 `IDetailCustomization` 자손 작성
- vault 평가자 86/100 + Major 권고: "`TSharedFromThis` 상속 추가"
- 외부 에이전트 반영 → **C2385 다이아몬드 상속** (`ue-editor-propertyeditor §2.6.9` 함정 9 그대로)
- 즉 vault 두 페이지가 모순 — 평가자 카드와 함정 9 카드

**사례 2** ([[sources/ue-meta-corrections]] §2.4) — vault 자체 2회 잘못된 진단 (2026-05-14):
- 1차 진단 "ToolMenus include path" — 잘못
- 2차 진단 "UCLASS MinimalAPI 외부 모듈 막힘" — 잘못
- 사용자 root cause 발견 (PI 매크로)

### 4.3 filing-back (2건 모두 완료)

- 사례 1 → [[sources/ue-agent-evaluator]] §3 self-correction 의무 신규 (권고 전 baseline grep 3단)
- 사례 2 → [[sources/ue-coreuobject-uobject]] §2.12.7 자체 평가 정정 + 진단 가이드 신규

## 5. 모델 진화 대응

상세 = [[sources/ue-ref-18-modelevolutionaudit]] + [[00_meta/04_AuditPolicy]].

### 5.1 Anthropic 모델 변경 시 (분기 audit)

| Quarter | 주체 | 작업 |
| -- | -- | -- |
| Q 시작 | ue-agent-audit | vault 전체 일관성 audit (lint / stats / wikilink-graph) |
| Q 시작 | ue-agent-audit | stale > 90 days 페이지 식별 (현재 0) |
| Q 시작 | sub-skill specialist | 새 모델 호환성 검증 (핵심 페이지 10건 read + 평가) |
| Q 진행 | ue-agent-wiki-maintainer | 검증 실패 페이지 보강 (deprecate 금지 — Live 유지 의무) |
| Q 종료 | ue-agent-audit | corrections.md 정정 5건 통계 + filing-back 매트릭스 |

### 5.2 UE 마이너 업그레이드 (5.7.x → 5.7.y / 5.7 → 5.8)

| 작업 | 영향 페이지 | 검증 의무 |
| -- | -- | -- |
| `raw/ue-wiki-llm/` 재ingest | sources/ 의 모든 source_path | 라인 번호 갱신 |
| entities/ 시그니처 검증 | 79 entities | 클래스 / virtual 매트릭스 grep |
| concepts/ 횡단 정책 audit | 46 concepts (의무 5종 포함) | Asset Loading / Iterator / Profiling 등 |
| synthesis/ broken-link 검증 | 43 synthesis | mcwiki:lint broken |
| 함정 카탈로그 (uobject §4) 재현 | 11대 함정 | 5.x 변화 재검증 |

### 5.3 KMCProject Phase 변경 시 (Phase 1 → 2 → 3 → ...)

| Phase 변경 | vault 영향 |
| -- | -- |
| Phase 1 → 2 (UMCHitBoneCurveUserData 신규) | sources/mc-* + assetuserdata §2.10 신규 |
| Phase 2 → 4 (런타임 hook 보류) | (대기 — Phase 3 진행 시 enrich) |
| Phase 5 (MCComboEditor) | uobject §2.13/§2.14 + asseteditortoolkit §2.15 + assettools §2.6.1 + synthesis 신규 (Cycle 5d 1차) |
| Phase 5 후속 (Cycle 5d 2차) | **본 README + meta 5종 + §2.11.1 보강** |

→ 매 KMCProject Phase 가 vault testbed 의 검증 사이트. **vault 의 testbed 가치 = 실측 사례로 함정 카탈로그를 일반화**.

## 6. 측정 가능한 품질 기준

[[00_meta/00_QualityCriteria]] + [[sources/ue-ref-17-qualitycriteria]] 정밀판.

### 6.1 4종 가중 100점

```
Performance 35 + Memory 25 + Network 15 + Maintainability 25 = 100
```

| 점수 | 결과 | 조치 |
| -- | -- | -- |
| 95~100 | ✅ Production ready | (없음) |
| 80~94 | ⚠️ Pass with notes | 권장 보강 (선택) |
| 70~79 | ❌ Fail — 보강 후 재평가 | 의무 보강 + 재평가 |
| <70 | 🚨 Critical Fail — 재작성 요청 | 페이지 Draft 강등 |

### 6.2 Cycle 5d 평균 점수 (2026-05-15)

| Cycle | 페이지 수 | 평균 점수 | 비고 |
| -- | -- | -- | -- |
| 5a (2026-05-14) | 4 | ~89 | const propagation + RegisterStartupCallback |
| 5b (2026-05-14) | 3 | ~91 | AssetEditor Window 메뉴 = TabManager 자체 발견 |
| 5c (2026-05-14) | 3 | ~88 | IStructureDetailsView dangling |
| 5d 1차 (2026-05-15) | 5 | **89.5** | MCComboEditor 함정 5건 |
| 5d 2차 (2026-05-15) | 7 (목표) | (본 작업 완료 후) | ref-00-readme + meta 5종 + §2.11.1 |

→ 평균 ≥ 80 PASS 유지. 단 한 페이지도 70 미만 없음 (재작성 의무 0).

## 7. ⚠ 본 거버넌스의 의무 적용 범위

- **vault 작성자** (ue-agent-wiki-maintainer / specialist) — 의무 적용 100%
- **vault 평가자** (ue-agent-evaluator) — 의무 적용 100% + Generator-Evaluator 분리 (Article 1)
- **vault 사용자** (Cowork / Claude Code / 사용자 직접) — 답변 시 [[00_meta/06_VaultCitationRule]] 3 tier 의무
- **vault 외부 agent** (외부 에이전트 / Journey 등) — 의무 적용 권장 (강제 X — Cycle 5d 1차 시점)

→ Phase II 게이트 PASS 후 main 측 orchestrator 가 외부 agent 호출 시 본 거버넌스 명시 강제 검토. 상세 = [[00_meta/07_AgentBoundaryProtocol]].

## 8. Cross-link

### 페어 (의무 Read)

- [[sources/ue-meta-honest-limits]] — 6대 한계 + Self-eval bias 사례 (본 §4.2 권위)
- [[sources/ue-meta-corrections]] — 정정 누적 (본 §4.2 사례 2 권위)
- [[sources/ue-meta-confidence-tags]] — 3 tier 체계 (본 §2 단계 2 권위)
- [[sources/ue-meta-improvement-roadmap]] — 향후 enrich trajectory

### 운영 메타 (00_meta 8)

- [[00_meta/00_QualityCriteria]] (본 §6 권위)
- [[00_meta/01_PolicyPriority]] (5단 Tier 정책)
- [[00_meta/02_FrontmatterStandard]] (본 §2 단계 1 권위)
- [[00_meta/03_EvaluatorRecipe]] (본 §4 권위)
- [[00_meta/04_AuditPolicy]] (본 §5 권위)
- [[00_meta/05_HandoffProtocol]] (본 §2 단계 3 권위)
- [[00_meta/06_VaultCitationRule]] (본 §2 단계 2 권위)
- [[00_meta/07_AgentBoundaryProtocol]] (본 §7 권위)

### references hub

- [[sources/ue-ref-14-taskhandofftemplate]] — 멀티 세션 인계 표준
- [[sources/ue-ref-15-evaluatorrecipe]] — 8단계 평가
- [[sources/ue-ref-16-policypriority]] — 5단 Tier 정책 우선순위
- [[sources/ue-ref-17-qualitycriteria]] — 4종 가중 채점
- [[sources/ue-ref-18-modelevolutionaudit]] — 분기 audit

### KMCProject 페어 (UE 도메인 측 ↔ KMCProject 도메인 측)

- `E:\MCProject\KMCProject\CLAUDE.md` §13 — KMCProject 측 거버넌스 mirror

## 9. Changelog

| 날짜 | 변경 |
| -- | -- |
| 2026-05-09 | 카드 작성 (raw ingest, slim) |
| **2026-05-15 (Cycle 5d 2차)** | **정밀 enrich** — §2 5단 의무 매트릭스 (4 단계 각 출처 cross-link) + §3 라이프사이클 5상태 + §4 Generator-Evaluator 분리 + 실패 사례 2건 + filing-back + §5 모델 진화 대응 3종 (Anthropic / UE 마이너 / KMCProject Phase) + §6 측정 가능한 품질 기준 + Cycle 5a~5d 평균 점수 매트릭스 + §7 의무 적용 범위 (vault 작성자 / 평가자 / 사용자 / 외부 agent) + §8 Cross-link 4 권위 (00_meta 8 + references 5 + meta 페어 4). raw slim → vault-side 정밀 mirror. 🟢 vault 직시 (모든 단계가 vault 내 00_meta + references + meta 페어 페이지로 검증 가능). |
