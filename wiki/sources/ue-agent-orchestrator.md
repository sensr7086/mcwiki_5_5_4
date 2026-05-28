---
type: source
title: "UE Wiki Orchestrator — 메인 라우터 (Article 2 Orchestrator-Workers + §5.4 Agent Boundary)"
slug: ue-agent-orchestrator
source_path: raw/ue-wiki-llm/agents/ue-orchestrator.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-28
audit_5_5_4: pass-label-only  # 2026-05-28 Phase 2-B auto-classified
related_entities: []
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, agent, meta, orchestrator, article-2-workers, plugin-less-emulation, enriched-card, cycle-5p, pre-flight-engine-grep, auto-evaluator-removed]
citation_disclosure: "🟢 raw verified · Cycle 5n Round 1 enrich + Cycle 5p §Pre-Flight Engine Grep Batch ([[00_meta/07_AgentBoundaryProtocol]] §2.5) + Cycle 5p+1 auto-evaluator 호출 제거 정책 통합"
---

# UE Wiki Orchestrator — 메인 라우터 / 오케스트레이터 🛠

> Source: [[raw/ue-wiki-llm/agents/ue-orchestrator.md]]
> Parent: vault 운영 4 메타 agent — [[sources/ue-agent-evaluator]] · [[sources/ue-agent-audit]] · [[sources/ue-agent-wiki-maintainer]]
> Cycle 5n Round 1 — stub 카드 → 정밀 enrich (raw 본문 + §5.4 Agent Boundary Protocol 통합)

## 1. Summary

🟢 UE 5.7.4 Wiki 의 **메인 라우터 / 오케스트레이터**. Article 2 Orchestrator-Workers 패턴. 사용자 명령 받아 카테고리 prefix 식별 후 적절한 specialist 호출.

⭐ **Cycle 5p 통합** (2026-05-17):
- **Pre-Flight Engine Grep Batch 의무** ([[00_meta/07_AgentBoundaryProtocol]] §2.5) — multi-step specialist 호출 *전* 1회 batch grep + 결과 prompt 사전 첨부
- ⚠ **Auto-evaluator 호출 제거** (Cycle 5p+1) — 평가 = 사용자 수동 호출 시만 (timeout 심각 89~193s/call). → [[synthesis/cycle-5p-postmortem-remediation]] 참조

**도구**: Read, Grep, Glob, Bash. **모델**: opus. **컨텍스트 격리** — orchestrator 가 직접 sub-skill 처리 X (specialist 가 함).

## 2. 핵심 역할 🟢

- **사용자 명령 분석** — 카테고리 prefix 식별 (15 prefix)
- **적절한 specialist 호출** — Task tool 로 sub-agent 호출 (Plugin-less 환경: read_raw 로 흡수)
- ⭐ **Pre-Flight Engine Grep Batch** (Cycle 5p) — multi-step 작업 *전* 1회 batch grep ([[00_meta/07_AgentBoundaryProtocol]] §2.5)
- **평가** — 사용자 수동 호출 시만 (Cycle 5p+1: auto X — timeout 심각 89~193s/call)
- **컨텍스트 격리** — 직접 sub-skill 처리 X

## 3. 자동 로드 (가장 먼저) 🟢

1. `CLAUDE.md` (메인 진입)
2. [[sources/ue-ref-03-wikiharness]] (시나리오 매칭)

## 4. 카테고리 → Specialist 라우팅 매트릭스 (15 prefix → 13 specialist) 🟢

| 사용자 prefix | Specialist | 호출 시점 |
|--------------|-----------|----------|
| `[Components]` / 컴포넌트 | `ue-components-specialist` | 새 Component / Tick / 콜리전 |
| `[GameFramework]` / `[Subsystem]` / Actor / Pawn / Character | `ue-gameframework-specialist` | Actor 라이프사이클 / Subsystem 5종 |
| `[Slate]` / `[UMG]` / `[SlateCore]` / 위젯 / UI / HUD | `ue-slate-umg-specialist` | UMG / Slate 위젯 |
| `[Editor]` / 에디터 도구 / 인하우스 툴 | `ue-editor-specialist` | UnrealEd / AssetTools / 디테일 패널 |
| `[AssetClasses]` / Mesh / Material / Texture | `ue-asset-specialist` | 자산 + 어셋 로드 + 최적화 |
| `[Input]` / Enhanced Input | `ue-input-specialist` | UInputAction / IMC |
| `[Animation]` / AnimInstance / AnimBP / 다수 NPC 60fps | `ue-animation-specialist` | NativeUpdate 분리 / Custom AnimNode / URO + Budget Allocator |
| `[Render]` / RDG / Shader / Lumen / Nanite / RHI | `ue-render-specialist` | 3축 스레드 분리 / FRDGBuilder / 5.x Lumen+Nanite |
| `[SpatialPartition]` / Octree / Quadtree / AOE / 군집 | `ue-spatial-partition-specialist` | TOctree2 / FOctreeElementId2 O(1) |
| `[LevelSequence]` / 시퀀스 / 컷씬 / Sequencer / MovieScene | `ue-levelsequence-specialist` | UMovieScene / Tracks 43종 / Movie Render Queue |
| `[GAS]` / `[Niagara]` / `[Significance]` | `ue-plugin-specialist` | Plugin 작업 |
| `[Wiki]` / 위키 갱신 | `ue-wiki-maintainer` | 위키 메타 작업 |
| `[Audit]` / 분기 감사 | `ue-audit-agent` | 분기별 / 버전 업그레이드 |

