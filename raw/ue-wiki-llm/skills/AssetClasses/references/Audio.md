---
name: assetclasses-audio
description: USoundBase (418) + USoundCue (379) + USoundWave (1,822) + USoundClass + USoundConcurrency + USoundMix + USoundAttenuation + 5.x MetaSounds.
---

# AssetClasses/Audio — USoundBase + USoundCue + USoundWave + SoundClass + Concurrency + Mix + Attenuation + MetaSounds

> **위치**: `Engine/Source/Runtime/Engine/Classes/Sound/`
> **파일**: `SoundBase.h` (418) + `SoundCue.h` (379) + `SoundWave.h` (1,822) + `SoundClass.h` + `SoundConcurrency.h` + `SoundMix.h` + `SoundAttenuation.h` + 5.x **MetaSoundSource** (Plugin)
> **베이스**: `USoundBase : public UObject` → `USoundCue` (Cue 그래프) / `USoundWave` (음원 데이터) / `UMetaSoundSource` (5.x — 절차적)
> **요지**: **모든 게임 사운드의 자산 트리** — 컴포넌트 (AudioComponent) 페어 + Concurrency / Mix / Attenuation 라우팅 시스템.

---

## 🚨 공통 정책

| 정책 | Audio 자산 적용 |
|------|----------------|
| 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) | **USoundWave = 가장 큼** (BGM = 10~50MB / Long SFX = 1~10MB). **TSoftObjectPtr<USoundBase>` + Stream-In 표준** (USoundWave 자체 Streaming). 자주 재생 SFX (발사 / 발자국) = Match Start `PreloadPrimaryAssets` 의무 — 첫 재생 히칭 회피. **MetaSounds (5.x)** = 더 큰 (절차적 + DSP). |
| 🚨 [`10_ComponentPolicies.md`](../../../references/10_ComponentPolicies.md) | Sound 멤버 = `UPROPERTY()` + `TObjectPtr<USoundBase>` 또는 `TSoftObjectPtr`. AudioComponent = `OnAudioFinished` 콜백 첫 줄 스코프. |
| 🚨 [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) | OnAudioFinished / OnQueuedAudioFinished 첫 줄 스코프. |
| [`05_EditorOnlyIndex.md`](../../../references/05_EditorOnlyIndex.md) | 🛠 SoundCue 그래프 (UEdGraph) = Editor 전용. Cooked = FirstNode 만. |
| 🎯 [`12_AssetOptimizationPolicy.md`](../../../references/12_AssetOptimizationPolicy.md) | **§4 Audio Culling 의무** — Attenuation MaxDistance (1차 컬링) + Concurrency MaxCount + 5종 ResolutionRule (StopFarthest 표준) + SoundMix Volume Mute (메뉴 시 BGM 죽임) + Significance 통합 (환경음 거리 기반 활성/비활성) + Audio Engine MaxChannels (자동 Voice Limit 64 채널). |

---

## 1. 베이스 트리

```
UObject
└── USoundBase (418 — 베이스, IAudioPropertiesSheetAssetUserInterface)
    ├── USoundCue (379 — 노드 그래프 + 분기 / 랜덤 / Mix)
    ├── USoundWave (1,822 — 단일 음원 데이터 + Streaming + Compression)
    │   ├── USoundWaveProcedural (런타임 생성)
    │   └── UMediaSoundWave (비디오 사운드)
    ├── UMetaSoundSource (5.x Plugin — 절차적)
    └── USoundCueTemplate (5.x — 템플릿 기반 Cue)
