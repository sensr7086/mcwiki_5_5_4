---
type: synthesis
title: "InstancedSubobject Customization Bypass — RegisterCustomClassLayout 미발화 + 4종 우회"
slug: instanced-subobject-customization-bypass
created: 2026-05-12
last_updated: 2026-05-12
sources:
  - "[[sources/ue-editor-propertyeditor]]"
  - "[[sources/ue-editor-asseteditorapi]]"
  - "[[sources/ue-editor-unrealed-asseteditortoolkit]]"
  - "[[sources/ue-assetclasses-assetuserdata]]"
  - "[[sources/ue-editor-personatoolkit]]"
  - "[[sources/ue-editor-eventbinding]]"
  - "[[sources/ue-slate-docking]]"
  - "[[sources/ue-slate-skill]]"
  - "[[sources/ue-slate-liststrees]]"
  - "[[sources/ue-ref-11-assetloadingpolicy]]"
  - "[[sources/ue-coreuobject-objecthandles]]"
  - "[[sources/ue-agent-evaluator]]"
  - "[[sources/ue-meta-honest-limits]]"
entities:
  - "[[entities/IDetailCustomization]]"
  - "[[entities/FTabManager]]"
  - "[[entities/IToolkit]]"
  - "[[entities/FSlateApplication]]"
concepts:
  - "[[concepts/Editor-Only-4-Tier-Separation]]"
  - "[[concepts/Asset-Loading-Policy]]"
  - "[[concepts/Slate-Editor-Runtime-Separation]]"
status: living
tags: [synthesis, editor, propertyeditor, instancedsubobject-pitfall, citation-3tier, mc-kmcproject, asseteditor-layout-bypass, tab-spawner-pattern]
citation_disclosure: "함정 자체 + UStaticMesh.AssetUserData = 🟢 KMCProject 실측 / 자산 에디터 부모 등록 layout delegate 우회 = 🟢 외부 에이전트 실측 / 우회 (c) Tab Spawner 완전 패턴 = 🟢 KMCProject 완전 실증 (P1+P2+P3 sequence + Undo) / 우회 (d) + 다른 자산 에디터 + Instanced TObjectPtr 임의 UCLASS = 🔴 INFERRED"
external_verification:
  - "외부 에이전트 자료 (StaticMeshNiagaraPreview_Journey.md, 2026-05-12) — ⭐⭐ 신뢰도"
  - "KMCProject 우회 (c) Tab Spawner 완전 구현 (P1 + P2 SListView + P3 hook + Undo, 2026-05-12) — 외부 §Phase 6 다음 단계 (미구현) 를 *먼저 검증*"
---

# InstancedSubobject Customization Bypass — RegisterCustomClassLayout 미발화 + 4종 우회

> **Citation 마커** ([[00_meta/06_VaultCitationRule]] 3 tier):
> 🟢 vault raw / 사용자 코드 / 실측 검증 — `[verified]` 또는 직접 검증
> 🟡 PARTIAL — vault 카드 근거 일부 + 외삽
> 🔴 INFERRED — vault 미확정, 일반 UE 지식 추론 (filing-back 의무)

## 1. Thesis (확장)

🟢 **`RegisterCustomClassLayout` 은 *root object* 의 클래스만 매칭** — InstancedSubobject 자손 등록은 호출 X (KMCProject 실측).

🟢 **자산 에디터 (`UStaticMesh` 등) 의 root UCLASS 등록도 발화 안 됨** — `FStaticMeshEditor` 가 Properties Tab 의 `IDetailsView` 에 `SetGenericLayoutDetailsDelegate` 또는 자체 layout delegate 를 *강제 적용* (외부 에이전트 실측, 7가지 회피 시도 무위).

🟢 **우회 (c) Tab Spawner = *유일하게 작동하는 완전 패턴*** — KMCProject 가 외부 에이전트의 Phase 6 "다음 단계 (미구현)" 를 *먼저 검증* (P1 Nomad 탭 + P2 SListView 본체 + P3 WeakWidget hook + Undo PostEditUndo, 2026-05-12).

## 2. 매트릭스 / 결정 트리

### 2.1 함정 발생 매트릭스 (2 차원, 검증 출처별)

