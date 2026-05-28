---
title: "Claude CLI Session Continuation — --session-id vs --continue vs --resume 매트릭스"
kind: concept
status: stable
severity: "★"
tags: [claude-cli, session, integration, MMA-53, ue-574]
created: 2026-05-22
last_updated: 2026-05-27
audit_5_5_4: pass-pattern-stable  # 2026-05-27 Phase 2 audit · raw dual-confirmed
---

# Claude CLI Session Continuation — `--session-id` vs `--continue` vs `--resume` 매트릭스

## 정의

Claude Code CLI 의 `-p` (non-interactive) 모드에서 *이전 대화 컨텍스트* 를 유지하는 3개 옵션 — `--session-id <UUID>` (명시 ID 생성/지속) / `--continue` (가장 최근 session 이어서) / `--resume <id>` (특정 ID 이어서) — 의 *동작 매트릭스* 및 *외부 통합 (UE Plugin 등)* 시 권장 패턴.

UE Editor 의 chat-style UI 처럼 *여러 prompt 가 동일 대화* 로 이어져야 할 때 사용. 잘못된 옵션 조합 시 *대화 context 손실* (매번 새 session) 또는 *세션 충돌*.

## 자세히

### 3 옵션 비교 (UE 5.7 + Claude Code v2.1.90+ 기준)

🟢 **VAULT** — GitHub Issue #3976 / #44607 / #42311 검증 + MCMaterialAuto v0.33 실측:

