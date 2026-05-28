---
name: animation-animinstance
description: UAnimInstance (1,776 lines) 라이프사이클 + FAnimInstanceProxy (worker 스레드) + Curve API + Montage_* 시리즈. NativeInitializeAnimation/NativeBeginPlay/NativeUpdateAnimation/NativeThreadSafeUpdateAnimation/NativeUninitializeAnimation 5단계 + Super 호출 규약 + 게임/워커 스레드 분리 표준.
---

# Animation/AnimInstance — UAnimInstance 라이프사이클 + Proxy + Curve + Montage

> **위치**: `Engine/Source/Runtime/Engine/Public/Animation/AnimInstance.h` (1,776) + `AnimInstanceProxy.h`
> **베이스**: `UAnimInstance : public UObject` (Outer = SkeletalMeshComponent)
> **요지**: AnimBP 컴파일 결과 클래스의 베이스 — **게임 스레드 (NativeUpdate) ↔ 워커 스레드 (FAnimInstanceProxy + NativeThreadSafe)** 두 축 분리가 핵심.

---

## 🚨 공통 정책 (자동 적용)

| 정책 | 적용 |
|------|------|
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | NativeInitialize / NativeBeginPlay / NativeUpdate / NativeThreadSafeUpdate / NativeUninitialize 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 |
| 🚨 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) | `TObjectPtr<UAnimInstance>` (UPROPERTY) / Owner 캐싱 = `TWeakObjectPtr<ACharacter>` 또는 값 복사 |
| 🚨 [`04_OverrideIndex.md`](../../../references/04_OverrideIndex.md) §6 | Super 호출 규약 — Initialize/BeginPlay/Update = Super FIRST, Uninitialize = Super LAST |

---

## 1. 라이프사이클 5단계 + Super 호출 규약

```cpp
// 1. NativeInitializeAnimation — Owner 캐싱 등 (1회)
virtual void NativeInitializeAnimation() override
{
    Super::NativeInitializeAnimation();  // ⭐ FIRST
    TRACE_CPUPROFILER_EVENT_SCOPE(NativeInitializeAnimation);
    CachedOwner = Cast<ACharacter>(TryGetPawnOwner());
}

// 2. NativeBeginPlay — Owner BeginPlay 후 (1회)
virtual void NativeBeginPlay() override
{
    Super::NativeBeginPlay();            // ⭐ FIRST
    TRACE_CPUPROFILER_EVENT_SCOPE(NativeBeginPlay);
}

// 3. NativeUpdateAnimation — 매 프레임 (게임 스레드)
virtual void NativeUpdateAnimation(float DT) override
{
    Super::NativeUpdateAnimation(DT);    // ⭐ FIRST
    TRACE_CPUPROFILER_EVENT_SCOPE(NativeUpdateAnimation);
    // 게임 스레드 — Owner 접근 OK / 워커 데이터 캐싱
}

// 4. NativeThreadSafeUpdateAnimation — 매 프레임 (워커 스레드, 병렬) ⭐ 권장
virtual void NativeThreadSafeUpdateAnimation(float DT) override
{
    Super::NativeThreadSafeUpdateAnimation(DT);  // ⭐ FIRST
    TRACE_CPUPROFILER_EVENT_SCOPE(NativeThreadSafe);
    // 워커 스레드 — Owner / Component 직접 접근 X / 캐싱 값만
}

// 5. NativeUninitializeAnimation — 종료
virtual void NativeUninitializeAnimation() override
{
    TRACE_CPUPROFILER_EVENT_SCOPE(NativeUninitialize);
    // 정리 작업 먼저
    CachedOwner = nullptr;
    Super::NativeUninitializeAnimation();  // ⭐ LAST
}
```

---

## 2. NativeUpdate vs NativeThreadSafe (5.x 핵심 분리)

| 측면 | `NativeUpdateAnimation` | `NativeThreadSafeUpdateAnimation` |
|------|------------------------|-----------------------------------|
| 스레드 | 게임 스레드 | 워커 스레드 (병렬) ⭐ |
| Owner 접근 | OK (`TryGetPawnOwner`) | ❌ 금지 |
| Component 접근 | OK | ❌ 금지 |
| World 접근 | OK | ❌ 금지 |
| BlueprintReadOnly UPROPERTY 쓰기 | OK | OK (자기 객체) |
| 무거운 계산 | ❌ 권장 X | ✅ ⭐ 권장 |
| `Super` 호출 | FIRST | FIRST |

### 표준 분리 패턴

