---
name: components-renderingcomponents
description: UDecalComponent + UTextRenderComponent + USceneCaptureComponent2D + USceneCaptureComponentCube + UPostProcessComponent + 6대 정책.
---

# Components / RenderingComponents — Decal + TextRender + SceneCapture + Billboard (Engine 모듈)

> **위치**: `Engine/Source/Runtime/Engine/Classes/Components/{DecalComponent,TextRenderComponent,BillboardComponent,MaterialBillboardComponent,SceneCaptureComponent,SceneCaptureComponent2D,SceneCaptureComponentCube,PostProcessComponent,DrawSphereComponent,DrawFrustumComponent,ArrowComponent}.h`
> **베이스**: `USceneComponent` (Decal/SceneCapture/PostProcess) 또는 `UPrimitiveComponent` (Billboard/Arrow/TextRender/MaterialBillboard/DrawFrustum)
> **요지**: **렌더링 보조 컴포넌트 11종** — 표면 데칼, 3D 텍스트, Billboard 아이콘, 거울/카메라 캡처, PostProcess Volume 대체.

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
| 🎯 **어셋 로드** | 🚨 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) — **Decal Material / TextRender Font / Billboard Texture / SceneCapture RenderTarget / PostProcess Material = Soft + Pre-Load 표준** (특히 PostProcess Material 은 매우 큼 — Lumen 영향). SceneCapture 의 RenderTarget = 동적 생성 (`UTextureRenderTarget2D::CreateDefaultSubobject` 또는 `NewObject` + 메모리 큼). Decal Material PSO 컴파일 = 첫 표시 히칭. |

---

## 1. 컴포넌트 11종 한 줄 요약

| # | 컴포넌트 | 베이스 | 역할 |
|---|---------|--------|------|
| 1 | `UDecalComponent` | `USceneComponent` | 표면에 머티리얼 투영 (피탄·발자국·핏자국) |
| 2 | `UTextRenderComponent` | `UPrimitiveComponent` | 3D 텍스트 (이름표·툴팁) |
| 3 | `UBillboardComponent` | `UPrimitiveComponent` | 단순 카메라 향한 스프라이트 (에디터 아이콘) |
| 4 | `UMaterialBillboardComponent` | `UPrimitiveComponent` | 머티리얼 기반 빌보드 (런타임용) |
| 5 | `USceneCaptureComponent` (abstract) | `USceneComponent` | 카메라 캡처 베이스 |
| 6 | `USceneCaptureComponent2D` | `USceneCaptureComponent` | 2D 캡처 (거울/CCTV/미니맵) |
| 7 | `USceneCaptureComponentCube` | `USceneCaptureComponent` | Cubemap 캡처 (반사 확률) |
| 8 | `UPostProcessComponent` | `USceneComponent` (+`IInterface_PostProcessVolume`) | PostProcessVolume 대체 (Actor 단위) |
| 9 | `UArrowComponent` | `UPrimitiveComponent` | 에디터 방향 화살표 |
| 10 | `UDrawSphereComponent` | `USphereComponent` | 에디터 디버그 스피어 |
| 11 | `UDrawFrustumComponent` | `UPrimitiveComponent` | 에디터 프러스텀 (카메라 시야) |

---

## 2. UDecalComponent — 표면 데칼

[`DecalComponent.h:24-200`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/DecalComponent.h):

### 2.1 핵심 필드

| 필드 | 의미 |
|------|------|
| `DecalMaterial` | `UMaterialInterface*` — `Material Domain = Deferred Decal` |
| `DecalSize` | `FVector` — 박스 영역 (X 가 투영 방향) |
| `FadeStartDelay` | 페이드 시작 지연 (s) |
| `FadeDuration` | 페이드 시간 |
| `FadeScreenSize` | 화면 비율 미만이면 페이드 |
| `bDestroyOwnerAfterFade` | 페이드 후 Owner 삭제 |
| `SortOrder` | 같은 위치 데칼 우선순위 |

### 2.2 표준 사용

```cpp
// 발사 흔적
UGameplayStatics::SpawnDecalAtLocation(
    GetWorld(),
    BulletDecalMaterial,
    FVector(8.f, 8.f, 8.f),                   // Size
    Hit.Location,
    Hit.Normal.Rotation(),                     // X 가 -Normal 방향
    /*LifeSpan=*/10.f);

// 또는 Mesh 에 부착 (이동 표면)
UDecalComponent* Decal = UGameplayStatics::SpawnDecalAttached(
    DecalMaterial, FVector(8), HitMesh, NAME_None,
    Hit.Location, Hit.Normal.Rotation(),
    EAttachLocation::KeepWorldPosition,
    /*LifeSpan=*/30.f);
```

