---
name: components-lightcomponents
description: UPointLight + USpotLight + URectLight + UDirectionalLight + USkyLight + ULocalLight + Mobility 매트릭스 (Static/Stationary/Movable) + 6대 정책.
---

# Components / LightComponents — 라이트 (Engine 모듈)

> **위치**: `Engine/Source/Runtime/Engine/Classes/Components/{LightComponentBase,LightComponent,LocalLightComponent,PointLightComponent,SpotLightComponent,RectLightComponent,DirectionalLightComponent,SkyLightComponent,LightmassPortalComponent}.h`
> **베이스**: `USceneComponent` → `ULightComponentBase` (abstract) → `ULightComponent` (abstract) → `ULocalLightComponent` (abstract) → `UPointLightComponent` → `USpotLightComponent` / `URectLightComponent`. 평행 광은 `ULightComponent` 직속, 환경 광은 `ULightComponentBase` 직속 (SkyLight).
> **요지**: **Mobility (Static/Stationary/Movable) 가 비용의 핵심** — Movable = 매 프레임 Shadow Map. **광원 개수 + Shadow + Volumetric** 이 GPU 시간의 60% 이상을 차지하는 흔한 병목. 본 sub-skill 은 7종 라이트 + Shadow / Volumetric / Reflection 비용 매트릭스.

---

## 🚨 공통 정책 (Components 6대 의무)

> 모든 컴포넌트는 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) 의 5대 정책 적용.

