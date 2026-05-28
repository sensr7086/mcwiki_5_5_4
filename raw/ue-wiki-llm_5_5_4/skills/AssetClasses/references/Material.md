---
name: assetclasses-material
description: UMaterial (2,083) + UMaterialInstanceConstant + UMaterialInstanceDynamic + UMaterialInterface (1,278) - Domain 7종 + BlendMode 7종 + ShadingModel 12종 + 5.x PSO Precache.
---

# AssetClasses/Material — UMaterial + UMaterialInstance + UMaterialInterface

> **위치**: `Engine/Source/Runtime/Engine/Public/Materials/Material.h` (2,083) + `MaterialInstance.h` (1,177) + `MaterialInterface.h` (1,278) + `MaterialFunction.h` + `MaterialParameterCollection.h`
> **베이스**: `UMaterialInterface : public UObject` → `UMaterial` (베이스 머티리얼) / `UMaterialInstance` (인스턴스 — 파라미터 오버라이드) → `UMaterialInstanceConstant` (에디터) / `UMaterialInstanceDynamic` (런타임)
> **요지**: **모든 렌더링의 셰이더 진입점** — Mesh / Decal / PostProcess / UI / Light / Volume 모두 Material 사용. **PSO 컴파일 비용 + Shader Permutation 폭발이 가장 큰 성능 함정**.

---

## 🚨 공통 정책 (어셋 로드 + Shader Permutation)

| 정책 | Material 자산 적용 |
|------|------------------|
| 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) | Material 변경 시 **PSO 컴파일 발생** (Cooked 빌드 첫 표시 = 50~500ms 히칭). **TSoftObjectPtr<UMaterialInterface>` 표준** + Match Start `PreloadPrimaryAssets` + **5.x PSO Precache** (`r.PSOPrecaching=1`). MaterialInstance 가 Hard 참조 + 부모 Material Hard — 자동 함께 로드. |
| 🚨 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) | Material 멤버 = `UPROPERTY()` + `TObjectPtr<UMaterialInterface>` (Hard) 또는 `TSoftObjectPtr` (Soft). UMaterialInstanceDynamic = 런타임 NewObject — 컴포넌트가 GC 보호 (자동 OwnedComponent). |
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | PostLoad / Recompile / SetParameter* 첫 줄 스코프. |
| [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) | 🛠 Material Expression 트리 (`UMaterialExpression*`) 모두 Editor 전용. Cooked = `FMaterialResource` 만. |

---

## 1. 베이스 트리 (UMaterialInterface)

```
UObject
└── UMaterialInterface (1,278 lines — IBlendableInterface, IInterface_AssetUserData)
    ├── UMaterial (2,083 lines — 베이스 머티리얼, Material Editor 그래프)
    └── UMaterialInstance (1,177 lines — 파라미터 오버라이드 + Static Permutation)
        ├── UMaterialInstanceConstant (.uasset 자산 — 에디터에서 작성)
        └── UMaterialInstanceDynamic (런타임 동적 — `CreateAndSetMaterialInstanceDynamic` / `UMaterialInstanceDynamic::Create`)
```

> **계층 추적** — `MaterialInterface->GetMaterial()` 은 항상 베이스 `UMaterial` 반환 (자식 체인 따라가며).

---

## 2. UMaterial (베이스 머티리얼) — Material.h:419

### 2.1 핵심 필드 — Domain / BlendMode / ShadingModel

```cpp
class UMaterial : public UMaterialInterface
{
    // Material.h:453 — 머티리얼 용도 결정
    UPROPERTY(EditAnywhere, Category=Material, AssetRegistrySearchable)
    TEnumAsByte<EMaterialDomain> MaterialDomain;

    // Material.h:457 — 블렌드 방식
    UPROPERTY(EditAnywhere, Category=Material)
    TEnumAsByte<EBlendMode> BlendMode;

    // Material.h:482 — Lighting Model
    UPROPERTY(EditAnywhere, Category=Material)
    TEnumAsByte<EMaterialShadingModel> ShadingModel;