### 2.3 비용

> **데칼 비용 = 화면 차지 영역 × Material 복잡도** — Deferred Decal 은 G-Buffer 패스에서 후 합성. `DecalSize` 작게 + `FadeScreenSize` 활용.

---

## 3. UTextRenderComponent — 3D 텍스트

[`TextRenderComponent.h`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/TextRenderComponent.h):

### 3.1 핵심 필드

| 필드 | 의미 |
|------|------|
| `Text` | `FText` — 표시 텍스트 (다국어) |
| `TextMaterial` | 머티리얼 (`Used with TextRender3d`) |
| `Font` | `UFont*` |
| `TextRenderColor` | 색상 |
| `XScale` / `YScale` | 스케일 |
| `WorldSize` | 월드 크기 (단위) |
| `HorizontalAlignment` | `EHorizTextAligment` (Left/Center/Right) |
| `VerticalAlignment` | `EVerticalTextAligment` (Top/Center/Bottom/QuadTop) |
| `bAlwaysRenderAsText` | 비텍스처 폰트 — 항상 텍스트 렌더 |

### 3.2 동작

```cpp
TextComp = CreateDefaultSubobject<UTextRenderComponent>(TEXT("Label"));
TextComp->SetupAttachment(RootComponent);
TextComp->SetText(FText::FromString(TEXT("Player Name")));
TextComp->SetTextRenderColor(FColor::White);
TextComp->WorldSize = 32.f;
TextComp->HorizontalAlignment = EHTA_Center;
TextComp->VerticalAlignment = EVRTA_TextCenter;
```

> **`SetText` (FText)** 사용 — 다국어. `SetTextValue` (블루프린트 우선).
> **WorldSize** 가 글자 높이 — 화면 상수 텍스트 원하면 매 Tick 거리 기반 스케일 (또는 UMG WidgetComponent).

---

## 4. UBillboardComponent / UMaterialBillboardComponent

### 4.1 UBillboardComponent — 에디터 아이콘 위주

[`BillboardComponent.h:19-100`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/BillboardComponent.h):

| 필드 | 의미 |
|------|------|
| `Sprite` | `UTexture2D*` — 표시 텍스쳐 |
| `bIsScreenSizeScaled` | 화면 비율로 자동 스케일 |
| `ScreenSize` | 화면 비율 (0.0025 표준) |
| `U` / `V` / `UL` / `VL` | UV 영역 (텍스쳐 내 일부) |
| `OpacityMaskRefVal` | 알파 임계 |

> **에디터 전용 시각화** — `UPROPERTY(VisibleAnywhere, Category=Sprite)` 같은 컴포넌트가 자동 스폰. 런타임 빌보드는 `UMaterialBillboardComponent` 사용.

### 4.2 UMaterialBillboardComponent — 런타임용

| 필드 | 의미 |
|------|------|
| `Elements` | `TArray<FMaterialSpriteElement>` — 다중 빌보드 |
|   `.Material` | `UMaterialInterface*` |
|   `.bSizeIsInScreenSpace` | 화면 비율 vs 월드 |
|   `.BaseSizeX/Y` | 크기 |
|   `.DistanceToOpacityCurve` | 거리 ↔ 알파 |
|   `.DistanceToSizeCurve` | 거리 ↔ 크기 |

> **UI 위 떠다니는 머티리얼 효과** (HP바 / 데미지 숫자 등) — UMG WidgetComponent 가 더 일반적이지만 머티리얼 자유도가 더 큼.

---

## 5. USceneCaptureComponent (abstract) → 2D / Cube

[`SceneCaptureComponent.h:72-200`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/SceneCaptureComponent.h):

### 5.1 베이스 필드

| 필드 | 의미 |
|------|------|
| `ShowFlags` | `FEngineShowFlags` — 캡처할 패스 (DynamicShadows 등) |
| `HiddenActors` | 캡처에서 숨길 Actor |
| `ShowOnlyActors` | 캡처에 표시할 Actor (whitelist) |
| `bCaptureEveryFrame` | 매 프레임 캡처 (비쌈) |
| `bCaptureOnMovement` | 이동 시만 캡처 |
| `LODDistanceFactor` | LOD 거리 배율 |
| `MaxViewDistanceOverride` | 최대 시야 거리 |

