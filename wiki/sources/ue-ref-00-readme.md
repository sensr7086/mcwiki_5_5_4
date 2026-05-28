---
type: source
title: "UE refs — 00 README (UE Wiki 진입)"
slug: ue-ref-00-readme
source_path: raw/ue-wiki-llm/references/00_README.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-28
audit_5_5_4: pass-label-only  # 2026-05-28 Phase 2-B auto-classified
tags: [ue, reference, wiki-meta, vault-entry, governance, karpathy-schema]
citation_disclosure: "본 카드 = 🟢 vault 직접 직시 (디렉토리 구조 / 도구 매트릭스 / agent 카탈로그 / Cycle 진행 표). raw/ue-wiki-llm/references/00_README.md 원본은 ingest 시점 카드 (slim) — 본 §2 이후 enrich 는 KMCProject vault 진화 (Phase 1~10 + Cycle 5d) 반영 vault-side mirror."
---

# UE refs — 00 README (UE Wiki 진입점)

> Source: [[raw/ue-wiki-llm/references/00_README.md]]
>
> **본 페이지의 역할** — UE 5.7.4 LLM Wiki vault (`E:\MCWiki`) 의 진입점. CLAUDE.md §5.2 step 1 의 1차 게이트 + §5.4 G2 게이트의 의무 Read 후보. vault 전체 진화 (Phase 1~10 + Cycle 1~5d) 와 도구 / agent / 갱신 절차 catalog.
>
> **Citation 마커** ([[00_meta/06_VaultCitationRule]]): 🟢 vault 직시 / 🟡 외삽 / 🔴 INFERRED.

## 1. Summary

UE 5.7.4 (`C:\Unreal\UnrealEngine`) 의 Engine/Source/Runtime 트리 (189 모듈) 를 분석한 LLM Wiki 의 진입점. **Karpathy schema 4축** (sources / entities / concepts / synthesis) + 운영 메타 (00_meta / templates / raw / tools) + 검증 절차 (lint / stats / evaluator) + 8 agent + 14 specialist 합성. 본 README 는 vault 의 **진입 + 갱신 + 운영 전반** catalog.

## 2. 의무 Read 의 진입 절차 (CLAUDE.md §5.2)

```text
사용자 질문
  ↓
[Step 1] mcwiki:read_index   → 카테고리 + 페이지 인덱스 파악 (본 README 페어)
[Step 2] mcwiki:search query="<keywords>" → vault 매치 확인
[Step 3] 매치 페이지 read_page → 본문 수집
[Step 4] 답변 작성 — [[00_meta/06_VaultCitationRule]] 3-Tier 마커 의무
[Step 5] (선택) propose_synthesis / append_log filing-back
```

🚨 **Wiki 사용 전 의무 Read** — [[sources/ue-meta-honest-limits]] (vault 한계 6대 + Self-eval bias 사례). 사용 시점에 본 README + honest-limits + confidence-tags 3종 일독 권장.

## 3. vault 디렉토리 구조 (Karpathy schema + 정밀판)

```
E:\MCWiki\
├── wiki\                       # 🌐 메인 vault
│   ├── index.md                # ⭐ 카탈로그 hub (sources/entities/concepts/synthesis 일람)
│   ├── log.md                  # ⭐ append-only 운영 로그 (매 ingest/lint/refactor entry)
│   ├── sources\                # source 페이지 (221) — raw 카드 + vault-side enrich 카드
│   ├── entities\               # entity 페이지 (79) — UE 클래스 / API 단위
│   ├── concepts\               # concept 페이지 (46) — 추상 개념 / 횡단 정책
│   └── synthesis\              # synthesis 페이지 (43) — 다중 source 합성 / 패턴 / 측정
├── 00_meta\                    # ⭐ 운영 메타 (Karpathy 정밀판 8 룰)
│   ├── 00_QualityCriteria.md   # 4종 가중 채점 (Performance 35 / Memory 25 / Network 15 / Maintainability 25)
│   ├── 01_PolicyPriority.md    # 5단 Tier 정책 우선순위 + §10 점수
│   ├── 02_FrontmatterStandard.md  # 4줄 의무 (name / description / type / slug)
│   ├── 03_EvaluatorRecipe.md   # 8단계 회의적 평가
│   ├── 04_AuditPolicy.md       # 분기별 audit 의무
│   ├── 05_HandoffProtocol.md   # 멀티 세션 인계 5필드
│   ├── 06_VaultCitationRule.md # 🟢/🟡/🔴 3 tier 인용 의무
│   └── 07_AgentBoundaryProtocol.md  # main ↔ specialist boundary 5 단계
├── templates\                  # source / entity / concept / synthesis 4 템플릿
├── raw\                        # 원본 ingest (ue-wiki-llm + articles + papers + youtube + notes)
│   └── ue-wiki-llm\            # UE LLM Wiki 원본 (C:\Unreal\UnrealEngine\LLM_Wiki 의 ingest 스냅샷)
└── tools\                      # 검증 도구 (Python — lint / stats / wikilink-graph)
```

