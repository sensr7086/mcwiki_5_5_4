---
name: override-tables-deep
description: 모듈별 virtual 함수 + override 테이블 깊이 자료 — CoreUObject (UObject 라이프사이클) + SlateCore (SWidget 베이스) + Slate (인하우스 툴) + UMG (위젯 라이프사이클) + RebuildWidget 사이클.
---

# Override Index — Deep Reference (§1~§5)

> 본 문서는 [`04_OverrideIndex.md`](../04_OverrideIndex.md) 의 §1~§5 깊이 자료. 메인 문서는 §0 사용 규칙 + §6 Super 호출 순서 통합 표 (가장 자주 틀리는 부분). 본 reference 는 모듈별 virtual 함수 상세 표.

---

## 1. CoreUObject 모듈 — 가장 자주 override

### 1.1 UObject 라이프사이클 (가장 자주)

> 위치: [`skills/CoreUObject/references/UObject.md §4.1`](../skills/CoreUObject/references/UObject.md). `Object.h` 라인 번호.

| 시그니처 | 위치 | Super 필수 | 호출 시점 |
|----------|------|------------|-----------|
| `virtual void PostInitProperties()` | L222 | ✅ 처음 | 생성자 + UPROPERTY 기본값 적용 직후 |
| `virtual void PostLoad()` | L351 | ✅ 처음 | 디스크 로드 + 참조 해소 후 — 마이그레이션 표준 |
| `virtual void BeginDestroy()` | L366 | ✅ **마지막** | 파괴 1단계 — 비동기 작업 취소 |
| `virtual bool IsReadyForFinishDestroy()` | L373 | ✅ AND | 비동기 정리 완료 폴링 |
| `virtual void FinishDestroy()` | L387 | ✅ 마지막 | 파괴 2단계 — 메모리 해제 직전 |
| `virtual UWorld* GetWorld() const` | L719 | (override 권장) | 위젯/컴포넌트의 World 반환 |
| `virtual void Serialize(FArchive&)` | L393 | ✅ 처음 | UPROPERTY 자동 직렬화 + 추가 데이터 |

### 1.2 UObject 에디터 콜백 🛠

> 위치: [`CoreUObject/references/Editor.md §4`](../skills/CoreUObject/references/Editor.md). 자세한 §5 참조.

| 시그니처 | 위치 | 가드 | 용도 |
|----------|------|------|------|
| `virtual void PreEditChange(FProperty*)` 🛠 | Object.h L431 | `WITH_EDITOR` | 디테일 패널 변경 직전 |
| `virtual void PostEditChangeProperty(FPropertyChangedEvent&)` 🛠 | Object.h L473 | `WITH_EDITOR` | **가장 자주 override** — 값 변경 후 |
| `virtual void PostEditChangeChainProperty(FPropertyChangedChainEvent&)` 🛠 | Object.h L479 | `WITH_EDITOR` | 중첩 USTRUCT 변경 |
| `virtual bool CanEditChange(const FProperty*) const` 🛠 | Object.h L450 | `WITH_EDITOR` | 편집 가능 여부 |
| `virtual bool Modify(bool bAlwaysMarkDirty=true)` 🛠 (실효) | Object.h L308 | (런타임 시그니처) | Undo 트랜잭션 등록 |
| `virtual void PreEditUndo()` / `PostEditUndo()` 🛠 | Object.h L485 / L488 | `WITH_EDITOR` | Undo 전후 |
| `virtual EDataValidationResult IsDataValid(FDataValidationContext&) const` 🛠 | Object.h L1098 | `WITH_EDITOR` | "Validate Asset" |
| `virtual void GetAssetRegistryTags(FAssetRegistryTagsContext)` 🛠 | Object.h L898 | `WITH_EDITORONLY_DATA` | 에셋 검색 태그 |
| `virtual void PostDuplicate(EDuplicateMode::Type)` 🛠 | Object.h L539 | `WITH_EDITOR` | 복제 후 |

### 1.3 UObject 네트워크 복제

