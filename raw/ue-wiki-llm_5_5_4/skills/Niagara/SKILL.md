---
name: niagara-main
description: Niagara Plugin (5.x VFX 표준) - UNiagaraComponent + UNiagaraSystem + Stack 모듈 + Data Interface 9종 + GPU vs CPU + ENCPoolMethod::AutoRelease + Significance 통합.
---

# Niagara — VFX 시스템 (Plugin)

> **위치**: `Engine/Plugins/FX/Niagara/Source/Niagara/` (Epic 표준 플러그인 — 5.x 이후 기본 활성)
> **5.5.4 헤더 경로 주의**: `UNiagaraSystem` / `UNiagaraEmitter` / `UNiagaraScript` / `UNiagaraEffectType` 는 `Niagara/Classes/` 안 (UHT-generated UCLASS 관례). 그 외 (NiagaraComponent / FunctionLibrary / DataInterface*) 는 `Niagara/Public/`.
> **모듈명**: `Niagara` (Runtime) + `NiagaraCore` + `NiagaraShader` + `NiagaraVertexFactories` + `NiagaraEditor` (에디터)
> **베이스**: `UNiagaraComponent : public UFXSystemComponent` (`UFXSystemComponent : public USceneComponent`)
> **요지**: **Cascade 의 후속 — 5.x VFX 표준**. GPU 시뮬 + Stack 기반 모듈 + 데이터 인터페이스 (Skeletal Mesh / Static Mesh / Audio 등 풍부) + Niagara Script 의 BP 같은 그래프. **신규 VFX 자산은 무조건 Niagara**.

---

## 🚨 공통 정책 (Components 6대 의무)

> 모든 컴포넌트는 [`10_ComponentPolicies.md`](../../references/10_ComponentPolicies.md) 의 6대 정책 적용.

| # | 정책 | Niagara 특화 |
|---|------|-------------|
| 1 | **Mobility** | UNiagaraComponent = USceneComponent — Movable 표준 (이펙트 = 동적) |
| 2 | **NewObject + DuplicateObject** | Niagara 인스턴스 = `SpawnSystemAtLocation/Attached` 가 자동 — 직접 X |
| 3 | **GC 방어** | NiagaraSystem 자산 = `UPROPERTY()` + `TObjectPtr<UNiagaraSystem>` |
| 4 | **GetOwner 캐싱** | NiagaraComponent 가 Auto-Pool 사용 — Owner 가 직접 캐싱 안 함 |
| 5 | **PrimaryComponentTick** | NiagaraComponent = Tick ON (시뮬). Significance 통합으로 거리 기반 비활성 |
| 6 | **CDO** | NiagaraSystem 자산이 CDO 데이터 — 인스턴스는 자동 복제 |
| 🎯 **어셋 로드** | 🚨 [`11_AssetLoadingPolicy.md`](../../references/11_AssetLoadingPolicy.md) — **NiagaraSystem 자산이 매우 큼** (Module Stack + Data Interface + GPU 시뮬 데이터). `TSoftObjectPtr<UNiagaraSystem>` + `UAssetManager::PreloadPrimaryAssets(bLoadRecursive=true)` Match Start 사전 로드 의무. **Pool 활성 (`ENCPoolMethod::AutoRelease`) + 메모리 상주** — 자주 Spawn = 풀이 사전 인스턴스. SpawnSystemAtLocation 첫 호출 히칭 = NiagaraSystem CDO 로드 + Shader PSO 컴파일. |
| 🎯 **품질 스케일링** | 🚨 [`12_AssetOptimizationPolicy.md`](../../references/12_AssetOptimizationPolicy.md) — **§5 Niagara Quality Scaling 의무** — **모든 NiagaraSystem 자산 = `UNiagaraEffectType` 지정 의무**. 품질 레벨별 SpawnCountScale (Cinematic 1.0 / High 1.0 / Medium 0.7 / Low 0.4 / Mobile 0.2) + UpdateRateScale + MaxDistance + MaxSystemInstances. ENiagaraSignificanceHandling 4종 (EarliestCullDistance / EarliestActorBased / EarliestKill / EarliestKeepActive) — Significance Manager 통합. UGameUserSettings + Scalability::SetQualityLevels 런타임 전환. |

---

## 1. 핵심 구성 요소

