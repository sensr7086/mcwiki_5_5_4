---
name: assetclasses-physics
description: UPhysicalMaterial + EPhysicalSurface 32종 + UPhysicalMaterialMask 5.x + UPhysicsConstraintTemplate (6DoF Profile).
---

# AssetClasses/Physics — UPhysicalMaterial + UPhysicalMaterialMask + UPhysicsConstraintTemplate + UPhysicsAsset (cross-link)

> **위치**: `Engine/Source/Runtime/Engine/Public/PhysicalMaterials/PhysicalMaterial.h` + `Classes/PhysicalMaterials/PhysicalMaterialMask.h` + `Classes/PhysicsEngine/PhysicsConstraintTemplate.h` + `PhysicsAsset.h` (이미 [`AssetClasses/Mesh §4`](../Mesh/SKILL.md))
> **베이스**: `UPhysicalMaterial : public UObject` / `UPhysicsConstraintTemplate : public UObject`
> **요지**: **물리 재질 + 콘스트레인트 템플릿** — 표면 마찰·반발·서피스 종류 (발자국·총알 흔적) 결정.

---

## 🚨 공통 정책

| 정책 | Physics 자산 적용 |
|------|------------------|
| 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) | PhysicalMaterial = 작은 자산 (Hard OK). PhysicsAsset = 큰 자산 (이미 SkeletalMesh 페어 — 자동 함께 로드). |
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | OnHit / OnPhysicsImpactCallback 첫 줄 스코프. |

---

## 1. UPhysicalMaterial (마찰·반발·서피스 종류)

```cpp
class UPhysicalMaterial : public UObject
{
    // 마찰 계수 (0~1+ — 1.0 = 일반 / 2.0 = 고무 / 0.1 = 얼음)
    UPROPERTY(EditAnywhere)
    float Friction;

    // 마찰 조합 모드 (Average / Min / Max / Multiply)
    UPROPERTY(EditAnywhere)
    TEnumAsByte<enum EFrictionCombineMode::Type> FrictionCombineMode;

    // 반발 계수 (0~1)
    UPROPERTY(EditAnywhere)
    float Restitution;

    // 반발 조합 모드
    UPROPERTY(EditAnywhere)
    TEnumAsByte<enum EFrictionCombineMode::Type> RestitutionCombineMode;

    // 밀도 (kg/cm^3) — Mass 자동 계산
    UPROPERTY(EditAnywhere)
    float Density;

    // 슬립 임계값
    UPROPERTY(EditAnywhere)
    float SleepLinearVelocityThreshold;
    UPROPERTY(EditAnywhere)
    float SleepAngularVelocityThreshold;

    // ⭐ Surface Type — 발자국 / 총알 흔적 결정 (가장 흔한 사용)
    UPROPERTY(EditAnywhere)
    TEnumAsByte<EPhysicalSurface> SurfaceType;
};
```

### 1.1 EPhysicalSurface (32종 — Project Settings 에서 정의)

```ini
; DefaultEngine.ini
[/Script/Engine.PhysicsSettings]
PhysicalSurfaces=(SurfaceType=SurfaceType1, Name="Concrete")
PhysicalSurfaces=(SurfaceType=SurfaceType2, Name="Wood")
PhysicalSurfaces=(SurfaceType=SurfaceType3, Name="Metal")
PhysicalSurfaces=(SurfaceType=SurfaceType4, Name="Grass")
PhysicalSurfaces=(SurfaceType=SurfaceType5, Name="Water")
; ... 최대 32종
```

### 1.2 Surface Type 사용 패턴 (발자국 / 총알 흔적)

```cpp
// 라인 트레이스 후 어떤 표면?
FHitResult Hit;
if (GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility))
{
    EPhysicalSurface Surface = UGameplayStatics::GetSurfaceType(Hit);
    switch (Surface)
    {
        case SurfaceType1: PlayFootstep_Concrete(); break;
        case SurfaceType2: PlayFootstep_Wood(); break;
        case SurfaceType3: PlayFootstep_Metal(); break;
        // ...
    }
}

// 또는 데이터 테이블 매핑
FFootstepRow* Row = FootstepTable->FindRow<FFootstepRow>(GetSurfaceFName(Surface), TEXT(""));
PlaySound(Row->FootstepSound);
SpawnDecal(Row->FootstepDecal);
```

---

## 2. UPhysicalMaterialMask (Material 안 마스크 — 5.x)

