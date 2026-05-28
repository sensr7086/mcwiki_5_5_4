---
name: ue-metasound
description: UE 5.7.4 MetaSound 위키. UMetaSoundSource + UMetaSoundPatch + Graph 노드 + Trigger/Audio/Wave 데이터 타입 + Parameter Pack 런타임 제어 + AudioComponent 페어. Cascade-style USoundCue 대비 5.x DSP 그래프 표준. AssetClasses/Audio sub-skill의 5.x 페어.
---

# MetaSound — UE 5.7.4 5.x DSP 그래프 사운드 시스템

> **카테고리** — Tier 1 (Audio — 5.x 신규 표준)
> **대표 클래스** — `UMetaSoundSource`, `UMetaSoundPatch`, `FMetasoundFrontendDocument`, `IMetaSoundParameterControlled`
> **트리거 키워드** — Metasound, MetaSound, MetasoundSource, IMetaSoundParameterControlled, SetTriggerParameter, MetaSoundEditor

본 sub-skill은 [`skills/AssetClasses/references/Audio.md`](../SKILL.md)의 5.x 페어. USoundCue / USoundWave는 호환만, 신규 사운드는 MetaSound 권장.

---

## 1. MetaSound 자산 종류

| 자산 | 베이스 | 용도 |
|------|--------|------|
| `UMetaSoundSource` | `USoundBase` | 재생 가능한 단일 사운드 (USoundCue 대체) |
| `UMetaSoundPatch` | `UObject` | 재사용 그래프 — Source가 import |
| `UMetaSoundSourcePreset` / Preset | 인스턴스 — Parameter override | 같은 그래프, 다른 파라미터 |

> 🚨 **MetaSoundSource = USoundBase 자손** — `UAudioComponent::SetSound(MetaSoundSource)` 그대로 사용. Cue처럼 다룸 [grep-listed].

---

## 2. 그래프 구조

```
[Inputs] ──> [Wave Player] ──> [Mix] ──> [LowPassFilter] ──> [Outputs]
                                ↑
                            [Trigger Inputs]
```

| 핀 타입 | 의미 |
|---------|------|
| `Trigger` | 이벤트 — Play/Stop/Beat |
| `Audio` | 오디오 신호 (Float[]) |
| `Wave` | USoundWave 참조 |
| `Float / Int / Bool / String` | 파라미터 |
| `Time` | 초 단위 |

---

## 3. 런타임 파라미터 제어 (C++)

```cpp
UAudioComponent* AC = GetAudioComponent();
AC->SetSound(MyMetaSoundSource);
AC->SetTriggerParameter("StartLoop");      // Trigger
AC->SetFloatParameter("Pitch", 1.2f);       // Float
AC->SetWaveParameter("WaveAsset", MyWave); // Wave
AC->Play();
```

또는 `IMetaSoundParameterControlled` 인터페이스 직접 호출:

```cpp
// 5.x — UAudioComponent가 IMetaSoundParameterControlled 구현
TArray<FAudioParameter> Params;
Params.Emplace(FAudioParameter("Pitch", 1.2f));
AC->SetParameters_Blueprint(Params);
```

> 🚨 파라미터 이름 타이포 — 컴파일 안 잡힘. `FName` 상수 const 권장 [grep-listed].

---

## 4. Parameter Pack (5.x — 효율 갱신)

매 프레임 다수 파라미터 갱신 시 — 단일 호출로 묶음:

```cpp
TSharedRef<FAudioParameterCollectionInstance> Pack = ...;
Pack->SetParameter("Pitch", 1.2f);
Pack->SetParameter("Volume", 0.8f);
Pack->Apply();  // 한 번만
```

→ 매 프레임 N개 파라미터 갱신 비용 → 1 RPC급 [inferred — 일반 측정치].

---

## 5. AudioComponent 페어 — `skills/Components/AudioComponent`

```cpp
UMyComp::UMyComp()
{
    AC = CreateDefaultSubobject<UAudioComponent>(TEXT("AC"));
    AC->bAutoActivate = false;
    AC->SetIsReplicated(false);  // 사운드는 보통 클라 측만
}

void UMyComp::PlayHit()
{
    AC->SetSound(HitMetaSound);
    AC->SetFloatParameter("Intensity", LastHitForce);
    AC->Play();
}
```

> 🚨 **데디 서버는 사운드 NOP** — `BlueprintCosmetic` / `IsRunningDedicatedServer` 가드 의무 (`skills/Networking/SKILL.md §7`).

---

## 6. Concurrency / Attenuation / SoundClass

| 자산 | 역할 |
|------|------|
| `USoundConcurrency` | 동시 재생 수 제한 + Resolution Rule |
| `USoundAttenuation` | 거리 감쇠 + 3D 위치화 |
| `USoundClass` | 그룹 볼륨 / Mix |

MetaSoundSource도 일반 USoundBase처럼 Attenuation/Concurrency 적용.

> 🎯 `12_AssetOptimizationPolicy §Audio` — Concurrency Resolution Rule 5종 + Attenuation 의무 적용.

---

## 7. 디버깅

| 도구 | 용도 |
|------|------|
| MetaSound Editor (Editor 전용) | Live Preview + Auralize |
| `Audio Insights` (5.x) | 런타임 그래프 시각화 |
| `stat SoundCues` / `stat Audio` | 활성 음원 수 |
| `au.Debug.Sounds 1` | 콘솔 디버그 |

---

## 8. Cascade(Cue)/MetaSound 마이그레이션

| 기존 | 5.x |
|------|-----|
| `USoundCue` Random | MetaSound Random Play 노드 |
| `USoundCue` Concatenator | MetaSound Sequence + Trigger |
| `USoundCue` Parameter | MetaSound Input + `SetFloatParameter` |
| Cue Modulator | MetaSound LFO / Envelope |

> 🚨 MetaSound 자체로 작성 권장. Cue 자동 변환은 없음 [grep-listed].

---

## 9. 정책 의무

- 🚨 `04_OverrideIndex` — `UAudioComponent` 자손 시 Super 호출
- 🚨 `07_ProfilingScopeRule` — `Play()` 호출 측정
- 🎯 `12_AssetOptimizationPolicy §Audio` — Concurrency / Attenuation / Significance
- 🚨 `skills/Networking/SKILL.md` — 데디 서버 사운드 NOP

---

## 10. 외부 검증

- 위키에 없는 MetaSound 노드 → docs.unrealengine.com `MetaSound` 섹션
- Quartz (5.x 음악 동기화) → 위키에 없음, `[inferred]`
- AudioModulation Plugin → 위키에 없음

---

## 관련

- [`skills/AssetClasses/references/Audio.md`](../SKILL.md) — Audio 자산 전체
- [`skills/Components/references/AudioComponent.md`](../../../Components/references/AudioComponent.md) — 컴포넌트 페어
- [`skills/Networking/SKILL.md`](../../../Networking/SKILL.md) — 데디 서버 NOP
- [`references/12_AssetOptimizationPolicy.md`](../../../../references/12_AssetOptimizationPolicy.md)
- [`references/19_ExternalSourcesGuide.md`](../../../../references/19_ExternalSourcesGuide.md)
