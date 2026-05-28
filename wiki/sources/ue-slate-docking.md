---
type: source
title: "UE Slate — Docking sub-skill"
slug: ue-slate-docking
source_path: raw/ue-wiki-llm/skills/Slate/references/Docking.md
source_kind: text
source_date: 2026-05-09
ingested: 2026-05-09
last_updated: 2026-05-28
audit_5_5_4: pass-line-shifted  # 2026-05-28 Phase 2-B auto-classified
related_entities:
  - "[[entities/FTabManager]]"
tags: [ue, slate, editor, ui, tab-spawner-pattern]
---

# UE Slate — Docking sub-skill

> Source: [[raw/ue-wiki-llm/skills/Slate/references/Docking.md]]
> Parent: [[sources/ue-slate-skill]]

## 1. Summary

🛠 Docking 시스템 — [[entities/FTabManager]] + FTabSpawnerEntry + FLayoutExtender + SDockTab + SDockingArea. 인하우스 에디터 표준.

## 2. Key claims

- FTabManager: 탭 + dock layout 관리.
- FTabSpawnerEntry: 탭 등록 메타 (Name / Label / Icon / SpawnDelegate).
- FLayoutExtender: 다른 모듈이 기존 layout 에 탭 추가.
- SDockTab: 실제 탭 위젯. SetContent(SWidget) 으로 본문.
- SDockingArea: 도킹 영역 (탭 컨테이너 + splitter).
- Layout 저장: FTabManager::FLayout / FStack / FArea — XML 자동 저장 → 사용자 layout 보존.
- 표준 패턴: TabManager->RegisterTabSpawner("MyTab", FOnSpawnTab::CreateRaw(this, &FMyToolkit::SpawnMyTab)).

## 4. KMCProject Tab Spawner 실증 패턴 + 함정 매트릭스 신규 5건 (2026-05-12)

> [[synthesis/instanced-subobject-customization-bypass]] §4.3 우회 (c) 의 KMCProject P1+P2+P3 완전 실증 결과 — vault 카드 보강.
> Citation 마커: 🟢 KMCProject 실측 검증.

### 4.1 함정 11 — `WorkspaceMenu` 카테고리 DisplayName 의 로케일 의존 🟢

`GetDeveloperToolsMiscCategory()` 의 `GetDisplayName()` 이 시스템 로케일에 따라 다른 문자열 반환:
- 영문: `"Misc"`
- 한국어: `"기타"`
- 일본어: `"その他"`

영문 메뉴 안내 ("Window > Developer Tools > Misc") 만 제공하면 사용자가 못 찾음. **사용자 안내 시 *로케일 무관 키워드* (Tab DisplayName) 사용 의무**. 진단 로그에 `WorkspaceItem->GetDisplayName().ToString()` 출력 권장 — KMCProject 실측에서 `'기타'` 로 표시되어 메뉴 위치 진단 가능.

### 4.2 함정 12 — `FSlateApplication` 미초기화 시 `FCoreDelegates::OnPostEngineInit` 지연 🟢

`UEditorSubsystem::Initialize` 가 *Slate 초기화 전* 호출될 수 있음. `RegisterNomadTabSpawner` 가 `FSlateApplication::Get()` 의존 → crash 또는 silent fail.

```cpp
void UMyEditorSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
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

void UMyEditorSubsystem::Deinitialize()
{
    if (PostEngineInitHandle.IsValid())
    {
        FCoreDelegates::OnPostEngineInit.Remove(PostEngineInitHandle);
    }
    ...
}
```

KMCProject 실측 — `IsInitialized=1` 케이스 (정상). 다만 *Slate 미초기화 경로* 도 코드에 보강해 두는 게 표준.

### 4.3 함정 13 — Tab 안 위젯의 `WeakWidget` hook + 자산 변경 시 자동 SetData 🟢

Tab Spawner 가 위젯 *Construct 시점에 데이터 fix* — 사용자가 자산 변경하면 위젯이 stale. `UEditorSubsystem` 측에서 `TWeakPtr<SMyWidget> WeakListWidget` 보관 + `OnAssetOpenedInEditor` 콜백에서 `WeakListWidget.Pin()->SetData(...)` 호출.

