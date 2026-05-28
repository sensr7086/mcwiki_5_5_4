---
name: slate-grapheditor
description: 🛠 SGraphEditor + UEdGraph + UEdGraphNode + UEdGraphSchema - 노드 그래프 에디터.
---

# Slate / GraphEditor — 인하우스 노드 그래프 에디터

> **위치**: `Engine/Source/Runtime/Engine/Classes/EdGraph/` (UEdGraph 런타임) + `Engine/Source/Editor/GraphEditor/` (SGraphEditor 위젯)
> **요지**: BP/Material/Niagara 모두 같은 베이스 — `UEdGraph` 의 `Nodes` 배열에 `UEdGraphNode` 인스턴스가 추가되고, `UEdGraphSchema` (UClass) 가 핀 연결 / 그래프 동작 정책을 결정. **인하우스 비주얼 스크립트 / 머티리얼 같은 도구 작성 시 본 sub-skill** — Engine (런타임) + Editor (시각화) 모듈로 명확히 분리.

---

## 1. 개요

UE 의 **모든 노드 그래프** (Blueprint / Material / Niagara / AnimGraph / SoundCue / BehaviorTree / SequenceEditor 등) 는 `EdGraph` + `GraphEditor` 의 **공통 베이스** 를 사용:

| 영역 | 모듈 | 빌드 | 핵심 클래스 |
|------|------|------|-------------|
| **그래프 데이터 (런타임 OK)** | `Engine` | 게임 빌드 OK | `UEdGraph` / `UEdGraphNode` / `UEdGraphPin` / `UEdGraphSchema` |
| **시각화 (에디터 only)** 🛠 | `GraphEditor` | 게임 빌드 X | `SGraphEditor` / `SGraphPanel` / `SGraphNode` / `SGraphPin` / `FConnectionDrawingPolicy` |

**핵심 결정**:
- 실행 / 인터프리트 는 **런타임 (Engine 모듈)** — `UEdGraph::Nodes` 순회, `UEdGraphNode` 멤버 읽기
- 편집 / 와이어 시각화 / 컨텍스트 메뉴 는 **에디터 (GraphEditor 모듈)** — 게임 빌드 시 stripped

---

## 2. 🚨 런타임 / 에디터 모듈 분리 (이 sub-skill 의 핵심 규약)

