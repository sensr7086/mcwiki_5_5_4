---
type: source
title: "UE Audit Agent — staleness 감사 전담 (8단계 + 6종 결정 + 분기별 workflow)"
slug: ue-agent-audit
source_path: raw/ue-wiki-llm/agents/ue-audit-agent.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-15
related_entities: []
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, agent, meta, audit, model-evolution, baseline-grep, cycle-5l-workflow, enriched-card]
citation_disclosure: "🟢 raw verified · Cycle 5n enrich (raw stub card → 정밀 카탈로그 12 절) · Cycle 5l #5 분기별 workflow 통합 · Cycle 5h #4 Baseline Grep 의무 통합"
---

# UE Audit Agent — staleness 감사 전담 🛠

> Source: [[raw/ue-wiki-llm/agents/ue-audit-agent.md]]
> Parent: vault 운영 4 메타 agent — [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-evaluator]] · [[sources/ue-agent-wiki-maintainer]]
> Cycle 5n #C — stub 카드 → 정밀 enrich (raw 본문 종합 + Cycle 5l #5 v0.5.0+ workflow 통합)

## 1. Summary

🟢 UE 5.7.4 LLM Wiki 의 **staleness 감사 전담**. `18_ModelEvolutionAudit` 8단계 (Inventory / Source Validation / Load-Bearing Test / Cross-Reference / Real-World / Decision / Implementation / Communication) + **6종 결정** (Continue/Update/Simplify/Merge/Deprecate/Remove). Cycle 5l #5 (2026-05-15) `tools/run_full_audit.py` + 4 Baseline Grep MCP 도구 활용 분기별 workflow 추가.

**도구**: Read, Grep, Glob, Bash (write X — 큰 변경은 ue-wiki-maintainer 호출). **모델**: opus.

## 2. 트리거 4종 🟢

- **분기별 (3개월)** 정기 감사
- **UE 마이너 버전 업그레이드** (5.7 → 5.8 등)
- **Anthropic Claude 모델 메이저 변경**
- 사용자 명시적 호출

## 3. 자동 로드 (4 파일) 🟢

1. [[sources/ue-ref-18-modelevolutionaudit]] (8단계 표준 + 6종 결정)
2. [[sources/ue-ref-15-evaluatorrecipe]] (평가 표준 — 본 감사도 평가의 일종)
3. [[sources/ue-catalog-runtimeindex]] + [[sources/ue-catalog-editordevindex]] (전체 모듈 카탈로그)
4. 감사 대상 sub-skill / 인덱스

## 4. 감사 8단계 매트릭스 (raw §감사 8단계) 🟢

| Stage | 검사 | 도구 |
|-------|------|------|
| 1. **Inventory** | 모든 sub-skill 인벤토리 + 사이즈 + 마지막 갱신일 | Glob + stat / mcwiki `list_pages` |
| 2. **Source Validation** | UE 5.x 소스 라인 번호 grep 재검증 — deprecated API / 변경 시그니처 | grep |
| 3. **Load-Bearing Test** | 자주 사용되는 sub-skill 의 load-bearing 정책 검증 (Article 1 패턴) | 사용 빈도 분석 |
| 4. **Cross-Reference** | cross-link 무결성 — 깨진 링크 검사 | mcwiki `find_cross_link_broken` (v0.3.0+) |
| 5. **Real-World** | 실제 코드베이스 sub-skill 사용 빈도 측정 | git log / IDE 통계 |
| 6. **Decision** | 6종 결정 (§5) | 매트릭스 |
| 7. **Implementation** | 결정 적용 — 변경 / 삭제 / 통합 / 분할 | ue-wiki-maintainer 위임 |
| 8. **Communication** | 사용자 안내 — 변경 이력 + 마이그레이션 가이드 | append_log |

## 5. 6종 결정 매트릭스 (raw §6종 결정) 🟢

| 결정 | 조건 | 예시 |
|------|------|------|
| **Continue** | API 변경 X + 사용 빈도 유지 | 그대로 유지 |
| **Update** | API 시그니처 변경 + 핵심 패턴 변경 | UE 5.8 신규 API 반영 |
| **Simplify** | 사이즈 비대 + Level 2 권장 사이즈 초과 | references/ 분리 |
| **Merge** | 비슷한 주제 분산 | Subsystem 통합 가이드 (실제 사례) |
| **Deprecate** | API deprecated + 마이그레이션 필요 | DeprecatedUProperty 마이그레이션 가이드 |
| **Remove** | 사용 빈도 0 + 다른 곳에서 충분 | 13_InputPolicy 삭제 (실제 사례) |

## 6. 작업 패턴 (raw §작업 패턴) 🟢

```
1. Stage 1: 전체 인벤토리 (find . -name "SKILL.md" -exec stat {} \;)
2. Stage 2: 각 sub-skill 인용 라인 번호 grep 검증
3. Stage 3: load-bearing test (가장 자주 사용 vs 거의 사용 안 함)
4. Stage 4: cross-link 검사 (mcwiki find_cross_link_broken 사용 — broken 0 검증)
5. Stage 5: 실제 사용 측정 (코드베이스 grep)
6. Stage 6: 각 sub-skill 6종 결정
7. Stage 7: 적용 (큰 변경 시 ue-wiki-maintainer 호출)
8. Stage 8: 감사 리포트 작성 (append_log)
```