    // Material.h:532 — 양면 렌더링
    UPROPERTY(EditAnywhere, Category=Material)
    uint8 TwoSided : 1;

    // Material.h:667 — Skeletal Mesh 사용 (Static Switch 활성)
    UPROPERTY()
    uint8 bUsedWithSkeletalMesh : 1;

    // Material.h:709 — Niagara Mesh 파티클
    UPROPERTY()
    uint8 bUsedWithNiagaraMeshParticles : 1;

    // Material.h:719 — Static Lighting (Lightmap)
    UPROPERTY()
    uint8 bUsedWithStaticLighting : 1;
};
```

### 2.2 EMaterialDomain (Material.h:27 — 7종)

| Domain | 의미 | 페어 컴포넌트 |
|--------|------|------------|
| `MD_Surface` | 일반 표면 (Mesh) — 가장 흔함 | StaticMesh / SkeletalMesh / Decal (X) |
| `MD_DeferredDecal` | 데칼 — 표면에 투영 | DecalComponent |
| `MD_LightFunction` | Light 의 Mask | LightComponent (LightFunctionMaterial) |
| `MD_Volume` | Volumetric Cloud / Fog | VolumetricCloudComponent / ExpHeightFog |
| `MD_PostProcess` | Post Process Volume | PostProcessComponent / SceneCapture |
| `MD_UI` | UMG / Slate | UMG Image / Slate Brush |
| `MD_RuntimeVirtualTexture` | RVT (오픈 월드) | RuntimeVirtualTextureComponent |

### 2.3 EBlendMode

| BlendMode | 의미 | 사용 |
|-----------|------|------|
| `BLEND_Opaque` | 불투명 | 일반 표준 (가장 빠름) |
| `BLEND_Masked` | Alpha Test | 잎사귀 / 머리카락 / 울타리 (DepthSorting 필요 X) |
| `BLEND_Translucent` | 반투명 | 유리 / 물 (DepthSorting 비쌈) |
| `BLEND_Additive` | 가산 (라이트 강조) | 발광 / 발사 효과 / 폭발 |
| `BLEND_Modulate` | 곱하기 (어둡게) | 섀도우 / Decal |
| `BLEND_AlphaComposite` | Pre-multiplied Alpha | UI |
| `BLEND_AlphaHoldout` | Holdout (알파 채널만) | Compositing |

### 2.4 EMaterialShadingModel

| ShadingModel | 의미 |
|--------------|------|
| `MSM_Unlit` | Light 무시 (UI / Emissive only) |
| `MSM_DefaultLit` | 표준 PBR (가장 흔함) |
| `MSM_Subsurface` | SSS (피부·왁스) — 빠른 근사 |
| `MSM_PreintegratedSkin` | 사실적 피부 |
| `MSM_ClearCoat` | 도장 / 자동차 페인트 |
| `MSM_SubsurfaceProfile` | 사실적 SSS (Profile 지정) |
| `MSM_TwoSidedFoliage` | 잎사귀 (양면 SSS) |
| `MSM_Hair` | 머리카락 (anisotropic) |
| `MSM_Cloth` | 천 (Sheen) |
| `MSM_Eye` | 눈 (각막 Refraction) |
| `MSM_SingleLayerWater` | 단층 물 |
| `MSM_ThinTranslucent` | Thin Glass |

### 2.5 GetDefaultMaterial (Domain 별 기본)

```cpp
// Material.h:1388
static UMaterial* GetDefaultMaterial(EMaterialDomain Domain);

// 사용 — Material 이 nullptr 이면 Default 사용
UMaterialInterface* Mat = MeshComp->GetMaterial(0);
if (!Mat) Mat = UMaterial::GetDefaultMaterial(MD_Surface);
```

### 2.6 ForceRecompileForRendering (런타임 재컴파일 — 매우 비쌈)

```cpp
// Material.h:1335 — 셰이더 재컴파일 (수십 ms ~ 수 초)
ENGINE_API virtual void ForceRecompileForRendering(EMaterialShaderPrecompileMode CompileMode = EMaterialShaderPrecompileMode::Default) override;

