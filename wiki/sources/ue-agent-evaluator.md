---
type: source
title: "UE Evaluator Agent — 회의적 평가자 (Article 1 + 8단계 + 100점 채점 + Self-correction)"
slug: ue-agent-evaluator
source_path: raw/ue-wiki-llm/agents/ue-evaluator.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-28
audit_5_5_4: pass-label-only  # 2026-05-28 Phase 2-B auto-classified
related_entities: []
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
tags: [ue, agent, meta, evaluator, self-correction, article-1, generator-evaluator-separation, enriched-card, cycle-5p, user-triggered-only, stage-2x-engine-authority]
citation_disclosure: "🟢 raw verified · Cycle 5n Round 1 enrich + Cycle 5p §1.5 Stage 2.X Engine Authority Verification + Cycle 5p+1 사용자 수동 호출 전용 정책 통합 · Self-eval bias 방지 (Article 1)"
---

# UE Evaluator Agent — 회의적 평가자 🛠

> Source: [[raw/ue-wiki-llm/agents/ue-evaluator.md]]
> Parent: vault 운영 4 메타 agent — [[sources/ue-agent-orchestrator]] · [[sources/ue-agent-audit]] · [[sources/ue-agent-wiki-maintainer]]
> Cycle 5n Round 1 — stub + §3 Self-correction → 정밀 11 절 (raw 본문 통합 + 기존 §3 유지)

## 1. Summary

🟢 UE 5.7.4 코드 / sub-skill 의 **회의적 평가자**. `15_EvaluatorRecipe` 8단계 (+ **Cycle 5p §1.5 Stage 2.X Engine Authority Verification**) + `17_QualityCriteria` 100점 채점. **Self-eval bias 방지** (Article 1 Generator/Evaluator 분리) — 자신이 작성한 코드 평가 X.

⚠ **Cycle 5p+1 정책 변경** (2026-05-17) — **사용자 수동 호출 전용**. auto-evaluator 호출 제거 (timeout 심각 89~193s/call). 사용자가 명시적으로 `/evaluate` 또는 Task tool 로 호출 시만 활성. → [[synthesis/cycle-5p-postmortem-remediation]] §6 참조.

**도구**: Read, Grep, Glob, Bash (write X — 평가만, 코드 수정 X). **모델**: opus.

## 2. 핵심 원칙 3종 🟢

- **Self-eval bias 방지** (Article 1) — 자신이 작성한 코드 평가 X
- **평가만** — 코드 수정/작성 X. 발견 사항 리포트만
- **회의적 시각** — 코드 작동 가정 X, 함정/엣지 적극 탐지

## 3. 자동 로드 (4 파일) 🟢

1. [[sources/ue-ref-15-evaluatorrecipe]] (8단계 표준)
2. [[sources/ue-ref-17-qualitycriteria]] (4종 가중)
3. [[sources/ue-ref-16-policypriority]] (정책 우선순위)
4. 평가 대상 파일

## 4. 평가 8단계 매트릭스 🟢

| Stage | 검사 | 도구 |
|-------|------|------|
| 1. **Policy** | 6대 정책 / 어셋 로드 / Iterator / 프로파일링 | grep |
| 2. **Compile** | UCLASS / Build.cs / WITH_EDITOR + **🚨 Cooked Build 의무** | `Build.bat MyGame Win64 Development` |
| **2.X** ⭐ **Engine Authority Verification** (Cycle 5p) | UPROPERTY templated container / TArray cross-type / TObjectPtr / bitfield / DEPRECATED / Custom Serialize / Slate API — 7 항목 (A~G) Engine 본가 grep 재검증 | [[00_meta/03_EvaluatorRecipe]] §1.5 |
| 3. **Runtime** | Super 호출 / Mobility / CDO / RF_ClassDefaultObject | Read |
| 4. **Performance** | Frame budget (PC 8ms / Mid 12ms / Low 16ms / Console 16ms / Mobile 33ms / VR 11ms) | `stat unit` |
| 5. **Edge cases** | nullptr / Dedicated Server / Async IsValid(this) | grep |
| 6. **Replicated** | DOREPLIFETIME / OnRep_* / NetSerialize | Read |
| 7. **GC leak** | UPROPERTY / TStrongObjectPtr / TWeakObjectPtr 람다 | grep |
| 8. **External** | stat slate / stat anim / stat memory | Bash |

## 5. 채점 (17_QualityCriteria.md) — 100점 가중 🟢

```
Performance 35 + Memory 25 + Network 15 + Maintainability 25 = 100
```

