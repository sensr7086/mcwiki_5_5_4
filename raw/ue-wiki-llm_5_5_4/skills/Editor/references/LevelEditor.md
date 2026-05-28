---
name: leveleditor-main
description: 🛠 LevelEditor 모듈 - FLevelEditorModule + ILevelEditor + SLevelViewport + ULevelEditorSubsystem + FLevelEditorCommands + 5.x Element 선택.
---

# LevelEditor Module 🛠

> **모듈**: `Engine/Source/Editor/LevelEditor/` (Editor 전용)
> **사이즈**: Public 19 헤더
> **카테고리**: `[Slate]` 인하우스 툴 (🛠 에디터 전용)

---

## 1. 개요

UE 에디터에서 가장 중심이 되는 **레벨 에디터** 본체. 메인 뷰포트·아웃라이너·디테일 패널·트랜스폼 위젯·툴바·뷰포트 클라이언트가 모두 이 모듈에서 통합. 인하우스 툴이 메인 에디터에 항목을 추가하거나 뷰포트와 상호작용할 때 진입점.

핵심 객체:
- **`FLevelEditorModule`** — 모듈 진입 (StartupModule 에서 단축키·메뉴 등록)
- **`ILevelEditor`** — 레벨 에디터 위젯 인터페이스 (`SCompoundWidget` + `IToolkitHost`)
- **`SLevelViewport`** — 뷰포트 위젯
- **`ULevelEditorSubsystem`** — 레벨 에디터 BP 헬퍼
- **`FLevelEditorCommands`** — 표준 단축키 (`TCommands<T>`)
- **`FLevelEditorActions`** — 액션 콜백
- **레벨 에디터 컨텍스트 메뉴** — `LevelEditorContextMenu`

---

## 2. 핵심 헤더

| 헤더 | 클래스 | 의미 |
|------|--------|------|
| `LevelEditor.h` | `FLevelEditorModule` (L70) + `LevelEditorTabIds` (L33) | 모듈 진입 + 표준 탭 ID |
| `ILevelEditor.h` | `ILevelEditor` (L28) | 레벨 에디터 인터페이스 |
| `LevelEditorActions.h` | `FLevelEditorCommands` (TCommands L31) + `FLevelEditorActionCallbacks` (L703) | 단축키 + 콜백 |
| `LevelEditorModesActions.h` | EdMode 단축키 | |
| `LevelViewportActions.h` | 뷰포트 단축키 | |
| `LevelEditorSubsystem.h` | `ULevelEditorSubsystem` (L38) | BP 헬퍼 |
| `LevelEditorContextMenu.h` | `FLevelEditorContextMenu` | 컨텍스트 메뉴 |
| `LevelEditorMenuContext.h` | `ULevelEditorMenuContext` 등 | 메뉴 컨텍스트 |
| `LevelEditorOutlinerSettings.h` | 아웃라이너 설정 | |
| `LevelEditorCameraEditorState.h` | 카메라 상태 (⚠ **5.5 에는 없음 — 5.7+ 추가**) | |
| `SLevelViewport.h` | `SLevelViewport` | 뷰포트 위젯 |
| `LevelViewportLayout.h` | 뷰포트 레이아웃 | |
| `LevelViewportTabContent.h` | 뷰포트 탭 콘텐츠 | |
| `ViewportTypeDefinition.h` | 뷰포트 타입 정의 | |
| `LightmapResRatioAdjust.h` | 라이트맵 해상도 조정 | |
| `DlgDeltaTransform.h` | 델타 변환 다이얼로그 | |
| `Elements/` | 5.x Element System 통합 | |

---

## 3. FLevelEditorModule (모듈 진입)

### 3.1 핵심 API (LevelEditor.h L70)

