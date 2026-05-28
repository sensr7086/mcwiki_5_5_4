---
name: model-evolution-audit
description: 정기적 정책 staleness 감사 표준 (분기별). UE 5.x 진화 (5.7→5.8→6.0) + Anthropic 모델 진화 (Sonnet→Opus 4.6→6.0)에 따라 정책 stale 가능. 글 1 의 "load-bearing component 검증" 적용.
---

# 18. Model Evolution Audit — 정책 Staleness 감사 표준

> 본 문서는 **글 1 (harness-design) 의 핵심 통찰** — "**hardness 안 모든 컴포넌트는 모델이 못 하는 것에 대한 가정이며 stale 될 수 있다**" — 의 LLM_Wiki 적용. **분기별 정기 감사** 로 정책의 staleness 검토.
>
> **요지**: 5.7.4 기준 작성된 정책들이 5.8 / 6.0 / 7.0 에서 stale 가능. **정기적 검증 + 한 정책씩 제거하며 영향 측정**.

---

## 0. Staleness 의 두 축

### 0.1 UE 진화 축

```
UE 5.7.4 (현재) → 5.8 → 5.9 → 6.0 → 6.1 → ...

각 메이저 / 마이너 버전 = 일부 정책 stale 가능:
- 5.x Nanite — Static Mesh LOD 정책 일부 무의미
- 5.x WorldPartition — Level Streaming 정책 일부 변경
- 5.x Mass Entity — TActorIterator 정책 보완 (Mass = ECS)
- 5.x Enhanced Input — Legacy 정책 deprecated
- 5.7+ TObjectPtr 표준화 — Raw pointer 정책 강화
- 6.0 Lyra Style → Modular Game Framework — 권장 변경
```

### 0.2 Anthropic 모델 진화 축

```
Claude Sonnet 4.5 → Sonnet 4.6 → Opus 4.6 → 4.7 → 5.0 → ...

각 모델 진화 = 일부 정책 무의미 가능 (글 1 핵심):
- 모델이 더 좋아지면 = "어셋 로드 정책" 같은 helper 정책이 모델 단독 능력 안 들어감
- 글 1 사례: SonnetGen → OpusEval = SonnetGen+SonnetEval 보다 적은 비용
- 즉 정책 자체가 stale 될 가능성 — Evaluator 가 Generator 보다 너무 똑똑하면 정책 무의미
```

---

## 1. 감사 주기 + 트리거

### 1.1 정기 감사 (분기별)

| 시점 | 작업 | 대상 |
|------|------|------|
| **분기 시작** (1/1, 4/1, 7/1, 10/1) | 모든 정책 status 검토 | 13 횡단 인덱스 + 100+ sub-skill |
| UE 마이너 릴리스 (5.8 / 5.9 / 6.0) | 영향받는 정책 검증 | 해당 영역 정책만 |
| 모델 진화 (Sonnet → Opus) | 정책 가치 재평가 | 모든 정책 — load-bearing 검증 |
| 사용자 보고 (정책 모순 / 깨짐) | 즉시 검토 | 보고된 정책 |

### 1.2 트리거 시그널

```
🚨 즉시 감사 트리거:
- 정책 따랐는데도 동작 안 함 (정책 → 코드 → 검증 실패)
- 정책끼리 충돌 발견 (16_PolicyPriority 결정 트리도 안 풀림)
- UE 공식 문서 / 릴리스 노트와 모순
- Claude 가 정책 위반을 매우 정당화 (반복적)
- Evaluator 발견 사항이 정책에 없는 새로운 패턴
```

---

## 2. 감사 절차 (8단계)

### Stage 1 — Inventory (정책 목록화)

```
┌─ 13 횡단 인덱스 (references/04~13)
├─ 카테고리별 정책 (Components 6대 / Input 12종 등)
├─ Sub-skill 별 정책 (각 SKILL.md 의 "공통 정책" 블록)
└─ 결정 트리 (정책별 §내 결정 트리 50+)

→ 각각 ID 부여 (P1, P2, ... Pn)
```

### Stage 2 — Source Validation (출처 검증)

```
각 정책에 대해:
  □ UE 5.x 공식 문서와 일치?
  □ Engine 트리 grep 검증 (예: bCanEverTick, DOREPLIFETIME)?
  □ 5.x Release Notes 와 모순?
  □ 5.x Lyra Sample 과 일치?
  □ Epic Games 공식 발표 (Conference / GDC) 와 일치?

스코어:
  ✅ 출처 명확 + UE 5.x 일치
  ⚠️ 출처 모호 또는 부분 일치
  ❌ 출처 없음 또는 5.x 모순
```

### Stage 3 — Load-Bearing Test (글 1 핵심)