> 위치: [`CoreUObject/references/Network.md §4`](../skills/CoreUObject/references/Network.md).

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>&) const` | Object.h L1052 | **거의 모든 복제 액터/컴포넌트** — `DOREPLIFETIME*` |
| `virtual bool IsSupportedForNetworking() const` | Object.h L1072 | 네트워크 직렬화 적합 |
| `virtual bool IsNameStableForNetworking() const` | Object.h L1066 | Name 식별 안정성 |
| `virtual void PreNetReceive()` / `PostNetReceive()` | Object.h L1079 / L1082 | 복제 패킷 전후 |
| `virtual void PostRepNotifies()` | Object.h L1085 | 모든 RepNotify 후 |
| `virtual void PreDestroyFromReplication()` | Object.h L1088 | 서버 파괴 수신 |
| `virtual void ProcessEvent(UFunction*, void*)` | Object.h L1499 | UFUNCTION 디스패치 — RPC 게이트 |
| `virtual int32 GetFunctionCallspace(UFunction*, FFrame*)` | Object.h L1509 | 로컬/원격 결정 |

### 1.4 UObject 쿠킹·플랫폼 게이팅

> 위치: [`CoreUObject/references/Cooking.md §4`](../skills/CoreUObject/references/Cooking.md).

| 시그니처 | 위치 | 의미 (false → 빌드 제외) |
|----------|------|--------------------------|
| `virtual bool NeedsLoadForClient() const` | Object.h L559 | 클라 빌드 |
| `virtual bool NeedsLoadForServer() const` | Object.h L567 | 서버 빌드 |
| `virtual bool NeedsLoadForTargetPlatform(const ITargetPlatform*) const` | Object.h L575 | 특정 타겟 |
| `virtual bool IsEditorOnly() const` | Object.h L593 | 쿠킹 자동 제외 |
| `virtual bool IsPostLoadThreadSafe() const` | Object.h L614 | 비동기 PostLoad 가능 |
| `virtual void BeginCacheForCookedPlatformData(const ITargetPlatform*)` 🛠 | Object.h L1211 | `WITH_EDITOR` — 쿠킹 사전 빌드 |
| `virtual bool IsCachedCookedPlatformDataLoaded(const ITargetPlatform*)` 🛠 | Object.h L1218 | `WITH_EDITOR` — 폴링 |

### 1.5 FGCObject (비-UObject 매니저용)

> 위치: [`CoreUObject/references/GC.md §4.1`](../skills/CoreUObject/references/GC.md).

| 시그니처 | 위치 | 의미 |
|----------|------|------|
| `virtual void AddReferencedObjects(FReferenceCollector&) = 0` | GCObject.h L195 | **PURE_VIRTUAL** — 모든 보유 UObject 등록 |
| `virtual FString GetReferencerName() const = 0` | GCObject.h L198 | **PURE_VIRTUAL** — 디버그 이름 |
| `virtual bool GetReferencerPropertyName(UObject*, FString&) const` | GCObject.h L201 | 어느 멤버가 잡고 있는지 (선택) |

### 1.6 FProperty PURE_VIRTUAL (커스텀 프로퍼티 작성 시)

> 위치: [`CoreUObject/references/Property.md §4.1`](../skills/CoreUObject/references/Property.md). 일반 게임 코드는 거의 override 안 함.

| 시그니처 | 위치 | 의미 |
|----------|------|------|
| `virtual FString GetCPPType(FString*, uint32) const` | UnrealType.h L339 | C++ 표기 |
| `virtual bool Identical(const void*, const void*, uint32) const` | UnrealType.h L515 | 두 값 동일 |
| `virtual void SerializeItem(FStructuredArchive::FSlot, void*, const void*) const` | UnrealType.h L581 | 단일 값 직렬화 |
| `virtual void ExportText_Internal(...)` / `ImportText_Internal(...)` | UnrealType.h L718 / L719 | 텍스트 변환 |

---

## 2. SlateCore 모듈 — 위젯 기본 virtual

### 2.1 SWidget 레이아웃·페인트 (가장 자주)

> 위치: [`SlateCore/references/SWidget.md §4`](../skills/SlateCore/references/SWidget.md).

| 시그니처 | 위치 | Super | 용도 |
|----------|------|-------|------|
| `virtual int32 OnPaint(...) const = 0` | SWidget.h L1650 | (자식 OnPaint 받기) | 그리기 — `FSlateDrawElement::Make*` 누적 |
| `virtual void OnArrangeChildren(const FGeometry&, FArrangedChildren&) const = 0` | SWidget.h L1659 | — | Panel/CompoundWidget 자식 배치 |
| `virtual FVector2D ComputeDesiredSize(float) const = 0` | SWidget.h L731 | — | 자연 크기 |
| `virtual FChildren* GetChildren() = 0` | SWidget.h L856 | — | 자식 컬렉션 |
| `virtual bool ComputeVolatility() const` | SWidget.h L1616 | — | 휘발성 자동 결정 |
| `virtual bool CustomPrepass(float)` | SWidget.h L710 | — | 커스텀 prepass |

### 2.2 SWidget 입력 (FReply 반환)

> 위치: [`SlateCore/references/Input.md §4`](../skills/SlateCore/references/Input.md). 기본은 `FReply::Unhandled()`.

| 카테고리 | 시그니처 핵심 |
|----------|--------------|
| 마우스 | `OnMouseButtonDown/Up/DoubleClick/Move/Enter/Leave/Wheel`, `OnDragDetected/Enter/Over/Drop/Leave`, `OnCursorQuery` |
| 키보드 | `OnKeyDown/Up`, `OnKeyChar`, `OnAnalogValueChanged` |
| 포커스 | `OnFocusReceived/Lost`, `OnFocusChanging` |
| 터치/모션 | `OnTouchStarted/Moved/Ended`, `OnMotionDetected` |
| 내비 | `OnNavigation` (FNavigationReply 반환) |
| 캡처 | `OnMouseCaptureLost` |

`SupportsKeyboardFocus() = true` 도 같이 override 해야 키 이벤트 도착.

### 2.3 FProperty / FField (커스텀 프로퍼티)

§1.6 동일. SlateCore 측 추가 virtual 없음.

---

## 3. Slate 모듈 — 인하우스 툴 묶음

### 3.1 IInputProcessor (전역 입력 후크)

> 위치: [`Slate/references/EditorApplication.md §6.1`](../skills/Slate/references/EditorApplication.md). 8 virtual.

| 시그니처 | 위치 | 의미 |
|----------|------|------|
| `virtual void Tick(float, FSlateApplication&, TSharedRef<ICursor>) = 0` | IInputProcessor.h L21 | 매 프레임 |
| `virtual bool HandleKeyDownEvent(FSlateApplication&, const FKeyEvent&)` | L24 | true → 위젯 트리 차단 |
| 그 외 7개 (`HandleKeyUp`/`HandleAnalog`/`HandleMouseMove`/`HandleMouseButton*`/`HandleMouseWheel`/`HandleMotion*`) | L27~L52 | 동일 패턴 |

### 3.2 TCommands<T>

> 위치: [`Slate/references/Commands.md §4.1`](../skills/Slate/references/Commands.md). 1 virtual (필수).

| 시그니처 | 의미 |
|----------|------|
| `virtual void RegisterCommands() override` | `UI_COMMAND` 매크로로 명령 정의 |

### 3.3 FTabManager / SDockTab 콜백 🛠

> 위치: [`Slate/references/Docking.md §4`](../skills/Slate/references/Docking.md).

`FTabManager::TryInvokeTab` (L1049, virtual) — 드물게 override. SDockTab 의 9 SLATE_EVENT 콜백 (`OnTabClosed`/`OnTabActivated`/`OnTabRelocated`/`OnCanCloseTab`/`OnPersistVisualState`/`OnExtendContextMenu` 등).

### 3.4 GraphEditor — UEdGraphNode / UEdGraphSchema 🛠

> 위치: [`Slate/references/GraphEditor.md §5`](../skills/Slate/references/GraphEditor.md). **UEdGraphNode 30+ / UEdGraphSchema 50+**.

UEdGraphNode 핵심 12 (전체는 sub-skill §5.2 표 참조):

| 시그니처 | 위치 |
|----------|------|
| `virtual void AllocateDefaultPins()` | EdGraphNode.h L704 |
| `virtual void ReconstructNode()` | L712 |
| `virtual void PinDefaultValueChanged(UEdGraphPin*)` | L827 |
| `virtual void PinConnectionListChanged(UEdGraphPin*)` | L830 |
| `virtual void NodeConnectionListChanged()` | L841 |
| `virtual void AutowireNewNode(UEdGraphPin*)` | L820 |
| `virtual void PostPlacedNewNode()` | L824 |
| `virtual TSharedPtr<SGraphNode> CreateVisualWidget()` 🛠 | L964 |

UEdGraphSchema 핵심 8 (전체는 sub-skill §5.3):

| 시그니처 | 위치 |
|----------|------|
| `virtual void GetGraphContextActions(FGraphContextMenuBuilder&) const` | (베이스) |
| `virtual const FPinConnectionResponse CanCreateConnection(const UEdGraphPin*, const UEdGraphPin*) const` | EdGraphSchema.h L773 |
| `virtual FLinearColor GetPinTypeColor(const FEdGraphPinType&) const` | L964 |
| `virtual EGraphType GetGraphType(const UEdGraph*) const` | L1013 |
| `virtual void CreateDefaultNodesForGraph(UEdGraph&) const` | L1091 |
| `virtual void SplitPin(UEdGraphPin*, bool=true) const` | L1051 |
| `virtual TSharedPtr<FEdGraphSchemaAction> GetCreateCommentAction() const` | L1130 |

SGraphNode 위젯 virtual (Editor 모듈):

| 시그니처 | 위치 |
|----------|------|
| `virtual void UpdateGraphNode()` 🛠 | (Editor) |
| `virtual void CreateBelowWidgetControls(TSharedPtr<SVerticalBox>)` 🛠 | L345 |
| `virtual FReply OnAddPin()` 🛠 | L440 |

---

## 4. UMG 모듈 — 위젯 라이프사이클

### 4.1 UWidget 핵심 4 (가장 자주)

> 위치: [`UMG/references/UWidget.md §4.1`](../skills/UMG/references/UWidget.md).

| 시그니처 | 위치 | Super | 호출 시점 |
|----------|------|-------|-----------|
| `virtual void SynchronizeProperties()` | Widget.h L930 | ✅ 처음 | 디테일 패널 변경 / CreateWidget / RerunConstructionScript |
| `virtual TSharedRef<SWidget> RebuildWidget()` (protected) | Widget.h L1140 | (override 시 자체 위젯 반환) | UWidget → SWidget 변환 — **§5 별도** |
| `virtual void OnWidgetRebuilt()` | Widget.h | ✅ 처음 | RebuildWidget 직후 |
| `virtual void ReleaseSlateResources(bool)` (UVisual) | Visual.h | ✅ 처음 | SWidget 해제 |
| `virtual void SetIsEnabled(bool)` | Widget.h L545 | (선택) | 활성 변경 |
| `virtual void SetVisibility(ESlateVisibility)` | Widget.h L590 | (선택) | 가시성 변경 |

### 4.2 UUserWidget Native\* 30+

> 위치: [`UMG/references/UUserWidget.md §4`](../skills/UMG/references/UUserWidget.md). 라이프사이클 5 + Paint 1 + 입력 30+ 분류.

#### 라이프사이클 (5)

| 시그니처 | 위치 | Super | 호출 시점 |
|----------|------|-------|-----------|
| `virtual void NativeOnInitialized()` | UserWidget.h L1574 | ✅ 처음 | `Initialize()` 안 — 한 번만 |
| `virtual void NativePreConstruct()` | L1575 | ✅ 처음 | 디자이너 미리보기 + 실행 전 |
| `virtual void NativeConstruct()` | L1576 | ✅ 처음 | **매 뷰포트 추가마다** |
| `virtual void NativeDestruct()` | L1577 | ✅ 마지막 (또는 처음, 정리 순서) | 매 뷰포트 제거마다 |
| `virtual void NativeTick(const FGeometry&, float DeltaTime)` | L1578 | ✅ 처음 | **매 프레임** (TickFrequency 결정 시) |

#### Paint (1 — 함정 의무)

| 시그니처 | 위치 | Super | 메모 |
|----------|------|-------|------|
| `virtual int32 NativePaint(const FPaintArgs&, const FGeometry&, const FSlateRect&, FSlateWindowElementList&, int32 LayerId, const FWidgetStyle&, bool) const` | L1584 | **반드시 ✅ — 반환값 사용** | **마지막 수단** — 자동 휘발성. 자세한 함정 [`UMG/references/UUserWidget.md §5.4`](../skills/UMG/references/UUserWidget.md) |

#### 입력 (FReply 반환)

| 카테고리 | virtual 묶음 | 위치 |
|----------|--------------|------|
| 키보드 | `NativeOnPreviewKeyDown`/`NativeOnKeyDown`/`NativeOnKeyUp`/`NativeOnKeyChar`/`NativeOnAnalogValueChanged` | L1600/L1601/L1602/L1599/L1603 |
| 마우스 | `NativeOnPreviewMouseButtonDown`/`NativeOnMouseButtonDown`/`Up`/`DoubleClick`/`Move`/`Enter`/`Leave`/`Wheel` | L1605/L1604/L1606/L1611/L1607/L1608/L1609/L1610 |
| 포커스 | `NativeOnFocusReceived`/`Lost`/`Changing`/`AddedToFocusPath`/`RemovedFromFocusPath` + `NativeSupportsKeyboardFocus`/`NativeSupportsCustomNavigation`/`NativeIsInteractable` | L1593~L1597 + L1589~L1591 |
| 드래그 | `NativeOnDragDetected`/`Enter`/`Leave`/`Over`/`Drop`/`Cancelled` | L1612~L1617 |
| 터치/모션 | `NativeOnTouchStarted`/`Moved`/`Ended`/`Gesture`/`ForceChanged`/`FirstMove` + `NativeOnMotionDetected` | L1619~L1624 + L1622 |

### 4.3 UUserWidget UWidget/UVisual/UObject override

> [`UMG/references/UUserWidget.md §4.4`](../skills/UMG/references/UUserWidget.md).

| 시그니처 | 위치 |
|----------|------|
| `virtual UWorld* GetWorld() const override` | UserWidget.h |
| `virtual bool Initialize()` | L300 |
| `virtual ULocalPlayer* GetOwningLocalPlayer() const override` | L411 |
| `virtual APlayerController* GetOwningPlayer() const override` | L433 |
| `virtual void SynchronizeProperties() override` (UWidget) | UserWidget.h |
| `virtual void ReleaseSlateResources(bool) override` (UVisual) | UserWidget.h |
| `virtual void GetSlotNames(TArray<FName>&) const override` (INamedSlotInterface) | UserWidget.h |
| `virtual UWidget* GetContentForSlot(FName) const override` | UserWidget.h |
| `virtual void SetContentForSlot(FName, UWidget*) override` | UserWidget.h |

---

## 5. ⚡ RebuildWidget 사이클 (UMG → SlateCore 변환의 핵심)

> 본 위키에서 가장 자주 만나는 패턴. UWidget 자손 작성 시 **반드시 이해해야 한다**.

### 5.1 사이클 전체 도식

```
[디자이너 / C++ 에서 UWidget 생성]
        │
        │ NewObject<T>(Outer)  + (BP라면) Initialize()
        ▼