```cpp
// 멤버: TWeakPtr<SMyWidget> WeakListWidget;

TSharedRef<SDockTab> UMyEditorSubsystem::SpawnDockTab(const FSpawnTabArgs&)
{
    TSharedPtr<SMyWidget> ListWidget;
    auto Root = SNew(SVerticalBox) + SVerticalBox::Slot()[ SAssignNew(ListWidget, SMyWidget).Data(...) ];
    WeakListWidget = ListWidget;  // 🟢 hook
    return SNew(SDockTab)
        .OnTabClosed_Lambda([WeakSelf](TSharedRef<SDockTab>){ if (auto S = WeakSelf.Get()) S->WeakListWidget.Reset(); })
        [ Root ];
}
void UMyEditorSubsystem::OnAssetOpened(UObject* Asset, IAssetEditorInstance*)
{
    CurrentAsset = Asset;
    if (auto LW = WeakListWidget.Pin()) { LW->SetData(GetDataFor(Asset)); }
}
```

🟢 KMCProject 실측 — 자산 변경 시 SListView 자동 갱신.

### 4.4 함정 14 — `UAssetEditorSubsystem::GetAllEditedAssets()` 폴백 (Tab Spawn 시점 강제 자산 검색) 🟢

사용자가 *도킹 탭을 먼저 invoke → 자산을 나중에 열기* 순서면 `OnAssetOpenedInEditor` 콜백 미발화 → `CurrentEditedAsset` nullptr → 위젯 빈 상태.

```cpp
UObject* UMyEditorSubsystem::ResolveCurrentEditedAssetForDockTab() const
{
    if (UObject* Cur = CurrentEditedAsset.Get()) { return Cur; }
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

🟢 KMCProject 실측 — 두 순서 모두 작동.

### 4.5 함정 15 — Undo/Redo 자동 UI 갱신 = `PostEditUndo` override + 정적 멀티캐스트 + SP 구독 🟢⭐

UObject 의 데이터 mutation 은 `FScopedTransaction + Modify()` 로 Undo 자동. 하지만 *UI 구독자* (SListView 등) 는 *자동 갱신 안 됨*. `PostEditUndo` override 필요 + 위젯이 정적 멀티캐스트 SP 구독.

```cpp
// UObject 측 (Bindings 같은 데이터)
#if WITH_EDITOR
void UMyData::PostEditUndo()
{
    Super::PostEditUndo();
    OnDataChanged.Broadcast(GetOuter());  // 정적 멀티캐스트 → 모든 UI 구독자 갱신
}
#endif

// Widget 측
void SMyListWidget::Construct(...)
{
    Handle = UMyData::OnDataChanged.AddSP(this, &SMyListWidget::OnDataChangedHandler);
    ...
}
SMyListWidget::~SMyListWidget()
{
    if (Handle.IsValid()) UMyData::OnDataChanged.Remove(Handle);
}
void SMyListWidget::OnDataChangedHandler(UObject* Host)
{
    if (WeakHostMesh.Get() == Host) RebuildItems();
}
```

🟢 KMCProject 실측 — Ctrl+Z / Ctrl+Y 시 SListView 행 즉시 복원. SP delegate 는 SWidget 베이스의 `TSharedFromThis<SWidget>` 이용. 추가 TSharedFromThis 상속 X (vault `[[sources/ue-editor-propertyeditor]]` §2.6.9 함정 9 회피).

### 4.6 적용 cross-link

- [[synthesis/instanced-subobject-customization-bypass]] §4.3.1~4.3.6 (P1+P2+P3 표준 패턴)
- [[sources/ue-measure-instancedsubobject-2026-05-12]] (⭐⭐ 측정)
- [[sources/ue-editor-asseteditorapi]] §1 (OnAssetOpenedInEditor + GetAllEditedAssets)
- [[sources/ue-editor-propertyeditor]] §2.6.1 함정 1 (PostEditUndo 페어 보강)
## §X. 5.5.4 Audit Status (2026-05-28)

> Phase 2-B sources audit · [[synthesis/phase-2b-sources-audit]] · **결정: 🟢 lineshift-only**

raw 5.5.4 vs 5.7.4 diff 자동 분류 결과: **lineshift-only**. 5.5↔5.7 raw diff 가 라인 번호 shift 만 — 본문 의미 무영향.

원본 5.7.4 시점 검증 내용 그대로 5.5.4 환경에서 유효. 본 페이지의 `raw/ue-wiki-llm/...` 인용은 5.7.4 vintage 표기 보존 — 신규 인용은 `raw/ue-wiki-llm_5_5_4/...` 사용 (CLAUDE.md §0.1).
