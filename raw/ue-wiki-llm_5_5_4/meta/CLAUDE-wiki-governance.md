---
name: claude-wiki-governance
description: 위키 자체 작성/갱신 시에만 적용되는 메타 룰 — sub-skill 생산 시 비판적 5단 검증 + 6단 체크리스트 + Anthropic Engineering 3개 글 패턴 영구 박제. 코드 작성 시는 로드 불필요.
---

# CLAUDE-wiki-governance.md — 위키 작성/갱신 메타 룰

> 본 문서는 **위키 자체 의 sub-skill / SKILL.md 작성 / 갱신 시에만 로드**. 코드 작성 시는 무시. CLAUDE.md 는 코드 작성용으로만 슬림화 유지.
>
> **트리거**: 사용자가 "새 sub-skill 작성", "기존 sub-skill 갱신", "새 카테고리 신설", "위키 정책 추가" 등을 요청 시 본 문서 의무 로드.

---

## 1. 적용 범위

- ✅ **적용** — 새 sub-skill 작성 / 기존 sub-skill 갱신 / 새 카테고리 신설 / 위키 인덱스 신설 / 정책 매트릭스 변경
- ❌ **비적용** — 일반 코드 작성 (Component / Actor / Slate 등) / 디버깅 / 리팩터링

작업 분류 결정:
- 사용자가 `[Render]`/`[Slate]`/`[Components]`/`[GameFramework]`/`[AssetClasses]`/`[Input]` 등 카테고리 명시 + UE C++ 코드 작성 요청 = **위키 사용** (CLAUDE.md 만 로드, 본 문서 X)
- 사용자가 "위키 갱신", "sub-skill 추가", "정책 추가" 등 메타 작업 요청 = **위키 갱신** (CLAUDE.md + 본 문서 둘 다 로드)

---

## 2. 5단 의무 검증 (Anthropic Engineering 3개 글 패턴)