// 게임 중 호출 금지 — 디버그 / 에디터 만
```

---

## 3. UMaterialInstance (인스턴스 — 파라미터 오버라이드) — MaterialInstance.h:587

### 3.1 핵심 — Parent + Static/Dynamic Parameters

```cpp
class UMaterialInstance : public UMaterialInterface
{
    // MaterialInstance.h:608 — 부모 Material (체인의 끝은 UMaterial)
    UPROPERTY(EditAnywhere)
    TObjectPtr<class UMaterialInterface> Parent;

    // MaterialInstance.h:571 — Static Parameters (셰이더 분기 — 컴파일 시 결정)
    FStaticParameterSet StaticParameters;

    // 런타임 파라미터 (Vector / Scalar / Texture)
    UPROPERTY(EditAnywhere)
    TArray<FScalarParameterValue> ScalarParameterValues;

    UPROPERTY(EditAnywhere)
    TArray<FVectorParameterValue> VectorParameterValues;

    UPROPERTY(EditAnywhere)
    TArray<FTextureParameterValue> TextureParameterValues;
};
```

### 3.2 UMaterialInstanceConstant (에디터 인스턴스)

> **`.uasset` 자산** — 디스크에 저장. 에디터에서 작성. 대부분의 Mesh Material 슬롯 = MIC.

```cpp
// 사용 — Mesh 의 Material 슬롯에 MIC 할당
StaticMeshComp->SetMaterial(0, LoadedMIC);

// MIC 의 Static Parameter 변경 = 새 Shader Permutation 컴파일 필요
// → 런타임 변경 매우 비쌈 → MID 사용 권장
```

### 3.3 UMaterialInstanceDynamic (런타임 동적)

> **런타임 생성** — Vector / Scalar / Texture 파라미터 동적 변경. **Static Parameter 변경 불가** (Permutation 그대로).

```cpp
// 표준 패턴 — Component 가 자동 GC 보호
UMaterialInstanceDynamic* MID = StaticMeshComp->CreateAndSetMaterialInstanceDynamic(/*ElementIndex=*/0);

// 또는 일반 NewObject
UMaterialInstanceDynamic* MID2 = UMaterialInstanceDynamic::Create(ParentMaterial, this);

// 파라미터 변경
MID->SetVectorParameterValue(TEXT("BaseColor"), FLinearColor::Red);
MID->SetScalarParameterValue(TEXT("DamageAmount"), 0.5f);
MID->SetTextureParameterValue(TEXT("Diffuse"), NewTexture);
```

### 3.4 MID 캐싱 패턴 (필수)

```cpp
// ❌ 안티패턴 — 매 프레임 MID 생성
void Tick()
{
    auto* MID = MeshComp->CreateAndSetMaterialInstanceDynamic(0);   // ⚠️ 매 프레임 새 인스턴스
    MID->SetScalarParameterValue(TEXT("Glow"), Time);
}

// ✅ 정답 — BeginPlay 에서 1회 생성 + 캐싱
UPROPERTY()
TObjectPtr<UMaterialInstanceDynamic> CachedMID;

void BeginPlay()
{
    Super::BeginPlay();
    CachedMID = MeshComp->CreateAndSetMaterialInstanceDynamic(0);
}

void Tick(float DT)
{
    Super::Tick(DT);
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyActor::Tick);
    if (CachedMID)
    {
        CachedMID->SetScalarParameterValue(TEXT("Glow"), Time);
    }
}
```

---

## 4. Material Function / Material Layer / Parameter Collection

### 4.1 UMaterialFunction (재사용 가능 노드 그래프)

```cpp
// Material 그래프 안 함수 호출
class UMaterialFunction : public UMaterialFunctionInterface
{
    UPROPERTY()
    TArray<TObjectPtr<UMaterialExpression>> FunctionExpressions;
};

