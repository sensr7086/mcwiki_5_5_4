---
type: source
title: "UE LevelSequence — FMovieScene3DTransformTrack × 9 FloatChannel lite 미러 (Sequencer 모듈 의존 회피 패턴)"
slug: ue-floatchannel-9-mirror
source_path: raw/ue-wiki-llm/skills/LevelSequence/references/FloatChannel-9-Mirror.md
source_kind: enriched
source_date: 2026-05-19
ingested: 2026-05-19
last_updated: 2026-05-19
cycle: 5p+5
tier: enriched
related_concepts:
  - "[[concepts/Slate-Paint-Cycle]]"
related_sources:
  - "[[sources/ue-levelsequence-tracks]]"
  - "[[sources/ue-levelsequence-moviescene]]"
  - "[[sources/ue-coreuobject-uobject]]"
trigger: "KMCProject MCComboEditor Phase 5p+7 — TransformSection 9 channel refactor (LocationX/Y/Z + RotationRoll/Pitch/Yaw + ScaleX/Y/Z, 단일 FTransform 키 → 9 FloatChannel) Sequencer 모듈 의존 회피 lite 미러. FMath::CubicInterp Catmull-Rom 정확."
tags: [ue, levelsequence, sequencer-lite, movieseen, transform-track, floatchannel, fmath-cubicinterp, catmull-rom, frotator-quaternion, keyframe-interpolation]
---

# UE LevelSequence — FMovieScene3DTransformTrack × 9 FloatChannel lite 미러

> Source: `Engine/Source/Runtime/MovieSceneTracks/Public/Tracks/MovieScene3DTransformTrack.h` + `MovieSceneFloatChannel.h` + `Engine/Math/UnrealMathUtility.h` L1212/L1226 (FMath::CubicInterp) + `Engine/Math/Rotator.h` L103/L568 (FRotator ctor) + KMCProject Phase 5p+7 실측 사례.

## 1. Summary

LevelSequence Sequencer 의 `UMovieScene3DTransformTrack` 는 9개 `FMovieSceneFloatChannel` (Location X/Y/Z + Rotation Roll/Pitch/Yaw + Scale X/Y/Z) 으로 transform 키프레임을 분리 저장. Sequencer 모듈 의존을 회피하면서 동일 모델을 가볍게 미러하는 패턴.

**핵심 차이점 (lite vs 풀스택)**:
- 풀스택: `FMovieSceneFloatChannel` 사용 → Sequencer 모듈 의존 + `FRichCurveKey` + 자동 Tangent 계산 (Auto / User / Break)
- lite: 자체 `FMCComboFloatKey` USTRUCT (Time + Value + per-key InterpMode) — Tangent 자동 Catmull-Rom (단순화)

## 2. 9 Channel 분리 모델

**Engine 권위**: `MovieSceneTracks/Public/Tracks/MovieScene3DTransformTrack.h` — `FMovieSceneFloatChannel Location[3]`, `Rotation[3]`, `Scale[3]` (또는 9 개별 멤버, Engine 버전별 차이 있음).

**lite 미러**:
```cpp
UCLASS(BlueprintType)
class UMyTransformSection : public UMySection
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Transform|Location")
    TArray<FMyFloatKey> LocationX;
    UPROPERTY(...) TArray<FMyFloatKey> LocationY;
    UPROPERTY(...) TArray<FMyFloatKey> LocationZ;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Transform|Rotation")
    TArray<FMyFloatKey> RotationRoll;
    UPROPERTY(...) TArray<FMyFloatKey> RotationPitch;
    UPROPERTY(...) TArray<FMyFloatKey> RotationYaw;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Transform|Scale")
    TArray<FMyFloatKey> ScaleX;
    UPROPERTY(...) TArray<FMyFloatKey> ScaleY;
    UPROPERTY(...) TArray<FMyFloatKey> ScaleZ;
};
```

## 3. FMyFloatKey USTRUCT — FRichCurveKey lite 미러

Engine `FRichCurveKey` (RichCurve.h) 는 Time + Value + ArriveTangent + LeaveTangent + InterpMode + TangentMode + TangentWeightMode. lite 미러는 Tangent 자동:

