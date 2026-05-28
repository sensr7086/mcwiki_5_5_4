---
type: source
title: "UE Editor — UnrealEd / Factories sub-skill 🛠 (UFactory / UActorFactory / UExporter / Interchange)"
slug: ue-editor-unrealed-factories
source_path: raw/ue-wiki-llm/skills/Editor/references/UnrealEd/Factories.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-13
related_entities:
  - "[[entities/AActor]]"
  - "[[entities/UStaticMesh]]"
related_concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Asset-Loading-Policy]]"
tags: [ue, editor, unrealed, factories, ufactory, uactorfactory, uexporter, interchange, reimport]
---

# UE Editor — UnrealEd / Factories sub-skill 🛠

> Source: [[raw/ue-wiki-llm/skills/Editor/references/UnrealEd/Factories.md]] · 10 KB raw · `Classes/Factories/` 111+ + `ActorFactories/` 50+ + `Exporters/`

## 1. Summary

UE 에디터의 **에셋 생성 / 임포트 / 내보내기 추상화**. 4 베이스: **`UFactory`** (외부 파일 → UObject — Right Click → Import / Add New) · **`UActorFactory`** (Asset → 레벨 액터 — 드래그앤드롭 / Place Actors) · **`UExporter`** (UObject → 외부 파일) · **`Interchange`** 5.x (UFactory 차세대 — fbx/obj/usd/gltf 통합, `InterchangeCore` + `InterchangeEngine`). **5.x 권장**: 신규 임포터 = Interchange. 기존 UFactory 호환 유지 (공존, 같은 포맷 동시 등록 금지).

## 2. Key claims

### 2.1. 헤더 / 베이스

- `Factory.h` — `UFactory` + `FReimportHandler` (Reimport 인터페이스)
- `ActorFactory.h` — `UActorFactory`
- `Exporter.h` — `UExporter`
- `AutomatedAssetImportData.h` — `UAutomatedAssetImportData` (CLI 자동 임포트)
- 빌트인: UFactory 자손 111 (Anim/Texture2D/Material/Sound 등) · UActorFactory 자손 50+ (AmbientSound/BasicShape/Blueprint/Character/Light/Pawn/StaticMesh)

### 2.2. UFactory 핵심 virtual (Factory.h) 🟢

| 시그니처 | 라인 | 의미 |
| -- | -- | -- |
| `CanCreateNew()` | L54 | Add New 메뉴? |
| `FactoryCanImport(FString& Filename)` | L64 | 확장자 검사 |
| **`FactoryCreateFile(UClass*, UObject*, FName, EObjectFlags, FString&, ..., bool& bOutCanceled)`** ⭐ | L102 | 파일→UObject (가장 자주 override) |
| `FactoryCreateNew(...)` | L116 / L132 | 빈 객체 생성 |
| `ImportObject(...)` | L137 | 라우팅 헬퍼 |
| `ShouldShowInNewMenu` / `GetDisplayName` / `GetToolTip` / `GetMenuCategories` / `GetMenuCategorySubMenus` | L155-173 | 메뉴 UI |
| `DoesSupportClass(UClass*)` / `ResolveSupportedClass()` | L189 / L195 | 지원 클래스 |
| `ConfigureProperties()` / `ConfigurePropertiesAsync` (5.x) | L198 / L211 | 임포트 설정 다이얼로그 |

생성자 ctor 설정: `bCreateNew = true` / `bEditAfterNew = true` / `bEditorImport = true` / `SupportedClass = UMyAsset::StaticClass()` / `Formats.Add(TEXT("myext;My Custom Asset"))`.

### 2.3. UActorFactory 핵심 virtual

- `CanCreateActorFrom(FAssetData&, FText& OutError)` — 배치 가능?
- `PostSpawnActor(UObject* Asset, AActor* NewActor)` — Spawn 후 초기화 (**`Modify()` 의무** — Undo/Redo)
- `NewActorClass` 필드 — 기본 액터 클래스
- `DisplayName` — Place Actors 패널 표시

`GEditor->ActorFactories` 에 자동 등록 (UCLASS 매크로). 5.x 는 [[sources/ue-editor-editorframework]] 의 `UPlacementSubsystem` 도 함께.

### 2.4. UExporter 핵심 virtual

- `ExportBinary(UObject*, TCHAR* Type, FArchive&, FFeedbackContext*, int32 FileIndex, uint32 PortFlags)` — 직렬화
- 생성자: `SupportedClass = ...` / `FormatExtension.Add("myext")` / `FormatDescription.Add("...")`

### 2.5. FReimportHandler — Reimport 지원

