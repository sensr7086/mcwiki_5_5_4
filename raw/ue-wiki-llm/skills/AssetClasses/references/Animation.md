---
name: assetclasses-animation
description: UAnimSequence (1,001) + UAnimMontage (996) + UBlendSpace (966) + UAnimBlueprint (299) + UAnimInstance (1,776) - 5.x NativeThreadSafeUpdateAnimation + Curve API + Montage_*.
---

# AssetClasses/Animation — UAnimSequence + UAnimMontage + UBlendSpace + UAnimBlueprint + UAnimInstance

> **위치**: `Engine/Source/Runtime/Engine/Classes/Animation/`
> **파일**: `AnimSequence.h` (1,001) + `AnimSequenceBase.h` (319) + `AnimMontage.h` (996) + `BlendSpace.h` (966) + `AnimBlueprint.h` (299) + `AnimInstance.h` (1,776) + Skeleton (이미 [`AssetClasses/Mesh §3`](../Mesh/SKILL.md))
> **베이스**: `UAnimationAsset : public UObject` → `UAnimSequenceBase` → `UAnimSequence` / `UAnimComposite` / `UAnimMontage` / `UAnimStreamable` (별도 = `UBlendSpace : public UAnimationAsset`)
> **요지**: **모든 SkeletalMesh 의 애니메이션 데이터** — 컴포넌트 (SkeletalMeshComponent) ↔ AnimInstance 페어. **Compression / Streaming / Curve / Notify / RootMotion** 5대 영역.

---

## 🚨 공통 정책

| 정책 | Animation 자산 적용 |
|------|--------------------|
| 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) | AnimSequence / AnimMontage = **메모리 큼** (긴 애니 = 1MB~10MB). **TSoftObjectPtr<UAnimSequenceBase>` + UAssetManager Primary Asset / Bundle 표준**. AnimBlueprint = BP 컴파일 비용 — Cooked 빌드 첫 컴파일 50~200ms. **Skeleton 호환 검사 의무**. |
| 🚨 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) | AnimInstance 멤버 = `UPROPERTY()` + `TObjectPtr<UAnimInstance>` (자동 GC). AnimMontage 인스턴스 = `FAnimMontageInstance` (struct — UPROPERTY X). |
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | NativeUpdateAnimation / Montage_Play / Notify 콜백 첫 줄 스코프. |
| 🎯 [`12_AssetOptimizationPolicy.md`](../../../references/12_AssetOptimizationPolicy.md) | **§1 SkeletalMesh Bone LOD 페어** — Animation 자산은 Skeleton 의 본 데이터를 압축 저장. **LOD 별 본 제거 시 — AnimSequence 의 RemoveTracksByBoneName** + AnimBlueprint 의 LOD Threshold 페어. **URO (Update Rate Optimization) + EVisibilityBasedAnimTickOption** 와 직접 통합 (자세한 = [`Components/MeshComponents §7`](../../Components/references/MeshComponents.md)). 다수 NPC 환경 = AnimationBudgetAllocator + Significance 통합 ([`Components/MeshComponents §7.6`](../../Components/references/MeshComponents.md)). |

---

## 1. 베이스 트리 (UAnimationAsset)

```
UObject
└── UAnimationAsset (베이스 — UAnimMontage 외 모두)
    ├── UAnimSequenceBase (319 lines — 키 기반 시퀀스)
    │   ├── UAnimSequence (1,001 lines — 가장 흔함, 일반 애니)
    │   │   └── UAnimStreamable (5.x — Streaming)
    │   ├── UAnimComposite (Section 합성 — Sequence 묶음)
    │   └── UAnimMontage (996 lines — Section + BlendIn/Out + Notify + RootMotion)
    └── UBlendSpace (966 lines — 1D / 2D / AimOffset Blend)
        ├── UBlendSpace1D
        └── UAimOffsetBlendSpace / UAimOffsetBlendSpace1D
```

```
UBlueprint
└── UAnimBlueprint (299 lines — TargetSkeleton 페어)
    ↓ 컴파일
    ├── 일반 클래스: UAnimInstance (1,776 lines)
    │   └── Native* 콜백 + Montage_Play / GetCurveValue
    └── 자식 클래스: UAnimLayerInterface (5.x)
```

---

## 2. UAnimSequence (가장 흔함 — 1,001 lines)

### 2.1 핵심 필드

```cpp
// AnimSequenceBase.h:36
class UAnimSequenceBase : public UAnimationAsset
{
    // AnimSequenceBase.h:61 — 재생 속도 배율
    UPROPERTY(EditAnywhere)
    float RateScale;
};