→ vault 의 핵심 가정: **모든 답변은 sources / entities / concepts / synthesis 4축 안에 위치** + 운영 정책은 00_meta 안 8 룰 정밀판으로 단일화.

## 4. 페이지 작성 표준

### 4.1 Frontmatter 4줄 의무 (00_meta/02_FrontmatterStandard)

```yaml
---
type: source                                 # sources/entities/concepts/synthesis 중 하나
title: "UE Foo — Bar sub-skill"             # 사람-친화 제목
slug: ue-foo-bar                             # 케밥 케이스 lower (file 명과 일치)
source_path: raw/ue-wiki-llm/skills/.../X.md # raw 원본 경로 (sources 만)
last_updated: 2026-05-15                     # 매 갱신 시 갱신 의무
tags: [...]                                  # 횡단 검색용 (75~250자 권장)
citation_disclosure: "🟢/🟡/🔴 사용 분포 명시"
related_concepts: ["[[concepts/...]]"]       # cross-link
---
```

### 4.2 Citation 마커 (00_meta/06_VaultCitationRule)

| Tier | 의미 | 사용 |
| -- | -- | -- |
| 🟢 VAULT | `read_page` / grep / 컴파일 / 직접 검증 완료 | `[[wikilink]]` 인용 + 라인 번호 |
| 🟡 PARTIAL | vault 근거 일부 + 외삽 | "(vault 근거: ... · 외삽)" 짧은 주석 |
| 🔴 INFERRED | vault 미확정 — 일반 지식 / 외부 docs | "**추론** (vault 미확정)" prefix 의무 |

🚨 **모든 fact 주장에 의무 적용** — Wiki 측 답변자 (agent / Cowork / specialist) 가 cross-tier 를 *섞어 진술* 하면 사용자가 vault 자산성과 LLM 인퍼런스를 식별 불가 → 위반.

### 4.3 5단 의무 (각 페이지 작성)

| 단계 | 의무 | 출처 |
| -- | -- | -- |
| 1. Frontmatter | 4줄 + tags + citation_disclosure | 00_meta/02 |
| 2. Quality | 🟢/🟡/🔴 3 tier 명시 + 검증 출처 | 00_meta/06 |
| 3. Handoff | Cross-link sections | 00_meta/05 |
| 4. Evaluator | 작성 직후 `ue-evaluator` 8단계 회의적 평가 (Self-eval bias 회피) | 00_meta/03 |
| 5. Audit | `last_updated` 갱신 + `wiki/log.md` append_log | 00_meta/04 |

→ 매 페이지 작성 시 작성자 ≠ 평가자 (Article 1 Generator/Evaluator 분리).

## 5. 도구 카탈로그 (mcwiki MCP)

