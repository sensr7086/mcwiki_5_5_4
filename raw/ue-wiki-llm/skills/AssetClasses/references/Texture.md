---
name: assetclasses-texture
description: UTexture (2,228) + UTexture2D + UTextureCube + UTextureRenderTarget2D + UVolumeTexture - CompressionSettings 10종 + TextureGroup 11종 + MipGenSettings 8종 + 5.x VirtualTexture/RVT.
---

# AssetClasses/Texture — UTexture + UTexture2D + UTextureCube + RenderTarget + VolumeTexture

> **위치**: `Engine/Source/Runtime/Engine/Classes/Engine/Texture.h` (2,228) + `Texture2D.h` (397) + `TextureCube.h` + `TextureRenderTarget2D.h` + `VolumeTexture.h`
> **베이스**: `UTexture : public UStreamableRenderAsset` → `UTexture2D` (가장 흔함) / `UTextureCube` / `UTextureRenderTarget*` / `UVolumeTexture`
> **요지**: **모든 텍스처 자산의 베이스** — Material 의 입력 + UI Brush + Light IES + Decal 모두 Texture. **메모리 + GPU 업로드 비용 + Streaming 이 가장 큰 성능 함정**.

---

## 🚨 공통 정책 (Compression / Streaming / 메모리)

| 정책 | Texture 자산 적용 |
|------|-----------------|
| 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) | **Texture 가 가장 큰 자산 카테고리** — 4K 텍스처 = 16MB+. **TSoftObjectPtr<UTexture2D>` + Stream-In 표준** (자동 Streaming). 자주 사용 = Material 의존이라 자동 함께 로드. **bForceMiplevelsToBeResident** = Boss / 캐릭터 사전 풀 해상도 보장. |
| 🚨 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) | Texture 멤버 = `UPROPERTY()` + `TObjectPtr<UTexture2D>` 또는 `TSoftObjectPtr`. RenderTarget = `CreateDefaultSubobject` 또는 `NewObject<UTextureRenderTarget2D>(this)` (Outer = Component). |
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | UpdateResource / PostLoad / BeginCacheForCooked 첫 줄 스코프. |
| [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) | 🛠 Source (FTextureSource) = Editor 전용. Cooked = PlatformData 만 (압축됨). |

---

## 1. 베이스 트리

```
UObject
└── UStreamableRenderAsset (Streaming 지원)
    └── UTexture (2,228 lines — 모든 Texture 베이스)
        ├── UTexture2D (397 — 가장 흔함, 일반 2D)
        │   ├── UTexture2DDynamic (런타임 동적 갱신)
        │   ├── UTextureRenderTarget2D (렌더 타겟 — SceneCapture)
        │   ├── UTextureRenderTarget2DArray
        │   └── UCanvasRenderTarget2D (BP 그리기)
        ├── UTextureCube (Cube 6면 — Reflection / SkyLight)
        ├── UTextureRenderTargetCube
        ├── UVolumeTexture (3D — Volumetric)
        ├── UTextureRenderTargetVolume
        ├── UTexture2DArray (Texture Array)
        ├── UMediaTexture (비디오)
        ├── ULightMapTexture2D (Lightmap — Cooked 시)
        ├── UShadowMapTexture2D (ShadowMap)
        └── UVirtualTexture (5.x VT)
