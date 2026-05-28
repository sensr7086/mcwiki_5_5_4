---
type: meta
title: "Agent Boundary Protocol (main ↔ specialist)"
slug: 07_AgentBoundaryProtocol
created: 2026-05-12
last_updated: 2026-05-17
tags: [meta, governance, agent, boundary, mcp, orchestration, pre-flight, cycle-5p]
---

# Agent Boundary Protocol

> CLAUDE.md §5.4 의 정밀판. `Task` tool 로 specialist subagent 를 호출하는 모든 main Cowork 대화 (또는 orchestrator) 가 의무 적용.
>
> **핵심**: vault 와 통신하는 도구 (`mcwiki` MCP 16종) 는 **main Cowork 만 보유**. specialist 는 raw/wiki 파일 시스템만 접근 가능. 따라서 §5.2 QUERY workflow 가 specialist 안에서 시행될 수 없다 → **main 이 boundary 에서 wrap** 해야 vault 가 누적된다.

---

## §1. 문제 정의

### 1.1. 현재 권한 매트릭스 (2026-05-12)

| 주체 | mcwiki MCP | 파일 (Read/Edit/Write) | Bash | Task (subagent spawn) |
| -- | -- | -- | -- | -- |
| **main Cowork** (지금 나) | ✅ 16종 deferred | ✅ | ✅ (sandbox) | ✅ |
| `ue-wiki-llm:*` specialist (12종) | ❌ | ✅ | ✅ | ❌ |
| `ue-wiki-llm:ue-orchestrator` | ❌ | ✅ (read-only 4종) | ✅ | ❌ (Read/Grep/Glob/Bash only) |
| `ue-wiki-llm:ue-evaluator` | ❌ | ✅ (read-only) | ✅ | ❌ |
| `ue-wiki-llm:ue-audit-agent` | ❌ | ✅ (read-only) | ✅ | ❌ |

→ **vault 갱신/조회 권한은 main 1점만**.

### 1.2. 위반 시나리오 (조용한 부패)

1. 사용자: "Editor sub-skill `ue-editor-mainframe` enrich 해줘"
2. main: `Task(ue-editor-specialist, "ue-editor-mainframe enrich")` — boundary §5.4 미적용
3. specialist: raw 읽어서 본문 작성 → 반환
4. main: 본문 그대로 사용자에게 표시 — **vault 무지 + §13 미적용**
5. 결과:
   - vault 에 이미 있는 [[entities/IMainFrameModule]] 등을 specialist 가 모른 채 재정의 → 중복
   - 🔴 INFERRED 구분 없이 평등 진술
   - synthesis 자동 시드 안 됨
   - log 에 아무 흔적 없음 → 다음 audit 가 못 잡음
   - lint 가 못 잡는 *조용한 부패* — broken-link 도 orphan 도 stale 도 아님

### 1.3. 즉시 해결 = §5.4 main wrap

main 이 specialist 호출 boundary 마다 `mcwiki` 5종 (read_index / search / read_page / write_page / append_log) 을 wrap 하면 specialist 권한 변경 없이 즉시 해결.

---

## §2. Phase I — Main 오케스트레이션 (즉시 적용)

### 2.1. 5단계 boundary

```text
사용자 요청
  ↓
[A. PRE-DELEGATE]  main 이 vault 정찰
  ├─ mcwiki:read_index                              ← 카탈로그
  ├─ mcwiki:search query="<주제 키워드>" scope="all" ← raw + wiki 양쪽
  └─ mcwiki:read_page kind=... slug=...            ← 매치 후보 본문
       → 컨텍스트 압축 (vault 에 이미 있는 것 + raw 위치 + 관련 entities/concepts)
  ↓
[B. DELEGATE]  Task(subagent_type, prompt)
  prompt 안에 A 의 압축 컨텍스트 + 사용자 요청 + boundary 의무 명시
  ↓
[C. POST-RECEIVE]  specialist 결과 받기 + §13 분해
  ├─ 🟢 부분: vault 인용 강화 (specialist 가 wikilink 누락했으면 main 이 추가)
  ├─ 🟡 부분: vault 갱신 후보로 표시 (사용자에게 노출)
  └─ 🔴 부분: 별도 섹션 분리 + synthesis 후보로 표시
  ↓
[D. FILE-BACK]  사용자 OK 시 vault 갱신
  ├─ mcwiki:write_page kind=sources/concepts/...   ← 갱신
  ├─ mcwiki:synthesis_seed + synthesis_finalize    ← 🔴 가치 있을 때
  └─ (사용자 OK 없으면 skip — 사용자 검증이 vault 게이트)
  ↓
[E. LOG]  mcwiki:append_log
  op=query|synthesis|note 중 적합
  title="<작업명> via Task(<specialist>)"
  body="touched: <slugs> · §13 결과: 🟢N 🟡M 🔴K"
```

