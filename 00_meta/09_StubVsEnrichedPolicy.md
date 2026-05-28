---
type: meta
title: "Stub vs Enriched Policy — vault sources/ 카탈로그 카드 + raw/ 본문 분리 + read_raw 자동 호출 의무"
slug: 09_StubVsEnrichedPolicy
created: 2026-05-16
last_updated: 2026-05-16
tags: [meta, governance, stub, enriched, catalog-card, read-raw, baseline-grep, enrich-status]
---

# Stub vs Enriched Policy — vault sources/ 카탈로그 카드 + raw/ 본문 분리

> 본 정책은 **vault `sources/` 페이지의 두 상태 (stub catalog card vs enriched)** + **stub 감지 시 `read_raw` 자동 호출 의무** 를 명시한다. [[sources/ue-meta-honest-limits]] §1.1 #5 (raw ingest = 2026-05-09 스냅샷) + index.md 정밀 source 88+ 카운트의 *공식 메커니즘*.
>
> 핵심: vault `sources/` 페이지의 **~56% 는 stub catalog card** (~112건 / 200건). 카드만 읽고 답변하면 raw/ 본문의 함정 / API 시그니처 / 코드 예제 누락. 본 정책은 agent / 사용자가 *stub 을 명시적으로 감지 + read_raw 보강* 하도록 강제한다.

## 1. 두 상태 정의

### 1.1 Stub (catalog card) — *기본값*

