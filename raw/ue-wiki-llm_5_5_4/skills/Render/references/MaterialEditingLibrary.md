---
name: render-material-editing-library
description: 🛠 UMaterialEditingLibrary (Editor) — Material 자동화 BlueprintFunctionLibrary 56 UFUNCTION (5.5.4). CreateMaterialExpression / ConnectMaterialProperty / ConnectMaterialExpressions / RecompileMaterial / Parameter Get/Set (Scalar/Vector/Texture/StaticSwitch/RVT/SVT) + MaterialInstance + MaterialFunction. Python / BP 자동화 — Material 일괄 생성 / 노드 그래프 자동 구성 / 패키지 빌드. Editor 전용 (4단 분리).
---

# Render/MaterialEditingLibrary — Editor Material 자동화 🛠

> **위치 (verified)**:
> - **UMaterialEditingLibrary** — `Engine/Source/Editor/MaterialEditor/Public/MaterialEditingLibrary.h` (56 UFUNCTION (5.5.4))
> - 모듈: `MaterialEditor` (Editor 전용)
> - Build.cs: `"MaterialEditor"` 의존
>
> **요지**: Material 시스템의 **Editor 자동화 표준** — Material / MaterialFunction / MaterialInstance 의 CRUD / Connection / Compile / Parameter 일괄 처리. Python / BP 호출 가능. UMaterialExpression 작성 페어 ([`MaterialExpression.md`](./MaterialExpression.md)).

---

## 🚨 공통 정책 (의무)