`UFactory` 자손이 추가 상속. 3 핵심:

- `CanReimport(UObject*, TArray<FString>& OutFilenames)`
- `SetReimportPaths(UObject*, TArray<FString>&)`
- `Reimport(UObject*)`

SourceControl 통합 + 자동 reimport.

### 2.6. Interchange (5.x 후속) ⚠

`InterchangeCore` / `InterchangeEngine` — fbx/obj/usd/gltf 통합 파이프라인. UFactory 보다 *모듈화 + 비동기 + 다단 변환* 지원.

| 측면 | `UFactory` | `Interchange` (5.x) |
| -- | -- | -- |
| 아키텍처 | 단일 클래스 | Pipeline (Translator → Pipeline → Factory → Writer) |
| 비동기 | 동기 (`FactoryCreateFile`) | 비동기 (Tasks) |
| 진행 표시 | `FFeedbackContext` 수동 | UI 자동 |
| 포맷 (5.7.4) | 거의 모든 포맷 | fbx / obj / gltf / usd / mp3 / wav 등 점진 확대 |
| 권장 | 레거시 호환 | **신규 임포터** |

🚨 **같은 포맷에 둘 다 등록 금지** — 충돌. 신규 = Interchange / 기존 = UFactory 유지.

### 2.7. 작성 패턴 — UFactory

```cpp
#if WITH_EDITOR
UCLASS()
class UMyAssetFactory : public UFactory
{
    GENERATED_BODY()
public:
    UMyAssetFactory()
    {
        bCreateNew = true; bEditAfterNew = true; bEditorImport = true;
        SupportedClass = UMyAsset::StaticClass();
        Formats.Add(TEXT("myext;My Custom Asset"));
    }
    virtual UObject* FactoryCreateFile(UClass* InClass, UObject* InParent, FName InName,
        EObjectFlags Flags, const FString& Filename, const TCHAR* Parms,
        FFeedbackContext* Warn, bool& bOutCanceled) override
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyAssetFactory_FactoryCreateFile);
        UMyAsset* NewAsset = NewObject<UMyAsset>(InParent, InClass, InName, Flags);
        // 파일 파싱 + 데이터 채우기
        return NewAsset;
    }
    virtual bool FactoryCanImport(const FString& Filename) override
    { return FPaths::GetExtension(Filename).Equals(TEXT("myext"), ESearchCase::IgnoreCase); }
};
#endif
```

UActorFactory / UExporter 작성 패턴 → raw §3.2 / §4 직접 참조.

### 2.8. KMCProject 페어

`MCEditorModule` 의 `MCStoryAssetEditorFactory` / `MCPartsAssetEditorFactory` 가 본 sub-skill 의 `UFactory::FactoryCreateNew` 패턴 적용 (외부 파일 임포트 아닌 *빈 에셋 생성*). [[sources/ue-docs-claude]] §architecture — Factory / Action / EditorApplication 표준 스택의 첫 단계.

### 2.9. 함정 (6대) 🟡

| # | 함정 | 회피 |
| -- | -- | -- |
| 1 | `Formats.Add("ext;Display")` 형식 오류 (`;` 분리자) | Add New 메뉴 안 보임 |
| 2 | `bCreateNew = true` + `FactoryCreateNew` 미구현 | null 반환 |
| 3 | `FactoryCreateFile` 안 `NewObject` 의 `InParent` 누락 | outer 깨짐 |
| 4 | Reimport 시 SourceFile 경로 변경 | `SetReimportPaths` 호출 의무 |
| 5 | `UActorFactory::PostSpawnActor` 안 `Modify()` 누락 | Undo/Redo 안 됨 |
| 6 | `UFactory` + `Interchange` 같은 포맷 동시 등록 | 충돌 — 한 시스템만 |

## 3. Cross-link

- 카테고리: [[sources/ue-editor-skill]] / [[sources/ue-editor-unrealed]]
- 페어: [[sources/ue-editor-assettools]] (`IAssetTypeActions` — Add Asset 메뉴 페어) / [[sources/ue-editor-editorframework]] (`UPlacementSubsystem` 5.x) / [[sources/ue-editor-unrealed-subsystems]] (`UImportSubsystem`)
- 횡단: [[sources/ue-ref-05-editoronlyindex]] · [[sources/ue-ref-11-assetloadingpolicy]] §3 (Editor 동기 로드 — 예외) · [[sources/ue-ref-07-profilingscopeRule]]
- MC-시리즈: [[sources/ue-docs-claude]] (KMCProject `MCStoryAssetEditorFactory` 패턴)
