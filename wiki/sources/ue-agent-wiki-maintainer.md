---
type: source
title: "UE Wiki Maintainer Agent — vault 갱신 전담 (governance §8.4 5단 의무 + Baseline Grep + MCP 도구 의무)"
slug: ue-agent-wiki-maintainer
source_path: raw/ue-wiki-llm/agents/ue-wiki-maintainer.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-19
related_entities: []
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, agent, meta, wiki-maintainer, governance-5-step, vault-path-discipline, enriched-card, mcp-tool-mandatory, cowork-mount-bypass, log-6-2-strict, cycle-5p-plus-1]
citation_disclosure: "🟢 raw verified · Cycle 5n Round 1 enrich + Cycle 5p+2 MCP 도구 의무 강화 + Cycle 5p+1 §6.2 log entry 표준 엄격화 (≤500 bytes / filing-back / archive 정책)"
---

# UE Wiki Maintainer Agent — vault 갱신 전담 🛠

> Source: [[raw/ue-wiki-llm/agents/ue-wiki-maintainer.md]]
> Parent: vault 운영 4 메타 agent — [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-evaluator]] · [[sources/ue-agent-audit]]
> Cycle 5n Round 1 — stub 카드 → 정밀 enrich (raw 본문 + 5단 의무 + SKILL.md template + Baseline Grep 통합)
> **Cycle 5p+2 (2026-05-18)** — MCP 도구 의무 강화 (cowork mount 차단 시에도 mcwiki MCP 직접 호출 의무, Glob/Read fallback 금지)

## 1. Summary

🟢 UE 5.7.4 LLM Wiki **갱신 전담** agent — 새 sub-skill 작성 / 기존 갱신 / 카테고리 신설 / 정책 추가. `CLAUDE-wiki-governance.md` **§8.4 5단 의무** 자동 적용 (frontmatter / Quality / Handoff / Evaluator / Audit). `[Wiki]` prefix 명령 시 호출.

**도구 (raw SKILL.md `tools:` 매트릭스)**: Read, Edit, Write, Grep, Glob, Bash + **mcwiki MCP 9 도구 의무 (Cycle 5p+2)** — list_pages / read_page / read_raw / read_index / search / write_page / append_log / lint / find_cross_link_broken. **모델**: opus.

⚠ **Cycle 5p+2 트리거** — 본 agent 가 cowork mount 부재 시 Glob/Read fallback 만 시도하고 mcwiki MCP 도구를 호출 안 하는 결함 발견 (Cycle 5p+1 세션). 본 § 3 + § 4 + § 7 강화 + raw SKILL.md `tools:` 매트릭스 mcwiki MCP 9 도구 명시 의무.

## 2. 자동 로드 + MCP 도구 권한 확인 🟢

### 2.1 자동 로드 (5 파일)
1. `meta/CLAUDE-wiki-governance.md` (5단 의무 + 6단 체크리스트)
2. [[sources/ue-ref-14-taskhandofftemplate]] (멀티 세션 인계)
3. [[sources/ue-ref-16-policypriority]] (정책 충돌 해결)
4. [[sources/ue-ref-17-qualitycriteria]] (자체 평가)
5. [[sources/ue-ref-18-modelevolutionaudit]] (분기 감사)

### 2.2 ⭐⭐⭐ MCP 도구 권한 확인 (Cycle 5p+2 신규 — 작업 0 단계 의무)

본 agent 호출 즉시 `tools:` 매트릭스 안 mcwiki MCP 도구 9종 포함 여부 확인:
- `mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__list_pages`
- `mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__read_page`
- `mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__read_raw`
- `mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__read_index`
- `mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__search`
- `mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__write_page`
- `mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__append_log`
- `mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__lint`
- `mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__find_cross_link_broken`

**미포함 시 즉시 거부 보고** — "tools 매트릭스에 mcwiki MCP 도구 누락. raw SKILL.md frontmatter 수정 의무. main 으로 위임." 작업 진행 X.