```cpp
UENUM(BlueprintType)
enum class EMyInterpMode : uint8
{
    Constant UMETA(DisplayName = "Constant (Step)"),
    Linear   UMETA(DisplayName = "Linear"),
    Cubic    UMETA(DisplayName = "Cubic (Hermite, Catmull-Rom Tangent 자동)"),
};

USTRUCT(BlueprintType)
struct FMyFloatKey
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FFrameNumber Time = FFrameNumber(0);

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Value = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    EMyInterpMode InterpMode = EMyInterpMode::Linear;
};
```

## 4. Cubic Hermite + Catmull-Rom Tangent 정확 공식

**Engine 권위**: `Engine/Source/Runtime/Core/Public/Math/UnrealMathUtility.h` L1212/L1226 — `FMath::CubicInterp(P0, T0, P1, T1, Alpha)` Hermite spline.

**Catmull-Rom Tangent 공식** (Engine `FRichCurve::EvalForTwoKeys` 패턴):
```
T_i = (P_{i+1} - P_{i-1}) * 0.5
```

**lite 구현**:
```cpp
case EMyInterpMode::Cubic:
{
    // 인접 prev/next key 안전 fallback (boundary clamp).
    const FMyFloatKey& Prev = (i > 0) ? Channel[i - 1] : A;
    const FMyFloatKey& Next = (i + 2 < KeyCount) ? Channel[i + 2] : B;
    const float T0 = (B.Value - Prev.Value) * 0.5f;
    const float T1 = (Next.Value - A.Value) * 0.5f;
    return FMath::CubicInterp(A.Value, T0, B.Value, T1, Alpha);
}
```

⚠ **Engine `FMath::CubicInterp` 시그니처** — 5 인자 (P0, T0, P1, T1, Alpha). 가짜 3 인자 (P0, P1, Alpha) 시그니처 없음. 6 인자 `(P0, P1, T0, T1, Alpha)` 순서 혼동 주의.

## 5. EvaluateAtFrame — 9 Channel → FTransform 재조합

**Engine `FRotator` ctor 순서**: `Rotator.h` L103/L568 — `FRotator(InPitch, InYaw, InRoll)` (Pitch first).

```cpp
FTransform UMyTransformSection::EvaluateAtFrame(FFrameNumber InLocalFrame) const
{
    const float LocX = EvaluateChannel(LocationX, InLocalFrame, 0.0f);
    const float LocY = EvaluateChannel(LocationY, InLocalFrame, 0.0f);
    const float LocZ = EvaluateChannel(LocationZ, InLocalFrame, 0.0f);

    const float Roll  = EvaluateChannel(RotationRoll,  InLocalFrame, 0.0f);
    const float Pitch = EvaluateChannel(RotationPitch, InLocalFrame, 0.0f);
    const float Yaw   = EvaluateChannel(RotationYaw,   InLocalFrame, 0.0f);

    const float SclX = EvaluateChannel(ScaleX, InLocalFrame, 1.0f);
    const float SclY = EvaluateChannel(ScaleY, InLocalFrame, 1.0f);
    const float SclZ = EvaluateChannel(ScaleZ, InLocalFrame, 1.0f);

    // ⭐ Engine 권위 FRotator(Pitch, Yaw, Roll) ctor 순서.
    const FRotator Rot(Pitch, Yaw, Roll);

    return FTransform(Rot.Quaternion(), FVector(LocX, LocY, LocZ), FVector(SclX, SclY, SclZ));
}
```

⚠ **Default 값 분기** — Location/Rotation = 0.0 (영점), Scale = 1.0 (단위). 빈 channel 시 default 반환 의무.

## 6. EvaluateChannel — 단일 채널 보간

```cpp
float UMyTransformSection::EvaluateChannel(const TArray<FMyFloatKey>& Channel, FFrameNumber InLocalFrame, float DefaultVal)
{
    const int32 KeyCount = Channel.Num();
    if (KeyCount == 0) return DefaultVal;
    if (KeyCount == 1) return Channel[0].Value;

    // Boundary clamp.
    if (InLocalFrame.Value <= Channel[0].Time.Value)         return Channel[0].Value;
    if (InLocalFrame.Value >= Channel.Last().Time.Value)     return Channel.Last().Value;

    // 두 인접 key 찾기 + InterpMode 보간.
    for (int32 i = 0; i < KeyCount - 1; ++i)
    {
        const FMyFloatKey& A = Channel[i];
        const FMyFloatKey& B = Channel[i + 1];
        if (InLocalFrame.Value >= A.Time.Value && InLocalFrame.Value <= B.Time.Value)
        {
            const int32 SpanFrames = B.Time.Value - A.Time.Value;
            const float Alpha = (SpanFrames > 0)
                ? static_cast<float>(InLocalFrame.Value - A.Time.Value) / static_cast<float>(SpanFrames)
                : 0.0f;

            switch (A.InterpMode)
            {
                case EMyInterpMode::Constant: return A.Value;
                case EMyInterpMode::Linear:   return FMath::Lerp(A.Value, B.Value, Alpha);
                case EMyInterpMode::Cubic:    return /* Catmull-Rom — §4 공식 */;
            }
        }
    }
    return Channel.Last().Value;  // 도달 안 함 (boundary clamp 처리)
}
```

