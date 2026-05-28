---
name: propertyeditor-main
description: 🛠 PropertyEditor 모듈 - IDetailCustomization + IPropertyTypeCustomization + IDetailLayoutBuilder + IPropertyHandle + FPropertyEditorModule.
---

# PropertyEditor Module 🛠

> **모듈**: `Engine/Source/Editor/PropertyEditor/` (Editor 전용)
> **사이즈**: Public 68 헤더
> **카테고리**: `[Slate]` 인하우스 툴 (🛠 에디터 전용)
> **어셋 로드 정책**: 🚨 디테일 패널 커스터마이징 = Editor 순수 모드 → **동기 로드 (`LoadSynchronous` / `TryLoad`) 표준** ([`11_AssetLoadingPolicy.md §3`](../../../references/11_AssetLoadingPolicy.md#3-환경-모드별-로드-정책--editor-pure-vs-pie-vs-cooked-game-)). `IDetailCustomization::CustomizeDetails` 안 비동기 콜백 = UI race 위험.

---

## 1. 개요

UE 에디터의 **디테일 패널** (Details Panel) 을 구성하는 시스템. 모든 에디터 (레벨/에셋/BP) 의 우측 디테일 패널이 본 모듈로 만들어진다. 사용자 정의 위젯·검증·동적 레이아웃 등 **디테일 패널 커스터마이징** 의 진입점.

**두 가지 커스터마이징**:
1. **클래스 단위 (`IDetailCustomization`)** — 특정 UCLASS 의 디테일 패널 전체 레이아웃 변경
2. **타입 단위 (`IPropertyTypeCustomization`)** — 특정 USTRUCT/UPROPERTY 타입의 표시 변경 (예: `FVector` 한 줄 표시)

> 본 sub-skill은 **자주 사용하는 핵심**(Customization·DetailsView·PropertyHandle) 위주로 다룸. PropertyTable / PropertyTree / 단일 프로퍼티 뷰 등의 보조 시스템은 §10 에 한 줄 요약.

---

## 2. 카테고리별 헤더 (68개)

| 카테고리 | 핵심 헤더 |
|----------|----------|
| **Customization 인터페이스** | `IDetailCustomization.h` · `IPropertyTypeCustomization.h` · `IDetailRootObjectCustomization.h` · `IDetailDragDropHandler.h` · `IDetailKeyframeHandler.h` · `IDetailPropertyExtensionHandler.h` · `IDetailPropertyChildrenCustomizationHandler.h` · `DetailsNameWidgetOverrideCustomization.h` |
| **Builder (Customization 안에서 사용)** | `IDetailLayoutBuilder.h` · `IDetailChildrenBuilder.h` · `IDetailCustomNodeBuilder.h` · `DetailLayoutBuilder.h` · `DetailCategoryBuilder.h` · `DetailWidgetRow.h` · `DetailBuilderTypes.h` |
| **Property Handle** | `PropertyHandle.h` · `IPropertyHandle` (in handle) · `PropertyChangeListener.h` · `IPropertyChangeListener.h` |
| **Details View** | `IDetailsView.h` · `DetailsViewArgs.h` · `DetailsViewObjectFilter.h` · `DetailsViewStyleKey.h` · `DetailsDisplayManager.h` · `DetailColumnSizeData.h` · `DetailRowMenuContext.h` · `DetailTreeNode.h` · `IDetailTreeNode.h` |
| **Single Property** | `ISinglePropertyView.h` |
| **Property Row Generator** | `IPropertyRowGenerator.h` |
| **Property Group** | `IDetailGroup.h` · `IDetailPropertyRow.h` |
| **Async Diff** | `AsyncDetailViewDiff.h` |
| **Property Table** (별도) | `IPropertyTable*.h` (10+) |
| **Property Tree** (별도) | `IPropertyTreeRow.h` |
| **Editor Conditions** | `EditConditionParser.h` · `IEditConditionParser.h` |
| **Style** | `PropertyEditorStyle.h` (private) |
| **모듈** | `PropertyEditorModule.h` · `PropertyEditorDelegates.h` |
| **Utilities** | `IPropertyUtilities.h` · `IPropertyDetailsUtilities.h` · `IPropertyTypeCustomization.h` (의 `IPropertyTypeCustomizationUtils`) |

---

## 3. FPropertyEditorModule (등록 진입)

`PropertyEditorModule.h` L238

| API | 라인 | 의미 |
|-----|------|------|
| `void RegisterCustomClassLayout(FName ClassName, FOnGetDetailCustomizationInstance Delegate, FRegisterCustomClassLayoutParams=...)` | L283 | 클래스 단위 커스터마이징 등록 |
| `void RegisterCustomPropertyTypeLayout(FName PropertyTypeName, FOnGetPropertyTypeCustomizationInstance Delegate, TSharedPtr<IPropertyTypeIdentifier>=nullptr)` | L300 | 타입 단위 커스터마이징 등록 |
| `void UnregisterCustomClassLayout(FName ClassName)` | (헤더) | 해제 |
| `void UnregisterCustomPropertyTypeLayout(FName PropertyTypeName)` | (헤더) | 해제 |
| `TSharedRef<IDetailsView> CreateDetailView(const FDetailsViewArgs&)` | (헤더) | 디테일 뷰 위젯 생성 |
| `TSharedRef<ISinglePropertyView> CreateSingleProperty(...)` | (헤더) | 단일 프로퍼티 뷰 |
| `TSharedRef<IPropertyRowGenerator> CreatePropertyRowGenerator(const FPropertyRowGeneratorArgs&)` | (헤더) | 행 생성기 |

### 3.1 사용 패턴

```cpp
#if WITH_EDITOR
void FMyEditorModule::StartupModule()
{
    FPropertyEditorModule& PropertyModule = FModuleManager::LoadModuleChecked<FPropertyEditorModule>("PropertyEditor");

    // 클래스 단위 — 특정 UCLASS의 디테일 레이아웃
    PropertyModule.RegisterCustomClassLayout(
        UMyAsset::StaticClass()->GetFName(),
        FOnGetDetailCustomizationInstance::CreateStatic(&FMyAssetCustomization::MakeInstance));

    // 타입 단위 — 특정 USTRUCT
    PropertyModule.RegisterCustomPropertyTypeLayout(
        FMyStruct::StaticStruct()->GetFName(),
        FOnGetPropertyTypeCustomizationInstance::CreateStatic(&FMyStructCustomization::MakeInstance));

    PropertyModule.NotifyCustomizationModuleChanged();
}

void FMyEditorModule::ShutdownModule()
{
    if (FPropertyEditorModule* PropertyModule = FModuleManager::GetModulePtr<FPropertyEditorModule>("PropertyEditor"))
    {
        PropertyModule->UnregisterCustomClassLayout(UMyAsset::StaticClass()->GetFName());
        PropertyModule->UnregisterCustomPropertyTypeLayout(FMyStruct::StaticStruct()->GetFName());
    }
}
#endif
```

---

## 4. IDetailCustomization (클래스 단위)

### 4.1 인터페이스 (IDetailCustomization.h L11)

```cpp
class IDetailCustomization : public TSharedFromThis<IDetailCustomization>
{
public:
    virtual ~IDetailCustomization() {}
    virtual void PendingDelete() {}
    virtual void CustomizeDetails(IDetailLayoutBuilder& DetailBuilder) = 0;            // PURE — 메인
    virtual void CustomizeDetails(const TSharedPtr<IDetailLayoutBuilder>& DetailBuilder) { CustomizeDetails(*DetailBuilder); }
};
```

### 4.2 작성 패턴

```cpp
#if WITH_EDITOR
class FMyAssetCustomization : public IDetailCustomization
{
public:
    static TSharedRef<IDetailCustomization> MakeInstance() { return MakeShared<FMyAssetCustomization>(); }

    virtual void CustomizeDetails(IDetailLayoutBuilder& DetailBuilder) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(FMyAssetCustomization_CustomizeDetails);

        // 카테고리 가져오기
        IDetailCategoryBuilder& Category = DetailBuilder.EditCategory("MyCategory", LOCTEXT("Cat", "My Settings"));

        // 프로퍼티 핸들 가져오기
        TSharedRef<IPropertyHandle> Handle = DetailBuilder.GetProperty(GET_MEMBER_NAME_CHECKED(UMyAsset, MyProperty));

        // 사용자 정의 위젯으로 행 추가
        Category.AddCustomRow(LOCTEXT("MyFilter", "My Filter"))
            .NameContent()[ SNew(STextBlock).Text(LOCTEXT("MyName", "My Name")) ]
            .ValueContent()[
                SNew(SButton)
                .Text(LOCTEXT("Click", "Click Me"))
                .OnClicked_Lambda([Handle]()
                {
                    TRACE_CPUPROFILER_EVENT_SCOPE(FMyAssetCustomization_OnClicked);
                    int32 Value = 0;
                    Handle->GetValue(Value);
                    Handle->SetValue(Value + 1);
                    return FReply::Handled();
                })
            ];

        // 프로퍼티 숨김
        DetailBuilder.HideProperty(GET_MEMBER_NAME_CHECKED(UMyAsset, HiddenProperty));
    }
};
#endif
```

---

## 5. IPropertyTypeCustomization (타입 단위)

### 5.1 인터페이스 (IPropertyTypeCustomization.h L27)

```cpp
class IPropertyTypeCustomization
{
public:
    virtual ~IPropertyTypeCustomization() {}

    // PURE — 헤더(접힌 상태) 표시
    virtual void CustomizeHeader(TSharedRef<IPropertyHandle> PropertyHandle, FDetailWidgetRow& HeaderRow, IPropertyTypeCustomizationUtils& CustomizationUtils) = 0;

    // PURE — 자식(펼친 상태) 표시
    virtual void CustomizeChildren(TSharedRef<IPropertyHandle> PropertyHandle, IDetailChildrenBuilder& ChildBuilder, IPropertyTypeCustomizationUtils& CustomizationUtils) = 0;

    virtual bool ShouldInlineKey() const { return false; }
};
```

### 5.2 IStructCustomization (편의 변형)

`IStructCustomization` (L97) — `CustomizeStructHeader` / `CustomizeStructChildren` 으로 분리. 주로 USTRUCT 커스터마이징에 사용.

### 5.3 작성 패턴 (USTRUCT)

```cpp
USTRUCT()
struct FMyStruct
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere) float X;
    UPROPERTY(EditAnywhere) float Y;
};

#if WITH_EDITOR
class FMyStructCustomization : public IPropertyTypeCustomization
{
public:
    static TSharedRef<IPropertyTypeCustomization> MakeInstance() { return MakeShared<FMyStructCustomization>(); }

    virtual void CustomizeHeader(TSharedRef<IPropertyHandle> PropertyHandle, FDetailWidgetRow& HeaderRow, IPropertyTypeCustomizationUtils& CustomizationUtils) override
    {
        // 한 줄 표시: "X: 1.0  Y: 2.0"
        TSharedPtr<IPropertyHandle> XHandle = PropertyHandle->GetChildHandle("X");
        TSharedPtr<IPropertyHandle> YHandle = PropertyHandle->GetChildHandle("Y");

        HeaderRow
        .NameContent()[ PropertyHandle->CreatePropertyNameWidget() ]
        .ValueContent().MinDesiredWidth(200.0f)[
            SNew(SHorizontalBox)
            +SHorizontalBox::Slot().AutoWidth()[ XHandle->CreatePropertyValueWidget() ]
            +SHorizontalBox::Slot().AutoWidth()[ YHandle->CreatePropertyValueWidget() ]
        ];
    }

    virtual void CustomizeChildren(TSharedRef<IPropertyHandle> PropertyHandle, IDetailChildrenBuilder& ChildBuilder, IPropertyTypeCustomizationUtils&) override
    {
        // 펼친 상태에서는 기본 레이아웃 사용
        uint32 NumChildren;
        PropertyHandle->GetNumChildren(NumChildren);
        for (uint32 i = 0; i < NumChildren; i++)
        {
            ChildBuilder.AddProperty(PropertyHandle->GetChildHandle(i).ToSharedRef());
        }
    }
};
#endif
```

---

## 6. IPropertyHandle (프로퍼티 접근)

`IPropertyHandle` 은 디테일 패널 안에서 UPROPERTY 에 접근하는 추상 핸들.

| API | 의미 |
|-----|------|
| `FPropertyAccess::Result GetValue<T>(T& OutValue)` | 값 읽기 |
| `FPropertyAccess::Result SetValue(const T& InValue, EPropertyValueSetFlags::Type=Default)` | 값 쓰기 |
| `TSharedPtr<IPropertyHandle> GetChildHandle(FName Name)` | 자식 (USTRUCT 멤버) |
| `void GetNumChildren(uint32& OutNum)` | 자식 수 |
| `FProperty* GetProperty() const` | FProperty 접근 |
| `int32 GetIndexInArray() const` | 배열 인덱스 |
| `bool IsValidHandle() const` | 유효성 |
| `TSharedRef<SWidget> CreatePropertyNameWidget()` | 이름 위젯 |
| `TSharedRef<SWidget> CreatePropertyValueWidget()` | 값 위젯 (기본 편집) |
| `void NotifyPreChange()` / `NotifyPostChange(EPropertyChangeType::Type)` | 변경 통지 |
| `FOnPropertyValueChanged GetOnPropertyValueChanged()` | 변경 옵서버 |

---

## 7. IDetailLayoutBuilder (커스터마이징 안에서 사용)

| API | 의미 |
|-----|------|
| `IDetailCategoryBuilder& EditCategory(FName CategoryName, FText DisplayName=GetEmpty, ECategoryPriority::Type=Default)` | 카테고리 가져오기/생성 |
| `TSharedRef<IPropertyHandle> GetProperty(FName PropertyPath, UClass* ClassOuter=nullptr)` | 프로퍼티 핸들 |
| `void HideProperty(FName PropertyPath, UClass* ClassOuter=nullptr)` | 숨김 |
| `void HideCategory(FName)` | 카테고리 숨김 |
| `IPropertyChangeListener& GetPropertyChangeListener()` | 변경 옵서버 |
| `const TArray<TWeakObjectPtr<UObject>>& GetSelectedObjects() const` | 선택된 객체들 |
| `void ForceRefreshDetails()` | 강제 리프레시 |

---

## 8. IDetailCategoryBuilder

| API | 의미 |
|-----|------|
| `IDetailPropertyRow& AddProperty(TSharedPtr<IPropertyHandle>)` | 표준 프로퍼티 행 |
| `FDetailWidgetRow& AddCustomRow(FText FilterString, bool bForAdvanced=false)` | 사용자 정의 위젯 |
| `IDetailGroup& AddGroup(FName GroupName, FText DisplayName, bool bStartExpanded=false, bool bAdvanced=false)` | 그룹 (펼침/접힘) |
| `void AddPropertyExternalObjects(...)` | 외부 객체의 프로퍼티 |

---

## 9. IDetailsView (디테일 뷰 위젯)

`IDetailsView.h` — 디테일 패널 위젯 인터페이스. `FAssetEditorToolkit` 자손에서 자체 디테일 뷰 만들 때 사용 ([`UnrealEd/AssetEditorToolkit`](../UnrealEd/AssetEditorToolkit/SKILL.md) §5.3 예제).

```cpp
FDetailsViewArgs Args;
Args.bAllowSearch = true;
Args.bShowOptions = true;
Args.bUpdatesFromSelection = false;
TSharedRef<IDetailsView> View = PropertyModule.CreateDetailView(Args);
View->SetObject(MyAsset);
```

---

## 10. 보조 시스템 (한 줄 요약)

| 시스템 | 의미 |
|--------|------|
| `IPropertyTable*` (10+ 헤더) | 표 형식 프로퍼티 표시 (스프레드시트) |
| `IPropertyTreeRow.h` | 트리 형식 (디테일 뷰의 베이스) |
| `ISinglePropertyView.h` | 단일 프로퍼티만 표시 |
| `IPropertyRowGenerator.h` | 디테일 뷰 외부에서 프로퍼티 행 생성 |
| `IDetailGroup.h` | 그룹 (펼침/접힘) 인터페이스 |
| `IDetailKeyframeHandler.h` | 키프레임 (시퀀서 통합) |
| `IDetailDragDropHandler.h` | 드래그앤드롭 |
| `IDetailPropertyExtensionHandler.h` | 프로퍼티 확장 (추가 위젯) |
| `IDetailRootObjectCustomization.h` | 루트 객체 커스터마이징 |
| `EditConditionParser.h` | `EditCondition` 메타키 파서 |
| `AsyncDetailViewDiff.h` | 비동기 비교 |

---

## 11. 가상 함수 / Super 호출

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `IDetailCustomization::CustomizeDetails(IDetailLayoutBuilder&)` | (override 시 자체 처리) | PURE |
| `IDetailCustomization::PendingDelete()` | (선택) | 소멸 직전 |
| `IPropertyTypeCustomization::CustomizeHeader/Children` | (override 시 자체 처리) | PURE |
| `IDetailRootObjectCustomization::*` | (override 시 자체 처리) | |
| `IModuleInterface::StartupModule` (자손) | (override 시 RegisterCustomClassLayout 호출) | |

---

## 12. 함정

| 함정 | 회피 |
|------|------|
| `RegisterCustomClassLayout` 후 `NotifyCustomizationModuleChanged` 누락 | 호출 시점에 따라 디테일 패널 갱신 안 됨 — 호출 의무 |
| Shutdown 시 `Unregister*` 누락 | 모듈 리로드 시 콜백 충돌 |
| `IPropertyHandle::SetValue` 후 NotifyPostChange 누락 | UPROPERTY 변경 통지 미발화 → 옵저버 미실행 |
| `CustomizeDetails` 안에서 무거운 작업 | 디테일 뷰 리프레시 시마다 호출 — 가벼운 빌드 + 무거운 건 `OnPropertyValueChanged` 콜백 |
| `OnClicked_Lambda` 등 람다에 강한 캡처 | TSharedPtr 캡처 + 스코프 |
| `NotifyCustomizationModuleChanged` 과도 호출 | 디테일 패널 깜빡임 — 일괄 등록 후 1회 |
| `GetProperty(GET_MEMBER_NAME_CHECKED(...))` 가 invalid handle 반환 | 클래스 outer 명시 (다중 상속·인터페이스) |
| 람다 / 콜백 스코프 누락 | [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) — `OnClicked_Lambda`/`OnPropertyValueChanged` 등 모두 |
| 5.x ToolMenus 와 혼용 | DetailRowMenuContext 가 ToolMenus 통합 — 우클릭 메뉴는 ToolMenus |

---

## 13. 에디터 전용 🛠

전체 모듈 에디터 빌드 전용. 4단 분리 — [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md).

---

## 14. 관련 sub-skill

- [`UnrealEd/AssetEditorToolkit`](../UnrealEd/AssetEditorToolkit/SKILL.md) — `CreateDetailView` 사용 (§5.3 예제)
- [`UnrealEd/Subsystems`](../UnrealEd/Subsystems/SKILL.md) — `UPropertyVisibilityOverrideSubsystem` (가시성 오버라이드)
- [`CoreUObject/Editor`](../CoreUObject/references/Editor.md) — `PostEditChangeProperty` (디테일 패널 변경 후)
- [`CoreUObject/Property`](../CoreUObject/references/Property.md) — FProperty 베이스
- [`CoreUObject/Reflection`](../CoreUObject/ref