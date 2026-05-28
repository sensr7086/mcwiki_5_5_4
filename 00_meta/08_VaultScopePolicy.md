---
type: meta
title: "Vault Scope Policy — General UE 5.7.4 vault, KMCProject = 실측 사례"
slug: 08_VaultScopePolicy
created: 2026-05-16
last_updated: 2026-05-16
tags: [meta, governance, scope, kmcproject, case-study, independence]
---

# Vault Scope Policy — General UE 5.7.4 Knowledge Vault

> 본 룰은 vault 의 *정체성과 적용 범위* 를 명시한다. **vault 는 KMCProject 에 묶이지 않는다** — vault 는 UE 5.7.4 의 일반 지식 베이스이며, KMCProject 는 단지 *실측 사례 (case study)* 로 사용된다.
>
> 핵심: vault 안의 모든 페이지 (sources / entities / concepts / synthesis / meta) 는 *일반 UE 프로젝트* 에 재사용 가능한 지식이어야 한다. KMCProject 종속 내용은 *`mc-`* 슬러그 접두사를 가진 페이지에 한정하며, 이 페이지들도 KMCProject 의 *실측 결과* 가 vault 의 *일반 패턴* 을 *검증* 하는 페어 구조로 작성된다.

## 1. 적용 범위 (Scope Statement)

| 항목 | 정책 |
| -- | -- |
| **vault 정체성** | UE 5.7.4 general knowledge vault. 특정 게임/프로젝트에 종속되지 않음. |
| **KMCProject 역할** | 단지 *실측 (measurement) 프로젝트* — vault 의 일반 패턴을 검증하는 사례 (case study). |
| **재사용성 의무** | vault 의 모든 일반 지식 페이지 (mc- 슬러그가 아닌 모든 페이지) 는 *다른 UE 5.7.4 프로젝트* 에 그대로 적용 가능해야 함. |
| **명시 의무** | KMCProject 종속 페이지는 frontmatter / 본문 모두에 "KMCProject 실측 사례" 명시. |

## 2. 슬러그 접두사 규약

| 접두사 | 의미 | 예시 |
| -- | -- | -- |
| `ue-` | UE 5.7.4 일반 지식 (모든 카테고리 main) | `ue-coreuobject-uobject`, `ue-editor-asseteditorapi`, `ue-render-rdg` |
| `ue-agent-` | UE wiki LLM agent vault 카탈로그 (16 agent) | `ue-agent-components`, `ue-agent-editor` |
| `ue-meta-` | vault governance 페이지 | `ue-meta-baseline-grep-system`, `ue-meta-governance` |
| `ue-ref-` | reference catalog (정책 / quality / audit) | `ue-ref-07-profilingscopeRule`, `ue-ref-17-qualitycriteria` |
| **`mc-`** | **KMCProject 실측 사례 (case study)** — vault 일반 패턴의 *검증* 페어 | `mc-asset-validation-policy`, `mc-character-hit-reaction-pipeline`, `mc-combo-editor-levelsequence-lite` |

⭐ **핵심**: `mc-` 접두사 페이지는 *일반 패턴 (ue-* 페이지)* 의 *검증/실측/적용* 사례이며, vault 의 일반성을 *해치지 않는다*.

## 3. KMCProject 실측 페이지 작성 표준

### 3.1 frontmatter 의무

`mc-` 접두사 페이지는 frontmatter 에 다음 키 의무:

```yaml
---
type: source | synthesis  # mc- 페이지는 sources/synthesis kind 만 허용
project_role: case-study   # vault 의 *실측 사례* 임을 명시
project: KMCProject        # 실측 프로젝트 명시
measured_date: YYYY-MM-DD  # 실측 시점 (빌드 통과 / 측정 일자)
sources:                   # 검증된 vault 일반 패턴 (필수 1+)
  - "[[sources/ue-...]]"
tags: [..., kmcproject, case-study, measured]
---
```

### 3.2 본문 §1 Thesis 의무

본문 첫 § 에 *검증 페어 구조* 명시:

```markdown
## 1. Thesis

**vault 일반 패턴**: [[sources/ue-...]] §X (UE 5.7.4 표준 — 모든 프로젝트 적용 가능)

**KMCProject 실측 검증**: 본 페이지는 위 일반 패턴을 KMCProject 의 *<도메인>* 시스템에 적용한 *실측 사례*. 빌드 통과 (YYYY-MM-DD) + N 파일 검증 + 함정 M 종 카탈로그.

⭐ 본 페이지의 *일반화 가능 부분* (UE 5.7.4 적용 가능 패턴) 은 vault 일반 페이지 [[sources/ue-...]] 의 §Y 에 *역참조* 보강됨.
```

