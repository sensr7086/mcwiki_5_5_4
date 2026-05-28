---
name: animation-rootmotion
description: RootMotion + IAnimRootMotionProvider (5.x) + FRootMotionSource 7종 + CharacterMovement 통합. AnimMontage RootMotion 모드 4종 + bEnableRootMotionMontagesOnly 페어 설정 + RootLock 모드 + 멀티플레이 RootMotion 동기화. 어택 이동 / Roll / Cinematic 표준.
---

# Animation/RootMotion — Montage RootMotion + RootMotionSource + 5.x Provider

> **위치**: `Engine/Source/Runtime/Engine/Public/Animation/AnimRootMotionProvider.h` + `Classes/Animation/AnimMontage.h` + `Classes/GameFramework/RootMotionSource.h`
> **요지**: 애니메이션의 본 이동을 캐릭터 이동에 적용 — Montage 측 활성 + CMC 측 활성 **페어 의무**. 5.x 신규 = `IAnimRootMotionProvider` 추상화.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 페어 활성 의무 | Montage `bEnableRootMotionTranslation/Rotation = true` + CMC `bEnableRootMotionMontagesOnly = true` |
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | `OnAnimationRootMotionExtracted` 첫 줄 프로파일링 스코프 |
| 🚨 멀티플레이 | `Replicates = true` Pawn → 서버에서 RootMotion 자동 동기 (신뢰 — 클라 예측) |

---

## 1. RootMotion 두 시스템

| 시스템 | 위치 | 사용 |
|--------|------|------|
| **AnimMontage RootMotion** | UAnimMontage 자체 | Anim 자산이 직접 이동 정의 (어택, Roll) |
| **FRootMotionSource** | CharacterMovementComponent | 코드 측 동적 — Jump Force, Constant Force, Move To 등 7종 |
| **IAnimRootMotionProvider (5.x)** | 추상 인터페이스 | 두 시스템 통합 — Custom Provider 가능 |

---

## 2. AnimMontage RootMotion (자산 측)

### 2.1 활성

```cpp
// AnimMontage 자산 안 (Editor)
Montage->bEnableRootMotionTranslation = true;
Montage->bEnableRootMotionRotation = true;
Montage->RootMotionRootLock = ERootMotionRootLock::AnimFirstFrame;
```

### 2.2 ERootMotionRootLock 4종

| Mode | 의미 | 사용 |
|------|------|------|
| `RefPose` | Skeleton Ref Pose Lock | 일반적 |
| `AnimFirstFrame` | 자산 첫 프레임 Lock | ⭐ 자주 사용 |
| `Zero` | Origin Lock | 정적 모션 |
| `AnimLockedToCurrentTransform` | 현재 변환 Lock | Cinematic |

### 2.3 CMC 측 페어 (의무)

```cpp
// 캐릭터 BP 또는 코드 — CMC 활성
GetCharacterMovement()->bEnableRootMotionMontagesOnly = true;
```

> **이거 누락 시 — RootMotion Montage 가 작동 안 함**.

---

## 3. FRootMotionSource (코드 측 동적 — 7종)

### 3.1 종류

```cpp
// Engine/Public/GameFramework/RootMotionSource.h
struct FRootMotionSource_ConstantForce      // 일정 힘 (예: 폭발 밀어내기)
struct FRootMotionSource_RadialForce        // 원형 힘 (예: 중심 근처 끌어당기기)
struct FRootMotionSource_MoveToForce        // 특정 위치까지 이동 (예: 그래플링)
struct FRootMotionSource_MoveToDynamicForce // 동적 타깃 (타깃 이동 추적)
struct FRootMotionSource_JumpForce          // Jump Force (Path 따라 이동)
```

### 3.2 사용 패턴 — Grappling Hook

```cpp
void AMyChar::DoGrapple(FVector TargetLoc)
{
    auto* CMC = GetCharacterMovement();
    if (!CMC) return;

    TSharedPtr<FRootMotionSource_MoveToForce> Source = MakeShared<FRootMotionSource_MoveToForce>();
    Source->InstanceName = TEXT("Grapple");
    Source->AccumulateMode = ERootMotionAccumulateMode::Override;
    Source->Settings.SetFlag(ERootMotionSourceSettingsFlags::UseSensitiveLiftoffCheck);
    Source->Priority = 5;
    Source->StartLocation = GetActorLocation();
    Source->TargetLocation = TargetLoc;
    Source->Duration = 0.5f;

    uint16 ID = CMC->ApplyRootMotionSource(Source);
}

// 정지
void AMyChar::CancelGrapple()
{
    auto* CMC = GetCharacterMovement();
    CMC->RemoveRootMotionSourceByName(TEXT("Grapple"));
}
```

### 3.3 ERootMotionAccumulateMode 2종

| Mode | 의미 |
|------|------|
| `Additive` | 다른 RootMotion 과 합쳐 |
| `Override` | 다른 RootMotion 무시 (이것만 적용) |

---

## 4. IAnimRootMotionProvider (5.x 추상 인터페이스)

### 4.1 정의

