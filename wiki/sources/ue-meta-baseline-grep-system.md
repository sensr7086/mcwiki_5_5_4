---
type: source
title: "ue-meta — Baseline Grep System (specialist agent vault 페어 자동 검증)"
slug: ue-meta-baseline-grep-system
source_path: (vault meta — Cycle 5e/5f/5g/5h 합성)
source_kind: synthesis
source_date: 2026-05-15
ingested: 2026-05-15
last_updated: 2026-05-15
related_entities: []
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, meta, baseline-grep, evaluator-self-correction, specialist-agents, mcp-tool-spec-cycle-5g, pr-request-cycle-5h, agent-prompt-patch-cycle-5h]
citation_disclosure: "🟢 design verified · Cycle 5e #12 단계 1 + Cycle 5f #3 단계 2 + Cycle 5g #4 단계 3 도구 4종 + Cycle 5h #3+#4 PR 요청서 + agent prompt 패치 명세"
---

# Baseline Grep System — specialist agent vault 페어 자동 검증

> 11 specialist + main orchestrator 의 vault 페어 페이지 **staleness / cross-link 누락 / claim 충돌 자동 검증** 시스템.
>
> Cycle 5e #12 = 단계 1 카탈로그 / Cycle 5f #3 = 단계 2 의무 / Cycle 5g #4 = 단계 3 도구 명세 / **Cycle 5h #3+#4 = PR 요청서 + agent prompt 패치 명세**.

## 1. Summary

