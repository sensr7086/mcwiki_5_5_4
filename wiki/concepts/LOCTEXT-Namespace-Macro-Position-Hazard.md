---
title: "LOCTEXT_NAMESPACE 매크로 위치 의존성 — file-local define 의 함정 (C2065)"
kind: concept
status: stable
severity: "★"
tags: [localization, loctext, macro, build-error, C2065, MMA-41, ue-574]
created: 2026-05-22
last_updated: 2026-05-22
---

# `LOCTEXT_NAMESPACE` 매크로 위치 의존성 — file-local define 의 함정 (C2065)

## 정의

UE 의 `LOCTEXT("Key", "Default")` 매크로는 preprocessor expansion 시 *현재 file 의 `#define LOCTEXT_NAMESPACE`* 를 참조한다. `LOCTEXT_NAMESPACE` 가 *LOCTEXT 호출 시점에 미정의* 상태면 → expansion 결과가 `LLOCTEXT_NAMESPACE` 같은 잘못된 token 이 되어 **C2065 (undeclared identifier)** 발생.

`#define LOCTEXT_NAMESPACE` 의 *물리적 위치* 가 source file 안에서 **LOCTEXT 호출 코드의 앞** 에 있어야 한다.

## 자세히

### 사례: MCMaterialAuto v0.20 빌드 (MMA-41)

🟢 **VAULT** — MMA-41 hazard 로그:

**file layout (실패)**:
```cpp
// MCEditorModule.cpp — 상단 includes

static void MCMaterialAuto_OnMaterialEditorOpened(...)
{
    // ⚠ 이 시점에 LOCTEXT_NAMESPACE 가 *미정의*
    LOCTEXT("Key", "Default");   // ❌ C2065
}

#define LOCTEXT_NAMESPACE "FMCEditorModule"   // ← LOCTEXT 호출 *뒤* 위치

void FMCEditorModule::StartupModule() { ... }
```

**에러 메시지** (MSVC, MCEditorModule.cpp:94):
```
error C2065: 'LLOCTEXT_NAMESPACE': 선언되지 않은 식별자입니다.
    LOCTEXT("MCMaterialAuto_ToolBar_Label", "MC Material Auto"),
```

### 원인 — LOCTEXT 매크로의 정의

UE 의 `LOCTEXT` 매크로 (`Internationalization/Text.h` 또는 유사 위치):
```cpp
#define LOCTEXT(InKey, InTextLiteral) \
    FInternationalization::ForUseOnlyByLocMacroAndGraphNodeTextLiterals_CreateText(InTextLiteral, TEXT(LOCTEXT_NAMESPACE), InKey)
```
- preprocessor expansion 시 `LOCTEXT_NAMESPACE` 토큰을 그대로 inject
- `LOCTEXT_NAMESPACE` 가 미정의면 → 식별자 그대로 남음 → compile 시 C2065

### Fix 3 패턴

#### Fix 1: `#define LOCTEXT_NAMESPACE` 를 file 상단 (LOCTEXT 호출 *앞*) 이동

```cpp
// includes
#define LOCTEXT_NAMESPACE "FMCEditorModule"

static void OnEditorOpened(...)
{
    LOCTEXT("Key", "Default");   // ✅ 이제 namespace 정의됨
}

void FMCEditorModule::StartupModule() { ... }

#undef LOCTEXT_NAMESPACE
```
- ⚠ file 의 모든 LOCTEXT 호출이 *같은 namespace* 사용 — 일반적으로 OK
- ⚠ `#undef` 가 file 끝에 와야 PCH unity build 안 다른 file 영향 회피

#### Fix 2: `NSLOCTEXT` 매크로 사용 — namespace 명시

```cpp
static void OnEditorOpened(...)
{
    NSLOCTEXT("FMCEditorModule", "Key", "Default");   // ✅ 위치 무관
}
```
- ✅ macro position 의존 *완전 제거*
- ✅ 함수마다 다른 namespace 가능 (드물지만 유용)
- ⚠ key 마다 namespace 반복 — file 의 LOCTEXT_NAMESPACE 와 *일치 보장* caller 책임

**MCMaterialAuto v0.20 채택**:
```cpp
NSLOCTEXT("FMCEditorModule", "MCMaterialAuto_ToolBar_Label",   "MC Material Auto"),
NSLOCTEXT("FMCEditorModule", "MCMaterialAuto_ToolBar_Tooltip", "머티리얼 자동 생성기 — Claude CLI + mcwiki MCP"),
```

