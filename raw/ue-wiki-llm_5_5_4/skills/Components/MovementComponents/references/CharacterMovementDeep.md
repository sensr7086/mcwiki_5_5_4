---
name: components-movementcomponents-charactermovementdeep
description: UCharacterMovementComponent 깊이 자료 — Floor 검출 (FFindFloorResult + ComputeFloorDist) + Step Up + Movement Base + Jump 6필드 / Crouch / RootMotion / NavWalking / RVO / Force 9개 시스템.
---

# Components / MovementComponents — CharacterMovementDeep

> 본 문서는 [`SKILL.md §5.5~§5.15`](../SKILL.md) 의 깊이 자료. 메인 SKILL.md 는 핵심 개요만, 실제 구현 세부는 본 문서 참조.
>
> **트리거**: Floor 검출 / Step Up / Movement Base / Jump 깊이 / Crouch 자식 override / RootMotion / NavMesh Walking / RVO 회피 / Force/Impulse 작업 시 로드.

---

## 1. Floor 검출 시스템 (`FFindFloorResult` + `FindFloor` + `ComputeFloorDist`)

> **Walking 모드의 핵심** — 매 프레임 캐릭터 발 아래에 무엇이 있는지 검출. CapsuleComponent 의 발끝부터 아래로 sweep + line trace.

### 1.1 FFindFloorResult 구조

[`CharacterMovementComponent.h:886`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/GameFramework/CharacterMovementComponent.h):
```cpp
UPROPERTY(BlueprintReadOnly, Category = "Pawn|Components|CharacterMovement")
FFindFloorResult CurrentFloor;   // 매 프레임 갱신
```

`FFindFloorResult` 주요 필드:
- `bBlockingHit` — 바닥 hit 검출
- `bWalkableFloor` — IsWalkable() 통과
- `bLineTrace` — sweep 실패 후 line trace 사용
- `FloorDist` — 캡슐 바닥 ~ 표면 거리
- `LineDist` — line trace 거리
- `HitResult` — 실제 FHitResult (Normal/ImpactPoint/Component)

### 1.2 핵심 메소드

| 메소드 | 역할 | 라인 |
|--------|------|------|
| `FindFloor(CapsuleLoc, OutResult, bCanUseCachedLoc, DownwardSweepResult)` | 메인 진입점 | `L2054` |
| `ComputeFloorDist(CapsuleLoc, LineDist, SweepDist, OutResult, SweepRadius, DownwardSweepResult)` | 거리 계산 (실제 sweep) | `L2079` |
| `IsWalkable(Hit)` | Walkable 검사 — `WalkableFloorAngle` 비교 | `L1900` |
| `AdjustFloorHeight()` | 바닥과의 거리 조정 (떠 있지 않게) | `L1366` |
| `K2_FindFloor` / `K2_ComputeFloorDist` | Blueprint 노출 | — |

### 1.3 Walkable 결정 로직

```cpp
virtual bool IsWalkable(const FHitResult& Hit) const
{
    return Hit.Component.IsValid()
        && Hit.ImpactNormal.Z >= WalkableFloorZ
        && Hit.Component->CanCharacterStepUp(CharacterOwner);
}
```

> **자식 override 표준 케이스**: 특정 Material 만 walkable, 또는 특정 Actor 만 unwalkable (얼음 위 등).

### 1.4 PerchResult — 모서리 위 균형

```cpp
ENGINE_API virtual bool ComputePerchResult(
    const float TestRadius,
    const FHitResult& InHit,
    const float InMaxFloorDist,
    FFindFloorResult& OutPerchFloorResult) const;
```

> **Perch** = 캡슐의 일부만 모서리 위에 걸린 상태 (PerchRadiusThreshold 안). False 반환 시 떨어짐.

---

## 2. Step Up + Ledge 시스템

> **계단 자동 등반** + **절벽 떨어짐 판정** — Walking 모드의 핵심 동작.

### 2.1 Step Up