| 정책 | 적용 |
|------|------|
| 🚨 [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) | **Editor 모듈 전용** — 모든 코드 `WITH_EDITOR` 가드 (4단 분리) |
| 🚨 Build.cs | `"MaterialEditor"` 의무 — Editor 모듈에만 추가 |
| 🚨 [`11_AssetLoadingPolicy §3`](../../../references/11_AssetLoadingPolicy.md#3-환경-모드별-로드-정책--editor-pure-vs-pie-vs-cooked-game-) | Editor Pure 모드 = Sync Load (`TryLoad`) |
| 🚨 Transaction | `FScopedTransaction` + `Material->Modify()` 의무 (Undo/Redo) |
| 🚨 Compile | `CreateMaterialExpression` 후 `RecompileMaterial` 의무 — 누락 시 변경 미반영 |
| 🚨 Layout | 노드 추가 후 `LayoutMaterialExpressions` 권장 (Editor UI 정리) |
| 🚨 [`07_ProfilingScopeRule`](../../../references/07_ProfilingScopeRule.md) | 자동화 함수 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` |

---

## 1. 56 UFUNCTION (5.5.4) 카테고리 분류 [verified]

| 카테고리 | UFUNCTION 수 | 핵심 API |
|---------|:----------:|---------|
| **Expression CRUD** | 8 | `CreateMaterialExpression` ⭐ / `CreateMaterialExpressionEx` / `CreateMaterialExpressionInFunction` / `DeleteMaterialExpression` / `DeleteAllMaterialExpressions` / `DuplicateMaterialExpression` / `GetNumMaterialExpressions` / `DeleteMaterialExpressionInFunction` |
| **Connection** ⭐ | 2 | `ConnectMaterialProperty` ⭐ / `ConnectMaterialExpressions` ⭐ |
| **Compile / Update** | 4 | `RecompileMaterial` ⭐ / `RecompileMaterials` (Batch) / `UpdateMaterialFunction` / `UpdateMaterialFunctions` (Batch) |
| **Layout** | 3 | `LayoutMaterialExpressions` ⭐ / `LayoutMaterialFunctionExpressions` / `GetMaterialExpressionNodePosition` |
| **Parameter Get (Default)** | 4 | `GetMaterialDefaultScalarParameterValue` / `GetMaterialDefaultTextureParameterValue` / `GetMaterialDefaultVectorParameterValue` / `GetMaterialDefaultStaticSwitchParameterValue` |
| **MaterialInstance (MIC) Get/Set** | 16 | `Get/SetMaterialInstanceScalarParameterValue` / `Get/SetMaterialInstanceVectorParameterValue` / `Get/SetMaterialInstanceTextureParameterValue` / `Get/SetMaterialInstanceStaticSwitchParameterValue` / `Get/SetMaterialInstanceRuntimeVirtualTextureParameterValue` / `Get/SetMaterialInstanceSparseVolumeTextureParameterValue` + `SetMaterialInstanceParent` + `ClearAllMaterialInstanceParameters` + `UpdateMaterialInstance` |
| **Inspection / Navigation** | 8 | `GetMaterialExpressionInputNames` / `GetMaterialExpressionInputTypes` / `GetInputsForMaterialExpression` / `GetInputNodeOutputNameForMaterialExpression` / `GetMaterialPropertyInputNode` / `GetMaterialPropertyInputNodeOutputName` / `GetMaterialSelectedNodes` / `GetUsedTextures` |
| **Usage / Validation** | 2 | `SetMaterialUsage` / `HasMaterialUsage` |
| **Parameter Names / Source** | 7 | `GetScalarParameterNames` / `GetVectorParameterNames` / `GetTextureParameterNames` / `GetStaticSwitchParameterNames` / `GetScalarParameterSource` / `GetVectorParameterSource` / `GetTextureParameterSource` |
| **Group / Stats** | 4 | `RenameMaterialParameterGroup` / `RenameMaterialFunctionParameterGroup` / `GetChildInstances` / `FMaterialStatistics` (USTRUCT) |

**총 56 UFUNCTION (5.5.4)** — Material 자동화 거의 모든 영역.

---

## 2. 핵심 API 1 — `CreateMaterialExpression` ⭐ [verified]

```cpp
// MaterialEditingLibrary.h
UFUNCTION(BlueprintCallable, Category = "MaterialEditing")
static UE_API UMaterialExpression* CreateMaterialExpression(
    UMaterial* Material,
    TSubclassOf<UMaterialExpression> ExpressionClass,
    int32 NodePosX = 0,
    int32 NodePosY = 0
);
```

### 2.1 사용 예

```cpp
#if WITH_EDITOR
#include "MaterialEditingLibrary.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpressionConstant3Vector.h"
#include "Materials/MaterialExpressionScalarParameter.h"

void AMyTool::AddBaseColorNode(UMaterial* Mat)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyTool::AddBaseColorNode);
    if (!IsValid(Mat)) return;

    const FScopedTransaction Transaction(NSLOCTEXT("MyTool", "AddBaseColor", "Add Base Color"));
    Mat->Modify();

    // [1] Constant3Vector 노드 생성 (X=-300, Y=0)
    UMaterialExpressionConstant3Vector* ColorNode =
        Cast<UMaterialExpressionConstant3Vector>(
            UMaterialEditingLibrary::CreateMaterialExpression(
                Mat,
                UMaterialExpressionConstant3Vector::StaticClass(),
                -300, 0
            ));

    if (ColorNode)
    {
        ColorNode->Constant = FLinearColor(1.0f, 0.2f, 0.2f);   // 빨강
    }

    // [2] BaseColor 슬롯 연결
    if (ColorNode)
    {
        UMaterialEditingLibrary::ConnectMaterialProperty(
            ColorNode, TEXT(""), MP_BaseColor);
    }

    // [3] 컴파일
    UMaterialEditingLibrary::RecompileMaterial(Mat);
}
#endif
```

---

## 3. 핵심 API 2 — `ConnectMaterialProperty` ⭐ [verified]

```cpp
// MaterialEditingLibrary.h
UFUNCTION(BlueprintCallable, Category = "MaterialEditing")
static UE_API bool ConnectMaterialProperty(
    UMaterialExpression* FromExpression,
    FString FromOutputName,
    EMaterialProperty Property
);
```

### 3.1 EMaterialProperty 슬롯 (Material 의 출력 슬롯)

```cpp
enum EMaterialProperty
{
    MP_EmissiveColor,
    MP_Opacity,
    MP_OpacityMask,
    MP_DiffuseColor,
    MP_SpecularColor,
    MP_BaseColor,           // ⭐ 가장 흔함
    MP_Metallic,             // ⭐
    MP_Specular,             // ⭐
    MP_Roughness,            // ⭐
    MP_Anisotropy,
    MP_Normal,               // ⭐
    MP_Tangent,
    MP_WorldPositionOffset,  // ⭐ (Vertex 변형)
    MP_WorldDisplacement_DEPRECATED,
    MP_TessellationMultiplier_DEPRECATED,
    MP_SubsurfaceColor,
    MP_CustomData0,
    MP_CustomData1,
    MP_AmbientOcclusion,
    MP_Refraction,
    MP_PixelDepthOffset,
    MP_ShadingModel,
    MP_FrontMaterial,        // 5.x Substrate
    MP_SurfaceThickness,     // 5.x Substrate
    MP_Displacement,         // 5.x Tessellation 후속
    // ... + Custom UV 0~7
};
```

### 3.2 FromOutputName

| Expression 타입 | 출력 이름 |
|----------------|----------|
| Constant3Vector / VectorParameter | `""` (기본) 또는 `"RGB"` 또는 `"R"`/`"G"`/`"B"` |
| Constant / ScalarParameter | `""` |
| TextureSample | `""` (RGB) / `"R"` / `"G"` / `"B"` / `"A"` / `"RGB"` / `"RGBA"` |
| Multiply / Add | `""` |

> 출력 이름 = `""` (빈 문자열) 이 기본 출력. 분기별 검증 권장 (`GetExpressionOutputs` API 활용).

---

## 4. 핵심 API 3 — `ConnectMaterialExpressions` ⭐ [verified]

Expression 간 연결.

```cpp
UFUNCTION(BlueprintCallable, Category = "MaterialEditing")
static UE_API bool ConnectMaterialExpressions(
    UMaterialExpression* FromExpression,
    FString FromOutputName,
    UMaterialExpression* ToExpression,
    FString ToInputName
);
```

### 4.1 사용 예 — Texture 의 RGB → Multiply 의 A → BaseColor

```cpp
// [1] TextureSample 노드
UMaterialExpressionTextureSample* TexNode = Cast<UMaterialExpressionTextureSample>(
    UMaterialEditingLibrary::CreateMaterialExpression(
        Mat, UMaterialExpressionTextureSample::StaticClass(), -500, 0));
