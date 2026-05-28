---
name: animation-ragdoll
description: Ragdoll (Skeletal 물리 시뮬) — USkeletalMeshComponent SetSimulatePhysics + SetAllBodiesBelowSimulatePhysics + SetPhysicsBlendWeight + BreakConstraint + UPhysicsAsset + 방향성 시뮬레이션 (AddImpulse / AddImpulseAtLocation / AddRadialImpulse / AddForce / AddAngularImpulse / SetPhysicsLinearVelocity 9 API). 죽음/히트 전환 + 초기 속도 계승 + 본별 충격 (헤드샷/풋샷) + 중력 변경 (Zero-G) + 바람 / 폭발 + UPhysicalAnimationComponent (5.x) + Mobile 제약 + Network 동기.
---

# Animation/Ragdoll — Skeletal 물리 시뮬 + 죽음/히트 전환

> **위치**: `Engine/Source/Runtime/Engine/Classes/Components/SkeletalMeshComponent.h` (`SetSimulatePhysics:1962` / `SetAllBodiesBelowSimulatePhysics:2230` / `SetPhysicsBlendWeight:2207` / `BreakConstraint:2353`) + `Engine/Source/Runtime/Engine/Classes/PhysicsEngine/PhysicsAsset.h` (UPhysicsAsset)
> **베이스**: USkeletalMeshComponent (Mesh) + UPhysicsAsset (자산) + FBodyInstance (Body 별)
> **요지**: Skeletal Mesh 의 본 단위 물리 시뮬 — 죽음 / 다운 / 폭발 / 충돌 반응. Animation ↔ Physics blend + PhysicsAsset Profile 표준.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | `OnRagdollStart` / `OnConstraintBreak` 콜백 첫 줄 스코프 |
| 🚨 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) §3 | UPhysicsAsset 멤버 = `UPROPERTY()` + `TSoftObjectPtr` (메모리 큼) |
| 🎯 [`12_AssetOptimizationPolicy.md`](../../../references/12_AssetOptimizationPolicy.md) §1 | 다수 NPC Ragdoll = Significance + Bone LOD + Body 수 제한 |
| 🚨 Network | Ragdoll = Replicated 의무 (서버 권한 + 클라 시뮬) — 비결정 동작 주의 |

---

## 1. Ragdoll 활성 — 5 API

### 1.1 전체 Ragdoll (가장 단순)

```cpp
// 캐릭터 죽음 처리
void AMyChar::Die()
{
    UE_PROFILE();
    USkeletalMeshComponent* Mesh = GetMesh();
    if (!IsValid(Mesh)) return;

    // 1. CharacterMovement 비활성 (CMC 가 충돌 처리 중지)
    if (auto* CMC = GetCharacterMovement())
    {
        CMC->DisableMovement();
        CMC->StopMovementImmediately();
    }

    // 2. 콜리전 프로필 = Ragdoll (Capsule 무시, Mesh 자체가 콜리전)
    Mesh->SetCollisionProfileName(TEXT("Ragdoll"));

    // 3. 모든 본 시뮬레이션 ON
    Mesh->SetSimulatePhysics(true);

    // 4. Capsule 콜리전 비활성 (Mesh 가 대신)
    GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}
```

### 1.2 부분 Ragdoll (상체만)

```cpp
// 상체만 Ragdoll (히트 반응 / 다운)
void AMyChar::UpperBodyRagdoll()
{
    UE_PROFILE();
    USkeletalMeshComponent* Mesh = GetMesh();

    // spine_01 본 아래 모든 본 = 시뮬레이션 ON
    Mesh->SetAllBodiesBelowSimulatePhysics(
        TEXT("spine_01"),
        /*bNewSimulate=*/ true,
        /*bIncludeSelf=*/ true);

    // Physics Blend = 0.7 (애니 30% + 물리 70%)
    Mesh->SetAllBodiesBelowPhysicsBlendWeight(TEXT("spine_01"), 0.7f, /*bSkipCustomPhysicsType=*/ false, /*bIncludeSelf=*/ true);
}
```