| API | 라인 | 의미 |
|-----|------|------|
| `void StartupModule()` | L80 | 모듈 시작 |
| `void ShutdownModule()` | L85 | 종료 |
| `void SummonSelectionDetails()` | L102 | 선택 디테일 호출 |
| `void SummonBuildAndSubmit()` | L108 | 빌드/제출 |
| `void SummonWorldBrowserHierarchy/Details/Composition()` | L110/111/112 | 월드 브라우저 |
| `TSharedPtr<SDockTab> AttachSequencer(TSharedPtr<SWidget>, TSharedPtr<IAssetEditorInstance>)` | L119 | 시퀀서 부착 |
| `void StartPlayInEditorSession()` | L124 | PIE 시작 |
| `void GoImmersiveWithActiveLevelViewport(const bool bForceGameView)` | L129 | 몰입 모드 |
| `void ToggleImmersiveOnActiveLevelViewport()` | L134 | 토글 |
| `TSharedPtr<ILevelEditor> GetFirstLevelEditor() const` | L137 | 첫 인스턴스 |
| `TSharedPtr<SDockTab> GetLevelEditorTab() const` | L140 | 레벨 에디터 탭 |
| `TSharedPtr<IAssetViewport> GetFirstActiveViewport()` | L147 | 첫 뷰포트 |

### 3.2 콜백 / 이벤트 (FLevelEditorModule)

`FLevelEditorModule` 의 멀티캐스트 델리게이트:

| 델리게이트 | 의미 |
|-----------|------|
| `FOnLevelEditorCreated& OnLevelEditorCreated()` | 레벨 에디터 인스턴스 생성 |
| `FOnActorSelectionChanged& OnActorSelectionChanged()` | 액터 선택 변경 (4.x — 5.x 는 Element System 권장) |
| `FOnComponentsEdited& OnComponentsEdited()` | 컴포넌트 편집 |
| `FOnRedrawLevelEditingViewports& OnRedrawLevelEditingViewports()` | 뷰포트 재페인트 |

### 3.3 사용 패턴

```cpp
#if WITH_EDITOR
FLevelEditorModule& Module = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");

// 인스턴스 생성 콜백 — StartupModule 안에서 등록
Module.OnLevelEditorCreated().AddLambda([this](TSharedPtr<ILevelEditor> InLevelEditor)
{
    TRACE_CPUPROFILER_EVENT_SCOPE(MyEditor_OnLevelEditorCreated);
    // 레벨 에디터에 사용자 정의 항목 추가
});

// 메뉴 확장 — ToolMenus 사용 권장
UToolMenu* ToolBar = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar");
FToolMenuSection& Section = ToolBar->FindOrAddSection("MyTools");
Section.AddMenuEntry(...);
#endif
```

---

## 4. ILevelEditor — 레벨 에디터 위젯

### 4.1 인터페이스 (ILevelEditor.h L28)

```cpp
class ILevelEditor : public SCompoundWidget, public IToolkitHost
```

`IToolkitHost` 자손 — 에셋 에디터를 호스팅 가능. 핵심:

| 시그니처 | 라인 | 의미 |
|----------|------|------|
| `virtual const UTypedElementSelectionSet* GetElementSelectionSet() const = 0` | L34 | 선택 셋 (5.x Element System) |
| `virtual UTypedElementSelectionSet* GetMutableElementSelectionSet() = 0` | L35 | 변경 가능 셋 |
| `virtual void SummonLevelViewportContextMenu(const FTypedElementHandle& HitProxyElement)` | L38 | 뷰포트 컨텍스트 메뉴 |
| `virtual TArray<TSharedPtr<SLevelViewport>> GetViewports() const = 0` | L50 | 모든 뷰포트 |
| `virtual TSharedPtr<SLevelViewport> GetActiveViewportInterface() = 0` | L53 | 활성 뷰포트 |
| `virtual const TSharedPtr<FUICommandList>& GetLevelEditorActions() const = 0` | L56 | 단축키 |
| `virtual void AppendCommands(const TSharedRef<FUICommandList>&)` | L62 | 사용자 단축키 추가 |
| `virtual TSharedRef<SWidget> CreateActorDetails(const FName TabIdentifier)` | L69 | 액터 디테일 위젯 |
| `virtual void SetActorDetailsRootCustomization(...)` | L72 | 디테일 패널 커스터마이징 |
| `virtual void AddActorDetailsSCSEditorUICustomization(...)` | L75 | SCS 에디터 커스터마이징 |
| `virtual TArray<TWeakPtr<ISceneOutliner>> GetAllSceneOutliners() const = 0` | L84 | 아웃라이너들 |

