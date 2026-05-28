---
name: components-shapecomponents
description: UBoxComponent + USphereComponent + UCapsuleComponent + UTriggerVolume - 트리거 콜리전 + 6대 정책.
---

# Components / ShapeComponents — 트리거 + 단순 콜리전 (Engine 모듈)

> **위치**: `Engine/Source/Runtime/Engine/Classes/Components/{ShapeComponent,BoxComponent,SphereComponent,CapsuleComponent,BrushComponent}.h`
> **베이스**: `UPrimitiveComponent` → `UShapeComponent` (abstract) → `UBoxComponent` / `USphereComponent` / `UCapsuleComponent` 또는 `UPrimitiveComponent` → `UBrushComponent`
> **요지**: **트리거(Trigger) 와 단순 콜리전(Simple Collision) 의 표준** — 게임 안 가장 흔한 컴포넌트. **`UCapsuleComponent` 는 ACharacter 의 RootComponent**. **Overlap 이벤트의 가장 큰 발생원** — 비용 관리는 [`08_OverlapHotspots.md`](../../../references/08_OverlapHotspots.md) + 본 §7.

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
UPrimitiveComponent
└── UShapeComponent  (abstract)         — UBodySetup + ShapeColor + DynamicObstacle (Nav)
│   ├── UBoxComponent                   — BoxExtent (FVector)
│   ├── USphereComponent                — SphereRadius (float, 균등 스케일)
│   └── UCapsuleComponent               — CapsuleRadius + CapsuleHalfHeight (Pawn 표준)
└── UBrushComponent                     — UModel (BSP, 에디터 위주)
```

> **`UShapeComponent` 는 abstract** — `UCLASS(abstract)` ([`ShapeComponent.h:23`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/ShapeComponent.h)).
> **`UBrushComponent` 는 ShapeComponent 자손 아님** — UPrimitiveComponent 직속 (BSP/볼륨 전용).

---

## 2. UShapeComponent — 베이스 (`ShapeComponent.h`)

### 2.1 핵심 필드

| 필드 | 타입 | 의미 |
|------|------|------|
| `ShapeBodySetup` | `TObjectPtr<UBodySetup>` | 콜리전 정의 — UpdateBodySetup 으로 자식이 생성 |
| `bUseArchetypeBodySetup` | `uint8:1` | CDO 와 동일하면 BodySetup 공유 (메모리 절약) |
| `ShapeColor` | `FColor` | 에디터/디버그 시 외곽선 색상 |
| `bDrawOnlyIfSelected` | `uint8:1` | Actor 선택 시에만 외곽선 표시 |
| `bShouldCollideWhenPlacing` | `uint8:1` | Place 시 콜리전 강제 |
| `bDynamicObstacle` | `uint8:1` | NavMesh 동적 모디파이어로 export |
| `bUseSystemDefaultObstacleAreaClass` | `uint8:1` | NavSystem 기본 ObstacleArea 사용 |
| `AreaClassOverride` | `TSubclassOf<UNavAreaBase>` | 커스텀 NavArea (bDynamicObstacle 일 때) |
| `LineThickness` | `float` | 외곽선 두께 |

### 2.2 베이스 virtual (`ShapeComponent.h:99-131`)

| virtual | 역할 |
|---------|------|
| `CreateSceneProxy` | 외곽선 디버그 Proxy (자식 override) |
| `GetBodySetup` | ShapeBodySetup 반환 |
| `DoCustomNavigableGeometryExport` | NavMesh export (`bDynamicObstacle`) |
| `GetNavigationData` | NavMesh 데이터 |
| `IsNavigationRelevant` | NavMesh 관련 여부 |
| `CalcBounds` | AABB (자식 override 필수) |
| `ShouldCollideWhenPlacing` | `bShouldCollideWhenPlacing || IsCollisionEnabled()` |
| `Serialize` | UNavAreaBase 마이그레이션 (5.0 deprecated AreaClass) |
| `PostEditChangeProperty` 🛠 | 크기 변경 시 BodySetup 재생성 |
| `UpdateBodySetup` | **자식 핵심 — Box/Sphere/Capsule 모양 생성** |
| `GetIgnoreBoundsForEditorFocus` 🛠 | true (선택 시 카메라 줌 안 함) |

### 2.3 `bUseArchetypeBodySetup` (메모리 최적화)

[`ShapeComponent.h:77-88`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/ShapeComponent.h):

```cpp
template<typename ComponentType>
bool PrepareSharedBodySetup()
{
    bool bSuccess = bUseArchetypeBodySetup;
    if (bUseArchetypeBodySetup && ShapeBodySetup == nullptr)
    {
        ShapeBodySetup = CastChecked<ComponentType>(GetArchetype())->GetBodySetup();
        bSuccess = ShapeBodySetup != nullptr;
    }
    return bSuccess;
}
```

> **CDO 와 동일한 크기**의 컴포넌트 인스턴스는 BodySetup 공유 — 같은 BoxComponent 100개를 같은 크기로 두면 BodySetup 1개만 메모리 점유. **크기를 바꾸는 순간 자체 BodySetup 생성** (자식 `SetBoxExtent` / `SetSphereRadius` / `SetCapsuleSize` 안에서 처리).

---

## 3. UBoxComponent — `FVector BoxExtent`

[`BoxComponent.h:18-70`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/BoxComponent.h):

```cpp
UCLASS(ClassGroup="Collision", meta=(DisplayName="Box Collision", BlueprintSpawnableComponent), MinimalAPI)
class UBoxComponent : public UShapeComponent
{
protected:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, export, Category=Shape)
    FVector BoxExtent;     // 반(half) extents

