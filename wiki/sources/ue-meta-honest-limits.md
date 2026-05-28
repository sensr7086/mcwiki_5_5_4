---
type: source
title: "UE meta — CLAUDE-wiki-honest-limits"
slug: ue-meta-honest-limits
source_path: raw/ue-wiki-llm/meta/CLAUDE-wiki-honest-limits.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-28
audit_5_5_4: pass-minor-numeric  # 2026-05-28 Phase 2-B remaining audit
tags: [ue, meta, governance, honest, self-eval-bias, six-essential-limits]
citation_disclosure: "본 카드 자체 = 🟢 vault 직시 (§2 Self-eval bias 사례 2건이 [[sources/ue-meta-corrections]] §2.4 + [[sources/ue-agent-evaluator]] §3 filing-back + Cycle 5d 2차 §2.11.1 격상으로 모두 vault 안 검증 가능). raw 본문 갱신은 별도 단계."
---

# UE meta — CLAUDE-wiki-honest-limits

> Source: [[raw/ue-wiki-llm/meta/CLAUDE-wiki-honest-limits.md]]

## 1. Summary

⚠️ 위키의 **6대 본질 문제 + 현실적 기대치** — 비숙련 + 게임 로직 + UE 5.7.x + 컴파일/Cooked 검증 루프 같이 일 때만 +15~25 %p (Components/GameFramework). Animation +25 %p / Render +5 %p / 비-UE 0 %p. 컴파일 검증 의무 + Cooked Build 검증 의무 + `[inferred]` 외부 검증 의무.

### 1.1 6대 본질 문제 (정밀판, 2026-05-15 Cycle 5d 2차 갱신)

| # | 본질 문제 | 현재 (2026-05-15) | 완화 절차 권위 |
| -- | -- | -- | -- |
| 1 | UE **5.7.4 만 검증** — 다른 마이너 외삽 | (그대로) — 분기 audit 시 새 마이너 검증 | [[sources/ue-meta-governance]] §5.2 |
| 2 | cross-platform 커버리지 ≠ 100% (Mobile / VR / Console 일부 외삽) | (그대로) — P2 우선순위 | [[sources/ue-meta-improvement-roadmap]] §2.3 P2.1 |
| 3 | KMCProject 외 검증 사이트 비율 | ~50% (Phase 4G) → **~65% (Cycle 5d 2차)** | [[sources/ue-coreuobject-uobject]] §2.11.1 (single-case 격상 사례) |
| 4 | Self-eval bias (vault 평가자 ≠ vault 작성자 의무) | 사례 2건 catalog 완료 + filing-back | 본 §2 (사례 1+2) + [[sources/ue-agent-evaluator]] §3 |
| 5 | raw/ ingest = **2026-05-09 스냅샷** — 그 이후 미반영 | (그대로) — Q2 2026 audit 시 재ingest | [[sources/ue-meta-improvement-roadmap]] §2.3 P2.4 |
| 6 | 비-UE 콘텐츠 (Anthropic SDK / 외부 패키지) 0 % 가산 | (의도된 한계) — 별도 vault 권장 | [[sources/ue-meta-improvement-roadmap]] §2.3 P2.2 |

→ **6 대 한계 중 #3 (검증 사이트 비율) 만 Cycle 5d 2차 시점 격상**. 나머지 5건은 분기 audit / 외부 의존 / 의도된 한계.

## 2. Self-eval bias 사례 누적 (신규 §)

> [[00_meta/06_VaultCitationRule]] §6 평가자 self-eval bias 의 *구체 사례* 누적.

### 2.1 사례 #1 — vault 평가자가 vault 함정 9 를 권고 (2026-05-12) 🟢

**상황**:
- 외부 에이전트 (`StaticMeshNiagaraPreview_Journey.md`) 가 `IDetailCustomization` 자손 작성.
- vault 평가자 (`ue-wiki-llm:ue-evaluator`) 채점 86/100. Major 권고: *`TSharedFromThis` 상속 추가*.
- 외부 에이전트 반영 → **C2385 다이아몬드 상속** ([[sources/ue-editor-propertyeditor]] §2.6.9 의 함정 9 그대로).

**vault 가 vault 함정을 만든 경로**:
- vault 평가자 (`ue-agent-evaluator`) 가 *함정 9 의 안티패턴을 권고*.
- 즉 vault 안 *두 페이지가 모순* — `ue-editor-propertyeditor §2.6.9` 는 "자식 TSharedFromThis 금지", `ue-agent-evaluator` 는 "TSharedFromThis 권고".
- 평가자 카드에 `IDetailCustomization` 베이스의 `TSharedFromThis` 검증 의무 명시 안 됨.

**filing-back** (✅ 2026-05-12):
- [[sources/ue-agent-evaluator]] §3 self-correction 의무 신규.
- 권고 전 의무 절차 3단 (baseline grep / `AsShared()` 권고 / 신규 상속 OK).
- 추적 매트릭스 (사례 1건 등재).

### 2.2 사례 #2 — 우리 측 비교 매트릭스의 self-eval bias (2026-05-12) 🟢

