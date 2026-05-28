---
name: assetclasses-camera
description: UCameraShakeBase + UCameraShakePattern 4종 (Wave/Perlin/Sequence/Custom) + UCameraModifier + 5.x UCameraAnimationSequence.
---

# AssetClasses/Camera — UCameraShakeBase + UCameraShakePattern + UCameraModifier

> **위치**: `Engine/Source/Runtime/Engine/Classes/Camera/CameraShakeBase.h` (690) + `CameraModifier.h` + `CameraAnimationHelper.h`
> **베이스**: `UCameraShakeBase : public UObject` + `UCameraShakePattern : public UObject` + `UCameraModifier : public UObject`
> **요지**: **카메라 효과 자산** — Shake (떨림) / Modifier (변형) / Animation (시퀀서). PlayerCameraManager 가 호스트.

---

## 🚨 공통 정책

| 정책 | Camera 자산 적용 |
|------|-----------------|
| 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) | CameraShake = 작은 자산 (Hard OK). 일부 큰 시퀀스 = Soft 검토. |
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | UpdateAndApplyCameraModifier / UpdateShake 첫 줄 스코프. |

---

## 1. UCameraShakeBase (Shake 베이스 — 5.x 표준)

```cpp
// CameraShakeBase.h:447
class UCameraShakeBase : public UObject
{
    // CameraShakeBase.h:624 — 핵심 Pattern 위임
    UPROPERTY(EditAnywhere, Instanced)
    TObjectPtr<UCameraShakePattern> RootShakePattern;

    // CameraShakeBase.h:576 — 시작
    ENGINE_API void StartShake(APlayerCameraManager* Camera, float Scale,
                                ECameraShakePlaySpace InPlaySpace,
                                FRotator UserPlaySpaceRot = FRotator::ZeroRotator);

    // CameraShakeBase.h:591 — 정지
    ENGINE_API void StopShake(bool bImmediately = true);
};
```

### 1.1 ECameraShakePlaySpace

| Space | 의미 |
|-------|------|
| `CameraLocal` | 카메라 로컬 (FPS 표준) |
| `World` | 월드 좌표 (절대) |
| `UserDefined` | 사용자 지정 회전 |

### 1.2 사용 패턴

```cpp
// PlayerCameraManager 가 시작
PlayerCameraManager->StartCameraShake(MyShakeClass, Scale=1.f);
PlayerCameraManager->StopCameraShake(MyShakeInstance);

// 또는 Component 측
UGameplayStatics::PlayWorldCameraShake(this, MyShakeClass, EpicenterLoc, InnerRadius=300.f, OuterRadius=2000.f, Falloff=1.f);
```

---

## 2. UCameraShakePattern (5.x — Shake 알고리즘)

> **CameraShake 의 실제 동작은 Pattern 에 위임** — 여러 Pattern 조합 가능.

```cpp
// CameraShakeBase.h:646
class UCameraShakePattern : public UObject
{
    ENGINE_API void StartShakePattern(const FCameraShakePatternStartParams& Params);
    ENGINE_API void StopShakePattern(const FCameraShakePatternStopParams& Params);

    // 자식 override
    virtual void StartShakePatternImpl(const FCameraShakePatternStartParams& Params) {}
    virtual void StopShakePatternImpl(const FCameraShakePatternStopParams& Params) {}
};
```

### 2.1 표준 Pattern 자식

| Pattern | 의미 |
|---------|------|
| `UPerlinNoiseCameraShakePattern` | Perlin 노이즈 (5.x 표준 — Continuous Shake) |
| `UWaveOscillatorCameraShakePattern` | Sin Wave (단발 Shake) |
| `USequenceCameraShakePattern` | LevelSequence 기반 (Cinematic) |
| `UMatineeCameraShakePattern` | 4.x Matinee 호환 |

### 2.2 표준 Shake 자식 패턴

```cpp
UCLASS()
class UMyExplosionShake : public UCameraShakeBase
{
    GENERATED_BODY()
public:
    UMyExplosionShake()
    {
        // 표준 — Perlin Noise Pattern
        UPerlinNoiseCameraShakePattern* Pattern = ChangeRootShakePattern<UPerlinNoiseCameraShakePattern>();
        Pattern->Duration = 0.5f;
        Pattern->LocationAmplitudeMultiplier = 5.f;
        Pattern->RotationAmplitudeMultiplier = 1.f;
    }
};
```