---

## 5. ULevelEditorSubsystem — BP 헬퍼

### 5.1 베이스 (LevelEditorSubsystem.h L38)

```cpp
class ULevelEditorSubsystem : public UEditorSubsystem, public IActorEditorContextClient
```

`UEditorSubsystem` 자손 — `GEditor->GetEditorSubsystem<ULevelEditorSubsystem>()` 로 접근.

### 5.2 자주 쓰는 BP 함수 (`UFUNCTION(BlueprintCallable, meta=(DevelopmentOnly))`)

| 카테고리 | 메서드 |
|----------|--------|
| 레벨 | `NewLevel` · `LoadLevel` · `SaveCurrentLevel` · `SaveAllDirtyLevels` · `LoadLevelByName` · `GetCurrentLevel` |
| 빌드 | `BuildLightMaps` · `BuildHLODs` · `BuildAllLandscape` · `BuildTextureStreaming` |
| PIE | `EditorPlaySimulate` · `EditorRequestEndPlay` |
| 뷰포트 | `EditorInvalidateViewports` · `PilotLevelActor` · `EjectPilotLevelActor` |
| 카메라 | `GetLevelViewportCameraInfo` · `SetLevelViewportCameraInfo` |
| 셀렉션 | `GetSelectionSet` |

---

## 6. FLevelEditorCommands — 표준 단축키

`LevelEditorActions.h` L31:

```cpp
class FLevelEditorCommands : public TCommands<FLevelEditorCommands>
```

표준 명령들 (`UI_COMMAND`):
- `BrowseDocumentation`
- `EditAssetNoConfirmMultiple`
- `Save` / `SaveAs` / `SaveCurrent`
- `OpenLevel` / `NewLevel`
- `Build` / `BuildAndSubmit` / `BuildLightingOnly` / `BuildReflectionCapturesOnly` / `BuildTextureStreaming` / `BuildHLODs`
- `Cut` / `Copy` / `Paste` / `Duplicate` / `Delete`
- `SelectNone` / `InvertSelection`
- 그 외 100+ 명령

자세한 TCommands<T> — [`Slate/Commands`](../Slate/references/Commands.md).

---

## 7. 표준 메뉴 / 툴바 이름 (ToolMenus)

| 이름 | 의미 |
|------|------|
| `LevelEditor.LevelEditorToolBar` | 메인 툴바 |
| `LevelEditor.MainMenu` | 메인 메뉴 |
| `LevelEditor.MainMenu.File` | File 메뉴 |
| `LevelEditor.MainMenu.Edit` | Edit |
| `LevelEditor.MainMenu.Window` | Window |
| `LevelEditor.MainMenu.Build` | Build |
| `LevelEditor.MainMenu.Select` | Select |
| `LevelEditor.MainMenu.Actor` | Actor |
| `LevelEditor.LevelViewportToolBar.Show` | 뷰포트 Show 메뉴 |
| `LevelEditor.LevelViewportContextMenu` | 뷰포트 컨텍스트 메뉴 |

자세한 메뉴 등록 — [`ToolMenus`](../ToolMenus/SKILL.md).

---

## 8. 사용 패턴

### 8.1 인하우스 도구 진입점 (StartupModule)

```cpp
#if WITH_EDITOR
void FMyEditorModule::StartupModule()
{
    UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FMyEditorModule::RegisterMenus));
}

void FMyEditorModule::RegisterMenus()
{
    FToolMenuOwnerScoped OwnerScoped(this);
    
    // 레벨 에디터 툴바에 버튼 추가
    UToolMenu* ToolBar = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar");
    FToolMenuSection& Section = ToolBar->FindOrAddSection("MyTools");
    Section.AddMenuEntry(...);

    // 레벨 에디터 단축키 추가
    FLevelEditorModule& LE = FModuleManager::LoadModuleChecked<FLevelEditorModule>("LevelEditor");
    LE.OnLevelEditorCreated().AddLambda([this](TSharedPtr<ILevelEditor> Editor)
    {
        TRACE_CPUPROFILER_EVENT_SCOPE(MyEditor_OnLevelEditorCreated);
        Editor->AppendCommands(MyCommandList.ToSharedRef());
    });
}
#endif
```