```

---

## 2. UTexture (베이스 — Texture.h:1218 — 2,228 lines)

### 2.1 핵심 필드 — Compression / LOD Group / Streaming

```cpp
class UTexture : public UStreamableRenderAsset,
                 public IInterface_AssetUserData,
                 public IInterface_AsyncCompilation
{
    // Texture.h:1156 — 압축 설정 (디스크 저장 형식)
    UPROPERTY(EditAnywhere, AssetRegistrySearchable)
    TEnumAsByte<enum TextureCompressionSettings> CompressionSettings;

    // Texture.h (LODGroup) — 메모리 그룹
    UPROPERTY(EditAnywhere, AssetRegistrySearchable)
    TEnumAsByte<enum TextureGroup> LODGroup;

    // 5.x Virtual Texture
    UPROPERTY(EditAnywhere, Category=VirtualTextures)
    uint8 VirtualTextureStreaming : 1;

    // Mip 강제 (메모리 비싸지만 즉시 사용 가능)
    UPROPERTY()
    uint8 bForceMiplevelsToBeResident : 1;
};
```

### 2.2 TextureCompressionSettings (디스크 형식)

| Setting | BC 포맷 | 사용 |
|---------|---------|------|
| `TC_Default` (BC1/BC3) | RGB / RGBA | 일반 Diffuse |
| `TC_NormalMap` (BC5) | Normal Map | 법선 맵 (RG only) |
| `TC_Masks` (BC1/BC3) | RGBA | 마스크 / Decal |
| `TC_Grayscale` (G8) | Single Channel | Height / Roughness |
| `TC_BC7` (BC7) | RGBA 고품질 | UI / 캐릭터 (느린 압축) |
| `TC_HDR` (FloatRGBA) | HDR | HDR Sky / Light |
| `TC_HDR_Compressed` (BC6H) | HDR 압축 | HDR (메모리 절감) |
| `TC_VectorDisplacementmap` (BGRA8) | Displacement | Tessellation |
| `TC_Alpha` (G8) | Alpha only | UI Mask |
| `TC_DistanceFieldFont` (G8) | DF Font | UMG Text |

### 2.3 TextureGroup (LODGroup — 메모리 풀)

| Group | 의미 |
|-------|------|
| `TEXTUREGROUP_World` | 일반 월드 (가장 흔함) |
| `TEXTUREGROUP_WorldNormalMap` | 월드 법선 |
| `TEXTUREGROUP_Character` | 캐릭터 (높은 품질) |
| `TEXTUREGROUP_Weapon` | 무기 |
| `TEXTUREGROUP_Vehicle` | 차량 |
| `TEXTUREGROUP_Cinematic` | 시네마틱 (최고 품질) |
| `TEXTUREGROUP_Effects` | VFX (낮은 품질) |
| `TEXTUREGROUP_UI` | UI (Mip 비활성) |
| `TEXTUREGROUP_LightAndShadowMap` | Lightmap / Shadowmap |
| `TEXTUREGROUP_RenderTarget` | RenderTarget |
| `TEXTUREGROUP_Mobile*` | 모바일 그룹 (별도 LODBias) |

> **`Project Settings > Rendering > Texture LOD Settings`** 에서 그룹 별 MaxSize / LODBias / MipGenSettings 결정.

### 2.4 MipGenSettings

```cpp
enum EMipGenSettings
{
    TMGS_FromTextureGroup,        // LODGroup 따름 (기본)
    TMGS_SimpleAverage,            // Box Filter
    TMGS_Sharpen0~10,              // 샤프닝 0-10
    TMGS_NoMipmaps,                // Mip 비활성 (UI / 작은 텍스처)
    TMGS_LeaveExistingMips,
    TMGS_Blur1~5,
    TMGS_Unfiltered,               // Filtering 안 함
    TMGS_Angular,                  // Cubemap 용
};
```

### 2.5 PostLoad / BeginCacheForCookedPlatformData

```cpp
// Cooked 시 — 플랫폼별 압축 (PC = BC1~BC7, Mobile = ASTC, Console = BC7)
ENGINE_API virtual void BeginCacheForCookedPlatformData(const ITargetPlatform* TargetPlatform);

// 런타임 PostLoad — Streaming 시작 / 메모리 등록
virtual void PostLoad() override;
{
    Super::PostLoad();
    UpdateResource();   // GPU 메모리 등록 + Streaming 시작
}
```

### 2.6 UpdateResource (런타임 갱신)

```cpp
// Texture 데이터 변경 후 GPU 재업로드
Texture->CompressionSettings = TC_Default;
Texture->UpdateResource();   // ⚠️ 비싸지만 필수 — 런타임 변경 후
```

---

## 3. UTexture2D (Texture2D.h:25 — 가장 흔함)

### 3.1 사이즈 / Format / Mip API

```cpp
class UTexture2D : public UTexture
{
    int32 GetSizeX() const;            // Texture2D.h:155
    int32 GetSizeY() const;            // Texture2D.h:156
    int32 GetNumMips() const;          // Texture2D.h:157
    EPixelFormat GetPixelFormat(uint32 LayerIndex = 0u) const;   // Texture2D.h:158
};
```

### 3.2 Transient 동적 생성

```cpp
// Texture2D.h:339 — 런타임 생성 (BP / 코드)
UTexture2D* DynamicTex = UTexture2D::CreateTransient(
    /*SizeX=*/ 256,
    /*SizeY=*/ 256,
    PF_B8G8R8A8,
    NAME_None,
    PixelData                       // 픽셀 데이터 (선택)
);