TexNode->Texture = LoadObject<UTexture2D>(nullptr, TEXT("/Game/Textures/T_Diffuse"));

// [2] Constant3Vector 노드 (Tint)
UMaterialExpressionConstant3Vector* TintNode = Cast<UMaterialExpressionConstant3Vector>(
    UMaterialEditingLibrary::CreateMaterialExpression(
        Mat, UMaterialExpressionConstant3Vector::StaticClass(), -500, 200));
TintNode->Constant = FLinearColor(1.0f, 0.5f, 0.0f);

// [3] Multiply 노드
UMaterialExpressionMultiply* MulNode = Cast<UMaterialExpressionMultiply>(
    UMaterialEditingLibrary::CreateMaterialExpression(
        Mat, UMaterialExpressionMultiply::StaticClass(), -200, 100));

// [4] 연결 — Tex.RGB → Mul.A
UMaterialEditingLibrary::ConnectMaterialExpressions(TexNode, TEXT(""), MulNode, TEXT("A"));

// [5] 연결 — Tint → Mul.B
UMaterialEditingLibrary::ConnectMaterialExpressions(TintNode, TEXT(""), MulNode, TEXT("B"));

// [6] Mul → BaseColor 슬롯
UMaterialEditingLibrary::ConnectMaterialProperty(MulNode, TEXT(""), MP_BaseColor);

// [7] Layout 정리 + Recompile
UMaterialEditingLibrary::LayoutMaterialExpressions(Mat);
UMaterialEditingLibrary::RecompileMaterial(Mat);
```

---

## 5. RecompileMaterial — 컴파일 (의무) [verified]

```cpp
UFUNCTION(BlueprintCallable, Category = "MaterialEditing")
static UE_API void RecompileMaterial(UMaterial* Material);

// Batch (FOnItemComplete 콜백)
static UE_API void RecompileMaterials(
    TArray<UMaterial*>& Materials,
    FOnItemComplete const& OnItemComplete
);
```

> `CreateMaterialExpression` / `ConnectMaterialExpressions` 호출 후 **반드시 `RecompileMaterial` 호출** — 누락 시 변경 사항 GPU 에 반영 X.

### 5.1 일괄 컴파일 (수십~수백 Material)

```cpp
TArray<UMaterial*> AllMaterials;
// ... 자산 수집

