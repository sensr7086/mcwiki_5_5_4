---
name: slatecore-trace
description: 🛠 Slate Trace - Insights 통합 + WidgetReflector + DebugWidgets cvar.
---

# SlateCore / Trace

> 부모 모듈: [`SlateCore`](../SKILL.md) · UE 5.7.4
> 다루는 영역: Slate 디버깅 — `FSlateTrace`(Unreal Insights 통합) + `FSlateDebugging`(이벤트 콜백) + `FSlateCrashReporterHandler` + `WITH_SLATE_DEBUGGING` 가드 분류
> 🛠 본 sub-skill 은 거의 전부 디버그·에디터·개발 빌드 전용.
> 관련 sub-skill: [`SWidget/`](../SWidget/SKILL.md), [`Drawing/`](../Drawing/SKILL.md), [`Application/`](../Application/SKILL.md)

---

## 1. 개요

Slate 의 디버깅·트레이스는 두 시스템:

1. **`FSlateTrace`** — Unreal Insights 의 `Slate` 채널로 이벤트 발행. 위젯 생성·인밸리데이션·페인트·입력을 시간축에 기록.
2. **`FSlateDebugging`** — 런타임 콜백 hook. 디테일 패널·Widget Reflector 가 사용. 외부 도구가 위젯 변경을 모니터링.

둘 다 `UE_BUILD_SHIPPING`/`UE_BUILD_TEST` 에서는 비활성 — `UE_SLATE_TRACE_ENABLED` / `WITH_SLATE_DEBUGGING` 매크로로 가드.

---

## 2. 핵심 헤더와 클래스

### 2.1 Trace (`Public/Trace/`)

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Trace/SlateTrace.h` | `class FSlateTrace : FNoncopyable` (~L40), `enum class ESlateTraceApplicationFlags : uint8` (None/GlobalInvalidation=1<<0/FastWidgetPath=1<<1), `UE_TRACE_CHANNEL_EXTERN(SlateChannel, SLATECORE_API)`, `UE_SLATE_TRACE_ENABLED` 매크로 | Insights 채널 + 트레이스 이벤트 발행. |
| `Trace/SlateMemoryTags.h` | `LLM_DECLARE_TAG_API(SlateUI, SLATECORE_API)` 등 | LLM(Low-Level Memory) 태그 — 슬레이트 메모리 사용량 분류. |

### 2.2 Debugging (`Public/Debugging/`)

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Debugging/SlateDebugging.h` | `class FSlateDebugging`, `WITH_SLATE_DEBUGGING` 매크로(default `!(UE_BUILD_SHIPPING || UE_BUILD_TEST)`), `UE_WITH_SLATE_DEBUG_WIDGETLIST` 매크로 | 런타임 디버그 콜백. 위젯 생성·인밸리데이션 등 이벤트 발행. |
| `Debugging/SlateCrashReporterHandler.h` | `FSlateCrashReporterHandler` | 크래시 시 Slate 컨텍스트(현재 페인트 중인 위젯 등) 수집. |

---

## 3. 사용 / 활성화

### 3.1 Insights 트레이스 켜기

```bash
# 게임 실행 시
UnrealEditor.exe MyProject -trace=cpu,frame,gpu,slate -tracehost=127.0.0.1
```

`-trace=` 에 `slate` 채널 추가 → Unreal Insights 의 Slate Insights 패널 활용.

또는 콘솔:

```
Trace.Enable Slate
Trace.SnapshotFile Slate.utrace
```

### 3.2 콘솔 명령

| 명령 | 효과 |
|------|------|
| `Slate.DebugWidgets` | 모든 위젯 트리 로그 출력. |
| `Slate.InvalidationDebugging.IsEnabled 1` | 인밸리데이션 발행 가시화. |
| `Slate.ShowBatching 1` | DrawCall 배치 경계 색칠. |
| `Slate.DrawElementsStats 1` | 프레임당 element/drawcall 통계. |
| `Slate.GlobalInvalidation 1` | 전체 인밸리데이션 (테스트). |
| `WidgetReflector` (메뉴 / `WidgetReflector` 콘솔) 🛠 | 위젯 트리 시각화 + 클릭으로 위젯 식별. **에디터 전용**. |