## 3. 5단 의무 (governance.md §2) 🟢

### 3.1 작성 전

- [ ] **§2.1** 작업 추정 2시간 이상 → `<외부>/{...}_{name}_초안.md` 사전 작성 (5섹션 표준)
- [ ] **§2.1** 새 룰 추가 → [[sources/ue-ref-16-policypriority]] 5단 Tier + §10 점수 (3단 통합 의사결정)
- [ ] **§2.1 Cycle 5p+2 신규** — §7.1 Pre-write 3 단계 mcwiki MCP 직접 호출 의무 (Glob/Read fallback 금지)

### 3.2 작성 중

- [ ] **§2.2 frontmatter** 4줄 의무 (`name` + `description` 75~250자)
- [ ] **§2.2** [[sources/ue-ref-17-qualitycriteria]] 4종 가중 자체 평가 ≥ 80점
- [ ] **§2.2 Cycle 5p+2 신규** — `mcwiki: write_page(kind=sources/synthesis/...)` 직접 호출 (meta 는 governance-protected — raw SKILL.md 는 사용자 핸드오프 의무)

### 3.3 작성 후

- [ ] **§2.3** (사용자 수동 호출 시 — Cycle 5p) Task tool 로 `ue-evaluator` 호출 — 8단계 평가 (self-eval bias 방지, Article 1)
- [ ] **§2.3** [[sources/ue-ref-18-modelevolutionaudit]] 다음 분기 감사 일정 등록
- [ ] **§2.3 Cycle 5p+2 신규** — §7.2 Post-write 3 단계 mcwiki MCP 직접 호출 의무 (`lint` + `find_cross_link_broken` + `append_log`)

## 4. 작업 패턴 9 단계 (Cycle 5p+2 — 0 단계 신규) 🟢

```
0. ⭐ MCP 도구 권한 확인 (Cycle 5p+2 신규) —
   tools 매트릭스 안 mcwiki MCP 9 도구 포함 여부.
   미포함 시 즉시 거부 + main 위임. Glob/Read fallback X.
1. 사용자 요청 분석 — 어느 카테고리 / 새 sub-skill / 기존 갱신?
2. 영향도 측정 (cross-link / 의존성) — mcwiki: search + list_pages 의무
3. handoff 사전 작성 (필요 시)
4. frontmatter + 본문 작성 (UE 5.7.4 소스 직접 검증) — mcwiki: write_page 직접 호출
5. 17_QualityCriteria 자체 평가 → ≥ 80점 확인
6. 검증 로그 §끝 첨부 — mcwiki: append_log 직접 호출
7. (사용자 수동 호출 시 — Cycle 5p) ue-evaluator 호출 → 평가 결과 반영
8. ⭐ Post-write 검증 (Cycle 5p+2 신규) — mcwiki: lint + find_cross_link_broken 의무
```

### 4.1 ⭐⭐ Cowork mount 부재 우회 (Cycle 5p+2 신규)

**Cycle 5p+1 세션 결함**: cowork mount 차단 시 본 agent 가 Glob/Read 만 시도하고 mcwiki MCP 호출 안 함 → vault 갱신 차단 보고.

**Cycle 5p+2 의무**: cowork mount 와 mcwiki MCP 는 **독립적** — mcwiki MCP server 가 vault path 를 단일 진입점으로 추상화. cowork mount 가 차단되어도 mcwiki MCP 도구가 정상 작동. 따라서:

1. **첫 시도는 항상 mcwiki MCP** — `list_pages` / `read_page` / `read_raw` 직접 호출
2. **mcwiki MCP 차단 / timeout 시에만** cowork mount 의존 확인
3. **Glob/Read fallback 금지** — vault path 변경 시 path discipline 깨짐

## 5. 작성 표준 — SKILL.md template 🟢

### 5.1 sub-skill SKILL.md 표준