---

## 3. UCameraModifier (카메라 변형 베이스)

```cpp
// CameraModifier.h:23
class UCameraModifier : public UObject
{
    // Priority — 낮을수록 먼저 적용
    UPROPERTY()
    uint8 Priority;

    // 활성 / 비활성
    UPROPERTY()
    uint8 bDisabled : 1;

    // CameraModifierShake 등이 자식
};
```

> **사용** — PlayerCameraManager 가 매 프레임 적용 (View Modifier).

### 3.1 자식 Modifier

| Modifier | 의미 |
|----------|------|
| `UCameraModifier_CameraShake` | Shake 통합 (Manager 가 사용) |

### 3.2 커스텀 Modifier 작성

```cpp
UCLASS()
class UMyZoomModifier : public UCameraModifier
{
    GENERATED_BODY()
public:
    virtual bool ModifyCamera(float DeltaTime, FMinimalViewInfo& InOutPOV) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyZoomModifier::ModifyCamera);
        InOutPOV.FOV *= ZoomScale;   // FOV 변경
        return false;   // false = 다음 Modifier 도 적용 / true = 종료
    }

    UPROPERTY()
    float ZoomScale = 0.5f;
};

// 등록 (PlayerCameraManager)
PlayerCameraManager->AddNewCameraModifier(UMyZoomModifier::StaticClass());
```

---

## 4. UCameraAnimationSequence (5.x — Sequencer 기반)

> **5.x 신규 — Sequencer 트랙 기반 카메라 애니메이션** (4.x UCameraAnim 대체).

```cpp
// 자산 = LevelSequence 자식
class UCameraAnimationSequence : public ULevelSequence
{
    // Sequencer 안 카메라 트랙 정의
};

// 사용
PlayerCameraManager->PlayCameraAnimation(CameraAnimSequence);
```

---

## 5. CameraShakeSourceComponent (3D 위치 기반 Shake)

```cpp
// 액터에 부착 — 위치 기반 Shake (폭발 / 전차 발사)
UCameraShakeSourceComponent* ShakeSource = CreateDefaultSubobject<...>(TEXT("Shake"));
ShakeSource->CameraShake = MyShakeClass;
ShakeSource->Attenuation = ECameraShakeAttenuation::Linear;
ShakeSource->InnerAttenuationRadius = 200.f;
ShakeSource->OuterAttenuationRadius = 2000.f;

ShakeSource->Start();   // 모든 PlayerCameraManager 에 자동 전송 (거리 기반)
```

---

## 6. 함정 & 안티패턴 (6종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | 4.x `UMatineeCameraShake` 사용 (5.x deprecated) | `UCameraShakeBase` + `UPerlinNoiseCameraShakePattern` |
| 2 | StopShake 호출 안 함 (영구 Shake) | `bImmediately=false` 로 Fade Out |
| 3 | Shake Scale = 1.0 고정 | 거리 기반 Falloff 또는 PlayWorldCameraShake 사용 |
| 4 | ModifyCamera 매 프레임 비싼 작업 | TRACE_CPUPROFILER_EVENT_SCOPE 의무 |
| 5 | CameraModifier 우선순위 (Priority) 안 정의 | 권장 설정 — Priority 0 (높음) ~ 255 (낮음) |
| 6 | `TObjectIterator<UCameraShakeBase>` | AssetRegistry 사용 |

---

## 7. 관련 sub-skill

- [`AssetClasses/SKILL.md`](../SKILL.md) — 메인
- [`Components/CameraComponent`](../../Components/references/CameraComponent.md) — Camera Component (호스트)
- [`GameFramework/Controller`](../../GameFramework/references/Controller.md) — APlayerCameraManager 진입점
- 교차: 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) (ModifyCamera 콜백)

---

## 8. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. **UCameraShakeBase (5.x 표준)** + RootShakePattern 위임 + StartShake/StopShake + ECameraShakePlaySpace 3종. **UCameraShakePattern** + 4종 표준 Pattern (PerlinNoise/WaveOscillator/Sequence/Matinee). **UCameraModifier** + Priority + ModifyCamera virtual. **5.x UCameraAnimationSequence** (LevelSequence 자식). **UCameraShakeSourceComponent** (거리 기반 Shake). 함정 6종. |