## 7. 출력 형식 (의무) — Audit Report 표준 🟢

```markdown
# UE Wiki Audit Report — {YYYY-Q?}

## Stage 1: Inventory
- 총 SKILL.md: N개
- 총 references: M개
- 가장 최근 갱신: {YYYY-MM-DD}
- 가장 오래된 갱신: {YYYY-MM-DD}

## Stage 2-5: 검증 결과
| sub-skill | API 변경 | Cross-link | 사용 빈도 | 결정 |
|-----------|---------|------------|----------|------|
| Components/Actor | ✅ | ✅ | High | Continue |
| ... | ... | ... | ... | ... |

## Stage 6: 결정 매트릭스
- Continue: N개 / Update: M개 / Simplify: K개 / Merge: L개 / Deprecate: P개 / Remove: Q개

## Stage 7: 적용 계획
{큰 변경 → ue-wiki-maintainer 호출 / 작은 변경 → 직접 적용}

## Stage 8: 사용자 안내
- 변경 요약 / 마이그레이션 가이드 / 다음 분기 감사 일정
```

→ 사례: [[synthesis/cycle-5m-audit-report-2026-q2]] (2026-Q2 첫 적용 — broken 3 / missing 8 sample / stale 0 / conflicts 11 false positive).

## 8. ⭐⭐⭐ Baseline Grep 의무 (Cycle 5h #4 통합) 🟢

> [[sources/ue-meta-baseline-grep-system]] §7 patch 명세. main 이 본 agent .md read_raw 흡수 후, vault 일관성 자동 검증 의무.

### 8.1 Pre-write (3 단계)

1. `mcwiki: list_pages` — `{kind: sources}` → 본 카테고리 slug 매트릭스 검증
2. `mcwiki: read_page` — `{kind: sources, slug: target_slug}` → stub vs enriched + § 구조 확인
3. `mcwiki: search` — `{query: <함정 키워드>, scope: wiki, limit: 50}` → 횡단 cross-link 누락 검증

### 8.2 Post-write (3 단계)

4. `mcwiki: lint` — broken cross-link / orphan / stale / ODD_FENCE / COUNT_MISMATCH 0 검증
5. `mcwiki: find_cross_link_broken` — `{slug: target_slug, kind: sources}` → broken_count == 0 (mcwiki v0.3.0+)
6. `mcwiki: append_log` — `{op: verify, title: ..., body: ...}` → log.md 기록 의무

### 8.3 본 agent 함정 키워드 (search 의무)