> **글 1 표준** — "한 컴포넌트씩 제거하며 영향 측정. 모델 업그레이드 시 일부 컴포넌트는 더 이상 load-bearing 이 아닐 수 있다."

```
각 정책에 대해:
  1. 정책을 제거하고 Claude (현재 모델) 가 같은 결과를 내나?
     - Yes → 정책 stale (모델이 자체 학습)
     - No → 정책 still load-bearing
  
  2. 정책을 단순화 (예: 12종 → 5종) 가능?
     - Yes → 단순화 권장
     - No → 현재 복잡도 유지
  
  3. 다른 정책으로 대체 가능?
     - Yes → 통합 / 대체
     - No → 독립 유지

테스트 방법 (Editor 시뮬):
  - Generator Claude 1: 정책 적용 + 코드 작성
  - Generator Claude 2: 정책 미적용 + 코드 작성
  - Evaluator Claude (별도 인스턴스): 두 결과 비교
```

### Stage 4 — Cross-Reference Check (정책 간 충돌)

```
각 정책 쌍 (Pa, Pb) 에 대해:
  □ 충돌 케이스 발생?
  □ 16_PolicyPriority 결정 트리로 해결 가능?
  □ Edge case (해결 안 되는) 존재?

발견 시:
  - 16_PolicyPriority §2.2 "자주 발생하는 충돌" 추가
  - 또는 정책 통합 / 단순화
```

### Stage 5 — Real-World Application (실 적용 검증)

```
실제 작업 시 정책이 어떻게 적용되었나:
  □ 작업 기록 (<외부>/) 분석
  □ 정책 위반 빈도
  □ 정책 적용 시 코드 품질 (17_QualityCriteria)
  □ 정책 무시 시 발생한 버그

도구:
  - grep _handoffs 의 Decision Log
  - 실제 게임 빌드 + Cooked 검증 결과
```

### Stage 6 — Decision (계속 / 수정 / 폐기)

각 정책에 대한 결정:

| 결정 | 조건 | 처리 |
|------|------|------|
| **Continue** | Stage 2 ✅ + Stage 3 still load-bearing + Stage 4 충돌 없음 | 변경 없음 |
| **Update** | Stage 2 부분 일치 또는 5.x 진화 반영 필요 | 정책 본문 갱신 + 변경 이력 |
| **Simplify** | Stage 3 단순화 가능 | 12종 → 5종 등 축약 |
| **Merge** | Stage 4 다른 정책과 통합 가능 | 정책 통합 + cross-link 갱신 |
| **Deprecate** | Stage 3 stale (모델 자체 학습) | Deprecated 마크 + 6개월 후 제거 |
| **Remove** | Stage 2 ❌ 또는 Stage 5 사용 안 함 | 즉시 제거 + 변경 이력 |

### Stage 7 — Implementation (변경 적용)

```
1. 정책 파일 수정 (references/*.md 또는 sub-skill)
2. 03_WikiHarness.md §0.1 인덱스 표 갱신
3. CLAUDE.md §0.2 + §8.1 갱신 (해당 시)
4. cross-link 갱신
5. <외부>/{날짜}_audit_{분기}.md 작성 (감사 기록)
6. E:\ 미러 동기
```

### Stage 8 — Communication (사용자 통보)

```
사용자에게 보고:
  - 변경된 정책 N개 (Continue / Update / Simplify / Merge / Deprecate / Remove)
  - 영향 받는 sub-skill 매트릭스
  - 사용자 협의 필요 사항 (큰 변경 시)
  - 다음 감사 일정
```

---

## 3. 정책 Status 매트릭스 (현재)

> **분기별 갱신 의무**. 각 정책의 현재 status + load-bearing 평가.

### 3.1 13 횡단 인덱스 (2026-05-05 첫 평가)