```

```
USoundClass        (Volume Mix 그룹 — Music / SFX / Voice / UI)
USoundConcurrency  (동시 재생 제한 — 무기 발사 16개 동시 X)
USoundMix          (Mix Profile — 메뉴 시 BGM 줄임)
USoundAttenuation  (3D 감쇠 + Spatial)
USoundSubmix       (DSP 라우팅 — Reverb / EQ / Compressor)
```

---

## 2. USoundBase (베이스 — 418 lines)

### 2.1 핵심 필드

```cpp
// SoundBase.h:108
class USoundBase : public UObject,
                   public IAudioPropertiesSheetAssetUserInterface,
                   public IInterface_AssetUserData
{
    // SoundBase.h:117 — Sound Class (Music / SFX / Voice / UI)
    UPROPERTY(EditAnywhere)
    TObjectPtr<USoundClass> SoundClassObject;

    // SoundBase.h:131 — Concurrency 오버라이드
    UPROPERTY(EditAnywhere)
    uint8 bOverrideConcurrency : 1;

    // SoundBase.h:188 — Concurrency 셋 (다중)
    UPROPERTY(EditAnywhere)
    TSet<TObjectPtr<USoundConcurrency>> ConcurrencySet;

    // SoundBase.h:202 — 길이 (초)
    UPROPERTY()
    float Duration;

    // 3D 감쇠 (Optional Override)
    UPROPERTY(EditAnywhere)
    uint8 bOverrideAttenuation : 1;

    UPROPERTY(EditAnywhere)
    TObjectPtr<USoundAttenuation> AttenuationSettings;
};
```

### 2.2 GetDuration / GetConcurrencyHandles

```cpp
// SoundBase.h:311
ENGINE_API virtual float GetDuration() const;

// SoundBase.h:361 — Concurrency 다수 조회
ENGINE_API void GetConcurrencyHandles(TArray<FConcurrencyHandle>& OutConcurrencyHandles) const;
```

---

## 3. USoundCue (Cue 그래프 — 379 lines)

### 3.1 핵심 — FirstNode

```cpp
// SoundCue.h:90
class USoundCue : public USoundBase
{
    // SoundCue.h:95 — Cue 그래프의 진입 노드
    UPROPERTY()
    TObjectPtr<USoundNode> FirstNode;

    // 캐싱된 정보
    float MaxDistance;
    int32 PrimeCount;

    // Cue 의 모든 노드
    UPROPERTY(transient)
    TArray<TObjectPtr<USoundNode>> AllNodes;
};
```

### 3.2 SoundNode 종류 (베이스 USoundNode)

| Node | 의미 |
|------|------|
| `USoundNodeWavePlayer` | SoundWave 재생 (Leaf) |
| `USoundNodeRandom` | 랜덤 선택 (다양성) |
| `USoundNodeAttenuation` | 감쇠 적용 |
| `USoundNodeConcatenator` | 순차 재생 |
| `USoundNodeMixer` | 믹싱 |
| `USoundNodeLooping` | 루프 |
| `USoundNodeDelay` | 딜레이 |
| `USoundNodeModulator` | Volume / Pitch 변조 |
| `USoundNodeBranch` | 조건 분기 |
| `USoundNodeOscillator` | LFO |

### 3.3 USoundCueTemplate (5.x 템플릿)

```cpp
// 자주 쓰는 Cue 패턴 — Template 기반 자동 생성
// 예: "랜덤 SoundWave + Attenuation" 템플릿 → SoundWave 만 지정하면 자동 Cue
```

---

## 4. USoundWave (음원 데이터 — 1,822 lines, 가장 큼)

### 4.1 핵심 — Audio Data + Streaming

```cpp
class USoundWave : public USoundBase
{
    // 채널 / 샘플 레이트 / 길이
    UPROPERTY()
    int32 NumChannels;          // 1 (Mono) / 2 (Stereo) / 6 (5.1) / 8 (7.1)

    UPROPERTY()
    int32 SampleRate;            // 44100 / 48000 / 22050 등

    UPROPERTY()
    float Duration;

    // 압축 데이터 (Cooked)
    FByteBulkData CompressedFormatData;

    // Loading Behavior (5.x)
    UPROPERTY(EditAnywhere)
    ESoundWaveLoadingBehavior LoadingBehavior;

