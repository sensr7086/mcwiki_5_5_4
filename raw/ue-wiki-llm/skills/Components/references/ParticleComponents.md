---
name: components-particlecomponents
description: UParticleSystemComponent (Cascade legacy) + UNiagaraComponent + UVectorFieldComponent + ENCPoolMethod::AutoRelease + 6대 정책.
---

# Components / ParticleComponents — 파티클 + Vector Field (Engine 모듈)

> **위치**: `Engine/Source/Runtime/Engine/Classes/Particles/ParticleSystemComponent.h` + `Components/VectorFieldComponent.h`
> **베이스**: `UFXSystemComponent` (FX 베이스, abstract) → `UParticleSystemComponent` (Cascade — 레거시) | `USceneComponent` → `UVectorFieldComponent`
> **요지**: **Cascade 는 레거시 — 신규 코드는 Niagara 사용** (`UNiagaraComponent` — Niagara 플러그인). 본 sub-skill 은 Cascade 베이스 (호환·기존 자산용) + Vector Field (3D 벡터 필드 — Cascade GPU 파티클·Niagara 양쪽 지원).

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
| 🎯 **어셋 로드** | 🚨 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) — **NiagaraSystem (5.x 표준) / ParticleSystem (Cascade — legacy) / VectorField = Soft + UAssetManager 표준** (대형 VFX). NiagaraComponent Pool (`ENCPoolMethod::AutoRelease`) = 사전 인스턴스 + 메모리 상주. SpawnSystemAtLocation 첫 호출 = NiagaraSystem CDO + Shader PSO 컴파일 → Match Start `PreloadPrimaryAssets` 의무. 자세한 = [`Niagara/SKILL.md`](../../Niagara/SKILL.md). |
| 🎯 **어셋 최적화** | 🚨 [`12_AssetOptimizationPolicy.md §5`](../../../references/12_AssetOptimizationPolicy.md) — **Niagara Quality Scaling 의무** — 모든 NiagaraSystem = `UNiagaraEffectType` 지정 + 품질 레벨 5종 매트릭스 (Cinematic 1.0 / High 1.0 / Medium 0.7 / Low 0.4 / Mobile 0.2 SpawnCountScale) + Pool (`ENCPoolMethod::AutoRelease`) + ENiagaraSignificanceHandling 4종 + `Scalability::SetQualityLevels` 런타임 전환. **Cascade UParticleSystem (legacy) = LODDistances 만 — 신규는 Niagara 의무**. |

---

## 1. UParticleSystemComponent — Cascade 파티클 (레거시)

[`ParticleSystemComponent.h`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Particles/ParticleSystemComponent.h):

### 1.1 핵심 필드

| 필드 | 의미 |
|------|------|
| `Template` | `UParticleSystem*` — Cascade 에셋 |
| `bAutoActivate` | 자동 시작 |
| `bResetOnDetach` | 부착 해제 시 리셋 |
| `bAutoDestroy` | 종료 시 자동 destroy |
| `EmitterInstances` | 런타임 Emitter 인스턴스 (transient) |
| `InstanceParameters` | `FParticleSysParam` 배열 — 동적 파라미터 |
| `bIgnoreOwnerHidden` | Owner 숨김 무시 |
| `bWasCompleted` | 시뮬레이션 완료 |
| `OnSystemFinished` | 종료 콜백 (Delegate) |

### 1.2 InstanceParameters — 동적 제어

```cpp
// Material Color 변경 (Cascade 안 Dynamic Parameter 모듈 통해)
ParticleComp->SetColorParameter(TEXT("MyColor"), FLinearColor::Red);
ParticleComp->SetFloatParameter(TEXT("MyScale"), 2.0f);
ParticleComp->SetVectorParameter(TEXT("MyVel"), FVector(100, 0, 0));
ParticleComp->SetActorParameter(TEXT("Target"), TargetActor);
ParticleComp->SetMaterialParameter(TEXT("OverrideMat"), CustomMat);
```

### 1.3 표준 패턴 (레거시)

```cpp
// Cascade 사용 (기존 자산만)
UGameplayStatics::SpawnEmitterAtLocation(
    GetWorld(),
    ParticleSystem,
    GetActorLocation(),
    GetActorRotation(),
    FVector::OneVector,
    /*bAutoDestroy=*/true);

// 또는 부착
UGameplayStatics::SpawnEmitterAttached(
    ParticleSystem,
    GetMesh(),
    TEXT("MuzzleSocket"),
    FVector::ZeroVector,
    FRotator::ZeroRotator,
    EAttachLocation::KeepRelativeOffset,
    /*bAutoDestroy=*/true);
```

> 🚨 **Cascade 는 5.x 에서 deprecated 마크는 안 됐지만** 신규 자산은 **Niagara 표준**. Cascade 자산은 점차 마이그레이션.

---

## 2. UNiagaraComponent — Niagara 파티클 (현행)

> **위치**: `Engine/Plugins/FX/Niagara/Source/Niagara/Public/NiagaraComponent.h` (별도 플러그인 — Niagara 모듈)

본 위키 범위 외 (Niagara 별도 sub-skill 가능). 핵심 패턴:

```cpp
// Niagara 표준 Spawn
UNiagaraFunctionLibrary::SpawnSystemAtLocation(
    GetWorld(),
    NiagaraSystem,    // UNiagaraSystem*
    GetActorLocation());

UNiagaraFunctionLibrary::SpawnSystemAttached(
    NiagaraSystem,
    GetMesh(),
    TEXT("MuzzleSocket"),
    FVector::ZeroVector,
    FRotator::ZeroRotator,
    EAttachLocation::KeepRelativeOffset,
    /*bAutoDestroy=*/true);

// 사용자 매개변수 (Niagara System 안에서 정의된 Module Inputs)
NiagaraComp->SetVariableLinearColor(FName("Color"), FLinearColor::Red);
NiagaraComp->SetVariableFloat(FName("Scale"), 2.0f);
NiagaraComp->SetVariableObject(FName("Mesh"), MeshAsset);
```