// AnimSequence.h:202
class UAnimSequence : public UAnimSequenceBase
{
    // AnimSequence.h:285 — Additive 종류 (베이스 위 더하기)
    UPROPERTY()
    TEnumAsByte<enum EAdditiveAnimationType> AdditiveAnimType;

    // AnimSequence.h:297 — Additive 베이스 포즈 (Ref Pose / 다른 시퀀스 / 첫 프레임)
    UPROPERTY()
    TObjectPtr<class UAnimSequence> RefPoseSeq;

    // AnimSequence.h:278 — 압축 데이터 (Cooked + DDC)
    FCompressedAnimSequence CompressedData;

    // 5.x — TargetFrameRate (Editor 전용)
    UPROPERTY()
    FPerPlatformFrameRate PlatformTargetFrameRate;
};
```

### 2.2 EAdditiveAnimationType

| Type | 의미 |
|------|------|
| `AAT_None` | 일반 (Full Pose) |
| `AAT_LocalSpaceBase` | Additive — Local Space (가장 흔함) |
| `AAT_RotationOffsetMeshSpace` | AimOffset 류 (Mesh Space Rotation) |

```cpp
// 사용 — Additive 는 베이스 위에 누적
// 예: Idle (Full) + Aim (AAT_RotationOffsetMeshSpace) = 조준하면서 Idle
```

### 2.3 GetAnimationPose (Compressed 추출)

```cpp
// AnimSequenceBase.h:185 — 시간 / 본 → Pose
virtual void GetAnimationPose(FAnimationPoseData& OutPoseData,
                               const FAnimExtractContext& ExtractionContext) const;

struct FAnimExtractContext
{
    double CurrentTime;             // 추출 시간 (초)
    bool bExtractRootMotion;        // RootMotion 포함?
    FDeltaTimeRecord DeltaTimeRecord;
};
```

### 2.4 GetPlayLength

```cpp
// AnimSequenceBase.h:86
ENGINE_API virtual float GetPlayLength() const override;
{
    // 5.0 부터 SequenceLength deprecated — GetPlayLength 사용
}
```

### 2.5 Compression (Cooked)

> **Editor** = RawAnimationData (FBoneAnimationTrack) + DDC 캐시
> **Cooked** = CompressedData (FCompressedAnimSequence) — 플랫폼별 압축

```cpp
// 압축 종류 — Project Settings > Animation > Compression
// - ACL (Animation Compression Library — 5.x 표준)
// - Bitwise / TrackOnly / Per-Track / Adaptive Error
```

### 2.6 5.x AnimDataController (Editor 전용)

```cpp
// 5.0+ — Raw 데이터 직접 접근 deprecated
// 대신 IAnimationDataController 사용
#if WITH_EDITOR
IAnimationDataController& Controller = AnimSeq->GetController();
Controller.SetPlayLength(2.0f);
Controller.SetFrameRate(FFrameRate(30, 1));
#endif
```

---

## 3. UAnimMontage (Section + Notify + RootMotion — 996 lines)

### 3.1 핵심 필드

```cpp
// AnimMontage.h:622
class UAnimMontage : public UAnimCompositeBase
{
    // AnimMontage.h:637 — BlendIn 설정
    UPROPERTY(EditAnywhere)
    FAlphaBlend BlendIn;

    // AnimMontage.h:646 — BlendOut 설정
    UPROPERTY(EditAnywhere)
    FAlphaBlend BlendOut;

    // Composite Section (Section 정의)
    UPROPERTY()
    TArray<FCompositeSection> CompositeSections;

    // Slot Animation Tracks
    UPROPERTY()
    TArray<FSlotAnimationTrack> SlotAnimTracks;

    // Notify 이벤트
    UPROPERTY()
    TArray<FAnimNotifyEvent> Notifies;

    // RootMotion 활성
    UPROPERTY(EditAnywhere)
    uint8 bEnableRootMotionTranslation : 1;
    uint8 bEnableRootMotionRotation : 1;
};
```

### 3.2 FCompositeSection (재생 단위)

```cpp
// AnimMontage.h:37
struct FCompositeSection : public FAnimLinkableElement
{
    FName SectionName;            // "Start" / "Middle" / "End"
    float LinkPos;                  // Section 시작 위치
    FName NextSectionName;          // 다음 Section 자동 전환
};

// 사용 — 멀티 단계 어택 (Combo)
// Section 1: Attack1
// Section 2: Attack2  (Attack1->NextSectionName = "Attack2")
// Section 3: Attack3
// → 입력 시 다음 Section 으로 점프
```

### 3.3 Montage_Play / Montage_Stop / JumpToSection (런타임)

```cpp
// AnimInstance.h:613
ENGINE_API float Montage_Play(UAnimMontage* MontageToPlay, float InPlayRate = 1.f, ...);

