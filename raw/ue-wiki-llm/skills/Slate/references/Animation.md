---
name: slate-animation
description: SBorder + SCurveHandle + 슬레이트 애니메이션 - FCurveSequence 통합.
---

# Slate · Animation sub-skill

> **모듈**: Slate (Tier 3 — 게임/에디터 공통)
> **위치**: `Engine/Source/Runtime/Slate/Public/Framework/Animation/` (3 헤더)
> **다루는 범위**: 5.x 신규 어트리뷰트 보간 — `FAnimatedAttribute<T>` · `FAnimatedAttributeManager` · `FAttributeInterpolator<T>`.

---

## 1. 개요

UE 5.x 부터 도입된 **TSlateAttribute의 자동 보간**. 기존 `FCurveSequence` ([`SlateCore/Animation`](../../SlateCore/references/Animation.md)) 가 Tween 진행만 다룬다면, `FAnimatedAttribute` 는 *값 자체의 부드러운 전환* 을 자동 보간 — setter에 대상값을 던지면 현재값에서 보간하며 자연스럽게 도달.

핵심 패턴:
- **`FAnimatedAttribute<T>`** — 일반 `TSlateAttribute<T>` 와 호환 + 보간 구간 동안 자동 인밸리데이션
- **`FAnimatedAttributeManager`** — 등록·진행 매니저 (글로벌)
- **`FAttributeInterpolator<T>`** — 사용자 정의 보간 함수 (Linear / Cubic / Spring 등)

> [`SlateCore/Animation`](../../SlateCore/references/Animation.md) 의 `FCurveSequence`/`FCurveHandle` 가 *진행도(0~1) 관리* 라면, 본 sub-skill의 `FAnimatedAttribute` 는 *값을 값으로 보간* — 두 시스템 보완적.

---

## 2. 핵심 헤더 (Slate/Public/Framework/Animation/)

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `AnimatedAttribute.h` | `FAnimatedAttribute<T>` | 보간되는 어트리뷰트 |
| `AnimatedAttributeManager.h` | `FAnimatedAttributeManager` (싱글턴) | 등록·진행 |
| `AttributeInterpolator.h` | `FAttributeInterpolator<T>` (베이스) | 보간 함수 |

---

## 3. FAnimatedAttribute<T> — 값 보간 어트리뷰트

```cpp
// 위젯 헤더
TSlateAttribute<FLinearColor> Color { *this, FLinearColor::White, EInvalidateWidgetReason::Paint };
FAnimatedAttribute<FLinearColor> AnimatedColor;

// Construct
AnimatedColor = FAnimatedAttribute<FLinearColor>::Create(*this, FLinearColor::White, EInvalidateWidgetReason::Paint);

// 사용 — 값 전달 시 자동 보간
AnimatedColor.Set(*this, FLinearColor::Red);    // White → Red 부드럽게
```

### API (개략)

| API | 의미 |
|-----|------|
| `static FAnimatedAttribute<T> Create(SWidget& Owner, T InitialValue, EInvalidateWidgetReason)` | 생성 |
| `void Set(SWidget& Owner, T NewValue)` | 보간 시작 |
| `void SetImmediate(SWidget& Owner, T NewValue)` | 즉시 (보간 X) |
| `T Get() const` | 현재 값 (보간 중간값) |
| `bool IsAnimating() const` | 보간 진행 중? |
| `void SetInterpolator(TSharedPtr<FAttributeInterpolator<T>>)` | 사용자 보간 함수 |
| `void SetDuration(float)` / `GetDuration()` | 보간 시간 |

> **자동 인밸리데이션**: 보간 중에는 `AnimatedAttributeManager` 가 매 프레임 위젯을 invalidate(reason) — `EInvalidateWidgetReason::Paint`/`Layout` 등.

---

## 4. FAttributeInterpolator<T> — 사용자 정의 보간

