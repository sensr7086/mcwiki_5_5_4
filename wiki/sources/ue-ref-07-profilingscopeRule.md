---
type: source
title: "UE refs — 07 ProfilingScopeRule (의무 hub)"
slug: ue-ref-07-profilingscopeRule
source_path: raw/ue-wiki-llm/references/07_ProfilingScopeRule.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-28
audit_5_5_4: pass-label-only  # 2026-05-28 Phase 2-B auto-classified
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, reference, policy, profiling, trace, insights]
---

# UE refs — 07 ProfilingScopeRule 🚨

> Source: [[raw/ue-wiki-llm/references/07_ProfilingScopeRule.md]] · CLAUDE.md §0.1.3 의무 정책 · UE 5.7.4 SlateCore/UMG grep 검증

## 1. Summary

🚨 **모든 sub-skill 공통 의무** — Tick / TimerManager / FTSTicker / 람다 / UFunction / `OnRep_*` / FieldNotify / ActiveTimer 의 **첫 줄**에 프로파일링 스코프 부착. 이름 없으면 Insights / Stat Profiler 에서 식별 불가 → 성능 문제 역추적 실패. 권위 concept = [[concepts/Profiling-Scope-Rule]].

## 2. 매크로 선택 가이드 🟢

| 매크로 | 시그니처 | 용도 |
| -- | -- | -- |
| `TRACE_CPUPROFILER_EVENT_SCOPE(Name)` | 컴파일 타임 이름 | **Unreal Insights 표준** — 새 코드 권장 |
| `TRACE_CPUPROFILER_EVENT_SCOPE_STR(NameStr)` | 런타임 문자열 | 동적 이름 (위젯 클래스명 등) |
| `SCOPED_NAMED_EVENT(Name, FColor)` | 컴파일 타임 + 색 | **외부 프로파일러** (Pix/Razor/Tracy) — Slate 본체 패턴 |
| `SCOPED_NAMED_EVENT_FSTRING(FString, FColor)` | FString + 색 | UMG `SObjectWidget::Tick` (UMG/Private/Slate/SObjectWidget.cpp L118) |
| `QUICK_SCOPE_CYCLE_COUNTER(STAT_X)` | STAT 식별자 | **`stat <Group>` 콘솔** — 즉석 STAT |
| `DECLARE_CYCLE_STAT` + `SCOPE_CYCLE_COUNTER` | 사전 선언 STAT | 그룹화된 정식 STAT |
| `LLM_SCOPE(Tag)` | 메모리 태그 | CPU 가 아닌 **메모리** 추적 |

**결정 트리**: 새 코드 = `TRACE_CPUPROFILER_EVENT_SCOPE` · Slate/UMG 본체 패턴 따라가기 = `SCOPED_NAMED_EVENT` · 즉석 측정 = `QUICK_SCOPE_CYCLE_COUNTER` · 동적 이름 = `SCOPED_NAMED_EVENT_FSTRING`.

## 3. 의무 부착 위치 🟢

| 진입점 | 권장 매크로 | 비고 |
| -- | -- | -- |
| `AActor::Tick` / `UActorComponent::TickComponent` | `TRACE_CPUPROFILER_EVENT_SCOPE` | Super 먼저, 스코프 그 다음 |
| `UUserWidget::NativeTick` | `SCOPED_NAMED_EVENT_TEXT("MyWidget::Tick", FColor::Cyan)` | Super FIRST → 스코프 |
| `SWidget::Tick` | `SCOPED_NAMED_EVENT(Name, FColor::Green)` | Slate 본체 패턴 |
| `IInputProcessor::Tick` | `TRACE_CPUPROFILER_EVENT_SCOPE` | EditorApplication |
| `FSceneViewExtensionBase::*Pass` | `TRACE_CPUPROFILER_EVENT_SCOPE` + `RDG_EVENT_SCOPE` | Render — 2중 |
| `FTimerManager::SetTimer` 콜백 (람다/UFunction) | `TRACE_CPUPROFILER_EVENT_SCOPE` | 콜백 첫 줄 |
| `FTSTicker::AddTicker` 람다 | `TRACE_CPUPROFILER_EVENT_SCOPE` | 콜백 첫 줄 |
| `SWidget::RegisterActiveTimer` 콜백 | `SCOPED_NAMED_EVENT` | UMG/Slate |
| `OnRep_*` (RepNotify) | `TRACE_CPUPROFILER_EVENT_SCOPE` | 클라이언트 임의 시점 |
| FieldNotify 콜백 | `TRACE_CPUPROFILER_EVENT_SCOPE` | ViewModel binding |
| `AddDynamic / AddUObject / BindUFunction` 바인딩 핸들러 | `TRACE_CPUPROFILER_EVENT_SCOPE` | 외부 시점 호출 |
| 람다 (`Async / ParallelFor / ENQUEUE_RENDER_COMMAND`) | `TRACE_CPUPROFILER_EVENT_SCOPE` | **이름 없음 → 의무** |

## 4. 표준 패턴 🟢