public:
    UFUNCTION(BlueprintCallable, Category="Components|Box")
    ENGINE_API void SetBoxExtent(FVector InBoxExtent, bool bUpdateOverlaps=true);

    UFUNCTION(BlueprintCallable, Category="Components|Box")
    FVector GetScaledBoxExtent() const;     // BoxExtent * Scale3D

    UFUNCTION(BlueprintCallable, Category="Components|Box")
    FVector GetUnscaledBoxExtent() const;   // BoxExtent

    inline void InitBoxExtent(const FVector& InBoxExtent) { BoxExtent = InBoxExtent; }
};
```

**virtual override (5종)**:
- `IsZeroExtent` — extent 0 검사
- `CreateSceneProxy` — 와이어프레임 박스
- `GetCollisionShape(Inflation)` — 물리 검사용 FCollisionShape
- `CalcBounds` — AABB
- `UpdateBodySetup` — UBodySetup 안에 `FKBoxElem` 생성

> **`BoxExtent` 는 반(half) 크기** — extent (X=50, Y=50, Z=50) → 100 × 100 × 100 cm 박스.
> **생성자에서**: `InitBoxExtent` 사용 (콜리전·렌더 업데이트 안 트리거 — Construction Script 표준).
> **런타임에서**: `SetBoxExtent` 사용 (BodySetup 업데이트 + Overlap 갱신).

---

## 4. USphereComponent — `float SphereRadius`

[`SphereComponent.h:17-66`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/SphereComponent.h):

```cpp
UCLASS(ClassGroup="Collision", meta=(DisplayName="Sphere Collision", BlueprintSpawnableComponent), MinimalAPI)
class USphereComponent : public UShapeComponent
{
protected:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, export, Category=Shape)
    float SphereRadius;