### 2.2. main 의 selfcheck (boundary 마다)

`Task` 호출 직전 다음 6개 질문 자가확인 (5개 boundary 단계 + 1 카운트 정합):

1. **PRE-DELEGATE — vault 정찰 했나?** `read_index` + `search` 적어도 1회 호출 했는지.
2. **DELEGATE — prompt 에 §13 의무 포함?** specialist 가 🟢/🟡/🔴 분리하도록 prompt 명시.
3. **POST-RECEIVE — §13 tier 분해 했나?** specialist 반환을 그대로 사용자에게 패스하지 않고 분류 + 보너스 발견 노출.
4. **POST-RECEIVE — 5-tier 카운트 정합 검사 했나?** ⭐ (2026-05-13 신설) — 새 source/concept/synthesis 추가 시 index.md 의 헤더 통계 / 섹션 헤더 / 하단 통계 / 카탈로그 항목 / 진척도 표 5 위치 cross-check. 자세히 §2.4.
5. **FILE-BACK — vault 갱신 후보 사용자에게 노출?** 자동 write_page 금지. 사용자 OK 게이트.
6. **LOG — append_log 호출?** boundary 통과 = 적어도 1줄.

6개 모두 ✅ 일 때만 boundary §5.4 충족.

### 2.4. POST-RECEIVE 카운트 정합 의무 (신설 2026-05-13)

**원인 사례** — Cycle #11 이후 v0.2.0 빌드 사전 검증 시 발견된 2건 stale:

1. `## Synthesis (38)` 섹션 헤더 — 헤더 통계 (40) / 하단 통계 (40) 와 불일치 (실제 40)
2. "raw/ue-wiki-llm/ — **7 phase 완료**" — 본문 다른 곳은 "Phase 1~8/9" 명시 (실제 9 phase)

→ POST-RECEIVE §C 의 selfcheck 한계 — 문서 *내부 정합* 검사 누락 가능. 카운트가 5+ 위치에 분산.

**5-tier 카운트 검사 의무 (index.md 변경 시)**:

| Tier | 위치 | 검사 의무 |
|------|------|----------|
| 1 | 헤더 line 3 (`Last updated: ...`) | 통계 4종 (sources/entities/concepts/synthesis) + 정밀 source N건 + governance meta N |
| 2 | 각 카테고리 섹션 헤더 (`## Sources (N)` / `## Concepts (N)` / `## Synthesis (N)` / `## Entities (N)`) | 섹션 내 항목 카운트 vs 헤더 N |
| 3 | 섹션 본문 wikilink 카탈로그 | 실제 항목 수 |
| 4 | "Ingest 진척도" 표 | 카테고리별 (`main + sub`) 카운트 + 합계 |
| 5 | 하단 통계 블록 + Last verification 라인 | sources/entities/concepts/synthesis/orphans/broken/stale |

**Cross-check 명령**:

```text
# Ground truth (mcwiki tools)
mcwiki:list_pages kind=sources    → 실제 sources 카운트
mcwiki:list_pages kind=synthesis  → 실제 synthesis 카운트
mcwiki:list_pages kind=concepts   → 실제 concepts 카운트
mcwiki:list_pages kind=entities   → 실제 entities 카운트
mcwiki:list_pages kind=meta       → 실제 meta 카운트

# 그 후 위 5 tier 위치 모두 일치 확인
```

**자동화 후보** — `tools/lint.py` 에 "index.md 5-tier 카운트 정합" 검사 추가. 현재 lint 가 broken-link / orphan / stale 만 잡음, 카운트 정합은 *수동* 검사. lint 확장 후엔 자동 검출 + CI 게이트 가능.

**boundary 적용 시점** — vault 자산 *추가* 또는 *제거* 의 모든 cycle 의 §C POST-RECEIVE 단계. 자산 변경 없는 cycle (예: 단순 본문 enrich) 은 skip 가능.

### 2.3. specialist 호출 prompt 템플릿 (main 작성)