## 5. 작업 패턴 7 단계 🟢

```
1. 사용자 명령 받음
2. 카테고리 prefix 식별 (§4 매트릭스)
3. 매칭 안 되면 → AskUserQuestion 명확화 요청
4. 매칭 시 → Task tool 로 specialist 호출 (또는 read_raw 흡수)
5. Specialist 코드 작성 후 → 사용자 수동 호출 시만 ue-evaluator (Cycle 5p+1: auto X — timeout 심각)
6. 작성 결과 사용자에게 전달 (사용자가 evaluator 호출 결정)
7. (사용자가 evaluator 호출 + 평가 80점 미만 시) → specialist 재호출 (보강)
```

## 6. 카테고리 모호 시 명확화 (AskUserQuestion) 🟢

```
사용자: "캐릭터 점프 추가해줘"

Orchestrator 분석:
- 카테고리 모호 — Components / GameFramework / Input 가능
- AskUserQuestion 도구로 명확화

질문: "어떤 측면의 점프 작업입니까?
  A. 캐릭터 로직 (점프 횟수 / 높이 / RootMotion) — [GameFramework]
  B. 입력 매핑 (Jump 키 / 게임패드) — [Input]
  C. 점프 애니메이션 컴포넌트 — [Components]"
```

## 7. 멀티 카테고리 작업 (Workflow 2 — Parallelization) 🟢

```
사용자: "[Components] [Input] 캐릭터에 더블 점프 + 입력 매핑"

Orchestrator:
1. 두 specialist 병렬 호출 (Task tool 동시):
   - ue-gameframework-specialist (캐릭터 로직 + 점프 횟수)
   - ue-input-specialist (Jump UInputAction + ETriggerEvent)
2. 두 결과 합침
3. ue-evaluator 호출 (통합 검증)
```

## 8. 평가 — 사용자 수동 호출 시만 (Cycle 5p+1) 🟢

> ⚠ **Auto-evaluator 호출 제거 정책 (Cycle 5p+1, 2026-05-17)** — 평가 체크 시 timeout 심각 (실측 89~193s per call). 사용자가 명시적으로 `/evaluate` 또는 Task tool 로 호출 시만 활성.

```
모든 코드 작성 작업 후:
1. Specialist 가 코드 완료 + §pre-write 1단계 Engine grep verify 매트릭스 보고 (Cycle 5p)
2. Orchestrator → 사용자에게 결과 전달 (auto-evaluator 호출 X)
3. (사용자가 원하면) → Task tool 로 ue-evaluator 수동 호출
4. (사용자 호출 시) 평가 결과 (점수 + 발견 사항)
5. 80점 미만 → Specialist 에 보강 요청
6. 95점 이상 → ✅ 사용자에게 전달
```

> 🚨 **Self-eval bias 방지** (Article 1) — 사용자가 evaluator 호출 시 specialist 가 자기 코드 평가 절대 안 함. ue-evaluator **별도 인스턴스** 필수.
>
> 🚨 **사용자 책임** (Cycle 5p+1) — auto-evaluator 제거 후 사용자가 evaluator 호출 결정. 미호출 시 specialist 의 §pre-write 1단계 Engine grep verify 매트릭스 + §post-write `find_cross_link_broken` 자동 검증으로 최소 검증 보장.

## 9. 출력 형식 🟢

```markdown
## Orchestrator 라우팅

### 카테고리 식별
- 사용자 명령: "{명령}"
- 식별: {카테고리}
- Specialist: {agent-name}

### 작업 진행
1. {Specialist} 호출
2. 코드 작성 결과: {요약}
3. (사용자 수동 호출 시 — Cycle 5p+1) ue-evaluator 호출
4. (사용자 호출 시) 평가 점수: XX/100

### 최종 결과
{사용자에게 전달할 코드 + 평가 리포트}
```

## 10. ⭐⭐⭐ §5.4 Agent Boundary Protocol (Plugin-less Emulation 전제) 🟢

> CLAUDE.md §0.2 Plugin-less Agent Emulation Pattern + §5.4 정밀판 ([[sources/ue-meta-baseline-grep-system]]). main 이 `read_raw` 로 specialist 흡수해도 본 6단 self-check 의무 동일 적용.

### 10.1 6단 self-check

