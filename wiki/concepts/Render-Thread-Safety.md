---
type: concept
title: "Render Thread Safety (3축 분리 + GT↔RT 캐싱 다리)"
aliases: ["RT safety", "Render Thread access rules", "ENQUEUE_RENDER_COMMAND"]
sources:
  - "[[sources/ue-render-skill]]"
  - "[[sources/ue-render-sceneviewextension]]"
  - "[[sources/ue-render-rdg]]"
  - "[[sources/ue-render-rhi]]"
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [render, gpu, render-thread, threading, sve, rdg]
last_updated: 2026-05-13
---

# Render Thread Safety

## 정의

UE 5.x 의 **3축 스레드 분리** — Game Thread (GT) / Render Thread (RT) / RHI Thread — 사이의 *데이터 흐름 안전성 규약*. Render 작업의 *유일한* race-free 기반.

```
GT (게임 로직 + UObject) → RT (Proxy 데이터 복사 + RDG 빌드) → RHI Thread (Command 실행)
```

각 스레드는 *자기 데이터만* 직접 접근. 경계 횡단 = 명시적 캐싱 다리.

## 핵심 규약

### 1. RT 안에서 UObject 직접 접근 금지

```cpp
// ❌ WRONG — RT 에서 GT 의 UObject 접근
void FMySVE::PrePostProcessPass_RenderThread(...)
{
    if (Owner->IsActorTickEnabled()) { ... }  // GT 의 AActor 접근 = race
}

// ✅ RIGHT — SetupView 에서 GT 의 데이터 캐싱
void FMySVE::SetupView(FSceneViewFamily&, FSceneView&) { CachedFlag = Owner->IsActorTickEnabled(); }
void FMySVE::PrePostProcessPass_RenderThread(...) { if (CachedFlag) { ... } }
```

### 2. ENQUEUE_RENDER_COMMAND — GT → RT 큐잉

```cpp
// GT 측에서 RT 작업 큐잉
ENQUEUE_RENDER_COMMAND(MyCommand)(
    [Param](FRHICommandListImmediate& RHICmdList)
    {
        // RT 안 실행 — Param 은 캡처 시점에 복사 (안전)
    });
```

### 3. RDG = GT → RT 의 5.x 권장 경로

RDG Pass 가 자동 GT→RT 분리 → ENQUEUE_RENDER_COMMAND 직접 사용 줄어듦. `FRDGBuilder` 자체는 RT 안에서만 사용.

### 4. RHI Thread 는 RT 가 통제

RT 에서 `FRHICommandList` 큐잉 → RHI Thread 가 실제 GPU 명령 실행. 직접 RHI Thread 접근 금지.

## SVE 의 다리 패턴

[[sources/ue-render-sceneviewextension]] 의 `SetupView` Hook 이 **GT→RT 캐싱 다리** 의 표준 — RT 진입 *전* GT 데이터 복사 → RT 후크에서 cached 값만 사용.

## 함정

- ❌ RT 후크 안 `UObject->GetX()` — race / dangling
- ❌ TArray 등 GT 컨테이너 mutation 중 RT 가 read → 비결정
- ❌ FString GT 캡처 후 RT 에서 사용 — refcount race 가능 (대신 FName 또는 ANSI literal)
- ✅ Plain struct / POD 만 RT 캡처
- ✅ TWeakObjectPtr 캡처 → RT 안 `.IsValid()` 검사 (단 .Get() 호출은 GT 만)

## Cross-link

- 권위 source: [[sources/ue-render-sceneviewextension]] §2 (SetupView 캐싱 다리)
- 페어: [[sources/ue-render-rdg]] (Pass Lambda 캡처 규약) · [[sources/ue-render-rhi]] (RHI Thread)
- 정책: [[concepts/Profiling-Scope-Rule]] (`RDG_EVENT_SCOPE` 의무)