| 도구 | 용도 | 호출 시점 |
| -- | -- | -- |
| `read_index` | 카탈로그 hub 일람 | 진입 / 페이지 위치 확인 |
| `search query=` | full-text 검색 | 질문 분석 후 vault 매치 확인 |
| `read_page slug=` | 페이지 본문 | 매치 후 본문 수집 |
| `read_raw` | raw/ 원본 (raw/ue-wiki-llm/ 등) | source 페이지 검증 |
| `list_pages kind=` | sources/entities/concepts/synthesis 목록 | 카테고리별 일람 |
| `write_page` | 신규/갱신 페이지 작성 (kind 제한) | 작성 단계 |
| `append_log op=` | log.md append-only entry | 작성 후 의무 (5단 §5) |
| `lint` | 카탈로그 무결성 (COUNT_MISMATCH / orphan / broken / stale) | refactor 후 / 분기 audit |
| `stats` | 통계 (sources / entities / concepts / synthesis / total) | lint 후 통계 갱신 |
| `synthesis_finalize` | synthesis 페이지 status: draft → living/finalized | lint pass 후 |
| `propose_synthesis` | 매치 없는 질문 → 새 synthesis 후보 propose | filing-back 단계 |
| `query_recap` | 최근 질문 패턴 + filing-back 후보 | 분기 audit |

🚨 `write_page kind=meta slug=index` 또는 `kind=log` 는 거부 — index.md / log.md 는 *직접 편집* 만 (Cowork 환경 mount 필요).

## 6. Agent 카탈로그 (Phase 5+, 15 agents)

### 6.1 메타 운영 (4)

| Agent | 역할 | 호출 |
| -- | -- | -- |
| **ue-agent-orchestrator** | main controller — 사용자 요청 분석 + 적합 specialist 위임 | 사용자 직접 |
| **ue-agent-evaluator** | 회의적 평가자 (8단계 + 4종 가중) — Self-eval bias 회피 | 작성자 ≠ 평가자 의무 |
| **ue-agent-audit** | 분기별 vault 무결성 audit (stale / orphan / broken) | 분기 시작 시 |
| **ue-agent-wiki-maintainer** | vault 갱신 전담 (본 README 의 작성자) | 사용자 `[Wiki] ...` 호출 |

### 6.2 카테고리 specialist (11)

| Specialist | 도메인 |
| -- | -- |
| **ue-agent-animation** | Animation (AnimGraph / IK / Notify / Sync / Optimization) |
| **ue-agent-asset** | AssetClasses + AssetUserData |
| **ue-agent-components** | Components (Actor / Scene / Primitive / Mesh / Light / Physics / Movement / etc) |
| **ue-agent-editor** | Editor (UnrealEd / PropertyEditor / ToolMenus / AssetEditorAPI) |
| **ue-agent-gameframework** | GameFramework (Actor / Pawn / Character / Controller / GameMode / World) |
| **ue-agent-input** | Input (EnhancedInput / Action / Subsystem / Legacy) |
| **ue-agent-plugin** | Plugin (Build.cs / module loading / dependency) |
| **ue-agent-render** | Render (RDG / Shader / RHI / Lumen / Nanite / Mobile / VR) |
| **ue-agent-slate-umg** | Slate / SlateCore / UMG |
| ⭐ **ue-agent-spatial-partition** | SpatialPartition (TOctree2 / TQuadTree / WorldPartition) — Cycle #11 |
| ⭐ **ue-agent-levelsequence** | LevelSequence (MovieScene / Tracks / Sequencer / MRQ) — Cycle #12 |

→ 모든 specialist 가 `Task tool` 로 ue-evaluator 호출 의무 (Article 1 분리). vault raw 15, plugin 활성 13.

## 7. Cycle 진행 표 (Phase 1~10 + Cycle 1~5d, 2026-05-15 기준)

### 7.1 Phase (raw ingest)

