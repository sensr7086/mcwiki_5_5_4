---
type: synthesis
title: "MC Validation 정적 분석 도구 — clang-tidy AST + VSCode/Rider IDE plugin + Reason 카탈로그"
slug: validation-static-analysis-ide-integration
created: 2026-05-11
last_updated: 2026-05-11
sources:
  - "[[sources/mc-asset-validation-policy]]"
  - "[[sources/ue-ref-15-evaluatorrecipe]]"
  - "[[sources/mc-soft-skeletalmesh-ragdoll]]"
entities:
  - "[[entities/UClass]]"
  - "[[entities/FProperty]]"
concepts:
  - "[[concepts/MC-Asset-Validation-Policy]]"
  - "[[concepts/Component-Policies-6]]"
status: living
tags: [synthesis, validation, clang-tidy, ast, vscode, rider, ide-plugin]
---

# MC Validation 정적 분석 도구

## 1. Thesis

[[synthesis/mc-validation-automation-tooling]] 의 4 미해결 — **(1) Python 정규식의 한계 (block 안 추가 코드 미감지) → clang-tidy AST 기반 / (2) IDE plugin (VSCode/Rider) — 실시간 silent return highlight + Quick Fix / (3) Reason 카탈로그 — 카테고리별 표준 메시지 / (4) /evaluate plugin 의 false negative — LLM 채점 보정**. 본 synthesis 는 4 축의 *Python → clang-tidy → IDE plugin → LLM* 도구 사슬 + 통합 워크플로우.

## 2. (1) clang-tidy AST Custom Check

Python 정규식은 *if (...) return;* 패턴만 — block 안 다른 코드 못 잡음. clang-tidy AST 기반 check 가 정확:

```cpp
// clang-tidy plugin — MCSilentReturnCheck.cpp
class MCSilentReturnCheck : public clang::tidy::ClangTidyCheck
{
public:
    void registerMatchers(MatchFinder *Finder) override
    {
        // AST 매처 — if (cond) { return; } 또는 if (cond) return;
        // 단, body 가 *return 만* 인 경우만 (다른 코드 없음 = silent)
        Finder->addMatcher(
            ifStmt(
                hasCondition(expr().bind("cond")),
                hasThen(
                    anyOf(
                        returnStmt().bind("ret"),
                        compoundStmt(
                            statementCountIs(1),
                            has(returnStmt())
                        ).bind("ret_block")
                    )
                )
            ).bind("silent_if"),
            this);
    }

    void check(const MatchFinder::MatchResult &Result) override
    {
        const auto *Cond = Result.Nodes.getNodeAs<Expr>("cond");
        // Cond 가 nullptr 비교 / IsNull / IsValid() == false 형식인지 검사
        if (IsValidationCondition(Cond)) {
            diag(Cond->getBeginLoc(), "silent return detected — use MC_LOGRET_* macro");
            // Quick Fix: 자동 변환 제안
            applyFix(Result, "MC_LOGRET_IF_NULL(...)");
        }
    }
};
```

**빌드 통합** — Build.cs 에 clang-tidy step 추가:

```csharp
// MCPlayModule.Build.cs
public MCPlayModule(ReadOnlyTargetRules Target) : base(Target)
{
    // ... 기존 deps
    if (Target.Configuration == UnrealTargetConfiguration.Development) {
        AdditionalCompilerArguments = "--clang-tidy=mc-silent-return";
    }
}
```

## 3. (2) VSCode / Rider IDE Plugin

실시간 highlight + Quick Fix:

```
VSCode → settings.json:
{
  "C_Cpp.codeAnalysis.clangTidy.enabled": true,
  "C_Cpp.codeAnalysis.clangTidy.checks.enabled": [
    "mc-silent-return",
    "mc-uncached-getowner",
    "mc-construction-unsafe"
  ]
}
```

**Quick Fix UI**:
- silent return 발견 → 빨간 줄
- 마우스 오버 → "MC Validation: silent return at line N — replace with MC_LOGRET_IF_NULL"
- Quick Fix 메뉴 → "Apply MC_LOGRET_IF_NULL" → 자동 변환 + Reason 자리 표시자 (`"Reason: ${1:reason}"`)

**Rider plugin** (JetBrains) — `.editorconfig` 에 룰 등록 + Live Template 으로 `MC_LOGRET_IF_NULL` 단축 입력.

## 4. (3) Reason 카탈로그

카테고리별 표준 Reason 문자열 (LLM / 사람 일관성):

```
// MC_REASON_CATALOG.md (vault 추가)

### Null 자산 / Soft
- "SoftAsset.IsNull() — 자산 미지정 (디테일 패널 안 채움)"
- "Soft.Get() == nullptr — 비동기 로드 미완 또는 Cooked 누락"

### GC / WeakObjectPtr
- "Owner GC during async load (World tear-down)"
- "CachedOwner GC (Pawn destroyed)"
- "this GC during async callback"

### 본 / 컴포넌트
- "BoneName.IsNone() — 디테일 패널 본 미설정"
- "Component not bound — SetSkeletalMeshComponent missing"

### Constructor / Policy 위반 (ensure)
- "Constructor / PostInit 단계 호출 — UnsafeDuringActorConstruction (BeginPlay 이후 의무)"
- "Skeleton 미호환 swap — Compatible Skeleton 등록 또는 같은 Skeleton 만"

### 임펄스 / 0 검사
- "Impulse.IsNearlyZero() — skipped (caller intent check)"
- "Strength <= 0 — invalid argument"
```