### 1.3 본 단위 충돌 — Constraint 끊기

```cpp
// 본 떨어뜨리기 (예: 폭발 시 팔 떨어짐)
void AMyChar::ExplodeImpulse(FVector ExplosionLocation, float Strength)
{
    UE_PROFILE();
    USkeletalMeshComponent* Mesh = GetMesh();

    FVector ImpactDir = (Mesh->GetSocketLocation(TEXT("upperarm_l")) - ExplosionLocation).GetSafeNormal();
    FVector Impulse = ImpactDir * Strength;

    // upperarm_l 본의 Constraint 끊기
    Mesh->BreakConstraint(Impulse, ExplosionLocation, TEXT("upperarm_l"));
}
```

---

## 2. SetPhysicsBlendWeight (Animation ↔ Physics 블렌드)

### 2.1 사용 — 부드러운 전환

```cpp
// 죽음 시 — Animation 100% → Ragdoll 100% 부드럽게 (1초)
void AMyChar::SmoothRagdollTransition()
{
    USkeletalMeshComponent* Mesh = GetMesh();
    Mesh->SetSimulatePhysics(true);

    // 시작 — Animation 100%
    Mesh->SetPhysicsBlendWeight(0.0f);

    // Timer 로 점차 증가 (0 → 1 over 1.0s)
    FTimerHandle BlendTimer;
    GetWorld()->GetTimerManager().SetTimer(BlendTimer,
        [WeakMesh = TWeakObjectPtr<USkeletalMeshComponent>(Mesh)]()
        {
            if (auto* M = WeakMesh.Get())
            {
                float Current = M->GetBoneAccessor(0).PhysicsBlendWeight;  // 추정
                float New = FMath::Min(Current + 0.1f, 1.0f);
                M->SetPhysicsBlendWeight(New);
            }
        },
        0.1f, /*bLoop=*/ true);
}
```

### 2.2 Blend Weight 의미

| 값 | 의미 |
|----|------|
| 0.0 | Animation 100% (시뮬 X) |
| 0.5 | Animation 50% + Physics 50% (부분 반응) |
| 1.0 | Physics 100% (완전 Ragdoll) |

---

## 3. UPhysicsAsset 표준 셋업

### 3.1 PhysicsAsset 구조

```
UPhysicsAsset (자산 — .uasset)
├── SkeletalBodySetup × N        (각 본의 Body Setup)
│   ├── Sphyl / Box / Sphere (Collision Shape)
│   ├── Mass / Linear Damping / Angular Damping
│   └── Physical Material
└── PhysicsConstraintTemplate × N  (관절 — Body 간 연결)
    ├── 6DoF Constraint (3 Translation + 3 Rotation)
    └── Joint Limit / Damping
```

### 3.2 Body 추가 (Editor 작업)

```
PhysicsAsset Editor:
1. Bone 선택
2. Generate Body (자동 Shape 생성)
3. Body Setup:
   - Shape = Sphyl (캡슐 형태) 또는 Box / Sphere
   - Mass = 자동 (BodySetup.MassScale 조정)
   - PhysicalMaterial = 본별 (관절 = 부드러움, 머리 = 무거움)
4. Constraint 자동 생성 (부모 Body 와 연결)
```

### 3.3 Constraint 설정 (관절 한계)

```
6 DoF Constraint:
- Linear Motion (X/Y/Z): Lock / Limited / Free
- Angular Motion (Swing1/Swing2/Twist): Locked / Limited / Free

표준:
- 어깨 / 엉덩이 = Swing1/2 Limited (45~90도) + Twist Limited
- 무릎 / 팔꿈치 = Swing1 Limited (0~135도) + 나머지 Lock
- 손목 / 발목 = Twist Limited + Swing 작게
```

