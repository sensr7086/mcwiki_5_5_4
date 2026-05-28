---
type: source
title: "04_OverrideIndex — Deep Reference (CoreUObject + SlateCore + Slate + UMG + RebuildWidget)"
slug: ue-ref-deep-overridetables
source_path: raw/ue-wiki-llm/references/deep/OverrideTablesDeep.md
source_kind: text
source_date: 2026-05-11
ingested: 2026-05-11
last_updated: 2026-05-15
related_entities:
  - "[[entities/UObject]]"
  - "[[entities/SWidget]]"
  - "[[entities/UWidget]]"
  - "[[entities/UUserWidget]]"
related_concepts:
  - "[[concepts/UMG-Super-Call-Convention]]"
  - "[[concepts/Object-Lifecycle]]"
tags: [ue, reference, override, lifecycle, enriched-card]
citation_disclosure: "🟢 16 / 🟡 3 / 🔴 0 · raw verified · Cycle 5f #1 enrich"
---

# 04_OverrideIndex — Deep Reference (§1~§5)

> Source: [[raw/ue-wiki-llm/references/deep/OverrideTablesDeep.md]]
> 부모: [[sources/ue-ref-04-overrideindex]] · [[concepts/UMG-Super-Call-Convention]]
> Cycle 5f #1 — stub 카드 → enrich 카드 (모듈별 virtual 매트릭스 + RebuildWidget 사이클 + 3-tier marker)

## 1. Summary

🟢 모듈별 virtual + override 매트릭스 5 카테고리 — CoreUObject (UObject 라이프사이클) + SlateCore (SWidget 베이스) + Slate (인하우스 툴) + UMG (위젯 라이프사이클) + RebuildWidget 사이클. Super 호출 규약 의무.

## 2. 모듈별 virtual 매트릭스 카탈로그 (raw §1~§5)

### 2.1 CoreUObject — UObject 라이프사이클 (raw §1.1) 🟢

| 시그니처 | 위치 | Super | 호출 시점 |
|----------|------|-------|-----------|
| `PostInitProperties()` | Object.h:222 | ✅ 처음 | UPROPERTY 기본값 적용 직후 |
| `PostLoad()` | L351 | ✅ 처음 | 디스크 로드 + 참조 해소 후 (마이그레이션) |
| `BeginDestroy()` | L366 | ✅ **마지막** | 파괴 1단계 — 비동기 작업 취소 |
| `IsReadyForFinishDestroy()` | L373 | ✅ AND | 비동기 정리 폴링 |
| `FinishDestroy()` | L387 | ✅ 마지막 | 파괴 2단계 |
| `GetWorld() const` | L719 | override 권장 | 위젯/컴포넌트 World |
| `Serialize(FArchive&)` | L393 | ✅ 처음 | UPROPERTY 자동 + 추가 데이터 |

### 2.2 CoreUObject — Editor 콜백 🛠 (raw §1.2) 🟢

`WITH_EDITOR` 가드 의무. `PostEditChangeProperty` 가 가장 자주 override (디테일 패널 값 변경). `IsDataValid` (`Object.h:1098`) = "Validate Asset". `GetAssetRegistryTags` = 에셋 검색.

### 2.3 CoreUObject — 네트워크 복제 (raw §1.3) 🟢

`GetLifetimeReplicatedProps` (`Object.h:1052`) = 거의 모든 복제 액터. `IsSupportedForNetworking` / `PreNetReceive` / `PostNetReceive` / `PostRepNotifies` / `ProcessEvent` (RPC 게이트) / `GetFunctionCallspace` (로컬/원격).

### 2.4 CoreUObject — 쿠킹/플랫폼 게이팅 (raw §1.4) 🟢

`NeedsLoadForClient/Server/TargetPlatform` / `IsEditorOnly` (쿠킹 자동 제외) / `IsPostLoadThreadSafe` / `BeginCacheForCookedPlatformData` 🛠 (`Object.h:1211` 사전 빌드) / `IsCachedCookedPlatformDataLoaded` 🛠 (폴링).

### 2.5 CoreUObject — FGCObject / FProperty (raw §1.5~§1.6) 🟢

- FGCObject: `AddReferencedObjects` (`GCObject.h:195` PURE_VIRTUAL) + `GetReferencerName` (L198 PURE_VIRTUAL) + `GetReferencerPropertyName` (L201 선택)
- FProperty PURE_VIRTUAL (커스텀 프로퍼티만): `GetCPPType` / `Identical` / `SerializeItem` / `ExportText_Internal` / `ImportText_Internal`

### 2.6 SlateCore — SWidget 베이스 (raw §2.1) 🟢

| 시그니처 | 위치 | 용도 |
|----------|------|------|
| `OnPaint(...) const = 0` | SWidget.h:1650 | PURE — 그리기 |
| `OnArrangeChildren(...) const = 0` | L1659 | PURE — 자식 배치 |
| `ComputeDesiredSize(float) const = 0` | L731 | PURE — 자연 크기 |
| `GetChildren() = 0` | L856 | PURE — 자식 컬렉션 |
| `ComputeVolatility() const` | L1616 | 휘발성 자동 결정 |
| `CustomPrepass(float)` | L710 | 커스텀 prepass |

