---
title: "UE CppComment Backslash LineContinuation Hazard — Windows path 주석 함정"
kind: concept
status: stable
severity: "★"
tags: [ue, cpp, preprocessor, comment, windows-path, c4010, hazard, ue-574]
related_concepts: []
related_synthesis: []
created: 2026-05-26
last_updated: 2026-05-26
---

# UE CppComment Backslash LineContinuation Hazard

> **유래**: MCDataTableAuto Phase 3c-2-ext 빌드 발견 (2026-05-26). McwikiResolver.cpp 의 `//` 주석 끝 Windows path 의 `\` 가 line continuation 으로 해석.

## 정의

C/C++ preprocessor 규칙에 따라 `//` 단일 행 주석 *끝* 의 backslash (`\`) 는 **line continuation 문자** 로 해석되어 *다음 줄* 까지 주석으로 합쳐짐. Windows path 를 *예시 텍스트* 로 주석에 적을 때 path 가 `\` 로 끝나면 무조건 발생.

증상:
- `error C4010: 한 줄로 된 주석에 줄 연속 문자가 있습니다`
- 다음 줄 코드가 *주석에 흡수* 되어 `C2065` / `C2059` cascade

## 자세히

### 사례 — MCDataTableAutoMcwikiResolver.cpp (Phase 3c-2-ext, 2026-05-26)

🟢 **VAULT** — KMCProject 실측.

**위반 코드**:
```cpp
// 3) fallback: %USERPROFILE%\.claude\plugins\ue-wiki-llm\
const FString Fallback = FPaths::Combine(
    FPlatformProcess::UserHomeDir(),
    TEXT(".claude/plugins/ue-wiki-llm"));
```

**preprocessor 처리 결과** (line splicing 적용):
```cpp
// 3) fallback: %USERPROFILE%\.claude\plugins\ue-wiki-llm\	const FString Fallback = FPaths::Combine(
// 위 한 줄 전체가 주석 (line continuation \ 효과)
    FPlatformProcess::UserHomeDir(),         // 의미 없는 코드
    TEXT(".claude/plugins/ue-wiki-llm"));    // 의미 없는 )) — C2059
// 아래 코드의 'Fallback' 변수 미선언 — C2065 cascade
```

**에러 출력**:
```
C4010: 한 줄로 된 주석에 줄 연속 문자가 있습니다.
   const FString Fallback = FPaths::Combine(
^
C2059: 구문 오류: ')'
   TEXT(".claude/plugins/ue-wiki-llm"));
C2065: 'Fallback': 선언되지 않은 식별자입니다.
   FResult R = TryPath(Fallback);
```

## 회피 — 4 패턴

### 1. Forward-slash 사용 (⭐ 추천)

```cpp
// 3) fallback: %USERPROFILE%/.claude/plugins/ue-wiki-llm
```

Windows API 도 forward-slash 허용 — *path 의미 그대로* 유지. 가장 안전.

### 2. 끝 `\` 제거

```cpp
// 3) fallback: %USERPROFILE%\.claude\plugins\ue-wiki-llm
```

Path 형태 손실 (trailing `\` 가 directory 표시) 하지만 안전.

### 3. `/* */` 다중 행 주석

```cpp
/* 3) fallback: %USERPROFILE%\.claude\plugins\ue-wiki-llm\ */
```

`/* */` 안에서는 `\` 가 line continuation 효과 없음.

### 4. 끝 `\` 다음 공백 (⚠ 취약)

```cpp
// 3) fallback: %USERPROFILE%\.claude\plugins\ue-wiki-llm\ 
//                                                        ↑ trailing space
```

작동하지만 *editor 의 trailing whitespace 자동 trim* (clang-format / VSCode 등) 으로 깨질 수 있음. 추천 안 함.

## 다른 사례 — *백슬래시 끝 주석*

Windows path 외에도 같은 함정 가능:

```cpp
// LaTeX 수식 안 \ \ (줄바꿈)\
int x = 1;   // 흡수됨!

// 정규식 \\
int y = 2;   // 흡수됨!

// 백슬래시 끝 텍스트 \
do_something();   // 흡수됨!
```

→ *모든* `//` 주석 끝 `\` 가 위험.

## 자동 검출

### grep
```
Grep "^\s*//.*\\$" Source/
```

`//` 로 시작 + `\` 로 끝나는 모든 라인.

### 컴파일러 경고
MSVC `/W3` 이상에서 C4010 경고. UE 의 `bUseStandardCppLib=true` (default) 에서 활성. CI 의 *warning-as-error* 셋업 권장.

### clang-format / editor
일부 formatter 가 자동 fix 안 함 — *경고만*. Manual 검토 의무.

## 회피 정책 (KMCProject)

신규 코드 작성 시:
1. Windows path 주석 *항상* forward-slash
2. PR review 에 `grep "^\s*//.*\\$"` 자동 점검 추가
3. C4010 경고 격상 → warning-as-error (CI)

## 관련

- [[concepts/UE-Phantom-Header-Hallucination-Hazard]] (다른 *Windows-specific* 함정 — phantom header)
- [[concepts/LOCTEXT-Namespace-Macro-Position-Hazard]] (preprocessor 관련 함정 family)

## 열린 질문

1. ❓ clang-format 의 *trailing backslash* 자동 변환 옵션 존재 가능성 — 검증 미수행.
2. ❓ 다른 preprocessor 변종 (Rust `//` / Python `#`) 도 같은 함정 — Rust 는 *없음* (line splicing 없음), Python 은 *없음*. C/C++ 특유.

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| `//` 끝 `\` 가 line continuation | 🟢 VAULT | C/C++ standard preprocessor 규칙 |
| MCDataTableAutoMcwikiResolver.cpp 실측 에러 | 🟢 VAULT | KMCProject Phase 3c-2-ext 빌드 실측 |
| MSVC C4010 / C2059 / C2065 cascade | 🟢 VAULT | 사용자 빌드 출력 스크린샷 |
| Forward-slash 가 Windows API 에서 허용 | 🟢 VAULT | Win32 API 표준 |
| clang-format 자동 변환 옵션 | 🔴 INFERRED | 미검증 |

## 변경 이력

- 2026-05-26: 초안 작성. MCDataTableAuto Phase 3c-2-ext 빌드 cycle 발견 — McwikiResolver.cpp 주석 끝 backslash. 4 회피 패턴 정리.