| 등록 대상 | 컨테이너 | 결과 | 검증 출처 |
| -- | -- | -- | -- |
| **자손 UCLASS** (InstancedSubobject) | `UStaticMesh::AssetUserData` 안 `UMCNiagaraSocketBindings` | `MakeInstance` / `CustomizeDetails` 둘 다 미호출 | **🟢** KMCProject 실측 (2026-05-12) |
| **부모 root UCLASS** (자산 에디터 있음) | `UStaticMesh` 직접 등록 | 둘 다 미호출 — SM Editor 의 layout delegate 강제 우회 | **🟢** 외부 에이전트 실측 (7가지 시도 무위) |
| **부모 root UCLASS** (자산 에디터 없음, 일반 UCLASS) | `UMyAsset` 등록 | 정상 발화 | 🟡 vault `[[sources/ue-editor-propertyeditor]]` §2.4 |
| UAssetUserData 호환 자산 부모 등록 | 동일 패턴 | 우회 가능성 | 🔴 INFERRED |
| 임의 UCLASS `Instanced TObjectPtr<UMyComponent>` | InstancedSubobject | 자손 등록 미호출 가능성 | 🔴 INFERRED |
| `UDataAsset` / `UStateTreeState` inner | InstancedSubobject | 동일 가능성 | 🔴 INFERRED |

### 2.2 우회 결정 트리 (보정)

```
디테일 표시 변경 원함 + 컨테이너 분석
│
├─ 컨테이너 = 자산 에디터 있음 (UStaticMesh / USkeletalMesh / UMaterial / 등)
│   ├─ element 가 USTRUCT + 한 줄 압축 OK
│   │   └─ ✅ 우회 (a) RegisterCustomPropertyTypeLayout — 🟢 권장 (최소 작업)
│   ├─ 진정한 SListView / 다중 컬럼 / 가상화 필요
│   │   ├─ ✅ 우회 (c) Tab Spawner — 🟢 KMCProject 완전 실증 (권장)
│   │   └─ 우회 (d) DataAsset 분리 — 🟡 검증된 패턴, 데이터 모델 변경 비용
│   └─ 우회 (b) 부모 UCLASS 등록 — ❌ **🔴 작동 안 함 실증**
│
├─ 컨테이너 = 일반 UCLASS (자산 에디터 없음)
│   └─ 우회 (b) 부모 UCLASS 등록 — 🟡 작동 가능 (plugin race 위험 남음)
│
└─ 컨테이너 = 일반 UCLASS root + 자기 변경 가능
    └─ 우회 (d) DataAsset 분리 — 🟡
```

## 3. KMCProject 사례 단계별 (P1 → P2 → P3 완전 실증)

### 3.1 P1 — Nomad Tab Spawner 등록 🟢

`UMCNiagaraSocketPreviewSubsystem::Initialize` 안 `FGlobalTabmanager::RegisterNomadTabSpawner` 호출. 사용자가 `창 > 개발자 도구 > 기타` 메뉴에서 invoke → 도킹 탭 표시. SM Editor 의 *내부 탭바 (디테일 / 소켓 매니저 / 프리뷰 씬 세팅 옆)* 에 도킹 가능. 함정 10 차원 2 (layout delegate) 영향 없음.

### 3.2 P2 — SListView 임베드 본체 🟢

`SMCBindingsListWidget` 신규 — SCompoundWidget 자손 (SListView<TSharedPtr<FMCBindingsListItem>> + SHeaderRow 6 컬럼 + SMultiColumnTableRow 자손). IPropertyHandle 의존 제거 — `TWeakObjectPtr<UMCNiagaraSocketBindings>` 직접 + 수동 mutation 패턴:

```cpp
FScopedTransaction Tx(LOCTEXT("EditX", "Edit X"));
Bindings->Modify();
Bindings->Bindings[i].XXX = NewValue;
Bindings->MarkPackageDirty();
UMCNiagaraSocketBindings::OnBindingsChanged.Broadcast(Bindings->GetOuter());
```

### 3.3 P3 — WeakWidget hook + Undo PostEditUndo 🟢