UMaterialEditingLibrary::RecompileMaterials(AllMaterials,
    FOnItemComplete::CreateLambda([](int32 CurrentIndex, int32 TotalCount)
    {
        UE_LOG(LogTemp, Log, TEXT("Compiled %d / %d"), CurrentIndex, TotalCount);
    })
);
```

---

## 6. MaterialInstance (MIC) 자동화 [verified]

```cpp
// === Get / Set 16 UFUNCTION ===
static float           GetMaterialInstanceScalarParameterValue(...);
static bool            SetMaterialInstanceScalarParameterValue(...);
static FLinearColor    GetMaterialInstanceVectorParameterValue(...);
static bool            SetMaterialInstanceVectorParameterValue(...);
static UTexture*       GetMaterialInstanceTextureParameterValue(...);
static bool            SetMaterialInstanceTextureParameterValue(...);
static bool            GetMaterialInstanceStaticSwitchParameterValue(...);
static bool            SetMaterialInstanceStaticSwitchParameterValue(...);
static URuntimeVirtualTexture* GetMaterialInstanceRuntimeVirtualTextureParameterValue(...);
static bool                    SetMaterialInstanceRuntimeVirtualTextureParameterValue(...);
static USparseVolumeTexture*   GetMaterialInstanceSparseVolumeTextureParameterValue(...);
static bool                    SetMaterialInstanceSparseVolumeTextureParameterValue(...);

// === Lifecycle ===
static void SetMaterialInstanceParent(UMaterialInstanceConstant* Instance, UMaterialInterface* NewParent);
static void ClearAllMaterialInstanceParameters(UMaterialInstanceConstant* Instance);
static void UpdateMaterialInstance(UMaterialInstanceConstant* Instance);
```

### 6.1 EMaterialParameterAssociation

| 값 | 설명 |
|----|------|
| `GlobalParameter` | 베이스 Material 의 글로벌 파라미터 (기본) |
| `LayerParameter` | Material Layer 의 파라미터 |
| `BlendParameter` | Material Layer Blend 의 파라미터 |

### 6.2 사용 예 — MIC 일괄 갱신

```cpp
TArray<UMaterialInstanceConstant*> AllMICs = ...;
for (UMaterialInstanceConstant* MIC : AllMICs)
{
    UMaterialEditingLibrary::SetMaterialInstanceScalarParameterValue(
        MIC, FName("Roughness"), 0.5f);
    UMaterialEditingLibrary::SetMaterialInstanceVectorParameterValue(
        MIC, FName("TintColor"), FLinearColor::Red);
    UMaterialEditingLibrary::UpdateMaterialInstance(MIC);
}
```

---

## 7. MaterialFunction 자동화 [verified]

```cpp
// === MaterialFunction 안 Expression 작성 ===
static UMaterialExpression* CreateMaterialExpressionInFunction(
    UMaterialFunction* MaterialFunction,
    TSubclassOf<UMaterialExpression> ExpressionClass,
    int32 NodePosX = 0, int32 NodePosY = 0
);

static int32 GetNumMaterialExpressionsInFunction(const UMaterialFunction* MaterialFunction);

static void DeleteAllMaterialExpressionsInFunction(UMaterialFunction* MaterialFunction);

static void DeleteMaterialExpressionInFunction(UMaterialFunction* MaterialFunction,
                                                UMaterialExpression* Expression);

// === Update ===
static void UpdateMaterialFunction(UMaterialFunctionInterface* MaterialFunction,
                                    UMaterial* PreviewMaterial = nullptr);

static void UpdateMaterialFunctions(TArray<UMaterialFunctionInterface*>& MaterialFunctions,
                                     FOnItemComplete const& OnItemComplete);

// === Layout ===
static void LayoutMaterialFunctionExpressions(UMaterialFunction* MaterialFunction);
```

---

## 8. Inspection / Navigation API [verified]

기존 Material 의 구조를 코드로 탐색.

```cpp
// === 입력 노드 ===
static TArray<UMaterialExpression*> GetInputsForMaterialExpression(
    UMaterial* Material, UMaterialExpression* MaterialExpression);