[UWidget 인스턴스 — UPROPERTY 멤버 보유, SWidget 미생성]
        │
        │ (부모가 트리에 추가 또는 AddToViewport 시)
        ▼
[UWidget::TakeWidget() 호출됨]
        │
        │ 내부에서 RebuildWidget() 호출 (한 번만 — IsConstructed() 체크)
        ▼
TSharedRef<SWidget> RebuildWidget() override
   ├─ SNew(SXxx) 로 Slate 위젯 생성
   ├─ 멤버 (TSharedPtr<SXxx>) 에 보존
   └─ 반환
        │
        ▼
[SObjectWidget 생성 — Slate 트리에 부착]
        │
        ▼
SynchronizeProperties() 호출
   └─ UPROPERTY → Slate 위젯에 반영 (모든 setter)
        │
        ▼
OnWidgetRebuilt() 호출 (선택 — 사후 처리)
        │
        ▼
[정상 동작 — 사용자 인터랙션·페인트·Tick]
        │
        │ (UWidget 멤버 변경 시)
        ▼
사용자 정의 SetXxx() → 멤버 변경 + Slate 측 setter 호출
   └─ Slate setter 가 자동 Invalidate(reason)
        │
        ▼
[제거 — RemoveFromParent / 부모 트리에서 제거]
        │
        ▼
