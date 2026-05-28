---
name: levelsequence-cinecamera
description: UCineCameraComponent + ACineCameraActor + FCameraFilmbackSettings / FCameraLensSettings / FCameraFocusSettings + ACameraRig_Crane / ACameraRig_Rail. Real-life camera 시뮬레이션 (Filmback 35mm/65mm, Aperture f-stop, Focal Length mm, Manual/Tracking Focus). LevelSequence Tracks/CameraCutTrack 페어.
---

# LevelSequence/CineCamera — 시네마틱 카메라

> **위치 (verified)**:
> - **UCineCameraComponent** — `Engine/Source/Runtime/CinematicCamera/Public/CineCameraComponent.h:21` (UE 5.5 — 268 lines)
> - **ACineCameraActor** — `Engine/Source/Runtime/CinematicCamera/Public/CineCameraActor.h`
> - **UCineCameraSettings** — `Engine/Source/Runtime/CinematicCamera/Public/CineCameraSettings.h`
> - **ACameraRig_Crane** — `Engine/Source/Runtime/CinematicCamera/Public/CameraRig_Crane.h`
> - **ACameraRig_Rail** — `Engine/Source/Runtime/CinematicCamera/Public/CameraRig_Rail.h`
>
> **요지**: 실 세계 카메라 시뮬레이션 — Filmback (필름 사이즈) + Lens (Focal Length / Aperture) + Focus (Manual / Tracking). LevelSequence 의 CameraCut Track 과 페어.

---

## 🚨 공통 정책

| 정책 | 적용 |
|------|------|
| 🚨 Component 베이스 | `UCineCameraComponent : public UCameraComponent` — Components/CameraComponent 정책 상속 |
| 🚨 5.x DoF | 자동 Depth of Field — `r.DepthOfFieldQuality=4` 권장 |
| 🚨 Mobile | DoF 비싸다 — Mobile = `bUseDoF=false` 분기 |
| 🚨 [`07_ProfilingScopeRule`](../../../references/07_ProfilingScopeRule.md) | Tick / Focus Track 콜백 첫 줄 스코프 |

---

## 1. UCineCameraComponent 구조 [verified — CineCameraComponent.h:33-92]

```cpp
UCLASS(HideCategories=(CameraSettings), ClassGroup=Camera,
       meta=(BlueprintSpawnableComponent), Blueprintable)
class CINEMATICCAMERA_API UCineCameraComponent : public UCameraComponent
{
public:
    // [1] Filmback (필름 사이즈) ⭐
    UPROPERTY(Interp, BlueprintSetter=SetFilmback, EditAnywhere, BlueprintReadWrite,
              Category="Current Camera Settings")
    FCameraFilmbackSettings Filmback;

    UFUNCTION(BlueprintSetter)
    void SetFilmback(const FCameraFilmbackSettings& NewFilmback);

    // [2] Lens Settings (렌즈) ⭐
    UPROPERTY(EditAnywhere, BlueprintSetter=SetLensSettings, BlueprintReadWrite,
              Category="Current Camera Settings")
    FCameraLensSettings LensSettings;

    UFUNCTION(BlueprintSetter)
    void SetLensSettings(const FCameraLensSettings& NewLensSettings);

    // [3] Focus Settings (포커스) ⭐⭐
    UPROPERTY(EditAnywhere, BlueprintSetter=SetFocusSettings, BlueprintReadWrite,
              Category="Current Camera Settings")
    FCameraFocusSettings FocusSettings;

    UFUNCTION(BlueprintSetter)
    void SetFocusSettings(const FCameraFocusSettings& NewFocusSettings);

    // [4] Crop Settings (5.x — 안전 영역)
    UPROPERTY(EditAnywhere, BlueprintSetter=SetCropSettings, BlueprintReadWrite,
              Category="Current Camera Settings")
    FCameraCropSettings CropSettings;

    UFUNCTION(BlueprintSetter)
    void SetCropSettings(const FCameraCropSettings& NewCropSettings);

    // [5] Focal Length (mm) ⭐⭐ — Sequencer Interp 가능
    UPROPERTY(Interp, BlueprintSetter=SetCurrentFocalLength, EditAnywhere, BlueprintReadWrite,
              Category="Current Camera Settings")
    float CurrentFocalLength;

    // [6] Aperture (f-stop) ⭐⭐
    UPROPERTY(Interp, BlueprintSetter=SetCurrentAperture, EditAnywhere, BlueprintReadWrite,
              Category="Current Camera Settings")
    float CurrentAperture;

    UFUNCTION(BlueprintSetter)
    void SetCurrentAperture(float NewAperture);

    // [7] Current Focus Distance (Read-only — FocusSettings 통한 제어)
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Current Camera Settings")
    float CurrentFocusDistance;

    // [8] Current FOV
    UPROPERTY(Interp, EditAnywhere, BlueprintReadWrite, Category="Current Camera Settings")
    float CurrentHorizontalFOV;

    // [9] Custom Near Clipping Plane (옵션)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, AdvancedDisplay, Category="Current Camera Settings",
              meta=(InlineEditConditionToggle))
    bool bOverride_CustomNearClippingPlane;

    UPROPERTY(Interp, BlueprintSetter=SetCustomNearClippingPlane, EditAnywhere, BlueprintReadWrite,
              AdvancedDisplay, Category="Current Camera Settings",
              meta=(UIMin="0.00001", ClampMin="0.00001", editcondition="bOverride_CustomNearClippingPlane", Units=cm))
    float CustomNearClippingPlane;
};
```