**P3-A (WeakWidget hook)** — `PreviewSubsystem::WeakListWidget` 멤버 보관:
- `SpawnDockTab` 안 `WeakListWidget = ListWidget` + `OnTabClosed_Lambda` 에서 reset.
- `OnAssetOpenedInEditor` / `OnAssetEditorRequestClose` 콜백 안 `SyncDockTabBindings()` 호출 → `WeakListWidget.Pin()->SetBindings(NewBindings, NewHostMesh)`.
- 결과: 사용자가 SM 에디터 *닫고 다른 자산 열기* → 도킹 탭 자동 갱신.

**P3-B (Tab Spawn 시점 강제 자산 검색)** — `ResolveCurrentEditedAssetForDockTab`:
- `CurrentEditedAsset` nullptr 면 `UAssetEditorSubsystem::GetAllEditedAssets()` 로 폴백.
- StaticMesh / SkeletalMesh 우선 검색.
- 결과: 사용자가 *도킹 탭 먼저 invoke → 자산 열기* 순서도 작동.

**P3-C (Undo/Redo 자동 갱신)** — `PostEditUndo` override:

```cpp
void UMCNiagaraSocketBindings::PostEditUndo()
{
    Super::PostEditUndo();
    if (UObject* HostAsset = GetOuter())
    {
        OnBindingsChanged.Broadcast(HostAsset);
    }
}
```

+ `SMCBindingsListWidget::Construct` 안 `OnBindingsChanged.AddSP(this, &OnBindingsChangedHandler)` 구독:

```cpp
void SMCBindingsListWidget::OnBindingsChangedHandler(UObject* HostAsset)
{
    if (WeakHostMesh.Get() == HostAsset) { RebuildItems(); }
}
```

+ Destructor 안 `OnBindingsChanged.Remove(Handle)` 해제.

결과: Ctrl+Z / Ctrl+Y → Transaction System 데이터 복원 → `PostEditUndo` 자동 호출 → Broadcast → `OnBindingsChangedHandler` → `RebuildItems` → SListView 행 즉시 갱신.

### 3.4 외부 에이전트 자료의 보정 회고

**우리 1차 추론 — *부모 등록 (우회 b) 이 외부 에이전트의 기본 접근*** → **틀림** (외부 Journey §Phase 5 의 7가지 무위 시도). 외부도 결국 도킹 탭으로 전환 결정 (§Phase 6) 하지만 *구현 미진행*. KMCProject 가 P1+P2+P3 *먼저 완성*.

함정 9 (TSharedFromThis 다이아몬드) 의 외부 evaluator 권고 사례 — vault 평가자 자체의 self-correction 의무 ([[sources/ue-agent-evaluator]] §3).

## 4. 우회 4종 상세 (보정)

### 4.1 우회 (a) — `RegisterCustomPropertyTypeLayout` USTRUCT 단위 🟢

```cpp
PropertyModule.RegisterCustomPropertyTypeLayout(
    FMyElementStruct::StaticStruct()->GetFName(),
    FOnGetPropertyTypeCustomizationInstance::CreateStatic(&FMyElementCustomization::MakeInstance));
```

- **작동 원리**: PropertyTypeLayout 은 *타입 단위 등록* — root/inner/element/InstancedSubobject 어디서나 호출.
- **제약**: element 한 줄 압축까지만. SListView 임베드 불가.
- **검증**: 🟢 KMCProject `FMCNiagaraSocketBindingDetails` 사용자 실측.

### 4.2 우회 (b) — 부모 UCLASS Customization 가로채기 🔴 **작동 안 함 (실증)**

- **🔴 실측 (외부 §Phase 5)**: `MakeInstance` / `CustomizeDetails` 둘 다 발화 X. 원인 — `FStaticMeshEditor` 의 `SetGenericLayoutDetailsDelegate` 강제 우회.
- **7가지 회피 시도 무위**: GetEditorName 비교 제거 / 자동 spawn / PostEditChangeProperty override / LoadingPhase 변경 / OnAssetEditorOpened hook 재등록 / GEditor 지연 init / 진단 로그.
- **결론**: 자산 에디터 안에선 사실상 불가능. 일반 UCLASS root 에선 작동 가능 (🟡 PARTIAL).