// 사용 — Material 그래프에서 MaterialFunctionCall 노드로 호출
```

### 4.2 UMaterialParameterCollection (글로벌 파라미터)

> **여러 Material 이 공유하는 글로벌 값** — 게임 전역 색상 / 시간 / 날씨 등.

```cpp
// 자산 (.uasset) — Vector / Scalar 파라미터 정의
class UMaterialParameterCollection : public UObject
{
    TArray<FCollectionScalarParameter> ScalarParameters;
    TArray<FCollectionVectorParameter> VectorParameters;
};

// 런타임 사용 — 모든 Material 동시 갱신
UMaterialParameterCollection* MPC = LoadObject<...>(...);
UMaterialParameterCollectionInstance* MPCI = World->GetParameterCollectionInstance(MPC);
MPCI->SetScalarParameterValue(TEXT("DayNight"), 0.5f);   // 모든 Material 갱신
```

### 4.3 Material Layer / Layer Stack (5.x — 표준)

```cpp
// Material 안에서 Layer 스택 정의 (Substance Painter 같은 워크플로)
struct FMaterialLayersFunctions
{
    TArray<TObjectPtr<UMaterialFunctionInterface>> Layers;
    TArray<TObjectPtr<UMaterialFunctionInterface>> Blends;
};

// MaterialInterface.h:633 — Layer 조회
virtual bool GetMaterialLayers(FMaterialLayersFunctions& OutLayers, ...) const;
```

---

## 5. PSO Precache (5.x — 가장 중요한 최적화)

> **5.x PSO Precaching** — Shader Permutation 첫 사용 시 PSO 컴파일 (50~500ms 히칭). 사전 컴파일.

### 5.1 활성

```ini
; DefaultEngine.ini
[/Script/Engine.RendererSettings]
r.PSOPrecaching=1
r.PSOPrecache.GlobalShaders=1
r.PSOPrecache.Resources=1
r.PSOPrecache.ProxyMaterials=1
```

### 5.2 컴포넌트 측 자동

```cpp
// 5.x — Component RegisterComponent 시 자동으로 PSO Precache 트리거
// UPrimitiveComponent::OnComponentCreated → PrecachePSOs
```

### 5.3 수동 트리거 (Boss / 일회용)

```cpp
// 큰 캐릭터 / 보스 등장 직전 사전 컴파일
FPSOPrecacheParamsList PSOParamsList;
Material->CollectPSOPrecacheData(PrimitiveType, VertexFactoryType, /*OutParams=*/ PSOParamsList);
FMaterialPSOPrecacheRequestID RequestID = Material->PrecachePSOs(PSOParamsList);
```

---

## 6. UMaterialInterface — 파라미터 조회 API

### 6.1 Get* 시리즈 (조회)

```cpp
FLinearColor BaseColor;
Material->GetVectorParameterValue(TEXT("BaseColor"), BaseColor);

float Roughness;
Material->GetScalarParameterValue(TEXT("Roughness"), Roughness);

UTexture* DiffuseTex;
Material->GetTextureParameterValue(TEXT("Diffuse"), DiffuseTex);
```

### 6.2 GetUsedTextures (자산 검사)

```cpp
// 머티리얼이 사용하는 모든 Texture 조회
TArray<UTexture*> Textures;
Material->GetUsedTextures(Textures);
// → Texture Streaming 결정 / 메모리 검사
```

### 6.3 PostProcess / Decal Order

```cpp
// PostProcess Material 우선순위 (Material.h)
UPROPERTY(EditAnywhere)
int32 BlendableLocation;   // BL_BeforeTonemapping / BL_AfterTonemapping / etc

