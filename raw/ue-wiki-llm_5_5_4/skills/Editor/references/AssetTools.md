---
name: assettools-main
description: 🛠 AssetTools 모듈 - IAssetTools + IAssetTypeActions + FAssetTypeActions_Base + EAssetTypeCategories - 에셋 타입별 동작 등록.
---

# AssetTools Module 🛠

> **모듈**: `Engine/Source/Developer/AssetTools/` (Developer — 에디터 빌드 의존)
> **사이즈**: Public 21 헤더
> **카테고리**: `[Slate]` 인하우스 툴 (🛠 에디터 전용)
> **어셋 로드 정책**: 🚨 `IAssetTypeActions::OpenAssetEditor` / 메뉴 콜백 = Editor 순수 모드 → **동기 로드 (`TryLoad`) 표준** ([`11_AssetLoadingPolicy.md §3`](../../../references/11_AssetLoadingPolicy.md#3-환경-모드별-로드-정책--editor-pure-vs-pie-vs-cooked-game-)).

---

## 1. 개요

UE 에디터에서 **에셋 클래스별 동작** 을 정의하는 모듈. 각 에셋 타입(`UStaticMesh` / `UMaterial` / `UMyAsset` 등) 마다 `IAssetTypeActions` 자손을 등록 → 컨텐츠 브라우저가 해당 에셋의:

- 이름·색·카테고리·툴팁 표시
- 더블클릭 시 어떤 에디터 열지 (`OpenAssetEditor`)
- 우클릭 컨텍스트 메뉴 항목 (`GetActions`)
- 썸네일 / 인포 표시
- 복제·이름 변경·머지 가능성

을 결정한다.

> **5.1+ 후속**: `IAssetTypeActions` 의 후계 시스템이 `UAssetDefinition` (모듈 `AssetDefinition`). 본 sub-skill은 5.5.4 기준 — 두 시스템 공존.

---

## 2. 핵심 헤더

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `IAssetTools.h` | `IAssetTools` (인터페이스 L283) + `UAssetTools` (UInterface L273) | 글로벌 매니저 — `RegisterAssetTypeActions` 진입 |
| `IAssetTypeActions.h` | `IAssetTypeActions` (인터페이스 L27) | 에셋 타입별 동작 (40+ pure virtual) |
| `AssetTypeActions_Base.h` | `FAssetTypeActions_Base` (L24) | 베이스 구현 — 거의 항상 자손 작성 |
| `AssetTypeActions_CSVAssetBase.h` | `FAssetTypeActions_CSVAssetBase` | CSV 베이스 |
| `AssetTypeActions/` | (서브폴더) | 표준 에셋 타입별 액션 |
| `IClassTypeActions.h` | `IClassTypeActions` | 클래스 타입 (Actor 등) 액션 |
| `ClassTypeActions_Base.h` | `FClassTypeActions_Base` | 클래스 타입 베이스 |
| `AssetTypeCategories.h` | `EAssetTypeCategories` (enum) + `FAdvancedAssetCategory` | 메뉴 카테고리 비트마스크 |
| `AssetTypeActivationOpenedMethod.h` | `EAssetTypeActivationOpenedMethod` | 열기 방식 (Edit/View/Diff) |
| `AssetToolsModule.h` | `FAssetToolsModule` | 모듈 진입 |
| `AssetToolsSettings.h` | `UAssetToolsSettings` | 프로젝트 설정 |
| `AssetViewUtils.h` | 파일 경로 헬퍼 | |
| `CollectionAssetManagement.h` | `FCollectionAssetManagement` | 컨텐츠 브라우저 컬렉션 |
| `IAssetTypeActions.h` | `EAssetTypeActivationMethod` | 활성화 방식 (Open/Preview/Edit) |
| `AdvancedCopyCustomization.h` | `UAdvancedCopyCustomization` | 고급 복제 |
| `PackageMigrationContext.h` | `FPackageMigrationContext` | 패키지 마이그레이션 |
| `FindSourceFileInExplorer.h` | OS 헬퍼 | |
| `ILocalizedAssetTools.h` | 지역화 |

---

## 3. IAssetTools (글로벌 매니저)

### 3.1 핵심 API (IAssetTools.h L283)

| API | 라인 | 의미 |
|-----|------|------|
| `void RegisterAssetTypeActions(TSharedRef<IAssetTypeActions> NewActions)` | L293 | 에셋 타입 등록 |
| `void UnregisterAssetTypeActions(TSharedRef<IAssetTypeActions> ActionsToRemove)` | L296 | 해제 |
| `void GetAssetTypeActionsList(TArray<TWeakPtr<IAssetTypeActions>>& Out) const` | L299 | 목록 |
| `TWeakPtr<IAssetTypeActions> GetAssetTypeActionsForClass(const UClass*) const` | L302 | 클래스 → 액션 |
| `EAssetTypeCategories::Type RegisterAdvancedAssetCategory(FName Key, FText DisplayName)` | L317 | 새 카테고리 등록 |
| `EAssetTypeCategories::Type FindAdvancedAssetCategory(FName Key) const` | L320 | 카테고리 검색 |
| `void RegisterClassTypeActions(TSharedRef<IClassTypeActions>)` | L326 | 클래스 액션 |
| `bool CanLocalize(const UClass*) const` | L306 | 지역화 가능? |
| `TOptional<FLinearColor> GetTypeColor(const UClass*) const` | L308 | 타입 색 |

### 3.2 사용 패턴

```cpp
#if WITH_EDITOR
IAssetTools& AssetTools = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get();

// 새 카테고리 등록
EAssetTypeCategories::Type MyCategory = AssetTools.RegisterAdvancedAssetCategory(
    FName("MyGame"), LOCTEXT("MyGame", "My Game"));

// 에셋 타입 등록
TSharedRef<FMyAssetTypeActions> Action = MakeShared<FMyAssetTypeActions>(MyCategory);
AssetTools.RegisterAssetTypeActions(Action);
RegisteredActions.Add(Action);    // shutdown 시 해제용 보관

// Shutdown
for (TSharedRef<IAssetTypeActions> A : RegisteredActions)
{
    AssetTools.UnregisterAssetTypeActions(A);
}
#endif
```

---

## 4. IAssetTypeActions (에셋 타입별 동작)

### 4.1 PURE_VIRTUAL — 자손 의무 구현 (IAssetTypeActions.h)

| 시그니처 | 라인 | 의미 |
|----------|------|------|
| `virtual FText GetName() const = 0` | L40 | 표시 이름 |
| `virtual UClass* GetSupportedClass() const = 0` | L43 | 지원 클래스 |
| `virtual FColor GetTypeColor() const = 0` | L46 | 컨텐츠 브라우저 표시 색 |
| `virtual bool ShouldFindEditorForAsset() const = 0` | L61 | 더블클릭 시 에디터 검색? |
| `virtual void OpenAssetEditor(const TArray<UObject*>&, TSharedPtr<IToolkitHost>=nullptr) = 0` | L64 | 에디터 열기 — 가장 자주 override |
| `virtual void OpenAssetEditor(const TArray<UObject*>&, EAssetTypeActivationOpenedMethod, TSharedPtr<IToolkitHost>=nullptr) = 0` | L67 | 메서드 명시 |
| `virtual bool AssetsActivatedOverride(const TArray<UObject*>&, EAssetTypeActivationMethod::Type) = 0` | L70 | 더블클릭 가로채기 |
| `virtual bool CanRename(const FAssetData&, FText*) const = 0` | L73 | 이름 변경 |
| `virtual bool CanDuplicate(const FAssetData&, FText*) const = 0` | L76 | 복제 |
| `virtual TArray<FAssetData> GetValidAssetsForPreviewOrEdit(...)` | L79 | |
| `virtual bool CanFilter() = 0` | L82 | 필터 가능? |
| `virtual FName GetFilterName() const = 0` | L85 | 필터 이름 |
| `virtual bool CanLocalize() const = 0` | L88 | 지역화 가능? |
| `virtual bool CanMerge() const = 0` | L91 | 머지 가능? |
| `virtual void Merge(UObject*) = 0` | L94 | 단순 머지 |
| `virtual void Merge(UObject* Base, UObject* Remote, UObject* Local, const FOnMergeResolved&) = 0` | L97 | 3-way 머지 |
| `virtual uint32 GetCategories() = 0` | L100 | 카테고리 비트마스크 |
| `virtual FString GetObjectDisplayName(UObject*) const = 0` | L103 | 객체별 이름 |
| `virtual const TArray<FText>& GetSubMenus() const = 0` | L106 | 서브 메뉴 |
| `virtual bool ShouldForceWorldCentric() = 0` | L109 | WorldCentric 강제? |
| `virtual void PerformAssetDiff(UObject* Old, UObject* New, ...)` | L112 | 비교 |
| `virtual UThumbnailInfo* GetThumbnailInfo(UObject*) const = 0` | L115 | 썸네일 정보 |

> 위 PURE 들 대부분은 **`FAssetTypeActions_Base` 가 합리적 기본 구현 제공** — 자손은 필요한 것만 override.

### 4.2 자주 override (FAssetTypeActions_Base 기본 위)

| 메서드 | 자주 override? | 메모 |
|--------|---------------|------|
| `GetName()` | ✅ | 표시 이름 |
| `GetSupportedClass()` | ✅ | 클래스 |
| `GetTypeColor()` | ✅ | 색 |
| `OpenAssetEditor` | ✅ | 커스텀 에디터 |
| `GetCategories()` | ✅ | 카테고리 |
| `GetActions(TArray<UObject*>, FToolMenuSection&)` | (선택) | 컨텍스트 메뉴 |
| `IsImportedAsset()` | (필요 시) | 임포트 에셋인지 |
| `GetThumbnailInfo()` | (필요 시) | 커스텀 썸네일 |
| `CanReimport()` (`FReimportHandler` 다중 상속 시) | | 재임포트 |

---

## 5. FAssetTypeActions_Base (베이스 구현)

`AssetTypeActions_Base.h` L24 — `IAssetTypeActions` 의 합리적 기본. 자손은 필요한 메서드만 override.

기본 동작:
- `OpenAssetEditor` (L39) — `FSimpleAssetEditor::CreateEditor` 호출 (디테일 패널만)
- `GetObjectDisplayName` — `Object->GetName()` 반환
- `CanRename`/`CanDuplicate` — true
- `CanFilter`/`CanLocalize`/`CanMerge` — false
- `IsImportedAsset` — false
- `GetThumbnailInfo` — nullptr
- `GetSubMenus` — 빈 배열

---

## 6. EAssetTypeCategories (카테고리 비트마스크)

`AssetTypeCategories.h`:

```cpp
namespace EAssetTypeCategories
{
    enum Type
    {
        None        = 0,
        Basic       = 1<<0,
        Animation   = 1<<1,
        MaterialsAndTextures = 1<<2,
        Sounds      = 1<<3,
        Physics     = 1<<4,
        UI          = 1<<5,
        Misc        = 1<<6,
        Gameplay    = 1<<7,
        Blueprint   = 1<<8,
        Media       = 1<<9,
        World       = 1<<10,
        // ... AdvancedAssetCategory 등록 시 1<<16+ 사용
    };
}
```

---

## 7. 작성 패턴 (커스텀 에셋 액션)

```cpp
#if WITH_EDITOR
class FMyAssetTypeActions : public FAssetTypeActions_Base
{
public:
    FMyAssetTypeActions(EAssetTypeCategories::Type InCategory) : Category(InCategory) {}

    // PURE 4종
    virtual FText GetName() const override { return LOCTEXT("MyAsset", "My Asset"); }
    virtual UClass* GetSupportedClass() const override { return UMyAsset::StaticClass(); }
    virtual FColor GetTypeColor() const override { return FColor(50, 150, 200); }
    virtual uint32 GetCategories() override { return Category; }

    // 커스텀 에디터 열기
    virtual void OpenAssetEditor(const TArray<UObject*>& InObjects, TSharedPtr<IToolkitHost> EditWithinLevelEditor) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(FMyAssetTypeActions_OpenAssetEditor);
        EToolkitMode::Type Mode = EditWithinLevelEditor.IsValid() ? EToolkitMode::WorldCentric : EToolkitMode::Standalone;
        for (UObject* Obj : InObjects)
        {
            if (UMyAsset* Asset = Cast<UMyAsset>(Obj))
            {
                TSharedRef<FMyAssetEditor> Editor = MakeShared<FMyAssetEditor>();
                Editor->InitMyAssetEditor(Mode, EditWithinLevelEditor, Asset);
            }
        }
    }

    // 컨텍스트 메뉴 항목 추가 (5.x — FToolMenuSection)
    virtual void GetActions(const TArray<UObject*>& InObjects, FToolMenuSection& Section) override
    {
        TArray<TWeakObjectPtr<UMyAsset>> Assets = GetTypedWeakObjectPtrs<UMyAsset>(InObjects);
        Section.AddMenuEntry(
            "ProcessMyAsset",
            LOCTEXT("ProcessMyAsset", "Process"),
            LOCTEXT("ProcessMyAssetTip", "Process selected"),
            FSlateIcon(),
            FUIAction(FExecuteAction::CreateLambda([Assets]()
            {
                TRACE_CPUPROFILER_EVENT_SCOPE(FMyAssetTypeActions_Process);
                // ...
            })));
    }

private:
    EAssetTypeCategories::Type Category;
};
#endif
```

---

## 8. 가상 함수 / Super 호출

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `IAssetTypeActions::*` | (override 시 자체 처리) | pure virtual 다수 |
| `FAssetTypeActions_Base::OpenAssetEditor` | (override 시 자체 처리 — Super 호출 X) | 기본은 SimpleAssetEditor — 사용자는 자체 구현 |
| `FAssetTypeActions_Base::GetActions` | (선택) | 베이스가 빈 구현 — Super 호출 무의미 |
| `IModuleInterface::StartupModule` (자손) | (override 시 RegisterAssetTypeActions 호출) | |

---

## 9. 함정

| 함정 | 회피 |
|------|------|
| `RegisterAssetTypeActions` 결과 보관 안 함 | Shutdown 시 `UnregisterAssetTypeActions` 호출 위해 `TArray<TSharedRef<IAssetTypeActions>>` 보관 |
| `GetCategories()` 가 0 반환 | 컨텐츠 브라우저 "Add New" 메뉴에 안 나타남 |
| `OpenAssetEditor` 안 무거운 작업에 스코프 누락 | [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) — `TRACE_CPUPROFILER_EVENT_SCOPE` |
| `GetActions` 의 람다에 강한 객체 캡처 | TWeakObjectPtr 또는 `GetTypedWeakObjectPtrs<T>` 사용 |
| 5.x — 컨텍스트 메뉴는 FToolMenuSection만 사용 | 4.x의 `GetActions(..., FMenuBuilder&)` 는 deprecated 경로 |
| `IAssetTools` 직접 캐스팅 | `FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get()` 사용 |
| `IsImportedAsset` true 인데 `FReimportHandler` 미상속 | 다중 상속 + `CanReimport`/`SetReimportPaths`/`Reimport` 구현 |
| 5.1+ 신규 시스템 (UAssetDefinition) 무시 | 두 시스템 공존 — UAssetDefinition 도 검토 |

---

## 10. UAssetDefinition (5.1+ 신규 후속)

`AssetDefinition` 모듈 (별도 모듈, 미마운트) 의 `UAssetDefinition` 베이스가 `IAssetTypeActions` 후속. 5.x 권장. 작동 방식이 비슷하나 UCLASS 라 BP/Python 노출 가능.

---

## 11. 에디터 전용 🛠

전체 모듈 에디터 빌드 전용. 4단 분리 — [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md).

---

## 12. 관련 sub-skill

- [`UnrealEd/AssetEditorToolkit`](../UnrealEd/AssetEditorToolkit/SKILL.md) — `OpenAssetEditor` 가 호출하는 베이스
- [`UnrealEd/Subsystems`](../UnrealEd/Subsystems/SKILL.md) — `UAssetEditorSubsystem` (외부에서 호출 시 라우팅)
- [`UnrealEd/Factories`](../UnrealEd/Factories/SKILL.md) — `UFactory` (Add New / Import)
- [`ToolMenus`](../ToolMenus/SKILL.md) — `GetActions(..., FToolMenuSection&)` 5.x 패턴
- [`Slate/Menu`](../Slate/