| # | 정책 | Status | Load-Bearing | UE 진화 | 비고 |
|---|------|--------|--------------|--------|------|
| 04 | OverrideIndex | ✅ Active | High | 5.x 호환 | virtual + Super |
| 05 | EditorOnlyIndex | ✅ Active | Medium | 5.x 호환 | WITH_EDITOR |
| 06 | InvalidationHotspots | ✅ Active | Medium | 5.x 호환 | UMG |
| 07 | ProfilingScopeRule | ✅ Active | High | 5.x 호환 | 모든 콜백 |
| 08 | OverlapHotspots | ✅ Active | Medium | 5.x 호환 | PrimitiveComponent |
| 09 | GlobalIteratorPolicy | ✅ Active | High | 5.x 호환 (Mass Entity 보완 검토) | 6.0 시 재평가 |
| 10 | ComponentPolicies | ✅ Active | High | 5.x 호환 | 6대 |
| 11 | AssetLoadingPolicy | ✅ Active | High | 5.x 호환 | 8단 |
| 12 | AssetOptimizationPolicy | ✅ Active | High | **5.x Nanite 일부 영향** | §2 StaticMesh LOD 부분 |
| 13 | InputPolicy | ✅ Active | High | 5.x 호환 | Enhanced Input 표준 |
| 14 | TaskHandoffTemplate | 🆕 New | High | (신규) | 글 1 핵심 |
| 15 | EvaluatorRecipe | 🆕 New | High | (신규) | 글 1 핵심 |
| 16 | PolicyPriority | 🆕 New | High | (신규) | 정책 충돌 |
| 17 | QualityCriteria | 🆕 New | High | (신규) | 측정 가능 |
| 18 | ModelEvolutionAudit | 🆕 New | Medium | (신규) | 본 문서 |

### 3.2 카테고리별 정책 status

| 카테고리 | 정책 수 | Status | 다음 감사 |
|---------|--------|--------|---------|
| `[Components]` | 6대 + 페어 정책 | ✅ Active | 2026-08-01 |
| `[GameFramework]` | Actor 11단계 + 6대 | ✅ Active | 2026-08-01 |
| `[AssetClasses]` | 자산별 + Cooked Build | ✅ Active | 2026-08-01 |
| `[Input]` | 12종 (5.x Enhanced Input) | ✅ Active | 2026-08-01 |
| `[Slate]` / `[UMG]` | UWidget Super + Invalidation | ✅ Active | 2026-08-01 |
| `[Render]` | (전용 정책 없음) | ⚠️ Gap | 향후 추가 |

---

## 4. UE 진화 추적 채널

### 4.1 공식 채널 (의무 모니터링)

```
1. UE Roadmap (Public Trello)
   - https://portal.productboard.com/epicgames/

2. Release Notes (5.x → 5.x+1)
   - https://docs.unrealengine.com/5.x/en-US/unreal-engine-5.x-release-notes/

3. UE GitHub (Epic-Games)
   - Branch: 5.x → 5.x+1 → master
   - Commit 검색: "deprecated", "breaking change"

4. GDC / Unreal Fest 발표
   - 기조연설 / 워크샵 영상
   - 새 시스템 / 정책 변화

5. Lyra Sample 갱신
   - 베스트 프랙티스 변화

6. Epic 공식 블로그
   - https://www.unrealengine.com/en-US/blog
```

### 4.2 자동화 추적 (선택)

```bash
# Release Notes Diff (수동)
diff UE-5.7-release-notes.md UE-5.8-release-notes.md > 5.7-to-5.8.diff
# → Claude 가 diff 분석 + 영향받는 정책 식별

# UE GitHub PR / Commit 추적 (선택)
git log --since="2026-01-01" --grep="deprecated" Engine/Source/Runtime/Engine
# → 정책 cross-link 자동 갱신
```

### 4.3 알려진 5.x 진화 영향

| 5.x 변경 | 영향 정책 | 권장 갱신 |
|---------|----------|----------|
| **5.4 — Substrate Material** | 12_AssetOptimizationPolicy §2 (Material) | Substrate 사용 시 PSO 별도 |
| **5.4 — Mover Plugin** | MovementComponents (Components) | Mover 권장 (CharacterMovement deprecated 추세) |
| **5.5 — Compatible Skeleton 표준화** | AssetClasses/Mesh §2 (USkeleton) | 표준 패턴 강화 |
| **5.5 — Iris Replication** | 11_AssetLoadingPolicy + Network | Iris 옵션 추가 |
| **5.6 — Mass Entity 안정화** | 09_GlobalIteratorPolicy | Mass = TActorIterator 대안 |
| **5.7 — Enhanced Input UserSettings** | Input §1 | Player Mappable Key 표준 |
| **6.0 (예정) — ?** | 모든 정책 | 향후 감사 |

---

## 5. Anthropic 모델 진화 추적 (글 1 핵심)

### 5.1 모델별 정책 의존도

```
Claude Sonnet 4.5 (작성 시점):
  - 정책 의존도: HIGH
  - LLM_Wiki 의 모든 정책이 load-bearing
  - 정책 없이 Claude = UE 표준 위반 가능성

Claude Opus 4.6 (현재 추정):
  - 정책 의존도: MEDIUM
  - 일부 정책 (예: Naming, const) 자체 학습
  - 핵심 정책 (Async Load, GC 방어) 여전히 필요

Claude 5.0 (미래):
  - 정책 의존도: LOW (예측)
  - 자체 학습 능력 강화
  - 위키는 reference 로 변환 (의무 → 참고)
```

