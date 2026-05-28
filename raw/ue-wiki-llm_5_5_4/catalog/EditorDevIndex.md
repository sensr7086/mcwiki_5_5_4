# Editor / Developer Module Catalog

> 본 위키의 분석 범위가 `Engine/Source/Runtime/` 외 **`Editor/`** 와 **`Developer/`** 로 확장됨에 따라 작성. **`Programs/` 는 분석 범위 외** (UnrealHeaderTool / UnrealBuildTool 등 빌드 시스템 — 게임/툴 코드와 분리).
> 전체 Engine/Source 모듈은 매우 많지만(수백 개), 본 위키는 **인하우스 툴 작성에 필수적인 Editor/Developer 모듈** 만 깊이 다룬다.
> 5.5.4 트리 기준 (`C:\Unreal\UnrealEngine\Engine\Source\<Editor|Developer>\<Module>`).

---

## 0. 사용 규칙

1. 본 카탈로그의 모듈은 **모두 에디터 빌드 의존** (🛠 마커). 게임 빌드(Shipping/Test)에는 컴파일에서 빠진다.
2. 인하우스 툴 작성 시 **`#if WITH_EDITOR` 가드 + 모듈 분리 + Build.cs `Type=Editor` + uplugin Editor-only** 4단 방어 의무. 자세한 [`05_EditorOnlyIndex.md`](../references/05_EditorOnlyIndex.md) 와 [`Slate/SKILL.md §8`](../skills/Slate/SKILL.md).
3. 본 카탈로그의 모든 모듈을 sub-skill로 작성하진 않는다. **인하우스 툴 시나리오에 자주 등장하는 것** 부터 우선 작성.

---

## 1. 현재 마운트된 모듈 (5개 — 분석 우선순위)

| # | 모듈 | 위치 | 헤더 수 | 핵심 클래스 / 패턴 | sub-skill 작성 예정 |
|---|------|------|---------|-------------------|---------------------|
| 1 | **UnrealEd** | `Engine/Source/Editor/` | 329 (Public) + 388 (Classes) = **717** | `FAssetEditorToolkit` · `BaseToolkit` · `SimpleAssetEditor` / `Toolkits` · `Subsystems` (UAssetEditorSubsystem 등) · `Kismet2` (BlueprintEditorUtils·KismetEditorUtilities·CompilerResultsLog) · `Elements` · `EditorState` · `Layers` · `Bookmarks` · `WorkflowOrientedApp` · `WorldPartition` | **5~7개 분할 예정** |
| 2 | **PropertyEditor** | `Engine/Source/Editor/` | 68 | `IDetailCustomization` · `IPropertyTypeCustomization` · `IDetailChildrenBuilder` · `DetailLayoutBuilder` · `DetailWidgetRow` · `IPropertyHandle` · `FPropertyEditorModule` | **1~2개 분할 예정** |
| 3 | **AssetTools** | `Engine/Source/Developer/` | 21 | `IAssetTools` · `IAssetTypeActions` · `FAssetTypeActions_Base` · `AssetTypeCategories` · `CollectionAssetManagement` · `AssetViewUtils` | **1개** |
| 4 | **EditorFramework** | `Engine/Source/Editor/` | 20 | `EditorModes` · `Toolkits` · `Subsystems` · `Tools` · `Viewports` · `EditorViewportLayout` · `Factories` · `Styling` | **1개** |
| 5 | **ToolMenus** | `Engine/Source/Developer/` | 14 | `UToolMenus` · `UToolMenu` · `FToolMenuEntry` · `FToolMenuSection` · `FToolMenuContext` · `FToolMenuOwner` · `FToolMenuDelegates` | **1개** |

> **ToolMenus 위치 주의**: UE 5.5에서 `Engine/Source/Developer/ToolMenus/` (Editor가 아님). FMenuBuilder의 모던 대체.

---

## 2. UnrealEd 내부 구조 (분할 후보)

UnrealEd는 단일 모듈이지만 거의 **에디터 전체** 를 다룸. sub-skill을 다음과 같이 분할 후보:

