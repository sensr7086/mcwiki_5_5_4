---
name: components-specialcomponents
description: USplineComponent + USplineMeshComponent + UTimelineComponent + UStereoLayerComponent + 6대 정책.
---

# Components / SpecialComponents — Spline + Timeline + Stereo Layer (Engine 모듈)

> **위치**: `Engine/Source/Runtime/Engine/Classes/Components/{SplineComponent,SplineMeshComponent,TimelineComponent,StereoLayerComponent}.h`
> **베이스**: `USceneComponent` → `USplineComponent` / `UStereoLayerComponent` / `UStaticMeshComponent` → `USplineMeshComponent` / `UActorComponent` → `UTimelineComponent`
> **요지**: **특수 목적 컴포넌트** — 경로/스플라인, 시간 기반 곡선 애니메이션, VR/AR Stereo Layer.

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

| # | 컴포넌트 | 베이스 | 역할 |
|---|---------|--------|------|
| 1 | `USplineComponent` | `USceneComponent` | 경로 / 곡선 (3D Bezier) |
| 2 | `USplineMeshComponent` | `UStaticMeshComponent` | StaticMesh 를 스플라인 따라 변형 |
| 3 | `UTimelineComponent` | `UActorComponent` | Curve 기반 시간 애니메이션 |
| 4 | `UStereoLayerComponent` | `USceneComponent` | VR/AR HMD 레이어 (Quad/Cylinder/Cubemap/Equirect) |

---

## 2. USplineComponent — 경로

[`SplineComponent.h`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/SplineComponent.h):

### 2.1 핵심 필드

| 필드 | 의미 |
|------|------|
| `SplineCurves` | `FSplineCurves` — Position/Rotation/Scale Curve |
| `bSplineHasBeenEdited` | 에디터 편집 여부 (재계산 트리거) |
| `bClosedLoop` | 루프 |
| `bDrawDebug` | 에디터 시각화 |
| `Duration` | Spline 시간 (Timeline 통합 시) |
| `bAllowDiscontinuousSpline` | 이산 (각진) Spline 허용 |
| `bModifiedByConstructionScript` | CS 에서 변경 표시 |

### 2.2 핵심 메소드

```cpp
// 점 추가/제거
Spline->AddSplinePoint(Location, ESplineCoordinateSpace::World);
Spline->AddSplinePointAtIndex(Location, Index, ESplineCoordinateSpace::World);
Spline->RemoveSplinePoint(Index);
Spline->ClearSplinePoints();

// Tangent / Type
Spline->SetSplinePointType(Index, ESplinePointType::Curve);   // Linear/Curve/Constant/CurveCustomTangent
Spline->SetTangentAtSplinePoint(Index, Tangent, ESplineCoordinateSpace::World);

// 거리/시간 기반 샘플링
const float Distance = Spline->GetDistanceAlongSplineAtSplinePoint(Index);
const float SplineLength = Spline->GetSplineLength();
const FVector Loc = Spline->GetLocationAtDistanceAlongSpline(D, ESplineCoordinateSpace::World);
const FVector Tan = Spline->GetTangentAtDistanceAlongSpline(D, ESplineCoordinateSpace::World);
const FQuat Rot = Spline->GetRotationAtDistanceAlongSpline(D, ESplineCoordinateSpace::World).Quaternion();

// 시간 기반 (0 ~ Duration)
const FVector LocByTime = Spline->GetLocationAtTime(Time, ESplineCoordinateSpace::World);

// Closest Point
const float Dist = Spline->FindInputKeyClosestToWorldLocation(Location);
```

### 2.3 표준 사용

```cpp
// AAIPatrolPath::AAIPatrolPath
PatrolSpline = CreateDefaultSubobject<USplineComponent>(TEXT("Spline"));
RootComponent = PatrolSpline;

// AI 가 Spline 따라 이동
void AAIController::MoveAlongSpline(USplineComponent* Spline, float& CurrentDistance)
{
    CurrentDistance += MoveSpeed * GetWorld()->GetDeltaSeconds();
    if (CurrentDistance > Spline->GetSplineLength())
    {
        CurrentDistance = 0.f;   // 또는 멈춤
    }
    const FVector Target = Spline->GetLocationAtDistanceAlongSpline(CurrentDistance, ESplineCoordinateSpace::World);
    GetPawn()->SetActorLocation(Target);
}
```

---

## 3. USplineMeshComponent — Mesh 변형

[`SplineMeshComponent.h`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/SplineMeshComponent.h):

### 3.1 핵심 필드 + 메소드