### 2.7 SlateCore — 입력 (raw §2.2) 🟢

`FReply` 반환 기본 `Unhandled()`. 5 카테고리:
- 마우스 (Down/Up/DoubleClick/Move/Enter/Leave/Wheel/Drag*/CursorQuery)
- 키보드 (KeyDown/Up/Char/AnalogValueChanged)
- 포커스 (Received/Lost/Changing) + `SupportsKeyboardFocus()=true` 같이 override
- 터치/모션 (TouchStarted/Moved/Ended/Motion)
- 내비 + 캡처 (Navigation/MouseCaptureLost)

### 2.8 Slate — 인하우스 툴 (raw §3) 🟢

- **IInputProcessor 8 virtual** — 전역 입력 후크, `IInputProcessor.h:21-52`
- **TCommands<T>::RegisterCommands** — `UI_COMMAND` 매크로
- **FTabManager::TryInvokeTab** (`Docking.md L1049`) 드물게 override. SDockTab 9 SLATE_EVENT (`OnTabClosed`/`OnTabActivated` 등)
- **GraphEditor** 🛠 — UEdGraphNode 30+ / UEdGraphSchema 50+
  - UEdGraphNode 핵심 12: `AllocateDefaultPins` / `ReconstructNode` / `PinDefaultValueChanged` / `PinConnectionListChanged` / `NodeConnectionListChanged` / `AutowireNewNode` / `PostPlacedNewNode` / `CreateVisualWidget` 🛠
  - UEdGraphSchema 핵심 8: `GetGraphContextActions` / `CanCreateConnection` (`EdGraphSchema.h:773`) / `GetPinTypeColor` / `GetGraphType` / `CreateDefaultNodesForGraph` / `SplitPin` / `GetCreateCommentAction`
  - SGraphNode 위젯: `UpdateGraphNode` / `CreateBelowWidgetControls` / `OnAddPin`

### 2.9 UMG — UWidget 핵심 4 (raw §4.1) 🟢

| 시그니처 | 위치 | Super | 호출 시점 |
|----------|------|-------|-----------|
| `SynchronizeProperties()` | Widget.h:930 | ✅ 처음 | 디테일 패널 변경 / CreateWidget / RerunConstructionScript |
| `RebuildWidget()` (protected) | L1140 | (자체 SWidget 반환) | **UWidget → SWidget 변환, §5 별도** |
| `OnWidgetRebuilt()` | — | ✅ 처음 | RebuildWidget 직후 |
| `ReleaseSlateResources(bool)` (UVisual) | — | ✅ 처음 | SWidget 해제 |
| `SetIsEnabled` / `SetVisibility` | L545/L590 | (선택) | 활성/가시성 변경 |

### 2.10 UMG — UUserWidget Native* 30+ (raw §4.2) 🟢

- **라이프사이클 5**: `NativeOnInitialized` (L1574) / `NativePreConstruct` (L1575) / `NativeConstruct` (L1576, **매 뷰포트마다**) / `NativeDestruct` (L1577) / `NativeTick` (L1578, 매 프레임 TickFrequency 결정)
- **Paint 1** 🚨: `NativePaint` (L1584) — **반드시 Super 반환값 사용**, **마지막 수단** (자동 휘발성)
- **입력 30+**: 키보드 5 / 마우스 8 / 포커스 8 / 드래그 6 / 터치+모션 7

### 2.11 UMG — UUserWidget override 9 (raw §4.3) 🟢

`GetWorld() const override` / `Initialize()` (L300) / `GetOwningLocalPlayer() const override` (L411) / `GetOwningPlayer() const override` (L433) + UWidget/UVisual override (SynchronizeProperties / ReleaseSlateResources) + INamedSlotInterface (GetSlotNames / GetContentForSlot / SetContentForSlot).

## 3. ⚡ RebuildWidget 사이클 (raw §5) 🟢

> 가장 자주 만나는 패턴. UWidget 자손 작성 시 의무 이해.

### 3.1 사이클 도식

```
[UWidget 생성] → TakeWidget() → RebuildWidget() (한 번만, IsConstructed 체크)
                                       │
                              SNew(SXxx) + 멤버 보존 → 반환
                                       │
                              [SObjectWidget 부착]
                                       │
                              SynchronizeProperties() → 모든 UPROPERTY → Slate setter
                                       │
                              OnWidgetRebuilt() (선택 사후 처리)
                                       │
                              [정상 동작]
                                       │ (setter 호출)
                                  멤버 변경 + Slate setter → 자동 Invalidate(reason)
                                       │ (RemoveFromParent)
                              ReleaseSlateResources(true) → TSharedPtr Reset + Super
                                       │
                              [BeginDestroy → UObject 파괴]
```

### 3.2 작성 패턴 4단계 (raw §5.2)

