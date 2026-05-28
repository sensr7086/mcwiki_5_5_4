# G3 게이트 작업 인계 — ue-wiki-llm plugin v1.8.0 → v1.9.0 (Baseline Grep 의무)

> **인계 대상**: ue-wiki-llm plugin 담당 다른 에이전트 (mcwiki main session 영역 X)
> **작성**: 2026-05-15 · Cycle 5e~5h Baseline Grep System 단계 1-3 완성 후
> **목적**: Cycle 5h #4 patch 적용 — 13 agent prompt 끝에 `## Baseline Grep 의무` § append + 카테고리 키워드 치환
> **이전 버전**: `g3-handoff-ue-wiki-llm-v1.8.0.md` (2 agent 활성 + orchestrator §5.4) — 본 v1.9.0 은 *추가 작업*
> **mcwiki MCP server 측**: 본 인계 *밖* — `E:\MCWiki\` 본체에 v0.3.0 이미 적용 완료 (find_cross_link_broken.py + mcp_server.py + manifest.json). 사용자가 mcpb pack + Cowork install 만 남음.

---

## 0. 현 상태 (2026-05-15, v1.8.0 작업 완료 후)

### v1.8.0 작업 (선행)

| 항목 | 상태 |
|------|------|
| 2 agent 활성 (spatial-partition + levelsequence) | 🟢 v1.8.0 doc 작성됨 |
| 2 skills 디렉토리 (SpatialPartition + LevelSequence 16 파일) | 🟢 v1.8.0 doc 작성됨 |
| orchestrator §5.4 (6단 self-check) | 🟢 v1.8.0 doc 작성됨 |
| plugin.json v1.6.0 → v1.8.0 | 🟢 v1.8.0 doc 작성됨 |
| **`mcpb pack`** | ⚠ 외부 에이전트 실행 대기 |

### v1.9.0 추가 작업 (본 인계)

| 항목 | raw (vault 측 명세) | plugin (agent prompts) |
|------|---------------------|------------------------|
| [[sources/ue-meta-baseline-grep-system]] §7 patch 명세 | ✅ 존재 (vault) | ❌ 미적용 (13 agent .md) |
| `## Baseline Grep 의무` § append (13 agent) | ✅ 명세 | ❌ |
| 카테고리 키워드 매트릭스 (§7.3) | ✅ 명세 (11 specialist) | ❌ |
| `mcwiki` MCP `find_cross_link_broken` 도구 | ✅ v0.3.0 (mcwiki 본체) | ❌ Cowork install 대기 |

---

## 1. v1.9.0 변경 5건

| # | 작업 | 출발지 → 도착지 |
|---|------|----------------|
| 1 | `plugin.json` version + description + keywords | v1.8.0 → **v1.9.0** |
| 2 | 13 agent prompts 끝에 `## Baseline Grep 의무` § append | `agents/*.md` 13개 in-place edit |
| 3 | specialist 11 의 § 안 카테고리 키워드 치환 | §7.3 매트릭스 (specialist 별 11 키워드 셋) |
| 4 | 4 메타 agent (orchestrator / evaluator / audit / wiki-maintainer) § 안 전역 검증 키워드 | §7.4 (specialist 와 다른 패턴) |
| 5 | `.mcpb` 재빌드 | `mcpb pack .` → `dist/ue-wiki-llm-1.9.0.mcpb` |

---

## 2. § patch 본문 (각 agent .md 끝에 append)