#### Fix 3: 함수를 `#define` 다음으로 이동

```cpp
#define LOCTEXT_NAMESPACE "FMCEditorModule"

static void OnEditorOpened(...)
{
    LOCTEXT("Key", "Default");   // ✅
}
```
- ✅ 기존 LOCTEXT 코드 유지
- ⚠ file 구조 강제 — file-local helper 함수가 `#define` 위에 못 옴

## 회피 패턴 (Production)

| 상황 | 권장 Fix |
|---|---|
| file 전체가 *단일 namespace* | Fix 1 (top `#define`, bottom `#undef`) — UE 표준 패턴 |
| file 안 *helper 함수가 `#define` 위* 정의 | Fix 2 (`NSLOCTEXT`) — 위치 무관 |
| 같은 file 안 *여러 namespace* 사용 | Fix 2 (`NSLOCTEXT`) — namespace per-call |
| header file 안 inline LOCTEXT | Fix 2 (`NSLOCTEXT`) — header 의 `#define` 은 caller 에 leak |

## 변형 사례

1. **PCH unity build 에서 `#define` leak**:
   - `#undef LOCTEXT_NAMESPACE` 누락 시 다음 .cpp 가 *이전 file 의 namespace* 상속 → silent wrong key
   - **회피**: file 끝 `#undef` 의무 (UE 표준 코드 컨벤션)
2. **inline 함수 / template 안 LOCTEXT**:
   - header 안 LOCTEXT 호출 → caller 의 `LOCTEXT_NAMESPACE` 사용 → 일관성 없음
   - **회피**: header 안은 `NSLOCTEXT` 의무
3. **DECLARE_LOG_CATEGORY** 등 다른 file-local macro:
   - 유사 패턴 — `#define` 위치 의존성 모두 동일 hazard

## 진단

컴파일 에러 메시지 패턴:
- MSVC: `error C2065: 'L<NamespaceMacroName>': 선언되지 않은 식별자` — `L` prefix 는 LOCTEXT 매크로의 token paste 결과
- Clang: `error: use of undeclared identifier 'L<NamespaceMacroName>'`

진단 절차:
1. 에러 식별자가 `L<NamespaceMacroName>` 형태 → LOCTEXT 매크로 expansion 결과 확인
2. file 안 `#define LOCTEXT_NAMESPACE` 위치 검사
3. LOCTEXT 호출 *앞* 에 정의되어 있는지 line 비교

## 관련 entity

- (`FText` — LOCTEXT 의 반환 타입, UE 의 기본 localization 타입. vault entity 미작성 — 본문 inline 처리)

## 열린 질문

1. ❓ UE 의 `LOCTEXT_NAMESPACE` Unity Build 통합 — file 들이 묶일 때 namespace 누수 정확한 동작 ([[concepts/Unity-Build-Include-Cascade]] 과 결합 검토 필요).
2. ❓ `NSLOCTEXT` 의 namespace 인자가 *런타임 변수* 가능한지 — 모두 compile-time literal 만 허용? UE source 직접 확인 필요.

## Cross-link

- `concepts/AssetEditor-Toolbar-OnEditorOpened-Pattern` (이 hazard 의 실측 발견 cycle)
- `concepts/UE-NameHiding-Override-Hazard` (같은 v0.20 빌드 fix 의 페어)
- `concepts/Unity-Build-Include-Cascade` (유사 build-error 함정)

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| `LOCTEXT_NAMESPACE` 매크로 expansion 시점 의존 | 🟢 VAULT | C/C++ preprocessor 표준 |
| LOCTEXT 매크로 정의 (token paste) | 🟢 VAULT | UE Internationalization 헤더 |
| NSLOCTEXT 위치 무관 동작 | 🟢 VAULT | UE 표준 매크로 |
| `#undef` 누락 시 namespace leak | 🟡 PARTIAL | Unity build 안 정확한 동작 미검증 |
| MCMaterialAuto v0.20 NSLOCTEXT 채택 동작 | 🟢 VAULT | 실측 |

## 변경 이력

- 2026-05-22: 초안 작성 (MMA-41 / MCMaterialAuto v0.20 빌드 fix 직후)
- 2026-05-22: FText link 정리 — vault entity 미작성으로 본문 inline 처리 (vault §06 정직성)