```markdown
## 작업
<사용자 요청 원문>

## Vault 컨텍스트 (main 이 PRE-DELEGATE 단계에서 압축)

vault 에 이미 있는 관련 자산:
- [[sources/...]] — 한 줄 요약
- [[entities/...]] — 사용 가능
- [[concepts/...]] — 정책 cross-link

raw 위치: raw/ue-wiki-llm/...

## 산출 형식

1. 작업물 (코드 / sub-skill 본문 / 분석)
2. **§13 Citation Tier 표** — 작업 안 모든 사실 주장을 🟢/🟡/🔴 로 분류 (vault 인용 부분은 [[wikilink]] 명시)
3. **추천 filing-back** — 어느 부분이 vault 화 가치 있는지 main 이 판단할 수 있게 표기
```

specialist 는 mcwiki 권한 없지만 *마크업 형식으로 §13 적용은 가능* — main 이 받아서 실제 vault 화 수행.

---

## §2.5 ⭐ Pre-Flight Engine Grep Batch 의무 (Cycle 5p 신규)

### 2.5.1 배경

Phase 2+ 의 multi-step specialist 호출 워크플로우 (예: KMCProject Phase 2a/2b/2c/2d) 시 메인 (오케스트레이터 역할) 이 specialist 호출 *전* 에 Engine 본가 grep 1회 batch 로 모든 specialist 가 동일 결과를 즉시 활용할 수 있도록 의무화.

KMCProject Phase 2 실측 (`outputs/cycle-5p-handoff/01_timing_analysis.md`): refactor 사이클 2회 발생 (~390-735s 손실, 24-45%). 메인 측 pre-flight batch 부재가 원인 #3 (specialist §pre-write + evaluator §Stage 2.X 와 함께 *3중 verify 의 첫 단계*).

### 2.5.2 Pre-Flight Engine Grep 7 항목

handoff document (`synthesis/*` 또는 `mc-*`) 의 §2 격상 매트릭스 / §5 BC 패턴 / §7 specialist 분담 에서 다음 항목 검출:

- **A. UPROPERTY 부착 타입** — templated container 사용 여부 (TRange/TMap/TSet/TVariant/TOptional/TFunction)
- **B. TArray cross-type copy-init** — `TArray<A*> = TArray<TObjectPtr<A>>` 패턴
- **C. TObjectPtr 변환** — `.Get()` 명시 필요 위치
- **D. bitfield UPROPERTY** — `uint8 b... : 1` 사용 여부
- **E. DEPRECATED 마이그레이션** — `_DEPRECATED` 접미사 vs CoreRedirects
- **F. Custom Serialize trait** — USTRUCT 래퍼 + `WithSerializer` 트레잇 필요 여부
- **G. Slate API 시그니처** — FCursorReply / EMouseCursor / FSlateDrawElement 정확성

각 항목에 대해 Engine 본가 grep 1회 (~5~15초) → 결과를 후속 specialist 호출 prompt 에 사전 첨부.

### 2.5.3 적용 예시 (KMCProject Phase 2 재구성)

```text
Phase 2 pre-flight task (메인 Claude):
1. 기존 MCCombo 파일 구조 파악 (기존 — 유지)
2. Engine 본가 Pre-Flight Grep Batch (Cycle 5p 신규):
   a. grep "UPROPERTY()\s*\n\s*TRange<" Engine/Source/...
      → 0건 확인 → FMovieSceneFrameRange USTRUCT 래퍼 의무
   b. read Engine/Source/Runtime/MovieScene/Public/MovieSceneFrameMigration.h L26-110
      → FMovieSceneFrameRange 패턴 학습 → FMCComboFrameRange 작성 의무
   c. grep "explicit TArray" Engine/Source/Runtime/Core/Public/Containers/Array.h
      → L752 explicit cross-type ctor 확인 → direct-init 의무
   d. grep "uint8 b\w+ : 1" Engine/Source/Runtime/...
      → MovieSceneSection.h L820/L824 + BodyInstanceCore.h L38-59 사례 4건
      → bitfield UPROPERTY 정식 지원 확인
3. 결과 batch document 작성 — 후속 4 specialist 호출 prompt 에 사전 첨부
```

### 2.5.4 Pre-Flight Batch Document 양식

메인 Claude 가 specialist 호출 prompt 안에 다음 §명시:

