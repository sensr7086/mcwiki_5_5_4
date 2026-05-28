---
title: UE FInteractiveProcess Wrapper Lifecycle Pattern
slug: UE-FInteractiveProcess-Wrapper-Lifecycle-Pattern
kind: concept
status: live
confidence: 🟢 VAULT
last_updated: 2026-05-27
audit_5_5_4: pass  # 2026-05-27 Phase 2 engine grep 완료
engine_version: 5.5.4
related_concepts:
  - UE-DelegateLambda-ParamCount-Mismatch-Hazard
  - Claude-CLI-Session-Continuation
related_synthesis:
  - mc-datatable-auto-blueprint
  - mc-datatable-auto-build-cycle-postmortem
  - mc-claude-mcp-editor-integration-blueprint
related_entities:
  - FInteractiveProcess
tags: [finteractiveprocess, lifecycle, tsharedptr, thread, delegate, race]
sources:
  - "C:/Unreal/UnrealEngine/Engine/Source/Runtime/Core/Public/Misc/InteractiveProcess.h"
---

# UE FInteractiveProcess Wrapper Lifecycle Pattern

## 한 줄 요약

**`FInteractiveProcess` wrapper TSharedPtr 는 process exit / OnCompleted delegate fire 후에도 자동 정리되지 않음.** 다음 `Run` 호출 시 *이전 wrapper 가 살아있다고 판정* → 자동 재시도 흐름 차단 / race 위험. **3-layer defense** 의무.

## 권위 (🟢 VAULT)

UE 5.7.4 engine source:

```
Source/Runtime/Core/Public/Misc/InteractiveProcess.h:25
  DECLARE_DELEGATE_TwoParams(FOnInteractiveProcessCompleted, int32 /*ExitCode*/, bool /*bShutdown*/);
```

`FInteractiveProcess` 자체는 `IsRunning()` / `Cancel()` / `OnCompleted` event 만 제공 — *wrapper TSharedPtr 의 자동 reset 책임 없음*.

→ wrapper 객체는 host (예: `UMCDataTableAutoSubsystem`) 의 멤버 `TSharedPtr<...> ActiveProcess` 가 reset 호출 안 하는 한 *영구* 살아있음.

## 함정 family

### 1. process exit 후에도 wrapper 살아있음

```cpp
TSharedPtr<FMCDataTableAutoClaudeProcess> ActiveProcess;

// 1. Run 호출 — wrapper 생성 + background process spawn
ActiveProcess = MakeShared<FMCDataTableAutoClaudeProcess>();
ActiveProcess->Run(...);

// 2. process exit → monitor thread → OnCompleted delegate fire
//   BUT: ActiveProcess TSharedPtr 는 *여전히 valid*.

// 3. 다음 Run 호출 시 guard:
if (ActiveProcess.IsValid() && ActiveProcess->IsRunning()) {
    // ❌ false positive — wrapper 살아있고 IsRunning() race
    return;  // 차단됨!
}
```

→ **자동 재시도 흐름이 차단됨**. 사용자 manual Cancel 후 재시도 필요.

### 2. OnCompleted 콜백의 thread 환경

`OnCompleted` delegate 는 *background monitor thread* 에서 fire. callback 안에서 `ActiveProcess.Reset()` 호출 시 *자기 자신 TSharedPtr 를 reset* → refcount 0 → wrapper 객체 dangling 위험 (callback stack 안에서 객체 소멸).

→ **callback 안 즉시 Reset 금지**. AsyncTask GameThread 마샬링 후 Reset 의무.

### 3. race window — concurrent Run + OnCompleted

GameThread 가 새 `Run` 호출하는 도중 / 직전에 background OnCompleted 가 Reset → 새 wrapper assign 도 race 위험.

## 회피 패턴 — 3-layer defense (🟢 VAULT — MCDataTableAuto 실측)

### Layer 1 — Run 진입점 unconditional Reset

```cpp
void UMCDataTableAutoSubsystem::StartGeneration(const FString& Prompt) {
    // ... 다른 guard ...

    if (ActiveProcess.IsValid()) {
        if (ActiveProcess->IsRunning()) {
            BroadcastLog("이전 작업 진행 중 — Cancel 후 새 spawn 자동 진행");
            ActiveProcess->Cancel();
        } else {
            BroadcastLog("이전 process wrapper 정리 (이미 종료됨)");
        }
        ActiveProcess.Reset();  // unconditional
    }

    // 새 wrapper 생성 + Run
    ActiveProcess = MakeShared<FMCDataTableAutoClaudeProcess>();
    ActiveProcess->Run(...);
}
```

### Layer 2 — OnCompleted defer Reset (GameThread 마샬링)

```cpp
auto OnDone = FOnComplete::CreateLambda([WeakThis](int32 ExitCode, bool bCanceled) {
    if (UMCDataTableAutoSubsystem* This = WeakThis.Get()) {
        This->BroadcastLog(FString::Printf(TEXT("[done] exit=%d"), ExitCode));
    }

    // GameThread defer Reset — callback stack 떠난 후 안전.
    AsyncTask(ENamedThreads::GameThread, [WeakThis]() {
        if (UMCDataTableAutoSubsystem* This = WeakThis.Get()) {
            // !IsRunning() 재확인 — 다음 Run 이 이미 새 wrapper 할당했을 가능성 회피.
            if (This->ActiveProcess.IsValid() && !This->ActiveProcess->IsRunning()) {
                This->ActiveProcess.Reset();
            }
        }
    });
});
```

### Layer 3 — 자동 재시도 흐름 직전 명시 cleanup

```cpp
// 자동 재시도 람다 안 — IngestSpreadsheet 진입 직전:
if (SS->ActiveProcess.IsValid() && !SS->ActiveProcess->IsRunning()) {
    SS->ActiveProcess.Reset();  // defense in depth
}
SS->ResetSession();
SS->IngestSpreadsheet(...);
```

## 진단 증상 (Layer 미적용 시)

- 사용자 widget 로그: `[warn] 이미 진행 중인 작업 있음 — Cancel 후 재시도` (그러나 사실은 종료된 process)
- `[done] exit=0` 후 새 Run 차단
- 자동 재시도 / 다음 cycle 진입 안 됨

## MCDataTableAuto 적용 사례

Phase 3c-3 후속 (2026-05-26) — 사용자 스크린샷에서 `[done] (exit code=0)` 후 자동 재시도 시 **`[warn] 이미 진행 중인 작업 있음`** 발생 → 3-layer defense 적용 후 정상 흐름 복귀.

## 변경 이력

- **2026-05-26** — 신규 작성. MCDataTableAuto Phase 3c-3 후속 자동 재시도 차단 case 정식화.
## §X. 5.5.4 Audit Status (2026-05-27) — engine grep 완료

> Phase 2 audit · [[synthesis/phase-2-audit-14-concepts]] §3·§5 · **결정**: pass

**검증 결과 (engine source dual-grep, 2026-05-27)**:

- `InteractiveProcess.h`: **5.5.4 = 5.7.4 = 260 lines, byte-identical** (diff 0)
- TSharedPtr wrapper / lifecycle 패턴 5.5.4 에서 동일
- **결정**: 🟢 본 페이지의 3-layer defense 패턴 5.5.4 에서도 그대로 유효.

> 본 audit 는 5.5.4 + 5.7.4 engine source 직접 grep 으로 수행 (2026-05-27). `[[raw/ue-wiki-llm/...]]` 인용은 5.7.4 vintage 자료 보존, 새 검증은 engine source 본가 기반.
