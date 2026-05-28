---
name: slatecore-text
description: FText + FString + LOCTEXT/NSLOCTEXT + STextBlock + 다국어 + Localization + Rich Text Markup.
---

# SlateCore / Text

> 부모 모듈: [`SlateCore`](../SKILL.md) · UE 5.5.4
> 다루는 영역: 폰트·텍스트 셰이핑 — `FSlateFontInfo`/`FCompositeFont`/`FSlateFontCache`/`FFontMeasureService` + HarfBuzz/FreeType/ICU 통합
> 관련 sub-skill: [`Drawing/`](../Drawing/SKILL.md), [`Styling/`](../Styling/SKILL.md), [`SWidget/`](../SWidget/SKILL.md)

---

## 1. 개요

Slate 텍스트 렌더링은 **HarfBuzz(셰이핑) + FreeType(글리프 래스터화) + ICU(텍스트 분석)** 의 조합으로 동작:

```
FText 
  ↓ FSlateFontInfo (폰트 패밀리·크기·필드)
  ↓ FFontMeasureService::Measure → 너비/높이 계산
  ↓ FSlateFontCache: 글리프 캐시 (텍스처 아틀라스)
  ↓ FSlateDrawElement::MakeText → DrawElement
  ↓ FSlateRenderer 가 GPU 제출 (폰트 atlas 텍스처 사용)
```

`SlateCore.Build.cs` 의 `WITH_FREETYPE` / `WITH_HARFBUZZ` 가 false 면(서버 빌드 등) 폰트 렌더링 비활성.

---

## 2. 핵심 헤더와 클래스

### 2.1 폰트 정보

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/Fonts/SlateFontInfo.h` | `struct FSlateFontInfo` (L146) | 폰트 패밀리 + 크기 + 타이포그래피 메타. UPROPERTY로 노출 가능. |
| `Public/Fonts/CompositeFont.h` | `struct FCompositeFont` (L429), `FTypeface`, `FCompositeFallbackFont`, `FCompositeSubFont` | 다국어 폴백 폰트 묶음. 영어는 A 폰트, CJK는 B 폰트 등. |
| `Public/Fonts/FontFaceInterface.h` | `IFontFaceInterface` | 폰트 페이스 추상 인터페이스. |
| `Public/Fonts/FontProviderInterface.h` | `ISlateFontProvider` | 폰트 제공자 인터페이스 — `UFont` 같은 UObject가 구현. |
| `Public/Fonts/FontBulkData.h` | `UFontBulkData` (UCLASS) | TTF/OTF 바이너리 데이터를 BulkData로 저장. |
| `Public/Fonts/FontTypes.h` | `EFontHinting`, `EFontLoadingPolicy`, `EFontLayoutMethod` 등 enum | 폰트 옵션. |
| `Public/Fonts/FontRasterizationMode.h` | `EFontRasterizationMode` | Bitmap / SDF (Signed Distance Field — 5.x). |
| `Public/Fonts/FontSdfSettings.h` | SDF 폰트 설정 | 5.x 신규 — 확대 시 선명. |

### 2.2 셰이핑·캐시·측정

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Public/Fonts/FontCache.h` | `class FSlateFontCache : ISlateAtlasProvider, FSlateFlushableAtlasCache` (L755) | 글리프 → 아틀라스 텍스처 캐시. 셰이핑 결과 캐시. |
| `Public/Fonts/FontMeasure.h` | `class FSlateFontMeasure` (`FFontMeasureService` 별칭으로 자주 사용) | 텍스트 너비·높이·줄바꿈 위치 계산. |
| `Public/Fonts/ShapedTextFwd.h` | `FShapedGlyphSequencePtr`, `FShapedGlyphSequence` forward | HarfBuzz 셰이핑 결과 (글리프 시퀀스). |
| `Public/Fonts/UnicodeBlockRange.h` (+ `.inl`) | `FUnicodeBlockRange` | 유니코드 블록 정의 (CJK / Latin / Arabic 등). 폴백 폰트 결정에 사용. |

### 2.3 텍스트 레이아웃 (다중 라인·런 시스템)

