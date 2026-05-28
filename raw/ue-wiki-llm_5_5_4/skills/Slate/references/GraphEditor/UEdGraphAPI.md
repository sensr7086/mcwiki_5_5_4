---
name: slate-grapheditor-uedgraphapi
description: UEdGraph + UEdGraphNode + UEdGraphSchema + SGraphNode + FConnectionDrawingPolicy 깊이 자료 — 자주 쓰는 API 5종 + 가상 함수 50+ 오버라이드 포인트.
---

# Slate / GraphEditor — UEdGraphAPI Reference

> 본 문서는 [`SKILL.md §4~§5`](../SKILL.md) 의 깊이 자료. 메인 SKILL.md 는 §1~§3 (개요/모듈분리/핵심클래스) + §6 (인하우스 골격) + §7~§9 (운영/에디터전용/관련). 본 reference 는 자주 쓰는 API + 가상 함수 깊이.
>
> **트리거**: 사용자 정의 노드 / Schema / 핀 / 와이어 / 위젯 작성 시 로드.

---

## 1. 자주 쓰는 API

### 1.1 런타임 — 그래프·노드·핀 만들기 (게임 빌드 OK)

```cpp
// === 그래프 만들기 ===
UEdGraph* Graph = NewObject<UEdGraph>(OuterAsset, UEdGraph::StaticClass());
Graph->Schema = UMyGraphSchema::StaticClass();
Graph->bEditable = true;
Graph->bAllowDeletion = true;

// === 노드 추가 ===
template<typename NodeType>
NodeType* AddNode(UEdGraph* G, FVector2D Pos)
{
    NodeType* Node = NewObject<NodeType>(G);
    G->Nodes.Add(Node);
    Node->NodePosX = Pos.X;
    Node->NodePosY = Pos.Y;
    Node->CreateNewGuid();
    Node->AllocateDefaultPins();
    return Node;
}
UMyMathNode* Add = AddNode<UMyMathNode>(Graph, FVector2D(100, 100));

// === 핀 만들기 (보통 AllocateDefaultPins 안에서) ===
UEdGraphPin* InPinA = CreatePin(EGPD_Input,  TEXT("Float"), TEXT("A"));
UEdGraphPin* InPinB = CreatePin(EGPD_Input,  TEXT("Float"), TEXT("B"));
UEdGraphPin* OutPin = CreatePin(EGPD_Output, TEXT("Float"), TEXT("Result"));

// === 핀 연결 ===
const UEdGraphSchema* Schema = Graph->GetSchema();
const FPinConnectionResponse Resp = Schema->CanCreateConnection(OutPinFromOther, InPinA);
if (Resp.Response != CONNECT_RESPONSE_DISALLOW)
{
    Schema->TryCreateConnection(OutPinFromOther, InPinA);
}

// === 그래프 변경 알림 ===
Graph->NotifyGraphChanged();
FDelegateHandle H = Graph->AddOnGraphChangedHandler(
    FOnGraphChanged::FDelegate::CreateLambda([](const FEdGraphEditAction& A) { /* ... */ }));
```

### 1.2 에디터 — SGraphEditor 띄우기 🛠

```cpp
#if WITH_EDITOR
TSharedRef<SGraphEditor> GraphEditor = SNew(SGraphEditor)
    .AdditionalCommands(MyCmds)
    .IsEditable(true)
    .DisplayAsReadOnly(false)
    .GraphToEdit(MyEdGraph)
    .GraphEvents(GraphEvents)
    .ShowGraphStateOverlay(true);

TSharedRef<SDockTab> Tab = SNew(SDockTab).TabRole(ETabRole::NomadTab)
    [ GraphEditor ];
#endif
```

`FGraphEditorEvents` 의 주요 콜백:

```cpp
SGraphEditor::FGraphEditorEvents Events;
Events.OnSelectionChanged = FOnSelectionChanged::CreateRaw(this, &FMyToolModule::OnNodeSelectionChanged);
Events.OnNodeDoubleClicked = FSingleNodeEvent::CreateRaw(this, &FMyToolModule::OnNodeDoubleClicked);
Events.OnTextCommitted     = FOnNodeTextCommitted::CreateRaw(this, &FMyToolModule::OnTitleCommitted);
Events.OnCreateActionMenu  = SGraphEditor::FOnCreateActionMenu::CreateRaw(this, &FMyToolModule::OnCreateActionMenu);
Events.OnNodeSpawnedByKeymap = SGraphEditor::FOnSpawnNodeByShortcut::CreateRaw(this, ...);
```

