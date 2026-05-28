---
type: source
title: "UE SpatialPartition Specialist Agent (14번째)"
slug: ue-agent-spatial-partition
source_path: raw/ue-wiki-llm/agents/ue-spatial-partition-specialist.md
source_kind: text
source_date: 2026-05-12
ingested: 2026-05-13
last_updated: 2026-05-16
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Global-Iterator-Avoidance]]"
  - "[[concepts/Subsystem-5-Types]]"
tags: [ue, agent, specialist, spatial-partition, octree, baseline-grep-cycle-5o, enriched-card]
citation_disclosure: "🟢 10 / 🟡 0 / 🔴 0 · 보너스 발견 1건 (plugin 미등록 상태 = G3 게이트 작업 후보) · Cycle 5o #1 Baseline Grep § 추가 — 다른 12 agent 카탈로그와 일관화"
---

# UE SpatialPartition Specialist Agent 🌐

> Source: [[raw/ue-wiki-llm/agents/ue-spatial-partition-specialist.md]] (189L)
> 14번째 agent (vault 신규) · plugin **미등록** (현재 13 agent만 plugin 활성, raw 만 정의)
> Pair: [[sources/ue-spatialpartition-skill]] (카테고리 main)
> 호출: `Task(subagent_type="ue-wiki-llm:ue-spatial-partition-specialist", ...)` — plugin 재배포 후 가능
> Cycle 5o #1 (2026-05-16) — §Baseline Grep + §변경 이력 추가 (다른 12 agent 일관화)

## 1. Summary

UE 5.7.4 SpatialPartition 카테고리 전문가 — 런타임 AActor 대규모 관리 + 공간 인덱싱 + 반경 쿼리. 4 sub-skill (TOctree2 ⭐⭐⭐ / TQuadTree / StaticSpatialIndex / WorldPartitionRuntime). `[SpatialPartition]` prefix 호출.

## 2. Key claims

### 2.1 자동 로드 8 파일 🟢 (raw L12-21)

1. `skills/SpatialPartition/SKILL.md` (메인)
2. `skills/SpatialPartition/references/TOctree2.md` ⭐⭐⭐
3. 사용자 요청 sub-skill (TQuadTree / StaticSpatialIndex / WorldPartitionRuntime)
4. 🚨 `references/09_GlobalIteratorPolicy.md`
5. 🚨 `references/07_ProfilingScopeRule.md`
6. 🚨 `references/10_ComponentPolicies.md §3` (GC 방어)
7. (페어) `skills/Subsystem/SKILL.md`
8. (페어) `skills/Significance/SKILL.md`

### 2.2 6 시나리오 매핑 🟢 (raw L23-32)

| 시나리오 | 필수 |
|---------|------|
| 다수 AActor 반경 쿼리 (AOE/AI Sight) ⭐⭐⭐ | TOctree2 + Subsystem |
| 2D 게임 반경 쿼리 | TQuadTree + Subsystem |
| 정적 데이터 검색 | StaticSpatialIndex R-Tree |
| 대규모 월드 (1km+) | WorldPartitionRuntime + World |
| 거리 LOD/Tick | Significance (별도) |
| 군집 행동 (Boids) | TOctree2 + AI |

### 2.3 TOctree2 4단 표준 패턴 🟢 (raw L34-42)

```
[1] Element struct      — TWeakObjectPtr<AActor> + FBoxSphereBounds + FOctreeElementId2
[2] Semantics 정의      — 6+ 요소 (MaxElementsPerLeaf / MinInclusive / MaxNodeDepth /
                          Allocator / GetBoundingBox / SetElementId / ApplyOffset / AreElementsEqual)
[3] UWorldSubsystem     — Initialize / Deinitialize / Register / Unregister / Update
[4] Query API           — GetActorsInRadius / GetActorsInBox / ForEachActorInRadius (람다)
```

### 2.4 3축 의무 자동 적용 🟢 (raw §3축)

- 🚨 GC 방어 — `TWeakObjectPtr<AActor>` + `IsValid` 의무 (`10_ComponentPolicies §3`)
- 🚨 TActorIterator 금지 (`09_GlobalIteratorPolicy`)
- 🚨 Profile scope (`07_ProfilingScopeRule`)

### 2.5 함정 자동 회피 12대 🟢 (raw §함정)

(상세 = [[sources/ue-spatialpartition-toctree2]] §3 + [[sources/ue-spatialpartition-skill]] §4)

### 2.6 적합도 매트릭스 🟢

다수 NPC 5중 최적화 ([[sources/ue-gameframework-characteroptimization]]) 의 *공간 인덱스 축* 담당. Significance Manager 와 페어 (거리 LOD/Tick) — TOctree2 는 *반경 쿼리*, Significance 는 *거리 priority*.

### 2.7 Build.cs 자동 의존 🟢

```csharp
PrivateDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine" });
```

WorldPartition 사용 시 추가 X (Engine 포함).

### 2.8 다른 specialist 와 협업

