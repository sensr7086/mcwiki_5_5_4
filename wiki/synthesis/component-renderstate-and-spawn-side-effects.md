---
type: synthesis
title: "Component RenderState 갱신 패턴 + SpawnSystemAttached 부수 효과 + Tick Hook 매트릭스"
slug: component-renderstate-and-spawn-side-effects
created: 2026-05-12
last_updated: 2026-05-12
sources:
  - "[[sources/ue-components-primitivecomponent]]"
  - "[[sources/ue-components-meshcomponents]]"
  - "[[sources/ue-niagara-skill]]"
  - "[[sources/ue-render-rdg]]"
  - "[[sources/ue-render-meshdrawing]]"
entities:
  - "[[entities/UPrimitiveComponent]]"
  - "[[entities/UStaticMeshComponent]]"
  - "[[entities/USkeletalMeshComponent]]"
  - "[[entities/UNiagaraSystem]]"
concepts:
  - "[[concepts/Component-Lifecycle]]"
  - "[[concepts/Component-Policies-6]]"
  - "[[concepts/Profiling-Scope-Rule]]"
status: living
tags: [synthesis, kmcproject, renderstate, niagara, ticker, timer, sideeffects]
---

# Component RenderState 갱신 패턴 + SpawnSystemAttached 부수 효과 + Tick Hook 매트릭스

> **목적**: KMCProject 의 `UMCSoftStaticMeshComponent` 디버깅 (2026-05-12) 에서 `MarkRenderStateDirty` / `RecreateRenderState_Concurrent` / `SpawnSystemAttached` 의 호스트 영향 / `FTSTicker` vs `FTimerManager` 의 Editor 컨텍스트 동작이 vault 에 정리되지 않아 *추측 기반 수정* 이 반복된 사례의 정리. [[00_meta/06_VaultCitationRule]] 3-tier 엄격 적용.
>
> **자매 페이지**: [[synthesis/bp-scs-preview-viewport-lifecycle]] (BP 컴포넌트 뷰포트 lifecycle + Editor World tick).

## 1. Thesis

UE 5.x 컴포넌트의 RenderState 갱신은 **4 가지 패턴** — 각각 비용 / 동기-비동기 / Editor 컨텍스트 안전성이 다름:

| API | 무엇 | 비용 | Editor World Realtime OFF 안전? |
| -- | -- | -- | -- |
| `MarkRenderStateDirty()` | dirty 마크만, 다음 World tick 에 자동 recreate | 매우 가벼움 | ❌ — tick 없으면 정지 |
| `RecreateRenderState_Concurrent()` | GameThread 즉시 destroy + recreate | 보통 | ✅ — tick 무관 동기 |
| `ReregisterComponent()` | Unregister + Register 전체 사이클 | 무거움 | ✅ |
| `MarkRenderTransformDirty()` | Transform 만 갱신, RenderState 유지 | 매우 가벼움 | ❌ — tick 의존 |

추가로 — `SpawnSystemAttached` (NiagaraComponent attach) 가 호스트 컴포넌트에 *부수 효과* 가 있는지가 KMCProject 디버깅의 핵심 가설이었음. **🔴 미검증 가설** 로 분류.

지연 실행 hook 도 두 가지 — `FTimerManager` (World tick 의존) vs `FTSTicker` (Engine tick) — Editor 컨텍스트에서는 후자 권장.

## 2. 🟢 VAULT — 직접 확인된 사실

### 2.1 UStaticMeshComponent::SetStaticMesh 의 내부 동작

[[entities/UStaticMeshComponent]] / [[sources/ue-components-meshcomponents]]:

- `SetStaticMesh(NewMesh)` 가 NewMesh != 기존 일 때:
  - `InvalidateLightingCache()`
  - `Modify()` — Editor Undo / archetype dirty
  - `StaticMesh = NewMesh`
  - `MarkRenderStateDirty()` — 다음 tick 에 SceneProxy recreate

→ **🟢 자동 MarkRenderStateDirty** — 일반 컨텍스트에서는 추가 호출 불필요.

### 2.2 Niagara Pool / AutoRelease