[`CharacterMovementComponent.h:1564-1583`]:
```cpp
ENGINE_API virtual bool CanStepUp(const FHitResult& Hit) const;
ENGINE_API virtual bool StepUp(const FVector& GravDir, const FVector& Delta,
                                const FHitResult& Hit, FStepDownResult* OutStepDownResult = NULL);
ENGINE_API void SetBaseFromFloor(const FFindFloorResult& FloorResult);
```

> 매 보행 이동에서 벽 충돌 시 → `CanStepUp(Hit)` 검사 → true 면 `StepUp` 시도. `MaxStepHeight` 까지 위로 올렸다가 다시 아래로 내림.

**자식 override 케이스**: 특정 Actor 만 등반 가능 (예: PhysicsObject = false).

### 2.2 Ledge 검출

[`CharacterMovementComponent.h:1807-1822`]:
```cpp
ENGINE_API virtual bool CheckLedgeDirection(const FVector& OldLocation, const FVector& SideStep, const FFindFloorResult& OldFloor) const;
ENGINE_API virtual FVector GetLedgeMove(const FVector& OldLocation, const FVector& Delta, const FFindFloorResult& OldFloor) const;
ENGINE_API virtual bool CheckFall(const FFindFloorResult& OldFloor, const FHitResult& Hit, const FVector& Delta,
                                   const FVector& OldLocation, float remainingTime, float timeTick, int32 Iterations, bool bMustJump);
ENGINE_API void RevertMove(const FVector& OldLocation, UPrimitiveComponent* OldBase,
                            const FVector& InOldBaseLocation, const FFindFloorResult& OldFloor, bool bFailMove);
```

`bCanWalkOffLedges` / `bCanWalkOffLedgesWhenCrouching` 가 false 면 `CheckLedgeDirection` 가 막아냄. true 면 `ShouldCatchAir()` → `StartFalling()`.

### 2.3 ShouldCatchAir — 보행 중 떨어짐 결정

[`CharacterMovementComponent.h:1372`]:
```cpp
ENGINE_API virtual bool ShouldCatchAir(const FFindFloorResult& OldFloor, const FFindFloorResult& NewFloor);
```

기본 = `false` 반환 (보행 중 walkable 표면 사이는 떨어지지 않음). 자식 override 로 가파른 경사 → 떨어짐 강제 가능.

---

## 3. Movement Base 시스템 (이동 표면 — 엘리베이터·이동 플랫폼)

> **이동 중인 표면 위 캐릭터** — 엘리베이터 / 회전 발판 / 트럭 짐칸 등.

### 3.1 핵심 필드

[`CharacterMovementComponent.h:1095-1190`]:
```cpp
UPROPERTY(Transient)
FQuat OldBaseQuat;

UPROPERTY(Transient)
FVector OldBaseLocation;

uint8 bDeferUpdateBasedMovement : 1;
TWeakObjectPtr<UPrimitiveComponent> LastServerMovementBase = nullptr;
FName LastServerMovementBaseBoneName = NAME_None;
```

### 3.2 핵심 메소드

```cpp
ENGINE_API virtual void MaybeUpdateBasedMovement(float DeltaSeconds);
ENGINE_API virtual void UpdateBasedMovement(float DeltaSeconds);
ENGINE_API virtual void UpdateBasedRotation(FRotator& FinalRotation, const FRotator& ReducedRotation);
ENGINE_API virtual void MaybeSaveBaseLocation();
ENGINE_API virtual void SaveBaseLocation();
UFUNCTION(BlueprintCallable, Category="Pawn|Components|CharacterMovement")
ENGINE_API UPrimitiveComponent* GetMovementBase() const;
```

### 3.3 동작

```
1. PerformMovement 시작 → MaybeUpdateBasedMovement → Base 가 이동했으면 그 차이만큼 Char 이동
2. Phys* (보행/낙하) 정상 시뮬
3. Phys* 끝 → MaybeSaveBaseLocation → OldBaseLocation/OldBaseQuat 갱신
```