### 5.2 USceneCaptureComponent2D

| 필드 | 의미 |
|------|------|
| `ProjectionType` | Perspective/Orthographic |
| `FOVAngle` | FOV |
| `OrthoWidth` | 직교 가로 |
| `TextureTarget` | `UTextureRenderTarget2D*` — 캡처 결과 |
| `CaptureSource` | `ESceneCaptureSource` (FinalColor / SceneColor / SceneDepth 등) |
| `CompositeMode` | `ESceneCaptureCompositeMode` |
| `PostProcessSettings` | 캡처 PostProcess 오버라이드 |

```cpp
// CCTV / 미니맵 / 거울
SceneCapture = CreateDefaultSubobject<USceneCaptureComponent2D>(TEXT("Capture"));
SceneCapture->TextureTarget = MyRenderTarget;
SceneCapture->FOVAngle = 90.f;
SceneCapture->bCaptureEveryFrame = false;     // 수동 호출
SceneCapture->bCaptureOnMovement = false;
// 매 N 프레임 명시 캡처
GetWorld()->GetTimerManager().SetTimer(CaptureTimer, [this]()
{
    TRACE_CPUPROFILER_EVENT_SCOPE(SceneCapture_Manual);
    SceneCapture->CaptureScene();
}, 0.1f, true);
```

### 5.3 USceneCaptureComponentCube

| 필드 | 의미 |
|------|------|
| `TextureTarget` | `UTextureRenderTargetCube*` |

> **Cubemap 6면 캡처** — 한 번에 6배 비싸짐. Reflection Capture 와 다름 (Reflection Capture 는 자체 Actor `AReflectionCapture`).

### 5.4 비용

> **bCaptureEveryFrame = true + ShowFlags 기본** = 카메라 한 개 추가 비용. **수동 캡처** + **HiddenActors / ShowOnlyActors 화이트리스트** + **저해상도 RenderTarget** 이 표준 절감.

---

## 6. UPostProcessComponent — Actor 단위 PostProcess Volume

[`PostProcessComponent.h:21-80`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/PostProcessComponent.h):

### 6.1 핵심 필드

```cpp
UCLASS(ClassGroup = Rendering, MinimalAPI)
class UPostProcessComponent : public USceneComponent, public IInterface_PostProcessVolume
{
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = PostProcessVolume)
    TArray<TObjectPtr<UShape>> Shapes;        // 영역 모양 (Box/Sphere)

    UPROPERTY(interp, EditAnywhere, BlueprintReadWrite, Category = PostProcessVolumeSettings)
    float Priority;                            // 겹침 시 우선순위

    UPROPERTY(interp, EditAnywhere, BlueprintReadWrite, Category = PostProcessVolumeSettings, meta = (ClampMin = "0.0", UIMin = "0.0", UIMax = "6000.0"))
    float BlendRadius;                         // 페이드 거리 (Unbound 아닐 때)

    UPROPERTY(interp, EditAnywhere, BlueprintReadWrite, Category = PostProcessVolumeSettings, meta = (UIMin = "0.0", UIMax = "1.0"))
    float BlendWeight;                         // 블렌드 가중치

    UPROPERTY(interp, EditAnywhere, BlueprintReadWrite, Category = PostProcessVolumeSettings)
    uint32 bUnbound : 1;                       // true = 무한 영역

    UPROPERTY(interp, EditAnywhere, BlueprintReadWrite, Category = PostProcessVolumeSettings, meta = (ShowOnlyInnerProperties))
    struct FPostProcessSettings Settings;
};
```

> **APostProcessVolume Actor 대체** — Actor 컴포넌트로 두면 동적 이동/생성 가능. `bUnbound = true` 면 영역 무관 (전역).

```cpp
// 데미지 받을 때 화면 빨강 페이드
PostProcess = CreateDefaultSubobject<UPostProcessComponent>(TEXT("PostProcess"));
PostProcess->bUnbound = true;
PostProcess->BlendWeight = 0.f;     // 시작은 0
PostProcess->Settings.bOverride_ColorSaturation = true;
PostProcess->Settings.ColorSaturation = FVector4(1, 0.3, 0.3, 1);

// 데미지 시
void OnDamage()
{
    PostProcess->BlendWeight = 0.8f;
    GetWorld()->GetTimerManager().SetTimer(FadeTimer, [this]()
    {
        PostProcess->BlendWeight = FMath::Max(0.f, PostProcess->BlendWeight - 0.1f);
        // 0.5초 동안 페이드
    }, 0.05f, true);
}
```

