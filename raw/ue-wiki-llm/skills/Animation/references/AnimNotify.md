---
name: animation-animnotify
description: UAnimNotify (점) vs UAnimNotifyState (구간) + FAnimNotifyEvent + Branch Point + Notify Queue 표준. 발자국·VFX·HitBox·Combo 윈도우·무기 트레이스 트리거 표준 패턴 + 게임 스레드 콜백 + Pool/AutoRelease 의무.
---

# Animation/AnimNotify — UAnimNotify + UAnimNotifyState + Branch Point

> **위치**: `Engine/Source/Runtime/Engine/Classes/Animation/AnimNotify*.h` + `AnimNotifyQueue.h`
> **베이스**: `UAnimNotify : public UObject` / `UAnimNotifyState : public UObject`
> **요지**: 애니메이션 시점에 게임 로직 트리거 — Notify (점, 1회) vs NotifyState (구간, Begin~End) 두 종류.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | `Notify` / `NotifyBegin` / `NotifyTick` / `NotifyEnd` 첫 줄 `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 |
| 🚨 Owner 검증 | `IsValid(MeshComp)` + `IsValid(MeshComp->GetOwner())` 의무 |
| 🎯 [`12_AssetOptimizationPolicy.md`](../../../references/12_AssetOptimizationPolicy.md) §5 | VFX Spawn = `ENCPoolMethod::AutoRelease` (Niagara 풀) |

---

## 1. UAnimNotify vs UAnimNotifyState

| 종류 | 특징 | 사용 예 |
|------|------|---------|
| `UAnimNotify` | 한 시점 (점) 트리거 | 발자국 사운드, VFX Spawn, 발사 |
| `UAnimNotifyState` | 시작 ~ 종료 구간 | Combo Window, HitBox 활성, 무기 트레이스 |

---

## 2. UAnimNotify 작성 표준

```cpp
// MyFootstepNotify.h
UCLASS(meta=(DisplayName="Footstep"))
class UMyFootstepNotify : public UAnimNotify
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, Category="Footstep")
    TObjectPtr<USoundBase> FootstepSound;

    UPROPERTY(EditAnywhere, Category="Footstep")
    FName FootBoneName = TEXT("foot_l");

    virtual void Notify(USkeletalMeshComponent* MeshComp,
                        UAnimSequenceBase* Animation,
                        const FAnimNotifyEventReference& EventReference) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyFootstepNotify::Notify);

        if (!IsValid(MeshComp) || !IsValid(MeshComp->GetOwner())) return;

        FVector FootLoc = MeshComp->GetSocketLocation(FootBoneName);

        // Sound 재생 — Pool 자동
        UGameplayStatics::SpawnSoundAtLocation(MeshComp->GetWorld(), FootstepSound, FootLoc);
    }

    virtual FString GetNotifyName_Implementation() const override
    {
        return TEXT("Footstep");
    }
};
```

---

## 3. UAnimNotifyState 작성 표준

```cpp
// MyHitboxNotifyState.h
UCLASS(meta=(DisplayName="Hitbox Active"))
class UMyHitboxNotifyState : public UAnimNotifyState
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, Category="Hitbox")
    float Damage = 10.f;

    UPROPERTY(EditAnywhere, Category="Hitbox")
    FName WeaponSocket = TEXT("hand_r_weapon");

    // 1. NotifyBegin — 구간 시작
    virtual void NotifyBegin(USkeletalMeshComponent* MeshComp,
                              UAnimSequenceBase* Animation,
                              float TotalDuration,
                              const FAnimNotifyEventReference& EventReference) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyHitboxNotifyState::Begin);
        if (!IsValid(MeshComp->GetOwner())) return;

        // HitBox 활성 (Owner 의 무기 컴포넌트에 알림)
        if (auto* WeaponComp = MeshComp->GetOwner()->FindComponentByClass<UWeaponComponent>())
        {
            WeaponComp->ActivateHitbox(Damage);
        }
    }

    // 2. NotifyTick — 매 프레임 (구간 동안)
    virtual void NotifyTick(USkeletalMeshComponent* MeshComp,
                             UAnimSequenceBase* Animation,
                             float FrameDeltaTime,
                             const FAnimNotifyEventReference& EventReference) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyHitboxNotifyState::Tick);
        if (!IsValid(MeshComp->GetOwner())) return;

        // 무기 Trace — 매 프레임 콜리전 체크
        FVector Start = MeshComp->GetSocketLocation(WeaponSocket);
        FVector End = Start + MeshComp->GetForwardVector() * 100.f;

        FHitResult Hit;
        FCollisionQueryParams Params(SCENE_QUERY_STAT(WeaponTrace), true, MeshComp->GetOwner());
        bool bHit = MeshComp->GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Pawn, Params);

        if (bHit && Hit.GetActor())
        {
            UGameplayStatics::ApplyDamage(Hit.GetActor(), Damage, nullptr, MeshComp->GetOwner(), nullptr);
        }
    }

    // 3. NotifyEnd — 구간 종료
    virtual void NotifyEnd(USkeletalMeshComponent* MeshComp,
                            UAnimSequenceBase* Animation,
                            const FAnimNotifyEventReference& EventReference) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyHitboxNotifyState::End);
        if (!IsValid(MeshComp->GetOwner())) return;

        if (auto* WeaponComp = MeshComp->GetOwner()->FindComponentByClass<UWeaponComponent>())
        {
            WeaponComp->DeactivateHitbox();
        }
    }
};
```

---

## 4. FAnimNotifyEvent (Notify 메타)

```cpp
// AnimSequenceBase.h
struct FAnimNotifyEvent : public FAnimLinkableElement
{
    UPROPERTY()
    TObjectPtr<UAnimNotify> Notify;             // 점 Notify

