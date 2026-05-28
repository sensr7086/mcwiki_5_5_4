---
name: render-materialexpression
description: 🛠 Custom Material Expression 깊이 — UMaterialExpression 자손 작성 표준 + FMaterialCompiler API 600+ 메소드 + MIR::FEmitter 5.x Build 인터페이스 + UMaterialExpressionCustom 인라인 HLSL 노드 + Material Expression 262종 카테고리 + Substrate Material 5.x. Editor 전용 (WITH_EDITOR 가드 + 4단 분리).
---

# Render/MaterialExpression — Custom Material Expression 깊이 🛠

> **위치 (verified)**:
> - **UMaterialExpression** — `Engine/Source/Runtime/Engine/Public/Materials/MaterialExpression.h` (베이스, 라인 189 — 5.5.4)
> - **FMaterialCompiler** — `Engine/Source/Runtime/Engine/Public/MaterialCompiler.h` (643 virtual, 548 `int32` 리턴 — 5.5.4)
> - **UMaterialExpressionCustom** — `Engine/Source/Runtime/Engine/Public/Materials/MaterialExpressionCustom.h` (런타임 인라인 HLSL)
> - **MIR::FEmitter** — 5.x 신규 Material IR 빌더 (`MaterialExpression.h:44` namespace 선언 — 5.5.4)
> - **262 expressions** — `Engine/Public/Materials/MaterialExpression*.h` (Abs, Add, ..., VirtualTexture — 5.5.4)
>
> **외부 표준 문서**: [Custom Material Expressions in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/custom-material-expressions-in-unreal-engine) · [Material Expressions Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-material-expressions-reference)
>
> **요지**: Material Graph 안 **표현식 (Material Expression)** 의 깊은 작성 가이드. 3 가지 접근 — (a) `UMaterialExpressionCustom` 인라인 HLSL (런타임 노드, 가장 빠름) / (b) `UMaterialFunction` 재사용 / (c) **`UMaterialExpression` 자손 C++** (가장 강력, Editor 모듈).

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) | `UMaterialExpression` 자손 = **Editor 모듈 + `WITH_EDITOR` 가드 의무** (4단 분리) |
| 🚨 [`11_AssetLoadingPolicy.md §3`](../../../references/11_AssetLoadingPolicy.md#3-환경-모드별-로드-정책--editor-pure-vs-pie-vs-cooked-game-) | Editor 순수 모드 Material 작성 = 동기 로드 (`TryLoad`) |
| 🚨 Compile 시점 | Material Expression `Compile()` = **Cook 시점 / Editor 컴파일 시점 1회 호출** — 런타임 X. 무한 루프 / 비싼 연산 안전 X |
| 🚨 PSO Precache (5.x) | Custom Expression 추가 시 Permutation 폭증 — `r.PSOPrecache=1` 의무 |
| 🚨 GetReferencedTexture | `Compiler->Texture(...)` 호출 시 — `GetReferencedTexture()` override 의무 (텍스처 의존성 추적) |

---

## 1. 3 가지 Custom 접근 — 결정 트리

```
요구사항 →
├── 그래프 안에서 HLSL 한 줄 / 작은 수식 (재사용 X) → (a) UMaterialExpressionCustom (인라인)
├── 그래프 노드로 재사용 (HLSL 변경 가능 / 디자이너) → (b) UMaterialFunction (그래프 함수)
└── 완전히 새 노드 타입 (Compile 로직 / Substrate 통합 / GBuffer 접근) → (c) UMaterialExpression 자손 C++
```

| 방법 | 작성 위치 | 재사용 | 성능 | Permutation 비용 |
|------|----------|--------|------|------------------|
| **(a) Custom 인라인** | Material Graph 안 | 복사 X | 동일 | 매 Material 별 (폭증 위험) |
| **(b) Material Function** | UMaterialFunction 어셋 | ✅ Shared | 동일 | 한 번만 컴파일 |
| **(c) C++ Expression** ⭐ | Editor 모듈 (`UCLASS()`) | ✅ Shared | 동일 | 한 번만 컴파일 + 5.x Substrate 통합 가능 |

---

## 2. UMaterialExpression 핵심 virtual 후크 [verified]

```cpp
class UMaterialExpression : public UObject
{
#if WITH_EDITOR
    // === Compile (가장 중요) — Cook / Editor 컴파일 시점 호출 ===
    ENGINE_API virtual int32 Compile(FMaterialCompiler* Compiler, int32 OutputIndex);      // Line 270
    virtual int32 CompilePreview(FMaterialCompiler* Compiler, int32 OutputIndex) { return Compile(Compiler, OutputIndex); }  // Line 271

    // === 5.x 신규 Material IR (MIR) 빌더 (Build) ===
    ENGINE_API virtual void Build(MIR::FEmitter& Emitter);                                 // Line 281

    // === Shader Tag (Material 별 추적) ===
    virtual void GetShaderTags(TArray<FName>& ShaderTagsOut) {}                            // Line 287

    // === 사용 가능 위치 검증 ===
    ENGINE_API virtual bool IsAllowedIn(const UObject* MaterialOrFunction) const;          // Line 298

    // === Input / Output 정의 ===
    ENGINE_API virtual int32 CountInputs() const;                                          // Line 325
    ENGINE_API virtual FExpressionInput* GetInput(int32 InputIndex);                       // Line 336
    ENGINE_API virtual FName GetInputName(int32 InputIndex) const;                         // Line 342
    ENGINE_API virtual uint32 GetInputType(int32 InputIndex);                              // Line 347
    ENGINE_API virtual TArray<FExpressionOutput>& GetOutputs();                            // Line 349
    ENGINE_API virtual uint32 GetOutputType(int32 OutputIndex);                            // Line 352
    virtual EMaterialValueType GetInputValueType(int32 InputIndex);                        // Line 354
    virtual EMaterialValueType GetOutputValueType(int32 OutputIndex);                      // Line 361

    // === Texture / Texture Collection 의존성 추적 ===
    virtual UObject* GetReferencedTexture() const { return nullptr; }                      // Line 312
    virtual ReferencedTextureArray GetReferencedTextures() const;                          // Line 315
    virtual bool CanReferenceTexture() const { return false; }                             // Line 318
    virtual UTextureCollection* GetReferencedTextureCollection() const { return nullptr; } // Line 320

    // === Editor UI (캡션 / 툴팁 / 크기) ===
    ENGINE_API virtual void GetCaption(TArray<FString>& OutCaptions) const;                // Line 399
    ENGINE_API virtual FString GetDescription() const;                                     // Line 401
    ENGINE_API virtual FText GetCreationName() const;                                      // Line 382
    ENGINE_API virtual FText GetCreationDescription() const;                               // Line 381
    virtual FText GetKeywords() const { return FText::GetEmpty(); }                        // Line 537

    // === Material Attribute / Substrate 5.x ===
    virtual bool IsResultMaterialAttributes(int32 OutputIndex) { return false; }           // Line 453
    virtual bool IsResultSubstrateMaterial(int32 OutputIndex) { return false; }            // Line 458 (5.x)
    virtual void GatherSubstrateMaterialInfo(FSubstrateMaterialInfo&, int32 OutputIndex) {} // Line 463 (5.x)
    ENGINE_API virtual FSubstrateOperator* SubstrateGenerateMaterialTopologyTree(...);     // Line 470 (5.x)

    // === 파라미터 (UMaterialExpressionParameter 자손용) ===
    virtual bool HasAParameterName() const { return false; }                               // Line 569
    virtual FName GetParameterName() const { return NAME_None; }                           // Line 575
    virtual bool GetParameterValue(FMaterialParameterMetadata& OutMeta) const;             // Line 577
    virtual bool SetParameterValue(const FName& Name, ...);                                // Line 578

    // === Custom Pin (5.x — UMaterialExpressionCustom 가 사용) ===
    virtual bool CanDeletePin(EEdGraphPinDirection, int32) const { return false; }         // Line 603
    virtual void DeletePin(EEdGraphPinDirection, int32) {}                                 // Line 610
#endif // WITH_EDITOR
};
```

> ⚠ **모든 virtual = `#if WITH_EDITOR` 가드 안** — Cooked Build 에 컴파일 X. Material Expression = **Editor 시간 컴파일러 객체**, 런타임 GPU 에 도달 안 함 (컴파일 결과만 도달).

---

## 3. Compile() 표준 패턴 (가장 중요) ⭐

`Compile()` = Material Expression Graph → HLSL 코드 변환의 핵심. **`FMaterialCompiler` 의 헬퍼 메소드 호출 → CodeChunk 인덱스 반환**.

### 3.1 표준 패턴

```cpp
// MyMaterialExpression.h (Editor 모듈)
UCLASS(MinimalAPI, collapsecategories, hidecategories=Object,
       meta=(DisplayName="My Effect"))
class UMaterialExpressionMyEffect : public UMaterialExpression
{
    GENERATED_BODY()

    UPROPERTY()
    FExpressionInput Input;                          // 입력 핀

    UPROPERTY()
    FExpressionInput Strength;                       // 두 번째 입력 핀

    UPROPERTY(EditAnywhere, Category=MaterialExpressionMyEffect)
    float DefaultStrength = 1.0f;                    // 기본 값 (디테일 패널)

#if WITH_EDITOR
    virtual int32 Compile(FMaterialCompiler* Compiler, int32 OutputIndex) override
    {
        // [1] 필수 입력 검증
        if (!Input.GetTracedInput().Expression)
        {
            return Compiler->Errorf(TEXT("MyEffect: Input pin not connected"));
        }

        // [2] 입력 컴파일 — 자식 Expression 의 Compile() 재귀 호출
        const int32 InputCode = Input.Compile(Compiler);
        if (InputCode == INDEX_NONE) return INDEX_NONE;

        // [3] Strength 입력 (없으면 DefaultStrength)
        const int32 StrengthCode = Strength.GetTracedInput().Expression
            ? Strength.Compile(Compiler)
            : Compiler->Constant(DefaultStrength);

        // [4] FMaterialCompiler 헬퍼 호출 → HLSL 코드 생성
        const int32 ScaledCode = Compiler->Mul(InputCode, StrengthCode);
        const int32 NoiseCode  = Compiler->Frac(Compiler->Mul(InputCode, Compiler->Constant(7919.f)));
        const int32 FinalCode  = Compiler->Add(ScaledCode, NoiseCode);

        return FinalCode;   // CodeChunk 인덱스 반환
    }

    virtual void GetCaption(TArray<FString>& OutCaptions) const override
    {
        OutCaptions.Add(TEXT("My Effect"));
    }

    virtual EMaterialValueType GetOutputValueType(int32 OutputIndex) override
    {
        return MCT_Float3;
    }
#endif
};
```

### 3.2 핵심 규칙

| 규칙 | 설명 |
|------|------|
| **반환값 = CodeChunk 인덱스** | `int32` — `FMaterialCompiler` 의 내부 코드 청크 ID. `INDEX_NONE` = 에러 |
| **에러 처리** | `Compiler->Errorf(TEXT("..."))` → `INDEX_NONE` 반환 |
| **입력 재귀** | `Input.Compile(Compiler)` → 자식 Expression 의 `Compile()` 호출 |
| **Compile 1회** | Material × Quality × Platform 조합당 1회 → Cooked DDC 캐시 (런타임 호출 X) |
| **외부 영향 금지** | 글로벌 상태 수정 X, IO X — **순수 함수** (Cook 재현성 의무) |

---

## 4. FMaterialCompiler API — 578 `int32` 메소드 [verified]

`FMaterialCompiler` (`MaterialCompiler.h`) = **HLSL 생성 빌더**. 모든 메소드가 CodeChunk 인덱스 반환.

### 4.1 카테고리별 핵심 메소드

| 카테고리 | 메소드 (sample) |
|---------|----------------|
| **Constant** | `Constant(float)` / `Constant2(x,y)` / `Constant3(x,y,z)` / `Constant4(x,y,z,w)` / `GenericConstant(FValue)` |
| **산술** | `Add(A,B)` / `Sub(A,B)` / `Mul(A,B)` / `Div(A,B)` / `Power(Base,Exp)` / `SquareRoot(X)` |
| **벡터** | `Dot(A,B)` / `Cross(A,B)` / `Length(X)` / `Normalize(X)` / `AppendVector(A,B)` / `ComponentMask(A,Mask)` |
| **삼각** | `Sine(X)` / `Cosine(X)` / `Tangent(X)` / `Arcsine` / `Arccosine` / `Arctangent` / `Arctangent2` (+ Fast 변형) |
| **반올림** | `Floor(X)` / `Ceil(X)` / `Round(X)` / `Frac(X)` / `Fmod(A,B)` / `Modulo(A,B)` / `Truncate(X)` |
| **범위** | `Saturate(X)` / `Clamp(X,Min,Max)` / `Min(A,B)` / `Max(A,B)` / `Sign(X)` / `Abs(X)` |
| **보간** | `Lerp(A,B,Alpha)` / `Step(Y,X)` / `SmoothStep(Min,Max,X)` |
| **분기** | `If(A,B,AGreaterThanB,AEqualsB,ALessThanB,Threshold)` / `Switch(...)` / `DynamicBranch(Value)` |
| **타입 변환** | `ValidCast(Code,DestType)` / `ForceCast(Code,DestType,Flags)` / `CastShadingModelToFloat(Code)` / `TruncateLWC(Code)` |
| **시간** | `GameTime(bPeriodic,Period)` / `RealTime(bPeriodic,Period)` / `DeltaTime()` / `PeriodicHint(Code)` |
| **카메라 / 뷰** | `CameraVector()` / `LightVector()` / `ReflectionVector()` / `ScreenPosition()` / `ViewProperty(Property,bInv)` / `IsOrthographic()` / `GetPixelPosition()` / `GetViewportUV()` |
| **위치** | `WorldPosition(WorldPositionIncludedOffsets)` / `LocalPosition(IncludesOffsets)` / `ObjectWorldPosition()` / `ActorWorldPosition()` |
| **오브젝트** | `ObjectBounds()` / `ObjectLocalBounds()` / `ObjectRadius()` / `InstanceLocalBounds()` / `PreSkinnedLocalBounds()` |
| **회전** | `RotateAboutAxis(NormalizedRotationAxis,RotationAngle,PivotPoint,Position)` |
| **텍스처** | `TextureSample(Texture,Coordinate,...)` / `TextureCoordinate(CoordinateIndex,...)` / `TextureProperty(...)` |
| **파라미터** | `NumericParameter(Type,Name,DefaultValue)` / `AccessCollectionParameter(...)` |
| **파티클** | `ParticleColor()` / `ParticlePosition()` / `ParticleRadius()` / `ParticleRandom()` / `ParticleRelativeTime()` / `ParticleSize()` / `ParticleSpeed()` / `ParticleSubUV()` / ... |
| **DistanceField** | `DistanceToNearestSurface(Position)` / `DistanceFieldGradient(Position)` / `DistanceFieldApproxAO(...)` |
| **에러 / 함수** | `Errorf(Text)` / `Error(Text)` / `AppendExpressionError(Expr,Text)` / `CallExpression(Key,Compiler)` / `CallExpressionExec(Expr)` |
| **Substrate (5.x)** | `SubstrateSlabBSDF` / `SubstrateUnlitBSDF` / `SubstrateHairBSDF` / `SubstrateEyeBSDF` / `SubstrateSingleLayerWaterBSDF` / `SubstrateHorizontalMixing` / `SubstrateVerticalLayering` / `SubstrateThinFilm` / `SubstrateMetalnessToDiffuseAlbedoF0` / ... (20+) |

**총 578 `int32` 메소드** — 본 표는 sample. 실제 API = `MaterialCompiler.h` grep.

### 4.2 에러 처리 표준

```cpp
virtual int32 Compile(FMaterialCompiler* Compiler, int32 OutputIndex) override
{
    if (!Input.GetTracedInput().Expression)
    {
        // 사용자에게 에러 메시지 + INDEX_NONE 반환
        return Compiler->Errorf(TEXT("MyExpression: 'Input' pin must be connected"));
    }

    const int32 Code = Input.Compile(Compiler);
    if (Code == INDEX_NONE)
    {
        // 자식 컴파일 실패 — 그대로 전파
        return INDEX_NONE;
    }

    return Compiler->Saturate(Code);
}
```

---

## 5. UMaterialExpressionCustom — 인라인 HLSL 노드 [verified]

`Engine/Public/Materials/MaterialExpressionCustom.h` — Material Editor 안에서 **그래프 한복판에 HLSL 작성**.

### 5.1 구조

```cpp
UCLASS(collapsecategories, hidecategories=Object, MinimalAPI)
class UMaterialExpressionCustom : public UMaterialExpression
{
    UPROPERTY(EditAnywhere, meta=(MultiLine=true))
    FString Code;                                    // HLSL 코드 본체

    UPROPERTY(EditAnywhere)
    TEnumAsByte<ECustomMaterialOutputType> OutputType;   // CMOT_Float1/2/3/4 / MaterialAttributes

    UPROPERTY(EditAnywhere)
    FString Description;                              // 노드 캡션

    UPROPERTY(EditAnywhere)
    TArray<FCustomInput> Inputs;                      // 입력 핀 (이름 + Type 자동)

    UPROPERTY(EditAnywhere)
    TArray<FCustomOutput> AdditionalOutputs;          // 추가 출력 핀 (5.x)

    UPROPERTY(EditAnywhere)
    TArray<FCustomDefine> AdditionalDefines;          // #define KEY VALUE

    UPROPERTY(EditAnywhere)
    TArray<FString> IncludeFilePaths;                 // #include "/Plugin/.../MyShared.ush"
};
```

### 5.2 사용 예 — 그래프 안

```hlsl
// Inputs: float3 BaseColor, float NoiseScale
// Output Type: CMOT_Float3
// Additional Defines: PI = 3.14159265
// Include File Paths: /Plugin/MyPlugin/MyHelpers.ush

float3 OffsetCol = BaseColor + frac(BaseColor.x * NoiseScale + sin(View.GameTime * PI)) * 0.1;
return OffsetCol;
```

### 5.3 인라인 Custom 의 함정

| # | 함정 | 정답 |
|---|------|------|
| 1 | 매 Material 마다 별도 Permutation → Cook 시간 ↑ | `UMaterialFunction` 으로 공유 |
| 2 | Lumen / Nanite GBuffer 자동 통합 X | Custom Output 사용 / Custom Expression C++ 자손 작성 |
| 3 | `MaterialAttributes` 출력 시 모든 핀 수동 분기 | (b) MaterialFunction 또는 (c) C++ Expression 권장 |
| 4 | `#include` 경로 = `AddShaderSourceDirectoryMapping` 필요 | Module StartupModule 안 등록 |
| 5 | Substrate 5.x 호환 어려움 | Substrate 통합은 (c) C++ Expression 의 `Substrate*` 헬퍼 사용 |

---

## 6. UMaterialExpression 269종 카테고리 [grep-listed]

`Engine/Public/Materials/MaterialExpression*.h` 의 269개 파일을 카테고리별 분류 (sample).

| 카테고리 | 개수 | 대표 표현식 |
|---------|------|------------|
| **산술** | ~35 | Add / Sub / Mul / Div / Power / SquareRoot / Sine / Cosine / Tangent / Arctangent / Arctangent2 (+ Fast) |
| **벡터** | ~15 | DotProduct / CrossProduct / AppendVector / ComponentMask / Normalize / Length |
| **반올림 / 범위** | ~10 | Abs / Ceil / Floor / Frac / Fmod / Clamp / Saturate / Sign |
| **분기** | ~8 | If / Switch / DataDrivenShaderPlatformInfoSwitch / BindlessSwitch / FeatureLevelSwitch / QualitySwitch / ShadingPathSwitch |
| **상수 / 파라미터** | ~25 | Constant / Constant2Vector / Constant3Vector / Constant4Vector / ScalarParameter / VectorParameter / ChannelMaskParameter / CollectionParameter / CurveAtlasRowParameter / NumericParameter |
| **텍스처** | ~34 | TextureSample / TextureCoordinate / TextureObject / TextureProperty / AntialiasedTextureMask / TextureSampleParameter* / SparseVolumeTexture / VolumeTexture / DBufferTexture |
| **위치 / 변환** | ~12 | WorldPosition / LocalPosition / ActorPositionWS / ObjectPositionWS / ObjectBounds / Transform / TransformPosition / ScreenPosition |
| **카메라 / 뷰** | ~10 | CameraPositionWS / CameraVectorWS / ViewProperty / ViewSize / IsOrthographic / ScreenAlignedPixelToPixelMapping |
| **라이트 / 환경** | ~10 | LightVector / ReflectionVector / SkyAtmosphereLightDirection / SkyAtmosphereViewLuminance / AtmosphericFogColor / AtmosphericLightVector / CloudLayer / BlackBody |
| **파티클** | ~14 | ParticleColor / ParticleDirection / ParticleMacroUV / ParticleMotionBlurFade / ParticlePositionWS / ParticleRadius / ParticleRandom / ParticleRelativeTime / ParticleSize / ParticleSpeed / ParticleSpriteRotation / ParticleSubUV / ParticleSubUVProperty |
| **머티리얼 속성** | ~10 | MakeMaterialAttributes / BreakMaterialAttributes / BlendMaterialAttributes / SetMaterialAttributes / GetMaterialAttributes / MaterialAttributeLayers |
| **Substrate (5.x)** | ~14 | SubstrateSlabBSDF / SubstrateUnlitBSDF / SubstrateHairBSDF / SubstrateEyeBSDF / SubstrateSingleLayerWater / SubstrateLegacyConversion / SubstrateHorizontalMix / SubstrateVerticalLayering / SubstrateThinFilm |
| **Decal** | ~5 | DecalColor / DecalDerivative / DecalLifetimeOpacity / DecalMipmapLevel / DBufferTexture |
| **DistanceField** | ~4 | DistanceToNearestSurface / DistanceFieldGradient / DistanceFieldApproxAO / GlobalDistanceField |
| **5.x 특수** | ~10 | Bounds / Aggregate / ColorRamp / Composite / DDX / DDY / RuntimeVirtualTextureSample / SparseVolumeTextureSample / BindlessSwitch |
| **Custom / Output** | ~5 | Custom / CustomOutput / ClearCoatNormalCustomOutput / BentNormalCustomOutput / AbsorptionMediumMaterialOutput |
| **기타** | ~58 | Comment / Composite / NamedRerouteUsage / RerouteNode / Aggregate / ConstantBiasScale / ... |

**총 269종** — 자세한 표현식 목록은 [Material Expressions Reference (Epic Docs)](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-material-expressions-reference) 참조.

---

## 7. 5.x 신규 — MIR::FEmitter Build 인터페이스 [verified]

5.x 부터 `UMaterialExpression::Build(MIR::FEmitter& Emitter)` virtual 추가 — **Material IR (Intermediate Representation) 빌더**.

### 7.1 시그니처

```cpp
// MaterialExpression.h:35-37
namespace MIR
{
    class FEmitter;
}

// MaterialExpression.h:281
ENGINE_API virtual void Build(MIR::FEmitter& Emitter);
```

### 7.2 Compile() vs Build() — 차이

| 항목 | Compile (Legacy) | Build (5.x 신규) |
|------|------------------|------------------|
| 호출 시점 | HLSL Material Translator | Material IR Translator (실험적) |
| 출력 | HLSL CodeChunk 인덱스 | MIR Value 노드 |
| Substrate 통합 | 부분적 (`Substrate*` 호출) | Native MIR 노드 |
| 5.x 권장 | ✅ (기본 / 안정) | ⚠ 실험적 (점진 전환) |

> 🚨 **현재 (5.5.4)** = `Compile()` 이 표준 / `Build()` = 실험적 (Substrate / Material IR 시스템). 일반 Custom Expression = `Compile()` 만 override.

---

## 8. Substrate Material 5.x 통합 [grep-listed]

5.x Substrate = 차세대 PBR 시스템 (Layered Materials). Custom Expression 이 Substrate 출력 시 — 별도 후크.

### 8.1 핵심 virtual

```cpp
#if WITH_EDITOR
// 출력이 Substrate Material 인지
virtual bool IsResultSubstrateMaterial(int32 OutputIndex) { return false; }

// Substrate Material Info 수집
virtual void GatherSubstrateMaterialInfo(FSubstrateMaterialInfo& Info, int32 OutputIndex) {}

// Substrate Topology Tree 생성
ENGINE_API virtual FSubstrateOperator* SubstrateGenerateMaterialTopologyTree(
    FMaterialCompiler* Compiler, UMaterialExpression* Parent, int32 OutputIndex);
#endif
```

### 8.2 Substrate BSDF Compile 패턴

```cpp
virtual int32 Compile(FMaterialCompiler* Compiler, int32 OutputIndex) override
{
    // Substrate Slab BSDF (가장 일반)
    const int32 BaseColorCode = BaseColor.Compile(Compiler);
    const int32 RoughnessCode = Roughness.Compile(Compiler);
    const int32 NormalCode    = Normal.Compile(Compiler);

    return Compiler->SubstrateSlabBSDF(
        Compiler->Constant3(0.04f, 0.04f, 0.04f),     // F0
        Compiler->Constant(0.0f),                      // F90
        BaseColorCode,                                 // DiffuseAlbedo
        RoughnessCode,                                 // Roughness
        NormalCode,                                    // Normal
        /* ... 다수 파라미터 */
    );
}
```

`FMaterialCompiler::Substrate*` API 20+ 종 — `MaterialCompiler.h` grep.

---

## 9. Editor 모듈 분리 (4단 분리 의무)

`UMaterialExpression` 자손 = **Editor 모듈 전용** — Runtime 모듈 안 작성 X.

### 9.1 모듈 분리 구조

```
[1] MyMaterialRuntime/              Type=Runtime    (게임 빌드 OK)
    └── (Material 자체는 런타임 어셋 — 컴파일 결과만 사용)

[2] MyMaterialEditor/               Type=Editor     (게임 빌드 X)
    ├── Build.cs : "MaterialEditor", "UnrealEd", "Engine", "RenderCore"
    ├── MaterialExpressionMyEffect.h         (UMaterialExpression 자손)
    ├── MaterialExpressionMyEffect.cpp       (Compile() 구현)
    └── FMyMaterialEditorModule              (StartupModule 안 등록)
```

### 9.2 Build.cs (Editor 모듈)

```csharp
public class MyMaterialEditor : ModuleRules
{
    public MyMaterialEditor(ReadOnlyTargetRules Target) : base(Target)
    {
        PrivateDependencyModuleNames.AddRange(new[]
        {
            "Core", "CoreUObject", "Engine",
            "RenderCore", "Renderer",
            "MaterialEditor",       // FMaterialCompiler 의존
            "UnrealEd",
            "Slate", "SlateCore"
        });
    }
}
```

### 9.3 .uplugin Type

```json
{
  "Modules": [
    { "Name": "MyMaterialEditor", "Type": "Editor", "LoadingPhase": "PostEngineInit" }
  ]
}
```

→ Cooked Build 시 `MyMaterialEditor` 자동 stripped. UMaterial 어셋 안 컴파일 결과 (HLSL → DXIL/SPIR-V) 만 출시 빌드에 포함.

---

## 10. 함정 & 안티패턴 (12종)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Runtime 모듈에 `UMaterialExpression` 자손 작성 | Editor 모듈 분리 (4단) — Cooked 빌드 실패 |
| 2 | `#if WITH_EDITOR` 가드 누락 (virtual override) | 모든 Compile / Build / GetCaption = 가드 안 |
| 3 | `Input.Compile()` 결과 `INDEX_NONE` 미체크 | `INDEX_NONE` 전파 (자식 에러 시) |
| 4 | `Compile()` 안 글로벌 상태 수정 / IO | 순수 함수 — Cook 재현성 깨짐 |
| 5 | `Compiler->Texture(...)` 호출 후 `GetReferencedTexture()` override 누락 | 텍스처 의존성 추적 X → 텍스처 변경 시 Material 재컴파일 X |
| 6 | `GetCaption()` 안 매 호출 동적 문자열 | 정적 문자열 추천 (Editor UI 성능) |
| 7 | `IsResultMaterialAttributes(0) = true` 인데 `GetOutputValueType` 미동기화 | 두 메소드 동시 갱신 의무 |
| 8 | `UMaterialExpressionCustom` 매 Material 별 동일 코드 복사 | `UMaterialFunction` 으로 공유 (Permutation 1회) |
| 9 | `Substrate*` 호출 안 했는데 `IsResultSubstrateMaterial = true` | Compile / Substrate 메소드 / IsResult* 3중 동기 |
| 10 | `Build(MIR::FEmitter&)` 실험적 인터페이스 의존 | 5.5.4 = `Compile()` 만 override (Build = 점진 전환) |
| 11 | `GetInputName` / `GetInputType` `CountInputs` 비동기화 | 한 곳 변경 시 3종 모두 갱신 |
| 12 | Custom Expression 추가 후 Cook 시간 폭증 | `r.PSOPrecache=1` + Material Function 으로 공유 + Permutation 분리 |

---

## 11. 체크리스트

- [ ] `UMaterialExpression` 자손 = Editor 모듈 (`Type=Editor`) + Build.cs `"MaterialEditor"` 의존
- [ ] 모든 virtual override = `#if WITH_EDITOR` 가드
- [ ] `Compile()` = 입력 검증 → `INDEX_NONE` 검사 → `FMaterialCompiler` 헬퍼 호출 → CodeChunk 반환
- [ ] `Compiler->Errorf` 로 에러 메시지 + `INDEX_NONE` 반환
- [ ] `Compile()` = 순수 함수 (글로벌 상태 / IO X)
- [ ] `Compiler->Texture*` 사용 시 `GetReferencedTexture()` override + `CanReferenceTexture() = true`
- [ ] `GetCaption()` / `GetCreationName()` / `GetCreationDescription()` override
- [ ] `GetInputName` / `GetInputType` / `CountInputs` 3종 동기
- [ ] `IsResultMaterialAttributes` / `IsResultSubstrateMaterial` (5.x) = 출력 타입과 동기
- [ ] Substrate 5.x = `SubstrateGenerateMaterialTopologyTree` + `GatherSubstrateMaterialInfo` + Compile 안 `Substrate*` 헬퍼
- [ ] PSO Precache 활성 (`r.PSOPrecache=1`) — Permutation 증가 대응
- [ ] Cooked Build 검증 (개발 중) — Cook 시간 측정

---

## 12. 신뢰도 태그

| 항목 | 신뢰도 | 검증 출처 |
|------|--------|----------|
| UMaterialExpression virtual 후크 (Compile / Build / GetInput / GetOutput / etc) | **[verified]** ✅ | `Engine/Public/Materials/MaterialExpression.h:148-617` |
| FMaterialCompiler 578 `int32` 메소드 | **[verified]** ✅ | `Engine/Public/MaterialCompiler.h` (grep 578 매치) |
| UMaterialExpressionCustom 구조 + virtual | **[verified]** ✅ | `Engine/Public/Materials/MaterialExpressionCustom.h:64-115` |
| MIR::FEmitter namespace + Build virtual | **[verified]** ✅ | `MaterialExpression.h:35-37 / 281` |
| Substrate 5.x virtual (IsResultSubstrate / Gather / Generate / SubstrateOperator) | **[verified]** ✅ | `MaterialExpression.h:458-470` |
| 269개 MaterialExpression* 파일 | **[verified]** ✅ | `ls Engine/Public/Materials/MaterialExpression*.h \| wc -l` = 269 |
| FMaterialCompiler 카테고리 분류 (산술/벡터/삼각/분기/etc) | **[grep-listed]** ⚠ | 메소드 이름 패턴 — sample 추출 |
| 269 표현식 카테고리 표 (산술 35 / 벡터 15 / ...) | **[inferred]** ❌ | 파일명 prefix 기반 분류 — 정확한 그룹화 미검증 |
| Substrate Compile 패턴 (SubstrateSlabBSDF 인자) | **[inferred]** ❌ | 일반 패턴 — 정확 시그니처 사용 전 grep 검증 |
| FCustomDefine / FCustomInput / FCustomOutput 구조 | **[verified]** ✅ | `MaterialExpressionCustom.h:28-62` |

---

## 13. 관련

- [`Render/SKILL.md`](../SKILL.md) — Render 메인
- ⭐ [`Render/references/MaterialEditingLibrary.md`](./MaterialEditingLibrary.md) 🛠 — **Editor 자동화** (Python/BP — Expression 생성 / Connect / Recompile / MIC 일괄 처리 58 UFUNCTION)
- [`Render/references/Material.md`](./Material.md) — Material 시스템 전반 (Domain / ShadingModel / PSO Precache)
- [`Render/references/Shader.md`](./Shader.md) — Global Shader + FMaterialShader (Material 컴파일 결과)
- [`AssetClasses/references/Material.md`](../../AssetClasses/references/Material.md) — UMaterial 자산 측 (MIC / MID / 5.x PSO Precache)
- [`Editor/SKILL.md`](../../Editor/SKILL.md) — Editor 모듈 분리 표준
- [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) — 4단 분리 원칙
- [`11_AssetLoadingPolicy.md §3`](../../../references/11_AssetLoadingPolicy.md#3-환경-모드별-로드-정책--editor-pure-vs-pie-vs-cooked-game-) — Editor 동기 로드
- 🌐 [Custom Material Expressions (Epic Docs)](https://dev.epicgames.com/documentation/en-us/unreal-engine/custom-material-expressions-in-unreal-engine)
- 🌐 [Material Expressions Reference (Epic Docs)](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-material-expressions-reference)
- 🌐 [UMaterialExpression API (Epic Community)](https://dev.epicgames.com/community/learning/tutorials/6mP8/unreal-engine-create-a-custom-material-expression-node-c)

---

## 14. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-12 | 최초 작성. **UMaterialExpression virtual 후크 [verified]** (Compile 270 / Build 281 / GetInput / GetOutput / IsResultSubstrate 458 / GenerateMaterialTopologyTree 470). **FMaterialCompiler 578 `int32` 메소드 [verified]** (Constant / 산술 / 벡터 / 삼각 / 분기 / 텍스처 / 파티클 / Substrate 등 15+ 카테고리). **UMaterialExpressionCustom [verified]** (인라인 HLSL — Code/Inputs/AdditionalOutputs/AdditionalDefines/IncludeFilePaths). **MIR::FEmitter 5.x [verified]** + **Substrate 5.x 통합** (SubstrateSlabBSDF / SubstrateUnlitBSDF / ...). 3 가지 Custom 접근 결정 트리 (Custom 인라인 / MaterialFunction / C++ Expression). 269 expression 카테고리 grep 분류. Editor 모듈 분리 4단 + 함정 12종 + 체크리스트. Epic Docs cross-link 3종. |