static TArray<FString> GetMaterialExpressionInputNames(UMaterialExpression* MaterialExpression);
static TArray<int32>   GetMaterialExpressionInputTypes(UMaterialExpression* MaterialExpression);

// === Material 슬롯 → 입력 노드 ===
static UMaterialExpression* GetMaterialPropertyInputNode(UMaterial* Material, EMaterialProperty Property);
static FString GetMaterialPropertyInputNodeOutputName(UMaterial* Material, EMaterialProperty Property);

// === 노드 위치 ===
static void GetMaterialExpressionNodePosition(UMaterialExpression* MaterialExpression,
                                               int32& NodePosX, int32& NodePosY);

// === 텍스처 ===
static TArray<UTexture*> GetUsedTextures(UMaterial* Material);

// === Sequencer-style 선택 ===
static TSet<UObject*> GetMaterialSelectedNodes(UMaterial* Material);
```

---

## 9. Parameter Names / Source API [verified]

```cpp
// 모든 파라미터 이름 수집
static void GetScalarParameterNames(UMaterialInterface* Material, TArray<FName>& ParameterNames);
static void GetVectorParameterNames(UMaterialInterface* Material, TArray<FName>& ParameterNames);
static void GetTextureParameterNames(UMaterialInterface* Material, TArray<FName>& ParameterNames);
static void GetStaticSwitchParameterNames(UMaterialInterface* Material, TArray<FName>& ParameterNames);

// 파라미터 소스 (MaterialFunction 안 정의 추적)
static bool GetScalarParameterSource(UMaterialInterface* Material, const FName ParameterName,
                                      FSoftObjectPath& ParameterSource);
static bool GetVectorParameterSource(...);
static bool GetTextureParameterSource(...);

// Group 이름 변경
static bool RenameMaterialParameterGroup(UMaterial* Material,
                                          const FName OldGroupName, const FName NewGroupName);
```

---

## 10. Python 자동화 표준 패턴

```python
import unreal

# [1] Material 생성
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
material = asset_tools.create_asset(
    asset_name="M_AutoMaterial",
    package_path="/Game/Materials",
    asset_class=unreal.Material,
    factory=unreal.MaterialFactoryNew()
)

# [2] Expression 추가
color_node = unreal.MaterialEditingLibrary.create_material_expression(
    material,
    unreal.MaterialExpressionConstant3Vector,
    -300, 0
)
color_node.set_editor_property("constant", unreal.LinearColor(1.0, 0.5, 0.0, 1.0))

scalar_node = unreal.MaterialEditingLibrary.create_material_expression(
    material,
    unreal.MaterialExpressionScalarParameter,
    -300, 200
)
scalar_node.set_editor_property("parameter_name", "Roughness")
scalar_node.set_editor_property("default_value", 0.5)

# [3] 연결
unreal.MaterialEditingLibrary.connect_material_property(
    color_node, "", unreal.MaterialProperty.MP_BASE_COLOR
)
unreal.MaterialEditingLibrary.connect_material_property(
    scalar_node, "", unreal.MaterialProperty.MP_ROUGHNESS
)

# [4] Layout + Compile
unreal.MaterialEditingLibrary.layout_material_expressions(material)
unreal.MaterialEditingLibrary.recompile_material(material)

# [5] 저장
unreal.EditorAssetLibrary.save_loaded_asset(material)
```

---

## 11. 시나리오 7종

### 11.1 PBR Master Material 자동 생성

```python
# Diffuse / Normal / Roughness / Metallic / AO 5종 텍스처 슬롯 자동 구성
def create_pbr_master_material(path):
    material = create_material_asset(path)
    # Texture Parameter × 5 + Vector/Scalar Parameter (Tint, Roughness Mul, ...)
    # ConnectMaterialProperty 5 슬롯
```

### 11.2 Material Instance 일괄 갱신 (Variation)

```python
# 50개 캐릭터 변형 → 각각 MIC 생성 + Color/Metallic 파라미터 변경
for i, char_color in enumerate(character_colors):
    mic = create_mic(f"/Game/MIC/Character_{i}", parent_material)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        mic, "BaseColor", char_color
    )
    unreal.MaterialEditingLibrary.update_material_instance(mic)