---

## 2. FCameraFilmbackSettings (필름 사이즈)

```cpp
USTRUCT(BlueprintType)
struct FCameraFilmbackSettings
{
    // 가로 (mm)
    UPROPERTY(Interp, EditAnywhere, BlueprintReadWrite, Category="Filmback")
    float SensorWidth = 24.89f;       // Super 35 (기본)

    // 세로 (mm)
    UPROPERTY(Interp, EditAnywhere, BlueprintReadWrite, Category="Filmback")
    float SensorHeight = 18.67f;      // Super 35

    // 종횡비 (Read-only — Width/Height 자동 계산)
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Filmback")
    float SensorAspectRatio;
};
```

### 2.1 일반적 필름 프리셋

| 프리셋 | Sensor Width × Height | 비고 |
|--------|----------------------|------|
| Super 35 | 24.89 × 18.67 mm | 디지털 영화 표준 |
| 16mm | 10.26 × 7.49 mm | 작은 센서 |
| 35mm Film | 35 × 24 mm | 사진 |
| 65mm | 52.45 × 23.34 mm | IMAX 유사 |
| 8K Vista Vision | 37.72 × 25.18 mm | 큰 센서 |
| Custom | 사용자 입력 | 임의 값 |

> Sequencer 안 Filmback Preset = `UCineCameraSettings` 자산 안 정의.

---

## 3. FCameraLensSettings (렌즈)

```cpp
USTRUCT(BlueprintType)
struct FCameraLensSettings
{
    // Focal Length 범위 (mm)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Lens")
    float MinFocalLength = 4.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Lens")
    float MaxFocalLength = 1000.0f;

    // Aperture 범위 (f-stop)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Lens")
    float MinFStop = 1.2f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Lens")
    float MaxFStop = 22.0f;

    // Aperture 블레이드 수 (보케 모양)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Lens")
    int32 DiaphragmBladeCount = 7;

    // Diaphragm Blade Count Range
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Lens")
    float MinimumFocusDistance = 15.0f;        // cm
};
```

### 3.1 Focal Length 효과 (mm)

| Focal Length | 효과 | 사용 시점 |
|-------------|------|----------|
| 14~24mm | 광각 — 광활 / 왜곡 | 풍경 / 액션 |
| 35~50mm | 표준 — 인간 시야 | 대화 / 일반 |
| 85~135mm | 망원 — 인물 / DoF 강함 | 클로즈업 / 인터뷰 |
| 200mm+ | 초망원 — 압축감 | 야생 / 스포츠 |

