---
type: source
title: "UE refs — 18 ModelEvolutionAudit (분기별 staleness 감사 🕰)"
slug: ue-ref-18-modelevolutionaudit
source_path: raw/ue-wiki-llm/references/18_ModelEvolutionAudit.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
tags: [ue, reference, governance, audit, staleness, load-bearing]
---

# UE refs — 18 ModelEvolutionAudit 🕰

> Source: [[raw/ue-wiki-llm/references/18_ModelEvolutionAudit.md]] · Anthropic Article 1 의 *load-bearing component 검증* UE vault 적용

## 1. Summary

정기적 정책 staleness 감사 표준. **2축 staleness** (UE 5.x 진화 + Anthropic 모델 진화) + 8단 감사 프로세스 + 6종 결정 (Continue / Update / Simplify / Merge / Deprecate / Remove). Article 1 핵심 — *"harness 안 모든 컴포넌트는 모델이 못 하는 것에 대한 가정, stale 될 수 있다"*. vault [[00_meta/04_AuditPolicy]] 의 UE 특화 정밀판. CLAUDE.md §0.1.2 매핑.

## 2. Staleness 2축 🟢

### 2.1. UE 진화 축

```
UE 5.7.4 (현재) → 5.8 → 5.9 → 6.0 → 6.1 → ...
```

각 메이저 / 마이너 = 일부 정책 stale 가능:
- 5.x Nanite → Static Mesh LOD 정책 일부 무의미
- 5.x WorldPartition → Level Streaming 정책 일부 변경
- 5.x Mass Entity → TActorIterator 정책 보완 (ECS)
- 5.x Enhanced Input → Legacy 정책 deprecated
- 5.7+ TObjectPtr 표준화 → Raw pointer 정책 강화
- 6.0 (예정) Modular Game Framework → 권장 변경

### 2.2. Anthropic 모델 진화 축

```
Claude Sonnet 4.5 → Sonnet 4.6 → Opus 4.6 → Opus 5.0 → ...
```

Article 1 핵심: **모델 진화 시 일부 정책 stale 가능** — Evaluator 가 Generator 보다 너무 똑똑하면 정책 무의미. SonnetGen + OpusEval = SonnetGen+SonnetEval 보다 적은 비용 (글 1 사례).

## 3. 감사 주기 + 트리거 🟢

### 3.1. 정기 감사

| 시점 | 작업 | 대상 |
| -- | -- | -- |
| **분기 시작** (1/1, 4/1, 7/1, 10/1) | 모든 정책 status 검토 | 13 횡단 + 100+ sub-skill |
| UE 마이너 릴리스 (5.8 / 5.9 / 6.0) | 영향 정책 검증 | 해당 영역만 |
| 모델 진화 (Sonnet → Opus) | 정책 가치 재평가 | 모든 정책 — load-bearing |
| 사용자 보고 (정책 모순 / 깨짐) | 즉시 검토 | 보고된 정책 |

### 3.2. 즉시 감사 트리거 🚨

- 정책 따랐는데도 동작 안 함
- 정책끼리 충돌 ([[sources/ue-ref-16-policypriority]] 결정 트리도 안 풀림)
- UE 공식 문서 / 릴리스 노트와 모순
- Claude 가 정책 위반을 매우 정당화 (반복적)
- Evaluator 발견 사항이 정책에 없는 새 패턴

## 4. ⭐ 8단 감사 절차 🟢

### Stage 1 — Inventory (정책 목록화)

```
13 횡단 인덱스 (references/04~13)
+ 카테고리별 정책 (Components 6대 / Input 12종)
+ Sub-skill 별 "공통 정책" 블록
+ 결정 트리 50+
→ 각각 ID 부여 (P1, P2, ... Pn)
```

### Stage 2 — Source Validation (출처 검증)

