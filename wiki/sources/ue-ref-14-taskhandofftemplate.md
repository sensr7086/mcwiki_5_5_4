---
type: source
title: "UE refs — 14 TaskHandoffTemplate (멀티 세션 인계 표준 📋)"
slug: ue-ref-14-taskhandofftemplate
source_path: raw/ue-wiki-llm/references/14_TaskHandoffTemplate.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
tags: [ue, reference, governance, handoff, context-reset, multi-session]
---

# UE refs — 14 TaskHandoffTemplate 📋

> Source: [[raw/ue-wiki-llm/references/14_TaskHandoffTemplate.md]] · Anthropic "harness-design-long-running-apps" Article 1 의 *context reset > compaction* 패턴 UE vault 적용

## 1. Summary

멀티 세션 작업의 인계 표준. **Context Reset + Handoff File** = Anthropic harness-design Article 1 정답 (compaction = 같은 세션 요약, context anxiety 해결 X). 5 섹션 표준 (Sprint Contract / Decision Log / Progress / Evaluator Findings / Next Session Brief). vault [[00_meta/05_HandoffProtocol]] 의 UE 특화 정밀판. CLAUDE.md §0.1.2 매핑.

## 2. 사용 시나리오

| 시나리오 | 사용 |
| -- | -- |
| 세션 종료 직전 | Claude 가 본 템플릿대로 `_HANDOFF_*.md` 작성 |
| 새 세션 시작 | 다음 Claude 가 `_HANDOFF_*.md` 우선 Read → 컨텍스트 복원 |
| 멀티 에이전트 (Generator → Evaluator) | Generator 작성 → Evaluator 평가 → 갱신 |
| 큰 작업 (5+ 단계) | 매 단계 종료 시 작성 |
| 컨텍스트 60% 도달 시 | 의무 작성 |

**표준 위치**: `<외부 사용자 폴더>` (gitignore — 임시 작업 파일).

## 3. 파일 명명 규칙 🟢

```
<외부>/{날짜YYYY-MM-DD}_{작업명}_{단계}.md

예시:
<외부>/2026-05-13_GameFramework_3sub-skill-완료.md
<외부>/2026-05-13_AssetClasses_Mesh-검증.md
<외부>/2026-05-13_Niagara-VFX_evaluator-피드백.md
```

## 4. 5섹션 표준 매트릭스 🟢

| § | 섹션 | 작성자 | 핵심 내용 |
| -- | -- | -- | -- |
| **§1** | **Sprint Contract** (Done 정의) | Generator (세션 시작) | 목표 / Done 체크리스트 / Out of Scope / 시간·비용 추정 |
| §2 | Decision Log | Generator | 주요 결정 + 근거 (글/정책 cross-link) + 거부된 대안 |
| §3 | Progress | Generator | 완료 / 진행 중 (현재 위치) / 대기 |
| **§4** | **Evaluator Findings** | **다른 Claude 또는 사용자** | 이슈 (Critical / Major / Minor) + 정책 위반 검사 + Cooked Build 검증 |
| **§5** | **Next Session Brief** | Generator | 우선순위 작업 + 사전 Read 의무 파일 + 알려진 함정 + 사용자 검증 필요 |

§6 첨부 (Optional) — 코드 스니펫 / 에러 로그 / 관련 자산.

## 5. Sprint Contract 작성 규칙 (§1)

### 5.1. 핵심 원칙

> Anthropic Article 1 — *Generator + Evaluator 가 코딩 전 'done' 협상*. vault 에서:
> - **Generator** = 본 세션 Claude
> - **Evaluator** = 다음 세션 Claude 또는 사용자
> - **Contract** = `<외부>/_HANDOFF_*.md §1`

### 5.2. Done 기준 작성 — 구체적 + 측정 가능

| ✅ 좋은 Done 기준 | ❌ 나쁜 Done 기준 |
| -- | -- |
| GameFramework/Actor §12 SpawnActor 히칭 방지 4단 패턴 추가 (코드 + 결정 트리 + 함정 + 체크리스트) | Actor 깊이 확장 |
| 횡단 인덱스 11_AssetLoadingPolicy.md cross-link 추가 | 정리 |
| E:\ 미러 동기 + grep 검증 | 동기화 |

### 5.3. 시간 / 비용 추정 (Article 1 표준)

| 추정 | 시간 | 토큰 비용 | 적합한 작업 |
| -- | -- | -- | -- |
| **LOW** | < 1 세션 | < 50K | 단일 sub-skill 갱신 / cross-link 추가 |
| **MEDIUM** | 1-3 세션 | 50K-200K | 새 sub-skill 1-3개 작성 |
| **HIGH** | 3+ 세션 | 200K+ | 새 카테고리 / 횡단 인덱스 신설 |

## 6. Decision Log 작성 규칙 (§2)

### 6.1. 무엇을 기록?

| 기록 | 기록 안 함 |
| -- | -- |
| 분할안 / 구조 결정 | 사소한 변수 이름 |
| Hard vs Soft 결정 | 일반 코드 작성 |
| 정책 충돌 해결 (16_PolicyPriority 적용) | 단순 typo 수정 |
| 거부된 대안 | 자명한 결정 |
| 사용자 명시 vs Claude 자체 결정 | 자명한 결정 |

### 6.2. 근거 형식