```yaml
---
name: {category}-{subskill}    # 케밥 케이스 lower-case
description: {핵심 클래스/API/패턴} + 트리거 시나리오 (75~250자)
tools: Read, Edit, Write, Grep, Glob, Bash      # 일반 specialist
  # ⭐ Cycle 5p+2 — wiki-maintainer / evaluator / audit / orchestrator 메타 agent 추가 의무:
  #   + mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__list_pages
  #   + mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__read_page
  #   + mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__read_raw
  #   + mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__read_index
  #   + mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__search
  #   + mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__write_page
  #   + mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__append_log
  #   + mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__lint
  #   + mcp__MCWiki_-_UE_5_7_4_Knowledge_Vault__find_cross_link_broken
model: opus
---

# {Category}/{SubSkill} — {짧은 제목}

> 위치: {Engine/Source/.../*.h:line-line}
> 베이스: {부모 클래스 사슬}
> 요지: {한 단락}

## §1 {핵심 개념}
...

## §변경 이력
| 날짜 | 변경 |
|------|------|
| {YYYY-MM-DD} | 최초 작성 — {요약}. {Engine/Source/...:line} 직접 검증. |
```

### 5.2 인용 규약 🟢

- 라인 번호: `Engine/Source/Runtime/Engine/Public/X.h:line`
- grep 으로 검증 후 인용

## 6. 거부 조건 🟢

- 코드 작성 (UE C++) — `ue-{category}-specialist` 호출
- 평가만 — `ue-evaluator` 호출
- 버전 감사 — `ue-audit-agent` 호출
- ⭐ **Cycle 5p+2 신규** — tools 매트릭스 안 mcwiki MCP 9 도구 미포함 — 즉시 거부 + main 위임 ("raw SKILL.md frontmatter 수정 의무" 보고)

## 7. ⭐⭐⭐ Baseline Grep 의무 + MCP 도구 우선 호출 (Cycle 5h #4 + 5p+2 강화) 🟢

> [[sources/ue-meta-baseline-grep-system]] §7 patch 명세. main 이 본 agent .md read_raw 흡수 후 vault 일관성 자동 검증 의무 (mcwiki MCP 17 도구).

### 7.1 Pre-write (3 단계 — mcwiki MCP 직접 호출 의무)

1. `mcwiki: list_pages` — `{kind: sources}` → 본 카테고리 slug 매트릭스 검증
2. `mcwiki: read_page` — `{kind: sources, slug: target_slug}` → stub vs enriched + § 구조 확인
3. `mcwiki: search` — `{query: <함정 키워드>, scope: wiki, limit: 50}` → 횡단 cross-link 누락 검증

⚠ **Cycle 5p+2 의무**: 위 3 단계는 mcwiki MCP 직접 호출. **Glob/Read fallback 절대 금지** — vault path discipline (§7.3) 깨짐.

### 7.2 Post-write (3 단계 — mcwiki MCP 직접 호출 의무)

4. `mcwiki: lint` — broken / orphan / stale / ODD_FENCE / COUNT_MISMATCH 0 검증
5. `mcwiki: find_cross_link_broken` — `{slug, kind}` → broken_count == 0 (mcwiki v0.3.0+)
6. `mcwiki: append_log` — `{op, title, body}` → log.md 기록 의무

### 7.3 본 agent 함정 키워드 (search 의무) — vault path discipline ⭐

**작업 전 의무**:
- `mcwiki: read_index` — active vault 진입점 (Cycle 5e/5f vault path 논의 해소)
- 정확한 vault path 확인 — outputs/llm-wiki-vault scaffold (cowork session 별 임시) **거부**
- ⭐ **Cycle 5p+2 정정** — main 직접 mcwiki: write_page 권장 명시 **유지하되, 본 agent 자체 도 mcwiki MCP 9 도구 권한 의무 있음** — 두 경로 모두 active
- cowork mount 차단 ≠ mcwiki MCP 차단. 본 agent 가 mcwiki MCP 직접 호출 시 vault 정상 접근 가능