| 헤더 (Slate 모듈에 본체 — cross-reference) | 심볼 | 역할 |
|--------------------------------------------|------|------|
| `Slate/Public/Framework/Text/IRun.h` | `class IRun` | 텍스트의 한 "런(run)" — 동일 스타일 구간. |
| `Slate/Public/Framework/Text/ITextLayoutMarshaller.h` | `class ITextLayoutMarshaller` | 텍스트 ↔ Run 변환 (RTF/Markdown 등 포맷). |
| `Slate/Public/Framework/Text/SlateTextRun.h` | `FSlateTextRun : IRun` | 표준 텍스트 런. |
| `Slate/Public/Framework/Text/SlateImageRun.h` | `FSlateImageRun : IRun` | 인라인 이미지 (이모지 등). |
| `Slate/Public/Framework/Text/FTextLayout.h` | `FTextLayout` | 다중 라인·서식 텍스트 레이아웃 엔진. |

> 본 sub-skill 은 **SlateCore 폰트** 까지. Run 시스템은 `Slate` 모듈 sub-skill (`TextInput`/`MultiLineTextInput` 등) 에서 다룬다.

---

## 3. 자주 쓰는 API

### 3.1 폰트 정보 만들기

```cpp
// 표준 스타일에서 (가장 흔함)
FSlateFontInfo Font = FCoreStyle::Get().GetFontStyle("NormalFont");
FSlateFontInfo Bold = FCoreStyle::Get().GetFontStyle("BoldFont");

// FAppStyle (활성 앱 기준)
FSlateFontInfo F = FAppStyle::Get().GetFontStyle("Heading");

// 직접 (폰트 에셋 + 크기)
FSlateFontInfo Custom(MyUFont, /*Size=*/14, /*TypeFace=*/TEXT("Bold"));

// SlateStyleMacros.h 매크로
#include "Styling/SlateStyleMacros.h"
// 스타일셋 안에서:
Set("MyStyle.Title", DEFAULT_FONT("Bold", 24));
```

### 3.2 텍스트 측정

```cpp
TSharedRef<FSlateFontMeasure> Measure = FSlateApplication::Get().GetRenderer()->GetFontMeasureService();
FVector2D Size = Measure->Measure(TEXT("Hello"), Font);
float Height   = Measure->GetMaxCharacterHeight(Font);
float Baseline = Measure->GetBaseline(Font);
```

### 3.3 위젯에서 텍스트 그리기

```cpp
virtual int32 OnPaint(...) const override
{
    FSlateDrawElement::MakeText(
        Out, LayerId,
        Geo.ToPaintGeometry(),
        FText::FromString(TEXT("Hello")),
        Font,
        ESlateDrawEffect::None,
        FLinearColor::White
    );
    return LayerId + 1;
}
```

자세한 그리기 흐름은 [`Drawing/`](../Drawing/SKILL.md). 일반적으로는 직접 그리지 않고 `STextBlock`/`SRichTextBlock` (Slate 모듈) 사용.

### 3.4 다국어 / 컴포지트 폰트

```cpp
// FCompositeFont 자동 폴백
//   - 기본 typeface (예: Roboto)
//   - SubFont 1: CJK 범위 → NotoSans CJK
//   - SubFont 2: Arabic → NotoNaskh
// 사용자 코드는 FSlateFontInfo 만 만들면 SlateFontCache 가 자동 선택
```

`UFont` 에셋의 디테일에서 SubFont 와 유니코드 범위 매핑.

---

## 4. 가상 함수 (오버라이드 포인트)

게임 코드는 폰트 인터페이스를 직접 구현할 일이 거의 없다. 다음 인터페이스가 존재함을 알아두면 됨:

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `class IFontFaceInterface` | FontFaceInterface.h | 폰트 페이스 제공자. UFont가 구현. |
| `class ISlateFontProvider` | FontProviderInterface.h | 폰트 정보 → 페이스 변환 제공자. |
| `class FSlateFontCache : ISlateAtlasProvider, FSlateFlushableAtlasCache` | FontCache.h L755 | 글리프 캐시 — 엔진이 단일 인스턴스 보유. |

---

## 5. 예제

### 5.1 다국어 안전한 텍스트 위젯