### 3.3 일반화 가능 부분 → vault 일반 페이지 역참조 의무

KMCProject 실측에서 발견된 *일반 함정 / 표준 패턴* 은 *반드시* vault 일반 페이지 (`ue-` 접두사) 에 *역참조 보강*:

- 예: KMCProject 빌드 시 `forward declare → UObject* C2664` 함정 → [[sources/ue-coreuobject-uobject]] §2.13 에 *일반 패턴* 으로 카탈로그화
- 예: KMCProject MCComboEditor `WorkflowOrientedApp` UBT RulesError → [[sources/ue-editor-unrealed-asseteditortoolkit]] §2.15 에 *일반 함정* 으로 카탈로그화

→ **vault 가 KMCProject 에 묶이지 않도록** 보장하는 핵심 메커니즘.

### 3.4 ⭐ Vault 작성 Plan 명시 의무 (Cycle 5o #12 신규)

**`mc-` 페이지 작성/갱신 작업 진입 *전*, 그리고 *코드 작성 전*** 에 다음 양식의 **vault 작성 Plan** 을 명시 보고 의무:

#### 3.4.1 표준 양식

```markdown
## Vault 작성 Plan (작업 진입 전 명시 의무 — 08_VaultScopePolicy §3.4)

### A. 신규 작성 페이지

| kind | slug | 핵심 § (3-5건) | 정당화 (왜 신규 필요) |
| -- | -- | -- | -- |
| synthesis | mc-...                            | §1 Thesis + §2 매핑 + §N 함정 매트릭스 | 신규 도메인 자산 + Trigger 임박 |
| sources  | mc-... (case study source)        | §1 Summary + §2 Key claims            | 일반 패턴의 *측정 데이터* 보관 |

### B. 갱신 페이지

| kind | slug | 변경 § | 영향 + cross-link |
| -- | -- | -- | -- |
| synthesis | mc-combo-editor-levelsequence-lite | §3.1 계층 갱신 / §7.1 함정 매트릭스 / §12 변경 이력 | UMCComboAsset → UMCTimelineAsset 자손 마이그레이션 명시 |
| sources  | ue-coreuobject-uobject §2.16 후보 | C3668 override 부적격 일반 패턴 | KMCProject 실측 함정 #6 → 일반화 격상 |

### C. frontmatter 영향 (mc- 페이지)

- [ ] `type: synthesis` 또는 `source`
- [ ] `project_role: case-study` (의무)
- [ ] `project: KMCProject` (의무)
- [ ] `measured_date: YYYY-MM-DD` (의무 — 빌드 통과 일자)
- [ ] `sources: [[sources/ue-...]]` cross-link 1+ (vault 일반 패턴 인용)
- [ ] `tags: [..., kmcproject, case-study, measured]`

### D. cross-link 영향 (역참조 보강 후보)

`ue-` 일반 페이지에 *KMCProject 실측 사례 참조* 보강 후보 명시:
- [[sources/ue-...]] §X — "Case Study: <도메인>" 섹션 후보
- [[sources/ue-...]] §Y — 함정 매트릭스 격상 후보

### E. 함정 / 일반화 후보 (Cycle N+1 후보)

KMCProject 작업 시 *새로 발견된 일반 함정* 을 vault 일반 페이지 enrich 후보로 사전 명시:
- [[sources/ue-...]] §N 신규 — <함정 시그니처> + 진단 + fix

### F. Post-write 검증 의무 (mcwiki v0.5.1 6 도구)

- [ ] `lint` — 0 issues
- [ ] `find_cross_link_broken({slug, kind})` — broken_count == 0
- [ ] `suggest_missing_cross_link({slug, kind})` — high/med confidence missing 0
- [ ] `find_claim_conflict({slug_a, slug_b})` — 휴리스틱 충돌 0 (관련 페어)
- [ ] `find_stale_baseline({slug, threshold_days: 90})` — is_stale == false
- [ ] `append_log({op, title, body})` — log.md 기록 의무
```

#### 3.4.2 의무 효과

| 의무 | 효과 |
| -- | -- |
| **A 신규 + B 갱신 표** | 작업 *진입 전* 어느 페이지가 영향 받는지 명확 — 누락 회피 |
| **C frontmatter 체크박스** | `mc-` 페이지 작성 표준 자동 준수 (§3.1 의무) |
| **D 역참조 보강 후보** | §3.3 의 역참조 의무를 *진입 전 명시* (작업 후 잊지 않음) |
| **E 일반화 후보** | KMCProject 실측 → vault 일반 패턴 격상 *사전 명시* — Cycle N+1 enrich 후보 풀에 자동 진입 |
| **F 6 도구 검증 plan** | mcwiki v0.5.1 의 4 Baseline Grep + lint + append_log — 작업 후 일관 검증 |