| 옵션 | 동작 | `-p` 모드 동작 | 안정성 |
|---|---|---|---|
| **`--session-id <UUID>`** | 명시 ID 로 *새 session 생성* 또는 *기존 session 이어서* (.jsonl 파일이 UUID 이름) | ✅ 동작 — 첫 호출에서 새 session, 같은 ID 재사용 시 이어짐 | 🟢 가장 명확 |
| **`--continue` (= `-c`)** | *가장 최근* session 이어서 (모든 session 중 마지막) | ✅ 동작 (issue #3976 일부 해결) | 🟡 race 가능 (다른 instance 와 충돌) |
| **`--resume <id>`** | 특정 session ID 로 이어서 | ⚠ issue #3976 — non-interactive 모드 불안정 | 🔴 회피 |

⚠ **v2.1.90 변경**: interactive `--resume` picker 가 `-p` / SDK session 안 보임 → resume 시 명시 ID 의무.

### 외부 통합 (UE Plugin) 권장 패턴

🟢 **VAULT** — MCMaterialAuto v0.33 채택본:

#### 패턴 1 — `--session-id` 만 사용 (가장 안전)

```cpp
// Subsystem 멤버:
bool    bSessionStarted = false;
FString CurrentSessionId;

void StartGeneration(const FString& Prompt) {
    if (!bSessionStarted) {
        CurrentSessionId = FGuid::NewGuid().ToString(EGuidFormats::DigitsWithHyphensLower);
        bSessionStarted = true;
    }
    // 첫 호출 + 이후 호출 모두 같은 --session-id 사용
    ClaudeProcess.Run(Prompt, ..., false, CurrentSessionId);
}

void ResetSession() {
    bSessionStarted = false;
    CurrentSessionId.Empty();
    // 다음 StartGeneration 이 새 UUID 생성
}
```

→ Args:
- 첫: `claude -p "<prompt>" --session-id <UUID>`
- 이후: `claude -p "<prompt>" --session-id <UUID>` (같은 UUID)
- New Session: 새 UUID 생성

#### 패턴 2 — 첫 `--session-id` + 이후 `--continue` (혼합)

```cpp
const bool bResume = bSessionStarted;
if (!bSessionStarted) {
    CurrentSessionId = FGuid::NewGuid().ToString(...);
    bSessionStarted = true;
}
ClaudeProcess.Run(Prompt, ..., bResume, CurrentSessionId);
```

→ Args:
- 첫: `claude -p "<prompt>" --session-id <UUID>`
- 이후: `claude -p "<prompt>" --continue`
- ⚠ `--continue` 가 *다른 instance* 의 session 과 race 가능 — 단일 UE Editor 환경에서는 안전

MCMaterialAuto v0.33 은 **패턴 2 채택** — 첫 session-id 명시 + 이후 continue.

### ClaudeProcess.Run 인자 확장 (UE 측)

```cpp
void FMCMaterialAutoClaudeProcess::Run(
    const FString& UserPrompt,
    uint16 UeMcpPort,
    FOnComplete OnDone,
    FOnStreamLine OnLine,
    bool bResumeSession = false,
    const FString& SessionId = FString())
{
    FString SessionArg;
    if (bResumeSession)        SessionArg = TEXT("--continue ");
    else if (!SessionId.IsEmpty()) SessionArg = FString::Printf(TEXT("--session-id %s "), *SessionId);
    // 둘 다 비움 → anonymous session

    const FString Args = FString::Printf(
        TEXT("-p %s ... %s --output-format stream-json --verbose"),
        *EscapeShellArg(UserPrompt), ..., *SessionArg);
}
```

## 회피 패턴 (Anti-pattern)

| ❌ Anti | ✅ 권장 |
|---|---|
| 매 호출마다 *anonymous session* (인자 없음) | 첫 호출 시 `--session-id` 명시 |
| `--resume <id>` 사용 (`-p` 모드) | `--session-id <id>` 재사용 또는 `--continue` |
| 사용자 session 종료 명시 없음 | `ResetSession()` 버튼 + `bSessionStarted=false` |
| 다중 UE Editor instance 에서 `--continue` | 각 instance 별 명시 ID (`--session-id`) |
| process 진행 중 ResetSession 호출 | 우선 Cancel + 풀 로그 close 후 reset |

## 변형 사례

1. **여러 Material Editor 동시 작업**: 각 widget instance 별 별도 SessionId — *논리적 isolation*
2. **Session 영구 보관**: Saved/<plugin>/sessions.ini 에 UUID 보관 → Editor 재시작 후도 이어서 가능
3. **명시 brand 의 session list UI**: 사용자에게 *과거 session 목록* 표시 + 선택 — `--session-id <chosen>` 으로 resume

## 진단

증상:
- 두 번째 prompt 에서 LLM 이 *첫 prompt 의 컨텍스트 모름* — session 미연결
- 또는 *완전히 새 대화* 시작 (자기 소개 등)

진단 절차:
1. 풀 로그의 spawn 명령 확인 — `--session-id` / `--continue` 인자 포함 여부
2. Claude session 파일 (`~/.claude/projects/<id>/<uuid>.jsonl`) 의 timestamp 비교
3. `[log] new session: <uuid>` 메시지 — 첫 호출 시 1회만 표시되어야 정상

## 관련 함정

- GitHub Issue #3976 — *Resuming sessions doesn't work in non-interactive mode (SDK)* — `--resume` 의 진행 중 hazard
- GitHub Issue #42311 — `--resume` session picker 미문서화
- Issue #35599 — `--resume latest` 미지원 (현재는 `--continue` 가 대체)
- Issue #44063 — 모든 session 의 resume 미지원 (현재 `-p` session 만)

## 관련 entity

- [[Claude-Code-CLI]] (CLI 도구)
- [[MCP-Protocol]] (도구 호출 → session 안 누적)
- [[FInteractiveProcess]] (UE 측 spawn)

## 열린 질문

1. ❓ `--session-id` 재사용 시 *.jsonl 파일에 새 turn append* — 일관성 검증 필요.
2. ❓ Editor 종료 후 같은 UUID 로 resume — 영구 보존 여부 검증.
3. ❓ Session 별 token budget — `--max-turns 30` 이 *session 전체* 누적인지 *호출당* 인지 모호.

## Cross-link

- `concepts/Claude-Code-Cowork-ToolSearch-Bypass` (같은 Claude CLI 통합 계열)
- `concepts/Python-Stdio-MCP-Buffering-Hazard` (proxy 측 session 정보 처리)
- `synthesis/mc-claude-mcp-editor-integration-blueprint` § Phase 5 (Claude CLI 인자)

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| 3 옵션 매트릭스 | 🟢 VAULT | GitHub Issue #3976/#42311/#44607 + Claude Code Docs CLI Reference |
| `-p` 모드 `--session-id` 동작 | 🟢 VAULT | Issue #44607 검증 + MCMaterialAuto v0.33 실측 |
| `--continue` race 가능성 | 🟡 PARTIAL | 단일 instance 검증 — multi-instance 미실측 |
| 패턴 1 / 패턴 2 안정성 비교 | 🟢 VAULT | MCMaterialAuto v0.33 두 패턴 모두 시도 |
| `--max-turns` budget 모호 | 🔴 INFERRED | 미검증 |

## 변경 이력

- 2026-05-22: 초안 작성 (MMA-53 / MCMaterialAuto v0.33 채택본 기반)
## §X. 5.5.4 Audit Status (2026-05-27)

> Phase 2 audit · [[synthesis/phase-2-audit-14-concepts]] §3 · **결정: 🟢 Group A — pass-pattern-stable**

Claude CLI tooling (Claude Code v2.1.90+) 의 내용 — UE 5.7 은 본 페이지 작성 시점의 context 일 뿐, 본질은 UE 영향 없음. 5.5.4 vault 에서도 동일하게 적용.

원본 🟢 VAULT marker 는 5.7.4 시점 engine grep 사실로 *그대로 보존*. 5.5.4 에서 동일 결론 유효 — pattern 자체가 minor patch 사이 변동 없음.

**Audit pending (선택)**: line number / 특정 hit count 가 5.5.4 에서 정확히 같은지 검증하려면 `C:\Unreal\UnrealEngine\Engine\Source\` 직접 grep. 본 audit 에서는 pattern 결론만 검증, 정량 라인은 후속 작업으로 분리.