---

## 4. UPhysicalAnimationComponent (5.x — 강력)

Animation 위에 Physics 보강 (전체 Ragdoll 없이 부분 시뮬).

### 4.1 사용

```cpp
// AMyChar.h
UPROPERTY(VisibleAnywhere)
TObjectPtr<UPhysicalAnimationComponent> PhysicalAnimComp;

// AMyChar.cpp Constructor
AMyChar::AMyChar()
{
    PhysicalAnimComp = CreateDefaultSubobject<UPhysicalAnimationComponent>(TEXT("PhysicalAnim"));
}

// 활성
void AMyChar::EnablePhysicalAnimation()
{
    PhysicalAnimComp->SetSkeletalMeshComponent(GetMesh());

    // 본별 Strength 설정 (Profile)
    FPhysicalAnimationData PhysicalAnimData;
    PhysicalAnimData.bIsLocalSimulation = true;
    PhysicalAnimData.OrientationStrength = 1000.0f;
    PhysicalAnimData.AngularVelocityStrength = 100.0f;
    PhysicalAnimData.PositionStrength = 1000.0f;
    PhysicalAnimData.VelocityStrength = 100.0f;
    PhysicalAnimData.MaxLinearForce = 0.0f;
    PhysicalAnimData.MaxAngularForce = 0.0f;

    // spine_01 본 아래 모두 적용
    PhysicalAnimComp->ApplyPhysicalAnimationSettingsBelow(TEXT("spine_01"), PhysicalAnimData);
}
```

### 4.2 효과
- Animation 이 Pose 결정 + Physics 가 외력 반응 (예: 폭발 / 충격)
- Animation 완전 무시 (Ragdoll) 와 Animation 완전 사용 (없음) 의 중간

---

## 5. 죽음 시 표준 흐름 (5단)

```cpp
void AMyChar::HandleDeath()
{
    UE_PROFILE();

    // 1. AI / Controller 분리 (이미 죽었으므로)
    if (auto* AC = GetController())
    {
        AC->UnPossess();
    }

    // 2. CharacterMovement 비활성
    if (auto* CMC = GetCharacterMovement())
    {
        CMC->DisableMovement();
        CMC->StopMovementImmediately();
    }

    // 3. Capsule 콜리전 비활성 (Mesh 가 대신)
    GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);

    // 4. Mesh = Ragdoll
    USkeletalMeshComponent* Mesh = GetMesh();
    Mesh->SetCollisionProfileName(TEXT("Ragdoll"));
    Mesh->SetSimulatePhysics(true);

    // 5. Death Force 적용 (선택 — 임팩트 방향)
    Mesh->AddImpulse(LastHitDirection * 1000.0f, NAME_None, /*bVelChange=*/ false);

    // 6. Lifespan (10초 후 자동 Destroy)
    SetLifeSpan(10.0f);
}
```

---

## 6. 방향성 Ragdoll 시뮬레이션 ⭐ (히트 / 폭발 / 모멘텀 / 중력)

> Ragdoll 단순 활성 (Section 1) 보다 한 단계 깊이 — **힘 방향 / 속도 / 회전 / 본별 충격** 으로 자연스러운 반응.

### 6.1 힘 / 임펄스 API 매트릭스 (PrimitiveComponent / SkeletalMeshComponent)