```cpp
// 게임 스레드 — Owner 접근 + 캐싱
void UMyAnimInstance::NativeUpdateAnimation(float DT)
{
    Super::NativeUpdateAnimation(DT);
    TRACE_CPUPROFILER_EVENT_SCOPE(GameThread_Cache);

    if (auto* C = CachedOwner.Get())
    {
        CachedSpeed = C->GetVelocity().Size();
        CachedDirection = ComputeDirection(C);
        bCachedCrouched = C->bIsCrouched;
        bCachedFalling = C->GetCharacterMovement()->IsFalling();
    }
}

// 워커 스레드 — 캐싱된 값으로 무거운 계산 (병렬, 빠름)
void UMyAnimInstance::NativeThreadSafeUpdateAnimation(float DT)
{
    Super::NativeThreadSafeUpdateAnimation(DT);
    TRACE_CPUPROFILER_EVENT_SCOPE(WorkerThread_Calc);

    // BlueprintReadOnly 변수 = AnimGraph 가 사용
    Speed = CachedSpeed;
    Direction = CachedDirection;
    bIsCrouched = bCachedCrouched;
    bIsFalling = bCachedFalling;

    // 무거운 계산 — 예: Lean Angle 보간
    LeanAngle = FMath::FInterpTo(LeanAngle, TargetLeanAngle, DT, 5.f);
}
```

---

## 3. FAnimInstanceProxy (워커 스레드 본체)

> AnimInstance 의 워커 스레드 측 데이터 — `Update_AnyThread` / `Evaluate_AnyThread` 가 Proxy 위에서 동작.

```cpp
// AnimInstanceProxy.h:143
struct FAnimInstanceProxy
{
    // Initialize
    ENGINE_API virtual void Initialize(UAnimInstance* InAnimInstance);

    // Update (워커 스레드) — NativeThreadSafeUpdate 후
    ENGINE_API virtual void Update(float DeltaSeconds);

    // Evaluate (워커 스레드) — Pose 평가
    ENGINE_API virtual bool Evaluate(FPoseContext& Output);

    // 종료
    ENGINE_API virtual void Uninitialize(UAnimInstance* InAnimInstance);
};
```

### Custom Proxy 작성 (드물지만 가능)

```cpp
USTRUCT()
struct FMyAnimInstanceProxy : public FAnimInstanceProxy
{
    GENERATED_BODY()

    virtual void Update(float DT) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(FMyProxy::Update);
        Super::Update(DT);
        // 워커 측 무거운 계산 — Proxy 자체 멤버 사용
    }
};

// AnimInstance 와 페어
UCLASS()
class UMyAnimInstance : public UAnimInstance
{
    GENERATED_BODY()
private:
    virtual FAnimInstanceProxy* CreateAnimInstanceProxy() override
    {
        return new FMyAnimInstanceProxy(this);
    }

    virtual void DestroyAnimInstanceProxy(FAnimInstanceProxy* Proxy) override
    {
        delete Proxy;
    }
};
```

---

## 4. Curve API

```cpp
// AnimInstance.h:1205 — Curve 값 조회
ENGINE_API float GetCurveValue(FName CurveName) const;
ENGINE_API bool GetCurveValueWithDefault(FName CurveName, float DefaultValue, float& OutValue);

// 사용 — IK Foot Lock / 발자국 Trigger / 표정 Curve
float FootLockL = AnimInstance->GetCurveValue(TEXT("FootLock_L"));
float Speech = AnimInstance->GetCurveValue(TEXT("Mouth_Open"));

// Curve 값 변화 콜백 (delegate)
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FAnimCurveChanged, FName, Name, float, Value);
```

---

## 5. Montage_* 시리즈 API

```cpp
// 재생
float Montage_Play(UAnimMontage* Montage, float PlayRate = 1.f, ...);
float Montage_PlayWithBlendIn(UAnimMontage* Montage, const FAlphaBlendArgs& BlendIn, ...);

// 정지
void Montage_Stop(float BlendOut, const UAnimMontage* Montage = nullptr);
void Montage_StopGroupByName(float BlendOut, FName GroupName);  // Slot 그룹별

// Section 점프
void Montage_JumpToSection(FName SectionName, const UAnimMontage* Montage = nullptr);
void Montage_JumpToSectionsEnd(FName SectionName, const UAnimMontage* Montage = nullptr);

// 위치 / 속도 변경
void Montage_SetPlayRate(const UAnimMontage* Montage, float PlayRate);
void Montage_SetPosition(const UAnimMontage* Montage, float Position);

// 콜백 바인딩
void Montage_SetEndDelegate(FOnMontageEnded& Delegate, const UAnimMontage* Montage);
void Montage_SetBlendingOutDelegate(FOnMontageBlendingOutStarted& Delegate, const UAnimMontage* Montage);

// 상태 조회
bool Montage_IsPlaying(const UAnimMontage* Montage) const;
FName Montage_GetCurrentSection(const UAnimMontage* Montage = nullptr) const;
float Montage_GetPlayRate(const UAnimMontage* Montage) const;
```

### Montage 표준 패턴 — Combo 어택