### 1.3 사용자 정의 노드 위젯 등록 🛠

`UEdGraphNode::CreateVisualWidget()` (virtual) 를 override 해서 직접 `SGraphNode` 자손 반환:

```cpp
// UMyMathNode.h
UCLASS()
class UMyMathNode : public UEdGraphNode
{
    GENERATED_BODY()
public:
    virtual void AllocateDefaultPins() override;
    virtual FText GetNodeTitle(ENodeTitleType::Type) const override;
    virtual FLinearColor GetNodeTitleColor() const override;

#if WITH_EDITOR
    virtual TSharedPtr<SGraphNode> CreateVisualWidget() override;
#endif
};

// UMyMathNode.cpp
#if WITH_EDITOR
TSharedPtr<SGraphNode> UMyMathNode::CreateVisualWidget()
{
    return SNew(SMyMathNodeWidget, this);
}
#endif
```

`CreateVisualWidget` 가 nullptr 반환하면 `FNodeFactory::CreateNodeWidget` 가 기본 `SGraphNodeDefault` 사용.

### 1.4 사용자 정의 Schema 핵심 메서드 🛠

```cpp
UCLASS()
class UMyGraphSchema : public UEdGraphSchema
{
    GENERATED_BODY()
public:
    virtual void GetGraphContextActions(FGraphContextMenuBuilder& ContextMenuBuilder) const override;
    virtual const FPinConnectionResponse CanCreateConnection(const UEdGraphPin* A, const UEdGraphPin* B) const override;
    virtual FLinearColor GetPinTypeColor(const FEdGraphPinType& PinType) const override;
    virtual void CreateDefaultNodesForGraph(UEdGraph& Graph) const override;
    virtual EGraphType GetGraphType(const UEdGraph* TestEdGraph) const override { return GT_Function; }
};
```

자세한 50+ virtual 은 §2.3.

### 1.5 우클릭 노드 추가 메뉴 (`SGraphActionMenu`) 🛠

```cpp
TSharedRef<SWidget> CreateActionMenu(...)
{
    TSharedRef<SGraphActionMenu> Menu = SNew(SGraphActionMenu)
        .OnActionSelected(FOnActionSelected::CreateRaw(this, &FMyToolModule::OnNodeAdded))
        .OnCollectAllActions(FOnCollectAllActions::CreateRaw(this, &FMyToolModule::CollectActions));
    return Menu;
}

void FMyToolModule::CollectActions(FGraphActionListBuilderBase& Out)
{
    TSharedPtr<FEdGraphSchemaAction_NewNode> Action(new FEdGraphSchemaAction_NewNode(...));
    Out.AddAction(Action);
}
```

---

## 2. 가상 함수 (오버라이드 포인트)

### 2.1 UEdGraph (런타임)

대부분 엔진이 처리. 게임 코드는 거의 override 하지 않음. UObject 라이프사이클은 [`../../../CoreUObject/UObject/`](../../../CoreUObject/references/UObject.md). 🛠 에디터 전용:

| 시그니처 | 위치 | 가드 |
|----------|------|------|
| `virtual void Serialize(FStructuredArchiveRecord)` 🛠 | EdGraph.h | `WITH_EDITORONLY_DATA` |
| `virtual void PostInitProperties()` 🛠 | EdGraph.h | `WITH_EDITORONLY_DATA` |
| `virtual void PostLoad()` 🛠 | EdGraph.h | `WITH_EDITORONLY_DATA` |
| `virtual void BuildSubobjectMapping(...)` 🛠 | EdGraph.h | `WITH_EDITORONLY_DATA` |

### 2.2 UEdGraphNode (사용자 정의 노드 — 가장 자주 override)

