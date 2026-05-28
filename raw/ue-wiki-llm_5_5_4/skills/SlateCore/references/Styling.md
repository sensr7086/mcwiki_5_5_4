---
name: slatecore-styling
description: FSlateStyleSet + FSlateBrush + FSlateColor + FSlateFontInfo + FSlateWidgetStyle - Style 등록/해제.
---

# SlateCore / Styling

> 부모 모듈: [`SlateCore`](../SKILL.md) · UE 5.5.4
> 다루는 영역: 스타일 시스템 — `ISlateStyle`/`FSlateStyleSet`/`FSlateBrush`/`FSlateColor`/`FSlateWidgetStyle` + `FAppStyle`/`FCoreStyle`/`StarshipCoreStyle`/`StyleColors` + `USlateWidgetStyleAsset` 🛠
> 관련 sub-skill: [`Drawing/`](../Drawing/SKILL.md), [`SWidget/`](../SWidget/SKILL.md), [`Text/`](../Text/SKILL.md)

---

## 1. 개요

Slate 스타일 시스템은 **이름 → 자원**(브러시·색상·폰트·위젯 스타일) 매핑이다. 위젯 안에 색·이미지를 하드코딩하지 않고 스타일셋에서 끌어 쓴다 — 테마 변경·재스킨이 가능.

```
ISlateStyle (인터페이스)
  └─ FSlateStyleSet (구체 — 이름→자원 등록)
       ├─ FCoreStyle / FAppStyle / FStarshipCoreStyle / FUMGCoreStyle  ← 엔진 표준
       └─ 게임 코드의 FProjectStyle                                     ← 사용자 정의

자원 타입:
  - FSlateBrush     (이미지/박스/색상)
  - FSlateColor     (테마 연동 색상)
  - FSlateFontInfo  (폰트 정보 — Text sub-skill)
  - FSlateWidgetStyle (위젯별 묶음 — SButtonStyle/STextBlockStyle 등)
```

5.x부터 `Starship` 테마(에디터 기본)와 `UMGCoreStyle`(게임 UI) 가 분리되어 제공된다.

---

## 2. 핵심 헤더와 클래스