### 3.2 Aperture (f-stop) 효과

| f-stop | DoF | 빛 양 |
|--------|-----|------|
| f/1.2 ~ f/1.8 | 매우 얕음 (배경 흐림) | 많음 |
| f/2.8 ~ f/4 | 얕음 | 중간 |
| f/5.6 ~ f/8 | 보통 | 보통 |
| f/11 ~ f/22 | 깊음 (모두 선명) | 적음 |

---

## 4. FCameraFocusSettings (포커스) ⭐⭐

```cpp
USTRUCT(BlueprintType)
struct FCameraFocusSettings
{
    // Focus Method
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Focus Settings")
    ECameraFocusMethod FocusMethod = ECameraFocusMethod::Manual;

    // Manual Focus (cm)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Focus Settings",
              meta=(EditCondition="FocusMethod==ECameraFocusMethod::Manual"))
    float ManualFocusDistance = 100000.0f;       // cm (1000m 기본)

    // Tracking Focus (액터 추적)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Focus Settings",
              meta=(EditCondition="FocusMethod==ECameraFocusMethod::Tracking"))
    FCameraTrackingFocusSettings TrackingFocusSettings;

    // Smoothing
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Focus Settings")
    bool bSmoothFocusChanges = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Focus Settings",
              meta=(EditCondition="bSmoothFocusChanges"))
    float FocusSmoothingInterpSpeed = 8.0f;
};
```

### 4.1 ECameraFocusMethod 4종

| Method | 설명 |
|--------|------|
| `DoNotOverride` | DoF 사용 X (기본 카메라처럼) |
| `Manual` | 거리 직접 입력 (cm) — Sequencer 안 Interp |
| `Tracking` ⭐ | 액터 자동 추적 — Component / Socket / Offset |
| `Disable` | 5.x — DoF 완전 비활성 |

### 4.2 Tracking Focus 표준

```cpp
FCameraTrackingFocusSettings TrackSettings;
TrackSettings.ActorToTrack = HeroActor;          // 추적 대상
TrackSettings.ComponentName = TEXT("Head");      // 본 / 컴포넌트 이름 (옵션)
TrackSettings.RelativeOffset = FVector(0, 0, 0); // 오프셋
TrackSettings.bDrawDebugTrackingFocusPoint = false;

CineCamera->FocusSettings.FocusMethod = ECameraFocusMethod::Tracking;
CineCamera->FocusSettings.TrackingFocusSettings = TrackSettings;
```

---

## 5. ACameraRig_Crane / ACameraRig_Rail [grep-listed]

### 5.1 Crane (크레인 — 회전 베이스)

```cpp
// ACameraRig_Crane — 크레인 형태 카메라 리그
// - CranePitch / CraneYaw / CraneArmLength 조작 가능
// - 카메라는 크레인 끝에 부착

// Sequencer 안 Interp 가능 속성:
// - CranePitch (위/아래)
// - CraneYaw (좌/우)
// - CraneArmLength (팔 길이)
```

### 5.2 Rail (레일 — 경로 추종)

```cpp
// ACameraRig_Rail — Spline 따라 이동
// - RailLocationsArray / RailSpline (스플라인 컴포넌트)
// - CurrentPositionOnRail (0.0 ~ 1.0)

// 시퀀스 안 카메라가 스플라인 따라 매끄럽게 이동
```

---

## 6. ACineCameraActor

```cpp
UCLASS()
class ACineCameraActor : public ACameraActor
{
public:
    // 자동으로 UCineCameraComponent 보유
    UPROPERTY(Category=CineCameraActor, VisibleAnywhere, BlueprintReadOnly,
              meta=(AllowPrivateAccess="true"))
    TObjectPtr<UCineCameraComponent> CineCameraComponent;

    // CameraComponent 와 호환 (ACameraActor 자손)
};
```

