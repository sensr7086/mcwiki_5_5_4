---
title: "Claude CLI Session ID UUID Format Strict — DigitsWithHyphensLower 의무"
kind: concept
status: stable
severity: "★★"
tags: [claude-cli, mcp, session, uuid, format, hazard, ue-574, kmcproject]
related_concepts:
  - "[[concepts/Claude-CLI-Session-Continuation]]"
  - "[[concepts/UE-Phantom-Header-Hallucination-Hazard]]"
related_synthesis:
  - "[[synthesis/ue-llm-assumption-hazard-family]]"
created: 2026-05-26
last_updated: 2026-05-26
---

# Claude CLI Session ID UUID Format Strict

> **유래**: MCDataTableAuto Phase 3c-2-ext 빌드 실측 (2026-05-26). claude CLI 의 `--session-id` 가 표준 UUID format 요구 — UE `EGuidFormats::DigitsLower` (하이픈 없는 32 hex) 거부.

## 정의

Claude CLI 의 `--session-id <uuid>` 인자는 **표준 UUID 8-4-4-4-12 format** 강제. 하이픈 없는 32 hex 또는 다른 형식 → `Error: Invalid session ID. Must be a valid UUID.` 즉시 exit code 1.

UE 의 `FGuid::ToString` 은 여러 format 지원하나 *DigitsWithHyphensLower* 만 표준 UUID. 다른 format 사용 시 claude CLI 거부.

## 자세히

### 사례 — MCDataTableAuto Phase 3c-2-ext (2026-05-26)

🟢 **VAULT** — KMCProject 실측.

**위반 코드** (Phase 3c-2 작성):
```cpp
CurrentSessionId = FGuid::NewGuid().ToString(EGuidFormats::DigitsLower);
// 결과: "1058182443591951846dff92a4bc8951" — 32 hex 하이픈 없음
```

**spawn**:
```
claude -p ... --session-id 1058182443591951846dff92a4bc8951 ...
```

**claude CLI 응답**:
```
Error: Invalid session ID. Must be a valid UUID.
exit code: 1
```

**Fix**:
```cpp
CurrentSessionId = FGuid::NewGuid().ToString(EGuidFormats::DigitsWithHyphensLower);
// 결과: "bd048ce3-358b-46c5-8cee-627c719418f8" — 8-4-4-4-12 표준 UUID
```

## UUID 표준 — 8-4-4-4-12

