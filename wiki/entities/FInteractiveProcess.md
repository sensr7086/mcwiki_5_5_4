---
title: "FInteractiveProcess"
kind: entity
status: stub
parent: core
tags: [core, hal, process, stdin-stdout, ue-574]
module: Core
header: "Public/Misc/InteractiveProcess.h"
created: 2026-05-22
last_updated: 2026-05-22
---

# FInteractiveProcess

UE 의 **외부 프로세스 launch + stdio piping wrapper**. `FPlatformProcess::CreateProc` 위에 비동기 output capture + cancel 기능 추가. claude.exe / python / 외부 도구 통합 시 사용.

## 핵심 특성

- **Async output**: `OnOutput().BindLambda` 로 stdout line-by-line 수신
- **Completion callback**: `OnCompleted().BindLambda(int32 ExitCode, bool bShutdown)`
- **Cancel + tree kill**: `Cancel(/*KillTree*/true)` — 자식 PID tree 까지 종료
- **Long-running flag**: constructor 의 `bLongRunning` 으로 hint

## 주요 API

| API | 설명 |
|---|---|
| `FInteractiveProcess(Path, Args, bHidden, bLongRunning)` | 생성자 |
| `Launch()` | 프로세스 시작 — bool 반환 |
| `Cancel(bKillTree)` | 종료 |
| `IsRunning()` | 상태 |
| `OnOutput()` | output delegate |
| `OnCompleted()` | 완료 delegate |

## 사용 패턴

```cpp
TSharedPtr<FInteractiveProcess> P = MakeShared<FInteractiveProcess>(
    Exe, Args, /*Hidden*/true, /*LongRunning*/true);
P->OnOutput().BindLambda([](const FString& Out) { /* parse NDJSON */ });
P->OnCompleted().BindLambda([](int32 Code, bool) { /* cleanup */ });
if (!P->Launch()) { /* error */ }
```

## 관련 함정

- Output 이 **block-buffered** 외부 프로세스는 line 단위 수신 안 됨 — [[concepts/Python-Stdio-MCP-Buffering-Hazard]]
- Cancel 시 자식 프로세스 tree 처리 — `bKillTree=true` 명시 의무 (MMA-18)
- stdin 쓰기 API 직접 노출 안됨 — 양방향 통신 필요 시 별도 pipe handle 관리

## 관련 entity

- [[UObject]] (사용처는 대부분 UEditorSubsystem)

## Citation Disclosure

| 주장 | Tier |
|---|---|
| OnOutput / OnCompleted delegate | 🟢 VAULT (UE 5.7 `InteractiveProcess.h`) |
| Cancel KillTree 동작 | 🟢 VAULT (MMA-18 실측) |
| stdin 직접 노출 부재 | 🟡 PARTIAL (header 확인, undocumented 우회 가능성) |

## 변경 이력

- 2026-05-22: stub 작성 (MMA-13/18/29 filing-back cross-link)