### 2.1 스타일 베이스 (`Public/Styling/`)

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Styling/ISlateStyle.h` | `class ISlateStyle` (L17) | 스타일 조회 인터페이스. `GetBrush(FName)`, `GetColor(FName)`, `GetFontStyle(FName)`, `GetWidgetStyle<T>(FName)` 등. |
| `Styling/SlateStyle.h` | `class FSlateStyleSet : public ISlateStyle` (L27) | 표준 구현. `Set(FName, T Value)` 로 등록, 같은 이름으로 조회. |
| `Styling/SlateStyleRegistry.h` | `class FSlateStyleRegistry` (L13) | 모든 스타일셋의 전역 등록소. `RegisterSlateStyle`/`UnRegisterSlateStyle`/`FindSlateStyle`. |
| `Styling/SlateStyleMacros.h` | `IMAGE_BRUSH`/`BOX_BRUSH`/`BORDER_BRUSH`/`TTF_FONT`/`OTF_FONT` 매크로 | 스타일 등록 시 코드 단축. |

### 2.2 표준 스타일 인스턴스

| 헤더 | 심볼 | 용도 |
|------|------|------|
| `Styling/CoreStyle.h` | `class FCoreStyle` (L14) | Slate 자체의 기본 (버튼/체크박스 등 — 4.x 호환). |
| `Styling/StarshipCoreStyle.h` | `FStarshipCoreStyle` | 5.x 신표준 (에디터 기본). |
| `Styling/AppStyle.h` | `class FAppStyle` (L23) | 현재 활성 앱 스타일을 가리키는 정적 진입점 — `FAppStyle::Get()`. |
| `Styling/UMGCoreStyle.h` | `FUMGCoreStyle` | UMG 위젯의 기본 스타일. |
| `Styling/StyleColors.h` | `USlateThemeManager : UObject` (L145) | 5.x 테마 관리자 (라이트/다크). |
| `Styling/DefaultStyleCache.h` | 스타일 캐시 | 위젯 타입별 기본 스타일 (lazy init). |
| `Styling/SlateIconFinder.h` | `FSlateIconFinder` | 클래스/에셋 → 아이콘 매핑. |

### 2.3 자원 타입

| 헤더 | 심볼 | 역할 |
|------|------|------|
| `Styling/SlateBrush.h` | `USTRUCT FSlateBrush` (L235), `class ISlateBrushSource` (L530), `enum ESlateBrushMirrorType`, `enum ESlateBrushImageType` | 그리기 자원. 이미지·박스·9-slice·둥근 모서리 등. |
| `Styling/SlateColor.h` | `USTRUCT FSlateColor` (L41) | 테마 연동 색상 (직접 색상 vs 테마 슬롯 참조). |
| `Styling/WidgetStyle.h` | `class FWidgetStyle` (L14) | 페인트 시 부모로부터 내려오는 색·투명도 — `OnPaint`의 `InWidgetStyle` 인자. |
| `Styling/SlateWidgetStyle.h` | `struct FSlateWidgetStyle` | 위젯별 스타일 묶음 베이스 (자식: `FButtonStyle`/`FTextBlockStyle` 등). |
| `Styling/SlateTypes.h` | `FButtonStyle`, `FTextBlockStyle`, `FCheckBoxStyle`, `FComboBoxStyle`, `FEditableTextStyle`, `FScrollBarStyle`, `FSpinBoxStyle`, `FProgressBarStyle` 등 다수 | 표준 위젯 스타일 정의. |
| `Styling/ToolBarStyle.h`, `SegmentedControlStyle.h` | 추가 위젯 스타일 | 5.x 에디터 위젯. |
| `Styling/SlateWidgetStyleAsset.h` 🛠 | `class USlateWidgetStyleAsset : UObject` (L17) | 위젯 스타일을 .uasset 으로 저장 (BP/디테일 패널 노출). |
| `Styling/SlateWidgetStyleContainerBase.h`, `SlateWidgetStyleContainerInterface.h` 🛠 | UCLASS 컨테이너 베이스 | UPROPERTY로 노출 가능한 스타일 컨테이너. |

---

## 3. 자주 쓰는 API

```cpp
// === 표준 스타일 조회 ===
const FSlateBrush* B = FAppStyle::Get().GetBrush("Border");
FSlateColor      C  = FAppStyle::Get().GetSlateColor("Foreground");
FSlateFontInfo   F  = FAppStyle::Get().GetFontStyle("NormalFont");
const FButtonStyle& Btn = FAppStyle::Get().GetWidgetStyle<FButtonStyle>("PrimaryButton");

// 또는 게임 UI는 FCoreStyle::Get() / FUMGCoreStyle::Get()
const FSlateBrush* WhiteBox = FCoreStyle::Get().GetBrush("WhiteBrush");

// === 사용자 정의 스타일셋 ===
class FProjectStyle : public FSlateStyleSet
{
public:
    FProjectStyle() : FSlateStyleSet("ProjectStyle")
    {
        SetContentRoot(FPaths::ProjectContentDir() / TEXT("Slate"));

        // 매크로로 단축 (SlateStyleMacros.h)
        Set("HUD.Health", new IMAGE_BRUSH("Icons/Health", FVector2D(32, 32)));
        Set("HUD.Title",  FTextBlockStyle()
            .SetFont(DEFAULT_FONT("Bold", 18))
            .SetColorAndOpacity(FLinearColor::White));
    }

    static const FProjectStyle& Get()
    {
        static FProjectStyle Inst;
        return Inst;
    }
};

// 모듈 시작 시 등록
FSlateStyleRegistry::RegisterSlateStyle(FProjectStyle::Get());
// 모듈 종료 시 해제
FSlateStyleRegistry::UnRegisterSlateStyle(FProjectStyle::Get());

// === 위젯에서 사용 ===
SNew(SImage).Image(FProjectStyle::Get().GetBrush("HUD.Health"));
SNew(STextBlock).TextStyle(&FProjectStyle::Get().GetWidgetStyle<FTextBlockStyle>("HUD.Title"));
```

### 3.1 FSlateBrush 패턴

```cpp
FSlateBrush B;
B.DrawAs       = ESlateBrushDrawType::Image;          // Image / Box / Border / RoundedBox / NoDrawType
B.ImageSize    = FVector2D(32, 32);
B.SetResourceObject(MyTexture2D);                     // UTexture2D
B.TintColor    = FSlateColor(FLinearColor::White);