[RFC 4122](https://www.rfc-editor.org/rfc/rfc4122) 정의:

```
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
8 chars - 4 - 4 - 4 - 12 = 32 hex + 4 hyphens = 36 chars
```

예: `bd048ce3-358b-46c5-8cee-627c719418f8`

대소문자 양쪽 허용 (`DigitsWithHyphens` / `DigitsWithHyphensLower` 둘 다 OK).

## UE EGuidFormats — 6 종

🟢 VAULT — Engine grep `Misc/Guid.h:30-80`:

| Enum | Format | UUID 표준 |
|---|---|---|
| `Digits` | 32 hex | ❌ 하이픈 없음 |
| `DigitsLower` | 32 hex lower | ❌ 하이픈 없음 |
| `DigitsWithHyphens` | 8-4-4-4-12 upper | ✅ |
| **`DigitsWithHyphensLower`** | 8-4-4-4-12 lower | ✅ ⭐ 표준 |
| `DigitsWithHyphensInBraces` | `{xxx-xxx-...}` | ⚠ Windows registry 형식 — claude 거부 |
| `DigitsWithHyphensInParentheses` | `(xxx-xxx-...)` | ⚠ COM 형식 — claude 거부 |
| `HexValuesInBraces` | `{0xXX, 0xXX, ...}` | ❌ C++ literal — claude 거부 |
| `UniqueObjectGuid` | UE 내부 형식 | ❌ |

→ **`DigitsWithHyphensLower` 가 claude CLI 와 호환되는 유일한 권장 enum** (DigitsWithHyphens 대문자 도 OK 지만 표준은 lower).

## UE 코드의 GUID 사용처별 권장 format

| 용도 | 권장 format | 이유 |
|---|---|---|
| **Claude CLI `--session-id`** | `DigitsWithHyphensLower` | claude 검증 의무 |
| mcp-config 파일명 | `DigitsLower` | 파일명 자유 형식 |
| Random Bearer token | `DigitsLower` | 임의 string, format 검증 없음 |
| 로그 ID / 임시 키 | `DigitsLower` | 짧은 form 선호 |
| Windows registry 키 | `DigitsWithHyphensInBraces` | Windows 표준 |
| 외부 시스템 UUID (DB / REST) | `DigitsWithHyphensLower` | RFC 4122 표준 |

→ **외부 시스템과 통신 시 항상 표준 UUID** (`DigitsWithHyphensLower`).

## 회피

### Layer 1: 코드 작성 시 format 의도 명시

```cpp
// 외부 시스템 통신 — 표준 UUID 의무
const FString Uuid = FGuid::NewGuid().ToString(EGuidFormats::DigitsWithHyphensLower);

// 내부 식별자 — 짧은 form OK
const FString Token = FGuid::NewGuid().ToString(EGuidFormats::DigitsLower);
```

주석으로 *왜 그 format* 인지 명시.

### Layer 2: 외부 docs / 표준 검증

claude CLI / REST API / DB column 등 *외부 시스템 spec* 의 UUID format 요구사항 확인. 추측 금지.

### Layer 3: 실측 빌드 검증

Phase 단위로 *실제 claude CLI spawn* 테스트. spawn 명령의 `--session-id <uuid>` 출력 형식이 정상 UUID 인지 육안 검증.

### Layer 4: vault citation rule

[[00_meta/06_VaultCitationRule]] §1 — *내부 UE 지식 prior* (DigitsLower 가 기본 GUID 형식) 를 🟢 처럼 단정 금지. 외부 시스템 검증은 🟡 PARTIAL 또는 🔴 INFERRED 표시.

## 답습 reference

MCMaterialAuto `Subsystem.cpp:107` (KMCProject 실측 정확 패턴):
```cpp
CurrentSessionId = FGuid::NewGuid().ToString(EGuidFormats::DigitsWithHyphensLower);
```

MCDataTableAuto Phase 3c-2 의 *부정확 답습* 으로 인한 함정 발생. 답습 시 *정확 grep* 필수.

## 관련

- [[concepts/Claude-CLI-Session-Continuation]] (MMA-53 — --session-id / --continue 동작)
- [[concepts/UE-Phantom-Header-Hallucination-Hazard]] (signature hallucination family)
- [[concepts/UE-DelegateLambda-ParamCount-Mismatch-Hazard]] (같은 cycle 발견)

## 열린 질문

1. ❓ claude CLI 가 다른 UUID variant (v4 외 v1/v5 등) 도 허용하는지 — UE FGuid 는 v4 만 생성. 미검증.
2. ❓ Anthropic API 의 다른 endpoint (session 외) 가 UUID 검증 강제하는지 — claude API 일반 검증 정책.

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| claude CLI --session-id UUID 강제 | 🟢 VAULT | KMCProject Phase 3c-2-ext 실측 에러 |
| UE EGuidFormats 6종 | 🟢 VAULT | Engine grep Guid.h:30-80 |
| DigitsWithHyphensLower 가 정답 | 🟢 VAULT | MCMaterialAuto Subsystem.cpp:107 + 실측 동작 |
| 다른 InBraces / InParentheses variant 의 claude 거부 | 🔴 INFERRED | 미검증 — 추정 |
| API v4 외 variant 허용 | 🔴 INFERRED | 미검증 |

## 변경 이력

- 2026-05-26: 초안 작성. MCDataTableAuto Phase 3c-2-ext 빌드 실측 — DigitsLower → DigitsWithHyphensLower fix. [[concepts/Claude-CLI-Session-Continuation]] 보강 사례.