자주 override 하는 30+ virtual 중 핵심:

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual void AllocateDefaultPins()` | EdGraphNode.h L694 | **핵심** — 노드 생성 시 핀 배열 초기화 (`CreatePin` 호출). |
| `virtual void ReconstructNode()` | L702 | 리프레시 시 핀 재구성 (옛 데이터 마이그레이션). |
| `virtual void PinDefaultValueChanged(UEdGraphPin*)` | L812 | 핀 기본값 변경 시 — 의존 노드 갱신. |
| `virtual void PinConnectionListChanged(UEdGraphPin*)` | L815 | 핀 연결/해제 시. |
| `virtual void PinTypeChanged(UEdGraphPin*)` | L818 | 핀 타입 변경 시 (Wildcard 등). |
| `virtual void NodeConnectionListChanged()` | L826 | 모든 핀 연결 변화 후 한 번. |
| `virtual void AutowireNewNode(UEdGraphPin* FromPin)` | L805 | 드래그로 노드 추가 시 자동 와이어. |
| `virtual void PostPlacedNewNode()` | L809 | 새 노드 배치 직후. |
| `virtual void PostPasteNode()` | L732 | 복붙 후. |
| `virtual void PrepareForCopying()` | L712 | 복사 전. |
| `virtual bool CanPasteHere(const UEdGraph*) const` | L717 | 붙여넣기 가능 여부. |
| `virtual bool CanCreateUnderSpecifiedSchema(const UEdGraphSchema*) const` | L722 | Schema 호환성. |
| `virtual TArray<UEdGraph*> GetSubGraphs() const` | L687 | 서브 그래프 (collapsed nodes). |
| `virtual void GetNodeContextMenuActions(UToolMenu*, UGraphNodeContextMenuContext*) const` 🛠 | L875 | 노드 우클릭 메뉴 항목. |
| `virtual void ValidateNodeDuringCompilation(FCompilerResultsLog&) const` 🛠 | L881 | 컴파일 검증. |
| `virtual void GetMenuEntries(FGraphContextMenuBuilder&) const` 🛠 | L887 | 그래프 메뉴 등록. |
| `virtual TSharedPtr<INameValidatorInterface> MakeNameValidator() const` 🛠 | L890 | 이름 검증기. |
| `virtual void OnRenameNode(const FString& NewName)` 🛠 | L893 | 이름 변경 콜백. |
| `virtual bool SupportsCommentBubble() const` 🛠 | L899 | 코멘트 버블 표시. |
| `virtual void OnPinRemoved(UEdGraphPin*)` | L905 | 핀 제거 시. |
| `virtual UEdGraphPin* GetPassThroughPin(const UEdGraphPin*) const` | L937 | 핀 통과(예: Knot 노드). |
| `virtual TSharedPtr<SGraphNode> CreateVisualWidget()` 🛠 | L943 | **사용자 정의 위젯 반환** — 핵심 override. |
| `virtual TSharedPtr<SWidget> CreateNodeImage() const` 🛠 | L946 | 노드 미니맵 이미지. |

또한 `GetNodeTitle(ENodeTitleType)` / `GetNodeTitleColor()` / `GetTooltipText()` / `GetNodeContextMenuActions()` 도 자주.

### 2.3 UEdGraphSchema (사용자 정의 Schema — 50+ virtual)

핵심 22개:

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual void GetGraphContextActions(FGraphContextMenuBuilder&) const` | EdGraphSchema.h | 우클릭 메뉴에 노드 추가 액션 채움. |
| `virtual const FPinConnectionResponse CanCreateConnection(const UEdGraphPin* A, const UEdGraphPin* B) const` | L754 | 두 핀 연결 가능 여부 + 사용자 표시 메시지. |
| `virtual bool TryCreateConnection(UEdGraphPin*, UEdGraphPin*) const` | (베이스 자동) | 실제 연결 (LinkedTo 갱신). |
| `virtual const FPinConnectionResponse CanMergeNodes(const UEdGraphNode* A, const UEdGraphNode* B) const` | L767 | 두 노드 합치기 (Knot 등). |
| `virtual FLinearColor GetPinTypeColor(const FEdGraphPinType&) const` | L935 | 핀 색상 (FLinearColor). |
| `virtual FLinearColor GetSecondaryPinTypeColor(const FEdGraphPinType&) const` | L937 | 컨테이너 타입의 보조 색. |
| `virtual EGraphType GetGraphType(const UEdGraph*) const` | L974 | GT_Function/GT_Macro/GT_Animation/GT_StateMachine. |
| `virtual bool IsTitleBarPin(const UEdGraphPin&) const` | L983 | 타이틀바에 표시할 핀. |
| `virtual void SplitPin(UEdGraphPin*, bool bNotify=true) const` | L1012 | struct 핀 분해. |
| `virtual void RecombinePin(UEdGraphPin*) const` | L1015 | 분해된 핀 재결합. |
| `virtual void OnPinConnectionDoubleCicked(UEdGraphPin*, UEdGraphPin*, FVector2D) const` | L1018 | 와이어 더블클릭 (Reroute Knot). 5.5: FVector2D (5.7 에서 FVector2f). |
| `virtual bool IsSelfPin(const UEdGraphPin&) const` | L1034 | self 핀 판정. |
| `virtual void CreateDefaultNodesForGraph(UEdGraph&) const` | L1045 | 새 그래프 생성 시 기본 노드. |
| `virtual UEdGraphNode* CreateSubstituteNode(...) const` | L1110 | 노드 호환 안 될 때 대체. |
| `virtual TSharedPtr<FEdGraphSchemaAction> GetCreateCommentAction() const` | L1130 | 코멘트 박스 추가 액션. |
| `virtual bool TryDeleteGraph(UEdGraph*) const` | L1140 | 그래프 삭제 가능 여부. |
| `virtual bool TryRenameGraph(UEdGraph*, const FName&) const` | L1145 | 그래프 이름 변경. |
| `virtual FString IsPinDefaultValid(const UEdGraphPin*, const FString& NewVal, ...) const` | L882 | 핀 기본값 검증. |
| `virtual bool ShouldHidePinDefaultValue(UEdGraphPin*) const` | L946 | 기본값 입력 칸 숨김. |
| `virtual bool ShouldShowAssetPickerForPin(UEdGraphPin*) const` | L949 | 오브젝트 핀의 에셋 피커 표시. |
| `virtual bool DoesSupportPinWatching() const` 🛠 | L895 | 디버그 watch 지원. |

