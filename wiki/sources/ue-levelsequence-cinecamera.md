---
type: source
title: "UE LevelSequence — CineCamera (시네마틱 카메라)"
slug: ue-levelsequence-cinecamera
source_path: raw/ue-wiki-llm/skills/LevelSequence/references/CineCamera.md
source_kind: text
source_date: 2026-05-13
ingested: 2026-05-14
last_updated: 2026-05-15
related_concepts:
  - "[[concepts/Profiling-Scope-Rule]]"
tags: [ue, levelsequence, cinecamera, enriched, verified]
citation_disclosure: "🟢 13 / 🟡 3 / 🔴 1 · raw verified · Cycle #13.4 enrich"
---

# UE LevelSequence — CineCamera

> Source: [[raw/ue-wiki-llm/skills/LevelSequence/references/CineCamera.md]] (444L)
> Parent: [[sources/ue-levelsequence-skill]] · 위치: `Engine/Source/Runtime/CinematicCamera/Public/` (6 헤더)

## 1. Summary

🟢 실 세계 카메라 시뮬레이션 — Filmback (필름) + Lens (Focal Length / Aperture) + Focus (Manual / Tracking) + Camera Rig (Crane / Rail). `UCineCameraComponent` (`UCameraComponent` 자손) + `ACineCameraActor`. LevelSequence CameraCut Track 페어. 5.x = DoF 자동 + CineCameraSettings 자산.

## 2. Key claims

### 2.1 UCineCameraComponent 9 핵심 필드 🟢 (raw §1 — CineCameraComponent.h:33-92)

```cpp
UCLASS(HideCategories=(CameraSettings), ClassGroup=Camera,
       meta=(BlueprintSpawnableComponent), Blueprintable)
class UCineCameraComponent : public UCameraComponent
{
    UPROPERTY(Interp, BlueprintSetter=SetFilmback, EditAnywhere)
    FCameraFilmbackSettings Filmback;            // [1] 필름 사이즈

    UPROPERTY(Interp, BlueprintSetter=SetLensSettings, EditAnywhere)
    FCameraLensSettings LensSettings;            // [2] 렌즈

    UPROPERTY(Interp, BlueprintSetter=SetFocusSettings, EditAnywhere)
    FCameraFocusSettings FocusSettings;          // [3] 포커스

    UPROPERTY(Interp, BlueprintSetter=SetCropSettings, EditAnywhere)
    FCameraCropSettings CropSettings;            // [4] 5.x Crop

    UPROPERTY(Interp, BlueprintSetter=SetCurrentFocalLength)
    float CurrentFocalLength;                    // [5] mm

    UPROPERTY(Interp, BlueprintSetter=SetCurrentAperture)
    float CurrentAperture;                       // [6] f-stop

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    float CurrentFocusDistance;                  // [7] cm (Read-only)

    UPROPERTY(Interp, EditAnywhere)
    float CurrentHorizontalFOV;                  // [8] FOV

    UPROPERTY(Interp, BlueprintSetter=SetCustomNearClippingPlane, AdvancedDisplay)
    float CustomNearClippingPlane;               // [9] 옵션
};
```

### 2.2 FCameraFilmbackSettings + 6 프리셋 🟢 (raw §2)

```cpp
struct FCameraFilmbackSettings {
    UPROPERTY(Interp) float SensorWidth = 24.89f;   // Super 35 (기본)
    UPROPERTY(Interp) float SensorHeight = 18.67f;
    UPROPERTY(VisibleAnywhere) float SensorAspectRatio;  // Read-only 자동
};
```

| 프리셋 | W × H (mm) | 비고 |
|--------|-----------|------|
| Super 35 ⭐ | 24.89 × 18.67 | 디지털 영화 표준 |
| 16mm | 10.26 × 7.49 | 작은 센서 |
| 35mm Film | 35 × 24 | 사진 |
| 65mm | 52.45 × 23.34 | IMAX 유사 |
| 8K Vista Vision | 37.72 × 25.18 | 큰 센서 |
| Custom | 사용자 | 임의 |