| API | 단위 | 영향 | 사용 시점 |
|-----|------|------|---------|
| `AddImpulse(Impulse, BoneName, bVelChange)` | 즉발 (속도 변경) | 본 1개 (NAME_None = 전체) | 총알 히트 / 펀치 |
| `AddImpulseAtLocation(Impulse, Location, BoneName)` | 즉발 + 위치 기반 토크 | 본 + 회전 발생 | 비대칭 충격 |
| `AddRadialImpulse(Origin, Radius, Strength, Falloff, bVelChange)` | 원형 폭발 | 범위 내 모든 본 | 폭발 / 충격파 |
| `AddForce(Force, BoneName, bAccelChange)` | 지속 힘 | 본 1개 | 바람 / 자기장 |
| `AddForceAtLocation(Force, Location, BoneName)` | 지속 + 토크 | 본 + 회전 | 비대칭 지속 |
| `AddRadialForce(Origin, Radius, Strength, Falloff)` | 원형 지속 | 범위 내 본들 | 회오리 / 인력 |
| `AddTorque(Torque, BoneName, bAccelChange)` | 회전 즉발 | 본 1개 | 회전 충격 |
| `AddAngularImpulse(AngularImpulse, BoneName, bVelChange)` | 회전 즉발 (각속도 변경) | 본 1개 | 빠른 회전 |
| `SetPhysicsLinearVelocity(NewVelocity, bAddToCurrent, BoneName)` | 절대 속도 설정 | 본 1개 | 초기 속도 설정 |
| `SetPhysicsAngularVelocityInDegrees(Vel, bAddToCurrent, BoneName)` | 절대 각속도 설정 | 본 1개 | 회전 초기화 |

### 6.2 히트 방향 충격 (가장 흔함)

```cpp
// 히트 방향에 따른 비대칭 임펄스 (총알 / 펀치)
void AMyChar::ApplyHitImpulse(FVector HitDirection, FVector HitLocation, FName HitBone, float Strength)
{
    UE_PROFILE();
    USkeletalMeshComponent* Mesh = GetMesh();
    if (!IsValid(Mesh) || !Mesh->IsSimulatingPhysics(HitBone))
    {
        return;   // Ragdoll 활성 후만 의미
    }

    // ⭐ AddImpulseAtLocation — 위치 기반 (자동 토크 발생)
    FVector Impulse = HitDirection.GetSafeNormal() * Strength;
    Mesh->AddImpulseAtLocation(Impulse, HitLocation, HitBone);
}

// 사용 — 총알 히트
void AMyChar::OnBulletHit(const FHitResult& Hit, FVector BulletVelocity)
{
    // 1. 데미지 처리 → 죽음
    if (Health <= 0)
    {
        Die();   // Ragdoll 활성
    }

    // 2. 히트 방향 충격 (Ragdoll 활성 후)
    FVector HitDir = -Hit.ImpactNormal;   // 입사 방향
    ApplyHitImpulse(BulletVelocity * 0.5f, Hit.ImpactPoint, Hit.BoneName, 500.0f);
}
```

### 6.3 폭발 — Radial Impulse (방사형)

```cpp
// 폭발 = 위치 중심 + 거리 falloff (모든 본에 적용)
void AMyChar::ApplyExplosionImpulse(FVector ExplosionLocation, float Radius, float Strength)
{
    UE_PROFILE();
    USkeletalMeshComponent* Mesh = GetMesh();
    if (!IsValid(Mesh)) return;

    // 모든 본 = 위치별 다른 충격 (거리 falloff)
    Mesh->AddRadialImpulse(
        ExplosionLocation,
        Radius,
        Strength,
        ERadialImpulseFalloff::RIF_Linear,   // 선형 감쇠
        /*bVelChange=*/ false);              // 질량 영향 받음
}

// 폭발 + RadialForce 컴포넌트 결합 (지속 힘)
void AMyChar::ApplyExplosionWithLingerForce(FVector Loc, float Radius, float Strength)
{
    // 즉발 — Impulse
    GetMesh()->AddRadialImpulse(Loc, Radius, Strength, ERadialImpulseFalloff::RIF_Linear, false);

    // 추가 지속 — RadialForceComponent (5초간 약한 힘)
    URadialForceComponent* Force = NewObject<URadialForceComponent>(this);
    Force->RegisterComponent();
    Force->SetWorldLocation(Loc);
    Force->Radius = Radius;
    Force->ForceStrength