> Level 안 배치 시 자동으로 CineCameraComponent 보유. Sequencer 안 CameraCut Track 으로 활성 카메라 전환.

---

## 7. LevelSequence 안 통합 흐름

```
Sequencer 안:
1. + Track → "Cine Camera Actor" 검색 → Level 안 ACineCameraActor 바인딩 (Possessable)
2. CineCameraActor Possessable 안 + Track:
   ├── Transform Track (위치 / 회전)
   ├── Focal Length Track (Interp UPROPERTY)
   ├── Aperture Track (Interp UPROPERTY)
   ├── Filmback Track (선택)
   └── Focus Settings → Manual Focus Distance Track
3. 시퀀스 루트의 CameraCut Track:
   └── [0~120 프레임] → CineCamera_01 활성
   └── [120~240 프레임] → CineCamera_02 활성
```

---

## 8. 5.x 신규 — CineCameraSettings + CineCameraRigs

### 8.1 UCineCameraSettings (Filmback Preset 자산)

```cpp
// 프로젝트 별 Filmback Preset 모음
UCLASS(BlueprintType, Blueprintable)
class UCineCameraSettings : public UObject
{
    // FilmbackPresets / LensPresets 등록
    // Sequencer 안 드롭다운 자동 표시
};
```

### 8.2 CineCameraRigs Plugin (Experimental — 5.x)

`Plugins/Experimental/CineCameraRigs/` — 스튜디오용 카메라 리그 (Studio LED Wall / Virtual Production).

---

## 9. 시나리오 5종

### 9.1 대화 클로즈업

```
CineCamera 설정:
- Focal Length: 85mm
- Aperture: f/2.8 (얕은 DoF — 배경 흐림)
- Focus: Tracking (Hero->Head Socket)
- Filmback: Super 35
```

### 9.2 액션 시퀀스 (광각)

```
CineCamera 설정:
- Focal Length: 24mm
- Aperture: f/5.6 (충분히 깊음)
- Focus: Manual (10m)
- Camera Rig: Rail (Spline 따라 추격)
```

### 9.3 보스 등장 (드라마틱)

```
CineCamera 설정:
- Focal Length: 135mm → 50mm (Interp — 줌 아웃)
- Aperture: f/1.4 → f/8 (Interp — DoF 깊어짐)
- Camera Rig: Crane (Pitch Up → Boss 클로즈)
```

### 9.4 카메라 전환 (CameraCut)

```
시퀀스 루트:
└── CameraCut Track
    ├── [0~60]   → Camera_Wide
    ├── [60~120] → Camera_Closeup
    └── [120~]   → Camera_Hero_OverShoulder
```

### 9.5 Mobile 최적화

```cpp
// Mobile = DoF 비활성
if (CurrentPlatform == EMobile)
{
    CineCamera->FocusSettings.FocusMethod = ECameraFocusMethod::Disable;
    CineCamera->LensSettings.MinFStop = 5.6f;  // 깊은 DoF 강제
}
```

---

## 10. 함정 & 안티패턴 (10종)

| # | 함정 | 정답 |
|---|------|------|
| 1 | UPROPERTY 안 `Interp` 누락 → Sequencer 트랙 자동 X | `Interp` meta 추가 |
| 2 | Manual Focus 거리 단위 혼동 (cm vs m) | **cm** — 100000 = 1000m |
| 3 | Mobile + DoF 활성 → 60fps 미달 | Mobile = `Disable` 또는 `bUseDoF=false` |
| 4 | Filmback 변경 후 Aspect Ratio 수동 변경 시도 | `SensorAspectRatio` = 자동 계산 (Read-only) |
| 5 | f-stop 1.2 미만 / 22 초과 입력 | LensSettings.MinFStop / MaxFStop 범위 검증 |
| 6 | Tracking Focus 액터 nullptr → 크래시 | TrackingFocusSettings.ActorToTrack IsValid 검사 |
| 7 | Crane 안 카메라 직접 Transform 변경 → 리그 깨짐 | Crane 속성만 변경 (CranePitch/Yaw/ArmLength) |
| 8 | 5.x DoF 품질 = 기본 추측 | `r.DepthOfFieldQuality=4` 권장 |
| 9 | CameraCut 변경 시 즉시 / Blend 추측 | Section Easing 으로 Blend 가능 (5.x) |
| 10 | CineCamera Component 직접 NewObject | Actor (ACineCameraActor) 통한 접근 |