> Anthropic 의 [`harness-design-long-running-apps`](https://www.anthropic.com/engineering/harness-design-long-running-apps), [`building-effective-agents`](https://www.anthropic.com/engineering/building-effective-agents), [`equipping-agents-for-the-real-world-with-agent-skills`](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) 3개 글에서 도출된 패턴을 **위키 작성·검증 표준으로 영구 박제**.

### 2.1 작성 전 의무 (Pre-Write Mandate)

**Step 1: 멀티 세션 인계 — [`14_TaskHandoffTemplate.md`](../references/14_TaskHandoffTemplate.md) 적용 의무**
- sub-skill 작성이 **2시간 / 1세션 이상 추정** 시 즉시 `<외부>/{...}_{sub-skill명}_초안.md` 작성
- 5섹션: Sprint Contract / Decision Log / Progress / Evaluator Findings / Next Session Brief
- 컨텍스트 60% 초과 시 강제 작성
- **Article 1 "context reset > compaction"** 패턴

**Step 2: 정책 충돌 사전 해결 — [`16_PolicyPriority.md`](../references/16_PolicyPriority.md) 적용 의무**
- sub-skill 안 새 룰 추가 시 기존 50+ 룰과 **충돌 사전 검사**
- **3단 통합 의사결정**:
  1. **(1차) Tier 분류** (Compile > GC > Runtime > Performance > Maintainability 5단)
  2. **(2차) 점수 차 기반 정량 결정** ([`§10`](../references/16_PolicyPriority.md#10--점수-기반-충돌-해결-시스템-정량-우선순위))
     - 4종 가중 (Severity 25 + Reversibility 25 + DetectionDifficulty 25 + Scope 25 = 0~100점)
     - 점수 차 ≥10 → 즉시 결정 / 5~9 → 컨텍스트 / <5 → 동급
  3. **(3차) §2.1 결정 트리** (구체성·측정성·예외)
- 새 규약 추가 시 4종 점수 평가 + Tier 매핑 + Decision Log 기록 의무

### 2.2 작성 중 의무 (In-Progress Mandate)

**Step 3: YAML Frontmatter 표준 (Anthropic Skills 호환)**

모든 SKILL.md 첫 4줄 의무 형식:
```yaml
---
name: {category}-{subskill}    # 케밥 케이스 lower-case
description: {핵심 클래스/API/패턴 + 트리거 시나리오 — Article 3 routing 용}
---
```

- `name` 은 카테고리 자동 매칭 키 (`gameframework-actor`, `components-meshcomponents`)
- `description` 은 **첫 헤딩보다 강함** — 핵심 클래스명 + 핵심 API + 트리거 키워드 모두 포함 (75자 ~ 250자)
- `description` 약 한 줄 ≤ 250자 — 더 길면 description-routing 정확도 저하

**Step 4: 측정 가능한 품질 — [`17_QualityCriteria.md`](../references/17_QualityCriteria.md) 적용 의무**
- sub-skill 안 코드 예제 / 패턴 추천 시 4종 가중 (Performance 35% + Memory 25% + Network 15% + Maintainability 25%)
- **자체 평가 점수 80점 이상**
- 95점 Good / 32점 Bad few-shot 비교
- 플랫폼별 임계 (PC High 8ms / Mid 12ms / Low 16ms / Console 16ms / Mobile 33ms / VR 11ms) 명시

### 2.3 작성 후 의무 (Post-Write Mandate)

**Step 5: Generator/Evaluator 분리 — [`15_EvaluatorRecipe.md`](../references/15_EvaluatorRecipe.md) 적용 의무**
- sub-skill 작성 완료 후 **다른 Claude 인스턴스 / 사용자가 평가자 역할**
- 8단계 회의적 평가:
  1. Policy 위반
  2. Compile
  3. Runtime
  4. Performance 4기준
  5. Edge cases
  6. Replicated integrity
  7. GC leak
  8. External verification
- Cooked Build 검증 명령 (`Build.bat` / `stat unit` / `stat slate` / `stat anim`) + 100점 채점
- **자기 자신이 평가하면 self-evaluation bias** — Article 1 핵심 발견
- 평가 결과를 sub-skill 본문 §끝 "검증 로그" 섹션에 첨부

**Step 6: Staleness 주기 감사 — [`18_ModelEvolutionAudit.md`](../references/18_ModelEvolutionAudit.md) 적용 의무**
- 작성된 sub-skill 은 **분기별 (3개월) staleness 감사 대상**
- 2축 (UE 진화 + Anthropic 모델 진화)
- 8단계 감사 프로세스 (Inventory / Source Validation grep / Load-Bearing Test / Cross-Reference / Real-World 사용 / Decision / Implementation / Communication)
- 6종 결정 (Continue / Update / Simplify / Merge / Deprecate / Remove)
- **UE 마이너 버전 업그레이드 시 + Anthropic 모델 메이저 변경 시 트리거**

---

## 3. sub-skill 의무 검증 6단 체크리스트 (작성 직전 + 직후 둘 다 의무)

### 3.1 작성 직전

- [ ] **1️⃣ 멀티 세션 인계 사전 작성** — 작업 추정 2시간 / 1세션 이상이면 [`14_TaskHandoffTemplate.md`](../references/14_TaskHandoffTemplate.md) 의 5섹션 인계 파일 `<외부>/` 에 사전 작성
- [ ] **2️⃣ 정책 충돌 사전 검사** — 새 룰 추가 시 [`16_PolicyPriority.md`](../references/16_PolicyPriority.md) **3단 통합 의사결정** 적용:
  - (1차) 5단 Tier 분류
  - (2차) **§10 점수 시스템 4종 가중 평가 (0~100점) + 점수 차 ≥10 즉시 결정 / 5~9 컨텍스트 / <5 동급**
  - (3차) §2.1 결정 트리
  - **점수 매트릭스 §10.3 에 새 규약 등록**

### 3.2 작성 중

- [ ] **3️⃣ YAML frontmatter** — `name` (케밥 lower-case) + `description` (75~250자 / 핵심 클래스 + API + 트리거) 첫 4줄 의무
- [ ] **4️⃣ 품질 자체 평가** — [`17_QualityCriteria.md`](../references/17_QualityCriteria.md) 4종 가중 자체 평가 80점 이상 + 플랫폼 임계 매트릭스 명시

### 3.3 작성 직후

- [ ] **5️⃣ Evaluator 평가** — [`15_EvaluatorRecipe.md`](../references/15_EvaluatorRecipe.md) 8단계 평가 — **다른 Claude 인스턴스 / 사용자**가 회의적 평가 + Cooked Build 검증 명령 + 100점 채점 → 본문 §끝 "검증 로그" 첨부
- [ ] **6️⃣ 분기 감사 등록** — [`18_ModelEvolutionAudit.md`](../references/18_ModelEvolutionAudit.md) 다음 분기 감사 일정 메타에 등록

---

## 4. 카테고리 메인 SKILL.md 작성 시 추가 의무

- [ ] **§1 이 카테고리 한 줄** — `description` frontmatter 와 일치 + 카테고리 sub-skill 개수 명시
- [ ] **§2 sub-skill 인덱스 표** — 모든 sub-skill 의 한 줄 요약 + 의존성 화살표
- [ ] **§3 공통 의무 정책 블록** — 카테고리 전체 적용 정책 (예: Components 6대 / GameFramework 어셋 로드 / Input 12종 규약) 본문 시작부 의무 삽입
- [ ] **§4 결정 트리** — sub-skill 간 선택 결정 트리 (예: Pawn vs Character / Static vs Skeletal / Hard vs Soft Reference)
- [ ] **§끝 변경 이력** — 분기별 갱신 + 사용자 피드백 + Evaluator 검증 결과

---

## 4-A. 정책 주석 — 느슨한 컨벤션 ⭐ (2026-05-08 — P0-7 토큰 절감)

> **이전**: 모든 멤버 / 모든 안전 가드에 정책 ID 주석 의무 (`// 10_§3 GC 방어`)
> **현재**: 느슨한 인용 — 파일 헤더 1회 + 비명백 / Critical 회피 시만 인라인

### 4-A.1 적용 규칙

| 위치 | 정책 인용 | 사유 |
|------|---------|------|
| **파일 헤더** (1회) | ✅ 의무 | `// Applies: 10_§1+§3+§5, 11_§3+§5+§6, 07` 한 줄 |
| **매크로 사용 줄** | ❌ 생략 | 매크로 이름 자체가 정책 명시 (`UE_DECLARE_STREAMABLE_HANDLE` = 11_§3+§6) |
| **자명한 정책** (UPROPERTY 등) | ❌ 생략 | 이미 표준 — 반복 X |
| **비명백한 결정** (Soft vs Hard, RootMotion 등) | ✅ 인라인 OK | "왜 이 선택?" 답하는 한 줄 |
| **Critical 회피** (Cooked Build 함정) | ✅ 인라인 의무 | 미래 디버그 시 단서 |

### 4-A.2 예시

```cpp
// ✅ 좋음 — 파일 헤더 + 비명백 결정 / Critical 회피만 인라인
// MyComponent.cpp
// Applies: 10_§1+§3+§5, 11_§3+§5+§6, 07

#include "MyComponent.h"
#include "UEWikiMacros.h"

UMyComponent::UMyComponent()
{
    UE_COMPONENT_DEFAULTS();   // (정책 자명 — 매크로명에서)
}

void UMyComponent::LoadAsset()
{
    UE_PROFILE();
    UE_WEAK_THIS(W);

    // 비명백한 선택: 자주 안 쓰는 자산이라 PreLoad 부담 회피
    LoadHandle = UAssetManager::GetStreamableManager().RequestAsyncLoad(...);
}
```

```cpp
// ❌ 나쁨 — 자명한 정책 반복 (토큰 낭비)
UPROPERTY()  // 10_§3 GC 방어
TObjectPtr<UStaticMesh> Mesh;  // 10_§3 GC 방어 + UPROPERTY 의무
```

### 4-A.3 효과 (예상)

- 정책 주석 영역: **~600 → ~100 토큰** (-83%)
- measurements/2026-05-08 기준: 4,400 → ~3,900 토큰 (-11%)
- 매크로 라이브러리 (P0-7) 와 결합 시: 4,400 → ~2,900 (-34%)

---

## 5. 위반 시 처리

| 위반 | 처리 |
|------|------|
| **frontmatter 누락** | 자