### 5.2 글 1 의 SonnetGen + OpusEval 패턴

```
LLM_Wiki 적용:
  Generator: Claude Sonnet 4.5 (작은 / 빠른)
    - 본 wiki 의 정책 따라 코드 작성
    - 토큰 비용 LOW
  
  Evaluator: Claude Opus 4.6 (큰 / 정확)
    - 15_EvaluatorRecipe 표준 적용
    - 회의적 평가
    - 토큰 비용 HIGH but 가치 있음

  결과: 작은 모델로 빠른 작성 + 큰 모델로 정확한 평가 = 비용 효율
```

### 5.3 모델 진화 시 wiki 변화

| 모델 세대 | wiki 역할 |
|----------|----------|
| **Current (Sonnet 4.5)** | 의무 정책 — Claude 가 따라야 함 |
| **Future (5.0+)** | Reference — Claude 가 참고 |
| **Future (6.0+)** | 일부 정책 deprecate — 모델 자체 학습 |

→ **wiki 가 stale 되는 자연스러운 진화**. 정기 감사로 추적.

---

## 6. 감사 결과 보고서 표준

### 6.1 분기별 보고서 형식

```markdown
# Model Evolution Audit — Q{N} {YYYY}

## §1. 감사 범위
- 정책 N개 (13 횡단 인덱스 + 카테고리별)
- UE 버전: {5.x.x}
- Claude 모델: {모델명}
- 감사자: {Claude 인스턴스 / 사용자}

## §2. 결과 요약
| 결정 | 정책 수 |
|------|--------|
| Continue | N |
| Update | N |
| Simplify | N |
| Merge | N |
| Deprecate | N |
| Remove | N |

## §3. 변경 사항 (자세히)
### 3.1 Update — Policy X (12_AssetOptimizationPolicy §2)
- 변경: Nanite 자동화 → LOD 정책 일부 무의미
- 갱신: §2 에 "Nanite 활성 시 LOD 강제 무시" 명시
- Cross-link: AssetClasses/Mesh §1.4

### 3.2 Deprecate — Policy Y
...

## §4. 향후 모니터링
- UE 5.8 (예정) 감사 트리거
- 6.0 발표 시 즉시 감사

## §5. 사용자 협의 필요
- {큰 변경 — 사용자 결정 필요}
```

### 6.2 보고서 위치

```
<외부>/_audits/{YYYY}_Q{N}_audit_report.md
```

---

## 7. 안티패턴 (8종)

| # | 안티패턴 | 정답 |
|---|---------|------|
| 1 | 정책 작성 후 방치 | 분기별 정기 감사 의무 |
| 2 | UE 릴리스 노트 안 봄 | §4.1 채널 모니터링 의무 |
| 3 | "정책 따랐는데 깨짐" 무시 | 즉시 감사 트리거 |
| 4 | 모델 진화 무시 — 모든 정책 영구 유지 | 글 1 load-bearing 검증 |
| 5 | 정책 충돌 발견 + 16_PolicyPriority 갱신 안 함 | 충돌 발견 시 즉시 §2.2 추가 |
| 6 | 감사 결과 사용자 통보 안 함 | Stage 8 — 큰 변경 시 협의 의무 |
| 7 | 한 정책만 보고 다른 정책 영향 미평가 | Cross-Reference Check (Stage 4) |
| 8 | 자기 평가 (Claude 가 자기 정책 평가) | 별도 Evaluator 인스턴스 또는 사용자 |

---

## 8. 관련 문서

- 모든 횡단 인덱스 (04~17) — 본 문서가 정기 감사 대상
- [`14_TaskHandoffTemplate.md`](./14_TaskHandoffTemplate.md) — Decision Log + 감사 결과 인계
- [`15_EvaluatorRecipe.md`](./15_EvaluatorRecipe.md) — 정책 위반 검증 (감사 결과 적용)
- [`16_PolicyPriority.md`](./16_PolicyPriority.md) — 정책 충돌 (감사 시 갱신)
- [`17_QualityCriteria.md`](./17_QualityCriteria.md) — 정책 적용 시 품질 측정

---

## 9. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. 글 1 의 "load-bearing component 검증" 적용. **2축 staleness** (UE 진화 + 모델 진화) + **8단 감사 절차** (Inventory / Source Validation / Load-Bearing Test / Cross-Reference / Real-World / Decision / Implementation / Communication) + **6종 결정** (Continue / Update / Simplify / Merge / Deprecate / Remove) + **정책 Status 매트릭스 (2026-Q2)** + UE 진화 추적 채널 + Anthropic 모델 진화 추적 + 분기별 보고서 표준 + 안티패턴 8종. |