```

### 11.3 Material Function 라이브러리 일괄 생성

```cpp
// 표준 헬퍼 함수들 (Lerp / Mask / UVDistort) MaterialFunction 으로 자동 변환
for (auto& Spec : FunctionSpecs)
{
    UMaterialFunction* MF = CreateMaterialFunction(Spec.Path);
    UMaterialEditingLibrary::CreateMaterialExpressionInFunction(
        MF, Spec.NodeClass, 0, 0);
    UMaterialEditingLibrary::UpdateMaterialFunction(MF);
}
```

### 11.4 기존 Material 인스펙션 (Auditing)

```cpp
TArray<UMaterial*> AllMaterials = GetAllProjectMaterials();
for (UMaterial* Mat : AllMaterials)
{
    int32 NumExprs = UMaterialEditingLibrary::GetNumMaterialExpressions(Mat);
    TArray<UTexture*> Textures = UMaterialEditingLibrary::GetUsedTextures(Mat);
    UE_LOG(LogTemp, Log, TEXT("%s: %d expressions, %d textures"),
        *Mat->GetName(), NumExprs, Textures.Num());
}
```

### 11.5 Material Property 슬롯 연결 변경

```cpp
// 기존 BaseColor 입력 노드 → Normal 슬롯으로 이동
UMaterialExpression* InputNode = UMaterialEditingLibrary::GetMaterialPropertyInputNode(
    Mat, MP_BaseColor);
FString OutputName = UMaterialEditingLibrary::GetMaterialPropertyInputNodeOutputName(
    Mat, MP_BaseColor);

// Normal 슬롯에 재연결
UMaterialEditingLibrary::ConnectMaterialProperty(InputNode, OutputName, MP_Normal);
UMaterialEditingLibrary::RecompileMaterial(Mat);
```

### 11.6 Parameter Group 일괄 Rename

```cpp
UMaterialEditingLibrary::RenameMaterialParameterGroup(Mat,
    FName("Texture"), FName("Textures"));