// FImage 로부터 생성
FImage Image;
UTexture2D* FromImage = UTexture2D::CreateTransientFromImage(&Image);
```

### 3.3 EPixelFormat (Runtime GPU 형식)

| Format | 의미 |
|--------|------|
| `PF_B8G8R8A8` | 32-bit BGRA (UI / 일반) |
| `PF_R8G8B8A8` | 32-bit RGBA |
| `PF_DXT1` (BC1) | 4-bit RGB 압축 |
| `PF_DXT5` (BC3) | 8-bit RGBA 압축 |
| `PF_BC5` | 8-bit RG (Normal Map) |
| `PF_BC6H` | HDR 압축 |
| `PF_BC7` | 8-bit RGBA 고품질 |
| `PF_FloatRGBA` | Half-float RGBA (HDR) |
| `PF_R32_FLOAT` | Single-channel Float |
| `PF_DepthStencil` | Depth + Stencil |

---

## 4. Texture Streaming

### 4.1 활성 / 비활성

```cpp
// 표준 — Streaming 활성 (LODGroup 따름)
Texture->NeverStream = false;          // Streaming ON

// 강제 비활성 (UI / 작은 Texture / VFX)
Texture->NeverStream = true;           // 모든 Mip 메모리 상주

// 모든 Mip 강제 메모리 (Boss / 캐릭터)
Texture->bForceMiplevelsToBeResident = true;

// 임시 강제 (예: 컷씬 시작)
Texture->SetForceMipLevelsToBeResident(/*Seconds=*/30.f, ...);
```

### 4.2 Mip Bias / LOD Bias

```cpp
// Texture 별 Bias
Texture->LODBias = 1;                  // Mip 1단계 낮음 (메모리 절감)

// LODGroup 별 (Project Settings)
// TEXTUREGROUP_Character LODBias = 0   (full)
// TEXTUREGROUP_Effects   LODBias = 1   (반)
```

### 4.3 모니터링

```cpp
// 콘솔 명령
// stat streaming    — Streaming 통계
// stat memorystatic — 정적 텍스처 메모리
// listusedtextures  — 현재 사용 텍스처 목록
```

---

## 5. UTextureRenderTarget2D (런타임 그리기)

### 5.1 동적 생성 (BP 그리기 / SceneCapture)

```cpp
// Constructor 안 (또는 BeginPlay)
RenderTarget = NewObject<UTextureRenderTarget2D>(this);
RenderTarget->RenderTargetFormat = ETextureRenderTargetFormat::RTF_RGBA16f;
RenderTarget->InitAutoFormat(/*Width=*/ 512, /*Height=*/ 512);
RenderTarget->UpdateResource();

// SceneCapture 가 사용
SceneCaptureComp->TextureTarget = RenderTarget;
```

### 5.2 BP 그리기 (UCanvasRenderTarget2D)

```cpp
// BP 에서 Canvas 로 그리기
UCanvasRenderTarget2D* CRT = UCanvasRenderTarget2D::CreateCanvasRenderTarget2D(
    this, UCanvasRenderTarget2D::StaticClass(), 256, 256
);

CRT->OnCanvasRenderTargetUpdate.AddDynamic(this, &AMyActor::DrawToCanvas);
CRT->UpdateResource();
```

---

## 6. UTextureCube (Reflection / SkyLight)

```cpp
// Cubemap — 6면 (Right/Left/Up/Down/Front/Back)
class UTextureCube : public UTexture
{
    int32 GetSizeX() const;
    int32 GetSizeY() const;
};

// 사용
SkyLightComp->Cubemap = LoadedCubemap;
SkyLightComp->RecaptureSky();   // 갱신
```

---

## 7. UVolumeTexture (Volumetric — Cloud / Fog)

```cpp
// 3D 텍스처 (Volumetric Cloud / Volumetric Fog)
class UVolumeTexture : public UTexture
{
    int32 GetSizeX(), GetSizeY(), GetSizeZ();
};
```

---

## 8. 5.x Virtual Texture (오픈 월드 표준)

### 8.1 활성

```cpp
// Texture.h
UPROPERTY(EditAnywhere)
uint8 VirtualTextureStreaming : 1;

// Texture 자산에서 활성 = Material 가 자동 인지
```

### 8.2 RuntimeVirtualTexture (RVT — 5.x 오픈 월드)

```cpp
// 자산 — 런타임 가상 텍스처
class URuntimeVirtualTexture : public UObject
{
    int32 TileSize;        // 타일 크기 (256 표준)
    int32 PageTableSize;
};

