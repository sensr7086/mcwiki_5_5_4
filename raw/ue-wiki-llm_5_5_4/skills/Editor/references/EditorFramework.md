---
name: editorframework-main
description: 🛠 EditorFramework 모듈 - IToolkit + IToolkitHost + UEdMode + UPlacementSubsystem + 5.x Element System 통합.
---

# EditorFramework Module 🛠

> **모듈**: `Engine/Source/Editor/EditorFramework/` (Editor 전용)
> **사이즈**: Public 20 헤더
> **빌드 의존**: `EditorSubsystem` · `InteractiveToolsFramework` · `TypedElementFramework` · `TypedElementRuntime` (Public) + `Core`/`CoreUObject`/`Engine`/`Slate`/`SlateCore`/`ToolMenus` (Private)
> **카테고리**: `[Slate]` 인하우스 툴 (🛠 에디터 전용)

---

## 1. 개요

UnrealEd 가 의존하는 **에디터 베이스**. Editor 모듈 가운데 가장 가볍고 의존성이 적어 인하우스 툴 작성 시 베이스로 자주 사용. `IToolkit` / `IToolkitHost` 인터페이스 + EdMode 진입점 + Placement 서브시스템 + 5.x Element System 인터페이스.

**핵심 책임**:
- `IToolkit` / `IToolkitHost` 정의 (UnrealEd의 `FAssetEditorToolkit` 이 구현)
- `UEdMode` (5.x InteractiveTool 진입점)
- `UPlacementSubsystem` (5.x 액터 배치 추상화)
- `UEditorElementSubsystem` (5.x Element System Editor 어댑터)
- 일부 Slate 위젯 (`SDepthBar` / `InViewportUIDragOperation`)

---

## 2. 파일 카테고리

| 카테고리 | 헤더 |
|----------|------|
| **Toolkits** | `IToolkit.h` · `IToolkitHost.h` · `ToolkitManager.h` · `AssetEditorModeUILayer.h` |
| **Tools / EdMode** | `Tools/Modes.h` · `Tools/AssetEditorContextInterface.h` · `EditorModes.h` |
| **Subsystems** | `Subsystems/EditorElementSubsystem.h` · `Subsystems/PlacementSubsystem.h` |
| **Elements (5.x Typed Element)** | `Elements/Framework/TypedElementAssetEditorToolkitHostMixin.h` · `Elements/Framework/TypedElementViewportInteraction.h` · `Elements/Interfaces/TypedElementDetailsInterface.h` |
| **Factories** | `Factories/AssetFactoryInterface.h` |
| **Viewport** | `EditorViewportLayout.h` · `ViewportTabContent.h` · `Viewports/InViewportUIDragOperation.h` (⚠ `SDepthBar.h` 는 5.5 에 없음 — 5.7+ 추가) |
| **Styling** | (⚠ `DepthBarStyle.h` 는 5.5 에 없음 — 5.7+ 추가) |
| **모듈** | `EditorFrameworkModule.h` · `UnrealWidgetFwd.h` |

---

## 3. IToolkit / IToolkitHost (Toolkits/)

### 3.1 IToolkit (인터페이스)

`IToolkit.h` — 에디터 인스턴스가 구현해야 하는 인터페이스. `FAssetEditorToolkit`(UnrealEd) 이 구현.

| 시그니처 | 의미 |
|----------|------|
| `virtual FName GetToolkitFName() const = 0` | 고유 식별 |
| `virtual FText GetBaseToolkitName() const = 0` | 표시 이름 |
| `virtual FString GetWorldCentricTabPrefix() const = 0` | WorldCentric 탭 prefix |
| `virtual FLinearColor GetWorldCentricTabColorScale() const = 0` | 탭 색조 |
| `virtual void RegisterTabSpawners(TSharedRef<FTabManager>)` | 탭 등록 |
| `virtual void UnregisterTabSpawners(TSharedRef<FTabManager>)` | 탭 해제 |
| `virtual void BringToolkitToFront()` | 포커스 |
| `virtual TSharedPtr<SWidget> GetInlineContent() const` | 인라인 콘텐츠 |
| `virtual bool IsAssetEditor() const` | 에셋 에디터인지 |
| `virtual bool IsHosted() const` | 호스팅 모드 |
| `virtual TSharedRef<IToolkitHost> GetToolkitHost() const` | 호스트 |
| `virtual TSharedRef<FWorkspaceItem> GetWorkspaceMenuCategory() const = 0` | 워크스페이스 메뉴 |
| `virtual FEditorModeTools& GetEditorModeManager() const = 0` | EdMode 매니저 |

### 3.2 IToolkitHost (인터페이스)

`IToolkitHost.h` — toolkit을 호스팅하는 윈도우/메인 영역. `SStandaloneAssetEditorToolkitHost` (UnrealEd) 가 구현.

