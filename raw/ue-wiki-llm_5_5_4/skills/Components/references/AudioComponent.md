---
name: components-audiocomponent
description: UAudioComponent + UForceFeedbackComponent + 5.x ISoundParameterController - Attenuation + Concurrency + 6대 정책.
---

# Components / AudioComponent — 오디오 + 햅틱 (Engine 모듈)

> **위치**: `Engine/Source/Runtime/Engine/Classes/Components/{AudioComponent,ForceFeedbackComponent}.h`
> **베이스**: `USceneComponent` → `UAudioComponent` (+ `ISoundParameterControllerInterface` + `FQuartzTickableObject`) / `UForceFeedbackComponent`
> **요지**: **3D 위치 사운드 + Attenuation + Concurrency + Sound Parameter (5.x Quartz 통합)**. Force Feedback 은 게임패드 진동 (Gamepad rumble + 햅틱).

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
| 🎯 **어셋 로드** | 🚨 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) — **SoundCue / SoundWave / SoundClass = Soft + UAssetManager Primary Asset 표준** (BGM / 큰 SFX 는 메모리 큼). 자주 재생 SFX (발사·발자국) = Match Start `PreloadPrimaryAssets` 의무 — 첫 재생 히칭 회피. **MetaSounds (5.x)** = 자체 자산 — Soft 표준. ForceFeedback Effect = 작은 자산 (Hard OK). |
| 🎯 **어셋 최적화** | 🚨 [`12_AssetOptimizationPolicy.md §4`](../../../references/12_AssetOptimizationPolicy.md) — **Audio Culling 의무** — Attenuation `MaxDistance + FalloffDistance` (1차 컬링) + Concurrency `MaxCount + StopFarthest` (16개 → 4개) + SoundMix Volume Mute (메뉴 시 BGM 죽임) + **Significance Manager 통합** (환경음 거리 기반 활성/비활성 — `SigMgr->RegisterObject` + 콜백 안 `New < 0.01f` = `Stop` / `New > 0.05f` = `Play`) + Audio Engine MaxChannels 자동 Voice Limit. |

---

## 1. UAudioComponent — 사운드 재생

[`AudioComponent.h:166-700`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/AudioComponent.h):

### 1.1 핵심 필드

| 필드 | 의미 |
|------|------|
| `Sound` | `TObjectPtr<USoundBase>` — 재생할 SoundCue/SoundWave/MetaSound |
| `bAutoActivate` | 컴포넌트 활성 시 자동 재생 |
| `bAllowSpatialization` | 3D 공간화 (false = 2D 배경음) |
| `bIsUISound` | UI 사운드 (Pause 시에도 재생) |
| `bShouldRemainActiveIfDropped` | Concurrency 한도 초과 시에도 재생 유지 |
| `bIsPreviewSound` | 에디터 프리뷰 (런타임 식별) |
| `AttenuationSettings` | `USoundAttenuation*` — 거리 감쇠/공간화 |
| `ConcurrencySet` | `TSet<USoundConcurrency*>` — 동시 재생 제한 |
| `VolumeMultiplier` / `PitchMultiplier` | 베이스 배율 |
| `Modulation` | Volume/Pitch/Lowpass/Highpass 모듈레이션 (5.x) |
| `EnvelopeFollowingAttackTime` / `EnvelopeFollowingReleaseTime` | Envelope 분석 (Audio-driven 애니메이션) |
| `bEnableBaseSubmix` | Submix 라우팅 |
| `SoundSubmixSends` | 추가 Submix 송신 |

### 1.2 콜백 (Delegate)

```cpp
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnAudioFinished);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAudioPlaybackPercent, const class USoundWave*, const float);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnAudioSingleEnvelopeValue, const float);

UPROPERTY(BlueprintAssignable)
FOnAudioFinished OnAudioFinished;          // 재생 완료

UPROPERTY(BlueprintAssignable)
FOnAudioPlaybackPercent OnAudioPlaybackPercentNative;   // 진행률

UPROPERTY(BlueprintAssignable)
FOnAudioSingleEnvelopeValue OnAudioSingleEnvelopeValue; // Envelope (Lipsync 등)
```

### 1.3 Sound Parameter Interface (5.x)

`UAudioComponent` 가 `ISoundParameterControllerInterface` 구현 — MetaSound / SoundCue 의 매개변수 런타임 변경:

```cpp
// 3D Action / Trigger / Float / Bool / Object 파라미터
AudioComp->SetTriggerParameter(TEXT("FireGun"));
AudioComp->SetFloatParameter(TEXT("Volume"), 0.5f);
AudioComp->SetBoolParameter(TEXT("UnderWater"), true);
AudioComp->SetIntParameter(TEXT("WeaponType"), 2);
AudioComp->SetObjectParameter(TEXT("WaveAsset"), MyWave);
AudioComp->SetStringParameter(TEXT("Variant"), TEXT("Heavy"));
```

> **MetaSound 인스턴스 매개변수** — 게임 상태에 따라 사운드 동적 변경. SoundCue 보다 강력.

### 1.4 Quartz 통합 (음악 동기화)

`FQuartzTickableObject` 자손 — `UQuartzClockHandle` 으로 박자 기준 재생:

```cpp
// 다음 다운비트에 재생
FQuartzQuantizationBoundary Boundary(EQuartzCommandQuantization::Bar, 1, EQuarztQuantizationReference::CurrentTimeRelative);
AudioComp->StartQuartz(Clock, Boundary);
```

### 1.5 표준 패턴

```cpp
// AGunActor::Fire
USoundAttenuation* Attenuation = LoadObject<USoundAttenuation>(/* path */);

UAudioComponent* SoundComp = UGameplayStatics::SpawnSoundAttached(
    GunFireSound,
    GetMesh(),
    TEXT("MuzzleSocket"),
    FVector::ZeroVector,
    EAttachLocation::KeepRelativeOffset,
    /*bStopWhenAttachedToDestroyed=*/true,
    /*VolumeMultiplier=*/1.0f,
    /*PitchMultiplier=*/FMath::FRandRange(0.95f, 1.05f),  // 약간 랜덤
    /*StartTime=*/0.0f,
    Attenuation);
```

> **`SpawnSoundAttached` / `SpawnSoundAtLocation` / `PlaySound2D`** 표준 — 직접 UAudioComponent 생성 보다.

---

## 2. UForceFeedbackComponent — 게임패드 진동 + 햅틱

[`ForceFeedbackComponent.h:59-200`](../../../../../UnrealEngine/Engine/Source/Runtime/Engine/Classes/Components/ForceFeedbackComponent.h):

### 2.1 핵심 필드

| 필드 | 의미 |
|------|------|
| `ForceFeedbackEffect` | `UForceFeedbackEffect*` — 진동 패턴 |
| `bAutoDestroy` | 종료 시 자동 destroy |
| `bStopWhenOwnerDestroyed` | Owner destroy 시 중지 |
| `bLooping` | 반복 |
| `bIgnoreTimeDilation` | TimeDilation 영향 없음 |
| `IntensityMultiplier` | 강도 배율 |
| `AttenuationSettings` | `UForceFeedbackAttenuation*` — 거리 감쇠 (Sound 와 동일 컨셉) |

### 2.2 표준 패턴

```cpp
// AExplosion::Detonate
UForceFeedbackEffect* Effect = LoadObject<UForceFeedbackEffect>(/* path */);

UGameplayStatics::SpawnForceFeedbackAtLocation(
    GetWorld(),
    Effect,
    GetActorLocation(),
    /*bLooping=*/false,
    /*IntensityMultiplier=*/1.0f,
    /*StartTime=*/0.0f,
    Attenuation);
```

> **`SpawnForceFeedbackAtLocation` / `SpawnForceFeedbackAttached`** 가 표준 — 자동으로 모든 LocalPlayerController 의 패드에 거리 기반 강도로 진동.

---

## 3. Concurrency 시스템 (Audio 전용)

> **`USoundConcurrency`** — 같은 그룹 사운드 동시 재생 한계.

```cpp
// Concurrency 설정 예
USoundConcurrency Concurrency;
Concurrency.Concurrency.MaxCount = 4;                            // 동시 4개
Concurrency.Concurrency.ResolutionRule = StopOldest;             // 초과 시 가장 오래된 정지
Concurrency.Concurrency.VolumeScale = 0.7f;                      // Voice steal 시 볼륨
Concurrency.Concurrency.bLimitToOwner = true;                    // Actor 단위 제한
```

> **모든 발사음에 같은 Concurrency** — 100발 동시 발사 시에도 4개만 들림. 사운드 채널 폭사 방지.

---

## 4. 비용 + 공간화

| 항목 | 비용 |
|------|------|
| 동시 재생 사운드 수 | **가장 큰 비용** — Concurrency 로 제한 |
| Spatialization (HRTF) | 2D 보다 ~3배 |
| Attenuation 검사 | LineTrace Occlusion 시 비싸짐 |
| Submix 효과 (Reverb 등) | 그룹 단위 — 비용 1회 |
| Modulation | 거의 무료 |
| Envelope Following | 약간 (CPU FFT) |

---

## 5. 함정 & 안티패턴

| # | 함정 | 정답 |
|---|------|-----|
| 1 | 매 발사음에 `UAudioComponent` 새로 생성 | `SpawnSoundAttached` 사용 (자동 풀링 + 재사용) |
| 2 | Concurrency 없이 100개 사운드 동시 재생 | Concurrency 표준 적용 |
| 3 | `bAllowSpatialization = true` 인 2D BGM | BGM 은 false |
| 4 | UI 사운드가 Pause 시 멈춤 | `bIsUISound = true` |
| 5 | `SetFloatParameter` 매 Tick 호출 (값 동일해도) | 변화 시점에만 |
| 6 | 폭발음에 ForceFeedback 없음 | `SpawnForceFeedbackAtLocation` 페어 |
| 7 | Owner Destroy 시 사운드 안 멈춤 | `bStopWhenOwnerDestroyed = true` (default false) |
| 8 | `bAutoActivate = true` + 제어 안 됨 | 명시 `Play()` 호출 |
| 9 | 🚨 OnAudioFinished 콜백 첫 줄 프로파일링 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` ([`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)) |

---

##