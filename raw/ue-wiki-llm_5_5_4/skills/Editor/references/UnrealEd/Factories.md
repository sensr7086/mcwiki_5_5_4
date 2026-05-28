---
name: unrealed-factories
description: 🛠 UFactory + UFactoryNew + ImportNew + 새 에셋 생성.
---

# UnrealEd · Factories sub-skill 🛠

> **모듈**: UnrealEd (Editor 전용)
> **위치**: `Engine/Source/Editor/UnrealEd/Classes/Factories/` (111개) + `Classes/ActorFactories/` + `Classes/Exporters/` + `Public/AutoReimport/`
> **다루는 범위**: Asset 임포트/생성/내보내기 파이프라인 + 액터 배치 팩토리 — `UFactory` · `UActorFactory` · `UExporter` + Reimport + Interchange 통합.
> **어셋 로드 정책**: 🚨 `UFactory::FactoryCreateNew` / `ImportObject` 등 = Editor 순수 모드 → **동기 로드 (`TryLoad`) 표준** ([`11_AssetLoadingPolicy.md §3`](../../../../references/11_AssetLoadingPolicy.md#3-환경-모드별-로드-정책--editor-pure-vs-pie-vs-cooked-game-)).

---

## 1. 개요

UE 에디터의 **에셋 생성/임포트/내보내기 추상화**:

- `UFactory` — 외부 파일/Make-from-scratch → UObject (`Right Click > Import` / `Add New > ...`)
- `UActorFactory` — Asset → 레벨에 액터 배치 (드래그앤드롭 / `Place Actors` 탭)
- `UExporter` — UObject → 외부 파일
- `Interchange` (5.x 신규) — `UFactory` 의 차세대 대체 — fbx/obj/usd 임포트 통합 (`InterchangeCore`/`InterchangeEngine` 모듈)

**5.x 권장**: 신규 임포터는 **Interchange** 사용. 기존 UFactory는 호환을 위해 유지.

---

## 2. 핵심 헤더

| 클래스 | 헤더 | 메모 |
|--------|------|------|
| `UFactory` | `Classes/Factories/Factory.h` | 모든 임포터·"Add New" 의 베이스 |
| `UActorFactory` | `Classes/ActorFactories/ActorFactory.h` | 모든 액터 배치 팩토리 베이스 |
| `UExporter` | `Classes/Exporters/Exporter.h` | UObject → 파일 |
| `UAutomatedAssetImportData` | `Classes/AutomatedAssetImportData.h` | CLI 자동 임포트 |
| `UReimportFactory` (인터페이스 ref) | `Classes/Factories/Factory.h` 의 `FReimportHandler` | Reimport 지원 |
| `UFactory` 자손 (예시) | 111개 (Anim/Texture2D/Material/Sound/...) | 빌트인 |
| `UActorFactory` 자손 (예시) | ActorFactoryAmbientSound·BasicShape·Blueprint·Character·Class·Light·Pawn·StaticMesh 등 50+ | 빌트인 |

---

## 3. UFactory — Asset 임포터/생성기

### 3.1 핵심 virtual (Factory.h)

| 시그니처 | 라인 | 의미 |
|----------|------|------|
| `virtual bool CanCreateNew() const` | L54 | "Add New" 메뉴 표시? |
| `virtual bool FactoryCanImport(const FString& Filename)` | L64 | 확장자 검사 |
| `virtual bool CanImportBeCanceled() const` | L72 | 사용자가 취소 가능? |
| `virtual UObject* FactoryCreateFile(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, const FString& Filename, const TCHAR* Parms, FFeedbackContext* Warn, bool& bOutOperationCanceled)` | L102 | **파일 → UObject** (가장 자주 override) |
| `virtual UObject* FactoryCreateNew(...)` | L116 / L132 | **빈 객체 생성** (Add New 시) |
| `virtual UObject* ImportObject(UClass*, UObject*, FName, EObjectFlags, const FString& Filename, const TCHAR* Parms, bool& OutCanceled)` | L137 | 라우팅 헬퍼 (FactoryCreateFile 호출) |
| `virtual bool ShouldShowInNewMenu() const` | L155 | "Add New" 메뉴? |
| `virtual FText GetDisplayName() const` | L164 | 메뉴 이름 |
| `virtual uint32 GetMenuCategories() const` | L167 | 메뉴 카테고리 비트마스크 |
| `virtual const TArray<FText>& GetMenuCategorySubMenus() const` | L170 | 서브 메뉴 |
| `virtual FText GetToolTip() const` | L173 | 툴팁 |
| `virtual bool DoesSupportClass(UClass* Class)` | L189 | 지원 클래스? |
| `virtual UClass* ResolveSupportedClass()` | L195 | 지원 클래스 반환 |
| `virtual bool ConfigureProperties()` | L198 | 임포트 설정 다이얼로그 |
| `virtual bool ConfigurePropertiesAsync(...)` | L211 | 비동기 설정 (5.x) |

### 3.2 작성 패턴 (커스텀 임포터)

```cpp
#if WITH_EDITOR
UCLASS()
class MYGAMEEDITOR_API UMyAssetFactory : public UFactory
{
    GENERATED_BODY()
public:
    UMyAssetFactory()
    {
        bCreateNew = true;       // Add New 메뉴
        bEditAfterNew = true;    // 생성 후 자동 열기
        bEditorImport = true;    // 임포트 가능
        SupportedClass = UMyAsset::StaticClass();
        Formats.Add(TEXT("myext;My Custom Asset"));    // 확장자
    }

    virtual UObject* FactoryCreateFile(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags,
        const FString& Filename, const TCHAR* Parms, FFeedbackContext* Warn, bool& bOutOperationCanceled) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyAssetFactory_FactoryCreateFile);    // ← 스코프
        UMyAsset* NewAsset = NewObject<UMyAsset>(InParent, InClass, InName, Flags);
        // ... 파일 파싱 + 데이터 채우기
        return NewAsset;
    }

    virtual UObject* FactoryCreateNew(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn) override
    {
        return NewObject<UMyAsset>(InParent, InClass, InName, Flags);
    }

    virtual bool FactoryCanImport(const FString& Filename) override
    {
        return FPaths::GetExtension(Filename).Equals(TEXT("myext"), ESearchCase::IgnoreCase);
    }

    virtual FText GetDisplayName() const override { return NSLOCTEXT("MyEditor", "FactoryName", "My Asset"); }
};
#endif
```

---

## 4. FReimportHandler 인터페이스 (재임포트)

```cpp
class UMyAssetFactory : public UFactory, public FReimportHandler
{
    // FReimportHandler interface
    virtual bool CanReimport(UObject* Obj, TArray<FString>& OutFilenames) override;
    virtual void SetReimportPaths(UObject* Obj, const TArray<FString>& NewReimportPaths) override;
    virtual EReimportResult::Type Reimport(UObject* Obj) override;
};
```

`CanReimport` 가 true 반환하면 컨텐츠 브라우저 우클릭 → "Reimport" 메뉴 활성화.

---

## 5. UActorFactory — 액터 배치 팩토리

### 5.1 핵심 virtual (ActorFactory.h)

| 시그니처 | 라인 | 의미 |
|----------|------|------|
| `virtual bool CanCreateActorFrom(const FAssetData& AssetData, FText& OutErrorMsg)` | L67 | 이 에셋으로 액터 생성 가능? |
| `virtual AActor* GetDefaultActor(const FAssetData& AssetData)` | L73 | 기본 액터 인스턴스 |
| `virtual UClass* GetDefaultActorClass(const FAssetData& AssetData)` | L76 | 기본 액터 클래스 |
| `virtual UObject* GetAssetFromActorInstance(AActor* ActorInstance)` | L83 | 역방향 — 액터 → 에셋 |
| `virtual FQuat AlignObjectToSurfaceNormal(...)` | L86 | 표면 법선 정렬 |
| `virtual bool CanPlaceElementsFromAssetData(const FAssetData&)` | L89 | 5.x Element System |
| `virtual TArray<FTypedElementHandle> PlaceAsset(...)` | L91 | 5.x Element System 배치 |
| `virtual bool PreSpawnActor(UObject* Asset, FTransform& InOutLocation)` | L106 | 스폰 직전 |
| `virtual AActor* SpawnActor(UObject*, ULevel*, const FTransform&, const FActorSpawnParameters&)` | L108 | 실제 스폰 |
| `virtual void PostSpawnActor(UObject*, AActor*)` | (헤더) | 스폰 후 (자식이 자주 override) |

### 5.2 등록

```cpp
// MyGameEditorModule.cpp StartupModule
GEditor->ActorFactories.Add(NewObject<UMyActorFactory>());
```

---

## 6. UExporter — UObject → 파일

| 시그니처 | 의미 |
|----------|------|
| `virtual bool ExportText(const FExportObjectInnerContext*, UObject* Object, const TCHAR* Type, FOutputDevice& Out, FFeedbackContext* Warn, uint32 PortFlags=0)` | 텍스트 내보내기 |
| `virtual bool ExportBinary(UObject* Object, const TCHAR* Type, FArchive& Ar, FFeedbackContext* Warn, int32 FileIndex=0, uint32 PortFlags=0)` | 바이너리 내보내기 |
| `virtual int32 GetFileCount()` | 다중 파일 |
| `virtual FString GetUniqueFilename(const TCHAR* Filename, int32 FileIndex, int32 FileCount)` | 파일명 생성 |

---

## 7. Interchange (5.x 신규) — 향후 권장

기존 `UFactory` 대신 5.x Interchange 시스템 사용 권장:
- `UInterchangeFactoryBase` — Interchange 팩토리 베이스
- `UInterchangePipelineBase` — 임포트 파이프라인
- `UInterchangeTranslatorBase` — 파일 → Interchange Node 변환
- 모듈: `InterchangeCore` · `InterchangeEngine` · `InterchangeImport` (별도)

본 sub-skill 범위 외. 신규 임포터 작성 시 Interchange 검토 권장.

---

## 8. AutoReimport (Public/AutoReimport/)

파일 변경 감지 후 자동 재임포트. `FAutoReimportManager` (Private) — 사용자 설정 기반.

---

## 9. Super 호출 / 함정

| virtual | Super | 의미 |
|---------|-------|------|
| `UFactory::FactoryCreateFile` | (override 시 자체 처리) | 베이스가 ImportObject 라우팅 |
| `UFactory::FactoryCreateNew` | (override 시 자체 처리) | |
| `UActorFactory::PostSpawnActor` | **FIRST** | 베이스가 기본 컴포넌트 셋업 |
| `UActorFactory::PreSpawnActor` | **FIRST** | 위치 보정 |

| 함정 | 회피 |
|------|------|
| `Formats.Add` 누락 | 임포트 메뉴에 안 나타남 |
| `SupportedClass` 누락 | "Add New" 메뉴에 안 나타남 |
| `bCreateNew=true` 인데 `FactoryCreateNew` 미구현 | 빈 객체 생성 실패 |
| `FactoryCreateFile` 안에서 무거운 작업에 스코프 누락 | [`07_ProfilingScopeRule.md`](../../../references/07_ProfilingScopeRule.md) 의무 |
| Reimport 처리 안 함 | `FReimportHandler` 다중 상속 + `CanReimport` 구현 |
| `UActorFactory::SpawnActor` 안 override | 기본 동작 사용 — `PostSpawnActor` 만 override 권장 |
| Interchange 도입 안 함 (5.x) | 신규 임포터는 Interchange 검토 |

---

## 10. 에디터 전용 🛠

전체 sub-skill 에디터 빌드 전용. Module 의존: `UnrealEd` + (Interchange 시) `InterchangeCore`/`InterchangeEngine`.

---

## 11. 관련 sub-skill

- [`UnrealEd/SKILL.md`](../SKILL.md) — UnrealEd 메인
- [`UnrealEd/Subsystems`](../Subsystems/SKILL.md) — `UImportSubsystem` (라우팅)
- [`UnrealEd/AssetEditorToolkit`](../AssetEditorToolkit/SKILL.md) — 임포트 후 자동 에디터 열기
- [`AssetTools/SKILL.md`](../../AssetTools/SKILL.md) (향후) — `IAssetTypeActions` 와 연결
- [`CoreUObject/Package`](../../CoreUObject/references/Package.md) — 패키지 저장
- [`CoreUObje