| 클래스 / 자산 | 역할 |
|--------------|------|
| `UNiagaraSystem` | **VFX 자산** — Emitter 들의 컬렉션 (.uasset) |
| `UNiagaraEmitter` | 단일 Emitter (파티클 그룹) — System 안에 포함 |
| `UNiagaraComponent` | 런타임 인스턴스 — Actor 에 부착 |
| `UNiagaraScript` | Stack 모듈 그래프 (BP 비슷) — Spawn/Update/Particle 단계 |
| `UNiagaraDataInterface` | 외부 데이터 접근 (Skeletal Mesh / Static Mesh / Audio / Volume Texture 등) |
| `UNiagaraComponentPool` | 자동 풀링 (UWorld 안 1개) — 재사용 표준 |

```
UNiagaraSystem (asset)
├── TArray<FNiagaraEmitterHandle> Emitters
│   └── FNiagaraEmitterHandle
│       └── UNiagaraEmitter
│           ├── UNiagaraScript SpawnScript (한 번)
│           ├── UNiagaraScript UpdateScript (매 프레임)
│           └── UNiagaraScript ParticleSpawnScript / ParticleUpdateScript
└── User Variables (TArray<FNiagaraVariable>)   ← 외부 게임 코드에서 SetVariable*
```

---

## 2. UNiagaraComponent — 런타임 컴포넌트

### 2.1 표준 사용 — Spawn 함수

```cpp
#include "NiagaraFunctionLibrary.h"

// 위치 spawn
UNiagaraComponent* Comp = UNiagaraFunctionLibrary::SpawnSystemAtLocation(
    GetWorld(),
    NiagaraSystem,                                  // UNiagaraSystem*
    GetActorLocation(),
    GetActorRotation(),
    FVector::OneVector,                              // Scale
    /*bAutoDestroy=*/true,                           // 종료 후 destroy (false = 풀로 반환)
    /*bAutoActivate=*/true,
    ENCPoolMethod::AutoRelease,                      // 풀링 표준
    /*bPreCullCheck=*/true);

// 부착 spawn
UNiagaraComponent* AttachedComp = UNiagaraFunctionLibrary::SpawnSystemAttached(
    NiagaraSystem,
    GetMesh(),                                       // USceneComponent
    TEXT("MuzzleSocket"),
    FVector::ZeroVector, FRotator::ZeroRotator,
    EAttachLocation::KeepRelativeOffset,
    /*bAutoDestroy=*/true,
    /*bAutoActivate=*/true,
    ENCPoolMethod::AutoRelease);
```

### 2.2 ENCPoolMethod — 풀링 정책

| 값 | 동작 |
|----|------|
| `None` | 풀 미사용 — 매번 NewObject (느림) |
| `AutoRelease` | **표준** — 종료 후 자동 풀로 반환 |
| `ManualRelease` | 수동 `ReleaseToPool()` 호출 |
| `ManualRelease_OnComplete` | 종료 시점에 수동 release |
| `FreeInPool` | 풀에서 free 상태 (Spawn 안 됨) |

> **표준 = `AutoRelease`** — 매 발사 발생음/이펙트 등 빈번한 Spawn 에 필수. `bAutoDestroy = false` 일 때만 풀로 반환.

### 2.3 User Variables — 동적 매개변수

```cpp
// Niagara System 안에서 정의된 User Variable 들 (예: User.Color, User.Scale, User.MeshSampler)
NiagaraComp->SetVariableLinearColor(FName("Color"), FLinearColor::Red);
NiagaraComp->SetVariableFloat(FName("Scale"), 2.0f);
NiagaraComp->SetVariableInt(FName("Count"), 100);
NiagaraComp->SetVariableVec3(FName("Direction"), FVector::UpVector);
NiagaraComp->SetVariableQuat(FName("Rotation"), FQuat::Identity);

// 데이터 인터페이스 (SkeletalMesh 샘플러)
NiagaraComp->SetVariableObject(FName("MeshSampler"), MyMeshAsset);

// Static Mesh 데이터 인터페이스 (5.x — 메시 표면에서 spawn)
UNiagaraDataInterfaceStaticMesh* MeshDI = ...;
NiagaraComp->SetVariableObject(FName("StaticMesh"), MeshDI);
```

> **User Variable 표준** — Niagara System 안 `User.` 네임스페이스로 노출 + 코드에서 `SetVariable*` 으로 매번 갱신.

### 2.4 활성/비활성 제어

```cpp
NiagaraComp->Activate(/*bReset=*/false);            // 시작 (bReset=true 면 처음부터)
NiagaraComp->Deactivate();                          // 부드러운 종료 (남은 파티클 자연 소멸)
NiagaraComp->DeactivateImmediate();                 // 즉시 종료 (모든 파티클 소멸)
NiagaraComp->IsActive();
NiagaraComp->IsComplete();                          // 시뮬 완료 (Auto-pool 직전)

// 콜백
NiagaraComp->OnSystemFinished.AddDynamic(this, &AMyActor::OnVFXFinished);
```

