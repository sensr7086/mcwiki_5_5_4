---
name: slatecore-animation
description: FCurveSequence + FCurveHandle + Interpolation + Sequencer + ActiveTimer.
---

# SlateCore / Animation

> 부모 모듈: [`SlateCore`](../SKILL.md) · UE 5.5.4
> 다루는 영역: Slate 위젯의 **단순 트위닝** — `FCurveSequence`/`FCurveHandle`/`FSlateSprings` + `FActiveTimerHandle` 등록 패턴
> ⚠ 본 sub-skill 은 **MovieScene 시퀀서와 무관하다**. UMG의 `UWidgetAnimation`(시퀀서 통합)은 향후 LevelSequence 위키에서 다룬다.
> 관련 sub-skill: [`SWidget/`](../SWidget/SKILL.md), [`Application/`](../Application/SKILL.md), [`Drawing/`](../Drawing/SKILL.md)

---

## 1. 개요

SlateCore의 `Animation/` 폴더는 위젯이 **호버 페이드·패널 슬라이드·툴팁 펼침** 같은 짧고 단순한 트위닝을 만들 때 쓰는 경량 도구다. 시퀀서 평가 그래프 없이 단일 커브 또는 스프링 시뮬레이션으로 값 보간.

```
사용 패턴:
1. 위젯 멤버에 FCurveSequence 보유
2. AddCurve(StartTime, Duration, EaseFunction) 로 커브 추가 → FCurveHandle 받음
3. Play(SharedThis(this)) — 위젯에 ActiveTimer 등록
4. OnPaint / 다른 어트리뷰트 람다에서 Curve.GetLerp() 로 [0,1] 진행도 조회
```

---

## 2. 핵심 헤더와 클래스

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/Animation/CurveSequence.h` | `struct FCurveSequence : TSharedFromThis<FCurveSequence>`, `struct FCurveSequence::FSlateCurve` (내부) | 여러 커브를 시간 오프셋과 함께 묶음. `Play`/`PlayReverse`/`JumpToStart`/`JumpToEnd`. |
| `Public/Animation/CurveHandle.h` | `class FCurveHandle` | 단일 커브 핸들. `GetLerp()` (0~1), `GetLerpLooping()`, `IsPlaying()`. |
| `Public/Animation/SlateSprings.h` | `FFloatSpringState`, `FVectorSpringState`, `UpdateSpring(...)` | 스프링 시뮬레이션 (튕김/감쇠). |
| `Public/Types/WidgetActiveTimerDelegate.h` | `DECLARE_DELEGATE_RetVal_TwoParams(EActiveTimerReturnType, FWidgetActiveTimerDelegate, double, float)`, `enum class EActiveTimerReturnType : uint8` (Continue/Stop) | ActiveTimer 콜백 시그니처. `FCurveSequence::Play` 가 내부적으로 사용. |

### 2.1 ECurveEaseFunction (CurveSequence.h)

```
Linear, QuadIn, QuadOut, QuadInOut, CubicIn, CubicOut, CubicInOut
```

기본은 `Linear`. 대부분 `CubicInOut` (자연스러운 시작·종료) 권장.

---

## 3. 자주 쓰는 API

### 3.1 단일 커브 페이드

```cpp
class SFadeIn : public SCompoundWidget
{
public:
    void Construct(const FArguments& InArgs)
    {
        FadeInCurve = FadeAnim.AddCurve(0.f, 0.3f, ECurveEaseFunction::CubicOut);

        ChildSlot
        [
            SNew(SBorder)
            .BorderBackgroundColor_Lambda([this]()
            {
                FLinearColor C = FLinearColor::White;
                C.A = FadeInCurve.GetLerp();              // 0.0 → 1.0
                return C;
            })
            [ /* content */ ]
        ];

        FadeAnim.Play(SharedThis(this));                  // ActiveTimer 자동 등록
    }

private:
    FCurveSequence FadeAnim;
    FCurveHandle  FadeInCurve;
};
```

### 3.2 스태거(stagger) — 여러 커브를 시간 오프셋과 함께

```cpp
// 0~0.15 줌, 0.15~0.25 페이드 인
ZoomCurve = Sequence.AddCurve(0.0f,  0.15f, ECurveEaseFunction::CubicOut);
FadeCurve = Sequence.AddCurve(0.15f, 0.10f, ECurveEaseFunction::Linear);
Sequence.Play(SharedThis(this));

// 사용 시:
float Scale = FMath::Lerp(0.8f, 1.0f, ZoomCurve.GetLerp());
float Alpha = FadeCurve.GetLerp();   // 0~0.15s 동안 0
```

### 3.3 스프링 (튕김)

```cpp
class SBouncyButton : public SButton
{
public:
    void Construct(const FArguments& InArgs)
    {
        SButton::Construct(/* ... */);
        // 매 프레임 갱신을 위해 ActiveTimer 등록
        RegisterActiveTimer(0.f, FWidgetActiveTimerDelegate::CreateSP(this, &SBouncyButton::TickSpring));
    }