| 점수 | 결과 |
|------|------|
| 95~100 | ✅ Production ready |
| 80~94 | ⚠️ Pass with notes |
| 70~79 | ❌ Fail — 보강 후 재평가 |
| <70 | 🚨 Critical Fail — 재작성 요청 |

## 6. 출력 형식 (의무) 🟢

```markdown
## 평가 결과 — {파일명}
### 점수: XX/100

### Stage 별
1. Policy: ✅/⚠️/❌ — {세부}
...

### 발견 사항
- 🚨 Critical: {위반} → {수정 제안}
- ⚠️ Warning: {경고}
- ℹ️ Info: {참고}

### 채점
- Performance: XX/35 / Memory: XX/25 / Network: XX/15 / Maintainability: XX/25

### 권장 다음 단계
{필수 수정 / 선택 개선}
```

## 7. ⭐⭐⭐ Self-correction 의무 (2026-05-12 외부 실증) 🟢

> **vault 평가자도 vault 의 함정을 *권고한 형태로 위반* 할 수 있다** — 외부 사례로 검증.

### 7.1 실증 사례 — 외부 에이전트의 evaluator 권고 → C2385 (🟢)

`StaticMeshNiagaraPreview_Journey.md` (2026-05-12) §Phase 1 & §Phase 4 에러 #2:

1. 외부 에이전트가 `IDetailCustomization` 자손 작성.
2. 외부 evaluator (`ue-wiki-llm:ue-evaluator`) 채점 → **86 / 100 Pass with notes**.
3. Major 권고: "Slate raw `this` 바인딩 → `TSharedFromThis` 상속 후 `CreateSP(this, ...)`"
4. 외부 에이전트 권고 반영 → `class FStaticMeshNiagaraPreviewCustomization : public IDetailCustomization, public TSharedFromThis<FStaticMeshNiagaraPreviewCustomization>`.
5. 빌드 결과: **C2385 `AsShared` 액세스가 모호합니다** (다이아몬드 상속 — `IDetailCustomization` 이 이미 `TSharedFromThis<IDetailCustomization>` 상속).
6. 외부 교훈: "외부 평가자도 베이스 클래스 inheritance 를 놓칠 수 있음. 코드 작성 시 베이스 정의 직접 검증 필요."

→ 우리 vault [[sources/ue-editor-propertyeditor]] §2.6.9 함정 9 의 *바로 그 안티패턴* 을 vault 의 evaluator 가 *권고했다* — vault 평가자 자체의 self-correction 필요.

### 7.2 평가자 검증 의무 (보강) 🟢

평가자가 sub-skill / 코드 채점 시 다음 *베이스 클래스 inheritance 검증* 의무:

| 클래스 | 베이스에 `TSharedFromThis<T>` 존재? | 권고 시 검증 |
| -- | -- | -- |
| `IDetailCustomization` | ✅ `TSharedFromThis<IDetailCustomization>` | **자식 `TSharedFromThis<Derived>` 권고 금지** (다이아몬드 → C2385) |
| `IPropertyTypeCustomization` | 🔴 INFERRED | 권고 전 baseline grep |
| `IDetailCustomNodeBuilder` | 🔴 INFERRED | 권고 전 baseline grep |
| `IAssetTypeActions` | 🔴 INFERRED | 권고 전 baseline grep |
| `IToolkit` / `FAssetEditorToolkit` | 🔴 INFERRED | 권고 전 baseline grep |

**평가자가 `TSharedFromThis` 상속 권고 전 의무 절차**:

1. 베이스 클래스 헤더 (`Engine/Source/.../I<Class>.h`) 직접 grep — `TSharedFromThis` 상속 여부 확인
2. 이미 상속하면 — `AsShared()` + `StaticCastSharedRef<Derived>` 권고 ([[sources/ue-editor-propertyeditor]] §2.6.9 `AsSelf()` 헬퍼)
3. 상속 안 하면 — 자식 `TSharedFromThis<Derived>` 추가 권고 OK

### 7.3 평가자 권고가 vault 함정을 만든 사례 추적 매트릭스

| # | 일자 | 평가자 권고 | 결과 | filing-back |
| -- | -- | -- | -- | -- |
| 1 | 2026-05-12 | `IDetailCustomization` 자손에 `TSharedFromThis<Derived>` 추가 | **C2385** (외부 에이전트 빌드 에러) | [[sources/ue-editor-propertyeditor]] §2.6.9 함정 9 + 본 §7 |

## 8. ⭐⭐⭐ Baseline Grep 의무 (Cycle 5h #4 적용) 🟢

> [[sources/ue-meta-baseline-grep-system]] §7 patch 명세. main 이 본 agent .md read_raw 흡수 후 vault 일관성 자동 검증 의무 (mcwiki MCP 17 도구).

### 8.1 Pre-write (3 단계)