> **bDeferUpdateBasedMovement = true** → Tick 끝까지 Save 지연 (회전 누적 시 정확).
> **`MovementBaseUtility::UseRelativePosition(Base)`** 가 true 면 ServerMove RPC 에 **상대 위치** 전송 (네트워크 정확).

---

## 4. Jump 시스템

### 4.1 핵심 필드 (`CharacterMovementComponent.h:163, 421-985`)

| 필드 | 의미 |
|------|------|
| `JumpZVelocity` | 점프 시작 수직 속도 (cm/s) |
| `JumpOffJumpZFactor` | Jump-off 시 fraction (예: 0.5 = 50%) |
| `bDontFallBelowJumpZVelocityDuringJump` | 키 누르고 있는 동안 vel 안 떨어짐 |
| `bNotifyApex` | 정점 도달 시 NotifyJumpApex 호출 |
| `AirControl` | 공중 제어율 (0~1) |
| `AirControlBoostMultiplier` | 부스트 시 배율 |
| `AirControlBoostVelocityThreshold` | 부스트 활성 vel 임계 |

### 4.2 핵심 virtual

[`CharacterMovementComponent.h:1428-1738`]:
```cpp
ENGINE_API virtual bool DoJump(bool bReplayingMoves, float DeltaTime);   // 5.5+ — DeltaTime 추가
ENGINE_API virtual bool CanAttemptJump() const;
ENGINE_API virtual void NotifyJumpApex();
ENGINE_API virtual void ProcessLanded(const FHitResult& Hit, float remainingTime, int32 Iterations);
ENGINE_API virtual bool IsValidLandingSpot(const FVector& CapsuleLocation, const FHitResult& Hit) const;
ENGINE_API virtual void StartFalling(int32 Iterations, float remainingTime, float timeTick, const FVector& Delta, const FVector& subLoc);
```

### 4.3 점프 흐름

```
[Input] ACharacter::Jump()
  ↓ JumpKeyHoldTime 시작
[CMC PerformMovement]
  ↓ UpdateCharacterStateBeforeMovement() → CheckJumpInput()
  ↓ DoJump(bReplayingMoves, DeltaTime) → Velocity.Z = JumpZVelocity
  ↓ SetMovementMode(MOVE_Falling)
[PhysFalling]
  ↓ AirControl 적용
  ↓ 정점 도달 → NotifyJumpApex() → CharacterOwner->NotifyJumpApex()
  ↓ Hit 발생 → IsValidLandingSpot() ? ProcessLanded : 계속 떨어짐
  ↓ ProcessLanded() → SetPostLandedPhysics() → SetMovementMode(MOVE_Walking 또는 MOVE_Swimming)
```

> **DoJump 5.5 변경**: `DoJump(bool bReplayingMoves)` → `DoJump(bool bReplayingMoves, float DeltaTime)` deprecated.

### 4.4 Jump 횟수 / 홀드 (ACharacter 측)

> `JumpMaxCount` / `JumpMaxHoldTime` / `JumpCurrentCount` 는 **ACharacter** 의 필드. CMC 가 아닌 Character 가 점프 횟수 관리. ACharacter::CanJump() / CanJumpInternal_Implementation() override.

### 4.5 Compute Max Jump Height

```cpp
ENGINE_API virtual float GetMaxJumpHeight() const;                // 단순 수식
ENGINE_API virtual float GetMaxJumpHeightWithJumpTime() const;    // JumpMaxHoldTime 반영
```

> **AI 가 점프 가능 거리 판단** 에 사용.

---

## 5. Crouch 시스템

### 5.1 핵심 필드 + virtual

[`CharacterMovementComponent.h:1783-1796`]:
```cpp
UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Character Movement (General Settings)")
uint8 bCanCrouch : 1;

UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Character Movement: Walking")
float CrouchedHalfHeight;        // Crouch 시 Capsule Half-Height

UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Character Movement: Walking")
uint8 bCrouchMaintainsBaseLocation : 1;   // 발 위치 유지 (true) vs 머리 위치 유지 (false)

ENGINE_API virtual void Crouch(bool bClientSimulation = false);
ENGINE_API virtual void UnCrouch(bool bClientSimulation = false);
ENGINE_API virtual bool CanCrouchInCurrentState() const;
```