### 4.3 우회 (c) — Tab Spawner / Nomad Tab 🟢 **KMCProject 완전 실증** (P1+P2+P3)

#### 4.3.1 등록 표준 패턴

```cpp
#if WITH_EDITOR
void UMyEditorSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    // 🟢 P3 함정 12 — FSlateApplication 미초기화 시 OnPostEngineInit 지연
    if (FSlateApplication::IsInitialized())
    {
        RegisterDockTab();
    }
    else
    {
        PostEngineInitHandle = FCoreDelegates::OnPostEngineInit.AddUObject(
            this, &UMyEditorSubsystem::RegisterDockTab);
    }
}

void UMyEditorSubsystem::RegisterDockTab()
{
    // 🟢 P3 함정 14 — WorkspaceMenuStructure 모듈 명시 로드
    if (!FModuleManager::Get().IsModuleLoaded("WorkspaceMenuStructure"))
    {
        FModuleManager::Get().LoadModule(TEXT("WorkspaceMenuStructure"));
    }
    // 중복 등록 방지
    if (FGlobalTabmanager::Get()->HasTabSpawner(MyTabId)) { return; }

    FGlobalTabmanager::Get()->RegisterNomadTabSpawner(MyTabId,
        FOnSpawnTab::CreateUObject(this, &UMyEditorSubsystem::SpawnDockTab))
        .SetDisplayName(LOCTEXT("MyTabName", "My Tab"))
        .SetGroup(WorkspaceMenu::GetMenuStructure().GetDeveloperToolsMiscCategory())
        .SetIcon(FSlateIcon(FAppStyle::GetAppStyleSetName(), "Icons.Niagara"));
}
#endif
```

🟢 vault 정합: [[sources/ue-slate-docking]] §3.1 + §3.6 [verified].

#### 4.3.2 자산 자동 잡기 (P3-B 패턴)

```cpp
UObject* UMyEditorSubsystem::ResolveCurrentEditedAssetForDockTab() const
{
    // 1차 — CurrentEditedAsset 캐싱 (OnAssetOpenedInEditor 콜백에서 set)
    if (UObject* Cur = CurrentEditedAsset.Get()) { return Cur; }

    // 2차 — GetAllEditedAssets 폴백 (사용자가 자산 *먼저 열고* 도킹 탭 *나중에 invoke* 한 케이스)
    UAssetEditorSubsystem* AES = GEditor ? GEditor->GetEditorSubsystem<UAssetEditorSubsystem>() : nullptr;
    if (!AES) { return nullptr; }
    for (UObject* Asset : AES->GetAllEditedAssets())
    {
        if (Asset && (Asset->IsA<UStaticMesh>() || Asset->IsA<USkeletalMesh>()))
        {
            return Asset;
        }
    }
    return nullptr;
}
```

🟢 vault 정합: [[sources/ue-editor-asseteditorapi]] §1 [verified].

#### 4.3.3 WeakWidget hook (P3-A 패턴)

```cpp
// 멤버: TWeakPtr<SMyListWidget> WeakListWidget;

TSharedRef<SDockTab> UMyEditorSubsystem::SpawnDockTab(const FSpawnTabArgs& Args)
{
    TSharedPtr<SMyListWidget> ListWidget;
    TSharedRef<SVerticalBox> RootBox = SNew(SVerticalBox)
        + SVerticalBox::Slot().FillHeight(1.f)
        [ SAssignNew(ListWidget, SMyListWidget).Data(GetInitialData()) ];

    // 🟢 P3-A 함정 13 — WeakWidget hook (자산 변경 시 자동 SetData)
    WeakListWidget = ListWidget;

    return SNew(SDockTab)
        .TabRole(ETabRole::NomadTab)
        .Label(LOCTEXT("MyTab", "My Tab"))
        .OnTabClosed_Lambda([WeakSelf](TSharedRef<SDockTab>)
        {
            if (auto Self = WeakSelf.Get()) { Self->WeakListWidget.Reset(); }
        })
        [ RootBox ];
}

void UMyEditorSubsystem::OnAssetOpened(UObject* Asset, IAssetEditorInstance* Inst)
{
    CurrentEditedAsset = Asset;
    if (auto LW = WeakListWidget.Pin()) { LW->SetData(GetDataFor(Asset)); }
}
```