### 3.3 LLM (Low-Level Memory) 태그

```bash
stat LLM
# 또는
Memreport -full
```

`SlateUI` 태그로 Slate 메모리 추적. `Public/Trace/SlateMemoryTags.h` 가 `LLM_DECLARE_TAG_API` 로 등록.

---

## 4. FSlateDebugging 콜백 hook (`Debugging/SlateDebugging.h`) 🛠

런타임에 위젯 이벤트를 감시하는 외부 도구가 사용. 일반 게임 코드에서는 거의 만지지 않지만, 디버깅 툴/자동화 테스트 작성 시 활용.

```cpp
#if WITH_SLATE_DEBUGGING
// 인밸리데이션 발행 감시
FSlateDebugging::WidgetInvalidate.AddLambda([](const FSlateDebuggingInvalidateArgs& Args)
{
    UE_LOG(LogTemp, Log, TEXT("Invalidate: %s reason=%s"),
        *Args.Widget->GetTypeAsString(),
        *LexToString(Args.InvalidateReason));
});

// 페인트 단계 감시
FSlateDebugging::PaintDebugInfo.AddLambda([](const FSlateDebuggingPaintArgs& Args) { /* ... */ });

// 입력 라우팅 감시
FSlateDebugging::InputEvent.AddLambda([](const FSlateDebuggingInputEventArgs& Args) { /* ... */ });
#endif
```

(실제 콜백 시그니처는 헤더 참조 — `FSlateDebugging` 의 정적 델리게이트들.)

### 4.1 주요 콜백 카테고리 (개념)

| 콜백 | 발행 시점 |
|------|----------|
| `WarningEvent` | 경고 |
| `WidgetInvalidate` | 위젯 인밸리데이션 |
| `WidgetUpdated` | 위젯 갱신 |
| `Paint` / `PaintDebugInfo` | 페인트 단계 |
| `InputEvent` | 입력 이벤트 |
| `FocusEvent` | 포커스 변경 |
| `NavigationEvent` | 내비게이션 |

---

## 5. CSV / Stat 통계

```cpp
// CSV Profiler 에 통합 — Public/Debugging/SlateDebugging.h 의 SLATE_CSV_TRACKER 매크로
SLATE_CSV_TRACKER(MyEvent, Value);
```

`stat Slate` / `stat SlateRendering` / `stat SlateInvalidation` — 콘솔에서 프레임 단위 통계.

---

## 6. 가상 함수 (오버라이드 포인트)

`FSlateTrace` / `FSlateDebugging` 둘 다 정적 클래스 + 정적 델리게이트로 가상 함수가 없다. 외부 도구는 델리게이트 바인딩으로 hook.

`FSlateCrashReporterHandler` 도 internal 사용으로 일반 코드 비대상.

---

## 7. 예제

### 7.1 인밸리데이션 추적 (디버그 빌드만)

```cpp
#if WITH_SLATE_DEBUGGING
void FMyDebugTool::Init()
{
    FSlateDebugging::WidgetInvalidate.AddRaw(this, &FMyDebugTool::OnInvalidate);
}

void FMyDebugTool::OnInvalidate(const FSlateDebuggingInvalidateArgs& Args)
{
    if (Args.Widget && Args.InvalidateReason != EInvalidateWidgetReason::None)
    {
        Frequency.FindOrAdd(Args.Widget->GetTypeAsString())++;
    }
}

// 결과: 어떤 위젯 타입이 가장 자주 인밸리데이션 발행하는지
void FMyDebugTool::Report() const
{
    for (const auto& Pair : Frequency)
        UE_LOG(LogTemp, Log, TEXT("%s: %d"), *Pair.Key, Pair.Value);
}
#endif
```