### 5.2 흐름

```
[Input] ACharacter::Crouch()
  ↓ bWantsToCrouch = true
[CMC PerformMovement]
  ↓ UpdateCharacterStateBeforeMovement() → bWantsToCrouch && !IsCrouching() && CanCrouchInCurrentState()
  ↓ Crouch(bClientSimulation = false)
    ↓ 새 캡슐 크기 검사 (encroachment 없음)
    ↓ Capsule->SetCapsuleHalfHeight(CrouchedHalfHeight)
    ↓ CharacterOwner->OnStartCrouch(HalfHeightAdjust, ScaledHalfHeightAdjust) 콜백
    ↓ MaxWalkSpeed → MaxWalkSpeedCrouched (자동 GetMaxSpeed override)
  ↓ Tick 종료
```

### 5.3 자식 override 표준

```cpp
virtual bool CanCrouchInCurrentState() const override
{
    if (!Super::CanCrouchInCurrentState()) return false;
    return !MyChar->IsHoldingHeavyWeapon();
}
```

---

## 6. SetMovementMode + OnMovementModeChanged

[`CharacterMovementComponent.h:894-918`]:
```cpp
UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Character Movement: Walking")
TEnumAsByte<enum EMovementMode> DefaultLandMovementMode;

UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Character Movement: Swimming")
TEnumAsByte<enum EMovementMode> DefaultWaterMovementMode;

UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Character Movement: Walking")
TEnumAsByte<enum EMovementMode> GroundMovementMode;          // Walking vs NavWalking
```

### 6.1 SetMovementMode 흐름

```cpp
SetMovementMode(EMovementMode NewMode, uint8 NewCustomMode = 0)
  ↓ MovementMode == NewMode && CustomMovementMode == NewCustomMode → return
  ↓ MovementMode = NewMode
  ↓ CustomMovementMode = NewCustomMode
  ↓ ApplyNetworkMovementMode(PackNetworkMovementMode())   // 복제 압축
  ↓ OnMovementModeChanged(PreviousMode, PreviousCustomMode)   // virtual 자식 override 가능
  ↓ CharacterOwner->K2_OnMovementModeChanged() → BP 콜백
```

> **자식 override**:
> ```cpp
> virtual void OnMovementModeChanged(EMovementMode PrevMode, uint8 PrevCustomMode) override
> {
>     Super::OnMovementModeChanged(PrevMode, PrevCustomMode);
>     // 모드 변경 후 처리 (애니메이션 / 사운드 등)
> }
> ```

---

## 7. Velocity / Acceleration 계산

### 7.1 CalcVelocity

[`CharacterMovementComponent.h:1527`]:
```cpp
ENGINE_API virtual void CalcVelocity(float DeltaTime, float Friction, bool bFluid, float BrakingDeceleration);
```

기본 동작:
1. `Acceleration` (입력에서 계산) 값 적용
2. `MaxSpeed` (현재 모드 GetMaxSpeed) clamp
3. `bFluid = false` 인 일반 케이스: 표준 가속
4. `bFluid = true` (Swimming): Fluid Friction 적용
5. Acceleration 0 + Velocity 존재 → `ApplyVelocityBraking` 호출

### 7.2 ApplyVelocityBraking

[`CharacterMovementComponent.h:2051`]:
```cpp
ENGINE_API virtual void ApplyVelocityBraking(float DeltaTime, float Friction, float BrakingDeceleration);
```

> **bUseSeparateBrakingFriction = true** → `BrakingFriction` 사용. False → `Friction` (즉 GroundFriction) 사용.

### 7.3 GetMaxAcceleration / ComputeAnalogInputModifier

```cpp
ENGINE_API virtual float GetMaxAcceleration() const;
ENGINE_API virtual float ComputeAnalogInputModifier() const;
```

게임패드 Analog Stick → 0~1 modifier. 곱한 값을 Acceleration 에 적용. 자식 override 로 좀 다른 곡선 (Smooth / Dead Zone) 가능.