### 2.4 SGraphNode 위젯 virtual 🛠

`SGraphNode : SNodePanel::SNode` 에서 자주 override:

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual void UpdateGraphNode()` | (SGraphNode.h) | **핵심** — 위젯 트리 빌드 (타이틀·핀 영역·하단 컨트롤). |
| `virtual void CreateBelowWidgetControls(TSharedPtr<SVerticalBox>)` | L345 | 노드 하단 추가 위젯 (예: 미리보기). |
| `virtual void CreateBelowPinControls(TSharedPtr<SVerticalBox>)` | L348 | 핀 영역 아래 위젯. |
| `virtual void CreateInputSideAddButton(TSharedPtr<SVerticalBox>)` | L428 | 입력 측 "+" 버튼 (가변 핀 노드). |
| `virtual void CreateOutputSideAddButton(TSharedPtr<SVerticalBox>)` | L431 | 출력 측 "+" 버튼. |
| `virtual FReply OnAddPin()` | L440 | "+" 버튼 클릭 시. |
| `virtual TSharedPtr<SToolTip> GetComplexTooltip()` | L342 | 호버 툴팁 (커스텀). |
| `virtual void SetDefaultTitleAreaWidget(TSharedRef<SOverlay>)` | L416 | 타이틀 오버레이 (아이콘·뱃지). |
| `virtual bool UseLowDetailPinNames() const` | L389 | 줌아웃 시 저상세 라벨. |
| `virtual FSlateColor GetCommentColor() const` | L394 | 코멘트 색. |

### 2.5 FConnectionDrawingPolicy 🛠

| 시그니처 | 용도 |
|----------|------|
| `virtual void DetermineWiringStyle(UEdGraphPin*, UEdGraphPin*, FConnectionParams&)` | 와이어 두께·색·스타일. |
| `virtual void Draw(...)` | 와이어 자체 그리기. |
| `virtual void DrawSplineWithArrow(...)` | 화살표 포함 곡선. |

`FKismetConnectionDrawingPolicy` (BP) — 실행 와이어/데이터 와이어 차별화. 같은 패턴으로 사용자 정의 가능.

---

## 3. 변경 이력

| 날짜 | 변경 |
|------|------|
| 2026-05-06 | Slate/references/GraphEditor.md §4~§5 에서 분리. 메인 35KB → ~17KB / reference ~18KB. |