```cpp
// 단일 Material 에 다중 Surface Type (예: 도로 + 도로변 잔디)
class UPhysicalMaterialMask : public UPhysicalMaterial
{
    // Mask Texture
    UPROPERTY(EditAnywhere)
    TObjectPtr<UTexture> MaskTexture;

    // 채널 별 Surface Type
    UPROPERTY(EditAnywhere)
    TArray<TEnumAsByte<EPhysicalSurface>> PhysicalMaterialMap;
};

// 사용 — Material 에서 PhysicalMaterialMask 활성 → UV 기반 Surface 결정
```

---

## 3. UPhysicsConstraintTemplate (Constraint 자산)

> **PhysicsAsset 안에서 사용** — 본 ↔ 본 연결 정의. PhysicsConstraintComponent 가 런타임 호스트.

```cpp
// PhysicsConstraintTemplate.h
class UPhysicsConstraintTemplate : public UObject
{
    // 6DoF Constraint 설정
    UPROPERTY()
    FConstraintProfileProperties DefaultProfile;

    // 다중 Profile (런타임 전환)
    UPROPERTY()
    TArray<FName> ProfileNames;

    UPROPERTY()
    TArray<FConstraintProfileProperties> ProfileInstances;
};
```

### 3.1 6DoF — 6 자유도 (Linear X/Y/Z + Angular X/Y/Z)

```cpp
struct FConstraintProfileProperties
{
    FLinearConstraint LinearLimit;          // Linear 6 자유도 (Locked / Limited / Free)
    FConeConstraint   ConeLimit;             // Cone 회전 (Swing 1/2)
    FTwistConstraint  TwistLimit;            // Twist 회전
    FConstraintDrive  LinearDrive;           // Linear 드라이브 (목표 위치)
    FConstraintDrive  AngularDrive;          // Angular 드라이브
};
```

### 3.2 Profile 동적 전환

```cpp
// PhysicsAsset 안 Constraint Profile = "Default" / "Ragdoll" / "HitReaction"
SkelMeshComp->SetConstraintProfile(BoneName, TEXT("HitReaction"), /*bDefaultIfNotFound=*/ true);
SkelMeshComp->SetConstraintProfileForAll(TEXT("Ragdoll"), false);
```

---

## 4. UPhysicsAsset (cross-link)

> **자세한 = [`AssetClasses/Mesh §4`](../Mesh/SKILL.md)** — SkeletalBodySetups / ConstraintSetup / Ragdoll 표준 패턴.

---

## 5. 함정 & 안티패턴 (6종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | EPhysicalSurface 정의 안 하고 사용 | DefaultEngine.ini 의무 등록 (32 종 한정) |
| 2 | `GetSurfaceType(Hit)` 가 SurfaceType_Default | PhysicalMaterial 미할당 — Material 에 PhysMaterial 설정 |
| 3 | Constraint Profile 동적 전환 안 함 | Default / Ragdoll / HitReaction 등 미리 정의 + `SetConstraintProfile` |
| 4 | OnHit 콜백 매 프레임 발자국 Spawn | Throttle (1 fps 제한) 또는 DistanceCheck |
| 5 | PhysicalMaterialMask 사용 시 Mask Texture 누락 | Texture + PhysicalMaterialMap 페어 의무 |
| 6 | OnHit 콜백 첫 줄 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 |

---

## 6. 관련 sub-skill

- [`AssetClasses/SKILL.md`](../SKILL.md) — 메인
- [`AssetClasses/Mesh §4`](../Mesh/SKILL.md) — UPhysicsAsset (SkeletalBodySetup + ConstraintSetup)
- [`Components/PhysicsComponents`](../../Components/references/PhysicsComponents.md) — UPhysicsConstraintComponent / Spring / Handle / Thruster (런타임 호스트)
- [`Components/PrimitiveComponent`](../../Components/references/PrimitiveComponent.md) — BodySetup (Mesh 측 Collision)
- 교차: [`08_OverlapHotspots.md`](../../../references/08_OverlapHotspots.md) (PhysicalMaterial 가 Overlap / Hit 콜백 영향)

---

## 7. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. **UPhysicalMaterial** (Friction / Restitution / Density / Sleep Threshold / **EPhysicalSurface 32종** + DefaultEngine.ini 등록 / Surface Type 사용 패턴 — 발자국·총알 흔적). **UPhysicalMaterialMask 5.x** (다중 Surface — Mask Texture + PhysicalMaterialMap). **UPhysicsConstraintTemplate** (FConstraintProfileProperties 6DoF — Linear/Cone/Twist Limit + Drive + Profile 동적 전환). **UPhysicsAsset** cross-link → AssetClasses/Mesh §4. 함정 6종. |