```markdown

---

## Baseline Grep 의무 (Cycle 5h #4 적용)

> [[sources/ue-meta-baseline-grep-system]] §7 patch 명세 — agent prompt 측 미러. 작성/갱신 전후 mcwiki MCP 도구로 vault 일관성 자동 검증 의무.

### Pre-write (3 단계)

1. **`list_pages`** — `{kind: sources}` 호출 → 본 카테고리 slug 매트릭스 검증
2. **`read_page`** — `{kind: sources, slug: target_slug}` 호출 → stub vs enriched + § 구조 확인
3. **`search`** — `{query: <함정 키워드>, scope: wiki, limit: 50}` 호출 → 횡단 cross-link 누락 검증 (§ "카테고리 키워드 매트릭스" 참조)

### Post-write (3 단계)

4. **`lint`** — broken cross-link / orphan / stale / ODD_FENCE / COUNT_MISMATCH 0 검증
5. **`find_cross_link_broken`** (v0.3.0 신규) — `{slug: target_slug, kind: sources}` 호출 → broken_count == 0 검증 (line_number + section_path 추적)
6. **`append_log`** — `{op: feature|fix|verify|note, title: ..., body: ...}` → log.md 기록 의무

### 카테고리 키워드 매트릭스 (specialist 별)

| 본 specialist | 함정 키워드 (search 의무) |
|--------------|--------------------------|
<!-- ⭐ 각 specialist .md 에는 본 행만 남기고 나머지 행 삭제 -->
| ue-animation-specialist | `UAnimInstance` / `FAnimNode_` / `AnimNotify` / `URO` / `IKRig` |
| ue-asset-specialist | `TSoftObjectPtr` / `FStreamableHandle` / `UAssetManager` / `Cooked` / `LOD` |
| ue-components-specialist | `UActorComponent` / `Mobility` / `Tick` / `CDO` / `GetOwner` |
| ue-editor-specialist | `ToolMenus` / `OnRegisterTabs` / `OnRegisterTabsForEditor` / `IDetailsView::SetObject` / `WorkflowOrientedApp` / forward declare / `SetGenericLayoutDetailsDelegate` |
| ue-gameframework-specialist | `AActor` / `BeginPlay` / `EndPlay` / `Possession` / `SpawnActor` |
| ue-input-specialist | `UInputAction` / `IMC` / `ETriggerEvent` / `Enhanced` |
| ue-plugin-specialist | `AbilitySystem` / `GameplayEffect` / `Niagara` / `Significance` |
| ue-render-specialist | `RDG` / `Lumen` / `Nanite` / `PSO` / `FRHICommandList` |
| ue-slate-umg-specialist | `SWidget` / `Invalidate` / `RebuildWidget` / `NativePaint` |
| ue-spatial-partition-specialist | `TOctree2` / `TQuadTree` / `WorldPartition` |
| ue-levelsequence-specialist | `UMovieScene` / `FFrameNumber` / `Sequencer` |

### governance §8.4 와의 매트릭스 통합

| §8.4 5단 의무 | §4 baseline grep 의무 |
| -- | -- |
| 1. Frontmatter | 의무 외 (vault 표준) |
| 2. Quality (🟢/🟡/🔴 3 tier) | post-write `read_page` 검증 |
| 3. Handoff (cross-link) | pre-write `list_pages` + `search` |
| 4. Evaluator (외부 평가) | post-write `find_cross_link_broken` + ue-evaluator 호출 |
| 5. Audit | post-write `lint` |
```

---

## 3. 메타 agent (4개) 의 § 변형

orchestrator / evaluator / audit / wiki-maintainer 는 specialist 와 다른 패턴 — 전역 검증 / cross-category.

```markdown
### 메타 agent 키워드 매트릭스 (specialist 와 다름)

| 메타 agent | 검증 의무 |
|-----------|----------|
| ue-orchestrator | §5.4 boundary 6단 self-check 의무 — 모든 specialist 호출 wrap |
| ue-evaluator | 평가 대상의 `find_cross_link_broken` broken_count == 0 의무 (Article 1) |
| ue-audit-agent | 분기별 `find_stale_baseline` (Cycle 5i+ 단계 3 도구 #4 후속) 실행 |
| ue-wiki-maintainer | 작업 전 `read_index` + 정확한 vault path (`E:\MCWiki\wiki\`) 확인 의무 — outputs/llm-wiki-vault scaffold 거부 ([[synthesis/agent-boundary-cycles-2026-q2]] cross-link) |
```

---

## 4. plugin.json v1.9.0 body (v1.8.0 의 확장)

```json
{
  "name": "ue-wiki-llm",
  "version": "1.9.0",
  "description": "UE 5.7.4 specialist plugin - 13 agents (11 specialist + 4 meta) + 21 skill categories. v1.9.0: Baseline Grep obligation (Cycle 5h #4) - 13 agent prompts get '## Baseline Grep 의무' section appended + category keyword matrix. mcwiki MCP server v0.3.0 add find_cross_link_broken (post-write validation). v1.8.0 cumulative: SpatialPartition (Cycle #11) + LevelSequence (Cycle #12) - 2 new agents + 16 skill files + orchestrator §5.4 boundary protocol (6-step self-check).",
  "keywords": [
    "ue", "unreal-engine", "5.7", "specialist",
    "spatial-partition", "octree", "worldpartition",
    "levelsequence", "sequencer", "cinematic", "moviescene", "cinecamera", "movierenderpipeline",
    "baseline-grep", "find-cross-link-broken"
  ]
}
```

---

## 5. 실행 절차 (외부 에이전트 8단계)

```powershell
# 0. v1.8.0 작업 완료 가정 (2 agent + 2 skills + §5.4 + plugin.json v1.8.0 + mcpb pack 끝)
cd $env:USERPROFILE\AppData\Roaming\Claude\local-agent-mode-sessions\<uuid>\<uuid>\rpm\plugin_019SPM4GSPfAfagqWFsrexY4

# 1. plugin.json v1.8.0 → v1.9.0
# (위 §4 body 적용)

# 2. 13 agent prompts 의 끝에 §2 patch 본문 append
foreach ($agent in (Get-ChildItem agents\*.md)) {
    $patch = Get-Content "..\patch-template.md" -Raw   # §2 patch 본문 추출
    # specialist 인 경우 — §3 키워드 행 본인 것만 남김
    if ($agent.BaseName -match "specialist") {
        $patch = $patch -replace "<KEYWORDS_PLACEHOLDER>", $specialist_keywords[$agent.BaseName]
    } else {
        # 메타 agent — §3 메타 패턴 사용
    }
    Add-Content $agent.FullName "`n$patch"
}

