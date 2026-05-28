---
type: source
title: "UE Render — MeshDrawing sub-skill"
slug: ue-render-meshdrawing
source_path: raw/ue-wiki-llm/skills/Render/references/MeshDrawing.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-10
last_updated: 2026-05-12
related_entities:
  - "[[entities/UPrimitiveComponent]]"
related_concepts: []
tags: [ue, render, gpu, mesh, scene-proxy, vertex-factory, gpu-scene]
---

# UE Render — MeshDrawing

> Source: [[raw/ue-wiki-llm/skills/Render/references/MeshDrawing.md]]
> Parent: [[sources/ue-render-skill]] · Pair: [[sources/ue-render-shader]] · [[sources/ue-render-rdg]] · [[sources/ue-render-material]]

## §13 Citation tier

- 🟢 VAULT — §1~§5 의 모든 claim/코드/함정은 raw `skills/Render/references/MeshDrawing.md` (L1~L274) 에서 직접 인용.
- 🟡 PARTIAL — 없음 (slim 카드 범위 내 외삽 없음).
- 🔴 INFERRED — 보너스 발견 (§7) 의 "Phase II Nanite Vertex Factory 별도 노트 후보" 만. vault 미확정.

---

## §1 Summary

UE 5.x **Mesh Drawing 파이프라인** = `Component → FPrimitiveSceneProxy → FMeshBatch → FMeshPassProcessor → FMeshDrawCommand → GPU draw` 의 5축 흐름. 게임 스레드의 `UMeshComponent` 가 `CreateSceneProxy()` 로 Render Thread 측 `FPrimitiveSceneProxy` 를 생성 → Proxy 가 `GetDynamicMeshElements()` 에서 `FMeshBatch` 를 채워 `FMeshElementCollector` 에 제출 → Pass 별 `FMeshPassProcessor` 가 `AddMeshBatch()` 로 `FMeshDrawCommand` 를 생성·캐싱 → RHI 가 GPU draw 호출 (raw L23~L31, L86~L122). 5.x 부터 **GPU Scene** 통합으로 Per-Primitive Uniform 이 단일 GPU 버퍼로 일원화되며, Custom Vertex Factory 는 GPU Scene 호환이 의무 (Nanite 베이스, L152~L165).

## §2 Key claims (8)

1. **FMeshBatch = per-Mesh per-Frame 단일 그리기 단위** — `VertexFactory + MaterialRenderProxy + LCI + CastShadow + bUseAsOccluder` + `FMeshBatchElement` (IndexBuffer / PrimitiveUniformBuffer / FirstIndex / NumPrimitives / Min·MaxVertexIndex) 페어 의무 (raw L101~L117).
2. **FMeshPassProcessor = Pass 별 (Depth/GBuffer/Translucent/Velocity/Custom) 메시 명령 생성기** — `AddMeshBatch(MeshBatch, BatchElementMask, PrimitiveSceneProxy, StaticMeshId)` 가 표준 진입점. 5.x Custom Pass = `EMeshPass::Custom` (raw L128~L144).
3. **FPrimitiveSceneProxy = Component 의 Render Thread 표현** — `CreateSceneProxy()` 로 생성, 게임 스레드 데이터를 생성자에서 캐시. `GetTypeHash()` 오버라이드 의무 (자식 클래스마다 정적 변수 + `reinterpret_cast<size_t>`) — 누락 시 Pass 분류 오류 (raw L37~L82, L207~L214).
4. **FVertexFactory = 메시 데이터 layout** (Static / Skeletal / Procedural / Niagara / Custom). 5.x = Vertex Shader 안에서 GPU Scene 데이터를 읽으므로 Custom VF 시 GPU Scene 헬퍼 호출 의무 (raw L153~L165).
5. **FShaderMeshDeclaration / FMeshMaterialShader** — Mesh 파이프라인이 사용하는 Material Shader. [[sources/ue-render-shader]] §FMeshMaterialShader 와 페어 (raw L266).
6. **GetDynamicMeshElements (per-frame Dynamic Path)** — View 별 `VisibilityMap` bit 검사 → `Collector.AllocateMesh()` → `FMeshBatch` 채움 → `Collector.AddMesh(ViewIdx, Mesh)`. 매 프레임 호출 (raw L90~L121).
7. **Cached vs Dynamic Path** — Static Mesh = `FMeshDrawCommand` 가 자동 캐시 (Cached Mesh Draw Command Path), 변하지 않는 한 재사용. Dynamic Path = `GetDynamicMeshElements()` 매 프레임 (raw L23~L31 파이프라인 + L240의 LOD 별 분기).
8. **5.x GPU Scene 통합** — 모든 Primitive Transform/Material 이 GPU 단일 버퍼에 통합 → Per-Primitive CPU 명령 ↓. Nanite 는 GPU Scene 위에서 동작 → Legacy Vertex Factory + Nanite = 호환 불가 (raw L152~L165).

## §3 함정 (raw §6 → 5대 발췌)

1. SceneProxy 안 UObject 직접 접근 → 생성 시 Component → Proxy 데이터 캐싱 (raw L235).
2. 게임 스레드 → SceneProxy 직접 조작 → `ENQUEUE_RENDER_COMMAND` 큐잉 + `MarkRenderDynamicDataDirty()` (raw L236, L240).
3. `GetTypeHash` 누락 → Pass 분류 오류. 자식 클래스마다 정적 변수 + reinterpret_cast 의무 (raw L237).
4. 5.x Nanite + Legacy Vertex Factory → Nanite 비활성 또는 GPU Scene 호환 VF (raw L239).
5. `bAlwaysHasVelocity` 미지정 → Velocity Pass 누락 (raw L243).