### 2.5 매개변수 수집 (Pawn → Niagara 전달)

```cpp
// 캐릭터 위치 + 속도를 Niagara System 으로 전달
void UpdateVFX()
{
    if (NiagaraComp && NiagaraComp->IsActive())
    {
        NiagaraComp->SetVariableVec3(FName("PawnLocation"), GetOwner()->GetActorLocation());
        NiagaraComp->SetVariableVec3(FName("PawnVelocity"), GetCharacterMovement()->Velocity);
    }
}
```

---

## 3. UNiagaraSystem — VFX 자산 (BP 에셋)

### 3.1 자산 구성

> **NiagaraSystem 은 BP 에셋** — 코드에서 직접 작성 안 함. Niagara Editor 에서:
> 1. **Emitter 목록** 추가 (Sprite/Mesh/Beam/Ribbon 등)
> 2. **각 Emitter 의 Spawn/Update Script** Stack 모듈 추가
> 3. **각 Particle 의 SpawnPerFrame/UpdateScript** Stack 모듈 추가
> 4. **User Variables** 정의 (코드에서 `SetVariable*` 가능하게)

### 3.2 5.x 권장 구조 — Scratch Pad / Module

| 모듈 위치 | 용도 |
|----------|------|
| **System Spawn** (1회) | 시스템 시작 시 1회 (예: 시작 위치 설정) |
| **System Update** (매 프레임) | 시스템 전체 갱신 |
| **Emitter Spawn** (1회) | Emitter 시작 시 1회 |
| **Emitter Update** (매 프레임) | Emitter 갱신 |
| **Particle Spawn** (파티클 생성 시) | 파티클 초기화 |
| **Particle Update** (매 프레임) | 파티클 갱신 (Velocity / Color / Scale / Lifetime) |
| **Render** | Sprite / Mesh / Light / Ribbon |

### 3.3 데이터 인터페이스 (Data Interface)

> **Niagara 의 핵심 — 외부 데이터 접근**. Cascade 가 못 하던 기능.

| Data Interface | 외부 데이터 |
|---------------|------------|
| `UNiagaraDataInterfaceSkeletalMesh` | 본 위치 / Vertex / Surface 샘플 |
| `UNiagaraDataInterfaceStaticMesh` | StaticMesh Vertex / Surface 샘플 |
| `UNiagaraDataInterfacePhysicsAsset` | PhysicsAsset Body 위치 |
| `UNiagaraDataInterfaceCurve` | Float / Vector / Color Curve |
| `UNiagaraDataInterfaceVolumeTexture` | 3D 텍스처 샘플 |
| `UNiagaraDataInterfaceRenderTarget2D` | RT 읽기/쓰기 |
| `UNiagaraDataInterfaceCollisionQuery` | Trace / Overlap |
| `UNiagaraDataInterfaceAudioOscilloscope` | Audio 분석 (시각화) |
| `UNiagaraDataInterfaceParticleRead` | 다른 Niagara System 의 파티클 읽기 |

```cpp
// Skeletal Mesh 데이터 인터페이스 — User Variable 로 노출 후 코드에서 set
NiagaraComp->SetVariableObject(FName("MeshSampler"), GetMesh());
// → Niagara Stack 안에서 "Spawn from Skeletal Mesh Surface" 모듈이 사용
```

---

## 4. GPU vs CPU 시뮬

### 4.1 SimTarget — Emitter 별 설정

| SimTarget | 시뮬 위치 | 사용 |
|-----------|----------|------|
| **CPU** | 게임 스레드 (또는 별도 워커) | 100~1000 파티클 |
| **GPU** | Compute Shader | 10000~1M 파티클 (Cascade 못 함) |

> **GPU Emitter 한계**:
> - Mesh particle 안 됨 (Sprite 만)
> - 일부 Data Interface 안 됨 (CollisionQuery / SkeletalMesh sample 등 — 5.x 일부 추가)
> - GPU → CPU readback 비용 (필요 시 Async)

### 4.2 GPU Emitter 표준 셋업

> Niagara Editor 안 Emitter Properties:
> - **Sim Target**: GPUCompute
> - **Required Modules**: Spawn 모듈은 GPU 호환만
> - **Bounds**: 수동 설정 필수 (GPU 는 자동 계산 안 함)

---

## 5. Pooling — `UNiagaraComponentPool`

### 5.1 자동 풀

