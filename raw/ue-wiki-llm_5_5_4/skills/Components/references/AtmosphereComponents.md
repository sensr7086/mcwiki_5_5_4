---
name: components-atmospherecomponents
description: USkyAtmosphereComponent + UExponentialHeightFogComponent + UVolumetricCloudComponent + UWindDirectionalSourceComponent + 6대 정책.
---

# Components / AtmosphereComponents — 대기 + 안개 + 구름 + 바람 (Engine 모듈)

> **위치**: `Engine/Source/Runtime/Engine/Classes/Components/{SkyAtmosphereComponent,ExponentialHeightFogComponent,VolumetricCloudComponent,WindDirectionalSourceComponent}.h` (+ `SkyLightComponent` — [`LightComponents`](../LightComponents/SKILL.md))
> **베이스**: `USceneComponent` 자손 (전부)
> **요지**: **하늘·대기·안개·구름·바람** — 야외 환경의 시각 토대. 5.x 표준 워크플로 = SkyAtmosphere + DirectionalLight + SkyLight + ExpHeightFog + VolumetricCloud (5종 페어).

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

## 1. 컴포넌트 4종 한 줄 요약

| # | 컴포넌트 | 역할 |
|---|---------|------|
| 1 | `USkyAtmosphereComponent` | 물리 기반 하늘 (Rayleigh/Mie 산란) — 동적 시간 변화 가능 |
| 2 | `UExponentialHeightFogComponent` | 지수 높이 안개 + Volumetric Fog (Light Shaft 통합) |
| 3 | `UVolumetricCloudComponent` | 볼류메트릭 구름 (3D 실시간 — Movable Sun 그림자) |
| 4 | `UWindDirectionalSourceComponent` | 방향성 바람 (Foliage / Cloth / Niagara 영향) |

> **5.x 야외 표준 페어**:
> ```
> ASkyAtmosphere + ASkyLight (bRealTimeCapture=true) + ADirectionalLight (Stationary/Movable)
>     + AExponentialHeightFog + AVolumetricCloud + (선택) AWindDirectionalSource
> ```

---

## 2. USkyAtmosphereComponent — 물리 기반 대기

[`SkyAtmosphereComponent.h`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/SkyAtmosphereComponent.h):

### 2.1 핵심 필드

| 필드 | 의미 |
|------|------|
| `TransformMode` | `ESkyAtmosphereTransformMode` (PlanetTopAtAbsoluteWorldOrigin / PlanetTopAtComponentTransform / PlanetCenterAtComponentTransform) |
| `BottomRadius` | 행성 반경 (km) — 기본 6360 (지구) |
| `AtmosphereHeight` | 대기 높이 (km) — 기본 60 |
| `GroundAlbedo` | 지면 반사 색 |
| `RayleighScattering` | 청색 산란 (FLinearColor) |
| `RayleighScatteringScale` / `RayleighExponentialDistribution` | Rayleigh 분포 |
| `MieScattering` / `MieAbsorption` | Mie 산란/흡수 (대형 입자) |
| `MieScatteringScale` / `MieAbsorptionScale` | Mie 강도 |
| `OtherAbsorption` | 오존 (Ozone) 흡수 |
| `bHoldoutForCompositing` | 합성용 홀드아웃 (영화 합성) |

### 2.2 동작

> **물리 기반 — DirectionalLight 의 방향에 따라 자동 색상 변화** (일출/일몰/한낮). 시간 변화는 DirectionalLight 회전만으로.

```cpp
// Time of Day 시스템
void ATimeOfDay::Tick(float Dt)
{
    CurrentTime += Dt / DayLengthSeconds;
    SunLight->SetWorldRotation(FRotator(-CurrentTime * 360.f, 0, 0));
    // SkyAtmosphere 가 자동으로 일출/노을/한낮/일몰 색상 처리
}
```

### 2.3 SkyLight + 통합

```cpp
// SkyLight 의 RealTimeCapture = true 면 SkyAtmosphere 변화 자동 반영
SkyLight->bRealTimeCapture = true;
SkyLight->SetCastShadows(false);   // SkyLight 자체 그림자 보통 비활성
```

> **bRealTimeCapture 의 비용** ([LightComponents §10](../LightComponents/SKILL.md)) — 적당한 간격으로 캡처.

---

## 3. UExponentialHeightFogComponent — 안개 + Volumetric Fog

[`ExponentialHeightFogComponent.h:17-200`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/ExponentialHeightFogComponent.h):

### 3.1 기본 안개 (Exponential Height)