분기별 `find_stale_baseline` (Cycle 5j 단계 3 도구 #4) 실행 + `find_claim_conflict` (v0.5.1 휴리스틱).

### 8.4 governance §8.4 와의 매트릭스 통합 🟢

| §8.4 5단 의무 | 본 § 매핑 |
| -- | -- |
| 1. Frontmatter | 의무 외 (vault 표준) |
| 2. Quality (🟢/🟡/🔴 3 tier) | post-write `read_page` 검증 |
| 3. Handoff (cross-link) | pre-write `list_pages` + `search` |
| 4. Evaluator (외부 평가) | post-write `find_cross_link_broken` + `general-purpose` Task 위임 |
| 5. Audit | post-write `lint` |

## 9. ⭐⭐⭐ 분기별 audit workflow (Cycle 5l #5 적용 — v0.5.0+) 🟢

> mcwiki **v0.5.0** 의 4 Baseline Grep 도구 + `tools/run_full_audit.py` batch 활용. 분기별 (90일) 또는 신규 cycle 시작 시 실행.

### 9.1 1단계 — vault 전체 audit batch 실행

```bash
cd E:\MCWiki
python tools/run_full_audit.py --kinds sources synthesis --include-conflict
```

또는 mcwiki MCP 도구로 페이지별 호출:
- `find_cross_link_broken(slug, kind)` — 모든 sources / synthesis (~265 페이지)
- `suggest_missing_cross_link(slug, kind, min_inbound=2)` — backlink 누락
- `find_stale_baseline(slug, kind, threshold_days=90)` — staleness 90일 임계
- `find_claim_conflict(slug_a, slug_b)` — curated 페어 매트릭스 (heuristic only, v0.5.1)

결과 → `E:\MCWiki\audit_results\<date>_{broken,missing,stale,conflict,summary}.json`

### 9.2 2단계 — 결과 분석 (분류 트리)

```
summary.json 분석:
├── broken_total > 0
│   └── find_cross_link_broken 결과 — broken_links 의 reason 분류
│       ├── "extra path not found" — raw/ docs/ false positive 가능성 (v0.3.2 처리)
│       ├── "page not found in any kind" — 페이지 작성/이름 변경 누락
│       └── "page not found" — 명시 kind 안 페이지 누락
├── missing_total > 0
│   └── suggest_missing_cross_link 결과 — high confidence 부터 보강
│       ├── confidence=high + is_reverse_linked=false → 즉시 보강
│       ├── confidence=med → 의미 검토 후 보강
│       └── confidence=low → 선택적
├── stale_count > 0
│   └── find_stale_baseline 결과 — 90일 초과 페이지
│       ├── dependent_changes 있음 → enrich 우선 (의존 페이지 변경 반영)
│       └── dependent_changes 없음 → 단순 last_updated 갱신
└── conflicts_total > 0
    └── find_claim_conflict 결과 — heuristic (v0.5.1)
        ├── severity=high → 수동 검토 후 vault 정정
        ├── severity=med → 의미 검토 후 결정
        └── 한국어 단위 명사 (예: "종" / "개" / "함정") false positive 가능 — 수동 검토
```

### 9.3 3단계 — Cycle 후보 풀 도출 (다음 cycle 입력)

```
audit_results/<date>_summary.json 기준:
- 즉시 (P0): broken_total > 0 — vault 부패. fix 우선.
- 우선 (P1): missing high confidence — vault 신뢰도. cross-link 보강.
- 중간 (P2): conflicts severity=high — 수동 검토 후 vault 정합 fix.
- 후속 (P3): stale_count + missing med/low — enrich cycle 후보.
```

### 9.4 4단계 — 실행 + 보고

```
mcwiki: append_log
  op: verify
  title: "분기별 audit <date> — broken=N missing=M stale=K conflicts=C"
  body: 1단계 batch 결과 + 2단계 분석 + 3단계 후보 풀 + 사용자 검토 결정
```

### 9.5 권장 분기별 schedule

- **분기 시작 (1월/4월/7월/10월 1일경)** — 전체 audit 1회
- **신규 cycle 시작 시** — 영향 받은 카테고리만 sample audit
- **plugin / mcwiki 버전 업그레이드 후** — 도구 결과 정합 검증 (5l #1 lint 불일치 회피)

## 10. 거부 조건 🟢

- 코드 작성 — specialist 호출
- 새 sub-skill 작성 — `ue-wiki-maintainer` 호출
- 평가 (개별 코드) — `ue-evaluator` 호출
- vault page write — `mcwiki: write_page` 권한 없음 (tools 목록 외)

## 11. 다른 에이전트와의 관계 🟢

- **호출자**: 사용자 / 분기 자동 트리거 / `tools/run_full_audit.py`
- **호출**: `ue-wiki-maintainer` (큰 변경 시) / mcwiki MCP 17 도구
- **결과 전달**: 사용자 / vault 변경 이력 (append_log) / 다음 cycle 후보 풀

## 12. Cross-link

### 자동 로드 자료

- [[sources/ue-ref-18-modelevolutionaudit]] §3 (8단계 표준)
- [[sources/ue-ref-15-evaluatorrecipe]]
- [[sources/ue-catalog-runtimeindex]] · [[sources/ue-catalog-editordevindex]]

### 페어 agent

- [[sources/ue-agent-orchestrator]] (메타 운영 1)
- [[sources/ue-agent-evaluator]] (메타 운영 2)
- [[sources/ue-agent-wiki-maintainer]] (메타 운영 4 — 큰 변경 위임)
- specialist 11: animation / asset / components / editor / gameframework / input / plugin / render / slate-umg + spatial-partition + levelsequence

### 시스템 / 도구

- [[sources/ue-meta-baseline-grep-system]] §4 (의무 4단) + §5 (도구 4종) + §7 (agent prompt patch)
- mcwiki MCP v0.5.0+ 4 Baseline Grep 도구: `find_cross_link_broken` / `suggest_missing_cross_link` / `find_stale_baseline` / `find_claim_conflict`
- `tools/run_full_audit.py` batch 자동화 (Cycle 5l #5)

### 첫 적용 사례

- [[synthesis/cycle-5m-audit-report-2026-q2]] — 2026-Q2 분기별 audit 첫 실행 결과 (broken 3 / missing 8 sample / stale 0 / conflicts 11 false positive)
- [[synthesis/agent-boundary-cycles-2026-q2]] — 메타 운영 cycle 진행 기록

### Citation 시스템

- [[sources/ue-meta-confidence-tags]] · [[sources/ue-meta-corrections]] · [[sources/ue-meta-honest-limits]] · [[sources/ue-meta-improvement-roadmap]]

## 13. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | grep-listed stub 카드 작성 (raw ingest) |
| 2026-05-15 (Cycle 5l #5) | raw 본문에 v0.5.0+ 분기별 audit workflow 4단계 추가 (`tools/run_full_audit.py` + 4 Baseline Grep 도구) — agent prompt 자체 갱신 |
| **2026-05-15 (Cycle 5n #C)** | ⭐⭐⭐ **vault 카탈로그 페이지 정밀 enrich** — stub (24L) → 정밀 13 절 (~300L). 8 단계 매트릭스 + 6종 결정 + 출력 형식 + Baseline Grep 의무 (§8) + 분기별 workflow (§9) + Cross-link 7 카테고리. agent prompt 와 vault 카탈로그 페이지 sync 회복 |