    // 5.x Streaming
    UPROPERTY(EditAnywhere)
    uint8 bStreaming : 1;
};
```

### 4.2 ESoundWaveLoadingBehavior (5.x — 4종)

| Behavior | 의미 |
|----------|------|
| `Inherited` | SoundClass 의 설정 따름 |
| `RetainOnLoad` | 메모리 상주 (자주 재생) |
| `PrimeOnLoad` | 첫 재생 시 압축 해제 |
| `LoadOnDemand` | 매번 디스크 (스트리밍 — BGM 표준) |
| `ForceInline` | 인라인 (Bulk Data 안 메모리) |

### 4.3 Streaming (대용량 BGM)

```cpp
SoundWave->bStreaming = true;
SoundWave->LoadingBehavior = ESoundWaveLoadingBehavior::LoadOnDemand;
SoundWave->StreamingPriority = 100;   // 우선순위
```

### 4.4 Procedural Sound Wave (런타임)

```cpp
// USoundWaveProcedural — 런타임 PCM 생성
class UMyProceduralWave : public USoundWaveProcedural
{
    int32 OnGeneratePCMAudio(TArray<uint8>& OutAudio, int32 NumSamples) override
    {
        // PCM 데이터 생성 (DSP / 합성)
        return SamplesGenerated;
    }
};
```

---

## 5. USoundClass (Volume Mix 그룹)

```cpp
// SoundClass.h
class USoundClass : public UObject
{
    UPROPERTY(EditAnywhere)
    FSoundClassProperties Properties;
    // - Volume         (0~1)
    // - Pitch
    // - LowPassFilterFrequency
    // - VoiceCenterChannelVolume
    // - bApplyEffects
    // - bApplyAmbientVolumes

    UPROPERTY(EditAnywhere)
    TArray<TObjectPtr<USoundClass>> ChildClasses;   // 계층 구조
};

// 표준 트리
// Master
//  ├── SFX
//  │   ├── Footsteps
//  │   ├── Weapons
//  │   └── Environment
//  ├── Music
//  ├── Voice
//  └── UI
```

---

## 6. USoundConcurrency (동시 재생 제한)

```cpp
// SoundConcurrency.h
class USoundConcurrency : public UObject
{
    UPROPERTY(EditAnywhere)
    FSoundConcurrencySettings Concurrency;
    // - MaxCount               : 동시 재생 최대 N개
    // - bLimitToOwner          : Actor 별 제한
    // - ResolutionRule         : Oldest / Quietest / NewestStops / etc
    // - VolumeScale            : 동시 재생 시 Volume 감소
};

// 사용 예 — 발사음 16개 → 4개로 제한
SoundCue->ConcurrencySet.Add(WeaponConcurrency);   // MaxCount = 4
```

### ResolutionRule

| Rule | 의미 |
|------|------|
| `PreventNew` | 가득 차면 새 사운드 무시 |
| `StopOldest` | 가장 오래된 정지 |
| `StopFarthest` | 가장 먼 정지 |
| `StopQuietest` | 가장 조용한 정지 |
| `StopLowestPriority` | 우선순위 낮은 정지 |

---

## 7. USoundMix (Mix Profile)

```cpp
// 게임 상태에 따라 Sound Class Volume 조절
// 예: 메뉴 열면 BGM 줄이고 UI 키우기

// 활성
UGameplayStatics::PushSoundMixModifier(this, MenuSoundMix);

// 비활성
UGameplayStatics::PopSoundMixModifier(this, MenuSoundMix);

// MenuSoundMix.uasset = 어떤 SoundClass Volume 변경할지 정의
```

---

## 8. USoundAttenuation (3D 감쇠)

```cpp
// SoundAttenuation.h
class USoundAttenuation : public UObject
{
    UPROPERTY(EditAnywhere)
    FSoundAttenuationSettings Attenuation;
    // - DistanceAlgorithm: Linear / Logarithmic / Inverse / LogReverse / NaturalSound
    // - AttenuationShape: Sphere / Capsule / Box / Cone
    // - InnerRadius / FalloffDistance
    // - bSpatialize             : 3D 위치 활성
    // - SpatializationAlgorithm : Default / HRTF / Object-Based
    // - bAttenuateWithLPF       : 거리 LPF
    // - LPFRadiusMin/Max
    // - OcclusionTraceChannel   : Occlusion (벽 막힘)
    // - bEnableSendToReverbBus  : Reverb 전송
};
```

---

## 9. 5.x MetaSounds (Plugin — 절차적)

```cpp
// Plugin: MetaSound
// USoundCue 의 차세대 — Audio DSP 그래프 (BP 같은)
class UMetaSoundSource : public USoundBase {};

// 사용 — 런타임 파라미터 변경 (Vector / Scalar)
AudioComp->SetSound(MetaSoundSource);
AudioComp->SetFloatParameter(TEXT("Pitch"), 1.5f);
AudioComp->SetWaveParameter(TEXT("WaveInput"), NewWave);
```

> **5.x 신규 사운드 = MetaSounds 권장** — SoundCue 는 호환·기존만.

---

## 10. AudioComponent 사용 패턴 (런타임)

```cpp
// 컴포넌트 페어 — 자세한 = Components/AudioComponent

