---
name: components-cameracomponent
description: UCameraComponent + UCineCameraComponent - PostProcessSettings + ProjectionMode + FieldOfView + 6대 정책.
---

# Components / CameraComponent — 카메라 (Engine 모듈)

> **위치**: `Engine/Source/Runtime/Engine/Classes/Camera/{CameraComponent,CameraShakeSourceComponent}.h`
> **베이스**: `USceneComponent` → `UCameraComponent` (+ `UCameraProxyMeshComponent` 에디터 시각화)
> **요지**: **카메라 뷰 + Projection + PostProcess 오버라이드**. SpringArm + CameraComponent 페어가 표준 — SpringArm 은 [`MovementComponents`](../MovementComponents/SKILL.md) 에. CameraShakeSource 는 PointSource 카메라 흔들림.

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

## 1. UCameraComponent — 카메라 뷰포인트

[`CameraComponent.h:32-300`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Camera/CameraComponent.h):

### 1.1 Projection — Perspective / Orthographic

| 필드 | Perspective | Orthographic |
|------|-------------|--------------|
| `ProjectionMode` | `ECameraProjectionMode::Perspective` | `Orthographic` |
| `FieldOfView` | 가로 FOV (deg) | 무시 |
| `OrthoWidth` | 무시 | 가로 단위 |
| `OrthoNearClipPlane` | 무시 | 직교 Near (필요 시) |
| `OrthoFarClipPlane` | 무시 | 직교 Far |
| `bAutoCalculateOrthoPlanes` | — | 자동 Near/Far 계산 |
| `bUpdateOrthoPlanes` | — | 매 프레임 보정 (라이트 아티팩트 방지) |

### 1.2 First Person 시스템 (5.x 신규)

```cpp
UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = CameraSettings,
    meta = (Units = deg, EditCondition = "bEnableFirstPersonFieldOfView"))
float FirstPersonFieldOfView;        // 1인칭 메시 전용 FOV (보통 90)

UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = CameraSettings,
    meta = (EditCondition = "bEnableFirstPersonScale"))
float FirstPersonScale;              // 1인칭 메시 스케일 (0.001~1)
```

> **`IsFirstPerson` 태그가 있는 Primitive** 에 별도 FOV/Scale 적용 — 1인칭 무기 메시가 환경과 클리핑 안 되게.

### 1.3 Aspect Ratio

| 필드 | 의미 |
|------|------|
| `AspectRatio` | Width/Height (bConstrainAspectRatio 필요) |
| `bConstrainAspectRatio` | 검은 띠 추가 (시네마) |
| `AspectRatioAxisConstraint` | `MaintainXFOV` / `MaintainYFOV` / `MajorAxisFOV` |
| `bOverrideAspectRatioAxisConstraint` | LocalPlayer 기본 오버라이드 |

### 1.4 PostProcess 오버라이드

```cpp
UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = PostProcess)
float PostProcessBlendWeight;        // 블렌드 가중치 (0~1)

UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = PostProcess)
struct FPostProcessSettings PostProcessSettings;   // 모든 PostProcess 옵션 오버라이드
```

> **카메라마다 다른 PostProcess** — 1인칭/3인칭 전환, Aim Down Sights (DOF) 등.

### 1.5 ViewTarget 통합

```cpp
// AActor 의 ViewTarget 메소드 — 자동으로 첫 UCameraComponent 사용
void AActor::CalcCamera(float DeltaTime, FMinimalViewInfo& OutResult) override
{
    // 기본 동작: 첫 UCameraComponent 의 GetCameraView() 호출
}

// UCameraComponent::GetCameraView (자식 override 가능)
virtual void GetCameraView(float DeltaTime, FMinimalViewInfo& DesiredView);
```

### 1.6 표준 셋업 (3인칭)

```cpp
// AMyChar::AMyChar
SpringArm = CreateDefaultSubobject<USpringArmComponent>(TEXT("SpringArm"));
SpringArm->SetupAttachment(GetCapsuleComponent());
SpringArm->TargetArmLength = 350.f;
SpringArm->bUsePawnControlRotation = true;

Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
Camera->SetupAttachment(SpringArm, USpringArmComponent::SocketName);
Camera->bUsePawnControlRotation = false;          // SpringArm 만 회전
Camera->FieldOfView = 90.f;
Camera->bConstrainAspectRatio = false;
```

---

## 2. UCameraShakeSourceComponent — PointSource 흔들림

[`CameraShakeSourceComponent.h`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Camera/CameraShakeSourceComponent.h):

### 2.1 핵심 필드 + 메소드