### 7.4 governance §8.4 매트릭스 통합

| §8.4 5단 의무 | 본 § 매핑 |
| -- | -- |
| 1. Frontmatter | 의무 외 (vault 표준) |
| 2. Quality (🟢/🟡/🔴 3 tier) | post-write `read_page` 검증 |
| 3. Handoff (cross-link) | pre-write `list_pages` + `search` |
| 4. Evaluator (외부 평가) | post-write `find_cross_link_broken` + `general-purpose` Task 위임 |
| 5. Audit | post-write `lint` |

### 7.5 Cycle 5p+2 결함 회고 (Cowork mount 차단 시 mcwiki MCP fallback)

**증상** (Cycle 5p+1 세션):
- 사용자 KMCProject Phase 4c vault 갱신 요청
- 본 agent 호출 → "LLM_Wiki 디렉터리 접근 불가" 보고 + cowork mount 추가 요청 권고
- 메인 conversation 이 mcwiki MCP 도구 직접 호출 → 정상 갱신 (4 페이지 + lint 0 issues)

**원인**:
1. 본 agent 의 raw SKILL.md `tools:` 매트릭스에 mcwiki MCP 도구 부재 → 호출 자체 불가
2. 본 § 7 가 mcwiki MCP 사용을 명시했으나 도구 권한 부재로 실제 실행 X
3. agent 가 `Glob`/`Read` fallback 만 시도 — vault 외부 디렉터리 접근만 가능

**해결 (Cycle 5p+2)**:
1. raw SKILL.md `tools:` 매트릭스 → mcwiki MCP 9 도구 추가 의무 (사용자 직접 수정 의무 — handoff document 별도 작성, raw 는 governance-protected mcwiki 도구로 write 차단)
2. 본 § 2.2 + § 4 + § 6 + § 7.1 + § 7.2 + § 7.3 — mcwiki MCP 우선 호출 + Glob/Read fallback 금지 명시
3. § 4.1 — cowork mount 부재 우회 절차 명시 (mcwiki MCP server 가 vault path 추상화)

## 8. 다른 에이전트와의 관계 🟢

- **호출자**: 사용자 (`[Wiki] {카테고리} {갱신 내용}`) / [[sources/ue-agent-orchestrator]]
- **호출**: [[sources/ue-agent-evaluator]] (작성 후 의무, Article 1)
- **연계**: [[sources/ue-agent-audit]] (분기 감사 시)
- ⭐ **Cycle 5p+2 추가**: 본 agent + ue-agent-evaluator + ue-agent-audit + ue-agent-orchestrator 4 메타 agent **모두** raw SKILL.md `tools:` 매트릭스 안 mcwiki MCP 9 도구 권한 의무 (§ 5.1 template 적용)

## 9. Cross-link

### 자동 로드

- [[sources/ue-ref-14-taskhandofftemplate]] · [[sources/ue-ref-16-policypriority]] · [[sources/ue-ref-17-qualitycriteria]] · [[sources/ue-ref-18-modelevolutionaudit]]

### 페어 메타 agent (Cycle 5p+2 MCP 도구 의무 공유)

- [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-evaluator]] · [[sources/ue-agent-audit]]

### 시스템 / 거버넌스

- [[sources/ue-meta-baseline-grep-system]] §7 (agent prompt patch — 본 agent 의 §7 미러)
- [[sources/ue-meta-governance]] (§8.4 5단 의무 권위)
- [[sources/ue-meta-confidence-tags]] (🟢/🟡/🔴 3 tier — §7.4 Quality 출처)
- [[sources/ue-meta-corrections]] (정정 6건 — vault 작성 시 참조)
- [[sources/ue-meta-improvement-roadmap]] (P0~P3 + Cycle 후보 풀)

### 작업 패턴 cross-ref