    UPROPERTY()
    TObjectPtr<UAnimNotifyState> NotifyStateClass;  // 구간 Notify

    UPROPERTY()
    float Duration;                              // 구간 길이 (NotifyState)

    UPROPERTY()
    bool bConvertedFromBranchingPoint;           // Branch Point (Montage)
};
```

---

## 5. Branch Point (UAnimMontage 전용)

> **일반 Notify** = 게임 스레드 시뮬레이션 후 호출 (1~2 프레임 지연 가능).
> **Branch Point** = AnimGraph 평가 중 즉시 호출 (지연 0).

```cpp
// AnimMontage 의 Notify = bAlwaysFromTrack = true → Branch Point
// 사용 — Section 자동 점프, Combo Window 정밀
```

---

## 6. Notify Queue + Tick Order

```
1. NativeUpdateAnimation (게임 스레드)
2. AnimGraph Update (워커 스레드) — Notify 누적 → FAnimNotifyQueue
3. CompleteParallelAnimationEvaluation (게임 스레드)
4. TriggerAnimNotifies — Queue 의 Notify 모두 호출 (순서대로)
5. Notify::Notify / NotifyBegin / NotifyTick / NotifyEnd 콜백
```

> **순서**: Begin → (Tick × N) → End. NotifyState 구간은 시작/종료 시점 자동 매칭.

---

## 7. Anti-pattern: 무거운 Spawn

```cpp
// ❌ Notify 안 직접 SpawnEmitter (히칭)
void UMyVFXNotify::Notify(...)
{
    UGameplayStatics::SpawnEmitterAtLocation(World, MyParticle, Loc);  // 비용 큼
}

// ✅ Niagara + AutoRelease Pool
void UMyVFXNotify::Notify(USkeletalMeshComponent* MeshComp, ...)
{
    if (!IsValid(MeshComp->GetOwner())) return;

    UNiagaraFunctionLibrary::SpawnSystemAtLocation(
        MeshComp->GetWorld(),
        MyNiagaraSystem,
        MeshComp->GetComponentLocation(),
        FRotator::ZeroRotator,
        FVector(1.0f),
        /*bAutoDestroy=*/ false,
        /*bAutoActivate=*/ true,
        /*PoolingMethod=*/ ENCPoolMethod::AutoRelease  // ⭐ 5.x 표준
    );
}
```

---

## 8. 함정 & 안티패턴 (10대)

| # | 함정 | 정답 |
|---|------|------|
| 1 | Owner 검증 누락 | `IsValid(MeshComp)` + `IsValid(MeshComp->GetOwner())` 의무 |
| 2 | Notify 안 직접 SpawnEmitter / SpawnSound (반복 = 히칭) | Pool / AutoRelease (Niagara `ENCPoolMethod::AutoRelease`) |
| 3 | NotifyState `NotifyEnd` 누락 (HitBox stuck) | 모든 NotifyBegin 페어 NotifyEnd |
| 4 | Notify 안 무거운 Trace / Cast | 캐싱 + 경량화 |
| 5 | Branch Point 미사용 — Section 점프 부정확 | `bAlwaysFromTrack = true` (AnimMontage) |
| 6 | NotifyTick 안 매 프레임 SpawnEmitter | 1회만 (NotifyBegin) 또는 Interval |
| 7 | 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 |
| 8 | UAnimNotify 가 Editor 전용 자산 (UTexture2D 미리보기) 사용 | `WITH_EDITORONLY_DATA` 가드 |
| 9 | Notify 가 GameInstance / World Subsystem 직접 검색 | `MeshComp->GetWorld()->GetSubsystem<>()` 캐싱 |
| 10 | 다수 NPC — Notify 가 매 프레임 무거운 작업 | Significance + LOD 시 Tick 회피 |

---

## 9. 체크리스트

- [ ] Notify / NotifyBegin / NotifyTick / NotifyEnd 첫 줄 프로파일링 스코프
- [ ] Owner 검증 (`IsValid`)
- [ ] VFX Spawn = Pool / AutoRelease
- [ ] NotifyState NotifyEnd 의무 (HitBox 정리)
- [ ] Branch Point (AnimMontage Section 정밀)
- [ ] 다수 NPC = Significance + Tick 회피

---

## 10. 관련

- [`Animation/SKILL.md`](../SKILL.md) — 메인
- [`Animation/references/AnimInstance.md`](../AnimInstance/SKILL.md) — Notify Queue 흐름
- [`AssetClasses/references/Animation.md`](../../AssetClasses/references/Animation.md) §7 — Notify 구조
- [`Niagara/SKILL.md`](../../Niagara/SKILL.md) — VFX Pool 표준
- [`AssetClasses/references/Audio.md`](../../AssetClasses/references/Audio.md) — Sound Spawn

## 11. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-07 | 최초 작성. UAnimNotify + UAnimNotifyState 표준 + Branch Point + Tick Order + Pool 의무 + 함정 10대. |