```cpp
void AMyChar::DoAttack()
{
    if (!IsValid(AttackMontage)) return;

    auto* AnimInst = GetMesh()->GetAnimInstance();
    if (!AnimInst) return;

    // 1. 재생
    AnimInst->Montage_Play(AttackMontage, 1.f);

    // 2. 완료 콜백 바인딩
    FOnMontageEnded EndedDelegate;
    EndedDelegate.BindUObject(this, &AMyChar::OnAttackEnded);
    AnimInst->Montage_SetEndDelegate(EndedDelegate, AttackMontage);
}

// 3. 콤보 입력 — Section 점프
void AMyChar::OnAttackInput()
{
    auto* AnimInst = GetMesh()->GetAnimInstance();
    if (AnimInst && AnimInst->Montage_IsPlaying(AttackMontage))
    {
        FName Current = AnimInst->Montage_GetCurrentSection(AttackMontage);
        if (Current == TEXT("Attack1"))
        {
            AnimInst->Montage_JumpToSection(TEXT("Attack2"), AttackMontage);
        }
        else if (Current == TEXT("Attack2"))
        {
            AnimInst->Montage_JumpToSection(TEXT("Attack3"), AttackMontage);
        }
    }
}
```

---

## 6. AnimNotify 호출 흐름 (간략 — 자세한 = AnimNotify sub-skill)

```cpp
// AnimNotify 가 트리거되면 AnimInstance 가 자동 호출
// 흐름: NativeUpdate → Notify Queue 적재 → 게임 스레드 콜백
virtual void NativeNotifyBeginPlay();  // (별도 콜백 — 일반적으로 사용 X)
```

---

## 7. 표준 자식 클래스 패턴 (체크리스트 적용)

```cpp
// MyAnimInstance.h
UCLASS(Transient, Blueprintable)
class UMyAnimInstance : public UAnimInstance
{
    GENERATED_BODY()
public:
    virtual void NativeInitializeAnimation() override;
    virtual void NativeBeginPlay() override;
    virtual void NativeUpdateAnimation(float DT) override;
    virtual void NativeThreadSafeUpdateAnimation(float DT) override;
    virtual void NativeUninitializeAnimation() override;

    // BlueprintReadOnly — AnimGraph 가 읽음 (워커 스레드 기록)
    UPROPERTY(BlueprintReadOnly, Category="Anim")
    float Speed = 0.f;

    UPROPERTY(BlueprintReadOnly, Category="Anim")
    float Direction = 0.f;

    UPROPERTY(BlueprintReadOnly, Category="Anim")
    bool bIsCrouched = false;

    UPROPERTY(BlueprintReadOnly, Category="Anim")
    bool bIsFalling = false;

private:
    // 게임 스레드 캐싱 → 워커 스레드 사용
    TWeakObjectPtr<ACharacter> CachedOwner;
    float CachedSpeed = 0.f;
    float CachedDirection = 0.f;
    bool bCachedCrouched = false;
    bool bCachedFalling = false;
};
```

---

## 8. 함정 & 안티패턴 (8대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | `NativeUpdate` 안 무거운 계산 | `NativeThreadSafeUpdate` 분리 |
| 2 | `NativeThreadSafeUpdate` 안 Owner / Component 직접 접근 | NativeUpdate 에 캐싱, 워커는 캐싱 값만 |
| 3 | Initialize / BeginPlay / Update Super 누락 | Super FIRST 의무 |
| 4 | Uninitialize Super 첫 줄 호출 | Super LAST 의무 |
| 5 | Owner = `UPROPERTY() ACharacter*` (강한 참조 — GC 문제) | `TWeakObjectPtr<ACharacter>` 사용 |
| 6 | Montage_Play 후 EndedDelegate 누락 | `Montage_SetEndDelegate` 의무 |
| 7 | NativeInit 안 무거운 자산 로드 | Soft + Match Start PreLoad ([`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md)) |
| 8 | 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 |

---

## 9. 체크리스트

- [ ] 5개 Native* 콜백 = Super FIRST (Uninit = LAST) + 첫 줄 프로파일링 스코프
- [ ] NativeUpdate (게임 스레드) = Owner 캐싱 / NativeThreadSafe (워커) = 계산
- [ ] Owner 참조 = `TWeakObjectPtr` 또는 값 복사
- [ ] Montage_Play 시 EndedDelegate 바인딩 (완료 처리 시)
- [ ] BlueprintReadOnly UPROPERTY = AnimGraph 가 읽는 변수
- [ ] AnimBP / Montage 자주 쓰면 Match Start PreLoad

---

## 10. 관련

- [`Animation/SKILL.md`](../SKILL.md) — 메인 인덱스
- [`Animation/references/AnimGraph.md`](../AnimGraph/SKILL.md) — Custom AnimNode (`Update_AnyThread` / `Evaluate_AnyThread`)
- [`Animation/references/AnimNotify.md`](../AnimNotify/SKILL.md) — Notify / NotifyState
- [`AssetClasses/references/Animation.md`](../../AssetClasses/references/Animation.md) — 자산 페어
- [`Components/references/MeshComponents.md`](../../Components/references/MeshComponents.md) — SkeletalMeshComponent (호스트)

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-07 | 최초 작성. 라이프사이클 5단계 + Super 규약 + NativeUpdate vs NativeThreadSafe + FAnimInstanceProxy + Curve + Montage_* + 함정 8대. |