| 시그니처 | 의미 |
|----------|------|
| `virtual TSharedRef<SWidget> GetParentWidget() = 0` | 부모 위젯 |
| `virtual void BringToFront()` | 윈도우 포커스 |
| `virtual TSharedRef<SDockTabStack> GetTabSpot(const EToolkitTabSpot::Type)` | 탭 스폿 |
| `virtual TSharedPtr<FTabManager> GetTabManager() const = 0` | TabManager |
| `virtual void OnToolkitHostingStarted(TSharedRef<IToolkit>)` | 호스팅 시작 |
| `virtual void OnToolkitHostingFinished(TSharedRef<IToolkit>)` | 종료 |
| `virtual UWorld* GetWorld() const = 0` | World |
| `virtual FEditorModeTools& GetEditorModeManager() const = 0` | EdMode |

### 3.3 FToolkitManager

`ToolkitManager.h` — 활성 Toolkit 목록 관리. `FToolkitManager::Get()` 글로벌 싱글턴.

```cpp
FToolkitManager::Get().RegisterNewToolkit(MyToolkit);
FToolkitManager::Get().CloseToolkit(MyToolkit);
```

### 3.4 FAssetEditorModeUILayer

`AssetEditorModeUILayer.h` — 에디터 안 EdMode UI 계층 (모달리티 분리).

---

## 4. UEdMode (Tools/Modes.h) — 5.x InteractiveTool 진입점

UE 5.x의 새 모달 시스템. 기존 `FEdMode` (구식)의 후계.

| 핵심 virtual | 의미 |
|-------------|------|
| `virtual void Enter()` | 모드 진입 |
| `virtual void Exit()` | 종료 |
| `virtual bool ShouldDrawWidget() const` | 위젯 그릴지 |
| `virtual void Render(const FSceneView*, FViewport*, FPrimitiveDrawInterface*)` | 3D 뷰포트 렌더 |
| `virtual void Tick(FEditorViewportClient*, float DeltaTime)` | 매 프레임 |
| `virtual bool InputKey(...)` / `InputAxis(...)` | 입력 |
| `virtual TSharedRef<FUICommandList> GetCommandList() const` | 단축키 |
| `virtual TMap<FName, TArray<TSharedPtr<FUICommandInfo>>> GetModeCommands() const` | 모드별 명령 |

**InteractiveToolsFramework 통합**: `UEdMode` 가 `UInteractiveToolManager` 보유 → `UInteractiveTool` 자손으로 모달 도구 작성.

---

## 5. Subsystems

### 5.1 UPlacementSubsystem (`PlacementSubsystem.h`)

5.x 신규 — 액터 배치를 Element System으로 추상화. `UActorFactory` (UnrealEd/Factories) 가 사용.

| API | 의미 |
|-----|------|
| `TArray<FTypedElementHandle> PlaceAsset(const FAssetPlacementInfo&, const FPlacementOptions&)` | 에셋 → Element 배치 |
| `void RegisterAssetFactory(IAssetFactoryInterface* Factory)` | 팩토리 등록 |
| `void UnregisterAssetFactory(IAssetFactoryInterface*)` | 해제 |

### 5.2 UEditorElementSubsystem (`EditorElementSubsystem.h`)

Editor에서 5.x Element System (`FTypedElementHandle`) 작업의 진입점. UnrealEd/Elements 와 통합.

---

## 6. IAssetFactoryInterface (`Factories/AssetFactoryInterface.h`)

UPlacementSubsystem 의 팩토리 인터페이스. `UActorFactory` 가 구현. 자세한 사용은 [`UnrealEd/Factories`](../UnrealEd/Factories/SKILL.md).

---

## 7. Viewport / Style

| 헤더 | 의미 |
|------|------|
| `EditorViewportLayout.h` | 뷰포트 레이아웃 (1/4 분할 등) |
| `ViewportTabContent.h` | 뷰포트 탭 콘텐츠 |
| `Viewports/InViewportUIDragOperation.h` | 뷰포트 안 UI 드래그 |
| `Viewports/SDepthBar.h` | 깊이 바 위젯 |
| `Styling/DepthBarStyle.h` | 깊이 바 스타일 |

거의 사용 안 함 — 표준 LevelEditor 가 직접 노출.

---

## 8. 5.x Element System 통합

### 8.1 TypedElementAssetEditorToolkitHostMixin

`Elements/Framework/TypedElementAssetEditorToolkitHostMixin.h` — IToolkitHost 가 구현하면 5.x Element System으로 선택·편집 가능.

### 8.2 TypedElementViewportInteraction

뷰포트에서 Element 인터랙션 처리.

### 8.3 TypedElementDetailsInterface

Element가 Details 패널에 노출되는 방식.

