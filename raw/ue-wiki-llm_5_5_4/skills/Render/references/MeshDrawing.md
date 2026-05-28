---
name: render-meshdrawing
description: Mesh Drawing 파이프라인 — FMeshBatch + FMeshPassProcessor + FStaticMeshSceneProxy + FPrimitiveSceneInfo + Vertex Factory. Custom Mesh Renderer 작성 / Mesh Pass 추가 / GBuffer 출력 / Custom GPU 데이터 표준.
---

# Render/MeshDrawing — Mesh Pass + SceneProxy + Custom Renderer

> **위치**: `Engine/Source/Runtime/Renderer/Public/MeshPassProcessor.h` + `MeshMaterialShader.h` + `MeshDrawShaderBindings.h` + `PrimitiveSceneInfo.h`
> **요지**: Static / Skeletal Mesh 가 GPU 까지 전달되는 흐름 + Custom Mesh Renderer 작성 패턴.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 SceneProxy Lifetime | Component 라이프사이클과 동기 — `CreateSceneProxy()` / 자동 해제 |
| 🚨 Vertex Factory | 5.x = GPU Scene 통합 — Custom VF 시 호환 검사 |
| 🎯 [`12_AssetOptimizationPolicy.md`](../../../references/12_AssetOptimizationPolicy.md) §1 | Bone LOD + URO + Visibility Tick |

---

## 1. Mesh Drawing 파이프라인 (5축)

```
[Component]                  [SceneProxy]           [MeshPass]              [GPU]
UStaticMeshComponent         FStaticMeshSceneProxy  FStaticMeshPassProcessor
  ↓ CreateSceneProxy()         ↓ GetMeshElements      ↓ AddMesh
  Component → Proxy           FMeshBatch 생성        Mesh Draw Command       GPU draw
  (게임 스레드 → Render)       (per-frame)             (자동 캐시)
```

---

## 2. 4 핵심 클래스

### 2.1 FPrimitiveSceneProxy (가장 중요)

각 Component 의 Render 측 표현. Component → Proxy 데이터 단방향 전달.

```cpp
// MyMeshComponent.h
class UMyMeshComponent : public UMeshComponent
{
    GENERATED_BODY()

    // Render Thread 가 사용할 Proxy 생성
    virtual FPrimitiveSceneProxy* CreateSceneProxy() override;
};

// MyMeshComponent.cpp
FPrimitiveSceneProxy* UMyMeshComponent::CreateSceneProxy()
{
    return new FMyMeshSceneProxy(this);
}

// FMyMeshSceneProxy — Render Thread 측 Proxy
class FMyMeshSceneProxy : public FPrimitiveSceneProxy
{
public:
    FMyMeshSceneProxy(UMyMeshComponent* Component)
        : FPrimitiveSceneProxy(Component)
        , CachedData(Component->GetData())   // 게임 스레드에서 데이터 복사
    {
    }

    virtual SIZE_T GetTypeHash() const override
    {
        static size_t UniquePointer;
        return reinterpret_cast<size_t>(&UniquePointer);
    }

    // Mesh Element 생성 (per-frame)
    virtual void GetDynamicMeshElements(
        const TArray<const FSceneView*>& Views,
        const FSceneViewFamily& ViewFamily,
        uint32 VisibilityMap,
        FMeshElementCollector& Collector) const override;

private:
    FMyData CachedData;   // Render Thread 가 사용할 데이터
};
```

### 2.2 FMeshBatch (per-Mesh per-Frame)

각 메시 그리기 단위.

```cpp
void FMyMeshSceneProxy::GetDynamicMeshElements(
    const TArray<const FSceneView*>& Views,
    const FSceneViewFamily& ViewFamily,
    uint32 VisibilityMap,
    FMeshElementCollector& Collector) const
{
    for (int32 ViewIdx = 0; ViewIdx < Views.Num(); ViewIdx++)
    {
        if (VisibilityMap & (1 << ViewIdx))
        {
            // FMeshBatch 생성
            FMeshBatch& Mesh = Collector.AllocateMesh();
            Mesh.VertexFactory = MyVertexFactory.Get();
            Mesh.MaterialRenderProxy = MaterialProxy;
            Mesh.LCI = nullptr;
            Mesh.bCanApplyViewModeOverrides = false;
            Mesh.CastShadow = true;
            Mesh.bUseAsOccluder = true;

            // FMeshBatchElement
            FMeshBatchElement& BatchElement = Mesh.Elements[0];
            BatchElement.IndexBuffer = &MyIndexBuffer;
            BatchElement.PrimitiveUniformBuffer = GetUniformBuffer();
            BatchElement.FirstIndex = 0;
            BatchElement.NumPrimitives = NumTriangles;
            BatchElement.MinVertexIndex = 0;
            BatchElement.MaxVertexIndex = NumVertices - 1;

            Collector.AddMesh(ViewIdx, Mesh);
        }
    }
}
```

### 2.3 FMeshPassProcessor

각 Pass (Depth / GBuffer / Translucent) 의 메시 그리기 명령 생성.

```cpp
// MyMeshPassProcessor.h
class FMyMeshPassProcessor : public FMeshPassProcessor
{
public:
    FMyMeshPassProcessor(const FScene* InScene, const FSceneView* InView,
                         FMeshPassDrawListContext* InDrawListContext);

    virtual void AddMeshBatch(const FMeshBatch& MeshBatch,
                              uint64 BatchElementMask,
                              const FPrimitiveSceneProxy* PrimitiveSceneProxy,
                              int32 StaticMeshId = -1) override;
};

// 사용 — 새 Mesh Pass 정의 시
EMeshPass::Type CustomPass = EMeshPass::Custom;   // 5.x 표준 Pass
```

