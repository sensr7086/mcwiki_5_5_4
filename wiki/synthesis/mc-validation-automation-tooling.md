---
type: synthesis
title: "MC Validation Policy 자동화 도구 — Python silent-return 변환 script + Multi-category 로그 + ue-wiki-llm:evaluate 통합"
slug: mc-validation-automation-tooling
created: 2026-05-10
last_updated: 2026-05-10
sources:
  - "[[sources/mc-asset-validation-policy]]"
  - "[[sources/ue-ref-15-evaluatorrecipe]]"
  - "[[sources/mc-soft-skeletalmesh-ragdoll]]"
entities:
  - "[[entities/UClass]]"
concepts:
  - "[[concepts/MC-Asset-Validation-Policy]]"
  - "[[concepts/Component-Policies-6]]"
status: living
tags: [synthesis, validation, automation, python, lint, evaluator]
---

# MC Validation Policy 자동화 도구

## 1. Thesis

[[synthesis/mc-validation-policy-rollout]] §9 — 다른 MC 컴포넌트 일괄 적용을 *수동* 으로 하면 일관성 깨짐 + 시간 소요. 자동화 3 도구 — **(1) Python script — silent return 사이트 자동 식별 + `MC_LOGRET_*` 변환 후보 제안 / (2) Multi-category 로그 — `LogMCAsset` 외에 도메인별 (`LogMCStory`, `LogMCParts`) 분리 정책 + 단일 매크로 / (3) `ue-wiki-llm:evaluate` plugin 통합 — 정책 준수도 100점 채점 자동화**. 본 synthesis 는 각 도구의 설계 + 구현 골격 + CI 통합.

## 2. (1) Python silent-return 변환 script

### 2.1 식별 패턴

```python
# tools/mc_lint_silent_return.py
import re
from pathlib import Path

# 패턴: 단일 if + return; (block 안 다른 코드 없음)
SILENT_RETURN_PATTERN = re.compile(
    r'(\t+)if\s*\(\s*(![^)]+|[^!]+\s*==\s*nullptr|[^!]+\.IsNull\(\)|[^!]+\.IsValid\(\)\s*==\s*false)\s*\)\s*(\{[^}]*return[^;]*;\s*\}|return[^;]*;)',
    re.MULTILINE
)

def scan_file(path: Path) -> list[dict]:
    """Returns silent-return sites + suggested macro."""
    sites = []
    text = path.read_text(encoding='utf-8')
    for m in SILENT_RETURN_PATTERN.finditer(text):
        condition = m.group(2)
        line_no = text[:m.start()].count('\n') + 1
        # 매크로 후보 결정
        if 'IsNull()' in condition:
            suggested = 'MC_LOGRET_IF_SOFT_NULL'
        elif 'IsValid()' in condition:
            suggested = 'MC_LOGRET_IF_INVALID_WEAK'
        elif 'nullptr' in condition or condition.startswith('!'):
            suggested = 'MC_LOGRET_IF_NULL'
        else:
            suggested = 'MC_LOGRET_IF_FALSE'
        sites.append({
            'file': str(path),
            'line': line_no,
            'condition': condition,
            'suggested': suggested,
        })
    return sites

def scan_directory(root: Path):
    all_sites = []
    for cpp in root.rglob('*.cpp'):
        all_sites.extend(scan_file(cpp))
    for h in root.rglob('*.h'):
        all_sites.extend(scan_file(h))
    return all_sites
```

### 2.2 출력 — Markdown 보고서

```markdown
# MC Validation Lint — 2026-05-10

## Sites: 47

| File | Line | Condition | Suggested |
| -- | -- | -- | -- |
| MCBouyancyComponent.cpp | 42 | `!Volume` | `MC_LOGRET_IF_NULL` |
| MCMoveComponent.cpp | 87 | `!CharacterMovement` | `MC_LOGRET_IF_NULL` |
| ... | | | |

## Auto-fix candidates: 38 / 47
(나머지 9 — 복잡한 조건, 수동 검토 필요)
```

### 2.3 Auto-fix 모드 (선택)

```python
def auto_fix(path: Path, sites: list[dict], reason_lookup: dict[tuple, str]):
    """Replace silent return with macro. reason_lookup[(file, line)] = "Reason string"."""
    text = path.read_text(encoding='utf-8')
    # 역순 — 라인 번호 변경 회피
    for site in reversed(sites):
        reason = reason_lookup.get((site['file'], site['line']),
                                    f"silent return at line {site['line']} — review reason")
        replacement = f"{site['suggested']}({extract_var(site['condition'])}, \"{reason}\");"
        # 정규식 매칭 부분 교체
        # ... (구현 세부)
    path.write_text(text, encoding='utf-8')
```

**Reason 자동 생성은 LLM** — script 가 식별만, Reason 문자열은 사람 / LLM 이 채움.

## 3. (2) Multi-category 로그 정책

```cpp
// MCAssetValidation.h 확장
DECLARE_LOG_CATEGORY_EXTERN(LogMCAsset,    Log, All);  // 자산 / 컴포넌트 (이미 있음)
DECLARE_LOG_CATEGORY_EXTERN(LogMCStory,    Log, All);  // MCStory subsystem / asset
DECLARE_LOG_CATEGORY_EXTERN(LogMCParts,    Log, All);  // MCParts loader / nodes
DECLARE_LOG_CATEGORY_EXTERN(LogMCNetwork,  Log, All);  // Replication / RPC
DECLARE_LOG_CATEGORY_EXTERN(LogMCInput,    Log, All);  // Enhanced Input

// 카테고리 별 매크로
#define MC_LOGRET_IF_NULL_CAT(Category, Ptr, Reason) \
    do { \
        if ((Ptr) == nullptr) { \
            UE_LOG(Category, Warning, ...); \
            return; \
        } \
    } while (0)

#define MC_LOGRET_IF_NULL(Ptr, Reason) MC_LOGRET_IF_NULL_CAT(LogMCAsset, Ptr, Reason)
```