    EActiveTimerReturnType TickSpring(double InCurrentTime, float InDeltaTime)
    {
        // Hover 시 Target = 1.1, 아니면 Target = 1.0
        const float Target = IsHovered() ? 1.1f : 1.0f;
        FFloatSpringState::Update(SpringState, Target, InDeltaTime, /*Stiffness=*/200.f, /*Damping=*/12.f);

        // SpringState.Position 으로 RenderTransform 적용
        SetRenderTransform(FSlateRenderTransform(FScale2D(SpringState.Position)));
        return EActiveTimerReturnType::Continue;
    }

private:
    FFloatSpringState SpringState;
};
```

---

## 4. ActiveTimer 등록 패턴

ActiveTimer 는 **위젯 단위 타이머**로, 매 프레임 위젯의 콜백을 호출한다. Tick virtual 보다 가볍고, 콜백이 `EActiveTimerReturnType::Stop` 반환 시 자동 해제.

```cpp
// SWidget 멤버에 핸들 보유 (선택)
TSharedPtr<FActiveTimerHandle> ActiveTimer;

// 등록
ActiveTimer = RegisterActiveTimer(
    0.0f,                                                        // 첫 호출까지 지연 (초)
    FWidgetActiveTimerDelegate::CreateSP(this, &SMy::TickAnim)
);

// 콜백
EActiveTimerReturnType SMy::TickAnim(double InCurrentTime, float InDeltaTime)
{
    if (Anim.IsPlaying()) return EActiveTimerReturnType::Continue;
    return EActiveTimerReturnType::Stop;        // 자동 해제
}

// 명시적 해제 (선택)
if (ActiveTimer.IsValid()) UnRegisterActiveTimer(ActiveTimer.ToSharedRef());
```

`FCurveSequence::Play(SharedThis(this))` 는 내부적으로 위 패턴을 자동 처리.

---

## 5. 가상 함수 (오버라이드 포인트)

`FCurveSequence`/`FCurveHandle`/스프링은 일반 C++ struct로 가상 함수가 없다. 대신 SWidget 측의 ActiveTimer 등록 hook 활용:

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `TSharedRef<FActiveTimerHandle> SWidget::RegisterActiveTimer(float, FWidgetActiveTimerDelegate)` | SWidget.h | 위젯 단위 타이머 등록. |
| `void SWidget::UnRegisterActiveTimer(const TSharedRef<FActiveTimerHandle>&)` | SWidget.h | 해제. |
| `virtual void SWidget::Tick(const FGeometry&, double, float)` | SWidget.h | 매 프레임 — **비싸다**. ActiveTimer 권장. |

> 가능하면 `Tick` virtual override 회피 — `RegisterActiveTimer` 또는 `TSlateAttribute` 자동 인밸리데이션을 우선.

---

## 6. 운영 가이드 / 함정

1. **`Play(SharedThis(this))` 의 인자 빠뜨림** — 인자 없으면 ActiveTimer가 등록 안 됨 → 커브가 흐르지 않음. 항상 `SharedThis(this)` 또는 명시적 위젯 전달.
2. **EaseFunction 미설정** → `Linear` 기본. UI 트위닝은 `CubicOut`/`CubicInOut` 권장.
3. **재생 중 `Play` 다시 호출** — 처음부터 다시. 누적이 아닌 리셋. 누적 효과는 `PlayRelative` 또는 직접 시간 관리.
4. **메모리 누수** — `FCurveSequence` 가 멤버이고 위젯 파괴 시 함께 해제되면 안전. 외부에서 보유하면 ActiveTimer 가 위젯을 잡을 수 있음.
5. **MovieScene 과 혼동 금지** — `UWidgetAnimation` 은 별개 시스템. 시퀀서 키프레임 작업이 필요하면 UMG 의 `UWidgetAnimation` 사용 (LevelSequence 위키).

---

## 7. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| (없음 — 본 영역은 전부 런타임) | — | — | 단순 커브는 게임 빌드에서도 동일 동작. |

> Unreal Insights `Slate` 채널에서 ActiveTimer 콜백 시간 측정 가능 (`UE_TRACE_ENABLED`).

---

## 8. 관련 sub-skill

- [`SWidget/`](../SWidget/SKILL.md) — `RegisterActiveTimer` / `Tick` virtual
- [`Application/`](../Application/SKILL.md) — Slate Tick 사이클이 ActiveTimer 처리
- [`Drawing/`](../Drawing/SKILL.md) — 커브 값을 색·위치에 적용 → `Invalidate(EInvalidateWidgetReason::Paint)` 자동
- [`Types/`](../Types/SKILL.md) — `EActiveTimerReturnType`, `FWidgetActiveTimerDelegate`