```
✅ 좋은 근거:
"Article 3 progressive disclosure (§1.1) — 30KB SKILL.md 는 Level 3 분리 권장.
 또한 12_AssetOptimizationPolicy §6 통합 매트릭스가 별도 reference 로 적합."

❌ 나쁜 근거:
"이 방식이 더 나아 보였음"
```

## 7. Evaluator Findings 작성 규칙 (§4) 🟢

### 7.1. 심각도 분류

| 🔴 Critical | 🟡 Major | 🟢 Minor |
| -- | -- | -- |
| Crash / Compile 실패 | Performance 저하 | Naming / Style |
| 메모리 누수 | 정책 부분 위반 | 주석 부족 |
| Replication 깨짐 | 코드 중복 | 변수 명명 |
| Cooked Build 동작 X | 가독성 저하 | 자명한 사소함 |

### 7.2. 외부 검증 명령어 표준 (UE 5.7.4)

```bash
# 1. Build (Development Editor)
"<UE>/Engine/Build/BatchFiles/Build.bat" <Project>Editor Win64 Development -Project="<.uproject>"

# 2. Build (Cooked / Shipping) — Article 1 핵심 검증
"<UE>/Engine/Build/BatchFiles/RunUAT.bat" BuildCookRun -project="<.uproject>" -platform=Win64 -clientconfig=Development -build -cook -package

# 3. 런타임 검증 (Editor 콘솔)
stat unit           ; 프레임 시간 (Game / Draw / GPU)
stat fps            ; FPS
stat memory         ; 메모리
memreport -full     ; 풀 메모리 리포트
stat slate          ; UMG/Slate
stat input          ; 입력 처리
profilegpu          ; GPU 프로파일 (1 프레임)
```

## 8. 표준 사용 흐름 🟢

### 8.1. 세션 시작 시 (Continue)

```
1. <외부>/ 폴더 → 가장 최근 _HANDOFF_*.md Read
2. §3 (진행 상태) — 어디까지 했나?
3. §5 (다음 세션 안내) — 우선순위 작업
4. §5.2 (사전 Read 의무 파일) Read
5. §1 (Sprint Contract) 의 Done 기준에 맞춰 진행
```

### 8.2. 세션 종료 시 (Hand Off)

```
1. <외부>/{날짜}_{작업명}_{단계}.md 작성
2. §1 Sprint Contract — Done 체크 (완료 / 부분 / 미완)
3. §2 Decision Log — 본 세션 결정 사항
4. §3 진행 상태 — 완료 / 진행 중 / 대기
5. §4 Evaluator Findings — 자체 평가 (다음 세션 / 사용자 보강)
6. §5 다음 세션 안내 — 우선순위 + 함정 + Read 파일
7. 사용자에게 handoff 파일 경로 보고
```

### 8.3. 멀티 에이전트 (Generator → Evaluator → Generator)

```
Session A (Generator):
  1. 작업 진행 + 코드 작성
  2. <외부>/{날짜}_{작업명}_generator.md 작성 (§1-§3)

Session B (Evaluator — 다른 Claude 인스턴스):
  1. _generator.md Read
  2. 15_EvaluatorRecipe 표준 적용 — 회의적 평가
  3. <외부>/{날짜}_{작업명}_evaluator.md 작성 (§4 채움)

Session C (Generator — 수정 Pass):
  1. _evaluator.md Read
  2. §4 이슈 수정
  3. <외부>/{날짜}_{작업명}_v2.md 작성
```

## 9. 안티패턴 (10대) 🟡

| # | 함정 | 정답 |
| -- | -- | -- |
| 1 | 세션 종료 시 handoff 안 작성 | 의무 — 다음 세션이 처음부터 시작 |
| 2 | "정리됨" 같은 모호한 진행 상태 | 구체적 + 측정 가능 (§3 표준) |
| 3 | Decision Log 근거 없음 | 글 / 정책 cross-link 의무 |
| 4 | Evaluator 자기 평가 (Article 1 함정) | 다른 Claude 또는 사용자가 §4 |
| 5 | "Cooked Build 검증" 적기만 함 | 실제 빌드 + 명령어 결과 첨부 |
| 6 | 다음 세션 안내 §5 없음 | 우선순위 + 함정 + Read 파일 의무 |
| 7 | handoff 파일 너무 김 (10KB+) | 5-8KB 권장 — 핵심만, 자세한 건 wiki cross-link |
| 8 | 에러 / 경고 로그 안 첨부 | 같은 에러 반복 — 첨부 의무 |
| 9 | Sprint Contract 없이 코딩 시작 | 사전 협상 의무 — Article 1 핵심 |
| 10 | `<외부>/` git commit | gitignore — 임시 파일 |

## 10. Cross-link

- 자매 governance hub: 🚨 [[sources/ue-ref-15-evaluatorrecipe]] (회의적 평가 표준) · 🎯 [[sources/ue-ref-16-policypriority]] (정책 충돌 해결) · 📊 [[sources/ue-ref-17-qualitycriteria]] (4 기준 100점)
- 기반: [[sources/ue-ref-02-verificationlog]] (영구 로그 — handoff 와 다른 용도) · [[sources/ue-ref-03-wikiharness]] (시나리오 라우팅)
- vault meta: [[00_meta/05_HandoffProtocol]] (vault 일반판) · [[00_meta/03_EvaluatorRecipe]] · [[00_meta/01_PolicyPriority]] · [[00_meta/00_QualityCriteria]]
- Audit hook: [[sources/ue-ref-18-modelevolutionaudit]] (분기별 handoff archive 검토)