// 헬퍼들 (Drawing/SKILL.md §2.2 참조):
FSlateImageBrush  ImgB(MyTexture, FVector2D(64, 64));
FSlateBoxBrush    BoxB(MyTexture, FMargin(4.f / 16.f));   // 9-slice
FSlateColorBrush  ColB(FLinearColor::Black);
FSlateRoundedBoxBrush RoundB(FLinearColor::White, /*Radius=*/4.f, /*Outline=*/FLinearColor::Black, /*OutlineWidth=*/1.f);
```

### 3.2 FSlateColor (테마 연동)

```cpp
FSlateColor Direct(FLinearColor::Red);                 // 직접 값
FSlateColor Themed(FCoreStyle::Get().GetSlateColor("AccentBlue"));  // 테마 슬롯

// 페인트 시 해석:
FLinearColor Resolved = MyColor.GetColor(InWidgetStyle);  // FWidgetStyle 컨텍스트
```

`USlateThemeManager` 가 활성 테마를 관리하며, `FSlateColor` 는 슬롯 이름으로 참조해 테마 변경 시 자동 반영.

---

## 4. 가상 함수 (오버라이드 포인트)

대부분의 스타일 자원(`FSlateBrush`/`FSlateColor`/`FSlateWidgetStyle`)은 **USTRUCT**로 일반 가상 함수가 없다 (`TStructOpsTypeTraits` 특화로 동작).

### 4.1 ISlateStyle (조회 인터페이스)

```cpp
class ISlateStyle {
public:
    virtual const FSlateBrush*    GetBrush(const FName Name, const ANSICHAR* Specifier=nullptr) const = 0;
    virtual FSlateColor           GetSlateColor(const FName Name, const ANSICHAR* Specifier=nullptr) const = 0;
    virtual FSlateFontInfo        GetFontStyle(const FName Name, const ANSICHAR* Specifier=nullptr) const = 0;
    virtual const FSlateWidgetStyle* GetWidgetStyleInternal(...) const = 0;
    // ...
};
```

게임 코드가 `ISlateStyle` 자체를 구현할 일은 없다 — `FSlateStyleSet` 을 상속/사용한다.

### 4.2 ISlateBrushSource (`SlateBrush.h:530`)

```cpp
class ISlateBrushSource {
public:
    virtual const FSlateBrush* GetSlateBrush() const = 0;
};
```

UPROPERTY 멤버에서 브러시를 동적으로 제공하고 싶을 때 이 인터페이스를 구현한 UObject로 노출.

### 4.3 USlateWidgetStyleAsset 🛠 / USlateWidgetStyleContainerBase 🛠

`UCLASS` 자손이라 UObject 가상 함수(`PostLoad` 등)는 다 적용. 자세한 UObject 라이프사이클은 [`CoreUObject/UObject/`](../../CoreUObject/references/UObject.md).

---

## 5. 예제

### 5.1 게임 모듈에서 스타일셋 등록

```cpp
// FMyGameStyle.h
class FMyGameStyle : public FSlateStyleSet
{
public:
    FMyGameStyle();
    virtual ~FMyGameStyle();

    static void Initialize();
    static void Shutdown();
    static const FMyGameStyle& Get();
    static FName GetStyleSetName() { return TEXT("MyGameStyle"); }

private:
    static TSharedPtr<FMyGameStyle> Instance;
};

// FMyGameStyle.cpp
FMyGameStyle::FMyGameStyle() : FSlateStyleSet(GetStyleSetName())
{
    SetContentRoot(IPluginManager::Get().FindPlugin("MyGame")->GetBaseDir() / TEXT("Resources/Slate"));

    Set("HUD.HealthIcon", new IMAGE_BRUSH("Icons/Health", FVector2D(32, 32)));
    Set("HUD.HealthBarBG", new BOX_BRUSH("HUD/HealthBarBG", FMargin(4.f / 16.f)));
    Set("HUD.Title",
        FTextBlockStyle()
        .SetFont(DEFAULT_FONT("Bold", 24))
        .SetColorAndOpacity(FLinearColor::White)
        .SetShadowOffset(FVector2D(1, 1))
        .SetShadowColorAndOpacity(FLinearColor::Black));
}