[[sources/ue-niagara-skill]] §SpawnSystemAttached / §Pool:

- `ENCPoolMethod::AutoRelease` — 런타임 spawn 자동 풀 관리
- `ENCPoolMethod::None` — Editor preview 컨텍스트, Pool 우회
- `MCNiagaraSocketBindingHelpers::SpawnAllNow` 가 `WorldType == EditorPreview` → `Pool=None`, 그 외 → `Pool=AutoRelease` 분기 (KMCProject 코드 검증)

### 2.3 컴포넌트 Tick 정책

[[concepts/Component-Policies-6]] §5 / [[sources/ue-ref-10-componentpolicies]]:

- `PrimaryComponentTick.bCanEverTick = false` — Tick 미사용 컴포넌트 기본값
- Editor World 의 컴포넌트도 동일 규칙 — Tick 자체는 작동하지만 Editor pause 시 정지

### 2.4 Profiling Scope Rule

[[concepts/Profiling-Scope-Rule]] / [[sources/ue-ref-07-profilingscopeRule]]:

- 모든 진입점 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` 의무
- 지연된 lambda (Ticker / Timer) 안에도 적용

## 3. 🟡 PARTIAL — vault 근거 + 외삽

### 3.1 RenderState 갱신 API 가족

vault 의 [[sources/ue-components-primitivecomponent]] 에 *MarkRenderStateDirty* 만 일부 언급, 다른 API 는 정밀하지 않음.

- vault 근거: `MarkRenderStateDirty` 가 다음 tick 에 SceneProxy recreate 트리거 ([[sources/ue-components-primitivecomponent]] L?? — 정확한 라인 미검증)
- 외삽: `RecreateRenderState_Concurrent` 는 즉시 동기 destroy + recreate — 일반 UE 지식 + Engine source `ActorComponent.cpp`
- 외삽: `ReregisterComponent` = Unregister + Register 사이클 — `FComponentReregisterContext` 와 동등 — UE 표준

→ **🟡 결론**: 4 API 매트릭스는 *부분 검증 + 외삽 조합*. 후속 검증으로 Engine source 라인 인용 추가 필요.

### 3.2 Editor World 의 tick 동작

[[synthesis/bp-scs-preview-viewport-lifecycle]] §4.1 에서 다룬 내용과 동일 — 일반 UE 지식. 본 페이지에서는 *RenderState 측면* 만 추가:

- Editor World tick 정지 시 → `MarkRenderStateDirty` 후 SceneProxy recreate 안 됨 → viewport stale
- **이 경우 `RecreateRenderState_Concurrent` 호출이 동기 해결** — tick 무관 즉시 재생성

이번 KMCProject 디버깅에서 사용자 보고 *"메시가 안 보임"* 의 원인 가설 중 하나가 이 시나리오 (🔴 — 빌드 후 검증 대기).

## 4. 🔴 INFERRED — vault 미확인, 일반 지식 / 추론

### 4.1 SpawnSystemAttached 의 호스트 컴포넌트 부수 효과

**가설 (vault 미확인, 일반 UE 지식 일부)**:

`UNiagaraFunctionLibrary::SpawnSystemAttached` 가 새 `UNiagaraComponent` 를 호스트 컴포넌트에 `AttachToComponent` — 일반적으로 호스트 RenderState 에 부수 효과 없음. *자식 컴포넌트 등록은 부모 RenderState 와 분리* (UE 표준 attachment model).

다만:
- 호스트 컴포넌트가 *Attached children 변경* 콜백을 처리하면 `MarkRenderTransformDirty` 또는 `MarkRenderStateDirty` 자체 호출 가능 (커스텀 컴포넌트일 때)
- 일반 `UStaticMeshComponent` 는 이런 콜백 없음 → 부수 효과 없음 (추측)

이번 KMCProject 디버깅에서 *호스트 메시 stale* 의 직접 원인은 SpawnSystemAttached 가 아니라 **`ProcessAssetUserDataAfterMeshLoadedEditorSync` 자체가 반복 호출되어 매번 DeactivateAll + SpawnAllNow 사이클** 이 부수 효과를 누적시켰을 가능성 (🔴 가설).

**후속 검증 후보**:
- `UNiagaraFunctionLibrary::SpawnSystemAttached` 소스 (`NiagaraFunctionLibrary.cpp`) 직접 확인
- AttachToComponent 의 호스트 영향 검증 (`USceneComponent::AttachToComponent`)

### 4.2 FTSTicker vs FTimerManager 매트릭스

**일반 UE 5.x 지식 (vault 미확인)**:

| 항목 | `FTSTicker::GetCoreTicker()` | `UWorld::GetTimerManager()` |
| -- | -- | -- |
| Tick 위치 | Engine main loop | World tick group |
| World pause 영향 | ❌ 무관 | ✅ paused 시 정지 |
| Editor Realtime OFF | ✅ 동작 | ❌ 정지 가능 |
| Game World 시 | ✅ 동작 | ✅ 동작 |
| API | `AddTicker(FTickerDelegate, Delay)` | `SetTimerForNextTick`, `SetTimer(Handle, ...)` |
| Delegate 반환값 | `bool` — `false` = 1회, `true` = 계속 | 없음 (Handle 로 해제) |
| Editor-only hook 권장 | ✅ | ❌ |

이번 KMCProject 디버깅 (2026-05-12) — OnRegister 안에서 Niagara 처리를 지연할 때 *Editor World Realtime OFF 안전* 을 위해 `FTSTicker` 선택. 다만 *next-tick 지연 자체* 가 회귀 (메시 + Niagara 둘 다 안 보임) 를 일으킨 다른 원인 (무한 spawn/destroy) 으로 인해 효과 검증 미완.

**후속 검증 후보**:
- Editor World Realtime OFF 시 `FTimerManager` 실제 정지 여부 (Engine source `LevelTick.cpp` 또는 `UnrealEdEngine.cpp`)
- `FTSTicker` 의 Editor 컨텍스트 발화 빈도 측정

### 4.3 MarkRenderStateDirty 의 Editor World 동작 정밀

**일반 UE 5.x 지식 (vault 미검증)**:

`MarkRenderStateDirty` 는 컴포넌트의 `bRenderStateDirty = true` 마크 → 다음 `UActorComponent::DoDeferredRenderUpdates_Concurrent` 호출 시 SceneProxy recreate. 이 호출 위치:

- `UWorld::SendAllEndOfFrameUpdates` — 매 World tick 끝
- Editor World 가 tick 안 되면 호출 안 됨 — **🔴 stale 영구화 위험**

→ Editor Realtime OFF 컨텍스트에서 안전한 패턴 = **MarkRenderStateDirty + RecreateRenderState_Concurrent 페어 호출**:

```cpp
MarkRenderStateDirty();           // dirty 마크 (Game World 안전)
RecreateRenderState_Concurrent(); // Editor Realtime OFF 안전 — 즉시 동기 recreate
```

후자만 호출해도 충분하지만, 전자도 같이 호출하면 *외부 시스템이 dirty 마크 체크* 하는 경우에도 호환.

### 4.4 RecreateRenderState_Concurrent 의 안전성

**일반 UE 5.x 지식 (vault 미검증)**:

- 호출 조건: 컴포넌트가 `IsRegistered() == true`
- 호출 시점: GameThread 안 (RenderThread 동기 처리 자동)
- 내부 동작: SceneProxy destroy → CreateSceneProxy → 새 SceneProxy + RenderState 등록
- 비용: 메시 / 머티리얼 / Niagara 별로 다름. 일반적으로 ms 단위 — 빈번한 호출은 피해야

이번 KMCProject — 동일 메타 skip 가드 추가로 매 OnRegister 마다 호출되지 않게 처리 (2026-05-12). 정상 동작 시 사용자 인터랙션 (디테일 변경 / BP 컴파일) 당 1-2 회만 호출.

### 4.5 동일 메타 skip 가드 패턴

**KMCProject 디버깅에서 발견 (vault 미반영, 일반화 가능)**:

Editor preview 측 비동기 spawn / sync spawn 호출이 매 OnRegister 마다 반복되어 무한 spawn/destroy 사이클이 발생할 위험. 가드:

```cpp
// 동일 메타 + 모든 spawn 활성 → skip
if (NewBindings == CachedBindings
    && SpawnedComponents.Num() == NewBindings->Children.Num()
    && AllWeakPtrsValid(SpawnedComponents))
{
    return;
}
```

이 패턴은 *Editor preview 측 hook* 일반에 적용 가능 — UMCNiagaraSocketBindings 뿐 아니라 다른 AssetUserData 자손도 동일.

## 5. 적용 사례 — 2026-05-12 MCSoftStaticMesh 디버깅

| 시도 | API | 효과 | tier |
| -- | -- | -- | -- |
| `SetStaticMesh(Mesh)` 만 호출 | 기본 자동 MarkRenderStateDirty | Realtime OFF 컨텍스트 stale 가능 (가설) | 🔴 |
| 추가 `MarkRenderStateDirty()` 명시 | dirty 마크 강화 | Realtime ON 컨텍스트만 효과 | 🟡 |
| 추가 `RecreateRenderState_Concurrent()` | 동기 recreate | Realtime OFF 컨텍스트도 즉시 viewport 갱신 | 🟢 일반 UE 지식 일치 |
| `FTSTicker::GetCoreTicker().AddTicker` | next-tick 지연 | World pause 무관 발화 | 🟢 일반 UE 지식 일치 |
| 동일 메타 skip 가드 | 무한 spawn/destroy 깨기 | 호스트 RenderState stale 회피 | 🔴 가설, 검증 대기 |

→ 6 일자 23시 시점 빌드 후 사용자 확인 대기 (`§5 [2026-05-12] fix` log entries).

## 6. 후속 검증 / vault 편입 후보

🔴 → 🟢 승격 후보:

- [ ] §4.1 — `UNiagaraFunctionLibrary::SpawnSystemAttached` 호스트 영향 (Engine source 직접 확인)
- [ ] §4.2 — `FTSTicker` vs `FTimerManager` 실제 동작 (Engine source `Ticker.cpp` + `TimerManager.cpp`)
- [ ] §4.3 — `MarkRenderStateDirty` 의 `SendAllEndOfFrameUpdates` 호출 위치 (`World.cpp` 또는 `Renderer` 모듈)
- [ ] §4.4 — `RecreateRenderState_Concurrent` GameThread 동기 보장 (Engine source `ActorComponent.cpp`)
- [ ] §4.5 — 동일 메타 skip 가드 패턴이 다른 AssetUserData 자손 / Editor preview hook 에도 일반화 가능한지 검증

후속 작업으로 [[sources/ue-components-primitivecomponent]] / [[sources/ue-render-meshdrawing]] / [[sources/ue-niagara-skill]] 에 본 페이지 §4 내용을 검증된 형태로 보강. 또는 *neue* `sources/ue-render-componentrenderstate` 신설.

## 7. cross-link

### Sources

[[sources/ue-components-primitivecomponent]] · [[sources/ue-components-meshcomponents]] · [[sources/ue-niagara-skill]] · [[sources/ue-render-rdg]] · [[sources/ue-render-meshdrawing]] · [[sources/ue-render-sceneviewextension]]

### Entities

[[entities/UPrimitiveComponent]] · [[entities/UStaticMeshComponent]] · [[entities/USkeletalMeshComponent]] · [[entities/UNiagaraSystem]]

### Concepts

[[concepts/Component-Lifecycle]] · [[concepts/Component-Policies-6]] · [[concepts/Profiling-Scope-Rule]] · [[concepts/Editor-Only-4-Tier-Separation]]

### Related synthesis

[[synthesis/bp-scs-preview-viewport-lifecycle]] (BP 컴포넌트 뷰포트 lifecycle 자매 페이지) · [[synthesis/mc-soft-asset-component-pattern]] §7 (적용 사례) · [[synthesis/editor-preview-scene-runtime-handoff]] (Editor preview 와 런타임 분리)