### 7.2 Insights 마커 발행 (사용자 코드에서)

```cpp
#if UE_TRACE_ENABLED
TRACE_BOOKMARK(TEXT("UI.MainMenuOpened"));
#endif

// 또는 범위 트레이스 (자체 채널)
SCOPED_NAMED_EVENT(UI_BuildInventory, FColor::Cyan);
{
    BuildInventoryWidgets();
}
```

---

## 8. 운영 가이드 / 함정

1. **Shipping 빌드** — `WITH_SLATE_DEBUGGING` 와 `UE_SLATE_TRACE_ENABLED` 둘 다 0 → 콜백 등록 코드는 컴파일 자체가 빠짐. `#if` 가드 필수.
2. **델리게이트 강 참조** — 인스턴스 멤버에 바인딩 후 정리 안 하면 누수. `RemoveAll(this)` 명시.
3. **Trace 오버헤드** — 모든 채널 켜면 프레임 시간 증가. 필요한 채널만 (`-trace=cpu,frame,slate`).
4. **Reflector 에서 위젯 클릭** — 위젯 코드 위치를 IDE 에서 열려면 `Reflection/PickWidget` 메뉴 + 리플렉션 메타데이터 활성. `FReflectionMetaData` 가 디버그 정보 보유 ([`Types/`](../Types/SKILL.md) §2.3).
5. **GlobalInvalidation** — 디버그용. 게임 빌드에 켜두면 모든 위젯이 매 프레임 재페인트 → 성능 폭락.
6. **Slate Insights** vs **CPU 프로파일러** — Slate Insights는 Slate 사이클 단계별 분해, CPU 프로파일러는 함수별. 둘 다 같이 보면 효율적.

---

## 9. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

본 sub-skill 전체가 디버그·개발 빌드 위주:

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `FSlateTrace` 🛠 | Trace/SlateTrace.h | `UE_SLATE_TRACE_ENABLED` (= `UE_TRACE_ENABLED && !IS_PROGRAM && !UE_BUILD_SHIPPING`) | Insights 채널 발행. |
| `FSlateDebugging` 🛠 | Debugging/SlateDebugging.h | `WITH_SLATE_DEBUGGING` (= `!(UE_BUILD_SHIPPING || UE_BUILD_TEST)`) | 런타임 콜백 hook. |
| `FSlateCrashReporterHandler` 🛠 | Debugging/SlateCrashReporterHandler.h | (개발 빌드) | 크래시 컨텍스트 수집. |
| `Widget Reflector` (FWidgetReflector — Slate 모듈) 🛠 | Slate 측 | `WITH_SLATE_DEBUGGING` | 에디터/개발 빌드 위젯 시각화. |
| `Slate.*` cvar 다수 🛠 | (콘솔) | 디버그·개발 | 프로파일링·디버그용. |
| `LLM_DECLARE_TAG_API(SlateUI, ...)` 🛠 | Trace/SlateMemoryTags.h | `LLM_ENABLED` | LLM 태그 — 메모리 추적. |
| `UE_WITH_SLATE_DEBUG_WIDGETLIST` 🛠 | Debugging/SlateDebugging.h | (디버그) | 모든 SWidget 인스턴스 리스트 보유. |

런타임 게임 빌드에는 본 sub-skill의 hook 들이 거의 다 컴파일에서 빠진다 — 코드 가드 필수.

---

## 10. 관련 sub-skill

- [`SWidget/`](../SWidget/SKILL.md) — 위젯 인밸리데이션이 `FSlateTrace`/`FSlateDebugging` 으로 발행
- [`Drawing/`](../Drawing/SKILL.md) — Paint 단계 트레이스 (`Slate.DrawElementsStats` / `ShowBatching`)
- [`Application/`](../Application/SKILL.md) — Tick 사이클 단계가 Insights `Slate` 채널에 표시
- [`Types/`](../Types/SKILL.md) — `FReflectionMetaData` 가 Reflector 디버그 정보 제공