```cpp
// AutoRelease 표준 — Component 가 Complete 시 자동 풀로
UNiagaraFunctionLibrary::SpawnSystemAtLocation(...,
    /*bAutoDestroy=*/false,
    /*bAutoActivate=*/true,
    ENCPoolMethod::AutoRelease);
```

> **풀 크기 제한** — `UNiagaraComponentPool::PrimePool(System, 16)` 으로 미리 16개 생성. 첫 Spawn 시 lag 방지.

### 5.2 PoolingMethod = None (풀 미사용)

```cpp
// Niagara System 의 Properties 안 PoolingMethod = None 설정
// 이러면 SpawnSystemAtLocation 의 ENCPoolMethod 인자 무시
```

> **표준 = AutoRelease + bAutoDestroy=false**. 빈번한 Spawn (총구 화염 등) 필수.

---

## 6. Significance 통합 — 거리 기반 LOD

```cpp
// AVFXSig::Tick (USignificanceManager 자식)
void Tick(USignificanceManager& Mgr, FTransform InVT, float InSig)
{
    auto* NC = NiagaraCompWeak.Get();
    if (!NC) return;

    if (InSig < 0.05f)
    {
        NC->DeactivateImmediate();   // 매우 멀리 — 시뮬 정지
    }
    else if (InSig < 0.3f)
    {
        // 멀리 — Spawn Rate 30%
        NC->Activate();
        NC->SetVariableFloat(FName("SpawnRateMultiplier"), 0.3f);
    }
    else
    {
        // 가까이 — 풀
        NC->Activate();
        NC->SetVariableFloat(FName("SpawnRateMultiplier"), 1.0f);
    }
}
```

> Niagara System 안 **`User.SpawnRateMultiplier`** 사용자 변수를 정의 + Spawn 모듈에서 곱하기.

---

## 7. 표준 패턴

### 7.1 무기 발사 화염 (총구 socket)

```cpp
void AGun::Fire()
{
    UNiagaraComponent* Muzzle = UNiagaraFunctionLibrary::SpawnSystemAttached(
        MuzzleFlashSystem, GetMesh(), TEXT("Muzzle"),
        FVector::ZeroVector, FRotator::ZeroRotator,
        EAttachLocation::SnapToTarget,
        /*bAutoDestroy=*/false,           // 풀로 반환
        /*bAutoActivate=*/true,
        ENCPoolMethod::AutoRelease);

    // 매번 새로운 색상
    Muzzle->SetVariableLinearColor(FName("Color"), FLinearColor::MakeFromHSV8(
        FMath::RandRange(0, 60), 200, 255));
}
```

### 7.2 폭발 + Decal + Audio 조합

```cpp
void AExplosion::Detonate()
{
    // Niagara 폭발
    UNiagaraFunctionLibrary::SpawnSystemAtLocation(
        GetWorld(), ExplosionSystem, GetActorLocation(), GetActorRotation(),
        FVector::OneVector, /*bAutoDestroy=*/true, /*bAutoActivate=*/true,
        ENCPoolMethod::AutoRelease);

    // Decal (RenderingComponents)
    UGameplayStatics::SpawnDecalAtLocation(GetWorld(), ScorchMark, FVector(200), GetActorLocation(),
        FRotator::ZeroRotator, 30.f);

    // Audio (AudioComponent)
    UGameplayStatics::SpawnSoundAtLocation(this, ExplosionSound, GetActorLocation());

    // ForceFeedback
    UGameplayStatics::SpawnForceFeedbackAtLocation(this, ExplosionFeedback, GetActorLocation());
}
```

### 7.3 SkeletalMesh 표면 Spawn (마법 효과)

```cpp
void AMage::CastSpell()
{
    UNiagaraComponent* Aura = UNiagaraFunctionLibrary::SpawnSystemAttached(
        AuraSystem, GetMesh(), TEXT("Spine"),
        FVector::ZeroVector, FRotator::ZeroRotator,
        EAttachLocation::SnapToTarget,
        /*bAutoDestroy=*/false,
        /*bAutoActivate=*/true,
        ENCPoolMethod::AutoRelease);

    // SkeletalMesh 데이터 인터페이스 — Body 표면에서 파티클 spawn
    Aura->SetVariableObject(FName("MeshSampler"), GetMesh());
}
```

### 7.4 다른 시스템과 데이터 공유 (Particle Read)

```cpp
// System A 의 파티클을 System B 에서 읽기
NiagaraCompB->SetVariableObject(FName("OtherSystemRef"), NiagaraCompA);
// Niagara Stack 안에서 "Particle Read" Data Interface 사용
```