clang-tidy / IDE 가 Quick Fix 시 — 사용자가 *카테고리 선택* → 표준 Reason 자동 삽입.

## 5. (4) LLM Evaluator 보정 — false negative 감소

[[sources/ue-ref-15-evaluatorrecipe]] §8 단계 + 다음 보정:

```
LLM Eval false negative 종류:
1. 정책 위반 누락 — LLM 이 "OK" 판정 했지만 실제 위반
   → 보정: clang-tidy + script 의 sites 카운트를 LLM 에 동시 입력
   → LLM 이 정량 + 정성 비교 → discrepancy 시 사용자 review
2. 잘못된 위반 감지 — LLM 이 OK 코드를 violation 판정
   → 보정: vault 의 vault [[concepts/MC-Asset-Validation-Policy]] 의 *예외* 명시
   → 예: Critical 영역 (Render thread / Physics tick) 의 LOG 비용 — 본 정책 비-적용
3. 등급 부정확 — Critical 을 Medium 으로 / vice versa
   → 보정: 등급 기준 표 ([[synthesis/lint-2026-05-10-mcsoft-components]] §2) 를 prompt 의무 첨부
```

**CI 통합**:

```yaml
# .github/workflows/validation.yml
- name: MC Lint (Python regex — 빠름)
  run: python tools/mc_lint_silent_return.py Source/ > python-report.json
- name: MC Static Analysis (clang-tidy)
  run: clang-tidy -p build/ Source/**/*.cpp --checks=mc-* > tidy-report.json
- name: MC LLM Evaluate (조합)
  run: |
    claude-code-cli /evaluate \
      --static-report tidy-report.json \
      --python-report python-report.json \
      Source/KMCProject/MCPlayModule/ > eval-report.md
- name: Threshold check
  run: |
    SCORE=$(grep "Policy compliance" eval-report.md | grep -oP '\d+(?=/100)')
    if [ "$SCORE" -lt 85 ]; then exit 1; fi
```

## 6. 도구 사슬 — Coverage 비교

| 도구 | 정밀도 | 속도 | Quick Fix |
| -- | -- | -- | -- |
| Python regex | 낮음 (block 안 코드 못 잡음) | 매우 빠름 | 자동 (위험) |
| clang-tidy AST | 높음 (AST 정확) | 중간 (compile DB 의존) | 자동 (안전) |
| VSCode/Rider plugin | 높음 (clang-tidy 위) | 실시간 | 사용자 승인 |
| LLM Evaluator (/evaluate) | 정성 — 의도 해석 | 느림 (분 단위) | 제안만 |

Production CI = clang-tidy + LLM Evaluator 조합 / 개발 = VSCode plugin + Python script.

## 7. 함정 / 열린 질문

- [ ] **clang-tidy + UE5 의 compile DB** — UE 의 UBT 가 표준 compile_commands.json 안 생성. `UnrealBuildTool.exe -Mode=GenerateCompileDB` 필요
- [ ] **clang-tidy 가 UPROPERTY / UFUNCTION 매크로 오해** — UHT 가 펼친 후 검사라 일반 매크로처럼 보임. 사용자 정의 check 가 `UFUNCTION` 안 함수 식별 어려움
- [ ] **IDE plugin 의 *대규모 codebase* 성능** — 전체 Source/ 검사 → IDE freeze. 변경 파일만 incremental check
- [ ] **Reason 카탈로그의 *진화 관리*** — 카테고리 추가 / 표현 변경 시 vault 갱신 + clang-tidy plugin 재컴파일. 별도 .yaml 카탈로그 파일로 분리
- [ ] **LLM Evaluator 의 *비용*** — Claude API 호출 × 사이트 수 — 큰 PR 시 비용 폭발. 변경 파일만 평가 + 결과 cache
- [ ] **CI threshold 의 *false positive* 처리** — 정당한 silent return (의도된 idempotent) 도 violation 판정 → block CI. exempt list (코드 주석 `// NOLINT(mc-silent-return)`) 지원
- [ ] **Cross-platform clang-tidy** — Windows / Linux / Mac 동일 동작 — UBT 가 platform-specific compile flag 처리. CI matrix 검증 필요 (열린)
- [ ] **VSCode plugin 의 Quick Fix 안 정 Reason 입력** — 사용자가 Reason 자리에 빈 문자열 → silent fix. Empty Reason 검출 — 또 다른 check (열린)

## 8. 관련

### Sources

[[sources/mc-asset-validation-policy]] · [[sources/ue-ref-15-evaluatorrecipe]] · [[sources/mc-soft-skeletalmesh-ragdoll]]

### Entities

[[entities/UClass]] · [[entities/FProperty]]

### Concepts

[[concepts/MC-Asset-Validation-Policy]] · [[concepts/Component-Policies-6]]

### Related synthesis

[[synthesis/mc-validation-automation-tooling]] (베이스 — Python script + Multi-category log) · [[synthesis/mc-validation-policy-rollout]] (적용 매트릭스) · [[synthesis/lint-2026-05-10-mcsoft-components]] (audit 사례)