// AnimInstance.h:626
ENGINE_API void Montage_Stop(float InBlendOutTime, const UAnimMontage* Montage = NULL);

// AnimInstance.h:650 — Section 점프
ENGINE_API void Montage_JumpToSection(FName SectionName, const UAnimMontage* Montage = NULL);

// 사용
SkelMeshComp->GetAnimInstance()->Montage_Play(AttackMontage, 1.f);
SkelMeshComp->GetAnimInstance()->Montage_JumpToSection(TEXT("Attack2"));
```

### 3.4 Montage 콜백 (Delegate)

```cpp
// AnimMontage.h:188-204 — 4종 Delegate
DECLARE_DELEGATE_TwoParams(FOnMontageEnded, class UAnimMontage*, bool /*bInterrupted*/);
DECLARE_DELEGATE_TwoParams(FOnMontageBlendingOutStarted, class UAnimMontage*, bool /*bInterrupted*/);
DECLARE_DELEGATE_OneParam(FOnMontageBlendedInEnded, class UAnimMontage*);
DECLARE_DELEGATE_ThreeParams(FOnMontageSectionChanged, class UAnimMontage*, FName, bool);

// 사용 — Montage 완료 콜백
FOnMontageEnded EndedDelegate;
EndedDelegate.BindUObject(this, &AMyChar::OnAttackEnded);
SkelMeshComp->GetAnimInstance()->Montage_SetEndDelegate(EndedDelegate, AttackMontage);
```

### 3.5 RootMotion

```cpp
// 활성 — Montage 가 RootMotion 적용
Montage->bEnableRootMotionTranslation = true;
Montage->bEnableRootMotionRotation = true;
Montage->RootMotionRootLock = ERootMotionRootLock::AnimFirstFrame;

// CharacterMovement 가 자동 적용 (CMC 의 RootMotion 활성)
// 자세한 패턴 = Components/MovementComponents §5.12
```

### 3.6 Slot Animation Tracks

```cpp
// AnimBP 의 Slot 노드 = "DefaultSlot" / "UpperBody" / "LowerBody" / etc
// Montage 가 Slot 별로 분리 — 동시 재생 가능 (예: 상체 공격 + 하체 이동)
```

---

## 4. UBlendSpace (966 lines — 1D / 2D Blend)

### 4.1 1D / 2D / AimOffset

```cpp
// BlendSpace.h
class UBlendSpace : public UAnimationAsset
{
    // 2D Blend (X = Speed, Y = Direction)
    UPROPERTY(EditAnywhere)
    FBlendParameter BlendParameters[3];   // [0] X, [1] Y, [2] Z (드물게)

    // Sample Data — 각 좌표의 Animation
    UPROPERTY()
    TArray<FBlendSample> SampleData;
};

// UBlendSpace1D — 단일 차원 (걷기 → 달리기)
// UAimOffsetBlendSpace — 조준 (Yaw / Pitch)
```

### 4.2 사용 (AnimBP 안)

```cpp
// AnimBP 그래프에서 BlendSpacePlayer 노드 사용
// 입력 = 캐릭터 Speed / Direction
// 출력 = 블렌드된 Pose
```

---

## 5. UAnimBlueprint (299 lines)

### 5.1 핵심 — TargetSkeleton

```cpp
// AnimBlueprint.h:81
class UAnimBlueprint : public UBlueprint, public IInterface_PreviewMeshProvider
{
    // AnimBlueprint.h:91 — 호환 Skeleton (의무)
    UPROPERTY(AssetRegistrySearchable)
    TObjectPtr<USkeleton> TargetSkeleton;

    // 5.x — Animation Layer Interface
    UPROPERTY()
    TArray<FBPInterfaceDescription> AnimBPInterfaces;
};
```

> **컴파일 결과** = `UAnimInstance` 자식 클래스 — `BPGC_*_C` 형식.

### 5.2 Animation Layer Interface (5.x)

```cpp
// 다른 AnimBP 가 이 BP 의 Layer 사용 가능 (Modular Animation)
// 예: Base AnimBP + Weapon AnimBP Layer = 조합
SkelMeshComp->LinkAnimClassLayers(WeaponAnimBPClass);
SkelMeshComp->UnlinkAnimClassLayers(WeaponAnimBPClass);
```

---

## 6. UAnimInstance (런타임 — 1,776 lines, 가장 큼)

### 6.1 베이스 + Native* 콜백

```cpp
class UAnimInstance : public UObject
{
    // AnimInstance.h:1372 — 초기화 (BeginPlay 시점)
    ENGINE_API virtual void NativeInitializeAnimation();