### 2.1 Public/ 디렉토리 (24개)

```
Public/
├── Toolkits/             ← FAssetEditorToolkit · BaseToolkit · SimpleAssetEditor · GlobalEditorCommonCommands
├── Subsystems/           ← AssetEditorSubsystem · EditorActorSubsystem · EditorAssetSubsystem · ImportSubsystem 등 12개
├── Kismet2/              ← BlueprintEditorUtils · KismetEditorUtilities · CompilerResultsLog · DebuggerCommands · KismetReinstanceUtilities
├── Elements/             ← FElementSelectionSet · FTypedElementSelectionSet 등 (5.x Element System)
├── EditorState/          ← FEditorState · 에디터 상태 보존
├── Layers/               ← FLayers · 레이어 시스템
├── Bookmarks/            ← UWorldBookmark · 카메라 북마크
├── DragAndDrop/          ← FAssetDragDropOp 등
├── Settings/             ← UEditorPerProjectUserSettings 등
├── ImportUtils/          ← Import 헬퍼
├── ViewportToolbar/      ← 뷰포트 툴바
├── WorkflowOrientedApp/  ← WorkflowOrientedApplication · 모달 워크플로우
├── WorldPartition/       ← World Partition 통합
├── AutoReimport/
├── Commandlets/
├── Dialogs/
├── Editor/
├── Features/
├── Instances/
├── Serialization/
├── Tests/
├── Text/
└── Tools/
```

### 2.2 Classes/ 디렉토리 (UCLASS 정의 위치)

```
Classes/
├── ActorFactories/       ← UActorFactory 자손
├── Animation/            ← Animation 에디터 클래스
├── Builders/             ← Builder Brush
├── Commandlets/          ← Editor 전용 commandlets
├── CookOnTheSide/        ← Cook 헬퍼
├── Editor/               ← UEditorEngine 등
├── Exporters/            ← UExporter 자손
├── Factories/            ← UFactory 자손 (가장 큼 — Asset 임포트)
├── MaterialEditor/       ← Material Editor 클래스
├── MaterialGraph/        ← UMaterialGraph 등
├── Preferences/          ← Preferences UCLASS
├── Settings/             ← Settings UCLASS
├── ThumbnailRendering/   ← UThumbnailRenderer 자손
└── UserDefinedStructure/ ← UUserDefinedStruct 에디터
```

### 2.3 분할안 (제안)

| sub-skill | 다루는 영역 | 예상 헤더 |
|-----------|-------------|-----------|
| `UnrealEd/AssetEditorToolkit` | `Toolkits/` 전체 + `WorkflowOrientedApp` + 인하우스 에셋 에디터 작성 패턴 | ~30 |
| `UnrealEd/Subsystems` | `Subsystems/` 12개 (AssetEditorSubsystem / EditorActorSubsystem 등) + Subsystems 등록·확장 | ~12 |
| `UnrealEd/Kismet2` | Kismet2 (BlueprintEditorUtils·KismetEditorUtilities) + 블루프린트 컴파일러 통합 | ~15 |
| `UnrealEd/Factories` | `Classes/Factories/` 전체 + Asset 임포트 파이프라인 + UActorFactory | ~80 |
| `UnrealEd/Elements` | 5.x Element Selection System (FTypedElementSelectionSet 등) | ~15 |
| `UnrealEd/Layers` | Layers + Bookmarks + WorldPartition 통합 | ~10 |
| `UnrealEd/MaterialEditor` | Material Editor + MaterialGraph 통합 | ~15 |
| `UnrealEd/Misc` | Settings·Preferences·ImportUtils·Tools·기타 | ~30 |

> 각 sub-skill 독립적이지만 메인 `UnrealEd/SKILL.md`에서 **에디터 진입점·서브시스템 라이프사이클·툴킷 사이클** 공통 규약 명시.

---

## 3. 향후 추가 마운트 후보 (현재 미마운트)

### 3.1 Editor/