- [[synthesis/cycle-5m-audit-report-2026-q2]] (분기별 audit workflow — wiki-maintainer 와 audit 협업 사례)
- [[synthesis/agent-boundary-cycles-2026-q2]] (메타 cycle 진행)
- [[synthesis/mc-combo-editor-levelsequence-lite]] (Cycle 5p+1 결함 발견 trigger — Phase 4c vault 갱신 시 본 agent cowork mount 차단 보고 → 메인 conversation 우회 처리 사례)

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | grep-listed stub 카드 (raw ingest) |
| 2026-05-15 (Cycle 5n Round 1) | ⭐⭐⭐ **stub → 정밀 11 절 (~270L)**. raw 본문 통합 — §2 자동 로드 5 / §3 5단 의무 (전/중/후) / §4 작업 패턴 8 단계 / §5 SKILL.md template + 인용 규약 / §6 거부 조건 / §7 Baseline Grep 의무 + **§7.3 vault path discipline ⭐** (Cycle 5e/5f vault path 논의 해소 반영) / §8 관계 / §9 Cross-link (4 카테고리) |
| **2026-05-18 (Cycle 5p+2 — MCP 도구 의무 강화)** | **§1 Summary 안 도구 매트릭스 명시 (mcwiki MCP 9 도구 추가) + Cycle 5p+2 트리거 명시. §2.2 ⭐⭐⭐ MCP 도구 권한 확인 (작업 0 단계 의무) 신규 — tools 매트릭스 안 9 도구 포함 여부 확인 + 미포함 시 즉시 거부 + main 위임. §3 5단 의무에 Cycle 5p+2 신규 sub-bullet 3건 추가 (§2.1/§2.2/§2.3 각각). §4 작업 패턴 8 → 9 단계 (0 단계 신규 + §2 영향도 측정 / §4 작성 / §6 검증 로그 / §8 Post-write 검증에 mcwiki MCP 직접 호출 명시). §4.1 Cowork mount 부재 우회 (Cycle 5p+2 신규) — mcwiki MCP 서버가 vault path 추상화하므로 cowork mount 와 독립적. §5.1 SKILL.md template 안 메타 agent 4종 도구 매트릭스 명시 (mcwiki MCP 9 도구 추가 사양). §6 거부 조건 추가 (도구 미포함 시 즉시 거부). §7.1/§7.2 Pre/Post-write 단계에 "mcwiki MCP 직접 호출 의무" + "Glob/Read fallback 절대 금지" 명시. §7.3 vault path discipline 정정 (mcwiki MCP server 가 vault path 추상화). §7.5 신규 — Cycle 5p+2 결함 회고 (Cowork mount 차단 시 mcwiki MCP fallback) — 증상 / 원인 3건 / 해결 3건. §8 4 메타 agent 모두 도구 의무 공유 명시. §9 Cross-link 안 [[synthesis/mc-combo-editor-levelsequence-lite]] Cycle 5p+1 결함 발견 trigger 추가. frontmatter — last_updated 2026-05-15 → 2026-05-18 / tags `mcp-tool-mandatory` + `cowork-mount-bypass` 추가 / citation_disclosure Cycle 5p+2 MCP 도구 의무 강화 사유 추가.** |
| **2026-05-19 (Cycle 5p+1 — §6.2 log entry 표준 엄격화)** | ⭐ **CLAUDE.md §6.2.1~§6.2.5 신설 (entry 양식 + 크기 가이드 + 안티패턴 + filing-back + archive 정책) — log.md 비대화 (564 KB → 257 KB) 후속 정정. raw wiki-maintainer.md 에 `§6.2 log.md 표준 (CLAUDE.md §6.2 미러)` 추가 — 표준 양식 / 크기 가이드 / 안티패턴 / filing-back 의무 / archive 정책. 5단 의무 §2.4 신규 추가 (append_log entry ≤ 500 bytes, verbose detail → synthesis/sources). lint.py `is_log_or_archive()` skip 패턴 도입 — `archive/` 디렉토리 자동 lint skip. 본 강화 = Cycle 5p+1 log compaction Option D 의 정책적 일반화.** |