```cpp
// 4.1 — NativeTick (Super FIRST + 스코프)
void UMyHUDWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    SCOPED_NAMED_EVENT_TEXT("MyHUDWidget::Tick", FColor::Cyan);
    // 작업
}

// 4.2 — Timer 람다 (WeakLambda + 스코프)
GetWorld()->GetTimerManager().SetTimer(Handle,
    FTimerDelegate::CreateWeakLambda(this, [this]()
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(MyComp_RegenTick);
        if (CurrentHP < MaxHP) CurrentHP = FMath::Min(MaxHP, CurrentHP + Regen);
    }), 0.5f, true);

// 4.3 — OnRep_* (클라이언트 시점)
UFUNCTION() void UMyComp::OnRep_CurrentHealth(float OldHealth)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyComp_OnRep_CurrentHealth);
    OnHealthChanged.Broadcast(CurrentHealth);
}

// 4.4 — Render 람다 (Render Thread)
ENQUEUE_RENDER_COMMAND(MyCmd)([](FRHICommandListImmediate& RHICmdList)
{
    SCOPED_NAMED_EVENT(MyClass_RenderEnqueue, FColor::Magenta);
    // RHICmdList.*
});
```

## 5. 카테고리별 우선순위 🟡

| 카테고리 | 핵심 hotspot | 강도 |
| -- | -- | -- |
| **Render** | RDG pass / SVE / 셰이더 디스패치 | 🚨 최우선 — `RDG_EVENT_SCOPE` + `TRACE_*` 2중 |
| **Slate / UMG** | NativeTick / NativeOnPaint / ActiveTimer / FieldNotify | 🚨 최우선 — `SCOPED_NAMED_EVENT` |
| **Components** | Tick / TimerManager / OnRep_* / RPC | 🚨 최우선 |
| 사용자 인터랙션 (OnClicked) | 본체가 무거우면 | 🟡 권장 |
| 생성자 · 1회 초기화 | 의심 시 | 🟢 선택 |

## 6. 함정 (9대)

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | 람다에 스코프 없음 | 람다 = 익명 → 무조건 스코프 |
| 2 | `OnRep_*` 에 스코프 없음 | 클라이언트 임의 시점 → 첫 줄 |
| 3 | Super 보다 스코프 먼저 | Super FIRST → 스코프 (Super 비용은 베이스 자체 측정) |
| 4 | 동적 이름 `FString::Printf` 매 프레임 | 디버그 빌드만 또는 경량 사용 |
| 5 | 같은 이름 여러 위치 | Insights 합산 → 위치별 고유 이름 |
| 6 | `QUICK_SCOPE_CYCLE_COUNTER` 와 STAT 충돌 | 즉석 = `QUICK_*` / 정식 = `DECLARE_CYCLE_STAT` |
| 7 | `LLM_SCOPE` 와 CPU 스코프 혼동 | LLM = 메모리 / TRACE_CPU = 시간 |
| 8 | 너무 잘게 자른 스코프 | 매크로 자체 비용 (~ns) — 핫루프 내부 외부 1회 |
| 9 | `AddDynamic`/`AddUObject` 핸들러 미스코프 | 외부 호출 시점 모름 → 첫 줄 |

## 7. Insights / Stat 콘솔

| 명령 | 효과 |
| -- | -- |
| `stat unit` | Frame / Game / Draw / GPU |
| `stat gpu` | GPU pass 별 |
| `stat slate` / `stat slatedetailed` | Slate 그룹 / 세부 |
| `stat <Group>` | `DECLARE_CYCLE_STAT` 그룹 |
| `Trace.Start cpu,frame,gpu,slate` | Insights 트레이스 시작 |

**중요**: `TRACE_CPUPROFILER_EVENT_SCOPE` 는 **Insights 트레이스에만** 잡힘 (Stat 콘솔 X). `QUICK_SCOPE_CYCLE_COUNTER` 는 `stat <Group>` 으로 확인. `SCOPED_NAMED_EVENT` 는 외부 프로파일러 색상 강조용.

## 8. Cross-link

- 권위 concept: [[concepts/Profiling-Scope-Rule]]
- 자매 정책 hub: [[sources/ue-ref-10-componentpolicies]] §5 (Tick 정책) · [[sources/ue-ref-09-globaliteratorpolicy]] · [[sources/ue-ref-11-assetloadingpolicy]] · [[sources/ue-ref-12-assetoptimizationpolicy]]
- Super 호출 통합: [[sources/ue-ref-04-overrideindex]] §6 (Super + 스코프 순서)
- 4단 분리: [[sources/ue-ref-05-editoronlyindex]]
- 인밸리데이션 hotspot: [[sources/ue-ref-06-invalidationhotspots]] (스코프 부착 필수 위치 다수)
- UMG/Slate Tick 적용: [[sources/ue-umg-uuserwidget]] §4.1 · [[sources/ue-slatecore-swidget]] · [[sources/ue-slatecore-trace]] 🛠
- Render 2중 스코프: [[sources/ue-render-skill]] · [[sources/ue-render-rdg]] (RDG_EVENT_SCOPE)
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 label-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **label-only**. 5.5↔5.7 raw diff 가 버전 라벨 (5.7.4 ↔ 5.5.4 문자열) 변경만 — 본문 정합 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