```cpp
// LOCTEXT 매크로 사용 — 빌드 시 키-값 추출, 다국어 .po 파일과 매핑
SNew(STextBlock)
.Text(LOCTEXT("HudGold", "Gold: {0}"))      // {0} = 인자 자리
.Font(FAppStyle::Get().GetFontStyle("HUD.Heading"))
.ColorAndOpacity(FSlateColor(FLinearColor::Yellow));

// 인자 바인딩
FFormatNamedArguments Args;
Args.Add(TEXT("0"), FText::AsNumber(GoldAmount));
FText Final = FText::Format(LOCTEXT("HudGold", "Gold: {0}"), Args);
```

### 5.2 폰트 측정 후 동적 사이즈

```cpp
const FSlateFontInfo& Font = FAppStyle::Get().GetFontStyle("Tooltip");
TSharedRef<FSlateFontMeasure> Measure =
    FSlateApplication::Get().GetRenderer()->GetFontMeasureService();

FVector2D TextSize = Measure->Measure(MyText, Font);
SetDesiredSize(TextSize + FVector2D(/*Padding=*/8.f));
```

### 5.3 RichText 같은 다중 스타일 (Slate 모듈)

```cpp
// SRichTextBlock (Slate 모듈) — <span style="..."> 같은 마크업 지원
SNew(SRichTextBlock)
.Text(LOCTEXT("Help", "Press <Style>Bold</> to continue"))
.TextStyle(&FAppStyle::Get().GetWidgetStyle<FTextBlockStyle>("NormalText"))
+ SRichTextBlock::Decorator(/* ... */);
// 자세한 사용은 Slate 모듈 sub-skill
```

---

## 6. 운영 가이드 / 함정

1. **하드코딩 영문 문자열 금지** — `LOCTEXT("Key", "English")` 또는 `NSLOCTEXT("Namespace", "Key", "English")`. `FText::FromString` 은 **번역 안 됨** — 사용자명 등 동적 문자열만.
2. **`FSlateFontInfo` 매 프레임 생성 금지** — `FCoreStyle::Get().GetFontStyle(...)` 의 결과를 멤버에 캐시 또는 람다에서 매번 같은 키로 조회.
3. **폰트 캐시 압박** — 너무 많은 폰트 크기·스타일을 동시 사용하면 atlas 가 비대해짐. 주요 크기(12/14/18/24/36) 정도로 표준화.
4. **`UFont` 에셋의 SubFont 누락** — 기본 폰트가 CJK 글리프 없으면 □ 로 표시. CompositeFont의 SubFont 매핑 확인.
5. **SDF 폰트 (5.x)** — 확대 시 선명하지만 atlas 비용 증가. UI 가 자주 줌되는 경우만.
6. **`FontMeasureService` 호출 비용** — 매 프레임 같은 텍스트를 측정하면 캐시되지만 새 텍스트는 새 측정. 변동이 큰 텍스트는 결과 캐시.
7. **DPI 스케일** — `GetMaxCharacterHeight(Font)` 같은 메서드는 폰트 크기 반영. DPI 변경 시 자동 재측정.

---

## 7. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `UFontFace` / `UFont` 에셋 편집 🛠 | UFont (Engine 모듈) | `WITH_EDITOR` | 에디터에서 SubFont 매핑 등 편집. 런타임에선 로드만. |
| `FCompositeFont` 의 일부 메타 🛠 | CompositeFont.h | `WITH_EDITORONLY_DATA` | 에디터 표시용 thumbnail 등. |
| `IMAGE_BRUSH` / `BOX_BRUSH` 매크로의 폰트 변형 (DEFAULT_FONT 등) 🛠 (실용) | SlateStyleMacros.h | (런타임 컴파일은 되지만 콘텐츠 경로) | 콘텐츠 디렉토리 해석은 빌드별 차이. |

런타임에서 안전한 API는 `FSlateFontInfo`, `FSlateFontMeasure::Measure`, 폰트 그리기 전부.

---

## 8. 관련 sub-skill

- [`Drawing/`](../Drawing/SKILL.md) — `FSlateDrawElement::MakeText` 가 폰트 atlas 텍스처 사용
- [`Styling/`](../Styling/SKILL.md) — `FTextBlockStyle` 이 `FSlateFontInfo`/`FSlateColor` 를 묶음
- [`SWidget/`](../SWidget/SKILL.md) — `OnPaint` 에서 텍스트 그리기
- [`../../Slate/`](../../Slate/SKILL.md) — `STextBlock`/`SRichTextBlock`/`SEditableText` (위젯 본체)