| 모듈 | 의미 | 우선순위 |
|------|------|----------|
| `EditorWidgets` | SAssetSearchBox·SAssetThumbnail 등 에디터 공통 위젯 | 높음 |
| `EditorSubsystem` | UEditorSubsystem 베이스 | 높음 |
| `MainFrame` | 메인 에디터 윈도우·메뉴 통합 | 중간 |
| `LevelEditor` | 레벨 에디터 본체 | 중간 |
| `BlueprintGraph` | UBlueprintGraph·UK2Node 베이스 | 중간 (Kismet) |
| `KismetCompiler` | BP→C++ 컴파일러 | 중간 (Kismet) |
| `Kismet` | Kismet 에디터 위젯 | 중간 |
| `KismetWidgets` | SBlueprintPalette 등 | 낮음 |
| `Persona` | Animation 에디터 | 낮음 (애니 카테고리) |
| `MaterialEditor` | Material 에디터 (UnrealEd 외부) | 중간 |
| `AnimationEditor` | 애니 시퀀서 | 낮음 |
| `ContentBrowser` | 컨텐츠 브라우저 | 중간 |
| `ContentBrowserData` | 컨텐츠 데이터 | 낮음 |
| `ClassViewer` | 클래스 선택 위젯 | 낮음 |
| `StructViewer` | 구조체 선택 위젯 | 낮음 |
| `StatusBar` | 에디터 상단 상태바 | 낮음 |
| `WorkspaceMenuStructure` | 워크스페이스 메뉴 카테고리 | 중간 |
| `Documentation` | 인-에디터 문서 | 낮음 |

### 3.2 Developer/

| 모듈 | 의미 | 우선순위 |
|------|------|----------|
| `AssetRegistry` | Asset 메타데이터 캐시 | 높음 |
| `DesktopPlatform` | 파일 다이얼로그·OS 통합 | 중간 |
| `MessageLog` | 에디터 메시지 로그 | 중간 |
| `OutputLog` | Output Log 위젯 | 중간 |
| `ToolWidgets` | 공통 도구 위젯 | 중간 |
| `SourceControl` | 소스 컨트롤 통합 | 낮음 |
| `Profiler` | Stat 프로파일러 | 중간 |
| `CrashTracker` | 크래시 추적 | 낮음 |
| `Settings` | Project Settings 등록 | 중간 |
| `MeshUtilities` | 메시 유틸 | 낮음 |
| `CollectionManager` | 컬렉션 관리 | 낮음 |

> `Programs/` 는 본 위키 분석 범위 **제외** — UnrealHeaderTool·UnrealBuildTool 등 빌드 도구. 게임/인하우스 툴 작성과 직접 연관 없음.

---

## 4. 의존 그래프 (5개 마운트 모듈)

> GraphEditor.Build.cs (이미 위키 작성됨) 의존 그래프에서 추출:

```
인하우스 에셋 에디터 작성 시
┌─────────────────────────────────────────┐
│  UnrealEd (FAssetEditorToolkit 베이스)   │
│  ↓ 의존                                  │
│  EditorFramework (베이스)                │
│  AssetTools (FAssetTypeActions_Base)    │
│  PropertyEditor (Details 패널)          │
│  ToolMenus (UToolMenus 등록)            │
│  ↓                                      │
│  Slate (인하우스 툴 묶음 5개)             │
│  ↓                                      │
│  SlateCore                              │
│  ↓                                      │
│  CoreUObject                            │
└─────────────────────────────────────────┘

노드 그래프 에디터 추가 의존:
  + GraphEditor (이미 sub-skill 작성됨)
  + BlueprintGraph (미마운트)
  + KismetCompiler (미마운트)
  + Kismet (미마운트)
```

---

## 5. 갱신 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-04 | 최초 작성. 위키 범위 확장 — Engine/Source/Runtime + Editor + Developer (Programs 제외). 5개 마운트 모듈 정찰 (UnrealEd/PropertyEditor/AssetTools/EditorFramework/ToolMenus). UnrealEd 8개 sub-skill 분할안 + 향후 마운트 후보 28개 카탈로그. |