ReleaseSlateResources(bRelease) 호출
   ├─ TSharedPtr<SXxx> Reset()
   └─ Super::ReleaseSlateResources(true) — 자식까지 재귀
        │
        ▼
[BeginDestroy → UObject 파괴]
```

### 5.2 RebuildWidget — 작성 패턴 (필수 4단계)

```cpp
UCLASS()
class UMyHealthBar : public UWidget
{
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Percent = 1.f;

    UFUNCTION(BlueprintCallable)
    void SetPercent(float NewPercent);

protected:
    // 1) Slate 위젯 생성 — SNew + 멤버 보존
    virtual TSharedRef<SWidget> RebuildWidget() override
    {
        MyProgressBar = SNew(SProgressBar).Percent(Percent);
        return MyProgressBar.ToSharedRef();
    }

    // 2) UPROPERTY → Slate 동기화 — 디자이너/생성 시 호출
    virtual void SynchronizeProperties() override
    {
        Super::SynchronizeProperties();   // Visibility/Enabled 등 부모 동기화
        if (MyProgressBar.IsValid())
        {
            MyProgressBar->SetPercent(Percent);
            // 다른 UPROPERTY 들도 여기서 모두 동기화
        }
    }

    // 3) 해제 — Reset + Super
    virtual void ReleaseSlateResources(bool bReleaseChildren) override
    {
        Super::ReleaseSlateResources(bReleaseChildren);
        MyProgressBar.Reset();
    }

private:
    TSharedPtr<SProgressBar> MyProgressBar;
};