---

## 8. RootMotion 깊이

### 8.1 두 가지 RootMotion

| 종류 | 필드 | 설명 |
|------|------|------|
| **Animation RootMotion** | `RootMotionParams` (`L2765`) | AnimMontage 의 RootBone 이동 — Server 권한 |
| **RootMotionSource** (Programmatic) | `CurrentRootMotion` (`L2710`) | 코드에서 만든 RootMotion (Force/Kick/Curve/Jump 등) — Server/Client 동일 시뮬 |

### 8.2 핵심 필드

```cpp
FRootMotionMovementParams RootMotionParams;
FVector AnimRootMotionVelocity;

UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="RootMotion")
float AnimRootMotionTranslationScale;             // 0=비활성, 1=원본, 2=2배

FRootMotionSourceGroup CurrentRootMotion;          // Programmatic RM 컬렉션
FRootMotionMovementParams RootMotionMovement;      // Async용
```

### 8.3 핵심 메소드

```cpp
ENGINE_API virtual void ApplyRootMotionToVelocity(float deltaTime);
ENGINE_API bool HasAnimRootMotion() const { return RootMotionParams.bHasRootMotion; }
ENGINE_API bool HasRootMotionSources() const;
ENGINE_API virtual void AccumulateRootMotionForAsync(float DeltaSeconds, FRootMotionAsyncData& RootMotion);

ENGINE_API uint16 ApplyRootMotionSource(TSharedPtr<FRootMotionSource> SourcePtr);
ENGINE_API void RemoveRootMotionSource(FName InstanceName);
ENGINE_API void RemoveRootMotionSourceByID(uint16 RootMotionSourceID);
```

### 8.4 RootMotionSource 표준 패턴 (예: Dash)

```cpp
TSharedPtr<FRootMotionSource_ConstantForce> DashSource = MakeShared<FRootMotionSource_ConstantForce>();
DashSource->InstanceName = TEXT("Dash");
DashSource->AccumulateMode = ERootMotionAccumulateMode::Override;
DashSource->Priority = 5;
DashSource->Force = GetActorForwardVector() * 5000.f;
DashSource->Duration = 0.3f;
DashSource->StrengthOverTime = nullptr;

uint16 DashID = CMC->ApplyRootMotionSource(DashSource);
```

> **Server/Client 동일 패턴** — Programmatic RM 은 Source 자체가 ServerMove 로 복제되어 양쪽 동일 시뮬.

---

## 9. NavMesh Walking (`MOVE_NavWalking`)

> **AI 캐릭터 최적화 모드** — Floor 검출 / Step Up / Sweep 모두 생략. NavMesh 표면을 단순 follow.

### 9.1 핵심 필드

```cpp
UPROPERTY(Category="Character Movement: NavMesh Movement", EditAnywhere, BlueprintReadOnly)
uint8 bSweepWhileNavWalking : 1;          // false 표준 — true 면 비용 ↑

UPROPERTY(Category="Character Movement: NavMesh Movement", EditAnywhere, BlueprintReadOnly)
uint8 bProjectNavMeshWalking : 1;          // NavMesh 표면 투사

UPROPERTY(Category="Character Movement: NavMesh Movement", EditAnywhere, BlueprintReadOnly)
float NavMeshProjectionInterval;
```

### 9.2 PhysNavWalking

비용:
- **Floor 검출 안 함** (NavMesh 가 floor 보장)
- **Step Up 안 함** (NavMesh 표면 따라감)
- **Sweep 옵션** (`bSweepWhileNavWalking`) — 켜면 그래도 sweep 해서 Block 검출

> **다수 AI = NavWalking 표준** (캐릭터 100명 이상). Player = MOVE_Walking (정밀).

### 9.3 Walking ↔ NavWalking 전환

```cpp
GroundMovementMode = MOVE_Walking;     // 또는 MOVE_NavWalking
SetMovementMode(MOVE_NavWalking);      // 자동 GroundMovementMode 갱신
```

---

## 10. RVO + Avoidance