```cpp
// SplineParams 구조체 (Start/End)
SplineMesh->SetStartAndEnd(StartPos, StartTangent, EndPos, EndTangent, /*bUpdate=*/true);

// 또는 개별 설정
SplineMesh->SetStartPosition(StartPos);
SplineMesh->SetStartTangent(StartTangent);
SplineMesh->SetEndPosition(EndPos);
SplineMesh->SetEndTangent(EndTangent);

SplineMesh->SetForwardAxis(ESplineMeshAxis::X);   // Mesh 의 어느 축이 Spline 방향
SplineMesh->SetSplineUpDir(FVector::UpVector);    // Up 축

// 스케일 곡선
SplineMesh->SetStartScale(FVector2D(1, 1));
SplineMesh->SetEndScale(FVector2D(0.5f, 0.5f));   // 끝으로 갈수록 가늘어짐
```

### 3.2 표준 사용 — 도로/케이블/덩굴

```cpp
// 두 점 사이 케이블
USplineMeshComponent* Mesh = NewObject<USplineMeshComponent>(this);
Mesh->RegisterComponent();
Mesh->AttachToComponent(RootComponent, FAttachmentTransformRules::KeepRelativeTransform);
Mesh->SetStaticMesh(CableMesh);
Mesh->SetStartAndEnd(Start, StartTan, End, EndTan, true);
Mesh->SetForwardAxis(ESplineMeshAxis::X);
```

### 3.3 USplineComponent + USplineMeshComponent 도로 패턴

```cpp
// Spline 의 각 세그먼트마다 SplineMesh 1개
const int32 N = Spline->GetNumberOfSplinePoints();
for (int32 i = 0; i < N - 1; ++i)
{
    USplineMeshComponent* SegMesh = NewObject<USplineMeshComponent>(this);
    SegMesh->SetStaticMesh(RoadMesh);
    SegMesh->SetForwardAxis(ESplineMeshAxis::X);

    const FVector Start = Spline->GetLocationAtSplinePoint(i, ESplineCoordinateSpace::Local);
    const FVector StartTan = Spline->GetTangentAtSplinePoint(i, ESplineCoordinateSpace::Local);
    const FVector End = Spline->GetLocationAtSplinePoint(i + 1, ESplineCoordinateSpace::Local);
    const FVector EndTan = Spline->GetTangentAtSplinePoint(i + 1, ESplineCoordinateSpace::Local);

    SegMesh->SetStartAndEnd(Start, StartTan, End, EndTan, true);
    SegMesh->AttachToComponent(RootComponent, FAttachmentTransformRules::KeepRelativeTransform);
    SegMesh->RegisterComponent();
}
```

> **각 SplineMeshComponent 는 별도 `FStaticMeshSceneProxy`** — 100개 세그먼트 = 100 드로우콜. **HISM 또는 Nanite** 가 더 나은 경우 많음.

---

## 4. UTimelineComponent — 시간 곡선 애니메이션

[`TimelineComponent.h`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/TimelineComponent.h):

### 4.1 핵심 메소드

```cpp
// 1. Timeline 정의 (생성자 또는 BeginPlay)
TimelineComp = CreateDefaultSubobject<UTimelineComponent>(TEXT("Timeline"));

// 2. Curve 추가 (FloatCurve / VectorCurve / LinearColorCurve / EventTrack)
FOnTimelineFloat OnUpdate;
OnUpdate.BindUFunction(this, FName("OnTimelineUpdate"));
TimelineComp->AddInterpFloat(MyCurve, OnUpdate);

FOnTimelineEvent OnFinished;
OnFinished.BindUFunction(this, FName("OnTimelineFinished"));
TimelineComp->SetTimelineFinishedFunc(OnFinished);

// Vector Curve
FOnTimelineVector OnVectorUpdate;
OnVectorUpdate.BindUFunction(this, FName("OnVectorUpdate"));
TimelineComp->AddInterpVector(MyVectorCurve, OnVectorUpdate);

// 3. 제어
TimelineComp->Play();              // 처음부터
TimelineComp->PlayFromStart();
TimelineComp->Reverse();
TimelineComp->Stop();
TimelineComp->SetLooping(true);
TimelineComp->SetPlayRate(2.0f);

// 4. UFUNCTION 콜백
UFUNCTION()
void OnTimelineUpdate(float Value)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyActor_TimelineUpdate);
    GetMesh()->SetRelativeLocation(FVector(0, 0, Value));
}
```

### 4.2 Direction

| 메소드 | 동작 |
|--------|------|
| `Play()` | 정방향 (현재 위치부터) |
| `PlayFromStart()` | 정방향 (0 부터) |
| `Reverse()` | 역방향 (현재 위치부터) |
| `ReverseFromEnd()` | 역방향 (끝부터) |

### 4.3 EventTrack — 특정 시점 콜백

```cpp
FOnTimelineEvent OnEvent;
OnEvent.BindUFunction(this, FName("OnEventFire"));
TimelineComp->AddEvent(0.5f, OnEvent);   // 0.5초에 발화
```

### 4.4 표준 사용 — 문 열림 / 깜빡임