| 필드 | 의미 |
|------|------|
| `FogDensity` | 베이스 밀도 |
| `FogHeightFalloff` | 높이 감쇠율 |
| `FogInscatteringColor` | 인스캐터 색상 (legacy) |
| `FogInscatteringLuminance` | HDR 인스캐터 (5.x) |
| `StartDistance` | 안개 시작 거리 |
| `FogCutoffDistance` | 안개 끝 거리 |
| `FogMaxOpacity` | 안개 최대 불투명도 |

### 3.2 Second Fog Layer

| 필드 | 의미 |
|------|------|
| `SecondFogData.FogDensity` | 두 번째 레이어 밀도 |
| `SecondFogData.FogHeightFalloff` | 두 번째 레이어 감쇠 |
| `SecondFogData.FogHeightOffset` | 높이 오프셋 |

> **두 레이어 합성** — 지면 안개 (낮고 짙음) + 원거리 안개 (높고 옅음) 분리.

### 3.3 Volumetric Fog

| 필드 | 의미 |
|------|------|
| `bEnableVolumetricFog` | 볼류메트릭 활성 (라이트 광선 보임) |
| `VolumetricFogScatteringDistribution` | 산란 분포 (-1~1) |
| `VolumetricFogAlbedo` | 산란 색 |
| `VolumetricFogEmissive` | 자체 발광 (오로라 등) |
| `VolumetricFogExtinctionScale` | 흡수 배율 |
| `VolumetricFogDistance` | 볼류메트릭 거리 |
| `VolumetricFogStartDistance` | 시작 거리 |
| `VolumetricFogStaticLightingScatteringIntensity` | 정적 라이트 기여 |

> **bEnableVolumetricFog = true** 가 5.x 야외 표준 — 라이트 광선 (Light Shaft / God Ray) 자연스럽게.
> **비용**: 큰 영향 — Mobile 끄기, Console/PC 활용.

### 3.4 Directional Inscattering

| 필드 | 의미 |
|------|------|
| `DirectionalInscatteringExponent` | DirectionalLight 방향 인스캐터 (해 색상 효과) |
| `DirectionalInscatteringStartDistance` | 시작 거리 |
| `DirectionalInscatteringLuminance` | 강도 |

---

## 4. UVolumetricCloudComponent — 3D 실시간 구름

[`VolumetricCloudComponent.h`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/VolumetricCloudComponent.h):

### 4.1 핵심 필드

| 필드 | 의미 |
|------|------|
| `LayerBottomAltitude` | 구름 시작 고도 (km) |
| `LayerHeight` | 구름 높이 (km) |
| `TracingStartMaxDistance` | 트레이싱 시작 거리 |
| `TracingMaxDistance` | 트레이싱 최대 거리 |
| `Material` | `UMaterialInterface*` — Material Domain = `Volume` |
| `bUsePerSampleAtmosphericLightTransmittance` | 샘플별 SkyAtmosphere 빛 통과 (정확) |
| `SkyLightCloudBottomOcclusion` | 구름 바닥 SkyLight 차단 |
| `ViewSampleCountScale` | 시야 샘플 배율 |
| `ReflectionViewSampleCountScale` | 반사용 샘플 배율 |
| `ShadowViewSampleCountScale` | 그림자 샘플 배율 |
| `ShadowReflectionViewSampleCountScale` | 반사 그림자 샘플 |
| `ShadowTracingDistance` | 그림자 트레이싱 거리 |

### 4.2 비용

> **매우 비쌈** (GPU 시뮬). **`*SampleCountScale`** 로 품질/비용 트레이드. PC 1.0, Console 0.5, Mobile 비활성.
> Movable DirectionalLight 의 Cascaded Shadow 와 통합 — 구름이 땅에 그림자 던짐.

---

## 5. UWindDirectionalSourceComponent — 바람

[`WindDirectionalSourceComponent.h:23-60`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/WindDirectionalSourceComponent.h):

### 5.1 핵심 필드

```cpp
UCLASS(MinimalAPI)
class UWindDirectionalSourceComponent : public USceneComponent
{
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category=WindDirectionalSourceComponent)
    float Strength;             // 바람 세기

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category=WindDirectionalSourceComponent)
    float Speed;                // 변화 속도 (sin 진동)

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category=WindDirectionalSourceComponent)
    float MinGustAmount;        // 최소 돌풍

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category=WindDirectionalSourceComponent)
    float MaxGustAmount;        // 최대 돌풍

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category=WindDirectionalSourceComponent)
    float Radius;               // 영향 반경 (PointSource 모드) — 0 = 무한

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category=WindDirectionalSourceComponent)
    TEnumAsByte<EWindSourceType::Type> SourceType;   // Directional / PointSource
};
```

### 5.2 동작

> **+X 축 방향**으로 바람 방출. Component 회전이 바람 방향.
> **영향 대상**:
> - **Foliage** (Wind Material 노드) — Material 안 `WorldPositionOffset` 으로 흔들림
> - **Cloth** (Skeletal Mesh ClothingAsset)
> - **Niagara** (Wind Component Sample DI)
> - **Hair Strands** (Groom 플러그인)