#### 3.4.3 적용 시점 — *코드 작성 *전* 의무*

```text
사용자 명령
  ↓
specialist agent 진입 (ue-*-specialist)
  ↓
§Pre-write Baseline Grep 4 단계 (Cycle 5o #11)
  ↓
⭐ Vault 작성 Plan 명시 (§3.4 본 양식) ← 본 정책의 핵심
  ↓ (main 검증 / 사용자 확인 — 선택)
실제 코드 작성 (Phase N)
  ↓
§Post-write 6 단계 — 위 §F 의 도구 호출
```

#### 3.4.4 사용 사례 — Cycle 5o KMCProject 작업 검증

| 작업 | §3.4 Plan 명시 여부 |
| -- | -- |
| Cycle 5d MCComboEditor Phase 1 (2026-05-15) | ❌ — Plan 없이 작업 후 vault 산출 (Cycle 5o #12 이전) |
| Cycle 5o Phase 2a (2026-05-16) | 🟡 — 부분 (`SMCComboPreviewSceneViewport.h/.cpp` 만 명시) |
| Cycle 5o UMCTimelineAsset Phase 1 설계 (2026-05-16) | ✅ — `ue-asset-specialist` 가 §5 mc- 페이지 작성/갱신 plan 자체 명시 → **본 §3.4 의 모범 사례** |

→ ue-asset-specialist 의 Phase 1 보고가 *본 §3.4 의무의 사례 1번째*. 이후 모든 `mc-` 작업은 본 양식 의무.

#### 3.4.5 미준수 시 평가 영향

[[sources/ue-agent-evaluator]] 의 평가 의무에 본 §3.4 위반 시 감점:

- Plan 양식 누락 (A/B 표 없음) — 중간 감점
- frontmatter 체크박스 누락 (C) — 큰 감점
- 역참조 / 일반화 후보 미명시 (D/E) — 중간 감점
- post-write 6 도구 검증 plan 누락 (F) — 작은 감점

### 3.5 ⭐ Handoff Document Compile-Level Verify 의무 (Cycle 5p 신규)

#### 3.5.1 배경

`mc-` 또는 `synthesis/*` handoff document (특히 Phase 1 설계 + Phase 2 specialist 인계용) 의 §2 격상 매트릭스 / §5 BC 패턴 / §7 specialist 분담 등에 작성된 **UPROPERTY 타입 / 함수 시그니처 / 직렬화 트레잇** 이 Engine 본가에서 실제 사용 가능한지 verify 의무.

본 §은 [[00_meta/03_EvaluatorRecipe]] Stage 2.X 의 *handoff document* 특화 보강 (Phase 1 evaluator 가 사용자 수동 호출 시 적용).

#### 3.5.2 Compile-Level Verify 7 항목 (specialist §pre-write A~G 와 동일)

handoff document 작성 시 각 항목 verify 필요:

- **A. UPROPERTY 부착 타입** — templated container (`TRange<>`, `TMap<,>`, `TSet<>`, `TVariant<>`, `TOptional<>`, `TFunction<>`) 직접 부착 가능성 verify (권위: `MovieSceneSection.h L787-788` + `MovieSceneFrameMigration.h L26-104`)
- **B. TArray cross-type copy-init** — `explicit` ctor 검증 (권위: `Containers/Array.h L745-755`)
- **C. TObjectPtr 변환** — `.Get()` 명시 의무
- **D. bitfield UPROPERTY** — Engine 본가 사용 사례 grep (권위: `MovieSceneSection.h L820, L824` + `BodyInstanceCore.h L38-59`)
- **E. DEPRECATED 마이그레이션 패턴** — CoreRedirects vs PostLoad 결정 (권위: `Class.cpp L1690-1760` + `MovieSceneSection.h L834-848`)
- **F. Custom Serialize trait** — `WithSerializer` + USTRUCT 래퍼 권위 (`MovieSceneFrameMigration.h L107-110`)
- **G. FCursorReply / EMouseCursor 시그니처** (권위: `CursorReply.h L33` + `ICursor.h L17~`)

#### 3.5.3 Phase 1 evaluator 의무 추가 (사용자 수동 호출 시)

[[00_meta/03_EvaluatorRecipe]] 의 Stage 2.X 적용 시 사용자가 evaluator 를 수동 호출하면:

1. handoff document 의 모든 UPROPERTY 타입 (§2 매트릭스 / §5 PostLoad 등) 을 Engine grep 으로 verify
2. 사용 사례 0건 또는 잘못된 타입 (USTRUCT 래퍼 미사용) → **Critical 감점 30** (Pass with notes 등급 강등 또는 Fail)
3. verify 결과를 evaluator 보고서 §"Compile-Level Engine Verify 매트릭스" 에 명시

#### 3.5.4 명세 작성자가 미리 할 수 있는 verify (의무화)

handoff document 작성 단계에서 (specialist 호출 전):

- 격상 매트릭스 작성 시 Engine 본가 grep 1회 batch (~30초)
- 각 UPROPERTY 행에 Engine 본가 사용 사례 라인 인용 의무 (예: `MovieSceneSection.h L788`)
- USTRUCT 래퍼 필요 시 명세에 명시 (specialist 가 따라 작성)

#### 3.5.5 예시 — 사례 (KMCProject Phase 2 정정 후)

```markdown
| **P0** | `SectionRange` | `FMCComboFrameRange` (USTRUCT 래퍼) | MovieSceneSection.h L788 (FMovieSceneFrameRange 미러) + MovieSceneFrameMigration.h L26-104 | StartFrame/EndFrame 통합. UPROPERTY 부착을 위해 TRange<FFrameNumber> 직접 부착 불가 → FMovieSceneFrameRange 패턴 차용 의무. |
```

→ 위 정정으로 specialist 가 1차 시도부터 USTRUCT 래퍼 작성 → refactor 사이클 0회. KMCProject Phase 2 실측 (`outputs/cycle-5p-handoff/01_timing_analysis.md`): refactor 회피 시 ~605s (37%) 단축 가능.

#### 3.5.6 Cross-link

- [[sources/ue-meta-baseline-grep-system]] §7 — specialist §pre-write A~G template
- [[00_meta/03_EvaluatorRecipe]] §Stage 2.X — evaluator 측 Engine Authority Verification (페어)
- [[00_meta/07_AgentBoundaryProtocol]] §Pre-Flight Engine Grep Batch — Orchestrator 측 사전 batch (페어)

## 4. vault 사용자 시나리오

### 4.1 일반 UE 프로젝트 사용자

UE 5.7.4 개발자는 vault 의 `ue-` 접두사 페이지만 읽고도 충분한 지식을 얻을 수 있어야 함.
- `ue-` 페이지는 KMCProject 언급이 *예시 / 보충 cross-link* 수준에만 있어야 함.
- `mc-` 접두사 페이지 cross-link 는 *추가 학습 자료* (실측 검증 사례) 로 분류, 핵심 지식은 `ue-` 페이지에 완결.

### 4.2 KMCProject 개발자 / 유사 도메인 개발자

격투 콤보 자산 / 부품 조립 자산 / 캐릭터 히트 리액션 등의 도메인을 다루는 개발자는 `mc-` 접두사 페이지를 *적용 가능한 실측 사례* 로 참조.
- `mc-` 페이지의 *결정 / trade-off / 함정* 부분을 직접 차용 가능.
- `mc-` 페이지의 `vault 일반 패턴` 부분 (§1 Thesis 의 `[[sources/ue-<카테고리>]]` 인용) 으로 일반화 베이스 학습.

## 5. 위반 사례 + 회피 패턴

### 5.1 ❌ 위반 — vault 일반 페이지가 KMCProject 종속

```markdown
## §X. SpawnActor 히칭 방지

UE 5.7.4 에서 SpawnActor 호출 시 **KMCProject 의 mc-actor-spawn-subsystem 의 4단 패턴** 을 사용해야 한다.
```

**문제**: `ue-gameframework-actor` 페이지가 KMCProject (mc-) 의 구현에 의존함을 *암시*. 일반 UE 프로젝트 사용자는 KMCProject 를 모름.

### 5.2 ✅ 정답 — vault 일반 + KMCProject 실측 페어

```markdown
## §X. SpawnActor 히칭 방지 — 4단 표준 패턴

UE 5.7.4 의 PreLoad → Wait → SpawnActorDeferred → FinishSpawning 4단 패턴 표준 (Epic 공식 / 모든 UE 프로젝트 적용).

→ KMCProject 실측 검증: [[synthesis/spawnactor-hitching-4-step-pattern]] + [[synthesis/mc-actor-spawn-subsystem-implementation]] (Hot 1ms 측정)
```

**개선**: 일반 패턴이 vault 일반 페이지에 *완결*. KMCProject 페어는 *cross-link 보충* (선택적 참조).

## 6. mcwiki 도구 vs Scope 정책

mcwiki MCP 4 Baseline Grep 도구 ([[sources/ue-meta-baseline-grep-system]]) 는 vault scope 정합성을 *자동 검증* 한다:

| 도구 | scope 정책 검증 |
| -- | -- |
| `find_cross_link_broken` | `mc-` 페이지가 `ue-` 페이지를 참조하는 *역방향* 만 broken 검증 — 일반성 보장 |
| `suggest_missing_cross_link` | `mc-` 페이지의 일반 패턴 부분이 `ue-` 페이지에 *역참조 누락* 시 missing 검출 |
| `find_claim_conflict` | 같은 일반 패턴을 `ue-` vs `mc-` 가 *다르게 claim* 시 충돌 검출 |
| `find_stale_baseline` | `ue-` 페이지 staleness 추적 — `mc-` 페이지 의존 변경 시 분기별 audit |

## 7. 현재 vault scope 진단 (2026-05-16)

| 분류 | 페이지 수 | 비고 |
| -- | -- | -- |
| `ue-` 일반 지식 (sources) | 198 | UE 5.7.4 표준 — 모든 UE 프로젝트 재사용 가능 |
| `mc-` KMCProject 실측 (sources) | 2 | `mc-asset-validation-policy`, `mc-soft-skeletalmesh-ragdoll` |
| `mc-` KMCProject 실측 (synthesis) | 7 | hit-reaction / soft-asset / spawn-subsystem 2종 / combo-editor / validation-* 2종 |
| **vault scope 비율 (`ue-` : `mc-`)** | **198 : 9** (96% 일반 / 4% 실측) | 일반성 강조 — KMCProject 종속 X |

→ vault 는 *KMCProject 가 없어도 95%+ 가치* 를 가짐. KMCProject 페이지는 *일반 패턴의 실측 보강* 으로 한정.

## 8. 한 줄 정리

> **vault 는 UE 5.7.4 의 일반 지식 베이스다. KMCProject 는 단지 vault 의 일반 패턴을 *검증* 하는 *실측 사례* 다.** `mc-` 접두사 페이지는 frontmatter `project_role: case-study` 명시 + vault 일반 페이지 (`ue-`) 와의 *검증 페어* 구조 의무.

## 9. 관련 governance

- [[00_meta/00_QualityCriteria]] — 4기준 가중 (Performance/Memory/Network/Maintainability) — vault 일반성은 Maintainability 25% 의 부분
- [[00_meta/05_HandoffProtocol]] — `mc-` 페이지 작성 시 `ue-` 페이지 역참조 의무 핸드오프
- [[00_meta/06_VaultCitationRule]] — 🟢/🟡/🔴 3 tier — `mc-` 페이지의 실측 데이터는 🟢 (직접 측정), 일반화 부분은 🟡 (외삽 가능) 표기 의무
- [[00_meta/07_AgentBoundaryProtocol]] — main ↔ specialist boundary — `mc-` 페이지 작성 시 specialist agent 의 `ue-` 일반 패턴 학습 의무

## 10. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-16 (Cycle 5o #9) | 최초 작성 — vault scope 정책 명시 (KMCProject = 실측 사례, vault 는 KMCProject 에 묶이지 않음). 슬러그 접두사 규약 + KMCProject 실측 페이지 작성 표준 + 위반/정답 사례 + scope 진단 매트릭스. |
| 2026-05-16 (Cycle 5o #12) | **§3.4 신규 — Vault 작성 Plan 명시 의무**. mc- 페이지 작성/갱신 작업 진입 *전* + 코드 작성 *전* 표준 양식 (A 신규 + B 갱신 + C frontmatter + D 역참조 + E 일반화 + F 6 도구 검증 plan) 의무 보고. ue-asset-specialist 의 UMCTimelineAsset Phase 1 보고가 본 §3.4 의 모범 사례. 미준수 시 평가 감점. |
| 2026-05-17 (Cycle 5p #2) | **§3.5 신규 — Handoff Document Compile-Level Verify 의무**. KMCProject Phase 2 postmortem 기반 (refactor 사이클 2회 / ~390-735s 손실 / ~605s 개선 가능). handoff document 의 UPROPERTY 타입 / 시그니처 / 직렬화 트레잇을 Engine 본가 grep 으로 verify 의무 (7 항목 A~G). Phase 1 evaluator (사용자 수동 호출 시) Critical 30 감점. 명세 작성자가 Engine 본가 인용 의무. specialist `§pre-write 1단계` + 00_meta/03 `Stage 2.X` + 00_meta/07 `§Pre-Flight Engine Grep Batch` 3중 verify 의 *handoff document 측 의무화*. |