public:
    UFUNCTION(BlueprintCallable, Category="Components|Sphere")
    ENGINE_API void SetSphereRadius(float InSphereRadius, bool bUpdateOverlaps=true);

    UFUNCTION(BlueprintCallable, Category="Components|Sphere")
    float GetScaledSphereRadius() const;     // Radius * MinScale (균등)

    UFUNCTION(BlueprintCallable, Category="Components|Sphere")
    float GetUnscaledSphereRadius() const;
};
```

**핵심 차이**: `GetShapeScale` 가 `MinimumAxisScale` — 비대칭 스케일이어도 **균등 구체** 유지. `GetScaledSphereRadius = Radius * min(SX, SY, SZ)`.

```cpp
// SphereComponent.h:81-84
inline float USphereComponent::GetShapeScale() const
{
    return GetComponentTransform().GetMinimumAxisScale();
}
```

> **Sphere 는 스케일 비대칭이면 가장 작은 축에 맞춤** — 비대칭 늘리려면 `UCapsuleComponent` 또는 `UBoxComponent` 사용.

---

## 5. UCapsuleComponent — Pawn 표준 콜리전

[`CapsuleComponent.h:16-187`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/CapsuleComponent.h):

### 5.1 필드 + 핵심 메소드

```cpp
protected:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, export, Category=Shape, meta=(ClampMin="0", UIMin="0"))
    float CapsuleHalfHeight;     // Center → 반구 끝 거리

    UPROPERTY(EditAnywhere, BlueprintReadOnly, export, Category=Shape, meta=(ClampMin="0", UIMin="0"))
    float CapsuleRadius;         // 반구 + 중심 실린더 반경

public:
    ENGINE_API void SetCapsuleSize(float InRadius, float InHalfHeight, bool bUpdateOverlaps=true);
    void SetCapsuleRadius(float Radius, bool bUpdateOverlaps=true);
    void SetCapsuleHalfHeight(float HalfHeight, bool bUpdateOverlaps=true);

    inline void InitCapsuleSize(float InRadius, float InHalfHeight)
    {
        CapsuleRadius = FMath::Max(0.f, InRadius);
        CapsuleHalfHeight = FMath::Max3(0.f, InHalfHeight, InRadius);   // HalfHeight ≥ Radius 보장
    }
```

### 5.2 Scaled vs Unscaled — 8개 헬퍼

| 메소드 | 반환 |
|--------|------|
| `GetScaledCapsuleRadius` | `Radius * min(SX, SY)` |
| `GetScaledCapsuleHalfHeight` | `HalfHeight * SZ` |
| `GetScaledCapsuleHalfHeight_WithoutHemisphere` | `Scaled HalfHeight - Scaled Radius` (실린더 부분만) |
| `GetUnscaledCapsuleRadius` | `CapsuleRadius` |
| `GetUnscaledCapsuleHalfHeight` | `CapsuleHalfHeight` |
| `GetUnscaledCapsuleHalfHeight_WithoutHemisphere` | `CapsuleHalfHeight - CapsuleRadius` |
| `GetScaledCapsuleSize(R&, H&)` | Out 파라미터 |
| `GetScaledCapsuleSize_WithoutHemisphere(R&, H&)` | 위 동일 (반구 제외) |

### 5.3 Constraint: HalfHeight ≥ Radius

```cpp
// CapsuleComponent.h:23-26 주석:
// "This cannot be less than CapsuleRadius."
```

> **HalfHeight < Radius 면 잘못된 캡슐** — Sphere 가 됨. `InitCapsuleSize` 안 `FMath::Max3` 가 자동 보정. `SetCapsuleSize` 도 내부 보정.

### 5.4 ACharacter 의 RootComponent

```cpp
// ACharacter::ACharacter (생성자 패턴)
GetCapsuleComponent()->InitCapsuleSize(34.f, 88.f);    // 반경 34, 반높이 88
GetCapsuleComponent()->SetCollisionProfileName(UCollisionProfile::Pawn_ProfileName);
```

> **ACharacter 의 캡슐 크기 변경** = `Crouch` / `UnCrouch` 의 핵심. `UCharacterMovementComponent::CrouchedHalfHeight` 가 Crouch 시 적용.

---

## 6. UBrushComponent — BSP / 볼륨 (에디터)

[`BrushComponent.h:21-76`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/BrushComponent.h):

```cpp
UCLASS(editinlinenew, MinimalAPI, hidecategories=(Physics, Lighting, LOD, Rendering, ...))
class UBrushComponent : public UPrimitiveComponent  // ← UShapeComponent 자손 아님!
{
    UPROPERTY()
    TObjectPtr<class UModel> Brush;            // BSP 데이터

