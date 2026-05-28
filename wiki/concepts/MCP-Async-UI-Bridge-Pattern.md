---
title: "MCP Async UI Bridge — TPromise + Multicast Delegate + Widget 사용자 입력 동기화"
kind: concept
status: stable
severity: "★★★"
tags: [mcp, async, ui-bridge, tpromise, multicast-delegate, editor-subsystem, MMA-49, ue-574]
created: 2026-05-22
last_updated: 2026-05-25
---

# MCP Async UI Bridge — TPromise + Multicast Delegate + Widget 사용자 입력 동기화

## 정의

MCP (Model Context Protocol) 도구 호출의 **동기 응답 기대** 와 UE Editor UI 의 **비동기 사용자 입력 대기** 사이의 *bridge* 패턴. MCP server (UE 측) 가 도구 호출 받음 → 즉시 응답 안 하고 *Promise 보관* + Widget broadcast → 사용자 클릭 대기 → 클릭 시 Promise SetValue → Future 해제 → MCP server 가 Claude 에 응답.

사용 예: LLM 이 작업 중 사용자 의도 확인 (예: "다음 중 어느 효과 적용?") — UE Widget 에 listbox/버튼 표시 → 사용자 선택 → Claude 에 결과 반환. 도구 호출이 *블로킹* — Claude turn 이 사용자 응답까지 대기.

## 자세히

### 사례: MCMaterialAuto v0.32 — ask_user_choice 도구 (MMA-49)

🟢 **VAULT** — MCMaterialAuto v0.32 채택본.

**문제 상황**:
- MCP tool 호출은 *request-response 동기 model* — `tools/call` 응답이 Claude 에 즉시 반환되어야 다음 turn 진행
- 그러나 *사용자 입력 대기* 는 본질적으로 비동기 — UI 버튼 클릭 시점이 외부 결정
- 두 시간 축의 *bridge* 가 필요 — Promise/Future 동기화 + multicast delegate broadcast

**구현 5-Layer**:

```cpp
// Layer 1 — Subsystem multicast delegate + pending promise
DECLARE_MULTICAST_DELEGATE_TwoParams(FOnAskUserChoice,
    const FString& /*Question*/, const TArray<FString>& /*Options*/);

class USubsystem {
    FOnAskUserChoice OnAskUserChoice;
    TSharedPtr<TPromise<TSharedPtr<FJsonObject>>, ESPMode::ThreadSafe> PendingPromise;
};

// Layer 2 — DispatchToolCall 안 비동기 path 분기
if (Method == TEXT("ask_user_choice")) {
    auto Promise = MakeShared<TPromise<TSharedPtr<FJsonObject>>, ESPMode::ThreadSafe>();
    TFuture Future = Promise->GetFuture();

    AsyncTask(ENamedThreads::GameThread, [this, Params, Promise]() {
        // 직전 미응답 promise race 방어
        if (PendingPromise.IsValid()) {
            TSharedPtr<FJsonObject> Cancel = MakeShared<FJsonObject>();
            Cancel->SetStringField(TEXT("error"), TEXT("superseded"));
            PendingPromise->SetValue(Cancel);
            PendingPromise.Reset();
        }
        PendingPromise = Promise.ToSharedPtr();

        // Widget 에 broadcast — UI 트리거
        OnAskUserChoice.Broadcast(Question, Options);
    });
    return Future;
}

// Layer 3 — Widget 의 핸들러 — UI 카드 + 버튼 동적 생성
void Widget::HandleAskUserChoice(const FString& Q, const TArray<FString>& Opts) {
    for (int32 i = 0; i < Opts.Num(); ++i) {
        SNew(SButton).OnClicked(FOnClicked::CreateSP(this,
            &Widget::OnOptionClicked, i, Opts[i]));
    }
}

// Layer 4 — Widget 의 클릭 콜백 — Subsystem 의 응답 함수 호출
FReply Widget::OnOptionClicked(int32 Index, FString Text) {
    if (USubsystem* Sub = Get()) Sub->RespondToUserChoice(Index, Text);
    return FReply::Handled();
}

// Layer 5 — Subsystem 의 응답 함수 — Promise SetValue
void USubsystem::RespondToUserChoice(int32 Index, const FString& Text) {
    if (!PendingPromise.IsValid()) return;
    TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>();
    R->SetNumberField(TEXT("selected_index"), Index);
    R->SetStringField(TEXT("selected"), Text);
    PendingPromise->SetValue(R);
    PendingPromise.Reset();
}
```

→ Claude → tools/call → DispatchToolCall (비동기) → Future 보관 → Widget UI 표시 → 사용자 클릭 → Promise SetValue → Future 해제 → MCP server 응답 송신 → Claude turn 재개.