    // BeginPlay 직후 — Owner 캐싱 등
    ENGINE_API virtual void NativeBeginPlay();

    // 게임 스레드 — 매 프레임 (Blueprint Update 전)
    ENGINE_API virtual void NativeUpdateAnimation(float DeltaSeconds);

    // 워커 스레드 — 매 프레임 (멀티 스레드 안전 — 권장)
    ENGINE_API virtual void NativeThreadSafeUpdateAnimation(float DeltaSeconds);

    // 종료
    ENGINE_API virtual void NativeUninitializeAnimation();
};
```

### 6.2 NativeThreadSafeUpdateAnimation (5.x 권장)

> **`NativeUpdateAnimation`** = 게임 스레드 (느림) / **`NativeThreadSafeUpdateAnimation`** = 워커 스레드 (병렬, 빠름).

```cpp
// MyAnimInstance.cpp
void UMyAnimInstance::NativeThreadSafeUpdateAnimation(float DeltaSeconds)
{
    Super::NativeThreadSafeUpdateAnimation(DeltaSeconds);
    TRACE_CPUPROFILER_EVENT_SCOPE(UMyAnimInstance::NativeThreadSafeUpdateAnimation);

    // ⚠️ 주의 — 게임 스레드 객체 직접 접근 금지 (Owner / Component)
    // 미리 캐싱한 데이터만 읽기
    Speed = CachedSpeed;
    Direction = CachedDirection;
}

// NativeUpdateAnimation 에서 캐싱
void UMyAnimInstance::NativeUpdateAnimation(float DeltaSeconds)
{
    Super::NativeUpdateAnimation(DeltaSeconds);
    if (auto* Owner = TryGetPawnOwner())
    {
        CachedSpeed = Owner->GetVelocity().Size();
        CachedDirection = ComputeDirection(Owner);
    }
}
```

### 6.3 Curve API

```cpp
// AnimInstance.h:1205 — Curve 값 조회 (AnimSequence / Montage 의 Curve)
ENGINE_API float GetCurveValue(FName CurveName) const;
ENGINE_API bool GetCurveValueWithDefault(FName CurveName, float DefaultValue, float& OutValue);

// 사용 — IK Foot Lock / 발자국 Trigger / 표정 Curve
float FootLockL = AnimInstance->GetCurveValue(TEXT("FootLock_L"));
```

### 6.4 Montage_* 시리즈 API

```cpp
// 재생 / 정지 / Section 점프
Montage_Play(Montage, /*PlayRate=*/ 1.f);
Montage_PlayWithBlendIn(Montage, FAlphaBlendArgs(0.2f));
Montage_Stop(/*BlendOut=*/ 0.2f, Montage);
Montage_JumpToSection(TEXT("Attack2"));
Montage_StopGroupByName(/*BlendOut=*/ 0.2f, TEXT("FullBody"));

// 상태 조회
bool bIsPlaying = AnimInstance->Montage_IsPlaying(Montage);
FName CurrentSection = AnimInstance->Montage_GetCurrentSection(Montage);
```

### 6.5 표준 자식 패턴

```cpp
// MyAnimInstance.h
UCLASS()
class UMyAnimInstance : public UAnimInstance
{
    GENERATED_BODY()
public:
    virtual void NativeInitializeAnimation() override;
    virtual void NativeUpdateAnimation(float DeltaSeconds) override;
    virtual void NativeThreadSafeUpdateAnimation(float DeltaSeconds) override;

    UPROPERTY(BlueprintReadOnly, Category="Anim")
    float Speed;

    UPROPERTY(BlueprintReadOnly, Category="Anim")
    float Direction;