// 4) 런타임 setter — Slate 측 setter 위임 (자동 Invalidate)
void UMyHealthBar::SetPercent(float NewPercent)
{
    Percent = FMath::Clamp(NewPercent, 0.f, 1.f);
    if (MyProgressBar.IsValid())
    {
        MyProgressBar->SetPercent(Percent);    // SProgressBar 가 자동 Invalidate(Paint)
    }
}
```

### 5.3 RebuildWidget vs SynchronizeProperties — 호출 시점 차이

| 시점 | RebuildWidget | SynchronizeProperties |
|------|---------------|------------------------|
| 첫 트리 추가 (TakeWidget) | ✅ | ✅ (RebuildWidget 후) |
| 디자이너 UPROPERTY 변경 | ❌ | ✅ |
| `CreateWidget<T>` (UUserWidget) | ❌ (BP가 트리 다 만들고 한 번에 RebuildWidget) | ✅ (Initialize 안에서) |
| `RemoveFromParent` 후 다시 추가 | ❌ (이미 만들어진 SWidget 재사용) | ❌ |
| 런타임 setter 호출 | ❌ | ❌ (사용자가 명시적으로 동기화) |

**핵심**: `RebuildWidget` 은 **한 번만** 호출 (IsConstructed() 체크). `SynchronizeProperties` 는 **여러 번** 호출 가능. 둘 다 중요하지만 역할이 다르다.

### 5.4 RebuildWidget 함정

1. **`RebuildWidget` 안에서 `Super::RebuildWidget()` 호출 금지** — 베이스 UWidget::RebuildWidget() 은 빈 SBox 반환. 자체 SNew 만 반환.
2. **Slate 위젯 멤버를 `TSharedPtr` 로 보존** — `TSharedRef` 는 nullptr 가능성 없어서 부적합. 위젯 트리 사이클상 멤버는 `TSharedPtr`.
3. **`SynchronizeProperties` 안에서 `Super::SynchronizeProperties()` 누락** → `Visibility`/`IsEnabled` 등 부모 동기화 안 됨. **반드시 처음에 Super 호출**.
4. **`ReleaseSlateResources` 안에서 `Reset()` 누락** → Slate 위젯이 살아있으면 GC 사이클. `Super::` + `Reset()` 둘 다.
5. **`RebuildWidget` 안에서 외부 강 참조** → 위젯 사이클 가능. `TWeakObjectPtr`/`TWeakPtr` 권장.
6. **런타임 setter 가 `SynchronizeProperties()` 호출** → 비효율. 변경된 값 하나만 Slate setter 로 위임.
7. **`RebuildWidget` 안에서 `IsConstructed()` 체크** → 의미 없음. RebuildWidget 자체가 첫 호출이라 항상 false.

### 5.5 RebuildWidget 디자이너 분기 🛠

```cpp
#if WITH_EDITOR
virtual TSharedRef<SWidget> RebuildDesignWidget(TSharedRef<SWidget> Content) override
{
    // 디자이너에서만 보이는 외곽선·플레이스홀더 추가
    return CreateDesignerOutline(Content);     // UWidget 헬퍼
}
#endif
```

게임 빌드와 디자이너 모드의 시각이 다를 수 있을 때 사용.

---