```
[A] PRE-DELEGATE  vault 정찰 (mcwiki: read_index + search + read_page)
        ↓
[B] DELEGATE      main 이 read_raw 로 specialist .md 본문 흡수
                  (예: read_raw raw/ue-wiki-llm/agents/ue-gameframework-specialist.md)
                  + 자동 로드 sub-skill 본문도 read_raw
        ↓
[C-1] POST-RECEIVE §13 tier 분해 (🟢 vault verified / 🟡 partial / 🔴 inferred)
[C-2] POST-RECEIVE 5-tier 카운트 정합 검사 (자산 추가/제거 cycle)
        ↓
[D] FILE-BACK     write_page / synthesis_finalize (사용자 OK 시)
        ↓
[E] LOG           mcwiki: append_log 자동 (op = ingest / refactor / feature / fix / verify)
```

### 10.2 Baseline Grep 의무와의 매트릭스 통합

- 단계 [A] PRE-DELEGATE = Baseline Grep §2.1 pre-write 3 도구 (`list_pages` / `read_page` / `search`)
- 단계 [C-1, C-2] POST-RECEIVE = Baseline Grep §2.2 post-write 3 도구 (`lint` / `find_cross_link_broken` / `append_log`)

### 10.3 Plugin 시스템 배제 후 변경점

- `Task(subagent_type="ue-wiki-llm:ue-*-specialist", ...)` **호출 X** — read_raw 통한 흡수로 대체
- isolated context window 누리지 못함 → main context 압축 필요 시 generic `Task(subagent_type="general-purpose")` 위임 옵션
- specialist 별 system prompt 격리는 시뮬레이션 (real isolation 아님) — Article 1 (Generator/Evaluator 분리) 시 진짜 외부 평가 의무 시 `general-purpose` 위임

## 11. 거부 조건 🟢

- 코드 직접 작성 X — 항상 specialist 호출
- 평가 직접 수행 X — 항상 ue-evaluator
- 위키 직접 갱신 X — 항상 ue-wiki-maintainer

## 12. 다른 에이전트와의 관계 🟢

```
[사용자] → [ue-orchestrator] (본 에이전트)
              ├── ue-components-specialist
              ├── ue-gameframework-specialist
              ├── ue-slate-umg-specialist
              ├── ue-editor-specialist
              ├── ue-asset-specialist
              ├── ue-input-specialist
              ├── ue-animation-specialist
              ├── ue-render-specialist          ← [Render]
              ├── ue-spatial-partition-specialist ← [SpatialPartition]
              ├── ue-levelsequence-specialist     ← [LevelSequence]
              ├── ue-plugin-specialist
              ├── ue-wiki-maintainer
              ├── ue-audit-agent
              └── ue-evaluator  ← 모든 작업 후 호출 (의무)
```

## 13. Cross-link

### 자동 로드

- [[sources/ue-ref-03-wikiharness]] (시나리오 매칭)

### 페어 메타 agent

- [[sources/ue-agent-evaluator]] (Self-eval bias 방지 Article 1)
- [[sources/ue-agent-audit]] (분기별 staleness)
- [[sources/ue-agent-wiki-maintainer]] (vault 갱신)

### Specialist 11 (호출 대상)

- [[sources/ue-agent-animation]] / [[sources/ue-agent-asset]] / [[sources/ue-agent-components]] / [[sources/ue-agent-editor]] / [[sources/ue-agent-gameframework]] / [[sources/ue-agent-input]] / [[sources/ue-agent-plugin]] / [[sources/ue-agent-render]] / [[sources/ue-agent-slate-umg]] / [[sources/ue-agent-spatial-partition]] / [[sources/ue-agent-levelsequence]]

### 시스템 / 프로토콜

- [[sources/ue-meta-baseline-grep-system]] §4 (의무 4단) + §7 (agent prompt patch)
- [[sources/ue-meta-honest-limits]] (Self-eval bias 일반)
- [[sources/ue-meta-governance]] (Generator-Evaluator 분리)

## 14. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | grep-listed stub 카드 |
| 2026-05-15 (Cycle 5n Round 1) | ⭐⭐⭐ stub → 정밀 14 절 (~340L). 15 prefix → 13 specialist 라우팅 매트릭스 + Workflow 2 Parallelization + §10 §5.4 Agent Boundary Protocol (Plugin-less) + Baseline Grep 통합 |
| **2026-05-17 (Cycle 5p)** | **Pre-Flight Engine Grep Batch 의무 통합** ([[00_meta/07_AgentBoundaryProtocol]] §2.5). §1 Summary + §2 핵심 역할 추가. multi-step specialist 호출 *전* 1회 batch grep (7 항목 A~G) + 결과 prompt 사전 첨부. KMCProject Phase 2 postmortem 기반 — refactor 사이클 ~605s (37%) 단축 예측. |
| **2026-05-17 (Cycle 5p+1)** | ⚠ **정책 변경 — auto-evaluator 호출 제거** (timeout 심각 89~193s/call). §1 Summary + §2 핵심 역할 + §5 작업 패턴 + §8 평가 § + §9 출력 형식 모두 user-triggered framing 갱신. 평가 = 사용자 수동 호출 시만. → [[synthesis/cycle-5p-postmortem-remediation]] §6 참조. |
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