    UPROPERTY(BlueprintReadOnly, Category="Anim")
    bool bIsCrouched;

private:
    TWeakObjectPtr<ACharacter> CachedOwner;
    float CachedSpeed = 0.f;
    float CachedDirection = 0.f;
};
```

---

## 7. AnimNotify (이벤트 트리거)

### 7.1 UAnimNotify vs UAnimNotifyState

| 종류 | 의미 | 사용 |
|------|------|------|
| `UAnimNotify` | 한 시점에 트리거 (점) | 발자국 / 발사음 / VFX Spawn |
| `UAnimNotifyState` | 시작 ~ 종료 시점 (구간) | Combo Window / Hit Box 활성 / 무기 트레이스 |

### 7.2 UAnimNotify 작성

```cpp
// MyFootstepNotify.h
UCLASS(meta=(DisplayName="Footstep"))
class UMyFootstepNotify : public UAnimNotify
{
    GENERATED_BODY()
public:
    virtual void Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyFootstepNotify::Notify);
        if (auto* Owner = MeshComp->GetOwner())
        {
            UGameplayStatics::SpawnSoundAtLocation(Owner, FootstepSound, Owner->GetActorLocation());
        }
    }

    UPROPERTY(EditAnywhere)
    TObjectPtr<USoundBase> FootstepSound;
};
```

### 7.3 UAnimNotifyState 작성

```cpp
// MyHitboxNotifyState.h
UCLASS()
class UMyHitboxNotifyState : public UAnimNotifyState
{
    GENERATED_BODY()
public:
    virtual void NotifyBegin(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, float TotalDuration, const FAnimNotifyEventReference& EventReference) override
    {
        // Hit Box 활성
    }

    virtual void NotifyEnd(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference) override
    {
        // Hit Box 비활성
    }
};
```

---

## 8. 함정 & 안티패턴 (12종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | 다른 Skeleton 의 AnimSequence 재생 | Skeleton 호환 검사. Compatible Skeleton 등록 |
| 2 | `NativeUpdateAnimation` 안 무거운 로직 | `NativeThreadSafeUpdateAnimation` (워커 스레드) 사용 |
| 3 | `NativeThreadSafeUpdateAnimation` 안 게임 스레드 객체 접근 | 미리 캐싱한 데이터만 |
| 4 | Constructor 안 `LoadObject<UAnimMontage>` | UPROPERTY EditAnywhere + BP 지정 또는 Soft |
| 5 | Montage_Play 후 `EndedDelegate` 바인딩 안 함 | `Montage_SetEndDelegate` 사용 — 완료 콜백 필요 시 |
| 6 | RootMotion 활성 + CMC 의 `bEnableRootMotionMontagesOnly = false` | CMC 측 `bEnableRootMotionMontagesOnly = true` 의무 |
| 7 | AnimNotify 가 `Owner` 검증 안 함 | `IsValid(MeshComp->GetOwner())` 가드 |
| 8 | BlendSpace Y 축 (Direction) 0~360 사용 | -180~180 표준 (Wrap-around 함정) |
| 9 | 5.0+ `SequenceLength` 직접 접근 | `GetPlayLength()` 사용 (Deprecated) |
| 10 | Cooked 빌드 안 `RawAnimationData` 접근 | `CompressedData` 만 — `WITH_EDITOR` 가드 |
| 11 | 🚨 `TObjectIterator<UAnimSequence>` | UAssetManager + AssetRegistry ([`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md)) |
| 12 | 🚨 자주 사용 Montage / AnimBP PreLoad 안 함 | Match Start `PreloadPrimaryAssets` ([`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md)) |

---

## 9. 체크리스트

- [ ] AnimSequence / AnimMontage / AnimBP 의 TargetSkeleton 호환 검사
- [ ] AnimInstance 자식 = `NativeUpdateAnimation` (캐싱) + `NativeThreadSafeUpdateAnimation` (계산) 분리
- [ ] Montage_Play 시 EndedDelegate 바인딩 (완료 처리)
- [ ] RootMotion = Montage 측 활성 + CMC 측 `bEnableRootMotionMontagesOnly = true`
- [ ] AnimNotify Owner 검증 + 첫 줄 프로파일링 스코프
- [ ] BlendSpace Direction = -180~180
- [ ] Cooked 빌드 RawAnimationData 접근 X (WITH_EDITOR 가드)
- [ ] AnimBP / AnimMontage = 자주 사용 시 Match Start PreLoad
- [ ] 🚨 6대 정책 + 어셋 로드 정책

---

## 10. 관련 sub-skill

- [`AssetClasses/SKILL.md`](../SKILL.md) — 메인
- [`AssetClasses/Mesh`](../Mesh/SKILL.md) — USkeleton (§3) + USkeletalMesh 페어
- [`Components/MeshComponents`](../../Components/references/MeshComponents.md) — SkeletalMeshComponent (호스트)
- [`Components/MovementComponents`](../../Components/references/MovementComponents.md) — RootMotion / RootMotionSource (§5.12)
- 교차: 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) (AnimBP / Montage PreLoad) · 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) (NativeUpdate 콜백)

---

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. **UAnimSequenceBase 319 + UAnimSequence 1,001** (RateScale / AdditiveAnimType 3종 / RefPoseSeq / GetAnimationPose / FAnimExtractContext / GetPlayLength / Compression FCompressedAnimSequence + A