### 2.3 FCameraLensSettings 🟢 (raw §3)

```cpp
struct FCameraLensSettings {
    float MinFocalLength = 4.0f, MaxFocalLength = 1000.0f;    // mm
    float MinFStop = 1.2f, MaxFStop = 22.0f;                  // f-stop
    int32 DiaphragmBladeCount = 7;                            // 보케 모양
    float MinimumFocusDistance = 15.0f;                       // cm
};
```

| Focal | 효과 | 사용 |
|-------|------|------|
| 14~24mm | 광각 / 왜곡 | 풍경 / 액션 |
| 35~50mm | 표준 (인간 시야) | 대화 |
| 85~135mm | 망원 / DoF 강 | 클로즈업 |
| 200mm+ | 초망원 / 압축감 | 야생 |

| f-stop | DoF | 빛 |
|--------|-----|-----|
| f/1.2~1.8 | 매우 얕음 (배경 흐림) | 많음 |
| f/2.8~4 | 얕음 | 중간 |
| f/5.6~8 | 보통 | 보통 |
| f/11~22 | 깊음 | 적음 |

### 2.4 FCameraFocusSettings + 4 Method 🟢 (raw §4)

```cpp
struct FCameraFocusSettings {
    ECameraFocusMethod FocusMethod = Manual;
    float ManualFocusDistance = 100000.0f;                      // cm (1000m 기본)
    FCameraTrackingFocusSettings TrackingFocusSettings;
    bool bSmoothFocusChanges = false;
    float FocusSmoothingInterpSpeed = 8.0f;
};
```

`ECameraFocusMethod` 4종 🔴 (enum grep 필요):
- `DoNotOverride` — DoF 사용 X
- `Manual` — 거리 직접 (cm) + Sequencer Interp
- `Tracking` ⭐ — 액터 자동 추적 (Component/Socket/Offset)
- `Disable` 5.x — DoF 완전 비활성

```cpp
// Tracking Focus 표준
FCameraTrackingFocusSettings T;
T.ActorToTrack = HeroActor;
T.ComponentName = TEXT("Head");                  // 본/컴포넌트
T.RelativeOffset = FVector::ZeroVector;
CineCamera->FocusSettings.FocusMethod = ECameraFocusMethod::Tracking;
CineCamera->FocusSettings.TrackingFocusSettings = T;
```

### 2.5 ACineCameraActor 🟢 (raw §6)

```cpp
UCLASS()
class ACineCameraActor : public ACameraActor
{
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, meta=(AllowPrivateAccess="true"))
    TObjectPtr<UCineCameraComponent> CineCameraComponent;
};
```

Level 안 배치 시 자동 CineCameraComponent 보유. Sequencer CameraCut Track 으로 활성 카메라 전환.

### 2.6 Camera Rig 2종 🟡 (raw §5 — grep-listed)

| Rig | Interp 가능 속성 | 용도 |
|-----|-----------------|------|
| `ACameraRig_Crane` | CranePitch / CraneYaw / CraneArmLength | 크레인 회전 |
| `ACameraRig_Rail` | CurrentPositionOnRail (0.0~1.0) + Spline | Spline 경로 추종 |

### 2.7 LevelSequence 통합 흐름 🟢 (raw §7)

```
Sequencer:
1. + Track → ACineCameraActor 바인딩 (Possessable)
2. 안에 + Track:
   ├── Transform / FocalLength / Aperture / Filmback (Interp)
   └── FocusSettings.ManualFocusDistance
3. 시퀀스 루트의 CameraCut Track:
   └── [0~120] → Cam_01, [120~240] → Cam_02 ...
```

### 2.8 5.x 신규 — UCineCameraSettings + CineCameraRigs 🟡

```cpp
UCLASS(BlueprintType, Blueprintable)
class UCineCameraSettings : public UObject
{
    // 프로젝트 별 Filmback / Lens 프리셋 자산 — Sequencer 드롭다운
};
```