```markdown
## Pre-Flight Engine Grep 결과 (사전 batch — 메인 수행)

| 항목 | Engine 본가 verify 결과 | 후속 작성 패턴 |
| -- | -- | -- |
| UPROPERTY SectionRange | MovieSceneSection.h L788 — FMovieSceneFrameRange USTRUCT 래퍼 (TRange<FFrameNumber> 직접 부착 0건) | FMCComboFrameRange USTRUCT 래퍼 의무 |
| TArray cross-type copy | Array.h L752 — explicit ctor | direct-init or manual .Get() loop 의무 |
| bitfield UPROPERTY | MovieSceneSection.h L820/L824 (uint32 :1) + BodyInstanceCore.h L38-59 (uint8 :1) | uint8 :1 + EditAnywhere + BlueprintReadOnly 정합 |
| FCursorReply 시그니처 | CursorReply.h L33 — `FCursorReply::Cursor(EMouseCursor::Type)` | OnCursorQuery 작성 시 권위 사용 |
```

### 2.5.5 책임 분리 (Article 1 + Article 2 통합)

**3중 verify 구조**:

| 단계 | 주체 | 위치 | 의무 |
| -- | -- | -- | -- |
| **사전** | 메인 (Orchestrator, Article 2) | 본 §2.5 | Pre-Flight Engine Grep Batch 1회 + prompt 사전 첨부 |
| **작성 직전** | Specialist (Generator) | specialist `.md` §pre-write 1단계 (Cycle 5p) | 메인의 batch 결과 *재검증* (sanity) |
| **작성 후** | Evaluator (사용자 수동 호출) | [[00_meta/03_EvaluatorRecipe]] §1.5 Stage 2.X | generator verify 결과 *재검증* (Article 1 self-eval bias 회피) |

→ 3중 verify 로 Compile blocker 영구 차단. 본 §의 *사전 batch* 가 후속 2 단계 (generator + evaluator) 의 *기준선*.

### 2.5.6 효과 검증

본 §적용 후 (Cycle 5p 보강 4건 모두 반영 가정):

- Phase 2 multi-step 워크플로우 시간 **~37% 단축** (예상, 605s 회수)
- refactor 사이클 0회 → 사용자 대기 시간 감소
- evaluator catch 부담 분산 → tool_uses 감소 (Phase 2 evaluator 18→? / 24→? 측정 필요 — Cycle 5p+1)

### 2.5.7 적용 시점

| 시점 | Pre-Flight |
| -- | -- |
| multi-step specialist 호출 (Phase 2+ 4 단계 이상) | **의무** |
| 단발 specialist 호출 (1단계 enrich 등) | *권장* (필요 시) |
| non-UE 작업 (vault meta 정리 / governance 등) | skip 가능 |

### 2.5.8 §2.2 self-check 갱신 (Cycle 5p)

§2.2 의 6개 self-check 질문에 다음 7번째 항목 추가 (multi-step UE 코드 작성 시):

7. **PRE-FLIGHT — Engine 본가 grep batch 1회 수행 했나?** 본 §2.5 의 7 항목 (A~G) 중 handoff document 에 해당하는 항목들 batch grep 후 specialist prompt 에 사전 첨부. multi-step UE 코드 작성 시만 적용.

## §3. Phase II — Specialist / Orchestrator MCP 권한 add (점진)

### 3.1. 옵션 비교

| 옵션 | 변경 범위 | 비용 | 효과 |
| -- | -- | -- | -- |
| **B. specialist 전체에 mcwiki 추가** | 12+ specialist 정의 수정 | 토큰 비용 ↑ (각 specialist 컨텍스트에 16 schema) | specialist 안에서 vault 조회 / 자가 인용 가능 |
| **C. orchestrator 만 mcwiki 추가** ⭐ | 1개 agent 정의 수정 | 토큰 비용 ↓ (단일 지점) | orchestrator 가 boundary wrap. specialist 는 그대로 |
| **D. main 만 (Phase I)** | 변경 0 | 0 | main 이 매 boundary wrap. 지금 즉시 가능 |

**권장 = D 즉시 + C 안정화 후**.

### 3.2. C 적용 조건 (안정화 게이트)

다음 3 게이트 모두 통과 시 C 적용:

1. **mcwiki MCP 도구 셋 1개월 변경 없음** — schema 변경이 잦으면 orchestrator 재배포 비용 ↑
2. **boundary 패턴이 main 운영으로 검증** — Phase I 로 최소 10 cycle 운영 후 패턴 안정
3. **orchestrator 의 prompt 가 boundary 5단계를 명문화** — 권한 추가 전 prompt 가 의무 알아야

### 3.3. C 적용 시 변경 사항