# 3. .mcpb 재빌드
mcpb pack . dist\ue-wiki-llm-1.9.0.mcpb

# 4. Cowork uninstall + install
# (UI 또는 CLI — 사용자 결정)

# 5. mcwiki v0.3.0 도 동시 install
cd E:\MCWiki
mcpb pack . dist\mcwiki-0.3.0.mcpb

# 6. Claude Desktop 재시작 (양쪽 plugin 모두 활성화 위해)

# 7. 검증 — specialist 호출 후 list_pages / search / find_cross_link_broken / lint 자동 호출 확인
# 8. ue-evaluator 호출 → find_cross_link_broken broken_count == 0 의무 검증
```

---

## 6. 검증 항목

| 검증 | 방법 |
|------|------|
| 13 agent prompt 모두 § append 됨 | `grep -l "Baseline Grep 의무"` 13 매치 |
| specialist 11 의 키워드 매트릭스 본인 것만 남음 | 각 specialist .md 안 본인 행 1개 + 다른 specialist 행 0개 |
| `mcwiki: find_cross_link_broken` 도구 호출 가능 | mcwiki v0.3.0 install 후 17번째 tool 등록 확인 |
| specialist 호출 시 pre/post 도구 자동 호출 | test_agent_call.py (Cycle 5h+ 후속) |

---

## 7. Cross-link (vault 측 명세)

- [[sources/ue-meta-baseline-grep-system]] §6 PR 요청서 + §7 agent prompt patch 명세 (본 인계 doc 의 origin)
- [[sources/ue-meta-baseline-grep-system]] §2 specialist 11 baseline 매트릭스 (키워드 출처)
- [[sources/ue-meta-baseline-grep-system]] §7.6 governance §8.4 매트릭스 통합
- [[00_meta/07_AgentBoundaryProtocol]] §5.4 + §2.4 5-tier 카운트 검사 (외부 에이전트도 동일 의무)
- [[synthesis/agent-boundary-cycles-2026-q2]] Phase II G2 게이트 PASS 10/10 (G3 외부 작업 후 G2 + G3 양립)
- mcwiki MCP v0.3.0: `tools/find_cross_link_broken.py` + `tools/mcp_server.py:845` handler + `manifest.json:6` version + `manifest.json:44` tool entry

---

## 8. v1.8.0 / v1.9.0 / mcwiki v0.3.0 관계

```
v1.8.0 (선행, 다른 에이전트 작업 대기)
├── 2 agent 활성 (spatial-partition + levelsequence)
├── 2 skills 디렉토리 (16 파일)
├── orchestrator §5.4 6단 self-check
└── mcpb pack v1.8.0

v1.9.0 (본 인계, 다른 에이전트 작업 대기)
├── 13 agent prompts § append (Baseline Grep 의무)
├── specialist 11 키워드 매트릭스 치환
└── mcpb pack v1.9.0

mcwiki v0.3.0 (이미 완료, mcwiki 본체)
├── tools/find_cross_link_broken.py — 175 LOC 신규
├── tools/mcp_server.py — 17번째 tool entry + handler (4 LOC handler / 18 LOC Tool entry)
├── manifest.json — v0.2.1 → v0.3.0 + 17 tools entry
└── (mcpb pack v0.3.0 — 사용자 직접 실행 대기)
```

→ **v1.9.0 + mcwiki v0.3.0 동시 install 권장** (post-write find_cross_link_broken 호출 의무가 v1.9.0 patch 의 핵심).

---

## 9. 후속 PR (v1.10.0+)

| PR # | 작업 | 우선도 |
|------|------|--------|
| v1.10.0 | `suggest_missing_cross_link` 도구 #2 (Cycle 5i 후보) | ⭐⭐ |
| v1.11.0 | `find_claim_conflict` 도구 #3 (LLM 호출 — Claude API key 필요) | ⭐⭐ |
| v1.12.0 | `find_stale_baseline` 도구 #4 (분기별 audit) | ⭐ |
| v1.13.0 | test_agent_call.py 검증 - Baseline Grep 의무 실행 회귀 | ⭐⭐⭐ |

---

## 10. v1.7.0 / v1.8.0 처리

- `g3-handoff-ue-wiki-llm-v1.7.0.md` — DEPRECATED (Cycle #11 시점, 1 agent)
- `g3-handoff-ue-wiki-llm-v1.8.0.md` — 활성 (v1.9.0 의 *선행 필수 작업*. 본 v1.9.0 은 *추가 작업*. 둘 다 진행해야 G3 게이트 완전 통과)

→ 외부 에이전트는 v1.8.0 + v1.9.0 둘 다 처리.