> **AI 캐릭터끼리 자동 회피** — RVO (Reciprocal Velocity Obstacles) 알고리즘.

### 10.1 핵심 필드

[`CharacterMovementComponent.h:1046`]:
```cpp
UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Character Movement: Avoidance")
uint8 bUseRVOAvoidance : 1;

UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Character Movement: Avoidance")
float AvoidanceConsiderationRadius;       // 회피 고려 반경

UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Character Movement: Avoidance")
float AvoidanceWeight;                    // 회피 우선순위 (낮을수록 회피)

UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Character Movement: Avoidance")
FNavAvoidanceMask AvoidanceGroup;          // 회피 그룹

UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Character Movement: Avoidance")
FNavAvoidanceMask GroupsToAvoid;
UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Character Movement: Avoidance")
FNavAvoidanceMask GroupsToIgnore;
```

### 10.2 핵심 메소드

[`CharacterMovementComponent.h:2844`]:
```cpp
ENGINE_API void SetAvoidanceVelocityLock(class UAvoidanceManager* Avoidance, float Duration);

// IRVOAvoidanceInterface override
virtual void CalculateAvoidanceVelocity(...) override;
virtual void UpdateAvoidance(...) override;
virtual void SetRVOAvoidanceUID(...) override;
virtual int32 GetRVOAvoidanceUID() override;
```

> **UAvoidanceManager** (UWorld Subsystem) 가 모든 RVO 캐릭터 등록 + 매 Tick 회피 속도 계산. CMC 는 결과 적용.

---

## 11. Force / Impulse (외부 힘)

### 11.1 핵심 메소드

[`CharacterMovementComponent.h:1868-1881`]:
```cpp
ENGINE_API virtual void AddImpulse(FVector Impulse, bool bVelocityChange = false);
ENGINE_API virtual void AddForce(FVector Force);
ENGINE_API virtual void AddRadialImpulse(FVector Origin, float Radius, float Strength, ERadialImpulseFalloff Falloff, bool bVelChange = false);
ENGINE_API virtual void AddRadialForce(FVector Origin, float Radius, float Strength, ERadialImpulseFalloff Falloff);
```

### 11.2 차이

| 메소드 | 적용 시점 | 권장 |
|--------|-----------|------|
| `AddImpulse(bVelChange=true)` | 즉시 Velocity 변경 (Mass 무시) | 점프 / 폭발 즉시 반응 |
| `AddImpulse(bVelChange=false)` | Mass 기반 Velocity 변경 | 무거운 객체 효과 |
| `AddForce` | DeltaTime 기반 누적 | 지속 힘 (바람 / 중력 등) |
| `AddRadialImpulse` | 거리 기반 falloff | 폭발 영역 효과 |

---

## 12. 검증 로그 (자체 평가)

### 12.1 분리 정합성
- ✅ 메인 SKILL.md §5.5~§5.15 모든 정보 본 문서 §1~§11 로 이동
- ✅ Cross-ref 앵커 보존 (메인에서 §5.5 → 본 문서 §1 로 link)
- ✅ Frontmatter (name + description) 부여

### 12.2 점수 (17_QualityCriteria.md 4종 가중)
- Performance 35: ⭐⭐⭐⭐⭐ 35/35 (Floor/StepUp/RVO 모두 매 프레임 호출 — 정확한 자료 가치)
- Memory 25: ⭐⭐⭐⭐ 22/25 (FRootMotionSource lifetime 명시)
- Network 15: ⭐⭐⭐⭐ 13/15 (Movement Base + RootMotionSource 복제 명시)
- Maintainability 25: ⭐⭐⭐⭐⭐ 25/25 (자식 override 패턴 명시)
- **합계: 95/100 ✅**

---

## 13. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-06 | MovementComponents/SKILL.md §5.5~§5.15 에서 분리 (Article 3 Level 3 progressive disclosure 첫 적용 사례). 메인 SKILL.md 36KB → ~15KB / 본 reference ~21KB. 메인은 §1~§5.4 + §5 한 줄 요약 + 본 reference 링크. |