🟢 **3 단계 + 2 명세 (전체 매트릭스)**:
1. **단계 1 (Cycle 5e 1차)** — specialist baseline 매트릭스 + grep query 카탈로그
2. **단계 2 (Cycle 5f #3)** — specialist agent prompt 의무 4단 명문화
3. **단계 3 (Cycle 5g #4)** — mcwiki MCP 도구 4종 상세 명세
4. **PR 요청서 (Cycle 5h #3)** — 도구 #1 `find_cross_link_broken` 구현 PR 형식 명세
5. **agent prompt 패치 (Cycle 5h #4)** — 11 specialist 의 prompt patch 명세 (governance protected 영역의 vault 측 미러)

## 2. specialist 11 baseline 매트릭스 (단계 1) 🟢

(매트릭스 유지 — Cycle 5e 1차 카탈로그)

| specialist | page list | 함정 키워드 grep |
|------------|-----------|----------------|
| ue-animation-specialist | `ue-animation-*` (9) | `UAnimInstance` / `FAnimNode_` / `AnimNotify` / `URO` / `IKRig` |
| ue-asset-specialist | `ue-assetclasses-*` (12) | `TSoftObjectPtr` / `FStreamableHandle` / `UAssetManager` / `Cooked` / `LOD` |
| ue-components-specialist | `ue-components-*` (17) | `UActorComponent` / `Mobility` / `Tick` / `CDO` / `GetOwner` |
| ue-editor-specialist | `ue-editor-*` (26) | `ToolMenus` / `OnRegisterTabs` / `OnRegisterTabsForEditor` / `IDetailsView::SetObject` / `WorkflowOrientedApp` / forward declare |
| ue-gameframework-specialist | `ue-gameframework-*` (8) | `AActor` / `BeginPlay` / `EndPlay` / `Possession` / `SpawnActor` |
| ue-input-specialist | `ue-input-*` (6) | `UInputAction` / `IMC` / `ETriggerEvent` / `Enhanced` |
| ue-plugin-specialist | `ue-gas-skill` / `ue-niagara-skill` / `ue-significance-skill` | `AbilitySystem` / `GameplayEffect` / `Niagara` / `Significance` |
| ue-render-specialist | `ue-render-*` (13) | `RDG` / `Lumen` / `Nanite` / `PSO` / `FRHICommandList` |
| ue-slate-umg-specialist | `ue-slate-*` + `ue-slatecore-*` + `ue-umg-*` | `SWidget` / `Invalidate` / `RebuildWidget` / `NativePaint` |
| ⭐ ue-spatial-partition-specialist | `ue-spatialpartition-*` (5) | `TOctree2` / `TQuadTree` / `WorldPartition` |
| ⭐ ue-levelsequence-specialist | `ue-levelsequence-*` (11) | `UMovieScene` / `FFrameNumber` / `Sequencer` |

## 3. mcwiki MCP 도구 호출 패턴 (단계 1) 🟢

```python
slugs = mcwiki.list_pages("sources")
my_slugs = [s for s in slugs if s.startswith("ue-animation-")]
for slug in my_slugs:
    page = mcwiki.read_page("sources", slug)
    # frontmatter / citation / cross-link 검증
hits = mcwiki.search("URO", scope="wiki", limit=50)
```

## 4. 단계 2 — specialist agent prompt 의무 4단 (Cycle 5f #3) 🟢

### 4.1 작성/갱신 의무 4단

1. **list_pages 확인** — 작성 대상이 active vault 에 존재
2. **read_page 본문 확인** — stub vs enriched
3. **search 함정 키워드** — 핵심 패턴 누락 확인
4. **lint 검증 자동** — 작성/갱신 후

### 4.2 5단 의무 매핑

| 의무 | 검증 출처 | governance §8.4 매핑 |
|------|----------|---------------------|
| 1. list_pages | 페이지 존재 가시화 | Handoff |
| 2. read_page | 본문 검증 | Quality |
| 3. search | 횡단 cross-link | Handoff |
| 4. lint | 자동 검증 | Audit |

## 5. ⭐⭐⭐ 단계 3 — mcwiki MCP 도구 4종 (Cycle 5g #4) 🟢

### 5.1 `find_cross_link_broken(slug)` ⭐⭐⭐

**목적**: 페이지 안 `[[wikilink]]` 가 active vault 에 실제 존재하는지 검증.

```python
def find_cross_link_broken(slug: str) -> List[BrokenLink]:
    """페이지 [[wikilink]] 추출 → list_pages 검증."""
```

**구현 힌트**: 정규식 `\[\[(.+?)\]\]` 추출 + `kind` 추론 + `list_pages` 매칭.

### 5.2 `find_claim_conflict(slug, related_slugs)` ⭐⭐

**목적**: 두 페이지의 같은 키워드 claim 비교.

**구현 힌트**: 키워드 패턴 추출 + LLM Haiku 3.5 호출 비교.

### 5.3 `find_stale_baseline(slug, threshold_days)` ⭐

**목적**: `last_updated` 기준 + 의존 페이지 변경 추적.

### 5.4 `suggest_missing_cross_link(slug)` ⭐⭐

**목적**: 전역 backlink 분석으로 누락 cross-link 추천.

### 5.5 evaluator 워크플로우 (단계 3 완성 시)

```
페이지 작성 → evaluator 호출 →
  1. find_cross_link_broken → broken 0 검증
  2. find_claim_conflict → conflict 0 검증
  3. find_stale_baseline → stale 0 검증
  4. suggest_missing_cross_link → 누락 0~N 보고
  5. 100점 채점 + 4 기준
  6. 점수 70 미만 → 재작업
```

### 5.6 구현 우선순위

| # | 도구 | 우선도 | 구현 난이도 | 활용 빈도 |
| -- | -- | -- | -- | -- |
| 1 | `find_cross_link_broken` | ⭐⭐⭐ | 낮음 | 매 evaluator |
| 2 | `suggest_missing_cross_link` | ⭐⭐ | 중 | 매 작성 |
| 3 | `find_claim_conflict` | ⭐⭐ | 높음 (LLM) | 매 evaluator |
| 4 | `find_stale_baseline` | ⭐ | 중 | 분기별 audit |

## 6. ⭐⭐⭐ PR 요청서 — `find_cross_link_broken` (Cycle 5h #3) 🟢

mcwiki MCP server 에 도구 #1 추가 PR 형식 명세.

### 6.1 PR 메타데이터

```yaml
Title: feat(mcp): add find_cross_link_broken tool for vault validation
Repository: mcwiki MCP server
Branch: feature/find-cross-link-broken
Target: main
Priority: P1 (Cycle 5h #4 도구 가장 우선)
Estimated LOC: ~150 (Python) — JSON schema + 정규식 + 매칭 로직
Test Plan: pytest + 본 vault 안 모든 페이지 회귀 (broken 0 기대)
```

### 6.2 도구 JSON Schema (`mcp_tool.json`)

```json
{
  "name": "find_cross_link_broken",
  "description": "vault 페이지 안 [[wikilink]] 가 active vault 에 실제로 존재하는지 검증. broken link 리스트 반환 (target_slug + line_number + section_path).",
  "parameters": {
    "type": "object",
    "properties": {
      "slug": {
        "type": "string",
        "description": "검증할 페이지 slug (예: 'ue-editor-asseteditorapi')"
      },
      "kind": {
        "type": "string",
        "enum": ["sources", "entities", "concepts", "synthesis", "meta"],
        "description": "페이지 kind (옵션 — 자동 추론 가능)"
      }
    },
    "required": ["slug"]
  }
}
```

### 6.3 동작 명세 (의사 코드)

```python
def find_cross_link_broken(slug: str, kind: Optional[str] = None) -> Dict:
    # 1. 페이지 본문 읽기
    page_kind = kind or auto_detect_kind(slug)
    content = read_file(f"wiki/{page_kind}/{slug}.md")

    # 2. wikilink 추출 (정규식 + 라인 번호 추적)
    wikilink_re = re.compile(r"\[\[([^\]]+)\]\]")
    links = []
    for line_no, line in enumerate(content.splitlines(), 1):
        for match in wikilink_re.finditer(line):
            target = match.group(1).strip()
            section = parse_current_section(content, line_no)
            links.append({
                "target": target,
                "line_number": line_no,
                "section_path": section
            })

    # 3. 각 target 의 kind / slug 분리 + 존재 검증
    broken = []
    for link in links:
        target_kind, target_slug = parse_target(link["target"])
        if not is_page_exists(target_kind, target_slug):
            broken.append({
                **link,
                "target_kind": target_kind,
                "target_slug": target_slug,
                "reason": "page not found"
            })

    return {
        "slug": slug,
        "total_wikilinks": len(links),
        "broken_count": len(broken),
        "broken_links": broken
    }
```

### 6.4 테스트 케이스

```python
def test_find_cross_link_broken_on_asseteditorapi():
    """Cycle 5h 시점 asseteditorapi 페이지 — 알려진 cross-link 100% verified."""
    result = find_cross_link_broken("ue-editor-asseteditorapi")
    assert result["broken_count"] == 0
    assert result["total_wikilinks"] >= 15   # §5 + §8 + §11 cross-link 다수

def test_find_cross_link_broken_synthetic_broken():
    """가짜 broken link 가 포함된 임시 페이지 — broken 검출."""
    # write_page("sources", "test-broken", "... [[sources/non-existent]] ...")
    result = find_cross_link_broken("test-broken")
    assert result["broken_count"] == 1
    assert result["broken_links"][0]["target_slug"] == "non-existent"

def test_find_cross_link_broken_kind_inference():
    """kind 미지정 시 자동 추론."""
    # slug 'ue-editor-asseteditorapi' → kind 'sources' 추론
    result = find_cross_link_broken("ue-editor-asseteditorapi")  # kind=None
    assert result is not None
```

### 6.5 도입 후 효과 (예측)

- evaluator 호출 시간 단축: ~3-5초 / 페이지
- broken link 자동 검출 → governance §8.4 Audit 강화
- Cycle 5h+ 단계 3 시작 — 다음 3 도구 PR 후속

### 6.6 후속 PR 후보 (도구 #2-#4)

| PR # | 도구 | 우선도 | 의존 |
| -- | -- | -- | -- |
| #2 | `find_cross_link_broken` 본 PR | ⭐⭐⭐ Cycle 5h | (independent) |
| #3 | `suggest_missing_cross_link` | ⭐⭐ Cycle 5i | #2 의 wikilink 추출 로직 재사용 |
| #4 | `find_claim_conflict` | ⭐⭐ Cycle 5j+ | LLM provider 환경 (Claude API key) |
| #5 | `find_stale_baseline` | ⭐ Cycle 5k+ (분기별 audit 도입 시) | frontmatter 파서 |

## 7. ⭐⭐⭐ specialist 11 agent prompt 패치 명세 (Cycle 5h #4) 🟢

각 specialist agent prompt 파일 (agent 정의 source) 에 §4 의무 4단 추가하는 patch 명세. agent prompt 변경 자체는 governance protected 영역 — vault 안 명세만 작성.

### 7.1 패치 대상

11 specialist + 4 메타 agent (orchestrator / evaluator / audit / wiki-maintainer) = **15 agent**.

vault 안 페어 페이지: `sources/ue-agent-*` (raw 15, plugin 활성 13).

### 7.2 patch 텍스트 (각 specialist prompt 에 추가)

```yaml
# specialist agent prompt frontmatter 또는 instructions 에 추가
baseline_grep_obligations:
  description: "작성/갱신 전후 mcwiki MCP 도구로 vault 일관성 자동 검증 의무 — Cycle 5f #3 단계 2 명문화"
  pre_write:
    - tool: list_pages
      args: {kind: sources}
      check: "본인 카테고리 슬러그 매트릭스 검증"
    - tool: read_page
      args: {kind: sources, slug: target_slug}
      check: "stub vs enriched + § 구조 확인"
    - tool: search
      args: {query: "<함정 키워드>", scope: wiki, limit: 50}
      check: "횡단 cross-link 누락 검증 — specialist 별 키워드 매트릭스 참조"
  post_write:
    - tool: lint
      check: "0 issues — broken cross-link / orphan / stale 검출"
    - tool: append_log
      args: {op: "feature|fix|verify|note", title: "...", body: "..."}
      check: "log.md 기록 의무"
```

### 7.3 specialist 별 카테고리 키워드 매트릭스 (§2 카탈로그 미러)

각 specialist 가 자기 함정 키워드 grep 의무:
- ue-editor-specialist: `ToolMenus` / `OnRegisterTabs` / `OnRegisterTabsForEditor` / `IDetailsView::SetObject` / `WorkflowOrientedApp` / forward declare / `SetGenericLayoutDetailsDelegate`
- ue-components-specialist: `UActorComponent` / `Mobility` / `Tick` / `CDO` / `GetOwner`
- (나머지 9 = §2 매트릭스 참조)

### 7.4 patch 적용 위치 — agent prompt 파일 vs vault 페이지

| 항목 | agent prompt (governance) | vault 페이지 (본 명세) |
| -- | -- | -- |
| 의무 4단 실제 코드 | ✅ 적용 의무 (Cycle 5i+) | ❌ 명세만 |
| keywords 매트릭스 | ✅ 적용 의무 | ✅ §2 + §7.3 미러 |
| version 매니페스트 | ✅ frontmatter | ✅ Changelog |
| 평가 의무 (post-write evaluator) | ✅ instructions | ✅ §5.5 |

### 7.5 적용 절차 (Cycle 5i+)

1. agent prompt 파일 위치 확인 (`.claude/agents/ue-wiki-llm/...`?)
2. 각 11 specialist + 4 메타 agent 의 prompt 안 `baseline_grep_obligations:` block 추가
3. specialist 별 키워드 매트릭스 (§7.3) 삽입
4. 평가 의무 (post-write evaluator) instructions 강화
5. governance §8.4 5단 의무 1-4 단 (Frontmatter / Quality / Handoff / Evaluator) 와 통합
6. test_agent_call.py — 적용 후 specialist 호출 → list_pages/search 자동 호출 검증

### 7.6 governance §8.4 와의 매트릭스 통합

| §8.4 5단 의무 | §4 baseline grep 의무 |
| -- | -- |
| 1. Frontmatter | 의무 외 (vault 표준) |
| 2. Quality (🟢/🟡/🔴 3 tier) | §4.2 매핑 |
| 3. Handoff (cross-link) | **§4.2 list_pages + search 매핑** |
| 4. Evaluator (외부 평가) | **§5.5 evaluator 워크플로우 (단계 3 완성 시 자동화)** |
| 5. Audit | **§4.2 lint 매핑** |

→ §4 baseline grep 의무 4단 = §8.4 의 3+4+5단의 자동화 + 사전 검증.

## 8. 첫 적용 사례 8건 (단계 1~2 + Cycle 5g 추가) 🟢

| # | 검증 | 결과 |
|---|------|------|
| 1 | `OnRegisterTabs` cross-link (Cycle 5e #6) | BlueprintEditor 🔴→🟢 3-param accessor 함정 |
| 2 | `FText idempotency` (Cycle 5e #11) | 🟡→🟢 두번째 호출 무시 |
| 3 | `array-element-pointer` (Cycle 5e #10) | 7 시스템 매트릭스 + 함정 11→13 |
| 4 | ref-deep 5종 (Cycle 5f #1) | stub → enrich 31 KB |
| 5 | uobject §2.11.1 외삽 (Cycle 5f #4) | FInstancedStruct 🟡→🟢 / TSharedPtr 🟡→🔴 not-hazard / NotifyHook 🟡 single-case |
| 6 | 자산 9 매트릭스 (Cycle 5f #5 + 5g #1 + 5h #1) | 🟢 1→4 / 🟡 0→4 / 🔴 9→2 |
| 7 | OnRegisterTabs 6 호스트 (Cycle 5g #2 + 5h #2 시그니처 정밀) | 6 verified — 2 호스트 `OnRegisterTabs()` + 4 호스트 `OnRegisterTabsForEditor()` ⚠ |
| 8 | NotifyHook/Delegate 일반화 (Cycle 5g #3) | 일반화 X 검증 — PerlinNoise 1 사이트 단독 |

## 9. Cross-link

### Governance + meta

- [[00_meta/00_QualityCriteria]] · [[00_meta/03_EvaluatorRecipe]] · [[00_meta/05_HandoffProtocol]] · [[00_meta/06_VaultCitationRule]] · [[00_meta/07_AgentBoundaryProtocol]]
- 평가: [[sources/ue-ref-15-evaluatorrecipe]] · [[sources/ue-ref-17-qualitycriteria]] · [[sources/ue-ref-16-policypriority]]

### Audit / corrections

- [[sources/ue-meta-corrections]] · [[sources/ue-meta-honest-limits]] · [[sources/ue-meta-improvement-roadmap]]

### Agent 카탈로그 (15)

- [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-evaluator]] · [[sources/ue-agent-audit]] · [[sources/ue-agent-wiki-maintainer]]
- specialist 11: [[sources/ue-agent-animation]] / [[sources/ue-agent-asset]] / [[sources/ue-agent-components]] / [[sources/ue-agent-editor]] / [[sources/ue-agent-gameframework]] / [[sources/ue-agent-input]] / [[sources/ue-agent-plugin]] / [[sources/ue-agent-render]] / [[sources/ue-agent-slate-umg]] / [[sources/ue-agent-spatial-partition]] / [[sources/ue-agent-levelsequence]]

### 첫 적용 사례 cross-link

- §11.4 OnRegisterTabs 6 호스트 정밀: [[sources/ue-editor-asseteditorapi]] §11.4 + [[sources/ue-editor-personatoolkit]] §2.7
- FText idempotency: [[sources/ue-editor-assettools]] §2.6.1
- array-element-pointer: [[sources/ue-coreuobject-uobject]] §2.11 + §2.11.1

## 10. 후속 검증 후보 (Cycle 5i+)

- [ ] **단계 3 도구 #1 `find_cross_link_broken` mcwiki MCP server 실제 구현** (§6 PR 요청서 제출)
- [ ] specialist 11 agent prompt 의 `baseline_grep_obligations` block 실제 추가 (§7 patch 적용)
- [ ] **단계 2 검증 메트릭** — 적용 전후 cross-link 누락 / 함정 miss 감소율 측정
- [ ] 도구 #2 `suggest_missing_cross_link` PR (Cycle 5i 후보)

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-15 (Cycle 5e 1차 #12) | 단계 1 — specialist 11 baseline 매트릭스 + grep query 카탈로그 |
| 2026-05-15 (Cycle 5f #3) | 단계 2 — specialist agent prompt 의무 4단 명문화 + 첫 적용 사례 3건 |
| 2026-05-15 (Cycle 5g #4) | 단계 3 — mcwiki MCP 도구 4종 상세 명세 + 사례 8건 |
| **2026-05-15 (Cycle 5h #3+#4)** | ⭐⭐⭐ **§6 PR 요청서 (find_cross_link_broken 도구 #1) + §7 specialist 11 agent prompt 패치 명세 + §7.6 governance §8.4 매트릭스 통합**. tag `pr-request-cycle-5h` + `agent-prompt-patch-cycle-5h` |