FMyGameStyle::~FMyGameStyle() {}

void FMyGameStyle::Initialize()
{
    if (!Instance.IsValid())
    {
        Instance = MakeShared<FMyGameStyle>();
        FSlateStyleRegistry::RegisterSlateStyle(*Instance);
    }
}

void FMyGameStyle::Shutdown()
{
    if (Instance.IsValid())
    {
        FSlateStyleRegistry::UnRegisterSlateStyle(*Instance);
        Instance.Reset();
    }
}
```

`StartupModule()` 에서 `FMyGameStyle::Initialize()`, `ShutdownModule()` 에서 `Shutdown()`.

### 5.2 위젯에서 사용

```cpp
ChildSlot
[
    SNew(SBorder)
    .BorderImage(FMyGameStyle::Get().GetBrush("HUD.HealthBarBG"))
    .Padding(FMargin(4.f))
    [
        SNew(SHorizontalBox)
        + SHorizontalBox::Slot().AutoWidth()
        [
            SNew(SImage).Image(FMyGameStyle::Get().GetBrush("HUD.HealthIcon"))
        ]
        + SHorizontalBox::Slot().FillWidth(1.f)
        [
            SNew(STextBlock)
            .TextStyle(&FMyGameStyle::Get().GetWidgetStyle<FTextBlockStyle>("HUD.Title"))
            .Text(LOCTEXT("HP", "HP 100"))
        ]
    ]
];
```

### 5.3 동적 스타일 변경

```cpp
// 색상이 자주 바뀌는 경우 — TAttribute 사용
SNew(SBorder)
.BorderBackgroundColor_Lambda([this]() {
    return Health < 30 ? FLinearColor::Red : FLinearColor::White;
})
[ /* ... */ ];
```

매번 `GetBrush` 호출은 FName 해시 비용이 있으니, 자주 쓰는 브러시는 멤버에 캐시.

---

## 6. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `USlateWidgetStyleAsset` 🛠 | SlateWidgetStyleAsset.h L17 | UCLASS — 에디터에서 .uasset으로 편집 | 런타임에선 단순히 로드. |
| `USlateWidgetStyleContainerBase` 🛠 | SlateWidgetStyleContainerBase.h | UCLASS | UPROPERTY로 디테일 패널 노출. |
| `FStarshipCoreStyle` 🛠 (실용) | StarshipCoreStyle.h | (런타임에도 존재) | 주 용도가 에디터 — 게임 UI는 `FUMGCoreStyle` 권장. |
| `FAppStyle` 🛠 (실용) | AppStyle.h | (런타임에도 존재) | 에디터에선 `Starship`, 게임에선 `UMGCoreStyle` 을 가리킴 — 게임 코드에서는 명시적으로 `FUMGCoreStyle::Get()` 사용 권장. |
| `FSlateIconFinder` 🛠 | SlateIconFinder.h | 에디터 통합 위주 | 클래스 → 아이콘 매핑은 에디터 컨텍스트. |
| `IMAGE_BRUSH`/`BOX_BRUSH` 매크로의 `SetContentRoot` 🛠 | SlateStyleMacros.h | (에디터·런타임 모두) | 단, 콘텐츠 디렉토리 경로 해석은 빌드 환경에 따라 다름. |

런타임에서 안전한 API는 `FSlateStyleSet`, `FSlateBrush`, `FSlateColor`, `FCoreStyle::Get()`, `FUMGCoreStyle::Get()` 전부.

---

## 7. 관련 sub-skill

- [`Drawing/`](../Drawing/SKILL.md) — `FSlateBrush` 가 `FSlateDrawElement::MakeBox` 의 입력
- [`SWidget/`](../SWidget/SKILL.md) — `OnPaint` 의 `FWidgetStyle` 인자로 부모 색이 내려옴
- [`Text/`](../Text/SKILL.md) — `FSlateFontInfo` / `FTextBlockStyle`
- [`CoreUObject/UObject/`](../../CoreUObject/references/UObject.md) — `USlateWidgetStyleAsset` 라이프사이클