### 2.4 FPrimitiveSceneInfo

Render Scene 안 Primitive 1개 정보. Proxy 와 Pass Processor 사이 매개체.

---

## 3. 5.x GPU Scene 통합

### 3.1 정의

5.x = 모든 Primitive 의 Transform / Material 데이터를 **GPU 측 단일 버퍼** 에 통합. Per-Primitive CPU 명령 수 ↓.

### 3.2 영향
- Custom Vertex Factory = GPU Scene 호환 의무 (Vertex Shader 가 GPU Scene 데이터 읽음)
- Per-Primitive Uniform Buffer = 5.x 부터 GPU Scene 으로 자동
- Nanite = GPU Scene 위에서 동작 (호환 의무)

### 3.3 함정
- Legacy Vertex Factory + 5.x = Nanite 호환 X
- Custom VF + GPU Scene = Vertex Shader 안 GPUScene 함수 호출 의무

---

## 4. SceneProxy 표준 패턴 — Custom Render

### 4.1 게임 스레드 → Render Thread 데이터

```cpp
class UMyComponent : public UMeshComponent
{
    UPROPERTY()
    float Strength = 1.0f;

    // 데이터 변경 시 Render Thread 갱신
    virtual void SendRenderDynamicData_Concurrent() override
    {
        Super::SendRenderDynamicData_Concurrent();

        if (SceneProxy)
        {
            // 데이터 큐잉
            FMyData NewData = GetData();
            ENQUEUE_RENDER_COMMAND(MyComponentUpdateData)(
                [SceneProxy = static_cast<FMySceneProxy*>(SceneProxy), NewData](FRHICommandList&)
                {
                    SceneProxy->UpdateData_RenderThread(NewData);
                });
        }
    }
};

// Render Thread 측 갱신
void FMySceneProxy::UpdateData_RenderThread(const FMyData& NewData)
{
    check(IsInRenderingThread());
    CachedData = NewData;
}
```

### 4.2 GetTypeHash 의무

```cpp
virtual SIZE_T GetTypeHash() const override
{
    static size_t UniquePointer;
    return reinterpret_cast<size_t>(&UniquePointer);
}
// → 각 SceneProxy 자식 클래스마다 정적 변수 (고유 hash)
```

---

## 5. RuntimeVirtualTexture (5.x)

```cpp
// SceneProxy 가 RVT 출력
virtual void GetDynamicRayTracingInstances(
    FRayTracingMaterialGatheringContext& Context,
    TArray<FRayTracingInstance>& OutRayTracingInstances) override;

// RVT 사용 시 Material Domain = RuntimeVirtualTexture
```

---

## 6. 함정 & 안티패턴 (10대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | SceneProxy 안 UObject 직접 접근 | 데이터 캐싱 (생성 시 Component → Proxy 복사) |
| 2 | 게임 스레드에서 SceneProxy 직접 조작 | `ENQUEUE_RENDER_COMMAND` 큐잉 |
| 3 | GetTypeHash 누락 (각 자식 클래스) | 의무 — 정적 변수 + reinterpret_cast |
| 4 | FMeshBatch 누락 / 잘못된 VertexFactory | Vertex Factory + Material Proxy 페어 |
| 5 | 5.x Nanite + Legacy Vertex Factory | Nanite 비활성 또는 GPU Scene 호환 VF |
| 6 | Component 변경 → SendRenderDynamicData 누락 | `MarkRenderDynamicDataDirty()` 호출 |
| 7 | Proxy Lifetime — Component 파괴 후 Proxy 잔존 | 자동 해제 — but 큐잉된 명령은 IsValid 검사 |
| 8 | EMeshPass 잘못 지정 | Custom Pass = EMeshPass::Custom (5.x) |
| 9 | bAlwaysHasVelocity 미지정 → Velocity 누락 | Setup 시 의무 |
| 10 | 다수 LOD 간 Mesh Batch 중복 | LOD 별 분기 + StaticMeshId 정확 |

---

## 7. 체크리스트

- [ ] FPrimitiveSceneProxy 자손 + GetTypeHash 의무
- [ ] CreateSceneProxy() Component 측
- [ ] 게임 → Render 데이터 = ENQUEUE_RENDER_COMMAND 큐잉
- [ ] FMeshBatch + Vertex Factory + Material Proxy 페어
- [ ] 5.x GPU Scene 호환 (Custom VF 시)
- [ ] EMeshPass 정확
- [ ] SendRenderDynamicData_Concurrent 의무 (변경 시)
- [ ] LOD 별 Mesh Batch 분리

---

## 8. 관련

- [`Render/SKILL.md`](../SKILL.md) — 메인
- **호스트 페어**: [`Components/references/MeshComponents.md`](../../Components/references/MeshComponents.md) — UMeshComponent (CreateSceneProxy 호출)
- [`Render/references/Shader.md`](../Shader/SKILL.md) — FMeshMaterialShader
- [`Render/references/Material.md`](../Material/SKILL.md) — Material Proxy
- [`Components/references/PrimitiveComponent.md`](../../Components/references/PrimitiveComponent.md) §11+ — FPrimitiveSceneProxy 작성 패턴

## 9. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-08 | 최초 작성. Mesh Drawing 5축 파이프라인 + FMeshBatch / FMeshPassProcessor / FPrimitiveSceneProxy / 5.x GPU Scene + Custom Render 패턴 + 함정 10대. |