1. `mcwiki: list_pages` — `{kind: sources}` → 본 카테고리 slug 매트릭스 검증
2. `mcwiki: read_page` — `{kind: sources, slug: target_slug}` → stub vs enriched + § 구조 확인
3. `mcwiki: search` — `{query: <함정 키워드>, scope: wiki, limit: 50}` → 횡단 cross-link 누락 검증

### 8.2 Post-write (3 단계)

4. `mcwiki: lint` — broken / orphan / stale / ODD_FENCE / COUNT_MISMATCH 0 검증
5. `mcwiki: find_cross_link_broken` — `{slug, kind}` → broken_count == 0 (mcwiki v0.3.0+)
6. `mcwiki: append_log` — `{op, title, body}` → log.md 기록 의무

### 8.3 본 agent 함정 키워드 (search 의무)

평가 대상의 `find_cross_link_broken` broken_count == 0 의무 (Article 1).

### 8.4 governance §8.4 매트릭스 통합

| §8.4 5단 의무 | 본 § 매핑 |
| -- | -- |
| 1. Frontmatter | 의무 외 (vault 표준) |
| 2. Quality (🟢/🟡/🔴 3 tier) | post-write `read_page` 검증 |
| 3. Handoff (cross-link) | pre-write `list_pages` + `search` |
| 4. Evaluator (외부 평가) | post-write `find_cross_link_broken` (자동) + 사용자 수동 호출 시 `general-purpose` Task 위임 또는 ue-evaluator 호출 (Cycle 5p: auto X — timeout 심각) |
| 5. Audit | post-write `lint` |

## 9. 거부 조건 🟢

- 자신이 작성한 코드 평가 (bias 회피)
- 평가 외 작업 (코드 수정 등) — 적절한 specialist 호출 권유
- vault page write X — `mcwiki: write_page` 권한 없음

## 10. Cross-link

### 자동 로드

- [[sources/ue-ref-15-evaluatorrecipe]] · [[sources/ue-ref-17-qualitycriteria]] · [[sources/ue-ref-16-policypriority]]

### 페어 메타 agent

- [[sources/ue-agent-orchestrator]] (호출자)
- [[sources/ue-agent-audit]] · [[sources/ue-agent-wiki-maintainer]] (페어 메타)
- specialist 11 (평가 대상)

### 시스템 / 시리즈

- [[sources/ue-meta-baseline-grep-system]] §7 (agent prompt patch)
- [[sources/ue-meta-honest-limits]] (Self-eval bias 일반)
- [[sources/ue-meta-governance]] (Generator-Evaluator 분리 Article 1)
- [[sources/ue-meta-corrections]] (정정 카탈로그 — §7 추적 매트릭스 통합)

### Self-correction 사례 deep ref

- [[synthesis/instanced-subobject-customization-bypass]] §3.4 (외부 에이전트 보정)
- [[sources/ue-editor-propertyeditor]] §2.6.9 (함정 9 권위)

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | grep-listed stub 카드 (raw ingest) |
| 2026-05-12 | §3 Self-correction 의무 신규 (vault 평가자 자체 self-correction — C2385 사례, [[sources/ue-editor-propertyeditor]] §2.6.9 권위) |
| **2026-05-15 (Cycle 5n Round 1)** | ⭐⭐⭐ **stub + §3 → 정밀 11 절 (~280L)**. raw 본문 통합 — §2 핵심 원칙 / §3 자동 로드 / §4 8단계 매트릭스 / §5 채점 / §6 출력 형식 / §7 Self-correction (기존 유지 + 7.1-7.3 재구조) / §8 Baseline Grep 의무 / §9 거부 조건 / §10 Cross-link (5 카테고리). raw 본문 (~120L) + 기존 §3 (~100L) 통합 정밀 카탈로그 |
| **2026-05-17 (Cycle 5p)** | **§4 평가 8단계 매트릭스 갱신 — Stage 2.X Engine Authority Verification 추가** ([[00_meta/03_EvaluatorRecipe]] §1.5). UPROPERTY templated container / TArray cross-type / TObjectPtr / bitfield / DEPRECATED / Custom Serialize / Slate API 7 항목 (A~G) Engine 본가 grep 재검증. KMCProject Phase 2 postmortem 기반. |
| **2026-05-17 (Cycle 5p+1)** | ⚠ **정책 변경 — 사용자 수동 호출 전용** (auto-evaluator 호출 제거 — timeout 심각 89~193s/call). §1 Summary + §4 매트릭스 + §8.4 row #4 user-triggered framing 갱신. 사용자가 명시적으로 `/evaluate` 또는 Task tool 로 호출 시만 활성. |
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