    UPROPERTY()
    TObjectPtr<class UBodySetup> BrushBodySetup;

#if WITH_EDITOR
    ENGINE_API virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;
    void ConditionalRebuildAlteredBSP() const;
#endif

    virtual class UBodySetup* GetBodySetup() override { return BrushBodySetup; };
    virtual ESceneDepthPriorityGroup GetStaticDepthPriorityGroup() const override;
    virtual bool IsEditorOnly() const override;     // 패키지 빌드 시 제외 가능
    virtual bool ShouldCollideWhenPlacing() const override { return true; }

    ENGINE_API bool HasInvertedPolys() const;
    ENGINE_API void RequestUpdateBrushCollision();
    ENGINE_API void BuildSimpleBrushCollision();
};
```

**용도**:
- **Volume** (트리거/PostProcess/PainCausing 등 `AVolume` 자손) — 런타임 작동
- **BSP Brush** (레벨 디자인 초기 단계) — 일반적으로 StaticMesh 로 변환

> **신규 게임 코드에서 직접 사용 금지** — 트리거는 `UBoxComponent` / `USphereComponent` 가 표준. `UBrushComponent` 는 Volume 자손 사용 시에만 자동 생성.

---

## 7. Overlap 비용 — Shape 별 가장 흔한 함정

> 자세한 정책: [`08_OverlapHotspots.md`](../../../references/08_OverlapHotspots.md). 여기서는 Shape 특화 항목.

### 7.1 SetCollisionEnabled / SetCollisionResponseToChannel — Overlap 갱신 비용

| 메소드 | bUpdateOverlaps 기본값 | 비용 |
|--------|------------------------|------|
| `SetBoxExtent(NewExtent, true)` | true | UpdateOverlaps 트리거 |
| `SetSphereRadius(NewRadius, true)` | true | UpdateOverlaps 트리거 |
| `SetCapsuleSize(R, H, true)` | true | UpdateOverlaps 트리거 |
| `InitBoxExtent / InitSphereRadius / InitCapsuleSize` | — | **Overlap 갱신 안 함** (Constructor 전용) |

```cpp
// 안티패턴 — 매 프레임 Overlap 재계산
void Tick(float Dt)
{
    Trigger->SetBoxExtent(FVector(50 + sinf(GetWorld()->TimeSeconds) * 10), /*bUpdateOverlaps=*/true);
    // ↑ 매 프레임 PhysX 의 Shape 재생성 + Overlap 갱신
}

// 정답 — Overlap 갱신 비활성 + 일회 호출 시점에만 true
void OnTriggerExpand()
{
    Trigger->SetBoxExtent(FVector(100), /*bUpdateOverlaps=*/false);
    Trigger->UpdateOverlaps();   // 명시 1회 호출
}
```

### 7.2 Shape 비교 — Sweep/Overlap 비용

| Shape | 비용 (대략) | 비고 |
|-------|------------|------|
| Sphere | **가장 저렴** | 점-구 거리만 비교 |
| Capsule | 중간 | 선분-구 거리 |
| Box | 비쌈 | OBB 기반 SAT |
| Convex / TriMesh | **가장 비쌈** | UPrimitiveComponent 자손 (StaticMesh) — Shape 아님 |

> **트리거는 Sphere 우선**. 정확도 필요 시 Box/Capsule. Mesh 충돌은 ShapeComponents 가 아닌 StaticMeshComponent 의 `bUseComplexAsSimpleCollision`.

### 7.3 NavMesh 비용

- `bDynamicObstacle = true` → NavSystem 매 변경 시 invalidate 영역 재계산
- 자주 움직이는 Shape (이동 트리거 등) 는 **`bDynamicObstacle = false`** 고정 (NavMesh 영향 없음)
- `SetWorldLocation` 시 NavMesh 자동 재계산 (`bUpdateNavOctreeOnComponentChange = false` 로 끌 수 있음 — UPrimitiveComponent 의 `SetCanEverAffectNavigation(false)`)

```cpp
Trigger->SetCanEverAffectNavigation(false);    // NavMesh 완전 무시 — 비용 0
```

---

## 8. 표준 패턴

### 8.1 트리거 박스 (게임 영역 진입 감지)

```cpp
// AVolumeTrigger.h
UCLASS()
class AVolumeTrigger : public AActor
{
    GENERATED_BODY()
public:
    AVolumeTrigger();

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UBoxComponent> TriggerBox;