// 컴포넌트 = URuntimeVirtualTextureComponent
// 사용 — Landscape / 큰 Mesh 의 Texture 동적 생성
```

---

## 9. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | UI Texture LODGroup = `TEXTUREGROUP_World` | UI 그룹 = `TEXTUREGROUP_UI` (Mip 비활성, 메모리 효율) |
| 2 | Normal Map CompressionSettings = `TC_Default` | `TC_NormalMap` (BC5 — RG only, 메모리 절감) |
| 3 | 4K Texture 로 캐릭터 LODGroup = `Character` | 1K~2K 충분. LODBias 또는 World 그룹 검토 |
| 4 | `UpdateResource` 매 프레임 호출 | 비싼 작업 — 변경 시만 |
| 5 | RenderTarget Constructor 안 `InitAutoFormat` | NewObject 후 BeginPlay 또는 OnRegister |
| 6 | bForceMiplevelsToBeResident 모든 Texture 활성 | 메모리 폭발 — Boss / 캐릭터 만 |
| 7 | Editor 전용 `Source` 멤버 (`FTextureSource`) Cooked 빌드 접근 | `WITH_EDITOR` 가드 + `PlatformData` 사용 |
| 8 | NeverStream + 큰 Texture | 메모리 + 첫 로드 비용. Streaming 활성 권장 |
| 9 | 🚨 `TObjectIterator<UTexture2D>` | UAssetManager + AssetRegistry ([`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md)) |
| 10 | 🚨 큰 Texture (Boss 캐릭터 4K) PreLoad 안 함 | Match Start `PreloadPrimaryAssets` + 첫 표시 직전 `bForceMiplevelsToBeResident=true` ([`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md)) |

---

## 10. 체크리스트

- [ ] CompressionSettings 정확히 (NormalMap = BC5 / Diffuse = BC1 / UI = BC7)
- [ ] LODGroup 정확히 (Character / World / UI / Effects)
- [ ] MipGenSettings (UI = NoMipmaps / 일반 = FromTextureGroup)
- [ ] Streaming 활성 (`NeverStream = false`) — 단 작은 UI Texture 만 비활성
- [ ] bForceMiplevelsToBeResident = Boss / 캐릭터 / 첫 표시 임박 시만
- [ ] 4K Texture 사용 = LODBias 검토 (모바일 / 저사양)
- [ ] RenderTarget = NewObject (Constructor 가능) + UpdateResource 분리
- [ ] Editor 전용 Source (`FTextureSource`) 런타임 X (`WITH_EDITOR` 가드)
- [ ] 🚨 6대 정책 + 어셋 로드 정책
- [ ] Cooked Build (Development) `stat streaming` 검증

---

## 11. 관련 sub-skill

- [`AssetClasses/SKILL.md`](../SKILL.md) — 메인
- [`AssetClasses/Material`](../Material/SKILL.md) — Material 의 Texture 파라미터
- [`AssetClasses/Mesh`](../Mesh/SKILL.md) — Mesh 의 Lightmap / Shadowmap
- [`Components/RenderingComponents`](../../Components/references/RenderingComponents.md) — SceneCapture / RenderTarget
- [`Components/MeshComponents`](../../Components/references/MeshComponents.md) — Material 슬롯 (Texture 간접)
- [`UMG/UWidget`](../../UMG/references/UWidget.md) — UI Brush Texture
- 교차: 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) (Texture Streaming + bForceMiplevelsToBeResident) · [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) (FTextureSource Editor 전용)

---

## 12. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. **UTexture 2,228 lines** (TextureCompressionSettings 10종 / TextureGroup 11종 / MipGenSettings 8종 / VirtualTextureStreaming / bForceMiplevelsToBeResident / UpdateResource / BeginCacheForCookedPlatformData). **UTexture2D 397** (GetSizeX/Y / GetNumMips / GetPixelFormat / CreateTransient / CreateTransientFromImage / EPixelFormat 10종). **Texture Streaming** (NeverStream / LODBias / SetForceMipLevelsToBeResident / stat streaming). **UTextureRenderTarget2D** (NewObject + InitAutoFormat) + **UCanvasRenderTarget2D** (BP 그리기). **UTextureCube** (SkyLight). **UVolumeTexture** (Volumetric). **5.x Virtual Texture / RuntimeVirtualTexture (RVT)**. 함정 10종 + 10단 체크리스트. |