## §4 코드 예 — SceneProxy 게임→Render Thread 데이터 큐잉 (raw §4.1)

```cpp
// UMyComponent::SendRenderDynamicData_Concurrent — 데이터 변경 시 Render Thread 갱신
virtual void SendRenderDynamicData_Concurrent() override
{
    Super::SendRenderDynamicData_Concurrent();
    if (SceneProxy)
    {
        FMyData NewData = GetData();
        ENQUEUE_RENDER_COMMAND(MyComponentUpdateData)(
            [SceneProxy = static_cast<FMySceneProxy*>(SceneProxy), NewData](FRHICommandList&)
            {
                SceneProxy->UpdateData_RenderThread(NewData);
            });
    }
}

// FMySceneProxy::UpdateData_RenderThread — Render Thread 측 갱신
void FMySceneProxy::UpdateData_RenderThread(const FMyData& NewData)
{
    check(IsInRenderingThread());
    CachedData = NewData;
}

// GetTypeHash — 자식 클래스마다 의무
virtual SIZE_T GetTypeHash() const override
{
    static size_t UniquePointer;
    return reinterpret_cast<size_t>(&UniquePointer);
}
```

## §5 Cross-link

- **Parent**: [[sources/ue-render-skill]] — 3축 스레드 분리 / 8 시나리오 / Build.cs 의존성
- **Pair**:
  - [[sources/ue-render-shader]] — FMeshMaterialShader / Permutation / `ShouldCompilePermutation`
  - [[sources/ue-render-rdg]] — Custom Mesh Pass 의 GraphBuilder 통합
  - [[sources/ue-render-material]] — `MaterialRenderProxy` (FMeshBatch 의 의무 필드)
- **Host**: [[entities/UPrimitiveComponent]] — `CreateSceneProxy()` 호출 주체. raw 의 `Components/references/MeshComponents.md` 및 `PrimitiveComponent.md §11+` 페어 (raw L264~L267)
- **5.x 신규**: [[sources/ue-render-lumennanite]] — Nanite Vertex Factory 호환 (raw L161, L239)

## §6 신뢰도 매트릭스

| 영역 | tier | 근거 |
|------|------|------|
| 파이프라인 5축 | 🟢 | raw L23~L31 다이어그램 + L86~L144 코드 |
| 8 Key claim 전체 | 🟢 | raw §2.1~§3.3 + §4 + §6 |
| GPU Scene + Nanite 비호환 | 🟢 | raw L153~L165, L239 |
| GetTypeHash 자식 의무 | 🟢 | raw L207~L214, L237 |
| Cached vs Dynamic Path 구분 | 🟢 | raw L23~L31 (파이프라인) + L244 (LOD) — 단 raw 가 명시적으로 "Cached" 용어를 쓰진 않음 (UE 표준 용어). 본문은 표준 용어로 정리 |
| 보너스 발견 (§7) | 🔴 | vault 미확정 — 별도 노트 후보로만 표시 |

---

## (Boundary) 보너스 발견

- **🔴 INFERRED — Nanite Vertex Factory 호환 검사 절차 별도 노트**: raw 가 "Legacy VF + Nanite = 호환 X" (L161, L239) 만 명시하고 *어떤 GPU Scene 헬퍼 함수* 가 Custom VF 의 Vertex Shader 에 들어가야 하는지 (예: `GetPrimitiveData()` / `GetInstanceData()` USF 매크로) 는 raw 내 미수록. [[sources/ue-render-lumennanite]] 와 [[sources/ue-render-shader]] §5 (USF / Permutation) 의 교차점 — Cycle #7+ 에서 *Nanite VF 호환 체크리스트* synthesis 후보.
- **🔴 INFERRED — `FCachedMeshDrawCommandInfo` / Cached Path 캐시 무효화 트리거 (Material 변경 / LOD 변경 / Visibility 변경) 별도 카드**: raw L23~L31 의 "자동 캐시" 한 줄 + L244 LOD 별 분기 외에 무효화 조건이 raw 본문엔 없음. Material PSO 캐시 ([[sources/ue-render-material]] §5) 와 페어로 *언제 Cached → Dynamic 으로 떨어지는가* 만 별도 작은 카드로 정리하면 Custom Renderer 디버깅 가치.
- **🟡 PARTIAL 후보 — `bAlwaysHasVelocity` (raw L243) 의 정확한 의미**: raw 는 "Velocity Pass 누락 방지" 한 줄. TSR / Motion Blur / Temporal Upscaler 와의 관계는 [[sources/ue-render-postprocess]] 와 교차 — 추후 PostProcess 카드 enrich 시 cross-link 보강.

---

## 변경 이력
- 2026-05-10 — slug stub (29 L).
- 2026-05-12 — Cycle #6 slim enrich. §13 tier + §1 Summary (5축 파이프라인) + §2 8 claims (FMeshBatch / FMeshPassProcessor / FPrimitiveSceneProxy / FVertexFactory / FShaderMeshDeclaration / GetDynamicMeshElements / Cached vs Dynamic / 5.x GPU Scene) + §3 함정 5대 + §4 코드 (게임→Render 큐잉 + GetTypeHash) + §5 cross-link (parent/pair/host/5.x) + §6 신뢰도 + 보너스 발견 3건 (Nanite VF 호환 / Cached Path 무효화 / bAlwaysHasVelocity).