    UFUNCTION()
    void OnBeginOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor, UPrimitiveComponent* OtherComp,
                        int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult);
};

// .cpp
AVolumeTrigger::AVolumeTrigger()
{
    PrimaryActorTick.bCanEverTick = false;     // Tick 불필요 (Overlap 이벤트 사용)

    TriggerBox = CreateDefaultSubobject<UBoxComponent>(TEXT("TriggerBox"));
    RootComponent = TriggerBox;
    TriggerBox->InitBoxExtent(FVector(100.f));
    TriggerBox->SetCollisionProfileName(TEXT("Trigger"));   // Trigger Profile (Block 없음, Overlap All)
    TriggerBox->SetGenerateOverlapEvents(true);
    TriggerBox->SetCanEverAffectNavigation(false);          // NavMesh 비용 ↓
    TriggerBox->OnComponentBeginOverlap.AddDynamic(this, &AVolumeTrigger::OnBeginOverlap);
}

void AVolumeTrigger::OnBeginOverlap(UPrimitiveComponent* OverlappedComp, AActor* OtherActor,
                                    UPrimitiveComponent* OtherComp, int32 OtherBodyIndex,
                                    bool bFromSweep, const FHitResult& SweepResult)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(VolumeTrigger_OnBeginOverlap);
    if (auto* P = Cast<APawn>(OtherActor))
    {
        // ...
    }
}
```

### 8.2 Pawn 캡슐 (ACharacter 자손)

```cpp
// ACharacter 자식 — 생성자
GetCapsuleComponent()->InitCapsuleSize(42.f, 96.f);
GetCapsuleComponent()->SetCollisionProfileName(UCollisionProfile::Pawn_ProfileName);
GetCapsuleComponent()->SetGenerateOverlapEvents(false);   // Pawn 은 보통 Overlap 안 씀 (Block 위주)
```

> **Pawn 은 Overlap 보다 Block + Hit** 가 표준. `GetGenerateOverlapEvents() = false` 로 두면 Overlap 비용 0.

### 8.3 InteractionRange (구체)

```cpp
// AInteractableActor::AInteractableActor
InteractionRange = CreateDefaultSubobject<USphereComponent>(TEXT("InteractionRange"));
InteractionRange->SetupAttachment(RootComponent);
InteractionRange->InitSphereRadius(150.f);
InteractionRange->SetCollisionEnabled(ECollisionEnabled::QueryOnly);    // 물리 무시 (Query 만)
InteractionRange->SetCollisionObjectType(ECC_GameTraceChannel1);        // Custom: Interaction
InteractionRange->SetCollisionResponseToAllChannels(ECR_Ignore);
InteractionRange->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
```

---

## 9. 함정 & 안티패턴

| # | 함정 | 정답 |
|---|------|-----|
| 1 | 매 Tick `SetBoxExtent` / `SetSphereRadius` 호출 | 변경 시점에만 호출. 또는 `bUpdateOverlaps=false` 후 명시 `UpdateOverlaps()` |
| 2 | 생성자 안 `SetBoxExtent` 호출 (콜리전 시스템 미초기화) | 생성자는 `InitBoxExtent` (콜리전 갱신 안 함). 런타임은 `SetBoxExtent` |
| 3 | 큰 트리거 박스로 NavMesh 영향 (Bridge/Tunnel 등) | `SetCanEverAffectNavigation(false)` 또는 `bDynamicObstacle=false` |
| 4 | Sphere 컴포넌트의 비대칭 스케일 → 늘어난 구체 기대 | Sphere 는 균등. 늘리려면 Capsule (Z 만 따로) 또는 Box |
| 5 | Capsule 의 `HalfHeight < Radius` 직접 설정 | `InitCapsuleSize` / `SetCapsuleSize` 사용 — 자동 보정 |
| 6 | 트리거에 `Block All` 콜리전 프로필 | Trigger 는 `Overlap` (Block 시 캐릭터 멈춤) |
| 7 | 트리거 OverlapEvent 안 `Cast<APawn>` 후 다른 컴포넌트 가져오기 (`OtherActor->FindComponentByClass<>()`) | 인터페이스 사용 또는 Component Tag 검사 |
| 8 | `OnComponentBeginOverlap` 콜백에서 `Destroy()` 호출 — Iterator 충돌 | `SetLifeSpan(0.001f)` 또는 다음 프레임 destroy |
| 9 | UBrushComponent 를 신규 코드에서 사용 | `UBoxComponent` / `USphereComponent` 사용 |
| 10 | 트리거 Pivot 이 박스 중심 아닌 코너 | 트리거 박스는 중심 Pivot — `UStaticMeshComponent` 와 다름 |
| 11 | 🚨 **OverlapBegin 콜백 안 `TActorIterator`** 사용 | 절대 — Subsystem / Spatial Hash. [`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md) |
| 12 | 🚨 **OverlapBegin 콜백 첫 줄 프로파일링 스코프 누락** | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무. [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) |