```text
plugin_019SPM4GSPfAfagqWFsrexY4/agents/ue-orchestrator.{md,json}
  ├─ tools: [Read, Grep, Glob, Bash]
  │     → [Read, Grep, Glob, Bash,
  │        mcp__MCWiki___UE_5_7_4_Knowledge_Vault__read_index,
  │        ...search, ...read_page, ...write_page, ...append_log,
  │        ...synthesis_seed, ...synthesis_finalize]
  └─ system_prompt: + §5.4 AGENT BOUNDARY 5단계 명시 + §13 Citation 의무
```

`mcpb pack` 으로 .mcpb 재빌드 + manifest.json version bump + Cowork 재install.

### 3.4. Phase II 적용 후 변화

- main 의 boundary wrap 부담 ↓ — orchestrator 가 specialist 호출 + vault 갱신 모두 처리
- main 은 orchestrator 호출 1회 → orchestrator 가 내부에서 specialist N 회 + boundary N 회 wrap
- 토큰 효율 ↑ — main 컨텍스트에 vault 압축 결과 N 회 누적 불필요

---

## §4. boundary 적용 예 (Phase I)

### 4.1. 사례 — "ue-editor-mainframe enrich" 요청

```text
[A. PRE-DELEGATE]
  main → mcwiki:read_index
       → mcwiki:search query="MainFrame" scope="all"
       → mcwiki:read_page kind=sources slug=ue-editor-mainframe
       → mcwiki:read_raw path=raw/ue-wiki-llm/skills/Editor/MainFrame/SKILL.md

  결과: vault 에 source 1건 (4.3 KB, slim 상태), raw 8 KB, IMainFrameModule entity 없음

[B. DELEGATE]
  Task(subagent_type="ue-wiki-llm:ue-editor-specialist",
       prompt=<§2.3 템플릿 + 위 컨텍스트>)

[C. POST-RECEIVE]
  specialist 반환:
    - 작업물: ue-editor-mainframe 본문 5.5 KB (slim 가이드)
    - §13 표: 🟢 8개 (raw 직접 인용) / 🟡 2개 (Slate menu 통합 — vault 부분 근거) / 🔴 1개 (FProjectStatus 시그니처 — vault 없음)
    - 추천: IMainFrameModule entity 신규 + concepts/MainFrame-Lifecycle 검토

[D. FILE-BACK] — 사용자 OK 후
  mcwiki:write_page kind=sources slug=ue-editor-mainframe content=<반환 본문>
  사용자가 entity 신규 OK → write_page kind=entities slug=IMainFrameModule

[E. LOG]
  mcwiki:append_log
    op="query"
    title="ue-editor-mainframe enrich via Task(ue-editor-specialist)"
    body="touched: sources/ue-editor-mainframe, entities/IMainFrameModule (new)
         §13: 🟢8 / 🟡2 / 🔴1
         🔴 FProjectStatus 시그니처 — 추후 검증 후 vault 화"
```

### 4.2. boundary 미적용 시 (현재 함정)

위 사례에서 main 이 §5.4 미적용 시:

- vault 에 이미 4.3 KB source 있는데 specialist 는 raw 부터 다시 읽음 → 토큰 낭비
- IMainFrameModule entity 신규 후보를 사용자가 못 봄 → vault 가 손해
- 🔴 FProjectStatus 시그니처 추론 부분이 🟢 인 척 답변에 섞임 → §13 위반
- log 에 흔적 없음 → 다음 audit (`18_ModelEvolutionAudit`) 가 못 잡음

---

## §5. 위반 감지 — lint 가 못 잡는 부분의 감지법

§5.4 위반은 lint 의 정적 검사로 못 잡는다 (broken-link 도 orphan 도 stale 도 아님). 대신:

1. **수동 audit**: `wiki/log.md` 의 query/synthesis op 비율 vs Task 호출 빈도 비교. Task 가 많은데 log 에 query/synthesis 가 적으면 boundary 부정.
2. **stats.py 확장 후보**: `tools/stats.py` 에 "Task 호출 카운터 vs log mcwiki op 카운터" 추가. boundary 위반 의심 cycle 자동 보고.
3. **사용자 spot-check**: 분기별 `18_ModelEvolutionAudit` 시 boundary §5.4 적용 cycle 표본 추출.

→ Phase II 적용 후엔 orchestrator 안에서 자동 enforce 가능.

### 5.1. 🚨 POST-RECEIVE 파일 검증 방법론 (2026-05-13 보강 — Cycle #3-10 incident 후속)