#### 4.3.4 Undo/Redo 자동 갱신 (P3-C 패턴) ⭐

```cpp
// UObject 측 (Bindings 같은 데이터 클래스)
#if WITH_EDITOR
void UMyData::PostEditUndo()
{
    Super::PostEditUndo();
    OnDataChanged.Broadcast(GetOuter());   // 정적 멀티캐스트 → UI 구독자 모두 갱신
}
#endif

// Widget 측
void SMyListWidget::Construct(const FArguments& InArgs)
{
    // ... data 설정
    OnDataChangedHandle = UMyData::OnDataChanged.AddSP(this, &SMyListWidget::OnDataChangedHandler);
    // ... ChildSlot 빌드
}

SMyListWidget::~SMyListWidget()
{
    if (OnDataChangedHandle.IsValid())
    {
        UMyData::OnDataChanged.Remove(OnDataChangedHandle);
    }
}

void SMyListWidget::OnDataChangedHandler(UObject* HostAsset)
{
    if (WeakHostMesh.Get() == HostAsset) { RebuildItems(); }
}
```

#### 4.3.5 Mutation 표준 패턴 (수동 Undo)

```cpp
FScopedTransaction Tx(LOCTEXT("EditX", "Edit X"));
Data->Modify();
Data->Field = NewValue;
Data->MarkPackageDirty();
UMyData::OnDataChanged.Broadcast(Data->GetOuter());  // PostEditUndo 가 Undo/Redo 시 자동 호출
```

#### 4.3.6 vault 정합 매트릭스

- 🟢 `[[sources/ue-slate-docking]]` §3.1 [verified] `RegisterNomadTabSpawner` (TabManager.h L1499)
- 🟢 `[[sources/ue-editor-asseteditorapi]]` §1 [verified] `OnAssetOpenedInEditor` 2-param + `GetAllEditedAssets`
- 🟢 `[[sources/ue-editor-eventbinding]]` [verified] Initialize/Deinitialize 페어
- 🟢 KMCProject 사용자 실측 — 도킹 탭 표시 + SListView 본체 + Undo/Redo 모두 작동 (스크린샷 3건)

### 4.4 우회 (d) — 데이터 모델을 별도 PrimaryDataAsset 으로 분리 🟡

(이전 내용 유지 — 별도 root UCLASS 라 자산 에디터 없음 → `RegisterCustomClassLayout` 정상 발화. SListView 임베드 가능. vault `[[concepts/Asset-Loading-Policy]]` §2.3 + `[[sources/ue-coreuobject-objecthandles]]`. KMCProject 시도 안 함.)

## 5. 함정 / 열린 질문 (filing-back 완료 / 후보)

### 5.1 filing-back 완료 (🔴 → 🟢)

- [x] 🟢 우회 (b) 자산 에디터 안 미발화 — 외부 에이전트 Journey Phase 5 실증 (2026-05-12)
- [x] 🟢 함정 9 (TSharedFromThis 다이아몬드) 의 외부 평가자 권고 사례
- [x] 🟢 **우회 (c) Tab Spawner 완전 패턴** — KMCProject P1+P2+P3 실증 (2026-05-12) ⭐
- [x] 🟢 **함정 12 — FSlateApplication 미초기화 시 FCoreDelegates::OnPostEngineInit 지연** — KMCProject 실증
- [x] 🟢 **함정 13 — Tab 안 위젯 자산 변경 시 WeakWidget hook + SetData 패턴** — KMCProject P3-A 실증
- [x] 🟢 **함정 14 — UAssetEditorSubsystem::GetAllEditedAssets() 폴백 (Tab Spawn 시점 강제 자산 검색)** — KMCProject P3-B 실증
- [x] 🟢 **함정 15 — Undo/Redo 자동 UI 갱신 = PostEditUndo override + 정적 멀티캐스트 + SP 구독** — KMCProject P3-C 실증 ⭐

### 5.2 filing-back 후보 (🔴 INFERRED 잔존)