---

## 8. 비용 + 최적화

### 8.1 비용 매트릭스

| 항목 | 비용 |
|------|------|
| Spawn Rate (parts/sec) | CPU/GPU 둘 다 비례 |
| Particle Count | GPU < CPU (GPU 가 효율적) |
| Mesh Particle | StaticMesh 인스턴싱 — Mesh 복잡도 |
| Light Particle | **매우 비쌈** — 보통 1-2개 한도 |
| Data Interface (SkeletalMesh) | 본 수 × Spawn 수 |
| Render Target Read/Write | GPU 동기화 비용 |
| Significance 통합 | 거리 기반 LOD — 권장 |

### 8.2 최적화 체크리스트

- [ ] **풀링** = `AutoRelease` (필수)
- [ ] **Bounds** 수동 설정 (GPU Emitter)
- [ ] **CullDistance** Niagara System 안 설정 (멀리서 비활성)
- [ ] **DistanceFieldFade** 카메라 가까이 fadeout (가까이 가면 안 보이게)
- [ ] **Light Module** 1-2개 한도
- [ ] **GPU vs CPU** 분기 (1000+ = GPU)
- [ ] **Significance** 통합 (거리 기반 SpawnRate)

---

## 9. 함정 & 안티패턴

| # | 함정 | 정답 |
|---|------|-----|
| 1 | 신규 자산을 Cascade 로 작업 | Niagara 무조건 (5.x 신규 자산 표준) |
| 2 | `SpawnSystemAttached` 의 결과 무시 + 매번 새 spawn | 풀링 사용 = 같은 Component 반환 |
| 3 | `bAutoDestroy = true` + AutoRelease | 모순 — 풀링 시 false |
| 4 | User Variable 매 Tick `SetVariable*` (값 동일해도) | 변경 시점에만 |
| 5 | GPU Emitter Bounds 자동 가정 | GPU = 수동 설정 필수 |
| 6 | Light Module 5+ 개 | 1-2개 한도 |
| 7 | 1000+ 파티클을 CPU Emitter | GPU 사용 |
| 8 | NiagaraComponent 의 Material 직접 수정 | User Variable (Material Asset) 으로 전달 |
| 9 | 🚨 OnSystemFinished 콜백 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` ([`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md)) |
| 10 | 🚨 ParticleUpdate 모듈 안 `TActorIterator` 비슷한 BP 노드 사용 | Data Interface (Spatial Hash 등) — [`09_GlobalIteratorPolicy.md`](../../references/09_GlobalIteratorPolicy.md) |

---

## 10. UFXSystemComponent — Cascade/Niagara 공통 베이스

> **`UNiagaraComponent` 와 `UParticleSystemComponent` 모두 `UFXSystemComponent` 자손** — 마이그레이션 시 공통 인터페이스 사용:

```cpp
UFXSystemComponent* FX = ...;   // Cascade or Niagara

FX->Activate(/*bReset=*/false);
FX->Deactivate();
FX->IsActive();

// 매개변수 (이름 + 타입)
FX->SetFloatParameter(TEXT("MyFloat"), 1.0f);
FX->SetVectorParameter(TEXT("MyVec"), FVector::UpVector);
FX->SetColorParameter(TEXT("MyColor"), FLinearColor::Red);
FX->SetMaterialParameter(TEXT("MyMat"), MyMaterial);
```

---

## 11. 체크리스트

- [ ] Build.cs 에 `Niagara` + `NiagaraCore` 추가
- [ ] `#include "NiagaraFunctionLibrary.h"` + `#include "NiagaraComponent.h"`
- [ ] `SpawnSystemAtLocation` / `SpawnSystemAttached` 사용 — 직접 컴포넌트 생성 X
- [ ] PoolingMethod = `AutoRelease` + `bAutoDestroy = false`
- [ ] User Variables 로 동적 제어 (매 Tick `Set*` 안 함, 변경 시점만)
- [ ] Niagara System: User Variables 정의 + Bounds 설정 (GPU)
- [ ] Significance 통합 — 거리 기반 SpawnRateMultiplier
- [ ] OnSystemFinished 콜백 스코프
- [ ] 🚨 매 Tick TActorIterator 안 씀

---

## 12. 관련 문서

- [`Components/ParticleComponents`](../Components/references/ParticleComponents.md) — Cascade (legacy) + UFXSystemComponent 베이스 + VectorField (Cascade/Niagara 양쪽)
- [`Components/AudioComponent`](../Components/references/AudioComponent.md) — Niagara + Audio 페어 표준
- [`Comp