```cpp
// 문 열림 — Yaw 0 → 90° 회전
void ADoor::Open()
{
    if (!TimelineComp->IsPlaying())
    {
        TimelineComp->PlayFromStart();
    }
}

UFUNCTION()
void ADoor::OnTimelineUpdate(float Value)
{
    DoorMesh->SetRelativeRotation(FRotator(0, FMath::Lerp(0.f, 90.f, Value), 0));
}
```

---

## 5. UStereoLayerComponent — VR/AR HMD 레이어

[`StereoLayerComponent.h:268-400`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/StereoLayerComponent.h):

### 5.1 Shape 4종 (`StereoLayerComponent.h:73-260`)

| 클래스 | 모양 |
|--------|------|
| `UStereoLayerShapeQuad` | 평면 사각형 — UI 패널 |
| `UStereoLayerShapeCylinder` | 곡면 실린더 — 휘어진 메뉴 |
| `UStereoLayerShapeCubemap` | 큐브맵 — 스카이박스 |
| `UStereoLayerShapeEquirect` | 에쿼렉탱귤러 — 360° 영상 |

### 5.2 핵심 필드

| 필드 | 의미 |
|------|------|
| `Texture` | `UTexture*` — 표시 텍스쳐 |
| `LeftTexture` | 스테레오 좌안 텍스쳐 (3D 영상) |
| `bSupportsDepth` | 깊이 통합 (Depth 합성) |
| `bNoAlphaChannel` | 알파 채널 무시 |
| `bQuadPreserveTextureRatio` | 비율 유지 |
| `QuadSize` | 패널 크기 (Quad) |
| `UVRect` | UV 영역 |
| `StereoLayerType` | World/FaceLocked/TrackerLocked |
| `Priority` | 같은 위치 레이어 우선순위 |
| `Shape` | `UStereoLayerShape*` 인스턴스 |

### 5.3 동작

> **HMD 가 직접 합성** — UMG WidgetComponent 보다 픽셀 명확 (HMD 의 reprojection 후에도 또렷). VR HUD / 메뉴 표준.

```cpp
StereoLayer = CreateDefaultSubobject<UStereoLayerComponent>(TEXT("Layer"));
StereoLayer->Texture = UITexture;
StereoLayer->Shape = NewObject<UStereoLayerShapeQuad>(this);
StereoLayer->QuadSize = FVector2D(100, 100);
StereoLayer->StereoLayerType = SLT_TrackerLocked;   // 사용자 손에 고정
```

> **5.x VR 표준** — 단 모든 HMD 가 모든 Shape 지원 안 함 (Quad / Cylinder 가장 호환).

---

## 6. 함정 & 안티패턴

| # | 함정 | 정답 |
|---|------|-----|
| 1 | SplineMesh 100개 세그먼트 + 단순 Mesh — 드로우콜 폭사 | HISM 또는 Nanite 활용 |
| 2 | Spline 매 Tick `GetLocationAtDistanceAlongSpline` 호출 (긴 스플라인) | 캐시 또는 인덱스 기반 |
| 3 | Timeline Tick 안 `Set*` 매 프레임 (값 동일) | 변경 시점만 또는 Timeline 자체 정지 |
| 4 | Timeline Curve 가 Tick 비 `LinearTangent` (모든 점 Curve) | Linear 도 적절히 사용 |
| 5 | Timeline + UFUNCTION 콜백 안 `TActorIterator` | 등록 패턴 ([`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md)) |
| 6 | StereoLayer 가 모든 HMD Shape 지원한다고 가정 | Quad/Cylinder 가장 호환 |
| 7 | Spline 의 `bSplineHasBeenEdited = true` 매 프레임 | ConstructionScript 외 변경 안 함 |
| 8 | 🚨 Timeline 콜백 첫 줄 프로파일링 스코프 누락 | 의무 ([`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)) |

---

## 7. 체크리스트

- [ ] Spline: bClosedLoop / Duration 명시
- [ ] SplineMesh: SetForwardAxis 정확 (Mesh 의 길이 축)
- [ ] SplineMesh: 100+ 세그먼트면 HISM/Nanite 검토
- [ ] Timeline: Play / Reverse / SetLooping 사용 — 직접 Tick 안 함
- [ ] Timeline: UFUNCTION 콜백 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE`
- [ ] StereoLayer: Quad/Cylinder 가장 호환 — 다른 Shape 은 HMD 호환 검증
- [ ] Spline 의 `GetLocationAtDistanceAlongSpline` 매 Tick 호출 시 캐시 검토

---

## 8. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. 4개 SpecialComponents — USplineComponent (Bezier 곡선 + 거리/시간 샘플링) + USplineMeshComponent (Mesh 변형 + 도로 패턴) + UTimelineComponent (Curve 기반 + Play/Reverse/Event Track + UFUNCTION 콜백) + UStereoLayerComponent (VR/AR HMD 레이어 + 4 Shape Quad/Cylinder/Cubemap/Equirect). 함정 8종 + 체크리스트. |