---

## 10. 체크리스트 (Shape 컴포넌트 작성)

- [ ] 어떤 Shape (Box/Sphere/Capsule)? 비용 우선순위 Sphere → Capsule → Box
- [ ] 생성자: `Init*` 사용 (콜리전 갱신 안 함)
- [ ] 런타임: `Set*(InNew, bUpdateOverlaps=false)` + 명시 `UpdateOverlaps()` (필요 시 1회)
- [ ] 콜리전 프로필: 트리거 = `Trigger`, Pawn = `Pawn`, Custom 채널 사용?
- [ ] `SetGenerateOverlapEvents` 명시 — 필요 없으면 false (비용 0)
- [ ] `SetCanEverAffectNavigation(false)` 검토 (NavMesh 영향 없으면)
- [ ] `bDynamicObstacle` 는 정말 필요할 때만 (NavMesh 재계산 비용)
- [ ] `OnComponentBeginOverlap` / `OnComponentEndOverlap` 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`
- [ ] 콜백 안 `TActorIterator` 절대 안 씀
- [ ] BoxComponent: extent 는 **half** 값 (전체가 아님)
- [ ] CapsuleComponent: `HalfHeight ≥ Radius` 보장 — `Init*` / `Set*` 사용
- [ ] 🚨 매 Tick 콜리전 크기 변경 안 함 — Overlap 갱신 비용 ↑

---

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. UShapeComponent (베이스 + bUseArchetypeBodySetup BodySetup 공유) + UBoxComponent (BoxExtent half) + USphereComponent (균등 스케일) + UCapsuleComponent (HalfHeight ≥ Radius 보장 + 8개 Scaled/Unscaled 헬퍼 + ACharacter RootComponent) + UBrushComponent (BSP/Volume 에디터). Overlap 비용 (Shape 별 비교) + NavMesh 비용 + 표준 패턴 3종 (트리거/Pawn/InteractionRange) + 함정 12종 + 체크리스트. |