### 8.2 활성 뷰포트 액세스

```cpp
FLevelEditorModule& LE = FModuleManager::GetModuleChecked<FLevelEditorModule>("LevelEditor");
TSharedPtr<ILevelEditor> Editor = LE.GetFirstLevelEditor();
if (Editor.IsValid())
{
    TSharedPtr<SLevelViewport> Viewport = Editor->GetActiveViewportInterface();
    // ...
}
```

### 8.3 액터 선택 (5.x Element System)

```cpp
// 레거시 4.x
GEditor->GetSelectedActors()->Iterator()...    // (deprecated 권장 X)

// 5.x 권장 — Element System
const UTypedElementSelectionSet* SelSet = Editor->GetElementSelectionSet();
SelSet->ForEachSelectedElement<ITypedElementWorldInterface>([](const TTypedElement<ITypedElementWorldInterface>& Element)
{
    FTransform T;
    Element.GetWorldTransform(T);
    return true;
});
```

자세한 — [`UnrealEd/Elements`](../UnrealEd/Elements/SKILL.md).

---

## 9. 가상 함수 / Super 호출

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `ILevelEditor::*` | (override 시 자체 처리) | pure virtual 다수 |
| `ULevelEditorSubsystem::Initialize/Deinitialize` | **FIRST/LAST** | UEditorSubsystem 베이스 |
| `FLevelEditorModule::StartupModule/ShutdownModule` | **FIRST** (StartupModule에서) | 모듈 라이프사이클 |
| `FLevelEditorActionCallbacks::*` | (static 헬퍼) | 콜백들 |

---

## 10. 함정

| 함정 | 회피 |
|------|------|
| `OnLevelEditorCreated` 늦게 등록 — 이미 발화 후 | StartupModule 안에서 등록 + 이미 존재하면 즉시 처리 |
| 4.x `GEditor->GetSelectedActors()` 만 사용 | 5.x Element System (`GetElementSelectionSet`) 권장 |
| `GetFirstLevelEditor()` nullptr 반환 | 검사 의무 — 에디터 시작 전 |
| `OnRedrawLevelEditingViewports` 콜백 빈도 | 매 페인트마다 호출 — 무거운 작업 금지 |
| 람다 캡처 + 강한 참조 | TWeakPtr<ILevelEditor> + TWeakObjectPtr |
| 콜백 스코프 누락 | [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) |
| `LevelEditor.LevelEditorToolBar` 등록 시 OwnerScoped 누락 | RAII — Shutdown 시 자동 해제 |
| `ULevelEditorSubsystem` 메서드 `meta=(DevelopmentOnly)` 누락 — Shipping 빌드에서 호출 | 빌드 가드 |

---

## 11. 에디터 전용 🛠

전체 모듈 에디터 빌드 전용. 4단 분리 — [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md).

---

## 12. 관련 sub-skill

- [`MainFrame`](../MainFrame/SKILL.md) — 메인 윈도우 안에 LevelEditor 호스트
- [`ToolMenus`](../ToolMenus/SKILL.md) — `LevelEditor.LevelEditorToolBar` / `LevelEditor.MainMenu.*` 메뉴 확장
- [`Slate/Commands`](../Slate/references/Commands.md) — `FLevelEditorCommands` (TCommands<T>)
- [`Slate/Docking`](../Slate/references/Docking.md) — FTabManager / SDockTab
- [`UnrealEd/Subsystems`](../UnrealEd/Subsystems/SKILL.md) — `UEditorActorSubsystem` (ULevelEditorSubsystem 과 보완)
- [`UnrealEd/Elements`](../UnrealEd/Elements/SKILL.md) — 5.x 선택 시스템
- [`EditorFramework`](../EditorFramework/SKILL.md) — `IToolkitHost` 베이스 (ILevelEditor 가 구현)
- [`EditorWidgets`](../EditorWidgets/SKILL.md) — 공통 위젯 (검색·필터)
- [`AssetRegistry`](../AssetRegistry/SKILL.md) — Asset 메타 (씬 아웃라이너 / 레퍼런스 뷰어)
- 교차: [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) · [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) (콜백·뷰포트 Tick 스코프)