// 정적 — Spawn
UGameplayStatics::SpawnSoundAtLocation(this, GunfireSound, Location);
UGameplayStatics::SpawnSoundAttached(EngineSound, MeshComp, NAME_None);

// 컴포넌트 — 동적 (멤버 보관)
AudioComp->SetSound(NewSound);
AudioComp->Play();
AudioComp->FadeIn(/*Duration=*/ 1.f);
AudioComp->FadeOut(/*Duration=*/ 1.f, /*Volume=*/ 0.f);
AudioComp->Stop();

// MetaSound 파라미터 (5.x)
AudioComp->SetFloatParameter(TEXT("Pitch"), 1.5f);
```

---

## 11. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|-----|
| 1 | 매 발사 SFX `SpawnSoundAttached` 직접 | Concurrency 활성 + MaxCount = 4 (16개 동시 재생 회피) |
| 2 | BGM = `LoadingBehavior::ForceInline` | LoadOnDemand + Streaming (메모리 절감) |
| 3 | UI Sound = SoundClass = SFX | UI SoundClass 분리 (게임 일시정지 시도 UI 음 들리게) |
| 4 | SoundCue 의 `ConcurrencySet` 비활성 | 무기 / 발자국 등 모두 Concurrency 의무 |
| 5 | 3D Sound 가 Attenuation 없음 | Sphere Attenuation 추가 (거리 감쇠) |
| 6 | 매 프레임 `SetFloatParameter` 호출 | 변경 시만 — 효율 |
| 7 | Constructor 안 `LoadObject<USoundBase>` | UPROPERTY EditAnywhere + BP 지정 또는 Soft |
| 8 | `OnAudioFinished` 콜백 첫 줄 스코프 누락 | `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 |
| 9 | 🚨 `TObjectIterator<USoundBase>` | UAssetManager + AssetRegistry ([`09_GlobalIteratorPolicy.md`](../../../references/09_GlobalIteratorPolicy.md)) |
| 10 | 🚨 자주 재생 SFX PreLoad 안 함 | Match Start `PreloadPrimaryAssets` ([`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md)) |

---

## 12. 체크리스트

- [ ] 모든 SoundBase = SoundClass 지정 (Music / SFX / Voice / UI)
- [ ] 자주 재생 사운드 = Concurrency 적용 (MaxCount + ResolutionRule)
- [ ] 3D Sound = Attenuation 의무
- [ ] BGM = LoadingBehavior = LoadOnDemand + bStreaming = true
- [ ] 자주 SFX = LoadingBehavior = RetainOnLoad
- [ ] SoundClass 트리 (Master → SFX/Music/Voice/UI) 정의
- [ ] SoundMix 사용 (메뉴 열면 BGM Duck)
- [ ] 5.x = MetaSounds 사용 (SoundCue 는 legacy)
- [ ] 🚨 6대 정책 + 어셋 로드 정책

---

## 13. 관련 sub-skill

- [`AssetClasses/SKILL.md`](../SKILL.md) — 메인
- [`Components/AudioComponent`](../../Components/references/AudioComponent.md) — 호스트 컴포넌트 (Audio + ForceFeedback + 5.x ISoundParameterController)
- 교차: 🎯 [`11_AssetLoadingPolicy.md`](../../../references/11_AssetLoadingPolicy.md) (USoundWave Streaming + 자주 SFX PreLoad)

---

## 14. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-05 | 최초 작성. **USoundBase 418** (SoundClass / Concurrency / Attenuation / Duration / GetConcurrencyHandles). **USoundCue 379** (FirstNode + SoundNode 10종 — WavePlayer/Random/Attenuation/Concatenator/Mixer/Looping/Delay/Modulator/Branch/Oscillator + USoundCueTemplate 5.x). **USoundWave 1,822** (NumChannels / SampleRate / CompressedFormatData / **ESoundWaveLoadingBehavior 4종** — RetainOnLoad/PrimeOnLoad/LoadOnDemand/ForceInline / Streaming bStreaming + StreamingPriority / USoundWaveProcedural). **USoundClass** (Volume / Pitch / LPF / 계층 트리).