| Phase | 기간 | 결과 |
| -- | -- | -- |
| 1~3 | ~2026-05-08 | main SKILL 18종 + sub 일부 + entities/concepts 골격 |
| 4A~4H | 2026-05-09~10 | sub-skills 132 + refs/catalog/docs/meta 30 + deep refs 6 + manifests 2 → **168 sources** |
| 5 | 2026-05-10 | Measurements 5 + agents 15 (raw, plugin 13) |
| 6~7 | 2026-05-10~11 | concepts 정밀화 (Render PSO / Motion-To-Photon 등) |
| 8 | 2026-05-11 | Render 카테고리 11 sub-skill 추가 |
| 9 | 2026-05-12~13 | Render Cycle #1-10 enrich + ⭐⭐⭐ refactor Cycle 1+2+3+4 (slim 19/19 + vault 보강 6) |
| 10 | 2026-05-13~14 | SpatialPartition (Cycle #11) + LevelSequence (Cycle #12) 신규 카테고리 |

### 7.2 Cycle (vault 후속 보강 + KMCProject testbed)

| Cycle | 날짜 | 결과 | 함정 카탈로그 |
| -- | -- | -- | -- |
| 1+2+3+4 | 2026-05-13 | refs slim 19/19 + interface §5 / mc-validation §6 / mc-actor-spawn §9.5 | 6대 → 9대 |
| 5a | 2026-05-14 | const propagation C2440 + RegisterStartupCallback (4 페이지) | 9대 |
| 5b | 2026-05-14 | ⭐⭐⭐ AssetEditor Window 메뉴 = TabManager 자체 발견 (3 페이지) | 9대 |
| 5c | 2026-05-14 | IStructureDetailsView / SCurveEditor dangling + Hit Curve Pipeline (3 페이지) | 9대 → 10대 |
| 5d 1차 | 2026-05-15 | MCComboEditor 함정 5건 (uobject §2.13/§2.14 + asseteditortoolkit §2.15 + assettools §2.6.1 + synthesis 신규) | 10대 → **11대** |
| **5d 2차** | **2026-05-15** | **기존 1+3+5 보강 (ref-00-readme + ue-meta-\* 5종 + uobject §2.11 후속)** | 11대 |

→ Cycle 5d 2차 = 본 README 갱신 + meta 5종 정밀 보강 + §2.11.1 (다른 customization 재현 검증).

## 8. 갱신 절차

### 8.1 Anthropic 모델 변경 시 (분기 audit)

```text
1. wiki/00_meta/04_AuditPolicy 의 분기 일정 확인 (Q1/Q2/Q3/Q4)
2. ue-agent-audit 호출 → vault 전체 일관성 audit
3. stale > 90 days 페이지 확인 (현재 0)
4. 새 모델 호환성 검증 — 핵심 페이지 10건 read + 회의적 평가
5. 검증 실패 페이지 → 보강 의무 (자동 deprecate 금지)
```

### 8.2 UE 마이너 업그레이드 시 (5.7.x → 5.7.y / 5.7 → 5.8)

```text
1. raw/ue-wiki-llm/ 재ingest (UE 새 버전 Engine/Source/Runtime grep 갱신)
2. 각 sources/ 페이지 last_updated + 라인 번호 갱신 의무
3. 함정 카탈로그 (uobject §4 11대) 재현 가능 여부 검증 (5.x 변화 가능)
4. entities/ 페이지 — 클래스 시그니처 / virtual 매트릭스 갱신
5. concepts/ — 횡단 정책 (Asset Loading / Iterator / Profiling) 변화 audit
6. synthesis/ — 다중 source 합성 페이지 lint (broken 발생 시 재합성)
```

### 8.3 KMCProject Phase 변경 시 (Phase 2 → 3 → 4 → ...)

```text
1. KMCProject CLAUDE.md (E:\MCProject\KMCProject\CLAUDE.md) Phase 진행 갱신
2. testbed 매트릭스 vault 반영 — sources/mc-* + synthesis/mc-* 페이지 갱신
3. 새 함정 발견 시 — 해당 sub-skill source 페이지 § 신규
4. evaluator 평균 ≥ 80 권장 (Cycle 5d 1차 평균 89.5 PASS / 2차 후속 동일 목표)
5. index.md 의 "Cycle X 후속 보강 누적" 블록 갱신 의무
```

→ KMCProject 의 vault testbed 가치 = **실측 사례** 가 vault 의 함정 카탈로그를 일반화/검증. KMCProject 외 검증 사이트 확보 시 신뢰도 🟡 → 🟢 격상 (예: §2.11.1 — UE Engine SRowEditor 재현).

## 9. 본 vault 의 한계 (의무 Read 위치)

상세 = [[sources/ue-meta-honest-limits]] (6대 본질 문제 + Self-eval bias 사례 2건).

요약:

1. UE **5.7.4 만 검증** — 다른 마이너 버전 외삽 의무
2. cross-platform 커버리지 ≠ 100% — Mobile / VR / Console 일부 외삽
3. KMCProject 외 검증 사이트 비율 = 약 **65%** (Cycle 5d 2차 기준 — §2.11.1 격상 후) — single-case 페이지 의심 의무
4. Self-eval bias — vault 평가자 ≠ vault 작성자 의무 (Article 1)
5. raw/ue-wiki-llm/ ingest = **2026-05-09 스냅샷** — 그 이후 UE Engine 변경 미반영
6. 비-UE 콘텐츠 (Anthropic SDK / 외부 패키지) = 0 % 가산

→ 사용자가 `[inferred]` / 🔴 INFERRED 항목 사용 전 외부 검증 의무 ([[sources/ue-meta-corrections]] 누적).

## 10. 통계 (2026-05-15 기준)

```
sources:    221
entities:    79
concepts:    46
synthesis:   43
orphans:      0
broken:       0
stale (>90d): 0
정밀 source: 67건 (Editor 15 + Render 9 + SpatialPartition 6 + LevelSequence 12 + 기타 25 — Cycle #13 enrich 후 모두 full)
함정 카탈로그 (uobject §4): 11대
agent (vault raw): 15 (plugin 활성 13)
governance meta (00_meta): 8
references: 19 + deep 5
measurements: 5 (⭐⭐ 1 — §2 Self-eval bias 측정)
MC 시리즈 sources: 2 + synthesis: 8
```

→ 매 운영 후 `lint` + `stats` 검증 의무. 현재 lint 378 pages **0 issues** / stale 0 / orphan 0 / broken 0 (Cycle 5d 2차 시점).

## 11. Cross-link

### 진입 페어 (의무 Read)

- [[sources/ue-meta-honest-limits]] — vault 6대 한계 + Self-eval bias 사례
- [[sources/ue-meta-confidence-tags]] — 🟢/🟡/🔴 3 tier 의무
- [[sources/ue-meta-governance]] — 거버넌스 마스터 (CLAUDE-wiki-governance.md vault 측 미러)

### 운영 메타 (00_meta 8)

- [[00_meta/00_QualityCriteria]] · [[00_meta/01_PolicyPriority]] · [[00_meta/02_FrontmatterStandard]]
- [[00_meta/03_EvaluatorRecipe]] · [[00_meta/04_AuditPolicy]] · [[00_meta/05_HandoffProtocol]]
- [[00_meta/06_VaultCitationRule]] · [[00_meta/07_AgentBoundaryProtocol]]

### 19 references hub

- [[sources/ue-ref-01-layermap]] ~ [[sources/ue-ref-19-externalsourcesguide]] (19) + deep refs 5
- 의무 정책 5종: [[sources/ue-ref-07-profilingscopeRule]] · [[sources/ue-ref-09-globaliteratorpolicy]] · [[sources/ue-ref-10-componentpolicies]] · [[sources/ue-ref-11-assetloadingpolicy]] · [[sources/ue-ref-12-assetoptimizationpolicy]]

### Agent 카탈로그

- 메타 4: [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-evaluator]] · [[sources/ue-agent-audit]] · [[sources/ue-agent-wiki-maintainer]]
- specialist 11 (위 §6.2 참조)

### Manifests

- [[sources/ue-readme]] (raw UE LLM Wiki README) · [[sources/ue-manifest]]

## 12. Changelog

| 날짜 | 변경 |
| -- | -- |
| 2026-05-09 | 카드 작성 (raw ingest, slim) |
| **2026-05-15 (Cycle 5d 2차)** | **정밀 enrich** — §2 의무 Read 진입 절차 + §3 디렉토리 구조 + §4 페이지 작성 표준 (frontmatter / citation / 5단 의무) + §5 mcwiki MCP 도구 매트릭스 + §6 15 agent 카탈로그 + §7 Phase 1~10 + Cycle 1~5d 진행 표 + §8 갱신 절차 3종 (Anthropic 모델 / UE 마이너 / KMCProject Phase) + §9 vault 한계 + §10 통계 (2026-05-15) + §11 Cross-link 5종. raw/ue-wiki-llm/references/00_README.md 원본 슬림 → vault-side 정밀 보강. **🟢 vault 직시 (현재 디렉토리 / 도구 / agent / Cycle 모두 vault 안 페어 페이지로 검증 가능)**. |
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