---

## 9. 가상 함수 / Super 호출

| 시그니처 | Super | 의미 |
|----------|-------|------|
| `IToolkit::*` | (override 시 자체 처리 — pure virtual 다수) | |
| `IToolkitHost::*` | (override 시 자체 처리) | |
| `UEdMode::Enter()` | **FIRST** | 베이스 셋업 |
| `UEdMode::Exit()` | **LAST** | 사용자 cleanup 후 |
| `UEdMode::Render(...)` | **FIRST** | 베이스 위젯 |
| `UEdMode::Tick(...)` | **FIRST** + 스코프 | 매 프레임 — [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) |
| `UEditorSubsystem::Initialize` (자손) | **FIRST** | UnrealEd/Subsystems sub-skill 패턴 |
| `UEditorSubsystem::Deinitialize` | **LAST** | |

자세한 Super 호출 규약은 [`04_OverrideIndex.md §6`](../../references/04_OverrideIndex.md).

---

## 10. 작성 패턴

### 10.1 인하우스 EdMode

```cpp
#if WITH_EDITOR
UCLASS()
class MYGAMEEDITOR_API UMyEdMode : public UEdMode
{
    GENERATED_BODY()
public:
    UMyEdMode()
    {
        Info = FEditorModeInfo(
            FName("MyEdMode"),
            LOCTEXT("MyEdMode", "My Custom Mode"),
            FSlateIcon(),
            true);
    }

    virtual void Enter() override
    {
        Super::Enter();    // ← FIRST
        TRACE_CPUPROFILER_EVENT_SCOPE(UMyEdMode_Enter);
        // 도구 등록·UI 생성
    }

    virtual void Exit() override
    {
        // cleanup
        Super::Exit();     // ← LAST
    }

    virtual void Render(const FSceneView* View, FViewport* Viewport, FPrimitiveDrawInterface* PDI) override
    {
        Super::Render(View, Viewport, PDI);
        // 3D 그리기
    }

    virtual void Tick(FEditorViewportClient* ViewportClient, float DeltaTime) override
    {
        Super::Tick(ViewportClient, DeltaTime);
        SCOPED_NAMED_EVENT(UMyEdMode_Tick, FColor::Cyan);    // ← 매 프레임 스코프
        // ...
    }
};
#endif
```

### 10.2 진입

```cpp
GLevelEditorModeTools().ActivateMode(UMyEdMode::EM_MyEdMode);
GLevelEditorModeTools().DeactivateMode(UMyEdMode::EM_MyEdMode);
```

---

## 11. 함정

| 함정 | 회피 |
|------|------|
| `IToolkit` 인터페이스 직접 구현 | 보통 `FAssetEditorToolkit` 자손 (UnrealEd 가 처리) |
| `UEdMode::Tick` 에 스코프 누락 | [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) — `SCOPED_NAMED_EVENT` 의무 |
| 게임 모듈에서 `UEdMode` 의존 | Editor 전용 — Build.cs `Type=Editor` |
| `FToolkitManager::Get()` 직접 호출 | 보통 `GEditor->GetEditorSubsystem<UAssetEditorSubsystem>()->OpenEditorForAsset` 가 처리 |
| `UPlacementSubsystem::PlaceAsset` 직접 호출 | 보통 `UActorFactory::PlaceAsset` 가 처리 |

---

## 12. 에디터 전용 🛠

전체 모듈 에디터 빌드 전용. 4단 분리 — [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md).

---

## 13. 관련 sub-skill

- [`UnrealEd/AssetEditorToolkit`](../UnrealEd/AssetEditorToolkit/SKILL.md) — `FAssetEditorToolkit` 이 IToolkit 구현 (본 모듈 인터페이스)
- [`UnrealEd/Subsystems`](../UnrealEd/Subsystems/SKILL.md) — `UEditorSubsystem` 베이스
- [`UnrealEd/Elements`](../UnrealEd/Elements/SKILL.md) — Element System 통합
- [`UnrealEd/Factories`](../UnrealEd/Factories/SKILL.md) — `UActorFactory` ↔ `UPlacementSubsystem`
- [`ToolMenus`](../ToolMenus/SKILL.md) — EdMode 메뉴 등록
- [`Slate/Docking`](../Slate/references/Docking.md) — `IToolkitHost::GetTabManager`
- 향후: `InteractiveToolsFramework` (별도 모듈, 미마운트) — `UInteractiveTool`
- 교차: [`04_OverrideIndex.md §6`](../../references/04_OverrideIndex.md) (UEdMode Super) · [`05_EditorOnlyIndex.md`](../../references/05_EditorOnlyIndex.md) · [`07_ProfilingScopeRule.md`](../../references/07_ProfilingScopeRule.md) (Tick·Render)