| 검사 | 통과 기준 |
| -- | -- |
| ✅ 출처 명확 + UE 5.x 일치 | 공식 문서 / Engine grep 일치 |
| ⚠️ 출처 모호 또는 부분 일치 | 5.x 릴리스 노트 부분 | UE 검증 일부 |
| ❌ 출처 없음 또는 5.x 모순 | 즉시 Update 또는 Remove |

검증 채널: UE 5.x 공식 문서 / Engine 트리 grep / Release Notes / Lyra Sample / GDC 발표.

### Stage 3 — ⭐ Load-Bearing Test (Article 1 핵심)

> **글 1** — "한 컴포넌트씩 제거하며 영향 측정. 모델 업그레이드 시 일부 컴포넌트는 더 이상 load-bearing 이 아닐 수 있다."

```
각 정책 P 에 대해:
  1. P 제거 시 Claude (현재 모델) 가 같은 결과?
     - Yes → 정책 stale (모델 자체 학습)
     - No → still load-bearing

  2. 단순화 가능 (예: 12종 → 5종)?
     - Yes → 단순화 권장
     - No → 현재 복잡도 유지

  3. 다른 정책으로 대체 가능?
     - Yes → 통합 / 대체
     - No → 독립 유지
```

검증 방법 (Editor 시뮬):
```
Generator A: 정책 적용 + 코드 작성
Generator B: 정책 미적용 + 코드 작성
Evaluator (별도 Claude 인스턴스): 두 결과 비교
```

### Stage 4 — Cross-Reference Check

각 정책 쌍 (Pa, Pb) 충돌 검사 → [[sources/ue-ref-16-policypriority]] §2.2 결정 트리 적용 가능? 불가능 시 §2.2 "자주 발생하는 충돌" 추가 또는 정책 통합 / 단순화.

### Stage 5 — Real-World Application

```
실제 작업 시 정책이 어떻게 적용되었나:
- 작업 기록 (<외부>/) 분석
- 정책 위반 빈도
- 정책 적용 시 코드 품질 ([[sources/ue-ref-17-qualitycriteria]])
- 정책 무시 시 발생 버그
```

### Stage 6 — ⭐ Decision (6종) 🟢

| 결정 | 조건 | 처리 |
| -- | -- | -- |
| **Continue** | Stage 2 ✅ + Stage 3 still load-bearing + Stage 4 충돌 없음 | 변경 없음 |
| **Update** | Stage 2 부분 일치 또는 5.x 진화 반영 | 본문 갱신 + 변경 이력 |
| **Simplify** | Stage 3 단순화 가능 (12종→5종 등) | 축약 |
| **Merge** | Stage 4 다른 정책과 통합 가능 | 통합 + cross-link 갱신 |
| **Deprecate** | Stage 3 stale (모델 자체 학습) | Deprecated 마크 + 6개월 후 제거 |
| **Remove** | Stage 2 ❌ 또는 Stage 5 사용 안 함 | 즉시 제거 + 변경 이력 |

### Stage 7 — Implementation

```
1. 정책 파일 수정 (references/*.md 또는 sub-skill)
2. 03_WikiHarness.md §0.1 인덱스 표 갱신
3. CLAUDE.md §0.2 + §8.1 갱신 (해당 시)
4. cross-link 갱신
5. <외부>/_audits/{YYYY}_Q{N}_audit_report.md 작성
6. E:\ 미러 동기
```

### Stage 8 — Communication

사용자에게 보고: 변경 정책 N개 (6종 결정별) + 영향 sub-skill 매트릭스 + 사용자 협의 필요 사항 + 다음 감사 일정.

## 5. 정책 Status 매트릭스 (2026-Q2) 🟢

### 5.1. 13 횡단 인덱스 status