`Plugins/Experimental/CineCameraRigs/` 5.x — Studio LED Wall / Virtual Production 용.

### 2.9 5 시나리오 🟢 (raw §9)

| # | 시나리오 | 설정 |
|---|---------|------|
| 1 | 대화 클로즈업 | 85mm / f/2.8 / Tracking(Head) / Super 35 |
| 2 | 액션 광각 | 24mm / f/5.6 / Manual(10m) / Rail |
| 3 | 보스 등장 | 135→50mm Interp / f/1.4→f/8 / Crane Pitch |
| 4 | CameraCut 전환 | Wide → Closeup → OverShoulder |
| 5 | Mobile 최적 | FocusMethod=Disable / MinFStop=5.6 |

## 3. 함정 10 🟢 (raw §10)

| # | 함정 | 정답 |
|---|------|------|
| 1 | UPROPERTY `Interp` 누락 → Sequencer X | `Interp` meta 추가 |
| 2 | Manual Focus 단위 혼동 (cm vs m) | **cm** — 100000 = 1000m |
| 3 | Mobile + DoF 활성 → 60fps 미달 | `Disable` 또는 `bUseDoF=false` |
| 4 | SensorAspectRatio 수동 변경 | 자동 계산 (Read-only) |
| 5 | f-stop 범위 위반 | MinFStop / MaxFStop 검증 |
| 6 | Tracking ActorToTrack nullptr 크래시 | IsValid 검사 |
| 7 | Crane 안 카메라 직접 Transform | 리그 속성만 (CranePitch/Yaw/ArmLength) |
| 8 | DoF 품질 기본 추측 | `r.DepthOfFieldQuality=4` 권장 |
| 9 | CameraCut 즉시 전환 추측 | Section Easing Blend 가능 (5.x) |
| 10 | CineCamera Component 직접 NewObject | ACineCameraActor 통한 접근 |

## 4. 체크리스트 🟢 (raw §11)

- [ ] CineCameraActor = Level 배치 또는 Sequencer Spawnable
- [ ] UPROPERTY `Interp` meta (Sequencer 추적)
- [ ] Focal Length = mm / Aperture = f-stop / Focus = cm
- [ ] Mobile = DoF 비활성 분기
- [ ] Tracking = ActorToTrack IsValid
- [ ] Crane = 속성만 변경
- [ ] Filmback Preset = `UCineCameraSettings` 자산
- [ ] CameraCut Section Easing (5.x Blend)

## 5. 신뢰도 🟢 (raw §12)

| 항목 | tier | 출처 |
|------|------|------|
| UCineCameraComponent 핵심 필드 | 🟢 verified | `CineCameraComponent.h:33-92` |
| `Interp` UPROPERTY meta | 🟢 verified | `:37,65,69,80` |
| BlueprintSetter (SetFilmback etc) | 🟢 verified | `:40,47,54,61,72` |
| FCameraFilmback/Lens/Focus 필드 | 🟡 grep-listed | `CineCameraSettings.h` grep |
| ACameraRig_Crane/Rail API | 🟡 grep-listed | 헤더 존재 |
| ECameraFocusMethod 4종 | 🔴 inferred | enum grep 필요 |
| 5.x CineCameraSettings UCLASS | 🟢 verified | 헤더 존재 |

## 6. Cross-link

- Parent: [[sources/ue-levelsequence-skill]]
- 페어: [[sources/ue-levelsequence-tracks]] (CameraCutTrack §3) · [[sources/ue-levelsequence-levelsequenceplayer]] (OnCameraCut 콜백)
- 자산: [[sources/ue-assetclasses-camera]] (UCameraAnimationSequence 5.x)
- 컴포넌트 베이스: [[sources/ue-components-cameracomponent]] (UCameraComponent)
- Render 페어: [[sources/ue-render-postprocess]] (DoF 패스)