- [ ] 🔴 다른 자산 에디터 (`USkeletalMesh` / `UMaterial` / `UAnimBlueprint` / `UBehaviorTree` / `UNiagaraSystem`) 의 layout delegate 우회 — 미검증
- [ ] 🔴 `FRegisterCustomClassLayoutParams` (5.x) — InstancedSubobject 강제 발화 hook
- [ ] 🔴 `IDetailRootObjectCustomization` 와 결합 시 우회 가능성
- [ ] 🔴 임의 UCLASS Instanced TObjectPtr / `UDataAsset` inner / `UStateTreeState` Task/Condition
- [ ] 🔴 우회 (d) DataAsset 분리 시 cross-asset preview 표시
- [ ] 🔴 우회 (c) Nomad 탭이 *Major Tab* 또는 *Minor Tab* 으로 자산 에디터 *내부 사이드* 에 직접 도킹되는 메커니즘 (외부 에이전트 §Phase 6 의 "별도 도킹 가능한 탭" 의 *정확한 통합 경로*)

## 6. 관련

### Sources (13)

- [[sources/ue-editor-propertyeditor]] §2.6.10 — 함정 10 권위 매트릭스
- [[sources/ue-editor-asseteditorapi]] §1/§3/§4 — [verified]
- [[sources/ue-editor-unrealed-asseteditortoolkit]] — 22 KB raw enrich 후보
- [[sources/ue-assetclasses-assetuserdata]] §3 — IInterface_AssetUserData
- [[sources/ue-editor-personatoolkit]] — Skeletal Mesh 분기
- [[sources/ue-editor-eventbinding]] — OnAssetOpenedInEditor 라이프사이클
- [[sources/ue-slate-docking]] §3.1/§3.6/§7 — 도킹 탭 + 함정 11~15
- [[sources/ue-slate-skill]] — Slate 메인
- [[sources/ue-slate-liststrees]] §11 — SListView 함정 (P2 적용)
- [[sources/ue-ref-11-assetloadingpolicy]] §2/§6 — 우회 (d)
- [[sources/ue-coreuobject-objecthandles]] — FPrimaryAssetId
- [[sources/ue-agent-evaluator]] — self-correction
- [[sources/ue-meta-honest-limits]] — self-eval bias

### Entities / Concepts / Governance

- [[entities/IDetailCustomization]] · [[entities/FTabManager]] · [[entities/IToolkit]] · [[entities/FSlateApplication]]
- [[concepts/Editor-Only-4-Tier-Separation]] · [[concepts/Asset-Loading-Policy]] · [[concepts/Slate-Editor-Runtime-Separation]]
- [[00_meta/06_VaultCitationRule]]

### External Sources / 측정

- `StaticMeshNiagaraPreview.md` + `StaticMeshNiagaraPreview_Journey.md` (외부 에이전트, 2026-05-12)
- [[sources/ue-measure-instancedsubobject-2026-05-12]] — ⭐⭐ 측정

## 7. Changelog

| 날짜 | 변경 |
| -- | -- |
| 2026-05-12 | 최초 작성 — KMCProject `UMCNiagaraSocketBindings` 케이스 + 함정 10 + 우회 4종 + 3 tier citation 마커 |
| 2026-05-12 | 외부 에이전트 자료 보정 ⭐⭐ — Journey Phase 5 의 7가지 무위 시도 매트릭스 + §4.2 우회 (b) 🔴 강화 + §4.3 우회 (c) 외부 결정 사례 |
| 2026-05-12 | **§4.3 우회 (c) Tab Spawner 🟡 → 🟢 완전 승급** ⭐ — KMCProject P1 (Nomad 탭 등록) + P2 (SListView 본체 추출) + P3 (WeakWidget hook + GetAllEditedAssets 폴백 + Undo PostEditUndo + OnBindingsChanged SP 구독) 완전 실증. §3 KMCProject 사례 단계별 P1/P2/P3 분리 + §4.3.1~4.3.6 표준 패턴 6 단 + §5.1 filing-back 완료 5건 (우회 c + 함정 12/13/14/15). 외부 §Phase 6 의 "다음 단계 (미구현)" 부분을 KMCProject 가 *먼저 검증* — vault filing-back ROI 실증. external_verification 갱신 + tag `tab-spawner-pattern` 추가. |