| # | 정책 | Status | Load-Bearing | UE 진화 영향 |
| -- | -- | -- | -- | -- |
| 04 | OverrideIndex | ✅ Active | High | 5.x 호환 |
| 05 | EditorOnlyIndex | ✅ Active | Medium | 5.x 호환 |
| 06 | InvalidationHotspots | ✅ Active | Medium | 5.x 호환 |
| 07 | ProfilingScopeRule | ✅ Active | High | 5.x 호환 |
| 08 | OverlapHotspots | ✅ Active | Medium | 5.x 호환 |
| 09 | GlobalIteratorPolicy | ✅ Active | High | **Mass Entity 보완 검토 (6.0 시)** |
| 10 | ComponentPolicies | ✅ Active | High | 5.x 호환 |
| 11 | AssetLoadingPolicy | ✅ Active | High | 5.x 호환 |
| 12 | AssetOptimizationPolicy | ✅ Active | High | **§2 5.x Nanite 일부 영향** |
| 14 | TaskHandoffTemplate | 🆕 New | High | (신규 — 글 1 핵심) |
| 15 | EvaluatorRecipe | 🆕 New | High | (신규 — 글 1 핵심) |
| 16 | PolicyPriority | 🆕 New | High | (신규 — 정책 충돌) |
| 17 | QualityCriteria | 🆕 New | High | (신규 — 측정 가능) |
| 18 | ModelEvolutionAudit | 🆕 New | Medium | (본 문서) |

### 5.2. 카테고리별 status

| 카테고리 | Status | 다음 감사 |
| -- | -- | -- |
| `[Components]` 6대 + 페어 | ✅ Active | 2026-08-01 |
| `[GameFramework]` Actor 11단 + 6대 | ✅ Active | 2026-08-01 |
| `[AssetClasses]` 자산별 + Cooked | ✅ Active | 2026-08-01 |
| `[Input]` 12종 Enhanced Input | ✅ Active | 2026-08-01 |
| `[Slate]/[UMG]` Super + Invalidation | ✅ Active | 2026-08-01 |
| `[Render]` (전용 정책 없음) | ⚠️ Gap | 향후 추가 |

## 6. UE 진화 추적 채널 🟢

### 6.1. 공식 채널 (의무 모니터링)

| 채널 | URL |
| -- | -- |
| UE Roadmap (Productboard) | https://portal.productboard.com/epicgames/ |
| Release Notes | https://docs.unrealengine.com/5.x/en-US/unreal-engine-5.x-release-notes/ |
| UE GitHub (Epic-Games) | branch `release` / `5.x` + commit "deprecated" / "breaking change" 검색 |
| GDC / Unreal Fest 발표 | 기조연설 / 워크샵 |
| Lyra Sample 갱신 | 베스트 프랙티스 |
| Epic Blog | https://www.unrealengine.com/en-US/blog |

### 6.2. 알려진 5.x 진화 영향 매트릭스

| 5.x 변경 | 영향 정책 | 권장 갱신 |
| -- | -- | -- |
| **5.4 Substrate Material** | 12_AssetOptimization §2 | Substrate PSO 별도 |
| **5.4 Mover Plugin** | Components/Movement | Mover 권장 (CMC deprecated 추세) |
| **5.5 Compatible Skeleton** | AssetClasses/Mesh §2 | 표준 패턴 강화 |
| **5.5 Iris Replication** | 11_AssetLoading + Network | Iris 옵션 |
| **5.6 Mass Entity 안정화** | 09_GlobalIterator | Mass = TActorIterator 대안 |
| **5.7 Enhanced Input UserSettings** | Input §1 | Player Mappable Key |
| **5.x IsDataValid 5.x 시그니처** | UObject / UAssetUserData | FDataValidationContext (Phase 4 적용) |
| **6.0 (예정)** | 모든 정책 | 향후 감사 |

## 7. ⭐ Anthropic 모델 진화 추적 (Article 1 핵심) 🟢

### 7.1. 모델별 정책 의존도 (예측)

| 모델 세대 | 정책 의존도 | wiki 역할 |
| -- | -- | -- |
| **Sonnet 4.5 (작성 시점)** | HIGH | 의무 정책 — Claude 따라야 함 |
| **Opus 4.6 (현재 추정)** | MEDIUM | 일부 정책 (Naming / const) 자체 학습 |
| **Future (5.0+)** | LOW | Reference — Claude 참고 |
| **Future (6.0+)** | 일부 deprecate | 자체 학습 / wiki = Edge case |