```cpp
class FCubicEaseInterpolator : public FAttributeInterpolator<FLinearColor>
{
public:
    virtual FLinearColor Interpolate(const FLinearColor& From, const FLinearColor& To, float Alpha) const override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(FCubicEaseInterpolator_Interpolate);
        const float Eased = FMath::InterpEaseInOut(0.f, 1.f, Alpha, /*Exp=*/3.f);
        return FMath::Lerp(From, To, Eased);
    }
};

// 사용
AnimatedColor.SetInterpolator(MakeShared<FCubicEaseInterpolator>());
```

빌트인 보간기:
- `FLinearInterpolator<T>` — 단순 선형 (기본)
- (사용자 정의로 EaseIn/EaseOut/Spring/Bezier 등 직접 작성)

---

## 5. FAnimatedAttributeManager — 글로벌

`FAnimatedAttributeManager::Get()` 싱글턴. 모든 `FAnimatedAttribute` 가 자동 등록. Slate Tick 사이클에서 매 프레임 진행 + 위젯 Invalidate.

직접 사용하는 일은 드물고, `FAnimatedAttribute` 가 내부적으로 사용.

---

## 6. SlateCore/Animation 의 FCurveSequence와 비교

| 측면 | `FCurveSequence` (SlateCore) | `FAnimatedAttribute` (Slate) |
|------|------------------------------|------------------------------|
| 다루는 것 | 진행도 0~1 | 값 자체의 보간 |
| 사용 시점 | 일반 트위닝 (페이드 인/아웃 등) | 어트리뷰트 자동 보간 (값 변경 시 부드럽게) |
| 매뉴얼 vs 자동 | 매뉴얼 — `Play()`/`Reverse()` 호출 | 자동 — `Set()` 만 호출 |
| 인밸리데이션 | 진행 중 위젯이 직접 invalidate | 매니저가 자동 invalidate |
| 5.x 권장 | (계속 사용 — 진행도 시) | (신규 — 값 보간 시) |

조합 사용 가능 — `FCurveSequence` 로 진행도 만들고 `FAnimatedAttribute` 로 값 전이.

---

## 7. 가상 함수 / Super 호출

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `FAttributeInterpolator<T>::Interpolate(From, To, Alpha)` | (override 시 자체 처리) | PURE |
| `FAnimatedAttribute<T>::Set` | (override 안 함 — final) | |

본 sub-skill은 SWidget의 새 virtual 추가 X — 기존 `OnPaint`/`Tick` 안에서 보간 결과 사용.

---

## 8. 함정

| 함정 | 회피 |
|------|------|
| `Set()` 매 프레임 호출 — 매번 보간 재시작 | 변경 시에만 호출 (이전 값 비교) |
| `IsAnimating()` 검사 안 하고 `SetImmediate` 강제 | 진행 중 인터럽트 시 자연스러움 깨짐 — 체크 후 분기 |
| 사용자 정의 `FAttributeInterpolator` 안에서 무거운 작업 | 매 프레임 호출 — `TRACE_CPUPROFILER_EVENT_SCOPE` 의무 ([`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md)) |
| `EInvalidateWidgetReason::Layout` 사용 시 매 프레임 레이아웃 재계산 | 색상 같은 페인트만이면 `Paint` 사용 |
| 보간 중 위젯 파괴 | `FAnimatedAttributeManager` 가 자동 정리 — 단, 사용자 람다는 weak capture |
| `FAnimatedAttribute` 와 `TSlateAttribute` 혼용 | 한 위젯에서 같은 값을 두 시스템으로 관리 X |

---

## 9. 에디터 전용? 🛠

런타임 모듈 — **게임/에디터 공통**. 4단 분리 불필요. 다만 모든 Slate UI는 게임 빌드에서도 동작.

---

## 10. 관련 sub-skill

- [`SlateCore/Animation`](../../SlateCore/references/Animation.md) — `FCurveSequence`/`FCurveHandle`/`FSlateSprings` (진행도 시스템)
- [`SlateCore/Types`](../../SlateCore/references/Types.md) — `TSlateAttribute<T>` 베이스
- [`SlateCore/SWidget`](../../SlateCore/references/SWidget.md) — TSlateAttribute 자동 인밸리데이션
- [`SlateCore/Drawing`](../../SlateCore/references/Drawing.md) — Invalidate(reason) 8종
- 교차: [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) (Interpolate / Tick 스코프)