⚠ **Linear scan** — N keys 일 시 O(N) per evaluate × 9 channel × 매 paint. 100+ keys 시 `Algo::LowerBound` 또는 last-hit cache hint 권장 (lite 단계 무시 가능).

## 7. SetKeyAll — 9 Channel 동시 추가 (Sequencer 미러)

Sequencer 의 "Set Key" 명령은 모든 visible channel 에 동시 키 추가. lite 미러:

```cpp
void UMyTransformSection::AddKeyAtGlobalFrame(FFrameNumber InGlobalFrame, EMyInterpMode InMode)
{
    // Section boundary clamp.
    const int32 StartGlobal = GetStartFrame().Value;
    const int32 EndGlobal   = GetEndFrame().Value;
    const int32 ClampedGlobal = FMath::Clamp(InGlobalFrame.Value, StartGlobal, EndGlobal);
    const FFrameNumber LocalFrame(ClampedGlobal - StartGlobal);

    // 현재 보간 값 capture (Sequencer SetKeyAll 미러).
    const FTransform CurrentValue = EvaluateAtFrame(LocalFrame);
    const FVector Loc = CurrentValue.GetLocation();
    const FRotator Rot = CurrentValue.GetRotation().Rotator();
    const FVector Scl = CurrentValue.GetScale3D();

#if WITH_EDITOR
    Modify();
#endif

    AddKeyToChannel(LocationX,     LocalFrame, Loc.X,    InMode);
    AddKeyToChannel(LocationY,     LocalFrame, Loc.Y,    InMode);
    AddKeyToChannel(LocationZ,     LocalFrame, Loc.Z,    InMode);
    AddKeyToChannel(RotationRoll,  LocalFrame, Rot.Roll, InMode);
    AddKeyToChannel(RotationPitch, LocalFrame, Rot.Pitch, InMode);
    AddKeyToChannel(RotationYaw,   LocalFrame, Rot.Yaw,  InMode);
    AddKeyToChannel(ScaleX,        LocalFrame, Scl.X,    InMode);
    AddKeyToChannel(ScaleY,        LocalFrame, Scl.Y,    InMode);
    AddKeyToChannel(ScaleZ,        LocalFrame, Scl.Z,    InMode);
}
```

`AddKeyToChannel` 안 동일 Time key 있으면 overwrite (중복 차단):
```cpp
static void AddKeyToChannel(TArray<FMyFloatKey>& Channel, FFrameNumber InTime, float InValue, EMyInterpMode InMode)
{
    for (FMyFloatKey& Key : Channel)
    {
        if (Key.Time.Value == InTime.Value) { Key.Value = InValue; Key.InterpMode = InMode; return; }
    }
    // 정렬 위치 삽입 (또는 push + 외부 Sort 호출)
    int32 InsertIdx = 0;
    for (; InsertIdx < Channel.Num(); ++InsertIdx)
    {
        if (Channel[InsertIdx].Time.Value > InTime.Value) break;
    }
    Channel.Insert(FMyFloatKey(InTime, InValue, InMode), InsertIdx);
}
```

## 8. Per-channel API (UI direct edit, SpinBox 용)

단일 channel value 평가 + 단일 channel key 추가 (9 channel SetKeyAll 과 별개):

```cpp
float UMyTransformSection::GetChannelValueAtLocalFrame(FName ChannelName, FFrameNumber InLocalFrame) const
{
    // ChannelName ("Location.X" / "Rotation.Roll" / ...) → channel array + default value 매핑.
    // EvaluateChannel 호출 후 결과 반환.
}

void UMyTransformSection::SetChannelKeyAtGlobalFrame(FName ChannelName, FFrameNumber InGlobalFrame, float InValue, EMyInterpMode InMode)
{
    // 단일 channel 만 mutate (AddKeyAtGlobalFrame 의 9 channel SetKeyAll 과 별개).
}
```