**상황**:
- 우리 측에서 "MCWiki 활용 vs 비활용 차이" 비교 매트릭스 작성.
- A/B/C 시나리오 정량 추정 (라인 / 토큰 / 진단 시간 / ROI) 자기 평가.
- vault `[[sources/ue-measure-readme]]` 의 ⭐ 등급 (가상 baseline + 자기 평가) — 신뢰도 가장 낮음.

**자기참조성 루프**:
1. 우리가 vault 활용 사이트를 *내가 판단*.
2. vault 비활용 시나리오를 *내가 상상* (실재 없음).
3. ROI 자릿수 압도 결론 — 자기 평가.
4. 측정 페이지 작성 제안 — 자기 결과를 자기 평가로 정착.

**보정**:
- 사용자가 *외부 비판적 시각* 요청 → 매트릭스 10건의 위반 사이트 자체 식별.
- 외부 에이전트 자료 1건 도착 → A/B/C 시나리오의 가정 자체 보정 (외부도 함정 9 + 10 둘 다 만남).
- 결론: ⭐⭐ 신뢰도 측정 페이지 1건 ([[sources/ue-measure-instancedsubobject-2026-05-12]]) — 가설 H1 (Self-eval bias 측정) 의 첫 ⭐⭐ 데이터.

### 2.3 일반 패턴 — vault 측 self-eval bias 회피 의무

| 시점 | 의무 |
| -- | -- |
| 평가자 권고 작성 | 베이스 클래스 inheritance baseline grep |
| 측정 페이지 작성 | ⭐⭐⭐ (별도 세션 + 별도 평가자) 추구. ⭐ 등급은 *vault summary 누적* 에만 사용, *결론 도출* 금지 |
| 비교 매트릭스 / ROI 분석 | 외부 자료 1건 이상 확보 후 작성. 가상 baseline 단독 금지 |
| filing-back | 🔴 INFERRED 사이트의 *향후 검증* 명시 의무 |

## 3. Cross-link

- 원본: [[raw/ue-wiki-llm/meta/CLAUDE-wiki-honest-limits.md]]
- 카테고리: meta
- self-correction 페어: [[sources/ue-agent-evaluator]] §3
- citation rule: [[00_meta/06_VaultCitationRule]] §6
- 측정 시스템: [[sources/ue-measure-readme]] / [[sources/ue-measure-summary]]
- ⭐⭐ 측정 1건: [[sources/ue-measure-instancedsubobject-2026-05-12]] (사례 #2 의 결과)
- 함정 9 권위: [[sources/ue-editor-propertyeditor]] §2.6.9 (사례 #1 의 권위)

### Cycle 5d 2차 신규 페어 (2026-05-15)

- [[sources/ue-meta-confidence-tags]] §6 — self-eval bias 회피의 평가자 측 의무
- [[sources/ue-meta-corrections]] §2.4 + §5 — vault 자체 진단 실패 (PI 매크로) 권위 사례
- [[sources/ue-meta-governance]] §4.2 — Generator-Evaluator 분리 권위 + 실패 사례 2건 통합
- [[sources/ue-meta-improvement-roadmap]] §2 P0.1/P0.2 — vault 자체 진단 실패 / 평가자 함정 권고 완료 사례
- [[sources/ue-coreuobject-uobject]] §2.11.1 — single-case 의심 회피의 격상 사례 (Cycle 5d 2차 검증)


### Cycle 5o reverse-link 보강 (high confidence missing)

- [[sources/ue-ref-00-readme]] (inbound=3, suggest_missing_cross_link high confidence)
## 4. Changelog

| 날짜 | 변경 |
| -- | -- |
| 2026-05-09 | 카드 작성 (raw ingest) |
| 2026-05-12 | **§2 Self-eval bias 사례 누적 신규** — (1) vault 평가자가 vault 함정 9 를 권고한 사례 (외부 에이전트 Journey 실증, filing-back 완료). (2) 우리 측 비교 매트릭스의 self-eval bias 사례 (외부 자료 1건으로 보정, ⭐⭐ 측정 페이지로 정착). §2.3 일반 패턴 — 4 사이트별 self-eval 회피 의무. raw 본문 갱신은 별도 단계. |
| **2026-05-15 (Cycle 5d 2차)** | **citation_disclosure 갱신** (🟡 → 🟢) — §2 self-eval bias 사례 2건이 corrections.md §2.4 (PI 매크로) + agent-evaluator §3 (Generator-Evaluator 분리) + §2.11.1 격상 (single-case → 일반 패턴) 3 사이트로 모두 vault 안 검증 가능. tags + last_updated 갱신. Cycle 5e 후보 풀 cross-link 추가 (§3 권위). |
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 pass-minor-numeric** (자동 분석)

raw 5.5.4 vs 5.7.4 diff: 시그니처 0 / 추가 0 / 제거 0 / 수치 0 — 표면 변경만, 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효.

raw 5.5.4 본문 직접 참조: `raw/ue-wiki-llm_5_5_4/meta/CLAUDE-wiki-honest-limits.md` · 5.7.4 vintage 비교: `raw/ue-wiki-llm/meta/CLAUDE-wiki-honest-limits.md`
