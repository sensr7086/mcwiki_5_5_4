---
title: "Claude Code Cowork mode — ToolSearch 우회 패턴"
kind: concept
status: stable
severity: "★★"
tags: [claude-cli, mcp, toolsearch, cowork, MMA-27, hazard, integration]
created: 2026-05-22
last_updated: 2026-05-22
---

# Claude Code Cowork mode — `ToolSearch` 우회 패턴

## 정의

Claude Code 의 **Cowork mode** 는 MCP tool 들을 **deferred (lazy-load)** 로 등록한다 — 사용 직전에 `ToolSearch` 도구를 호출해 schema 를 로드하는 것이 default 동작. 그러나 non-interactive `-p` 모드 + 자동화 시나리오에서는:
1. `ToolSearch` 호출이 한 턴을 소비 → max-turns 빠르게 소진
2. `ToolSearch` 가 *어떤* 도구를 로드할지 LLM 판단 → 의도한 도구가 활성화 안될 위험
3. 도구 namespace 가 정확히 안 잡혀 `mcp__<server>__<tool>` 호출 시 InputValidationError

해결: **`--allowed-tools` 인자로 사전 명시** + **`--disallowed-tools "ToolSearch"`** — 사용할 도구를 사전 활성화하고 ToolSearch 자체를 차단.

> ℹ️ `ToolSearch` 는 Cowork mode 의 내장 도구 — 별도 entity 페이지 없이 본 concept 안에서 다룬다.

## 자세히

### 사례: MCMaterialAuto v0.9.4 도입

🟢 **VAULT** — MMA-24/27 hazard 로그:

문제 증상:
- claude.exe 가 첫 턴에서 `ToolSearch` 호출 → "select:mcp__ue_material__*" query → schema 응답
- 두 번째 턴에서 도구 호출 시도 → "tool not found" 또는 InputValidationError
- `max-turns 30` 인데 ToolSearch 만 반복하다 종료

원인:
- Cowork mode 의 deferred registry 는 LLM 이 `ToolSearch` 를 거쳐야 도구 schema 가 보이는 구조
- 그러나 LLM 이 *server name* 을 정확히 모르면 query 가 broad → 무관 도구가 잡혀 max-turns 소진
- Server name 의 dash/underscore 표기 불일치(MMA-19)와 결합 시 영구 미인식

### Fix

MCMaterialAuto 의 ClaudeProcess wrapper (v0.9.4 채택본 — KMCProject 내부 `FMCMaterialAutoClaudeProcess` class):

```cpp
const FString AllowedTools =
    TEXT("mcp__ue_material__list_textures,")
    TEXT("mcp__ue_material__read_material,")
    TEXT("mcp__ue_material__create_master_material,")
    // ... 모든 도구 명시 ...
    TEXT("mcp__mcwiki__read_index,")
    TEXT("mcp__mcwiki__read_page,")
    // ...
    TEXT("mcp__mcwiki__stats");

// args 조합:
// --allowed-tools "<above>" --disallowed-tools "ToolSearch,<mcwiki-write-tools>"
// --permission-mode bypassPermissions
```

**핵심 효과**:
1. `--allowed-tools` 명시 → Cowork 의 deferred registry 가 *시작 시* 즉시 활성화 (lazy-load 우회)
2. `--disallowed-tools "ToolSearch"` → LLM 이 ToolSearch 호출 시도해도 거부 → 막다른 길 차단
3. LLM 은 `mcp__ue_material__*` namespace 를 첫 턴부터 인식 → 직접 호출 가능

### 추가 변형 (SystemPrompt)

System prompt 에 의무 항목 0번으로 추가:
> "도구 호출 시 절대 ToolSearch 를 사용하지 말 것. 모든 도구는 사전 활성화되어 있음."

🟡 **PARTIAL** — LLM 행동 reinforcement — 100% 차단은 `--disallowed-tools` 가 담당. SystemPrompt 는 추가 안전망.

## 회피 패턴

1. **All-tools 사전 명시**:
   - production: 자동화에서 사용할 모든 `mcp__*` 도구를 `--allowed-tools` 에 enumerate
   - LLM 이 발견할 수 없는 도구는 호출도 불가능 → ToolSearch 필요 자체가 없음

2. **ToolSearch 차단 의무**:
   - non-interactive `-p` + 자동화에서는 항상 `--disallowed-tools` 에 `ToolSearch` 포함
   - 사용자가 명시적 조정 원할 때만 interactive mode 에서 활용

3. **Server name 통일**:
   - MCP server name 은 `[a-z_]+` 만 사용 (dash 금지) — `mcp__<server>__<tool>` namespace 가 LLM 입력에서 깔끔히 파싱
   - MMA-19 와 결합 — `ue-material` 대신 `ue_material`

## 변형 사례

1. **Interactive mode (`claude` REPL)**:
   - ToolSearch 가 유용 — 사용자가 도구 발견 / 선택
   - 자동화 모드 외에는 차단 불요

2. **`--mcp-config` 단일 server**:
   - server 하나만 등록되어도 도구 다수면 동일 문제 발생
   - tool 개수 ≥ ~10 부터 deferred 효과 두드러짐

3. **`max-turns` budget**:
   - ToolSearch 차단으로 turn budget 절약 → 같은 작업이 더 적은 turn 으로 완료
   - MCMaterialAuto: 30 turns 의무, 사전 명시 후 평균 10 turn 이하로 감소 (🔴 INFERRED — 정확한 메트릭은 미수집)

## 관련 entity

- [[Claude-Code-CLI]]
- [[MCP-Protocol]]
- [[FInteractiveProcess]] (UE 측 spawn)

## 열린 질문

1. ❓ Cowork mode 의 deferred registry 가 정확히 어떤 임계치 (도구 개수? schema 크기?) 에서 발동하는지 — 공식 문서 미확인.
2. ❓ Plugin namespace (예: `mcp__plugin:server__tool`) 의 `--allowed-tools` 명시 형식 — colon 처리 방식 미확인. 현재는 underscore-only namespace 만 검증됨.
3. ❓ `--allowed-tools` 의 wildcard 지원 (`mcp__ue_material__*`) — 미검증. 현재는 fully-qualified enumeration.

## Cross-link

- `concepts/Python-Stdio-MCP-Buffering-Hazard` (같은 MCP integration 작업)
- `concepts/Material-Editor-External-Change-Reopen`
- `synthesis/UE-Claude-MCP-Integration-Patterns` (TODO)
- `00_meta/03_EvaluatorRecipe` § Stage 6 (Integration boundary 검증)

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| Cowork mode 가 도구 deferred | 🟢 VAULT | Cowork mode system prompt 명시 |
| `--allowed-tools` 가 deferred 사전 활성화 | 🟢 VAULT | 실측 — MCMaterialAuto v0.9.4 fix 확인 |
| `--disallowed-tools` 가 ToolSearch 차단 | 🟢 VAULT | 실측 동일 |
| SystemPrompt 가 추가 안전망 | 🟡 PARTIAL | LLM 행동 reinforcement, 정량 검증 미완 |
| turn budget 절약 정량값 | 🔴 INFERRED | 정확한 메트릭 미수집 |
| Plugin namespace 처리 | 🔴 INFERRED | 미검증 |

## 변경 이력

- 2026-05-22: 초안 작성 (MMA-27 fix 직후, MCMaterialAuto v0.9.4 채택본 기반)
- 2026-05-22: cross-link 정리 — ToolSearch (inline 처리) / MCMaterialAutoClaudeProcess (KMCProject 내부 class, vault scope 외) link 제거