```cpp
UCLASS(ClassGroup=Camera, meta=(BlueprintSpawnableComponent))
class UCameraShakeSourceComponent : public USceneComponent
{
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category=CameraShake)
    FCameraShakeSourceComponentParams Params;
    // - Attenuation: ECameraShakeAttenuation (Linear/Quadratic)
    // - InnerAttenuationRadius: 풀 강도 반경
    // - OuterAttenuationRadius: 0 강도 반경
    // - bAutoStart: 시작 시 자동 시작
    // - CameraShake: TSubclassOf<UCameraShakeBase>

    UFUNCTION(BlueprintCallable)
    void Start();

    UFUNCTION(BlueprintCallable)
    void StopAllCameraShakes(bool bImmediately = true);

    UFUNCTION(BlueprintCallable)
    void StartCameraShake(TSubclassOf<UCameraShakeBase> InCameraShake, float Scale = 1.f);

    UFUNCTION(BlueprintCallable)
    void StopCameraShake(TSubclassOf<UCameraShakeBase> InCameraShake, bool bImmediately = true);

    // 카메라가 이 위치 기준으로 받을 강도 (자동 호출)
    float GetAttenuationFactor(const FVector& Location) const;
};
```

### 2.2 표준 패턴 — 폭발 위치 흔들림

```cpp
// AExplosion::AExplosion
ShakeSource = CreateDefaultSubobject<UCameraShakeSourceComponent>(TEXT("ShakeSource"));
ShakeSource->Params.InnerAttenuationRadius = 200.f;
ShakeSource->Params.OuterAttenuationRadius = 1500.f;
ShakeSource->Params.Attenuation = ECameraShakeAttenuation::Quadratic;
ShakeSource->Params.bAutoStart = false;

void AExplosion::Detonate()
{
    ShakeSource->StartCameraShake(UExplosionShake::StaticClass(), 1.f);
}
```

> **Attenuation Inner~Outer**: Inner 안 = 풀 강도, Outer 밖 = 0, 사이는 Quadratic/Linear 보간.
> **자동으로 모든 PlayerController** 의 카메라가 이 Source 의 거리 기반 강도로 받음.

---

## 3. 함정 & 안티패턴

| # | 함정 | 정답 |
|---|------|-----|
| 1 | SpringArm + Camera 모두 `bUsePawnControlRotation = true` (이중 회전) | SpringArm 만 true, Camera false |
| 2 | UCameraComponent 직접 회전 매 Tick | SpringArm 사용 (lag + 충돌 회피) |
| 3 | PostProcessSettings 전체 오버라이드 (한 옵션만 변경하려고) | `bOverride_*` 비트만 true 설정 |
| 4 | Orthographic 카메라 Near/Far 0 (자동 안 켬) | `bAutoCalculateOrthoPlanes = true` 또는 명시 설정 |
| 5 | CameraShake `Outer < Inner` 설정 | Inner < Outer 보장 |
| 6 | 매 Tick `StartCameraShake` 호출 (싱글 인스턴스 가정) | `StartCameraShake` 는 새 인스턴스 만듦 — 한 번 호출 |
| 7 | 🚨 카메라 Tick 안 `TActorIterator` 로 다른 Pawn 검색 | Subsystem / GameMode 등록 ([`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md)) |

---

## 4. 체크리스트

- [ ] UCameraComponent 의 `bUsePawnControlRotation` 검토 (SpringArm 부착 시 false)
- [ ] Projection 모드 명시 (Perspective/Orthographic)
- [ ] FOV 적정 (3인칭 90, 1인칭 90~110, 시네마 30~60)
- [ ] FirstPerson 메시 사용 시 `bEnableFirstPersonFieldOfView` + `FirstPersonScale`
- [ ] `bConstrainAspectRatio` — 시네마 검은 띠 필요 시
- [ ] PostProcessSettings: `bOverride_*` 비트만 활성 (전체 덮어씌움 금지)
- [ ] CameraShakeSource: Inner < Outer + Attenuation 명시
- [ ] CameraShake 클래스가 `UCameraShakeBase` 자손인지 확인
- [ ] 🚨 카메라 GetCameraView override 시 첫 줄 프로파일링 스코프

---

## 5. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. UCameraComponent (Perspective/Orthographic + FirstPerson 5.x 신규 + AspectRatio + PostProcessSettings 오버라이드 + ViewTarget 통합) + UCameraShakeSourceComponent (PointSource Attenuation Inner/Outer + StartCameraShake) + 표준 3인칭 셋업 + 함정 7종. SpringArm 은 MovementComponents 참조. |