---

## 11. 체크리스트

- [ ] CineCameraActor = Level 안 배치 (또는 Sequencer 안 Spawnable)
- [ ] UPROPERTY 안 `Interp` meta 확인 (Sequencer 추적 가능)
- [ ] Focal Length 단위 = mm
- [ ] Aperture 단위 = f-stop (1.2 ~ 22)
- [ ] Manual Focus 단위 = cm (10cm ~ 100000cm)
- [ ] Mobile = DoF 비활성 분기
- [ ] Tracking Focus = ActorToTrack IsValid 검사
- [ ] Crane = 속성만 변경 (Transform 직접 X)
- [ ] Filmback Preset = `UCineCameraSettings` 자산 사용
- [ ] CameraCut Section Easing 사용 (5.x Blend)

---

## 12. 신뢰도 태그

| 항목 | 신뢰도 | 검증 출처 |
|------|--------|----------|
| UCineCameraComponent 핵심 필드 (Filmback / LensSettings / FocusSettings / CurrentFocalLength / CurrentAperture / CurrentFocusDistance) | **[verified]** ✅ | `CineCameraComponent.h:33-92` (grep 매치) |
| UPROPERTY `Interp` meta | **[verified]** ✅ | `CineCameraComponent.h:37, 65, 69, 80` |
| BlueprintSetter 패턴 (SetFilmback / SetLensSettings / SetFocusSettings / SetCropSettings / SetCurrentAperture) | **[verified]** ✅ | `CineCameraComponent.h:40, 47, 54, 61, 72` |
| FCameraFilmbackSettings / FCameraLensSettings / FCameraFocusSettings 필드 | **[grep-listed]** ⚠ | 일반 명명 — `CineCameraSettings.h` grep 권장 |
| ACameraRig_Crane / ACameraRig_Rail API | **[grep-listed]** ⚠ | 헤더 존재 (`CameraRig_Crane.h` / `CameraRig_Rail.h`) |
| ECameraFocusMethod 4종 (DoNotOverride / Manual / Tracking / Disable) | **[inferred]** ❌ | UE 일반 — enum grep 필요 |
| 5.x CineCameraSettings UCLASS | **[verified]** ✅ | `CineCameraSettings.h` 헤더 존재 |

---

## 13. 관련

- [`../SKILL.md`](../SKILL.md) — LevelSequence 메인
- [`./Tracks.md`](./Tracks.md) — UMovieSceneCameraCutTrack §2
- [`./LevelSequencePlayer.md`](./LevelSequencePlayer.md) — OnCameraCut 콜백
- [`../../Components/references/CameraComponent.md`](../../Components/references/CameraComponent.md) — UCameraComponent 베이스
- [`../../AssetClasses/references/Camera.md`](../../AssetClasses/references/Camera.md) — UCameraAnimationSequence (관련 자산)
- [`../../Render/references/PostProcess.md`](../../Render/references/PostProcess.md) — DoF Render 패스

---

## 14. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-13 | 최초 작성. **UCineCameraComponent 9 핵심 필드 [verified]** + **Filmback / LensSettings / FocusSettings / CropSettings BlueprintSetter** + ECameraFocusMethod 4종 + Filmback 프리셋 6 + Focal Length 효과 4단 + Aperture DoF 효과 + Tracking Focus + ACameraRig_Crane / Rail + 시나리오 5종 + 함정 10. Engine 5.5.4 검증 — CineCameraComponent.h:33-92. |