vault `sources/` 페이지가 *raw 본문의 인덱스 카드* 역할:
- frontmatter `source_path` 가 `raw/...` 본문으로 포인터
- 본문 = 짧은 요약 (§1 Summary, §2 Key claims) + cross-link 만
- 본문 길이 보통 **< 2 KB** (frontmatter 포함 ~30 라인 이하)
- 명시 키워드: "*전문은 원본 raw 참조 — 본 페이지는 ingest 카탈로그 목적의 카드*" (예: [[sources/ue-editor-advancedpreviewscene]] §2)
- raw/ ingest = **2026-05-09 스냅샷** ([[sources/ue-meta-honest-limits]] §1.1 #5)

### 1.2 Enriched — *Cycle 5e+ 작업 결과*

vault `sources/` 페이지가 *raw 본문 + 추가 정보* 합본:
- KMCProject 작업 트리거 (함정 발견 / 코드 검증 / 외삽 검증) 로 enrich
- 본문 길이 보통 **> 5 KB** (정밀 페이지는 20-30 KB)
- §2-§N 정밀 카탈로그 (함정 매트릭스 / 시그니처 grep / 호스트별 비교 등)
- frontmatter `last_updated` 가 `ingested` 보다 신함

## 2. Frontmatter `enrich_status` 키 (선택, 명시 우선)

vault `sources/` 페이지의 frontmatter 에 *선택적* 명시:

```yaml
---
type: source
slug: ue-...
source_path: raw/...
ingested: 2026-05-09
last_updated: 2026-05-15
enrich_status: enriched     # 또는 catalog-card (기본값, 생략 가능)
...
---
```

| 값 | 의미 | 기본값 |
| -- | -- | -- |
| `catalog-card` | stub 카탈로그 카드 — raw 본문 별도 호출 의무 | ✅ (생략 시 default) |
| `enriched` | Cycle 작업으로 정밀 enrich — raw 본문 추가 호출 *선택* | (명시 의무) |
| `partial` | 부분 enrich — 본문 일부만 enrich, 나머지는 raw 참조 의무 | (명시 의무) |

⭐ **점진적 명시 권장** — 200 페이지 일괄 변경 부담. **enriched 페이지만 명시** 적용 후 stub 페이지 = 자동 default. (Cycle 5o #11 시점 = 88+ enriched 페이지에만 frontmatter 추가, 향후 Cycle 5p+ 에서 점진).

## 3. ⭐ Stub 감지 + read_raw 자동 호출 의무 — agent 측

mcwiki MCP 를 통해 vault 를 *읽고 답변하는* 모든 agent (Cowork / Claude Code / specialist subagent) 의 **pre-write Baseline Grep §** 에 추가 의무:

### 3.1 Stub 감지 (3 단계 fallback)

```text
Step 1 — Frontmatter 확인 (명시 우선)
   if (frontmatter.enrich_status == "enriched")  → enriched
   if (frontmatter.enrich_status == "partial")   → partial (raw 호출 의무)
   if (frontmatter.enrich_status == "catalog-card" OR missing) → stub

Step 2 — 본문 키워드 검사 (frontmatter 부재 fallback)
   본문에서 다음 키워드 발견 시 → stub:
   - "ingest 카탈로그 목적의 카드"
   - "전문은 원본 raw 참조"
   - "[inferred]" 가 title 에 포함 (frontmatter `title:` 검사)

Step 3 — 본문 길이 fallback
   본문 length < 2 KB (frontmatter 제외) → stub
   본문 length 2-5 KB → partial
   본문 length > 5 KB → enriched
```

### 3.2 read_raw 자동 호출

stub 또는 partial 로 감지 시 *반드시* 추가 호출:

```text
1. read_page(kind, slug) 호출 → frontmatter + 본문 카드
2. frontmatter 의 source_path 추출 (예: "raw/ue-wiki-llm/skills/Editor/AssetEditorAPI/references/AdvancedPreviewScene.md")
3. read_raw(rel_path) 호출 — source_path 의 raw/ 이하 path 사용 (예: "ue-wiki-llm/skills/Editor/AssetEditorAPI/references/AdvancedPreviewScene.md")
4. raw 본문을 vault 카드와 합본해서 답변 / 코드 작성 베이스로 사용
```

### 3.3 enriched 페이지의 *선택적* read_raw

enriched 페이지는 *vault 본문이 raw 본문 + 추가 정보* 합본 — `read_raw` 추가 호출 *선택*. 단, 다음 시나리오에선 호출 권장:
- raw 의 *원본 시그니처* 가 vault 본문에 인용 형식 (line 번호) 으로 참조될 때 — 원문 검증
- `last_updated` 가 `ingested` (raw snapshot) 보다 *전* 일 때 — 거의 없음

## 4. Specialist agent prompt §pre-write 갱신 표준

11 specialist agent (raw `ue-wiki-llm/agents/*specialist.md`) 의 Baseline Grep § Pre-write 단계가 본 정책 의무화 (Cycle 5o #11):

```markdown
### Pre-write (4 단계 — Cycle 5o #11 추가)
0. ⭐ **stub 감지 + read_raw 자동 호출** — 본 카테고리 페이지의 `enrich_status` (또는 본문 키워드 / 길이) 검사 → stub/partial 시 `read_raw {rel_path=frontmatter.source_path}` 호출 의무 (→ [[00_meta/09_StubVsEnrichedPolicy]] §3).
1. `mcwiki: list_pages` — `{kind: sources}` → 본 카테고리 slug 매트릭스 검증
2. `mcwiki: read_page` — `{kind: sources, slug: target_slug}` → frontmatter `enrich_status` + 본문 § 구조 확인
3. `mcwiki: search` — `{query: <함정 키워드>, scope: wiki, limit: 50}` → 횡단 cross-link 누락 검증
```

## 5. 정량 매트릭스 — 2026-05-16 시점

> index.md narrative + ue-meta-honest-limits §1.1 기반.

### 5.1 정밀 enriched 88+ 건

| 카테고리 | 정밀 | 정밀률 |
| -- | -- | -- |
| SpatialPartition | 5/5 | 100% |
| LevelSequence | 11/11 | 100% |
| Meta | 6/6 | 100% |
| Agents | 16/16 | 100% |
| MC 시리즈 | 2/2 | 100% |
| Measurements | 5/5 | 100% |
| Render | 9/13 | 69% |
| Editor | 15/26 | 58% |
| Ref | 6/~20 | 30% |
| CoreUObject | 1/14 (uobject) | 7% |
| AssetClasses | 1/12 (assetuserdata) | 8% |
| Animation | 1/9 (ragdoll) | 11% |
| Components | 1/17 (charactermovementdeep) | 6% |
| GameFramework | 1/8 (characteroptimization) | 13% |
| Input / Slate / SlateCore / UMG | 0 | 0% |

### 5.2 stub catalog card ~112건

→ vault 사용자 / agent 가 `read_raw` 추가 호출 의무 대상.

## 6. 적용 우선순위 매트릭스 — 향후 enrich Cycle 후보

### 6.1 KMCProject 작업 trigger 카테고리 (우선)

| 카테고리 | 작업 trigger | enrich 우선 |
| -- | -- | -- |
| Editor 11 stub (`leveleditor`, `mainframe`, `assetregistry`, `advancedpreviewscene`, `editorframework` 등) | MCComboEditor Phase 2b+ / MCHitBoneCurveEditor 잔여 | ⭐⭐⭐ P0 |
| Render 4 stub (`material`, `vulkan` 등) | KMCProject 렌더 작업 미시점 | ⭐⭐ P1 |
| CoreUObject 13 stub (`reflection`, `property`, `package`, `gc`, `network` 등) | C2440 / forward declare 후속 trigger | ⭐⭐ P1 |
| AssetClasses 11 stub (`mesh`, `audio`, `vfx` 등) | MCComboEditor `TSoftObjectPtr<UAnimMontage>` 후속 | ⭐⭐ P1 |

### 6.2 비-trigger 카테고리 (후순위)

| 카테고리 | enrich 우선 |
| -- | -- |
| Input / Slate / SlateCore / UMG | ⭐ P2-P3 (KMCProject 직접 trigger 적음) |
| Animation 8 stub | ⭐ P2 (Phase 3 후속 trigger 시) |
| Components 16 stub | ⭐ P2 (Component 6대 정책 검증 시 trigger) |

## 7. 사용자 측 대응

vault 답변을 평가할 때 다음 패턴 인지:

| 답변 양식 | 의미 | 사용자 대응 |
| -- | -- | -- |
| `[[sources/ue-<카테고리>]]` §X.Y 인용 + 정밀 함정 명시 | enriched 페이지 인용 — 검증 가능 | ✅ 신뢰 |
| `[[sources/ue-<카테고리>]]` §1 Summary 만 인용 | stub 카드만 — raw 본문 누락 의심 | 🟡 raw 본문 추가 요청 |
| raw 본문 인용 없이 함정 디테일 답변 | INFERRED 가능 (vault 본문에 안 적힘) | 🔴 [[00_meta/06_VaultCitationRule]] §1 3-tier 분류 요청 |

## 8. 한 줄 정리

> **vault `sources/` 페이지의 ~56% 는 stub catalog card — frontmatter `source_path` 의 raw 본문 별도 `read_raw` 호출이 의무 다.** agent / 사용자 모두 stub 감지 + read_raw 자동 호출 규약을 따른다.

## 9. 관련 governance

- [[00_meta/00_QualityCriteria]] — Maintainability 25% — stub vs enriched 분리 = vault 일관성의 부분
- [[00_meta/05_HandoffProtocol]] — agent 간 핸드오프 시 stub 페이지 인용 = read_raw 의무 함께 전달
- [[00_meta/06_VaultCitationRule]] — 🟢/🟡/🔴 3 tier — stub 카드만 인용 시 🟡 PARTIAL 로 분류 + 명시
- [[00_meta/07_AgentBoundaryProtocol]] — specialist agent 경계 — stub 페이지 처리는 보장 의무
- [[00_meta/08_VaultScopePolicy]] — vault 범위 — stub 카드도 *일반 UE 지식* (KMCProject 종속 X)
- [[sources/ue-meta-baseline-grep-system]] §7 — Baseline Grep 도구 4종 → §pre-write 갱신 권위
- [[sources/ue-meta-honest-limits]] §1.1 #5 — raw ingest 2026-05-09 스냅샷 권위

## 10. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-16 (Cycle 5o #11) | 최초 작성 — stub vs enriched 정책 + `enrich_status` frontmatter 키 + stub 감지 3 단계 fallback + read_raw 자동 호출 의무 + specialist agent prompt 갱신 표준 + 정량 매트릭스 (88+ enriched / ~112 stub). 11 specialist agent prompt §pre-write 0 단계 추가. |