### Race 방어 — Promise supersession

여러 ask_user_choice 가 동시 호출되면 (LLM 의 buggy 행동) — *최신 Promise 만 유효* + 이전 Promise 에 `superseded` 에러 응답. 위 코드의 Layer 2 안.

### Thread safety 의무

- `PendingPromise` 는 **game thread 안에서만** 읽기/쓰기 — Layer 2 의 `AsyncTask GameThread` 안에서 등록, Layer 5 의 `RespondToUserChoice` 도 Widget 콜백이라 game thread.
- `TSharedPtr<..., ESPMode::ThreadSafe>` — Promise 자체는 thread-safe.
- HTTP server thread (MCP) 가 DispatchToolCall 호출 → AsyncTask 로 game thread 마샬링.

## 회피 패턴

| Anti-pattern | 회피 |
|---|---|
| Promise 없이 동기 응답 시도 | Widget 클릭 = 외부 비동기 → 즉시 응답 불가능 |
| HTTP thread 에서 직접 SetValue | game thread 마샬링 의무 — AsyncTask |
| 한 Promise 만 유지 (race 무시) | supersede 패턴 — race 발생 시 이전 cancel |
| 사용자 응답 없이 timeout 없음 | 무한 대기 가능 — Claude `--max-turns` 가 외부 제한 |

## 변형 사례

1. **파일 선택 dialog**: LLM 이 `ask_user_file(filter)` 호출 → Widget 의 SFilePathPicker → 사용자 선택 → path 반환
2. **확인 버튼만 (Yes/No)**: ask_user_choice 의 단순 변형 — options=["Yes", "No"]
3. **자유 텍스트 입력**: `ask_user_text(question, placeholder)` — SEditableText + Submit 버튼
4. **숫자 슬라이더**: `ask_user_number(question, min, max)` — SSlider + Submit
5. **다중 선택**: options 의 multi-select — TArray<int32> 응답

## 관련 함정

- LLM 이 *자발적으로 호출 안 함* — system prompt 에 사용 가이드 명시 필요 ("작업 중 사용자 의도 확인 필요 시 ask_user_choice 호출")
- *블로킹 호출* — Claude turn 이 사용자 응답까지 대기 → `--max-turns` 소진 가능. 응답 시점 모니터링 의무
- Widget destroy 중 Promise 미해제 → MCP 응답 timeout. Widget 소멸자에서 PendingPromise cancel 의무 (현재 미구현 — 후속)

## 관련 entity

- [[MCP-Protocol]] (도구 호출 동기 model)
- [[Claude-Code-CLI]] (caller — turn 단위 진행)
- [[USubsystem]] (Subsystem 패턴 base)

## 열린 질문

1. ❓ Widget destroy 시 PendingPromise lifecycle — 현재 미해제 시 Future 영원히 대기 → MCP server 타임아웃 후 처리 (검증 미완).
2. ❓ 다중 ask 동시 호출 (병렬 도구 호출) — supersede 가 *최신만* 보존하지만 LLM 의도가 다를 수도 (Stack 보존 가능성).
3. ❓ 사용자 *Cancel* 버튼 — 명시적 거부 응답 — `error: user_canceled` 같은 형식 표준화.

## Cross-link

- `concepts/MCP-Tool-Schema-LLM-Friendly-Design` (도구 schema 4 패턴 — 본 패턴은 5번째 추가 가능)
- `concepts/Python-Stdio-MCP-Buffering-Hazard` (같은 MCP integration 계열)
- `concepts/Claude-Code-Cowork-ToolSearch-Bypass` (Cowork 도구 전체 통제)
- `synthesis/mc-claude-mcp-editor-integration-blueprint` (Phase 3 — MCP server)
- `synthesis/ue-llm-assumption-hazard-family` (Layer 4 — ask_user_choice 강제)

## Citation Disclosure

| 주장 | Tier | 근거 |
|---|---|---|
| 5-Layer 구조 (delegate / promise / handler / callback / setvalue) | 🟢 VAULT | MCMaterialAuto v0.32 실측 채택 |
| Promise supersede race 방어 | 🟢 VAULT | 실측 코드 |
| HTTP thread → game thread 마샬링 의무 | 🟢 VAULT | vault `[[concepts/MCP-Tool-Schema-LLM-Friendly-Design]]` 패턴 1+2 |
| Widget destroy 시 lifecycle | 🔴 INFERRED | 미검증 |
| Multi-ask Stack 보존 가능성 | 🔴 INFERRED | 미검증 |

## 변경 이력

- 2026-05-22: 초안 작성 (MMA-49 / MCMaterialAuto v0.32 채택본 기반)
- 2026-05-25: frontmatter `last_updated` 추가 + hazard-family synthesis cross-link 추가