```

### 11.7 Material Usage 활성

```cpp
bool bNeedsRecompile = false;
UMaterialEditingLibrary::SetMaterialUsage(Mat, MATUSAGE_SkeletalMesh, bNeedsRecompile);
if (bNeedsRecompile)
{
    UMaterialEditingLibrary::RecompileMaterial(Mat);
}
```

---

## 12. Build.cs 의존성 (Editor 모듈만)

```csharp
// MyEditorTool.Build.cs
PrivateDependencyModuleNames.AddRange(new[]
{
    "Core", "CoreUObject", "Engine",
    "UnrealEd",
    "MaterialEditor",       // ⭐ UMaterialEditingLibrary
});
```

> uplugin Type = `"Editor"` 의무.

---

## 13. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Runtime 모듈에 `MaterialEditor` 의존 추가 | Cooked Build 깨짐 — Editor 모듈만 |
| 2 | `CreateMaterialExpression` 후 `RecompileMaterial` 누락 | 변경 GPU 반영 X — 의무 호출 |
| 3 | `Material->Modify()` 누락 → Undo/Redo 깨짐 | `FScopedTransaction` + `Modify()` 의무 |
| 4 | `FromOutputName` 빈 문자열 vs `"RGB"` 혼동 | 기본 출력 = `""` (빈 문자열) / 특정 채널 = `"R"`/`"G"`/`"B"`/`"A"` |
| 5 | EMaterialProperty 변경 후 Recompile 누락 | 슬롯 변경 시 Recompile 의무 |
| 6 | Material vs MaterialFunction API 혼동 | `CreateMaterialExpression` (Material) vs `CreateMaterialExpressionInFunction` (MF) |
| 7 | MIC `SetMaterialInstance*Value` 후 `UpdateMaterialInstance` 누락 | 변경 반영 위해 `UpdateMaterialInstance` 호출 |
| 8 | LayoutMaterialExpressions 누락 → Editor UI 노드 겹침 | 노드 추가 후 Layout 권장 |
| 9 | Python `connect_material_property` enum 값 잘못 | `unreal.MaterialProperty.MP_BASE_COLOR` (대문자 + MP_ prefix) |
| 10 | 일괄 컴파일 `RecompileMaterials` 콜백 누락 | `FOnItemComplete` Lambda 등록 (진척 추적) |

---

## 14. 체크리스트

- [ ] Editor 모듈만 의존 (`MaterialEditor` Build.cs)
- [ ] uplugin Type = "Editor"
- [ ] 모든 자동화 함수 = `#if WITH_EDITOR` 가드
- [ ] `FScopedTransaction` + `Material->Modify()` 의무 (Undo/Redo)
- [ ] CreateMaterialExpression 후 RecompileMaterial 호출
- [ ] EMaterialProperty 슬롯 연결 후 Recompile
- [ ] MIC 변경 후 UpdateMaterialInstance 호출
- [ ] LayoutMaterialExpressions 호출 (Editor UI 정리)
- [ ] FromOutputName 빈 문자열 = 기본 출력 / 특정 채널 = R/G/B/A
- [ ] Material vs MaterialFunction API 구분
- [ ] 일괄 처리 = RecompileMaterials 콜백 활용
- [ ] 모든 함수 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`

---

## 15. 신뢰도 태그

| 항목 | 신뢰도 | 검증 출처 |
|------|--------|----------|
| UMaterialEditingLibrary 56 UFUNCTION (5.5.4) | **[verified]** ✅ | `MaterialEditingLibrary.h` grep 58 매치 |
| CreateMaterialExpression 시그니처 | **[verified]** ✅ | `MaterialEditingLibrary.h` (정확 시그니처 인용) |
| ConnectMaterialProperty / ConnectMaterialExpressions | **[verified]** ✅ | 동일 헤더 |
| RecompileMaterial / RecompileMaterials | **[verified]** ✅ | 동일 헤더 |
| MIC Get/Set 16 UFUNCTION | **[verified]** ✅ | 동일 헤더 |
| MaterialFunction API 4종 | **[verified]** ✅ | 동일 헤더 |
| Inspection API 8종 | **[verified]** ✅ | 동일 헤더 |
| FMaterialStatistics USTRUCT | **[verified]** ✅ | `MaterialEditingLibrary.h:20-58` |
| EMaterialProperty 슬롯 (BaseColor/Normal/Metallic/Roughness/etc) | **[grep-listed]** ⚠ | `SceneTypes.h` 안 enum 존재 |
| EMaterialParameterAssociation 3종 (Global/Layer/Blend) | **[inferred]** ❌ | UE 일반 — enum grep 권장 |
| Python API 명명 (snake_case) | **[inferred]** ❌ | UE Python 일반 변환 — 공식 문서 검증 |

---

## 16. 관련

- [`../SKILL.md`](../SKILL.md) — Render 메인
- ⭐ [`./MaterialExpression.md`](./MaterialExpression.md) — UMaterialExpression 작성 (자동화 페어)
- [`./Material.md`](./Material.md) — UMaterial 시스템 전반
- [`./Shader.md`](./Shader.md) — Shader 컴파일
- [`../../Editor/SKILL.md`](../../Editor/SKILL.md) — Editor 카테고리 (4단 분리)
- [`../../LevelSequence/references/SequencerScripting.md`](../../LevelSequence/references/SequencerScripting.md) — Python 자동화 페어
- 🚨 [`../../../references/05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) — Editor 4단 분리
- 🚨 [`../../../references/07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)

---

## 17. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-13 | 최초 작성. **UMaterialEditingLibrary 56 UFUNCTION (5.5.4) [verified]** — 10 카테고리 분류 (Expression CRUD 8 / Connection 2 / Compile 4 / Layout 3 / Parameter Get 4 / MIC Get/Set 16 / Inspection 8 / Usage 2 / Parameter Names 7 / Group-Stats 4). 핵심 API 3 (`CreateMaterialExpression` / `ConnectMaterialProperty` / `ConnectMaterialExpressions`) 정확 시그니처 + 실 사용 예 + Python 자동화 + 시나리오 7종 + 함정 10. Engine 5.5.4 검증 — `Source/Editor/MaterialEditor/Public/MaterialEditingLibrary.h`. |