- [[sources/ue-agent-gameframework]] — BeginPlay/EndPlay 페어 표준
- [[sources/ue-agent-components]] — Subsystem 안 등록 패턴
- [[sources/ue-agent-plugin]] — Significance Manager 와 페어
- [[sources/ue-agent-render]] — `FScenePrimitiveOctree` (Engine 검증 패턴)

### 2.9 신뢰도 태그 사용 🟢

raw 가 명시 — `[verified]` / `[grep-listed]` / `[inferred]` 3 단계 사용. SpatialPartition raw 페이지 모두 `[verified]` (Engine source 직접 참조).

### 2.10 plugin 미등록 — G3 게이트 작업 후보 🟡

현재 Cowork 의 `ue-wiki-llm:*` agent 목록에 `ue-spatial-partition-specialist` 미존재 (13 agents 만 활성). raw 만 정의 → **plugin 재배포 필요**. G3 게이트 (orchestrator system_prompt §5.4 명문화) 와 동시 작업 후보 — `.mcpb` 재빌드 + Cowork 재install.

## 3. ⭐⭐⭐ Baseline Grep 의무 (Cycle 5h #4 + Cycle 5o #1 적용) 🟢

> [[sources/ue-meta-baseline-grep-system]] §7 patch 명세. main 이 본 agent .md 를 read_raw 로 흡수한 후, vault 일관성 자동 검증 의무 (mcwiki MCP v0.5.1 4 Baseline Grep 도구 활용).

### 3.1 Pre-write (3 단계)

1. `mcwiki: list_pages` — `{kind: sources}` → 본 카테고리 slug 매트릭스 검증
2. `mcwiki: read_page` — `{kind: sources, slug: target_slug}` → stub vs enriched + § 구조 확인
3. `mcwiki: search` — `{query: <함정 키워드>, scope: wiki, limit: 50}` → 횡단 cross-link 누락 검증

### 3.2 Post-write (3 단계)

4. `mcwiki: lint` — broken cross-link / orphan / stale / ODD_FENCE / COUNT_MISMATCH 0 검증
5. `mcwiki: find_cross_link_broken` — `{slug: target_slug, kind: sources}` → broken_count == 0 (mcwiki v0.3.0+)
6. `mcwiki: append_log` — `{op: feature|fix|verify|note|refactor, title: ..., body: ...}` → log.md 기록 의무

### 3.3 본 agent 함정 키워드 (search 의무)

`TOctree2` / `TQuadTree` / `FOctreeElementId2` / `FBoxSphereBounds` / `WorldPartition` / `TActorIterator` / `TWeakObjectPtr<AActor>` / `UWorldSubsystem` / `Boids` / `Octree Semantics`

### 3.4 governance §8.4 와의 매트릭스 통합 🟢

| §8.4 5단 의무 | 본 § 매핑 |
| -- | -- |
| 1. Frontmatter | 의무 외 (vault 표준) |
| 2. Quality (🟢/🟡/🔴 3 tier) | post-write `read_page` 검증 |
| 3. Handoff (cross-link) | pre-write `list_pages` + `search` |
| 4. Evaluator (외부 평가) | post-write `find_cross_link_broken` + `general-purpose` Task 위임 |
| 5. Audit | post-write `lint` |

### 3.5 신규 도구 활용 (mcwiki v0.5.1 — Cycle 5j+)

분기별 또는 cycle 진행 시 추가 도구 사용 권장:
- `suggest_missing_cross_link` — outbound/inbound + 누락 reverse-link 추천
- `find_stale_baseline` — 90일 임계 staleness 검출
- `find_claim_conflict` — 페어 페이지 일관성 검증 (heuristic, 한국어 단위 명사 false positive 회피 필요)

## 4. Cross-link

- Pair: [[sources/ue-spatialpartition-skill]] (카테고리 main, 4 sub-skill 인덱스)
- 다른 agents (메타 4): [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-evaluator]] · [[sources/ue-agent-audit]] · [[sources/ue-agent-wiki-maintainer]]
- 페어 specialist: [[sources/ue-agent-gameframework]] · [[sources/ue-agent-components]] · [[sources/ue-agent-plugin]] · [[sources/ue-agent-render]]
- 정책: [[concepts/Profiling-Scope-Rule]] · [[concepts/Component-Policies-6]] · [[concepts/Global-Iterator-Avoidance]] · [[concepts/Subsystem-5-Types]]
- 시스템: [[sources/ue-meta-baseline-grep-system]] §7

## 5. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-13 | 14번째 agent slim card 작성 (Cycle #11 카테고리 신설 동시 — 정밀 10 claims) |
| **2026-05-16 (Cycle 5o #1)** | ⭐⭐⭐ **§3 Baseline Grep 의무 § 신규 추가** (Cycle 5h #4 patch + Cycle 5o 일관화) — Pre-write 3단 + Post-write 3단 + 본 agent 함정 키워드 + governance §8.4 매트릭스 통합 + 신규 도구 v0.5.1 활용. + §5 변경 이력 §추가. last_updated 갱신 (2026-05-13 → 2026-05-16) |