### 7.2. SonnetGen + OpusEval 패턴 (Article 1)

```
Generator: Claude Sonnet 4.5 (작은 / 빠른) — wiki 정책 따라 코드 작성, 토큰 LOW
Evaluator: Claude Opus 4.6 (큰 / 정확) — 15_EvaluatorRecipe 표준, 토큰 HIGH but 가치
결과: 빠른 작성 + 정확 평가 = 비용 효율
```

### 7.3. 모델 진화 시 wiki 변화 (자연스러운 staleness)

wiki 가 stale 되는 자연스러운 진화 — 정기 감사로 추적.

## 8. 감사 보고서 표준 🟢

### 8.1. 분기별 보고서 형식

```markdown
# Model Evolution Audit — Q{N} {YYYY}

## §1. 감사 범위
- 정책 N개 / UE 버전 {5.x.x} / Claude 모델 {모델명} / 감사자 {인스턴스 / 사용자}

## §2. 결과 요약 (6 결정별 카운트)
| Continue | Update | Simplify | Merge | Deprecate | Remove |

## §3. 변경 사항 (자세히)
### 3.1 Update — Policy X (12_AssetOptimization §2)
- 변경: Nanite 자동화 → LOD 정책 일부 무의미
- 갱신: §2 에 "Nanite 활성 시 LOD 강제 무시" 명시
- Cross-link: AssetClasses/Mesh §1.4

## §4. 향후 모니터링
## §5. 사용자 협의 필요
```

### 8.2. 보고서 위치

```
<외부>/_audits/{YYYY}_Q{N}_audit_report.md
```

## 9. 안티패턴 (8대) 🟡

| # | 함정 | 정답 |
| -- | -- | -- |
| 1 | 정책 작성 후 방치 | 분기별 정기 감사 의무 |
| 2 | UE 릴리스 노트 안 봄 | §6.1 채널 모니터링 의무 |
| 3 | "정책 따랐는데 깨짐" 무시 | 즉시 감사 트리거 |
| 4 | 모델 진화 무시 — 모든 정책 영구 유지 | Article 1 load-bearing 검증 |
| 5 | 정책 충돌 발견 + 16_PolicyPriority 갱신 X | 즉시 §2.2 추가 |
| 6 | 감사 결과 사용자 통보 X | Stage 8 — 큰 변경 시 협의 의무 |
| 7 | 한 정책만 보고 다른 영향 미평가 | Cross-Reference Check (Stage 4) |
| 8 | 자기 평가 (Claude 가 자기 정책 평가) | 별도 Evaluator 또는 사용자 |

## 10. Cross-link

- 모든 횡단 인덱스 (04-17) — 본 페이지가 정기 감사 대상
- 자매 governance hub: 📋 [[sources/ue-ref-14-taskhandofftemplate]] (Decision Log + 감사 인계) · 🔍 [[sources/ue-ref-15-evaluatorrecipe]] (정책 위반 검증) · ⚖ [[sources/ue-ref-16-policypriority]] (정책 충돌 — 감사 시 갱신) · 📊 [[sources/ue-ref-17-qualitycriteria]] (정책 적용 시 품질 측정)
- vault meta: [[00_meta/04_AuditPolicy]] (vault 일반판)
- 검증 베이스: [[sources/ue-ref-02-verificationlog]] (1차 검증) · [[sources/ue-meta-corrections]] (정정 누적)


### Cycle 5o reverse-link 보강 (high confidence missing)

- [[sources/ue-meta-governance]] (inbound=3, suggest_missing_cross_link high confidence)
## 11. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-13 | full slim 보강 — 2축 staleness + 8단 절차 + 6 결정 매트릭스 + 정책 status 매트릭스 (Q2) + UE 진화 영향 + Anthropic 모델 진화 추적 + 분기별 보고서 표준 + 안티패턴 8대 |