UPROPERTY(EditAnywhere)
int32 BlendablePriority;
```

---

## 7. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | 매 프레임 `CreateAndSetMaterialInstanceDynamic` | BeginPlay 에서 1회 + 캐싱 |
| 2 | `ForceRecompileForRendering` 게임 중 호출 | 수십 ms ~ 수 초 — 에디터 / 디버그 만 |
| 3 | UMaterial Static Parameter 변경 (런타임) | Static = 컴파일 시 — 변경 불가. Dynamic 파라미터만 |
| 4 | MID Static Permutation 변경 시도 | Permutation = MIC 만. Vector/Scalar/Texture 만 동적 |
| 5 | Constructor 안 `LoadObject<UMaterial>` | UPROPERTY EditAnywhere + BP 지정 또는 Soft |
| 6 | Material 변경 후 MeshComponent `MarkRenderStateDirty` 안 호출 | `SetMaterial` API 가 자동 — 직접 변경 시 의무 |
| 7 | bUsedWithSkeletalMesh 안 켜고 SkeletalMesh 에 사용 | Default Material 폴백 — Material 우클릭 "Used With" 체크 |
| 8 | PSO Precache 비활성 + Cooked 빌드 첫 표시 | 50~500ms 히칭 — `r.PSOPrecaching=1` 의무 |
| 9 | 🚨 `TObjectIterator<UMaterial>` | UAssetManager + Primary Asset Type ([`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md)) |
| 10 | 🚨 자주 사용 Material PreLoad 안 함 | Match Start `PreloadPrimaryAssets` ([`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md)) |

---

## 8. 체크리스트

- [ ] 멤버 = `TObjectPtr<UMaterialInterface>` (Hard) / `TSoftObjectPtr<UMaterialInterface>` (Soft·다수)
- [ ] Constructor 안 LoadObject 사용 안 함
- [ ] MID 사용 = BeginPlay 에서 1회 생성 + UPROPERTY 캐싱
- [ ] Material 의 "Used With" 플래그 (SkeletalMesh / Niagara / Static Lighting) 정확히 체크
- [ ] PSO Precache 활성 (`r.PSOPrecaching=1`)
- [ ] Static Parameter 변경 = MIC (런타임 X) / Dynamic 만 = MID
- [ ] Domain (Surface / Decal / PostProcess / UI) 정확히 사용
- [ ] BlendMode (Opaque / Masked / Translucent) 비용 검토 — Translucent = 비쌈
- [ ] 🚨 6대 정책 + 어셋 로드 정책
- [ ] Cooked Build (Development) `stat unit` 첫 표시 시 검증

---

## 9. 관련 sub-skill

- [`AssetClasses/SKILL.md`](../SKILL.md) — 메인 (페어 매트릭스)
- [`AssetClasses/Mesh`](../Mesh/SKILL.md) — Mesh 가 Material 슬롯 보유
- [`AssetClasses/Texture`](../Texture/SKILL.md) — Material 의 Texture 파라미터
- [`Components/MeshComponents`](../../Components/references/MeshComponents.md) — Material Slot 호스트
- [`Components/RenderingComponents`](../../Components/references/RenderingComponents.md) — Decal / PostProcess Material
- [`Components/LightComponents`](../../Components/references/LightComponents.md) — LightFunction Material
- 교차: 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) (PSO Precache + Material PreLoad) · 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) (Recompile 콜백)

---

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. **UMaterialInterface 1,385** (베이스 + GetMaterial / GetUsedTextures / GetMaterialLayers / GetMaterialResource) → **UMaterial 2,166** (Material Domain 7종 / BlendMode 7종 / ShadingModel 12종 / Used With 플래그 / Default Material / ForceRecompile) → **UMaterialInstance 1,256** (Parent / StaticParameters / Vector·Scalar·Texture 파라미터 / **MIC vs MID** + MID 캐싱 패턴). MaterialFunction / Material Layer Stack / **UMaterialParameterCollection** (글로벌 파라미터 + MPCI). **5.x PSO Precache** (`r.PSOPrecaching=1` + 자동 + 수동 트리거). 함정 10종 + 10단 체크리스트. |