> Niagara 의 핵심 차이: GPU 시뮬레이션 + Stack 기반 모듈 + 데이터 인터페이스 (Skeletal Mesh / Static Mesh 샘플 등 풍부). Cascade 못 하던 작업 가능.

---

## 3. UVectorFieldComponent — 3D 벡터 필드

[`VectorFieldComponent.h`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/VectorFieldComponent.h):

### 3.1 핵심 필드

```cpp
UCLASS(ClassGroup=Effects, hidecategories=(Object, Mobility), editinlinenew, MinimalAPI)
class UVectorFieldComponent : public UPrimitiveComponent
{
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category=VectorFieldComponent)
    TObjectPtr<UVectorField> VectorField;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, interp, Category=VectorFieldComponent)
    float Intensity;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, interp, Category=VectorFieldComponent)
    float Tightness;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category=VectorFieldComponent)
    bool bPreviewVectorField;
};
```

### 3.2 동작

> **VectorField 안에 들어온 GPU 파티클** 의 속도를 변경 — 회오리/와류/난류 시뮬. Cascade 의 Vector Field 모듈 또는 Niagara 의 Vector Field 데이터 인터페이스가 사용.

```cpp
// Tornado 액터
VectorField = CreateDefaultSubobject<UVectorFieldComponent>(TEXT("Tornado"));
RootComponent = VectorField;
VectorField->VectorField = TornadoFieldAsset;        // .vf 또는 .fga 파일
VectorField->Intensity = 1.5f;
VectorField->Tightness = 0.5f;
```

---

## 4. UFXSystemComponent — 베이스 (abstract)

`UParticleSystemComponent` / `UNiagaraComponent` 모두 `UFXSystemComponent` 자손 — 공통 인터페이스:

```cpp
// 공통 메소드 (둘 다)
virtual void Activate(bool bReset = false);
virtual void Deactivate();
virtual void DeactivateImmediate();
virtual bool IsActive() const;

// FX 매개변수 (이름 + 타입)
virtual void SetFloatParameter(FName ParameterName, float Param);
virtual void SetVectorParameter(FName ParameterName, FVector Param);
virtual void SetColorParameter(FName ParameterName, FLinearColor Param);
virtual void SetMaterialParameter(FName ParameterName, UMaterialInterface* Param);
```

> **`UFXSystemComponent*`** 변수로 Cascade/Niagara 둘 다 받을 수 있음 — 마이그레이션 진행 중인 코드에 유용.

---

## 5. 비용 + 풀링

### 5.1 파티클 비용 매트릭스

| 항목 | 비용 |
|------|------|
| Spawn Rate (parts/sec) | 매우 큼 (CPU/GPU 둘 다) |
| Particle Count | GPU 비용 거의 선형 |
| Mesh Particle | StaticMesh 인스턴싱 — Mesh 복잡도에 비례 |
| Light Module (Cascade) | **매우 비쌈** — 보통 1-2개 한도 |
| Niagara GPU 시뮬 | CPU 보다 훨씬 효율적 |
| VectorField | GPU 1회 텍스처 샘플 — 저렴 |
| Significance 통합 | 거리 기반 Spawn Rate 토글 |

### 5.2 풀링

```cpp
// SpawnEmitterAttached / SpawnSystemAttached 의 PoolingMethod
UNiagaraFunctionLibrary::SpawnSystemAtLocation(
    GetWorld(), NiagaraSystem, Location, Rotation, Scale,
    /*bAutoDestroy=*/false,        // false 면 풀로 반환
    /*bAutoActivate=*/true,
    ENCPoolMethod::AutoRelease,    // 풀 사용
    /*bPreCullCheck=*/true);
```

> **`ENCPoolMethod::AutoRelease`** 표준 — 매 발사마다 새로 spawn 보다 풀 재사용. ParticlePool / NiagaraComponentPool 자동 관리.

---

## 6. Significance 통합

```cpp
void UParticleSig::Tick(USignificanceManager& Mgr, FTransform InVT, float Sig)
{
    auto* P = ParticleWeak.Get();
    if (!P) return;

    if (Sig < 0.1f) P->DeactivateImmediate();
    else if (Sig < 0.4f)
    {
        P->Activate();
        P->SetFloatParameter(TEXT("SpawnRateMultiplier"), 0.3f);
    }
    else
    {
        P->Activate();
        P->SetFloatParameter(TEXT("SpawnRateMultiplier"), 1.0f);
    }
}
```

> **거리 멀어지면 Spawn Rate 0.3 / 0.1 / 0** — VFX 가 화면에서 차지 비중 작을 때 비용 절감.

---

## 7. 함정 & 안티패턴

| # | 함정 | 정답 |
|---|------|-----|
| 1 | 신규 자산을 Cascade 로 작업 | Niagara 사용 (Cascade 는 호환만) |
| 2 | `bAutoDestroy = true` + 풀링 둘 다 의도 | 풀링 시 false |
| 3 | 매 Tick `Set*Parameter` (값 동일) | 변화 시점에만 |
| 4 | Light Module 한 시스템에 5+ 개 | 1-2개 한도 |
| 5 | GPU 파티클 100k + CPU Sort | Niagara GPU 정렬 사용 |
| 6 | `SpawnEmitterAttached` 결과 무시 (`UAudioComponent*` 와 마찬