→ SpinBox.OnValueCommitted 핸들러 안 `SetChannelKeyAtGlobalFrame` 호출 — channel sub-row 우측 numeric editbox 패턴.

## 9. GetUniqueKeyTimes — Diamond paint 용

```cpp
TArray<FFrameNumber> UMyTransformSection::GetUniqueKeyTimes() const
{
    TSet<int32> UniqueTimes;
    auto Gather = [&](const TArray<FMyFloatKey>& Channel) {
        for (const auto& K : Channel) UniqueTimes.Add(K.Time.Value);
    };
    Gather(LocationX); Gather(LocationY); Gather(LocationZ);
    Gather(RotationRoll); Gather(RotationPitch); Gather(RotationYaw);
    Gather(ScaleX); Gather(ScaleY); Gather(ScaleZ);

    TArray<FFrameNumber> Result;
    Result.Reserve(UniqueTimes.Num());
    for (int32 Frame : UniqueTimes) Result.Add(FFrameNumber(Frame));
    Result.Sort([](const FFrameNumber& A, const FFrameNumber& B) { return A.Value < B.Value; });
    return Result;
}
```

→ TrackArea 의 Section row 위 diamond paint — 9 channel 중 어느 곳이든 key 있는 frame 표시 (Sequencer 표준).

## 10. 함정 카탈로그

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | `FMath::CubicInterp` 시그니처 혼동 (P0, T0, P1, T1, Alpha 5 인자) | Engine `UnrealMathUtility.h` L1212/L1226 권위 verify |
| 2 | `FRotator(Roll, Pitch, Yaw)` ctor 순서 혼동 (실제 Pitch first) | Engine `Rotator.h` L103/L568 `FRotator(InPitch, InYaw, InRoll)` |
| 3 | Catmull-Rom Tangent 공식 오기 (1/3 / 2/3 / 1/2 혼동) | `T_i = (P_{i+1} - P_{i-1}) * 0.5` (Engine FRichCurve::EvalForTwoKeys 미러) |
| 4 | 빈 channel 시 default 값 누락 (Location/Rotation=0, Scale=1) | EvaluateChannel default 인자 channel 별 분기 |
| 5 | 같은 LocalFrame 의 key 중복 (AddKey 시 overwrite 안 함) | AddKeyToChannel 안 동일 Time 검색 + Value/InterpMode overwrite |
| 6 | Sort 누락 (Insert 순서 무관 그냥 push) | 정렬 위치 Insert 또는 외부 SortAllChannels 호출 |
| 7 | C3668 base non-virtual AddSection 시 자손 single-Section enforce override 실패 | 베이스 `UMyTrack::AddSection` virtual 격상 |
| 8 | Linear scan 100+ keys hot path | `Algo::LowerBound` 또는 last-hit cache hint |

## 11. Cross-link

- [[sources/ue-levelsequence-tracks]] §5 (UMovieScene3DTransformTrack 풀스택)
- [[sources/ue-levelsequence-moviescene]] §2.5 (FFrameNumber + UMovieSceneSection 데이터 모델)
- [[sources/ue-coreuobject-uobject]] (UPROPERTY USTRUCT)
- [[synthesis/mc-combo-editor-levelsequence-lite]] §5.10 (KMCProject Phase 5p+5..5p+8 실측)
- [[synthesis/timeline-custom-slate-widget-pattern]] (Custom Timeline 일반 패턴)

## 12. 변경 이력

| 날짜 | 변경 |
| -- | -- |
| 2026-05-19 (Cycle 5p+5) | 최초 작성 — FMovieScene3DTransformTrack × 9 FloatChannel lite 미러 일반화. KMCProject Phase 5p+7 사례 (FMCComboFloatKey × 9 channels + FMath::CubicInterp Catmull-Rom + FRotator(Pitch,Yaw,Roll) ctor + AddKeyAtGlobalFrame SetKeyAll + GetUniqueKeyTimes diamond paint) 통합. 8 함정 카탈로그 (CubicInterp 시그니처 / FRotator ctor 순서 / Catmull-Rom 공식 / default 값 / 중복 차단 / Sort / C3668 / Linear scan). |