1. **RebuildWidget**: `SNew(SXxx)` + 멤버 (TSharedPtr<SXxx>) 보존 + 반환 — Super 호출 X
2. **SynchronizeProperties**: Super FIRST + 모든 UPROPERTY 동기화 (멤버 IsValid 검사)
3. **ReleaseSlateResources**: Super FIRST + 멤버 Reset
4. **런타임 setter**: 멤버 변경 + Slate 측 setter 위임 (자동 Invalidate)

### 3.3 RebuildWidget vs SynchronizeProperties 호출 차이 (raw §5.3) 🟢

| 시점 | RebuildWidget | SynchronizeProperties |
|------|---------------|------------------------|
| 첫 트리 추가 (TakeWidget) | ✅ | ✅ (RebuildWidget 후) |
| 디자이너 UPROPERTY 변경 | ❌ | ✅ |
| `CreateWidget<T>` (UUserWidget) | ❌ | ✅ |
| `RemoveFromParent` 후 다시 추가 | ❌ (재사용) | ❌ |
| 런타임 setter 호출 | ❌ | ❌ |

🟢 **핵심**: RebuildWidget = 한 번만 / SynchronizeProperties = 여러 번.

### 3.4 RebuildWidget 함정 7종 (raw §5.4) 🟢

| # | 함정 | 정답 |
|---|------|------|
| 1 | `Super::RebuildWidget()` 호출 (빈 SBox 반환) | 자체 SNew 만 반환 |
| 2 | 멤버를 `TSharedRef` (nullptr 불가) | `TSharedPtr` |
| 3 | `SynchronizeProperties` Super 누락 | Super FIRST 필수 |
| 4 | `ReleaseSlateResources` Reset 누락 (GC 사이클) | Super + Reset 둘 다 |
| 5 | 외부 강 참조 (위젯 사이클) | TWeakObjectPtr / TWeakPtr |
| 6 | 런타임 setter 가 SynchronizeProperties 호출 (비효율) | 변경값만 Slate setter |
| 7 | RebuildWidget 안 IsConstructed 체크 (의미 X) | 항상 첫 호출 |

### 3.5 디자이너 분기 🛠 (raw §5.5) 🟢

`#if WITH_EDITOR` + `RebuildDesignWidget(Content)` override + `CreateDesignerOutline(Content)` — 디자이너 모드 외곽선/플레이스홀더.

## 4. Cross-link

- 부모: [[sources/ue-ref-04-overrideindex]] · [[concepts/UMG-Super-Call-Convention]]
- CoreUObject: [[sources/ue-coreuobject-uobject]] · [[sources/ue-coreuobject-editor]] · [[sources/ue-coreuobject-network]] · [[sources/ue-coreuobject-cooking]] · [[sources/ue-coreuobject-gc]]
- SlateCore: [[sources/ue-slatecore-swidget]] · [[sources/ue-slatecore-input]]
- Slate 🛠: [[sources/ue-slate-grapheditor]] · [[sources/ue-slate-docking]] · [[sources/ue-slate-commands]]
- UMG: [[sources/ue-umg-uwidget]] · [[sources/ue-umg-uuserwidget]] (§5.4 NativePaint 함정)
- 페어: [[sources/ue-ref-deep-invalidationhotspots]] §2.6 (NativePaint 회피)

## 5. 신뢰도 + 변경 이력

| 항목 | tier | 출처 |
|------|------|------|
| UObject 7 라이프사이클 | 🟢 verified | `Object.h:222,351,366,373,387,719,393` |
| UObject 9 Editor 콜백 | 🟢 verified | `Object.h:431-1098` |
| UObject 8 네트워크 | 🟢 verified | `Object.h:1052-1509` |
| UObject 7 쿠킹 | 🟢 verified | `Object.h:559-1218` |
| FGCObject 3 PURE_VIRTUAL | 🟢 verified | `GCObject.h:195-201` |
| FProperty 4 PURE_VIRTUAL | 🟡 inferred (자주 X) | `UnrealType.h:339-719` |
| SWidget 6 베이스 | 🟢 verified | `SWidget.h:710-1659` |
| Slate IInputProcessor 8 | 🟢 verified | `IInputProcessor.h:21-52` |
| GraphEditor UEdGraphNode 12 + UEdGraphSchema 8 | 🟢 verified | `EdGraphNode.h` + `EdGraphSchema.h:773` |
| UWidget 핵심 4 | 🟢 verified | `Widget.h:545-1140` |
| UUserWidget Native* 30+ | 🟢 verified | `UserWidget.h:1574-1624` |
| RebuildWidget 사이클 4 단계 + 함정 7 | 🟢 verified | raw §5 + UE 실측 |
| RebuildDesignWidget 🛠 | 🟡 verified | `#if WITH_EDITOR` |

| 날짜 | 변경 |
|------|------|
| 2026-05-11 | 04_OverrideIndex §1~§5 분리 |
| 2026-05-15 | Cycle 5f #1 — stub 카드 → enrich 카드 (모듈 5 매트릭스 + RebuildWidget 사이클 4단 + 함정 7 + 3-tier marker + Cross-link 12건) |