다른 5.x 시스템 (Pose Search, Motion Matching) 이 RootMotion 통합 시 사용. 일반 게임에선 거의 안 쓰지만 — 인지하고 있어야.

```cpp
// Engine/Public/Animation/AnimRootMotionProvider.h
class IAnimRootMotionProvider
{
    virtual void ExtractRootMotion(...) = 0;
    virtual bool HasRootMotion(...) = 0;
};
```

---

## 5. 멀티플레이 RootMotion

### 5.1 동기 방식

| Replication 모드 | RootMotion |
|-----------------|-----------|
| Server Authority (`Replicates = true`) | 서버가 모션 시뮬 → 클라 보정 |
| Client Prediction | 클라 예측 → 서버 검증 |

### 5.2 패턴 — Replicated Montage

```cpp
// Server 측에서 실행 — 자동 복제
if (HasAuthority())
{
    GetMesh()->GetAnimInstance()->Montage_Play(AttackMontage);
    // 서버가 RootMotion 시뮬 → 클라 자동 동기
}

// 또는 Replicated Montage (Multicast)
UFUNCTION(NetMulticast, Reliable)
void Multicast_PlayMontage(UAnimMontage* M);
```

### 5.3 함정

- **클라이언트 RootMotion 예측 부정확** — `bEnableServerAuthRotationCheck = true` 의무 (CMC)
- **Listen Server 호스트와 클라이언트 RootMotion 어긋남** — `bRunPhysicsWithNoController = true` 검토

---

## 6. 표준 패턴 — Roll Dodge

```cpp
// 1. AnimMontage 자산 — RollMontage (RootMotion 활성, AnimFirstFrame Lock)

// 2. CMC 측 페어 (Constructor)
ACharacter::ACharacter()
{
    GetCharacterMovement()->bEnableRootMotionMontagesOnly = true;
}

// 3. Roll 입력
void AMyChar::DoRoll()
{
    if (!IsValid(RollMontage)) return;

    auto* AnimInst = GetMesh()->GetAnimInstance();
    if (AnimInst && !AnimInst->Montage_IsPlaying(RollMontage))
    {
        AnimInst->Montage_Play(RollMontage);

        FOnMontageEnded EndedDelegate;
        EndedDelegate.BindUObject(this, &AMyChar::OnRollEnded);
        AnimInst->Montage_SetEndDelegate(EndedDelegate, RollMontage);
    }
}

// 4. 완료 콜백
void AMyChar::OnRollEnded(UAnimMontage* M, bool bInterrupted)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(AMyChar::OnRollEnded);
    if (M == RollMontage)
    {
        // 무적 시간 해제 등
    }
}
```

---

## 7. 함정 & 안티패턴 (8대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Montage RootMotion 활성 + CMC `bEnableRootMotionMontagesOnly = false` | CMC 측 `true` 의무 |
| 2 | RootMotion + 직접 `SetActorLocation` 동시 호출 (충돌) | RootMotion 활성 시 SetActorLocation 회피 |
| 3 | RootLock = `RefPose` (정적 모션 — 시작 위치 어색) | `AnimFirstFrame` 권장 |
| 4 | RootMotionSource 의 InstanceName 누락 (Cancel 불가) | 모든 Source = InstanceName 의무 |
| 5 | Multicast Montage_Play (서버 제외) | Server Auth → 자동 복제 OR `Replicates = true` |
| 6 | 클라 예측 부정확 — 서버와 어긋남 | `bClientAuthorityHandlesEffects = true` (5.x) |
| 7 | RootMotion + Listen Server 캐릭터 RootMotion 어긋남 | `bRunPhysicsWithNoController = true` 검토 |
| 8 | EndedDelegate 누락 — 무적 해제 안 됨 | `Montage_SetEndDelegate` 의무 |

---

## 8. 체크리스트

- [ ] Montage RootMotion 활성 + CMC `bEnableRootMotionMontagesOnly = true` 페어
- [ ] RootLock = `AnimFirstFrame` 권장
- [ ] RootMotionSource = InstanceName 의무 (Cancel 가능)
- [ ] 멀티플레이 = Server Auth + 자동 복제
- [ ] EndedDelegate 바인딩 (무적 해제 / 상태 정리)
- [ ] Roll / Dodge / Grapple = RootMotion 표준
- [ ] 5.x = IAnimRootMotionProvider 인지

---

## 9. 관련

- [`Animation/SKILL.md`](../SKILL.md) — 메인
- [`Animation/references/AnimInstance.md`](../AnimInstance/SKILL.md) — Montage_Play / EndedDelegate
- [`Components/references/MovementComponents.md`](../../Components/references/MovementComponents.md) §5.12 — CMC RootMotion 깊이
- [`AssetClasses/references/Animation.md`](../../AssetClasses/references/Animation.md) §3.5 — Montage RootMotion 자산 측
- [`GameFramework/references/PawnCharacter.md`](../../GameFramework/references/PawnCharacter.md) — Character Replication

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-07 | 최초 작성. Montage RootMotion + FRootMotionSource 7종 + IAnimRootMotionProvider (5.x) + ERootMotionRootLock 4종 + 멀티플레이 + 함정 8대. |