**카테고리 결정 트리**:
- 자산 / 컴포넌트 → `LogMCAsset` (디폴트)
- MCStory / MCParts 그래프 노드 / 자산 → `LogMCStory` / `LogMCParts`
- Replication / Multicast / RPC → `LogMCNetwork`
- Input Mapping / Action → `LogMCInput`

QA 가 *문제 영역만 필터* 가능 — `Log LogMCNetwork Verbose` 콘솔.

## 4. (3) `ue-wiki-llm:evaluate` plugin 통합

[[sources/ue-ref-15-evaluatorrecipe]] §8 단계 — 정책 100점 채점:

```cpp
// 코드 작성 후 — Claude Code 안 /evaluate 명령
// /evaluate Source/KMCProject/MCPlayModule/Actor/Component/MCSoftSkeletalMeshComponent.h

// 출력 (recipe 8 단계):
// 1. Policy compliance: 92/100
//    - [[concepts/Component-Policies-6]] §1~6: 5/6 (CDO 검사 누락)
//    - [[concepts/Asset-Loading-Policy]] §2 단계 5: 100% (LoadHandle Pin/Cancel)
//    - [[concepts/Profiling-Scope-Rule]]: 100% (모든 콜백)
//    - [[concepts/MC-Asset-Validation-Policy]]: 95/100 (3 silent return 잔존)
// 2. Compile: PASS
// 3. Runtime: PASS (단위 테스트 PASS)
// 4. Performance: 88/100 (Tick 안 LOG 매크로 — Verbose 분기 추가 권장)
// ...
```

CI 통합:
```yaml
# .github/workflows/ci.yml
- name: MC Lint
  run: python tools/mc_lint_silent_return.py Source/ > lint-report.md
- name: MC Evaluate
  run: claude-code-cli /evaluate Source/KMCProject/MCPlayModule/ > eval-report.md
- name: Threshold check
  run: |
    SCORE=$(grep "Policy compliance" eval-report.md | grep -oP '\d+(?=/100)')
    if [ "$SCORE" -lt 80 ]; then exit 1; fi
```

## 5. 통합 워크플로우

```
[개발자가 새 컴포넌트 작성]
    ↓
[python tools/mc_lint_silent_return.py NewFile.cpp]
    ↓ (silent return 사이트 N 식별)
[개발자가 Reason 문자열 채움 + Auto-fix 실행 또는 수동 변환]
    ↓
[빌드 + Editor 실행 — LOG 발화 검증]
    ↓
[claude-code /evaluate NewFile.cpp]
    ↓ (점수 90+ 면 통과)
[PR 제출]
    ↓
[CI — lint + evaluate + threshold check]
    ↓
[Merge]
```

## 6. 함정 / 열린 질문

- [ ] **정규식의 한계** — `if (Cond) { /* 다른 코드 */ return; }` 같은 *block 안 추가 코드* 케이스는 silent return 아님. 정규식이 못 잡거나 잘못 잡음. 추가 검증 의무
- [ ] **Auto-fix 의 위험** — 잘못된 변환은 컴파일 에러. CI 가 컴파일 단계 의무 — Auto-fix → 빌드 → 통과 확인
- [ ] **Reason 문자열의 일관성** — 사람 / LLM 마다 표현 다름. *카테고리별 권장 Reason 카탈로그* 작성 (열린)
- [ ] **`/evaluate` plugin 의 false negative** — LLM 채점은 *경향*. 100% 정확 아님. CI threshold 80 권장
- [ ] **Multi-category 로그의 구분 비용** — 5 카테고리 × 매크로 변형 = 매크로 폭발. `MC_LOGRET_*_CAT` 가 베이스, 단순 매크로는 `LogMCAsset` 디폴트 wrapper
- [ ] **Static analysis tool (clang-tidy) 통합** — 정규식 대신 AST 기반 분석. 더 정확하지만 셋업 비용 큼 (열린)
- [ ] **IDE plugin (VSCode / Rider)** — 실시간 silent return highlight + Quick fix. UE 5.x 의 Live Coding 환경에서 검증 (열린)
- [ ] **Eval recipe 의 8 단계 자동화 한계** — 단위 테스트 / Cooked Build 검증은 자동화 어려움 — 사용자 manual (열린)

## 7. 관련

### Sources

[[sources/mc-asset-validation-policy]] · [[sources/ue-ref-15-evaluatorrecipe]] · [[sources/mc-soft-skeletalmesh-ragdoll]]

### Entities

[[entities/UClass]]

### Concepts

[[concepts/MC-Asset-Validation-Policy]] · [[concepts/Component-Policies-6]]

### Related synthesis

[[synthesis/mc-validation-policy-rollout]] (수동 적용 절차 → 자동화) · [[synthesis/mc-soft-asset-component-pattern]] (적용 대상) · [[synthesis/subsystem-graph-online-wrapper]] (그래프 시각화 도구화 결합)

### Cycle 5o reverse-link 보강 (high confidence missing)

- [[synthesis/lint-2026-05-10-mcsoft-components]] (inbound=4, suggest_missing_cross_link high confidence)