---

## 7. 에디터 시각화 컴포넌트 (`ArrowComponent`, `DrawSphereComponent`, `DrawFrustumComponent`)

> **에디터 전용** — 패키지 빌드 시 자동 컬링 (단 `bIsScreenSizeScaled` 등 일부 옵션은 게임 빌드 영향).

### 7.1 UArrowComponent
- `ArrowColor`, `ArrowSize`, `ArrowLength`, `ScreenSize`, `bIsScreenSizeScaled`
- 방향 표시 (Pawn Forward 등)

### 7.2 UDrawSphereComponent
- `USphereComponent` 자손 — 콜리전 가능 + 디버그 시각화

### 7.3 UDrawFrustumComponent
- 카메라 시야 시각화 — `FrustumAngle`, `FrustumAspectRatio`, `FrustumStartDist`, `FrustumEndDist`

> **`bHiddenInGame = true`** 가 표준 — 패키지 빌드 영향 없음.

---

## 8. 비용 + 함정 표

| 컴포넌트 | 비용 (대략) | 함정 |
|---------|------------|------|
| Decal | 화면 차지 영역 × Material | 매 발사 떠나면 Decal 폭사 — LifeSpan 짧게 + Pool |
| TextRender | 폰트 텍스쳐 + 글자 수 | 매 Tick `SetText` 호출 (LOD 효과 없음) |
| Billboard | 매우 작음 | 에디터 전용 — 게임 빌드 시 자동 hide |
| MaterialBillboard | Material 비용 | 너무 많이 (HP바 100개) → UMG WidgetComponent 또는 Niagara |
| SceneCapture2D | **카메라 1개 추가** | bCaptureEveryFrame = true 가 가장 큰 함정 |
| SceneCaptureCube | **카메라 6개** | Reflection 은 ReflectionCapture Actor |
| PostProcess | 영향 옵션별로 다름 | bOverride_* 비트 — 모든 옵션 활성 시 PostProcess 풀 비용 |

---

## 9. 함정 & 안티패턴

| # | 함정 | 정답 |
|---|------|-----|
| 1 | 매 발사 Decal Spawn + LifeSpan 무한 | LifeSpan 5-30s + FadeDuration 1s |
| 2 | TextRender 매 Tick `SetText` (FText 변환 비용) | 변경 시점에만 |
| 3 | SceneCapture2D `bCaptureEveryFrame = true` 항상 | 수동 `CaptureScene()` + Timer |
| 4 | SceneCapture HiddenActors 미설정 (모두 캡처) | 화이트리스트 ShowOnlyActors |
| 5 | UPostProcessComponent + `bOverride_*` 미설정 (모든 옵션 덮어씌움) | 변경할 옵션의 `bOverride_*` 만 true |
| 6 | DrawSphereComponent 가 콜리전 활성 (트리거로 사용) | 의도면 OK, 아니면 `bHiddenInGame = true` + `Collision = NoCollision` |
| 7 | MaterialBillboard 100개 (HP바) | UMG WidgetComponent 또는 Niagara 통합 |
| 8 | Decal Material Domain 잘못 (`Surface` 사용) | `Deferred Decal` Domain 필수 |
| 9 | 🚨 SceneCapture 콜백 / Tick 첫 줄 프로파일링 스코프 누락 | 의무 ([`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)) |

---

## 10. 체크리스트

- [ ] Decal: Material Domain = Deferred Decal + LifeSpan + FadeScreenSize
- [ ] TextRender: WorldSize 적정 + Alignment 명시
- [ ] SceneCapture: bCaptureEveryFrame = false (수동) + HiddenActors/ShowOnlyActors
- [ ] SceneCapture: TextureTarget 해상도 적정 (저해상도면 비용 ↓)
- [ ] PostProcess: 변경 옵션의 `bOverride_*` 만 true
- [ ] PostProcess: `bUnbound = true` 면 모든 카메라 영향
- [ ] 에디터 시각화 (Arrow/DrawSphere/DrawFrustum) `bHiddenInGame = true`
- [ ] MaterialBillboard 100개 이상 — UMG WidgetComponent 검토
- 