> 메인 [`Slate/SKILL.md §8`](../SKILL.md#8--런타임--에디터-분리-원칙-인하우스-툴-묶음-공통-규약) 4단 방어 원칙 의무.

```
프로젝트 인하우스 노드 에디터 = 2개 모듈로 강제 분리:

[1] MyNodeRuntime/                  Type=Runtime    (게임 빌드 OK)
    ├── Build.cs : "Engine" 만 의존
    ├── UMyGraph (UEdGraph 자손)
    ├── UMyNodeBase (UEdGraphNode 자손) — 데이터·인터프리트 로직
    └── UMyAsset                       — UMyGraph 보유한 게임 에셋

[2] MyNodeEditor/                   Type=Editor     (게임 빌드 X)
    ├── Build.cs : "Slate","SlateCore","UnrealEd","GraphEditor","ToolMenus" 의존
    ├── UMyGraphSchema (UEdGraphSchema 자손) — 핀 정책
    ├── SMyNodeWidget (SGraphNode 자손) — 시각화
    ├── FMyAssetEditor (FAssetEditorToolkit 자손) — 도킹 + 그래프 에디터
    └── FMyNodeEditorModule — 에셋 액션 / 팩토리 등록
```

**4단 방어**:
1. **모듈 분리** — Runtime / Editor 두 모듈
2. **uplugin Type** — Runtime / Editor 명시
3. **Build.cs 분기** — Editor 모듈은 `bBuildDeveloperTools=true` 만
4. **`#if WITH_EDITOR`** — 에디터 전용 코드 가드

---

## 3. 핵심 헤더와 클래스

### 3.1 런타임 — `EdGraph/` 모듈 (Engine 의존)

| 헤더 | 클래스 | 역할 |
|------|--------|------|
| `EdGraph.h` | `UEdGraph` | 노드 컨테이너 — `Nodes` 배열 + `Schema` (UClass) |
| `EdGraphNode.h` | `UEdGraphNode` | 단일 노드 — `Pins` 배열 + `NodePosX/Y` + `NodeGuid` |
| `EdGraphPin.h` | `UEdGraphPin` | 핀 (포인트 데이터) — UObject 아님, GC 자체 시스템 |
| `EdGraphSchema.h` | `UEdGraphSchema` | 정책 — `CanCreateConnection` / `GetGraphContextActions` 등 50+ virtual |

**위 4개 헤더는 게임 빌드 안전**. 하지만 대부분의 멤버는 `WITH_EDITORONLY_DATA` 가드 — 런타임 빌드 시 stripped.

### 3.2 에디터 — `Editor/GraphEditor/` 모듈 (UnrealEd 의존) 🛠

70+ 헤더. 핵심:

| 헤더 / 폴더 | 역할 | 핵심 |
|-------------|------|------|
| `SGraphEditor.h` | 메인 위젯 | `.GraphToEdit(UEdGraph*)` + `FGraphEditorEvents` |
| `SGraphPanel.h` | 패닝/줌 컨테이너 | 노드 배치·드래그·zoom 처리 |
| `SGraphNode.h` | 노드 위젯 베이스 | `UpdateGraphNode` virtual |
| `SGraphPin.h` | 핀 위젯 베이스 | 핀 색상·타입 표시 |
| `NodeFactory.h` | `FNodeFactory` | 노드 → 위젯 매핑 (사용자 정의 등록) |
| `ConnectionDrawingPolicy.h` | `FConnectionDrawingPolicy` | 와이어 그리기 |
| `KismetNodes/` (폴더) | BP 노드 위젯 | 참고 패턴 |
| `MaterialNodes/` (폴더) | 머티리얼 노드 위젯 | 참고 패턴 |
| `DragAndDrop/` (폴더) | 그래프 드래그 작업 | `FGraphNodeDragDropOp`/`FGraphPinDragDropOp` — 노드/핀 드래그. |

> 🛠 위 70개 GraphEditor 헤더는 **본 위키 정식 분석 범위 외**(Editor 모듈). 라인 번호 인용은 신뢰성 한정 — 5.5.4 Editor 트리에서 확인된 것만 표기.

---

## 4 ~ 5 깊이 자료 — [`references/UEdGraphAPI.md`](./references/UEdGraphAPI.md) ✂️

> **Article 3 Level 3 progressive disclosure 적용** — 메인 SKILL.md 슬림화 (35KB → ~14KB) + 깊이 자료 별도 파일 (~18KB).

| § | 내용 | reference 위치 |
|---|------|----------------|
| 4.1 | **런타임 그래프·노드·핀 API** (NewObject<UEdGraph> + AllocateDefaultPins + CreatePin + Schema->TryCreateConnection + NotifyGraphChanged) | [`§1.1`](./references/UEdGraphAPI.md#11-런타임--그래프노드핀-만들기-게임-빌드-ok) |
| 4.2 | **SGraphEditor 띄우기** 🛠 (.GraphToEdit + FGraphEditorEvents 5종 콜백) | [`§1.2`](./references/UEdGraphAPI.md#12-에디터--sgrapheditor-띄우기-) |
| 4.3 | **사용자 정의 노드 위젯 등록** 🛠 (CreateVisualWidget override) | [`§1.3`](./references/UEdGraphAPI.md#13-사용자-정의-노드-위젯-등록-) |
| 4.4 | **사용자 정의 Schema 핵심 메서드** 🛠 (5개 핵심 virtual) | [`§1.4`](./references/UEdGraphAPI.md#14-사용자-정의-schema-핵심-메서드-) |
| 4.5 | **우클릭 노드 추가 메뉴 (`SGraphActionMenu`)** 🛠 | [`§1.5`](./references/UEdGraphAPI.md#15-우클릭-노드-추가-메뉴-sgraphactionmenu-) |
| 5.1 | **UEdGraph virtual** 🛠 (4개 — 모두 WITH_EDITORONLY_DATA 가드) | [`§2.1`](./references/UEdGraphAPI.md#21-uedgraph-런타임) |
| 5.2 | **UEdGraphNode virtual 30+** (가장 자주 — AllocateDefaultPins / CreateVisualWidget / NodeConnectionListChanged 등) | [`§2.2`](./references/UEdGraphAPI.md#22-uedgraphnode-사용자-정의-노드--가장-자주-override) |
| 5.3 | **UEdGraphSchema virtual 50+** (CanCreateConnection / GetGraphContextActions / GetPinTypeColor / SplitPin 등 22개 핵심) | [`§2.3`](./references/UEdGraphAPI.md#23-uedgraphschema-사용자-정의-schema--50-virtual) |
| 5.4 | **SGraphNode 위젯 virtual** 🛠 (UpdateGraphNode / CreateBelowWidgetControls 등) | [`§2.4`](./references/UEdGraphAPI.md#24-sgraphnode-위젯-virtual-) |
| 5.5 | **FConnectionDrawingPolicy** 🛠 (와이어 두께·색·스타일 + FKismetConnectionDrawingPolicy 패턴) | [`§2.5`](./references/UEdGraphAPI.md#25-fconnectiondrawingpolicy-) |

---

## 6. 인하우스 노드 에디터 모듈 골격

### 6.1 디렉토리 구조

```
Source/MyNodeRuntime/             (Type=Runtime — 게임 빌드 OK)
├─ MyNodeRuntime.Build.cs        : "Engine" 만 의존
├─ Public/
│   ├─ Graph/
│   │   ├─ UMyGraph.h             ← UEdGraph 자손 (또는 그대로 사용)
│   │   ├─ UMyNodeBase.h          ← UEdGraphNode 자손
│   │   ├─ UMyMathNode.h
│   │   └─ UMyConditionNode.h
│   └─ MyAsset.h                  ← UMyGraph 보유한 에셋

Source/MyNodeEditor/              (Type=Editor — 게임 빌드 X)
├─ MyNodeEditor.Build.cs         : "Slate", "SlateCore", "UnrealEd", "GraphEditor", "ToolMenus" 의존
├─ Public/
│   ├─ Schema/
│   │   └─ UMyGraphSchema.h       ← UEdGraphSchema 자손
│   ├─ Widgets/
│   │   ├─ SMyMathNodeWidget.h    ← SGraphNode 자손
│   │   └─ SMyMathPinWidget.h     ← SGraphPin 자손
│   ├─ FMyNodeEditorModule.h
│   └─ FMyAssetEditor.h           ← FAssetEditorToolkit 자손 (탭 매니저)
```

### 6.2 에디터 모듈 진입

```cpp
// FMyNodeEditorModule.cpp
void FMyNodeEditorModule::StartupModule()
{
    // 1) 에셋 액션 등록 — "Create > MyAsset"
    AssetTypeActions = MakeShared<FAssetTypeActions_MyAsset>();
    FAssetToolsModule::GetModule().Get().RegisterAssetTypeActions(AssetTypeActions.ToSharedRef());

    // 2) 사용자 정의 노드 팩토리 등록
    NodeFactory = MakeShared<FMyGraphNodeFactory>();
    FEdGraphUtilities::RegisterVisualNodeFactory(NodeFactory);

    // 3) 사용자 정의 핀 팩토리
    PinFactory = MakeShared<FMyGraphPinFactory>();
    FEdGraphUtilities::RegisterVisualPinFactory(PinFactory);

    // 4) 단축키 등록 (Commands sub-skill)
    FMyGraphCommands::Register();
}

void FMyNodeEditorModule::ShutdownModule()
{
    if (FAssetToolsModule::IsModuleLoaded("AssetTools") && AssetTypeActions.IsValid())
        FAssetToolsModule::GetModule().Get().UnregisterAssetTypeActions(AssetTypeActions.ToSharedRef());
    if (NodeFactory.IsValid()) FEdGraphUtilities::UnregisterVisualNodeFactory(NodeFactory);
    if (PinFactory.IsValid())  FEdGraphUtilities::UnregisterVisualPinFactory(PinFactory);
    FMyGraphCommands::Unregister();
}
```

### 6.3 에셋 에디터 토킷 (도킹 + 그래프 에디터 통합)

```cpp
void FMyAssetEditor::InitMyAssetEditor(UMyAsset* InAsset)
{
    EditingAsset = InAsset;
    GraphEditor = CreateGraphEditorWidget();

    TSharedRef<FTabManager::FLayout> Layout = FTabManager::NewLayout("MyAssetEditor_Layout_v1")
        ->AddArea(
            FTabManager::NewPrimaryArea()->SetOrientation(Orient_Horizontal)
            ->Split(FTabManager::NewStack()->SetSizeCoefficient(0.2f)->AddTab(PaletteTabId, ETabState::OpenedTab))
            ->Split(FTabManager::NewStack()->SetSizeCoefficient(0.6f)->AddTab(GraphTabId,   ETabState::OpenedTab))
            ->Split(FTabManager::NewStack()->SetSizeCoefficient(0.2f)->AddTab(DetailsTabId, ETabState::OpenedTab))
        );

    InitAssetEditor(...);
}

TSharedRef<SGraphEditor> FMyAssetEditor::CreateGraphEditorWidget()
{
    SGraphEditor::FGraphEditorEvents Events;
    Events.OnSelectionChanged   = FOnSelectionChanged::CreateSP(this, &FMyAssetEditor::OnNodeSelectionChanged);
    Events.OnNodeDoubleClicked  = FSingleNodeEvent::CreateSP(this, &FMyAssetEditor::OnNodeDoubleClicked);
    Events.OnCreateActionMenu   = SGraphEditor::FOnCreateActionMenu::CreateSP(this, &FMyAssetEditor::OnCreateActionMenu);

    return SNew(SGraphEditor)
        .AdditionalCommands(GraphCmds)
        .IsEditable(true)
        .GraphToEdit(EditingAsset->Graph)
        .GraphEvents(Events);
}
```

---

## 7. 운영 가이드 / 함정

1. **`UEdGraphPin` 은 UObject 가 아니다** — `NewObject<UEdGraphPin>` 금지. 항상 `UEdGraphNode::CreatePin(...)` 사용. GC 는 자체 시스템.
2. **`PinId` 는 보존** — `ReconstructNode` 시 같은 `PinId` 면 LinkedTo 자동 보존. 새로 만들면 연결 끊김.
3. **`AllocateDefaultPins` vs `ReconstructNode`** — 전자는 처음 생성, 후자는 핀 구조 변경 시 (옛 데이터 마이그레이션). `ReconstructNode` 안에서 옛 핀 → 새 핀 수동 매핑.
4. **`OrphanedPinSaveMode`** — 핀이 사라진 옛 노드 로드 시 처리 정책 (SaveAll/SaveValues/SaveNone). 호환성 핵심.
5. **Schema 클래스 (UClass) vs 인스턴스 (CDO)** — `Graph->Schema = UMyGraphSchema::StaticClass()` (UClass), `Graph->GetSchema()` 가 CDO 반환. CDO 라 멤버 변수 변경 금지 — 모든 정책은 virtual 안에서.
6. **`NotifyGraphChanged()`** 호출 누락 → 위젯 안 갱신.
7. **`UEdGraphSchema` virtual 의 `UE_SLATE_DEPRECATED_VECTOR_VIRTUAL_FUNCTION`** — 5.x 에서 `FVector2D` → `FVector2f` 마이그레이션 중.
8. **`CreateVisualWidget` nullptr 반환** → `FNodeFactory::CreateNodeWidget` 가 자동 처리.
9. **`FEdGraphUtilities::RegisterVisualNodeFactory`** — 모듈 셧다운 시 `Unregister` 누락하면 다음 hot-reload 댕글링.
10. **`FAssetEditorToolkit`** — 본 sub-skill 범위 외 (UnrealEd 모듈) 이지만 인하우스 에셋 에디터의 표준 진입점.
11. **그래프 직렬화 호환성** — 옛 .uasset 의 노드/핀 구조가 바뀌면 `PostLoad` + `ReconstructNode` 로 마이그레이션.
12. **컴파일 결과 게임에 가져가기** — EdGraph 자체는 런타임이지만 컴파일된 결과(BP의 `UFunction`/바이트코드)는 별도.

---

## 8. 에디터 전용 (WITH_EDITOR / WITH_EDITORONLY_DATA) 🛠

> **🚨 런타임/에디터 분리 원칙은 [`Slate/SKILL.md §8`](../SKILL.md#8--런타임--에디터-분리-원칙-인하우스-툴-묶음-공통-규약) 의무 규약.**

| 항목 | 위치 | 가드 | 메모 |
|------|------|------|------|
| `UEdGraph::SubGraphs`/`GraphGuid`/`InterfaceGuid` 🛠 | EdGraph.h | `WITH_EDITORONLY_DATA` | 에디터 빌드만 보유. |
| `UEdGraph::PostInitProperties`/`PostLoad`/`Serialize`/`BuildSubobjectMapping` 🛠 | EdGraph.h | `WITH_EDITORONLY_DATA` | 에디터 측 라이프사이클. |
| `UEdGraphNode::bCanResizeNode`/`bCommentBubble*`/`bCanRenameNode`/`NodeUpgradeMessage` 🛠 | EdGraphNode.h | `WITH_EDITORONLY_DATA` | 에디터 시각 메타. |
| `UEdGraphNode::GetNodeContextMenuActions`/`ValidateNodeDuringCompilation`/`GetMenuEntries` 🛠 | EdGraphNode.h L875~L887 | `WITH_EDITOR` | 에디터 콜백 다수. |
| `UEdGraphPin::bHidden`/`bAdvancedView`/`bDeprecated`/`bDisplayAsMutableRef` 🛠 | EdGraphPin.h | `WITH_EDITORONLY_DATA` | 시각 메타. |
| `UEdGraphSchema` 의 모든 50+ virtual 🛠 | EdGraphSchema.h | (UClass 자체는 런타임) | 정책 호출은 거의 모두 에디터에서. |
| **GraphEditor 모듈 전체** 🛠 | `Engine/Source/Editor/GraphEditor/` | 모듈 `Type=Editor` | `SGraphPanel`/`SGraphNode`/`SGraphPin`/`FNodeFactory`/`FConnectionDrawingPolicy` — 전부 에디터 빌드만. |
| `BlueprintGraph`/`KismetCompiler` 모듈 🛠 | `Engine/Source/Editor/` | 모듈 `Type=Editor` | BP 컴파일러 — 인하우스 노드 컴파일 시 참고. |

---

## 9. 관련 sub-skill

- [`EditorApplication/`](../EditorApplication/SKILL.md) — `FSlateApplication::Get()` 가 그래프 에디터를 띄움
- [`Docking/`](../Docking/SKILL.md) — 그래프 에디터를 `SDockTab` 으로 호스팅
- [`Menu/`](../Menu/SKILL.md) — 그래프 컨텍스트 메뉴 / 툴바
- [`Commands/`](../Commands/SKILL.md) — `FGraphEditorCommandsImpl` 가 같은 패턴
- [`../../CoreUObject/UObject/`](../../CoreUObject/references/UObject.md) — `UEdGraph`/`UEdGraphNode`/`UEdGraphSchema` 라이프사이클
- [`../../CoreUObject/Editor/`](../../CoreUObject/references/Editor.md) — `PostEditChangeProperty`·`Modify`
- [`../../CoreUObject/Serialization/`](../../CoreUObject/references/Serialization.md) — 그래프 직렬화·옛 .uasset 마이그레이션

---

## 10. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-06 | **Level 3 분리 완료** — §4~§5 깊이 자료를 [`references/UEdGraphAPI.md`](./references/UEdGraphAPI.md) 로 이동. 메인 35KB → ~14KB / reference ~18KB. |