**함정**: Cycle #3-10 배치 후 main 이 bash `wc -c` 로 사이즈 검증 → 모든 파일이 stub 사이즈로 보임 → INCIDENT 선언. 실제로는 **bash mount stale** (Cowork file tool 의 Write 직후 bash sandbox sync 지연).

| 검증 방법 | 결과 | 비고 |
|----------|------|------|
| ❌ bash `wc -c` / `ls -la` 단독 | false negative 가능 | mount sync 지연 (수 초~수십 초) |
| ✅ file `Read` tool (limit 5-15 라인) | 진짜 view | Cowork file tool 과 동일 mount |
| ✅ mcwiki `read_page` | 진짜 view | MCP server 직접 vault access |
| ⭐ **두 방법 cross-check** | 안전 | file Read + mcwiki read_page 결과 일치 확인 |

**boundary §C POST-RECEIVE 의무 갱신**: specialist 자가 보고 (claim "Files written") 신뢰 X → 반드시 file `Read` 또는 mcwiki `read_page` 로 *실제 본문 첫 15라인* 확인. bash 사이즈 단독 의존 금지.

**진정한 위반**: Cycle #10 specialist 가 mcwiki `append_log` 우회하여 `log.md` 직접 Bash/Edit 한 1건만 *진정 boundary 위반*. main 이 §E LOG 의 유일한 권위 — specialist 가 form 만 맞춰서 직접 작성하면 boundary 부정.

---

## §6. cross-link

- [[CLAUDE.md#§5.4. AGENT BOUNDARY protocol]] — 마스터 schema 의 1단락 의무
- [[00_meta/06_VaultCitationRule]] — §13 Citation 정밀판 (boundary §C 단계의 분류 기준)
- [[00_meta/05_HandoffProtocol]] — 동일 sprint 안 main → main 의 handoff (boundary 와 직교)
- [[00_meta/04_AuditPolicy]] — 분기별 boundary 적용 spot-check
- [[sources/ue-agent-orchestrator]] — Phase II 대상 (현재 mcwiki 권한 없음)
- [[sources/ue-agent-evaluator]] — §13 위반 시 evaluator 평가 감점
- ⭐ [[synthesis/agent-boundary-cycles-2026-q2]] — **Phase II G2 게이트 누적 추적** (live cycle 로그)

---

## §7. 한 줄 정리

> **`Task` tool 로 specialist 호출하는 모든 boundary 에서, main Cowork 가 PRE-DELEGATE QUERY → POST-RECEIVE §13 분해 → FILE-BACK → LOG 5단계를 wrap**. specialist 권한 변경 없이 즉시 가능. 안정화 후 orchestrator 에 MCP 권한 추가 (Phase II) 로 main wrap 부담 ↓.

---

## §8. Cycle Log (Phase II G2 게이트 — 10 cycle 누적 검증)

> 정밀 로그: [[synthesis/agent-boundary-cycles-2026-q2]] (live, 매 cycle 직후 갱신)
>
> 본 절은 *진행률 요약* 만 — 자세한 cycle entry 는 위 synthesis 페이지.

### 8.1 진행률 (2026-05-12 시점)

| 게이트 | 상태 | 진행 |
|--------|------|------|
| G1 mcwiki MCP 도구 셋 1개월 변경 없음 | 🟡 진행중 | 2026-05-12 0.1.9 → 다음 변경 없을 시 2026-06-12 통과 |
| **G2 Phase I 최소 10 cycle 운영 검증** | ✅ **PASS** | **10 / 10** (100%) · 누적 보너스 37건 (조건 2 740% 통과) · 평균 토큰 ~68 KB/cycle (조건 3 ✅) |
| G3 orchestrator system_prompt 가 §5.4 5단계 명문화 | 🔴 미시작 | plugin 수정 필요 |

### 8.2 cycle 등록 표준 프로토콜

매 specialist 호출 직후 main 이:

1. `read_page kind=synthesis slug=agent-boundary-cycles-2026-q2` — 현재 cycle 로그 읽음
2. `write_page` — §4 cycle 로그에 새 entry append (5-step self-check ✅ 표 + 정량 메트릭)
3. 집계 메트릭 갱신 (평균 + 비율 + 누적 카운트 + G2 진행률 n/10)
4. cycle #10 도달 시 §6 Phase II 결정 트리 적용

상세 메트릭 / 결정 트리 / 자기 추적 = [[synthesis/agent-boundary-cycles-2026-q2]].