| # | 정책 | 핵심 규칙 |
|---|------|-----------|
| 1 | **Mobility** | 생성자에서 `Static`/`Stationary`/`Movable` 명시. 런타임 `SetMobility` 금지 ([§1](../../../references/10_ComponentPolicies.md#1-mobility-정책-ecomponentmobilitystatic-stationary-movable)) |
| 2 | **NewObject + DuplicateObject** | Constructor=`CreateDefaultSubobject` / 런타임=`NewObject<T>(this)` / Deep copy=`DuplicateObject<T>(Source, Outer)` ([§2](../../../references/10_ComponentPolicies.md#2-newobject--duplicateobject-정책)) |
| 3 | **GC 방어** | UObject 멤버 = `UPROPERTY()` + `TObjectPtr<T>`. 비-UCLASS = `TStrongObjectPtr<T>` ([§3](../../../references/10_ComponentPolicies.md#3-gc-방어-전략)) |
| 4 | **GetOwner 캐싱** | `BeginPlay` 에서 `TWeakObjectPtr<AOwner>` 1회 캐싱. Tick/콜백 안 매번 Cast 금지 ([§4](../../../references/10_ComponentPolicies.md#4-getowner-캐싱-정책)) |
| 5 | **PrimaryComponentTick** | 기본 `bCanEverTick = false`. 필요 시 `TickInterval` 우선 (0.1~1s). 매 프레임 = 마지막 수단 ([§5](../../../references/10_ComponentPolicies.md#5-primarycomponenttick-정책)) |
| 6 | **CDO** | `GetMutableDefault` 로 CDO 변경 금지. `PostInitProperties` 안 `HasAnyFlags(RF_ClassDefaultObject)` 검사. `CreateDefaultSubobject` 는 Constructor 안만 ([§6](../../../references/10_ComponentPolicies.md#6-cdo-class-default-object-정책)) |

---

## 1. 상속 트리

```
USceneComponent
└── ULightComponentBase  (abstract)         — Intensity / LightColor / CastShadows / 베이스 옵션
    ├── ULightComponent  (abstract)         — Temperature / IES Profile / MaxDrawDistance / Shadow*
    │   ├── ULocalLightComponent  (abstract) — AttenuationRadius / IntensityUnits (lumens/cd/lux/EV)
    │   │   ├── UPointLightComponent        — bUseInverseSquaredFalloff / SourceRadius / SourceLength
    │   │   │   └── USpotLightComponent     — InnerConeAngle / OuterConeAngle (degrees)
    │   │   └── URectLightComponent         — SourceWidth / SourceHeight / BarnDoor*
    │   └── UDirectionalLightComponent      — Cascaded Shadow Maps (CSM) + LightShafts
    └── USkyLightComponent                  — 환경광 (Cubemap or Real-time Capture)

USceneComponent
└── ULightmassPortalComponent               — Lightmass Bake 힌트 (Static 전용 — 런타임 비용 없음)
```

> **ULightComponent 자손은 9개**:
> 1. `UPointLightComponent` (전구)
> 2. `USpotLightComponent` (스폿/손전등)
> 3. `URectLightComponent` (사각형 패널)
> 4. `UDirectionalLightComponent` (태양/달)
> 5. `USkyLightComponent` (환경광 — `ULightComponent` 자손 아님 — `ULightComponentBase` 직속)
> 6. `ULightmassPortalComponent` — 빌드 힌트 (라이트 아님)

---

## 2. Mobility — 비용의 핵심

[`SceneComponent.h`] `Mobility` 필드 — Light 의 동작·비용 결정.

| Mobility | Shadow | Lighting | 비용 | 사용 |
|----------|--------|----------|------|------|
| **Static** | Lightmap (precomputed) | Lightmap | **0 (런타임)** | Lightmass 빌드 시 Bake — 변경 안 함 |
| **Stationary** | Static + Dynamic 합성 (CSM 거리 안에서만) | Lightmap (Direct) + Realtime (Direct) | 중간 | 위치 고정·Color/Intensity 변경 가능 |
| **Movable** | Realtime Shadow Map | Realtime | **가장 비쌈** | 캐릭터·물건에 부착 — 매 프레임 |

> **Mobility 변경은 에디터에서만** — 런타임에 `SetMobility` 호출 금지 (Lightmass 데이터 무효).

```cpp
// 생성자 — Mobility 설정
PointLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("PointLight"));
PointLight->SetMobility(EComponentMobility::Movable);  // Player 손전등
PointLight->Intensity = 5000.f;        // lumens (bUseInverseSquaredFalloff 시 luminous flux)
PointLight->AttenuationRadius = 1000.f;
PointLight->SetCastShadows(true);
```

---

## 3. ULightComponentBase — 모든 라이트의 베이스

[`LightComponentBase.h:13-120`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/LightComponentBase.h):

### 3.1 핵심 필드

| 필드 | 의미 |
|------|------|
| `Intensity` | 광원 총 에너지 (자식별로 단위 다름) |
| `LightColor` | 색상 필터 (FColor) |
| `bAffectsWorld` | 라이트 활성 (false 시 무시 — Lightmass 재빌드 트리거) |
| `CastShadows` | 그림자 캐스팅 (전체 토글) |
| `CastStaticShadows` | Static 객체 그림자 |
| `CastDynamicShadows` | Dynamic 객체 그림자 (Movable + 동적 캐릭터) |
| `bAffectTranslucentLighting` | 투명 객체에 영향 (작은 라이트 많을 때 비활성 권장) |
| `bTransmission` | 서브서피스 산란 통과 — Movable 전용 |
| `bCastVolumetricShadow` | Volumetric Fog 그림자 |
| `bCastDeepShadow` | Hair 자기 그림자 |
| `CastRaytracedShadow` | Ray-Traced Shadow (`ECastRayTracedShadow::Type` enum) |
| `bAffectReflection` | Ray-Traced Reflection 영향 |
| `bAffectGlobalIllumination` | Ray-Traced GI 영향 |
| `IndirectLightingIntensity` | GI 기여 배율 (0 = GI 비활성) |
| `VolumetricScatteringIntensity` | Volumetric 산란 기여 |

### 3.2 비용 토글 (성능 최적화 핵심)

```cpp
// 작은 fill 라이트 — Translucent / Volumetric 영향 없음으로 비용 절감
SmallFillLight->bAffectTranslucentLighting = false;
SmallFillLight->bCastVolumetricShadow = false;
SmallFillLight->bAffectReflection = false;        // RT Reflection 비활성
SmallFillLight->bAffectGlobalIllumination = false; // RT GI 비활성
SmallFillLight->IndirectLightingIntensity = 0.f;   // Lightmass 기여 0 (Static 시 의미)
```

---

## 4. ULightComponent — Temperature / IES / Shadow*

[`LightComponent.h:45-200`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/LightComponent.h):

### 4.1 핵심 필드

| 필드 | 의미 |
|------|------|
| `Temperature` | 색온도 (Kelvin) — D65 = 6500K, 백열 = 2700K, 주광 = 5500K |
| `bUseTemperature` | Temperature 활성 |
| `MaxDrawDistance` | 라이트 컬링 거리 — 0 = 무제한 |
| `MaxDistanceFadeRange` | MaxDrawDistance 도달 전 페이드 범위 |
| `SpecularScale` / `DiffuseScale` | 비물리적 — 특수 효과만 |
| `ShadowResolutionScale` | Shadow Map 해상도 배율 (0 = 비활성) |
| `ShadowBias` / `ShadowSlopeBias` | 그림자 자기 그림자 보정 |
| `ContactShadowLength` | 매우 짧은 거리 self-shadow (Screen-space) |
| `IESTexture` | IES 광원 분포 (실제 조명 데이터) |
| `LightFunctionMaterial` | 라이트 함수 (스포트라이트 영상 효과) |
| `LightingChannels` | LightingChannel0/1/2 — 라이트가 영향 줄 객체 채널 |

### 4.2 LightingChannels (성능 + 아트 디렉션)

```cpp
// 캐릭터 전용 라이트 — 환경에 영향 없음
CharacterRimLight->LightingChannels.bChannel0 = false;  // 기본 World 채널 끔
CharacterRimLight->LightingChannels.bChannel1 = true;   // Channel 1 만 — Character Mesh 도 동일 채널

// Character Mesh
CharacterMesh->LightingChannels.bChannel0 = true;       // World 라이트 받음
CharacterMesh->LightingChannels.bChannel1 = true;       // RimLight 받음
```

> **3채널 (0/1/2)** — Mesh 와 Light 양쪽 매칭되는 비트가 있어야 영향. 비물리적 — 컨셉아트/모바일 우선.

---

## 5. ULocalLightComponent — Point/Spot/Rect 베이스

[`LocalLightComponent.h:17-80`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/LocalLightComponent.h):

### 5.1 핵심 필드

| 필드 | 의미 |
|------|------|
| `IntensityUnits` | `ELightUnits` — Unitless / Candelas / Lumens / EV / Nits / Lux |
| `AttenuationRadius` | 라이트 영향 반경 — **비물리적** 컬링 (큰 값 = 비쌈) |
| `LightmassSettings` | Lightmass Bake 옵션 (`FLightmassPointLightSettings`) |
| `InverseExposureBlend` | Intensity / Exposure 블렌드 |

### 5.2 IntensityUnits 변환

[`LocalLightComponent.h:58-59`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/LocalLightComponent.h):

```cpp
UFUNCTION(BlueprintPure, Category="Rendering|Lighting")
static ENGINE_API float GetUnitsConversionFactor(ELightUnits SrcUnits, ELightUnits TargetUnits, float CosHalfConeAngle = -1);
```

| Unit | 의미 | 사용 |
|------|------|------|
| `Unitless` | 0~∞ | 레거시 (5.0 이전) |
| `Candelas` | 광원 방향 광도 | 스포트라이트 표준 |
| `Lumens` | 광원 총 광량 | 일반 전구 (예: 100W = 1700 lm) |
| `EV` | Exposure Value | 사진 노출 |
| `Nits` | 표면 광도 | RectLight 패널 |
| `Lux` | 조명도 | DirectionalLight |

```cpp
PointLight->IntensityUnits = ELightUnits::Lumens;
PointLight->Intensity = 1700.f;   // 100W 전구
```

### 5.3 AttenuationRadius — 큰 값 = 비싼 라이트

```cpp
// 너무 큰 반경 — 컬링 안 되고 매 픽셀 검사
PointLight->AttenuationRadius = 5000.f;   // 가장 흔한 실수

// 정답 — 시각적으로 의미 있는 거리만
PointLight->AttenuationRadius = 800.f;    // 캐릭터 손전등 정도
```

> **비용 = O(AttenuationRadius² × CastShadows × Mobility)**. Movable + 큰 반경 + Shadow ON = GPU 폭사.

---

## 6. UPointLightComponent — 전구

[`PointLightComponent.h:18-97`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/PointLightComponent.h):

| 필드 | 의미 |
|------|------|
| `bUseInverseSquaredFalloff` | 물리 기반 거리² 감쇠 (true = lumens 단위) |
| `LightFalloffExponent` | 비물리 모드 감쇠 (2 = 거의 선형, 8 = 사실적) |
| `SourceRadius` / `SoftSourceRadius` | 광원 모양 반경 (Soft Shadow) |
| `SourceLength` | 광원 모양 길이 (튜브 라이트) |

> **bUseInverseSquaredFalloff = true** 가 5.x 표준 — `LightFalloffExponent` 무시. False 는 레거시·예술적 컨트롤.

---

## 7. USpotLightComponent — 손전등 / 무대 조명

[`SpotLightComponent.h:16-52`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/SpotLightComponent.h):

```cpp
class USpotLightComponent : public UPointLightComponent
{
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category=Light, meta=(UIMin = "1.0", UIMax = "80.0"))
    float InnerConeAngle;       // 풀 강도 영역 (degrees)

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category=Light, meta=(UIMin = "1.0", UIMax = "80.0"))
    float OuterConeAngle;       // 페이드 끝 (degrees)

    ENGINE_API float GetHalfConeAngle() const;
    ENGINE_API float GetCosHalfConeAngle() const;

    virtual FSphere GetBoundingSphere() const override;
    virtual bool AffectsBounds(const FBoxSphereBounds& InBounds) const override;
};
```

> Inner < Outer. Inner = Outer 면 hard 가장자리 (무대 조명).
> 컬링 정확도: Bounding Sphere = `AttenuationRadius * sin(OuterConeAngle/2)` 가 아닌 conical bounds — `AffectsBounds` override 로 정밀 컬링.

---

## 8. URectLightComponent — 사각 패널 (TV / 창문)

[`RectLightComponent.h:23-60`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/RectLightComponent.h):

| 필드 | 의미 |
|------|------|
| `SourceWidth` | 패널 가로 |
| `SourceHeight` | 패널 세로 |
| `BarnDoorAngle` | Barn Door 가림판 각도 (0-90°) |
| `BarnDoorLength` | Barn Door 길이 |
| `LightFunctionConeAngle` | LightFunction 투영 각 (0 = orthographic) |
| `SourceTexture` | 패널 텍스쳐 (TV 화면 빛) |

> **Barn Door**: 사진 스튜디오 라이트 가림판 — 패널 라이트 바운딩 좁히기. RectLight 만 지원.
> **비용**: Point/Spot 보다 비쌈 (Surface Light 적분).

---

## 9. UDirectionalLightComponent — 태양 / 달

[`DirectionalLightComponent.h:18-200`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/DirectionalLightComponent.h):

> `ULocalLightComponent` 자손 **아님** — `ULightComponent` 직속. AttenuationRadius 무한 (평행광).

### 9.1 Cascaded Shadow Map (CSM) — Movable 핵심

| 필드 | 의미 |
|------|------|
| `DynamicShadowDistanceMovableLight` | Movable 시 Shadow 커버 거리 (cm) — 0 = 비활성 |
| `DynamicShadowDistanceStationaryLight` | Stationary 시 Shadow 커버 거리 |
| `DynamicShadowCascades` | Cascade 분할 개수 (0~4) — 많을수록 해상도 ↑ + 비용 ↑ |
| `CascadeDistributionExponent` | Cascade 분포 (1 = 비례, 4 = 카메라 가까이 집중) |
| `CascadeTransitionFraction` | Cascade 전환 페이드 (0~0.3) |
| `ShadowDistanceFadeoutFraction` | Shadow 끝 페이드 |
| `ShadowCascadeBiasDistribution` | Cascade 별 Bias 스케일 (0~1) |

### 9.2 Light Shafts (God Rays)

| 필드 | 의미 |
|------|------|
| `bEnableLightShaftOcclusion` | 안개에 차단됨 |
| `OcclusionMaskDarkness` | 차단 어둠 강도 |
| `OcclusionDepthRange` | 차단 거리 |
| `LightShaftOverrideDirection` | 시각적 방향 (실제 라이트 방향과 다르게 — 미적) |

```cpp
// 표준 태양 셋업
SunLight = CreateDefaultSubobject<UDirectionalLightComponent>(TEXT("SunLight"));
SunLight->SetMobility(EComponentMobility::Stationary);   // CSM + Lightmap 합성
SunLight->Intensity = 10.f;        // Lux 단위면 10000 lux (한낮)
SunLight->IntensityUnits = ELightUnits::Lux;
SunLight->Temperature = 5500.f;
SunLight->bUseTemperature = true;
SunLight->DynamicShadowCascades = 3;
SunLight->DynamicShadowDistanceMovableLight = 5000.f;   // 50m
SunLight->CascadeDistributionExponent = 3.f;
```

---

## 10. USkyLightComponent — 환경광 (HDR Cubemap or Real-time Capture)

[`SkyLightComponent.h:101-200`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/SkyLightComponent.h):

> `ULightComponentBase` 직속 (ULightComponent 자손 아님).

### 10.1 SourceType (`SkyLightComponent.h:84-91`)

```cpp
UENUM()
enum ESkyLightSourceType : int
{
    SLS_CapturedScene,        // 실시간 캡처 (SkyAtmosphere/Cloud + 스카이박스 메시)
    SLS_SpecifiedCubemap,     // 미리 만든 HDR 큐브맵
};
```

### 10.2 핵심 필드

| 필드 | 의미 |
|------|------|
| `bRealTimeCapture` | 매 프레임 캡처 (구름 변화 등 동적) — 비쌈 |
| `SourceType` | CapturedScene vs Cubemap |
| `Cubemap` | `UTextureCube` (SLS_SpecifiedCubemap) |
| `SourceCubemapAngle` | Cubemap 회전 |
| `SkyDistanceThreshold` | 스카이 인식 거리 (이 이상이면 환경) |
| `LowerHemisphereColor` | 하반구 단순 색 |
| `OcclusionMaxDistance` | DFAO (Distance Field Ambient Occlusion) 최대 거리 |
| `Contrast` / `MinOcclusion` | DFAO 컨트라스트/최소 |

> **Real-time Capture 비용**: 매 프레임 6면 캡처 + Convolution. **bRealTimeCapture = false** 가 표준 (한 번 캡처 후 정적 사용).
> **`RecaptureSky`** 호출로 명시적 재캡처: `SkyLight->RecaptureSky();`.

---

## 11. ULightmassPortalComponent — Bake 힌트 (Static 전용)

[`LightmassPortalComponent.h:11-20`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/LightmassPortalComponent.h):

> 라이트 **아님** — Lightmass 빌드 시 환경광 진입 영역 힌트 (창문 등). **런타임 비용 0**.

```cpp
UCLASS(hidecategories=(Collision, Object, Physics, SceneComponent, Activation, Mobility), MinimalAPI)
class ULightmassPortalComponent : public USceneComponent
{
    GENERATED_UCLASS_BODY()
    // 시각적 박스 모양만 — Lightmass 빌드 시 영향
};
```

---

## 12. 라이트 비용 매트릭스 (실전 가이드)

### 12.1 Mobility × Type 비용

| Type | Static | Stationary | Movable |
|------|--------|-----------|---------|
| Directional | Lightmap | Lightmap + CSM (제한 거리) | **CSM 전체** — 가장 비쌈 |
| Point | Lightmap | Lightmap + Realtime Direct | **Realtime + Shadow Map (큐브맵 6면)** |
| Spot | Lightmap | Lightmap + Realtime Direct | Realtime + Shadow Map (1면) — Point 보다 저렴 |
| Rect | Lightmap | Lightmap + Realtime Direct | Realtime + Surface Integration — Point 보다 비쌈 |
| Sky | Lightmap | Lightmap + DFAO | Real-time Capture — bRealTimeCapture 시 매우 비쌈 |

### 12.2 빠른 절감 체크리스트

- [ ] **장식용 라이트는 Static** — Mobility = Static 면 런타임 비용 0
- [ ] **캐릭터 따라가는 라이트는 Movable + 작은 AttenuationRadius (300~800)**
- [ ] **AttenuationRadius 가능한 작게** — 시각 영향 끝 = 컬링 끝
- [ ] **CastShadows = false** — 작은 fill / 디테일 라이트
- [ ] **bAffectTranslucentLighting = false** — 작은 라이트 (UI/안 보이는 효과)
- [ ] **bCastVolumetricShadow = false** — 안개 안 영향 안 받는 라이트
- [ ] **MaxDrawDistance** 설정 — 멀어지면 컬
- [ ] **CSM Cascade 개수 줄이기** — Mobile 1-2, PC Console 3, High-End 4
- [ ] **SkyLight bRealTimeCapture = false** — 정적 환경 표준
- [ ] **LightingChannels** 활용 — 캐릭터 전용 라이트는 Channel 0 끔
- [ ] **IES Profile** 정확하게 — 광원 데이터 시뮬

---

## 13. Significance 통합 (거리 기반 라이트 토글)

[`Significance/SKILL.md`](../../Significance/SKILL.md) 와 통합 — NPC 멀어지면 라이트 비활성:

```cpp
void UMyLightSignificance::Tick(USignificanceManager& Manager, FTransform InVT, float InSig)
{
    auto* Light = LightWeak.Get();
    if (!Light) return;

    if (InSig < 0.1f)
    {
        // 멀리 — 라이트 끔
        Light->SetVisibility(false);
    }
    else if (InSig < 0.5f)
    {
        // 중간 — Shadow 끔
        Light->SetVisibility(true);
        Light->SetCastShadows(false);
        Light->SetIntensity(BaseIntensity * 0.5f);
    }
    else
    {
        // 가까이 — 풀 옵션
        Light->SetVisibility(true);
        Light->SetCastShadows(true);
        Light->SetIntensity(BaseIntensity);
    }
}
```

> **NPC 손전등**·**자동차 헤드라이트** 등 다수 라이트 환경의 표준 패턴. CastShadows 토글이 가장 비용 절감.

---

## 14. 함정 & 안티패턴

| # | 함정 | 정답 |
|---|------|-----|
| 1 | Movable 라이트 100개 + Shadow ON | 거리에 따라 Significance 로 Shadow 토글 |
| 2 | AttenuationRadius 5000 (시각적 끝 100) | 시각 끝까지만 — 컬링 효과 |
| 3 | bUseInverseSquaredFalloff = false 신규 코드 | 5.x 표준은 true (lumens 단위) |
| 4 | Mobility 런타임 변경 (`SetMobility`) | 에디터에서만 — Lightmass 데이터 무효 |
| 5 | SkyLight bRealTimeCapture = true 항상 | 정적 환경은 false + 명시 RecaptureSky |
| 6 | 모든 라이트에 Channel 0 사용 (LightingChannels 활용 0) | 캐릭터 전용 라이트는 Channel 1 분리 |
| 7 | DirectionalLight CSM Cascade 4 + Distance 무한 | Mobile = 1-2, 거리 5000-10000 표준 |
| 8 | RectLight 를 단순 사각 영역 표시에 사용 | RectLight 는 비쌈 — 단순 영역은 Decal 또는 Spot |
| 9 | LightFunctionMaterial 매 프레임 변경 | LightFunction 은 정적 (애니메이션은 머티리얼 안에서) |
| 10 | Stationary 라이트 5개 이상 겹침 (4 채널 압축 한계) | 영역 분리 또는 1개를 Movable 로 |
| 11 | 🚨 **Tick 안 라이트 Intensity 변경** (Modify 호출 등) | `SetIntensity` 만 호출 (매 프레임 OK) — Modify 불필요 |
| 12 | 🚨 **OnConstruction 에서 Light 생성/제거** | 생성자 또는 BeginPlay — Construction Script 는 빠르게 |

---

## 15. 체크리스트 (라이트 컴포넌트 작성)

- [ ] Type 선택: Sun = Directional, 전구 = Point, 손전등 = Spot, TV = Rect, 환경 = Sky
- [ ] Mobility 명시 (Static/Stationary/Movable)
- [ ] `IntensityUnits` 정확히 (Lumens/Candelas/Lux/Nits)
- [ ] `AttenuationRadius` 가능한 작게 (시각 끝)
- [ ] `MaxDrawDistance` + `MaxDistanceFadeRange` 설정
- [ ] `CastShadows` 진정 필요? 작은 라이트는 false
- [ ] `bAffectTranslucentLighting` / `bCastVolumetricShadow` 필요한 것만
- [ ] DirectionalLight: `DynamicShadowCascades` + `DynamicShadowDistance*` 적정
- [ ] SkyLight: `bRealTimeCapture` 진짜 필요? 정적이면 false + RecaptureSky
- [ ] `LightingChannels` 활용 — 캐릭터 전용 라이트 분리
- [ ] Significance 통합 — 거리 기반 Shadow / Intensity 토글
- [ ] 🚨 Tick 안 라이트 다수 검사 시 `TActorIterator` 사용 안 함 — 등록 패턴 ([`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md))

---

## 16. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. ULightComponentBase (베이스 옵션 + bAffectTranslucentLighting 등 비용 토글) → ULightComponent (Temperature/MaxDrawDistance/IES/LightFunction/LightingChannels) → ULocalLightComponent (AttenuationRadius/IntensityUnits 6종) → UPointLightComponent (InverseSquared/SourceRadius/SourceLength) → USpotLightComponent (Inner/Outer Cone) / URectLightComponent (Source W/H + BarnDoor + Texture) / UDirectionalLightComponent (CSM 7개 옵션 + LightShafts) → USkyLightComponent (Real-time Capture vs Cubemap + DFAO) + ULightmassPortalComponent (Bake 힌트). Mobility × Type 비용 매트릭스 + 절감 체크리스트 + Significance 통합 + 함정 12종. |