```cpp
// 방향성 바람 (Directional)
WindSource = CreateDefaultSubobject<UWindDirectionalSourceComponent>(TEXT("Wind"));
WindSource->Strength = 1.0f;
WindSource->Speed = 0.1f;
WindSource->MinGustAmount = 0.1f;
WindSource->MaxGustAmount = 0.4f;
WindSource->SourceType = EWindSourceType::Directional;

// 토네이도 (PointSource)
TornadoWind->SourceType = EWindSourceType::PointSource;
TornadoWind->Radius = 1500.f;
TornadoWind->Strength = 5.0f;
```

---

## 6. 표준 야외 셋업 (참고)

```cpp
// AOutdoorEnvironment::AOutdoorEnvironment
// 1. SkyAtmosphere
SkyAtmo = CreateDefaultSubobject<USkyAtmosphereComponent>(TEXT("SkyAtmo"));
SkyAtmo->TransformMode = ESkyAtmosphereTransformMode::PlanetTopAtAbsoluteWorldOrigin;

// 2. SkyLight (LightComponents)
SkyLight = CreateDefaultSubobject<USkyLightComponent>(TEXT("SkyLight"));
SkyLight->bRealTimeCapture = true;
SkyLight->SourceType = SLS_CapturedScene;

// 3. DirectionalLight — 별도 Actor (보통)
// 4. ExpHeightFog
Fog = CreateDefaultSubobject<UExponentialHeightFogComponent>(TEXT("Fog"));
Fog->FogDensity = 0.02f;
Fog->FogHeightFalloff = 0.2f;
Fog->bEnableVolumetricFog = true;

// 5. VolumetricCloud
Cloud = CreateDefaultSubobject<UVolumetricCloudComponent>(TEXT("Cloud"));
Cloud->LayerBottomAltitude = 5.0f;
Cloud->LayerHeight = 8.0f;

// 6. Wind
Wind = CreateDefaultSubobject<UWindDirectionalSourceComponent>(TEXT("Wind"));
Wind->Strength = 0.5f;
```

---

## 7. 함정 & 안티패턴

| # | 함정 | 정답 |
|---|------|-----|
| 1 | SkyAtmosphere 만 추가 + SkyLight bRealTimeCapture = false | bRealTimeCapture = true (또는 RecaptureSky 매뉴얼) |
| 2 | DirectionalLight 의 Mobility = Static (시간 변화 못 함) | Stationary/Movable |
| 3 | ExpHeightFog 의 `bEnableVolumetricFog = true` 모바일 | Mobile 비활성 (cvar `r.VolumetricFog 0`) |
| 4 | VolumetricCloud `*SampleCountScale = 1.0` 모바일/저사양 | 0.25-0.5 또는 비활성 |
| 5 | VolumetricCloud Material Domain = Surface | `Volume` 필수 |
| 6 | Wind Source 추가 후 Foliage Material 에 Wind 노드 누락 | Material 안 `WorldPositionOffset` + Wind 노드 |
| 7 | SkyAtmosphere 의 `BottomRadius` 6360km 인데 Map 단위 cm | UE 단위 cm — SkyAtmosphere 의 km 단위 주의 |
| 8 | 매 Tick SkyAtmosphere 옵션 변경 (재컴파일) | 변경 시점에만 |
| 9 | 🚨 환경 컴포넌트 callback 첫 줄 프로파일링 스코프 누락 | 의무 ([`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)) |

---

## 8. 체크리스트

- [ ] 야외 5종 페어 (SkyAtmo + SkyLight + DirLight + ExpHeightFog + Cloud)
- [ ] DirectionalLight Mobility = Stationary 또는 Movable (시간 변화)
- [ ] SkyLight bRealTimeCapture 검토
- [ ] ExpHeightFog: bEnableVolumetricFog 플랫폼별
- [ ] VolumetricCloud: SampleCountScale 플랫폼별
- [ ] VolumetricCloud Material = Volume Domain
- [ ] Wind Source: Foliage Material 에 Wind 노드 페어
- [ ] Wind Strength + Gust 적정 (1.0 이상이면 Cloth 폭주)

---

## 9. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. 4개 AtmosphereComponents — USkyAtmosphereComponent (Rayleigh/Mie 물리 기반 + 시간 변화 자동 반영) + UExponentialHeightFogComponent (Exp + Second Layer + Volumetric Fog + Directional Inscattering) + UVolumetricCloudComponent (3D 실시간 + ShadowSampleCount) + UWindDirectionalSourceComponent (Foliage/Cloth/Niagara 영향). 5.x 야외 5종 페어 표준 셋업 + 함정 9종. |
